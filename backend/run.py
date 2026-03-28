import os
import sys
from pathlib import Path

import uvicorn
from app.config import get_settings


ENV_FILE = Path(__file__).resolve().parent / ".env"
GEMINI_DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
GEMINI_DEFAULT_MODEL = "gemini-2.0-flash-lite"


def _read_env_value(file_path: Path, key: str) -> str:
    if not file_path.exists():
        return ""
    prefix = f"{key}="
    for line in file_path.read_text(encoding="utf-8").splitlines():
        if line.startswith(prefix):
            return line[len(prefix) :]
    return ""


def _upsert_env_value(file_path: Path, key: str, value: str) -> None:
    lines = []
    found = False

    if file_path.exists():
        lines = file_path.read_text(encoding="utf-8").splitlines()

    prefix = f"{key}="
    next_lines = []
    for line in lines:
        if line.startswith(prefix):
            next_lines.append(f"{key}={value}")
            found = True
        else:
            next_lines.append(line)

    if not found:
        next_lines.append(f"{key}={value}")

    file_path.write_text("\n".join(next_lines).rstrip() + "\n", encoding="utf-8")


def _confirm(prompt: str, default_yes: bool = True) -> bool:
    if not sys.stdin.isatty():
        return default_yes

    suffix = " [Y/n]: " if default_yes else " [y/N]: "
    answer = input(prompt + suffix).strip().lower()
    if not answer:
        return default_yes
    return answer in {"y", "yes"}


def _discover_news_key() -> tuple[str, str]:
    file_value = _read_env_value(ENV_FILE, "NEWS_LLM_API_KEY").strip()
    if file_value:
        return file_value, "backend/.env:NEWS_LLM_API_KEY"

    for env_key in ("NEWS_LLM_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY"):
        env_value = os.getenv(env_key, "").strip()
        if env_value:
            return env_value, f"env:{env_key}"

    for alias_key in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
        alias_value = _read_env_value(ENV_FILE, alias_key).strip()
        if alias_value:
            return alias_value, f"backend/.env:{alias_key}"

    return "", ""


def _ensure_news_llm_key() -> None:
    key, source = _discover_news_key()

    if not key and sys.stdin.isatty():
        entered = input(
            "[GlanceOS] Gemini API key not found. Enter key for News summaries (press Enter to skip): "
        ).strip()
        if entered:
            key = entered
            source = "prompt"

    if not key:
        print("[GlanceOS] Gemini API key not found. News crux summaries will use non-LLM fallback.")
        return

    current_news_key = _read_env_value(ENV_FILE, "NEWS_LLM_API_KEY").strip()
    should_persist = current_news_key != key

    if should_persist and source.startswith("env:"):
        should_persist = _confirm(
            f"[GlanceOS] Found key in {source}. Persist it to backend/.env as NEWS_LLM_API_KEY?",
            default_yes=True,
        )

    if should_persist:
        _upsert_env_value(ENV_FILE, "NEWS_LLM_API_KEY", key)

    if _read_env_value(ENV_FILE, "NEWS_LLM_PROVIDER").strip().lower() != "gemini":
        _upsert_env_value(ENV_FILE, "NEWS_LLM_PROVIDER", "gemini")

    if not _read_env_value(ENV_FILE, "NEWS_LLM_BASE_URL").strip():
        _upsert_env_value(ENV_FILE, "NEWS_LLM_BASE_URL", GEMINI_DEFAULT_BASE_URL)

    if not _read_env_value(ENV_FILE, "NEWS_LLM_MODEL").strip():
        _upsert_env_value(ENV_FILE, "NEWS_LLM_MODEL", GEMINI_DEFAULT_MODEL)

    os.environ["NEWS_LLM_API_KEY"] = key
    print(f"[GlanceOS] News LLM key ready ({source}).")


def main():
    _ensure_news_llm_key()
    get_settings.cache_clear()
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
        access_log=False,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
