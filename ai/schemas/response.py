from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ai.schemas.architecture import ArchitectureOutput
from ai.schemas.delivery import DeliveryOutput
from ai.schemas.requirements import RequirementsOutput
from ai.schemas.technology import TechnologyOutput
from ai.schemas.validation import ValidationOutput


class BlueprintMeta(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model: str = Field(min_length=1)
    duration_seconds: float = Field(ge=0)
    repair_iterations: int = Field(ge=0, le=3)


class BlueprintResponse(BaseModel):
    """Return type of ai.service.generate_blueprint(). Matches API contract section 7."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["success"]
    project_id: str = Field(min_length=1)
    requirements: RequirementsOutput
    architecture: ArchitectureOutput
    technology: TechnologyOutput
    delivery: DeliveryOutput
    validation: ValidationOutput
    blueprint_md: str = Field(min_length=1)
    blueprint_html: str = Field(min_length=1)
    meta: BlueprintMeta
