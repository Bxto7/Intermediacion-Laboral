from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.common import UserRole


class RegisterRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    role: UserRole = UserRole.WORKER
    full_name: str = Field(default="", min_length=0, max_length=100)
    dni: str = Field(default="", min_length=0, max_length=8)


class LoginRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class MessageResponse(BaseModel):
    message: str


class ForgotPasswordRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    email: EmailStr


class VerifyEmailRequest(BaseModel):
    token: str = Field(..., min_length=32, max_length=128)


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=32, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=128)


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    role: UserRole
