import os
from pathlib import Path

MAX_UPLOAD_BYTES = int(float(os.getenv("MAX_UPLOAD_MB", "50")) * 1024 * 1024)

_DEFAULT_MAX_TOTAL_CHARS = 350000


def _max_total_chars() -> int:
    raw = os.getenv("MAX_TOTAL_CHARS")
    if raw is None or raw.strip() == "":
        return _DEFAULT_MAX_TOTAL_CHARS
    try:
        n = int(raw.strip(), 10)
    except ValueError:
        return _DEFAULT_MAX_TOTAL_CHARS
    if n <= 0:
        return _DEFAULT_MAX_TOTAL_CHARS
    return n


MAX_TOTAL_CHARS = _max_total_chars()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/app.db")

_upload = os.getenv("UPLOAD_DIR", "uploads")
UPLOAD_DIR = Path(_upload)

CORS_ORIGINS = [
    o.strip()
    for o in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if o.strip()
]

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
OPENROUTER_BASE_URL = os.getenv(
    "OPENROUTER_BASE_URL",
    "https://openrouter.ai/api/v1",
).strip().rstrip("/")
OPENROUTER_MODEL = os.getenv(
    "OPENROUTER_MODEL",
    "openai/gpt-4o-mini",
).strip()
OPENROUTER_APP_NAME = os.getenv("OPENROUTER_APP_NAME", "").strip()
OPENROUTER_SITE_URL = os.getenv("OPENROUTER_SITE_URL", "").strip()

OPENROUTER_KEY_MISSING_MESSAGE = (
    "OPENROUTER_API_KEY is not set on the server. Set it in the process environment "
    "(for example from a gitignored .env file). This value is never sent by the browser "
    "and must not be hardcoded in the repository."
)
