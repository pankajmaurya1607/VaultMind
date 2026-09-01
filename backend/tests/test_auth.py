import pytest
from datetime import timedelta

from app.auth.jwt import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.schemas.auth import validate_password_strength


def test_password_hashing():
    raw_password = "SecurePassword123"
    hashed = hash_password(raw_password)

    assert hashed != raw_password
    assert verify_password(raw_password, hashed) is True
    assert verify_password("WrongPassword123", hashed) is False


def test_password_strength_validation():
    # Valid password
    assert validate_password_strength("ValidPass123") == "ValidPass123"

    # Too short
    with pytest.raises(ValueError, match="at least 8 characters"):
        validate_password_strength("Short1")

    # No letters
    with pytest.raises(ValueError, match="at least one letter"):
        validate_password_strength("12345678")

    # No digits
    with pytest.raises(ValueError, match="at least one digit"):
        validate_password_strength("AllLettersPass")


def test_jwt_access_token_creation_and_decoding():
    data = {"sub": "42", "email": "user@example.com", "role": "Employee"}
    token = create_access_token(data)

    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == "42"
    assert payload["email"] == "user@example.com"
    assert payload["role"] == "Employee"
    assert payload["type"] == "access"
    assert "jti" in payload
    assert "exp" in payload


def test_jwt_refresh_token_creation_and_decoding():
    data = {"sub": "42"}
    token = create_refresh_token(data)

    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == "42"
    assert payload["type"] == "refresh"


def test_invalid_token_decoding():
    invalid_token = "invalid.token.string"
    payload = decode_token(invalid_token)
    assert payload is None


def test_expired_token():
    # Create token that expired 10 minutes ago
    data = {"sub": "42"}
    token = create_access_token(data, expires_delta=timedelta(minutes=-10))

    payload = decode_token(token)
    assert payload is None
