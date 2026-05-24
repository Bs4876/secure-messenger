"""Seed the messenger.db with several test users for manual testing.

This script uses the project's repositories and hashing helper to create
users that the server understands. Run it from the repository root:

    python seed.py

It will create users: alice, bob, charlie, dave, batsheva — all with
password 'testpass123' (for convenience in local testing).
"""

from server.models import engine, create_tables, SessionLocal
from server.repositories import UserRepository
from server.auth import hash_password


USERS = [
    ("alice", "testpass123"),
    ("bob", "testpass123"),
    ("charlie", "testpass123"),
    ("dave", "testpass123"),
    ("batsheva", "testpass123"),
]


def main():
    create_tables()
    db = SessionLocal()
    repo = UserRepository(db)
    for username, password in USERS:
        existing = repo.get_by_username(username)
        if existing:
            print(f"User exists, skipping: {username}")
            continue
        repo.create(username, hash_password(password))
        print(f"Created user: {username} (password: {password})")
    db.close()


if __name__ == "__main__":
    main()
