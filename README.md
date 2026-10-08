# College Internship Application & Offer Tracking Portal

A full-stack web portal for college students to track internship applications, interviews,
and offers, and for the Training & Placement / Internship Cell to manage students,
internship opportunities, and placement statistics.

## 1. Project Description

Students can create a profile, browse internship opportunities posted by the Internship
Cell, apply, track every application through a defined status pipeline (Interested →
Applied → ... → Accepted), log interview rounds, and record/accept/decline offers.
Admins get a dashboard with charts, student/application/internship/offer management
screens, and CSV export.

## 2. Features

**Student**
- Registration & login (hashed passwords), profile with academic info, skills, resume (PDF) upload
- Dashboard with summary cards, recent applications, upcoming-interview widget, status chart
- Browse/search/filter internship opportunities, apply directly (deadline-enforced)
- Add/edit/delete applications manually, update status through an enforced status flow
- Interview tracking per application (round, type, date, interviewer, result)
- Offer tracking (create when "Offer Received", accept/decline with confirmation)
- Chronological activity/history timeline per application

**Admin**
- Dashboard: totals + 4 charts (status, top companies, work modes, monthly applications)
- Student directory with search/filter by department & year, per-student detail view
- Application management: search/filter (student, company, status, department, date), pagination, status override
- Internship CRUD, auto-expiry after deadline, manual "close", per-internship applicant list
- Offer directory with filters
- CSV export (Applications / Students / Offers)

## 3. Technology Stack

- Backend: Python 3, Flask
- Frontend: HTML5, CSS3, vanilla JavaScript, Bootstrap 5, Bootstrap Icons, Chart.js
- Database: SQLite via Flask-SQLAlchemy (SQLAlchemy ORM)
- Templating: Jinja2
- Auth/Security: Flask sessions, Werkzeug password hashing, Flask-WTF CSRF protection

No React, Tailwind, Node.js, or MongoDB is used anywhere in this project.

## 4. Folder Structure

```
internship_portal/
├── app.py                  # Flask application factory
├── config.py                # Configuration (env-driven)
├── extensions.py             # Shared SQLAlchemy instance
├── init_db.py                # DB init + seed script
├── requirements.txt
├── .env.example
├── README.md
│
├── instance/                 # SQLite DB file lives here (internship.db)
├── models/                   # SQLAlchemy models (one file per entity)
├── routes/                   # Flask blueprints (auth, student, applications, offers, internships, admin)
├── templates/                # Jinja2 templates (base + auth/ + student/ + admin/ + errors/)
├── static/
│   ├── css/style.css
│   └── js/main.js
└── uploads/resumes/          # Uploaded student resumes (PDF)
```

## 5. Installation Steps

```bash
git clone <this-project-folder>   # or unzip the provided archive
cd internship_portal
```

## 6. Virtual Environment Setup

```bash
python -m venv venv
```

Windows:
```bash
venv\Scripts\activate
```

macOS / Linux:
```bash
source venv/bin/activate
```

## 7. Dependencies

```bash
pip install -r requirements.txt
```

Installs: Flask, Flask-SQLAlchemy, Flask-WTF, Werkzeug, email-validator.

## 8. Database Initialization

```bash
python init_db.py
```

This drops/recreates all tables, creates the first admin account, and seeds sample
students, internship opportunities, and applications (with varied statuses) so the
dashboards are populated on first run.

## 9. Admin Account Creation

The first admin account is created by `init_db.py`, **not** hardcoded in source code.
Credentials come from environment variables (with safe defaults for local/demo use):

```bash
# optional — override before running init_db.py
set ADMIN_EMAIL=admin@college.edu        (Windows: use `set`)
set ADMIN_PASSWORD=Admin@123
```

or on macOS/Linux:
```bash
export ADMIN_EMAIL=admin@college.edu
export ADMIN_PASSWORD=Admin@123
```

If not set, defaults from `config.py` are used (`admin@college.edu` / `Admin@123`).
The password is hashed with Werkzeug before being stored — never stored in plain text.

Also set a real `SECRET_KEY` for anything beyond local demo use:
```bash
export SECRET_KEY=some-long-random-string
```
See `.env.example` for the full list of variables the app reads.

## 10. How to Run the Application

```bash
python app.py
```

Then open **http://127.0.0.1:5000** in your browser.

## 11. Default Routes

| Route | Description |
|---|---|
| `/` | Redirects to dashboard or login |
| `/auth/login`, `/auth/register`, `/auth/logout` | Authentication |
| `/student/dashboard`, `/student/profile` | Student dashboard & profile |
| `/internships/` | Browse internship opportunities |
| `/applications/` | Student's application tracker |
| `/offers/` | Student's offers |
| `/admin/dashboard` | Admin dashboard |
| `/admin/students`, `/admin/applications`, `/admin/internships`, `/admin/offers` | Admin management pages |
| `/admin/export/applications`, `/admin/export/students`, `/admin/export/offers` | CSV export |

## 12. Sample Login Information

After running `python init_db.py`:

- **Admin:** `admin@college.edu` / `Admin@123` (or your overridden env vars)
- **Demo student:** `aarav.sharma@college.edu` / `Student@123`
  (7 more seeded students follow the same `firstname.lastname@college.edu` / `Student@123` pattern)

## 13. How the Major Modules Work

- **`extensions.py` / `app.py`** — `db` (SQLAlchemy) lives in its own module to avoid
  circular imports; `create_app()` wires config, initializes `db` and CSRF protection,
  and registers each feature's blueprint.
- **`models/`** — One file per entity. `Application` owns the status-flow logic
  (`STATUS_FLOW` dict) that both the student and admin routes consult before allowing
  a status transition, and a badge-color map used everywhere a status is displayed.
- **`routes/decorators.py`** — `login_required`, `student_required`, `admin_required`
  wrap views and redirect/`403` as appropriate, enforcing role separation.
- **`routes/applications.py`** — The core tracker: create/edit/delete an application,
  move it through statuses (writing an `ApplicationActivity` row on every change),
  attach interviews, and hand off to offer creation once status reaches "Offer Received".
- **`routes/internships.py`** — Student-facing browse/search/filter/apply flow; applying
  auto-creates an `Application` row linked back to the `Internship`.
  `Internship.effective_status()` derives Active/Expired/Closed from the stored deadline.
- **`routes/admin.py`** — Dashboard aggregation queries (status/company/work-mode/monthly
  counts for the charts), student/application/internship/offer management screens, and
  CSV export using Python's built-in `csv` module streamed via `Response`.
  Every admin view is wrapped in `@admin_required`.
- **Templates** — `base.html` renders a role-aware sidebar (different links for student
  vs admin) and includes `_flash.html` for Bootstrap alert messages; every other template
  extends it and only fills in `content` (or `guest_content` for the logged-out auth pages).

## 14. Future Improvements

- Email notifications for status changes / upcoming interviews
- Recruiter-facing self-service internship posting with an approval step
- Bulk import of students via CSV
- Richer analytics (placement rate by department, average time-to-offer)
- Pagination on the internship browse page and admin students page
- Automated background job to flip expired internships instead of computing on read
