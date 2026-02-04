"""
Role repository (ORM): get by name. Used when creating users (assign default role).
"""
from typing import Optional

from db.engine import SessionLocal
from db.models import Role


def get_by_name(name: str) -> Optional[Role]:
    """Return the role with the given name, or None."""
    session = SessionLocal()
    try:
        return session.query(Role).filter(Role.name == name).first()
    finally:
        session.close()
