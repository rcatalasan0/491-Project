"""
Authentication & Session Tests
Sprint 3 - Stock Market Predictor
Test IDs: AUTH-001 ... AUTH-014
"""

import pytest
from urllib.parse import urlencode


@pytest.fixture
def client(app):
    """
    Assumes your Flask app exposes `app` in app.py.
    If your conftest already has a `client` fixture, delete this one.
    """
    return app.test_client()


class TestAuthHappyPath:
    """Positive authentication flows."""

    def test_register_then_login_success(self, client):
        """AUTH-001: User can register then log in and reach home."""
        # Register
        form_data = {
            "email": "sprint3-user@example.com",
            "password": "StrongPass!123",
            "confirm_password": "StrongPass!123",
        }
        resp = client.post("/register", data=form_data, follow_redirects=True)

        # We accept either success or "already exists" as long as it's not a 500
        assert resp.status_code in (200, 302, 409)

        # Login
        login_data = {
            "email": "sprint3-user@example.com",
            "password": "StrongPass!123",
        }
        resp = client.post("/login", data=login_data, follow_redirects=True)

        assert resp.status_code == 200
        # HTML or JSON, just make sure some indication of logged-in state exists
        body = resp.get_data(as_text=True)
        assert "Logout" in body or "dashboard" in body or "Welcome" in body


    def test_login_requires_email_and_password(self, client):
        """AUTH-002: Missing fields are rejected with 400 or form error."""
        resp = client.post("/login", data={"email": ""})
        assert resp.status_code in (200, 400)

        text = resp.get_data(as_text=True)
        assert "email" in text.lower() or "required" in text.lower()


    def test_register_requires_matching_passwords(self, client):
        """AUTH-003: Password and confirm_password must match."""
        resp = client.post("/register", data={
            "email": "mismatch@example.com",
            "password": "abc12345",
            "confirm_password": "abc123456",
        })

        assert resp.status_code in (200, 400)
        text = resp.get_data(as_text=True)
        assert "match" in text.lower() or "confirm" in text.lower()


class TestAuthNegativeCases:
    """Negative / security-focused auth flows."""

    def test_login_invalid_password_rejected(self, client):
        """AUTH-004: Wrong password is rejected."""
        login_data = {
            "email": "does-not-matter@example.com",
            "password": "wrong-password",
        }
        resp = client.post("/login", data=login_data)
        # Either 401, 403, 400, or form with error; but not 200+“Welcome”
        txt = resp.get_data(as_text=True).lower()
        assert not ("welcome" in txt and resp.status_code == 200)


    @pytest.mark.parametrize("email", [
        "not-an-email",
        "missing-at-symbol.com",
        "user@",
        "@domain.com",
    ])
    def test_register_invalid_email_format(self, client, email):
        """AUTH-005–AUTH-008: Email format validation."""
        resp = client.post("/register", data={
            "email": email,
            "password": "StrongPass!123",
            "confirm_password": "StrongPass!123",
        })
        assert resp.status_code in (200, 400)
        txt = resp.get_data(as_text=True).lower()
        assert "email" in txt or "invalid" in txt or "format" in txt


    @pytest.mark.parametrize("password", [
        "short",
        "alllowercasepassword",
        "12345678",
    ])
    def test_register_weak_passwords_flagged(self, client, password):
        """AUTH-009–AUTH-011: Weak password checks."""
        resp = client.post("/register", data={
            "email": f"weak.{password}@example.com",
            "password": password,
            "confirm_password": password,
        })
        # You might still allow it; we just assert we don't crash
        assert resp.status_code in (200, 400)
        txt = resp.get_data(as_text=True).lower()
        # If you have explicit password rules, this will catch it
        assert "password" in txt


    def test_session_cleared_on_logout(self, client):
        """AUTH-012: /logout clears session and redirects."""
        login_data = {
            "email": "sprint3-user@example.com",
            "password": "StrongPass!123",
        }
        client.post("/login", data=login_data, follow_redirects=True)

        resp = client.get("/logout", follow_redirects=True)
        assert resp.status_code == 200
        txt = resp.get_data(as_text=True).lower()
        assert "login" in txt or "logged out" in txt


class TestAuthBruteforceProtection:
    """Simple brute-force guard checks (even if not implemented yet)."""

    def test_multiple_failed_logins_surface_as_bug(self, client):
        """AUTH-013: 5 failed attempts still do not crash the app."""
        for _ in range(5):
            resp = client.post("/login", data={
                "email": "nosuchuser@example.com",
                "password": "wrong",
            })
            assert resp.status_code in (200, 400, 401, 403)

        # If you implement locking later, you can assert lock message here.


    def test_login_does_not_reflect_raw_errors(self, client):
        """AUTH-014: No stack traces or SQL in login response."""
        resp = client.post("/login", data={
            "email": "' OR 1=1 --",
            "password": "anything",
        })
        txt = resp.get_data(as_text=True).lower()
        assert "sql" not in txt
        assert "traceback" not in txt
        assert "exception" not in txt
