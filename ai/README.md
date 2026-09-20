# AI Layer — SolutionForge

CrewAI-powered multi-agent pipeline that turns a business idea and delivery
constraints into a structured, validated solution blueprint. This is the
`ai/` package's own reference doc — what each piece does, how they fit
together, and how to work with them. Product-level scope/contract docs live
in `docs/`.

## Public boundary

The rest of the system (a future FastAPI backend) talks to exactly one
function:

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

The backend never needs to know about individual agents, CrewAI, or repair
routing — all of that stays behind `generate_blueprint()`.

## Architecture

```
GenerateRequest (6 fields)
        |
        v
+-------------------+
|  Business Analyst  |  -> RequirementsOutput
+-------------------+
        |
        v
+-------------------+
| Solution Architect |  -> ArchitectureOutput
+-------------------+
        |
        v
+-------------------+
| Technology Advisor |  -> TechnologyOutput
+-------------------+
        |
        v
+-------------------+
|  Delivery Planner  |  -> DeliveryOutput
+-------------------+
        |
        v
+-------------------+
| Consistency        |  -> ValidationOutput
| Validator          |
+-------------------+
        |
   PASS |  FAIL
        |    \
        |     determine_repair_plan()  [ai/repair.py]
        |     -> run only the affected stage(s), then re-validate
        |     -> repeat until PASS, max iterations (3), or no
        |        actionable plan
        v
  BlueprintResponse
  (structured outputs + blueprint_md + blueprint_html + meta)
```

Every stage produces a strict, `extra="forbid"` Pydantic model — there is no
free-form text handoff between agents. Each stage's task is built with the
*actual* upstream Pydantic object(s) as input, not CrewAI's own inter-task
context passing.

## Folder layout

```
ai/
├── README.md            this file
├── config.py             LLM provider config + low-level HTTP client
├── crew.py                CrewAI execution: single-stage + full-pipeline runners
├── repair.py               Repair-plan routing (decides WHICH stages rerun)
├── service.py               Public boundary: generate_blueprint()
├── agents/                 One CrewAI Agent (role/goal/backstory) per stage
│   ├── business_analyst.py
│   ├── solution_architect.py
│   ├── technology_advisor.py
│   ├── delivery_planner.py
│   └── consistency_validator.py
├── tasks/                  One CrewAI Task builder per stage (prompt + expected output)
│   ├── business_analysis.py
│   ├── architecture.py
│   ├── technology.py
│   ├── delivery.py
│   └── validation.py
├── schemas/                 Pydantic contracts every stage's output must satisfy
│   ├── requirements.py     RequirementsOutput
│   ├── architecture.py     ArchitectureOutput
│   ├── technology.py       TechnologyOutput
│   ├── delivery.py         DeliveryOutput
│   ├── validation.py       ValidationOutput
│   └── response.py         BlueprintResponse (what generate_blueprint returns)
└── tests/                   Full suite — see "Testing" below (not pushed to GitHub)
```

## The agents

Each agent is intentionally narrow — every backstory explicitly states what
it must **never** do, so scope never silently creeps between stages.

### Business Analyst (`agents/business_analyst.py`, `tasks/business_analysis.py`)
Receives the six raw request fields. Produces `RequirementsOutput`: problem
statement, stakeholders, functional/non-functional requirements, MVP
priorities, future scope, assumptions, constraints, business risks, and
open clarifications. Never touches architecture, technology, or delivery
planning.

### Solution Architect (`agents/solution_architect.py`, `tasks/architecture.py`)
Receives the Business Analyst's `RequirementsOutput` (treated as ground
truth) plus traffic/timeline/country. Produces `ArchitectureOutput`:
architecture style, components + responsibilities, data flow, storage,
security, scalability, MVP architecture, future evolution. Stays
technology-neutral — never names a specific framework, database product, or
cloud vendor.

### Technology Advisor (`agents/technology_advisor.py`, `tasks/technology.py`)
Receives `RequirementsOutput` + `ArchitectureOutput` plus the original
tech/cloud preference, traffic, timeline, country. Produces
`TechnologyOutput`: per-component technology recommendations with
alternatives/reasons/trade-offs, cloud fit, open-source fit, lock-in
considerations, and an indicative infrastructure/service cost estimate
(ranges/qualified statements only, never false precision). Explicitly
respects `tech_preference` and `cloud_preference`.

### Delivery Planner (`agents/delivery_planner.py`, `tasks/delivery.py`)
Receives `RequirementsOutput` + `ArchitectureOutput` + `TechnologyOutput`
plus the delivery timeline. Produces `DeliveryOutput`: workstreams, team
roles/counts, timeline/milestones, dependencies, testing strategy,
deployment strategy, delivery risks + mitigations, effort/complexity, and an
indicative implementation/team cost estimate — kept explicitly separate
from the Technology Advisor's infrastructure cost.

### Consistency Validator (`agents/consistency_validator.py`, `tasks/validation.py`)
Receives all four upstream outputs plus every original constraint and the
current repair-iteration count. Cross-checks 8 categories (Requirements↔
Architecture, Architecture↔Technology, Technology↔Constraints, Scope↔
Timeline, Architecture/Technology↔Scale, Security, Delivery, Cost/Effort)
and produces `ValidationOutput`: overall PASS/FAIL, one entry per check
(name, status, issue, owner), and non-blocking warnings. Purely
diagnostic — it never redesigns, rewrites, or repairs anything itself.

**Ownership assignment** (who owns fixing a FAIL) is based on *which stage
would actually have to change its own output to fix the problem* — not
merely which category the check falls under. Example baked into the
prompt: if "appointment cancellation" is already a clear requirement but
the architecture doesn't explicitly show how it's handled, the owner is the
**Solution Architect**, not the Business Analyst. Every category's
prompt spells out this corrective-ownership split explicitly (see
`tasks/validation.py`).

## The repair loop

`ai/repair.py` (`determine_repair_plan`) decides *which* stages need to
rerun from a `ValidationOutput` — it never executes anything itself.
Routing rules per owner (each ends at the Validator):

| Failed check owner | Stages rerun |
|---|---|
| Business Analyst | BA → SA → TA → DP → Validator |
| Solution Architect | SA → TA → DP → Validator |
| Technology Advisor | TA → DP → Validator |
| Delivery Planner | DP → Validator |
| Cross-stage | BA → SA → TA → DP → Validator |

`ai/crew.py` (`run_stage`, `run_stages`) executes whatever plan it's given,
via an injectable `Stage -> executor` mapping. Each stage executor:
overwrites its own field, clears every *downstream* field (so a stale
output is never silently reused), and — only for the stage actually named
as the failing owner — receives the Validator's specific issue text
(`repair_issues`), stitched together in `ai/service.py`.

`generate_blueprint()` in `ai/service.py` ties it together: run the initial
pipeline once (`iterations=0`) → if FAIL, ask `ai.repair` for a plan →
execute it via `ai.crew` → re-validate → repeat until PASS, the plan is no
longer actionable, or `MAX_REPAIR_ITERATIONS` (3) is reached — then return
the best available result either way, never a fabricated PASS.

## Configuration

`ai/config.py` reads from the environment (and `.env`, via `python-dotenv`):

```
LLM_PROVIDER=openai            # or: openrouter
MODEL_NAME=gpt-4o-mini         # or e.g. openai/gpt-4o-mini for openrouter
OPENAI_API_KEY=...             # exactly one of these two, matching LLM_PROVIDER
OPENROUTER_API_KEY=...
```

Two construction points, deliberately separate:
- `get_llm()` — CrewAI-facing; returns a real `crewai.LLM` for
  `Agent(llm=...)`. This is what every agent uses.
- `get_llm_client()` — low-level; always returns our own `LLMClient`
  (`.complete(prompt) -> str`), used only by the standalone connectivity
  check, never by agents.

## Testing

`ai/tests/` (kept local, not pushed to GitHub — see repo `.gitignore`) is
split consistently across every module:
- Fast, unconditional tests: schema validation, prompt/scope content,
  routing logic, orchestration structure — no CrewAI or network needed.
- CrewAI-dependent construction tests: build real `Agent`/`Task` objects,
  with `Crew.kickoff()` mocked so no real LLM call happens.
- One opt-in live connectivity smoke test, skipped unless real credentials
  are configured.

Run everything: `python -m pytest ai/tests -v`

## Current status

The five-agent pipeline, repair loop, and service boundary are all built,
tested (279 tests, no real LLM calls), and verified against real OpenAI
calls end-to-end. Known open item: even with correct ownership routing, a
targeted repair does not always converge to PASS within the 3-iteration
cap in real runs — the diagnosis is now reliably correct, but the
correction the repaired stage produces doesn't always satisfy the
Validator on the first few tries. Not yet root-caused.

Not yet built: `service.py`'s caller (FastAPI), Firebase auth, MongoDB
persistence, Streamlit frontend, Serper/web-search integration.
