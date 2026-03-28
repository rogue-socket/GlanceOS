import httpx
import logging

logger = logging.getLogger("glanceos.cricket")

# Uses the free Cricbuzz / Cricket Data API via cricketdata.org
# Fallback: scrape ESPN Cricinfo's public JSON endpoints
CRICAPI_BASE = "https://api.cricapi.com/v1"
ESPN_SCOREBOARD_URL = "https://site.api.espn.com/apis/site/v2/sports/cricket/scoreboard"


async def fetch_cricket_scores(api_key: str = "") -> dict:
    """Fetch live IPL / international cricket scores."""

    # Prefer keyed source when available for reliability.
    if api_key:
        try:
            data = await _fetch_cricapi(api_key)
            if data.get("data", {}).get("matches"):
                return data
        except Exception:
            logger.exception("cricapi failed")

    # Preferred live source: ESPN public scoreboard API.
    try:
        data = await _fetch_espn_scoreboard()
        if data.get("data", {}).get("matches"):
            return data
    except Exception:
        logger.debug("ESPN scoreboard endpoint failed")

    # Backup live source: legacy ESPN Cricinfo endpoint.
    try:
        data = await _fetch_espn_scores()
        if data.get("data", {}).get("matches"):
            return data
    except Exception:
        logger.debug("Legacy ESPN endpoint failed, trying cricapi")

    return {
        "type": "cricket",
        "data": {
            "matches": _get_fallback_matches(),
            "source": "sample",
        },
    }


def _clean_score(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if not text:
        return ""
    return text


async def _fetch_espn_scoreboard() -> dict:
    """Fetch live scores from ESPN's public site scoreboard API."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(ESPN_SCOREBOARD_URL, headers={"User-Agent": "GlanceOS/0.1"})
        resp.raise_for_status()
        raw = resp.json()

    matches = []
    events = raw.get("events", [])
    for event in events[:8]:
        competition = (event.get("competitions") or [{}])[0]
        competitors = competition.get("competitors") or []

        team1 = competitors[0] if len(competitors) > 0 else {}
        team2 = competitors[1] if len(competitors) > 1 else {}

        status = (
            competition.get("status", {}).get("type", {}).get("description")
            or competition.get("status", {}).get("type", {}).get("name")
            or competition.get("status", {}).get("displayClock")
            or event.get("status", {}).get("type", {}).get("description")
            or ""
        )

        matches.append(
            {
                "id": str(event.get("id") or ""),
                "title": event.get("shortName") or event.get("name") or "Match",
                "status": status,
                "team1": {
                    "name": (team1.get("team") or {}).get("shortDisplayName")
                    or (team1.get("team") or {}).get("displayName")
                    or "Team 1",
                    "score": _clean_score(team1.get("score")),
                },
                "team2": {
                    "name": (team2.get("team") or {}).get("shortDisplayName")
                    or (team2.get("team") or {}).get("displayName")
                    or "Team 2",
                    "score": _clean_score(team2.get("score")),
                },
            }
        )

    return {"type": "cricket", "data": {"matches": matches, "source": "espn-scoreboard"}}


async def _fetch_espn_scores() -> dict:
    """Fetch from ESPN Cricinfo's public live scores JSON."""
    url = "https://www.espncricinfo.com/api/livescores"
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url, headers={"User-Agent": "GlanceOS/0.1"})
        resp.raise_for_status()
        raw = resp.json()

    matches = []
    for m in raw.get("matches", raw.get("data", []))[:8]:
        matches.append({
            "id": str(m.get("id", "")),
            "title": m.get("title", m.get("name", "Match")),
            "status": m.get("status", m.get("statusText", "")),
            "team1": _extract_team(m, 0),
            "team2": _extract_team(m, 1),
        })

    return {"type": "cricket", "data": {"matches": matches, "source": "espn"}}


def _extract_team(match: dict, idx: int) -> dict:
    teams = match.get("teams", [])
    if idx < len(teams):
        t = teams[idx]
        return {
            "name": t.get("name", t.get("teamName", f"Team {idx+1}")),
            "score": t.get("score", t.get("scoreValue", "")),
        }
    return {"name": f"Team {idx+1}", "score": ""}


async def _fetch_cricapi(api_key: str) -> dict:
    url = f"{CRICAPI_BASE}/currentMatches"
    params = {"apikey": api_key, "offset": 0}
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        raw = resp.json()

    matches = []
    for m in raw.get("data", [])[:8]:
        t1 = m.get("teamInfo", [{}])[0] if m.get("teamInfo") else {}
        t2 = m.get("teamInfo", [{}, {}])[1] if len(m.get("teamInfo", [])) > 1 else {}
        scores = m.get("score", [])
        score1 = ""
        score2 = ""
        if scores:
            s1 = scores[0]
            s1_runs = s1.get("r")
            s1_wickets = s1.get("w")
            s1_overs = s1.get("o")
            if s1_runs is not None:
                score1 = str(s1_runs)
                if s1_wickets is not None:
                    score1 += f"/{s1_wickets}"
                if s1_overs is not None:
                    score1 += f" ({s1_overs})"
        if len(scores) > 1:
            s2 = scores[1]
            s2_runs = s2.get("r")
            s2_wickets = s2.get("w")
            s2_overs = s2.get("o")
            if s2_runs is not None:
                score2 = str(s2_runs)
                if s2_wickets is not None:
                    score2 += f"/{s2_wickets}"
                if s2_overs is not None:
                    score2 += f" ({s2_overs})"

        matches.append({
            "id": m.get("id", ""),
            "title": m.get("name", "Match"),
            "status": m.get("status", ""),
            "team1": {
                "name": t1.get("shortname", "T1"),
                "score": score1,
            },
            "team2": {
                "name": t2.get("shortname", "T2"),
                "score": score2,
            },
        })

    return {"type": "cricket", "data": {"matches": matches, "source": "cricapi"}}


def _get_fallback_matches() -> list:
    """Sample IPL data when no live API is available."""
    return [
        {
            "id": "ipl-1",
            "title": "CSK vs MI — IPL 2026",
            "status": "CSK won by 6 wickets",
            "team1": {"name": "CSK", "score": "182/4 (18.3)"},
            "team2": {"name": "MI", "score": "178/7 (20.0)"},
        },
        {
            "id": "ipl-2",
            "title": "RCB vs KKR — IPL 2026",
            "status": "In Progress",
            "team1": {"name": "RCB", "score": "94/2 (11.4)"},
            "team2": {"name": "KKR", "score": "165/8 (20.0)"},
        },
        {
            "id": "ipl-3",
            "title": "DC vs RR — IPL 2026",
            "status": "Starts at 7:30 PM IST",
            "team1": {"name": "DC", "score": "—"},
            "team2": {"name": "RR", "score": "—"},
        },
    ]
