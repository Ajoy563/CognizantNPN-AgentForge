"""AI service boundary for SolutionForge.

Exposes exactly one public function:

    generate_blueprint(request) -> BlueprintResponse

This is the only thing the HTTP backend needs to call. It never needs to
know about individual agents or CrewAI — those stay behind this boundary,
owned by ai.crew. This module only orchestrates:

1. Run the pipeline once via ai.crew.run_pipeline() (Business Analyst ->
   Solution Architect -> Technology Advisor -> Delivery Planner, followed
   by the single plain-Python completion patch).
2. Render the Markdown and HTML reports from the four structured outputs.
"""

import time
import uuid
from typing import Any, Callable, Literal, Optional

from ai.config import LLMConfigError, load_llm_config
from ai.crew import PipelineResult, run_pipeline
from ai.report.html import render_blueprint_html
from ai.report.markdown import render_blueprint_markdown
from ai.schemas.response import BlueprintMeta, BlueprintResponse
from pydantic import BaseModel, ConfigDict, Field

TechPreference = Literal["opensource", "enterprise"]
CloudPreference = Literal["aws", "azure", "gcp", "none"]


class GenerateRequest(BaseModel):
    """The six official generation-request fields. No other field is
    accepted — the AI layer never receives a Firebase UID/token or
    anything persistence-related for reasoning."""

    model_config = ConfigDict(extra="forbid")

    business_idea: str = Field(min_length=1)
    tech_preference: TechPreference
    cloud_preference: CloudPreference
    expected_daily_traffic: int = Field(gt=0)
    delivery_timeline_months: int = Field(gt=0)
    country: str = Field(min_length=1)


class BlueprintGenerationError(RuntimeError):
    """Raised when blueprint generation actually fails: a stage/CrewAI/LLM
    error, or report rendering failing. Always chains the original
    exception via `from` — never swallowed, and generate_blueprint never
    returns a BlueprintResponse when this is raised."""


def _resolve_model_name(llm: Optional[Any], model_name: Optional[str]) -> str:
    if model_name:
        return model_name
    try:
        config = load_llm_config()
        return f"{config.provider}/{config.model}"
    except LLMConfigError:
        pass
    if llm is not None:
        model_attr = getattr(llm, "model", None)
        if model_attr:
            return str(model_attr)
    return "unknown"


def generate_blueprint(
    request: GenerateRequest,
    *,
    project_id: Optional[str] = None,
    llm: Optional[Any] = None,
    model_name: Optional[str] = None,
    executors: Optional[dict] = None,
    run_pipeline: Callable[..., PipelineResult] = run_pipeline,
    render_markdown: Callable[..., str] = render_blueprint_markdown,
    render_html: Callable[..., str] = render_blueprint_html,
) -> BlueprintResponse:
    """The one public AI service boundary.

    Runs the four-stage pipeline once and renders the reports. Raises
    BlueprintGenerationError (never swallowed) on any stage/CrewAI/LLM/
    report-rendering failure.

    `project_id`/`llm`/`model_name`/`executors`/`run_pipeline`/
    `render_markdown`/`render_html` are all optional — normal backend
    usage is simply `generate_blueprint(request)`.
    """
    started = time.monotonic()

    try:
        result = run_pipeline(
            business_idea=request.business_idea,
            tech_preference=request.tech_preference,
            cloud_preference=request.cloud_preference,
            expected_daily_traffic=request.expected_daily_traffic,
            delivery_timeline_months=request.delivery_timeline_months,
            country=request.country,
            llm=llm,
            executors=executors,
        )
    except Exception as exc:
        raise BlueprintGenerationError(f"Pipeline failed: {exc}") from exc

    try:
        blueprint_md = render_markdown(
            result.requirements, result.architecture, result.technology, result.delivery
        )
        blueprint_html = render_html(
            result.requirements, result.architecture, result.technology, result.delivery
        )
    except Exception as exc:
        raise BlueprintGenerationError(f"Report rendering failed: {exc}") from exc

    return BlueprintResponse(
        status="success",
        project_id=project_id or str(uuid.uuid4()),
        requirements=result.requirements,
        architecture=result.architecture,
        technology=result.technology,
        delivery=result.delivery,
        blueprint_md=blueprint_md,
        blueprint_html=blueprint_html,
        meta=BlueprintMeta(
            model=_resolve_model_name(llm, model_name),
            duration_seconds=time.monotonic() - started,
        ),
    )
