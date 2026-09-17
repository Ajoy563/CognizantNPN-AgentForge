from pydantic import BaseModel, ConfigDict, Field


class TeamRole(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: str = Field(min_length=1)
    count: int = Field(ge=1)


class TimelinePhase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    phase: str = Field(min_length=1)
    duration: str = Field(min_length=1)
    deliverables: list[str]


class DeliveryRisk(BaseModel):
    model_config = ConfigDict(extra="forbid")

    risk: str = Field(min_length=1)
    impact: str = Field(min_length=1)
    mitigation: str = Field(min_length=1)


class DeliveryCostEstimate(BaseModel):
    """Indicative implementation/team cost range. Advisory only, never a billing calculation."""

    model_config = ConfigDict(extra="forbid")

    estimated_effort: str = Field(min_length=1)
    estimated_team_cost: str = Field(min_length=1)
    assumptions: list[str]


class DeliveryOutput(BaseModel):
    """Delivery Planner structured output."""

    model_config = ConfigDict(extra="forbid")

    workstreams: list[str]
    team_roles: list[TeamRole]
    timeline: list[TimelinePhase]
    dependencies: list[str]
    testing_strategy: list[str]
    deployment_strategy: list[str]
    risks: list[DeliveryRisk]
    effort_complexity: str = Field(min_length=1)
    cost_estimate: DeliveryCostEstimate
    future_evolution: list[str]
