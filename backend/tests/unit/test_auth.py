import pytest
from app.auth.jwt import hash_password, verify_password, create_access_token, create_refresh_token, decode_token


class TestPasswordHashing:
    def test_hash_and_verify(self):
        password = "SecurePass123!"
        hashed = hash_password(password)
        assert hashed != password
        assert verify_password(password, hashed) is True
        assert verify_password("wrong", hashed) is False


class TestJWT:
    def test_create_access_token(self):
        token = create_access_token({"sub": "1"})
        assert token is not None
        payload = decode_token(token)
        assert payload["sub"] == "1"
        assert payload["type"] == "access"

    def test_create_refresh_token(self):
        token = create_refresh_token({"sub": "1"})
        assert token is not None
        payload = decode_token(token)
        assert payload["sub"] == "1"
        assert payload["type"] == "refresh"

    def test_expired_token(self):
        from datetime import timedelta
        token = create_access_token({"sub": "1"}, expires_delta=timedelta(seconds=-1))
        import time
        time.sleep(1)
        payload = decode_token(token)
        assert payload is None

    def test_invalid_token(self):
        payload = decode_token("invalid.token.here")
        assert payload is None
