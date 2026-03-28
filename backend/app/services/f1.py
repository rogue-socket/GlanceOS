from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

logger = logging.getLogger("glanceos.f1")

JOLPICA_BASE_URL = "https://api.jolpi.ca/ergast/f1"
OPENF1_BASE_URL = "https://api.openf1.org/v1"

TARGET_SESSION_NAMES = {
    "Practice 1",
    "Practice 2",
    "Practice 3",
    "Qualifying",
    "Race",
}

SESSION_SORT_ORDER = {
    "Practice 1": 1,
    "Practice 2": 2,
    "Practice 3": 3,
    "Qualifying": 4,
    "Race": 5,
}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _to_iso(dt: datetime | None) -> str | None:
    if not dt:
        return None
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        normalized = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        return None


def _parse_ergast_datetime(date_value: str | None, time_value: str | None = None) -> datetime | None:
    if not date_value:
        return None
    if time_value:
        return _parse_datetime(f"{date_value}T{time_value}")
    return _parse_datetime(f"{date_value}T00:00:00Z")


def _to_int(value: Any, fallback: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _to_float(value: Any, fallback: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def _read_numeric(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _read_last_numeric(value: Any) -> float | None:
    if isinstance(value, list):
        numeric_values = [v for v in (_read_numeric(item) for item in value) if v is not None]
        if not numeric_values:
            return None
        return numeric_values[-1]
    return _read_numeric(value)


def _format_seconds(value: float | None) -> str | None:
    if value is None:
        return None
    if value < 0:
        return None
    if value < 60:
        return f"{value:.3f}s"

    minutes = int(value // 60)
    seconds = value - (minutes * 60)
    return f"{minutes}:{seconds:06.3f}"


def _format_gap(value: float | None) -> str | None:
    if value is None:
        return None
    if abs(value) < 0.001:
        return "Leader"
    return f"+{value:.3f}s"


async def _fetch_json(client: httpx.AsyncClient, url: str, params: dict[str, Any] | None = None) -> Any:
    response = await client.get(url, params=params)
    response.raise_for_status()
    return response.json()


def _parse_driver_standings(payload: dict[str, Any]) -> tuple[str, str, list[dict[str, Any]]]:
    standings_table = payload.get("MRData", {}).get("StandingsTable", {})
    season = str(standings_table.get("season") or "")
    round_number = str(standings_table.get("round") or "")

    lists = standings_table.get("StandingsLists") or []
    if not lists:
        return season, round_number, []

    output: list[dict[str, Any]] = []
    for entry in lists[0].get("DriverStandings", []):
        driver = entry.get("Driver") or {}
        constructors = entry.get("Constructors") or []
        constructor = constructors[0] if constructors else {}
        output.append(
            {
                "position": _to_int(entry.get("position")),
                "points": _to_float(entry.get("points")),
                "wins": _to_int(entry.get("wins")),
                "driver": {
                    "code": driver.get("code") or "",
                    "name": f"{driver.get('givenName', '')} {driver.get('familyName', '')}".strip(),
                    "nationality": driver.get("nationality") or "",
                },
                "team": constructor.get("name") or "",
            }
        )

    return season, round_number, output


def _parse_constructor_standings(payload: dict[str, Any]) -> tuple[str, str, list[dict[str, Any]]]:
    standings_table = payload.get("MRData", {}).get("StandingsTable", {})
    season = str(standings_table.get("season") or "")
    round_number = str(standings_table.get("round") or "")

    lists = standings_table.get("StandingsLists") or []
    if not lists:
        return season, round_number, []

    output: list[dict[str, Any]] = []
    for entry in lists[0].get("ConstructorStandings", []):
        constructor = entry.get("Constructor") or {}
        output.append(
            {
                "position": _to_int(entry.get("position")),
                "points": _to_float(entry.get("points")),
                "wins": _to_int(entry.get("wins")),
                "team": {
                    "name": constructor.get("name") or "",
                    "nationality": constructor.get("nationality") or "",
                },
            }
        )

    return season, round_number, output


def _find_race_week(races: list[dict[str, Any]], now: datetime) -> dict[str, Any] | None:
    candidates: list[tuple[float, dict[str, Any]]] = []

    for race in races:
        race_start = _parse_ergast_datetime(race.get("date"), race.get("time"))
        if not race_start:
            continue

        first_session = _parse_ergast_datetime(
            (race.get("FirstPractice") or {}).get("date"),
            (race.get("FirstPractice") or {}).get("time"),
        )
        if not first_session:
            first_session = race_start - timedelta(days=2)

        window_start = first_session - timedelta(hours=24)
        window_end = race_start + timedelta(hours=12)
        if window_start <= now <= window_end:
            distance_seconds = abs((race_start - now).total_seconds())
            candidates.append((distance_seconds, race))

    if not candidates:
        return None

    candidates.sort(key=lambda item: item[0])
    return candidates[0][1]


async def _fetch_meeting_key(
    client: httpx.AsyncClient,
    season: str,
    country_name: str,
    race_name: str,
    race_start: datetime | None,
) -> int | None:
    params: dict[str, Any] = {"year": season}
    if country_name:
        params["country_name"] = country_name

    meetings_payload = await _fetch_json(
        client,
        f"{OPENF1_BASE_URL}/meetings",
        params=params,
    )

    meetings = meetings_payload if isinstance(meetings_payload, list) else []
    if not meetings:
        return None

    race_name_lower = race_name.lower()
    scored: list[tuple[float, int]] = []

    for meeting in meetings:
        meeting_key = _to_int(meeting.get("meeting_key"), fallback=-1)
        if meeting_key <= 0:
            continue

        name = str(meeting.get("meeting_name") or "")
        score = 1000.0
        if race_name_lower and race_name_lower in name.lower():
            score -= 500.0

        meeting_start = _parse_datetime(meeting.get("date_start"))
        if race_start and meeting_start:
            score += abs((meeting_start - race_start).total_seconds())

        scored.append((score, meeting_key))

    if not scored:
        return None

    scored.sort(key=lambda item: item[0])
    return scored[0][1]


async def _fetch_session_standings(
    client: httpx.AsyncClient,
    session_key: int,
    session_name: str,
) -> list[dict[str, Any]]:
    results_payload, drivers_payload = await asyncio.gather(
        _fetch_json(client, f"{OPENF1_BASE_URL}/session_result", params={"session_key": session_key}),
        _fetch_json(client, f"{OPENF1_BASE_URL}/drivers", params={"session_key": session_key}),
        return_exceptions=True,
    )

    results: list[dict[str, Any]] = []
    if isinstance(results_payload, list):
        results = results_payload

    drivers_map: dict[int, dict[str, Any]] = {}
    if isinstance(drivers_payload, list):
        for driver in drivers_payload:
            number = _to_int(driver.get("driver_number"), fallback=-1)
            if number > 0:
                drivers_map[number] = driver

    standings: list[dict[str, Any]] = []
    for row in sorted(results, key=lambda item: _to_int(item.get("position"), fallback=999)):
        position = _to_int(row.get("position"), fallback=0)
        if position <= 0:
            continue

        driver_number = _to_int(row.get("driver_number"), fallback=0)
        driver = drivers_map.get(driver_number, {})

        duration_value = _read_last_numeric(row.get("duration"))
        gap_value = _read_last_numeric(row.get("gap_to_leader"))

        if session_name == "Qualifying":
            metric = _format_seconds(duration_value)
        elif session_name.startswith("Practice"):
            metric = _format_seconds(duration_value)
        else:
            metric = _format_seconds(duration_value)

        standings.append(
            {
                "position": position,
                "driver_number": driver_number,
                "driver": {
                    "code": driver.get("name_acronym") or "",
                    "name": driver.get("full_name") or "",
                },
                "team": driver.get("team_name") or "",
                "team_color": driver.get("team_colour") or "",
                "points": _read_numeric(row.get("points")),
                "laps": _to_int(row.get("number_of_laps"), fallback=0),
                "metric": metric,
                "gap": _format_gap(gap_value),
                "dnf": bool(row.get("dnf")),
                "dns": bool(row.get("dns")),
                "dsq": bool(row.get("dsq")),
            }
        )

    return standings


async def _fetch_race_weekend_data(
    client: httpx.AsyncClient,
    race: dict[str, Any],
    now: datetime,
) -> dict[str, Any]:
    season = str(race.get("season") or "")
    race_name = str(race.get("raceName") or "")
    round_number = str(race.get("round") or "")

    location = ((race.get("Circuit") or {}).get("Location") or {})
    country_name = str(location.get("country") or "")

    race_start = _parse_ergast_datetime(race.get("date"), race.get("time"))
    meeting_key = await _fetch_meeting_key(client, season, country_name, race_name, race_start)
    if not meeting_key:
        return {
            "meeting_key": None,
            "sessions": [],
            "latest_completed_session_key": None,
        }

    sessions_payload = await _fetch_json(client, f"{OPENF1_BASE_URL}/sessions", params={"meeting_key": meeting_key})
    sessions = sessions_payload if isinstance(sessions_payload, list) else []

    filtered = [session for session in sessions if str(session.get("session_name") or "") in TARGET_SESSION_NAMES]
    filtered.sort(
        key=lambda s: (
            SESSION_SORT_ORDER.get(str(s.get("session_name") or ""), 99),
            _parse_datetime(s.get("date_start")) or datetime.max.replace(tzinfo=timezone.utc),
        )
    )

    output_sessions: list[dict[str, Any]] = []
    latest_completed_session_key: int | None = None

    for session in filtered:
        session_key = _to_int(session.get("session_key"), fallback=0)
        if session_key <= 0:
            continue

        session_name = str(session.get("session_name") or "")
        start_dt = _parse_datetime(session.get("date_start"))
        end_dt = _parse_datetime(session.get("date_end"))

        status = "scheduled"
        if start_dt and end_dt and start_dt <= now <= end_dt:
            status = "live"
        elif end_dt and now > end_dt:
            status = "completed"

        standings: list[dict[str, Any]] = []
        if status in {"completed", "live"}:
            try:
                standings = await _fetch_session_standings(client, session_key, session_name)
            except Exception:
                logger.debug("Failed to fetch session standings for %s", session_key)

        if status == "completed" and standings:
            latest_completed_session_key = session_key

        output_sessions.append(
            {
                "session_key": session_key,
                "name": session_name,
                "status": status,
                "start": _to_iso(start_dt),
                "end": _to_iso(end_dt),
                "standings": standings,
            }
        )

    return {
        "meeting_key": meeting_key,
        "sessions": output_sessions,
        "latest_completed_session_key": latest_completed_session_key,
    }


async def fetch_f1_data() -> dict[str, Any]:
    now = _utc_now()

    timeout = httpx.Timeout(12.0, connect=6.0)
    async with httpx.AsyncClient(timeout=timeout, headers={"User-Agent": "GlanceOS/0.1"}) as client:
        driver_task = _fetch_json(client, f"{JOLPICA_BASE_URL}/current/driverstandings.json")
        constructor_task = _fetch_json(client, f"{JOLPICA_BASE_URL}/current/constructorstandings.json")
        schedule_task = _fetch_json(client, f"{JOLPICA_BASE_URL}/current.json")

        driver_payload, constructor_payload, schedule_payload = await asyncio.gather(
            driver_task,
            constructor_task,
            schedule_task,
            return_exceptions=True,
        )

        if isinstance(driver_payload, Exception):
            logger.exception("Failed to fetch F1 driver standings")
            driver_payload = {}
        if not isinstance(driver_payload, dict):
            driver_payload = {}

        if isinstance(constructor_payload, Exception):
            logger.exception("Failed to fetch F1 constructor standings")
            constructor_payload = {}
        if not isinstance(constructor_payload, dict):
            constructor_payload = {}

        if isinstance(schedule_payload, Exception):
            logger.exception("Failed to fetch F1 schedule")
            schedule_payload = {}
        if not isinstance(schedule_payload, dict):
            schedule_payload = {}

        season_a, standings_round_a, driver_standings = _parse_driver_standings(driver_payload)
        season_b, standings_round_b, constructor_standings = _parse_constructor_standings(constructor_payload)

        season = season_a or season_b
        standings_round = standings_round_a or standings_round_b

        races = (
            schedule_payload.get("MRData", {})
            .get("RaceTable", {})
            .get("Races", [])
            if isinstance(schedule_payload, dict)
            else []
        )

        race_week_race = _find_race_week(races, now)
        is_race_week = race_week_race is not None

        race_weekend = {
            "race": None,
            "meeting_key": None,
            "sessions": [],
            "latest_completed_session_key": None,
        }

        if race_week_race:
            race_start = _parse_ergast_datetime(race_week_race.get("date"), race_week_race.get("time"))
            first_practice = _parse_ergast_datetime(
                (race_week_race.get("FirstPractice") or {}).get("date"),
                (race_week_race.get("FirstPractice") or {}).get("time"),
            )
            weekend_data = await _fetch_race_weekend_data(client, race_week_race, now)
            race_weekend = {
                "race": {
                    "season": str(race_week_race.get("season") or ""),
                    "round": str(race_week_race.get("round") or ""),
                    "name": race_week_race.get("raceName") or "",
                    "circuit": ((race_week_race.get("Circuit") or {}).get("circuitName") or ""),
                    "country": (((race_week_race.get("Circuit") or {}).get("Location") or {}).get("country") or ""),
                    "start": _to_iso(race_start),
                    "first_practice": _to_iso(first_practice),
                },
                "meeting_key": weekend_data.get("meeting_key"),
                "sessions": weekend_data.get("sessions") or [],
                "latest_completed_session_key": weekend_data.get("latest_completed_session_key"),
            }

    return {
        "type": "f1",
        "data": {
            "season": season,
            "standings_round": standings_round,
            "is_race_week": is_race_week,
            "driver_standings": driver_standings,
            "constructor_standings": constructor_standings,
            "race_weekend": race_weekend,
            "updated_at": _to_iso(now),
            "source": "jolpica+openf1",
        },
    }
