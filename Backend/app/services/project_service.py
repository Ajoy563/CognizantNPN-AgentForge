from datetime import datetime, timezone

from typing import Any

from app.core.errors import AppError

from app.db.repositories import projects as projects_repository

def create_project(

    uid: str,

    request: Any,

    title: str | None = None,

) -> dict:

    """

    Create a new project for the authenticated user.

    The UID must come from the verified Firebase token.

    """

    if not uid:

        raise AppError(

            message="Authenticated user ID is required.",

            status_code=401,

            error_code="AUTH_REQUIRED",

        )

    try:

        now = datetime.now(timezone.utc)

        project_data = {

            "uid": uid,

            "title": title or "Untitled Solution",

            "business_idea": request.business_idea,

            "tech_preference": request.tech_preference,

            "cloud_preference": request.cloud_preference,

            "expected_daily_traffic": request.expected_daily_traffic,

            "delivery_timeline_months": request.delivery_timeline_months,

            "country": request.country,

            "created_at": now,

            "updated_at": now,

        }

        project = projects_repository.create_project(project_data)

        if not project:

            raise AppError(

                message="Project could not be created.",

                status_code=500,

                error_code="DATABASE_ERROR",

            )

        return project

    except AppError:

        raise

    except Exception as exc:

        raise AppError(

            message="Failed to create project.",

            status_code=500,

            error_code="DATABASE_ERROR",

        ) from exc

def get_user_projects(uid: str) -> list[dict]:

    """

    Return all projects belonging to the authenticated user.

    Ownership is enforced using the verified Firebase UID.

    """

    if not uid:

        raise AppError(

            message="Authenticated user ID is required.",

            status_code=401,

            error_code="AUTH_REQUIRED",

        )

    try:

        projects = projects_repository.get_projects_by_uid(uid)

        return projects or []

    except Exception as exc:

        raise AppError(

            message="Failed to retrieve projects.",

            status_code=500,

            error_code="DATABASE_ERROR",

        ) from exc

def get_project(

    project_id: str,

    uid: str,

) -> dict:

    """

    Get a single project belonging to the authenticated user.

    The project must belong to the supplied verified Firebase UID.

    """

    if not uid:

        raise AppError(

            message="Authenticated user ID is required.",

            status_code=401,

            error_code="AUTH_REQUIRED",

        )

    if not project_id:

        raise AppError(

            message="Project ID is required.",

            status_code=400,

            error_code="VALIDATION_ERROR",

        )

    try:

        project = projects_repository.get_project_by_id(project_id)

        if not project:

            raise AppError(

                message="Project not found.",

                status_code=404,

                error_code="PROJECT_NOT_FOUND",

            )

        # Server-side ownership check.

        if project.get("uid") != uid:

            raise AppError(

                message="You do not have access to this project.",

                status_code=403,

                error_code="FORBIDDEN",

            )

        return project

    except AppError:

        raise

    except Exception as exc:

        raise AppError(

            message="Failed to retrieve project.",

            status_code=500,

            error_code="DATABASE_ERROR",

        ) from exc