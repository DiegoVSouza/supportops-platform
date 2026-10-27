"""Billing and CRM mock tools with an explicit in-process authorization gateway."""

from __future__ import annotations

from dataclasses import dataclass
from opentelemetry import trace

from mcp.server import MCPServer
from mcp.server.auth.middleware.auth_context import get_access_token
from mcp.server.auth.provider import AccessToken, TokenVerifier
from mcp.server.auth.settings import AuthSettings
from pydantic import AnyHttpUrl

from supportops_platform.contracts import Principal
from supportops_platform.integrations.toolkit import bounded_tool
from supportops_platform.repositories import AuthorizationError


@dataclass(frozen=True, slots=True)
class MockInvoice:
    tenant_id: str
    invoice_id: str
    amount_cents: int
    status: str


class ToolPolicy:
    """Allowlist binds each local mock tool to a scope and a caller role."""

    REQUIRED: dict[str, tuple[str, frozenset[str]]] = {
        "lookup_invoice": ("billing:read", frozenset({"agent", "approver"})),
        "lookup_customer": ("crm:read", frozenset({"agent", "approver"})),
        "propose_refund": ("refund:request", frozenset({"agent"})),
    }

    @classmethod
    def authorize(cls, principal: Principal, tool_name: str) -> None:
        required = cls.REQUIRED.get(tool_name)
        if required is None:
            raise AuthorizationError("tool is not allowlisted")
        scope, roles = required
        if scope not in principal.scopes or not principal.roles.intersection(roles):
            raise AuthorizationError("principal is not authorized for this tool")


class LocalToolGateway:
    """Testable gateway keeps principal context outside model-controlled arguments."""

    def __init__(self) -> None:
        self.invoices = {
            "inv-a-1": MockInvoice("tenant-a", "inv-a-1", 2500, "paid"),
            "inv-b-1": MockInvoice("tenant-b", "inv-b-1", 9000, "paid"),
        }
        self.customers = {
            ("tenant-a", "customer-a"): {"customer_id": "customer-a", "tier": "standard"},
            ("tenant-b", "customer-b"): {"customer_id": "customer-b", "tier": "standard"},
        }
        self._invoice_tool = bounded_tool(
            "lookup_invoice", self._lookup_invoice_raw,
            {"invoice_id": {"type": "string", "minLength": 1, "maxLength": 64}},
            {"invoice_id": {"type": "string"}, "amount_cents": {"type": "integer"}, "status": {"type": "string"}},
        )
        self._customer_tool = bounded_tool(
            "lookup_customer", self._lookup_customer_raw,
            {"tenant_id": {"type": "string"}, "customer_id": {"type": "string"}},
            {"customer_id": {"type": "string"}, "tier": {"type": "string"}},
        )
        self._refund_tool = bounded_tool(
            "propose_refund", self._propose_refund_raw,
            {"ticket_id": {"type": "string"}, "tenant_id": {"type": "string"}, "amount_cents": {"type": "integer"}},
            {"ticket_id": {"type": "string"}, "tenant_id": {"type": "string"}, "amount_cents": {"type": "integer"}, "state": {"type": "string"}, "effect_performed": {"type": "boolean"}},
        )

    def _lookup_invoice_raw(self, invoice_id: str) -> dict[str, object]:
        invoice = self.invoices.get(invoice_id)
        if invoice is None:
            raise ValueError("invoice not found")
        return {"invoice_id": invoice.invoice_id, "amount_cents": invoice.amount_cents, "status": invoice.status}

    def _lookup_customer_raw(self, tenant_id: str, customer_id: str) -> dict[str, str]:
        customer = self.customers.get((tenant_id, customer_id))
        if customer is None:
            raise ValueError("customer not found")
        return customer.copy()

    @staticmethod
    def _propose_refund_raw(ticket_id: str, tenant_id: str, amount_cents: int) -> dict[str, object]:
        if amount_cents <= 0 or amount_cents > 5000:
            raise ValueError("refund exceeds local approval ceiling")
        return {
            "ticket_id": ticket_id,
            "tenant_id": tenant_id,
            "amount_cents": amount_cents,
            "state": "needs_approval",
            "effect_performed": False,
        }

    def lookup_invoice(self, principal: Principal, invoice_id: str) -> dict[str, object]:
        ToolPolicy.authorize(principal, "lookup_invoice")
        invoice = self.invoices.get(invoice_id)
        if invoice is None or invoice.tenant_id != principal.tenant_id:
            raise AuthorizationError("invoice not found")
        from supportops_toolkit.guardrails import authorize_tool

        authorize_tool("support", "lookup_invoice")
        return self._invoice_tool(invoice_id=invoice_id)

    def lookup_customer(self, principal: Principal, customer_id: str) -> dict[str, str]:
        ToolPolicy.authorize(principal, "lookup_customer")
        if (principal.tenant_id, customer_id) not in self.customers:
            raise AuthorizationError("customer not found")
        return self._customer_tool(tenant_id=principal.tenant_id, customer_id=customer_id)

    def propose_refund(
        self, principal: Principal, ticket_id: str, amount_cents: int
    ) -> dict[str, object]:
        ToolPolicy.authorize(principal, "propose_refund")
        return self._refund_tool(
            ticket_id=ticket_id, tenant_id=principal.tenant_id, amount_cents=amount_cents
        )


def create_mock_mcp_server(
    gateway: LocalToolGateway | None = None,
    authenticated_principal: Principal | None = None,
) -> MCPServer:
    """Create an offline server with identity injected outside model-controlled args."""
    gateway = gateway or LocalToolGateway()
    server = MCPServer("supportops-mock-tools", version="0.2.0")

    def require_principal() -> Principal:
        if authenticated_principal is None:
            raise AuthorizationError("authenticated principal is required")
        return authenticated_principal

    @server.tool()
    def lookup_invoice(invoice_id: str) -> dict[str, object]:
        """Return a synthetic invoice summary for the injected authenticated tenant."""
        return gateway.lookup_invoice(require_principal(), invoice_id)

    @server.tool()
    def propose_refund(ticket_id: str, amount_cents: int) -> dict[str, object]:
        """Create an approval proposal only; this tool never issues a refund."""
        return gateway.propose_refund(require_principal(), ticket_id, amount_cents)

    return server


def create_network_mcp_server(
    token_verifier: TokenVerifier,
    issuer_url: str,
    resource_server_url: str,
    gateway: LocalToolGateway | None = None,
) -> MCPServer:
    """Create an HTTP MCP server whose principal comes only from verified bearer context."""
    gateway = gateway or LocalToolGateway()
    server = MCPServer(
        "supportops-network-tools",
        version="0.3.0",
        token_verifier=token_verifier,
        auth=AuthSettings(
            issuer_url=AnyHttpUrl(issuer_url),
            resource_server_url=AnyHttpUrl(resource_server_url),
            required_scopes=["billing:read"],
            validate_token_resource=True,
        ),
    )

    def transport_principal() -> Principal:
        token: AccessToken | None = get_access_token()
        if token is None:
            raise AuthorizationError("verified transport identity is required")
        claims = token.claims or {}
        tenant_id = claims.get("tenant_id")
        roles = claims.get("roles", [])
        if not isinstance(tenant_id, str) or not tenant_id or not isinstance(roles, list):
            raise AuthorizationError("verified token lacks principal claims")
        return Principal(
            subject=token.subject or token.client_id,
            tenant_id=tenant_id,
            roles=frozenset(str(role) for role in roles),
            scopes=frozenset(token.scopes),
        )

    @server.tool()
    def lookup_invoice(invoice_id: str) -> dict[str, object]:
        """Look up an invoice inside the authenticated transport tenant."""
        with trace.get_tracer("p05.tools").start_as_current_span("tool.lookup_invoice",record_exception=False):
            return gateway.lookup_invoice(transport_principal(), invoice_id)

    @server.tool()
    def lookup_customer(customer_id: str) -> dict[str, str]:
        """Look up a customer inside the authenticated transport tenant."""
        with trace.get_tracer("p05.tools").start_as_current_span("tool.lookup_customer",record_exception=False):
            return gateway.lookup_customer(transport_principal(), customer_id)

    @server.tool()
    def propose_refund(ticket_id: str, amount_cents: int) -> dict[str, object]:
        """Create a refund proposal for the authenticated principal; never issue a refund."""
        with trace.get_tracer("p05.tools").start_as_current_span("tool.propose_refund",record_exception=False):
            return gateway.propose_refund(transport_principal(), ticket_id, amount_cents)

    return server
