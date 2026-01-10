# PR0: Project Bootstrap

> **STATUS: ✅ COMPLETED**  
> **Completed:** 2026-01-10  
> **Verification:** All bootstrap requirements verified and passing. See walkthrough for details.

## 0) Project Type
- **Full-Stack Web (Python)** — Backend API + Frontend + Data Pipeline + PDF Generation

## 1) Assumptions (max 3)
- Development will start with SQLite for local development; production may migrate to PostgreSQL later
- PDF generation will use a Python library (e.g., ReportLab or WeasyPrint) rather than a JavaScript solution
- Frontend will be served via FastAPI with Jinja2 templates + HTMX for interactivity, avoiding a separate React/Next.js setup for MVP simplicity

## 2) PSD Extraction (scaffolding-relevant only)
- **App type:** Full-stack web application with public-facing analytics, admin panel, scheduled data ingestion, and PDF export
- **Key pages/flows (names only):**
  - Home/Search
  - Listing/Unit Input
  - Fair Value Results
  - Block X-Ray
  - Compare (side-by-side)
  - Callback Request Form
  - PDF Export
  - Admin Lead Inbox
  - Data Status Page
- **Data needs:** SQLite (dev) → PostgreSQL (prod); ingestion pipeline for HDB transactions, POIs, MRT/LRT locations, amenities
- **Auth need:** Admin-only authentication for Lead Inbox and admin functions; no buyer login required

## 3) Tech Decisions (DECIDED)
- **Stack preset:** FastAPI + Jinja2 + HTMX + SQLAlchemy + Alembic + APScheduler (for scheduled ingestion)
- **Package manager:** uv
- **Test runner:** pytest + pytest-cov
- **Lint/format:** Ruff
- **Typecheck:** mypy
- **Environment strategy (.env.*):** python-dotenv
- **Minimal CI checks:** lint + format + typecheck + test
- **Additional tools:**
  - **PDF generation:** WeasyPrint or ReportLab
  - **Geocoding/routing:** OneMap API integration (or fallback to distance calculations)
  - **Job scheduling:** APScheduler (for automated data ingestion)
  - **Database:** SQLAlchemy ORM + Alembic migrations

## 4) Repo Structure (DECIDED)
- **Top-level folders:**
  ```
  ResaleLens_SG-V1/
  ├── src/                     # Application code
  ├── tests/                   # Test suite
  ├── docs/                    # Documentation (PSD, plans, technical)
  │   ├── psd/
  │   ├── plans/
  │   └── technical/
  ├── data/                    # Local data storage (ingested datasets, SQLite DB)
  ├── scripts/                 # Utility scripts (manual ingestion, data setup)
  ├── static/                  # Static assets (CSS, JS, images)
  ├── templates/               # Jinja2 HTML templates
  ├── .github/workflows/       # CI configuration
  ├── pyproject.toml           # Project config + dependencies
  ├── .env.example             # Environment template
  └── README.md                # Setup and usage guide
  ```
- **Where app code lives:** `src/resalelens/` (package structure)
- **Where tests live:** `tests/`
- **Where config lives:** root (`pyproject.toml`, `.env`)
- **Where DB/migrations live:** `data/` (SQLite DB), `src/resalelens/migrations/` (Alembic)

## 5) PR0 Details

### Goal
Establish a runnable FastAPI application with:
- Basic routing and health check
- Database setup (SQLAlchemy + Alembic)
- Environment configuration (.env)
- Testing, linting, formatting, and typechecking infrastructure
- CI/CD pipeline (GitHub Actions)
- Scheduled job runner skeleton (APScheduler)
- Clear setup instructions in README

### Scope
**In scope:**
- Bootstrap FastAPI app with Uvicorn
- SQLAlchemy models and Alembic migrations setup
- Basic Jinja2 template rendering
- APScheduler integration (skeleton job)
- Environment config with python-dotenv
- pytest suite with sample test
- Ruff + mypy configuration
- GitHub Actions CI (lint, format, typecheck, test)
- Comprehensive README with setup and command reference
- `.env.example` for local setup

**Out of scope:**
- Feature implementation (Fair Value Engine, Block X-Ray, etc.)
- Data ingestion logic
- Frontend styling or production UI
- External API integrations (OneMap, etc.)

### Files to create

#### Configuration & Setup
- `README.md` — Setup instructions, architecture overview, command reference
- `pyproject.toml` — Dependencies, tool configuration (Ruff, mypy, pytest), project metadata
- `.env.example` — Template for environment variables
- `.gitignore` — Exclude `.env`, `data/`, `__pycache__`, etc.

#### CI/CD
- `.github/workflows/ci.yml` — GitHub Actions workflow (lint, format, typecheck, test)

#### Application Code
- `src/resalelens/__init__.py` — Package marker
- `src/resalelens/main.py` — FastAPI app entry point, basic routes
- `src/resalelens/config.py` — Environment config loader (using python-dotenv)
- `src/resalelens/database.py` — SQLAlchemy engine and session setup
- `src/resalelens/models.py` — SQLAlchemy ORM models (initial skeleton)
- `src/resalelens/scheduler.py` — APScheduler setup (skeleton with sample job)

#### Database Migrations
- `src/resalelens/migrations/env.py` — Alembic environment configuration
- `src/resalelens/migrations/script.py.mako` — Alembic migration template
- `alembic.ini` — Alembic configuration file

#### Templates & Static
- `templates/base.html` — Base Jinja2 template
- `templates/index.html` — Home page template (minimal)
- `static/styles.css` — Minimal CSS skeleton

#### Tests
- `tests/__init__.py` — Test package marker
- `tests/conftest.py` — pytest fixtures (app client, test DB)
- `tests/test_main.py` — Sample tests (health check, basic routes)

#### Documentation
- `docs/technical/context.md` — Project context, architecture decisions, and developer onboarding

#### Data & Scripts
- `data/.gitkeep` — Ensure data directory exists
- `scripts/setup_db.py` — Script to initialize database and run migrations

### Commands to establish

| Command | Description |
|---------|-------------|
| `uv sync` | Install dependencies and setup virtual environment |
| `uv run uvicorn src.resalelens.main:app --reload --host 0.0.0.0 --port 8000` | Start development server |
| `uv run pytest` | Run all tests |
| `uv run pytest --cov=src --cov-report=term-missing` | Run tests with coverage report |
| `uv run ruff check .` | Lint codebase |
| `uv run ruff format .` | Format codebase |
| `uv run mypy src/` | Run type checker |
| `uv run alembic upgrade head` | Apply database migrations |
| `uv run alembic revision --autogenerate -m "message"` | Generate new migration |
| `uv run python scripts/setup_db.py` | Initialize database (first-time setup) |

### Verification checklist
- [ ] `uv sync` completes without errors
- [ ] FastAPI dev server starts and responds to `http://localhost:8000`
- [ ] Health check endpoint (`/health`) returns 200 OK
- [ ] Home page (`/`) renders Jinja2 template
- [ ] `pytest` runs and all tests pass
- [ ] `ruff check .` passes with no errors
- [ ] `ruff format .` runs without issues
- [ ] `mypy src/` passes type checking
- [ ] Alembic migrations can be applied (`alembic upgrade head`)
- [ ] APScheduler starts without errors (logs show job scheduling)
- [ ] GitHub Actions CI workflow runs successfully on push
- [ ] `.env.example` exists and documents all required environment variables
- [ ] README provides clear setup instructions for new developers

### Risks / gotchas
- **uv version:** Ensure uv is installed and up-to-date; fallback to `pip + venv` if uv causes issues
- **Alembic setup:** Alembic configuration requires careful path setup; migrations directory must be correctly referenced
- **APScheduler conflicts:** APScheduler may need specific configurations to avoid conflicts with Uvicorn's auto-reload in development
- **Database location:** SQLite database file path must be correctly set in `.env` to avoid "database not found" errors
- **HTMX integration:** HTMX script inclusion should be tested in base template; CDN link may be preferred initially
- **Mypy strict mode:** Initial mypy configuration should be lenient; strict mode can be enabled incrementally

## 6) Next Step
- **After PR0 is implemented:** Run `/plan_product` to generate the full product plan (PR1..n) based on the PSD feature roadmap
