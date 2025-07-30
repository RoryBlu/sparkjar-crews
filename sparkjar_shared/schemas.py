from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class CrewExecutionRequest(BaseModel):
    crew_name: str
    inputs: Dict[str, Any]


class CrewExecutionResponse(BaseModel):
    success: bool
    crew_name: str
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None


class CrewHealthResponse(BaseModel):
    status: str
    service: str
    environment: str
    available_crews: List[str]


class CrewListResponse(BaseModel):
    available_crews: Dict[str, Any]
    total_count: int
    timestamp: datetime
