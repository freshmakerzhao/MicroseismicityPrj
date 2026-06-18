from typing import Optional

from pydantic import BaseModel


class LoginPayload(BaseModel):
    username: str
    password: str


class RegisterPayload(BaseModel):
    username: str
    password: str
    display_name: Optional[str] = ""


class UserUpdatePayload(BaseModel):
    display_name: Optional[str] = None
    role: Optional[str] = None
    enabled: Optional[bool] = None
    password: Optional[str] = None
