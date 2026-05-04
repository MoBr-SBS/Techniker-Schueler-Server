import datetime
from flask import Blueprint, render_template, request, redirect, url_for, current_app
from core import queries
from core.nav import NAV_ITEMS

bp = Blueprint("tests", __name__)


@bp.route("/tests")
def index():
    today = datetime.date.today()
    upcoming, past = [], []
    for row in queries.get_all_tests():
        d = dict(row)
        d["days"] = (datetime.date.fromisoformat(d["datum"]) - today).days
        (upcoming if d["days"] >= 0 else past).append(d)
    past.reverse()
    return render_template(
        "tests.html",
        page_id="tests",
        nav=NAV_ITEMS,
        server_name=current_app.config["SERVER_NAME_DISPLAY"],
        upcoming=upcoming,
        past=past,
    )


@bp.route("/tests/add", methods=["POST"])
def add():
    fach         = request.form["fach"].strip()
    datum        = request.form["datum"]
    beschreibung = request.form.get("beschreibung", "").strip()
    if fach and datum:
        queries.add_test(fach, datum, beschreibung)
    return redirect(url_for("tests.index"))


@bp.route("/tests/<int:test_id>")
def detail(test_id):
    row = queries.get_test(test_id)
    if not row:
        return redirect(url_for("tests.index"))
    test = dict(row)
    test["days"] = (datetime.date.fromisoformat(test["datum"]) - datetime.date.today()).days
    return render_template(
        "test_detail.html",
        page_id="tests",
        nav=NAV_ITEMS,
        server_name=current_app.config["SERVER_NAME_DISPLAY"],
        test=test,
        material=queries.get_lernmaterial(test_id),
    )


@bp.route("/tests/<int:test_id>/material/add", methods=["POST"])
def add_material(test_id):
    inhalt = request.form["inhalt"].strip()
    if inhalt:
        queries.add_lernmaterial(test_id, inhalt)
    return redirect(url_for("tests.detail", test_id=test_id))


@bp.route("/tests/<int:test_id>/material/delete/<int:mid>", methods=["POST"])
def delete_material(test_id, mid):
    queries.delete_lernmaterial(test_id, mid)
    return redirect(url_for("tests.detail", test_id=test_id))


@bp.route("/tests/<int:test_id>/delete", methods=["POST"])
def delete(test_id):
    queries.delete_test(test_id)
    return redirect(url_for("tests.index"))
