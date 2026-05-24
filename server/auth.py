"""
auth.py — Password hashing and JWT token logic.

╔══════════════════════════════════════════════╗
║  YOUR TASK: implement the five functions.    ║
╚══════════════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CONCEPT 1 — WHY WE HASH PASSWORDS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Imagine every password in your database was stored as plain text.
  One database leak → every user's password is exposed, forever.

  bcrypt solves this by being a ONE-WAY function:
    hash("secret123") → "$2b$12$eImiTXuW..." (a fingerprint)
    There is no reverse. The original password is gone.

  When a user logs in, we don't un-hash. Instead we re-hash the
  typed password and compare the two fingerprints. If they match —
  the password was correct, without ever knowing the original.

  bcrypt is also INTENTIONALLY SLOW (has a "cost factor").
  Even if someone steals your DB, brute-forcing takes years.

  Use:
    import bcrypt
    hash  = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    match = bcrypt.checkpw(password.encode(), stored_hash.encode())

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CONCEPT 2 — WHY WE USE JWT TOKENS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  After a successful login, the server gives the client a JWT token.
  Think of it as a signed wristband at a concert:
    - It proves you paid (authenticated) without checking your ID again
    - It has an expiry date printed on it
    - The bouncer (server) can verify it's real by checking the signature
    - The server never needs to look up a database to validate it

  A JWT has three parts, separated by dots:
    header.payload.signature
    eyJhbGc...  .eyJzdWI...  .SflKxw...

  The payload contains the username and expiry time — readable but
  tamper-proof (changing anything breaks the signature).

  Use:
    from jose import jwt, JWTError
    token   = jwt.encode({"sub": username, "exp": expire}, SECRET_KEY, algorithm="HS256")
    payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CONCEPT 3 — FASTAPI DEPENDENCY INJECTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  require_auth() is a FastAPI "dependency". Instead of copy-pasting
  token validation into every route, you declare it once here and
  inject it into any route that needs it:

    @router.get("/messages")
    def get_messages(username: str = Depends(require_auth)):
        # username is already validated — if we got here, the token was valid
        ...

  FastAPI calls require_auth() automatically before your route runs.
  If the token is missing or invalid, it raises HTTP 401 and your
  route never executes.

  The HTTPBearer() helper extracts the token from the header:
    Authorization: Bearer eyJhbGc...
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status, Request


SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-to-a-long-random-string-in-production")
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_token(username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRE_HOURS)
    return jwt.encode({"sub": username, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None


def require_auth(request: Request) -> str:
  """
  FastAPI dependency that accepts a token from the Authorization header
  or as a `token` query parameter (useful for EventSource which can't
  set custom headers).

  Behavior matches tests:
    - Missing token -> HTTP 403
    - Invalid token -> HTTP 401
  """
  # Try Authorization header first (format: Bearer <token>)
  token = None
  auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
  if auth_header:
    parts = auth_header.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
      token = parts[1]

  # If no header token, try query parameter (useful for EventSource)
  if not token:
    token = request.query_params.get("token")

  if not token:
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authenticated")

  username = decode_token(token)
  if not username:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
  return username
