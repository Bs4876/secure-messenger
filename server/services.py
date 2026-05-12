"""
services.py — Business logic layer.

Services orchestrate repositories and utilities (auth, crypto).
They know WHAT to do but not HOW data is stored (that's the repository's job).

WHY THIS MATTERS:
  When Stage 2 adds SSE broadcasting, send_message() is the single place
  to add the broadcast call — routes.py stays untouched.
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from .models import Message
from .repositories import UserRepository, MessageRepository
from .auth import hash_password, verify_password, create_token
from .crypto import encrypt, decrypt
from .schemas import MessageResponse


class AuthService:
    def __init__(self, db: Session):
        self.users = UserRepository(db)

    def register(self, username: str, password: str) -> None:
        if self.users.get_by_username(username):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken")
        self.users.create(username, hash_password(password))

    def login(self, username: str, password: str) -> str:
        user = self.users.get_by_username(username)
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        return create_token(username)


class MessageService:
    def __init__(self, db: Session):
        self.messages = MessageRepository(db)

    def send(self, sender: str, recipient: str, content: str) -> MessageResponse:
        msg = self.messages.create(sender, recipient, encrypt(content))
        return MessageResponse(
            id=msg.id, sender=msg.sender, recipient=msg.recipient,
            content=content, created_at=msg.created_at,
        )

    def get_inbox(self, username: str) -> list[MessageResponse]:
        return [
            MessageResponse(
                id=m.id, sender=m.sender, recipient=m.recipient,
                content=decrypt(m.ciphertext), created_at=m.created_at,
            )
            for m in self.messages.get_for_user(username)
        ]
