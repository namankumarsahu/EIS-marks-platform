# EIS Class 6 Marks Platform

A small slice of Euro International School's in-house platform: importing a
messy marks export from the school ERP into a clean relational model,
serving it through a Django REST Framework API, and showing it in a React
frontend. Built for the Platform Engineer screening assignment.

## Repo structure

```
eis-platform/
├── backend/                        Django + DRF API
│   ├── config/                     Project settings, root urls
│   ├── core/                       The one app: models, views, serializers
│   │   ├── models.py                Student, Subject, Mark
│   │   ├── services.py              Pure cleaning/averaging logic (import-agnostic, unit tested)
│   │   ├── serializers.py           DRF serializers for the three GET endpoints
│   │   ├── views.py                 StudentListView, StudentDetailView, SummaryView, MarkCorrectionView
│   │   ├── urls.py                  /api/ route table
│   │   ├── admin.py                 Django admin registration (handy for poking at data)
│   │   ├── management/commands/
│   │   │   └── import_marks.py      Re-runnable import command
│   │   └── tests/                   50 unit tests (services, models, views, corrections)
│   ├── scripts/
│   │   └── apply_corrections.py     Loops corrections.json through the API
│   ├── data/
│   │   ├── students_marks.csv       The raw export
│   │   └── corrections.json         The correction batch from the exam office
│   ├── requirements.txt
│   └── manage.py
│
├── frontend/                       React (Vite) app
│   ├── src/
│   │   ├── api/client.js            fetch wrappers for the four endpoints
│   │   ├── components/              SearchBox, NavBar
│   │   ├── pages/                   StudentsList, StudentDetail, Summary
│   │   ├── utils/format.js          Pure display-formatting logic (unit tested)
│   │   ├── tests/                   14 unit tests (utils, SearchBox, StudentsList)
│   │   ├── App.jsx, main.jsx
│   │   └── index.css
│   ├── vite.config.js              Dev-server proxy to the Django API, Vitest config
│   └── package.json
│
└── README.md                       This file
```

## Component-by-component: how it works

**Import** (`core/services.py` + `core/management/commands/import_marks.py`)
`services.py` holds pure functions with no Django/DB dependency — `normalize_name`,
`normalize_date`, `parse_marks`, `merge_duplicate_marks`, `average_of`, and
`read_and_clean_csv`, which reads the whole file and applies the dedup rule in
memory before anything touches the database. The management command is a thin
wrapper: it calls `read_and_clean_csv`, wipes existing `Student`/`Subject`/`Mark`
rows, and re-creates them from the cleaned data. Wiping first is what makes the
command **re-runnable** — running it twice, or running it after corrections
have been applied, always lands on the same clean baseline.

**Backend** (`core/models.py`, `serializers.py`, `views.py`)
Three tables: `Student`, `Subject` (kept as a real table rather than free text, so
the five valid subjects are enforceable), and `Mark` (one row per student/subject,
`marks_obtained` nullable to represent an absence). Averages and totals are never
stored — they're computed on read from whatever `Mark` rows currently exist, so a
correction is reflected everywhere immediately without a cache-invalidation step.

**Corrections endpoint** (`views.py::MarkCorrectionView`)
Validates shape with a serializer, then does three business checks by hand so the
400 response says exactly what's wrong: admission number must exist, subject must
be one of the five, marks must be an integer 0–100. Any failure returns 400 and
touches no data. A pass overwrites the `Mark` row (creating it if the student had
no row for that subject yet), including turning an absence into a real mark.

**Frontend** (`src/pages/*`, `src/api/client.js`)
Three pages, each independently fetching its own data on mount: `StudentsList`
(search box wired to `?search=`), `StudentDetail` (per-subject table, absences
rendered as "Absent" via `formatMark`), and `Summary` (subject averages + top
student). `api/client.js` is a thin fetch wrapper so the pages don't know about
URLs or status codes directly.

## Setup

### Prerequisites
- Python 3.10+
- Node 18+
- PostgreSQL (optional — SQLite is the default and needs no setup)

### Backend

```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

python manage.py migrate
python manage.py import_marks data/students_marks.csv   # see below
python manage.py runserver   # http://127.0.0.1:8000
```

To use Postgres instead of the bundled SQLite, set before running the commands
above: `DB_ENGINE=postgres DB_NAME=... DB_USER=... DB_PASSWORD=... DB_HOST=... DB_PORT=...`.

### Frontend

```bash
cd frontend
npm install
npm run dev   # http://localhost:5173, proxies /api to the Django server
```

### Running the import

```bash
python manage.py import_marks data/students_marks.csv
```

This is **re-runnable**: it deletes all existing `Student`/`Subject`/`Mark` rows
and rebuilds them from the CSV every time, so you can always get back to a clean,
pre-corrections state by running it again.

### Applying corrections

With the backend server running:

```bash
cd backend
python scripts/apply_corrections.py data/corrections.json http://127.0.0.1:8000/api
```

This POSTs each record in `corrections.json` to `/api/marks/corrections/` and
prints the result. In the provided batch, 6 records are valid and 3 are rejected
(an out-of-range mark, an admission number that doesn't exist, and a subject that
isn't one of the five known ones).

### Running the tests

```bash
# backend — 50 tests
cd backend && python manage.py test core -v 2

# frontend — 14 tests
cd frontend && npm test
```

## Schema

```
Student
  admission_no   varchar, unique   — business key from the ERP
  name           varchar           — Title Case, trimmed, single-spaced
  student_class  varchar
  section        varchar
  date_of_birth  date              — normalized to YYYY-MM-DD

Subject
  name           varchar, unique   — one of: English, Hindi, Maths, Science, Social Science

Mark
  student        FK -> Student
  subject        FK -> Subject
  marks_obtained integer, nullable — null means Absent, never 0
  max_marks      integer, default 100
  unique_together (student, subject)
```

Students and marks are in separate tables (a student has many marks, one per
subject) so a correction is a single-row update and averages/totals are always
computed from current data rather than a denormalized, cacheable field.

## Data-cleaning decisions worth calling out

- **Duplicate resolution**: when two rows share `(admission_no, subject)`, a
  real mark always beats a blank one (a blank carries no information to
  "disagree" with); if both have marks, the higher one wins, per the spec.
- **Date formats**: the CSV actually contains `DD-MM-YYYY` and `DD-Mon-YY`
  (not quite the three examples in the brief), so `normalize_date` handles
  both of those plus the slash and `DD-Mon-YYYY` variants for robustness.
- **Absences are never coerced to 0** — not in storage, not in `average_of`,
  not in the frontend's `formatMark`. This was checked at each layer since
  it's easy to accidentally let a `None` become falsy-zero in aggregation.

## What I'd do next with more time

- Add auth/permissions to the API (currently fully open, fine for a
  screening assignment but not for a real deployment).
- Move the CSV path and API base URL into environment variables / a
  settings module rather than defaults baked into the command and script.
- Add pagination to `/api/students/` — fine at 47 rows, not at real scale.
- Add a small integration test that runs the actual `import_marks` command
  against the shipped CSV and asserts on a few known post-import values,
  rather than only unit-testing the pieces.
- Frontend: loading skeletons instead of plain "Loading...", and a debounce
  on the search box so every keystroke doesn't trigger a fetch.
- A `docker-compose.yml` with Postgres + backend + frontend for a
  one-command spin-up.
