from pydantic import BaseModel, ConfigDict, Field


class RequirementsOutput(BaseModel):
    """Business Analyst structured output."""

    model_config = ConfigDict(extra="forbid")

    problem: str = Field(min_length=1)
    stakeholders: list[str]
    functional_requirements: list[str]
    non_functional_requirements: list[str]
    mvp_priorities: list[str]
    future_scope: list[str]
    assumptions: list[str]
    constraints: list[str]
    risks: list[str]
    clarifications: list[str]
