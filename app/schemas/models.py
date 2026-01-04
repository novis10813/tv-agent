"""
Pydantic schemas for request/response models
"""

from typing import Optional
from pydantic import BaseModel


class CommandRequest(BaseModel):
    text: str
    user_id: Optional[str] = None


class CommandResponse(BaseModel):
    success: bool
    message: str
    tool_calls: list[dict] = []


class ProfileCreate(BaseModel):
    user_id: str
    netflix_profile_index: int = 1
    netflix_pin: Optional[str] = None
    youtube_account_name: Optional[str] = None  # YouTube 帳號名稱 (用 OCR 辨識)


class ProfileResponse(BaseModel):
    user_id: str
    netflix_profile_index: int
    netflix_pin: Optional[str] = None
    youtube_account_name: Optional[str] = None
