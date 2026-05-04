from flask import Blueprint, render_template, session, current_app, redirect, url_for
from core import queries
from core.encryption import decrypt
from core.webuntis_client import get_timetable_cached, invalidate_cache
from core.nav import NAV_ITEMS

bp = Blueprint("mein_stundenplan", __name__)

WOCHENTAGE = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag"]


@bp.route("/mein-stundenplan")
def index():
    creds = queries.get_webuntis_credentials(session["user_id"])

    if not creds:
        return render_template(
            "mein_stundenplan.html",
            page_id="mein_stundenplan",
            nav=NAV_ITEMS,
            server_name=current_app.config["SERVER_NAME_DISPLAY"],
            configured=False,
        )

    grid, monday, periods_info, warning = get_timetable_cached(
        session["user_id"],
        creds["server"],
        creds["school"],
        creds["wt_username"],
        decrypt(creds["wt_password"]),
    )

    return render_template(
        "mein_stundenplan.html",
        page_id="mein_stundenplan",
        nav=NAV_ITEMS,
        server_name=current_app.config["SERVER_NAME_DISPLAY"],
        configured=True,
        grid=grid,
        periods_info=periods_info,
        wochentage=WOCHENTAGE,
        monday=monday,
        fetch_error=warning if grid is None else None,
        fetch_warning=warning if grid is not None else None,
    )


@bp.route("/mein-stundenplan/aktualisieren", methods=["POST"])
def refresh():
    invalidate_cache(session["user_id"])
    return redirect(url_for("mein_stundenplan.index"))
