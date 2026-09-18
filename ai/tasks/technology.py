"""Technology Advisor CrewAI task.

Consumes the Business Analyst's RequirementsOutput and the Solution
Architect's ArchitectureOutput as upstream context, plus the original
technology preference, cloud preference, expected traffic, delivery
timeline, and hosting country, and produces a structured result
conforming to ai.schemas.technology.TechnologyOutput.
"""

from typing import Any, Literal, Optional

from ai.schemas.architecture import ArchitectureOutput
from ai.schemas.requirements import RequirementsOutput
from ai.schemas.technology import TechnologyOutput

TechPreference = Literal["opensource", "enterprise"]
CloudPreference = Literal["aws", "azure", "gcp", "none"]

OUTPUT_SCHEMA = TechnologyOutput

TECHNOLOGY_EXPECTED_OUTPUT = (
    "A single JSON object matching the TechnologyOutput schema exactly, with "
    "these keys and no others: recommendations (list of objects, each with "
    "component, recommended, alternatives, reason, tradeoffs), cloud_fit "
    "(string), open_source_fit (string), lock_in_considerations (string), "
    "cost_estimate (object with infrastructure_monthly, implementation, "
    "assumptions). cost_estimate.infrastructure_monthly and "
    "cost_estimate.implementation must each be an indicative range or a "
    "clearly qualified statement such as 'Not enough information for a "
    "reliable estimate' — never a single precise number presented as fact. "
    "cost_estimate.implementation here means only the one-time "
    "infrastructure/service setup cost — never team or delivery "
    "implementation cost, which belongs to the Delivery Planner. Every item "
    "must be concrete and specific — no placeholders, no boilerplate."
)


def build_technology_task(
    agent: Any,
    *,
    requirements: RequirementsOutput,
    architecture: ArchitectureOutput,
    tech_preference: TechPreference,
    cloud_preference: CloudPreference,
    expected_daily_traffic: int,
    delivery_timeline_months: int,
    country: str,
    repair_issues: Optional[tuple] = None,
) -> Any:
    """Construct the Technology Advisor's task for one generation request.

    Requires the `crewai` package. `agent` should come from
    `ai.agents.technology_advisor.build_technology_advisor_agent`.
    `requirements` and `architecture` must be the Business Analyst's and
    Solution Architect's structured outputs for this same request — they
    are the Technology Advisor's upstream context.

    `repair_issues`: optional Consistency Validator issue text for this
    stage specifically (e.g. `RepairPlan.issues_by_owner["Technology Advisor"]`
    from `ai.repair`), used only when this task is a targeted repair rerun.
    `None`/omitted (the default) reproduces the original, non-repair prompt
    exactly — normal initial generation is unaffected.
    """
    from crewai import Task  # local import: keeps this module importable/testable
    # even in environments where crewai itself cannot be installed.

    description = _build_description(
        requirements=requirements,
        architecture=architecture,
        tech_preference=tech_preference,
        cloud_preference=cloud_preference,
        expected_daily_traffic=expected_daily_traffic,
        delivery_timeline_months=delivery_timeline_months,
        country=country,
        repair_issues=repair_issues,
    )
    return Task(
        description=description,
        expected_output=TECHNOLOGY_EXPECTED_OUTPUT,
        agent=agent,
        output_pydantic=TechnologyOutput,
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
            _bullets("Data flow", architecture.data_flow),
            _bullets("Storage approach", architecture.storage),
            _bullets("Security controls", architecture.security),
            _bullets("Scalability approach", architecture.scalability),
            _bullets("MVP architecture", architecture.mvp_architecture),
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
    tech_preference: TechPreference,
    cloud_preference: CloudPreference,
    expected_daily_traffic: int,
    delivery_timeline_months: int,
    country: str,
    repair_issues: Optional[tuple] = None,
) -> str:
    return (
        "Recommend specific technologies for the architecture below, produced "
        "by the Solution Architect against the Business Analyst's requirements. "
        "Treat both as ground truth — do not redefine the requirements and do "
        "not redesign the architecture; recommend technologies that fit the "
        "components you were given. Do not produce a delivery timeline, assign "
        "team roles, estimate implementation/team cost, or perform consistency "
        "validation — those belong to other specialists.\n\n"
        f"{_summarize_requirements(requirements)}\n\n"
        f"{_summarize_architecture(architecture)}\n\n"
        f"Technology preference: {tech_preference}\n"
        f"Cloud preference: {cloud_preference}\n"
        f"Expected daily traffic: {expected_daily_traffic}\n"
        f"Delivery timeline (months): {delivery_timeline_months}\n"
        f"Country where data will be hosted: {country}\n\n"
        "Produce:\n"
        "1. For each major component, a specific recommended technology, at "
        "least one alternative, the reason for the recommendation, and its "
        "trade-offs.\n"
        "2. Cloud fit: how well the recommendations fit the stated cloud "
        "preference (or, if no cloud preference was stated, how cloud-"
        "agnostic they are).\n"
        "3. Open-source fit: how well the recommendations respect the stated "
        "technology preference.\n"
        "4. Lock-in considerations for the recommended stack.\n"
        "5. An indicative infrastructure/service cost estimate, sized to the "
        "expected daily traffic, as a range or a clearly qualified statement — "
        "never false precision — plus the assumptions behind it. This is a "
        "one-time infrastructure/service setup cost and a monthly running "
        "cost only, never a team/delivery implementation cost.\n\n"
        "Explicitly respect the technology preference, the cloud preference, "
        "the expected daily traffic, the country where data will be hosted, "
        "and the delivery timeline in every recommendation. Keep every item "
        "concrete and specific to this system — no placeholders, no "
        "boilerplate.\n\n"
        "If you have access to a web search tool, you may use it — sparingly, "
        "a small number of targeted searches, not broad research — to check "
        "current technology options, current cloud services, current "
        "platform capabilities, or current pricing/reference information. "
        "Search results are supporting evidence only: you remain fully "
        "responsible for the final recommendation and trade-offs, and you "
        "never use search to redefine requirements, redesign the "
        "architecture, create a delivery plan, or perform consistency "
        "validation — those stay out of scope no matter what you find. If a "
        "search result includes pricing, treat it like any other cost "
        "information: state it as an indicative range or a clearly "
        "qualified statement and note that it came from a web search, never "
        "as a precise guaranteed price. If search is unavailable, or a "
        "search fails or returns nothing usable, continue with your own "
        "knowledge and the context already provided — never leave a "
        "recommendation incomplete because a search did not return results."
    ) + _repair_context_section(repair_issues)
