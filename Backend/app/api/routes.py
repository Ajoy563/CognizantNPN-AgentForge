from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse

from app.auth.dependencies import get_current_user
from app.db.mongodb import mongo
from app.db.repositories.generations import GenerationRepository
from app.schemas.requests import GenerateRequest
from app.schemas.responses import (
    BlueprintResponse,
    GenerationSummary,
    HealthResponse,
    ProjectDetail,
    ProjectSummary,
)
from app.services.generation_service import generation_service
from app.services.project_service import project_service


router = APIRouter(prefix="/api")


@router.get(
    "/health",
    response_model=HealthResponse,
)
async def health() -> HealthResponse:
    db_ok = mongo.health_check()

    return HealthResponse(
        status="ok" if db_ok else "degraded",
        service="SolutionForge AI",
    )


@router.post(
    "/generate",
    response_model=BlueprintResponse,
)
async def generate_blueprint(
    request: GenerateRequest,
    current_user: dict = Depends(get_current_user),
):
    firebase_uid = current_user["uid"]

    return await generation_service.generate(
        request=request,
        user_uid=firebase_uid,
    )


@router.get(
    "/projects",
    response_model=list[ProjectSummary],
)
async def get_projects(
    current_user: dict = Depends(get_current_user),
):
    firebase_uid = current_user["uid"]

    projects = project_service.list_projects(
        firebase_uid,
    )

    return [
        ProjectSummary(
            project_id=project["project_id"],
            name=project["name"],
            created_at=project["created_at"].isoformat(),
            latest_generation_id=project.get(
                "latest_generation_id"
            ),
        )
        for project in projects
    ]


@router.get(
    "/projects/{project_id}",
    response_model=ProjectDetail,
)
async def get_project(
    project_id: str,
    current_user: dict = Depends(get_current_user),
):
    firebase_uid = current_user["uid"]

    project = project_service.get_project(
        project_id=project_id,
        user_uid=firebase_uid,
    )

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found.",
        )

    generations = [
        GenerationSummary(
            generation_id=item["generation_id"],
            project_id=item["project_id"],
            created_at=item["created_at"].isoformat(),
            validation_status=item["validation"]["status"],
            repair_iterations=item["repair_iterations"],
        )
        for item in project["generations"]
    ]

    return ProjectDetail(
        project_id=project["project_id"],
        name=project["name"],
        created_at=project["created_at"].isoformat(),
        latest_generation_id=project.get(
            "latest_generation_id"
        ),
        generations=generations,
    )


@router.get(
    "/projects/{project_id}/generations",
    response_model=list[GenerationSummary],
)
async def get_generation_history(
    project_id: str,
    current_user: dict = Depends(get_current_user),
):
    firebase_uid = current_user["uid"]

    project = project_service.projects.get_project(
        project_id,
        firebase_uid,
    )

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found.",
        )

    generations = project_service.generations.list_generations(
        project_id,
        firebase_uid,
    )

    return [
        GenerationSummary(
            generation_id=item["generation_id"],
            project_id=item["project_id"],
            created_at=item["created_at"].isoformat(),
            validation_status=item["validation"]["status"],
            repair_iterations=item["repair_iterations"],
        )
        for item in generations
    ]


@router.get(
    "/generations/{generation_id}/report",
)
async def download_report(
    generation_id: str,
    current_user: dict = Depends(get_current_user),
):
    firebase_uid = current_user["uid"]

    generation = generation_service.get_generation(
        generation_id,
        firebase_uid,
    )

    if not generation:
        raise HTTPException(
            status_code=404,
            detail="Generation not found.",
        )

    return HTMLResponse(
        content=generation["report_html"],
        headers={
            "Content-Disposition": (
                f'attachment; filename="solutionforge-{generation_id}.html"'
            )
        },
    )