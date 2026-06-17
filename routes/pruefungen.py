import re
import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, abort
from core import queries
from core.webuntis_client import invalidate_exam_cache
from core.exam_utils import load_webuntis_exams, load_manual_exams
from core.nav import NAV_ITEMS

bp = Blueprint("pruefungen", __name__)


def _current_user():
    return queries.get_user_by_id(session["user_id"])


def _can_add(user):
    return bool(user and (user["is_admin"] or user["role"] == "trusted"))


@bp.route("/pruefungen")
def index():
    today = datetime.date.today()
    user  = _current_user()
    wu_exams, warning, wt_configured = load_webuntis_exams(session["user_id"], today)
    manual_exams = load_manual_exams(today, user_id=session["user_id"])

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
        today_iso=today.isoformat(),
        is_admin=bool(user and user["is_admin"]),
        can_add=_can_add(user),
        klassen=queries.get_klassen() if user and user["is_admin"] else [],
    )


@bp.route("/pruefungen/aktualisieren", methods=["POST"])
def refresh():
    invalidate_exam_cache(session["user_id"])
    return redirect(url_for("pruefungen.index"))


@bp.route("/pruefungen/manuell/hinzufuegen", methods=["POST"])
def manuell_add():
    user = _current_user()
    if not _can_add(user):
        abort(403)

    fach  = request.form.get("fach", "").strip()
    datum = request.form.get("datum", "").strip()
    notiz = request.form.get("notiz", "").strip()
    art   = request.form.get("art", "Ex").strip()
    if art not in ("Ex", "SA"):
        art = "Ex"
    return_url = request.form.get("_return", url_for("pruefungen.index"))

    if fach and datum:
        if user["is_admin"]:
            # Admin kann Klasse explizit wählen; kein Eintrag = global (None)
            try:
                klasse_id = int(request.form.get("klasse_id")) if request.form.get("klasse_id") else None
            except (ValueError, TypeError):
                klasse_id = None
        else:
            klasse_id = user["klasse_id"]
        queries.add_pruefung(fach, art, datum, notiz, klasse_id=klasse_id)
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
    user = _current_user()
    if not _can_add(user):
        abort(403)
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
