import logging
import re
from datetime import datetime, date, timezone
from urllib.parse import quote

import httpx

from app.config import get_settings

logger = logging.getLogger("glanceos.calendar")


def _parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        if value.endswith("Z"):
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _format_event_time(dt: datetime | None) -> str | None:
    if not dt:
        return None
    local_dt = dt.astimezone()
    return local_dt.strftime("%Y-%m-%d %H:%M")


def _parse_ics_datetime(raw: str) -> tuple[datetime | None, bool]:
    # Supports common Google ICS formats: YYYYMMDD (all-day), YYYYMMDDTHHMMSSZ, YYYYMMDDTHHMMSS
    if not raw:
        return None, False

    value = raw.strip()
    if "T" not in value:
        try:
            day = datetime.strptime(value, "%Y%m%d").date()
            return datetime.combine(day, datetime.min.time(), tzinfo=timezone.utc), True
        except ValueError:
            return None, True

    for fmt in ("%Y%m%dT%H%M%SZ", "%Y%m%dT%H%M%S"):
        try:
            parsed = datetime.strptime(value, fmt)
            if value.endswith("Z"):
                parsed = parsed.replace(tzinfo=timezone.utc)
            else:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed, False
        except ValueError:
            continue

    return None, False


def _unfold_ics_lines(text: str) -> list[str]:
    lines = text.replace("\r", "").split("\n")
    unfolded: list[str] = []
    for line in lines:
        if not line:
            continue
        if line.startswith((" ", "\t")) and unfolded:
            unfolded[-1] += line[1:]
        else:
            unfolded.append(line)
    return unfolded


async def _fetch_google_calendar_api(calendar_id: str, api_key: str) -> dict:
    now_utc = datetime.now(timezone.utc)
    encoded_calendar_id = quote(calendar_id, safe="")
    url = f"https://www.googleapis.com/calendar/v3/calendars/{encoded_calendar_id}/events"
    params = {
        "key": api_key,
        "maxResults": 12,
        "singleEvents": "true",
        "orderBy": "startTime",
        "timeMin": now_utc.isoformat().replace("+00:00", "Z"),
    }

    async with httpx.AsyncClient(timeout=12.0) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        payload = resp.json()

    events = []
    for idx, item in enumerate(payload.get("items", [])):
        start_raw = item.get("start", {})
        end_raw = item.get("end", {})

        all_day = bool(start_raw.get("date"))
        start_dt = _parse_iso_datetime(start_raw.get("dateTime"))
        end_dt = _parse_iso_datetime(end_raw.get("dateTime"))

        start_date = start_raw.get("date")
        end_date = end_raw.get("date")

        if all_day and start_date:
            try:
                start_dt = datetime.combine(
                    date.fromisoformat(start_date), datetime.min.time(), tzinfo=timezone.utc
                )
            except ValueError:
                start_dt = None

        if all_day and end_date:
            try:
                end_dt = datetime.combine(
                    date.fromisoformat(end_date), datetime.min.time(), tzinfo=timezone.utc
                )
            except ValueError:
                end_dt = None

        if not start_dt:
            continue

        events.append(
            {
                "id": item.get("id", f"api-{idx}"),
                "title": item.get("summary") or "Untitled event",
                "start": _format_event_time(start_dt),
                "end": _format_event_time(end_dt),
                "all_day": all_day,
                "location": item.get("location", ""),
                "url": item.get("htmlLink", ""),
            }
        )

    return {
        "type": "calendar",
        "data": {
            "events": events,
            "source": "google-api",
            "status": "connected",
            "calendar_id": calendar_id,
        },
    }


async def _fetch_google_calendar_ics(ics_url: str) -> dict:
    async with httpx.AsyncClient(timeout=12.0, follow_redirects=True) as client:
        resp = await client.get(ics_url)
        resp.raise_for_status()
        text = resp.text

    lines = _unfold_ics_lines(text)
    events = []
    now_utc = datetime.now(timezone.utc)

    current: dict[str, str] = {}
    in_event = False

    def flush_event() -> None:
        if not current:
            return

        summary = current.get("SUMMARY") or "Untitled event"
        uid = current.get("UID") or f"ics-{len(events)}"
        location = current.get("LOCATION", "")
        url = current.get("URL", "")

        start_raw = current.get("DTSTART", "")
        end_raw = current.get("DTEND", "")

        start_dt, all_day = _parse_ics_datetime(start_raw)
        end_dt, _ = _parse_ics_datetime(end_raw)

        if not start_dt:
            return

        # Keep only current/upcoming items.
        if end_dt and end_dt < now_utc:
            return
        if not end_dt and start_dt < now_utc and not all_day:
            return

        events.append(
            {
                "id": uid,
                "title": summary,
                "start": _format_event_time(start_dt),
                "end": _format_event_time(end_dt),
                "all_day": all_day,
                "location": location,
                "url": url,
            }
        )

    for line in lines:
        if line == "BEGIN:VEVENT":
            in_event = True
            current = {}
            continue

        if line == "END:VEVENT":
            flush_event()
            in_event = False
            current = {}
            continue

        if not in_event:
            continue

        if ":" not in line:
            continue

        key_part, value = line.split(":", 1)
        key = key_part.split(";", 1)[0].strip().upper()

        if key in {"UID", "SUMMARY", "LOCATION", "URL", "DTSTART", "DTEND"}:
            current[key] = value.strip()

    events.sort(key=lambda item: item.get("start") or "")

    return {
        "type": "calendar",
        "data": {
            "events": events[:12],
            "source": "google-ics",
            "status": "connected",
            "calendar_id": "ics",
        },
    }


async def fetch_calendar_events() -> dict:
    settings = get_settings()

    ics_url = (settings.google_calendar_ics_url or "").strip()
    calendar_id = (settings.google_calendar_id or "").strip()
    api_key = (settings.google_calendar_api_key or "").strip()

    if ics_url:
        try:
            return await _fetch_google_calendar_ics(ics_url)
        except Exception as exc:
            logger.warning("Google Calendar ICS fetch failed: %s", exc)

    if calendar_id and api_key:
        try:
            return await _fetch_google_calendar_api(calendar_id, api_key)
        except Exception as exc:
            logger.warning("Google Calendar API fetch failed: %s", exc)

    if not ics_url and not (calendar_id and api_key):
        return {
            "type": "calendar",
            "data": {
                "events": [],
                "source": "unconfigured",
                "status": "unconfigured",
                "message": "Set GOOGLE_CALENDAR_ICS_URL or GOOGLE_CALENDAR_ID + GOOGLE_CALENDAR_API_KEY",
            },
        }

    return {
        "type": "calendar",
        "data": {
            "events": [],
            "source": "error",
            "status": "error",
            "message": "Unable to fetch Google Calendar events",
        },
    }
