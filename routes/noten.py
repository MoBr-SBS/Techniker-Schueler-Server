import datetime
from flask import Blueprint, render_template, request, redirect, url_for, current_app
from core import queries
from core.nav import NAV_ITEMS

bp = Blueprint("noten", __name__)


def _grade_color(avg):
    if avg <= 2.0: return "green"
    if avg <= 3.0: return "blue"
    if avg <= 4.0: return "orange"
    return "red"


@bp.route("/noten")
def index():
    subjects = {}
    for row in queries.get_all_noten():
        f = row["fach"]
        if f not in subjects:
            subjects[f] = []
        subjects[f].append(dict(row))

    summaries = []
    for fach, noten_list in subjects.items():
        avg = round(sum(n["note"] for n in noten_list) / len(noten_list), 2)
        summaries.append({
            "fach":    fach,
            "noten":   noten_list,
            "schnitt": avg,
            "color":   _grade_color(avg),
            "count":   len(noten_list),
        })
    summaries.sort(key=lambda x: x["fach"])

    return render_template(
        "noten.html",
        page_id="noten",
        nav=NAV_ITEMS,
        server_name=current_app.config["SERVER_NAME_DISPLAY"],
        summaries=summaries,
        today=datetime.date.today().isoformat(),
    )


@bp.route("/noten/add", methods=["POST"])
def add():
    fach         = request.form["fach"].strip()
    datum        = request.form["datum"]
    beschreibung = request.form.get("beschreibung", "").strip()
    try:
        note = float(request.form["note"].replace(",", "."))
        if not (1.0 <= note <= 6.0):
            raise ValueError
    except (ValueError, KeyError):
        return redirect(url_for("noten.index"))
    if fach and datum:
        queries.add_note(fach, note, datum, beschreibung)
    return redirect(url_for("noten.index"))


@bp.route("/noten/delete/<int:note_id>", methods=["POST"])
def delete(note_id):
    queries.delete_note(note_id)
    return redirect(url_for("noten.index"))
