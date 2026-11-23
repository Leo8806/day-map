import os
from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from models import User


# --------------------------------------------------
# Authentication Configuration
# --------------------------------------------------

password_hash = PasswordHash.recommended()

SECRET_KEY = os.environ.get("DAYMAP_SECRET_KEY")
ALGORITHM = "HS256"

security = HTTPBearer()


# --------------------------------------------------
# Password Hashing and Verification
# --------------------------------------------------

def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return password_hash.verify(password, hashed)


# --------------------------------------------------
# JWT Access Token Generation
# --------------------------------------------------

def create_access_token(user_id: int) -> str:
    if not SECRET_KEY:
        raise RuntimeError(
            "DAYMAP_SECRET_KEY is not configured"
        )

    expiration = datetime.now(timezone.utc) + timedelta(hours=24)

    payload = {
        "sub": str(user_id),
        "exp": expiration
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


# --------------------------------------------------
# Authenticated User Dependency
# --------------------------------------------------

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    if not SECRET_KEY:
        raise RuntimeError(
            "DAYMAP_SECRET_KEY is not configured"
        )

    try:
        payload = jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = int(payload["sub"])

    except (jwt.PyJWTError, ValueError, KeyError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user = db.scalar(
        select(User).where(User.id == user_id)
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    return user


# --------------------------------------------------
# Administrator Authorization Dependency
# --------------------------------------------------

def get_current_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required"
        )

    return current_user
