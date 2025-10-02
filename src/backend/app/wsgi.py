# app/wsgi.py
from __future__ import annotations
from . import create_app

app = create_app()

if __name__ == "__main__":
    # For local dev only; in prod use gunicorn/uwsgi
    app.run(host="0.0.0.0", port=8000, debug=True)
