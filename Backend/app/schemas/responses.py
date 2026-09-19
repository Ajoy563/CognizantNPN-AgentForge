from typing import Any
from pydantic import BaseModel


class BlueprintResponse(BaseModel):
    blueprint: dict[str, Any]
from typing import List, Optional

class HealthResponse(BaseModel):
    status: str
    service: str

class GenerationSummary(BaseModel):
    generation_id: str
    project_id: str
    created_at: str

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
