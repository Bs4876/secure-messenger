import os
import time
from typing import Dict, Any
import bcrypt
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Read Secret Key from environment with fallback
SECRET_KEY: str = os.getenv("JWT_SECRET", "temporary_jwt_secret_development_only")
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

security = HTTPBearer()

def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against stored bcrypt hash."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

def create_token(username: str) -> str:
    """Generate a JWT token containing the username payload."""
    payload = {
        "sub": username,
        "exp": time.time() + (ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> str:
    """Decode token and return username. Raises JWTError on invalid/expired token."""
    payload: Dict[str, Any] = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    username: str | None = payload.get("sub")
    if not username:
        raise JWTError("Missing 'sub' field in token.")
    return username

def require_auth(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    Dependency to secure API routes.
    Returns 401 for bad token, conforming to strict HTTP semantics.
    """
    try:
        return decode_token(credentials.credentials)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired security token"
        )