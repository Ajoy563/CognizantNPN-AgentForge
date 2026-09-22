# AI Layer — SolutionForge

CrewAI-powered pipeline that turns a business idea and six delivery
constraints into a structured solution blueprint: requirements,
architecture (with a generated diagram), technology decisions, and a
delivery plan — rendered as self-contained Markdown and HTML. This is the
`ai/` package's own reference doc — what each piece does, how they fit
together, and how to work with them. Product-level scope/contract docs
live in `docs/`.

## Public boundary

The rest of the system (the FastAPI backend, via `Backend/app/services/
ai_service.py`) talks to exactly one function:

```python
from ai.service import generate_blueprint, GenerateRequest

response = generate_blueprint(GenerateRequest(
    business_idea="...",
    tech_preference="opensource",   # or "enterprise"
    cloud_preference="aws",         # "aws" | "azure" | "gcp" | "none"
    expected_daily_traffic=2000,
    delivery_timeline_months=4,
    country="India",
))
# response: ai.schemas.response.BlueprintResponse
```

The caller never needs to know about individual agents or CrewAI — all of
that stays behind `generate_blueprint()`.

## Architecture

```
GenerateRequest (6 fields)
        |
        v
+---------------------+
|  Business Analyst    |  ->  RequirementsOutput
+---------------------+
        |
        v
+---------------------+
| Solution Architect   |  ->  ArchitectureOutput
+---------------------+
        |
        v
+---------------------+
| Technology Advisor   |  ->  TechnologyOutput   (optional Serper web search)
+---------------------+
        |
        v
+---------------------+
|  Delivery Planner    |  ->  DeliveryOutput
+---------------------+
        |
        v
  apply_completion_patch()          [ai/completion.py — plain Python, no LLM]
  closes obvious requirement/component/technology/workstream gaps in one pass
        |
        v
  render_blueprint_markdown() + render_blueprint_html()   [ai/report/]
        |
        v
  BlueprintResponse
  (requirements, architecture, technology, delivery, blueprint_md,
   blueprint_html, meta)
```

Every stage produces a strict, `extra="forbid"` Pydantic model — there is
no free-form text handoff between agents. Each stage's task is built with
the *actual* upstream Pydantic object(s) as input, not CrewAI's own
inter-task context passing. That gives 4 LLM calls per blueprint (one per
agent), plus up to 3 optional web searches by the Technology Advisor.

There is no validator agent and no repair loop. An earlier design had
both; it was replaced because the loop added real latency (multi-minute
runs), extra LLM calls, and surfaced internal check language to users.
The single deterministic completion patch is faster, cheaper, and easier
to reason about — see "The completion patch" below for what it does and
does not catch.

## Folder layout

```
ai/
├── README.md              this file
├── config.py               LLM provider config + low-level HTTP client
├── crew.py                 CrewAI execution: single-stage + full-pipeline runners
├── completion.py           Post-pipeline gap-repair patch (no LLM)
├── service.py               Public boundary: generate_blueprint()
├── agents/                  One CrewAI Agent (role/goal/backstory) per stage
│   ├── business_analyst.py
│   ├── solution_architect.py
│   ├── technology_advisor.py
│   └── delivery_planner.py
├── tasks/                   One CrewAI Task builder per stage (prompt + expected output)
│   ├── business_analysis.py
│   ├── architecture.py
│   ├── technology.py
│   └── delivery.py
├── schemas/                  Pydantic contracts every stage's output must satisfy
│   ├── requirements.py      RequirementsOutput
│   ├── architecture.py      ArchitectureOutput
│   ├── technology.py        TechnologyOutput
│   ├── delivery.py          DeliveryOutput
│   └── response.py          BlueprintResponse (what generate_blueprint returns)
├── report/                   Deterministic rendering — no LLM involved
│   ├── markdown.py          render_blueprint_markdown()
│   ├── html.py               render_blueprint_html() (self-contained, no CDN)
│   ├── diagram.py            render_architecture_diagram_svg() — embedded in the HTML
│   └── title.py               derive_project_title()
├── tools/
│   └── serper_search.py     Optional web search tool, Technology Advisor only
└── tests/                    Full suite — see "Testing" below (not pushed to GitHub)
```

## The agents

Each agent is intentionally narrow — every backstory explicitly states
what it must **never** do, so scope never silently creeps between stages.
All four share MVP-scoping instructions: keep it proportionate to a real
MVP, don't invent enterprise scope the idea doesn't call for.

### Business Analyst (`agents/business_analyst.py`, `tasks/business_analysis.py`)
Receives the six raw request fields. Produces `RequirementsOutput`:
problem statement, business context, goals, personas, stakeholders, a
flat list of `REQ-001…` requirements (category + must/should/could
priority), MVP requirement ids + MVP focus, future scope, assumptions,
open questions, constraints, and business risks. Targets roughly 6–12
requirements — a practical MVP, not an enterprise programme. Never
touches architecture, technology, or delivery planning.

### Solution Architect (`agents/solution_architect.py`, `tasks/architecture.py`)
Receives the Business Analyst's `RequirementsOutput` (treated as ground
truth) plus traffic/timeline/country. Produces `ArchitectureOutput`:
architecture style + rationale, components (`ARCH-001…`, each with layer,
purpose, responsibility, interfaces, security/scalability notes, and a
`satisfies` list of requirement ids), data flow, request/authentication
flow, storage/caching/messaging, security controls (`SEC-001…`),
scalability/availability/disaster-recovery strategy, deployment
architecture, MVP vs future architecture. Defaults to a simple modular
monolith and roughly 5–10 components — one component may satisfy several
requirements, rather than one component per requirement. Stays
technology-neutral — never names a specific framework, database product,
or cloud vendor.

### Technology Advisor (`agents/technology_advisor.py`, `tasks/technology.py`)
Receives `RequirementsOutput` + `ArchitectureOutput` plus the original
tech/cloud preference, traffic, timeline, country. Produces
`TechnologyOutput`: technology decisions (`TECH-001…`, each with the
components it `supports`, the requirements it serves, reason,
alternatives, trade-offs, cost considerations, provider dependency,
portability risk, and migration mitigation), cloud fit, open-source fit,
overall lock-in assessment, and an indicative infrastructure cost
estimate. Targets roughly 5–8 decisions — one decision may support
several components. Explicitly respects `tech_preference` and
`cloud_preference`. The only agent with an optional web search tool (see
"Optional web search" below).

### Delivery Planner (`agents/delivery_planner.py`, `tasks/delivery.py`)
Receives `RequirementsOutput` + `ArchitectureOutput` + `TechnologyOutput`
plus the delivery timeline. Produces `DeliveryOutput`: workstreams
(`TASK-001…`, each with an `addresses` list of requirement/component
ids), milestones, dependencies, team roles/counts, timeline phases,
testing/UAT strategy, deployment/CI-CD, monitoring, rollback strategy,
delivery risks + mitigations, effort/complexity, and an indicative
implementation/team cost estimate — kept explicitly separate from the
Technology Advisor's infrastructure cost. Plans the MVP that fits the
stated timeline, not every future capability.

## The completion patch

`ai/completion.py` (`apply_completion_patch`) runs once, after the
Delivery Planner, in plain Python — no LLM call, no agent rerun, no loop.
It closes three kinds of structural gaps, in dependency order:

1. A must-priority or MVP requirement that no architecture component or
   security control claims — attached to the component whose layer best
   fits the requirement's category.
2. An architecture component that no technology decision supports —
   attached to the technology decision whose category/name/purpose best
   matches the component's layer.
3. An architecture component that no delivery workstream addresses — a
   new workstream is added only if nothing already covers it.

It never rewrites existing content, never re-runs a stage, and nothing it
does is reported to the user. It matches by id and by simple layer/keyword
rules, not by meaning — see `ai/tests/test_completion.py` for exact
behaviour and edge cases.

## Optional web search

`ai/tools/serper_search.py` wires in Serper.dev web search, available
only to the Technology Advisor. Disabled unless `SERPER_API_KEY` is set;
the pipeline works identically without it. Bounded to `MAX_SERPER_SEARCHES
= 3` searches with `SERPER_RESULTS_PER_SEARCH = 5` results each, and
`tool_failure_policy=WARN` so a failed/slow/unusable search never aborts
the stage — the agent just continues on its own knowledge. No other
module reads `SERPER_API_KEY`.

## Report rendering

`ai/report/` builds the two output documents from the four structured
outputs — pure string templating, fully deterministic, no LLM involved:

- **`markdown.py`** — `render_blueprint_markdown()`: a 9-section plain-text
  blueprint (Executive Summary, Requirements, Architecture, Technical
  Architecture Diagram (as layered text), Technology Decisions, Delivery
  Plan, Risks & Mitigations, Assumptions & Open Questions, Future
  Evolution).
- **`html.py`** — `render_blueprint_html()`: the same 9 sections as a
  single self-contained HTML file — embedded CSS, no external CDN/asset,
  works fully offline. Includes a requirement traceability table and a
  technology decision matrix built by cross-referencing ids across the
  four schemas. All AI-generated text is HTML-escaped before insertion.
- **`diagram.py`** — `render_architecture_diagram_svg()`: a layered SVG
  diagram (users → presentation → application → data → infrastructure)
  built from each component's `layer`, embedded directly in the HTML
  report. Long component names are truncated with "…".
- **`title.py`** — `derive_project_title()`: a short report title derived
  from the problem statement and business goals.

The backend prints the stored HTML to PDF on demand (headless
Chrome/Edge, `Backend/app/services/report_service.py`) — that PDF
generation lives in the backend, not in `ai/`, since it needs a browser
binary rather than any AI-layer logic.

## Configuration

`ai/config.py` reads from the environment (and `.env`, via
`python-dotenv`):

```
LLM_PROVIDER=openai            # or: openrouter
MODEL_NAME=gpt-4o-mini         # or e.g. openai/gpt-4o-mini for openrouter
OPENAI_API_KEY=...             # exactly one of these two, matching LLM_PROVIDER
OPENROUTER_API_KEY=...
SERPER_API_KEY=...             # optional — enables Technology Advisor web search
```

Two construction points, deliberately separate:
- `get_llm()` — CrewAI-facing; returns a real `crewai.LLM` for
  `Agent(llm=...)`. This is what every agent uses.
- `get_llm_client()` — low-level; always returns our own `LLMClient`
  (`.complete(prompt) -> str`), used only by the standalone connectivity
  check, never by agents.

Swapping the model or provider is a `.env` change, not a code change —
no agent or task file ever reads `LLM_PROVIDER`/`MODEL_NAME`/API keys
directly.



| File | Covers |
|---|---|
| `test_schemas.py` | Schema validation: required fields, id patterns, invalid values |
| `test_agents_and_tasks.py` | All 4 agents/tasks: schema references, scope isolation, prompt content, real CrewAI Agent/Task construction |
| `test_crew.py` | Stage orchestration, `StageContext` threading, failure propagation, real CrewAI Crew construction (`Crew.kickoff()` mocked) |
| `test_completion.py` | The completion patch's three repair rules and their edge cases |
| `test_diagram.py` | SVG diagram generation from architecture data |
| `test_title.py` | Report title derivation |
| `test_service.py` | `generate_blueprint()` end-to-end control flow, mocked pipeline |
| `test_serper_tool.py` | Serper tool isolation — only the Technology Advisor gets it |
| `test_llm_connection.py` | One opt-in live connectivity smoke test, skipped unless real credentials are configured |

Run everything: `python -m pytest ai/tests -v`

## Current status

The four-agent pipeline, completion patch, report rendering, and service
boundary are all built and tested, and verified against real OpenAI
calls end-to-end (real generations observed at roughly 60–155 seconds).
Wired into the FastAPI backend and the React frontend.

Known open items:
- Output quality depends on the configured model (currently
  `gpt-4o-mini`) and is not fact-checked; treat generated blueprints as a
  first draft for human review, not a final design.
- The completion patch only guarantees links at the component level —
  the HTML report's traceability matrix can still show an empty cell for
  a requirement that is only indirectly covered (e.g. through a component
  rather than a direct `requirements`/`addresses` reference).
- No lower-temperature/determinism setting yet — two runs on identical
  input can produce different wording, counts, and choices.
- No prompt-injection hardening yet — user-supplied text (`business_idea`,
  `country`) is interpolated directly into prompts with no delimiters. The
  generated report itself is safe to render (all text is HTML-escaped),
  but a crafted idea can currently steer an agent's own output (e.g. its
  problem-statement text).
