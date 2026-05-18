import datetime
from flask import Blueprint, render_template, current_app, session
from core import queries
from core.nav import NAV_ITEMS
from core.exam_utils import load_webuntis_exams, load_manual_exams
from core.encryption import decrypt
from core.webuntis_client import get_timetable_cached

bp = Blueprint("dashboard", __name__)

_WOCHENTAGE_LANG = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]


def _grade_color(avg):
    if avg is None: return "blue"
    if avg <= 2.0:  return "green"
    if avg <= 3.0:  return "blue"
    if avg <= 4.0:  return "orange"
    return "red"


def _load_today_timetable(user_id: int, today: datetime.date) -> tuple[list, str | None]:
    """Gibt (slots_heute, warnung) zurück. slots_heute = [{stunde, fach, lehrer, raum, start, end}]"""
    weekday = today.weekday()
    if weekday >= 5:
        return [], None

    creds = queries.get_webuntis_credentials(user_id)
    if not creds:
        return [], "not_configured"

    server, school = queries.get_webuntis_config()
    monday = today - datetime.timedelta(days=weekday)

    try:
        grid, _, periods_info, warning = get_timetable_cached(
            user_id, server, school,
            creds["wt_username"],
            decrypt(creds["wt_password"]),
            monday,
        )
    except Exception as e:
        return [], str(e)

    if not grid:
        return [], warning

    # periods_info ist 0-indiziert (Index = stunde-1)
    pi = {p["stunde"]: p for p in (periods_info or [])}

    slots = []
    for stunde in sorted(grid.keys()):
        slot = grid[stunde].get(weekday)
        if not slot or slot.get("cancelled") or not slot.get("fach"):
            continue
        p = pi.get(stunde, {})
        slots.append({
            "stunde": stunde,
            "fach":   slot["fach"],
            "lehrer": slot.get("lehrer") or "",
            "raum":   slot.get("raum") or "",
            "start":  p.get("start", ""),
            "end":    p.get("end", ""),
        })

    return slots, warning


@bp.route("/")
def index():
    user_id = session["user_id"]
    today   = datetime.date.today()

    # ── Noten ─────────────────────────────────────────────────────────────────
    all_noten    = list(queries.get_noten_for_user(user_id))
    recent_noten = sorted(all_noten, key=lambda n: n["datum"], reverse=True)[:5]

    gesamt_schnitt = None
    if all_noten:
        gesamt_schnitt = round(sum(n["note"] for n in all_noten) / len(all_noten), 2)

    # ── Prüfungen ──────────────────────────────────────────────────────────────
    wu_exams, _warn, _wt = load_webuntis_exams(user_id, today)
    manual_exams         = load_manual_exams(today)
    all_exams            = wu_exams + manual_exams

    upcoming      = sorted([e for e in all_exams if e["days"] >= 0], key=lambda e: e["datum"])
    past          = [e for e in all_exams if e["days"] < 0]
    next_exam     = upcoming[0] if upcoming else None
    next_5_exams  = upcoming[:5]

    graded_keys        = queries.get_graded_exam_keys_for_user(user_id)
    offene_bewertungen = sum(1 for e in past if e["exam_key"] not in graded_keys)

    week_start = today - datetime.timedelta(days=today.weekday())
    week_end   = week_start + datetime.timedelta(days=6)
    pruef_diese_woche = sum(1 for e in upcoming if week_start <= e["datum"] <= week_end)

    # ── Stundenplan heute (WebUntis) ───────────────────────────────────────────
    heute_slots, sp_warning = _load_today_timetable(user_id, today)
    heute_label = _WOCHENTAGE_LANG[today.weekday()]

    return render_template(
        "dashboard.html",
        page_id="dashboard",
        nav=NAV_ITEMS,
        today=today,
        gesamt_schnitt=gesamt_schnitt,
        note_color=_grade_color(gesamt_schnitt),
        next_exam=next_exam,
        next_5_exams=next_5_exams,
        pruef_diese_woche=pruef_diese_woche,
        offene_bewertungen=offene_bewertungen,
        recent_noten=recent_noten,
        heute_slots=heute_slots,
        heute_label=heute_label,
        is_weekend=(today.weekday() >= 5),
        sp_not_configured=(sp_warning == "not_configured"),
    )
