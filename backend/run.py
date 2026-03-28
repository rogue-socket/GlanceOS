import os
import sys
from getpass import getpass
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


def _ensure_env_file_exists() -> None:
    if ENV_FILE.exists():
        return

    example_file = ENV_FILE.with_name(".env.example")
    if example_file.exists():
        ENV_FILE.write_text(example_file.read_text(encoding="utf-8"), encoding="utf-8")
        return

    ENV_FILE.write_text("", encoding="utf-8")


def _confirm(prompt: str, default_yes: bool = True) -> bool:
    if not sys.stdin.isatty():
        return default_yes

    suffix = " [Y/n]: " if default_yes else " [y/N]: "
    answer = input(prompt + suffix).strip().lower()
    if not answer:
        return default_yes
    return answer in {"y", "yes"}


def _prompt_value(prompt: str, secret: bool = True) -> str:
    if not sys.stdin.isatty():
        return ""
    if secret:
        return getpass(prompt).strip()
    return input(prompt).strip()


def _discover_value(primary_key: str, aliases: tuple[str, ...] = ()) -> tuple[str, str]:
    file_value = _read_env_value(ENV_FILE, primary_key).strip()
    if file_value:
        return file_value, f"backend/.env:{primary_key}"

    for env_key in (primary_key, *aliases):
        env_value = os.getenv(env_key, "").strip()
        if env_value:
            return env_value, f"env:{env_key}"

    for alias_key in aliases:
        alias_value = _read_env_value(ENV_FILE, alias_key).strip()
        if alias_value:
            return alias_value, f"backend/.env:{alias_key}"

    return "", ""


def _persist_value(primary_key: str, value: str, source: str) -> None:
    current_value = _read_env_value(ENV_FILE, primary_key).strip()
    should_persist = current_value != value

    if should_persist and source.startswith("env:"):
        should_persist = _confirm(
            f"[GlanceOS] Found value in {source}. Persist it to backend/.env as {primary_key}?",
            default_yes=True,
        )

    if should_persist:
        _upsert_env_value(ENV_FILE, primary_key, value)

    os.environ[primary_key] = value


def _ensure_service_key(primary_key: str, label: str, aliases: tuple[str, ...] = ()) -> str:
    value, source = _discover_value(primary_key, aliases)

    if not value:
        entered = _prompt_value(
            f"[GlanceOS] {label} not found. Enter now (press Enter to skip): ",
            secret=True,
        )
        if entered:
            value = entered
            source = "prompt"

    if not value:
        print(f"[GlanceOS] {label} not configured.")
        return ""

    _persist_value(primary_key, value, source)
    print(f"[GlanceOS] {label} ready ({source}).")
    return value


def _ensure_google_calendar_config() -> None:
    ics_url, ics_source = _discover_value("GOOGLE_CALENDAR_ICS_URL")
    if ics_url:
        _persist_value("GOOGLE_CALENDAR_ICS_URL", ics_url, ics_source)
        print(f"[GlanceOS] Google Calendar ICS ready ({ics_source}).")
        return

    calendar_id, id_source = _discover_value("GOOGLE_CALENDAR_ID")
    calendar_api_key, key_source = _discover_value("GOOGLE_CALENDAR_API_KEY", aliases=("GOOGLE_API_KEY",))

    if calendar_id and calendar_api_key:
        _persist_value("GOOGLE_CALENDAR_ID", calendar_id, id_source)
        _persist_value("GOOGLE_CALENDAR_API_KEY", calendar_api_key, key_source)
        print(f"[GlanceOS] Google Calendar API config ready ({id_source}, {key_source}).")
        return

    if not sys.stdin.isatty():
        print("[GlanceOS] Google Calendar not configured.")
        return

    print("[GlanceOS] Google Calendar not configured.")
    entered_ics = _prompt_value(
        "[GlanceOS] Enter Google Calendar ICS URL (recommended, Enter to skip): ",
        secret=False,
    )
    if entered_ics:
        _persist_value("GOOGLE_CALENDAR_ICS_URL", entered_ics, "prompt")
        print("[GlanceOS] Google Calendar ICS ready (prompt).")
        return

    if not calendar_id:
        calendar_id = _prompt_value(
            "[GlanceOS] Enter Google Calendar ID for API mode (Enter to skip): ",
            secret=False,
        )
        if calendar_id:
            id_source = "prompt"

    if calendar_id and not calendar_api_key:
        calendar_api_key = _prompt_value(
            "[GlanceOS] Enter Google Calendar API key (Enter to skip): ",
            secret=True,
        )
        if calendar_api_key:
            key_source = "prompt"

    if calendar_id and calendar_api_key:
        _persist_value("GOOGLE_CALENDAR_ID", calendar_id, id_source or "prompt")
        _persist_value("GOOGLE_CALENDAR_API_KEY", calendar_api_key, key_source or "prompt")
        print("[GlanceOS] Google Calendar API config ready.")
    else:
        print("[GlanceOS] Google Calendar remains unconfigured.")


def _ensure_news_defaults() -> None:
    if not _read_env_value(ENV_FILE, "NEWS_LLM_PROVIDER").strip():
        _upsert_env_value(ENV_FILE, "NEWS_LLM_PROVIDER", "gemini")

    if not _read_env_value(ENV_FILE, "NEWS_LLM_BASE_URL").strip():
        _upsert_env_value(ENV_FILE, "NEWS_LLM_BASE_URL", GEMINI_DEFAULT_BASE_URL)

    if not _read_env_value(ENV_FILE, "NEWS_LLM_MODEL").strip():
        _upsert_env_value(ENV_FILE, "NEWS_LLM_MODEL", GEMINI_DEFAULT_MODEL)


def _ensure_service_credentials() -> None:
    _ensure_env_file_exists()
    _ensure_news_defaults()

    _ensure_service_key("WEATHER_API_KEY", "OpenWeatherMap API key")
    _ensure_service_key("GITHUB_TOKEN", "GitHub token")
    _ensure_service_key("TODOIST_API_TOKEN", "Todoist API token")
    _ensure_service_key(
        "NEWS_LLM_API_KEY",
        "Gemini API key for News summaries",
        aliases=("GEMINI_API_KEY", "GOOGLE_API_KEY"),
    )
    _ensure_google_calendar_config()

def main():
    _ensure_service_credentials()
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
