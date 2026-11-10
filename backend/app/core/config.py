from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[3]
BACKEND_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
ARTIFACTS_DIR = ROOT_DIR / "artifacts"
LEXICON_DIR = DATA_DIR / "lexicons"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CS_", env_file=".env", extra="ignore")

    app_name: str = "Urdu-English Code-Switching Analyzer"
    api_prefix: str = "/api"
    database_url: str = f"sqlite:///{(BACKEND_DIR / 'data' / 'app.db').as_posix()}"
    artifacts_dir: Path = ARTIFACTS_DIR
    lexicon_dir: Path = LEXICON_DIR
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    default_train_ratio: float = 0.70
    default_val_ratio: float = 0.15
    default_test_ratio: float = 0.15
    random_seed: int = 42
    # Code-switching: require both languages with at least this many confident tokens
    cs_min_tokens_per_language: int = 1
    cs_min_confidence: float = 0.55


settings = Settings()


def ensure_directories() -> None:
    for path in [
        BACKEND_DIR / "data",
        DATA_DIR / "raw",
        DATA_DIR / "processed",
        DATA_DIR / "lexicons",
        ARTIFACTS_DIR / "models",
        ARTIFACTS_DIR / "exports",
        ARTIFACTS_DIR / "logs",
    ]:
        path.mkdir(parents=True, exist_ok=True)
