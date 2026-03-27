import httpx
import logging

logger = logging.getLogger("glanceos.cricket")

# Uses the free Cricbuzz / Cricket Data API via cricketdata.org
# Fallback: scrape ESPN Cricinfo's public JSON endpoints
CRICAPI_BASE = "https://api.cricapi.com/v1"


async def fetch_cricket_scores(api_key: str = "") -> dict:
    """Fetch live IPL / international cricket scores."""

    # Try the free espncricinfo public endpoint first (no key needed)
    try:
        return await _fetch_espn_scores()
    except Exception:
        logger.debug("ESPN endpoint failed, trying cricapi")

    if api_key:
        try:
            return await _fetch_cricapi(api_key)
        except Exception:
            logger.exception("cricapi failed")

    return {
        "type": "cricket",
        "data": {
            "matches": _get_fallback_matches(),
            "source": "sample",
        },
    }


async def _fetch_espn_scores() -> dict:
    """Fetch from ESPN Cricinfo's public live scores JSON."""
    url = "https://www.espncricinfo.com/api/livescores"
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url, headers={"User-Agent": "GlanceOS/0.1"})
        resp.raise_for_status()
        raw = resp.json()

    matches = []
    for m in raw.get("matches", raw.get("data", []))[:6]:
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
    for m in raw.get("data", [])[:6]:
        t1 = m.get("teamInfo", [{}])[0] if m.get("teamInfo") else {}
        t2 = m.get("teamInfo", [{}, {}])[1] if len(m.get("teamInfo", [])) > 1 else {}
        scores = m.get("score", [])
        matches.append({
            "id": m.get("id", ""),
            "title": m.get("name", "Match"),
            "status": m.get("status", ""),
            "team1": {
                "name": t1.get("shortname", "T1"),
                "score": scores[0].get("r", "") if scores else "",
            },
            "team2": {
                "name": t2.get("shortname", "T2"),
                "score": scores[1].get("r", "") if len(scores) > 1 else "",
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
