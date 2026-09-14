from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hash_roundtrip() -> None:
    hashed = hash_password("Admin@123456")
    assert verify_password("Admin@123456", hashed)
    assert not verify_password("wrong", hashed)


def test_jwt_roundtrip() -> None:
    token, expires_in = create_access_token(subject="user-1", extra={"org_id": "org-1"})
    assert expires_in > 0
    payload = decode_access_token(token)
    assert payload["sub"] == "user-1"
    assert payload["org_id"] == "org-1"
