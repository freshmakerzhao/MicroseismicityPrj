import hashlib
import json
import secrets
import sqlite3
import uuid
from datetime import datetime
from typing import Any

from fastapi import HTTPException, status

from app.core.config import settings


USERS_FILE = settings.base_dir / "config" / "users.json"
USERS_DB = settings.base_dir / "data" / "users.db"
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
_DB_INITIALIZED = False


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


def _connect() -> sqlite3.Connection:
    USERS_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(USERS_DB)
    conn.row_factory = sqlite3.Row
    return conn


def _row_to_user(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    user = dict(row)
    user["enabled"] = bool(user.get("enabled", True))
    return user


def _ensure_store() -> None:
    global _DB_INITIALIZED
    if _DB_INITIALIZED:
        return

    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
                display_name TEXT NOT NULL DEFAULT '',
                role TEXT NOT NULL DEFAULT 'user',
                enabled INTEGER NOT NULL DEFAULT 1,
                salt TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
        _migrate_json_users(conn)
        _ensure_admin_user(conn)
        _append_default_users(conn)
        conn.commit()

    _DB_INITIALIZED = True


def _migrate_json_users(conn: sqlite3.Connection) -> None:
    if not USERS_FILE.exists():
        return
    try:
        with USERS_FILE.open("r", encoding="utf-8") as fp:
            users = json.load(fp)
    except (OSError, json.JSONDecodeError):
        return
    if not isinstance(users, list):
        return

    for user in users:
        if not isinstance(user, dict) or not user.get("username"):
            continue
        salt = user.get("salt") or secrets.token_hex(16)
        password_hash = user.get("password_hash") or _hash_password("user123", salt)
        conn.execute(
            """
            INSERT OR IGNORE INTO users (
                id, username, display_name, role, enabled, salt, password_hash, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user.get("id") or str(uuid.uuid4()),
                str(user.get("username")).strip(),
                str(user.get("display_name") or user.get("name") or user.get("username")).strip(),
                user.get("role") if user.get("role") in ROLES else "user",
                1 if user.get("enabled", True) else 0,
                salt,
                password_hash,
                user.get("created_at") or _now(),
                user.get("updated_at") or _now(),
            ),
        )


def _ensure_admin_user(conn: sqlite3.Connection) -> None:
    row = conn.execute("SELECT id FROM users WHERE lower(username) = lower(?)", ("admin",)).fetchone()
    if row:
        return

    salt = secrets.token_hex(16)
    conn.execute(
        """
        INSERT INTO users (
            id, username, display_name, role, enabled, salt, password_hash, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            str(uuid.uuid4()),
            "admin",
            "System Administrator",
            "admin",
            1,
            salt,
            _hash_password("admin123", salt),
            _now(),
            _now(),
        ),
    )


def _append_default_users(conn: sqlite3.Connection) -> None:
    for username, display_name in DEFAULT_USERS:
        row = conn.execute("SELECT id FROM users WHERE lower(username) = lower(?)", (username,)).fetchone()
        if row:
            continue
        salt = secrets.token_hex(16)
        conn.execute(
            """
            INSERT INTO users (
                id, username, display_name, role, enabled, salt, password_hash, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                username,
                display_name,
                "user",
                1,
                salt,
                _hash_password("user123", salt),
                _now(),
                _now(),
            ),
        )


def _load_users() -> list[dict[str, Any]]:
    _ensure_store()
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM users ORDER BY role ASC, created_at ASC, username ASC").fetchall()
    return [dict(_row_to_user(row)) for row in rows]


def find_user(username: str) -> dict[str, Any] | None:
    normalized = username.strip().lower()
    _ensure_store()
    with _connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE lower(username) = ?", (normalized,)).fetchone()
    return _row_to_user(row)


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
    _ensure_store()
    with _connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    user = _row_to_user(row)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session user not found")
    if not user.get("enabled", True):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is disabled")
    return user


def require_admin(user: dict[str, Any]) -> None:
    if user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")


def register_user(username: str, password: str, display_name: str = "") -> dict[str, Any]:
    username = username.strip()
    if len(username) < 3:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username must be at least 3 chars")
    if len(password) < 6:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password must be at least 6 chars")
    _ensure_store()
    if find_user(username):
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
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO users (
                id, username, display_name, role, enabled, salt, password_hash, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user["id"],
                user["username"],
                user["display_name"],
                user["role"],
                1 if user["enabled"] else 0,
                user["salt"],
                user["password_hash"],
                user["created_at"],
                user["updated_at"],
            ),
        )
        conn.commit()
    return _public_user(user)


def list_users() -> list[dict[str, Any]]:
    return [_public_user(user) for user in _load_users()]


def update_user(user_id: str, updates: dict[str, Any]) -> dict[str, Any]:
    _ensure_store()
    with _connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        user = _row_to_user(row)
        if not user:
            row = conn.execute("SELECT * FROM users WHERE username = ?", (user_id,)).fetchone()
            user = _row_to_user(row)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

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

        conn.execute(
            """
            UPDATE users
            SET display_name = ?, role = ?, enabled = ?, salt = ?, password_hash = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                user["display_name"],
                user["role"],
                1 if user["enabled"] else 0,
                user["salt"],
                user["password_hash"],
                user["updated_at"],
                user["id"],
            ),
        )
        conn.commit()
        return _public_user(user)


def delete_user(user_id: str, current_user_id: str) -> None:
    if user_id == current_user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete current user")
    _ensure_store()
    with _connect() as conn:
        cursor = conn.execute("DELETE FROM users WHERE id = ? OR username = ?", (user_id, user_id))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        conn.commit()
