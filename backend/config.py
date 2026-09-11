"""Application configuration loaded from environment variables."""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # SQLite (local dev – zero config)
    use_sqlite: bool = True
    sqlite_path: str = "travel_planner.db"

    # Database (MySQL – production)
    db_host: str = "localhost"
    db_port: int = 3306
    db_name: str = "travel_planner"
    db_user: str = "root"
    db_password: str = ""

    # IBM watsonx
    ibm_api_key: str = "oAUvGKtGg9WaduSC-Ot-d2F9GJJL4gt-kc89CVaMwHM8"
    ibm_url: str = "https://us-south.ml.cloud.ibm.com/ml/v1/text/generation?version=2023-05-29"
    ibm_project_id: str = "ecec1606-cf67-45c6-866b-cbedd54364ed"
    ibm_model_id: str = "ibm/granite-4-h-small"

    # IBM IAM token endpoint
    ibm_iam_url: str = "https://iam.cloud.ibm.com/identity/token"

    # OpenWeatherMap
    openweather_api_key: str = ""
    openweather_base_url: str = "https://api.openweathermap.org/data/2.5"

    # RAG
    rag_data_dir: str = "rag/data/destinations"
    chroma_persist_dir: str = "rag/embeddings/chroma_db"
    embedding_model: str = "all-MiniLM-L6-v2"
    rag_top_k: int = 5

    # LLM retries
    llm_max_retries: int = 3
    llm_retry_delay: float = 2.0

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
