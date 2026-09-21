# ⚡ SolutionForge AI

> **Turn a business idea into a consulting-style solution blueprint — powered by AI agents.**

🌐 **Live Demo:**  
👉 https://solutionforge-ai.vercel.app

---

## 🚀 What is SolutionForge AI?

SolutionForge AI transforms a **business idea + delivery constraints** into a structured software solution blueprint.

Instead of manually going through requirements, architecture, technology selection, and delivery planning, our AI-powered workflow handles these stages through specialized agents.

### 💡 Idea → 🤖 AI Consultation → 🏗️ Architecture → 🛠️ Technology → 📅 Delivery

---

## ✨ Key Features

- 🧠 **Business Analysis** — identifies goals, users, requirements and scope
- 🏗️ **Solution Architecture** — creates a scalable high-level architecture
- 🛠️ **Technology Selection** — recommends technologies based on project constraints
- 📅 **Delivery Planning** — creates workstreams, milestones, effort and risks
- 📄 **Blueprint Reports** — generate downloadable HTML/PDF reports
- 🔐 **Firebase Authentication** — secure user authentication
- 💾 **MongoDB Storage** — stores projects and generated blueprints
- ☁️ **Cloud-aware Recommendations** — supports AWS, Azure, GCP or no preference

---

## 🤖 Multi-Agent AI Workflow

```text
                    💡 Business Idea
                          │
                          ▼
                ┌──────────────────┐
                │ Business Analyst │
                └────────┬─────────┘
                         ▼
                ┌──────────────────┐
                │Solution Architect│
                └────────┬─────────┘
                         ▼
                ┌──────────────────┐
                │Technology Advisor│
                └────────┬─────────┘
                         ▼
                ┌──────────────────┐
                │ Delivery Planner │
                └────────┬─────────┘
                         ▼
                 📋 Solution Blueprint
```

## 📂 Project Structure

```text
SolutionForge-AI/
│
├── 📁 Backend/
│   │
│   ├── 📁 app/
│   │   ├── 📁 api/
│   │   │   └── routes.py
│   │   │
│   │   ├── 📁 auth/
│   │   │   ├── firebase.py
│   │   │   └── dependencies.py
│   │   │
│   │   ├── 📁 core/
│   │   │   ├── config.py
│   │   │   └── errors.py
│   │   │
│   │   ├── 📁 db/
│   │   │   ├── mongodb.py
│   │   │   └── 📁 repositories/
│   │   │       ├── users.py
│   │   │       ├── projects.py
│   │   │       └── generations.py
│   │   │
│   │   ├── 📁 schemas/
│   │   │   ├── requests.py
│   │   │   └── responses.py
│   │   │
│   │   ├── 📁 services/
│   │   │   ├── ai_service.py
│   │   │   ├── project_service.py
│   │   │   ├── generation_service.py
│   │   │   └── report_service.py
│   │   │
│   │   └── main.py
│   │
│   ├── 📁 tests/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── .env.example
│   └── .gitignore
│
├── 📁 Frontend/
│   │
│   ├── 📁 public/
│   │   └── ...
│   │
│   ├── 📁 src/
│   │   ├── 📁 assets/
│   │   ├── 📁 components/
│   │   ├── 📁 pages/
│   │   ├── 📁 services/
│   │   ├── 📁 styles/
│   │   ├── App.jsx
│   │   └── main.jsx
│   │
│   ├── index.html
│   ├── package.json
│   ├── package-lock.json
│   ├── vite.config.js
│   └── .gitignore
│
├── 📁 ai/
│   │
│   ├── 📁 agents/
│   │   ├── business_analyst.py
│   │   ├── solution_architect.py
│   │   ├── technology_advisor.py
│   │   ├── delivery_planner.py
│   │   └── consistency_validator.py
│   │
│   ├── 📁 tasks/
│   │   ├── business_analysis.py
│   │   ├── architecture.py
│   │   ├── technology.py
│   │   ├── delivery.py
│   │   └── validation.py
│   │
│   ├── 📁 schemas/
│   │   ├── requirements.py
│   │   ├── architecture.py
│   │   ├── technology.py
│   │   ├── delivery.py
│   │   ├── response.py
│   │   └── __init__.py
│   │
│   ├── 📁 tools/
│   │   └── ...
│   │
│   ├── 📁 report/
│   │   └── ...
│   │
│   ├── 📁 tests/
│   │   └── ...
│   │
│   ├── config.py
│   ├── crew.py
│   ├── completion.py
│   ├── service.py
│   └── README.md
│
├── .gitignore
├── README.md
└── Dockerfile
```

## 🏗️ System Architecture

```text
                         👤 USER
                           │
                           ▼
                ┌─────────────────────┐
                │    React + Vite     │
                │      Frontend       │
                └──────────┬──────────┘
                           │
                    Firebase Token
                           │
                           ▼
                ┌─────────────────────┐
                │       FastAPI       │
                │       Backend       │
                └──────────┬──────────┘
                           │
              ┌────────────┴────────────┐
              │                         │
              ▼                         ▼
       ┌─────────────┐          ┌──────────────┐
       │   MongoDB   │          │  AI Service  │
       │   Database  │          └──────┬───────┘
       └─────────────┘                 │
                                      ▼
                         ┌────────────────────────┐
                         │    CrewAI Workflow     │
                         │                        │
                         │ Business Analyst       │
                         │         ↓              │
                         │ Solution Architect     │
                         │         ↓              │
                         │ Technology Advisor     │
                         │         ↓              │
                         │ Delivery Planner       │
                         └───────────┬────────────┘
                                     │
                                     ▼
                           📋 Solution Blueprint
                                     │
                              ┌──────┴──────┐
                              ▼             ▼
                             HTML          PDF
```
