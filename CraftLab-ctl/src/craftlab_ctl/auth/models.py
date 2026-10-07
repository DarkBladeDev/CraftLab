from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class Role(str, Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    CREATOR = "creator"
    VIEWER = "viewer"


class User(BaseModel):
    id: str
    username: str
    password_hash: str
    display_name: str
    roles: List[str] = Field(default_factory=list)
    is_active: bool = True
    created_at: str
    updated_at: str


class Session(BaseModel):
    session_id: str
    user_id: str
    username: str
    roles: List[str] = Field(default_factory=list)
    created_at: str
    expires_at: str


class AuthContext(BaseModel):
    user_id: str
    username: str
    roles: List[str] = Field(default_factory=list)
    is_break_glass: bool = False

    def has_role(self, *required_roles: str) -> bool:
        if self.is_break_glass or Role.ADMIN.value in self.roles:
            return True
        return any(r in self.roles for r in required_roles)


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    status: str = "ok"
    user_id: str
    username: str
    display_name: str
    roles: List[str]


class UserCreateRequest(BaseModel):
    username: str
    password: str
    display_name: Optional[str] = None
    roles: List[str] = Field(default_factory=lambda: [Role.VIEWER.value])


class UserResponse(BaseModel):
    id: str
    username: str
    display_name: str
    roles: List[str]
    is_active: bool
    created_at: str
