from flask import Blueprint, render_template, request, redirect, url_for, current_app
from core import queries
from core.nav import NAV_ITEMS

bp = Blueprint("stundenplan", __name__)

WOCHENTAGE = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag"]
STUNDEN = list(range(1, 9))


@bp.route("/stundenplan")
def index():
    rows = queries.get_stundenplan()
    grid = {s: {d: None for d in range(5)} for s in STUNDEN}
    for row in rows:
        grid[row["stunde"]][row["wochentag"]] = row
    return render_template(
        "stundenplan.html",
        page_id="stundenplan",
        nav=NAV_ITEMS,
        server_name=current_app.config["SERVER_NAME_DISPLAY"],
        grid=grid,
        stunden=STUNDEN,
        wochentage=WOCHENTAGE,
    )


@bp.route("/stundenplan/add", methods=["POST"])
def add():
    wochentag = int(request.form["wochentag"])
    stunde    = int(request.form["stunde"])
    fach      = request.form["fach"].strip()
    lehrer    = request.form.get("lehrer", "").strip()
    raum      = request.form.get("raum", "").strip()
    if fach and 0 <= wochentag <= 4 and 1 <= stunde <= 8:
        queries.set_stundenplan_slot(wochentag, stunde, fach, lehrer, raum)
    return redirect(url_for("stundenplan.index"))


@bp.route("/stundenplan/delete/<int:slot_id>", methods=["POST"])
def delete(slot_id):
    queries.delete_stundenplan_slot(slot_id)
    return redirect(url_for("stundenplan.index"))
