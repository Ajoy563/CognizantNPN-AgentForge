"""Consistency Validator CrewAI task.

Consumes the Business Analyst's RequirementsOutput, the Solution
Architect's ArchitectureOutput, the Technology Advisor's
TechnologyOutput, and the Delivery Planner's DeliveryOutput as upstream
context, plus the original technology preference, cloud preference,
expected traffic, delivery timeline, hosting country, and the number of
repair iterations already attempted, and produces a structured result
conforming to ai.schemas.validation.ValidationOutput.
"""

from typing import Any, Literal

from ai.schemas.architecture import ArchitectureOutput
from ai.schemas.delivery import DeliveryOutput
from ai.schemas.requirements import RequirementsOutput
from ai.schemas.technology import TechnologyOutput
from ai.schemas.validation import ValidationOutput

TechPreference = Literal["opensource", "enterprise"]
CloudPreference = Literal["aws", "azure", "gcp", "none"]

MAX_REPAIR_ITERATIONS = 3

OUTPUT_SCHEMA = ValidationOutput

VALIDATION_CATEGORIES = (
    "A. Requirements <-> Architecture",
    "B. Architecture <-> Technology",
    "C. Technology <-> User Constraints",
    "D. Scope <-> Timeline",
    "E. Architecture/Technology <-> Scale",
    "F. Security consistency",
    "G. Delivery consistency",
    "H. Cost/Effort consistency",
)

VALIDATION_EXPECTED_OUTPUT = (
    "A single JSON object matching the ValidationOutput schema exactly, with "
    "these keys and no others: status ('PASS' or 'FAIL'), iterations "
    "(integer, 0-3), checks (list of objects, each with name, status ('PASS' "
    "or 'FAIL'), issue, owner), warnings (list of strings). status must be "
    "'PASS' only when no check has a blocking FAIL; otherwise it must be "
    "'FAIL'. For every check with status 'FAIL', issue must describe exactly "
    "what is inconsistent and owner must be exactly one of: 'Business "
    "Analyst', 'Solution Architect', 'Technology Advisor', 'Delivery "
    "Planner', or 'Cross-stage' when more than one stage shares the "
    "correction. For a check with status 'PASS', issue and owner should be "
    "omitted (null). Non-blocking concerns must be listed in warnings, never "
    "turned into a failing check. iterations must equal the number of repair "
    "iterations already attempted, given to you as input — never invented, "
    "and never above the maximum of 3. owner must be the stage that would "
    "actually have to change its own output to fix the problem, not simply "
    "the stage associated with the category name."
)


def build_validation_task(
    agent: Any,
    *,
    requirements: RequirementsOutput,
    architecture: ArchitectureOutput,
    technology: TechnologyOutput,
    delivery: DeliveryOutput,
    tech_preference: TechPreference,
    cloud_preference: CloudPreference,
    expected_daily_traffic: int,
    delivery_timeline_months: int,
    country: str,
    iterations: int = 0,
) -> Any:
    """Construct the Consistency Validator's task for one generation request.

    Requires the `crewai` package. `agent` should come from
    `ai.agents.consistency_validator.build_consistency_validator_agent`.
    `requirements`, `architecture`, `technology`, and `delivery` must be the
    four prior stages' structured outputs for this same request — they are
    the validator's upstream context. `iterations` is the number of repair
    iterations already attempted before this validation run (0 on the
    first run); the validator reports it back, it never performs a repair.
    """
    from crewai import Task  # local import: keeps this module importable/testable
    # even in environments where crewai itself cannot be installed.

    description = _build_description(
        requirements=requirements,
        architecture=architecture,
        technology=technology,
        delivery=delivery,
        tech_preference=tech_preference,
        cloud_preference=cloud_preference,
        expected_daily_traffic=expected_daily_traffic,
        delivery_timeline_months=delivery_timeline_months,
        country=country,
        iterations=iterations,
    )
    return Task(
        description=description,
        expected_output=VALIDATION_EXPECTED_OUTPUT,
        agent=agent,
        output_pydantic=ValidationOutput,
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
            "Technology Advisor's infrastructure/service cost estimate:",
            f"  - Infrastructure (monthly): "
            f"{technology.cost_estimate.infrastructure_monthly}",
            f"  - Infrastructure/service setup (one-time): "
            f"{technology.cost_estimate.implementation}",
        ]
    )


def _summarize_delivery(delivery: DeliveryOutput) -> str:
    team_roles_rendered = "\n".join(
        f"  - {role.role} x{role.count}" for role in delivery.team_roles
    )
    timeline_rendered = "\n".join(
        f"  - {phase.phase} ({phase.duration}): {', '.join(phase.deliverables)}"
        for phase in delivery.timeline
    )
    risks_rendered = "\n".join(
        f"  - {risk.risk} (impact: {risk.impact}; mitigation: {risk.mitigation})"
        for risk in delivery.risks
    )
    return "\n".join(
        [
            _bullets("Workstreams", delivery.workstreams),
            f"Team roles:\n{team_roles_rendered}",
            f"Timeline:\n{timeline_rendered}",
            _bullets("Dependencies", delivery.dependencies),
            _bullets("Testing strategy", delivery.testing_strategy),
            _bullets("Deployment strategy", delivery.deployment_strategy),
            f"Delivery risks:\n{risks_rendered}",
            f"Effort/complexity: {delivery.effort_complexity}",
            "Delivery Planner's implementation/team cost estimate (separate "
            "from the Technology Advisor's infrastructure cost above):",
            f"  - Estimated effort: {delivery.cost_estimate.estimated_effort}",
            f"  - Estimated team cost: "
            f"{delivery.cost_estimate.estimated_team_cost}",
        ]
    )


def _build_description(
    *,
    requirements: RequirementsOutput,
    architecture: ArchitectureOutput,
    technology: TechnologyOutput,
    delivery: DeliveryOutput,
    tech_preference: TechPreference,
    cloud_preference: CloudPreference,
    expected_daily_traffic: int,
    delivery_timeline_months: int,
    country: str,
    iterations: int,
) -> str:
    return (
        "Validate consistency across the four structured outputs below and "
        "the original constraints. Check, at minimum:\n\n"
        "A. Requirements <-> Architecture: the architecture addresses the "
        "important MVP requirements; major business requirements are not "
        "ignored. Ownership: if a requirement is missing, ambiguous, or "
        "incorrect, the owner is Business Analyst; if the requirement is "
        "already clear but the architecture does not explicitly address "
        "it, the owner is Solution Architect; if both genuinely need "
        "coordinated correction, the owner is Cross-stage.\n"
        "B. Architecture <-> Technology: the selected technologies support "
        "the proposed architecture; storage/security/scalability choices "
        "are compatible. Ownership: if the architecture needs correction, "
        "the owner is Solution Architect; if the technology choice needs "
        "correction, the owner is Technology Advisor; if both sides need "
        "coordinated correction, the owner is Cross-stage.\n"
        "C. Technology <-> User Constraints: the technology preference is "
        "respected; the cloud preference is respected; the country/data-"
        "hosting requirement is respected; the expected traffic/scale is "
        "reasonably supported. Ownership: any technology, cloud, or "
        "hosting choice that violates a stated constraint is owned by "
        "Technology Advisor.\n"
        "D. Scope <-> Timeline: the MVP scope is realistic for the stated "
        "delivery timeline. Ownership: if the scope or work plan must be "
        "reduced or the delivery plan changed, the owner is Delivery "
        "Planner; if the business scope itself is incorrect or unclear, "
        "the owner is Business Analyst.\n"
        "E. Architecture/Technology <-> Scale: the architecture and "
        "technologies are appropriate for the expected daily traffic. "
        "Ownership: an architecture scalability problem is owned by "
        "Solution Architect; a technology scaling choice problem is owned "
        "by Technology Advisor; if both need correction, the owner is "
        "Cross-stage.\n"
        "F. Security consistency: security requirements are reflected in "
        "the architecture and technology choices. Ownership: an "
        "architecture/security design problem is owned by Solution "
        "Architect; a technology/security selection problem is owned by "
        "Technology Advisor; if both, the owner is Cross-stage.\n"
        "G. Delivery consistency: workstreams and milestones correspond to "
        "the proposed solution; team roles are sufficient for the delivery "
        "plan. Ownership: any workstreams/team/timeline/deployment/testing "
        "problem is owned by Delivery Planner.\n"
        "H. Cost/Effort consistency: the Technology Advisor's "
        "infrastructure/service cost is consistent with the selected "
        "technologies; the Delivery Planner's implementation/team cost is "
        "clearly separate from it; effort, team size, and timeline are not "
        "obviously contradictory. Ownership: an infrastructure/service "
        "cost or technology cost problem is owned by Technology Advisor; "
        "an implementation/team effort or team cost problem is owned by "
        "Delivery Planner; if both, the owner is Cross-stage.\n\n"
        "In every category, choose the owner based on which stage would "
        "actually have to change its own output to fix the problem — never "
        "merely based on which category the check falls under. A "
        "requirement that is already clear but simply not yet reflected in "
        "a downstream stage's output is that downstream stage's issue, not "
        "the Business Analyst's.\n\n"
        "Do not redesign the architecture, choose replacement technologies, "
        "rewrite requirements, or create a delivery plan yourself, and do "
        "not modify any of the four outputs below directly — only report on "
        "them. Do not make external web searches or call Serper.\n\n"
        f"{_summarize_requirements(requirements)}\n\n"
        f"{_summarize_architecture(architecture)}\n\n"
        f"{_summarize_technology(technology)}\n\n"
        f"{_summarize_delivery(delivery)}\n\n"
        f"Technology preference: {tech_preference}\n"
        f"Cloud preference: {cloud_preference}\n"
        f"Expected daily traffic: {expected_daily_traffic}\n"
        f"Delivery timeline (months): {delivery_timeline_months}\n"
        f"Country where data will be hosted: {country}\n"
        f"Repair iterations already attempted: {iterations} (maximum "
        f"allowed: {MAX_REPAIR_ITERATIONS})\n\n"
        "For every check, record its name, a status of 'PASS' or 'FAIL', "
        "and, on 'FAIL', an issue describing exactly what is inconsistent "
        "and an owner — 'Business Analyst', 'Solution Architect', "
        "'Technology Advisor', 'Delivery Planner', or 'Cross-stage' — "
        "naming the stage responsible for the correction, with the issue "
        "text also explaining why it matters. Reserve FAIL for a "
        "meaningful, blocking inconsistency; put anything minor or "
        "stylistic in warnings instead. Set the overall status to 'PASS' "
        "only if no check fails, otherwise 'FAIL'. Report iterations "
        "exactly as given above — you do not execute the repair, you only "
        "report findings for a separate repair loop to act on."
    )
