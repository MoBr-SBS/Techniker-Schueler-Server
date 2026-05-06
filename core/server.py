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

    for bp in (dashboard_bp, stats_bp, settings_bp,
               noten_bp, auth_bp, admin_bp, profil_bp,
               mein_stundenplan_bp, pruefungen_bp, abwesenheit_bp):
        app.register_blueprint(bp)

    @app.before_request
    def require_login():
        if request.endpoint is None:
            return
        public = {"auth.login", "auth.logout", "static"}
        if request.endpoint not in public and "user_id" not in session:
            return redirect(url_for("auth.login"))

    @app.context_processor
    def inject_globals():
        import datetime
        from core.nav import NAV_ITEMS
        return {
            "current_user": session.get("username"),
            "is_admin":     session.get("is_admin", False),
            "nav":          NAV_ITEMS,
            "server_name":  app.config["SERVER_NAME_DISPLAY"],
            "session":      session,
            "timedelta":    datetime.timedelta,
        }

    return app