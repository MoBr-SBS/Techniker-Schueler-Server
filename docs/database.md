# Database Documentation

The application uses a single **SQLite** database file (`school.db`, created automatically on first
start). There is no ORM — all access goes through raw SQL in [`core/database.py`](../core/database.py)
(schema + migrations) and [`core/queries.py`](../core/queries.py) (all queries used by the routes).

Foreign keys are enforced at the connection level (`PRAGMA foreign_keys = ON`, see
[`core/database.py:12`](../core/database.py)), but several relationships between tables are **soft
links** (matched by value, not declared as `FOREIGN KEY`) — these are called out explicitly below.

---

## Entity-Relationship Diagram

```mermaid
erDiagram
    USERS ||--o| WEBUNTIS_CREDENTIALS : "has (1:1, cascade delete)"
    USERS ||--o{ NOTEN : "owns (nullable FK)"
    TESTS ||--o{ LERNMATERIAL : "contains (cascade delete)"
    KB_CATEGORIES ||--o{ KB_PAGES : "groups (SET NULL on delete)"
    USERS }o..o{ PRUEFUNGEN : "scoped by klasse_id (soft link)"
    USERS }o..o{ KLASSE_FAECHER : "klasse_id (soft link)"
    USERS }o..o{ FACH_VERBINDUNGEN : "klasse_id (soft link)"
    NOTEN }o..o| EXAM_NOTES : "exam_key (soft link, string match)"

    USERS {
        int id PK
        text username UK
        text password_hash
        int is_admin
        text role "user | trusted | admin"
        text erstellt_am
        text wt_key_salt "hex, for per-user encryption key"
        int klasse_id "cached from WebUntis"
        text klasse_name "cached from WebUntis"
        text language "UI language override, nullable"
    }

    WEBUNTIS_CREDENTIALS {
        int user_id PK_FK
        text server "legacy column, unused (always empty)"
        text school "legacy column, unused (always empty)"
        text wt_username
        text wt_password "Fernet-encrypted"
        text gespeichert_am
        int uses_user_key "0=legacy FERNET_KEY, 1=per-user key"
    }

    NOTEN {
        int id PK
        text fach
        real note
        text datum
        text beschreibung
        text erstellt_am
        text exam_key "nullable, links to WebUntis exam"
        real klassen_schnitt "nullable, class-average snapshot"
        int user_id FK "nullable"
        text art "SA | Ex"
    }

    EXAM_NOTES {
        text exam_key PK "format: {fach}_{YYYYMMDD}"
        text content "Markdown"
        text updated_at
        text updated_by
    }

    PRUEFUNGEN {
        int id PK
        text fach
        text art "CHECK: SA | Ex"
        text datum
        text notiz
        text erstellt_am
        int klasse_id "nullable, soft link to users.klasse_id"
    }

    KLASSE_FAECHER {
        int klasse_id PK
        text fach PK
    }

    FACH_VERBINDUNGEN {
        int gruppe_id PK
        int klasse_id PK
        text fach
    }

    KB_CATEGORIES {
        int id PK
        text name
        int sort_order
        int visible
    }

    KB_PAGES {
        int id PK
        int category_id FK "nullable, ON DELETE SET NULL"
        text title
        text content "Markdown"
        int visible
        int sort_order
        text created_at
        text updated_at
        text updated_by
    }

    TESTS {
        int id PK
        text fach
        text datum
        text beschreibung
        text erstellt_am
    }

    LERNMATERIAL {
        int id PK
        int test_id FK "ON DELETE CASCADE"
        text inhalt
        int reihenfolge
    }

    STUNDENPLAN {
        int id PK
        int wochentag "0-4 = Mon-Fri"
        int stunde
        text fach
        text lehrer
        text raum
    }

    APP_SETTINGS {
        text key PK
        text value
    }
```

> GitHub, GitLab and most modern Markdown viewers render the `mermaid` block above natively. If your
> viewer doesn't, paste the block into the [Mermaid Live Editor](https://mermaid.live) to see the diagram.

---

## Tables

### `users`

The central identity table. Every login, permission check, and per-user cache key refers back to this.

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK | Autoincrement |
| `username` | TEXT | `UNIQUE`, `NOT NULL` |
| `password_hash` | TEXT | Werkzeug `generate_password_hash` output |
| `is_admin` | INTEGER | Legacy boolean flag (0/1). Superseded by `role`, kept for compatibility |
| `role` | TEXT | `'user'` \| `'trusted'` \| `'admin'`, default `'user'` |
| `erstellt_am` | TEXT | Creation timestamp |
| `wt_key_salt` | TEXT | Hex-encoded random salt (32 bytes), generated lazily on first login. Used to derive the per-user WebUntis encryption key — see [webuntis-api.md](webuntis-api.md#credential-encryption) |
| `klasse_id` | INTEGER | WebUntis class ID, cached after the user's first successful WebUntis login |
| `klasse_name` | TEXT | WebUntis class name, cached alongside `klasse_id` |
| `language` | TEXT | Per-user UI language override (`de`/`en`), nullable — falls back to the server default |

### `webuntis_credentials`

Stores each user's WebUntis login, encrypted. One row per user (`user_id` is both primary key and
foreign key), enforced 1:1 by using `user_id` as the PK.

| Column | Type | Notes |
|---|---|---|
| `user_id` | INTEGER PK, FK → `users.id` | `ON DELETE CASCADE` |
| `server` | TEXT | Legacy column, always stored as `''` — actual server is read from `app_settings` (global, admin-configured) |
| `school` | TEXT | Legacy column, always stored as `''` — same as above |
| `wt_username` | TEXT | Plaintext WebUntis username |
| `wt_password` | TEXT | Fernet ciphertext of the WebUntis password |
| `gespeichert_am` | TEXT | Last-saved timestamp |
| `uses_user_key` | INTEGER | `0` = still encrypted with the legacy global `FERNET_KEY` (pending migration), `1` = encrypted with the user's derived key |

See [webuntis-api.md](webuntis-api.md) for the full encryption/migration flow.

### `noten` (grades)

Grades a user has entered manually, optionally linked to a WebUntis exam via `exam_key`.

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK | |
| `fach` | TEXT | Subject name |
| `note` | REAL | Grade value |
| `datum` | TEXT | ISO date |
| `beschreibung` | TEXT | Free-text note |
| `erstellt_am` | TEXT | |
| `exam_key` | TEXT | Nullable. Soft link to `exam_notes.exam_key` and to the WebUntis exam list, format `{fach}_{YYYYMMDD}` (see `queries.make_exam_key`) |
| `klassen_schnitt` | REAL | Nullable snapshot of the class average at entry time |
| `user_id` | INTEGER FK → `users.id` | Nullable (older rows predate per-user grades) |
| `art` | TEXT | `'SA'` (Schulaufgabe) or `'Ex'` (Exercise/short test), default `'Ex'` |

Class averages are computed on the fly by `queries.get_class_avgs_by_exam_keys()`, which groups all
users' `noten` rows sharing the same `exam_key`.

### `exam_notes`

Shared notes attached to a specific exam (identified by `exam_key`, not a foreign key — any string
matching the `{fach}_{YYYYMMDD}` convention works, whether the exam came from WebUntis or was entered
manually in `pruefungen`).

| Column | Type | Notes |
|---|---|---|
| `exam_key` | TEXT PK | |
| `content` | TEXT | Markdown |
| `updated_at` | TEXT | |
| `updated_by` | TEXT | Username, not a FK |

### `pruefungen` (manually entered exams)

Manual exam entries (created by `trusted`/`admin` users), independent from WebUntis' own exam data.

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK | |
| `fach` | TEXT | |
| `art` | TEXT | `CHECK (art IN ('SA','Ex'))` |
| `datum` | TEXT | |
| `notiz` | TEXT | |
| `erstellt_am` | TEXT | |
| `klasse_id` | INTEGER | Nullable soft link to `users.klasse_id` — scopes the exam to one class; `NULL` = visible to all classes |

### `klasse_faecher` (known subjects per class)

Populated automatically from each user's WebUntis timetable the first time they log in
(`auth.webuntis_setup`, see [webuntis-api.md](webuntis-api.md)). Used to populate subject dropdowns
per class in the admin UI.

| Column | Type | Notes |
|---|---|---|
| `klasse_id` | INTEGER PK (composite) | Soft link to `users.klasse_id` |
| `fach` | TEXT PK (composite) | |

### `fach_verbindungen` (cross-class subject links)

Because WebUntis subject names can differ between classes for what is conceptually the same subject,
admins can group them under a shared `gruppe_id` (via **Admin → Verbindungen**) so class-average
calculations can span classes.

| Column | Type | Notes |
|---|---|---|
| `gruppe_id` | INTEGER PK (composite) | Arbitrary group identifier, assigned as `MAX(gruppe_id)+1` |
| `klasse_id` | INTEGER PK (composite) | Soft link to `users.klasse_id` |
| `fach` | TEXT | Subject name as used in that specific class |

### `kb_categories` / `kb_pages` (knowledge base)

A simple Markdown-based CMS. Categories group pages; deleting a category does not delete its pages
(`ON DELETE SET NULL`).

**`kb_categories`**

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK | |
| `name` | TEXT | |
| `sort_order` | INTEGER | Manual ordering |
| `visible` | INTEGER | Hide category (and effectively its pages) from non-admins |

**`kb_pages`**

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK | |
| `category_id` | INTEGER FK → `kb_categories.id` | `ON DELETE SET NULL` |
| `title` | TEXT | |
| `content` | TEXT | Markdown, rendered with the `markdown` package |
| `visible` | INTEGER | |
| `sort_order` | INTEGER | |
| `created_at` / `updated_at` | TEXT | |
| `updated_by` | TEXT | Username, not a FK |

### `tests` / `lernmaterial` (legacy manual tests)

An older, class-wide "test + study material" feature, largely superseded by `pruefungen` +
WebUntis exams but still present in the schema and reachable in the UI.

**`tests`**

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK | |
| `fach` | TEXT | |
| `datum` | TEXT | |
| `beschreibung` | TEXT | |
| `erstellt_am` | TEXT | |

**`lernmaterial`**

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK | |
| `test_id` | INTEGER FK → `tests.id` | `ON DELETE CASCADE` |
| `inhalt` | TEXT | Study material content |
| `reihenfolge` | INTEGER | Sort order within the test |

### `stundenplan` (legacy manual timetable)

A manually maintained fallback timetable, predating the WebUntis integration. Still in the schema
but not actively used once WebUntis credentials are configured.

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK | |
| `wochentag` | INTEGER | `0`–`4` = Monday–Friday |
| `stunde` | INTEGER | Period number |
| `fach` | TEXT | |
| `lehrer` | TEXT | |
| `raum` | TEXT | |

### `app_settings`

Generic global key/value store for server-wide configuration, edited from **Admin → Settings**.

| Column | Type | Notes |
|---|---|---|
| `key` | TEXT PK | e.g. `webuntis_server`, `webuntis_school`, `server_name`, `logo_filename`, `favicon_filename`, `allow_registration`, `default_language` |
| `value` | TEXT | |

---

## Migrations

There is no migration framework (e.g. Alembic). `core/database.py::init_db()` runs on every app
start and:

1. Creates all tables with `CREATE TABLE IF NOT EXISTS`.
2. Runs a set of idempotent, hand-written migrations guarded by `PRAGMA table_info(...)` checks
   (e.g. adding `wt_key_salt`, `role`, `klasse_id`, `art`, the knowledge-base tables) — each one only
   runs if the column/table is missing.
3. Seeds a default `admin` / `admin123` account if the `users` table is empty.

This means the schema evolves by appending new `ALTER TABLE` migration blocks to `init_db()`, not by
versioned migration files.
