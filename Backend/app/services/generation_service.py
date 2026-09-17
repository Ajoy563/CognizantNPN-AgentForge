import time

from datetime import datetime, timezone

from typing import Any

from app.core.errors import AppError

from app.services.ai_service import generate_blueprint

from app.services.report_service import render_report, generate_pdf

from app.db.repositories import generations as generations_repository

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

        requirements = _get_value(

            blueprint,

            "requirements",

        )

        architecture = _get_value(

            blueprint,

            "architecture",

        )

        technology = _get_value(

            blueprint,

            "technology",

        )

        delivery = _get_value(

            blueprint,

            "delivery",

        )

        validation = _get_value(

            blueprint,

            "validation",

        )

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

        repair_iterations = _get_nested_value(

            blueprint,

            "meta",

            "repair_iterations",

            default=0,

        )

        # -----------------------------------------------------

        # 8. Generate HTML report

        # -----------------------------------------------------

        blueprint_html = render_report(

            blueprint_md

        )

        # -----------------------------------------------------

        # 9. Generate PDF report

        # -----------------------------------------------------

        blueprint_pdf = generate_pdf(

            blueprint_md

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

            "requirements": requirements,

            "architecture": architecture,

            "technology": technology,

            "delivery": delivery,

            "validation": validation,

            "blueprint_markdown": blueprint_md,

            "blueprint_html": blueprint_html,

            # PDF is stored as bytes for the generated report.

            "blueprint_pdf": blueprint_pdf,

            "repair_iterations": repair_iterations,

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

        generation_id = str(

            generation.get(

                "_id",

                generation.get("id", ""),

            )

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

            "validation": validation,

            "blueprint_md": blueprint_md,

            "blueprint_html": blueprint_html,

            "meta": {

                "model": model,

                "duration_seconds": duration_seconds,

                "repair_iterations": repair_iterations,

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