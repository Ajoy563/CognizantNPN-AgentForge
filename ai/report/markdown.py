"""Deterministic Markdown rendering of the full solution blueprint —
pure string formatting, no LLM calls, no templating engine."""

from ai.report.title import derive_project_title
from ai.schemas.architecture import ArchitectureOutput
from ai.schemas.delivery import DeliveryOutput
from ai.schemas.requirements import RequirementsOutput
from ai.schemas.technology import TechnologyOutput

_LAYER_ORDER = (
    "presentation",
    "api",
    "application",
    "domain",
    "data",
    "infrastructure",
    "external",
)


def _section(title: str, items: list) -> list:
    if not items:
        return []
    lines = [f"### {title}", ""]
    lines += [f"- {item}" for item in items]
    lines.append("")
    return lines


def render_blueprint_markdown(
    requirements: RequirementsOutput,
    architecture: ArchitectureOutput,
    technology: TechnologyOutput,
    delivery: DeliveryOutput,
) -> str:
    title = derive_project_title(requirements.problem, requirements.business_goals)
    lines: list = [f"# {title}", ""]

    # 1. Executive Summary
    lines += ["## 1. Executive Summary", "", requirements.problem, ""]
    lines += [f"**Business context:** {requirements.business_context}", ""]
    lines += _section("Business Goals", requirements.business_goals)
    lines += _section("Primary Stakeholders", requirements.stakeholders)
    lines += [f"**Recommended MVP focus:** {requirements.mvp_focus}", ""]

    # 2. Requirements
    lines += ["## 2. Requirements", ""]
    for req in requirements.requirements:
        lines.append(f"- **{req.id}** [{req.category}/{req.priority}]: {req.text}")
    lines.append("")
    lines += _section("MVP Requirement IDs", requirements.mvp_requirement_ids)
    lines += _section("Constraints", requirements.constraints)

    # 3. Architecture
    lines += ["## 3. Architecture", ""]
    lines.append(f"**Style:** {architecture.architecture_style}")
    lines.append("")
    lines.append(f"**Rationale:** {architecture.rationale}")
    lines.append("")
    lines.append("### Components")
    lines.append("")
    for c in architecture.components:
        lines.append(f"**{c.id} · {c.name}** [{c.layer}]")
        lines.append("")
        lines.append(f"- Purpose: {c.purpose}")
        lines.append(f"- Key responsibilities: {c.responsibility}")
        lines.append(f"- Interfaces: {', '.join(c.interfaces) or '-'}")
        lines.append(f"- Security: {c.security_consideration}")
        lines.append(f"- Scalability: {c.scalability_consideration}")
        lines.append(f"- Satisfies: {', '.join(c.satisfies)}")
        lines.append("")
    lines += _section("Request Flow", architecture.request_flow)
    lines += _section("Authentication Flow", architecture.authentication_flow)
    lines += _section("External Integrations", architecture.external_integrations)
    lines += _section("Storage", architecture.storage)
    lines += _section("Caching", architecture.caching)
    lines += _section("Messaging", architecture.messaging)
    lines += _section("Observability", architecture.observability)

    lines.append("### Security Controls")
    lines.append("")
    for s in architecture.security_controls:
        lines.append(f"- **{s.id}**: {s.control} (satisfies: {', '.join(s.satisfies)})")
    lines.append("")

    lines += _section("Scalability Strategy", architecture.scalability_strategy)
    lines += _section("Availability Strategy", architecture.availability_strategy)
    lines += _section("Disaster Recovery", architecture.disaster_recovery)
    lines += _section("Deployment Architecture", architecture.deployment_architecture)
    lines += _section("MVP Architecture", architecture.mvp_architecture)

    # 4. Technical Architecture Diagram — the HTML report embeds a real SVG;
    # the Markdown/PDF form renders the same graph as layered text.
    lines += ["## 4. Technical Architecture Diagram", ""]
    for layer in _LAYER_ORDER:
        members = [c for c in architecture.components if c.layer == layer]
        if members:
            lines.append(f"- **{layer}**: {', '.join(f'{c.id} {c.name}' for c in members)}")
    lines.append("")
    if architecture.data_flow:
        lines.append("### Connections")
        lines.append("")
        for step in architecture.data_flow:
            lines.append(f"- {step.from_node} -> {step.to_node}: {step.description}")
        lines.append("")

    # 5. Technology Decisions
    lines += ["## 5. Technology Decisions", ""]
    for d in technology.decisions:
        lines.append(f"**{d.id} · {d.technology}** ({d.category})")
        lines.append("")
        lines.append(f"- Purpose: {d.purpose}")
        lines.append(f"- Why selected: {d.reason}")
        lines.append(f"- Alternative: {d.alternatives[0] if d.alternatives else '-'}")
        lines.append(f"- Main trade-off: {d.tradeoffs[0] if d.tradeoffs else '-'}")
        lines.append(f"- Provider dependency: {d.provider_dependency}")
        lines.append(f"- Cost: {d.cost_considerations}")
        lines.append(f"- Supports: {', '.join(d.supports)} (requirements: {', '.join(d.requirements)})")
        lines.append("")
    lines.append(f"**Cloud fit:** {technology.cloud_fit}")
    lines.append("")
    lines.append(f"**Open-source fit:** {technology.open_source_fit}")
    lines.append("")
    lines.append(f"**Overall lock-in assessment:** {technology.overall_lock_in_assessment}")
    lines.append("")
    lines.append("### Infrastructure Cost (indicative)")
    lines.append("")
    lines.append(f"- Monthly: {technology.cost_estimate.infrastructure_monthly}")
    lines.append(f"- Setup: {technology.cost_estimate.implementation}")
    lines.append("")
    lines += _section("Cost Assumptions", technology.cost_estimate.assumptions)

    # 6. Delivery Plan
    lines += ["## 6. Delivery Plan", ""]
    for t in delivery.workstreams:
        lines.append(f"**{t.id} · {t.name}**")
        lines.append("")
        lines.append(f"- Purpose: {t.purpose}")
        lines.append(f"- Major activities: {', '.join(t.activities) or '-'}")
        lines.append(f"- Dependencies: {', '.join(t.dependencies) or 'None'}")
        lines.append(f"- Deliverable: {t.deliverable}")
        lines.append(f"- Effort: {t.effort}")
        lines.append(f"- Addresses: {', '.join(t.addresses)}")
        lines.append("")
    lines += _section("Milestones", delivery.milestones)
    lines += _section("Dependencies", delivery.dependencies)
    lines.append("### Team")
    lines.append("")
    for role in delivery.team_roles:
        lines.append(f"- {role.role} x{role.count}")
    lines.append("")
    lines.append("### Timeline")
    lines.append("")
    for phase in delivery.timeline:
        lines.append(
            f"- **{phase.phase}** ({phase.duration}) — milestone: {phase.milestone}: "
            f"{', '.join(phase.deliverables)}"
        )
    lines.append("")
    lines += _section("Testing Strategy", delivery.testing_strategy)
    lines += _section("Integration Testing", delivery.integration_testing)
    lines += _section("UAT Strategy", delivery.uat_strategy)
    lines += _section("Deployment Strategy", delivery.deployment_strategy)
    lines += _section("CI/CD", delivery.ci_cd)
    lines += _section("Monitoring", delivery.monitoring)
    lines += _section("Rollback Strategy", delivery.rollback_strategy)
    lines.append(f"**Effort & complexity:** {delivery.effort_complexity}")
    lines.append("")
    lines.append("### Implementation/Team Cost (indicative)")
    lines.append("")
    lines.append(f"- Effort: {delivery.cost_estimate.estimated_effort}")
    lines.append(f"- Team cost: {delivery.cost_estimate.estimated_team_cost}")
    lines.append("")

    # 7. Risks & Mitigations
    lines += ["## 7. Risks & Mitigations", ""]
    for risk in delivery.risks:
        lines.append(f"- **{risk.risk}** (impact: {risk.impact}) — mitigation: {risk.mitigation}")
    lines.append("")
    lines += _section("Business Risks", requirements.risks)

    # 8. Assumptions & Open Questions
    lines += ["## 8. Assumptions & Open Questions", ""]
    lines += _section("Assumptions", requirements.assumptions)
    lines += _section("Open Questions", requirements.open_questions)

    # 9. Future Evolution
    lines += ["## 9. Future Evolution", ""]
    lines += _section("Deferred Scope", requirements.future_scope)
    lines += _section("Architecture Evolution", architecture.future_evolution)
    lines += _section("Delivery Evolution", delivery.future_evolution)

    return "\n".join(lines).strip() + "\n"
