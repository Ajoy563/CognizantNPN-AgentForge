"""Solution Architect CrewAI task.

Consumes the Business Analyst's RequirementsOutput as upstream context and
produces a structured result conforming to
ai.schemas.architecture.ArchitectureOutput.
"""

from typing import Any, Optional

from ai.schemas.architecture import ArchitectureOutput
from ai.schemas.requirements import RequirementsOutput

OUTPUT_SCHEMA = ArchitectureOutput

ARCHITECTURE_EXPECTED_OUTPUT = (
    "A single JSON object matching the ArchitectureOutput schema exactly, with "
    "these keys and no others: architecture_style (string), components (list of "
    "objects, each with name and responsibility), data_flow (list of strings), "
    "storage (list of strings), security (list of strings), scalability (list of "
    "strings), mvp_architecture (list of strings), future_evolution (list of "
    "strings). Every item must be concrete and specific to this architecture — no "
    "placeholders, no boilerplate, and no specific technology/framework/cloud-"
    "vendor product names."
)


def build_architecture_task(
    agent: Any,
    *,
    requirements: RequirementsOutput,
    expected_daily_traffic: int,
    delivery_timeline_months: int,
    country: str,
    repair_issues: Optional[tuple] = None,
) -> Any:
    """Construct the Solution Architect's task for one generation request.

    Requires the `crewai` package. `agent` should come from
    `ai.agents.solution_architect.build_solution_architect_agent`.
    `requirements` must be the Business Analyst's RequirementsOutput for this
    same request — it is the Solution Architect's upstream context.

    `repair_issues`: optional Consistency Validator issue text for this
    stage specifically (e.g. `RepairPlan.issues_by_owner["Solution Architect"]`
    from `ai.repair`), used only when this task is a targeted repair rerun.
    `None`/omitted (the default) reproduces the original, non-repair prompt
    exactly — normal initial generation is unaffected.
    """
    from crewai import Task  # local import: keeps this module importable/testable
    # even in environments where crewai itself cannot be installed.

    description = _build_description(
        requirements=requirements,
        expected_daily_traffic=expected_daily_traffic,
        delivery_timeline_months=delivery_timeline_months,
        country=country,
        repair_issues=repair_issues,
    )
    return Task(
        description=description,
        expected_output=ARCHITECTURE_EXPECTED_OUTPUT,
        agent=agent,
        output_pydantic=ArchitectureOutput,
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
            _bullets("Stakeholders", requirements.stakeholders),
            _bullets("Functional requirements", requirements.functional_requirements),
            _bullets(
                "Non-functional requirements", requirements.non_functional_requirements
            ),
            _bullets("MVP priorities", requirements.mvp_priorities),
            _bullets("Future scope", requirements.future_scope),
            _bullets("Assumptions", requirements.assumptions),
            _bullets("Constraints", requirements.constraints),
            _bullets("Business risks", requirements.risks),
            _bullets("Open clarifications", requirements.clarifications),
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
    expected_daily_traffic: int,
    delivery_timeline_months: int,
    country: str,
    repair_issues: Optional[tuple] = None,
) -> str:
    return (
        "Design a system architecture for the business requirements below, "
        "produced by the Business Analyst. Treat these requirements as ground "
        "truth — do not redefine the business problem, stakeholders, or MVP "
        "priorities. Do not select a specific technology stack, framework, "
        "database product, or cloud vendor. Do not produce a delivery timeline, "
        "team plan, cost estimate, or perform consistency validation — those "
        "belong to other specialists.\n\n"
        f"{_summarize_requirements(requirements)}\n\n"
        f"Expected daily traffic: {expected_daily_traffic}\n"
        f"Delivery timeline (months): {delivery_timeline_months}\n"
        f"Country where data will be hosted: {country}\n\n"
        "Produce:\n"
        "1. Architecture style (e.g. modular monolith, layered, event-driven) "
        "described conceptually, not tied to a specific product.\n"
        "2. Major components and, for each, its responsibility.\n"
        "3. Data flow between components, from client through to storage.\n"
        "4. Storage approach (e.g. relational store for transactional data, "
        "object store for files) described by role, not by vendor/product name.\n"
        "5. Security controls needed to satisfy the non-functional requirements "
        "and the data residency implied by the hosting country.\n"
        "6. Scalability approach appropriate for the expected daily traffic — do "
        "not over-engineer for load this system will not see.\n"
        "7. MVP architecture: the minimal version of this architecture that can "
        "be built within the delivery timeline while still satisfying the MVP "
        "priorities.\n"
        "8. Future evolution: how the architecture could grow if traffic, scope, "
        "or timeline constraints change later.\n\n"
        "Keep every item concrete and specific to this system. Do not repeat the "
        "requirements verbatim; synthesize them into an architecture."
    ) + _repair_context_section(repair_issues)
