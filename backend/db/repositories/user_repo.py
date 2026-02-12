from typing import Optional

from db.engine import SessionLocal
from db.models import User


def get_by_username(username: str) -> Optional[User]:
    session = SessionLocal()
    try:
        return session.query(User).filter(User.username == username).first()
    finally:
        session.close()


def get_by_id(user_id: int) -> Optional[User]:
    session = SessionLocal()
    try:
        return session.query(User).filter(User.user_id == user_id).first()
    finally:
        session.close()


def create_user(username: str, password_hash: str, role_id: int) -> User:
    session = SessionLocal()
    try:
        user = User(username=username, password_hash=password_hash, role_id=role_id)
        session.add(user)
        session.commit()
        session.refresh(user)
        return user
    finally:
        session.close()
