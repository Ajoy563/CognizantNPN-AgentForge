# 02 — AI / CREWAI SPEC v3

## 1. AI layer responsibilities
Owns:
- CrewAI agents
- CrewAI tasks
- prompts
- internal Pydantic schemas
- sequential orchestration
- optional Serper integration
- consistency validation
- targeted repair loop
- final blueprint Markdown generation

Does not own:
- Firebase
- MongoDB
- HTTP/API routing
- Streamlit
- CORS
- Firebase Admin authentication
- report download endpoint

## 2. Input contract
The AI receives the normalized generation request containing exactly:
- business_idea
- tech_preference
- cloud_preference
- expected_daily_traffic
- delivery_timeline_months
- country

The AI does not receive Firebase UID or authentication tokens.

## 3. Agent 1 — Business Analyst
Receives all six normalized inputs.

Produces:
- business problem statement
- users/stakeholders
- functional requirements
- non-functional requirements
- MVP priorities
- future scope
- assumptions
- constraints
- business risks
- clarifications/open questions

Rules:
- do not select the final technology stack
- keep MVP practical
- distinguish known requirements from assumptions

## 4. Agent 2 — Solution Architect
Receives BA output plus original constraints.

Produces:
- architecture style
- major components and responsibilities
- data flow
- storage approach
- security controls
- scalability approach
- MVP architecture
- future evolution

Rules:
- architecture must satisfy requirements and traffic
- respect delivery timeline
- avoid unnecessary over-engineering

## 5. Agent 3 — Technology Advisor
Receives BA output, Architecture output and original constraints.

Produces:
- specific technology recommendations per major component
- alternatives
- rationale
- trade-offs
- scale/security/complexity considerations
- cloud fit
- open-source/enterprise fit
- lock-in considerations
- indicative infrastructure/service cost range and assumptions

Rules:
- explicitly respect `tech_preference`
- explicitly respect `cloud_preference`
- cost is advisory, not a billing calculation
- do not invent precise cloud bills without assumptions

### Optional Serper
Serper.dev may be enabled only for the Technology Advisor to retrieve current technology/cloud information.
The workflow must still work when Serper is disabled.

## 6. Agent 4 — Delivery Planner
Receives BA + Architecture + Technology outputs and original constraints.

Produces:
- implementation workstreams
- team roles and counts
- timeline and milestones
- dependencies/prerequisites
- testing strategy
- deployment/release strategy
- delivery risks and mitigations
- effort & complexity assessment
- indicative implementation/team cost range and assumptions
- future evolution

Rules:
- timeline must fit `delivery_timeline_months`
- team composition must be plausible for the scope
- cost/effort estimates must be clearly qualified

## 7. Consistency Validator
This is a quality-control stage, not a replacement for any official consulting agent.

Checks:
1. requirements -> architecture coverage
2. architecture -> technology fit
3. technology -> technology preference fit
4. technology/cloud -> cloud preference fit
5. expected traffic -> architecture/scalability fit
6. MVP scope -> timeline fit
7. architecture/security -> security requirement fit
8. technology/effort -> delivery timeline fit
9. implementation effort -> team composition fit
10. infrastructure cost -> selected technology and scale fit
11. implementation/team cost -> team size and timeline fit

Output:
- PASS or FAIL
- individual checks
- issue description when FAIL
- owner stage when a targeted repair is possible
- warnings
- iteration count

## 8. Targeted repair loop
The system must not blindly rerun every stage for every validation failure.

Repair routing:
- timeline issue -> Delivery Planner -> Validator
- technology mismatch -> Technology Advisor -> Delivery Planner -> Validator
- cloud/technology issue -> Technology Advisor -> Delivery Planner -> Validator
- architecture mismatch -> Solution Architect -> Technology Advisor -> Delivery Planner -> Validator
- requirement issue -> Business Analyst -> Solution Architect -> Technology Advisor -> Delivery Planner -> Validator
- cross-stage cost inconsistency -> rerun the affected owner stage and downstream stages -> Validator

Default `MAX_REPAIR_ITERATIONS=2`.
Maximum allowed by implementation: 3.

If validation still fails after the configured maximum, return the best available blueprint with warnings rather than looping indefinitely.

## 9. Timeouts
Recommended bounded timeouts:
- frontend `/generate` HTTP client: 300 seconds
- individual LLM call: 60–90 seconds where supported
- Serper: 15–30 seconds
- database operations: bounded driver/server/client timeouts

## 10. AI folder structure
```text
ai/
├── service.py
├── crew.py
├── config.py
├── agents/
│   ├── business_analyst.py
│   ├── solution_architect.py
│   ├── technology_advisor.py
│   ├── delivery_planner.py
│   └── consistency_validator.py
├── tasks/
│   ├── business_analysis.py
│   ├── architecture.py
│   ├── technology.py
│   ├── delivery.py
│   └── validation.py
├── schemas/
│   ├── request.py
│   ├── requirements.py
│   ├── architecture.py
│   ├── technology.py
│   ├── delivery.py
│   ├── validation.py
│   └── response.py
├── prompts/
│   ├── business_analyst.md
│   ├── solution_architect.md
│   ├── technology_advisor.md
│   ├── delivery_planner.md
│   └── consistency_validator.md
├── tools/
│   └── serper_search.py
└── tests/
    ├── test_schemas.py
    ├── test_agents.py
    ├── test_crew.py
    ├── test_validator.py
    └── test_service.py
```

## 11. Provider configuration
The AI implementation must keep the LLM provider/model configurable through environment/configuration.

Recommended variables:
```text
LLM_PROVIDER=openai|openrouter
MODEL_NAME=<provider model name>
OPENAI_API_KEY=<optional depending on provider>
OPENROUTER_API_KEY=<optional depending on provider>
```

Do not hard-code one provider inside agent classes.
