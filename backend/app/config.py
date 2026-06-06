from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@db:5432/uptime"

    class Config:
        env_prefix = ""


settings = Settings()
