"""
core/queries.py – Zentraler Datenbankzugriff.

Alle SQL-Abfragen befinden sich ausschließlich hier.
Route-Dateien importieren nur Funktionen aus diesem Modul.
"""

from core.database import get_db


# ── Stundenplan ───────────────────────────────────────────────────────────────

def get_stundenplan():
    return get_db().execute(
        "SELECT * FROM stundenplan ORDER BY wochentag, stunde"
    ).fetchall()


def get_stundenplan_for_day(wochentag: int):
    return get_db().execute(
        "SELECT * FROM stundenplan WHERE wochentag=? ORDER BY stunde",
        (wochentag,),
    ).fetchall()


def set_stundenplan_slot(wochentag, stunde, fach, lehrer, raum):
    db = get_db()
    db.execute(
        "DELETE FROM stundenplan WHERE wochentag=? AND stunde=?",
        (wochentag, stunde),
    )
    db.execute(
        "INSERT INTO stundenplan (wochentag, stunde, fach, lehrer, raum) VALUES (?,?,?,?,?)",
        (wochentag, stunde, fach, lehrer, raum),
    )
    db.commit()


def delete_stundenplan_slot(slot_id):
    db = get_db()
    db.execute("DELETE FROM stundenplan WHERE id=?", (slot_id,))
    db.commit()


# ── Tests ─────────────────────────────────────────────────────────────────────

def get_all_tests():
    return get_db().execute(
        "SELECT * FROM tests ORDER BY datum"
    ).fetchall()


def get_test(test_id):
    return get_db().execute(
        "SELECT * FROM tests WHERE id=?", (test_id,)
    ).fetchone()


def add_test(fach, datum, beschreibung):
    db = get_db()
    db.execute(
        "INSERT INTO tests (fach, datum, beschreibung) VALUES (?,?,?)",
        (fach, datum, beschreibung),
    )
    db.commit()


def delete_test(test_id):
    db = get_db()
    db.execute("DELETE FROM tests WHERE id=?", (test_id,))
    db.commit()


# ── Lernmaterial ──────────────────────────────────────────────────────────────

def get_lernmaterial(test_id):
    return get_db().execute(
        "SELECT * FROM lernmaterial WHERE test_id=? ORDER BY reihenfolge, id",
        (test_id,),
    ).fetchall()


def add_lernmaterial(test_id, inhalt):
    db = get_db()
    max_order = db.execute(
        "SELECT COALESCE(MAX(reihenfolge), 0) FROM lernmaterial WHERE test_id=?",
        (test_id,),
    ).fetchone()[0]
    db.execute(
        "INSERT INTO lernmaterial (test_id, inhalt, reihenfolge) VALUES (?,?,?)",
        (test_id, inhalt, max_order + 1),
    )
    db.commit()


def delete_lernmaterial(test_id, mid):
    db = get_db()
    db.execute(
        "DELETE FROM lernmaterial WHERE id=? AND test_id=?", (mid, test_id)
    )
    db.commit()


# ── Noten ─────────────────────────────────────────────────────────────────────

def get_noten_for_user(user_id):
    return get_db().execute(
        "SELECT * FROM noten WHERE user_id=? ORDER BY fach, datum DESC", (user_id,)
    ).fetchall()


def add_note(fach, note, datum, beschreibung, exam_key=None, user_id=None, art="Ex"):
    db = get_db()
    db.execute(
        "INSERT INTO noten (fach, note, datum, beschreibung, exam_key, user_id, art) VALUES (?,?,?,?,?,?,?)",
        (fach, note, datum, beschreibung, exam_key, user_id, art),
    )
    db.commit()


def update_note(note_id, note, beschreibung, art="Ex"):
    db = get_db()
    db.execute(
        "UPDATE noten SET note=?, beschreibung=?, art=? WHERE id=?",
        (note, beschreibung, art, note_id),
    )
    db.commit()


def get_note_by_exam_key_for_user(exam_key: str, user_id: int):
    return get_db().execute(
        "SELECT * FROM noten WHERE exam_key=? AND user_id=?", (exam_key, user_id)
    ).fetchone()


def get_graded_exam_keys_for_user(user_id: int) -> set:
    rows = get_db().execute(
        "SELECT exam_key FROM noten WHERE user_id=? AND exam_key IS NOT NULL AND exam_key != ''",
        (user_id,)
    ).fetchall()
    return {row["exam_key"] for row in rows}


def get_class_avgs_by_exam_keys(exam_keys: set) -> dict:
    """Returns {exam_key: {'avg': float, 'count': int}} – one entry per user (latest),
    only for notes that have a user_id."""
    if not exam_keys:
        return {}
    ph = ",".join("?" * len(exam_keys))
    keys = list(exam_keys)
    rows = get_db().execute(
        f"""SELECT exam_key, ROUND(AVG(note), 2) AS avg, COUNT(*) AS cnt
            FROM noten
            WHERE exam_key IN ({ph})
              AND user_id IS NOT NULL
              AND id IN (
                  SELECT MAX(id) FROM noten
                  WHERE exam_key IN ({ph})
                    AND user_id IS NOT NULL
                  GROUP BY exam_key, user_id
              )
            GROUP BY exam_key""",
        keys + keys,
    ).fetchall()
    return {row["exam_key"]: {"avg": row["avg"], "count": row["cnt"]} for row in rows}


def delete_note(note_id):
    db = get_db()
    db.execute("DELETE FROM noten WHERE id=?", (note_id,))
    db.commit()


# ── Benutzer ──────────────────────────────────────────────────────────────────

def get_user_by_username(username):
    return get_db().execute(
        "SELECT * FROM users WHERE username=?", (username,)
    ).fetchone()


def get_user_by_id(user_id):
    return get_db().execute(
        "SELECT * FROM users WHERE id=?", (user_id,)
    ).fetchone()


def update_password(user_id, password_hash):
    db = get_db()
    db.execute(
        "UPDATE users SET password_hash=? WHERE id=?", (password_hash, user_id)
    )
    db.commit()


def get_all_users():
    return get_db().execute(
        "SELECT id, username, is_admin, erstellt_am FROM users ORDER BY username"
    ).fetchall()


def count_admins():
    return get_db().execute(
        "SELECT COUNT(*) FROM users WHERE is_admin=1"
    ).fetchone()[0]


def add_user(username, password_hash, is_admin):
    db = get_db()
    db.execute(
        "INSERT INTO users (username, password_hash, is_admin) VALUES (?,?,?)",
        (username, password_hash, is_admin),
    )
    db.commit()


def user_exists(username):
    return get_db().execute(
        "SELECT id FROM users WHERE username=?", (username,)
    ).fetchone() is not None


def delete_user(user_id):
    db = get_db()
    db.execute("DELETE FROM users WHERE id=?", (user_id,))
    db.commit()


# ── Prüfungen (manuell) ───────────────────────────────────────────────────────

def get_all_pruefungen():
    return get_db().execute(
        "SELECT * FROM pruefungen ORDER BY datum"
    ).fetchall()


def get_pruefung(pruefung_id):
    return get_db().execute(
        "SELECT * FROM pruefungen WHERE id=?", (pruefung_id,)
    ).fetchone()


def add_pruefung(fach, art, datum, notiz=""):
    db = get_db()
    db.execute(
        "INSERT INTO pruefungen (fach, art, datum, notiz) VALUES (?,?,?,?)",
        (fach, art, datum, notiz),
    )
    db.commit()


def update_pruefung(pruefung_id, fach, art, datum, notiz=""):
    db = get_db()
    db.execute(
        "UPDATE pruefungen SET fach=?, art=?, datum=?, notiz=? WHERE id=?",
        (fach, art, datum, notiz, pruefung_id),
    )
    db.commit()


def delete_pruefung(pruefung_id):
    db = get_db()
    db.execute("DELETE FROM pruefungen WHERE id=?", (pruefung_id,))
    db.commit()


def get_stundenplan_faecher():
    rows = get_db().execute(
        "SELECT DISTINCT fach FROM stundenplan ORDER BY fach"
    ).fetchall()
    return [row["fach"] for row in rows]


def get_pruefungen_for_week(start, end):
    return get_db().execute(
        "SELECT * FROM pruefungen WHERE datum >= ? AND datum <= ? ORDER BY datum",
        (start.isoformat(), end.isoformat()),
    ).fetchall()


# ── WebUntis-Zugangsdaten ─────────────────────────────────────────────────────

def get_webuntis_credentials(user_id):
    return get_db().execute(
        "SELECT * FROM webuntis_credentials WHERE user_id=?", (user_id,)
    ).fetchone()


def save_webuntis_credentials(user_id, wt_username, wt_password):
    db = get_db()
    db.execute(
        """INSERT INTO webuntis_credentials (user_id, server, school, wt_username, wt_password)
           VALUES (?,?,?,?,?)
           ON CONFLICT(user_id) DO UPDATE SET
               wt_username=excluded.wt_username,
               wt_password=excluded.wt_password,
               gespeichert_am=datetime('now')""",
        (user_id, "", "", wt_username, wt_password),
    )
    db.commit()


def delete_webuntis_credentials(user_id):
    db = get_db()
    db.execute("DELETE FROM webuntis_credentials WHERE user_id=?", (user_id,))
    db.commit()


# ── Prüfungs-Hilfsfunktionen ──────────────────────────────────────────────────

import re as _re
import datetime as _dt


def make_exam_key(fach: str, datum: _dt.date) -> str:
    safe = _re.sub(r"[^A-Za-z0-9]", "_", fach).strip("_") or "unbekannt"
    return f"{safe}_{datum.strftime('%Y%m%d')}"


# ── Prüfungsnotizen ───────────────────────────────────────────────────────────

def get_exam_note(exam_key: str):
    return get_db().execute(
        "SELECT * FROM exam_notes WHERE exam_key=?", (exam_key,)
    ).fetchone()


def save_exam_note(exam_key: str, content: str, username: str):
    db = get_db()
    db.execute(
        """INSERT INTO exam_notes (exam_key, content, updated_at, updated_by)
           VALUES (?,?,datetime('now'),?)
           ON CONFLICT(exam_key) DO UPDATE SET
               content=excluded.content,
               updated_at=datetime('now'),
               updated_by=excluded.updated_by""",
        (exam_key, content, username),
    )
    db.commit()


def get_exam_note_keys() -> set:
    rows = get_db().execute(
        "SELECT exam_key FROM exam_notes WHERE content != ''"
    ).fetchall()
    return {row["exam_key"] for row in rows}


# ── App-Einstellungen (global, Admin) ─────────────────────────────────────────

def get_app_setting(key: str, default: str = "") -> str:
    row = get_db().execute(
        "SELECT value FROM app_settings WHERE key=?", (key,)
    ).fetchone()
    return row["value"] if row else default


def set_app_setting(key: str, value: str):
    db = get_db()
    db.execute(
        "INSERT INTO app_settings (key, value) VALUES (?,?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, value),
    )
    db.commit()


def get_all_app_settings() -> dict:
    rows = get_db().execute("SELECT key, value FROM app_settings").fetchall()
    return {row["key"]: row["value"] for row in rows}


def get_webuntis_config() -> tuple[str, str]:
    """Gibt (server, school) aus den globalen Einstellungen zurück."""
    return (
        get_app_setting("webuntis_server"),
        get_app_setting("webuntis_school"),
    )
