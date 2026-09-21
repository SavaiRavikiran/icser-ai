"""Application configuration via pydantic-settings."""
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # Environment
    environment: str = Field("production", alias="ENVIRONMENT")
    log_level: str = Field("INFO", alias="LOG_LEVEL")

    # Azure
    azure_tenant_id: str = Field("", alias="AZURE_TENANT_ID")
    azure_client_id: str = Field("", alias="AZURE_CLIENT_ID")
    azure_client_secret: str = Field("", alias="AZURE_CLIENT_SECRET")
    azure_subscription_id: str = Field("", alias="AZURE_SUBSCRIPTION_ID")
    azure_resource_group: str = Field("", alias="AZURE_RESOURCE_GROUP")
    azure_key_vault_name: str = Field("", alias="AZURE_KEY_VAULT_NAME")
    azure_storage_account: str = Field("", alias="AZURE_STORAGE_ACCOUNT")
    azure_eventhubs_connection: str = Field("", alias="AZURE_EVENTHUBS_CONNECTION")
    azure_search_endpoint: str = Field("", alias="AZURE_SEARCH_ENDPOINT")
    azure_search_key: str = Field("", alias="AZURE_SEARCH_KEY")
    azure_di_endpoint: str = Field("", alias="AZURE_DI_ENDPOINT")
    azure_di_key: str = Field("", alias="AZURE_DI_KEY")

    # Foundry
    foundry_endpoint: str = Field("", alias="FOUNDRY_ENDPOINT")
    foundry_api_key: str = Field("", alias="FOUNDRY_API_KEY")
    foundry_model_gpt4o: str = Field("gpt-4o", alias="FOUNDRY_MODEL_GPT4O")
    foundry_model_gpt4o_mini: str = Field("gpt-4o-mini", alias="FOUNDRY_MODEL_GPT4O_MINI")
    foundry_embedding_model: str = Field("text-embedding-3-large", alias="FOUNDRY_EMBEDDING_MODEL")

    # Langfuse
    langfuse_host: str = Field("", alias="LANGFUSE_HOST")
    langfuse_public_key: str = Field("", alias="LANGFUSE_PUBLIC_KEY")
    langfuse_secret_key: str = Field("", alias="LANGFUSE_SECRET_KEY")
    langfuse_release: str = Field("1.0.0", alias="LANGFUSE_RELEASE")

    # Database
    postgres_host: str = Field("", alias="POSTGRES_HOST")
    postgres_port: int = Field(5432, alias="POSTGRES_PORT")
    postgres_db: str = Field("icser_cases", alias="POSTGRES_DB")
    postgres_user: str = Field("", alias="POSTGRES_USER")
    postgres_password: str = Field("", alias="POSTGRES_PASSWORD")

    clickhouse_host: str = Field("", alias="CLICKHOUSE_HOST")
    clickhouse_port: int = Field(8123, alias="CLICKHOUSE_PORT")
    clickhouse_db: str = Field("langfuse", alias="CLICKHOUSE_DB")
    clickhouse_user: str = Field("", alias="CLICKHOUSE_USER")
    clickhouse_password: str = Field("", alias="CLICKHOUSE_PASSWORD")

    redis_host: str = Field("", alias="REDIS_HOST")
    redis_port: int = Field(6379, alias="REDIS_PORT")
    redis_db: int = Field(0, alias="REDIS_DB")

    # App
    max_compliance_iterations: int = Field(3, alias="MAX_COMPLIANCE_ITERATIONS")
    meddra_confidence_threshold: float = Field(0.85, alias="MEDDRA_CONFIDENCE_THRESHOLD")
    dedup_similarity_threshold: float = Field(0.92, alias="DEDUP_SIMILARITY_THRESHOLD")
    eval_sample_rate: float = Field(0.10, alias="EVAL_SAMPLE_RATE")
    cost_budget_monthly_usd: float = Field(45000.0, alias="COST_BUDGET_MONTHLY_USD")

    # Prometheus
    prometheus_port: int = Field(8000, alias="PROMETHEUS_PORT")

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()   