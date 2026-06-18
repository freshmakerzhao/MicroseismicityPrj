from fastapi import APIRouter, Depends, Header

from app.schemas.auth import LoginPayload, RegisterPayload, UserUpdatePayload
from app.services import auth_service

router = APIRouter()


def current_token(authorization: str = Header(default="")) -> str:
    prefix = "Bearer "
    if not authorization.startswith(prefix):
        return ""
    return authorization[len(prefix):].strip()


def current_user(token: str = Depends(current_token)) -> dict:
    return auth_service.get_user_by_token(token)


def admin_user(user: dict = Depends(current_user)) -> dict:
    auth_service.require_admin(user)
    return user


@router.post("/auth/login")
def login(payload: LoginPayload) -> dict:
    user = auth_service.authenticate(payload.username, payload.password)
    token = auth_service.create_session(user)
    return {"code": 200, "token": token, "user": auth_service._public_user(user)}


@router.post("/auth/register")
def register(payload: RegisterPayload) -> dict:
    user = auth_service.register_user(payload.username, payload.password, payload.display_name or "")
    return {"code": 200, "user": user}


@router.get("/auth/me")
def me(user: dict = Depends(current_user)) -> dict:
    return {"code": 200, "user": auth_service._public_user(user)}


@router.post("/auth/logout")
def logout(token: str = Depends(current_token)) -> dict:
    auth_service.remove_session(token)
    return {"code": 200, "msg": "logged out"}


@router.get("/users")
def users(_: dict = Depends(admin_user)) -> dict:
    return {"code": 200, "users": auth_service.list_users()}


@router.put("/users/{user_id}")
def update_user(user_id: str, payload: UserUpdatePayload, _: dict = Depends(admin_user)) -> dict:
    updates = payload.dict(exclude_none=True)
    return {"code": 200, "user": auth_service.update_user(user_id, updates)}


@router.delete("/users/{user_id}")
def delete_user(user_id: str, user: dict = Depends(admin_user)) -> dict:
    auth_service.delete_user(user_id, user["id"])
    return {"code": 200, "msg": "user deleted"}
