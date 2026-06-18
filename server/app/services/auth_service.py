import hashlib
import json
import secrets
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import HTTPException, status

from app.core.config import settings


USERS_FILE = settings.base_dir / "config" / "users.json"
ROLES = {"admin", "user"}
SESSIONS: dict[str, str] = {}
DEFAULT_USERS = [
    ("monitor01", "微震监测员01"),
    ("monitor02", "微震监测员02"),
    ("analyst01", "风险分析员01"),
    ("analyst02", "风险分析员02"),
    ("engineer01", "防冲工程师01"),
    ("engineer02", "防冲工程师02"),
    ("viewer01", "现场查看员01"),
    ("viewer02", "现场查看员02"),
]


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _hash_password(password: str, salt: str) -> str:
    raw = f"{salt}:{password}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _public_user(user: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": user["id"],
        "username": user["username"],
        "display_name": user.get("display_name", ""),
        "role": user.get("role", "user"),
        "enabled": bool(user.get("enabled", True)),
        "created_at": user.get("created_at", ""),
        "updated_at": user.get("updated_at", ""),
    }


def _ensure_store() -> None:
    USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if USERS_FILE.exists():
        return

    salt = secrets.token_hex(16)
    admin = {
        "id": str(uuid.uuid4()),
        "username": "admin",
        "display_name": "System Administrator",
        "role": "admin",
        "enabled": True,
        "salt": salt,
        "password_hash": _hash_password("admin123", salt),
        "created_at": _now(),
        "updated_at": _now(),
    }
    users = [admin]
    _append_default_users(users)
    _save_users(users)


def _append_default_users(users: list[dict[str, Any]]) -> bool:
    existing = {user["username"].lower() for user in users}
    changed = False
    for username, display_name in DEFAULT_USERS:
        if username.lower() in existing:
            continue
        salt = secrets.token_hex(16)
        users.append({
            "id": str(uuid.uuid4()),
            "username": username,
            "display_name": display_name,
            "role": "user",
            "enabled": True,
            "salt": salt,
            "password_hash": _hash_password("user123", salt),
            "created_at": _now(),
            "updated_at": _now(),
        })
        existing.add(username.lower())
        changed = True
    return changed


def _load_users() -> list[dict[str, Any]]:
    _ensure_store()
    with USERS_FILE.open("r", encoding="utf-8") as fp:
        users = json.load(fp)
    if not isinstance(users, list):
        raise ValueError("users.json must contain a list")
    if _append_default_users(users):
        _save_users(users)
    return users


def _save_users(users: list[dict[str, Any]]) -> None:
    USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with USERS_FILE.open("w", encoding="utf-8") as fp:
        json.dump(users, fp, ensure_ascii=False, indent=2)


def find_user(username: str) -> dict[str, Any] | None:
    normalized = username.strip().lower()
    for user in _load_users():
        if user["username"].lower() == normalized:
            return user
    return None


def authenticate(username: str, password: str) -> dict[str, Any]:
    user = find_user(username)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    if not user.get("enabled", True):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is disabled")
    if _hash_password(password, user["salt"]) != user["password_hash"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    return user


def create_session(user: dict[str, Any]) -> str:
    token = secrets.token_urlsafe(32)
    SESSIONS[token] = user["id"]
    return token


def remove_session(token: str) -> None:
    SESSIONS.pop(token, None)


def get_user_by_token(token: str) -> dict[str, Any]:
    user_id = SESSIONS.get(token)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    for user in _load_users():
        if user["id"] == user_id:
            if not user.get("enabled", True):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is disabled")
            return user
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session user not found")


def require_admin(user: dict[str, Any]) -> None:
    if user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")


def register_user(username: str, password: str, display_name: str = "") -> dict[str, Any]:
    username = username.strip()
    if len(username) < 3:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username must be at least 3 chars")
    if len(password) < 6:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password must be at least 6 chars")
    users = _load_users()
    if any(user["username"].lower() == username.lower() for user in users):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")

    salt = secrets.token_hex(16)
    user = {
        "id": str(uuid.uuid4()),
        "username": username,
        "display_name": display_name.strip() or username,
        "role": "user",
        "enabled": True,
        "salt": salt,
        "password_hash": _hash_password(password, salt),
        "created_at": _now(),
        "updated_at": _now(),
    }
    users.append(user)
    _save_users(users)
    return _public_user(user)


def list_users() -> list[dict[str, Any]]:
    return [_public_user(user) for user in _load_users()]


def update_user(user_id: str, updates: dict[str, Any]) -> dict[str, Any]:
    users = _load_users()
    for user in users:
        if user["id"] != user_id:
            continue
        if "role" in updates:
            role = updates["role"]
            if role not in ROLES:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role")
            user["role"] = role
        if "enabled" in updates:
            user["enabled"] = bool(updates["enabled"])
        if "display_name" in updates:
            user["display_name"] = str(updates["display_name"]).strip() or user["username"]
        if updates.get("password"):
            password = str(updates["password"])
            if len(password) < 6:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password must be at least 6 chars")
            user["salt"] = secrets.token_hex(16)
            user["password_hash"] = _hash_password(password, user["salt"])
        user["updated_at"] = _now()
        _save_users(users)
        return _public_user(user)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


def delete_user(user_id: str, current_user_id: str) -> None:
    if user_id == current_user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete current user")
    users = _load_users()
    next_users = [user for user in users if user["id"] != user_id]
    if len(next_users) == len(users):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    _save_users(next_users)
