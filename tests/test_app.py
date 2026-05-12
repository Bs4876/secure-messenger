"""
test_app.py — Integration tests for the Secure Messenger Stage 1 API.

Covers all 9 acceptance checks from STAGE_1.md:
  1.  POST /register          → 201 Created
  2.  POST /register (again)  → 400 Bad Request (duplicate username)
  3.  POST /login             → 200 OK + JWT token
  4.  GET  /messages (no token)   → 403 Forbidden
  5.  GET  /messages (fake token) → 401 Unauthorized
  6.  POST /messages (authenticated) → 201 Created, content decrypted
  7.  GET  /messages (authenticated) → 200 OK, plain-text content
  8.  DB ciphertext is not plain text
  9.  Two users only see their own messages
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import server.models as _models
from server.main import app
from server.models import Base, get_db, Message


# ---------------------------------------------------------------------------
# Shared in-memory SQLite — one connection kept alive for the whole session
# so all threads see the same data.
# ---------------------------------------------------------------------------
TEST_DATABASE_URL = "sqlite:///./test_messenger.db"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

# Patch the module-level engine so the app uses our test DB
_models.engine = engine
_models.SessionLocal = TestingSessionLocal


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def create_tables():
    """Create all tables once for the entire test session."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def reset_db():
    """Truncate all rows before every test for full isolation."""
    yield
    db = TestingSessionLocal()
    for table in reversed(Base.metadata.sorted_tables):
        db.execute(table.delete())
    db.commit()
    db.close()


@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=True)


# ---------------------------------------------------------------------------
# Test credentials — these are dummy values used only in tests
# ---------------------------------------------------------------------------
TEST_USER = "alice"
TEST_PASSWORD = "test-only-password-not-real"  # noqa: S105


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def register_user(client, username=TEST_USER, password=TEST_PASSWORD):
    return client.post("/register", json={"username": username, "password": password})


def login_user(client, username=TEST_USER, password=TEST_PASSWORD):
    return client.post("/login", json={"username": username, "password": password})


def get_auth_headers(client, username=TEST_USER, password=TEST_PASSWORD):
    token = login_user(client, username, password).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Test 1 — Successful registration returns 201
# ---------------------------------------------------------------------------
def test_register_success(client):
    response = register_user(client)
    assert response.status_code == 201


# ---------------------------------------------------------------------------
# Test 2 — Duplicate username returns 400
# ---------------------------------------------------------------------------
def test_register_duplicate_username(client):
    register_user(client)
    response = register_user(client)
    assert response.status_code == 400
    assert "taken" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Test 3 — Valid login returns 200 and a JWT token
# ---------------------------------------------------------------------------
def test_login_success(client):
    register_user(client)
    response = login_user(client)
    assert response.status_code == 200
    response_body = response.json()
    assert "access_token" in response_body
    assert response_body["token_type"] == "bearer"
    assert len(response_body["access_token"]) > 20


# ---------------------------------------------------------------------------
# Test 4 — GET /messages with no token returns 403
# ---------------------------------------------------------------------------
def test_get_messages_no_token(client):
    response = client.get("/messages")
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# Test 5 — GET /messages with a fake token returns 401
# ---------------------------------------------------------------------------
def test_get_messages_fake_token(client):
    response = client.get("/messages", headers={"Authorization": "Bearer this.is.fake"})
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Test 6 — POST /messages returns 201 with decrypted content in response
# ---------------------------------------------------------------------------
def test_send_message_authenticated(client):
    register_user(client, "alice")
    register_user(client, "bob")
    headers = get_auth_headers(client, "alice")

    response = client.post("/messages", json={"content": "hello bob", "recipient": "bob"}, headers=headers)
    assert response.status_code == 201
    response_body = response.json()
    assert response_body["content"] == "hello bob"
    assert response_body["sender"] == "alice"
    assert response_body["recipient"] == "bob"


# ---------------------------------------------------------------------------
# Test 7 — GET /messages returns 200 with readable plain-text content
# ---------------------------------------------------------------------------
def test_get_messages_returns_plaintext(client):
    register_user(client, "alice")
    register_user(client, "bob")
    headers = get_auth_headers(client, "alice")

    client.post("/messages", json={"content": "hello bob", "recipient": "bob"}, headers=headers)

    response = client.get("/messages", headers=headers)
    assert response.status_code == 200
    messages = response.json()
    assert len(messages) == 1
    assert messages[0]["content"] == "hello bob"


# ---------------------------------------------------------------------------
# Test 8 — Ciphertext stored in DB is not the plain-text message
# ---------------------------------------------------------------------------
def test_ciphertext_is_not_plaintext(client):
    register_user(client, "alice")
    register_user(client, "bob")
    headers = get_auth_headers(client, "alice")

    client.post("/messages", json={"content": "hello bob", "recipient": "bob"}, headers=headers)

    with TestingSessionLocal() as db:
        row = db.query(Message).first()

    assert row is not None
    assert row.ciphertext != "hello bob"
    assert len(row.ciphertext) > 10


# ---------------------------------------------------------------------------
# Test 9 — Users only see messages they sent or received
# ---------------------------------------------------------------------------
def test_message_visibility_isolation(client):
    register_user(client, "alice")
    register_user(client, "bob")
    register_user(client, "charlie")

    alice_headers = get_auth_headers(client, "alice")
    charlie_headers = get_auth_headers(client, "charlie")

    # Alice sends to Bob — Charlie should NOT see this
    client.post("/messages", json={"content": "private to bob", "recipient": "bob"}, headers=alice_headers)

    response = client.get("/messages", headers=charlie_headers)
    assert response.status_code == 200
    assert response.json() == []
