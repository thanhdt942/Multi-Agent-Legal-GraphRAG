from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "Vietnamese Legal Graph Retrieval API"
    app_version: str = "0.1.0"
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_auth: SecretStr
    neo4j_database: str = "neo4j"
    openai_api_key: SecretStr
    openai_embedding_model: str = "text-embedding-3-small"
    openai_embedding_dimensions: int = Field(default=1536, ge=1)
    request_timeout_ms: int = Field(default=10_000, ge=100, le=30_000)

    @field_validator("neo4j_auth")
    @classmethod
    def validate_auth(cls, value: SecretStr) -> SecretStr:
        if "/" not in value.get_secret_value():
            raise ValueError("NEO4J_AUTH must use username/password format")
        return value

    @property
    def neo4j_credentials(self) -> tuple[str, str]:
        return tuple(self.neo4j_auth.get_secret_value().split("/", 1))  # type: ignore[return-value]


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
