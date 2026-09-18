from typing import Any
from pydantic import BaseModel


class BlueprintResponse(BaseModel):
    validation_status: str
    blueprint: dict[str, Any]
    repair_iterations: int = 0
from typing import List, Optional

class HealthResponse(BaseModel):
    status: str
    service: str

class GenerationSummary(BaseModel):
    generation_id: str
    project_id: str
    created_at: str
    validation_status: str
    repair_iterations: int

class ProjectSummary(BaseModel):
    project_id: str
    name: str
    created_at: str
    latest_generation_id: Optional[str] = None

class ProjectDetail(BaseModel):
    project_id: str
    name: str
    created_at: str
    latest_generation_id: Optional[str] = None
    generations: List[GenerationSummary] = []
