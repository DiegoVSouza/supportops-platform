"""Signed local resource tokens; external issuer integration is separately configured."""

from datetime import datetime, timezone
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
