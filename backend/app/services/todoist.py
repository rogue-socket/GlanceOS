import logging
import time
from datetime import datetime

import httpx

from app.config import get_settings

logger = logging.getLogger("glanceos.todoist")

TODOIST_TASK_ENDPOINTS = [
    ("todoist-api-v1", "https://api.todoist.com/api/v1/tasks"),
]

_last_fetch_error_key = ""
_last_fetch_error_at = 0.0


def _throttled_warning(key: str, message: str, window_seconds: float = 600.0) -> None:
    global _last_fetch_error_key, _last_fetch_error_at

    now = time.monotonic()
    if key != _last_fetch_error_key or (now - _last_fetch_error_at) >= window_seconds:
        logger.warning(message)
        _last_fetch_error_key = key
        _last_fetch_error_at = now
    else:
        logger.debug(message)


def _parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        if value.endswith("Z"):
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _format_due(task: dict) -> str | None:
    due = task.get("due") or {}
    due_datetime = due.get("datetime")
    due_date = due.get("date")

    if due_datetime:
        parsed = _parse_iso_datetime(due_datetime)
        if parsed:
            return parsed.astimezone().strftime("%Y-%m-%d %H:%M")

    if due_date:
        return f"{due_date} all day"

    return None


def _task_sort_key(task: dict) -> tuple[int, str, str]:
    due = task.get("due") or {}
    due_dt = due.get("datetime")
    due_date = due.get("date")

    due_rank = 0 if (due_dt or due_date) else 1
    when = due_dt or due_date or "9999-99-99"
    content = task.get("content", "")
    return (due_rank, when, content)


def _extract_tasks(payload: object) -> list[dict]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]

    if isinstance(payload, dict):
        for key in ("results", "items", "tasks"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]

    return []


def _truncate(text: str, limit: int = 180) -> str:
    compact = " ".join((text or "").split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3] + "..."


async def _fetch_tasks_with_fallback(
    client: httpx.AsyncClient,
    headers: dict[str, str],
    params: dict[str, str | int],
) -> tuple[list[dict], str]:
    errors: list[str] = []

    for source, url in TODOIST_TASK_ENDPOINTS:
        try:
            resp = await client.get(url, headers=headers, params=params)
            resp.raise_for_status()
            return _extract_tasks(resp.json()), source
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            body = _truncate(exc.response.text)
            errors.append(f"{source} status={status} body={body}")
            continue
        except Exception as exc:
            errors.append(f"{source} error={exc}")
            continue

    raise RuntimeError("; ".join(errors) if errors else "Todoist request failed")


async def fetch_todoist_tasks(project_id: str | None = None) -> dict:
    settings = get_settings()

    token = (settings.todoist_api_token or "").strip()
    effective_project_id = (project_id or settings.todoist_project_id or "").strip()

    if not token:
        return {
            "type": "todo",
            "data": {
                "tasks": [],
                "source": "unconfigured",
                "status": "unconfigured",
                "project_id": effective_project_id or None,
                "message": "Set TODOIST_API_TOKEN in backend/.env",
            },
        }

    headers = {
        "Authorization": f"Bearer {token}",
    }
    params: dict[str, str | int] = {"limit": 50}
    if effective_project_id:
        params["project_id"] = effective_project_id

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            raw_tasks, source = await _fetch_tasks_with_fallback(client, headers, params)

        raw_tasks = sorted(raw_tasks, key=_task_sort_key)

        tasks = []
        for idx, task in enumerate(raw_tasks[:20]):
            task_id = str(task.get("id", f"task-{idx}"))
            tasks.append(
                {
                    "id": task_id,
                    "content": task.get("content", "Untitled task"),
                    "description": task.get("description", ""),
                    "priority": task.get("priority", 1),
                    "due": _format_due(task),
                    "project_id": task.get("project_id", ""),
                    "url": f"https://app.todoist.com/app/task/{task_id}",
                }
            )

        return {
            "type": "todo",
            "data": {
                "tasks": tasks,
                "source": source,
                "status": "connected",
                "project_id": effective_project_id or None,
            },
        }
    except Exception as exc:
        error_key = f"todoist-fetch:{type(exc).__name__}:{str(exc)[:120]}"
        _throttled_warning(error_key, f"Todoist fetch failed: {exc}")

    return {
        "type": "todo",
        "data": {
            "tasks": [],
            "source": "error",
            "status": "error",
            "project_id": effective_project_id or None,
            "message": "Unable to fetch Todoist tasks",
        },
    }
