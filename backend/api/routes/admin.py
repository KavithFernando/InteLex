from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends

from api.auth_deps import require_admin
from api.schemas.audit import AuditLogResponse
from api.schemas.auth import AdminUserResponse
from db.models.user import User
from db.repositories import audit_repo, user_repo
from services.audit import log_audit

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=list[AdminUserResponse])
def list_users(admin: User = Depends(require_admin)) -> list[AdminUserResponse]:
    """Return all registered users. Admin only."""
    users = user_repo.list_all()
    log_audit(
        "admin.list_users",
        user_id=admin.user_id,
        username=admin.username,
        success=True,
    )
    return [
        AdminUserResponse(
            user_id=u.user_id,
            username=u.username,
            role=u.role.name,
            created_at=u.created_at,
            last_login=u.last_login,
        )
        for u in users
    ]


@router.get("/audit-logs", response_model=list[AuditLogResponse])
def list_audit_logs(
    admin: User = Depends(require_admin),
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    since: Optional[datetime] = None,
    limit: int = 100,
) -> list[AuditLogResponse]:
    """Return audit logs with optional filters. Admin only."""
    logs = audit_repo.list_logs(user_id=user_id, action=action, since=since, limit=limit)
    return [AuditLogResponse(**r) for r in logs]
