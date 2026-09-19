"""Solution Architect CrewAI task.

Consumes the Business Analyst's RequirementsOutput as upstream context and
produces a structured, traceable result conforming to
ai.schemas.architecture.ArchitectureOutput.
"""

from typing import Any

from ai.schemas.architecture import ArchitectureOutput
from ai.schemas.requirements import RequirementsOutput

OUTPUT_SCHEMA = ArchitectureOutput

ARCHITECTURE_LAYERS = (
    "presentation",
    "api",
    "application",
    "domain",
    "data",
    "infrastructure",
    "external",
)

ARCHITECTURE_EXPECTED_OUTPUT = (
    "A single JSON object matching the ArchitectureOutput schema exactly, with "
    "these keys and no others: architecture_style (string), rationale "
    "(string), components (list of objects: id, name, layer, purpose, "
    "responsibility, interfaces, security_consideration, "
    "scalability_consideration, satisfies), data_flow (list of objects: "
    "from_node, to_node, description), request_flow (list of strings), "
    "authentication_flow (list of strings), external_integrations (list of "
    "strings), storage (list of strings), caching (list of strings), "
    "messaging (list of strings), observability (list of strings), "
    "security_controls (list of objects: id, control, satisfies), "
    "scalability_strategy (list of strings), availability_strategy (list "
    "of strings), disaster_recovery (list of strings), "
    "deployment_architecture (list of strings), mvp_architecture (list of "
    "strings), future_evolution (list of strings). Every component's id "
    "must be ARCH-001, ARCH-002, ... unique, never reused. layer must be "
    "exactly one of: presentation, api, application, domain, data, "
    "infrastructure, external. Every component's `satisfies` must list at "
    "least one real requirement id (REQ-xxx) from the input — never "
    "invented, never empty. Every security control's id must be SEC-001, "
    "SEC-002, ... with a non-empty `satisfies` list of requirement ids. "
    "Every component's purpose, security_consideration, and "
    "scalability_consideration must be non-empty; write 'Not applicable' "
    "plus a short reason when a concern genuinely does not apply. "
    "data_flow.from_node/to_node must each be either a component id "
    "(ARCH-xxx) or an external actor name (e.g. 'User', 'External API'). "
    "Every important requirement — not just functional ones — must be "
    "satisfied by at least one component or security control. Every item "
    "must be concrete and specific to this architecture — no placeholders, "
    "no boilerplate, and no specific technology/framework/cloud-vendor "
    "product names."
)


def build_architecture_task(
    agent: Any,
    *,
    requirements: RequirementsOutput,
    expected_daily_traffic: int,
    delivery_timeline_months: int,
    country: str,
) -> Any:
    """Construct the Solution Architect's task for one generation request.

    Requires the `crewai` package. `agent` should come from
    `ai.agents.solution_architect.build_solution_architect_agent`.
    `requirements` must be the Business Analyst's RequirementsOutput for this
    same request — it is the Solution Architect's upstream context.
    """
    from crewai import Task  # local import: keeps this module importable/testable
    # even in environments where crewai itself cannot be installed.

    description = _build_description(
        requirements=requirements,
        expected_daily_traffic=expected_daily_traffic,
        delivery_timeline_months=delivery_timeline_months,
        country=country,
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
    requirements_rendered = "\n".join(
        f"  - {req.id} [{req.category}/{req.priority}]: {req.text}"
        for req in requirements.requirements
    )
    return "\n".join(
        [
            f"Problem statement: {requirements.problem}",
            f"Business goals: {', '.join(requirements.business_goals)}",
            f"Requirements:\n{requirements_rendered}",
            f"MVP requirement ids: {', '.join(requirements.mvp_requirement_ids)}",
            _bullets("Constraints", requirements.constraints),
        ]
    )


def _build_description(
    *,
    requirements: RequirementsOutput,
    expected_daily_traffic: int,
    delivery_timeline_months: int,
    country: str,
) -> str:
    layers = ", ".join(ARCHITECTURE_LAYERS)
    return (
        "Design a system architecture for the business requirements below, "
        "produced by the Business Analyst. Treat these requirements as "
        "ground truth — do not redefine the business problem, "
        "stakeholders, or MVP priorities. Do not select a specific "
        "technology stack, framework, database product, or cloud vendor. "
        "Do not produce a delivery timeline, team plan, cost estimate, or "
        "perform consistency validation — those belong to other "
        "specialists.\n\n"
        f"{_summarize_requirements(requirements)}\n\n"
        f"Expected daily traffic: {expected_daily_traffic}\n"
        f"Delivery timeline (months): {delivery_timeline_months}\n"
        f"Country where data will be hosted: {country}\n\n"
        "Produce:\n"
        "1. Architecture style and the rationale for choosing it. The "
        "rationale must explain specifically why this style fits THIS "
        "MVP — its scope, its team size, its timeline, and its expected "
        "traffic — not why the style is good in general. Default to a "
        "simple modular monolith; choose microservices, event-driven, or "
        "any other distributed style only when the requirements and the "
        "expected traffic genuinely demand it, and say why.\n"
        f"2. Major components, each assigned to a layer ({layers}). For "
        "every component give: purpose (one sentence on why it exists), "
        "responsibility (what it actually does), interfaces (its inputs "
        "and outputs, e.g. 'REST /orders in, publishes OrderPlaced'), "
        "security_consideration (the main security concern for this "
        "specific component, or 'Not applicable' plus a reason), "
        "scalability_consideration (how it behaves under the expected "
        "load, or 'Not applicable' plus a reason), and a `satisfies` "
        "list naming every requirement id (REQ-xxx) it addresses. Keep "
        "each field to one or two sentences. Target "
        "roughly 5 to 10 components for a normal MVP. Group related "
        "responsibilities into one coherent component rather than "
        "creating a separate component for every individual "
        "requirement. Each component may satisfy several requirements. "
        "Every important requirement above — including non-functional, "
        "security, compliance, performance, availability, scalability, "
        "integration, data, and UX ones — must still be satisfied by at "
        "least one component or security control.\n"
        "3. Data flow between components (and external actors like "
        "'User'), from client through to storage; request flow; and "
        "authentication flow.\n"
        "4. External integrations, storage approach, caching (if "
        "relevant), messaging/queues/events (if relevant), and "
        "observability — described by role, not by vendor/product name.\n"
        "5. Security controls, each with a `satisfies` list of "
        "requirement ids, covering authentication, authorization, "
        "secrets management, encryption in transit and at rest, API "
        "security/input validation, and logging/auditing wherever the "
        "requirements call for them.\n"
        "6. Scalability strategy appropriate for the expected daily "
        "traffic, availability strategy, and disaster-recovery "
        "considerations — do not over-engineer for load this system "
        "will not see, but never omit these sections outright.\n"
        "7. Deployment architecture, MVP architecture (the minimal "
        "version buildable within the delivery timeline), and future "
        "evolution.\n\n"
        "Keep every item concrete and specific to this system. Do not "
        "repeat the requirements verbatim; synthesize them into an "
        "architecture."
    )
