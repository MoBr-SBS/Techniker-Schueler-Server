"""
core/server.py – Application Factory.
Registriert alle Blueprints und konfiguriert die Flask-App.
"""

from flask import Flask, session, request, redirect, url_for
from core.config import Config


def create_app(config: Config = None) -> Flask:
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )

    app.config.from_object(config or Config)

    from core.database import init_app as db_init
    db_init(app)

    from routes.dashboard        import bp as dashboard_bp
    from routes.stats            import bp as stats_bp
    from routes.settings         import bp as settings_bp
    from routes.noten            import bp as noten_bp
    from routes.auth             import bp as auth_bp
    from routes.admin            import bp as admin_bp
    from routes.profil           import bp as profil_bp
    from routes.mein_stundenplan import bp as mein_stundenplan_bp
    from routes.pruefungen       import bp as pruefungen_bp
    from routes.abwesenheit      import bp as abwesenheit_bp
    from routes.server_status    import bp as server_status_bp

    for bp in (dashboard_bp, stats_bp, settings_bp,
               noten_bp, auth_bp, admin_bp, profil_bp,
               mein_stundenplan_bp, pruefungen_bp, abwesenheit_bp,
               server_status_bp):
        app.register_blueprint(bp)

    @app.before_request
    def require_login():
        if request.endpoint is None:
            return
        public = {"auth.login", "auth.logout", "auth.register", "static"}
        if request.endpoint not in public and "user_id" not in session:
            return redirect(url_for("auth.login"))
        if ("user_id" in session and not session.get("is_admin")
                and request.endpoint not in public):
            from core.queries import get_app_setting
            if get_app_setting("maintenance_mode") == "1":
                from flask import render_template as _rt
                return _rt("maintenance.html",
                    server_name=get_app_setting("server_name") or app.config["SERVER_NAME_DISPLAY"],
                    message=get_app_setting("maintenance_message") or "Der Server wird gerade gewartet.")

    @app.context_processor
    def inject_globals():
        import datetime
        from core.nav import NAV_ITEMS
        from core.queries import get_app_setting
        from flask import url_for as _uf

        db_name = get_app_setting("server_name")
        server_name = db_name if db_name else app.config["SERVER_NAME_DISPLAY"]

        logo_file = get_app_setting("logo_filename")
        logo_url  = _uf("static", filename=f"uploads/{logo_file}") if logo_file else None

        fav_file = get_app_setting("favicon_filename")
        favicon_url = _uf("static", filename=f"uploads/{fav_file}") if fav_file else None

        return {
            "current_user":       session.get("username"),
            "is_admin":           session.get("is_admin", False),
            "nav":                NAV_ITEMS,
            "server_name":        server_name,
            "session":            session,
            "timedelta":          datetime.timedelta,
            "accent_color":       get_app_setting("accent_color"),
            "default_theme":      get_app_setting("default_theme", "dark"),
            "logo_url":           logo_url,
            "favicon_url":        favicon_url,
            "maintenance_mode":   get_app_setting("maintenance_mode") == "1",
            "allow_registration": get_app_setting("allow_registration") == "1",
        }

    return app