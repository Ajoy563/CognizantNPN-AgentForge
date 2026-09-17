from typing import Literal
from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    business_idea: str = Field(..., min_length=1)
    technology_preference: Literal["open-source", "enterprise"]
    cloud_preference: Literal[
        "AWS",
        "Azure",
        "GCP",
        "no specific cloud preference"
    ]
    expected_daily_traffic: str
    delivery_timeline_months: int = Field(..., gt=0)
    data_hosting_country: str