import pytest
from auth import hash_password, verify_password, create_token, decode_token


def test_password_round_trip():
    hashed = hash_password("secret")
    assert verify_password("secret", hashed) is True
    assert verify_password("wrong", hashed) is False


def test_token_round_trip():
    token = create_token(user_id=42, is_admin=True)
    payload = decode_token(token)
    assert payload["sub"] == "42"
    assert payload["is_admin"] is True


def test_invalid_token_raises():
    with pytest.raises(Exception):
        decode_token("not.a.token")
