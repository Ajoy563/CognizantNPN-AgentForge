"""Delivery Planner CrewAI task.

Consumes the Business Analyst's RequirementsOutput, the Solution
Architect's ArchitectureOutput, and the Technology Advisor's
TechnologyOutput as upstream context, plus the original delivery
timeline, and produces a structured, traceable result conforming to
ai.schemas.delivery.DeliveryOutput.
"""

from typing import Any

from ai.schemas.architecture import ArchitectureOutput
from ai.schemas.delivery import DeliveryOutput
from ai.schemas.requirements import RequirementsOutput
from ai.schemas.technology import TechnologyOutput

OUTPUT_SCHEMA = DeliveryOutput

DELIVERY_EXPECTED_OUTPUT = (
    "A single JSON object matching the DeliveryOutput schema exactly, with "
    "these keys and no others: workstreams (list of objects: id, name, "
    "purpose, activities, dependencies, deliverable, addresses, effort), "
    "milestones (list of strings), dependencies (list "
    "of strings), team_roles (list of objects: role, count), timeline "
    "(list of objects: phase, duration, milestone, deliverables), "
    "testing_strategy (list of strings), integration_testing (list of "
    "strings), uat_strategy (list of strings), deployment_strategy (list "
    "of strings), ci_cd (list of strings), monitoring (list of strings), "
    "rollback_strategy (list of strings), risks (list of objects: risk, "
    "impact, mitigation), effort_complexity (string), cost_estimate "
    "(object with estimated_effort, estimated_team_cost, assumptions), "
    "future_evolution (list of strings). Every workstream's id must be "
    "TASK-001, TASK-002, ... unique, never reused, with a non-empty "
    "`addresses` list of real requirement and/or component ids (REQ-xxx / "
    "ARCH-xxx) from the input — never invented. Every workstream's "
    "purpose and deliverable must be non-empty, and `activities` must "
    "list its major concrete pieces of work. `risks` must contain 4 to 6 "
    "entries, each with a real impact and a specific mitigation. "
    "cost_estimate."
    "estimated_effort and cost_estimate.estimated_team_cost must each be "
    "an indicative range or a clearly qualified statement such as 'Not "
    "enough information for a reliable estimate' — never a single "
    "precise number presented as fact. This cost_estimate covers only "
    "implementation/team cost — never the infrastructure/service cost, "
    "which the Technology Advisor already provided. The total effort "
    "implied by workstreams and timeline must be realistic for the team "
    "size in team_roles — never claim more scope than the team and "
    "timeline can plausibly deliver. Every item must be concrete and "
    "specific — no placeholders, no boilerplate."
)


def build_delivery_task(
    agent: Any,
    *,
    requirements: RequirementsOutput,
    architecture: ArchitectureOutput,
    technology: TechnologyOutput,
    delivery_timeline_months: int,
) -> Any:
    """Construct the Delivery Planner's task for one generation request.

    Requires the `crewai` package. `agent` should come from
    `ai.agents.delivery_planner.build_delivery_planner_agent`.
    `requirements`, `architecture`, and `technology` must be the Business
    Analyst's, Solution Architect's, and Technology Advisor's structured
    outputs for this same request — they are the Delivery Planner's
    upstream context.
    """
    from crewai import Task  # local import: keeps this module importable/testable
    # even in environments where crewai itself cannot be installed.

    description = _build_description(
        requirements=requirements,
        architecture=architecture,
        technology=technology,
        delivery_timeline_months=delivery_timeline_months,
    )
    return Task(
        description=description,
        expected_output=DELIVERY_EXPECTED_OUTPUT,
        agent=agent,
        output_pydantic=DeliveryOutput,
    )


def _summarize_requirements(requirements: RequirementsOutput) -> str:
    requirements_rendered = "\n".join(
        f"  - {req.id} [{req.priority}]: {req.text}"
        for req in requirements.requirements
    )
    return "\n".join(
        [
            f"Problem statement: {requirements.problem}",
            f"Requirements:\n{requirements_rendered}",
            f"MVP requirement ids: {', '.join(requirements.mvp_requirement_ids)}",
        ]
    )


def _summarize_architecture(architecture: ArchitectureOutput) -> str:
    components_rendered = "\n".join(
        f"  - {c.id}: {c.name} — {c.responsibility}" for c in architecture.components
    )
    return "\n".join(
        [
            f"Architecture style: {architecture.architecture_style}",
            f"Components:\n{components_rendered}",
        ]
    )


def _summarize_technology(technology: TechnologyOutput) -> str:
    decisions_rendered = "\n".join(
        f"  - {d.id}: {d.technology} ({d.reason}) [supports: {', '.join(d.supports)}]"
        for d in technology.decisions
    )
    return "\n".join(
        [
            f"Technology decisions:\n{decisions_rendered}",
            "Technology Advisor's infrastructure/service cost estimate "
            "(already provided — do not duplicate or replace this):",
            f"  - Infrastructure (monthly): "
            f"{technology.cost_estimate.infrastructure_monthly}",
            f"  - Infrastructure/service setup (one-time): "
            f"{technology.cost_estimate.implementation}",
        ]
    )


def _build_description(
    *,
    requirements: RequirementsOutput,
    architecture: ArchitectureOutput,
    technology: TechnologyOutput,
    delivery_timeline_months: int,
) -> str:
    return (
        "Turn the requirements, architecture, and technology decisions "
        "below into an executable, traceable delivery plan. Treat all "
        "three as ground truth — do not redefine the business "
        "requirements, do not redesign the architecture, and do not "
        "choose a different technology stack.\n\n"
        f"{_summarize_requirements(requirements)}\n\n"
        f"{_summarize_architecture(architecture)}\n\n"
        f"{_summarize_technology(technology)}\n\n"
        f"Delivery timeline (months): {delivery_timeline_months}\n\n"
        "Produce:\n"
        "1. Implementation workstreams. For each one give: purpose (why "
        "this workstream exists), activities (its major concrete pieces "
        "of work), dependencies (what must be in place before it can "
        "start — name other TASK ids where that is what you mean, or "
        "'None' when it can start immediately), deliverable (the "
        "tangible output or milestone it produces), effort (a realistic "
        "estimate), and an `addresses` list naming the requirement "
        "and/or component ids it covers. Plan "
        "the MVP that can actually be built in the stated timeline — "
        "not every capability the system could eventually have. Leave "
        "post-MVP capabilities to future_evolution instead of giving "
        "them workstreams.\n"
        "2. Milestones, dependencies, and team roles/counts sized to the "
        "scope and complexity — a plausible team for a project of this "
        "size and timeline. The total effort your workstreams imply must "
        "be realistic for that team size within the stated timeline.\n"
        "3. A timeline of phases, each with a duration, a concrete "
        "milestone, and its deliverables, fitting inside the stated "
        "delivery timeline.\n"
        "4. A real testing strategy: unit testing, integration testing, "
        "and a UAT strategy as separate, concrete concerns.\n"
        "5. Deployment strategy, CI/CD, monitoring, and a rollback "
        "strategy — grounded in the actual architecture and technology "
        "stack above.\n"
        "6. Between 4 and 6 delivery risks that genuinely threaten THIS "
        "project, each with its real impact and a concrete, specific "
        "mitigation — no generic 'communicate regularly' filler, and an "
        "effort/complexity assessment.\n"
        "7. An indicative implementation/team cost estimate — a range "
        "or a clearly qualified statement, never false precision — with "
        "the assumptions behind it. This is implementation/team cost "
        "only: do not duplicate or replace the Technology Advisor's "
        "infrastructure/service cost estimate above.\n"
        "8. Future evolution: how the delivery plan could extend if "
        "scope or timeline constraints change later.\n\n"
        "The full plan — every workstream, phase, and milestone — must "
        "fit inside the stated delivery timeline and be realistic for "
        "the team you defined. Keep every item concrete and specific to "
        "this project — no placeholders, no boilerplate."
    )
