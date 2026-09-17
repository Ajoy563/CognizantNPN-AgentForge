"""Business Analyst CrewAI task.

Turns the six normalized generation-request inputs into a structured
result conforming to ai.schemas.requirements.RequirementsOutput.
"""

from typing import Any, Literal, Optional

from ai.schemas.requirements import RequirementsOutput

TechPreference = Literal["opensource", "enterprise"]
CloudPreference = Literal["aws", "azure", "gcp", "none"]

OUTPUT_SCHEMA = RequirementsOutput

BUSINESS_ANALYSIS_EXPECTED_OUTPUT = (
    "A single JSON object matching the RequirementsOutput schema exactly, with these "
    "keys and no others: problem (string), stakeholders (list of strings), "
    "functional_requirements (list of strings), non_functional_requirements "
    "(list of strings), mvp_priorities (list of strings), future_scope (list of "
    "strings), assumptions (list of strings), constraints (list of strings), "
    "risks (list of strings), clarifications (list of strings). Every list item must "
    "be concrete and specific to this business idea — no placeholders, no boilerplate."
)


def build_business_analysis_task(
    agent: Any,
    *,
    business_idea: str,
    tech_preference: TechPreference,
    cloud_preference: CloudPreference,
    expected_daily_traffic: int,
    delivery_timeline_months: int,
    country: str,
    repair_issues: Optional[tuple] = None,
) -> Any:
    """Construct the Business Analyst's task for one generation request.

    Requires the `crewai` package. `agent` should come from
    `ai.agents.business_analyst.build_business_analyst_agent`.

    `repair_issues`: optional Consistency Validator issue text for this
    stage specifically (e.g. `RepairPlan.issues_by_owner["Business Analyst"]`
    from `ai.repair`), used only when this task is a targeted repair rerun.
    `None`/omitted (the default) reproduces the original, non-repair prompt
    exactly — normal initial generation is unaffected.
    """
    from crewai import Task  # local import: keeps this module importable/testable
    # even in environments where crewai itself cannot be installed.

    description = _build_description(
        business_idea=business_idea,
        tech_preference=tech_preference,
        cloud_preference=cloud_preference,
        expected_daily_traffic=expected_daily_traffic,
        delivery_timeline_months=delivery_timeline_months,
        country=country,
        repair_issues=repair_issues,
    )
    return Task(
        description=description,
        expected_output=BUSINESS_ANALYSIS_EXPECTED_OUTPUT,
        agent=agent,
        output_pydantic=RequirementsOutput,
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
    business_idea: str,
    tech_preference: TechPreference,
    cloud_preference: CloudPreference,
    expected_daily_traffic: int,
    delivery_timeline_months: int,
    country: str,
    repair_issues: Optional[tuple] = None,
) -> str:
    return (
        "Analyze the following business idea and produce structured requirements "
        "only. Do not select technologies, do not design system architecture, and "
        "do not produce a delivery plan, timeline, or team composition — those "
        "belong to other specialists.\n\n"
        f"Business idea / problem statement: {business_idea}\n"
        f"Technology preference: {tech_preference}\n"
        f"Cloud preference: {cloud_preference}\n"
        f"Expected daily traffic: {expected_daily_traffic}\n"
        f"Delivery timeline (months): {delivery_timeline_months}\n"
        f"Country where data will be hosted: {country}\n\n"
        "Produce:\n"
        "1. A precise problem statement.\n"
        "2. The users/stakeholders involved.\n"
        "3. Functional requirements needed to deliver the core value proposition.\n"
        "4. Non-functional requirements (performance, availability, compliance, "
        "data residency, etc.), informed by the expected daily traffic and the "
        "country where data will be hosted.\n"
        "5. MVP priorities: the smallest set of functional requirements that "
        "deliver value within the delivery timeline. Be ruthless — push anything "
        "non-essential to future scope.\n"
        "6. Future scope: valuable but non-essential capabilities deferred past "
        "the MVP.\n"
        "7. Assumptions you are making because the input did not specify them "
        "explicitly.\n"
        "8. Constraints (timeline, budget, regulatory, data residency, etc.).\n"
        "9. Business risks that could threaten the success of this initiative.\n"
        "10. Clarifications: open questions you would ask the client before "
        "proceeding, for anything genuinely ambiguous — never silently guess.\n\n"
        "Keep every item concrete and specific to this business idea. Do not "
        "repeat the input verbatim; synthesize it into requirements."
    ) + _repair_context_section(repair_issues)
