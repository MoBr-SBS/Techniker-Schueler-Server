from flask import Blueprint, render_template, current_app
from core.nav import NAV_ITEMS

bp = Blueprint("settings", __name__)

@bp.route("/settings")
def settings():
    return render_template(
        "settings.html",
        page_id="settings",
        nav=NAV_ITEMS,
        server_name=current_app.config["SERVER_NAME_DISPLAY"],
    )