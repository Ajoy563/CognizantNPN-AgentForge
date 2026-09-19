from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

RequirementCategory = Literal[
    "functional",
    "non_functional",
    "security",
    "compliance",
    "performance",
    "availability",
    "scalability",
    "integration",
    "data",
    "ux",
]
RequirementPriority = Literal["must", "should", "could"]


class Requirement(BaseModel):
    """One traceable requirement. Every downstream artifact (architecture
    component, technology decision, delivery workstream, validation check)
    references requirements by `id`, never by re-describing them."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^REQ-\d{3}$")
    category: RequirementCategory
    text: str = Field(min_length=1)
    priority: RequirementPriority


class Persona(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    role: str = Field(min_length=1)
    goals: list[str]


class RequirementsOutput(BaseModel):
    """Business Analyst structured output."""

    model_config = ConfigDict(extra="forbid")

    problem: str = Field(min_length=1)
    business_context: str = Field(min_length=1)
    business_goals: list[str]
    personas: list[Persona]
    stakeholders: list[str]
    requirements: list[Requirement]
    mvp_requirement_ids: list[str]
    mvp_focus: str = Field(min_length=1)
    future_scope: list[str]
    assumptions: list[str]
    open_questions: list[str]
    constraints: list[str]
    risks: list[str]
