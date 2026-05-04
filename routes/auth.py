from flask import (
    Blueprint, render_template, request, redirect, url_for,
    session, current_app,
)
from werkzeug.security import check_password_hash, generate_password_hash
from core import queries

bp = Blueprint("auth", __name__)


@bp.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        user = queries.get_user_by_username(username)
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"]  = user["id"]
            session["username"] = user["username"]
            session["is_admin"] = bool(user["is_admin"])
            return redirect(url_for("dashboard.index"))
        error = "Ungültiger Benutzername oder Passwort."
    return render_template(
        "login.html",
        server_name=current_app.config["SERVER_NAME_DISPLAY"],
        error=error,
    )


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))


@bp.route("/passwort", methods=["GET", "POST"])
def change_password():
    error   = None
    success = None
    if request.method == "POST":
        current_pw = request.form["current_password"]
        new_pw     = request.form["new_password"]
        new_pw2    = request.form["new_password2"]
        user = queries.get_user_by_id(session["user_id"])
        if not check_password_hash(user["password_hash"], current_pw):
            error = "Das aktuelle Passwort ist falsch."
        elif new_pw != new_pw2:
            error = "Die neuen Passwörter stimmen nicht überein."
        elif len(new_pw) < 6:
            error = "Das neue Passwort muss mindestens 6 Zeichen lang sein."
        else:
            queries.update_password(session["user_id"], generate_password_hash(new_pw))
            success = "Passwort erfolgreich geändert."
    return render_template("change_password.html", page_id=None, error=error, success=success)
