# 06 — FINAL SYSTEM ARCHITECTURE v3

```text
                         +----------------------+
                         |        User          |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         |      Streamlit       |
                         |      Frontend        |
                         +----+------------+----+
                              |            |
                      Google Sign-In      |
                              |            |
                              v            |
                       +-------------+     |
                       |  Firebase   |     |
                       |    Auth     |     |
                       +------+------+     |
                              |            |
                       Firebase ID Token   |
                              |            |
                              +-----+------+
                                    |
                           Bearer Token + JSON
                                    |
                                    v
                         +----------------------+
                         |       FastAPI        |
                         | Auth / Validation /  |
                         | Persistence / Report |
                         +----+-----------+-----+
                              |           |
                     generate_blueprint()|
                              |           +------------------+
                              v                              |
                   +----------------------+                 |
                   |      AI / CrewAI     |                 |
                   |                      |                 |
                   | BA -> SA -> TA -> DP |                 |
                   |        |             |                 |
                   |        v             |                 |
                   |   Consistency        |                 |
                   |   Validator          |                 |
                   |        |             |                 |
                   |   PASS / REPAIR      |                 |
                   +----------+-----------+                 |
                              |                             |
                              v                             v
                    +------------------+           +------------------+
                    | BlueprintResponse|           |  MongoDB Atlas   |
                    | Markdown + data  |           | users/projects/  |
                    +--------+---------+           | generations      |
                             |                     +------------------+
                             v
                    Markdown -> Jinja2 HTML
                             |
                             v
                         Streamlit
                      Results + Download
```

## Critical boundaries
1. Firebase = authentication/identity.
2. MongoDB = application persistence.
3. FastAPI = security + persistence + report boundary.
4. AI = business/technical reasoning only.
5. Frontend = presentation/client interaction only.

## Optional components
- Serper.dev for current technology/cloud information.
- Docker for packaging/deployment.
- RAG/vector database only as future enhancement.

## No MVP requirement for
- payment system
- billing engine
- ML training
- Kubernetes
- independent risk agent
- independent research agent
- independent cost agent
