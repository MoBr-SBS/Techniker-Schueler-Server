# Techniker-Schüler-Server

An internal web portal for vocational school students — displays timetables, exams, grades, and absences from WebUntis, extended by manual entries and a shared knowledge base.

---

## Features

| Section | Description |
|---|---|
| **Dashboard** | Overview: upcoming exams, timetable highlight, quick access |
| **Timetable** | Weekly view from WebUntis, automatically cached |
| **Exams** | WebUntis exams + manual entries (SA / Ex) with notes |
| **Grades** | Grade management per subject with class average |
| **Absences** | BAföG-relevant missed minutes calculation |
| **Knowledgebase** | Markdown pages with categories; admins manage, users read |
| **Profile** | WebUntis credentials, change password |
| **Admin** | User management, server config, server status, maintenance mode |

---

## Requirements

- Python 3.11+
- Access to a WebUntis instance (server and school are configured by an admin)

---

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/MoBr-SBS/Techniker-Schueler-Server
cd Techniker-Schueler-Server

# 2. Create a virtual environment and install dependencies
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install flask werkzeug cryptography markdown python-dotenv

# 3. Set environment variables
cp .env.example .env             # then edit .env (see below)

# 4. Start the server
python app.py
```

The server will be available at `http://localhost:8080`.

---

## Configuration (.env)

```env
SECRET_KEY=<long-random-string>
FERNET_KEY=<fernet-key>          # Legacy encryption, migrated automatically
SERVER_NAME_DISPLAY=MyServer     # Display name shown in the UI
DEBUG=false                      # true for development only
```

Generate a new Fernet key:

```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

---

## First Start

On the first start, an admin account is created automatically:

| Field | Value |
|---|---|
| Username | `admin` |
| Password | `admin123` |

**Change the password immediately!**

Afterwards, go to **Admin → Server-Config** to set the WebUntis server and school.

---

## Project Structure

```
.
├── app.py                  # Entry point
├── core/
│   ├── server.py           # App factory, blueprints, before_request
│   ├── database.py         # SQLite schema and migrations
│   ├── nav.py              # Navigation items
│   ├── queries.py          # All database queries
│   ├── config.py           # Flask config
│   ├── encryption.py       # Per-user AES encryption
│   ├── webuntis_client.py  # WebUntis API client with file cache
│   └── exam_utils.py       # Exam logic
├── routes/                 # Flask blueprints (one file per page)
├── templates/              # Jinja2 templates
├── static/
│   ├── css/main.css
│   └── js/main.js
├── cache/                  # WebUntis cache (created automatically)
├── static/uploads/         # Logo, favicon (created automatically)
└── school.db               # SQLite database (created automatically)
```

---

## User Roles

| Role | Description |
|---|---|
| `user` | Regular student — reads data, requires WebUntis login |
| `trusted` | Can create exams and entries for all users |
| `admin` | Full access, user management, server config |

Non-admin users are prompted to enter their WebUntis credentials on their very first login before they can access the portal.

---

## Security Notes

- WebUntis passwords are stored encrypted using a per-user key (PBKDF2 + AES).
- The key is derived from the user's app password — only the user themselves can decrypt it.
- This server is intended for use on an **internal school network**, not the public internet.
- Never use `DEBUG=true` in production.
