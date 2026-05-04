from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash
from core import queries

bp = Blueprint("admin", __name__)


def _require_admin():
    if not session.get("is_admin"):
        return redirect(url_for("dashboard.index"))
    return None


@bp.route("/admin/benutzer")
def benutzer():
    guard = _require_admin()
    if guard:
        return guard
    return render_template(
        "benutzer.html",
        page_id="benutzer",
        users=queries.get_all_users(),
        admin_count=queries.count_admins(),
    )


@bp.route("/admin/benutzer/add", methods=["POST"])
def add_benutzer():
    guard = _require_admin()
    if guard:
        return guard
    username = request.form["username"].strip()
    password = request.form["password"]
    is_admin = 1 if request.form.get("is_admin") else 0

    if not username:
        flash("Benutzername darf nicht leer sein.", "error")
    elif len(password) < 6:
        flash("Passwort muss mindestens 6 Zeichen haben.", "error")
    elif queries.user_exists(username):
        flash(f'Benutzername "{username}" ist bereits vergeben.', "error")
    else:
        queries.add_user(username, generate_password_hash(password), is_admin)
        flash(f'Benutzer "{username}" wurde angelegt.', "success")
    return redirect(url_for("admin.benutzer"))


@bp.route("/admin/benutzer/delete/<int:user_id>", methods=["POST"])
def delete_benutzer(user_id):
    guard = _require_admin()
    if guard:
        return guard
    if user_id == session["user_id"]:
        flash("Du kannst dein eigenes Konto nicht löschen.", "error")
        return redirect(url_for("admin.benutzer"))
    user = queries.get_user_by_id(user_id)
    if user and user["is_admin"] and queries.count_admins() <= 1:
        flash("Der letzte Administrator kann nicht gelöscht werden.", "error")
        return redirect(url_for("admin.benutzer"))
    queries.delete_user(user_id)
    flash("Benutzer wurde gelöscht.", "success")
    return redirect(url_for("admin.benutzer"))
