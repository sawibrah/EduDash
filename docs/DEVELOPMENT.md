# EduDash / EduPortal — Developer guide

This document complements [README.md](../README.md) (product overview) and [QUICK_START.md](../QUICK_START.md) (local run). It focuses on how the code is organized, how to test it, and how to work with translations and optional features.

---

## 1. Running the app locally

```powershell
cd path\to\EduDash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python .\main.py
```

Open **http://127.0.0.1:5000** (or `http://localhost:5000`).

- **SQLite (default):** `instance/edudash.db` is created automatically if missing.
- **Another database:** set `DATABASE_URL` (SQLAlchemy URI) before starting.

---

## 2. Environment variables

| Variable | Purpose |
|----------|---------|
| `SESSION_SECRET` | Flask session signing key. **Required in production.** If unset, a dev-only default is used (see `app.py`). |
| `DATABASE_URL` | Overrides default SQLite path. |
| `GOOGLE_OAUTH_CLIENT_ID` / `GOOGLE_OAUTH_CLIENT_SECRET` | Optional Google sign-in; see [README.md](../README.md) (Security) for redirect URI. |

---

## 3. Project layout and blueprints

Routes are split into Flask **blueprints** (registered from `blueprints/__init__.py` via `register_blueprints(app)` in `app.py`):

| Blueprint | Prefix / scope | Role |
|-----------|------------------|------|
| `auth` | `/login`, `/register`, `/logout`, `/change-password` | Public / authenticated |
| `main` | `/`, `/courses`, `/test-login`, language routes | Mixed |
| `admin` | `/admin/...` | Admin |
| `api` | `/api/...` | JSON (e.g. available courses) |
| `courses` | `/course/<id>/...` | Shared slides / downloads |
| `student` | `/student/...`, `/quiz/...` | Student flows |
| `teacher` | `/teacher/...` | Teacher flows |

Legacy `routes.py` is intentionally minimal; do not reintroduce large monolithic route files.

**URL generation in templates:** use blueprint endpoints, e.g. `url_for('auth.login')`, `url_for('student.student_dashboard')`, `url_for('teacher.view_course', course_id=course.id)`.

---

## 4. Automated tests

Dependencies include **pytest** (`requirements.txt`).

```powershell
pip install -r requirements.txt
python -m pytest tests/ -v
```

- Tests use a **temporary SQLite file** (see `tests/conftest.py`) and disable CSRF for the client.
- Covers login, enrollment POST, and exam JSON submit.

---

## 5. Internationalization (Babel)

- **Config:** [babel.cfg](../babel.cfg) — Jinja uses `jinja2.ext.i18n` (avoids extract issues with `autoescape`).
- **Catalogs:** `translations/<locale>/LC_MESSAGES/messages.po` and compiled `.mo` files.

**Extract strings** (from repo root; adjust venv folder names to match yours):

```powershell
pybabel extract -F babel.cfg -k _ -k gettext -k ngettext `
  --ignore-dirs=myenv --ignore-dirs=venv --ignore-dirs=.venv `
  --ignore-dirs=__pycache__ --ignore-dirs=tests --ignore-dirs=scripts `
  -o messages.pot .
```

Then update locale PO files and compile:

```powershell
pybabel update -i messages.pot -d translations
pybabel compile -d translations
```

**French gap check** (lists `messages.po` entries where `msgstr` is empty or still identical to `msgid`, plus any fuzzy flags):

```powershell
python scripts/fr_translation_audit.py
python scripts/fr_translation_audit.py --write translations/audit_fr_last_run.txt
```

---

## 6. Optional PDF generation (WeasyPrint)

Core `requirements.txt` does **not** install WeasyPrint (native dependencies vary by OS).

```powershell
pip install -r requirements-pdf.txt
```

If WeasyPrint is missing, teacher PDF generation and student course PDF download show a flash message instead of crashing.

**uv / pyproject:** optional PDF deps are under `[project.optional-dependencies] pdf` in [pyproject.toml](../pyproject.toml):

```powershell
uv sync --extra pdf
```

---

## 7. Google OAuth (optional)

Implemented in [gmail_auth.py](../gmail_auth.py), initialized from `app.py` when credentials are set. Blueprint is mounted under **`/oauth/google/`** so it does not replace the form login at `/login`.

---

## 8. Git workflow (feature branches)

- Day-to-day work can live on a branch such as **`tony-branch`**; push with `git push origin tony-branch`.
- **`main`** only changes when a maintainer merges (e.g. via pull request). Pushing a feature branch does not update `main` by itself.

---

## 9. End-user roles (student / teacher / admin)

See **[docs/USERS_AND_ROLES.md](USERS_AND_ROLES.md)** for what each role can do, demo accounts, and how to bootstrap the first admin.

---

## 10. Where to look next

| Topic | File / folder |
|--------|----------------|
| App factory / DB / CSRF / Babel | `app.py` |
| Login decorators | `auth.py` |
| Models | `models.py` |
| WTForms | `forms.py` |
| Blueprint registration | `blueprints/__init__.py` |
| Fix history (narrative) | [FIXES_SUMMARY.md](../FIXES_SUMMARY.md) |
| Demo users (`demo_student` / `demo_teacher`) | `scripts/seed_demo_users.py` |
