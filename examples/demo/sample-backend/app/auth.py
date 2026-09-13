"""JWT auth: password hashing (stdlib pbkdf2) + token issue/verify + auth dependency."""
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .db import get_conn
from .schemas import User

JWT_SECRET = os.environ.get("SAMPLE_JWT_SECRET", "milestone-dev-secret-not-for-production-use")
JWT_ALGORITHM = "HS256"
JWT_EXP_HOURS = 24

PBKDF2_ITERATIONS = 260_000

security = HTTPBearer(auto_error=False)


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERATIONS)
    return f"{salt.hex()}${dk.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        salt_hex, dk_hex = password_hash.split("$", 1)
    except ValueError:
        return False
    salt = bytes.fromhex(salt_hex)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERATIONS)
    return hmac.compare_digest(dk.hex(), dk_hex)


def create_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {"sub": str(user_id), "iat": now, "exp": now + timedelta(hours=JWT_EXP_HOURS)}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(security),
) -> User:
    if creds is None:
        raise _unauthorized()
    try:
        payload = jwt.decode(creds.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = int(payload["sub"])
    except Exception:
        raise _unauthorized()
    with get_conn() as c:
        row = c.execute("SELECT id, email, name, created_at FROM users WHERE id = ?", (user_id,)).fetchone()
    if not row:
        raise _unauthorized()
    return User(**dict(row))
