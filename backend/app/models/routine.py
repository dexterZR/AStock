from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime


class RoutineStep(BaseModel):
    step_id: str
    name: str
    description: str
    enabled: bool = True
    config: dict = {}


class RoutineTemplate(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    name: str
    description: str
    steps: List[RoutineStep] = []
    is_default: bool = False
    created_at: datetime = Field(default_factory=datetime.now)


class StepResult(BaseModel):
    step_id: str
    name: str
    status: str = "pending"  # pending/running/success/failed
    data: dict = {}
    error: Optional[str] = None
    duration_ms: int = 0


class RoutineResult(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    template_id: str
    template_name: str
    stock_code: str
    stock_name: str
    status: str = "running"  # running/completed/failed
    steps: List[StepResult] = []
    report: str = ""
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


class RoutineRunRequest(BaseModel):
    template_id: str = "default"
    stock_code: str
    stock_name: str = ""
