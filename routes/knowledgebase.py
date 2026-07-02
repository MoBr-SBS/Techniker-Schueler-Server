import markdown as md_lib
from flask import Blueprint, render_template, request, redirect, url_for, session, abort, jsonify
from core.database import get_db

bp = Blueprint("knowledgebase", __name__)


def _require_admin():
    if not session.get("is_admin"):
        abort(403)


def _get_categories(visible_only=False):
    q = "SELECT * FROM kb_categories"
    if visible_only:
        q += " WHERE visible=1"
    q += " ORDER BY sort_order, name"
    return get_db().execute(q).fetchall()


def _get_pages_by_category(visible_only=False):
    q = "SELECT * FROM kb_pages"
    if visible_only:
        q += " WHERE visible=1"
    q += " ORDER BY sort_order, title"
    pages = get_db().execute(q).fetchall()
    cats = _get_categories(visible_only=visible_only)
    grouped = {c["id"]: {"cat": c, "pages": []} for c in cats}
    ungrouped = []
    for p in pages:
        if p["category_id"] and p["category_id"] in grouped:
            grouped[p["category_id"]]["pages"].append(p)
        elif not p["category_id"]:
            ungrouped.append(p)
        # pages in hidden categories are omitted for non-admins
    result = list(grouped.values())
    result.sort(key=lambda x: (x["cat"]["sort_order"], x["cat"]["name"]))
    if ungrouped:
        result.append({"cat": None, "pages": ungrouped})
    return result


@bp.route("/knowledgebase")
def index():
    is_admin = bool(session.get("is_admin"))
    grouped = _get_pages_by_category(visible_only=not is_admin)
    return render_template(
        "knowledgebase.html",
        page_id="knowledgebase",
        grouped=grouped,
        view="list",
    )


@bp.route("/knowledgebase/page/<int:page_id>")
def view_page(page_id):
    is_admin = bool(session.get("is_admin"))
    db = get_db()
    page = db.execute("SELECT * FROM kb_pages WHERE id=?", (page_id,)).fetchone()
    if not page:
        abort(404)
    if not page["visible"] and not is_admin:
        abort(403)
    html_content = md_lib.markdown(
        page["content"],
        extensions=["fenced_code", "tables", "toc", "nl2br"],
    )
    grouped = _get_pages_by_category(visible_only=not is_admin)
    return render_template(
        "knowledgebase.html",
        page_id="knowledgebase",
        grouped=grouped,
        view="page",
        current_page=page,
        html_content=html_content,
    )


# ── Live preview ─────────────────────────────────────────────────────────────

@bp.route("/knowledgebase/_preview", methods=["POST"])
def preview():
    if not session.get("is_admin"):
        abort(403)
    content = request.json.get("content", "") if request.is_json else ""
    html = md_lib.markdown(content, extensions=["fenced_code", "tables", "toc", "nl2br"])
    return jsonify({"html": html})


# ── Admin: Category management ───────────────────────────────────────────────

@bp.route("/knowledgebase/admin/category/add", methods=["POST"])
def add_category():
    _require_admin()
    name = request.form.get("name", "").strip()
    sort_order = int(request.form.get("sort_order", 0) or 0)
    if name:
        get_db().execute(
            "INSERT INTO kb_categories (name, sort_order) VALUES (?,?)",
            (name, sort_order),
        )
        get_db().commit()
    return redirect(url_for("knowledgebase.index"))


@bp.route("/knowledgebase/admin/category/<int:cat_id>/delete", methods=["POST"])
def delete_category(cat_id):
    _require_admin()
    db = get_db()
    db.execute("UPDATE kb_pages SET category_id=NULL WHERE category_id=?", (cat_id,))
    db.execute("DELETE FROM kb_categories WHERE id=?", (cat_id,))
    db.commit()
    return redirect(url_for("knowledgebase.index"))


@bp.route("/knowledgebase/admin/category/<int:cat_id>/toggle", methods=["POST"])
def toggle_category_visibility(cat_id):
    _require_admin()
    db = get_db()
    db.execute(
        "UPDATE kb_categories SET visible = CASE WHEN visible=1 THEN 0 ELSE 1 END WHERE id=?",
        (cat_id,),
    )
    db.commit()
    return redirect(request.referrer or url_for("knowledgebase.index"))


@bp.route("/knowledgebase/admin/category/<int:cat_id>/edit", methods=["POST"])
def edit_category(cat_id):
    _require_admin()
    name = request.form.get("name", "").strip()
    sort_order = int(request.form.get("sort_order", 0) or 0)
    if name:
        db = get_db()
        db.execute(
            "UPDATE kb_categories SET name=?, sort_order=? WHERE id=?",
            (name, sort_order, cat_id),
        )
        db.commit()
    return redirect(url_for("knowledgebase.index"))


# ── Admin: Page management ────────────────────────────────────────────────────

@bp.route("/knowledgebase/admin/page/new")
def new_page():
    _require_admin()
    grouped = _get_pages_by_category(visible_only=False)
    return render_template(
        "knowledgebase.html",
        page_id="knowledgebase",
        grouped=grouped,
        view="edit",
        current_page=None,
        categories=_get_categories(visible_only=False),
    )


@bp.route("/knowledgebase/admin/page/<int:page_id>/edit")
def edit_page(page_id):
    _require_admin()
    page = get_db().execute("SELECT * FROM kb_pages WHERE id=?", (page_id,)).fetchone()
    if not page:
        abort(404)
    grouped = _get_pages_by_category(visible_only=False)
    return render_template(
        "knowledgebase.html",
        page_id="knowledgebase",
        grouped=grouped,
        view="edit",
        current_page=page,
        categories=_get_categories(visible_only=False),
    )


@bp.route("/knowledgebase/admin/page/save", methods=["POST"])
def save_page():
    _require_admin()
    page_id = request.form.get("page_id") or None
    title = request.form.get("title", "").strip()
    content = request.form.get("content", "")
    visible = 1 if request.form.get("visible") else 0
    sort_order = int(request.form.get("sort_order", 0) or 0)
    category_id = request.form.get("category_id") or None
    if category_id:
        category_id = int(category_id)

    db = get_db()
    if page_id:
        db.execute(
            """UPDATE kb_pages
               SET title=?, content=?, visible=?, sort_order=?, category_id=?,
                   updated_at=datetime('now'), updated_by=?
               WHERE id=?""",
            (title, content, visible, sort_order, category_id, session.get("username"), int(page_id)),
        )
        db.commit()
        return redirect(url_for("knowledgebase.view_page", page_id=int(page_id)))
    else:
        cur = db.execute(
            """INSERT INTO kb_pages (title, content, visible, sort_order, category_id, updated_by)
               VALUES (?,?,?,?,?,?)""",
            (title, content, visible, sort_order, category_id, session.get("username")),
        )
        db.commit()
        return redirect(url_for("knowledgebase.view_page", page_id=cur.lastrowid))


@bp.route("/knowledgebase/admin/page/<int:page_id>/delete", methods=["POST"])
def delete_page(page_id):
    _require_admin()
    db = get_db()
    db.execute("DELETE FROM kb_pages WHERE id=?", (page_id,))
    db.commit()
    return redirect(url_for("knowledgebase.index"))


@bp.route("/knowledgebase/admin/page/<int:page_id>/toggle", methods=["POST"])
def toggle_visibility(page_id):
    _require_admin()
    db = get_db()
    db.execute(
        "UPDATE kb_pages SET visible = CASE WHEN visible=1 THEN 0 ELSE 1 END WHERE id=?",
        (page_id,),
    )
    db.commit()
    return redirect(request.referrer or url_for("knowledgebase.index"))
