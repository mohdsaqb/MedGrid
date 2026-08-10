from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central place for configuration values.

    Values are read from environment variables (or a local .env file).
    This means the same code can run with different settings in
    development, testing, and production without any code changes -
    only the environment differs.
    """

    app_name: str = "MedGrid API"
    environment: str = "development"

    # Origins allowed to call this API from a browser (see CORS section).
    # A comma-separated string in .env, split into a list here.
    cors_origins: str = "http://localhost:5173"

    # No default on purpose: if this is missing, the app should fail to
    # start rather than silently connect to the wrong database.
    database_url: str

    # Signs and verifies JWTs. No default - a shipped default secret is a
    # real vulnerability (anyone reading the source could forge tokens).
    secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]


# Created once and imported wherever settings are needed.
settings = Settings()
