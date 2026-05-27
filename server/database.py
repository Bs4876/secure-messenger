"""
database.py — Modern SQLAlchemy 2.0 setup for SQLite (Fix Q4, Q20).
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./messenger.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# שימוש בייבוא המודרני של SQLAlchemy 2.0 (מונע את ה-MovedIn20Warning)
Base = declarative_base()

def get_db():
    """Dependency generator to yield a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initializes the database schema."""
    Base.metadata.create_all(bind=engine)