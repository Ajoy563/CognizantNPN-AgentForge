"""Technology Advisor CrewAI task.

Consumes the Business Analyst's RequirementsOutput and the Solution
Architect's ArchitectureOutput as upstream context, plus the original
technology preference, cloud preference, expected traffic, delivery
timeline, and hosting country, and produces a structured, traceable
result conforming to ai.schemas.technology.TechnologyOutput.
"""

from typing import Any, Literal

from ai.schemas.architecture import ArchitectureOutput
from ai.schemas.requirements import RequirementsOutput
from ai.schemas.technology import TechnologyOutput

TechPreference = Literal["opensource", "enterprise"]
CloudPreference = Literal["aws", "azure", "gcp", "none"]

OUTPUT_SCHEMA = TechnologyOutput

TECHNOLOGY_EXPECTED_OUTPUT = (
    "A single JSON object matching the TechnologyOutput schema exactly, with "
    "these keys and no others: decisions (list of objects: id, technology, "
    "category, purpose, supports, requirements, reason, integration_method, "
    "advantages, tradeoffs, security_considerations, "
    "scalability_considerations, operational_considerations, "
    "cost_considerations, provider_dependency, portability_risk, "
    "migration_mitigation, alternatives), cloud_fit (string), "
    "open_source_fit (string), overall_lock_in_assessment (string), "
    "cost_estimate (object with infrastructure_monthly, implementation, "
    "assumptions). Every decision's id must be TECH-001, TECH-002, ... "
    "unique, never reused. `supports` must list at least one real "
    "architecture component id (ARCH-xxx); `requirements` must list at "
    "least one real requirement id (REQ-xxx) — both from the input, never "
    "invented. provider_dependency must literally be the string 'none' "
    "when the technology is portable/self-hostable, otherwise the "
    "specific cloud/vendor it depends on — and when it is not 'none', "
    "portability_risk and migration_mitigation must be concrete, never a "
    "vague platitude. cost_estimate.infrastructure_monthly and "
    "cost_estimate.implementation must each be an indicative range or a "
    "clearly qualified statement such as 'Not enough information for a "
    "reliable estimate' — never a single precise number presented as "
    "fact. cost_estimate.implementation here means only the one-time "
    "infrastructure/service setup cost — never team or delivery "
    "implementation cost, which belongs to the Delivery Planner. Every "
    "item must be concrete and specific — no placeholders, no "
    "boilerplate."
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
) -> Any:
    """Construct the Technology Advisor's task for one generation request.

    Requires the `crewai` package. `agent` should come from
    `ai.agents.technology_advisor.build_technology_advisor_agent`.
    `requirements` and `architecture` must be the Business Analyst's and
    Solution Architect's structured outputs for this same request — they
    are the Technology Advisor's upstream context.
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
    requirements_rendered = "\n".join(
        f"  - {req.id} [{req.category}/{req.priority}]: {req.text}"
        for req in requirements.requirements
    )
    return "\n".join(
        [
            f"Problem statement: {requirements.problem}",
            f"Requirements:\n{requirements_rendered}",
        ]
    )


def _summarize_architecture(architecture: ArchitectureOutput) -> str:
    components_rendered = "\n".join(
        f"  - {c.id} [{c.layer}]: {c.name} — {c.responsibility} "
        f"(satisfies: {', '.join(c.satisfies)})"
        for c in architecture.components
    )
    security_rendered = "\n".join(
        f"  - {s.id}: {s.control} (satisfies: {', '.join(s.satisfies)})"
        for s in architecture.security_controls
    )
    return "\n".join(
        [
            f"Architecture style: {architecture.architecture_style}",
            f"Components:\n{components_rendered}",
            _bullets("Storage", architecture.storage),
            _bullets("Caching", architecture.caching),
            _bullets("Messaging", architecture.messaging),
            f"Security controls:\n{security_rendered}",
            _bullets("Scalability strategy", architecture.scalability_strategy),
        ]
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
) -> str:
    return (
        "Recommend specific technologies for the architecture below, "
        "produced by the Solution Architect against the Business "
        "Analyst's requirements. Treat both as ground truth — do not "
        "redefine the requirements and do not redesign the architecture; "
        "recommend technologies that fit the components you were given. "
        "Do not produce a delivery timeline, assign team roles, estimate "
        "implementation/team cost, or perform consistency validation — "
        "those belong to other specialists.\n\n"
        f"{_summarize_requirements(requirements)}\n\n"
        f"{_summarize_architecture(architecture)}\n\n"
        f"Technology preference: {tech_preference}\n"
        f"Cloud preference: {cloud_preference}\n"
        f"Expected daily traffic: {expected_daily_traffic}\n"
        f"Delivery timeline (months): {delivery_timeline_months}\n"
        f"Country where data will be hosted: {country}\n\n"
        "Produce:\n"
        "1. Roughly 5 to 8 primary technology decisions in total, each "
        "naming the component id(s) it `supports` and the requirement "
        "id(s) it ultimately serves. Every decision must carry: purpose "
        "(what job this technology does here), reason (why it was "
        "selected over the alternatives, specific to this project), at "
        "least one genuinely practical alternative in `alternatives`, at "
        "least one real trade-off in `tradeoffs` (the concrete cost of "
        "this choice, never 'none'), integration method, advantages, and "
        "cost_considerations. Keep each field to one or two sentences. "
        "One decision "
        "may support several components — do not pick a separate "
        "managed cloud service for every small function, and avoid "
        "enterprise services this MVP does not genuinely need. Every "
        "component must still be supported by at least one decision.\n"
        "2. For every decision, security/scalability/operational "
        "considerations and cost considerations.\n"
        "3. For every decision, an explicit provider_dependency ('none' "
        "or the specific vendor), and when it is not 'none', a concrete "
        "portability_risk and migration_mitigation — never hide this "
        "trade-off.\n"
        "4. Cloud fit, open-source fit, and an overall lock-in "
        "assessment across the whole stack.\n"
        "5. An indicative infrastructure/service cost estimate, sized to "
        "the expected daily traffic, as a range or a clearly qualified "
        "statement — never false precision — plus the assumptions "
        "behind it. This is a one-time infrastructure/service setup "
        "cost and a monthly running cost only, never a team/delivery "
        "implementation cost.\n\n"
        "Explicitly respect the technology preference, the cloud "
        "preference, the expected daily traffic, the country where data "
        "will be hosted, and the delivery timeline in every "
        "recommendation. If you have access to a web search tool, you "
        "may use it — sparingly, a small number of targeted searches, "
        "not broad research — to check current technology options, "
        "current cloud services, current platform capabilities, or "
        "current pricing/reference information. Search results are "
        "supporting evidence only: you remain fully responsible for the "
        "final recommendation and trade-offs, and you never use search "
        "to redefine requirements, redesign the architecture, create a "
        "delivery plan, or perform consistency validation. If a search "
        "result includes pricing, treat it like any other cost "
        "information: state it as an indicative range and note that it "
        "came from a web search, never as a precise guaranteed price. If "
        "search is unavailable, or a search fails or returns nothing "
        "usable, continue with your own knowledge and the context "
        "already provided. Keep every item concrete and specific to "
        "this system — no placeholders, no boilerplate."
    )
