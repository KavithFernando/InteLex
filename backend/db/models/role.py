"""
Role model (ORM) for auth. Maps to user_roles table.
"""
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.engine import Base


class Role(Base):
    __tablename__ = "user_roles"

    role_id: Mapped[int] = mapped_column(Integer(), primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)

    def __repr__(self) -> str:
        return f"<Role(role_id={self.role_id}, name={self.name!r})>"
