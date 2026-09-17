from pydantic import BaseModel, ConfigDict, Field


class Component(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    responsibility: str = Field(min_length=1)


class ArchitectureOutput(BaseModel):
    """Solution Architect structured output."""

    model_config = ConfigDict(extra="forbid")

    architecture_style: str = Field(min_length=1)
    components: list[Component]
    data_flow: list[str]
    storage: list[str]
    security: list[str]
    scalability: list[str]
    mvp_architecture: list[str]
    future_evolution: list[str]
