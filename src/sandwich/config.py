"""Configuration for the SANDWICH system."""

from pydantic_settings import BaseSettings
from pydantic import BaseModel


class DatabaseConfig(BaseModel):
    url: str = "postgresql://sandwich:sandwich@localhost:5432/sandwich"


class LLMConfig(BaseModel):
    provider: str = "anthropic"
    model: str = "claude-sonnet-4-20250514"
    embedding_model: str = "text-embedding-3-small"


class ValidityConfig(BaseModel):
    threshold: float = 0.7
    marginal_threshold: float = 0.5
    bread_compat_min: float = 0.3
    bread_compat_max: float = 0.9
    triviality_threshold: float = 0.85

    weight_bread_compat: float = 0.25
    weight_containment: float = 0.35
    weight_nontrivial: float = 0.20
    weight_novelty: float = 0.20


class ForagingConfig(BaseModel):
    max_patience: int = 5
    max_content_length: int = 10000

    wikipedia_enabled: bool = True
    arxiv_enabled: bool = True
    news_rss_enabled: bool = True
    web_search_enabled: bool = True


class SandwichConfig(BaseSettings):
    """Top-level configuration, populated from environment variables."""

    database: DatabaseConfig = DatabaseConfig()
    llm: LLMConfig = LLMConfig()
    validity: ValidityConfig = ValidityConfig()
    foraging: ForagingConfig = ForagingConfig()

    model_config = {"env_prefix": "SANDWICH_", "env_nested_delimiter": "__"}
