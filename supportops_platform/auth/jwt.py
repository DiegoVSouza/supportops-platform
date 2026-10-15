"""JWT verification for the local API boundary."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from jwt.exceptions import InvalidTokenError

from supportops_platform.contracts import Principal

ISSUER = "supportops-platform"
ALGORITHM = "HS256"


def decode_principal(token: str, secret: str) -> Principal:
    claims: dict[str, Any] = jwt.decode(
        token,
        secret,
        algorithms=[ALGORITHM],
        issuer=ISSUER,
        options={"require": ["exp", "sub", "tenant_id", "scope", "roles", "iss"]},
        leeway=0,
    )
    scopes = claims["scope"].split() if isinstance(claims["scope"], str) else claims["scope"]
    roles = claims["roles"]
    if not isinstance(claims["sub"], str) or not claims["sub"]:
        raise InvalidTokenError("subject claim must be a non-empty string")
    if not isinstance(claims["tenant_id"], str) or not claims["tenant_id"]:
        raise InvalidTokenError("tenant_id claim must be a non-empty string")
    if not isinstance(scopes, list) or not all(isinstance(item, str) for item in scopes):
        raise InvalidTokenError("scope claim must be a list or space-delimited string")
    if not isinstance(roles, list) or not all(isinstance(item, str) for item in roles):
        raise InvalidTokenError("roles claim must be a list of strings")
    return Principal(
        subject=claims["sub"],
        tenant_id=claims["tenant_id"],
        roles=frozenset(roles),
        scopes=frozenset(scopes),
    )


def issue_demo_token(
    subject: str,
    tenant_id: str,
    roles: list[str],
    scopes: list[str],
    secret: str,
    lifetime: timedelta = timedelta(minutes=15),
    now: datetime | None = None,
) -> str:
    """Issue a short-lived local demo token; production issuance is external to P05."""
    now = now or datetime.now(timezone.utc)
    claims = {
        "iss": ISSUER,
        "sub": subject,
        "tenant_id": tenant_id,
        "roles": roles,
        "scope": " ".join(scopes),
        "iat": now,
        "exp": now + lifetime,
    }
    return jwt.encode(claims, secret, algorithm=ALGORITHM)
