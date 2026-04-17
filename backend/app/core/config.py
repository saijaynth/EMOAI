from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = Field(default="Emo AI API", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    api_port: int = Field(default=8000, alias="API_PORT")
    allowed_origins: str = Field(
        default="http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000,http://127.0.0.1:3001",
        alias="ALLOWED_ORIGINS",
    )
    debug: bool = Field(default=False, alias="DEBUG")


settings = Settings()
