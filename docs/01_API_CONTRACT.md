# 01 — MASTER API CONTRACT v3

## 1. Authentication
Protected endpoints require:
```http
Authorization: Bearer <Firebase ID token>
```

FastAPI verifies the token with Firebase Admin SDK and derives the UID from the verified token. Never trust a user-supplied UID.

## 2. POST /generate

### Request
```json
{
  "business_idea": "string",
  "tech_preference": "opensource|enterprise",
  "cloud_preference": "aws|azure|gcp|none",
  "expected_daily_traffic": 20000,
  "delivery_timeline_months": 6,
  "country": "India"
}
```

Validation:
- `business_idea`: non-empty string
- `tech_preference`: one of `opensource`, `enterprise`
- `cloud_preference`: one of `aws`, `azure`, `gcp`, `none`
- `expected_daily_traffic`: integer > 0
- `delivery_timeline_months`: integer > 0
- `country`: non-empty string

### Success response
```json
{
  "status": "success",
  "project_id": "string",
  "generation_id": "string",
  "requirements": {},
  "architecture": {},
  "technology": {},
  "delivery": {},
  "validation": {},
  "blueprint_md": "string",
  "blueprint_html": "string",
  "meta": {
    "model": "string",
    "duration_seconds": 0.0,
    "repair_iterations": 0
  }
}
```

## 3. Other endpoints
- `GET /health` — public health check
- `GET /projects` — current authenticated user's projects
- `GET /projects/{project_id}` — current authenticated user's project detail

Ownership must be enforced server-side.

## 4. Error response
```json
{
  "status": "error",
  "code": "VALIDATION_ERROR",
  "message": "string",
  "details": {}
}
```

Error codes:
- `AUTH_REQUIRED` (401)
- `AUTH_INVALID` (401)
- `FORBIDDEN` (403)
- `VALIDATION_ERROR` (400)
- `MODEL_RATE_LIMIT` (429)
- `AI_GENERATION_ERROR` (500)
- `REPORT_GENERATION_ERROR` (500)
- `DATABASE_ERROR` (500)

## 5. AI service boundary
```python
from ai.service import generate_blueprint

result: BlueprintResponse = generate_blueprint(request)
```

FastAPI should call only this public AI service boundary, not individual CrewAI agents/tasks.

## 6. Internal structured outputs
The following Pydantic schemas are internal AI contracts. They are not the same thing as HTTP request/response schemas.

### RequirementsOutput
- `problem: str`
- `stakeholders: list[str]`
- `functional_requirements: list[str]`
- `non_functional_requirements: list[str]`
- `mvp_priorities: list[str]`
- `future_scope: list[str]`
- `assumptions: list[str]`
- `constraints: list[str]`
- `risks: list[str]`
- `clarifications: list[str]`

### ArchitectureOutput
- `architecture_style: str`
- `components: list[{name: str, responsibility: str}]`
- `data_flow: list[str]`
- `storage: list[str]`
- `security: list[str]`
- `scalability: list[str]`
- `mvp_architecture: list[str]`
- `future_evolution: list[str]`

### TechnologyOutput
```text
recommendations: [
  {
    component: str,
    recommended: str,
    alternatives: list[str],
    reason: str,
    tradeoffs: list[str]
  }
]
cloud_fit: str
open_source_fit: str
lock_in_considerations: str
cost_estimate: {
  infrastructure_monthly: str,
  implementation: str,
  assumptions: list[str]
}
```

`cost_estimate` is indicative only and must use ranges/assumptions rather than false precision.

### DeliveryOutput
```text
workstreams: list[str]
team_roles: [{role: str, count: int}]
timeline: [{phase: str, duration: str, deliverables: list[str]}]
dependencies: list[str]
testing_strategy: list[str]
deployment_strategy: list[str]
risks: [{risk: str, impact: str, mitigation: str}]
effort_complexity: str
cost_estimate: {
  estimated_effort: str,
  estimated_team_cost: str,
  assumptions: list[str]
}
future_evolution: list[str]
```

### ValidationOutput
```text
status: "PASS" | "FAIL"
iterations: int
checks: [
  {
    name: str,
    status: "PASS" | "FAIL",
    issue: str | null,
    owner: "Business Analyst" | "Solution Architect" | "Technology Advisor" | "Delivery Planner" | "Cross-stage" | null
  }
]
warnings: list[str]
```

Validator checks must include cost/effort consistency when cost is present.

## 7. Final BlueprintResponse
```text
status: "success"
project_id: str
requirements: RequirementsOutput
architecture: ArchitectureOutput
technology: TechnologyOutput
delivery: DeliveryOutput
validation: ValidationOutput
blueprint_md: str
blueprint_html: str
meta: {
  model: str,
  duration_seconds: float,
  repair_iterations: int
}
```
