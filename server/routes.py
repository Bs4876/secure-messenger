from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
from sqlalchemy.orm import Session
import json
import asyncio

from server.database import get_db
from server.schemas import RegisterRequest, LoginRequest, MessageRequest, MessageResponse, TokenResponse
from server.services import AuthService, MessageService
from server.auth import require_auth, decode_token
from server.broadcaster import broadcaster

router = APIRouter()

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    service.register(body.username, body.password)
    return {"status": "success"}

@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    token = service.login(body.username, body.password)
    return TokenResponse(access_token=token, token_type="bearer")

# Changed to async def to support safe non-blocking await calls (Fix Q14)
@router.post("/messages", response_model=MessageResponse)
async def send_message(
    body: MessageRequest, 
    sender: str = Depends(require_auth), 
    db: Session = Depends(get_db)
):
    service = MessageService(db)
    return await service.send(sender, body.recipient, body.content)

@router.get("/messages", response_model=list[MessageResponse])
def get_history(sender: str = Depends(require_auth), db: Session = Depends(get_db)):
    service = MessageService(db)
    return service.get_history(sender)

@router.get("/stream")
async def sse_stream(
    token: str | None = Query(None), 
    auth_header: str | None = Depends(require_auth)
):
    """
    Real-time message push via Server-Sent Events (SSE).
    Supports token inside header (CLI clients) or token inside URL query parameter (Browser EventSource).
    """
    username = auth_header
    if not username and token:
        try:
            username = decode_token(token)
        except Exception:
            pass

    if not username:
         raise HTTPException(
             status_code=status.HTTP_401_UNAUTHORIZED,
             detail="Authentication credentials missing or invalid"
         )

    async def event_generator():
        queue = broadcaster.register()
        try:
            while True:
                # Non-blocking fetch from client queue
                message = await queue.get()
                
                # Deliver only if the client is the sender or the recipient
                if message["sender"] == username or message["recipient"] == username:
                    yield {
                        "event": "message", # Named SSE Event (Bonus 4)
                        "data": json.dumps(message)
                    }
        except asyncio.CancelledError:
            # Handle abrupt disconnection safely
            raise
        finally:
            # Clean up subscriber list immediately to prevent memory leaks (Fix Q10)
            broadcaster.unregister(queue)

    return EventSourceResponse(event_generator())