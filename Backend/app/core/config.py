from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application
    app_name: str = "SolutionForge AI"
    app_version: str = "1.0.0"
    debug: bool = False

    # MongoDB Atlas
    mongodb_uri: str

    # Firebase
    firebase_project_id: str
    firebase_client_email: str
    firebase_private_key: str

    # CORS
    cors_origins: str = "*"

    # AI / Backend timeout
    ai_timeout_seconds: int = 300

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


settings = Settings()