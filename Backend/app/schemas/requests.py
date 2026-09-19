from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class GenerateRequest(BaseModel):
    """The public request contract, deliberately aligned with ``ai.service``."""

    model_config = ConfigDict(extra="forbid")

    business_idea: str = Field(min_length=1, max_length=10_000)
    tech_preference: Literal["opensource", "enterprise"]
    cloud_preference: Literal["aws", "azure", "gcp", "none"]
    expected_daily_traffic: int = Field(gt=0)
    delivery_timeline_months: int = Field(gt=0, le=60)
    country: str = Field(min_length=1, max_length=200)
