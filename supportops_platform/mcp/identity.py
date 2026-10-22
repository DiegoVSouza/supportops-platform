"""Signed local resource tokens; external issuer integration is separately configured."""

from datetime import datetime, timezone
import ipaddress
from urllib.parse import urlsplit

import httpx2
import jwt
from jwt.exceptions import InvalidTokenError
from mcp.server.auth.provider import AccessToken


class JWTTokenVerifier:
    def __init__(self, secret, issuer, resource):
        if len(secret) < 32: raise ValueError("MCP signing key must contain at least 32 characters")
        self.secret, self.issuer, self.resource = secret, issuer, resource

    def issue(self, subject, tenant_id, roles, scopes):
        now = int(datetime.now(timezone.utc).timestamp())
        return jwt.encode({"iss": self.issuer, "aud": self.resource, "sub": subject,
                           "tenant_id": tenant_id, "roles": sorted(roles),
                           "scope": " ".join(sorted(scopes)), "iat": now, "exp": now+120},
                          self.secret, algorithm="HS256")

    async def verify_token(self, token):
        try:
            data = jwt.decode(token, self.secret, algorithms=["HS256"], issuer=self.issuer,
                              audience=self.resource, options={"require": ["exp","sub","tenant_id","roles","scope","iss","aud"]})
            if not all(isinstance(data[k], str) and data[k] for k in ("sub","tenant_id")): return None
            if not isinstance(data["roles"], list) or not all(isinstance(r,str) for r in data["roles"]): return None
            if not isinstance(data["scope"], str): return None
            return AccessToken(token=token, client_id=data["sub"], subject=data["sub"],
                               scopes=data["scope"].split(), expires_at=int(data["exp"]),
                               resource=self.resource, claims={"tenant_id":data["tenant_id"],"roles":data["roles"]})
        except (InvalidTokenError, ValueError, TypeError): return None


class IntrospectionTokenVerifier:
    """Verify OAuth bearer tokens with RFC 7662 on every request, without caching revocation state."""

    def __init__(self, endpoint, client_id, client_secret, issuer, audience, timeout=3.0):
        parsed = urlsplit(endpoint)
        if parsed.scheme != "https":
            try:
                loopback = parsed.hostname == "localhost" or ipaddress.ip_address(parsed.hostname).is_loopback
            except (TypeError, ValueError):
                loopback = False
            if parsed.scheme != "http" or not loopback:
                raise ValueError("remote token introspection endpoints must use HTTPS")
        if not parsed.hostname or not parsed.path or not client_id or not client_secret:
            raise ValueError("token introspection endpoint and client credentials are required")
        if not issuer or not audience or timeout <= 0:
            raise ValueError("token introspection issuer, audience, and positive timeout are required")
        self.endpoint = endpoint
        self.client_id = client_id
        self.client_secret = client_secret
        self.issuer = issuer.rstrip("/")
        self.audience = audience
        self.timeout = timeout

    async def verify_token(self, token):
        if not isinstance(token, str) or not token:
            return None
        try:
            async with httpx2.AsyncClient(
                auth=(self.client_id, self.client_secret), timeout=self.timeout
            ) as client:
                response = await client.post(
                    self.endpoint,
                    data={"token": token, "token_type_hint": "access_token"},
                    headers={"Accept": "application/json"},
                )
                response.raise_for_status()
                data = response.json()
            if not isinstance(data, dict) or data.get("active") is not True:
                return None
            audiences = data.get("aud")
            if isinstance(audiences, str):
                audiences = [audiences]
            if not isinstance(audiences, list) or self.audience not in audiences:
                return None
            # RFC 7662 makes `sub` optional. Keycloak 26.8.1 introspection returns
            # the realm username claim instead of `sub` for this realm.
            subject = data.get("sub") or data.get("username")
            tenant_id = data.get("tenant_id")
            roles = data.get("roles")
            scope = data.get("scope")
            expires_at = data.get("exp")
            if (
                not isinstance(subject, str) or not subject
                or not isinstance(tenant_id, str) or not tenant_id
                or not isinstance(roles, list) or not all(isinstance(role, str) and role for role in roles)
                or not isinstance(scope, str)
                or not isinstance(expires_at, int) or expires_at <= int(datetime.now(timezone.utc).timestamp())
                or not isinstance(data.get("iss"), str) or data["iss"].rstrip("/") != self.issuer
            ):
                return None
            scopes = scope.split()
            if "billing:read" not in scopes:
                return None
            return AccessToken(
                token=token,
                client_id=data.get("client_id") if isinstance(data.get("client_id"), str) else subject,
                subject=subject,
                scopes=scopes,
                expires_at=expires_at,
                resource=self.audience,
                claims={"tenant_id": tenant_id, "roles": roles},
            )
        except (httpx2.HTTPError, ValueError, TypeError, KeyError):
            return None


class CompositeTokenVerifier:
    """Accept internal short-lived signed tokens and delegate other tokens to the configured issuer."""

    def __init__(self, local_verifier, external_verifier=None):
        self.local_verifier = local_verifier
        self.external_verifier = external_verifier

    async def verify_token(self, token):
        local = await self.local_verifier.verify_token(token)
        if local is not None:
            return local
        if self.external_verifier is None:
            return None
        return await self.external_verifier.verify_token(token)
