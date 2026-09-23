"""Settings from the repo-root .env (plus env vars) and fatigue defaults.

Tiny hand-rolled .env loader so we don't need an extra dependency.
Real environment variables always win over .env values.
"""

import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        value = value.split(" #", 1)[0].strip().strip('"').strip("'")
        os.environ.setdefault(key.strip(), value)


_load_dotenv(REPO_ROOT / ".env")


def _resolve_sqlite(url: str) -> str:
    """Make relative sqlite paths relative to backend/, not the current cwd."""
    prefix = "sqlite:///"
    if url.startswith(prefix) and not url.startswith(prefix + "/"):
        rel = url[len(prefix):]
        if rel != ":memory:":
            return prefix + str((BACKEND_DIR / rel).resolve())
    return url


class Settings:
    VERSION = "2.0"

    DATABASE_URL = _resolve_sqlite(
        os.getenv("DATABASE_URL", "sqlite:///./rebase.db")
    )
    SIM_TICK_SECONDS = float(os.getenv("SIM_TICK_SECONDS", "1"))

    # AI / voice (empty key -> those endpoints return 503, never crash)
    SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "")
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")
    LLM_API_KEY = os.getenv("LLM_API_KEY", "")
    LLM_MODEL = os.getenv("LLM_MODEL", "")
    # Groq: automatic fallback when the primary LLM fails (or the primary with LLM_PROVIDER=groq)
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "")
    EMBEDDING_MODEL = os.getenv(
        "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
    )
    CHROMA_DIR = str((BACKEND_DIR / os.getenv("CHROMA_DIR", "./data/models/chroma")).resolve())
    RAG_WARMUP = os.getenv("RAG_WARMUP", "1") != "0"  # build the vector store at server start
    ESTIMATOR_PATH = str(
        (BACKEND_DIR / os.getenv("ESTIMATOR_PATH", "./data/models/estimator.json")).resolve()
    )

    # Fatigue / rest defaults (placeholders inspired by aviation duty-time rules,
    # not legal limits). Used by E4 and the E10 gate.
    MAX_SHIFT_HOURS = 12.0
    MIN_REST_HOURS = 10.0
    MAX_HOURS_7D = 60.0


settings = Settings()
