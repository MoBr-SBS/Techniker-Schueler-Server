"""
routes/dashboard.py – Homepage / Dashboard.
"""

from flask import Blueprint, render_template, current_app
from core.nav import NAV_ITEMS

bp = Blueprint("dashboard", __name__)


@bp.route("/")
def index():
    stats = [
        {"label": "CPU",        "value": "23 %",   "icon": "cpu",        "color": "blue"},
        {"label": "RAM",        "value": "4.2 GB",  "icon": "database",   "color": "purple"},
        {"label": "Uptime",     "value": "14 d",    "icon": "clock",      "color": "green"},
        {"label": "Anfragen",   "value": "1 024",   "icon": "activity",   "color": "orange"},
    ]
    return render_template(
        "dashboard.html",
        page_id="dashboard",
        nav=NAV_ITEMS,
        server_name=current_app.config["SERVER_NAME_DISPLAY"],
        stats=stats,
    )