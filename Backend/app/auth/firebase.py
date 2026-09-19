from __future__ import annotations

from typing import Any

import firebase_admin
from firebase_admin import auth, credentials
from google.auth.exceptions import GoogleAuthError
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

from app.core.config import settings
from app.core.errors import AppError

_http_request = google_requests.Request()


def _has_service_account_credentials() -> bool:
    return bool(
        settings.google_application_credentials
        or (
            settings.firebase_project_id
            and settings.firebase_client_email
            and settings.firebase_private_key
        )
    )


def _initialize_firebase() -> None:
    if firebase_admin._apps:
        return

    try:
        if settings.google_application_credentials:
            cred = credentials.Certificate(
                settings.google_application_credentials
            )

        elif (
            settings.firebase_project_id
            and settings.firebase_client_email
            and settings.firebase_private_key
        ):
            private_key = settings.firebase_private_key.replace("\\n", "\n")

            service_account_info = {
                "type": "service_account",
                "project_id": settings.firebase_project_id,
                "client_email": settings.firebase_client_email,
                "private_key": private_key,
                "token_uri": "https://oauth2.googleapis.com/token",
            }

            cred = credentials.Certificate(service_account_info)

        else:
            return

        options = {}

        if settings.firebase_project_id:
            options["projectId"] = settings.firebase_project_id

        firebase_admin.initialize_app(
            cred,
            options=options or None,
        )

    except Exception as exc:
        raise AppError(
            message=f"Firebase initialization failed: {exc}",
            status_code=500,
            error_code="FIREBASE_INIT_ERROR",
        ) from exc


def verify_id_token(id_token: str) -> dict[str, Any]:
    if _has_service_account_credentials():
        _initialize_firebase()
        if firebase_admin._apps:
            try:
                decoded_token = auth.verify_id_token(
                    id_token,
                    check_revoked=False,
                )
                decoded_token["uid"] = decoded_token.get("uid") or decoded_token.get("user_id") or decoded_token.get("sub")
                return decoded_token

            except auth.ExpiredIdTokenError as exc:
                raise AppError(
                    "Firebase token has expired.",
                    status_code=401,
                    error_code="TOKEN_EXPIRED",
                ) from exc

            except auth.RevokedIdTokenError as exc:
                raise AppError(
                    "Firebase token has been revoked.",
                    status_code=401,
                    error_code="TOKEN_REVOKED",
                ) from exc

            except auth.UserDisabledError as exc:
                raise AppError(
                    "Firebase user is disabled.",
                    status_code=403,
                    error_code="USER_DISABLED",
                ) from exc

            except auth.InvalidIdTokenError as exc:
                raise AppError(
                    "Invalid Firebase ID token.",
                    status_code=401,
                    error_code="INVALID_TOKEN",
                ) from exc

            except Exception as exc:
                raise AppError(
                    "Firebase authentication failed.",
                    status_code=401,
                    error_code="AUTHENTICATION_FAILED",
                ) from exc

    try:
        project_id = settings.firebase_project_id or None
        decoded_token = google_id_token.verify_firebase_token(
            id_token,
            _http_request,
            audience=project_id,
        )
        if not decoded_token:
            raise AppError(
                "Invalid Firebase ID token.",
                status_code=401,
                error_code="INVALID_TOKEN",
            )
        decoded_token["uid"] = decoded_token.get("uid") or decoded_token.get("user_id") or decoded_token.get("sub")
        return decoded_token
    except AppError:
        raise
    except GoogleAuthError as exc:
        raise AppError(
            f"Invalid Firebase ID token: {exc}",
            status_code=401,
            error_code="INVALID_TOKEN",
        ) from exc
    except Exception as exc:
        raise AppError(
            "Firebase authentication failed.",
            status_code=401,
            error_code="AUTHENTICATION_FAILED",
        ) from exc