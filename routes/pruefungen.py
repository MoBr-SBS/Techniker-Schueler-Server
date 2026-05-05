import re
import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session
from core import queries
from core.encryption import decrypt
from core.webuntis_client import get_exams_cached, invalidate_exam_cache
from core.nav import NAV_ITEMS

bp = Blueprint("pruefungen", __name__)

_WOCHENTAGE   = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
_RANGE_PAST   = 60
_RANGE_FUTURE = 180


def _load_webuntis_exams(user_id, today):
    creds = queries.get_webuntis_credentials(user_id)
    if not creds:
        return [], None, False

    start  = today - datetime.timedelta(days=_RANGE_PAST)
    end    = today + datetime.timedelta(days=_RANGE_FUTURE)
    server, school = queries.get_webuntis_config()

    exams, warning = get_exams_cached(
        user_id, server, school,
        creds["wt_username"],
        decrypt(creds["wt_password"]),
        start, end,
    )

    noted_keys = queries.get_exam_note_keys()
    result = []
    for exam in exams:
        days = (exam["datum"] - today).days
        e = dict(exam)
        e["days"]      = days
        e["wochentag"] = _WOCHENTAGE[exam["datum"].weekday()]
        e["heute"]     = exam["datum"] == today
        e["exam_key"]  = queries.make_exam_key(exam["fach"], exam["datum"])
        e["has_note"]  = e["exam_key"] in noted_keys
        e["source"]    = "webuntis"
        result.append(e)

    return result, warning, True


def _load_manual_exams(today):
    noted_keys = queries.get_exam_note_keys()
    result = []
    for row in queries.get_all_pruefungen():
        datum = datetime.date.fromisoformat(row["datum"])
        days  = (datum - today).days
        exam_key = queries.make_exam_key(row["fach"], datum)
        result.append({
            "id":        row["id"],
            "fach":      row["fach"],
            "art":       row["art"],
            "datum":     datum,
            "notiz":     row["notiz"] or "",
            "days":      days,
            "wochentag": _WOCHENTAGE[datum.weekday()],
            "heute":     datum == today,
            "exam_key":  exam_key,
            "has_note":  exam_key in noted_keys,
            "source":    "manual",
        })
    return result


@bp.route("/pruefungen")
def index():
    today = datetime.date.today()
    wu_exams, warning, wt_configured = _load_webuntis_exams(session["user_id"], today)
    manual_exams = _load_manual_exams(today)

    all_exams = wu_exams + manual_exams
    all_exams.sort(key=lambda e: e["datum"])

    upcoming = [e for e in all_exams if e["days"] >= 0]
    past     = [e for e in all_exams if e["days"] < 0]
    past.reverse()

    return render_template(
        "pruefungen.html",
        page_id="pruefungen",
        nav=NAV_ITEMS,
        wt_configured=wt_configured,
        upcoming=upcoming,
        past=past,
        warning=warning,
        wt_error=warning if wt_configured and not wu_exams and warning else None,
    )


@bp.route("/pruefungen/aktualisieren", methods=["POST"])
def refresh():
    invalidate_exam_cache(session["user_id"])
    return redirect(url_for("pruefungen.index"))


@bp.route("/pruefungen/manuell/hinzufuegen", methods=["POST"])
def manuell_add():
    fach  = request.form.get("fach", "").strip()
    datum = request.form.get("datum", "").strip()
    notiz = request.form.get("notiz", "").strip()
    return_url = request.form.get("_return", url_for("pruefungen.index"))

    if fach and datum:
        queries.add_pruefung(fach, "Ex", datum, notiz)
    return redirect(return_url)


@bp.route("/pruefungen/manuell/<int:pruefung_id>/notiz", methods=["POST"])
def manuell_notiz(pruefung_id):
    notiz = request.form.get("notiz", "").strip()
    row = queries.get_pruefung(pruefung_id)
    if row:
        queries.update_pruefung(pruefung_id, row["fach"], row["art"], row["datum"], notiz)
    return redirect(url_for("pruefungen.index"))


@bp.route("/pruefungen/manuell/<int:pruefung_id>/loeschen", methods=["POST"])
def manuell_delete(pruefung_id):
    queries.delete_pruefung(pruefung_id)
    return_url = request.form.get("_return", url_for("pruefungen.index"))
    return redirect(return_url)


@bp.route("/pruefungen/notiz/<exam_key>")
def notiz(exam_key):
    if not re.match(r"^[A-Za-z0-9_]+$", exam_key):
        return redirect(url_for("pruefungen.index"))

    note = queries.get_exam_note(exam_key)
    edit = request.args.get("edit") == "1"

    fach      = request.args.get("fach", exam_key.rsplit("_", 1)[0].replace("_", " "))
    name      = request.args.get("name", "")
    art       = request.args.get("art", "")
    datum_str = request.args.get("datum", "")

    return render_template(
        "pruefung_notiz.html",
        page_id="pruefungen",
        nav=NAV_ITEMS,
        exam_key=exam_key,
        note=note,
        edit=edit,
        fach=fach,
        name=name,
        art=art,
        datum_str=datum_str,
    )


@bp.route("/pruefungen/notiz/<exam_key>/speichern", methods=["POST"])
def notiz_speichern(exam_key):
    if not re.match(r"^[A-Za-z0-9_]+$", exam_key):
        return redirect(url_for("pruefungen.index"))

    content = request.form.get("content", "").strip()
    queries.save_exam_note(exam_key, content, session["username"])

    return redirect(url_for(
        "pruefungen.notiz",
        exam_key=exam_key,
        fach=request.form.get("fach", ""),
        name=request.form.get("name", ""),
        art=request.form.get("art", ""),
        datum_str=request.form.get("datum_str", ""),
    ))
