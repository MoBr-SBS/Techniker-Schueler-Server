"""
core/nav.py – Zentrale Navigationsliste.

Jede neue Seite trägt sich hier ein.
Das Template liest diese Liste automatisch aus.
"""

NAV_ITEMS = [
    {"id": "dashboard",        "label": "Dashboard",        "icon": "grid",           "url": "/"},
    {"id": "mein_stundenplan", "label": "Mein Stundenplan", "icon": "calendar-check",  "url": "/mein-stundenplan"},
    {"id": "pruefungen",      "label": "Prüfungen",        "icon": "clipboard-list",  "url": "/pruefungen"},
    {"id": "noten",            "label": "Noten",            "icon": "award",          "url": "/noten"},
    {"id": "stats",            "label": "Statistiken",      "icon": "bar-chart-2",    "url": "/stats"},
    {"id": "settings",         "label": "Einstellungen",    "icon": "settings",       "url": "/settings"},
    {"id": "benutzer",         "label": "Benutzer",         "icon": "users",          "url": "/admin/benutzer",      "admin_only": True},
    {"id": "einstellungen",    "label": "Server-Config",    "icon": "sliders",         "url": "/admin/einstellungen", "admin_only": True},
]