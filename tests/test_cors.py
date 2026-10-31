"""CORS for a front served from another origin (lab ADR-001): allowlist only, bearer tokens, no credentials."""
import pytest
from fastapi.testclient import TestClient

from supportops_platform.api.app import create_app
from supportops_platform.api.cors import parse_cors_origins

from test_api_security import TEST_SECRET, auth_headers

PAGES = "https://supportops-console.pages.dev"


def client(origins: str | None) -> TestClient:
    return TestClient(create_app(token_secret=TEST_SECRET, cors_origins=origins))


def preflight(api: TestClient, origin: str, path: str = "/v1/tickets", method: str = "GET"):
    return api.options(
        path,
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": method,
            "Access-Control-Request-Headers": "authorization,traceparent,idempotency-key,content-type",
        },
    )


def test_allowed_origin_passes_preflight_without_credentials() -> None:
    response = preflight(client(PAGES), PAGES)
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == PAGES
    allowed = response.headers["access-control-allow-headers"].lower()
    for name in ("authorization", "traceparent", "idempotency-key", "content-type"):
        assert name in allowed
    assert "access-control-allow-credentials" not in response.headers
    assert response.headers["vary"].lower().count("origin") >= 1


def test_unknown_origin_gets_no_allow_origin_header() -> None:
    response = preflight(client(PAGES), "https://evil.example")
    assert "access-control-allow-origin" not in response.headers
    assert response.status_code == 400


def test_no_configuration_means_no_cors_at_all() -> None:
    api = client(None)
    response = preflight(api, PAGES)
    assert "access-control-allow-origin" not in response.headers
    plain = api.get("/healthz", headers={"Origin": PAGES})
    assert "access-control-allow-origin" not in plain.headers


def test_authorized_request_and_rejection_both_carry_the_header() -> None:
    api = client(PAGES)
    ok = api.get("/v1/tickets", headers={**auth_headers("tenant-a-agent"), "Origin": PAGES})
    assert ok.status_code == 200
    assert ok.headers["access-control-allow-origin"] == PAGES
    denied = api.get("/v1/tickets", headers={"Origin": PAGES})
    assert denied.status_code == 401
    assert denied.headers["access-control-allow-origin"] == PAGES


def test_cors_does_not_replace_authorization() -> None:
    api = client(PAGES)
    assert api.get("/v1/tickets", headers={"Origin": PAGES}).status_code == 401
    assert api.get("/v1/tickets", headers={**auth_headers("tenant-b-agent"), "Origin": "https://evil.example"}).status_code == 200
    # the server still answers; the browser is what withholds the response from a disallowed origin


def test_two_origins_are_matched_exactly() -> None:
    api = client(f"{PAGES}, http://localhost:44175")
    assert preflight(api, "http://localhost:44175").headers["access-control-allow-origin"] == "http://localhost:44175"
    assert "access-control-allow-origin" not in preflight(api, PAGES + ".evil.example").headers


@pytest.mark.parametrize(
    "value",
    ["*", "https://*.pages.dev", "https://a.example/path", "http://public.example", "ftp://a.example", "not a url", "https://a.example?x=1"],
)
def test_unsafe_values_are_rejected_at_startup(value: str) -> None:
    with pytest.raises(ValueError, match="CORS"):
        parse_cors_origins(value)
    with pytest.raises(ValueError, match="CORS"):
        create_app(token_secret=TEST_SECRET, cors_origins=value)


def test_parse_accepts_https_and_loopback_http_and_normalizes() -> None:
    assert parse_cors_origins(None) == []
    assert parse_cors_origins("") == []
    assert parse_cors_origins(" https://A.example/ , http://localhost:3000,http://127.0.0.1:44175 ") == [
        "https://a.example",
        "http://localhost:3000",
        "http://127.0.0.1:44175",
    ]
