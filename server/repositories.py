"""
repositories.py — Data access layer.

Each repository owns ALL direct DB queries for one model.
Routes and services never touch db.query() directly.

WHY THIS MATTERS:
  If you swap SQLite for PostgreSQL, or SQLAlchemy for another ORM,
  you change only this file — nothing in routes.py or services.py moves.
"""

from sqlalchemy.orm import Session
from .models import User, Message


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_username(self, username: str) -> User | None:
        return self.db.query(User).filter(User.username == username).first()

    def create(self, username: str, password_hash: str) -> User:
        user = User(username=username, password_hash=password_hash)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user


class MessageRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, sender: str, recipient: str, ciphertext: str) -> Message:
        msg = Message(sender=sender, recipient=recipient, ciphertext=ciphertext)
        self.db.add(msg)
        self.db.commit()
        self.db.refresh(msg)
        return msg

    def get_for_user(self, username: str) -> list[Message]:
        return (
            self.db.query(Message)
            .filter((Message.sender == username) | (Message.recipient == username))
            .order_by(Message.created_at)
            .all()
        )
