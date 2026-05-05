import datetime

from flask import Blueprint, render_template, session, current_app, redirect, url_for, request
from core import queries
from core.encryption import decrypt
from core.webuntis_client import get_timetable_cached, invalidate_cache
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
            server_name=current_app.config["SERVER_NAME_DISPLAY"],
            configured=False,
        )

    monday = _parse_monday(request.args.get("woche"))
    prev_monday = monday - datetime.timedelta(weeks=1)
    next_monday = monday + datetime.timedelta(weeks=1)

    grid, monday, periods_info, warning = get_timetable_cached(
        session["user_id"],
        creds["server"],
        creds["school"],
        creds["wt_username"],
        decrypt(creds["wt_password"]),
        monday,
    )

    # Prüfungen dieser Woche aus der DB holen
    week_end = monday + datetime.timedelta(days=4)
    day_exams = {i: [] for i in range(5)}
    for row in queries.get_all_pruefungen():
        datum = datetime.date.fromisoformat(row["datum"])
        if monday <= datum <= week_end:
            day_idx = datum.weekday()
            if 0 <= day_idx <= 4:
                day_exams[day_idx].append(dict(row))

    # Fach-Matching: welche Stundenplan-Zelle hat eine passende Prüfung?
    # Abgleich case-insensitiv und bidirektional (Kurzname ↔ Langname).
    exam_cells = {}
    if grid:
        for stunde, days in grid.items():
            for day_idx, slot in days.items():
                if slot and not slot.get("cancelled") and day_exams.get(day_idx):
                    sf = (slot["fach"] or "").lower().strip()
                    for exam in day_exams[day_idx]:
                        ef = exam["fach"].lower().strip()
                        if ef and sf and (ef in sf or sf in ef):
                            exam_cells[(stunde, day_idx)] = exam
                            break

    return render_template(
        "mein_stundenplan.html",
        page_id="mein_stundenplan",
        nav=NAV_ITEMS,
        server_name=current_app.config["SERVER_NAME_DISPLAY"],
        configured=True,
        grid=grid,
        periods_info=periods_info,
        day_exams=day_exams,
        exam_cells=exam_cells,
        wochentage=WOCHENTAGE,
        monday=monday,
        prev_monday=prev_monday,
        next_monday=next_monday,
        fetch_error=warning if grid is None else None,
        fetch_warning=warning if grid is not None else None,
    )


@bp.route("/mein-stundenplan/aktualisieren", methods=["POST"])
def refresh():
    woche = request.form.get("woche")
    monday = _parse_monday(woche)
    invalidate_cache(session["user_id"], monday)
    if woche:
        return redirect(url_for("mein_stundenplan.index", woche=woche))
    return redirect(url_for("mein_stundenplan.index"))
