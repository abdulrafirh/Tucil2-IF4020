# app/__init__.py
from __future__ import annotations
from flask import Flask, jsonify
from flask_cors import CORS
import os

def create_app() -> Flask:
    app = Flask(__name__)
    # Optional: limit upload size (set via env, default 50 MB)
    app.config["MAX_CONTENT_LENGTH"] = int(os.getenv("MAX_CONTENT_LENGTH", 50 * 1024 * 1024))
    # CORS (adjust origins as needed)
    CORS(app, resources={r"/api/*": {"origins": "*"}}, expose_headers=["X-PSNR-dB", "X-Ext"])

    # Register blueprints
    from .routes.api_bp import api_bp
    app.register_blueprint(api_bp, url_prefix="/api")

    # JSON error handler
    @app.errorhandler(Exception)
    def _on_error(e):
        # Keep simple; customize per error type if you like
        status = getattr(e, "code", 500)
        return jsonify({"ok": False, "error": str(e)}), status

    return app
