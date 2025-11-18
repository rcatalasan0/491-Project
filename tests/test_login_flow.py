import pytest


class TestLoginAndRegistrationFlow:
    """
    Sprint 3: end-to-end authentication flow tests.

    Covers:
      - basic happy path for register + login
      - invalid password and invalid email cases
    """

    def test_register_then_login_success(self, client):
        # Register
        resp = client.post(
            "/register",
            data={
                "email": "student@example.com",
                "password": "StrongPass123!",
            },
            follow_redirects=True,
        )
        assert resp.status_code == 200

        # Login with same credentials
        resp2 = client.post(
            "/login",
            data={
                "email": "student@example.com",
                "password": "StrongPass123!",
            },
            follow_redirects=True,
        )
        assert resp2.status_code == 200
        assert b"Welcome" in resp2.data or b"Home" in resp2.data

    def test_register_rejects_invalid_email(self, client):
        resp = client.post(
            "/register",
            data={"email": "bad-email", "password": "Pass123!"},
            follow_redirects=True,
        )
        # Should not crash or redirect to home
        assert resp.status_code == 400 or b"invalid" in resp.data.lower()

    def test_login_fails_wrong_password(self, client):
        # First create a valid user
        client.post(
            "/register",
            data={"email": "wrongpass@example.com", "password": "Correct123!"},
            follow_redirects=True,
        )

        # Then attempt login with wrong password
        resp = client.post(
            "/login",
            data={"email": "wrongpass@example.com", "password": "Nope123!"},
            follow_redirects=True,
        )

        assert resp.status_code in (400, 401)
        assert b"invalid" in resp.data.lower() or b"incorrect" in resp.data.lower()
