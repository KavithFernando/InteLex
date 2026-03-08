from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from api.auth_deps import get_current_user, get_current_user_optional
from api.limiter import limiter
from api.schemas.auth import (
    LoginRequest,
    PasswordChangeRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from db.models.user import User
from db.repositories import role_repo, user_repo
from services.audit import log_audit
from services.auth import (
    create_access_token,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer(auto_error=False)

DEFAULT_ROLE_NAME = "user"


@router.post("/register", response_model=TokenResponse)
def register(body: RegisterRequest) -> TokenResponse:
    if user_repo.get_by_username(body.username):
        log_audit("auth.register_failed", username=body.username, success=False, details={"reason": "username_taken"})
        raise HTTPException(status_code=400, detail="Username already taken.")
    role = role_repo.get_by_name(DEFAULT_ROLE_NAME)
    if not role:
        raise HTTPException(status_code=500, detail="Default role not found.")
    user = user_repo.create_user(body.username, hash_password(body.password), role.role_id)
    log_audit("auth.register", user_id=user.user_id, username=user.username, success=True)
    token = create_access_token(user.user_id, user.username)
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
def login(request: Request, body: LoginRequest) -> TokenResponse:
    user = user_repo.get_by_username(body.username)
    if not user or not verify_password(body.password, user.password_hash):
        log_audit("auth.login_failed", username=body.username, success=False)
        raise HTTPException(status_code=401, detail="Invalid username or password.")
    user_repo.update_last_login(user.user_id)
    log_audit("auth.login", user_id=user.user_id, username=user.username, success=True)
    token = create_access_token(user.user_id, user.username)
    return TokenResponse(access_token=token)


@router.post("/logout")
def logout(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    current_user: User | None = Depends(get_current_user_optional),
) -> dict:
    if current_user:
        log_audit("auth.logout", user_id=current_user.user_id, username=current_user.username, success=True)
    return {"message": "Logged out."}


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse(
        user_id=current_user.user_id,
        username=current_user.username,
        role=current_user.role.name,
        created_at=current_user.created_at,
        last_login=current_user.last_login,
    )


@router.post("/change-password")
def change_password(
    body: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
) -> dict:
    if not verify_password(body.current_password, current_user.password_hash):
        log_audit("auth.change_password_failed", user_id=current_user.user_id, username=current_user.username, success=False)
        raise HTTPException(status_code=400, detail="Current password is incorrect.")
    user_repo.update_password(current_user.user_id, hash_password(body.new_password))
    log_audit("auth.change_password", user_id=current_user.user_id, username=current_user.username, success=True)
    return {"message": "Password changed successfully."}
