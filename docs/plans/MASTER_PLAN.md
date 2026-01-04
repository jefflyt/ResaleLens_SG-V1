# MASTER PLAN: ResaleLens SG

**Product:** HDB Resale Fair Value + Block Intelligence Platform  
**Version:** 1.0  
**Date:** 2026-01-04  
**Based on:** PSD v2

---

## 1. Product Summary

### Problem Statement
HDB resale buyers in Singapore lack a credible, transparent way to determine fair value for units of interest and assess whether a block fits their lifestyle needs. Existing portals show raw historical transactions but do not normalize comparables into clear value bands with confidence scores, nor do they provide buyer-first filters grounded in verifiable datasets.

### Target Users
- **Primary:** First-time buyers, families with kids, multi-generational families, upgraders/second-time buyers
- **Secondary:** Admin (solo founder managing callback leads); Phase 2 will add agents with a "Saved Jobs" workspace

### Value Proposition
ResaleLens SG provides:
1. **Fair Value bands** with confidence scores based on real, normalized comparables
2. **Block X-Ray** showing transparent, data-backed neighborhood signals (commute, schools, amenities, lease, trends)
3. **Persona-based filtering** with explicit rules (not vibes)
4. **PDF export** and **callback requests** without requiring buyer login
5. **Data transparency** via a public Data Status page showing dataset freshness and sources

### Core Features
1. **Fair Value Engine:** Comp-based pricing with transparent fallback ladder, normalization, confidence scoring, and explainability
2. **Block X-Ray:** Remaining lease, transaction trends, volatility, MRT/amenity distances, noise-risk proxies
3. **Persona Filters:** Presets for first-time buyers, families, multi-gen, upgraders
4. **Shortlist & Compare:** Side-by-side comparison of up to 3 options
5. **PDF Export:** Template-driven generated report (not screenshot)
6. **Callback Request & Admin Lead Inbox:** No-login lead capture with structured form; admin-only inbox for follow-up
7. **Data Status Page:** Public transparency on dataset sources, last ingest, next scheduled ingest, and freshness status
8. **Automated Data Ingestion:** Scheduled jobs (weekly for transactions/blocks, monthly for POIs/MRT)

> **📌 Important Clarification:**  
> ResaleLens SG analyzes **historical HDB resale transaction data** (completed sales from data.gov.sg), **NOT active property listings for sale**. Users input a unit of interest (block, flat type, floor area, storey) to get Fair Value based on comparable past transactions. There is no property listing database or integration with active sales portals (PropertyGuru, 99.co, etc.).

---

## 2. Goals, Success Criteria, and Constraints

### Product Goals
- **Phase 1 (MVP):** Launch a functional Fair Value checker + Block X-Ray + Lead capture within 8–12 weeks
- **Activation:** ≥30% of visitors run at least 1 Fair Value check
- **Engagement:** Median ≥3 blocks/units evaluated per session
- **Trust:** ≥70% rate Fair Value explanation as "clear" (in-product micro survey)
- **Leads:** ≥2–5% submit a callback request
- **Exports:** ≥10% download a PDF report

### Success Criteria (Observable Outcomes)
1. **MVP Usable:**
   - Fair Value returns a band + confidence + comps for any valid HDB address/block
   - Block X-Ray displays lease, MRT distance/time, amenities, and transaction trend
   - Users can shortlist, compare, and export PDF without login
   - Callback requests persist to DB within 1 minute; admin can view and manage leads
   - Data Status page shows dataset freshness and sources

2. **Technical Health:**
   - p95 Fair Value response < 2.5s
   - p95 search/filter response < 1.5s
   - CI pipeline runs lint + format + typecheck + tests on every push
   - Code coverage ≥70% for core Fair Value and ingestion logic
   - Alembic migrations run cleanly; DB schema is version-controlled

3. **Data Transparency:**
   - Every metric card shows "Last updated" timestamp
   - PDF exports include "As of" and dataset timestamps
   - Data Status page reflects ingestion health; delayed data (>48h) shows a "Data delayed" badge

4. **Observability:**
   - Logs capture latency, errors, and ingestion run outcomes
   - Ingestion runs write audit records (start/end time, status, rows processed, errors)

### Constraints & Assumptions

#### Constraints (from PSD)
- Solo founder, full-stack development
- MVP supports block-level and transaction-level analytics based on historical data (not true unit-level condition/view/renovation quality)
- No buyer login required for Phase 1
- Admin authentication required for Lead Inbox
- Data ingestion automated on fixed schedules (weekly/monthly)
- Performance targets: p95 Fair Value < 2.5s, p95 search < 1.5s

#### Assumptions (Explicit)
1. **Assumption:** Initial traffic will be modest (<500 daily active users); scale-out can be deferred to Phase 2+
2. **Assumption:** OneMap API rate limits and routing costs are acceptable for MVP; caching + distance fallback will mitigate
3. **Assumption:** SQLite is sufficient for local development; PostgreSQL migration will occur before production deployment

---

## 3. Architecture & Technology Stack

> **🐍 Python-First Philosophy:**  
> This architecture prioritizes Python across the entire stack (~95% Python, ~5% JavaScript) to maximize solo founder velocity, maintain a single-language codebase, and leverage Python's mature data science ecosystem for the Fair Value Engine. A React prototype (`docs/design/prototype_app.jsx`) serves as a **functional reference** demonstrating key features and interactions, but the actual layout and user flow will be driven by the customer journeys defined in PSD Section 5.

### 3.1 Frontend

**Framework:** FastAPI + Jinja2 templates + HTMX

**Rationale (Python-First):**
- **Single Language:** All business logic, data processing, and templating in Python - no context-switching to JavaScript
- **No Build Pipeline:** No npm, webpack, or frontend tooling complexity - just Python and standard web technologies
- **Faster Development:** Server-rendered templates with HTMX provide modern interactivity without maintaining separate frontend/backend codebases
- **SEO-Friendly:** Server-side rendering ensures search engines can index all content
- **Prototype as Feature Reference:** The React prototype (`docs/design/prototype_app.jsx`) demonstrates **what features to build** (persona selector, location search, Block X-Ray modal, AI consultant modes, comparison tools) but the **layout and flow** will follow the logical customer journeys from the PSD, not the prototype's page structure

**Structure:**
- `templates/` directory with Jinja2 templates organized by page (base, index, results, block_xray, compare, admin)
- `static/` directory for CSS, JavaScript (HTMX, custom interactions), images, and fonts
- **Styling:** Vanilla CSS with CSS Grid/Flexbox; modern, clean aesthetic; Google Fonts (e.g., Inter, Roboto); responsive mobile-first design
- **Feature Inspiration from prototype_app.jsx (what to build, not how to layout):**
  - **Persona Selector:** Interactive buyer persona cards with icons and targeted flat types (First-Timer, Young Family, Multi-Gen, Budget) → implement as a feature, but placement follows customer journey
  - **Location Search:** Postal code search with radius filtering + real-time amenities radar (Transport, Schools, Retail, Groceries) → implement as a capability
  - **Block X-Ray Modal:** Rich modal with unit mix pie charts, lease clock visualization, height context bar, amenity badges → implement these data visualizations
  - **AI Consultant Modes:** Multi-mode AI assistant (Market Insight, Rate Unit/Price, Location Scout, Negotiation Helper, Renovation Estimator, Vibe Check, Grant Wizard, Feng Shui) → implement these AI capabilities
  - **Comparison Tools:** Side-by-side block comparison with interactive filtering → implement the comparison logic
  - **Interactive Charts:** Price trend line charts, volume bar charts, scatter plots with lease indicators → use appropriate charting library for these visualizations
  - **Color Palette:** Slate grays for neutrals, blue/violet for primary actions, semantic colors (green up, red down) → adopt this color system

**Page Structure (Customer Journey-Driven from PSD §5):**
Journey A: "Is this unit fairly priced?" (based on historical transactions) → Journey B: "Find blocks that fit my life" → Journey C: "Request callback + export PDF"

**Key Pages (aligned with customer journeys):**
- Home/Search (`/`) — Entry point with persona selector + search options (Journey A & B start here)
- Unit Input (`/input`) — User inputs block/address + flat attributes for a unit of interest (Journey A)
- Fair Value Results (`/results`) — Fair Value band + confidence + comps + explainability (Journey A output)
- Block Explorer (`/explore`) — Persona-based filtering + town/area selection (Journey B)
- Block X-Ray (`/block/<block_id>`) — Detailed block intelligence (Journey A & B deep-dive)
- Compare (`/compare`) — Side-by-side comparison (max 3 units) (Journey C preparation)
- Callback Request — Modal/inline form (Journey C)
- PDF Export — Generated report download (Journey C)
- Admin Lead Inbox (`/admin/leads`) — Admin-only lead management
- Data Status (`/data-status`) — Public transparency page

### 3.2 Backend

**Framework:** FastAPI (Python 3.11+)

**Structure:**
- `src/resalelens/` package with modular organization:
  - `main.py` — FastAPI app instance, route registration
  - `routers/` — Route handlers organized by domain (public, admin, api)
  - `services/` — Business logic (Fair Value calculation, comp selection, X-Ray aggregation, PDF generation)
  - `data/` — Data access layer (repository pattern for transactions, POIs, MRT, leads)
  - `ingestion/` — Data ingestion modules (HDB transactions, blocks, POIs, MRT)
  - `scheduler.py` — APScheduler setup for automated ingestion jobs
  - `config.py` — Environment configuration (dotenv)
  - `database.py` — SQLAlchemy engine and session management
  - `models.py` — SQLAlchemy ORM models

**API Style:** REST-like endpoints; may add GraphQL in Phase 3 if complexity warrants

**Layering Approach:**
- **Routers:** Handle HTTP request/response, validation (Pydantic models), route to services
- **Services:** Encapsulate business logic (Fair Value calculation, comp selection ladder, PDF generation)
- **Data Access (Repositories):** Abstract SQLAlchemy queries; each entity (Transaction, Block, POI, Lead) has a repository
- **Models:** SQLAlchemy ORM models map to DB tables

**Background Jobs:**
- APScheduler for scheduled ingestion (weekly transactions, monthly POIs/MRT)
- Jobs run in-process for MVP; may migrate to Celery or external job runner in Phase 2+ if needed

### 3.3 Data

**Database:** PostgreSQL (production) / SQLite (local development)

**ORM:** SQLAlchemy 2.0+

**Migrations:** Alembic

**Data Modeling:**

**Core Entities:**
- `transactions` — HDB resale transaction records (date, block, street, flat_type, storey_range, floor_area_sqm, price, lease_commence_date, town, flat_model, latitude, longitude, psm, ingestion_run_id)
- `blocks` — HDB block metadata (block, street, town, postal_code, latitude, longitude, lease_commence_year, flat_mix_distribution, last_updated)
- `pois` — Points of interest (poi_id, poi_type [MRT, LRT, supermarket, clinic, park, mall, hawker], name, latitude, longitude, last_updated)
- `leads` — Callback requests (lead_id, name, mobile, contact_window, budget_range, preferred_towns, flat_types, timeline, first_timer, financing_status, notes, filter_snapshot, shortlist_snapshot, created_at, status)
- `ingestion_runs` — Audit log for data ingestion (run_id, dataset_name, started_at, completed_at, status [success, failed], rows_processed, error_summary)

**Indexes:**
- `transactions`: (block, street, flat_type, date), (town, flat_type, date), (latitude, longitude)
- `blocks`: (block, street), (town)
- `pois`: (poi_type, latitude, longitude)
- `leads`: (created_at, status)

**Migrations Strategy:**
- Alembic autogenerate for initial schema
- Manual review of autogenerated migrations before applying
- Rollback scripts included for safety

### 3.4 Auth & Security

**Authentication:**
- **Admin-only:** Admin Lead Inbox and manual ingestion triggers require authentication
- **Method:** HTTP Basic Auth or session-based auth (e.g., via FastAPI's OAuth2PasswordBearer) with bcrypt-hashed passwords stored in DB
- **No buyer login:** Public-facing features (Fair Value, Block X-Ray, PDF export, callback request) are open access

**Authorization:**
- Simple role-based access: `admin` role required for `/admin/*` routes
- Middleware checks for admin role on protected routes

**Session/Token Handling:**
- Session cookies for admin login (HTTP-only, Secure, SameSite=Lax)
- CSRF protection for admin forms

**Anti-Spam (Callback Requests):**
- Rate limiting: max 3 callback requests per IP per 24 hours
- Basic validation: mobile number format, required fields
- Lightweight bot protection: honeypot field or simple CAPTCHA (e.g., hCaptcha)

### 3.5 Infrastructure & Deployment

**Hosting Model:**
- **MVP:** Single server deployment (e.g., Railway, Render, DigitalOcean App Platform, or AWS Lightsail)
- **Later:** Docker container + managed PostgreSQL; scale horizontally if needed

**Environments:**
- **Development:** Local (SQLite DB, `.env` with dev config)
- **Staging (optional):** Deployed preview environment for QA
- **Production:** Managed server + managed PostgreSQL

**CI/CD:**
- **CI:** GitHub Actions workflow (`.github/workflows/ci.yml`)
  - Lint (Ruff check)
  - Format check (Ruff format --check)
  - Typecheck (mypy)
  - Unit + integration tests (pytest)
- **CD (later):** Auto-deploy to staging on merge to `main`; manual promotion to production

**Observability:**
- **Logging:** Structured JSON logs (uvicorn + Python logging); log to stdout, capture via hosting platform
- **Error Tracking:** Sentry (or similar) for error aggregation
- **Metrics:** Log p95 latency for Fair Value and search queries; ingestion run durations and statuses
- **Monitoring:** Basic uptime monitoring (e.g., UptimeRobot or built-in platform health checks)

### 3.6 Cross-Cutting Concerns

> **Python Ecosystem Advantage:** Leveraging mature Python libraries for all cross-cutting concerns eliminates language fragmentation and tooling complexity.

**Config/Environment Variables:**
- `.env` file (local development; not committed)
- `.env.example` template for required variables
- **python-dotenv** for environment variable management
- Environment variables:
  - `DATABASE_URL` (PostgreSQL connection string)
  - `SECRET_KEY` (for session/token signing)
  - `ADMIN_USERNAME`, `ADMIN_PASSWORD_HASH`
  - `ONEMAP_API_KEY` (if OneMap requires auth)
  - `GEMINI_API_KEY` (for AI consultant features - inspired by prototype_app.jsx)
  - `SENTRY_DSN` (error tracking)
  - Ingestion schedule overrides (optional)

**Error Handling:**
- Centralized exception handlers in FastAPI (e.g., HTTPException, custom exceptions)
- User-facing errors: friendly messages with actionable guidance (e.g., "Comps < 5: widen time window")
- Admin-facing errors: detailed stack traces and error IDs
- **Python advantage:** Unified error handling across all layers (no JavaScript error handling)

**Logging Strategy:**
- Structured JSON logs with fields: timestamp, level, message, request_id, user_id (if admin), endpoint, latency
- **Python logging module** with custom formatters
- Log levels: DEBUG (dev), INFO (prod), WARN/ERROR (issues)
- Log ingestion runs: start/end, status, rows processed, errors
- **Python advantage:** Single logging configuration for entire application

**Performance/Caching:**
- **Routing/distance caching:** Store OneMap routing results in DB or in-memory cache (e.g., Redis or simple dict with TTL)
- **Fair Value caching:** Cache comp queries for identical block + flat_type + time window (TTL: 1 hour) using **Python functools.lru_cache** or Redis
- **POI distance caching:** Precompute distances from blocks to POIs during ingestion; store in `block_pois` table
- **Data processing:** Use **pandas** for efficient bulk operations on transaction data; **numpy** for statistical calculations (P25, P75, variance, MAD)
- **Python advantage:** pandas + numpy provide optimized C-extension performance for data-heavy operations

---

## 4. Project Phases

### Phase 1: Foundations & Core MVP (PR0–PR7)
**Objective:** Deliver a fully functional Fair Value + Block X-Ray + Lead Capture system with data transparency and automated ingestion.

**High-Level Scope:**
- Project bootstrap (commands, CI, skeleton app)
- Database schema and migrations
- Data ingestion pipeline (HDB transactions, blocks, POIs, MRT)
- Fair Value Engine (comp selection, normalization, confidence scoring)
- Block X-Ray (lease, trends, amenities, MRT)
- Public-facing UI (search, results, Block X-Ray, compare, PDF export)
- Admin Lead Inbox
- Data Status page
- Automated ingestion scheduling (APScheduler)
- Comprehensive testing and CI/CD

**Dependencies:** None (greenfield)

**Acceptance Criteria:**
- User can input a block/flat type and receive a Fair Value band with comps and confidence score
- User can view Block X-Ray with lease, transaction trend, MRT/amenity distances, and "Last updated" timestamps
- User can shortlist blocks, compare up to 3 side-by-side, and export a generated PDF
- User can submit a callback request; admin can view and manage leads in Admin Lead Inbox
- Data Status page shows all datasets, last ingest, next scheduled ingest, and current status
- Ingestion jobs run automatically on schedule; failures retry and log to `ingestion_runs`
- CI pipeline passes (lint, format, typecheck, tests)
- p95 Fair Value response < 2.5s (measured via logs)

---

### Phase 2: Agent Workspace & Market Context (PR8–PR12)
**Objective:** Enable agents to save and reopen work-in-progress customer entries; add market context indicators.

**High-Level Scope:**
- Agent authentication and "Saved Jobs" workspace (agent can log in, save customer research, reopen later)
- Market context module: descriptive trend indicators (not forecasting) based on published indices (e.g., HDB Resale Price Index)
- Commute-time lens: user can specify workplace(s); system shows commute times to blocks
- Share-link persistence: improve shareable URLs to include filter state and shortlist

**Dependencies:** Phase 1 complete

**Acceptance Criteria:**
- Agent can log in, create a "job" (customer research session), save shortlist/filters, and reopen later
- Market context card shows recent trends (e.g., "Town X prices +2.3% YoY") with clear source attribution
- User can input 1–2 workplace addresses and see commute times to blocks (via OneMap routing or fallback)
- Shareable link preserves filter state and shortlist; recipient sees same view

---

### Phase 3: Alerts & Advanced Analytics (PR13–PR17)
**Objective:** Proactive buyer engagement via alerts; exploratory ML/advanced pricing models.

**High-Level Scope:**
- Price drop alerts: user can subscribe to alerts for specific blocks/units (requires email collection)
- New comps alerts: notify when new transactions appear for a watched block
- Advanced pricing models (optional): hedonic regression or ML-based pricing with explainability
- Forecasting experiments (optional, clearly labeled): explore forward-looking price trend indicators (only after stable pipelines + evaluation + disclaimers)

**Dependencies:** Phase 2 complete

**Acceptance Criteria:**
- User can subscribe to email alerts for price drops or new comps on watched blocks
- Alerts are sent within 24 hours of new data ingestion
- Advanced pricing model (if implemented) is benchmarked against baseline comp-based model; explainability is maintained
- All forecasting outputs are clearly labeled as experimental and non-guaranteed

---

### Phase 4: Scale & Optimization (PR18+)
**Objective:** Optimize for higher traffic, reduce costs, improve performance.

**High-Level Scope:**
- Horizontal scaling: migrate APScheduler jobs to external job runner (Celery + Redis)
- Caching layer: Redis for routing/distance caching
- Database optimization: query performance tuning, read replicas if needed
- Cost optimization: batch OneMap API calls, reduce redundant routing queries

**Dependencies:** Phase 3 complete; traffic justifies optimization

**Acceptance Criteria:**
- System handles ≥5,000 daily active users with p95 latency targets maintained
- External job runner reliably processes ingestion jobs
- API call costs reduced by ≥50% via caching

---

## 5. Initial PR Breakdown (Phase 1)

### PR0: Project Bootstrap
**Status:** Plan exists at `docs/plans/PR0_BOOTSTRAP.md`

**Branch:** `pr0-bootstrap`

**Goal:** Establish a runnable FastAPI app skeleton with commands, CI, and developer documentation.

**Scope:**
- FastAPI app with health check and home route
- SQLAlchemy + Alembic setup
- APScheduler skeleton (sample job)
- Jinja2 template rendering (minimal base + index templates)
- pytest suite with sample tests
- Ruff + mypy configuration
- GitHub Actions CI (lint, format, typecheck, test)
- README with setup instructions and command reference
- `docs/technical/context.md` documenting repo structure and conventions

**Key Changes:**
- **Backend:** `src/resalelens/main.py`, `config.py`, `database.py`, `models.py`, `scheduler.py`
- **Migrations:** Alembic setup (`alembic.ini`, `src/resalelens/migrations/`)
- **Frontend:** `templates/base.html`, `templates/index.html`, `static/styles.css`
- **Tests:** `tests/conftest.py`, `tests/test_main.py`
- **Config:** `pyproject.toml`, `.env.example`, `.gitignore`
- **CI:** `.github/workflows/ci.yml`
- **Docs:** `README.md`, `docs/technical/context.md`

**Testing Focus:**
- Health check endpoint returns 200 OK
- Home route renders Jinja2 template
- Database connection initializes without error

**Verification:**
- `uv sync` completes
- `uv run uvicorn src.resalelens.main:app --reload` starts server
- `http://localhost:8000/health` returns 200 OK
- `uv run pytest` passes
- `uv run ruff check .` passes
- `uv run mypy src/` passes
- CI workflow runs successfully on push

---

### PR1: Database Schema & Migrations
**Branch:** `pr1-database-schema`

**Goal:** Define and apply the complete database schema for transactions, blocks, POIs, leads, and ingestion_runs.

**Scope:**
- SQLAlchemy ORM models for all core entities (transactions, blocks, pois, leads, ingestion_runs)
- Alembic migration to create tables and indexes
- Repository pattern for data access (transaction_repo, block_repo, poi_repo, lead_repo, ingestion_run_repo)
- Seed script for development data (optional: sample transactions, blocks, POIs)

**Key Changes:**
- **Backend:** Update `src/resalelens/models.py` with all ORM models
- **Data Access:** Create `src/resalelens/data/repositories.py` (base repo pattern + specific repos)
- **Migrations:** Alembic migration file (autogenerated + reviewed)
- **Scripts:** `scripts/seed_data.py` (optional dev seed)

**Testing Focus:**
- All models can be instantiated and persisted to DB
- Migrations apply cleanly (`alembic upgrade head`)
- Rollback works (`alembic downgrade -1`)
- Repository methods (create, read, update, delete) work as expected

**Verification:**
- `uv run alembic upgrade head` applies migration without errors
- `uv run pytest tests/test_models.py` passes (model instantiation, basic CRUD)
- Database inspection shows all tables and indexes created

---

### PR2: Data Ingestion Pipeline (HDB Transactions & Blocks)
**Branch:** `pr2-ingestion-hdb`

**Goal:** Implement automated ingestion for HDB resale transactions and block metadata; log ingestion runs.

**Scope:**
- Ingestion modules for HDB resale transactions (data.gov.sg API or CSV download)
- Ingestion module for HDB block/address reference + geocoding
- Ingestion run logging to `ingestion_runs` table
- Retry logic (3 retries with exponential backoff)
- Manual trigger endpoint for admin (`POST /admin/ingestion/trigger`)
- APScheduler jobs for weekly HDB transaction and block ingestion (Sunday 03:00 and 03:15 SGT)

**Key Changes:**
- **Backend:**
  - `src/resalelens/ingestion/hdb_transactions.py` (fetch, parse, upsert)
  - `src/resalelens/ingestion/hdb_blocks.py` (fetch, parse, upsert)
  - `src/resalelens/ingestion/utils.py` (retry decorator, run logging)
  - Update `src/resalelens/scheduler.py` to register ingestion jobs
- **Routers:** `src/resalelens/routers/admin.py` (manual trigger endpoint)

**Testing Focus:**
- Ingestion modules fetch and parse data correctly (use mock API responses in tests)
- Upsert logic correctly handles duplicates
- Ingestion run logs are created and updated correctly
- Retry logic retries on failure and logs errors
- Scheduled jobs are registered and would run at correct times (test job registration, not actual schedule)

**Verification:**
- Manual ingestion trigger (`POST /admin/ingestion/trigger?dataset=hdb_transactions`) completes successfully
- `ingestion_runs` table shows a successful run record
- `transactions` and `blocks` tables are populated
- Scheduled jobs appear in APScheduler logs

---

### PR3: Data Ingestion Pipeline (POIs & MRT)
**Branch:** `pr3-ingestion-pois-mrt`

**Goal:** Implement automated ingestion for MRT/LRT stations and amenity POIs; complete the data transparency foundation.

**Scope:**
- Ingestion module for MRT/LRT station locations (data.gov.sg or OneMap)
- Ingestion module for amenity POIs (supermarkets, clinics, parks, malls, hawkers) — may use OneMap or curated CSV
- APScheduler jobs for monthly POI and MRT ingestion (1st of month, 03:30 and 03:45 SGT)
- Precompute block-to-POI distances during ingestion; store in `block_pois` table (optional optimization)

**Key Changes:**
- **Backend:**
  - `src/resalelens/ingestion/mrt.py`
  - `src/resalelens/ingestion/pois.py`
  - Update `src/resalelens/scheduler.py` to register monthly jobs
  - (Optional) `src/resalelens/models.py` — add `block_pois` table for precomputed distances
- **Routers:** Update `src/resalelens/routers/admin.py` to support POI/MRT manual triggers

**Testing Focus:**
- MRT and POI ingestion modules correctly parse and upsert data
- Scheduled jobs are registered
- Precomputed distances (if implemented) are accurate (test with known block/POI pairs)

**Verification:**
- Manual ingestion trigger for MRT and POIs completes successfully
- `pois` table is populated with MRT/LRT, supermarkets, clinics, parks, malls, hawkers
- (Optional) `block_pois` table shows precomputed distances

---

### PR4: Fair Value Engine (Comp Selection & Normalization)
**Branch:** `pr4-fair-value-engine`

**Goal:** Implement the Fair Value calculation logic: comp selection ladder, normalization, confidence scoring, outlier handling.

**Scope:**
- Service layer (`src/resalelens/services/fair_value.py`) with:
  - Comp selection fallback ladder (same block, nearby radius, town-level)
  - Price-per-sqm normalization
  - Storey range adjustment (median deltas)
  - Outlier removal (P5–P95 or 2.5 MAD)
  - Confidence scoring (based on comp count, variance, recency)
  - Fair Value band (P25–P75) and user-facing labels (Fair, Slightly high, Slightly low, High risk)
- Explainability output: filters applied, adjustments, fallback used, comp count, variance
- Input validation (block, flat_type, floor_area, storey_range, time_window)

**Key Changes:**
- **Backend:**
  - `src/resalelens/services/fair_value.py` (core engine)
  - `src/resalelens/services/utils.py` (distance calculation, date filtering)
  - Pydantic models for input/output (`src/resalelens/schemas/fair_value.py`)

**Testing Focus:**
- Comp selection ladder correctly falls back when comps < 5
- Normalization adjusts for storey range correctly
- Outlier removal works as expected
- Confidence scoring reflects comp count, variance, recency
- Fair Value band is within expected range for known test data
- Edge cases: comps < 5, missing attributes, no comps found

**Verification:**
- Unit tests pass for all comp selection scenarios
- Integration test: call Fair Value service with known block + flat_type, verify band and confidence
- Performance test: Fair Value calculation completes in < 1s for typical inputs

---

### PR5: Fair Value API & Results UI
**Branch:** `pr5-fair-value-ui`

**Goal:** Expose Fair Value as an API endpoint and build the public-facing results page with explainability and comps table.

**Scope:**
- API endpoint: `POST /api/fair-value` (accepts block, flat_type, floor_area, storey_range, time_window)
- Results page template (`templates/results.html`) showing:
  - Fair Value band (price and psm)
  - Confidence score with reasons
  - User-facing label (Fair, Slightly high, etc.)
  - Comps table (date, price, sqm, storey, model, distance)
  - Explainability: filters applied, adjustments, fallback used
  - "Last updated" timestamp (transactions dataset)
- Input form on home page to trigger Fair Value check
- HTMX integration for form submission (or simple form POST)

**Key Changes:**
- **Backend:**
  - `src/resalelens/routers/api.py` (`POST /api/fair-value`)
  - `src/resalelens/routers/public.py` (results page route)
- **Frontend:**
  - Update `templates/index.html` with input form
  - `templates/results.html` with Fair Value band, comps table, explainability
  - `static/styles.css` for results page styling (modern, clean, mobile-responsive)

**Testing Focus:**
- API endpoint returns correct Fair Value for known inputs
- Results page renders correctly with Fair Value data
- Input validation errors are handled gracefully (e.g., invalid block)
- "Last updated" timestamp reflects latest transactions ingestion

**Verification:**
- Navigate to home, input a block + flat_type, submit form
- Results page displays Fair Value band, confidence, comps, and explainability
- p95 response time < 2.5s (check logs or manual timing)

---

### PR6: Block X-Ray & Data Status Page
**Branch:** `pr6-block-xray-data-status`

**Goal:** Implement Block X-Ray page with lease, trends, MRT/amenity distances; create public Data Status page for transparency.

**Scope:**
- Block X-Ray service (`src/resalelens/services/block_xray.py`):
  - Remaining lease + lease commence year (from `blocks` table)
  - Flat mix distribution (if available)
  - Transaction trend: median psm over time (group by quarter or year)
  - Volatility indicator (variance of psm)
  - MRT/LRT distance (nearest station via Haversine or OneMap routing)
  - Amenity distances (nearest supermarket, clinic, park, mall, hawker)
  - Noise-risk proxies (distance to expressways/major roads, rail lines) — labeled as proxies
- Block X-Ray page template (`templates/block_xray.html`)
- API endpoint: `GET /api/block-xray/<block_id>`
- Data Status page (`templates/data_status.html`) showing:
  - All datasets (HDB transactions, blocks, MRT/LRT, POIs)
  - Source label, last successful ingest, next scheduled ingest, status (Healthy/Delayed/Failed)
  - If transactions > 48h delayed: show "Data delayed" badge
- Service to query ingestion_runs for Data Status page

**Key Changes:**
- **Backend:**
  - `src/resalelens/services/block_xray.py`
  - `src/resalelens/services/data_status.py` (query ingestion_runs, compute freshness)
  - `src/resalelens/routers/api.py` (`GET /api/block-xray/<block_id>`)
  - `src/resalelens/routers/public.py` (Block X-Ray page, Data Status page)
- **Frontend:**
  - `templates/block_xray.html`
  - `templates/data_status.html`
  - Update `templates/base.html` footer with link to Data Status page
  - Styling for Block X-Ray cards and Data Status table

**Testing Focus:**
- Block X-Ray service returns correct lease, trend, MRT/amenity distances for known blocks
- Transaction trend calculation aggregates correctly
- Data Status page shows correct last ingest times and statuses
- "Data delayed" badge appears when transactions > 48h delayed

**Verification:**
- Navigate to `/block/<block_id>`, verify Block X-Ray displays lease, trends, MRT/amenities with "Last updated" labels
- Navigate to `/data-status`, verify all datasets shown with correct ingest times and statuses
- Manually delay a dataset ingestion (set last ingest to 3 days ago), verify "Data delayed" badge appears

---

### PR7: Shortlist, Compare, PDF Export, Callback & Admin Lead Inbox
**Branch:** `pr7-shortlist-compare-leads`

**Goal:** Complete the buyer journey with shortlist/compare, PDF export, callback request, and admin lead management.

**Scope:**
- **Shortlist & Compare:**
  - Session-based shortlist storage (in-memory or simple DB table per session)
  - Compare page (`/compare`) showing up to 3 blocks/units side-by-side (Fair Value, lease, MRT/amenities)
  - HTMX or JavaScript for shortlist add/remove interactions
- **PDF Export:**
  - Template-driven PDF generator using WeasyPrint or ReportLab
  - Endpoint: `GET /export/pdf?shortlist=<ids>`
  - PDF includes: filters used, shortlist items + key metrics, "As of" timestamp, dataset "Last updated" timestamps, disclaimer
- **Callback Request:**
  - Form (modal or inline) with required fields (name, mobile, contact_window, budget_range, preferred_towns, flat_types, timeline)
  - Optional fields (first_timer, financing_status, notes)
  - Auto-attach filter snapshot and shortlist snapshot
  - Endpoint: `POST /api/callback-request`
  - Store in `leads` table
  - (Optional) Send email notification to admin
  - Rate limiting (max 3/IP/24h) + basic bot protection (honeypot or hCaptcha)
- **Admin Lead Inbox:**
  - Admin-only route: `/admin/leads`
  - List view of all leads (sortable by date, status)
  - Detail view with attached snapshots (filter, shortlist)
  - Minimal note field + status update (New, Contacted, Closed)
  - Admin auth required (HTTP Basic or session-based)

**Key Changes:**
- **Backend:**
  - `src/resalelens/services/pdf_export.py` (PDF generation)
  - `src/resalelens/routers/api.py` (`POST /api/callback-request`, `GET /export/pdf`)
  - `src/resalelens/routers/admin.py` (`GET /admin/leads`, `GET /admin/leads/<lead_id>`, `POST /admin/leads/<lead_id>/update`)
  - `src/resalelens/routers/public.py` (compare page route)
  - Rate limiting middleware
- **Frontend:**
  - `templates/compare.html`
  - Callback request form (modal or inline in results/compare pages)
  - `templates/admin/leads_list.html`, `templates/admin/lead_detail.html`
  - HTMX interactions for shortlist add/remove

**Testing Focus:**
- Shortlist add/remove works correctly
- Compare page displays up to 3 items side-by-side
- PDF export generates correct content with timestamps and disclaimers
- Callback request form validates required fields
- Callback requests are stored in `leads` table within 1 minute
- Rate limiting blocks excessive requests
- Admin can view, sort, and update leads

**Verification:**
- Add 3 blocks to shortlist, navigate to `/compare`, verify side-by-side display
- Download PDF, verify content and timestamps
- Submit callback request, verify entry in `leads` table and admin inbox
- Attempt 4 callback requests from same IP, verify 4th is rejected
- Log in as admin, view lead, add note, update status

---

## 6. Risks, Trade-offs, and Open Questions

### Major Risks

1. **Sparse Comps in Low-Transaction Blocks**
   - **Risk:** Some blocks may have very few or no transactions in the last 12–24 months, leading to unreliable Fair Value bands or no result.
   - **Mitigation:** Fallback ladder (same block → nearby radius → town-level); wide confidence band; clear messaging to user ("Widen time window or radius").

2. **OneMap API Rate Limits & Costs**
   - **Risk:** Routing/distance API calls may hit rate limits or incur costs, especially during high-traffic periods.
   - **Mitigation:** Aggressive caching of routing results; fallback to straight-line distance when routing fails; precompute block-to-POI distances during ingestion.

3. **Data Staleness / Delayed Ingestion**
   - **Risk:** If HDB transaction data ingestion fails or is delayed, Fair Value results may be stale, eroding user trust.
   - **Mitigation:** Data Status page with transparent freshness indicators; "Data delayed" badge when transactions > 48h old; retry logic + alerts on ingestion failure.

4. **Trust & Regulatory Concerns**
   - **Risk:** Users may mistrust Fair Value estimates or confuse them with professional valuations, leading to poor decision-making or regulatory scrutiny.
   - **Mitigation:** Clear disclaimers ("not a valuation"); transparent methodology and explainability; "Last updated" timestamps; user education on Fair Value page.

5. **Performance Under Load**
   - **Risk:** p95 latency targets (<2.5s for Fair Value, <1.5s for search) may be missed under moderate traffic.
   - **Mitigation:** Caching (comp queries, routing results); database query optimization (indexes, query tuning); horizontal scaling in Phase 4 if needed.

### Key Trade-offs

1. **FastAPI + Jinja2 vs. Next.js + API**
   - **Choice:** FastAPI + Jinja2 + HTMX for server-rendered UI
   - **Trade-off:** Simpler deployment and fewer moving parts (solo founder win) vs. richer interactivity and frontend framework maturity (Next.js)
   - **Rationale:** MVP speed and simplicity outweigh the need for heavy client-side interactivity; HTMX provides sufficient interactivity for shortlist/compare

2. **SQLite (dev) vs. PostgreSQL (prod)**
   - **Choice:** SQLite for local development, PostgreSQL for production
   - **Trade-off:** Simplified local setup vs. potential DB-specific behavior differences
   - **Rationale:** SQLite is sufficient for solo dev and testing; PostgreSQL migration is straightforward via Alembic; production needs PostgreSQL for concurrent writes and performance

3. **APScheduler (in-process) vs. Celery (external)**
   - **Choice:** APScheduler in-process for MVP
   - **Trade-off:** Simplicity and no external dependencies vs. scalability and fault isolation
   - **Rationale:** MVP traffic and ingestion frequency don't justify Celery complexity; can migrate in Phase 4 if job volume increases

4. **Comp-Based Fair Value vs. ML/Hedonic Model**
   - **Choice:** Transparent comp-based Fair Value for MVP
   - **Trade-off:** Simplicity and explainability vs. potentially more accurate ML models
   - **Rationale:** Trust and transparency are critical for MVP; ML models deferred to Phase 3 with clear evaluation and explainability frameworks

### Open Questions

1. **OneMap API Access & Costs**
   - **Question:** Does OneMap API require API key or have rate limits that may block ingestion or routing queries?
   - **Action:** Verify OneMap API terms and limits; set up API key if needed; plan for fallback to Haversine distance if routing fails.

2. **HDB Transaction Data Freshness**
   - **Question:** How frequently is HDB resale transaction data published, and is data.gov.sg API the most reliable source?
   - **Action:** Confirm data.gov.sg API update frequency; validate data completeness; consider backup CSV ingestion if API is unreliable.

3. **Admin Authentication Complexity**
   - **Question:** Is HTTP Basic Auth sufficient for admin login, or should we implement full session-based auth with password reset?
   - **Assumption:** HTTP Basic Auth or simple session-based auth (bcrypt-hashed password) is sufficient for MVP; can enhance in Phase 2 if needed.

4. **PDF Generation Library Choice**
   - **Question:** Should we use WeasyPrint (HTML/CSS to PDF) or ReportLab (programmatic PDF generation)?
   - **Recommendation:** WeasyPrint for template-driven, styled PDFs (easier to maintain consistency with web UI); ReportLab if fine-grained control is needed.

5. **Persona Filter Rules**
   - **Question:** Are the persona filter rules (first-time buyer, family, multi-gen, upgrader) sufficiently defined in the PSD, or do we need additional clarification on priorities and weights?
   - **Action:** Validate persona filter rules with PSD §6.3; implement as explicit boolean/range filters in PR7 or defer to Phase 2 if complex scoring is needed.

---

---

## Summary

This master plan establishes ResaleLens SG as a **Python-first application** (~95% Python, ~5% JavaScript) that leverages the full Python ecosystem for data processing, business logic, and web serving. The architecture is optimized for a solo founder by eliminating frontend/backend language fragmentation, build pipeline complexity, and context-switching overhead.

**Python-First Architecture Benefits:**
- ✅ **Single Language:** Unified codebase in Python across all layers (FastAPI, Jinja2, pandas, numpy, SQLAlchemy)
- ✅ **No Build Pipeline:** No npm, webpack, or frontend tooling - just Python and standard web technologies
- ✅ **Data Science Ecosystem:** Native access to pandas for transaction processing, numpy for statistical calculations (P25, P75, variance, MAD)
- ✅ **Faster Development:** Server-rendered templates + HTMX eliminate the need for separate frontend/backend coordination
- ✅ **Simpler Deployment:** Single FastAPI application serves everything (HTML, API, scheduled jobs)

**Feature Implementation Approach:**
The React prototype (`docs/design/prototype_app.jsx`) serves as a **functional reference** demonstrating the features and capabilities to build (persona selector, location search, Block X-Ray data visualizations, AI consultant modes, comparison tools, interactive charts). However, the **page layout and user flow** will follow the **customer journeys defined in PSD Section 5** (Journey A: "Is this unit fairly priced?" (based on historical transactions), Journey B: "Find blocks that fit my life", Journey C: "Request callback + export PDF"). This ensures the application is structured around user goals, not arbitrary page layouts.

**Delivery Plan:**
Phase 1 (MVP) is deliverable in 7 PRs (PR0–PR7) over 8–12 weeks. The architecture prioritizes simplicity, transparency, and solo-founder velocity while maintaining technical health and user trust. Key risks (sparse comps, API limits, data staleness) are mitigated via fallback logic, caching, and transparency features (Data Status page).

**Next steps:**
- Implement PR0 (bootstrap) using `/implement_task`
- Validate OneMap API access and HDB data sources during PR2–PR3
- Extract feature requirements from prototype_app.jsx and implement in customer journey-driven layout during PR5–PR7
- Proceed sequentially through PR1–PR7 to deliver Phase 1 MVP

