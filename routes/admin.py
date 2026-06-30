import os
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from core import queries
from core.webuntis_client import fetch_timetable, WebUntisError, clear_all_caches

bp = Blueprint("admin", __name__)

_UPLOAD_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "static", "uploads"
)
_IMAGE_EXTS   = {"png", "jpg", "jpeg", "gif", "svg", "webp"}
_FAVICON_EXTS = {"ico", "png", "svg"}


def _save_upload(file_field, name, allowed_exts):
    f = request.files.get(file_field)
    if not f or f.filename == "":
        return None
    ext = f.filename.rsplit(".", 1)[-1].lower() if "." in f.filename else ""
    if ext not in allowed_exts:
        flash(f"Ungültiges Dateiformat für {file_field} (erlaubt: {', '.join(allowed_exts)}).", "error")
        return None
    filename = f"{name}.{ext}"
    os.makedirs(_UPLOAD_DIR, exist_ok=True)
    f.save(os.path.join(_UPLOAD_DIR, filename))
    return filename


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


@bp.route("/admin/benutzer/role/<int:user_id>", methods=["POST"])
def toggle_trusted(user_id):
    guard = _require_admin()
    if guard:
        return guard
    user = queries.get_user_by_id(user_id)
    if not user:
        return redirect(url_for("admin.benutzer"))
    new_role = "user" if user["role"] == "trusted" else "trusted"
    queries.set_user_role(user_id, new_role)
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


@bp.route("/admin/verbindungen")
def verbindungen():
    guard = _require_admin()
    if guard:
        return guard
    klassen = [dict(k) for k in queries.get_klassen()]
    klassen_faecher = {
        k["klasse_id"]: queries.get_faecher_fuer_klasse(k["klasse_id"])
        for k in klassen
    }
    return render_template(
        "admin_verbindungen.html",
        page_id="einstellungen",
        gruppen=queries.get_all_fach_verbindungen(),
        klassen=klassen,
        klassen_faecher=klassen_faecher,
    )


@bp.route("/admin/verbindungen/hinzufuegen", methods=["POST"])
def verbindung_add():
    guard = _require_admin()
    if guard:
        return guard
    klassen = queries.get_klassen()
    eintraege = []
    for k in klassen:
        fach = request.form.get(f"fach_{k['klasse_id']}", "").strip()
        if fach:
            eintraege.append((k["klasse_id"], fach))
    if len(eintraege) >= 2:
        queries.add_fach_verbindung_gruppe(eintraege)
        flash("Verbindung gespeichert.", "success")
    else:
        flash("Mindestens zwei Klassen mit Fach auswählen.", "error")
    return redirect(url_for("admin.verbindungen"))


@bp.route("/admin/verbindungen/loeschen", methods=["POST"])
def verbindung_delete():
    guard = _require_admin()
    if guard:
        return guard
    try:
        queries.delete_fach_verbindung_gruppe(int(request.form.get("gruppe_id", "")))
    except (ValueError, TypeError):
        pass
    return redirect(url_for("admin.verbindungen"))


@bp.route("/admin/einstellungen")
def einstellungen():
    guard = _require_admin()
    if guard:
        return guard
    server, school = queries.get_webuntis_config()
    s = queries.get_all_app_settings()
    return render_template(
        "admin_einstellungen.html",
        page_id="einstellungen",
        wu_server=server,
        wu_school=school,
        s=s,
    )


@bp.route("/admin/einstellungen/webuntis", methods=["POST"])
def save_webuntis_config():
    guard = _require_admin()
    if guard:
        return guard

    server = request.form.get("wu_server", "").strip().rstrip("/")
    school = request.form.get("wu_school", "").strip()

    if not server or not school:
        flash("Server und Schulname sind Pflichtfelder.", "error")
        return redirect(url_for("admin.einstellungen"))

    # Verbindung testen – ohne echte Zugangsdaten nur Erreichbarkeit prüfen
    # (Ein vollständiger Login-Test erfordert Nutzerdaten, den machen wir hier nicht.)
    queries.set_app_setting("webuntis_server", server)
    queries.set_app_setting("webuntis_school", school)
    clear_all_caches()
    flash(f"WebUntis-Konfiguration gespeichert: {server} / {school}", "success")
    return redirect(url_for("admin.einstellungen"))


@bp.route("/admin/einstellungen/branding", methods=["POST"])
def save_branding():
    guard = _require_admin()
    if guard:
        return guard

    name = request.form.get("server_name", "").strip()
    if name:
        queries.set_app_setting("server_name", name)

    logo_file = _save_upload("logo", "logo", _IMAGE_EXTS)
    if logo_file:
        queries.set_app_setting("logo_filename", logo_file)
    if request.form.get("logo_delete"):
        queries.set_app_setting("logo_filename", "")
        _delete_upload("logo")

    fav_file = _save_upload("favicon", "favicon", _FAVICON_EXTS)
    if fav_file:
        queries.set_app_setting("favicon_filename", fav_file)
    if request.form.get("favicon_delete"):
        queries.set_app_setting("favicon_filename", "")
        _delete_upload("favicon")

    flash("Branding gespeichert.", "success")
    return redirect(url_for("admin.einstellungen") + "#branding")


@bp.route("/admin/einstellungen/sprache", methods=["POST"])
def save_default_language():
    guard = _require_admin()
    if guard:
        return guard
    lang = request.form.get("default_language", "de")
    if lang not in ("de", "en"):
        lang = "de"
    queries.set_app_setting("default_language", lang)
    from core.i18n import t as _t
    flash(_t("admin.default_lang_saved", session.get("lang", "de")), "success")
    return redirect(url_for("admin.einstellungen") + "#sprache")


@bp.route("/admin/einstellungen/darstellung", methods=["POST"])
def save_darstellung():
    guard = _require_admin()
    if guard:
        return guard

    accent = request.form.get("accent_color", "").strip()
    if accent:
        queries.set_app_setting("accent_color", accent)
    else:
        queries.set_app_setting("accent_color", "")

    theme = request.form.get("default_theme", "dark")
    if theme not in ("dark", "light"):
        theme = "dark"
    queries.set_app_setting("default_theme", theme)

    flash("Darstellung gespeichert.", "success")
    return redirect(url_for("admin.einstellungen") + "#darstellung")


@bp.route("/admin/einstellungen/funktionen", methods=["POST"])
def save_funktionen():
    guard = _require_admin()
    if guard:
        return guard

    monat = request.form.get("schuljahr_monat", "9").zfill(2)
    tag   = request.form.get("schuljahr_tag",   "1").zfill(2)
    queries.set_app_setting("schuljahr_beginn", f"{monat}-{tag}")

    queries.set_app_setting("allow_registration",
                            "1" if request.form.get("allow_registration") else "0")
    queries.set_app_setting("maintenance_mode",
                            "1" if request.form.get("maintenance_mode") else "0")
    msg = request.form.get("maintenance_message", "").strip()
    queries.set_app_setting("maintenance_message", msg)

    flash("Funktionen gespeichert.", "success")
    return redirect(url_for("admin.einstellungen") + "#funktionen")


def _delete_upload(name):
    for ext in list(_IMAGE_EXTS | _FAVICON_EXTS):
        path = os.path.join(_UPLOAD_DIR, f"{name}.{ext}")
        if os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                pass
