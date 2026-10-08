import os
from flask import Flask, render_template, redirect, url_for
from flask_wtf import CSRFProtect

from config import Config
from extensions import db


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure instance & upload folders exist
    os.makedirs(os.path.join(app.root_path, "instance"), exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    csrf = CSRFProtect(app)

    # Register blueprints
    from routes.auth import auth_bp
    from routes.student import student_bp
    from routes.applications import applications_bp
    from routes.offers import offers_bp
    from routes.internships import internships_bp
    from routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(applications_bp)
    app.register_blueprint(offers_bp)
    app.register_blueprint(internships_bp)
    app.register_blueprint(admin_bp)

    @app.route("/")
    def index():
        from flask import session
        if session.get("user_id"):
            if session.get("role") == "admin":
                return redirect(url_for("admin.dashboard"))
            return redirect(url_for("student.dashboard"))
        return redirect(url_for("auth.login"))

    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500

    # Template helpers
    from models.application import STATUS_BADGE_CLASS

    @app.context_processor
    def inject_helpers():
        return dict(status_badge=lambda s: STATUS_BADGE_CLASS.get(s, "secondary"))

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
