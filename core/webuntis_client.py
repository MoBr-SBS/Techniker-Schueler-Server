"""
core/webuntis_client.py – WebUntis JSON-RPC Client.

Ruft Stundenplandaten über die offizielle WebUntis-API ab.
Ergebnisse werden 30 Minuten im Arbeitsspeicher gecacht.
"""

import datetime
import requests

CACHE_TTL = 1800  # Sekunden (30 Minuten)
_cache: dict = {}


class WebUntisError(Exception):
    pass


# ── Interner RPC-Aufruf ───────────────────────────────────────────────────────

def _rpc(session: requests.Session, url: str, method: str, params: dict = None):
    payload = {"id": "1", "method": method, "params": params or {}, "jsonrpc": "2.0"}
    try:
        r = session.post(url, json=payload, timeout=10)
        r.raise_for_status()
    except requests.Timeout:
        raise WebUntisError("WebUntis antwortet nicht (Timeout nach 10 s).")
    except requests.ConnectionError:
        raise WebUntisError("WebUntis-Server nicht erreichbar. Serveradresse prüfen.")
    except requests.HTTPError as e:
        raise WebUntisError(f"HTTP-Fehler: {e}")

    data = r.json()
    if "error" in data:
        code = data["error"].get("code", 0)
        msg  = data["error"].get("message", "Unbekannter Fehler")
        if code in (-8520, -8504, -8503):
            raise WebUntisError("Ungültige WebUntis-Zugangsdaten.")
        raise WebUntisError(f"WebUntis: {msg} (Code {code})")

    return data.get("result")


def _safe_rpc(session, url, method, params=None) -> list:
    try:
        return _rpc(session, url, method, params) or []
    except Exception:
        return []


# ── Hilfsfunktionen ───────────────────────────────────────────────────────────

def _fmt(t: int) -> str:
    """Wandelt WebUntis-Zeit (z. B. 800 oder 1330) in 'HH:MM' um."""
    return f"{t // 100:02d}:{t % 100:02d}"


def _to_minutes(t: int) -> int:
    return (t // 100) * 60 + (t % 100)


def _parse_timegrid(timegrid) -> tuple:
    """
    Gibt (period_map, periods_info) zurück.
      period_map   : {startTime (int) → Stundennummer (1-basiert)}
      periods_info : Liste von Dicts mit start, end, pause_nach (Minuten)
    """
    # Ersten Tag mit Einträgen nutzen – Zeiten sind in der Regel täglich gleich
    units = []
    for day in (timegrid or []):
        candidate = day.get("timeUnits", [])
        if len(candidate) > len(units):
            units = candidate

    period_map   = {}
    periods_info = []
    for i, unit in enumerate(units, start=1):
        start = unit.get("startTime", 0)
        end   = unit.get("endTime",   0)
        period_map[start] = i
        periods_info.append({
            "stunde":     i,
            "start":      _fmt(start),
            "end":        _fmt(end),
            "start_int":  start,
            "end_int":    end,
            "pause_nach": 0,   # wird unten berechnet
        })

    # Pausendauer zwischen aufeinanderfolgenden Stunden berechnen
    for i in range(len(periods_info) - 1):
        gap = _to_minutes(periods_info[i + 1]["start_int"]) \
            - _to_minutes(periods_info[i]["end_int"])
        periods_info[i]["pause_nach"] = max(gap, 0)

    return period_map, periods_info


def _resolve_name(items: list, lookup: dict, long: bool = True) -> str:
    if not items:
        return ""
    item    = items[0]
    item_id = item.get("id")
    ref     = lookup.get(item_id, {}) if item_id else {}
    if long:
        return (item.get("longname") or item.get("name")
                or ref.get("longname") or ref.get("name") or "–")
    return (item.get("name") or ref.get("name") or "")


def _build_grid(periods, period_map: dict, n_periods: int, monday: datetime.date,
                subjects: dict, teachers: dict, rooms: dict) -> dict:
    """Baut das Grid {stunde → {wochentag → Slot-Dict oder None}}."""
    grid = {s: {d: None for d in range(5)} for s in range(1, n_periods + 1)}

    for p in (periods or []):
        date_str = str(p.get("date", ""))
        if len(date_str) != 8:
            continue
        try:
            lesson_date = datetime.date(
                int(date_str[:4]), int(date_str[4:6]), int(date_str[6:])
            )
        except ValueError:
            continue

        wochentag = (lesson_date - monday).days
        if not (0 <= wochentag <= 4):
            continue

        stunde = period_map.get(p.get("startTime"))
        if stunde is None or stunde > n_periods:
            continue

        grid[stunde][wochentag] = {
            "fach":      _resolve_name(p.get("su") or [], subjects, long=True),
            "lehrer":    _resolve_name(p.get("te") or [], teachers, long=False),
            "raum":      _resolve_name(p.get("ro") or [], rooms,    long=False),
            "cancelled": p.get("cellState") == "CANCELLED",
        }

    return grid


# ── Öffentliche API ───────────────────────────────────────────────────────────

def fetch_timetable(server: str, school: str, username: str, password: str,
                    monday: datetime.date = None) -> tuple:
    """
    Gibt (grid, monday, periods_info) zurück oder wirft WebUntisError.
    monday: Zielwoche; None = aktuelle Woche.
    """
    url = f"https://{server}/WebUntis/jsonrpc.do?school={school}"
    s   = requests.Session()

    auth = _rpc(s, url, "authenticate", {
        "user":     username,
        "password": password,
        "client":   "schulserver",
    })

    person_id   = auth["personId"]
    person_type = auth["personType"]
    klasse_id   = auth.get("klasseId")

    if monday is None:
        today  = datetime.date.today()
        monday = today - datetime.timedelta(days=today.weekday())
    start_date = int(monday.strftime("%Y%m%d"))
    end_date   = int((monday + datetime.timedelta(days=4)).strftime("%Y%m%d"))

    timegrid               = _safe_rpc(s, url, "getTimegridUnits")
    period_map, periods_info = _parse_timegrid(timegrid)
    n_periods              = len(periods_info) or 8

    periods = _rpc(s, url, "getTimetable", {
        "id":        person_id,
        "type":      person_type,
        "startDate": start_date,
        "endDate":   end_date,
    })

    # Fallback: Klassenplan wenn Schülerplan leer
    if klasse_id and not periods:
        periods = _rpc(s, url, "getTimetable", {
            "id":        klasse_id,
            "type":      1,
            "startDate": start_date,
            "endDate":   end_date,
        })

    raw_subjects = _safe_rpc(s, url, "getSubjects")
    raw_teachers = _safe_rpc(s, url, "getTeachers")
    raw_rooms    = _safe_rpc(s, url, "getRooms")

    subjects = {item["id"]: item for item in raw_subjects if "id" in item}
    teachers = {item["id"]: item for item in raw_teachers if "id" in item}
    rooms    = {item["id"]: item for item in raw_rooms    if "id" in item}

    try:
        _rpc(s, url, "logout")
    except Exception:
        pass

    grid = _build_grid(periods, period_map, n_periods, monday, subjects, teachers, rooms)
    return grid, monday, periods_info


def get_timetable_cached(user_id: int, server: str, school: str,
                         username: str, password: str,
                         monday: datetime.date = None) -> tuple:
    """
    Gibt (grid, monday, periods_info, warnung_oder_None) zurück.
    Cache-Key: (user_id, monday_iso) – jede Woche wird separat gecacht.
    """
    if monday is None:
        today  = datetime.date.today()
        monday = today - datetime.timedelta(days=today.weekday())

    cache_key = (user_id, monday.isoformat())
    cached    = _cache.get(cache_key)
    if cached:
        age = (datetime.datetime.now() - cached["ts"]).total_seconds()
        if age < CACHE_TTL:
            return cached["grid"], cached["monday"], cached["periods_info"], None

    try:
        grid, monday, periods_info = fetch_timetable(
            server, school, username, password, monday
        )
        _cache[cache_key] = {
            "grid": grid, "monday": monday,
            "periods_info": periods_info,
            "ts": datetime.datetime.now(),
        }
        return grid, monday, periods_info, None
    except WebUntisError as e:
        if cached:
            return (cached["grid"], cached["monday"], cached["periods_info"],
                    f"Aktualisierung fehlgeschlagen: {e}")
        return None, None, [], str(e)


def invalidate_cache(user_id: int, monday: datetime.date = None):
    if monday is not None:
        _cache.pop((user_id, monday.isoformat()), None)
    else:
        for key in list(_cache.keys()):
            if key[0] == user_id:
                _cache.pop(key, None)


def clear_all_caches():
    _cache.clear()
