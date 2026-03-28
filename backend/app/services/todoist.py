import logging
import time
from datetime import datetime

import httpx

from app.config import get_settings

logger = logging.getLogger("glanceos.todoist")

TODOIST_TASK_ENDPOINTS = [
    ("todoist-api-v1", "https://api.todoist.com/api/v1/tasks"),
]

TODOIST_PROJECT_ENDPOINTS = [
    ("todoist-rest-v2", "https://api.todoist.com/rest/v2/projects"),
]

TODOIST_SECTION_ENDPOINTS = [
    ("todoist-rest-v2", "https://api.todoist.com/rest/v2/sections"),
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


def _extract_list_items(payload: object) -> list[dict]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]

    if isinstance(payload, dict):
        for key in ("results", "items", "projects", "sections"):
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


async def _fetch_projects_with_fallback(
    client: httpx.AsyncClient,
    headers: dict[str, str],
) -> tuple[list[dict], str]:
    errors: list[str] = []

    for source, url in TODOIST_PROJECT_ENDPOINTS:
        try:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            return _extract_list_items(resp.json()), source
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            body = _truncate(exc.response.text)
            errors.append(f"{source} status={status} body={body}")
            continue
        except Exception as exc:
            errors.append(f"{source} error={exc}")
            continue

    raise RuntimeError("; ".join(errors) if errors else "Todoist project request failed")


async def _fetch_sections_with_fallback(
    client: httpx.AsyncClient,
    headers: dict[str, str],
    project_id: str,
) -> tuple[list[dict], str]:
    errors: list[str] = []

    for source, url in TODOIST_SECTION_ENDPOINTS:
        try:
            resp = await client.get(url, headers=headers, params={"project_id": project_id})
            resp.raise_for_status()
            return _extract_list_items(resp.json()), source
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            body = _truncate(exc.response.text)
            errors.append(f"{source} status={status} body={body}")
            continue
        except Exception as exc:
            errors.append(f"{source} error={exc}")
            continue

    raise RuntimeError("; ".join(errors) if errors else "Todoist sections request failed")


def _resolve_inbox_project_id(projects: list[dict]) -> str | None:
    for project in projects:
        if project.get("is_inbox_project"):
            return str(project.get("id", "")).strip() or None

    for project in projects:
        name = str(project.get("name", "")).strip().lower()
        if name == "inbox":
            return str(project.get("id", "")).strip() or None

    return None


def _build_task_view(task: dict, index: int) -> dict:
    task_id = str(task.get("id", f"task-{index}"))
    section_id = str(task.get("section_id") or "")

    return {
        "id": task_id,
        "content": task.get("content", "Untitled task"),
        "description": task.get("description", ""),
        "priority": task.get("priority", 1),
        "due": _format_due(task),
        "project_id": task.get("project_id", ""),
        "section_id": section_id,
        "todoist_url": f"todoist://task?id={task_id}",
        "web_url": f"https://app.todoist.com/app/task/{task_id}",
    }


def _section_order_value(section: dict) -> int:
    raw = section.get("order")
    try:
        return int(raw)
    except (TypeError, ValueError):
        return 999999


def _build_section_groups(tasks: list[dict], sections: list[dict]) -> list[dict]:
    tasks_by_section: dict[str, list[dict]] = {}
    unsectioned: list[dict] = []

    for task in tasks:
        section_id = str(task.get("section_id") or "")
        if section_id:
            tasks_by_section.setdefault(section_id, []).append(task)
        else:
            unsectioned.append(task)

    ordered_sections = sorted(
        sections,
        key=lambda section: (
            _section_order_value(section),
            str(section.get("name", "")).lower(),
        ),
    )

    groups: list[dict] = []

    if unsectioned:
        groups.append({"id": "inbox-unsectioned", "name": "Inbox", "tasks": unsectioned})

    for section in ordered_sections:
        sid = str(section.get("id", "")).strip()
        if not sid:
            continue
        section_tasks = tasks_by_section.get(sid, [])
        if not section_tasks:
            continue
        groups.append(
            {
                "id": sid,
                "name": str(section.get("name") or "Section"),
                "tasks": section_tasks,
            }
        )

    known_ids = {str(section.get("id", "")).strip() for section in ordered_sections}
    for sid, section_tasks in tasks_by_section.items():
        if sid in known_ids:
            continue
        groups.append({"id": sid, "name": "Section", "tasks": section_tasks})

    return groups


async def fetch_todoist_tasks(project_id: str | None = None) -> dict:
    settings = get_settings()

    token = (settings.todoist_api_token or "").strip()
    _ = project_id

    if not token:
        return {
            "type": "todo",
            "data": {
                "tasks": [],
                "sections": [],
                "source": "unconfigured",
                "status": "unconfigured",
                "project_id": None,
                "message": "Set TODOIST_API_TOKEN in backend/.env",
            },
        }

    headers = {
        "Authorization": f"Bearer {token}",
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            projects, project_source = await _fetch_projects_with_fallback(client, headers)
            inbox_project_id = _resolve_inbox_project_id(projects)

            if not inbox_project_id:
                raise RuntimeError("Inbox project not found")

            params: dict[str, str | int] = {"limit": 100, "project_id": inbox_project_id}
            raw_tasks, task_source = await _fetch_tasks_with_fallback(client, headers, params)

            try:
                raw_sections, section_source = await _fetch_sections_with_fallback(
                    client,
                    headers,
                    inbox_project_id,
                )
            except Exception as section_exc:
                _throttled_warning(
                    f"todoist-sections:{type(section_exc).__name__}:{str(section_exc)[:120]}",
                    f"Todoist sections fetch failed: {section_exc}",
                )
                raw_sections = []
                section_source = "none"

        raw_tasks = sorted(raw_tasks, key=_task_sort_key)

        tasks = [_build_task_view(task, idx) for idx, task in enumerate(raw_tasks[:30])]
        sections = _build_section_groups(tasks, raw_sections)

        return {
            "type": "todo",
            "data": {
                "tasks": tasks,
                "sections": sections,
                "source": f"{task_source}; projects={project_source}; sections={section_source}",
                "status": "connected",
                "project_id": inbox_project_id,
                "scope": "inbox",
                "view_url": "todoist://inbox",
                "add_task_url": "todoist://addtask",
            },
        }
    except Exception as exc:
        error_key = f"todoist-fetch:{type(exc).__name__}:{str(exc)[:120]}"
        _throttled_warning(error_key, f"Todoist fetch failed: {exc}")

    return {
        "type": "todo",
        "data": {
            "tasks": [],
            "sections": [],
            "source": "error",
            "status": "error",
            "project_id": None,
            "message": "Unable to fetch Todoist tasks",
        },
    }
