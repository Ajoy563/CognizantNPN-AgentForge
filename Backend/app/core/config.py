from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

_backend_dir = Path(__file__).resolve().parents[2]
_root_dir = Path(__file__).resolve().parents[3]

class Settings(BaseSettings):
    # Application
    app_name: str = "SolutionForge AI"
    app_version: str = "1.0.0"
    debug: bool = False

    # MongoDB Atlas
    mongodb_uri: str
    mongodb_db_name: str = "solutionforge"

    # Firebase
    google_application_credentials: str = ""
    firebase_project_id: str = ""
    firebase_client_email: str = ""
    firebase_private_key: str = ""
    firebase_api: str = ""

    # CORS
    cors_origins: str = "*"

    # AI / Backend timeout
    ai_timeout_seconds: int = 300

    model_config = SettingsConfigDict(
        env_file=(_backend_dir / ".env", _root_dir / ".env", ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


settings = Settings()