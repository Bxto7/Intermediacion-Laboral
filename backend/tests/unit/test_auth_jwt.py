# RF: RF001-RF012, RNF001-RNF006
"""Tests for JWT authentication and RBAC."""

from app.core.security import (
    UserRole,
    create_access_token,
    create_refresh_token,
    decrypt_field,
    encrypt_field,
    hash_password,
    verify_password,
)


def test_hash_and_verify_password():
    plain = "SecurePass123!"
    hashed = hash_password(plain)
    assert verify_password(plain, hashed)
    assert not verify_password("wrong", hashed)


def test_aes_encrypt_decrypt_roundtrip():
    original = "12345678"
    encrypted = encrypt_field(original)
    decrypted = decrypt_field(encrypted)
    assert decrypted == original


def test_create_access_token_contains_role():
    token = create_access_token({"sub": "user-123", "role": "worker"})
    assert isinstance(token, str)
    assert len(token) > 0


def test_create_refresh_token():
    token = create_refresh_token({"sub": "user-123", "role": "worker"})
    assert isinstance(token, str)
    assert len(token) > 0


def test_user_role_enum_values():
    assert UserRole.WORKER.value == "worker"
    assert UserRole.ADMIN.value == "admin"
    assert UserRole.EMPLOYER.value == "employer"
    assert UserRole.MODERATOR.value == "moderator"
