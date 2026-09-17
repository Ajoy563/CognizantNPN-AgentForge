from typing import Any

from app.core.errors import AppError

def generate_blueprint(request: Any) -> Any:

    """

    Calls the AI team's public blueprint-generation service.

    The backend communicates with the AI layer through a single

    public function: generate_blueprint(request).

    The internal CrewAI agents, tasks, workflow, validator,

    and repair loop are owned by the AI team.

    """
    try:

        # Import lazily so the backend can run even while the

        # AI module is not yet connected.

        
        from ai.service import generate_blueprint as ai_generate_blueprint

    except ImportError as exc:

        raise AppError(

            message="AI service is not available.",

            status_code=500,

            error_code="AI_GENERATION_ERROR",

        ) from exc

    try:

        result = ai_generate_blueprint(request)

        if result is None:

            raise AppError(

                message="AI service returned an empty result.",

                status_code=500,

                error_code="AI_GENERATION_ERROR",

            )

        return result

    except AppError:

        raise
    except Exception as exc:

        raise AppError(

            message="Failed to generate the solution blueprint.",

            status_code=500,

            error_code="AI_GENERATION_ERROR",

        ) from exc