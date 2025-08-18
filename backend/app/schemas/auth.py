from pydantic import BaseModel, EmailStr
from typing import Optional


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class AdminResponse(BaseModel):
    id: int
    name: str
    email: str
    permission_level: str
    is_active: bool
    last_login: Optional[str] = None
    created_at: str

class LoginResponse(BaseModel):
    admin: AdminResponse
    tokens: TokenResponse
    message: str = "Login successful"