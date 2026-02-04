"""
User repository (ORM): get by email, create user. Password hashing is done in auth layer.
"""
from typing import Optional

from db.engine import SessionLocal
from db.models import User


def get_by_email(email: str) -> Optional[User]:
    """Return the user with the given email, or None."""
    session = SessionLocal()
    try:
        return session.query(User).filter(User.email == email).first()
    finally:
        session.close()


def get_by_id(user_id: int) -> Optional[User]:
    """Return the user with the given id, or None."""
    session = SessionLocal()
    try:
        return session.query(User).filter(User.user_id == user_id).first()
    finally:
        session.close()


def create_user(email: str, password_hash: str) -> User:
    """Create a new user. Caller must ensure email is unique."""
    session = SessionLocal()
    try:
        user = User(email=email, password_hash=password_hash)
        session.add(user)
        session.commit()
        session.refresh(user)
        return user
    finally:
        session.close()
