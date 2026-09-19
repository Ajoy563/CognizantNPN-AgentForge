from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ArchitectureLayer = Literal[
    "presentation",
    "api",
    "application",
    "domain",
    "data",
    "infrastructure",
    "external",
]


class Component(BaseModel):
    """One traceable architecture component. `layer` drives the generated
    diagram; `satisfies` links it back to Requirement ids."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^ARCH-\d{3}$")
    name: str = Field(min_length=1)
    layer: ArchitectureLayer
    purpose: str = Field(min_length=1)
    responsibility: str = Field(min_length=1)
    interfaces: list[str]
    # "Not applicable" is a valid answer when the concern genuinely does not
    # apply to this component — but it is never left blank.
    security_consideration: str = Field(min_length=1)
    scalability_consideration: str = Field(min_length=1)
    satisfies: list[str] = Field(min_length=1)  # Requirement ids (REQ-xxx)


class DataFlowStep(BaseModel):
    """One edge in the request/data flow graph, also used to draw
    connections in the generated diagram. `from_node`/`to_node` are either
    a Component id (ARCH-xxx) or an external actor name (e.g. "User",
    "External API")."""

    model_config = ConfigDict(extra="forbid")

    from_node: str = Field(min_length=1)
    to_node: str = Field(min_length=1)
    description: str = Field(min_length=1)


class SecurityControl(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^SEC-\d{3}$")
    control: str = Field(min_length=1)
    satisfies: list[str] = Field(min_length=1)  # Requirement ids (REQ-xxx)


class ArchitectureOutput(BaseModel):
    """Solution Architect structured output. Security is a first-class,
    requirement-traceable part of this output rather than a separate
    agent — see 02_AI_SPEC's cost-of-a-fifth-LLM-call tradeoff."""

    model_config = ConfigDict(extra="forbid")

    architecture_style: str = Field(min_length=1)
    rationale: str = Field(min_length=1)
    components: list[Component] = Field(min_length=1)
    data_flow: list[DataFlowStep]
    request_flow: list[str]
    authentication_flow: list[str]
    external_integrations: list[str]
    storage: list[str]
    caching: list[str]
    messaging: list[str]
    observability: list[str]
    security_controls: list[SecurityControl]
    scalability_strategy: list[str]
    availability_strategy: list[str]
    disaster_recovery: list[str]
    deployment_architecture: list[str]
    mvp_architecture: list[str]
    future_evolution: list[str]
