"""Exercise token issuance, RFC 7662 introspection, and revocation against local Keycloak."""

import asyncio
import os
import sys
import time

import httpx2

from supportops_platform.mcp.identity import IntrospectionTokenVerifier


BASE_URL = os.getenv("P05_KEYCLOAK_URL", "http://127.0.0.1:28180").rstrip("/")
REALM = "p05-local"
CLIENT_ID = "p05-resource"
CLIENT_SECRET = "p05-local-resource-secret-only"
ISSUER = f"{BASE_URL}/realms/{REALM}"
ENDPOINT = f"{ISSUER}/protocol/openid-connect/token/introspect"


async def check():
    async with httpx2.AsyncClient(timeout=5) as client:
        token_response = await client.post(
            f"{ISSUER}/protocol/openid-connect/token",
            data={
                "grant_type": "password",
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "username": "agent-a",
                "password": "p05-test-password-only",
                "scope": "openid billing:read",
            },
        )
        if token_response.is_error:
            body = token_response.json()
            raise RuntimeError(
                f"Keycloak token issuance failed: {body.get('error', 'unknown')} "
                f"({body.get('error_description', 'no description')})"
            )
        token = token_response.json()["access_token"]
        verifier = IntrospectionTokenVerifier(
            endpoint=ENDPOINT,
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            issuer=ISSUER,
            audience=CLIENT_ID,
        )
        accepted = await verifier.verify_token(token)
        if accepted is None:
            diagnostic = await client.post(
                ENDPOINT,
                data={"token": token, "token_type_hint": "access_token"},
                auth=(CLIENT_ID, CLIENT_SECRET),
            )
            diagnostic.raise_for_status()
            raise RuntimeError(
                "Keycloak-issued token did not pass configured MCP claim checks: "
                f"{diagnostic.json()}"
            )
        if accepted.subject != "agent-a" or accepted.claims != {
            "tenant_id": "tenant-a",
            "roles": ["agent"],
        }:
            raise RuntimeError("Keycloak introspection claims did not map to the P05 principal")
        print("PASS token issued; authenticated introspection accepted subject, tenant, role, audience, and scope")

        revoke_response = await client.post(
            f"{ISSUER}/protocol/openid-connect/revoke",
            data={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "token": token,
                "token_type_hint": "access_token",
            },
        )
        revoke_response.raise_for_status()

        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            if await verifier.verify_token(token) is None:
                print("PASS revoked token became inactive at Keycloak introspection")
                return
            await asyncio.sleep(0.25)
        raise RuntimeError("Keycloak continued to report the revoked token as active")


if __name__ == "__main__":
    try:
        asyncio.run(check())
    except Exception as exc:
        print(f"FAIL {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1)
