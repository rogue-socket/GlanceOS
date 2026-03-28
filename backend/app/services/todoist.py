import logging
from datetime import datetime

import httpx

from app.config import get_settings

logger = logging.getLogger("glanceos.todoist")


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
    params = {}
    if effective_project_id:
        params["project_id"] = effective_project_id

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://api.todoist.com/rest/v2/tasks",
                headers=headers,
                params=params,
            )
            resp.raise_for_status()
            raw_tasks = resp.json()

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
                    "url": f"https://todoist.com/showTask?id={task_id}",
                }
            )

        return {
            "type": "todo",
            "data": {
                "tasks": tasks,
                "source": "todoist-api",
                "status": "connected",
                "project_id": effective_project_id or None,
            },
        }
    except Exception as exc:
        logger.warning("Todoist fetch failed: %s", exc)

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
