from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        extra="ignore",
    )

    DATABASE_URL: str = (
        "postgresql+psycopg://postgres:postgres@localhost:5432/pinkroute"
    )
    FRONTEND_URL: str = "http://localhost:5500"
    MODEL_PATH: Path = BASE_DIR / "model" / "eta_xgboost.json"
    CROWD_MODEL_PATH: Path = BASE_DIR / "model" / "crowd_xgboost.json"


settings = Settings()

if not settings.MODEL_PATH.is_absolute():
    settings.MODEL_PATH = BASE_DIR / settings.MODEL_PATH

if not settings.CROWD_MODEL_PATH.is_absolute():
    settings.CROWD_MODEL_PATH = BASE_DIR / settings.CROWD_MODEL_PATH
