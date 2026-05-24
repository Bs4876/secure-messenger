# Secure Messenger (Stage 2)

A secured, real-time private messaging REST API and command-line interface (CLI) client featuring end-to-end encryption at rest and live message broadcasting.

## Features
- **Secure Authentication:** User registration and login verified via one-way password hashing (`bcrypt`). Sessions managed using signed JWT tokens.
- **Encryption at Rest:** All messages are encrypted prior to database storage using 256-bit AES in Galois/Counter Mode (GCM), ensuring both confidentiality and tamper-resistance.
- **Real-Time Delivery:** Instant message streaming via Server-Sent Events (SSE) through an in-memory asynchronous Pub/Sub Broadcaster.
- **Interactive CLI Client:** Terminal-based user interface supporting concurrent user interaction and live message streaming.

---

## Installation & Setup

### 1. Install Dependencies
Ensure you have Python 3.10+ installed. Install the required libraries:
```bash
pip install -r requirements.txt
```

### 2. Populate the Database (Seeding)
Initialize the SQLite database with test users (alice, bob, charlie, etc.) and seed data:

```bash
python seed.py
```

## How to Run

1. Start the Server
Run the FastAPI backend server using Uvicorn:

```bash
uvicorn server.main:app --reload
```

The server will start running on http://127.0.0.1:8000.

2. Run the CLI Clients
Open multiple terminal windows to test real-time interaction. In each terminal, start the CLI client package:

```bash
python -m client.client
```

### Login Credentials (from Seed):

User 1: alice (Password: testpass123)
User 2: bob (Password: testpass123)

### CLI Usage:

- Type `/inbox` to display historical messages.
- Send a message by typing `<username>: <message>` (e.g., `alice: Hello there!`).
- Type `/quit` to close the client connection.

## Running Tests
To execute the automated unit and integration tests (including the SSE streaming test suite), run:

```bash
pytest tests/ -v
```

---

### 🎨 איך התיקייה שלך תיראה עכשיו?
לאחר הניקוי ועדכון הקובץ, תיקיית השורש תהיה נקייה ומרשימה:

```text
SECURE-MESSENGER/
├── client/
├── docs/
├── server/
├── tests/
├── .gitignore
├── Dockerfile
├── requirements.txt
├── seed.py
└── README.md         <-- זה יהיה קובץ ה-Markdown היחיד בשורש!

```

הגשה במצב כזה מראה על רמת גימור (Polish) של מפתחת תוכנה מקצועית שיודעת לא רק לכתוב קוד, אלא גם לסדר את סביבת העבודה שלה בצורה נקייה.

