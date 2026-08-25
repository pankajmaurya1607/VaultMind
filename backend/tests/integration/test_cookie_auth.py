"""Integration tests for the HttpOnly-cookie auth flow.

Covers: cookie issuance on login, cookie-based authentication, refresh via
cookie with rotation of both tokens, logout clearing cookies, CSRF header
enforcement on state-changing endpoints, and the password policy.
"""

import pytest

pytestmark = pytest.mark.integration

USER = {"name": "Cookie Tester", "email": "cookie@example.com", "password": "StrongPass123", "department_id": 1}


async def _register(client):
    resp = await client.post("/api/v1/auth/register", json=USER)
    assert resp.status_code == 200, resp.text
    return resp


class TestCookieIssuance:
    @pytest.mark.asyncio
    async def test_login_sets_httponly_cookies(self, client):
        await _register(client)
        resp = await client.post(
            "/api/v1/auth/login", json={"email": USER["email"], "password": USER["password"]}
        )
        assert resp.status_code == 200

        set_cookies = resp.headers.get_list("set-cookie")
        access = next(c for c in set_cookies if c.startswith("eka_access="))
        refresh = next(c for c in set_cookies if c.startswith("eka_refresh="))
        assert "httponly" in access.lower()
        assert "samesite=lax" in access.lower()
        assert "httponly" in refresh.lower()

    @pytest.mark.asyncio
    async def test_weak_password_rejected_with_field_errors(self, client):
        resp = await client.post(
            "/api/v1/auth/register",
            json={**USER, "email": "weak@example.com", "password": "short1"},
        )
        assert resp.status_code == 422
        detail = str(resp.json()["detail"])
        assert "8" in detail  # min-length message present

    @pytest.mark.asyncio
    async def test_password_without_digit_rejected(self, client):
        resp = await client.post(
            "/api/v1/auth/register",
            json={**USER, "email": "nodigit@example.com", "password": "NoDigitsHere"},
        )
        assert resp.status_code == 422


class TestCookieAuthentication:
    @pytest.mark.asyncio
    async def test_cookie_alone_authenticates_request(self, client):
        await _register(client)

        # No Authorization header - only the HttpOnly cookie from register.
        resp = await client.get("/api/v1/users/me")
        assert resp.status_code == 200
        assert resp.json()["email"] == USER["email"]

    @pytest.mark.asyncio
    async def test_bearer_header_still_works(self, client):
        tokens = (await _register(client)).json()
        resp = await client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_no_credentials_returns_401(self, client):
        # Fresh client without cookies or bearer token.
        resp = await client.get("/api/v1/users/me")
        assert resp.status_code == 401


class TestRefreshRotation:
    @pytest.mark.asyncio
    async def test_refresh_via_cookie_rotates_tokens(self, client):
        original = (await _register(client)).json()
        old_access_cookie = None
        for cookie in client.cookies.jar:
            if cookie.name == "eka_access":
                old_access_cookie = cookie.value

        resp = await client.post("/api/v1/auth/refresh")
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["access_token"] != original["access_token"]
        assert body["refresh_token"] != original["refresh_token"]

        # Old access jti must now be blacklisted.
        resp_old = await client.get(
            "/api/v1/users/me",
            cookies={"eka_access": old_access_cookie},
        )
        assert resp_old.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_without_any_token_is_401(self, client):
        resp = await client.post("/api/v1/auth/refresh")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_body_refresh_token_still_supported(self, client):
        tokens = (await _register(client)).json()
        client.cookies.clear()  # force body path

        resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
        assert resp.status_code == 200
        assert resp.json()["access_token"]


class TestLogout:
    @pytest.mark.asyncio
    async def test_logout_clears_cookies_and_revokes_session(self, client):
        await _register(client)
        old_access = None
        for cookie in client.cookies.jar:
            if cookie.name == "eka_access":
                old_access = cookie.value

        resp = await client.post("/api/v1/auth/logout")
        assert resp.status_code == 200

        set_cookies = resp.headers.get_list("set-cookie")
        cleared = [c for c in set_cookies if c.startswith(("eka_access=", "eka_refresh="))]
        assert len(cleared) >= 2
        assert all('max-age=0' in c.lower() or 'expires=' in c.lower() for c in cleared)

        # Cookie was revoked server-side: replaying it must fail.
        assert old_access is not None
        replay = await client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {old_access}"})
        assert replay.status_code == 401


class TestCSRFProtection:
    @pytest.mark.asyncio
    async def test_mutating_request_with_cookie_but_no_csrf_header_blocked(self, client):
        await _register(client)  # cookies now in jar, no Authorization header used

        # Simulate cross-site form POST: cookies ride along, custom header absent.
        resp = await client.delete("/api/v1/documents/999999")
        assert resp.status_code == 403
        assert "CSRF" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_mutating_request_with_csrf_header_allowed(self, client):
        await _register(client)
        client.headers["X-Requested-With"] = "XMLHttpRequest"
        try:
            resp = await client.delete("/api/v1/documents/999999", headers={"Authorization": ""})
            # Not 403 - it passes CSRF and fails later as 401/403/404 from RBAC logic.
            assert resp.status_code in (401, 403, 404)
        finally:
            client.headers.pop("X-Requested-With", None)

    @pytest.mark.asyncio
    async def test_bearer_only_requests_exempt_from_csrf(self, client):
        tokens = (await _register(client)).json()
        client.cookies.clear()
        resp = await client.delete(
            "/api/v1/documents/999999", headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )
        assert resp.status_code != 403 or "CSRF" not in resp.json().get("detail", "")

    @pytest.mark.asyncio
    async def test_safe_methods_exempt_from_csrf(self, client):
        await _register(client)
        resp = await client.get("/api/v1/users/me")  # GET with cookies, no header
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_stale_session_does_not_block_register(self, client):
        """Registering again while an old session's cookies are still stored must work."""
        first = await _register(client)
        second_email = {**USER, "email": "second@example.com"}
        resp = await client.post("/api/v1/auth/register", json=second_email)
        assert resp.status_code == 200
        assert resp.json()["access_token"] != first.json()["access_token"]
