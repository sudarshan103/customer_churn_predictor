from functools import lru_cache
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseModel):
    app_name: str = "Churn Predictor API"
    app_version: str = "1.0.0"
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_fine_tuned_model: str = Field(default="", alias="OPENAI_FINE_TUNED_MODEL")
    workers: int = Field(default=4, alias="WORKERS")
    openai_timeout_seconds: float = Field(default=30.0, alias="OPENAI_TIMEOUT_SECONDS")
    openai_temperature: float = Field(default=0.0, ge=0.0, le=2.0, alias="OPENAI_TEMPERATURE")
    openai_max_tokens: int = Field(default=150, gt=0, alias="OPENAI_MAX_TOKENS")
    rate_limit_per_minute: int = Field(default=120, alias="RATE_LIMIT_PER_MINUTE")


@lru_cache
def get_settings() -> Settings:
    import os

    return Settings.model_validate(os.environ)
