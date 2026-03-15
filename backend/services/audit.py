"""
Audit service for logging system activities.
Sensitive data (IP, user agent, etc.) is not collected or stored.
"""
from typing import Any, Optional

from db.repositories import audit_repo


def log_audit(
    action: str,
    *,
    user_id: Optional[int] = None,
    username: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    details: Optional[dict[str, Any]] = None,
    success: bool = True,
) -> None:
    """Log an audit event. Fire-and-forget; does not block the request."""
    try:
        audit_repo.create(
            action=action,
            user_id=user_id,
            username=username,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            success=success,
        )
    except Exception:
        pass  # Do not fail the request if audit logging fails
