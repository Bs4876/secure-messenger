import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import asyncio

from server.main import app
from server.database import get_db          # מייבאים רק את get_db מכאן
from server.broadcaster import broadcaster

# התיקון הקריטי: מייבאים את Base, User ו-Message ישירות מ-models!
# זה מבטיח ש-SQLAlchemy ישתמש ב-Registry הנכון שבו רשומות הטבלאות.
from server.models import Base, User, Message

# הגדרת SQLite בזיכרון עם StaticPool לשיתוף החיבור
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(autouse=True)
def setup_db():
    """יוצר את טבלאות בסיס הנתונים האמיתיות לפני כל טסט ומנקה בסיום."""
    # יוצר את הטבלאות הרשומות ב-Base של המודלים
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def override_get_db():
    """מזריק את חיבור ה-DB של הבדיקות במקום ה-DB האמיתי."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

# --- בדיקות פונקציונליות של השרת ---

def test_register_user():
    response = client.post("/register", json={"username": "alice", "password": "password123"})
    assert response.status_code == 201
    assert response.json() == {"status": "success"}

def test_login_user():
    client.post("/register", json={"username": "bob", "password": "password123"})
    response = client.post("/login", json={"username": "bob", "password": "password123"})
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_send_message():
    client.post("/register", json={"username": "sender_user", "password": "password123"})
    login_res = client.post("/login", json={"username": "sender_user", "password": "password123"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        "/messages", 
        json={"recipient": "recipient_user", "content": "Hello World!"},
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["sender"] == "sender_user"
    assert data["recipient"] == "recipient_user"
    assert data["content"] == "Hello World!"

def test_get_history():
    client.post("/register", json={"username": "user_a", "password": "password123"})
    login_res = client.post("/login", json={"username": "user_a", "password": "password123"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    client.post("/messages", json={"recipient": "user_b", "content": "Message 1"}, headers=headers)
    client.post("/messages", json={"recipient": "user_b", "content": "Message 2"}, headers=headers)

    response = client.get("/messages", headers=headers)
    assert response.status_code == 200
    history = response.json()
    assert len(history) == 2
    assert history[0]["content"] == "Message 1"
    assert history[1]["content"] == "Message 2"

# --- בדיקת ה-Broadcaster האסינכרונית ---

@pytest.mark.asyncio
async def test_sse_broadcaster_event_dispatch():
    """
    Verifies that SSE broadcasting delivers messages to registered client queues.
    """
    client_queue = broadcaster.register()
    
    test_msg = {
        "id": 100,
        "sender": "alice",
        "recipient": "bob",
        "content": "Secret real-time message!",
        "created_at": "2026-05-27T12:00:00"
    }

    try:
        await broadcaster.publish(test_msg)
        received = await asyncio.wait_for(client_queue.get(), timeout=1.0)
        
        assert received == test_msg
        assert received["sender"] == "alice"
        assert received["content"] == "Secret real-time message!"
        
    finally:
        broadcaster.unregister(client_queue)