import asyncio
from datetime import datetime, timezone

import jwt
import pytest

from supportops_platform.mcp.identity import JWTTokenVerifier


@pytest.mark.parametrize("mutation", ["signature", "expired", "audience", "issuer", "roles", "tenant"])
def test_signed_mcp_identity_rejects_invalid_claims(mutation):
    secret = "test-only-signing-material-at-least-32-characters"
    claims = {"iss": "http://127.0.0.1/issuer", "aud": "http://127.0.0.1/mcp",
              "sub": "agent", "tenant_id": "tenant-a", "roles": ["agent"],
              "scope": "billing:read", "exp": int(datetime.now(timezone.utc).timestamp()) + 60}
    if mutation == "expired": claims["exp"] = 1
    if mutation == "audience": claims["aud"] = "another-resource"
    if mutation == "issuer": claims["iss"] = "another-issuer"
    if mutation == "roles": claims["roles"] = "admin"
    if mutation == "tenant": claims["tenant_id"] = ""
    token = jwt.encode(claims, "wrong-key-material-at-least-32-characters" if mutation == "signature" else secret, algorithm="HS256")
    verifier = JWTTokenVerifier(secret, "http://127.0.0.1/issuer", "http://127.0.0.1/mcp")
    assert asyncio.run(verifier.verify_token(token)) is None


def test_signed_mcp_identity_preserves_verified_tenant_roles_and_scopes():
    secret = "test-only-signing-material-at-least-32-characters"
    verifier = JWTTokenVerifier(secret, "http://127.0.0.1/issuer", "http://127.0.0.1/mcp")
    token = verifier.issue("agent", "tenant-a", ["agent"], ["billing:read"])
    verified = asyncio.run(verifier.verify_token(token))
    assert verified.subject == "agent"
    assert verified.claims["tenant_id"] == "tenant-a"
    assert verified.scopes == ["billing:read"]
