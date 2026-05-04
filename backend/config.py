"""Application configuration from environment variables."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://postgres:changeme@localhost:5432/ai_detection"

    # Auth
    secret_key: str = "dev-secret-key-change-in-production"
    jwt_expire_hours: int = 24
    admin_username: str = "admin"
    admin_password: str = "admin123"

    # go2rtc
    go2rtc_api: str = "http://localhost:1984"
    go2rtc_config_path: str = "./media_server/go2rtc.yaml"

    # Camera
    camera_onboard_limit: int = 10

    # Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
