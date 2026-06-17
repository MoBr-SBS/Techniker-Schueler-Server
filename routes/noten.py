import datetime
from flask import Blueprint, render_template, request, redirect, url_for, current_app, session
from core import queries
from core.nav import NAV_ITEMS
from core.exam_utils import load_webuntis_exams, load_manual_exams

bp = Blueprint("noten", __name__)


def _grade_color(avg):
    if avg <= 2.0: return "green"
    if avg <= 3.0: return "blue"
    if avg <= 4.0: return "orange"
    return "red"


def _weighted_avg(noten_list):
    """(2 * Ø_SA + Ø_Ex) / 3 — fällt eine Gruppe weg, gilt nur die vorhandene."""
    sa = [n["note"] for n in noten_list if n.get("art") == "SA"]
    ex = [n["note"] for n in noten_list if n.get("art") != "SA"]
    if sa and ex:
        return round((2 * (sum(sa) / len(sa)) + (sum(ex) / len(ex))) / 3, 2)
    if sa:
        return round(sum(sa) / len(sa), 2)
    return round(sum(ex) / len(ex), 2)


def _normalize_art(raw: str) -> str:
    """Normalisiert SA-Varianten ('SA', 'Schulaufgabe') → 'SA', alles andere → 'Ex'."""
    return "SA" if raw.strip() in ("SA", "Schulaufgabe") else "Ex"


def _parse_note(raw):
    note = float(raw.replace(",", "."))
    if not (1.0 <= note <= 6.0):
        raise ValueError
    return note


@bp.route("/noten")
def index():
    user_id = session["user_id"]

    # ── Eigene Noten laden ────────────────────────────────────────────────────
    subjects = {}
    for row in queries.get_noten_for_user(user_id):
        f = row["fach"]
        if f not in subjects:
            subjects[f] = []
        subjects[f].append(dict(row))

    # ── Klassendurchschnitt pro exam_key ──────────────────────────────────────
    all_exam_keys = {
        n["exam_key"]
        for notes in subjects.values()
        for n in notes
        if n.get("exam_key")
    }
    class_avgs = queries.get_class_avgs_by_exam_keys(all_exam_keys)

    # ── Fach-Zusammenfassungen ────────────────────────────────────────────────
    summaries = []
    for fach, noten_list in subjects.items():
        for n in noten_list:
            ca = class_avgs.get(n.get("exam_key") or "")
            n["class_avg"]   = ca["avg"]   if ca and ca["count"] >= 2 else None
            n["class_count"] = ca["count"] if ca and ca["count"] >= 2 else None

        avg = _weighted_avg(noten_list)

        sa_notes = [n for n in noten_list if n.get("art") == "SA"]
        ex_notes = [n for n in noten_list if n.get("art") != "SA"]
        avg_sa = round(sum(n["note"] for n in sa_notes) / len(sa_notes), 2) if sa_notes else None
        avg_ex = round(sum(n["note"] for n in ex_notes) / len(ex_notes), 2) if ex_notes else None

        summaries.append({
            "fach":    fach,
            "noten":   noten_list,
            "schnitt": avg,
            "avg_sa":  avg_sa,
            "avg_ex":  avg_ex,
            "color":   _grade_color(avg),
            "count":   len(noten_list),
        })
    summaries.sort(key=lambda x: x["fach"])

    # ── Gesamtschnitt = Ø der Fachschnitte ───────────────────────────────────
    gesamt_schnitt = None
    if summaries:
        gesamt_schnitt = round(sum(s["schnitt"] for s in summaries) / len(summaries), 2)

    # ── Vergangene Prüfungen für offene Bewertungen ───────────────────────────
    today = datetime.date.today()
    wu_exams, _warning, _wt_configured = load_webuntis_exams(user_id, today)
    manual_exams = load_manual_exams(today, user_id=user_id)

    all_past = [e for e in wu_exams + manual_exams if e["days"] < 0]
    all_past.sort(key=lambda e: e["datum"], reverse=True)

    graded_keys   = queries.get_graded_exam_keys_for_user(user_id)
    pending_exams = [e for e in all_past if e["exam_key"] not in graded_keys]

    user = queries.get_user_by_id(user_id)
    klasse_faecher = (
        queries.get_faecher_fuer_klasse(user["klasse_id"])
        if user and user["klasse_id"] else []
    )

    return render_template(
        "noten.html",
        page_id="noten",
        nav=NAV_ITEMS,
        summaries=summaries,
        gesamt_schnitt=gesamt_schnitt,
        today=today.isoformat(),
        pending_exams=pending_exams,
        klasse_faecher=klasse_faecher,
    )


@bp.route("/noten/add", methods=["POST"])
def add():
    fach         = request.form["fach"].strip()
    datum        = request.form["datum"]
    beschreibung = request.form.get("beschreibung", "").strip()
    exam_key     = request.form.get("exam_key", "").strip() or None
    art = _normalize_art(request.form.get("art", ""))
    try:
        note = _parse_note(request.form["note"])
    except (ValueError, KeyError):
        return redirect(url_for("noten.index"))
    if fach and datum:
        queries.add_note(fach, note, datum, beschreibung, exam_key, session["user_id"], art)
    return redirect(url_for("noten.index"))


@bp.route("/noten/update/<int:note_id>", methods=["POST"])
def update(note_id):
    try:
        note = _parse_note(request.form["note"])
    except (ValueError, KeyError):
        return redirect(url_for("noten.index"))
    beschreibung = request.form.get("beschreibung", "").strip()
    art          = _normalize_art(request.form.get("art", ""))
    queries.update_note(note_id, note, beschreibung, art)
    return redirect(url_for("noten.index"))


@bp.route("/noten/delete/<int:note_id>", methods=["POST"])
def delete(note_id):
    queries.delete_note(note_id)
    return redirect(url_for("noten.index"))
