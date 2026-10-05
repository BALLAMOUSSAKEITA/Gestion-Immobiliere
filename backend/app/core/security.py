import base64
import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import bcrypt
import jwt

from app.core.config import get_settings

settings = get_settings()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def hash_password(password: str) -> str:
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")


def _recoverable_password_key() -> bytes:
    return hashlib.sha256(f"pwd-view:{settings.secret_key}".encode()).digest()


def encrypt_recoverable_password(plain_password: str) -> str:
    key = _recoverable_password_key()
    data = plain_password.encode("utf-8")
    xored = bytes(byte ^ key[index % len(key)] for index, byte in enumerate(data))
    digest = hmac.new(key, xored, hashlib.sha256).digest()[:16]
    return base64.urlsafe_b64encode(digest + xored).decode("ascii")


def decrypt_recoverable_password(token: str | None) -> str | None:
    if not token:
        return None
    try:
        raw = base64.urlsafe_b64decode(token.encode("ascii"))
        key = _recoverable_password_key()
        digest, xored = raw[:16], raw[16:]
        expected = hmac.new(key, xored, hashlib.sha256).digest()[:16]
        if not hmac.compare_digest(digest, expected):
            return None
        return bytes(byte ^ key[index % len(key)] for index, byte in enumerate(xored)).decode(
            "utf-8"
        )
    except (ValueError, UnicodeDecodeError):
        return None


def assign_password(user: Any, password: str) -> None:
    user.password_hash = hash_password(password)
    user.password_secret = encrypt_recoverable_password(password)


def remember_plain_password(user: Any, password: str) -> None:
    user.password_secret = encrypt_recoverable_password(password)


def create_access_token(user_id: UUID) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": str(user_id),
        "type": "access",
        "exp": expire,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def get_refresh_token_expiry() -> datetime:
    return datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
