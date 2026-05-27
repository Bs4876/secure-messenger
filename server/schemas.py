"""
schemas.py — Pydantic models for request validation and serialization (Fix Q14, Q20).
Optimized for Pydantic V2.
"""

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)

class LoginRequest(BaseModel):
    username: str
    password: str

class MessageRequest(BaseModel):
    recipient: str = Field(..., min_length=1, max_length=50)
    content: str = Field(..., min_length=1)

class MessageResponse(BaseModel):
    id: int
    sender: str
    recipient: str
    content: str
    created_at: datetime

    # הגדרה מודרנית התואמת ל-Pydantic V2 (מעלים את כל ה-Warnings מהריצה)
    model_config = ConfigDict(from_attributes=True)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"