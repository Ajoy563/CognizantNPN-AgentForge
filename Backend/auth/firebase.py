from __future__ import annotations

from typing import Any

import firebase_admin
from firebase_admin import auth, credentials

from app.core.config import settings
from app.core.errors import AppError


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
            cred = credentials.ApplicationDefault()

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
            code="FIREBASE_INIT_ERROR",
        ) from exc


def verify_id_token(id_token: str) -> dict[str, Any]:
    _initialize_firebase()

    try:
        decoded_token = auth.verify_id_token(
            id_token,
            check_revoked=True,
        )

        return decoded_token

    except auth.ExpiredIdTokenError as exc:
        raise AppError(
            "Firebase token has expired.",
            status_code=401,
            code="TOKEN_EXPIRED",
        ) from exc

    except auth.RevokedIdTokenError as exc:
        raise AppError(
            "Firebase token has been revoked.",
            status_code=401,
            code="TOKEN_REVOKED",
        ) from exc

    except auth.UserDisabledError as exc:
        raise AppError(
            "Firebase user is disabled.",
            status_code=403,
            code="USER_DISABLED",
        ) from exc

    except auth.InvalidIdTokenError as exc:
        raise AppError(
            "Invalid Firebase ID token.",
            status_code=401,
            code="INVALID_TOKEN",
        ) from exc

    except Exception as exc:
        raise AppError(
            "Firebase authentication failed.",
            status_code=401,
            code="AUTHENTICATION_FAILED",
        ) from exc