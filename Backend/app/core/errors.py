from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


def _cors_headers(request: Request) -> dict[str, str]:
    origin = request.headers.get("origin")
    if origin:
        return {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
    return {
        "Access-Control-Allow-Origin": "*",
    }


class AppError(Exception):
    """
    Base exception for application-specific errors.
    """

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        code: str | None = None,
        details: dict | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = code or error_code
        self.details = details

        super().__init__(message)


async def app_error_handler(
    request: Request,
    exc: AppError,
) -> JSONResponse:
    """
    Handles application-specific errors.
    """

    return JSONResponse(
        status_code=exc.status_code,
        headers=_cors_headers(request),
        content={
            "status": "error",
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
            },
        },
    )


async def validation_error_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """
    Handles Pydantic request validation errors.
    """

    return JSONResponse(
        status_code=422,
        headers=_cors_headers(request),
        content={
            "status": "error",
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid request data.",
                "details": exc.errors(),
            },
        },
    )


async def general_error_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """
    Handles unexpected server errors.
    """

    return JSONResponse(
        status_code=500,
        headers=_cors_headers(request),
        content={
            "status": "error",
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred.",
            },
        },
    )