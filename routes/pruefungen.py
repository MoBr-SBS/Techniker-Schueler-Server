import datetime
from flask import Blueprint, render_template, request, redirect, url_for, current_app
from core import queries
from core.nav import NAV_ITEMS

bp = Blueprint("pruefungen", __name__)

_WOCHENTAGE = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
_MONATE_DE  = ["", "Januar", "Februar", "März", "April", "Mai", "Juni",
               "Juli", "August", "September", "Oktober", "November", "Dezember"]


@bp.route("/pruefungen")
def index():
    today    = datetime.date.today()
    upcoming = []
    past     = []
    for row in queries.get_all_pruefungen():
        d     = dict(row)
        datum = datetime.date.fromisoformat(d["datum"])
        d["days"]      = (datum - today).days
        d["wochentag"] = _WOCHENTAGE[datum.weekday()]
        d["heute"]     = datum == today
        (upcoming if d["days"] >= 0 else past).append(d)
    past.reverse()
    return render_template(
        "pruefungen.html",
        page_id="pruefungen",
        nav=NAV_ITEMS,
        server_name=current_app.config["SERVER_NAME_DISPLAY"],
        upcoming=upcoming,
        past=past,
    )


@bp.route("/pruefungen/add", methods=["POST"])
def add():
    fach  = request.form.get("fach", "").strip()
    art   = request.form.get("art", "")
    datum = request.form.get("datum", "")
    if fach and art in ("Schulaufgabe", "Ex") and datum:
        queries.add_pruefung(fach, art, datum)
    return redirect(url_for("pruefungen.index"))


@bp.route("/pruefungen/<int:pruefung_id>/delete", methods=["POST"])
def delete(pruefung_id):
    queries.delete_pruefung(pruefung_id)
    return redirect(url_for("pruefungen.index"))
