from datetime import datetime
from typing import Any, Optional

from db.engine import SessionLocal
from db.models.audit_log import AuditLog


def create(
    action: str,
    user_id: Optional[int] = None,
    username: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    details: Optional[dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    success: bool = True,
) -> AuditLog:
    session = SessionLocal()
    try:
        log = AuditLog(
            action=action,
            user_id=user_id,
            username=username,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
        )
        session.add(log)
        session.commit()
        session.refresh(log)
        return log
    finally:
        session.close()


def list_logs(
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    since: Optional[datetime] = None,
    limit: int = 100,
) -> list[dict]:
    session = SessionLocal()
    try:
        q = session.query(AuditLog).order_by(AuditLog.created_at.desc())
        if user_id is not None:
            q = q.filter(AuditLog.user_id == user_id)
        if action is not None:
            q = q.filter(AuditLog.action == action)
        if since is not None:
            q = q.filter(AuditLog.created_at >= since)
        rows = q.limit(limit).all()
        return [
            {
                "id": r.id,
                "created_at": r.created_at,
                "user_id": r.user_id,
                "username": r.username,
                "action": r.action,
                "resource_type": r.resource_type,
                "resource_id": r.resource_id,
                "details": r.details,
                "ip_address": r.ip_address,
                "user_agent": r.user_agent,
                "success": r.success,
            }
            for r in rows
        ]
    finally:
        session.close()
