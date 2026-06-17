import datetime

from flask import Blueprint, render_template, session, current_app, redirect, url_for, request
from core import queries
from core.encryption import decrypt_with_key
from core.webuntis_client import get_timetable_cached, get_exams_cached, get_absences_cached, invalidate_cache, invalidate_exam_cache
from core.nav import NAV_ITEMS

bp = Blueprint("mein_stundenplan", __name__)

WOCHENTAGE = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag"]


def _parse_monday(woche_str: str | None) -> datetime.date:
    today = datetime.date.today()
    monday = today - datetime.timedelta(days=today.weekday())
    if woche_str:
        try:
            d = datetime.date.fromisoformat(woche_str)
            monday = d - datetime.timedelta(days=d.weekday())
        except ValueError:
            pass
    return monday


@bp.route("/mein-stundenplan")
def index():
    creds = queries.get_webuntis_credentials(session["user_id"])

    if not creds:
        return render_template(
            "mein_stundenplan.html",
            page_id="mein_stundenplan",
            nav=NAV_ITEMS,
            configured=False,
        )

    monday = _parse_monday(request.args.get("woche"))
    prev_monday = monday - datetime.timedelta(weeks=1)
    next_monday = monday + datetime.timedelta(weeks=1)

    server, school = queries.get_webuntis_config()
    wu_user = creds["wt_username"]
    wu_pass = decrypt_with_key(creds["wt_password"], session.get("wt_key", "").encode())

    grid, monday, periods_info, warning = get_timetable_cached(
        session["user_id"],
        server, school, wu_user, wu_pass,
        monday,
    )

    week_end  = monday + datetime.timedelta(days=4)
    day_exams = {i: [] for i in range(5)}

    week_exams, _ = get_exams_cached(
        session["user_id"],
        server, school, wu_user, wu_pass,
        monday, week_end,
    )
    noted_keys = queries.get_exam_note_keys()
    for exam in week_exams:
        day_idx = exam["datum"].weekday()
        if 0 <= day_idx <= 4:
            exam = dict(exam)
            exam["exam_key"]  = queries.make_exam_key(exam["fach"], exam["datum"])
            exam["has_note"]  = exam["exam_key"] in noted_keys
            exam["datum_str"] = exam["datum"].strftime("%d.%m.%Y")
            exam["source"]    = "webuntis"
            day_exams[day_idx].append(exam)

    # Fach-Matching über Kurznamen (beide kommen jetzt aus WebUntis).
    exam_cells = {}
    if grid:
        for stunde, days in grid.items():
            for day_idx, slot in days.items():
                if slot and not slot.get("cancelled") and day_exams.get(day_idx):
                    sf = (slot.get("fach_kurz") or slot["fach"] or "").lower().strip()
                    for exam in day_exams[day_idx]:
                        ef = exam["fach"].lower().strip()
                        if ef and sf and (ef in sf or sf in ef):
                            exam_cells[(stunde, day_idx)] = exam
                            break

    # Manuelle Prüfungen für diese Woche laden
    week_end_date = monday + datetime.timedelta(days=4)
    manual_exam_cells = {}
    for row in queries.get_pruefungen_for_week(monday, week_end_date):
        datum   = datetime.date.fromisoformat(row["datum"])
        day_idx = (datum - monday).days
        if 0 <= day_idx <= 4 and grid:
            exam_key = queries.make_exam_key(row["fach"], datum)
            has_note = exam_key in noted_keys
            manual_exam = {
                "id":       row["id"],
                "fach":     row["fach"],
                "art":      row["art"],
                "datum":    datum,
                "datum_str": datum.strftime("%d.%m.%Y"),
                "notiz":    row["notiz"] or "",
                "exam_key": exam_key,
                "has_note": has_note,
                "name":     "",
                "source":   "manual",
            }
            key = row["fach"].lower() + "_" + str(day_idx)
            manual_exam_cells[key] = manual_exam
            day_exams[day_idx].append(manual_exam)

    # Abwesenheiten für die Woche laden und auf Zellen mappen
    week_absences, _ = get_absences_cached(
        session["user_id"],
        server, school, wu_user, wu_pass,
        monday, week_end,
    )
    absence_cells = {}
    for absence in week_absences:
        if not absence["start_time"] or not absence["end_time"]:
            continue
        day_idx = (absence["datum"] - monday).days
        if not (0 <= day_idx <= 4):
            continue
        for p in periods_info:
            if absence["start_time"] < p["end"] and absence["end_time"] > p["start"]:
                key = (p["stunde"], day_idx)
                if key not in absence_cells:
                    absence_cells[key] = absence

    today = datetime.date.today()
    now_time_str = datetime.datetime.now().strftime("%H:%M")
    is_xhr = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    template = "mein_stundenplan_partial.html" if is_xhr else "mein_stundenplan.html"

    return render_template(
        template,
        page_id="mein_stundenplan",
        nav=NAV_ITEMS,
        configured=True,
        grid=grid,
        periods_info=periods_info,
        day_exams=day_exams,
        exam_cells=exam_cells,
        manual_exam_cells=manual_exam_cells,
        absence_cells=absence_cells,
        wochentage=WOCHENTAGE,
        monday=monday,
        prev_monday=prev_monday,
        next_monday=next_monday,
        today=today,
        now_time_str=now_time_str,
        fetch_error=warning if grid is None else None,
        fetch_warning=warning if grid is not None else None,
    )


@bp.route("/mein-stundenplan/aktualisieren", methods=["POST"])
def refresh():
    woche = request.form.get("woche")
    # Alle gecachten Wochen + Prüfungen löschen (nicht nur die aktuelle)
    invalidate_cache(session["user_id"])
    invalidate_exam_cache(session["user_id"])
    if woche:
        return redirect(url_for("mein_stundenplan.index", woche=woche))
    return redirect(url_for("mein_stundenplan.index"))
