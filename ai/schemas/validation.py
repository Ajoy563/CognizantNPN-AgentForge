from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

CheckStatus = Literal["PASS", "FAIL"]
ValidationStatus = Literal["PASS", "FAIL"]
CheckOwner = Literal[
    "Business Analyst",
    "Solution Architect",
    "Technology Advisor",
    "Delivery Planner",
    "Cross-stage",
]


class ValidationCheck(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    status: CheckStatus
    issue: Optional[str] = None
    owner: Optional[CheckOwner] = None


class ValidationOutput(BaseModel):
    """Consistency Validator structured output. iterations is capped at MAX_REPAIR_ITERATIONS=3."""

    model_config = ConfigDict(extra="forbid")

    status: ValidationStatus
    iterations: int = Field(ge=0, le=3)
    checks: list[ValidationCheck]
    warnings: list[str]
