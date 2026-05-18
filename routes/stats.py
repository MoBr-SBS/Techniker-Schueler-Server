from flask import Blueprint, render_template
from core.nav import NAV_ITEMS

bp = Blueprint("stats", __name__)

@bp.route("/stats")
def stats():
    return render_template(
        "stats.html",
        page_id="stats",
        nav=NAV_ITEMS,
    )