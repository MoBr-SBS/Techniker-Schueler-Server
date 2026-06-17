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
        "SELECT id, username, is_admin, role, erstellt_am, klasse_id, klasse_name "
        "FROM users ORDER BY klasse_name NULLS LAST, username"
    ).fetchall()


def update_user_klasse(user_id, klasse_id, klasse_name=None):
    db = get_db()
    db.execute(
        "UPDATE users SET klasse_id=?, klasse_name=? WHERE id=?",
        (klasse_id, klasse_name, user_id),
    )
    db.commit()


def set_user_role(user_id, role):
    db = get_db()
    db.execute("UPDATE users SET role=? WHERE id=?", (role, user_id))
    db.commit()


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


# ── Klassen & Fächer ──────────────────────────────────────────────────────────

def get_klassen():
    """Alle bekannten Klassen aus der users-Tabelle."""
    return get_db().execute(
        "SELECT DISTINCT klasse_id, klasse_name FROM users "
        "WHERE klasse_id IS NOT NULL ORDER BY klasse_name"
    ).fetchall()


def get_faecher_fuer_klasse(klasse_id: int) -> list:
    return [
        row["fach"] for row in get_db().execute(
            "SELECT fach FROM klasse_faecher WHERE klasse_id=? ORDER BY fach",
            (klasse_id,),
        ).fetchall()
    ]


def set_klasse_faecher(klasse_id: int, faecher: set):
    db = get_db()
    db.execute("DELETE FROM klasse_faecher WHERE klasse_id=?", (klasse_id,))
    for fach in faecher:
        db.execute(
            "INSERT OR IGNORE INTO klasse_faecher (klasse_id, fach) VALUES (?,?)",
            (klasse_id, fach),
        )
    db.commit()


# ── Fach-Verbindungen ─────────────────────────────────────────────────────────

def get_all_fach_verbindungen():
    """Gibt alle Verbindungen gruppiert zurück: {gruppe_id: [{klasse_id, fach, klasse_name}]}"""
    rows = get_db().execute("""
        SELECT v.gruppe_id, v.klasse_id, v.fach, u.klasse_name
        FROM fach_verbindungen v
        LEFT JOIN (
            SELECT DISTINCT klasse_id, klasse_name FROM users WHERE klasse_id IS NOT NULL
        ) u ON u.klasse_id = v.klasse_id
        ORDER BY v.gruppe_id, u.klasse_name
    """).fetchall()
    gruppen: dict = {}
    for row in rows:
        gruppen.setdefault(row["gruppe_id"], []).append({
            "klasse_id":   row["klasse_id"],
            "fach":        row["fach"],
            "klasse_name": row["klasse_name"] or str(row["klasse_id"]),
        })
    return gruppen


def add_fach_verbindung_gruppe(eintraege: list[tuple[int, str]]):
    """Legt eine neue Verbindungsgruppe an. eintraege = [(klasse_id, fach), ...]"""
    db = get_db()
    row = db.execute("SELECT COALESCE(MAX(gruppe_id), 0) + 1 FROM fach_verbindungen").fetchone()
    gruppe_id = row[0]
    for klasse_id, fach in eintraege:
        db.execute(
            "INSERT OR REPLACE INTO fach_verbindungen (gruppe_id, klasse_id, fach) VALUES (?,?,?)",
            (gruppe_id, klasse_id, fach),
        )
    db.commit()


def delete_fach_verbindung_gruppe(gruppe_id: int):
    db = get_db()
    db.execute("DELETE FROM fach_verbindungen WHERE gruppe_id=?", (gruppe_id,))
    db.commit()


def delete_user(user_id):
    db = get_db()
    db.execute("DELETE FROM users WHERE id=?", (user_id,))
    db.commit()


# ── Prüfungen (manuell) ───────────────────────────────────────────────────────

def get_all_pruefungen(klasse_id=None):
    if klasse_id is not None:
        # Zeige Prüfungen der eigenen Klasse, klassenlose, und solche wo
        # Prüfungsklasse+Fach über eine Verbindungsgruppe mit der eigenen Klasse verknüpft ist.
        return get_db().execute("""
            SELECT p.* FROM pruefungen p
            WHERE p.klasse_id IS NULL
               OR p.klasse_id = ?
               OR EXISTS (
                   SELECT 1 FROM fach_verbindungen v1
                   JOIN fach_verbindungen v2 ON v1.gruppe_id = v2.gruppe_id
                   WHERE v1.klasse_id = p.klasse_id
                     AND v1.fach      = p.fach
                     AND v2.klasse_id = ?
               )
            ORDER BY p.datum
        """, (klasse_id, klasse_id)).fetchall()
    return get_db().execute(
        "SELECT * FROM pruefungen ORDER BY datum"
    ).fetchall()


def get_pruefung(pruefung_id):
    return get_db().execute(
        "SELECT * FROM pruefungen WHERE id=?", (pruefung_id,)
    ).fetchone()


def add_pruefung(fach, art, datum, notiz="", klasse_id=None):
    db = get_db()
    db.execute(
        "INSERT INTO pruefungen (fach, art, datum, notiz, klasse_id) VALUES (?,?,?,?,?)",
        (fach, art, datum, notiz, klasse_id),
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


def save_webuntis_credentials(user_id, wt_username, wt_password, uses_user_key: bool = False):
    db = get_db()
    db.execute(
        """INSERT INTO webuntis_credentials (user_id, server, school, wt_username, wt_password, uses_user_key)
           VALUES (?,?,?,?,?,?)
           ON CONFLICT(user_id) DO UPDATE SET
               wt_username=excluded.wt_username,
               wt_password=excluded.wt_password,
               uses_user_key=excluded.uses_user_key,
               gespeichert_am=datetime('now')""",
        (user_id, "", "", wt_username, wt_password, int(uses_user_key)),
    )
    db.commit()


def delete_webuntis_credentials(user_id):
    db = get_db()
    db.execute("DELETE FROM webuntis_credentials WHERE user_id=?", (user_id,))
    db.commit()


# ── Nutzerspezifischer Verschlüsselungs-Salt ──────────────────────────────────

import os as _os


def get_wt_salt(user_id: int) -> bytes | None:
    row = get_db().execute(
        "SELECT wt_key_salt FROM users WHERE id=?", (user_id,)
    ).fetchone()
    if row and row["wt_key_salt"]:
        return bytes.fromhex(row["wt_key_salt"])
    return None


def get_or_create_wt_salt(user_id: int) -> bytes:
    salt = get_wt_salt(user_id)
    if salt is None:
        salt = _os.urandom(32)
        db = get_db()
        db.execute("UPDATE users SET wt_key_salt=? WHERE id=?", (salt.hex(), user_id))
        db.commit()
    return salt


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
