from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from api.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from db.repositories import role_repo, user_repo
from services.auth import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer(auto_error=False)

DEFAULT_ROLE_NAME = "user"


@router.post("/register", response_model=TokenResponse)
def register(body: RegisterRequest) -> TokenResponse:
    if user_repo.get_by_username(body.username):
        raise HTTPException(status_code=400, detail="Username already taken.")
    role = role_repo.get_by_name(DEFAULT_ROLE_NAME)
    if not role:
        raise HTTPException(status_code=500, detail="Default role not found.")
    user = user_repo.create_user(body.username, hash_password(body.password), role.role_id)
    token = create_access_token(user.user_id, user.username)
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest) -> TokenResponse:
    user = user_repo.get_by_username(body.username)
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password.")
    token = create_access_token(user.user_id, user.username)
    return TokenResponse(access_token=token)


@router.post("/logout")
def logout(credentials: HTTPAuthorizationCredentials | None = Depends(security)) -> dict:
    return {"message": "Logged out."}
