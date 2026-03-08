"""
Audit service for logging system activities.
"""
from datetime import datetime
from typing import Any, Optional

from fastapi import Request

from db.repositories import audit_repo


def _get_client_ip(request: Optional[Request]) -> Optional[str]:
    if request is None:
        return None
    if request.client:
        return request.client.host
    return request.headers.get("x-forwarded-for", "").split(",")[0].strip() or None


def _get_user_agent(request: Optional[Request]) -> Optional[str]:
    if request is None:
        return None
    return request.headers.get("user-agent") or None


def log_audit(
    action: str,
    *,
    user_id: Optional[int] = None,
    username: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    details: Optional[dict[str, Any]] = None,
    success: bool = True,
    request: Optional[Request] = None,
) -> None:
    """Log an audit event. Fire-and-forget; does not block the request."""
    ip_address = _get_client_ip(request)
    user_agent = _get_user_agent(request)
    try:
        audit_repo.create(
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
    except Exception:
        pass  # Do not fail the request if audit logging fails
