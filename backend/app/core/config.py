from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/dbname"
    SECRET_KEY: str = "changeme-256-bit-secret"
    REFRESH_SECRET_KEY: str = "changeme-another-256-bit-secret"
    SUPABASE_URL: str = "https://placeholder.supabase.co"
    SUPABASE_ANON_KEY: str = "placeholder-anon-key"
    SUPABASE_SERVICE_KEY: str = "placeholder-service-key"
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000", "capacitor://localhost"]
    ENVIRONMENT: str = "development"
    SENTRY_DSN: str = ""


settings = Settings()
