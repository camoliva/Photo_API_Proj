# app/db.py 
"""
Database bootstrapper for the Photo Client Manager API.

This module:
- loads DATABASE_URL from .env
- creates a SQLAlchemy Engine and Session factoy
- exposes a FastAPI dependency `get_db()` that yields a session per request
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# loads environment variables from .env sitting at proj root.
load_dotenv()

# Expect a full SQLAlchemy URL string, eg:
# mysql+pymysql://user:password@localhost:3306/photo_db_v3
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # Fail fast so setup issues are obvious during development.
    raise RuntimeError("DATABASE_URL not set in .env")

# Creates the Engine. These options are safe defaults for MySQL.
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,   # ping before each checkout to avoid MySQL gone away
    pool_recycle=3600,    # recycle connections every hour
    echo=False,           # set to True only when you need SQL logging
)

# session factory used by FastAPI dependency
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# Declarative base for ORM models
Base = declarative_base()

def get_db():
    """
    FastAPI dependency that provides a scoped DB session.

    Usage:
        def route(dep: Session = Depends(get_db)): ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        # Always close so connections return to the pool.
        db.close()
