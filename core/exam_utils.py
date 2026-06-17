"""
core/exam_utils.py – Gemeinsame Hilfsfunktionen zum Laden von Prüfungen.
Wird von routes/pruefungen.py und routes/noten.py genutzt.
"""

import datetime
from flask import session
from core import queries
from core.encryption import decrypt_with_key
from core.webuntis_client import get_exams_cached

_WOCHENTAGE = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
_RANGE_FUTURE = 180


def _schuljahr_beginn(today: datetime.date) -> datetime.date:
    raw = queries.get_app_setting("schuljahr_beginn", "09-01")
    try:
        monat, tag = int(raw[:2]), int(raw[3:5])
    except (ValueError, IndexError):
        monat, tag = 9, 1
    started = today.month > monat or (today.month == monat and today.day >= tag)
    year = today.year if started else today.year - 1
    return datetime.date(year, monat, tag)


def load_webuntis_exams(user_id, today):
    creds = queries.get_webuntis_credentials(user_id)
    if not creds:
        return [], None, False

    start = _schuljahr_beginn(today)
    end = today + datetime.timedelta(days=_RANGE_FUTURE)
    server, school = queries.get_webuntis_config()

    exams, warning = get_exams_cached(
        user_id, server, school,
        creds["wt_username"],
        decrypt_with_key(creds["wt_password"], session.get("wt_key", "").encode()),
        start, end,
    )

    noted_keys = queries.get_exam_note_keys()
    result = []
    for exam in exams:
        days = (exam["datum"] - today).days
        e = dict(exam)
        e["days"] = days
        e["wochentag"] = _WOCHENTAGE[exam["datum"].weekday()]
        e["heute"] = exam["datum"] == today
        e["exam_key"] = queries.make_exam_key(exam["fach"], exam["datum"])
        e["has_note"] = e["exam_key"] in noted_keys
        e["source"] = "webuntis"
        result.append(e)

    return result, warning, True


def load_manual_exams(today, user_id=None):
    klasse_id = None
    if user_id is not None:
        user = queries.get_user_by_id(user_id)
        if user:
            klasse_id = user["klasse_id"]

    noted_keys = queries.get_exam_note_keys()
    result = []
    for row in queries.get_all_pruefungen(klasse_id=klasse_id):
        datum = datetime.date.fromisoformat(row["datum"])
        days = (datum - today).days
        exam_key = queries.make_exam_key(row["fach"], datum)
        result.append({
            "id": row["id"],
            "fach": row["fach"],
            "art": row["art"],
            "datum": datum,
            "notiz": row["notiz"] or "",
            "days": days,
            "wochentag": _WOCHENTAGE[datum.weekday()],
            "heute": datum == today,
            "exam_key": exam_key,
            "has_note": exam_key in noted_keys,
            "source": "manual",
        })
    return result
