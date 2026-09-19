from pydantic import BaseModel, ConfigDict, Field


class TechnologyDecision(BaseModel):
    """One traceable technology decision: what it supports architecturally
    (`supports` -> ARCH-xxx) and which requirements it ultimately serves
    (`requirements` -> REQ-xxx)."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^TECH-\d{3}$")
    technology: str = Field(min_length=1)
    category: str = Field(min_length=1)
    purpose: str = Field(min_length=1)
    supports: list[str] = Field(min_length=1)  # Component ids (ARCH-xxx)
    requirements: list[str] = Field(min_length=1)  # Requirement ids (REQ-xxx)
    reason: str = Field(min_length=1)
    integration_method: str = Field(min_length=1)
    advantages: list[str]
    tradeoffs: list[str]
    security_considerations: list[str]
    scalability_considerations: list[str]
    operational_considerations: list[str]
    cost_considerations: str = Field(min_length=1)
    # "none" when portable/self-hostable, otherwise the specific cloud/vendor this depends on.
    provider_dependency: str = Field(min_length=1)
    portability_risk: str = Field(min_length=1)
    migration_mitigation: str = Field(min_length=1)
    alternatives: list[str]


class TechnologyCostEstimate(BaseModel):
    """Indicative infrastructure/service cost range. Advisory only, never a billing calculation."""

    model_config = ConfigDict(extra="forbid")

    infrastructure_monthly: str = Field(min_length=1)
    implementation: str = Field(min_length=1)
    assumptions: list[str]


class TechnologyOutput(BaseModel):
    """Technology Advisor structured output."""

    model_config = ConfigDict(extra="forbid")

    decisions: list[TechnologyDecision] = Field(min_length=1)
    cloud_fit: str = Field(min_length=1)
    open_source_fit: str = Field(min_length=1)
    overall_lock_in_assessment: str = Field(min_length=1)
    cost_estimate: TechnologyCostEstimate
