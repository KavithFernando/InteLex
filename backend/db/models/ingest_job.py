"""
IngestJob ORM model. Maps to ingest_jobs table.
"""
from datetime import datetime
from typing import Any, List, Optional

from sqlalchemy import BigInteger, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from db.engine import Base


class IngestJob(Base):
    __tablename__ = "ingest_jobs"

    id: Mapped[int] = mapped_column(BigInteger(), primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="queued")
    submitted_at: Mapped[datetime] = mapped_column(DateTime(6), nullable=False, server_default=func.now())
    filenames: Mapped[List[str]] = mapped_column(JSON, nullable=False)
    clauses: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    log: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    frames_created: Mapped[int] = mapped_column(Integer(), nullable=False, default=0)
    frames_skipped: Mapped[int] = mapped_column(Integer(), nullable=False, default=0)
    errors: Mapped[int] = mapped_column(Integer(), nullable=False, default=0)
    error: Mapped[Optional[str]] = mapped_column(Text(), nullable=True)

    def __repr__(self) -> str:
        return f"<IngestJob(job_id={self.job_id!r}, status={self.status!r})>"
