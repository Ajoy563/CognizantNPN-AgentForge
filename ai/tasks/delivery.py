"""Delivery Planner CrewAI task.

Consumes the Business Analyst's RequirementsOutput, the Solution
Architect's ArchitectureOutput, and the Technology Advisor's
TechnologyOutput as upstream context, plus the original delivery
timeline, and produces a structured result conforming to
ai.schemas.delivery.DeliveryOutput.
"""

from typing import Any, Optional

from ai.schemas.architecture import ArchitectureOutput
from ai.schemas.delivery import DeliveryOutput
from ai.schemas.requirements import RequirementsOutput
from ai.schemas.technology import TechnologyOutput

OUTPUT_SCHEMA = DeliveryOutput

DELIVERY_EXPECTED_OUTPUT = (
    "A single JSON object matching the DeliveryOutput schema exactly, with "
    "these keys and no others: workstreams (list of strings), team_roles "
    "(list of objects, each with role and count), timeline (list of objects, "
    "each with phase, duration, deliverables), dependencies (list of "
    "strings), testing_strategy (list of strings), deployment_strategy (list "
    "of strings), risks (list of objects, each with risk, impact, "
    "mitigation), effort_complexity (string), cost_estimate (object with "
    "estimated_effort, estimated_team_cost, assumptions), future_evolution "
    "(list of strings). cost_estimate.estimated_effort and "
    "cost_estimate.estimated_team_cost must each be an indicative range or a "
    "clearly qualified statement such as 'Not enough information for a "
    "reliable estimate' — never a single precise number presented as fact. "
    "This cost_estimate covers only implementation/team cost — never the "
    "infrastructure/service cost, which the Technology Advisor already "
    "provided. Every item must be concrete and specific — no placeholders, "
    "no boilerplate."
)


def build_delivery_task(
    agent: Any,
    *,
    requirements: RequirementsOutput,
    architecture: ArchitectureOutput,
    technology: TechnologyOutput,
    delivery_timeline_months: int,
    repair_issues: Optional[tuple] = None,
) -> Any:
    """Construct the Delivery Planner's task for one generation request.

    Requires the `crewai` package. `agent` should come from
    `ai.agents.delivery_planner.build_delivery_planner_agent`.
    `requirements`, `architecture`, and `technology` must be the Business
    Analyst's, Solution Architect's, and Technology Advisor's structured
    outputs for this same request — they are the Delivery Planner's
    upstream context.

    `repair_issues`: optional Consistency Validator issue text for this
    stage specifically (e.g. `RepairPlan.issues_by_owner["Delivery Planner"]`
    from `ai.repair`), used only when this task is a targeted repair rerun.
    `None`/omitted (the default) reproduces the original, non-repair prompt
    exactly — normal initial generation is unaffected.
    """
    from crewai import Task  # local import: keeps this module importable/testable
    # even in environments where crewai itself cannot be installed.

    description = _build_description(
        requirements=requirements,
        architecture=architecture,
        technology=technology,
        delivery_timeline_months=delivery_timeline_months,
        repair_issues=repair_issues,
    )
    return Task(
        description=description,
        expected_output=DELIVERY_EXPECTED_OUTPUT,
        agent=agent,
        output_pydantic=DeliveryOutput,
    )


def _bullets(label: str, items: list[str]) -> str:
    if not items:
        return f"{label}: (none)"
    rendered = "\n".join(f"  - {item}" for item in items)
    return f"{label}:\n{rendered}"


def _summarize_requirements(requirements: RequirementsOutput) -> str:
    return "\n".join(
        [
            f"Problem statement: {requirements.problem}",
            _bullets("Functional requirements", requirements.functional_requirements),
            _bullets(
                "Non-functional requirements", requirements.non_functional_requirements
            ),
            _bullets("MVP priorities", requirements.mvp_priorities),
            _bullets("Constraints", requirements.constraints),
            _bullets("Business risks", requirements.risks),
        ]
    )


def _summarize_architecture(architecture: ArchitectureOutput) -> str:
    components_rendered = "\n".join(
        f"  - {component.name}: {component.responsibility}"
        for component in architecture.components
    )
    return "\n".join(
        [
            f"Architecture style: {architecture.architecture_style}",
            f"Components:\n{components_rendered}",
            _bullets("Storage approach", architecture.storage),
            _bullets("Security controls", architecture.security),
            _bullets("Scalability approach", architecture.scalability),
            _bullets("MVP architecture", architecture.mvp_architecture),
        ]
    )


def _summarize_technology(technology: TechnologyOutput) -> str:
    recommendations_rendered = "\n".join(
        f"  - {rec.component}: {rec.recommended} ({rec.reason})"
        for rec in technology.recommendations
    )
    return "\n".join(
        [
            f"Technology recommendations:\n{recommendations_rendered}",
            f"Cloud fit: {technology.cloud_fit}",
            f"Open-source fit: {technology.open_source_fit}",
            f"Lock-in considerations: {technology.lock_in_considerations}",
            "Technology Advisor's infrastructure/service cost estimate "
            "(already provided — do not duplicate or replace this):",
            f"  - Infrastructure (monthly): "
            f"{technology.cost_estimate.infrastructure_monthly}",
            f"  - Infrastructure/service setup (one-time): "
            f"{technology.cost_estimate.implementation}",
        ]
    )


def _repair_context_section(repair_issues: Optional[tuple]) -> str:
    if not repair_issues:
        return ""
    rendered = "\n".join(f"  - {issue}" for issue in repair_issues)
    return (
        "\n\nThis is a targeted repair. The Consistency Validator found the "
        "following issue(s) with your previous output for this stage — fix "
        "them specifically, while keeping everything else that was already "
        "correct:\n"
        f"{rendered}"
    )


def _build_description(
    *,
    requirements: RequirementsOutput,
    architecture: ArchitectureOutput,
    technology: TechnologyOutput,
    delivery_timeline_months: int,
    repair_issues: Optional[tuple] = None,
) -> str:
    return (
        "Turn the requirements, architecture, and technology recommendations "
        "below into an executable delivery plan. Treat all three as ground "
        "truth — do not redefine the business requirements, do not redesign "
        "the architecture, and do not choose a different technology stack. "
        "Do not perform consistency validation — that belongs to another "
        "specialist.\n\n"
        f"{_summarize_requirements(requirements)}\n\n"
        f"{_summarize_architecture(architecture)}\n\n"
        f"{_summarize_technology(technology)}\n\n"
        f"Delivery timeline (months): {delivery_timeline_months}\n\n"
        "Produce:\n"
        "1. Implementation workstreams that cover the components and MVP "
        "priorities above.\n"
        "2. Team roles and counts, sized to the scope and complexity — a "
        "plausible team for a project of this size and timeline.\n"
        "3. A timeline of phases and milestones that fits inside the stated "
        "delivery timeline, each with its deliverables.\n"
        "4. Dependencies and prerequisites between workstreams or on "
        "external factors.\n"
        "5. A testing strategy grounded in the actual architecture and "
        "technology stack above.\n"
        "6. A deployment/release strategy grounded in the actual "
        "architecture and technology stack above.\n"
        "7. Delivery risks, each with a concrete mitigation.\n"
        "8. An effort and complexity assessment for the project.\n"
        "9. An indicative implementation/team cost estimate — a range or a "
        "clearly qualified statement, never false precision — with the "
        "assumptions behind it. This is implementation/team cost only: do "
        "not duplicate or replace the Technology Advisor's infrastructure/"
        "service cost estimate above, which is already provided.\n"
        "10. Future evolution: how the delivery plan could extend if scope "
        "or timeline constraints change later.\n\n"
        "The full plan — every workstream, phase, and milestone — must fit "
        "inside the stated delivery timeline. Keep every item concrete and "
        "specific to this project — no placeholders, no boilerplate."
    ) + _repair_context_section(repair_issues)
