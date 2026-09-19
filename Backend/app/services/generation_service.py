import time

from datetime import datetime, timezone

from typing import Any

from app.core.errors import AppError

from app.services.ai_service import generate_blueprint

from app.db.repositories import generations as generations_repository
from app.db.repositories import projects as projects_repository

def generate_solution(uid: str, project_id: str, request: Any) -> dict:

    """

    Generate a complete solution blueprint for a project.

    Flow:

        Request

          ↓

        AI Service

          ↓

        Structured Blueprint

          ↓

        Markdown

          ↓

        HTML Report

          ↓

        PDF Report

          ↓

        MongoDB

          ↓

        API Response

    """

    # ---------------------------------------------------------

    # 1. Validate authentication

    # ---------------------------------------------------------

    if not uid:

        raise AppError(

            message="Authenticated user ID is required.",

            status_code=401,

            error_code="AUTH_REQUIRED",

        )

    # ---------------------------------------------------------

    # 2. Validate project ID

    # ---------------------------------------------------------

    if not project_id:

        raise AppError(

            message="Project ID is required.",

            status_code=400,

            error_code="VALIDATION_ERROR",

        )

    # ---------------------------------------------------------

    # 3. Start execution timer

    # ---------------------------------------------------------

    start_time = time.perf_counter()

    try:

        # -----------------------------------------------------

        # 4. Generate blueprint using AI service

        # -----------------------------------------------------

        blueprint = generate_blueprint(request)

        if blueprint is None:

            raise AppError(

                message="AI service returned an empty blueprint.",

                status_code=500,

                error_code="AI_GENERATION_ERROR",

            )

        # -----------------------------------------------------

        # 5. Extract blueprint sections

        # -----------------------------------------------------

        requirements = _to_document(_get_value(blueprint, "requirements"))

        architecture = _to_document(_get_value(blueprint, "architecture"))

        technology = _to_document(_get_value(blueprint, "technology"))

        delivery = _to_document(_get_value(blueprint, "delivery"))

        # -----------------------------------------------------

        # 6. Extract Markdown blueprint

        # -----------------------------------------------------

        blueprint_md = _get_value(

            blueprint,

            "blueprint_md",

            default="",

        )

        if not blueprint_md:

            raise AppError(

                message="AI service did not return blueprint Markdown.",

                status_code=500,

                error_code="AI_GENERATION_ERROR",

            )

        # -----------------------------------------------------

        # 7. Extract metadata

        # -----------------------------------------------------

        model = _get_nested_value(

            blueprint,

            "meta",

            "model",

            default="unknown",

        )

        # -----------------------------------------------------

        # 8. Extract the pre-rendered HTML report
        #
        # ai.service.generate_blueprint() already produces a
        # professional, self-contained HTML report (embedded
        # architecture diagram, traceability and technology
        # matrices). Re-deriving HTML from Markdown here would throw
        # all of that away, so we reuse it as-is.

        # -----------------------------------------------------

        blueprint_html = _get_value(
            blueprint,
            "blueprint_html",
            default="",
        )

        if not blueprint_html:
            raise AppError(
                message="AI service did not return blueprint HTML.",
                status_code=500,
                error_code="AI_GENERATION_ERROR",
            )

        # -----------------------------------------------------

        # 10. Calculate generation duration

        # -----------------------------------------------------

        duration_seconds = round(

            time.perf_counter() - start_time,

            3,

        )

        # -----------------------------------------------------

        # 11. Prepare generation data for MongoDB

        # -----------------------------------------------------

        generation_data = {

            "project_id": project_id,

            "uid": uid,

            "status": "success",

            "project_inputs": request.model_dump(),

            "requirements": requirements,

            "architecture": architecture,

            "technology": technology,

            "delivery": delivery,

            "blueprint_markdown": blueprint_md,

            "blueprint_html": blueprint_html,

            "model": model,

            "duration_seconds": duration_seconds,

            "created_at": datetime.now(timezone.utc),

        }

        # -----------------------------------------------------

        # 12. Save generation in MongoDB

        # -----------------------------------------------------

        generation = generations_repository.create_generation(

            generation_data

        )

        if not generation:

            raise AppError(

                message="Generation could not be saved.",

                status_code=500,

                error_code="DATABASE_ERROR",

            )

        # -----------------------------------------------------

        # 13. Get generation ID

        # -----------------------------------------------------

        generation_id = generation["generation_id"]
        projects_repository.set_latest_generation(
            project_id, uid, generation_id, datetime.now(timezone.utc)
        )

        # -----------------------------------------------------

        # 14. Return response

        # -----------------------------------------------------

        return {

            "status": "success",

            "project_id": project_id,

            "generation_id": generation_id,

            "requirements": requirements,

            "architecture": architecture,

            "technology": technology,

            "delivery": delivery,

            "blueprint_md": blueprint_md,

            "blueprint_html": blueprint_html,

            "meta": {

                "model": model,

                "duration_seconds": duration_seconds,

            },

        }

    # ---------------------------------------------------------

    # 15. Preserve application errors

    # ---------------------------------------------------------

    except AppError:

        raise

    # ---------------------------------------------------------

    # 16. Handle unexpected errors

    # ---------------------------------------------------------

    except Exception as exc:

        raise AppError(

            message="Failed to generate solution blueprint.",

            status_code=500,

            error_code="AI_GENERATION_ERROR",

        ) from exc

# =============================================================

# Helper Functions

# =============================================================

def _get_value(

    obj: Any,

    key: str,

    default: Any = None,

) -> Any:

    """

    Get a value from either a dictionary or an object.

    Supports both:

        blueprint["requirements"]

    and:

        blueprint.requirements

    """

    if isinstance(obj, dict):

        return obj.get(

            key,

            default,

        )

    return getattr(

        obj,

        key,

        default,

    )

def _get_nested_value(

    obj: Any,

    parent_key: str,

    child_key: str,

    default: Any = None,

) -> Any:

    """

    Get a nested value from either dictionaries or objects.

    Example:

        blueprint.meta.model

    or:

        blueprint["meta"]["model"]

    """

    parent = _get_value(

        obj,

        parent_key,

    )

    if parent is None:

        return default

    return _get_value(

        parent,

        child_key,

        default,

    )


def _to_document(value: Any) -> Any:
    """Make Pydantic AI outputs safe for BSON storage and JSON responses."""
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    return value
