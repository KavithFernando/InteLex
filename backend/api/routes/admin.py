from fastapi import APIRouter, Depends

from api.auth_deps import require_admin
from api.schemas.auth import AdminUserResponse
from db.models.user import User
from db.repositories import user_repo

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=list[AdminUserResponse])
def list_users(admin: User = Depends(require_admin)) -> list[AdminUserResponse]:
    """Return all registered users. Admin only."""
    users = user_repo.list_all()
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
