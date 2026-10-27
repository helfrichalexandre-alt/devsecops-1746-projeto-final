"""Fábrica da aplicação Clube Aurora."""

import os
from pathlib import Path

from flask import Flask

from . import db


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-only-change-me"),
        DATABASE=os.environ.get("DATABASE", str(Path(app.instance_path) / "aurora.db")),
        SEED_PASSWORD=os.environ.get("SEED_PASSWORD", "dev-only-change-me"),
    )
    if test_config:
        app.config.update(test_config)

    db_path = Path(app.config["DATABASE"])
    try:
        db_path.parent.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        app.config["DATABASE"] = str(Path("/tmp") / "aurora.db")

    app.teardown_appcontext(db.close_db)

    from .main import bp

    app.register_blueprint(bp)

    @app.cli.command("init-db")
    def init_db_command():
        """Recria o banco com dados de exemplo."""
        db.init_db()
        print("Banco inicializado.")

    with app.app_context():
        if not Path(app.config["DATABASE"]).exists() or os.path.getsize(app.config["DATABASE"]) == 0:
            db.init_db()

    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; frame-ancestors 'none'"
        )
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        return response

    return app
