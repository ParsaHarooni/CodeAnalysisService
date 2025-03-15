from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import ConfigDict, Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True
    )

    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Code Analysis Service"

    # Repository Settings
    REPO_STORAGE_PATH: str = Field(default="./repos")

    # Database Settings
    DATABASE_URL: str = Field(default="sqlite+aiosqlite:///./code_analysis.db")

    # LLM Service Settings
    # The URL of the LLM service endpoint that analyzes code and provides suggestions
    # Can be configured via environment variable LLM_SERVICE_URL
    # Example .env entry: LLM_SERVICE_URL=http://your-llm-service/analyze
    # The service expects POST requests with JSON payload: {"function_code": string}
    # Returns JSON response with suggestions array
    LLM_SERVICE_URL: str = Field(default="http://llm_service/analyze")



settings = Settings()
