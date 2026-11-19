"""Runtime configuration, read once from the environment."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DMVWATCH_", env_file=".env")

    database_url: str
    redis_url: str
    sweep_interval_seconds: int = 300
    user_agent: str = "dmvwatch/0.1 (+https://github.com/jkuwalek/dmv-reservation-scheduler)"
