"""Einfaches DE/EN Übersetzungssystem."""

# ── Wochentage ────────────────────────────────────────────────────────────────
_WEEKDAYS_LONG = {
    "de": ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"],
    "en": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
}
_WEEKDAYS_SHORT = {
    "de": ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"],
    "en": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
}


def weekday_long(n: int, lang: str) -> str:
    return _WEEKDAYS_LONG.get(lang, _WEEKDAYS_LONG["de"])[n]


def weekday_short(n: int, lang: str) -> str:
    return _WEEKDAYS_SHORT.get(lang, _WEEKDAYS_SHORT["de"])[n]


def weekdays_long(lang: str) -> list[str]:
    """Montag–Freitag in der gewählten Sprache."""
    return _WEEKDAYS_LONG.get(lang, _WEEKDAYS_LONG["de"])[:5]


# ── Übersetzungsdict ──────────────────────────────────────────────────────────
TRANSLATIONS: dict[str, dict[str, str]] = {

    # ── Navigation ────────────────────────────────────────────────────────────
    "nav.dashboard":        {"de": "Dashboard",        "en": "Dashboard"},
    "nav.mein_stundenplan": {"de": "Mein Stundenplan", "en": "My Timetable"},
    "nav.pruefungen":       {"de": "Prüfungen",        "en": "Exams"},
    "nav.abwesenheit":      {"de": "Abwesenheit",      "en": "Absences"},
    "nav.noten":            {"de": "Noten",            "en": "Grades"},
    "nav.knowledgebase":    {"de": "Knowledgebase",    "en": "Knowledge Base"},
    "nav.benutzer":         {"de": "Benutzer",         "en": "Users"},
    "nav.einstellungen":    {"de": "Server-Config",    "en": "Server Config"},
    "nav.server_status":    {"de": "Server-Status",    "en": "Server Status"},

    # ── Base ──────────────────────────────────────────────────────────────────
    "base.online":       {"de": "Online",                 "en": "Online"},
    "base.admin_label":  {"de": "Admin",                  "en": "Admin"},
    "base.profil_title": {"de": "Profil & Einstellungen", "en": "Profile & Settings"},
    "base.logout_title": {"de": "Abmelden",               "en": "Log out"},
    "base.maintenance":  {
        "de": "Wartungsmodus aktiv – Normale Benutzer sehen eine Wartungsseite.",
        "en": "Maintenance mode active – Regular users see a maintenance page.",
    },

    # ── Login / Register ──────────────────────────────────────────────────────
    "auth.login_heading":    {"de": "Anmelden",                                   "en": "Sign in"},
    "auth.login_sub":        {"de": "Bitte melde dich mit deinen Zugangsdaten an.","en": "Please sign in with your credentials."},
    "auth.username":         {"de": "Benutzername",                               "en": "Username"},
    "auth.password":         {"de": "Passwort",                                   "en": "Password"},
    "auth.login_btn":        {"de": "Anmelden",                                   "en": "Sign in"},
    "auth.no_account":       {"de": "Noch kein Konto?",                           "en": "No account yet?"},
    "auth.register_link":    {"de": "Registrieren",                               "en": "Register"},
    "auth.register_heading": {"de": "Registrieren",                               "en": "Register"},
    "auth.register_sub":     {"de": "Erstelle dein Konto.",                       "en": "Create your account."},
    "auth.pw_hint":          {"de": "Mindestens 6 Zeichen.",                      "en": "At least 6 characters."},
    "auth.pw_repeat":        {"de": "Passwort wiederholen",                       "en": "Repeat password"},
    "auth.register_btn":     {"de": "Konto erstellen",                            "en": "Create account"},
    "auth.have_account":     {"de": "Bereits registriert?",                       "en": "Already have an account?"},
    "auth.login_link":       {"de": "Anmelden",                                   "en": "Sign in"},

    # ── Gemeinsam ─────────────────────────────────────────────────────────────
    "common.refresh":        {"de": "Aktualisieren",       "en": "Refresh"},
    "common.setup_webuntis": {"de": "WebUntis einrichten", "en": "Set up WebUntis"},
    "common.check_creds":    {"de": "Zugangsdaten prüfen", "en": "Check credentials"},
    "common.setup_now":      {"de": "Jetzt einrichten",    "en": "Set up now"},
    "common.all":            {"de": "Alle",                "en": "All"},
    "common.delete":         {"de": "Löschen",             "en": "Delete"},
    "common.save":           {"de": "Speichern",           "en": "Save"},
    "common.add":            {"de": "Eintragen",           "en": "Add"},
    "common.today":          {"de": "Heute",               "en": "Today"},
    "common.tomorrow":       {"de": "Morgen",              "en": "Tomorrow"},
    "common.wu_not_setup":   {
        "de": "WebUntis-Zugangsdaten noch nicht eingerichtet.",
        "en": "WebUntis credentials not set up yet.",
    },
    "common.wu_unreachable": {"de": "WebUntis nicht erreichbar:",   "en": "WebUntis unreachable:"},
    "common.manual":         {"de": "Manuell",                       "en": "Manual"},
    "common.note_add":       {"de": "Notiz anlegen",                 "en": "Add note"},
    "common.note_view":      {"de": "Notiz ansehen",                 "en": "View note"},
    "common.days_n":         {"de": "Tage",                          "en": "days"},
    "common.days_in_n":      {"de": "in",                            "en": "in"},
    "common.subject":        {"de": "Fach",                          "en": "Subject"},
    "common.type":           {"de": "Art",                           "en": "Type"},
    "common.date":           {"de": "Datum",                         "en": "Date"},
    "common.note_field":     {"de": "Notiz",                         "en": "Note"},
    "common.class":          {"de": "Klasse",                        "en": "Class"},
    "common.global_all":     {"de": "Global (alle)",                 "en": "Global (all)"},

    # ── Dashboard ─────────────────────────────────────────────────────────────
    "dash.page_title":      {"de": "Dashboard",                  "en": "Dashboard"},
    "dash.next_exam":       {"de": "Nächste Prüfung",            "en": "Next exam"},
    "dash.no_exam":         {"de": "Keine Prüfung",              "en": "No exam"},
    "dash.avg_total":       {"de": "Noten-Ø gesamt",             "en": "Overall grade avg."},
    "dash.open_ratings_s":  {"de": "Offene Bewertung",           "en": "Pending rating"},
    "dash.open_ratings_p":  {"de": "Offene Bewertungen",         "en": "Pending ratings"},
    "dash.exams_week_s":    {"de": "Prüfung diese Woche",        "en": "Exam this week"},
    "dash.exams_week_p":    {"de": "Prüfungen diese Woche",      "en": "Exams this week"},
    "dash.today_plan":      {"de": "Heutiger Stundenplan",       "en": "Today's timetable"},
    "dash.weekend":         {"de": "Wochenende",                 "en": "Weekend"},
    "dash.wu_not_setup":    {"de": "WebUntis nicht eingerichtet","en": "WebUntis not set up"},
    "dash.no_lessons":      {"de": "Kein Unterricht heute",      "en": "No lessons today"},
    "dash.next_exams":      {"de": "Nächste Prüfungen",          "en": "Upcoming exams"},
    "dash.last_grades":     {"de": "Letzte Noten",               "en": "Recent grades"},
    "dash.no_exams":        {"de": "Keine bevorstehenden Prüfungen", "en": "No upcoming exams"},
    "dash.no_grades":       {"de": "Noch keine Noten eingetragen",   "en": "No grades entered yet"},

    # ── Noten ─────────────────────────────────────────────────────────────────
    "noten.page_title":    {"de": "Noten",              "en": "Grades"},
    "noten.gesamt":        {"de": "Gesamtdurchschnitt", "en": "Overall Average"},
    "noten.aus":           {"de": "aus",                "en": "from"},
    "noten.note_singular": {"de": "Note",               "en": "grade"},
    "noten.note_plural":   {"de": "Noten",              "en": "grades"},
    "noten.in":            {"de": "in",                 "en": "in"},
    "noten.fach_singular": {"de": "Fach",               "en": "subject"},
    "noten.fach_plural":   {"de": "Fächern",            "en": "subjects"},
    "noten.fachuebersicht":{"de": "Fachübersicht",      "en": "Subject Overview"},
    "noten.datum":         {"de": "Datum",              "en": "Date"},
    "noten.art":           {"de": "Art",                "en": "Type"},
    "noten.meine_note":    {"de": "Meine Note",         "en": "My Grade"},
    "noten.klassen_avg":   {"de": "Klassen-Ø",         "en": "Class Avg."},
    "noten.beschreibung":  {"de": "Beschreibung",       "en": "Description"},
    "noten.offene_bew":    {"de": "Offene Bewertungen", "en": "Pending Ratings"},
    "noten.manuell":       {"de": "Note manuell eintragen", "en": "Add grade manually"},
    "noten.fach_label":    {"de": "Fach",               "en": "Subject"},
    "noten.fach_waehlen":  {"de": "Fach wählen…",      "en": "Choose subject…"},
    "noten.note_label":    {"de": "Note",               "en": "Grade"},
    "noten.datum_label":   {"de": "Datum",              "en": "Date"},
    "noten.eintragen":     {"de": "Eintragen",          "en": "Add"},
    "noten.leere_noten":   {"de": "Noch keine Noten eingetragen.", "en": "No grades entered yet."},
    "noten.sim_aktuell":   {"de": "Aktueller Schnitt",    "en": "Current Average"},
    "noten.sim_proj":      {"de": "Projizierter Schnitt", "en": "Projected Average"},
    "noten.sim_delta":     {"de": "Veränderung",          "en": "Change"},
    "noten.sim_sa_neu":    {"de": "SA-Ø (neu)",          "en": "SA Avg. (new)"},
    "noten.sim_ex_neu":    {"de": "Ex-Ø (neu)",          "en": "Ex Avg. (new)"},
    "noten.sim_add":       {"de": "Hinzufügen",          "en": "Add"},
    "noten.sim_reset":     {"de": "Zurücksetzen",        "en": "Reset"},

    # ── Prüfungen ─────────────────────────────────────────────────────────────
    "pruef.page_title":     {"de": "Prüfungen",              "en": "Exams"},
    "pruef.upcoming":       {"de": "Bevorstehende Prüfungen","en": "Upcoming Exams"},
    "pruef.past":           {"de": "Vergangene Prüfungen",   "en": "Past Exams"},
    "pruef.add":            {"de": "Prüfung eintragen",      "en": "Add exam"},
    "pruef.add_confirm":    {"de": "Eintrag löschen?",       "en": "Delete entry?"},
    "pruef.no_upcoming":    {"de": "Keine bevorstehenden Prüfungen.", "en": "No upcoming exams."},
    "pruef.heute_badge":    {"de": "Heute",    "en": "Today"},
    "pruef.morgen":         {"de": "Morgen",   "en": "Tomorrow"},
    "pruef.in_n_tagen":     {"de": "in {n} Tagen", "en": "in {n} days"},
    "pruef.notiz_add":      {"de": "Notiz anlegen",  "en": "Add note"},
    "pruef.notiz_view":     {"de": "Notiz ansehen",  "en": "View note"},
    "pruef.wu_unreachable": {"de": "WebUntis nicht erreichbar:", "en": "WebUntis unreachable:"},

    # ── Stundenplan ───────────────────────────────────────────────────────────
    "sp.page_title":     {"de": "Mein Stundenplan",   "en": "My Timetable"},
    "sp.not_setup":      {"de": "WebUntis-Zugangsdaten noch nicht eingerichtet.", "en": "WebUntis credentials not set up yet."},
    "sp.load_error":     {"de": "Stundenplan konnte nicht geladen werden:", "en": "Timetable could not be loaded:"},
    "sp.prev_week":      {"de": "Vorherige Woche",    "en": "Previous week"},
    "sp.next_week":      {"de": "Nächste Woche",      "en": "Next week"},
    "sp.source":         {"de": "Quelle: WebUntis",   "en": "Source: WebUntis"},
    "sp.add_ex":         {"de": "Ex",                 "en": "Ex"},
    "sp.cancelled":      {"de": "Entfällt",           "en": "Cancelled"},
    "sp.pause":          {"de": "Min Pause",           "en": "min break"},
    "sp.note_hint":      {"de": "Notiz (optional)",   "en": "Note (optional)"},
    "sp.delete_ex_confirm": {"de": "Ex-Eintrag löschen?", "en": "Delete Ex entry?"},
    "sp.absent_excused":    {"de": "entschuldigt",    "en": "excused"},
    "sp.absent_unexcused":  {"de": "unentschuldigt",  "en": "unexcused"},
    "sp.note_exists":       {"de": "Notiz vorhanden", "en": "Note exists"},
    "sp.abwesend":          {"de": "Abwesend",        "en": "Absent"},

    # ── Abwesenheit ───────────────────────────────────────────────────────────
    "abs.page_title":      {"de": "Abwesenheit",                    "en": "Absences"},
    "abs.not_setup":       {"de": "WebUntis-Zugangsdaten noch nicht eingerichtet.", "en": "WebUntis credentials not set up yet."},
    "abs.load_error":      {"de": "Abwesenheiten konnten nicht geladen werden:", "en": "Absences could not be loaded:"},
    "abs.total":           {"de": "Einträge gesamt",                "en": "Total entries"},
    "abs.excused":         {"de": "Entschuldigt",                   "en": "Excused"},
    "abs.unexcused":       {"de": "Unentschuldigt",                 "en": "Unexcused"},
    "abs.total_time":      {"de": "Gesamtzeit",                     "en": "Total time"},
    "abs.bafog":           {"de": "BAföG Status",                   "en": "BAföG Status"},
    "abs.bafog_hint":      {
        "de": "Automatisch berechnet – nicht offiziell. Abwesenheiten während Freistunden oder Fehlerfassungen können die Quote verfälschen.",
        "en": "Automatically calculated – unofficial. Absences during free periods or recording errors may skew the quota.",
    },
    "abs.until_today":     {"de": "Bis heute",   "en": "Until today"},
    "abs.school_year":     {"de": "Schuljahr",   "en": "School year"},
    "abs.by_reason":       {"de": "Aufschlüsselung nach Grund", "en": "Breakdown by reason"},
    "abs.all_entries":     {"de": "Alle Einträge",               "en": "All entries"},
    "abs.excused_badge":   {"de": "Entschuldigt",                "en": "Excused"},
    "abs.unexcused_badge": {"de": "Unentschuldigt",              "en": "Unexcused"},
    "abs.none":            {"de": "Keine Abwesenheiten in diesem Schuljahr.", "en": "No absences this school year."},
    "abs.soll_now":        {"de": "Soll-Stunden bis heute:",      "en": "Target hours until today:"},
    "abs.soll_year":       {"de": "Soll-Stunden Schuljahr:",      "en": "Target hours school year:"},
    "abs.loading":         {
        "de": "Soll-Stunden werden beim ersten Aufruf aus dem Stundenplan berechnet.\nSeite kurz neu laden.",
        "en": "Target hours will be calculated from the timetable on first load.\nPlease reload the page.",
    },

    # ── Profil ────────────────────────────────────────────────────────────────
    "profil.page_title":        {"de": "Mein Profil",              "en": "My Profile"},
    "profil.lang_section":      {"de": "Sprache",                  "en": "Language"},
    "profil.lang_label":        {"de": "Anzeigesprache",           "en": "Display language"},
    "profil.lang_de":           {"de": "Deutsch",                  "en": "German"},
    "profil.lang_en":           {"de": "Englisch",                 "en": "English"},
    "profil.lang_save":         {"de": "Sprache speichern",        "en": "Save language"},
    "profil.lang_saved":        {"de": "Sprache gespeichert.",     "en": "Language saved."},
    "profil.pw_section":        {"de": "Server-Passwort ändern",   "en": "Change Server Password"},
    "profil.pw_current":        {"de": "Aktuelles Passwort",       "en": "Current password"},
    "profil.pw_new":            {"de": "Neues Passwort",           "en": "New password"},
    "profil.pw_new_hint":       {"de": "min. 6 Zeichen",           "en": "min. 6 characters"},
    "profil.pw_confirm":        {"de": "Neues Passwort bestätigen","en": "Confirm new password"},
    "profil.pw_save":           {"de": "Passwort speichern",       "en": "Save password"},
    "profil.wu_section":        {"de": "WebUntis-Zugangsdaten",    "en": "WebUntis Credentials"},
    "profil.wu_not_configured": {
        "de": "WebUntis wurde noch nicht vom Administrator konfiguriert.",
        "en": "WebUntis has not been configured by the administrator yet.",
    },
    "profil.wu_setup_link":     {"de": "Jetzt einrichten →",       "en": "Set up now →"},
    "profil.wu_connected":      {"de": "Verbunden",                "en": "Connected"},
    "profil.wu_saved_on":       {"de": "Zugangsdaten gespeichert am", "en": "Credentials saved on"},
    "profil.wu_to_timetable":   {"de": "Zum Stundenplan →",        "en": "Go to timetable →"},
    "profil.wu_delete":         {"de": "Zugangsdaten löschen",     "en": "Delete credentials"},
    "profil.wu_delete_confirm": {"de": "WebUntis-Zugangsdaten wirklich löschen?", "en": "Really delete WebUntis credentials?"},
    "profil.wu_security_head":  {"de": "Sicherheitshinweis – bitte lesen", "en": "Security notice – please read"},
    "profil.wu_security_1": {
        "de": "Deine WebUntis-Zugangsdaten werden <strong>verschlüsselt</strong> auf diesem Server gespeichert.",
        "en": "Your WebUntis credentials are stored <strong>encrypted</strong> on this server.",
    },
    "profil.wu_security_2": {
        "de": "Der Administrator dieses Servers hat technisch die Möglichkeit, gespeicherte Daten einzusehen. Speichere deine Daten nur, wenn du dem Administrator <strong>vertraust</strong>.",
        "en": "The administrator of this server technically has access to stored data. Only save your credentials if you <strong>trust</strong> the administrator.",
    },
    "profil.wu_security_3": {
        "de": "Ändere dein WebUntis-Passwort, musst du es auch <strong>hier aktualisieren</strong>.",
        "en": "If you change your WebUntis password, you must also <strong>update it here</strong>.",
    },
    "profil.wu_security_4": {
        "de": "Dieser Server ist nur für den Einsatz im <strong>internen Schulnetz</strong> gedacht.",
        "en": "This server is intended for use within the <strong>internal school network</strong> only.",
    },
    "profil.wu_update":         {"de": "Zugangsdaten aktualisieren", "en": "Update credentials"},
    "profil.wu_setup":          {"de": "Zugangsdaten einrichten",    "en": "Set up credentials"},
    "profil.wu_username":       {"de": "WebUntis-Benutzername",      "en": "WebUntis username"},
    "profil.wu_password":       {"de": "WebUntis-Passwort",          "en": "WebUntis password"},
    "profil.wu_pw_placeholder": {"de": "Leer lassen = unverändert",  "en": "Leave blank = unchanged"},
    "profil.wu_checkbox": {
        "de": "Ich habe den Sicherheitshinweis gelesen und verstanden.",
        "en": "I have read and understood the security notice.",
    },
    "profil.wu_save_test":   {"de": "Speichern & Verbindung testen",    "en": "Save & test connection"},
    "profil.wu_update_test": {"de": "Aktualisieren & Verbindung testen","en": "Update & test connection"},

    # ── Admin Einstellungen ───────────────────────────────────────────────────
    "admin.default_lang":       {"de": "Standard-Sprache", "en": "Default Language"},
    "admin.default_lang_hint":  {
        "de": "Gilt für neue Benutzer und Nutzer ohne eigene Spracheinstellung.",
        "en": "Applies to new users and users without a personal language setting.",
    },
    "admin.default_lang_save":  {"de": "Sprache speichern",           "en": "Save language"},
    "admin.default_lang_saved": {"de": "Standard-Sprache gespeichert.","en": "Default language saved."},
    "admin.lang_de":            {"de": "Deutsch",  "en": "German"},
    "admin.lang_en":            {"de": "Englisch", "en": "English"},
}


def t(key: str, lang: str) -> str:
    entry = TRANSLATIONS.get(key)
    if not entry:
        return key
    return entry.get(lang) or entry.get("de") or key
