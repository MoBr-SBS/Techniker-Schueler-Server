import datetime
import threading

from flask import (
    Blueprint, render_template, request, redirect, url_for,
    session, current_app, flash,
)
from werkzeug.security import check_password_hash, generate_password_hash
from core import queries, webuntis_client
from core.encryption import derive_key, encrypt_with_key, decrypt_with_key, legacy_decrypt

bp = Blueprint("auth", __name__)


def _prefetch_webuntis(app, user_id: int, wt_key: bytes):
    """Wärmt den WebUntis-Cache nach dem Login im Hintergrund auf."""
    with app.app_context():
        try:
            creds = queries.get_webuntis_credentials(user_id)
            if not creds:
                return
            server, school = queries.get_webuntis_config()
            if not server or not school:
                return
            password = decrypt_with_key(creds["wt_password"], wt_key)
            username = creds["wt_username"]
            today    = datetime.date.today()
            monday   = today - datetime.timedelta(days=today.weekday())
            webuntis_client.get_timetable_cached(
                user_id, server, school, username, password, monday)
            webuntis_client.get_exams_cached(
                user_id, server, school, username, password,
                today, today + datetime.timedelta(days=180))
        except Exception:
            pass


def _reencrypt_credentials(user_id: int, new_key: bytes):
    """Verschlüsselt gespeicherte WebUntis-Credentials mit neuem Key (nach Passwort-Änderung)."""
    creds = queries.get_webuntis_credentials(user_id)
    if not creds:
        return
    old_key_str = session.get("wt_key", "")
    if not old_key_str:
        return
    try:
        plaintext = decrypt_with_key(creds["wt_password"], old_key_str.encode())
        new_encrypted = encrypt_with_key(plaintext, new_key)
        queries.save_webuntis_credentials(user_id, creds["wt_username"], new_encrypted, uses_user_key=True)
    except Exception:
        queries.delete_webuntis_credentials(user_id)
        flash("WebUntis-Zugangsdaten konnten nicht migriert werden und wurden gelöscht. Bitte erneut eingeben.", "warning")


def _migrate_credentials(user_id: int, wt_key: bytes):
    """Migriert alte FERNET_KEY-verschlüsselte Credentials auf nutzerspezifischen Key."""
    creds = queries.get_webuntis_credentials(user_id)
    if not creds or creds["uses_user_key"]:
        return
    try:
        plaintext = legacy_decrypt(creds["wt_password"])
        new_encrypted = encrypt_with_key(plaintext, wt_key)
        queries.save_webuntis_credentials(user_id, creds["wt_username"], new_encrypted, uses_user_key=True)
    except Exception:
        pass


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
            session["lang"]     = user["language"] or None
            # Nutzerspezifischen Verschlüsselungs-Key aus Passwort ableiten
            salt   = queries.get_or_create_wt_salt(user["id"])
            wt_key = derive_key(password, salt)
            session["wt_key"] = wt_key.decode()
            _migrate_credentials(user["id"], wt_key)
            threading.Thread(
                target=_prefetch_webuntis,
                args=(current_app._get_current_object(), user["id"], wt_key),
                daemon=True,
            ).start()
            if not user["is_admin"] and not queries.get_webuntis_credentials(user["id"]):
                return redirect(url_for("auth.webuntis_setup"))
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
            salt    = queries.get_or_create_wt_salt(session["user_id"])
            new_key = derive_key(new_pw, salt)
            _reencrypt_credentials(session["user_id"], new_key)
            queries.update_password(session["user_id"], generate_password_hash(new_pw))
            session["wt_key"] = new_key.decode()
            success = "Passwort erfolgreich geändert."
    return render_template("change_password.html", page_id=None, error=error, success=success)


@bp.route("/login/webuntis", methods=["GET", "POST"])
def webuntis_setup():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    if session.get("is_admin") or queries.get_webuntis_credentials(session["user_id"]):
        return redirect(url_for("dashboard.index"))

    from core.webuntis_client import fetch_timetable, WebUntisError
    from core.encryption import encrypt_with_key

    error = None
    if request.method == "POST":
        wt_user = request.form.get("wt_username", "").strip()
        wt_pass = request.form.get("wt_password", "")
        confirmed = request.form.get("hinweis_bestaetigt")

        server, school = queries.get_webuntis_config()
        if not server or not school:
            error = "WebUntis ist noch nicht vom Administrator konfiguriert. Bitte wende dich an den Administrator."
        elif not confirmed:
            error = "Bitte bestätige den Sicherheitshinweis."
        elif not wt_user or not wt_pass:
            error = "Bitte fülle alle Felder aus."
        else:
            try:
                grid, _, _, klasse_id, klasse_name = fetch_timetable(server, school, wt_user, wt_pass)
                wt_key = session.get("wt_key", "").encode()
                queries.save_webuntis_credentials(
                    session["user_id"], wt_user,
                    encrypt_with_key(wt_pass, wt_key),
                    uses_user_key=True,
                )
                if klasse_id:
                    queries.update_user_klasse(session["user_id"], klasse_id, klasse_name)
                    if grid:
                        faecher = {
                            slot["fach_kurz"]
                            for slots in grid.values()
                            for slot in slots.values()
                            if slot and slot.get("fach_kurz")
                        }
                        queries.set_klasse_faecher(klasse_id, faecher)
                return redirect(url_for("dashboard.index"))
            except WebUntisError as e:
                error = f"Verbindung fehlgeschlagen: {e}"

    server_name, logo_url, favicon_url = _branding()
    return render_template(
        "webuntis_setup.html",
        server_name=server_name,
        logo_url=logo_url,
        favicon_url=favicon_url,
        error=error,
    )
