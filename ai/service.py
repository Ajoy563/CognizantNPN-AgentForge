"""AI service boundary for SolutionForge.

Exposes exactly one public function:

    generate_blueprint(request) -> BlueprintResponse

This is the only thing an HTTP backend, added in a later step, needs to
call. It never needs to know about individual agents, CrewAI, or repair
routing — those all stay behind this boundary, owned by ai.crew and
ai.repair respectively. This module only orchestrates:

1. Run the initial pipeline once via ai.crew.run_initial_pipeline()
   (Business Analyst -> Solution Architect -> Technology Advisor ->
   Delivery Planner -> Consistency Validator).
2. Inspect the resulting ValidationOutput. If it FAILs, ask
   ai.repair.determine_repair_plan() what to do, execute the returned
   stages via ai.crew.run_stage() (which reruns the Validator last, since
   every repair route ends at Stage.VALIDATOR), and repeat.
3. Stop when validation PASSes, the maximum repair iteration count is
   reached, or no actionable repair plan exists (all three are already
   distinguished by ai.repair.RepairPlanStatus) — then build the final
   BlueprintResponse from whatever the latest structured outputs are.

No GenerateRequest schema exists yet under ai/schemas/ (the six official
input fields have so far only been individual keyword arguments on each
task/pipeline builder), so GenerateRequest is defined here, matching
01_API_CONTRACT.md section 2 / 02_AI_SPEC.md section 2 exactly.
"""

import time
import uuid
from dataclasses import replace
from typing import Any, Callable, Literal, Optional

from ai.config import LLMConfigError, load_llm_config
from ai.crew import PipelineResult, StageContext, run_initial_pipeline, run_stage
from ai.repair import RepairPlan, Stage, determine_repair_plan
from ai.schemas.architecture import ArchitectureOutput
from ai.schemas.delivery import DeliveryOutput
from ai.schemas.requirements import RequirementsOutput
from ai.schemas.response import BlueprintMeta, BlueprintResponse
from ai.schemas.technology import TechnologyOutput
from ai.schemas.validation import ValidationOutput
from pydantic import BaseModel, ConfigDict, Field

TechPreference = Literal["opensource", "enterprise"]
CloudPreference = Literal["aws", "azure", "gcp", "none"]


class GenerateRequest(BaseModel):
    """The six official generation-request fields, matching
    01_API_CONTRACT.md section 2 / 02_AI_SPEC.md section 2 exactly. No
    other field is accepted — the AI layer never receives a Firebase
    UID/token or anything persistence-related for reasoning."""

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


# --- Report rendering -------------------------------------------------------
# Small, deterministic, pure-string helpers. No LLM calls, no templating
# engine, no separate reporting module — a fuller styled report is a later
# HTTP-layer report-endpoint concern (02_AI_SPEC.md section 1), not this
# service's job. Kept swappable via generate_blueprint()'s render_markdown/
# render_html parameters.


def _section(title: str, items: list) -> list:
    if not items:
        return []
    lines = [f"### {title}", ""]
    lines += [f"- {item}" for item in items]
    lines.append("")
    return lines


def render_blueprint_markdown(
    requirements: RequirementsOutput,
    architecture: ArchitectureOutput,
    technology: TechnologyOutput,
    delivery: DeliveryOutput,
    validation: ValidationOutput,
) -> str:
    """Deterministic Markdown rendering of the five structured outputs."""
    lines: list = ["# Solution Blueprint", ""]

    lines += ["## Delivery Overview", "", requirements.problem, ""]
    lines += _section("MVP Priorities", requirements.mvp_priorities)
    lines += _section("Future Scope", requirements.future_scope)
    lines += _section("Functional Requirements", requirements.functional_requirements)
    lines += _section(
        "Non-Functional Requirements", requirements.non_functional_requirements
    )

    lines += ["## Architecture", "", f"**Style:** {architecture.architecture_style}", ""]
    lines += ["### Components", ""]
    for component in architecture.components:
        lines.append(f"- **{component.name}**: {component.responsibility}")
    lines.append("")
    lines += _section("Data Flow", architecture.data_flow)
    lines += _section("Storage", architecture.storage)
    lines += _section("Security", architecture.security)
    lines += _section("Scalability", architecture.scalability)
    lines += _section("MVP Architecture", architecture.mvp_architecture)

    lines += ["## Technology Stack", ""]
    for rec in technology.recommendations:
        lines.append(f"- **{rec.component}**: {rec.recommended} — {rec.reason}")
    lines.append("")
    lines.append(f"**Cloud fit:** {technology.cloud_fit}")
    lines.append(f"**Open-source fit:** {technology.open_source_fit}")
    lines.append(f"**Lock-in considerations:** {technology.lock_in_considerations}")
    lines.append("")
    lines.append("### Infrastructure Cost (indicative)")
    lines.append("")
    lines.append(f"- Monthly: {technology.cost_estimate.infrastructure_monthly}")
    lines.append(f"- Setup: {technology.cost_estimate.implementation}")
    lines.append("")
    lines += _section("Infrastructure Cost Assumptions", technology.cost_estimate.assumptions)

    lines += ["## Delivery Plan", ""]
    lines += _section("Workstreams", delivery.workstreams)
    lines.append("### Team")
    lines.append("")
    for role in delivery.team_roles:
        lines.append(f"- {role.role} x{role.count}")
    lines.append("")
    lines.append("### Timeline")
    lines.append("")
    for phase in delivery.timeline:
        deliverables = ", ".join(phase.deliverables)
        lines.append(f"- **{phase.phase}** ({phase.duration}): {deliverables}")
    lines.append("")
    lines += _section("Dependencies", delivery.dependencies)
    lines += _section("Testing Strategy", delivery.testing_strategy)
    lines += _section("Deployment Strategy", delivery.deployment_strategy)
    lines.append("### Risks & Mitigations")
    lines.append("")
    for risk in delivery.risks:
        lines.append(
            f"- **{risk.risk}** (impact: {risk.impact}) — mitigation: {risk.mitigation}"
        )
    lines.append("")
    lines.append(f"**Effort & complexity:** {delivery.effort_complexity}")
    lines.append("")
    lines.append("### Implementation/Team Cost (indicative)")
    lines.append("")
    lines.append(f"- Effort: {delivery.cost_estimate.estimated_effort}")
    lines.append(f"- Team cost: {delivery.cost_estimate.estimated_team_cost}")
    lines.append("")
    lines += _section("Implementation Cost Assumptions", delivery.cost_estimate.assumptions)
    lines += _section(
        "Future Evolution", list(delivery.future_evolution) + list(architecture.future_evolution)
    )

    lines += ["## Assumptions & Open Questions", ""]
    lines += _section("Assumptions", requirements.assumptions)
    lines += _section("Constraints", requirements.constraints)
    lines += _section("Risks", requirements.risks)
    lines += _section("Clarifications", requirements.clarifications)

    lines += ["## Validation", "", f"**Status:** {validation.status}", ""]
    for check in validation.checks:
        detail = f" — {check.issue}" if check.issue else ""
        owner = f" (owner: {check.owner})" if check.owner else ""
        lines.append(f"- [{check.status}] {check.name}{detail}{owner}")
    lines.append("")
    lines += _section("Warnings", validation.warnings)

    return "\n".join(lines).strip() + "\n"


def _inline_markdown_to_html(text: str) -> str:
    import html as html_module

    escaped = html_module.escape(text)
    parts = escaped.split("**")
    rebuilt = [
        f"<strong>{part}</strong>" if index % 2 == 1 else part
        for index, part in enumerate(parts)
    ]
    return "".join(rebuilt)


def render_blueprint_html(markdown_text: str) -> str:
    """Minimal, dependency-free Markdown -> HTML conversion (headings,
    bullet lists, paragraphs, **bold**). Deterministic, no templating
    engine — a fully styled report is a later HTTP-layer concern."""
    import html as html_module

    body_parts: list = []
    list_buffer: list = []

    def flush_list():
        if list_buffer:
            items = "".join(f"<li>{item}</li>" for item in list_buffer)
            body_parts.append(f"<ul>{items}</ul>")
            list_buffer.clear()

    for raw_line in markdown_text.splitlines():
        line = raw_line.strip()
        if not line:
            flush_list()
            continue
        if line.startswith("### "):
            flush_list()
            body_parts.append(f"<h3>{html_module.escape(line[4:])}</h3>")
        elif line.startswith("## "):
            flush_list()
            body_parts.append(f"<h2>{html_module.escape(line[3:])}</h2>")
        elif line.startswith("# "):
            flush_list()
            body_parts.append(f"<h1>{html_module.escape(line[2:])}</h1>")
        elif line.startswith("- "):
            list_buffer.append(_inline_markdown_to_html(line[2:]))
        else:
            flush_list()
            body_parts.append(f"<p>{_inline_markdown_to_html(line)}</p>")
    flush_list()

    return (
        '<!doctype html><html><head><meta charset="utf-8">'
        "<title>Solution Blueprint</title></head><body>"
        + "".join(body_parts)
        + "</body></html>"
    )


# --- Repair-issue-to-stage adapter ------------------------------------------
# ai.repair keys issues by owner name (the ValidationCheck.owner literal
# values); ai.crew's StageContext.repair_issues is per-Stage. This mapping
# is the unavoidable, narrow join between the two — it does not decide
# which stages run or in what order (that stays entirely ai.repair's job).

_STAGE_OWNER_NAMES: dict = {
    Stage.BUSINESS_ANALYST: "Business Analyst",
    Stage.SOLUTION_ARCHITECT: "Solution Architect",
    Stage.TECHNOLOGY_ADVISOR: "Technology Advisor",
    Stage.DELIVERY_PLANNER: "Delivery Planner",
}


def _repair_issues_for_stage(
    stage: Stage, plan: RepairPlan, *, is_first_stage: bool
) -> Optional[tuple]:
    """The RepairPlan's issue text relevant to this one stage.

    Only a stage actually named as a failing owner receives issue text; a
    stage that is merely downstream of a repaired stage gets None — it
    receives the newly repaired upstream output normally, not issue text.
    'Cross-stage' issues (no single owning stage) attach to the first
    stage in the plan, since a Cross-stage repair always starts the full
    sequence from Business Analyst.
    """
    issues: tuple = ()
    owner_name = _STAGE_OWNER_NAMES.get(stage)
    if owner_name and owner_name in plan.issues_by_owner:
        issues += plan.issues_by_owner[owner_name]
    if is_first_stage and "Cross-stage" in plan.issues_by_owner:
        issues += plan.issues_by_owner["Cross-stage"]
    return issues or None


def _coerce_iterations(validation: ValidationOutput, iterations: int) -> ValidationOutput:
    """Authoritatively track the true repair-iteration count at the service
    level, rather than trusting the LLM's self-reported ValidationOutput
    .iterations — the task prompt asks the model to echo it back exactly,
    but nothing enforces compliance, and the max-iteration safety guarantee
    must not depend on that."""
    if validation.iterations == iterations:
        return validation
    return validation.model_copy(update={"iterations": iterations})


def _require_output(value: Optional[Any], name: str) -> Any:
    """Narrow an Optional[...] StageContext field to its concrete type.

    By construction this never actually fires: run_initial_pipeline()
    already requires all five outputs, and every repair-stage executor
    only ever clears fields that a later stage in the same plan is about
    to repopulate. It exists so a misbehaving injected `executors` dict
    fails with a clear BlueprintGenerationError instead of a bare
    AttributeError later, and so the type checker can see these are
    non-None past this point.
    """
    if value is None:
        raise BlueprintGenerationError(
            f"Repair execution left '{name}' unset; cannot build BlueprintResponse."
        )
    return value


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
    run_pipeline: Callable[..., PipelineResult] = run_initial_pipeline,
    plan_repair: Callable[[ValidationOutput], RepairPlan] = determine_repair_plan,
    render_markdown: Callable[..., str] = render_blueprint_markdown,
    render_html: Callable[[str], str] = render_blueprint_html,
) -> BlueprintResponse:
    """The one public AI service boundary.

    Runs the initial five-stage pipeline, then repairs and revalidates in
    a loop until validation PASSes, the maximum repair iteration count is
    reached, or no actionable repair plan exists — returning the latest
    structured outputs either way. Raises BlueprintGenerationError (never
    swallowed) on any stage/CrewAI/LLM/report-rendering failure.

    `project_id`/`llm`/`model_name`/`executors`/`run_pipeline`/
    `plan_repair`/`render_markdown`/`render_html` are all optional —
    normal backend usage is simply `generate_blueprint(request)`.
    """
    started = time.monotonic()

    try:
        pipeline_result = run_pipeline(
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
        raise BlueprintGenerationError(f"Initial pipeline failed: {exc}") from exc

    requirements = pipeline_result.requirements
    architecture = pipeline_result.architecture
    technology = pipeline_result.technology
    delivery = pipeline_result.delivery
    validation = _coerce_iterations(pipeline_result.validation, 0)

    while True:
        plan = plan_repair(validation)
        if not plan.is_actionable:
            break

        next_iteration = validation.iterations + 1
        context = StageContext(
            business_idea=request.business_idea,
            tech_preference=request.tech_preference,
            cloud_preference=request.cloud_preference,
            expected_daily_traffic=request.expected_daily_traffic,
            delivery_timeline_months=request.delivery_timeline_months,
            country=request.country,
            iterations=next_iteration,
            llm=llm,
            requirements=requirements,
            architecture=architecture,
            technology=technology,
            delivery=delivery,
            validation=validation,
        )

        try:
            for index, stage in enumerate(plan.stages):
                context = replace(
                    context,
                    repair_issues=_repair_issues_for_stage(
                        stage, plan, is_first_stage=(index == 0)
                    ),
                )
                context = run_stage(stage, context, executors=executors)
        except Exception as exc:
            raise BlueprintGenerationError(
                f"Repair execution failed for stage(s) {plan.stages}: {exc}"
            ) from exc

        # Read only from the post-loop context: any stage this repair pass
        # touched has already overwritten its own field and cleared every
        # downstream field, so nothing stale can leak through here.
        requirements = context.requirements
        architecture = context.architecture
        technology = context.technology
        delivery = context.delivery
        validation = _coerce_iterations(
            _require_output(context.validation, "validation"), next_iteration
        )

    requirements = _require_output(requirements, "requirements")
    architecture = _require_output(architecture, "architecture")
    technology = _require_output(technology, "technology")
    delivery = _require_output(delivery, "delivery")

    try:
        blueprint_md = render_markdown(requirements, architecture, technology, delivery, validation)
        blueprint_html = render_html(blueprint_md)
    except Exception as exc:
        raise BlueprintGenerationError(f"Report rendering failed: {exc}") from exc

    duration_seconds = time.monotonic() - started

    return BlueprintResponse(
        status="success",
        project_id=project_id or str(uuid.uuid4()),
        requirements=requirements,
        architecture=architecture,
        technology=technology,
        delivery=delivery,
        validation=validation,
        blueprint_md=blueprint_md,
        blueprint_html=blueprint_html,
        meta=BlueprintMeta(
            model=_resolve_model_name(llm, model_name),
            duration_seconds=duration_seconds,
            repair_iterations=validation.iterations,
        ),
    )
