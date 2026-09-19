"""Professional, self-contained HTML solution-blueprint report.

No external CSS/CDN/JS — everything (styles, the architecture diagram)
is embedded so the report works fully offline. Pure string templating,
no LLM calls."""

import html as html_module
from datetime import datetime, timezone

from ai.report.diagram import render_architecture_diagram_svg
from ai.report.title import derive_project_title
from ai.schemas.architecture import ArchitectureOutput
from ai.schemas.delivery import DeliveryOutput
from ai.schemas.requirements import RequirementsOutput
from ai.schemas.technology import TechnologyOutput

_PRIORITY_BADGE_CLASS = {"must": "badge-must", "should": "badge-should", "could": "badge-could"}

_CSS = """
:root {
  --ink: #0f172a; --muted: #64748b; --line: #e2e8f0; --card: #ffffff;
  --bg: #f8fafc; --brand: #4f46e5; --brand-2: #6366f1;
  --pass: #16a34a; --fail: #dc2626; --warn: #d97706;
}
* { box-sizing: border-box; }
body {
  margin: 0; background: var(--bg); color: var(--ink);
  font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.55;
}
.report { max-width: 1080px; margin: 0 auto; padding: 0 20px 60px; }
.header {
  background: linear-gradient(135deg, var(--brand), var(--brand-2));
  color: white; padding: 40px 32px; border-radius: 0 0 20px 20px; margin-bottom: 28px;
}
.header .brand { font-size: 13px; letter-spacing: 2px; opacity: 0.85; font-weight: 600; }
.header h1 { margin: 10px 0 6px; font-size: 30px; }
.header .meta-row { display: flex; gap: 22px; flex-wrap: wrap; margin-top: 18px; font-size: 13px; opacity: 0.92; }
.header .meta-row b { font-weight: 700; }
nav.toc {
  background: var(--card); border: 1px solid var(--line); border-radius: 14px;
  padding: 18px 22px; margin-bottom: 28px;
}
nav.toc h2 { margin: 0 0 10px; font-size: 15px; text-transform: uppercase; letter-spacing: 1px; color: var(--muted); }
nav.toc ol { margin: 0; padding-left: 20px; columns: 2; column-gap: 24px; font-size: 14px; }
nav.toc a { color: var(--brand); text-decoration: none; }
section { margin-bottom: 34px; }
section > h2 {
  font-size: 20px; border-bottom: 2px solid var(--line); padding-bottom: 8px; margin-bottom: 16px;
  scroll-margin-top: 12px;
}
.card {
  background: var(--card); border: 1px solid var(--line); border-radius: 12px;
  padding: 18px 20px; margin-bottom: 12px;
}
.card h3 { margin: 0 0 8px; font-size: 15px; }
.card .id { font-family: 'Consolas', monospace; font-size: 11px; color: var(--muted); }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 12px; }
.summary-card {
  background: var(--card); border: 1px solid var(--line); border-left: 5px solid var(--brand);
  border-radius: 12px; padding: 20px 22px;
}
table { width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 8px; }
th, td { border: 1px solid var(--line); padding: 8px 10px; text-align: left; vertical-align: top; }
th { background: #eef2ff; font-weight: 600; }
tr:nth-child(even) td { background: #fafbff; }
.badge {
  display: inline-block; padding: 2px 9px; border-radius: 999px; font-size: 11px;
  font-weight: 700; letter-spacing: 0.5px;
}
.badge-must { background: #ede9fe; color: #6d28d9; }
.badge-should { background: #e0f2fe; color: #0369a1; }
.badge-could { background: #f1f5f9; color: #475569; }
.diagram-wrap { background: white; border: 1px solid var(--line); border-radius: 12px; padding: 16px; overflow-x: auto; }
.diagram-wrap svg { max-width: 100%; height: auto; }
.risk-card { border-left: 4px solid var(--fail); }
dl.detail { margin: 8px 0 0; font-size: 13px; }
dl.detail dt {
  color: var(--muted); font-weight: 700; font-size: 10px; letter-spacing: 0.6px;
  text-transform: uppercase; margin-top: 8px;
}
dl.detail dt:first-child { margin-top: 0; }
dl.detail dd { margin: 2px 0 0; color: var(--ink); }
.footer { text-align: center; color: var(--muted); font-size: 12px; margin-top: 40px; padding-top: 20px; border-top: 1px solid var(--line); }

@page { margin: 12mm 10mm; }
@media print {
  /* Headless Chrome drops backgrounds unless printing is told otherwise —
     without this the gradient header and every badge render as plain white. */
  html, body, .header, .card, .summary-card, th, tr, .badge, .diagram-wrap {
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }
  body { background: white; }
  .report { max-width: none; padding: 0; }
  .header { border-radius: 0; margin-bottom: 18px; padding: 26px 24px; }
  .header h1 { font-size: 24px; }
  nav.toc { break-inside: avoid; break-after: page; }
  /* Sections are long; forcing them whole clips content. Keep the small
     units intact instead and let sections flow across pages. */
  section { break-inside: auto; }
  section > h2 { break-after: avoid; break-inside: avoid; }
  h3 { break-after: avoid; break-inside: avoid; }
  .card, .summary-card, .diagram-wrap, .count-tile { break-inside: avoid; }
  .grid { display: block; }
  .grid > .card { margin-bottom: 10px; }
  table { break-inside: auto; }
  thead { display: table-header-group; }
  tr, img, svg { break-inside: avoid; }
  a { text-decoration: none; color: inherit; }
  .footer { break-inside: avoid; }
}
@media (max-width: 640px) {
  nav.toc ol { columns: 1; }
  .header { padding: 26px 18px; }
}
"""


def _esc(text) -> str:
    return html_module.escape(str(text))


def _priority_badge(priority: str) -> str:
    return f'<span class="badge {_PRIORITY_BADGE_CLASS.get(priority, "badge-could")}">{_esc(priority)}</span>'


def _list_html(items: list) -> str:
    if not items:
        return "<p><em>None specified.</em></p>"
    return "<ul>" + "".join(f"<li>{_esc(item)}</li>" for item in items) + "</ul>"


def _refs_html(refs: list) -> str:
    if not refs:
        return "—"
    return ", ".join(f"<code>{_esc(r)}</code>" for r in refs)


def _build_traceability_rows(
    requirements: RequirementsOutput,
    architecture: ArchitectureOutput,
    technology: TechnologyOutput,
    delivery: DeliveryOutput,
) -> list[dict]:
    rows = []
    for req in requirements.requirements:
        arch_ids = [c.id for c in architecture.components if req.id in c.satisfies]
        arch_ids += [s.id for s in architecture.security_controls if req.id in s.satisfies]
        tech_ids = [d.id for d in technology.decisions if req.id in d.requirements]
        task_ids = [t.id for t in delivery.workstreams if req.id in t.addresses]
        rows.append(
            {
                "req": req,
                "arch_ids": arch_ids,
                "tech_ids": tech_ids,
                "task_ids": task_ids,
            }
        )
    return rows


def render_blueprint_html(
    requirements: RequirementsOutput,
    architecture: ArchitectureOutput,
    technology: TechnologyOutput,
    delivery: DeliveryOutput,
) -> str:
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    # The H1 is a short project name, never the raw business idea — the full
    # statement lives in the Executive Summary below.
    project_title = derive_project_title(requirements.problem, requirements.business_goals)
    trace_rows = _build_traceability_rows(requirements, architecture, technology, delivery)

    body: list[str] = []

    # Header
    body.append(
        '<div class="header"><div class="brand">SOLUTIONFORGE AI · SOLUTION BLUEPRINT</div>'
        f"<h1>{_esc(project_title)}</h1>"
        '<div class="meta-row">'
        f"<span><b>Generated:</b> {generated_at}</span>"
        f"<span><b>Requirements:</b> {len(requirements.requirements)}</span>"
        f"<span><b>Architecture components:</b> {len(architecture.components)}</span>"
        f"<span><b>Technology decisions:</b> {len(technology.decisions)}</span>"
        "</div></div>"
    )

    # TOC
    toc_items = [
        ("summary", "1. Executive Summary"),
        ("requirements", "2. Requirements"),
        ("architecture", "3. Architecture"),
        ("diagram", "4. Technical Architecture Diagram"),
        ("technology", "5. Technology Decisions"),
        ("delivery", "6. Delivery Plan"),
        ("risks", "7. Risks & Mitigations"),
        ("assumptions", "8. Assumptions & Open Questions"),
        ("future", "9. Future Evolution"),
    ]
    body.append(
        '<nav class="toc"><h2>Contents</h2><ol>'
        + "".join(f'<li><a href="#{key}">{_esc(label)}</a></li>' for key, label in toc_items)
        + "</ol></nav>"
    )

    # 1. Executive Summary
    body.append(
        '<section id="summary"><h2>1. Executive Summary</h2>'
        f'<div class="summary-card"><p>{_esc(requirements.problem)}</p>'
        f"<p><b>Business context:</b> {_esc(requirements.business_context)}</p>"
        f"<p><b>Business goals:</b> {', '.join(_esc(g) for g in requirements.business_goals) or '—'}</p>"
        f"<p><b>Primary stakeholders:</b> {', '.join(_esc(s) for s in requirements.stakeholders) or '—'}</p>"
        f"<p><b>Recommended MVP focus:</b> {_esc(requirements.mvp_focus)}</p>"
        "</div></section>"
    )

    # 2. Requirements
    req_rows = "".join(
        f"<tr><td><code>{_esc(r.id)}</code></td><td>{_esc(r.category)}</td>"
        f"<td>{_priority_badge(r.priority)}</td><td>{_esc(r.text)}</td>"
        f"<td>{'✓' if r.id in requirements.mvp_requirement_ids else ''}</td></tr>"
        for r in requirements.requirements
    )
    trace_rows_html = "".join(
        f"<tr><td><code>{_esc(row['req'].id)}</code></td>"
        f"<td>{_refs_html(row['arch_ids'])}</td>"
        f"<td>{_refs_html(row['tech_ids'])}</td>"
        f"<td>{_refs_html(row['task_ids'])}</td></tr>"
        for row in trace_rows
    )
    body.append(
        '<section id="requirements"><h2>2. Requirements</h2>'
        "<table><thead><tr><th>ID</th><th>Category</th><th>Priority</th>"
        "<th>Requirement</th><th>MVP</th></tr></thead>"
        f"<tbody>{req_rows}</tbody></table>"
        "<h3>Requirement Traceability Matrix</h3>"
        "<table><thead><tr><th>Requirement</th><th>Architecture</th><th>Technology</th>"
        f"<th>Delivery</th></tr></thead><tbody>{trace_rows_html}</tbody></table>"
        "</section>"
    )

    # 3. Architecture
    component_cards = "".join(
        f'<div class="card"><span class="id">{_esc(c.id)} · {_esc(c.layer)}</span>'
        f"<h3>{_esc(c.name)}</h3>"
        f"<dl class=\"detail\">"
        f"<dt>Purpose</dt><dd>{_esc(c.purpose)}</dd>"
        f"<dt>Key responsibilities</dt><dd>{_esc(c.responsibility)}</dd>"
        f"<dt>Interfaces</dt><dd>{', '.join(_esc(i) for i in c.interfaces) or '—'}</dd>"
        f"<dt>Security</dt><dd>{_esc(c.security_consideration)}</dd>"
        f"<dt>Scalability</dt><dd>{_esc(c.scalability_consideration)}</dd>"
        f"<dt>Satisfies</dt><dd>{_refs_html(c.satisfies)}</dd>"
        f"</dl></div>"
        for c in architecture.components
    )
    security_cards = "".join(
        f'<div class="card"><span class="id">{_esc(s.id)}</span><h3>{_esc(s.control)}</h3>'
        f"<p><b>Satisfies:</b> {_refs_html(s.satisfies)}</p></div>"
        for s in architecture.security_controls
    )
    body.append(
        '<section id="architecture"><h2>3. Architecture</h2>'
        f'<div class="summary-card"><p><b>Style:</b> {_esc(architecture.architecture_style)}</p>'
        f"<p><b>Rationale:</b> {_esc(architecture.rationale)}</p></div>"
        f'<h3>Components</h3><div class="grid">{component_cards}</div>'
        f'<h3>Security Controls</h3><div class="grid">{security_cards}</div>'
        f"<h3>Authentication Flow</h3>{_list_html(architecture.authentication_flow)}"
        f"<h3>Scalability Strategy</h3>{_list_html(architecture.scalability_strategy)}"
        f"<h3>Availability &amp; Disaster Recovery</h3>"
        f"{_list_html(list(architecture.availability_strategy) + list(architecture.disaster_recovery))}"
        f"<h3>Deployment Architecture</h3>{_list_html(architecture.deployment_architecture)}"
        "</section>"
    )

    # 4. Diagram
    body.append(
        '<section id="diagram"><h2>4. Technical Architecture Diagram</h2>'
        f'<div class="diagram-wrap">{render_architecture_diagram_svg(architecture)}</div>'
        "</section>"
    )

    # 5. Technology
    tech_cards = "".join(
        f'<div class="card"><span class="id">{_esc(d.id)} · {_esc(d.category)}</span>'
        f"<h3>{_esc(d.technology)}</h3>"
        f'<dl class="detail">'
        f"<dt>Purpose</dt><dd>{_esc(d.purpose)}</dd>"
        f"<dt>Why selected</dt><dd>{_esc(d.reason)}</dd>"
        f"<dt>Alternative</dt><dd>{_esc(d.alternatives[0]) if d.alternatives else '—'}</dd>"
        f"<dt>Main trade-off</dt><dd>{_esc(d.tradeoffs[0]) if d.tradeoffs else '—'}</dd>"
        f"<dt>Provider dependency</dt><dd>{_esc(d.provider_dependency)}"
        + (f" — {_esc(d.portability_risk)}" if d.provider_dependency.lower() != "none" else "")
        + "</dd>"
        f"<dt>Cost</dt><dd>{_esc(d.cost_considerations)}</dd>"
        f"<dt>Supports</dt><dd>{_refs_html(d.supports)} (requirements: {_refs_html(d.requirements)})</dd>"
        f"</dl></div>"
        for d in technology.decisions
    )
    tech_matrix_rows = "".join(
        f"<tr><td><code>{_esc(d.id)}</code></td><td>{_esc(d.technology)}</td><td>{_esc(d.purpose)}</td>"
        f"<td>{_refs_html(d.supports)}</td><td>{_refs_html(d.requirements)}</td>"
        f"<td>{_esc(d.reason)}</td><td>{', '.join(_esc(a) for a in d.alternatives) or '—'}</td>"
        f"<td>{', '.join(_esc(t) for t in d.tradeoffs) or '—'}</td>"
        f"<td>{_esc(d.provider_dependency)}</td></tr>"
        for d in technology.decisions
    )
    body.append(
        '<section id="technology"><h2>5. Technology Decisions</h2>'
        f'<div class="grid">{tech_cards}</div>'
        f'<div class="summary-card"><p><b>Cloud fit:</b> {_esc(technology.cloud_fit)}</p>'
        f"<p><b>Open-source fit:</b> {_esc(technology.open_source_fit)}</p>"
        f"<p><b>Overall lock-in assessment:</b> {_esc(technology.overall_lock_in_assessment)}</p>"
        f"<p><b>Infrastructure cost (indicative):</b> {_esc(technology.cost_estimate.infrastructure_monthly)} / month; "
        f"setup: {_esc(technology.cost_estimate.implementation)}</p></div>"
        "<h3>Technology Decision Matrix</h3>"
        "<table><thead><tr><th>ID</th><th>Technology</th><th>Purpose</th><th>Component</th>"
        "<th>Requirements</th><th>Why Selected</th><th>Alternatives</th><th>Trade-offs</th>"
        f"<th>Lock-in</th></tr></thead><tbody>{tech_matrix_rows}</tbody></table>"
        "</section>"
    )

    # 6. Delivery
    task_cards = "".join(
        f'<div class="card"><span class="id">{_esc(t.id)}</span>'
        f"<h3>{_esc(t.name)}</h3>"
        f'<dl class="detail">'
        f"<dt>Purpose</dt><dd>{_esc(t.purpose)}</dd>"
        f"<dt>Major activities</dt><dd>{', '.join(_esc(a) for a in t.activities) or '—'}</dd>"
        f"<dt>Dependencies</dt><dd>{', '.join(_esc(d) for d in t.dependencies) or 'None'}</dd>"
        f"<dt>Deliverable</dt><dd>{_esc(t.deliverable)}</dd>"
        f"<dt>Effort</dt><dd>{_esc(t.effort)}</dd>"
        f"<dt>Addresses</dt><dd>{_refs_html(t.addresses)}</dd>"
        f"</dl></div>"
        for t in delivery.workstreams
    )
    timeline_html = "".join(
        f'<div class="card"><b>{_esc(p.phase)}</b> · {_esc(p.duration)}'
        f"<p><b>Milestone:</b> {_esc(p.milestone)}</p>"
        f"<p>{', '.join(_esc(d) for d in p.deliverables)}</p></div>"
        for p in delivery.timeline
    )
    team_html = ", ".join(f"{_esc(r.role)} × {r.count}" for r in delivery.team_roles)
    body.append(
        '<section id="delivery"><h2>6. Delivery Plan</h2>'
        f'<h3>Workstreams</h3><div class="grid">{task_cards}</div>'
        f"<h3>Team</h3><p>{team_html or '—'}</p>"
        f'<h3>Timeline</h3><div class="grid">{timeline_html}</div>'
        f"<h3>Testing Strategy</h3>{_list_html(delivery.testing_strategy)}"
        f"<h3>Integration Testing</h3>{_list_html(delivery.integration_testing)}"
        f"<h3>UAT Strategy</h3>{_list_html(delivery.uat_strategy)}"
        f"<h3>Deployment / CI-CD</h3>{_list_html(list(delivery.deployment_strategy) + list(delivery.ci_cd))}"
        f"<h3>Monitoring &amp; Rollback</h3>{_list_html(list(delivery.monitoring) + list(delivery.rollback_strategy))}"
        f'<div class="summary-card"><p><b>Effort/complexity:</b> {_esc(delivery.effort_complexity)}</p>'
        f"<p><b>Implementation/team cost (indicative):</b> {_esc(delivery.cost_estimate.estimated_effort)}, "
        f"{_esc(delivery.cost_estimate.estimated_team_cost)}</p></div>"
        "</section>"
    )

    # 7. Risks
    risk_cards = "".join(
        f'<div class="card risk-card"><h3>{_esc(r.risk)}</h3>'
        f"<p><b>Impact:</b> {_esc(r.impact)}</p><p><b>Mitigation:</b> {_esc(r.mitigation)}</p></div>"
        for r in delivery.risks
    )
    body.append(
        '<section id="risks"><h2>7. Risks &amp; Mitigations</h2>'
        f'<div class="grid">{risk_cards}</div>'
        f"<h3>Business Risks</h3>{_list_html(requirements.risks)}"
        "</section>"
    )

    # 8-9. Assumptions/open questions, future evolution
    body.append(
        '<section id="assumptions"><h2>8. Assumptions &amp; Open Questions</h2>'
        f"<h3>Assumptions</h3>{_list_html(requirements.assumptions)}"
        f"<h3>Open Questions</h3>{_list_html(requirements.open_questions)}"
        f"<h3>Constraints</h3>{_list_html(requirements.constraints)}"
        "</section>"
    )
    body.append(
        '<section id="future"><h2>9. Future Evolution</h2>'
        f"{_list_html(list(requirements.future_scope) + list(architecture.future_evolution) + list(delivery.future_evolution))}"
        "</section>"
    )

    body.append(
        '<div class="footer">Generated by SolutionForge AI — advisory blueprint, not a substitute '
        "for professional engineering review.</div>"
    )

    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        "<title>Solution Blueprint</title>"
        f"<style>{_CSS}</style></head><body><div class=\"report\">"
        + "".join(body)
        + "</div></body></html>"
    )
