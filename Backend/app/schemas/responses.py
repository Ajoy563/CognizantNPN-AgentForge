from typing import Any
from pydantic import BaseModel


class BlueprintResponse(BaseModel):
    validation_status: str
    blueprint: dict[str, Any]
    repair_iterations: int = 0