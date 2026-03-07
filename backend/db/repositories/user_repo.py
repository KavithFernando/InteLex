from datetime import datetime, timezone
from typing import List, Optional

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


def list_all() -> List[User]:
    session = SessionLocal()
    try:
        return session.query(User).order_by(User.created_at.desc()).all()
    finally:
        session.close()


def update_password(user_id: int, new_password_hash: str) -> None:
    session = SessionLocal()
    try:
        session.query(User).filter(User.user_id == user_id).update(
            {"password_hash": new_password_hash}
        )
        session.commit()
    finally:
        session.close()


def update_last_login(user_id: int) -> None:
    session = SessionLocal()
    try:
        session.query(User).filter(User.user_id == user_id).update(
            {"last_login": datetime.now(timezone.utc)}
        )
        session.commit()
    finally:
        session.close()
