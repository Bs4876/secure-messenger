"""
routes.py — All API route handlers.

╔══════════════════════════════════════════════╗
║  YOUR TASK: implement the four routes.       ║
╚══════════════════════════════════════════════╝

WHY A SEPARATE routes.py?
  In real projects, main.py only creates the app and wires things together.
  The actual logic lives in dedicated files — one per feature area.
  This keeps files small, focused, and easy to navigate.
  main.py imports this router and registers it with one line.

THE FOUR ROUTES YOU NEED TO IMPLEMENT:

  ┌─────────────────────────────────────────────────────────────────────┐
  │ POST /register                                                      │
  │   Receives: RegisterRequest (username, password)                    │
  │   1. Check if the username is already taken → return 400 if so     │
  │   2. Hash the password (NEVER store plain text)                     │
  │   3. Save the new User to the database                              │
  │   4. Return a success message                                       │
  └─────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────────┐
  │ POST /login                                                         │
  │   Receives: LoginRequest (username, password)                       │
  │   1. Find the user in the database → return 401 if not found       │
  │   2. Verify the password against the stored hash → 401 if wrong    │
  │   3. Create and return a JWT token                                  │
  └─────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────────┐
  │ POST /messages                          [requires valid JWT]        │
  │   Receives: SendMessageRequest (content, recipient)                 │
  │   1. Encrypt the content with encrypt()                             │
  │   2. Save a new Message row (sender=current user, recipient=...)    │
  │   3. Return the message as MessageResponse (with decrypted content) │
  └─────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────────┐
  │ GET /messages                           [requires valid JWT]        │
  │   1. Fetch all messages from the database                           │
  │   2. Decrypt each message's ciphertext before returning             │
  │   3. Return a list of MessageResponse objects                       │
  │                                                                     │
  │   THINK ABOUT: should a user see ALL messages, or only those        │
  │   where they are the sender or recipient?                           │
  └─────────────────────────────────────────────────────────────────────┘

USEFUL IMPORTS ALREADY PROVIDED BELOW.
USEFUL PATTERN — how to query the database:
  user = db.query(User).filter(User.username == "alice").first()
  messages = db.query(Message).order_by(Message.created_at).all()

USEFUL PATTERN — how to save a new row:
  new_user = User(username="alice", password_hash="$2b$...")
  db.add(new_user)
  db.commit()
  db.refresh(new_user)   ← fills in the auto-generated id and created_at
"""

import logging

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from .models import get_db
from .schemas import (
    RegisterRequest, LoginRequest, TokenResponse,
    SendMessageRequest, MessageResponse,
)
from .auth import require_auth
from .services import AuthService, MessageService
from .broadcaster import broadcaster

from sse_starlette.sse import EventSourceResponse
import asyncio
import json


log = logging.getLogger(__name__)
router = APIRouter()


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    AuthService(db).register(body.username, body.password)
    log.info("Registered user: %s", body.username[:50].replace("\n", "").replace("\r", ""))
    return {"message": "User registered successfully"}


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    token = AuthService(db).login(body.username, body.password)
    log.info("Login successful: %s", body.username[:50].replace("\n", "").replace("\r", ""))
    return TokenResponse(access_token=token)


@router.post("/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def send_message(
    body: SendMessageRequest,
    db: Session = Depends(get_db),
    username: str = Depends(require_auth),
):
    log.info("Message sent from %s to %s", username[:20], body.recipient[:20])
    return MessageService(db).send(username, body.recipient, body.content)


@router.get("/messages", response_model=list[MessageResponse])
def get_messages(
    db: Session = Depends(get_db),
    username: str = Depends(require_auth),
):
    return MessageService(db).get_inbox(username)


@router.get("/stream")
async def stream_messages(username: str = Depends(require_auth)):
  """Server-Sent Events endpoint. Streams messages where the user is
  the sender or recipient. Each event is a JSON payload with the
  message fields. This is an in-memory, single-process implementation
  suitable for Stage 2 development.
  """
  q = broadcaster.register()

  async def event_generator():
    try:
      while True:
        data = await q.get()
        # Only send relevant messages to the connected user
        try:
          if data.get("recipient") == username or data.get("sender") == username:
            # ensure the data is a JSON string (double-quoted) for the SSE client
            json_data = json.dumps(data)
            yield {"event": "message", "data": json_data}
        except Exception:
          # Ignore malformed events
          continue
    finally:
      broadcaster.unregister(q)

  return EventSourceResponse(event_generator())
