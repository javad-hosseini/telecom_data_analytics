from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ClickHouse Settings
    clickhouse_host: str = "192.168.247.128"
    clickhouse_port: int = 8123
    clickhouse_database: str = "telecom_analytics"
    clickhouse_username: str = "default"
    clickhouse_password: str = ""
    clickhouse_secure: bool = False

    # Connection Settings
    connection_timeout: int = 30
    query_timeout: int = 10

    # API Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_debug: bool = False
    api_cors_origins: list = ["*"]

    # Data Generation Settings
    batch_size: int = 50000
    total_records: int = 5_000_000

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env/.env.local"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
