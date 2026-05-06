from flask import (
    Blueprint, render_template, request, redirect, url_for,
    session, current_app, flash,
)
from werkzeug.security import check_password_hash, generate_password_hash
from core import queries

bp = Blueprint("auth", __name__)


def _branding():
    db_name = queries.get_app_setting("server_name")
    server_name = db_name if db_name else current_app.config["SERVER_NAME_DISPLAY"]
    logo_file = queries.get_app_setting("logo_filename")
    logo_url  = url_for("static", filename=f"uploads/{logo_file}") if logo_file else None
    fav_file  = queries.get_app_setting("favicon_filename")
    favicon_url = url_for("static", filename=f"uploads/{fav_file}") if fav_file else None
    return server_name, logo_url, favicon_url


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
    server_name, logo_url, favicon_url = _branding()
    return render_template(
        "login.html",
        server_name=server_name,
        logo_url=logo_url,
        favicon_url=favicon_url,
        allow_registration=queries.get_app_setting("allow_registration") == "1",
        error=error,
    )


@bp.route("/register", methods=["GET", "POST"])
def register():
    if queries.get_app_setting("allow_registration") != "1":
        return redirect(url_for("auth.login"))
    error = None
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        password2 = request.form["password2"]
        if not username:
            error = "Benutzername darf nicht leer sein."
        elif len(password) < 6:
            error = "Passwort muss mindestens 6 Zeichen haben."
        elif password != password2:
            error = "Passwörter stimmen nicht überein."
        elif queries.user_exists(username):
            error = f'Benutzername "{username}" ist bereits vergeben.'
        else:
            queries.add_user(username, generate_password_hash(password), 0)
            flash("Konto erstellt – du kannst dich jetzt anmelden.", "success")
            return redirect(url_for("auth.login"))
    server_name, logo_url, favicon_url = _branding()
    return render_template(
        "register.html",
        server_name=server_name,
        logo_url=logo_url,
        favicon_url=favicon_url,
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
