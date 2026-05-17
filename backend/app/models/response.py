from pydantic import BaseModel
from typing import Any, Optional


class BaseResponse(BaseModel):
    success: bool = True
    data: Optional[Any] = None
    message: str = ""
    request_id: str = ""
    timestamp: str = ""
