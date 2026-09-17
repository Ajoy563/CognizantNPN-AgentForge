from pydantic import BaseModel, ConfigDict, Field


class TechnologyRecommendation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    component: str = Field(min_length=1)
    recommended: str = Field(min_length=1)
    alternatives: list[str]
    reason: str = Field(min_length=1)
    tradeoffs: list[str]


class TechnologyCostEstimate(BaseModel):
    """Indicative infrastructure/service cost range. Advisory only, never a billing calculation."""

    model_config = ConfigDict(extra="forbid")

    infrastructure_monthly: str = Field(min_length=1)
    implementation: str = Field(min_length=1)
    assumptions: list[str]


class TechnologyOutput(BaseModel):
    """Technology Advisor structured output."""

    model_config = ConfigDict(extra="forbid")

    recommendations: list[TechnologyRecommendation]
    cloud_fit: str = Field(min_length=1)
    open_source_fit: str = Field(min_length=1)
    lock_in_considerations: str = Field(min_length=1)
    cost_estimate: TechnologyCostEstimate
