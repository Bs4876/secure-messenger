# Secure Messenger

A production-grade, end-to-end secured real-time instant messaging system. This project features a robust FastAPI backend and an interactive terminal-based CLI client, implementing advanced cryptographic standards and asynchronous real-time event broadcasting.

---

## Key Features

### 🔒 Core Security (Stage 1)
- **Zero-Knowledge Password Hashing:** Passwords are never stored in plain text. They are hashed using `bcrypt` with a cryptographically secure, unique salt.
- **Stateless Authentication:** Secure session management using cryptographically signed JSON Web Tokens (JWT) via the `HS256` algorithm.
- **Military-Grade Encryption at Rest:** All chat messages are encrypted before saving to the SQLite database using **AES-256-GCM** (Galois/Counter Mode). This ensures both data confidentiality and tamper detection (integrity).
- **Cryptographic Nonce Isolation:** Every single message uses a unique, cryptographically random 12-byte Initialization Vector (Nonce/IV) to prevent pattern-analysis attacks.

### ⚡ Real-Time Infrastructure (Stage 2)
- **Server-Sent Events (SSE):** Uses unidirectional HTTP streaming via `GET /stream` to push messages instantly from the server to active clients, eliminating heavy polling.
- **Asynchronous Pub/Sub Broadcaster:** An in-memory asynchronous broadcaster managing thread-safe client queues (`asyncio.Queue`) for real-time delivery.
- **Strict Stream Isolation:** The server filters all broadcasted messages in real-time to guarantee that users only receive stream events belonging to them.

---

## Directory Structure

```text
SECURE-MESSENGER/
├── client/              # Client CLI package
│   ├── __init__.py      # Package initializer
│   ├── _impl.py         # CLI logic and interface
│   └── client.py        # Client entry point
├── server/              # FastAPI Backend
│   ├── auth.py          # JWT authentication dependencies
│   ├── broadcaster.py   # Asynchronous SSE broadcast manager
│   ├── crypto.py        # AES-GCM encryption & bcrypt hashing
│   ├── main.py          # App initialization and startup
│   ├── models.py        # SQLAlchemy Database models
│   ├── repositories.py  # Data access layer
│   ├── routes.py        # API endpoints (Auth, Messages, SSE)
│   ├── schemas.py       # Pydantic validation schemas
│   └── services.py      # Business logic layer
├── tests/               # Pytest suite
└── seed.py              # Database initialization and seeding script
```

---

## Installation & Setup

### 1. Install Dependencies
Make sure you have Python 3.10 or higher installed. Install all required packages:
```bash
pip install -r requirements.txt
```

### 2. Initialize and Seed the Database
Generate a clean SQLite database populated with default testing users (`alice`, `bob`, `charlie`, `dave`, `batsheva`):
```bash
python seed.py
```

---

## Running the Application

To experience real-time messaging, you must run the server and at least two clients simultaneously in separate terminal windows.

### Step 1: Start the Backend Server
Run the FastAPI backend using Uvicorn:
```bash
uvicorn server.main:app --reload
```
The server will boot up and listen on `http://127.0.0.1:8000`.

### Step 2: Launch CLI Clients
Open multiple terminals and run the client package inside each:
```bash
python -m client.client
```

### Credentials for Testing (from Seed)
* **User 1:** `alice` (Password: `testpass123`)
* **User 2:** `bob` (Password: `testpass123`)
* **User 3:** `charlie` (Password: `testpass123`)

---

## CLI Commands & Usage

Once logged in, you can interact with the secure chat using these commands:

* **View Inbox:** Type `/inbox` to fetch and decrypt all your past messages.
* **Send Message:** Type `<username>: <your_message>` (e.g., `alice: Hello!`) to send an encrypted message.
* **Exit:** Type `/quit` to safely disconnect and close the client.

---

## Running the Test Suite

To run the automated test suite (verifying authentication, database storage, encryption, and SSE stream connections), run:
```bash
pytest tests/ -v
```