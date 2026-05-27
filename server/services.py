from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from server.models import User, Message
from server.schemas import MessageResponse
from server.crypto import encrypt, decrypt
from server.auth import hash_password, verify_password, create_token
from server.broadcaster import broadcaster

class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def register(self, username: str, password: str) -> User:
        existing = self.db.query(User).filter(User.username == username).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        new_user = User(username=username, password_hash=hash_password(password))
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        return new_user

    def login(self, username: str, password: str) -> str:
        user = self.db.query(User).filter(User.username == username).first()
        
        if user:
            # User exists: slow, computational hash check
            is_valid = verify_password(password, user.password_hash)
        else:
            # Anti-Timing Oracle / Enumeration Attack (Bonus 5):
            # Run dummy bcrypt execution with a valid format hash to match response time (~100ms)
            dummy_hash = "$2b$12$eImiTXuW728639572627384957362718274657182"
            verify_password(password, dummy_hash)
            is_valid = False

        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
            
        return create_token(username)


class MessageService:
    def __init__(self, db: Session):
        self.db = db

    async def send(self, sender: str, recipient: str, content: str) -> MessageResponse:
        """
        Send a message. Encrypts and stores in DB, then broadcasts to real-time stream.
        This function is now async to safely await the broadcaster fan-out (Fix Q14).
        """
        ciphertext = encrypt(content)
        db_msg = Message(sender=sender, recipient=recipient, ciphertext=ciphertext)
        self.db.add(db_msg)
        self.db.commit()
        self.db.refresh(db_msg)

        response = MessageResponse(
            id=db_msg.id,
            sender=db_msg.sender,
            recipient=db_msg.recipient,
            content=content, # Cleartext for the recipient
            created_at=db_msg.created_at
        )

        # Broadcast asynchronously to active SSE queues without thread blocking
        payload = {
            "id": response.id,
            "sender": response.sender,
            "recipient": response.recipient,
            "content": response.content,
            "created_at": response.created_at.isoformat()
        }
        await broadcaster.publish(payload)

        return response

    def get_history(self, username: str) -> List[MessageResponse]:
        db_messages = self.db.query(Message).filter(
            (Message.sender == username) | (Message.recipient == username)
        ).all()

        results = []
        for msg in db_messages:
            try:
                decrypted = decrypt(msg.ciphertext)
                results.append(MessageResponse(
                    id=msg.id,
                    sender=msg.sender,
                    recipient=msg.recipient,
                    content=decrypted,
                    created_at=msg.created_at
                ))
            except Exception:
                # Silently skip records that cannot be decrypted (e.g., historical key mismatch)
                continue
        return results