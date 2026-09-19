"""Business Analyst CrewAI task.

Turns the six normalized generation-request inputs into a structured,
traceable result conforming to ai.schemas.requirements.RequirementsOutput.
"""

from typing import Any, Literal

from ai.schemas.requirements import RequirementsOutput

TechPreference = Literal["opensource", "enterprise"]
CloudPreference = Literal["aws", "azure", "gcp", "none"]

OUTPUT_SCHEMA = RequirementsOutput

REQUIREMENT_CATEGORIES = (
    "functional",
    "non_functional",
    "security",
    "compliance",
    "performance",
    "availability",
    "scalability",
    "integration",
    "data",
    "ux",
)

BUSINESS_ANALYSIS_EXPECTED_OUTPUT = (
    "A single JSON object matching the RequirementsOutput schema exactly, with "
    "these keys and no others: problem (string), business_context (string), "
    "business_goals (list of "
    "strings), personas (list of objects: name, role, goals), stakeholders "
    "(list of strings), requirements (list of objects: id, category, text, "
    "priority), mvp_requirement_ids (list of strings), mvp_focus (string), "
    "future_scope (list of "
    "strings), assumptions (list of strings), open_questions (list of "
    "strings), constraints (list of strings), risks (list of strings). Every "
    "requirement's id must be REQ-001, REQ-002, ... in the order introduced, "
    "unique, never reused. category must be exactly one of: functional, "
    "non_functional, security, compliance, performance, availability, "
    "scalability, integration, data, ux — cover every category that is "
    "actually relevant, not just functional. priority must be exactly one "
    "of: must, should, could. mvp_requirement_ids must reference only ids "
    "that exist in requirements. Every list item must be concrete and "
    "specific to this business idea — no placeholders, no boilerplate."
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
) -> Any:
    """Construct the Business Analyst's task for one generation request.

    Requires the `crewai` package. `agent` should come from
    `ai.agents.business_analyst.build_business_analyst_agent`.
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
    )
    return Task(
        description=description,
        expected_output=BUSINESS_ANALYSIS_EXPECTED_OUTPUT,
        agent=agent,
        output_pydantic=RequirementsOutput,
    )


def _build_description(
    *,
    business_idea: str,
    tech_preference: TechPreference,
    cloud_preference: CloudPreference,
    expected_daily_traffic: int,
    delivery_timeline_months: int,
    country: str,
) -> str:
    categories = ", ".join(REQUIREMENT_CATEGORIES)
    return (
        "Analyze the following business idea and produce structured, "
        "uniquely-identified requirements only. Do not select "
        "technologies, do not design system architecture, and do not "
        "produce a delivery plan, timeline, or team composition — those "
        "belong to other specialists.\n\n"
        f"Business idea / problem statement: {business_idea}\n"
        f"Technology preference: {tech_preference}\n"
        f"Cloud preference: {cloud_preference}\n"
        f"Expected daily traffic: {expected_daily_traffic}\n"
        f"Delivery timeline (months): {delivery_timeline_months}\n"
        f"Country where data will be hosted: {country}\n\n"
        "Produce:\n"
        "1. A precise problem statement; a short business_context paragraph "
        "(2-3 sentences) explaining the situation this solution is being "
        "built into and why it matters commercially; and the concrete "
        "business goals this solution must achieve.\n"
        "2. User personas (name, role, goals) and the stakeholders "
        "involved.\n"
        "3. A single flat list of requirements, each with a unique id "
        f"(REQ-001, REQ-002, ...), a category (one of: {categories}), the "
        "requirement text, and a priority (must/should/could). Target 6 "
        "to 12 requirements in total — this is a practical MVP, not an "
        "enterprise programme. Include a requirement only when the "
        "business idea above, or an explicit constraint, genuinely "
        "justifies it. Do not invent enterprise governance, advanced "
        "third-party integrations, multi-region disaster recovery, "
        "complex audit or approval systems, or similar heavyweight "
        "scope unless this specific idea actually calls for it. Cover "
        "non-functional, security, and data requirements when they "
        "matter, but keep them proportionate to the real scale. Each "
        "requirement's text must be one clear, testable sentence — "
        "specific enough that an engineer could verify it was met, but "
        "never a paragraph.\n"
        "4. mvp_requirement_ids: the smallest set of requirement ids that "
        "deliver value within the delivery timeline. Be ruthless — leave "
        "everything else for future scope. Also give mvp_focus: one or two "
        "sentences naming what the MVP should concentrate on first and "
        "what it deliberately defers.\n"
        "5. Future scope: valuable but non-essential capabilities "
        "deferred past the MVP.\n"
        "6. Assumptions you are making because the input did not specify "
        "them explicitly, and constraints (timeline, budget, regulatory, "
        "data residency, etc.).\n"
        "7. Business risks that could threaten the success of this "
        "initiative.\n"
        "8. Open questions: anything genuinely ambiguous that you cannot "
        "responsibly turn into an assumption — never silently guess when "
        "the answer actually matters.\n\n"
        "Keep every item concrete and specific to this business idea — "
        "no placeholders, no boilerplate, and never invent a fact the "
        "input didn't give you; record it as an assumption or open "
        "question instead."
    )
