# SolutionForge AI — Final Team Specification v3

## 1. Source-aligned scope
The Cognizant problem statement defines SolutionForge AI as a CrewAI-powered multi-agent solution blueprint generator that transforms a business idea and delivery constraints into a practical consulting-style blueprint. The official workflow is sequential:

Business Analyst -> Solution Architect -> Technology Advisor -> Delivery Planner

The official user inputs are exactly six:
1. Business Idea / Problem Statement
2. Technology Preference: open-source or enterprise
3. Cloud Preference: AWS, Azure, GCP, or no specific cloud preference
4. Expected Daily Traffic
5. Delivery Timeline in months
6. Country where data will be hosted

The official blueprint covers delivery overview, MVP scope/priorities, technology stack, workstreams, team/roles, timeline/milestones, effort & complexity, dependencies, architecture, testing, deployment, risks/mitigations, future evolution, and assumptions/open questions.

## 2. Team-added product decisions
These are additions chosen by the team; they are not mandatory source requirements:
- Firebase Authentication with Google Sign-In
- MongoDB Atlas for application persistence
- Project and generation history
- Consistency Validator after Delivery Planner
- Targeted repair loop with a maximum of 2 repair iterations by default
- Indicative cost estimation inside Technology Advisor and Delivery Planner
- Docker packaging for deployment

## 3. Core architecture
User -> Streamlit -> Firebase Auth -> FastAPI -> CrewAI workflow -> Validator/Repair -> Blueprint -> MongoDB persistence + Streamlit results/download.

## 4. Boundary rules
- Streamlit never connects directly to MongoDB.
- AI agents never connect directly to Firebase or MongoDB.
- FastAPI is the HTTP, authentication, authorization, validation, persistence, and report-rendering boundary.
- AI exposes one public application service function: `generate_blueprint(request) -> BlueprintResponse`.
- The AI layer never receives Firebase UID/token for reasoning.
- Frontend never owns CrewAI prompts or business reasoning.

## 5. AI workflow
```text
GenerateRequest
    |
    v
Business Analyst
    |
    v
RequirementsOutput
    |
    v
Solution Architect
    |
    v
ArchitectureOutput
    |
    v
Technology Advisor ---- optional Serper.dev
    |
    v
TechnologyOutput
    |
    v
Delivery Planner
    |
    v
DeliveryOutput
    |
    v
Consistency Validator
    |
    +---- PASS ----> BlueprintResponse
    |
    +---- FAIL ---> targeted repair of the affected stage(s)
                         |
                         +---- Validator again
                         |
                         +---- max 2 repair iterations
```

## 6. Cost model
Cost is an advisory estimate, not a billing engine.

Technology Advisor owns:
- indicative infrastructure/cloud/service cost range
- assumptions behind that range

Delivery Planner owns:
- indicative implementation effort
- indicative team/implementation cost range
- assumptions behind that range

Do not present false precision. Use ranges and assumptions. If cost cannot be estimated responsibly from the supplied information, return a clearly qualified statement such as `Not enough information for a reliable estimate`.

## 7. Risk ownership
Do not create a separate Risk Agent.

Delivery Planner owns delivery risks and mitigations as required by the source. The Validator may check risk-related consistency but does not become a fifth consulting agent.

## 8. MVP exclusions
No payments, billing, ML training pipeline, mandatory RAG/vector database, Kubernetes, or unrelated enterprise features.

RAG may be added later as an optional knowledge layer. Serper is optional and used only by the Technology Advisor.

## 9. Team integration contract
Frontend sends a Firebase bearer token plus the exact six-field generation request.
FastAPI verifies the token, validates the request, calls `generate_blueprint()`, persists the project/generation, renders the report, and returns the documented response.

## 10. Definition of done
The team should be able to:
1. sign in with Google through Firebase,
2. submit the six official inputs,
3. run the sequential AI workflow,
4. receive a structured blueprint with validation status,
5. see indicative effort/cost ranges with assumptions,
6. persist the generation in MongoDB Atlas,
7. view generation history,
8. download the styled HTML report,
9. change constraints and demonstrate that the recommendations, architecture, timeline and cost/effort adapt.
