from pydantic import BaseModel, ConfigDict, Field


class Workstream(BaseModel):
    """One traceable implementation workstream. `addresses` links back to
    Requirement and/or Component ids (REQ-xxx / ARCH-xxx)."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^TASK-\d{3}$")
    name: str = Field(min_length=1)
    purpose: str = Field(min_length=1)
    activities: list[str]
    dependencies: list[str]
    deliverable: str = Field(min_length=1)
    addresses: list[str] = Field(min_length=1)
    effort: str = Field(min_length=1)


class TeamRole(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: str = Field(min_length=1)
    count: int = Field(ge=1)


class TimelinePhase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    phase: str = Field(min_length=1)
    duration: str = Field(min_length=1)
    milestone: str = Field(min_length=1)
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

    workstreams: list[Workstream] = Field(min_length=1)
    milestones: list[str]
    dependencies: list[str]
    team_roles: list[TeamRole] = Field(min_length=1)
    timeline: list[TimelinePhase] = Field(min_length=1)
    testing_strategy: list[str]
    integration_testing: list[str]
    uat_strategy: list[str]
    deployment_strategy: list[str]
    ci_cd: list[str]
    monitoring: list[str]
    rollback_strategy: list[str]
    risks: list[DeliveryRisk]
    effort_complexity: str = Field(min_length=1)
    cost_estimate: DeliveryCostEstimate
    future_evolution: list[str]
