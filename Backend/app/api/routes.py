from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel, Field

from app.auth.dependencies import get_current_user
from app.db.mongodb import mongo
from app.db.repositories import generations as generations_repository
from app.schemas.requests import GenerateRequest
from app.schemas.responses import (
    BlueprintResponse,
    GenerationSummary,
    HealthResponse,
    ProjectDetail,
    ProjectSummary,
)
from app.services import generation_service
from app.services import project_service

router = APIRouter(prefix="/api")

@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    db_ok = mongo.health_check()
    return HealthResponse(
        status="ok" if db_ok else "degraded",
        service="SolutionForge AI",
    )

@router.post("/generate", response_model=BlueprintResponse)
async def generate_blueprint(
    request: GenerateRequest,
    current_user: dict = Depends(get_current_user),
):
    firebase_uid = current_user["uid"]

    project = project_service.create_project(uid=firebase_uid, request=request)

    # 2. Generate solution blueprint
    # Wait, generation_service.generate_solution is synchronous? Let's check.
    # It has no `async def`, so we can call it synchronously.
    blueprint = generation_service.generate_solution(
        uid=firebase_uid,
        project_id=project["project_id"],
        request=request
    )

    validation = blueprint["validation"]
    metadata = blueprint["meta"]
    return BlueprintResponse(
        validation_status=validation.get("status", "unknown"),
        blueprint=blueprint,
        repair_iterations=metadata.get("repair_iterations", 0)
    )

@router.get("/projects", response_model=list[ProjectSummary])
async def get_projects(
    current_user: dict = Depends(get_current_user),
):
    firebase_uid = current_user["uid"]
    projects = project_service.get_user_projects(firebase_uid)

    return [
        ProjectSummary(
            project_id=project["project_id"],
            name=project["title"],
            created_at=project["created_at"].isoformat(),
            latest_generation_id=project.get("latest_generation_id"),
        )
        for project in projects
    ]

@router.get("/projects/{project_id}", response_model=ProjectDetail)
async def get_project(
    project_id: str,
    current_user: dict = Depends(get_current_user),
):
    firebase_uid = current_user["uid"]
    project = project_service.get_project(
        project_id=project_id,
        uid=firebase_uid,
    )

    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    gens = generations_repository.list_generations(project_id, firebase_uid)

    generations = [
        GenerationSummary(
            generation_id=item["generation_id"],
            project_id=item["project_id"],
            created_at=item["created_at"].isoformat(),
            validation_status=item["validation"].get("status", "unknown") if item.get("validation") else "unknown",
            repair_iterations=item.get("repair_iterations", 0),
        )
        for item in gens
    ]

    return ProjectDetail(
        project_id=project["project_id"],
        name=project["title"],
        created_at=project["created_at"].isoformat(),
        latest_generation_id=project.get("latest_generation_id"),
        generations=generations,
    )

@router.get("/projects/{project_id}/generations", response_model=list[GenerationSummary])
async def get_generation_history(
    project_id: str,
    current_user: dict = Depends(get_current_user),
):
    firebase_uid = current_user["uid"]
    project = project_service.get_project(project_id, firebase_uid)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    gens = generations_repository.list_generations(project_id, firebase_uid)
    return [
        GenerationSummary(
            generation_id=item["generation_id"],
            project_id=item["project_id"],
            created_at=item["created_at"].isoformat(),
            validation_status=item["validation"].get("status", "unknown") if item.get("validation") else "unknown",
            repair_iterations=item.get("repair_iterations", 0),
        )
        for item in gens
    ]

@router.get("/generations/{generation_id}/report")
async def download_report(
    generation_id: str,
    current_user: dict = Depends(get_current_user),
):
    firebase_uid = current_user["uid"]
    generation = generations_repository.get_generation(generation_id, firebase_uid)
    if not generation:
        raise HTTPException(status_code=404, detail="Generation not found.")

    return HTMLResponse(
        content=generation.get("blueprint_html", ""),
        headers={
            "Content-Disposition": f'attachment; filename="solutionforge-{generation_id}.html"'
        },
    )
@router.get("/generations/{generation_id}/pdf")
async def download_pdf(
    generation_id: str,
    current_user: dict = Depends(get_current_user),
):
    firebase_uid = current_user["uid"]
    generation = generations_repository.get_generation(generation_id, firebase_uid)
    if not generation or not generation.get("blueprint_pdf"):
        raise HTTPException(status_code=404, detail="PDF not found.")

    return Response(
        content=generation["blueprint_pdf"],
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="solutionforge-{generation_id}.pdf"'
        },
    )

class UserProfileUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    # Profile images are stored in Firebase Storage; only the URL is persisted.
    photo_url: str = Field(default="", max_length=2_048)

@router.post("/users/me")
async def update_user_profile(
    update: UserProfileUpdate,
    current_user: dict = Depends(get_current_user),
):
    uid = current_user["uid"]
    db = mongo.get_db()
    db.users.update_one(
        {"uid": uid},
        {"$set": {"name": update.name.strip(), "photo_url": update.photo_url, "updated_at": datetime.now(timezone.utc)}},
        upsert=True
    )
    return {"name": update.name.strip(), "photo_url": update.photo_url, "email": current_user.get("email", "")}

@router.get("/users/me")
async def get_user_profile(
    current_user: dict = Depends(get_current_user),
):
    uid = current_user["uid"]
    db = mongo.get_db()
    user = db.users.find_one({"uid": uid})
    if user:
        return {"name": user.get("name", ""), "photo_url": user.get("photo_url", ""), "email": user.get("email", current_user.get("email", ""))}
    return {"name": "", "photo_url": "", "email": current_user.get("email", "")}

@router.get("/generations/{generation_id}")
async def get_generation_detail(
    generation_id: str,
    current_user: dict = Depends(get_current_user),
):
    firebase_uid = current_user["uid"]
    generation = generations_repository.get_generation(generation_id, firebase_uid)
    if not generation:
        raise HTTPException(status_code=404, detail="Generation not found.")

    # Remove binary data from response
    generation.pop("blueprint_pdf", None)

    # We also need the original project inputs!
    project = project_service.get_project(generation["project_id"], firebase_uid)
    if project:
        generation["project_inputs"] = {
            key: project.get(key) for key in (
                "business_idea", "tech_preference", "cloud_preference",
                "expected_daily_traffic", "delivery_timeline_months", "country",
            )
        }

    return generation
