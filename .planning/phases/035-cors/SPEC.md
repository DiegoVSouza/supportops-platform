# Specification

Let a browser front served from another origin (Cloudflare Pages, lab ADR-001) call this API, without widening the attack surface.

## Behaviour

- `CORS_ALLOWED_ORIGINS` is a comma-separated list of exact origins. Empty or unset: CORS is off and nothing changes.
- A listed origin gets preflight answered and `Access-Control-Allow-Origin` on responses, including 401 and 429, so the browser can show the error.
- An unlisted origin gets no `Access-Control-Allow-Origin`; preflight returns 400.
- Credentials stay off: clients use a bearer token. Allowed methods GET, POST, OPTIONS. Allowed headers Authorization, Content-Type, Idempotency-Key, traceparent, tracestate. `Retry-After` is exposed.
- Startup fails on `*`, a wildcard host, a path, a query, credentials in the URL, or plain http that is not loopback.
- The middleware is outermost so preflight is answered before authentication and rate limiting.

## Contract

| Requirement | Rule |
| --- | --- |
| API-002 | `tests/test_cors.py`. The OpenAPI document is unchanged (`scripts/export_openapi.py --check`). |
| SEC-002 | CORS never replaces authorization: a request from a disallowed origin is still served or refused by the same token checks. The browser, not the server, withholds the response. |

## Out of scope

Cookie sessions, per-route policy, the Fly setting itself and the Keycloak client (lab phase F4/F5).
