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
            "fach_kurz": _resolve_name(p.get("su") or [], subjects, long=False),
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


_RANGE_HALF = 2  # Wochen vor/nach der angefragten Woche, die pro Session mitgeladen werden


def get_timetable_cached(user_id: int, server: str, school: str,
                         username: str, password: str,
                         monday: datetime.date = None) -> tuple:
    """
    Gibt (grid, monday, periods_info, warnung_oder_None) zurück.
    Bei Cache-Miss werden ±_RANGE_HALF Wochen in einer einzigen Session geholt
    und jeweils separat gecacht.
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

    half        = _RANGE_HALF
    range_start = monday - datetime.timedelta(weeks=half)
    range_end   = monday + datetime.timedelta(weeks=half, days=4)

    try:
        url = f"https://{server}/WebUntis/jsonrpc.do?school={school}"
        s   = requests.Session()

        auth = _rpc(s, url, "authenticate", {
            "user": username, "password": password, "client": "schulserver",
        })
        person_id   = auth["personId"]
        person_type = auth["personType"]
        klasse_id   = auth.get("klasseId")

        timegrid               = _safe_rpc(s, url, "getTimegridUnits")
        period_map, periods_info = _parse_timegrid(timegrid)
        n_periods              = len(periods_info) or 8

        sd = int(range_start.strftime("%Y%m%d"))
        ed = int(range_end.strftime("%Y%m%d"))

        periods = _rpc(s, url, "getTimetable", {
            "id": person_id, "type": person_type,
            "startDate": sd, "endDate": ed,
        })
        if klasse_id and not periods:
            periods = _rpc(s, url, "getTimetable", {
                "id": klasse_id, "type": 1,
                "startDate": sd, "endDate": ed,
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

        # Alle Wochen im Range einzeln aufbauen und cachen
        now = datetime.datetime.now()
        for offset in range(-half, half + 1):
            week_monday = monday + datetime.timedelta(weeks=offset)
            grid = _build_grid(periods, period_map, n_periods, week_monday,
                               subjects, teachers, rooms)
            _cache[(user_id, week_monday.isoformat())] = {
                "grid":         grid,
                "monday":       week_monday,
                "periods_info": periods_info,
                "ts":           now,
            }

        entry = _cache[cache_key]
        return entry["grid"], entry["monday"], entry["periods_info"], None

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


# ── Prüfungen ─────────────────────────────────────────────────────────────────

_EXAM_TYPE_MAP = {"SA": "Schulaufgabe", "Ex": "Ex"}


def _parse_exam_date(d: int) -> datetime.date:
    s = str(d)
    return datetime.date(int(s[:4]), int(s[4:6]), int(s[6:]))


def fetch_exams(server: str, school: str, username: str, password: str,
                start_date: datetime.date, end_date: datetime.date) -> list:
    """Gibt eine sortierte Liste normalisierter Prüfungs-Dicts zurück."""
    url = f"https://{server}/WebUntis/jsonrpc.do?school={school}"
    s   = requests.Session()

    auth = _rpc(s, url, "authenticate", {
        "user": username, "password": password, "client": "schulserver",
    })
    student_id = auth["personId"]

    exams_url = f"https://{server}/WebUntis/api/exams"
    try:
        r = s.get(exams_url, params={
            "startDate":  int(start_date.strftime("%Y%m%d")),
            "endDate":    int(end_date.strftime("%Y%m%d")),
            "studentId":  student_id,
            "withGrades": "true",
            "klasseId":   -1,
        }, timeout=10)
        r.raise_for_status()
        raw = r.json().get("data", {}).get("exams", [])
    except requests.RequestException as e:
        raise WebUntisError(f"Prüfungen konnten nicht abgerufen werden: {e}")
    finally:
        try:
            _rpc(s, url, "logout")
        except Exception:
            pass

    result = []
    for exam in raw:
        try:
            datum = _parse_exam_date(exam["examDate"])
        except (KeyError, ValueError):
            continue
        result.append({
            "datum":    datum,
            "fach":     exam.get("subject", ""),
            "art":      _EXAM_TYPE_MAP.get(exam.get("examType", ""), exam.get("examType", "")),
            "name":     exam.get("name", ""),
            "start":    _fmt(exam["startTime"]) if exam.get("startTime") else "",
            "end":      _fmt(exam["endTime"])   if exam.get("endTime")   else "",
            "rooms":    exam.get("rooms", []),
            "teachers": exam.get("teachers", []),
        })

    result.sort(key=lambda x: x["datum"])
    return result


def get_exams_cached(user_id: int, server: str, school: str,
                     username: str, password: str,
                     start_date: datetime.date, end_date: datetime.date) -> tuple:
    """Gibt (exams_liste, warnung_oder_None) zurück."""
    cache_key = (user_id, "exams", start_date.isoformat(), end_date.isoformat())
    cached    = _cache.get(cache_key)
    if cached:
        age = (datetime.datetime.now() - cached["ts"]).total_seconds()
        if age < CACHE_TTL:
            return cached["exams"], None

    try:
        exams = fetch_exams(server, school, username, password, start_date, end_date)
        _cache[cache_key] = {"exams": exams, "ts": datetime.datetime.now()}
        return exams, None
    except WebUntisError as e:
        if cached:
            return cached["exams"], f"Aktualisierung fehlgeschlagen: {e}"
        return [], str(e)


def invalidate_exam_cache(user_id: int):
    for key in list(_cache.keys()):
        if key[0] == user_id and len(key) > 1 and key[1] == "exams":
            _cache.pop(key, None)
