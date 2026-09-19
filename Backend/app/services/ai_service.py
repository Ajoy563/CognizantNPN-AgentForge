import logging
from pathlib import Path
import sys
from typing import Any

from app.core.errors import AppError
from app.schemas.requests import GenerateRequest

logger = logging.getLogger(__name__)


import concurrent.futures

def generate_blueprint(request: GenerateRequest) -> Any:
    repository_root = str(Path(__file__).resolve().parents[3])
    if repository_root not in sys.path:
        sys.path.insert(0, repository_root)

    try:
        from ai.service import GenerateRequest as AIRequest
        from ai.service import generate_blueprint as run_ai_workflow

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(run_ai_workflow, AIRequest(**request.model_dump()))
            return future.result()
    except Exception as exc:
        logger.error("AI blueprint workflow exception: %s", exc, exc_info=True)
        # Deliberately do not leak provider details or credentials to clients.
        raise AppError(
            f"The AI blueprint workflow could not complete: {exc}",
            status_code=502,
            error_code="AI_GENERATION_ERROR",
        ) from exc
