"""
User repository (ORM): get by username, create user with role. Password hashing is done in auth layer.
"""
from typing import Optional

from db.engine import SessionLocal
from db.models import User


def get_by_username(username: str) -> Optional[User]:
    """Return the user with the given username, or None."""
    session = SessionLocal()
    try:
        return session.query(User).filter(User.username == username).first()
    finally:
        session.close()


def get_by_id(user_id: int) -> Optional[User]:
    """Return the user with the given id, or None."""
    session = SessionLocal()
    try:
        return session.query(User).filter(User.user_id == user_id).first()
    finally:
        session.close()


def create_user(username: str, password_hash: str, role_id: int) -> User:
    """Create a new user. Caller must ensure username is unique."""
    session = SessionLocal()
    try:
        user = User(username=username, password_hash=password_hash, role_id=role_id)
        session.add(user)
        session.commit()
        session.refresh(user)
        return user
    finally:
        session.close()
