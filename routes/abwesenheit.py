import datetime
from collections import defaultdict
from flask import Blueprint, render_template, request, redirect, url_for, session
from core import queries
from core.encryption import decrypt
from core.webuntis_client import (get_absences_cached, invalidate_absence_cache,
                                  get_scheduled_hours_cached)
from core.nav import NAV_ITEMS

bp = Blueprint("abwesenheit", __name__)


def _schuljahr_range() -> tuple[datetime.date, datetime.date]:
    today = datetime.date.today()
    raw = queries.get_app_setting("schuljahr_beginn", "09-01")
    try:
        monat, tag = int(raw[:2]), int(raw[3:5])
    except (ValueError, IndexError):
        monat, tag = 9, 1
    started = today.month > monat or (today.month == monat and today.day >= tag)
    if started:
        return datetime.date(today.year, monat, tag), datetime.date(today.year + 1, 7, 31)
    return datetime.date(today.year - 1, monat, tag), datetime.date(today.year, 7, 31)


def _fmt_minutes(mins: int) -> str:
    if mins <= 0:
        return "–"
    h, m = divmod(mins, 60)
    if h and m:
        return f"{h} Std {m} Min"
    return f"{h} Std" if h else f"{m} Min"


def _bafog_color(pct: float) -> str:
    if pct >= 20:
        return "var(--red)"
    if pct >= 10:
        return "var(--orange)"
    return "var(--green)"


def _compute_bafog(absence_minutes: int, soll_until_today: int, soll_full_year: int):
    if soll_full_year <= 0:
        return None
    pct_now  = (absence_minutes / soll_until_today * 100) if soll_until_today > 0 else 0.0
    pct_year = absence_minutes / soll_full_year * 100
    return {
        "pct_now_str":  f"{pct_now:.1f} %",
        "pct_year_str": f"{pct_year:.1f} %",
        "bar_now":      round(min(pct_now  / 30, 1) * 100, 2),
        "bar_year":     round(min(pct_year / 30, 1) * 100, 2),
        "color_now":    _bafog_color(pct_now),
        "color_year":   _bafog_color(pct_year),
        "soll_now_str": _fmt_minutes(soll_until_today),
        "soll_year_str":_fmt_minutes(soll_full_year),
    }


def _compute_summary(absences: list) -> dict:
    total   = len(absences)
    excused = sum(1 for a in absences if a["is_excused"])
    total_minutes = sum(a["minutes"] for a in absences)

    by_reason: dict = defaultdict(lambda: {"count": 0, "minutes": 0})
    for a in absences:
        r = a["reason"]
        by_reason[r]["count"]   += 1
        by_reason[r]["minutes"] += a["minutes"]

    max_count = max((v["count"] for v in by_reason.values()), default=1)

    return {
        "total":         total,
        "excused":       excused,
        "unexcused":     total - excused,
        "total_minutes": total_minutes,
        "total_time":    _fmt_minutes(total_minutes),
        "by_reason":     sorted(by_reason.items(), key=lambda x: x[1]["count"], reverse=True),
        "max_count":     max_count,
    }


_WOCHENTAGE = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]


@bp.route("/abwesenheit")
def index():
    creds = queries.get_webuntis_credentials(session["user_id"])
    if not creds:
        return render_template("abwesenheit.html", page_id="abwesenheit",
                               nav=NAV_ITEMS, configured=False)

    start, end = _schuljahr_range()
    server, school = queries.get_webuntis_config()

    pw = decrypt(creds["wt_password"])

    absences, warning = get_absences_cached(
        session["user_id"], server, school,
        creds["wt_username"], pw,
        start, end,
    )

    for a in absences:
        a["wochentag"] = _WOCHENTAGE[a["datum"].weekday()]

    summary = _compute_summary(absences)

    soll_now, soll_year, sched_warn = get_scheduled_hours_cached(
        session["user_id"], server, school,
        creds["wt_username"], pw,
        start, end,
    )
    bafog = _compute_bafog(summary["total_minutes"], soll_now, soll_year)

    return render_template(
        "abwesenheit.html",
        page_id="abwesenheit",
        nav=NAV_ITEMS,
        configured=True,
        absences=absences,
        summary=summary,
        bafog=bafog,
        schuljahr_start=start,
        schuljahr_end=end,
        warning=warning,
        error=warning if not absences and warning else None,
        fmt_minutes=_fmt_minutes,
    )


@bp.route("/abwesenheit/aktualisieren", methods=["POST"])
def refresh():
    invalidate_absence_cache(session["user_id"])
    return redirect(url_for("abwesenheit.index"))
