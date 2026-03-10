from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator, model_validator


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=True, env_file_encoding="utf-8"
    )

    APP_NAME: str = "NoCountry Video API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False)
    ENVIRONMENT: str = Field(default="development")

    DATABASE_URL: str = Field(default="postgresql://postgres:postgres@localhost:5432/postgres")
    DB_POOL_SIZE: int = Field(default=10)
    DB_MAX_OVERFLOW: int = Field(default=20)
    DB_ECHO: bool = Field(default=False)

    @model_validator(mode="before")
    @classmethod
    def populate_database_url(cls, values):
        database_url = values.get("DATABASE_URL")
        if database_url:
            return values

        pg_host = values.get("PGHOST")
        pg_port = values.get("PGPORT", "5432")
        pg_user = values.get("PGUSER")
        pg_password = values.get("PGPASSWORD")
        pg_database = values.get("PGDATABASE")

        if pg_host and pg_user and pg_password and pg_database:
            values["DATABASE_URL"] = (
                f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_database}"
            )

        return values

    @model_validator(mode="before")
    @classmethod
    def populate_minio_settings(cls, values):
        minio_url = (
            values.get("MINIO_ENDPOINT")
            or values.get("MINIO_URL")
            or values.get("MINIO_PRIVATE_URL")
            or values.get("S3_ENDPOINT")
            or values.get("S3_ENDPOINT_URL")
        )
        if minio_url and not values.get("MINIO_ENDPOINT"):
            values["MINIO_ENDPOINT"] = minio_url

        minio_public_url = (
            values.get("MINIO_PUBLIC_ENDPOINT")
            or values.get("MINIO_PUBLIC_URL")
            or values.get("S3_PUBLIC_ENDPOINT")
        )
        if minio_public_url and not values.get("MINIO_PUBLIC_ENDPOINT"):
            values["MINIO_PUBLIC_ENDPOINT"] = minio_public_url

        selected_endpoint = values.get("MINIO_ENDPOINT")
        if (not selected_endpoint or selected_endpoint == "minio:9000") and minio_public_url:
            values["MINIO_ENDPOINT"] = minio_public_url

        if values.get("MINIO_ENDPOINT", "").startswith("https://"):
            values["MINIO_SECURE"] = True
        elif values.get("MINIO_ENDPOINT", "").startswith("http://") and values.get("MINIO_SECURE") is None:
            values["MINIO_SECURE"] = False

        if values.get("AWS_ACCESS_KEY_ID") and not values.get("MINIO_ACCESS_KEY"):
            values["MINIO_ACCESS_KEY"] = values.get("AWS_ACCESS_KEY_ID")

        if values.get("MINIO_ROOT_USER") and not values.get("MINIO_ACCESS_KEY"):
            values["MINIO_ACCESS_KEY"] = values.get("MINIO_ROOT_USER")

        if values.get("AWS_SECRET_ACCESS_KEY") and not values.get("MINIO_SECRET_KEY"):
            values["MINIO_SECRET_KEY"] = values.get("AWS_SECRET_ACCESS_KEY")

        if values.get("MINIO_ROOT_PASSWORD") and not values.get("MINIO_SECRET_KEY"):
            values["MINIO_SECRET_KEY"] = values.get("MINIO_ROOT_PASSWORD")

        if values.get("S3_BUCKET") and not values.get("MINIO_BUCKET_VIDEOS"):
            values["MINIO_BUCKET_VIDEOS"] = values.get("S3_BUCKET")

        return values

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v):
        if v.startswith("postgres://"):
            v = "postgresql://" + v[len("postgres://") :]
        if not v.startswith("postgresql://"):
            raise ValueError("DATABASE_URL debe comenzar con postgresql://")
        return v

    # Redis puede usar REDIS_URL (Railway) o valores individuales (docker-compose)
    REDIS_URL: str | None = Field(default=None)
    REDIS_HOST: str = Field(default="redis")
    REDIS_PORT: int = Field(default=6379)
    REDIS_DB: int = Field(default=0)
    REDIS_PASSWORD: str | None = Field(default=None)

    MINIO_ENDPOINT: str = Field(default="minio:9000")
    MINIO_ACCESS_KEY: str = Field(default="minio")
    MINIO_SECRET_KEY: str = Field(default="miniopass")
    MINIO_BUCKET_VIDEOS: str = Field(default="videos")
    MINIO_SECURE: bool = Field(default=False)
    # Endpoint público para URLs presignadas (accesible desde navegador)
    MINIO_PUBLIC_ENDPOINT: str | None = Field(default=None)
    MINIO_PUBLIC_SECURE: bool | None = Field(default=None)

    SECRET_KEY: str = Field(default="")
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60 * 24 * 7)

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v, info):
        if not v or not v.strip():
            raise ValueError("SECRET_KEY es obligatorio y debe definirse por variable de entorno")
        if len(v) < 32:
            raise ValueError(
                "SECRET_KEY debe tener al menos 32 caracteres"
            )
        return v

    # === GOOGLE OAUTH ===
    GOOGLE_CLIENT_ID: str = Field(default="")
    GOOGLE_CLIENT_SECRET: str = Field(default="")
    GOOGLE_REDIRECT_URI: str = Field(default="http://localhost:3000/auth/callback")

    # === LLM metadata suggestions (optional) ===
    OPENROUTER_API_KEY: str = Field(default="")
    OPENROUTER_MODEL: str = Field(default="meta-llama/llama-3.1-8b-instruct:free")
    OPENROUTER_BASE_URL: str = Field(default="https://openrouter.ai/api/v1")

    @field_validator("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET")
    @classmethod
    def validate_google_credentials(cls, v, info):
        if info.data.get("ENVIRONMENT") == "production" and not v:
            raise ValueError(f"{info.field_name} is required in production")
        return v

    ALLOWED_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"]
    )

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    RATE_LIMIT_ENABLED: bool = Field(default=False)
    RATE_LIMIT_PER_MINUTE: int = Field(default=60)

    LOG_LEVEL: str = Field(default="INFO")
    LOG_FORMAT: str = Field(default="json")


settings = Settings()
