from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from core.i18n import t as _t
from werkzeug.security import check_password_hash, generate_password_hash
from core import queries
from core.encryption import derive_key, encrypt_with_key, decrypt_with_key
from core.webuntis_client import fetch_timetable, WebUntisError, invalidate_cache

bp = Blueprint("profil", __name__)


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


@bp.route("/profil")
def index():
    creds = queries.get_webuntis_credentials(session["user_id"])
    server, school = queries.get_webuntis_config()
    return render_template(
        "profil.html",
        page_id="profil",
        creds=creds,
        wu_server=server,
        wu_school=school,
    )


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
        salt    = queries.get_or_create_wt_salt(session["user_id"])
        new_key = derive_key(new_pw, salt)
        _reencrypt_credentials(session["user_id"], new_key)
        queries.update_password(session["user_id"], generate_password_hash(new_pw))
        session["wt_key"] = new_key.decode()
        flash("Passwort erfolgreich geändert.", "success")
    return redirect(url_for("profil.index"))


@bp.route("/profil/webuntis/speichern", methods=["POST"])
def save_webuntis():
    wt_user   = request.form["wt_username"].strip()
    wt_pass   = request.form.get("wt_password", "")
    confirmed = request.form.get("hinweis_bestaetigt")
    from_setup = request.form.get("from_setup")

    def _error_redirect(msg):
        flash(msg, "error")
        if from_setup:
            session["needs_webuntis_setup"] = True
        return redirect(url_for("profil.index") if not from_setup else url_for("dashboard.index"))

    server, school = queries.get_webuntis_config()
    if not server or not school:
        return _error_redirect("WebUntis ist noch nicht vom Administrator konfiguriert.")
    if not confirmed:
        return _error_redirect("Bitte bestätige den Sicherheitshinweis.")
    if not wt_user:
        return _error_redirect("Benutzername ist Pflicht.")

    wt_key = session.get("wt_key", "").encode()
    creds  = queries.get_webuntis_credentials(session["user_id"])
    if not wt_pass and creds:
        queries.save_webuntis_credentials(
            session["user_id"], wt_user, creds["wt_password"],
            uses_user_key=bool(creds["uses_user_key"]),
        )
        invalidate_cache(session["user_id"])
        session.pop("needs_webuntis_setup", None)
        flash("Benutzername aktualisiert.", "success")
        return redirect(url_for("profil.index") if not from_setup else url_for("dashboard.index"))

    if not wt_pass:
        return _error_redirect("Passwort ist Pflicht.")

    try:
        grid, _, _, klasse_id, klasse_name = fetch_timetable(server, school, wt_user, wt_pass)
    except WebUntisError as e:
        return _error_redirect(f"Verbindung fehlgeschlagen: {e}")

    queries.save_webuntis_credentials(
        session["user_id"], wt_user, encrypt_with_key(wt_pass, wt_key), uses_user_key=True,
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
    invalidate_cache(session["user_id"])
    session.pop("needs_webuntis_setup", None)
    flash("WebUntis-Zugangsdaten gespeichert. Verbindung erfolgreich getestet.", "success")
    return redirect(url_for("profil.index") if not from_setup else url_for("dashboard.index"))


@bp.route("/profil/sprache", methods=["POST"])
def change_language():
    lang = request.form.get("language", "de")
    if lang not in ("de", "en"):
        lang = "de"
    queries.set_user_language(session["user_id"], lang)
    session["lang"] = lang
    flash(_t("profil.lang_saved", lang), "success")
    return redirect(url_for("profil.index"))


@bp.route("/profil/webuntis/loeschen", methods=["POST"])
def delete_webuntis():
    queries.delete_webuntis_credentials(session["user_id"])
    invalidate_cache(session["user_id"])
    flash("WebUntis-Zugangsdaten gelöscht.", "success")
    return redirect(url_for("profil.index"))
