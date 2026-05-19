from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class LLMConfigRequest(BaseModel):
    name: str = ""
    base_url: str = ""
    api_key: str = ""
    model: str = ""


class LLMConfigResponse(BaseModel):
    name: str = ""
    base_url: str = ""
    api_key: str = ""
    model: str = ""
    is_active: bool = True
    updated_at: Optional[str] = None


class LLMTestResponse(BaseModel):
    success: bool
    message: str = ""


def mask_api_key(key: str) -> str:
    if not key or len(key) < 8:
        return "••••••••" if key else ""
    return key[:3] + "••••" + key[-4:]


def is_masked_key(key: str) -> bool:
    return "••••" in key
