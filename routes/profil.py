from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash, generate_password_hash
from core import queries
from core.encryption import encrypt
from core.webuntis_client import fetch_timetable, WebUntisError, invalidate_cache

bp = Blueprint("profil", __name__)


@bp.route("/profil")
def index():
    creds = queries.get_webuntis_credentials(session["user_id"])
    return render_template("profil.html", page_id="profil", creds=creds)


@bp.route("/profil/passwort", methods=["POST"])
def change_password():
    current_pw = request.form["current_password"]
    new_pw     = request.form["new_password"]
    new_pw2    = request.form["new_password2"]
    user       = queries.get_user_by_id(session["user_id"])

    if not check_password_hash(user["password_hash"], current_pw):
        flash("Das aktuelle Passwort ist falsch.", "error")
    elif new_pw != new_pw2:
        flash("Die neuen Passwörter stimmen nicht überein.", "error")
    elif len(new_pw) < 6:
        flash("Das neue Passwort muss mindestens 6 Zeichen lang sein.", "error")
    else:
        queries.update_password(session["user_id"], generate_password_hash(new_pw))
        flash("Passwort erfolgreich geändert.", "success")
    return redirect(url_for("profil.index"))


@bp.route("/profil/webuntis/speichern", methods=["POST"])
def save_webuntis():
    server    = request.form["server"].strip().rstrip("/")
    school    = request.form["school"].strip()
    wt_user   = request.form["wt_username"].strip()
    wt_pass   = request.form["wt_password"]
    confirmed = request.form.get("hinweis_bestaetigt")

    if not confirmed:
        flash("Bitte bestätige den Sicherheitshinweis.", "error")
        return redirect(url_for("profil.index"))
    if not all([server, school, wt_user, wt_pass]):
        flash("Alle Felder sind Pflicht.", "error")
        return redirect(url_for("profil.index"))

    try:
        fetch_timetable(server, school, wt_user, wt_pass)
    except WebUntisError as e:
        flash(f"Verbindung fehlgeschlagen: {e}", "error")
        return redirect(url_for("profil.index"))

    queries.save_webuntis_credentials(
        session["user_id"], server, school, wt_user, encrypt(wt_pass)
    )
    invalidate_cache(session["user_id"])
    flash("WebUntis-Zugangsdaten gespeichert. Verbindung erfolgreich getestet.", "success")
    return redirect(url_for("profil.index"))


@bp.route("/profil/webuntis/loeschen", methods=["POST"])
def delete_webuntis():
    queries.delete_webuntis_credentials(session["user_id"])
    invalidate_cache(session["user_id"])
    flash("WebUntis-Zugangsdaten gelöscht.", "success")
    return redirect(url_for("profil.index"))
