"""CrewAI orchestration layer for the SolutionForge pipeline.

Drives Business Analyst -> Solution Architect -> Technology Advisor ->
Delivery Planner -> Consistency Validator using the existing
build_*_agent/build_*_task pairs and each stage's real Pydantic output —
never CrewAI's own free-form inter-task context passing, since a
structured output already exists at every hand-off. Each stage runs as
its own single-agent, single-task Crew(process=Process.sequential); the
five stages are then driven sequentially at the Python level, because
each task builder needs the previous stage's actual parsed output as a
Python object before it can build its prompt.

This module only executes stages; it never decides which stages need to
rerun — that decision belongs entirely to ai.repair.determine_repair_plan.
The Stage -> executor mapping here is what ai.repair's RepairPlan.stages
gets applied against by a future service layer.
"""

from dataclasses import dataclass, replace
from typing import Any, Literal, Optional

from ai.agents.business_analyst import build_business_analyst_agent
from ai.agents.consistency_validator import build_consistency_validator_agent
from ai.agents.delivery_planner import build_delivery_planner_agent
from ai.agents.solution_architect import build_solution_architect_agent
from ai.agents.technology_advisor import build_technology_advisor_agent
from ai.repair import Stage
from ai.schemas.architecture import ArchitectureOutput
from ai.schemas.delivery import DeliveryOutput
from ai.schemas.requirements import RequirementsOutput
from ai.schemas.technology import TechnologyOutput
from ai.schemas.validation import ValidationOutput
from ai.tasks.architecture import build_architecture_task
from ai.tasks.business_analysis import build_business_analysis_task
from ai.tasks.delivery import build_delivery_task
from ai.tasks.technology import build_technology_task
from ai.tasks.validation import build_validation_task

TechPreference = Literal["opensource", "enterprise"]
CloudPreference = Literal["aws", "azure", "gcp", "none"]

INITIAL_PIPELINE_ORDER: tuple = (
    Stage.BUSINESS_ANALYST,
    Stage.SOLUTION_ARCHITECT,
    Stage.TECHNOLOGY_ADVISOR,
    Stage.DELIVERY_PLANNER,
    Stage.VALIDATOR,
)


class StageExecutionError(RuntimeError):
    """Raised when a stage's CrewAI execution fails, or returns no usable
    structured output. Always raised with the original exception chained
    via `from` — CrewAI errors are never swallowed."""


@dataclass(frozen=True)
class StageContext:
    """Everything a stage executor might need: the original request
    constraints, the current repair-iteration count, an injectable LLM,
    and whichever upstream structured outputs have been produced so far.
    Immutable — each executor returns a new StageContext via `replace()`.
    """

    business_idea: str
    tech_preference: TechPreference
    cloud_preference: CloudPreference
    expected_daily_traffic: int
    delivery_timeline_months: int
    country: str
    iterations: int = 0
    llm: Optional[Any] = None
    requirements: Optional[RequirementsOutput] = None
    architecture: Optional[ArchitectureOutput] = None
    technology: Optional[TechnologyOutput] = None
    delivery: Optional[DeliveryOutput] = None
    validation: Optional[ValidationOutput] = None
    # Consistency Validator issue text for whichever single stage is about to
    # run next (e.g. RepairPlan.issues_by_owner[owner] from ai.repair). Only
    # that one stage's executor consumes it, then clears it — it must never
    # leak into a downstream stage's task. None during normal initial
    # generation.
    repair_issues: Optional[tuple] = None


@dataclass(frozen=True)
class PipelineResult:
    """The five structured outputs of one full pipeline run."""

    requirements: RequirementsOutput
    architecture: ArchitectureOutput
    technology: TechnologyOutput
    delivery: DeliveryOutput
    validation: ValidationOutput


# Requirement 5: the Crew layer must not duplicate agent/task definitions —
# these mappings only ever reference the existing build_*_agent/build_*_task
# functions from ai/agents and ai/tasks.
STAGE_AGENT_BUILDERS: dict = {
    Stage.BUSINESS_ANALYST: build_business_analyst_agent,
    Stage.SOLUTION_ARCHITECT: build_solution_architect_agent,
    Stage.TECHNOLOGY_ADVISOR: build_technology_advisor_agent,
    Stage.DELIVERY_PLANNER: build_delivery_planner_agent,
    Stage.VALIDATOR: build_consistency_validator_agent,
}

STAGE_TASK_BUILDERS: dict = {
    Stage.BUSINESS_ANALYST: build_business_analysis_task,
    Stage.SOLUTION_ARCHITECT: build_architecture_task,
    Stage.TECHNOLOGY_ADVISOR: build_technology_task,
    Stage.DELIVERY_PLANNER: build_delivery_task,
    Stage.VALIDATOR: build_validation_task,
}

STAGE_OUTPUT_SCHEMAS: dict = {
    Stage.BUSINESS_ANALYST: RequirementsOutput,
    Stage.SOLUTION_ARCHITECT: ArchitectureOutput,
    Stage.TECHNOLOGY_ADVISOR: TechnologyOutput,
    Stage.DELIVERY_PLANNER: DeliveryOutput,
    Stage.VALIDATOR: ValidationOutput,
}


def _require(value: Optional[Any], name: str, stage: Stage) -> Any:
    if value is None:
        raise StageExecutionError(
            f"{stage.value} stage requires '{name}' in the context, but it was "
            "not provided."
        )
    return value


def _run_stage_crew(agent: Any, task: Any, schema: type, *, stage: Stage) -> Any:
    """Run a single agent/task pair as its own sequential Crew and return the
    parsed structured output. Requires the `crewai` package."""
    from crewai import Crew, Process  # local import: keeps this module importable/
    # testable even in environments where crewai itself cannot be installed.

    crew = Crew(agents=[agent], tasks=[task], process=Process.sequential)
    try:
        crew_output = crew.kickoff()
    except Exception as exc:  # CrewAI/LLM errors are surfaced, never swallowed.
        raise StageExecutionError(f"{stage.value} stage failed: {exc}") from exc

    return _extract_structured_output(crew_output, schema, stage=stage)


def _extract_structured_output(crew_output: Any, schema: type, *, stage: Stage) -> Any:
    pydantic_result = getattr(crew_output, "pydantic", None)
    if isinstance(pydantic_result, schema):
        return pydantic_result

    tasks_output = getattr(crew_output, "tasks_output", None) or []
    if tasks_output:
        candidate = getattr(tasks_output[-1], "pydantic", None)
        if isinstance(candidate, schema):
            return candidate

    raw = getattr(crew_output, "raw", None) or str(crew_output)
    try:
        return schema.model_validate_json(raw)
    except Exception as exc:
        raise StageExecutionError(
            f"{stage.value} stage did not return a structured {schema.__name__}: {exc}"
        ) from exc


def execute_business_analyst_stage(context: StageContext) -> StageContext:
    agent = build_business_analyst_agent(context.llm)
    task = build_business_analysis_task(
        agent,
        business_idea=context.business_idea,
        tech_preference=context.tech_preference,
        cloud_preference=context.cloud_preference,
        expected_daily_traffic=context.expected_daily_traffic,
        delivery_timeline_months=context.delivery_timeline_months,
        country=context.country,
        repair_issues=context.repair_issues,
    )
    requirements = _run_stage_crew(
        agent, task, RequirementsOutput, stage=Stage.BUSINESS_ANALYST
    )
    # A new requirements output invalidates every downstream stage's output —
    # never silently reuse a stale architecture/technology/delivery/validation.
    # repair_issues is consumed here; it must not leak to the next stage.
    return replace(
        context,
        requirements=requirements,
        architecture=None,
        technology=None,
        delivery=None,
        validation=None,
        repair_issues=None,
    )


def execute_solution_architect_stage(context: StageContext) -> StageContext:
    requirements = _require(context.requirements, "requirements", Stage.SOLUTION_ARCHITECT)
    agent = build_solution_architect_agent(context.llm)
    task = build_architecture_task(
        agent,
        requirements=requirements,
        expected_daily_traffic=context.expected_daily_traffic,
        delivery_timeline_months=context.delivery_timeline_months,
        country=context.country,
        repair_issues=context.repair_issues,
    )
    architecture = _run_stage_crew(
        agent, task, ArchitectureOutput, stage=Stage.SOLUTION_ARCHITECT
    )
    return replace(
        context,
        architecture=architecture,
        technology=None,
        delivery=None,
        validation=None,
        repair_issues=None,
    )


def execute_technology_advisor_stage(context: StageContext) -> StageContext:
    requirements = _require(context.requirements, "requirements", Stage.TECHNOLOGY_ADVISOR)
    architecture = _require(context.architecture, "architecture", Stage.TECHNOLOGY_ADVISOR)
    agent = build_technology_advisor_agent(context.llm)
    task = build_technology_task(
        agent,
        requirements=requirements,
        architecture=architecture,
        tech_preference=context.tech_preference,
        cloud_preference=context.cloud_preference,
        expected_daily_traffic=context.expected_daily_traffic,
        delivery_timeline_months=context.delivery_timeline_months,
        country=context.country,
        repair_issues=context.repair_issues,
    )
    technology = _run_stage_crew(
        agent, task, TechnologyOutput, stage=Stage.TECHNOLOGY_ADVISOR
    )
    return replace(
        context,
        technology=technology,
        delivery=None,
        validation=None,
        repair_issues=None,
    )


def execute_delivery_planner_stage(context: StageContext) -> StageContext:
    requirements = _require(context.requirements, "requirements", Stage.DELIVERY_PLANNER)
    architecture = _require(context.architecture, "architecture", Stage.DELIVERY_PLANNER)
    technology = _require(context.technology, "technology", Stage.DELIVERY_PLANNER)
    agent = build_delivery_planner_agent(context.llm)
    task = build_delivery_task(
        agent,
        requirements=requirements,
        architecture=architecture,
        technology=technology,
        delivery_timeline_months=context.delivery_timeline_months,
        repair_issues=context.repair_issues,
    )
    delivery = _run_stage_crew(agent, task, DeliveryOutput, stage=Stage.DELIVERY_PLANNER)
    return replace(context, delivery=delivery, validation=None, repair_issues=None)


def execute_validator_stage(context: StageContext) -> StageContext:
    requirements = _require(context.requirements, "requirements", Stage.VALIDATOR)
    architecture = _require(context.architecture, "architecture", Stage.VALIDATOR)
    technology = _require(context.technology, "technology", Stage.VALIDATOR)
    delivery = _require(context.delivery, "delivery", Stage.VALIDATOR)
    agent = build_consistency_validator_agent(context.llm)
    task = build_validation_task(
        agent,
        requirements=requirements,
        architecture=architecture,
        technology=technology,
        delivery=delivery,
        tech_preference=context.tech_preference,
        cloud_preference=context.cloud_preference,
        expected_daily_traffic=context.expected_daily_traffic,
        delivery_timeline_months=context.delivery_timeline_months,
        country=context.country,
        iterations=context.iterations,
    )
    validation = _run_stage_crew(agent, task, ValidationOutput, stage=Stage.VALIDATOR)
    # The Validator never receives repair_issues (it produces issues, it does
    # not consume them) — clear defensively so nothing lingers past this run.
    return replace(context, validation=validation, repair_issues=None)


STAGE_EXECUTORS: dict = {
    Stage.BUSINESS_ANALYST: execute_business_analyst_stage,
    Stage.SOLUTION_ARCHITECT: execute_solution_architect_stage,
    Stage.TECHNOLOGY_ADVISOR: execute_technology_advisor_stage,
    Stage.DELIVERY_PLANNER: execute_delivery_planner_stage,
    Stage.VALIDATOR: execute_validator_stage,
}


def default_executors() -> dict:
    """A fresh copy of the default Stage -> executor mapping. Callers
    (tests especially) mutate their own copy to inject mocks, rather than
    the shared STAGE_EXECUTORS mapping."""
    return dict(STAGE_EXECUTORS)


def run_stage(
    stage: Stage,
    context: StageContext,
    *,
    executors: Optional[dict] = None,
) -> StageContext:
    """Run exactly one stage against `context` and return the updated
    context. Does not decide which stage to run — the caller (normally
    ai.repair's RepairPlan) already decided that."""
    executors = executors if executors is not None else STAGE_EXECUTORS
    if stage not in executors:
        raise StageExecutionError(f"No executor registered for stage {stage!r}.")
    return executors[stage](context)


def run_stages(
    stages: tuple,
    context: StageContext,
    *,
    executors: Optional[dict] = None,
) -> StageContext:
    """Run an already-decided ordered sequence of stages — e.g.
    RepairPlan.stages from ai.repair.determine_repair_plan — against
    `context`, threading the updated context through each one in order.
    This function makes no decision about which stages to run."""
    for stage in stages:
        context = run_stage(stage, context, executors=executors)
    return context


def run_initial_pipeline(
    *,
    business_idea: str,
    tech_preference: TechPreference,
    cloud_preference: CloudPreference,
    expected_daily_traffic: int,
    delivery_timeline_months: int,
    country: str,
    llm: Optional[Any] = None,
    executors: Optional[dict] = None,
) -> PipelineResult:
    """Run Business Analyst -> Solution Architect -> Technology Advisor ->
    Delivery Planner -> Consistency Validator once, with iterations=0, and
    return all five structured outputs.

    Conceptually `run_initial_pipeline(request)`: takes the six
    GenerateRequest fields directly as keyword arguments, since no
    ai.schemas.request module exists yet. A future service layer calls
    this as `run_initial_pipeline(business_idea=request.business_idea, ...)`.
    """
    context = StageContext(
        business_idea=business_idea,
        tech_preference=tech_preference,
        cloud_preference=cloud_preference,
        expected_daily_traffic=expected_daily_traffic,
        delivery_timeline_months=delivery_timeline_months,
        country=country,
        iterations=0,
        llm=llm,
    )
    context = run_stages(INITIAL_PIPELINE_ORDER, context, executors=executors)
    return PipelineResult(
        requirements=_require(context.requirements, "requirements", Stage.VALIDATOR),
        architecture=_require(context.architecture, "architecture", Stage.VALIDATOR),
        technology=_require(context.technology, "technology", Stage.VALIDATOR),
        delivery=_require(context.delivery, "delivery", Stage.VALIDATOR),
        validation=_require(context.validation, "validation", Stage.VALIDATOR),
    )
