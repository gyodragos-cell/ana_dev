from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, g, redirect, render_template, request, url_for


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "feedback.sqlite3"

app = Flask(__name__)
app.config["SECRET_KEY"] = "jokerforge-public-demo-change-me"


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    db = get_db()
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    db.commit()


def clean_text(value: str, limit: int) -> str:
    value = (value or "").strip()
    value = " ".join(value.split())
    return value[:limit]


def looks_sensitive(text: str) -> bool:
    lowered = text.lower()
    blocked = ("api key", "password", "token", "secret", "private key")
    return any(word in lowered for word in blocked)


@app.before_request
def ensure_db():
    init_db()


@app.route("/", methods=["GET", "POST"])
def index():
    error = ""
    saved = False

    if request.method == "POST":
        name = clean_text(request.form.get("name", "Anonymous"), 80) or "Anonymous"
        message = clean_text(request.form.get("message", ""), 1200)

        if not message:
            error = "Please write feedback before sending."
        elif looks_sensitive(name + " " + message):
            error = "Please do not submit secrets, tokens, passwords, or API keys."
        else:
            db = get_db()
            db.execute(
                "INSERT INTO feedback (name, message, created_at) VALUES (?, ?, ?)",
                (name, message, datetime.now(timezone.utc).isoformat(timespec="seconds")),
            )
            db.commit()
            saved = True

    rows = get_db().execute(
        "SELECT name, message, created_at FROM feedback ORDER BY id DESC LIMIT 12"
    ).fetchall()

    return render_template("index.html", feedback=rows, error=error, saved=saved)


@app.route("/health")
def health():
    return {"status": "online", "project": "JokerForge public demo"}


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8088, debug=True)
