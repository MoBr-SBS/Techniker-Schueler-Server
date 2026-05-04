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

def get_all_noten():
    return get_db().execute(
        "SELECT * FROM noten ORDER BY fach, datum DESC"
    ).fetchall()


def add_note(fach, note, datum, beschreibung):
    db = get_db()
    db.execute(
        "INSERT INTO noten (fach, note, datum, beschreibung) VALUES (?,?,?,?)",
        (fach, note, datum, beschreibung),
    )
    db.commit()


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


# ── WebUntis-Zugangsdaten ─────────────────────────────────────────────────────

def get_webuntis_credentials(user_id):
    return get_db().execute(
        "SELECT * FROM webuntis_credentials WHERE user_id=?", (user_id,)
    ).fetchone()


def save_webuntis_credentials(user_id, server, school, wt_username, wt_password):
    db = get_db()
    db.execute(
        """INSERT INTO webuntis_credentials (user_id, server, school, wt_username, wt_password)
           VALUES (?,?,?,?,?)
           ON CONFLICT(user_id) DO UPDATE SET
               server=excluded.server,
               school=excluded.school,
               wt_username=excluded.wt_username,
               wt_password=excluded.wt_password,
               gespeichert_am=datetime('now')""",
        (user_id, server, school, wt_username, wt_password),
    )
    db.commit()


def delete_webuntis_credentials(user_id):
    db = get_db()
    db.execute("DELETE FROM webuntis_credentials WHERE user_id=?", (user_id,))
    db.commit()
