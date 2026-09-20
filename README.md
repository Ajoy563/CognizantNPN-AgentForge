# CognizantNPN-AgentForge
# Backend
 This directory contains the backend application for the project.

 ## Project Structure

```
backend/
└── app/
    ├── main.py
    ├── api/
    │   └── routes/
    │       ├── blueprint.py
    │       └── health.py
    ├── schemas/
    │   └── consultation.py
    ├── services/
    │   └── consultation_service.py
    └── core/
        ├── config.py
        └── exceptions.py
```

 ## Folder & File Description

 | File / Folder | Description |
| --- | --- |
| `main.py` | Main entry point of the backend application |
| `api/routes/` | Contains API route definitions |
| `blueprint.py` | Registers and organizes API routes |
| `health.py` | Contains health-check API endpoints |
| `schemas/` | Contains request and response schemas |
| `consultation.py` | Defines consultation-related data models and validation |
| `services/` | Contains application business logic |
| `consultation_service.py` | Handles consultation-related business logic |
| `core/` | Contains core application configuration and utilities |
| `config.py` | Manages application configuration |
| `exceptions.py` | Defines custom application exceptions |

## Architecture

 The backend follows a layered architecture:

```
Client
  │
  ▼
API Routes
  │
  ▼
Schemas / Validation
  │
  ▼
Service Layer
  │
  ▼
Core / Configuration
```

 ## Main Components

 ### API Layer

 Handles incoming HTTP requests and exposes the application's API endpoints.

 ### Schema Layer

 Responsible for validating incoming data and defining the structure of API requests and responses.

 ### Service Layer

 Contains the main business logic of the application and keeps it separate from the API routes.

 ### Core Layer

 Contains shared configuration and custom exception handling used throughout the application.

 ## Getting Started

 Navigate to the backend directory:

cd backend

 Install the required dependencies:

pip install -r requirements.txt

 Run the application using the appropriate command for your framework.

 ## Health Check

 The backend includes a health-check endpoint through:

api/routes/health.py

 This can be used to verify that the backend service is running correctly.
