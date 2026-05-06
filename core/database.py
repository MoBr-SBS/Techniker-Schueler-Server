import sqlite3
import os
from flask import g

_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "school.db")


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(_DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(_DB_PATH)
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript("""
        CREATE TABLE IF NOT EXISTS stundenplan (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            wochentag INTEGER NOT NULL,
            stunde    INTEGER NOT NULL,
            fach      TEXT    NOT NULL,
            lehrer    TEXT    DEFAULT '',
            raum      TEXT    DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS tests (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            fach         TEXT NOT NULL,
            datum        TEXT NOT NULL,
            beschreibung TEXT DEFAULT '',
            erstellt_am  TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS lernmaterial (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            test_id     INTEGER NOT NULL REFERENCES tests(id) ON DELETE CASCADE,
            inhalt      TEXT    NOT NULL,
            reihenfolge INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS noten (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            fach         TEXT NOT NULL,
            note         REAL NOT NULL,
            datum        TEXT NOT NULL,
            beschreibung TEXT DEFAULT '',
            erstellt_am  TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            is_admin      INTEGER DEFAULT 0,
            erstellt_am   TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS webuntis_credentials (
            user_id        INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
            server         TEXT NOT NULL,
            school         TEXT NOT NULL,
            wt_username    TEXT NOT NULL,
            wt_password    TEXT NOT NULL,
            gespeichert_am TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS pruefungen (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            fach        TEXT NOT NULL,
            art         TEXT NOT NULL CHECK(art IN ('SA', 'Ex')),
            datum       TEXT NOT NULL,
            notiz       TEXT DEFAULT '',
            erstellt_am TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS app_settings (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS exam_notes (
            exam_key   TEXT PRIMARY KEY,
            content    TEXT NOT NULL DEFAULT '',
            updated_at TEXT DEFAULT (datetime('now')),
            updated_by TEXT NOT NULL DEFAULT ''
        );
    """)
    # Migration: pruefungen schema (SA/Ex constraint + notiz column)
    row = db.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='pruefungen'"
    ).fetchone()
    if row and ("'Schulaufgabe'" in row[0] or "notiz" not in row[0]):
        db.execute("ALTER TABLE pruefungen RENAME TO _pruef_old")
        db.execute("""CREATE TABLE pruefungen (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fach TEXT NOT NULL,
            art TEXT NOT NULL CHECK(art IN ('SA','Ex')),
            datum TEXT NOT NULL,
            notiz TEXT DEFAULT '',
            erstellt_am TEXT DEFAULT (datetime('now'))
        )""")
        db.execute("""INSERT INTO pruefungen (id, fach, art, datum, notiz, erstellt_am)
            SELECT id, fach,
                   CASE WHEN art='Schulaufgabe' THEN 'SA' ELSE art END,
                   datum, '', erstellt_am
            FROM _pruef_old""")
        db.execute("DROP TABLE _pruef_old")
        db.commit()

    # Migrations: noten table extensions
    noten_cols = [row[1] for row in db.execute("PRAGMA table_info(noten)").fetchall()]
    if "exam_key" not in noten_cols:
        db.execute("ALTER TABLE noten ADD COLUMN exam_key TEXT DEFAULT NULL")
        db.commit()
    if "klassen_schnitt" not in noten_cols:
        db.execute("ALTER TABLE noten ADD COLUMN klassen_schnitt REAL DEFAULT NULL")
        db.commit()
    if "user_id" not in noten_cols:
        db.execute("ALTER TABLE noten ADD COLUMN user_id INTEGER REFERENCES users(id) DEFAULT NULL")
        db.commit()
    if "art" not in noten_cols:
        db.execute("ALTER TABLE noten ADD COLUMN art TEXT DEFAULT 'Ex'")
        db.commit()
        # Bestehende Einträge: art aus beschreibung ableiten falls möglich
        db.execute("UPDATE noten SET art='SA' WHERE beschreibung='SA'")
        db.execute("UPDATE noten SET art='Ex' WHERE beschreibung='Ex'")
        db.commit()

    if db.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        from werkzeug.security import generate_password_hash
        db.execute(
            "INSERT INTO users (username, password_hash, is_admin) VALUES (?,?,?)",
            ("admin", generate_password_hash("admin123"), 1),
        )
        print("Standard-Admin angelegt: admin / admin123  – Bitte Passwort sofort ändern!")
    db.commit()
    db.close()


def init_app(app):
    app.teardown_appcontext(close_db)
    init_db()
