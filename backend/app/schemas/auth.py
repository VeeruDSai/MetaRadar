import uuid
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class LoginRequest(BaseModel):
    email: str
    password: str


class DemoLoginRequest(BaseModel):
    role: str = Field(..., description="Role to authenticate as in demo mode (e.g. MEDICAL_AFFAIRS, REGULATORY, SAFETY, MARKET_ACCESS, COMMUNICATIONS, LEADERSHIP, ADMIN)")


class UserMe(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    email: str
    display_name: str
    role: str
    is_active: bool
    created_at: datetime


class CsrfResponse(BaseModel):
    csrf_token: str


class LogoutResponse(BaseModel):
    status: str = "logged_out"
    message: str = "Session successfully terminated"
