# Epic Plan: PR7 - Shortlist, Compare, PDF Export, Callback & Admin Lead Inbox

## 1. Feature/Epic Summary

### Objective
Complete the buyer journey by enabling users to shortlist blocks/units, compare them side-by-side, export professional PDF reports, and submit callback requests—all without requiring login. Implement an admin-only lead management inbox with authentication to manage incoming callback requests.

### User Impact
This epic closes the loop on the core user journeys defined in the PSD:
- **Journey C completion**: Users can save research progress (shortlist), make informed comparisons (compare view), preserve findings (PDF export), and request professional guidance (callback form)
- **Admin efficiency**: Structured lead capture with filter/shortlist context enables high-quality follow-up
- **Trust building**: PDF reports with timestamps and disclaimers provide tangible, shareable artifacts that reinforce transparency

### Dependencies
**Required PRs (must be merged first):**
- PR0 (Bootstrap): FastAPI app skeleton, CI, commands
- PR1 (Database Schema): ORM models and migrations framework
- PR2 (HDB Ingestion): Transaction and block data
- PR3 (POI/MRT Ingestion): Amenity data for Block X-Ray
- PR4 (Fair Value Engine): Core pricing logic
- PR5 (Fair Value UI): Results page and API
- PR6 (Block X-Ray & Data Status): Block intelligence and data transparency

**External Dependencies:**
- WeasyPrint library for PDF generation (HTML/CSS to PDF)
- Email provider (optional, for admin notifications)
- hCaptcha or similar (optional, for bot protection)

### Assumptions
1. **Assumption**: Shortlist state will be session-based (cookie/local storage) for MVP; persistent storage can be added in Phase 2
2. **Assumption**: Admin authentication via HTTP Basic Auth or simple session-based auth is sufficient for MVP (bcrypt-hashed passwords)
3. **Assumption**: PDF generation will use WeasyPrint (Python-based, matches existing Python-first architecture)
4. **Assumption**: Rate limiting will use simple in-memory storage (IP-based); Redis migration can occur in Phase 4 if needed
5. **Assumption**: Email notifications to admin are optional for MVP; DB-first lead capture is sufficient

---

## 2. Complexity & Fit

### Classification
**Multi-PR** (epic split into 3 sequential PRs)

### Rationale
- **Multiple user-facing features**: Shortlist, Compare, PDF Export, Callback Form—each with distinct UI/UX and backend logic
- **New authentication layer**: Admin auth is a cross-cutting concern that affects routing, middleware, and sessions
- **Multiple backend services**: PDF generation, lead capture, rate limiting, session management
- **Testing complexity**: Each feature requires unit, integration, and manual testing; splitting ensures each PR is independently testable
- **Risk management**: Callback form involves anti-spam measures (rate limiting, captcha); isolating this reduces blast radius if issues arise

### Estimated PRs
**3 PRs** (PR7a, PR7b, PR7c)

---

## 3. Full-Stack Impact

### Frontend
**Pages/components impacted:**
- **New pages**:
  - `/compare` — Side-by-side comparison view (max 3 blocks/units)
  - `/admin/leads` — Admin lead list view (authenticated)
  - `/admin/leads/<lead_id>` — Lead detail view with snapshots (authenticated)
  - `/admin/login` — Admin login page (session-based auth)
- **Modified pages**:
  - `templates/results.html` — Add "Add to Shortlist" button, callback request trigger
  - `templates/block_xray.html` — Add "Add to Shortlist" button, callback request trigger
  - `templates/base.html` — Add shortlist counter in header/nav, logout link for admin
- **New components**:
  - Shortlist widget (header badge showing count + quick access)
  - Callback request modal/form (can be modal or inline)
  - PDF export button/link

**UI states required:**
- Empty shortlist (show prompt to add blocks)
- Shortlist with 1-3 items (enable compare)
- Compare view with 2-3 items side-by-side
- Callback form validation errors (inline + summary)
- Rate limit exceeded message (after 3 requests/IP/24h)
- Admin login success/failure
- Admin lead inbox loading/empty/populated states

**Navigation/entry points:**
- Shortlist accessible from header/nav
- "Add to Shortlist" buttons on results and Block X-Ray pages
- "Compare" enabled when shortlist ≥ 2 items
- "Download PDF" button on compare page
- "Request Callback" accessible from results, Block X-Ray, compare pages
- Admin login from `/admin/login`; admin inbox from `/admin/leads`

### Backend
**APIs to add/modify:**
- **Shortlist Management**:
  - `POST /api/shortlist/add` — Add block/unit to session-based shortlist
  - `POST /api/shortlist/remove` — Remove from shortlist
  - `GET /api/shortlist` — Retrieve current shortlist items
- **Compare**:
  - `GET /compare` — Render compare page with shortlist data (server-side)
- **PDF Export**:
  - `GET /export/pdf` — Generate and download PDF report (query params: shortlist IDs, filters)
- **Callback Request**:
  - `POST /api/callback-request` — Submit callback form; store in `leads` table
- **Admin Lead Inbox**:
  - `GET /admin/leads` — List all leads (sortable, paginated)
  - `GET /admin/leads/<lead_id>` — Lead detail with snapshots
  - `POST /admin/leads/<lead_id>/update` — Update status/notes
- **Admin Auth**:
  - `POST /admin/login` — Session-based login (bcrypt password check)
  - `POST /admin/logout` — Session invalidation
  - `GET /admin/login` — Login page

**Services/modules impacted:**
- **New services**:
  - `src/resalelens/services/pdf_export.py` — PDF generation logic (WeasyPrint)
  - `src/resalelens/services/shortlist.py` — Session-based shortlist management
  - `src/resalelens/services/lead_capture.py` — Lead validation, storage, notification
- **New middleware**:
  - `src/resalelens/middleware/rate_limit.py` — Rate limiting for callback requests
  - `src/resalelens/middleware/auth.py` — Admin authentication check
- **Router updates**:
  - `src/resalelens/routers/api.py` — Add shortlist, callback endpoints
  - `src/resalelens/routers/admin.py` — Add leads management, login/logout
  - `src/resalelens/routers/public.py` — Add compare page route

**Validation/auth/error-handling concerns:**
- **Callback form validation**: Required fields (name, mobile, contact window, budget, towns, flat types, timeline); mobile format (SG +65)
- **Rate limiting**: Max 3 callback requests per IP per 24 hours (in-memory tracker with TTL)
- **Admin auth**: Session-based authentication (HTTP-only, Secure, SameSite=Lax cookies); bcrypt password verification
- **CSRF protection**: CSRF tokens for admin forms
- **Anti-spam**: Honeypot field + optional hCaptcha for callback form
- **PDF generation errors**: Handle WeasyPrint failures gracefully; return 500 with friendly message

### Data
**Entities/tables/fields involved:**
- **Modified**: None (schema already defined in PR1)
- **Used**:
  - `leads` table — Store callback requests
    - Fields: `lead_id`, `name`, `mobile`, `contact_window`, `budget_range`, `preferred_towns`, `flat_types`, `timeline`, `first_timer`, `financing_status`, `notes`, `filter_snapshot` (JSON), `shortlist_snapshot` (JSON), `created_at`, `status` (enum: New/Contacted/Closed)
  - `users` table (admin) — Admin authentication
    - Fields: `id`, `email`, `hashed_password`, `created_at`

**Migrations/backfills needed:**
- No new migrations required (schema defined in PR1)
- **Seed data (development only)**: Create 1 admin user via script (`scripts/create_admin.py`)

**Compatibility strategy:**
- No schema changes; backward-compatible with existing data

### Infra / Config
**Env vars/secrets:**
- `ADMIN_USERNAME` (admin email for login)
- `ADMIN_PASSWORD_HASH` (bcrypt-hashed admin password)
- `SECRET_KEY` (for session signing; already defined in PR0)
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` (optional, for email notifications)
- `HCAPTCHA_SECRET_KEY` (optional, for bot protection)

**Feature flags (if needed):**
- No feature flags for MVP (all features enabled once deployed)

**CI/CD or deployment considerations:**
- Add `weasyprint` dependency to `pyproject.toml` (note: requires system-level dependencies like `libpango`, `libcairo` on Linux)
- Update README with admin user creation instructions
- Ensure deployment environment has WeasyPrint dependencies installed (Docker or platform-specific)

---

## 4. PR Roadmap

### PR 7a: Shortlist & Compare

#### Goal
Enable users to build a shortlist of blocks/units and view them side-by-side in a comparison table, facilitating informed decision-making.

#### Scope
**In scope:**
- Session-based shortlist storage (cookie or server-side session)
- "Add to Shortlist" buttons on results and Block X-Ray pages
- Shortlist widget in header/nav showing count
- Compare page (`/compare`) showing up to 3 items side-by-side with Fair Value, lease, MRT/amenities
- HTMX interactions for add/remove (or simple form POST + HTMX swap)

**Out of scope:**
- Persistent shortlist storage (deferred to Phase 2 with user accounts)
- PDF export (PR7b)
- Callback request (PR7c)
- Admin features (PR7c)

#### Backend Changes
**APIs:**
- `POST /api/shortlist/add` — Add block/unit ID to session shortlist (returns updated count)
- `POST /api/shortlist/remove` — Remove item from shortlist
- `GET /api/shortlist` — Return shortlist items as JSON

**Services:**
- `src/resalelens/services/shortlist.py`:
  - `add_to_shortlist(session, block_id, unit_attrs)` — Store in session (max 10 items)
  - `remove_from_shortlist(session, item_id)`
  - `get_shortlist(session)` — Return list of items with basic metadata (block, flat_type, price)

**Session management:**
- Use FastAPI's session middleware (e.g., `starlette.middleware.sessions.SessionMiddleware`) with signed cookies
- Store shortlist as JSON array in session: `[{"block": "123", "street": "Main St", "flat_type": "4-ROOM", "fair_value": 450000}, ...]`

#### Frontend Changes
**Templates:**
- `templates/results.html` — Add "Add to Shortlist" button (HTMX post to `/api/shortlist/add`)
- `templates/block_xray.html` — Add "Add to Shortlist" button
- `templates/base.html` — Add shortlist badge in header (`<span hx-get="/api/shortlist/count" hx-trigger="load">0</span>`)
- `templates/compare.html` (new):
  - Side-by-side table with columns: Block/Address, Fair Value (band), Confidence, Lease Remaining, Nearest MRT (distance/time), Amenities Summary
  - Max 3 items; if shortlist < 2, show "Add more to compare"
  - "Remove" button for each item (HTMX post to `/api/shortlist/remove`)

**Styling:**
- Comparison table: responsive (stacked on mobile), semantic colors (green for favorable metrics, red for unfavorable)
- Shortlist badge: prominent in header, updates dynamically via HTMX

**HTMX integration:**
- `hx-post="/api/shortlist/add"` on "Add to Shortlist" button
- `hx-swap="outerHTML"` to replace button with "Added ✓" confirmation
- `hx-get="/api/shortlist/count"` to update badge count

#### Data Changes
No schema changes; session storage only.

#### Infra / Config
- Add `starlette` session middleware configuration to `src/resalelens/main.py`
- Update `.env.example` with `SECRET_KEY` requirement (already in PR0)

#### Testing
**Unit tests:**
- `tests/services/test_shortlist.py`:
  - `test_add_to_shortlist_success` — Add item, verify in session
  - `test_add_to_shortlist_max_items` — Add 11 items, verify max 10 enforced
  - `test_remove_from_shortlist` — Remove item, verify removal
  - `test_get_shortlist_empty` — Empty shortlist returns `[]`

**Integration/API tests:**
- `tests/test_api.py`:
  - `test_shortlist_add_endpoint` — POST to `/api/shortlist/add`, verify 200 + updated count
  - `test_shortlist_remove_endpoint` — POST to `/api/shortlist/remove`, verify removal
  - `test_compare_page_with_shortlist` — GET `/compare` with 3 items in session, verify rendering

**UI/e2e tests:**
- Manual testing (see Verification)

**Manual checks:**
- Add 3 blocks from results page, verify shortlist badge updates
- Navigate to `/compare`, verify side-by-side display
- Remove 1 item, verify comparison updates
- Clear session, verify shortlist resets

#### Verification
**Commands:**
- Install: `uv sync`
- Dev: `uv run uvicorn src.resalelens.main:app --reload`
- Test: `uv run pytest tests/services/test_shortlist.py tests/test_api.py -v`
- Lint: `uv run ruff check .`
- Typecheck: `uv run mypy src/`
- Build: Not applicable (no build step for server-rendered app)

**Manual verification checklist:**
1. Start dev server, navigate to `/` (home)
2. Run a Fair Value check, click "Add to Shortlist" on results page → Verify badge count updates to 1
3. Navigate to Block X-Ray, click "Add to Shortlist" → Verify badge count updates to 2
4. Add a third block → Badge shows 3
5. Click "Compare" in header/nav → Verify `/compare` shows 3 blocks side-by-side with Fair Value, lease, MRT, amenities
6. Click "Remove" on one block → Verify it's removed and comparison updates
7. Clear browser session/cookies → Verify shortlist resets to 0

**Expected results:**
- Shortlist badge shows correct count
- Compare page renders correctly with side-by-side layout
- HTMX interactions are smooth (no full page reloads)
- Empty shortlist shows helpful prompt ("Add blocks to compare")

#### Rollback Plan
**Revert strategy:**
- Revert PR7a merge commit
- Session storage is ephemeral; no data cleanup needed
- No migrations to rollback

**Feature flag / kill switch:**
- Not applicable (no flag for MVP)

#### Dependencies
**PRs that must be merged before this one:**
- PR0, PR1, PR2, PR3, PR4, PR5, PR6 (all previous PRs)

**External dependencies:**
- `starlette` session middleware (already included in FastAPI)

#### Risks & Mitigations
**Risks:**
1. **Session storage size limits**: Browser cookies have size limits (~4KB); 10-item shortlist may exceed this
   - **Mitigation**: Store only minimal data (block ID, flat_type) in session; fetch full details on-demand. Alternatively, use server-side session storage (e.g., Redis in Phase 4)

2. **Session expiry/loss**: Users lose shortlist if they clear cookies or session expires
   - **Mitigation**: Set session TTL to 24 hours; add "Export PDF" in PR7b to preserve state. Phase 2 will add persistent storage with user accounts

3. **HTMX browser compatibility**: Older browsers may not support HTMX dynamic swaps
   - **Mitigation**: HTMX degrades gracefully to standard form POST; ensure buttons work without JavaScript

---

### PR 7b: PDF Export

#### Goal
Enable users to download a professionally formatted PDF report of their research, including shortlist, filters, key metrics, timestamps, and disclaimers.

#### Scope
**In scope:**
- PDF generation service using WeasyPrint (Python-based, HTML/CSS to PDF)
- PDF template (`templates/pdf_report.html`) styled with print-friendly CSS
- Endpoint: `GET /export/pdf?shortlist=<ids>` (query params include filter state)
- PDF content:
  - Cover page with "ResaleLens SG Report" + "As of" timestamp
  - Filters used (persona, budget, towns, flat types, time window)
  - Shortlist items (block, address, Fair Value band, confidence, lease, MRT/amenities summary)
  - Comps table for each shortlist item (optional; can be truncated to top 5 comps)
  - Dataset "Last updated" timestamps (transactions, blocks, POIs, MRT)
  - Disclaimer: "This is an analytics estimate for decision support, not a professional valuation."
- "Download PDF" button on compare page

**Out of scope:**
- Callback request (PR7c)
- Admin features (PR7c)
- PDF customization (e.g., user branding, custom notes) — deferred to Phase 2+

#### Backend Changes
**APIs:**
- `GET /export/pdf` — Generate PDF and return as downloadable file
  - Query params: `shortlist` (comma-separated block IDs), `filters` (JSON-encoded filter state)
  - Response: PDF file with `Content-Disposition: attachment; filename="ResaleLens_Report_2026-01-10.pdf"`

**Services:**
- `src/resalelens/services/pdf_export.py`:
  - `generate_pdf_report(shortlist_items, filters, data_status)` → bytes (PDF file)
  - Uses WeasyPrint: `HTML(string=html).write_pdf()`
  - Template: `templates/pdf_report.html` (Jinja2 template rendered to HTML, then to PDF)
  - Styling: `static/styles_pdf.css` (print-friendly: no interactive elements, high-contrast, page breaks)

**Dependencies:**
- Add `weasyprint` to `pyproject.toml`
- WeasyPrint requires system-level dependencies (`libpango`, `libcairo` on Linux; install via package manager or Docker)

#### Frontend Changes
**Templates:**
- `templates/compare.html` — Add "Download PDF" button linking to `/export/pdf?shortlist=...`
- `templates/pdf_report.html` (new):
  - Cover page with logo (optional), title, "As of" timestamp
  - Filters summary section
  - Shortlist items section (table or cards)
  - Dataset timestamps section
  - Disclaimer section (footer)

**Styling:**
- `static/styles_pdf.css` (new):
  - Print-friendly layout (A4 page size, margins, page breaks)
  - High-contrast text (black on white)
  - No interactive elements (buttons, links)
  - Use system fonts (serif for body, sans-serif for headings)

#### Data Changes
No schema changes; PDF generation is read-only.

#### Infra / Config
**Dependencies:**
- Add `weasyprint>=62.0` to `pyproject.toml`
- Update deployment docs with WeasyPrint system dependencies:
  - **macOS**: `brew install pango cairo`
  - **Ubuntu/Debian**: `apt-get install libpango-1.0-0 libcairo2`
  - **Docker**: Add to Dockerfile (see example in docs)

**Config:**
- No new env vars required

#### Testing
**Unit tests:**
- `tests/services/test_pdf_export.py`:
  - `test_generate_pdf_report_success` — Mock shortlist + filters, verify PDF bytes returned
  - `test_pdf_report_includes_disclaimer` — Verify disclaimer text in generated PDF
  - `test_pdf_report_timestamps` — Verify "As of" and dataset timestamps are included

**Integration/API tests:**
- `tests/test_api.py`:
  - `test_export_pdf_endpoint` — GET `/export/pdf?shortlist=123,456`, verify 200 + PDF content type
  - `test_export_pdf_empty_shortlist` — Verify error message if shortlist is empty

**UI/e2e tests:**
- Manual testing (see Verification)

**Manual checks:**
- Add 3 blocks to shortlist, navigate to `/compare`
- Click "Download PDF" → PDF downloads with correct filename
- Open PDF → Verify cover page, filters, shortlist items, comps, timestamps, disclaimer
- Check PDF print quality (margins, fonts, page breaks)

#### Verification
**Commands:**
- Install: `uv sync` (installs WeasyPrint)
- Dev: `uv run uvicorn src.resalelens.main:app --reload`
- Test: `uv run pytest tests/services/test_pdf_export.py tests/test_api.py::test_export_pdf_endpoint -v`
- Lint: `uv run ruff check .`
- Typecheck: `uv run mypy src/`
- Build: Not applicable

**Manual verification checklist:**
1. Add 3 blocks to shortlist
2. Navigate to `/compare`
3. Click "Download PDF" button → Verify PDF downloads with filename `ResaleLens_Report_YYYY-MM-DD.pdf`
4. Open PDF in viewer:
   - **Cover page**: Title, "As of" timestamp (current date/time)
   - **Filters section**: Displays persona, budget, towns, flat types used (or "N/A" if default)
   - **Shortlist section**: 3 blocks with Fair Value band, confidence, lease, MRT/amenities summary
   - **Comps tables** (optional): Top 5 comps for each block
   - **Dataset timestamps**: Shows "Transactions last updated: YYYY-MM-DD HH:MM", "POIs last updated: ...", etc.
   - **Disclaimer**: "This is an analytics estimate for decision support, not a professional valuation."
5. Verify PDF print quality: margins are correct, text is readable, no cut-off content

**Expected results:**
- PDF downloads successfully
- PDF contains all required sections with accurate data
- PDF is print-friendly (A4, good margins, readable fonts)

#### Rollback Plan
**Revert strategy:**
- Revert PR7b merge commit
- No database changes; no cleanup needed
- If WeasyPrint causes deployment issues, temporarily disable PDF export endpoint (return 503)

**Feature flag / kill switch:**
- Not applicable (no flag for MVP)

#### Dependencies
**PRs that must be merged before this one:**
- PR7a (Shortlist & Compare) — PDF export depends on shortlist data structure

**External dependencies:**
- WeasyPrint library (Python package)
- System-level dependencies (`libpango`, `libcairo`)

#### Risks & Mitigations
**Risks:**
1. **WeasyPrint installation complexity**: System dependencies may fail on some platforms (especially Docker/cloud)
   - **Mitigation**: Provide clear installation instructions for macOS, Linux, Docker. Test on target deployment platform before merging.

2. **PDF generation performance**: Large shortlists (with many comps) may cause slow PDF generation (>5s)
   - **Mitigation**: Limit comps per block to 5 in PDF; add loading spinner in UI ("Generating PDF...")

3. **WeasyPrint rendering errors**: Complex CSS may not render correctly in PDF
   - **Mitigation**: Use simple, print-friendly CSS; test with multiple shortlist sizes and edge cases (empty filters, missing data)

4. **PDF file size**: Large PDFs may exceed browser download limits or cause slow downloads
   - **Mitigation**: Optimize images (use SVG for logos); limit comps per block; compress PDF (WeasyPrint default compression is sufficient)

---

### PR 7c: Callback Request & Admin Lead Inbox

#### Goal
Enable users to submit callback requests with structured lead capture, implement rate limiting and anti-spam measures, and provide an admin-only lead management inbox with authentication.

#### Scope
**In scope:**
- **Callback request form** (modal or inline) with required/optional fields per PSD §6.5.1
- **Lead capture API**: `POST /api/callback-request` (stores in `leads` table)
- **Rate limiting**: Max 3 requests per IP per 24 hours (in-memory tracker)
- **Anti-spam**: Honeypot field (hidden input; bot detection if filled) + optional hCaptcha
- **Auto-attach context**: Filter snapshot (JSON) + shortlist snapshot (JSON) attached to lead
- **Admin authentication**: Session-based login (bcrypt password check) at `/admin/login`
- **Admin Lead Inbox**: `/admin/leads` (list view) and `/admin/leads/<lead_id>` (detail view)
- **Lead management**: Admin can view, add notes, update status (New/Contacted/Closed)
- **Optional email notification**: Send email to admin when new lead submitted (configurable via env var)

**Out of scope:**
- Lead export/download (deferred to Phase 2)
- Email to user (confirmation email) — deferred to Phase 2
- CRM integration (Phase 3+)
- Advanced anti-spam (reCAPTCHA v3, ML-based bot detection) — can be added if spam becomes an issue

#### Backend Changes
**APIs:**
- **Callback Request**:
  - `POST /api/callback-request` — Submit callback form
    - Request body: `{name, mobile, contact_window, budget_range, preferred_towns, flat_types, timeline, first_timer?, financing_status?, notes?, filter_snapshot, shortlist_snapshot}`
    - Response: `201 Created` + `{lead_id}` or `429 Too Many Requests` if rate limit exceeded
- **Admin Auth**:
  - `POST /admin/login` — Login with username + password (bcrypt check); create session
  - `POST /admin/logout` — Destroy session
  - `GET /admin/login` — Login page (if not authenticated)
- **Admin Lead Inbox**:
  - `GET /admin/leads` — List all leads (sortable by `created_at`, `status`; paginated if >50 leads)
  - `GET /admin/leads/<lead_id>` — Lead detail with snapshots
  - `POST /admin/leads/<lead_id>/update` — Update status and/or notes

**Services:**
- `src/resalelens/services/lead_capture.py`:
  - `create_lead(lead_data)` — Validate, store in `leads` table, trigger optional email notification
  - `send_admin_notification(lead)` — Send email to admin (optional; uses SMTP)
- `src/resalelens/services/auth.py`:
  - `authenticate_admin(username, password)` — Verify bcrypt password hash
  - `create_session(user_id)` — Create session cookie
  - `get_current_admin(session)` — Retrieve admin from session (for protected routes)

**Middleware:**
- `src/resalelens/middleware/rate_limit.py`:
  - Track IP-based request counts (in-memory dict with TTL)
  - Structure: `{"<ip>": {"count": 3, "expires_at": <timestamp>}}`
  - If count ≥ 3, return `429 Too Many Requests`
- `src/resalelens/middleware/auth.py`:
  - Check session for admin routes (`/admin/*` except `/admin/login`)
  - If not authenticated, redirect to `/admin/login`

**Validation:**
- **Mobile format**: Validate SG mobile format (`+65 XXXX XXXX` or `XXXXXXXX`)
- **Required fields**: name, mobile, contact_window, budget_range, preferred_towns, flat_types, timeline
- **Optional fields**: first_timer, financing_status, notes
- **Honeypot**: Hidden field `website`; if filled, reject as bot (return 200 but don't store)

#### Frontend Changes
**Templates:**
- **Callback Request Form** (modal or inline):
  - `templates/callback_form.html` (can be included in results/compare/Block X-Ray pages)
  - Form fields:
    - Name (text, required)
    - Mobile (tel, required, placeholder: "+65 XXXX XXXX")
    - Contact window (select, required: "Weekday AM/PM", "Weekend AM/PM", "Anytime")
    - Budget range (select, required: presets like "< $300k", "$300k-$500k", "$500k-$700k", "> $700k")
    - Preferred towns (multi-select, required)
    - Flat types (multi-select, required: 2-ROOM, 3-ROOM, 4-ROOM, 5-ROOM, EXECUTIVE)
    - Timeline (select, required: "0-3 months", "3-6 months", "6-12 months", "12+ months")
    - First-timer (checkbox, optional)
    - Financing status (select, optional: "IPA approved", "In progress", "Not started")
    - Notes (textarea, optional, max 500 chars)
    - Hidden honeypot field: `<input type="text" name="website" style="display:none">`
  - Auto-attach filter snapshot and shortlist snapshot (hidden inputs populated via JavaScript)
  - Submit button: "Request Callback"
  - HTMX: `hx-post="/api/callback-request"` with `hx-swap="outerHTML"` to show success message

- **Admin Login**:
  - `templates/admin/login.html`:
    - Form: username (email), password
    - Submit button: "Login"
    - CSRF token (use FastAPI CSRF middleware or manual token)

- **Admin Lead Inbox**:
  - `templates/admin/leads_list.html`:
    - Table: Lead ID, Name, Mobile, Budget Range, Timeline, Created At, Status
    - Sortable columns (created_at desc by default)
    - Click row → navigate to `/admin/leads/<lead_id>`
  - `templates/admin/lead_detail.html`:
    - Lead info (name, mobile, contact window, budget, towns, flat types, timeline)
    - Optional info (first-timer, financing status, notes)
    - Filter snapshot (JSON formatted or summarized)
    - Shortlist snapshot (list of blocks/units)
    - Status dropdown (New, Contacted, Closed) + "Update" button
    - Admin notes field (textarea) + "Save" button
    - Timestamps (created_at)

**Styling:**
- Callback form: modal or inline, mobile-friendly, clear validation errors
- Admin login: centered form, simple and clean
- Admin inbox: table layout, responsive (stacked on mobile), semantic colors (New = blue, Contacted = yellow, Closed = gray)

**HTMX integration:**
- Callback form: `hx-post="/api/callback-request"` to submit without page reload
- Success message: Replace form with "Thank you! We'll contact you within 24 hours."
- Error message: Show validation errors inline (field-level) and summary at top

#### Data Changes
No schema changes; `leads` and `users` tables already defined in PR1.

**Seed data (development):**
- Create admin user via script:
  - `scripts/create_admin.py` — Prompt for username + password, hash with bcrypt, insert into `users` table

#### Infra / Config
**Env vars:**
- `ADMIN_USERNAME` (e.g., `admin@resalelens.sg`)
- `ADMIN_PASSWORD_HASH` (bcrypt hash; generate via `scripts/create_admin.py`)
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` (optional, for email notifications)
- `HCAPTCHA_SECRET_KEY` (optional, for bot protection)

**Feature flags:**
- `ENABLE_EMAIL_NOTIFICATIONS` (bool, default: False) — If True, send email to admin on new lead

**Dependencies:**
- Add `bcrypt` to `pyproject.toml` (for password hashing)
- Add `python-multipart` (for form data parsing in FastAPI)
- Add `aiosmtplib` (optional, for async SMTP email sending)

#### Testing
**Unit tests:**
- `tests/services/test_lead_capture.py`:
  - `test_create_lead_success` — Valid lead data, verify insert into `leads` table
  - `test_create_lead_missing_required_field` — Verify validation error
  - `test_create_lead_honeypot_filled` — Honeypot filled, verify lead not stored (bot detected)
  - `test_send_admin_notification` — Mock SMTP, verify email sent (if enabled)

- `tests/services/test_auth.py`:
  - `test_authenticate_admin_success` — Correct password, verify session created
  - `test_authenticate_admin_wrong_password` — Verify failure
  - `test_get_current_admin` — Valid session, verify admin returned

- `tests/middleware/test_rate_limit.py`:
  - `test_rate_limit_allows_3_requests` — 3 requests from same IP, verify all succeed
  - `test_rate_limit_blocks_4th_request` — 4th request, verify 429 response
  - `test_rate_limit_resets_after_24h` — Mock time, verify counter resets after 24h

**Integration/API tests:**
- `tests/test_api.py`:
  - `test_callback_request_endpoint_success` — POST valid lead data, verify 201 + lead in DB
  - `test_callback_request_rate_limit` — POST 4 requests from same IP, verify 4th returns 429
  - `test_admin_login_success` — POST correct credentials, verify session cookie set
  - `test_admin_login_wrong_password` — POST wrong credentials, verify error
  - `test_admin_leads_list_requires_auth` — GET `/admin/leads` without session, verify redirect to `/admin/login`
  - `test_admin_leads_list_authenticated` — GET `/admin/leads` with session, verify lead list
  - `test_admin_lead_detail` — GET `/admin/leads/<lead_id>` with session, verify detail view
  - `test_admin_update_lead_status` — POST to `/admin/leads/<lead_id>/update`, verify status updated

**UI/e2e tests:**
- Manual testing (see Verification)

**Manual checks:**
- Submit callback request, verify entry in `leads` table and admin inbox
- Submit 4 requests from same IP, verify 4th is blocked
- Fill honeypot field, verify request is silently ignored
- Admin login with correct/wrong password, verify success/failure
- Admin view lead detail, add note, update status, verify saved

#### Verification
**Commands:**
- Install: `uv sync`
- Dev: `uv run uvicorn src.resalelens.main:app --reload`
- Test: `uv run pytest tests/services/test_lead_capture.py tests/services/test_auth.py tests/middleware/test_rate_limit.py tests/test_api.py::test_callback_request_endpoint_success tests/test_api.py::test_admin_login_success -v`
- Lint: `uv run ruff check .`
- Typecheck: `uv run mypy src/`
- Build: Not applicable
- **Create admin user**: `uv run python scripts/create_admin.py` (prompts for username + password)

**Manual verification checklist:**
1. **Callback Request (Buyer Journey)**:
   - Navigate to `/results` or `/block/<block_id>`
   - Click "Request Callback" → Form opens (modal or inline)
   - Fill all required fields (name, mobile, contact window, budget, towns, flat types, timeline)
   - Submit → Verify success message ("Thank you! We'll contact you within 24 hours.")
   - Check database: `SELECT * FROM leads ORDER BY created_at DESC LIMIT 1;` → Verify lead exists with correct data
   - Verify filter_snapshot and shortlist_snapshot are populated (JSON)

2. **Rate Limiting**:
   - Submit 3 callback requests from same browser (use different names)
   - Attempt 4th request → Verify error message ("You've reached the maximum number of requests. Please try again in 24 hours.")

3. **Honeypot (Bot Detection)**:
   - Open browser dev tools, find honeypot field (`name="website"`)
   - Fill honeypot field with text, submit → Verify success message is shown BUT lead is NOT in database (bot detected)

4. **Admin Login**:
   - Navigate to `/admin/leads` (not logged in) → Verify redirect to `/admin/login`
   - On login page, enter correct username + password → Submit
   - Verify redirect to `/admin/leads` (now authenticated)
   - Attempt wrong password → Verify error message ("Invalid username or password")

5. **Admin Lead Inbox (List View)**:
   - Navigate to `/admin/leads` (authenticated)
   - Verify all leads displayed in table (sorted by created_at desc)
   - Verify columns: Lead ID, Name, Mobile, Budget Range, Timeline, Created At, Status
   - Click on a lead row → Navigate to `/admin/leads/<lead_id>`

6. **Admin Lead Detail**:
   - On lead detail page, verify all lead info displayed:
     - Name, mobile, contact window, budget, towns, flat types, timeline
     - First-timer status, financing status, notes (if provided)
     - Filter snapshot (formatted as bullet list or JSON)
     - Shortlist snapshot (list of blocks/units)
   - Update status dropdown (e.g., from "New" to "Contacted") → Click "Update" → Verify status saved
   - Add admin note in textarea → Click "Save" → Verify note saved

7. **Admin Logout**:
   - Click "Logout" in header → Verify redirect to `/admin/login` and session destroyed
   - Attempt to access `/admin/leads` → Verify redirect to `/admin/login`

8. **Email Notification (Optional, if enabled)**:
   - Set `ENABLE_EMAIL_NOTIFICATIONS=true` in `.env.local`
   - Configure SMTP settings (`SMTP_HOST`, etc.)
   - Submit callback request → Verify email received at admin inbox with lead details

**Expected results:**
- Callback requests are stored in `leads` table within 1 minute
- Rate limiting blocks 4th request from same IP
- Honeypot silently rejects bot submissions
- Admin can log in, view leads, update status/notes
- Admin inbox is sorted by created_at (most recent first)
- Email notification is sent (if enabled)

#### Rollback Plan
**Revert strategy:**
- Revert PR7c merge commit
- No schema changes; `leads` table may contain test data but can be left (or truncated via SQL)
- Admin user can be deleted from `users` table if needed

**Feature flag / kill switch:**
- Temporarily disable callback endpoint: comment out route registration in `src/resalelens/routers/api.py` or return 503

#### Dependencies
**PRs that must be merged before this one:**
- PR7a (Shortlist & Compare) — Callback form auto-attaches shortlist snapshot
- PR7b (PDF Export) — No strict dependency, but callback form is more useful after PDF export is available

**External dependencies:**
- `bcrypt` (password hashing)
- `python-multipart` (form data parsing)
- `aiosmtplib` (optional, for email notifications)
- hCaptcha (optional, for stronger bot protection)

#### Risks & Mitigations
**Risks:**
1. **Lead spam**: Even with rate limiting + honeypot, determined bots or malicious users may spam callback requests
   - **Mitigation**: 
     - Rate limiting (max 3/IP/24h) blocks bulk spam
     - Honeypot catches basic bots
     - Optional hCaptcha can be added if spam becomes an issue
     - Admin can mark leads as "Spam" status (add to status enum if needed)

2. **Session security**: Session cookies could be hijacked if not properly secured
   - **Mitigation**: 
     - Use HTTP-only, Secure, SameSite=Lax cookies
     - Set session TTL to 8 hours (admin must re-login after 8h)
     - Use strong SECRET_KEY (configured in `.env.local`, not committed)

3. **Admin password exposure**: Storing bcrypt hash in env var is less secure than dedicated secrets management
   - **Mitigation**: For MVP, this is acceptable (solo founder); Phase 2+ can migrate to proper secrets management (e.g., AWS Secrets Manager, 1Password)

4. **Email deliverability**: SMTP emails may be rejected as spam or fail to send
   - **Mitigation**: 
     - Use reputable SMTP provider (e.g., SendGrid, Mailgun, AWS SES)
     - Email is optional; DB-first ensures leads are never lost
     - Add email retry logic (3 attempts with backoff)

5. **Rate limiting accuracy**: In-memory IP tracker is lost on server restart; distributed systems need Redis
   - **Mitigation**: For MVP (single server), in-memory is sufficient; Phase 4 migration to Redis will solve this

---

## 5. Milestones & Sequence

### Milestone 1: Shortlist & Comparison (PR7a)
**What it unlocks:**
- Users can build a personal shortlist of candidate blocks/units
- Side-by-side comparison enables data-driven decision-making
- Foundation for PDF export (PR7b) and callback context (PR7c)

**PRs included:**
- PR7a

**"Done" means:**
- Users can add/remove blocks from shortlist via HTMX interactions
- Compare page displays up to 3 items side-by-side with Fair Value, lease, MRT/amenities
- Shortlist badge in header updates dynamically
- All tests pass (unit, integration)
- Manual verification confirms smooth UX

---

### Milestone 2: PDF Export (PR7b)
**What it unlocks:**
- Users can preserve and share their research findings
- Professional reports build trust and credibility
- PDF serves as tangible proof-of-work for ResaleLens value

**PRs included:**
- PR7b

**"Done" means:**
- Users can download generated PDF reports from compare page
- PDF includes cover page, filters, shortlist, comps, timestamps, disclaimer
- PDF is print-friendly (A4, good margins, readable fonts)
- WeasyPrint is successfully installed and tested on target deployment platform
- All tests pass

---

### Milestone 3: Lead Capture & Admin Inbox (PR7c)
**What it unlocks:**
- Users can request professional guidance via callback form
- Admin can efficiently manage and follow up on leads
- Anti-spam measures protect system integrity
- Admin authentication secures sensitive lead data

**PRs included:**
- PR7c

**"Done" means:**
- Users can submit callback requests with required/optional fields
- Rate limiting (max 3/IP/24h) and honeypot are active
- Callback requests are stored in `leads` table within 1 minute
- Admin can log in, view leads, update status/notes
- Email notifications work (if enabled)
- All tests pass (unit, integration, manual)

---

## 6. Risks, Trade-offs, and Open Questions

### Major Risks

1. **Session Storage Scalability**
   - **Risk**: Session-based shortlist storage may hit size limits with large shortlists (>10 items) or complex filter state
   - **Mitigation**: Limit shortlist to 10 items; store only minimal data (block ID, flat_type) in session; fetch full details on-demand. Phase 2 will add persistent storage with user accounts.

2. **WeasyPrint Installation Complexity**
   - **Risk**: System-level dependencies (`libpango`, `libcairo`) may fail on some cloud platforms or Docker environments
   - **Mitigation**: Test WeasyPrint installation on target deployment platform (Railway, Render, AWS) before finalizing PR7b. Provide clear docs with platform-specific instructions. Use official WeasyPrint Docker image if needed.

3. **PDF Generation Performance**
   - **Risk**: Generating PDFs for large shortlists (with many comps) may take >5 seconds, causing poor UX
   - **Mitigation**: Limit comps per block to 5 in PDF template; add loading spinner/progress indicator in UI. Monitor p95 latency; if >5s, implement async PDF generation (background job) in Phase 4.

4. **Lead Spam and Abuse**
   - **Risk**: Even with rate limiting + honeypot, determined spammers may flood callback requests
   - **Mitigation**: 
     - Rate limiting (3/IP/24h) blocks bulk spam
     - Honeypot catches basic bots
     - Optional hCaptcha can be added post-launch if spam becomes an issue
     - Admin can manually mark leads as spam and filter them out

5. **Admin Session Security**
   - **Risk**: Session cookies could be hijacked (XSS, CSRF) if not properly secured
   - **Mitigation**: 
     - Use HTTP-only, Secure, SameSite=Lax cookies
     - Implement CSRF tokens for admin forms
     - Set session TTL to 8 hours (force re-login)
     - Use strong SECRET_KEY (32+ random chars) in production

6. **Email Deliverability (if enabled)**
   - **Risk**: Admin notification emails may be marked as spam or fail to send
   - **Mitigation**: 
     - Use reputable SMTP provider (SendGrid, Mailgun, AWS SES)
     - Email is optional; DB-first ensures leads are never lost
     - Add retry logic (3 attempts with exponential backoff)
     - Monitor email logs and deliverability metrics

### Key Trade-offs

1. **Session-Based Shortlist vs. Persistent Storage**
   - **Choice**: Session-based shortlist (ephemeral) for MVP
   - **Trade-off**: Simplicity and no login requirement (buyer wins) vs. risk of losing shortlist on session expiry (mitigated by PDF export)
   - **Rationale**: Aligns with PSD goal of "no buyer login for Phase 1"; persistent storage can be added in Phase 2 when user accounts are introduced

2. **WeasyPrint vs. ReportLab for PDF Generation**
   - **Choice**: WeasyPrint (HTML/CSS to PDF)
   - **Trade-off**: Template-driven consistency with web UI (easier maintenance) vs. slightly slower generation and system dependency complexity
   - **Rationale**: WeasyPrint allows reuse of Jinja2 templates and CSS, reducing code duplication; Python-first architecture preference; installation complexity is manageable with clear docs

3. **In-Memory Rate Limiting vs. Redis**
   - **Choice**: In-memory rate limiting for MVP
   - **Trade-off**: Simplicity (no external dependencies) vs. rate limit reset on server restart and lack of distributed support
   - **Rationale**: MVP is single-server; in-memory is sufficient. Redis migration in Phase 4 will enable distributed rate limiting for multi-server deployments.

4. **HTTP Basic Auth vs. OAuth2/JWT for Admin**
   - **Choice**: Session-based auth with bcrypt-hashed passwords
   - **Trade-off**: Simplicity (no token management, no external auth provider) vs. less modern auth flow
   - **Rationale**: MVP admin is solo founder only; session-based auth is sufficient. OAuth2 can be added in Phase 2 if multi-admin or agent accounts are needed.

### Open Questions

1. **hCaptcha Integration Priority**
   - **Question**: Should hCaptcha (or similar) be included in MVP, or wait until spam becomes an actual problem?
   - **Recommendation**: Start without hCaptcha (use honeypot + rate limiting); monitor lead submissions post-launch. If spam rate >10%, add hCaptcha in a hotfix PR. This avoids adding UX friction prematurely.

2. **Email Notification Configuration**
   - **Question**: Should email notifications to admin be enabled by default, or opt-in via env var?
   - **Recommendation**: Make it opt-in (`ENABLE_EMAIL_NOTIFICATIONS=false` by default) to avoid SMTP setup blocking MVP deployment. Admin can enable later if desired.

3. **Lead Retention Policy**
   - **Question**: How long should leads be retained in the database? PSD suggests 90 days, but should this be configurable?
   - **Recommendation**: Store indefinitely for MVP (no auto-deletion); admin can manually archive/delete if needed. Phase 2 can add auto-archival policy if database size becomes an issue.

4. **Callback Form Placement**
   - **Question**: Should the callback form be a modal (overlay) or inline on the page?
   - **Recommendation**: Use a modal for MVP (cleaner UX, less page clutter). Modal can be triggered from multiple pages (results, Block X-Ray, compare) with consistent experience.

5. **Admin Role Granularity**
   - **Question**: Should there be multiple admin roles (e.g., "viewer" vs. "editor"), or just one "admin" role for MVP?
   - **Assumption**: Single "admin" role for MVP (solo founder only). Multi-role RBAC can be added in Phase 2 if agents or additional staff are onboarded.

6. **Shortlist Size Limit**
   - **Question**: What is the optimal shortlist size limit? 10 items seems reasonable, but should this be configurable?
   - **Recommendation**: Hard-code limit to 10 items for MVP (balances UX + session storage constraints). Can make configurable in Phase 2 if users request higher limits.

---

## Summary

PR7 completes the core buyer journey by enabling shortlisting, comparison, PDF export, and callback requests, while providing admin lead management via an authenticated inbox. The epic is split into 3 sequential PRs to ensure independent testability and incremental delivery:

- **PR7a (Shortlist & Compare)**: Foundation for user research workflow; session-based, no login
- **PR7b (PDF Export)**: Tangible artifacts for sharing and preservation; builds trust
- **PR7c (Callback & Admin Inbox)**: Lead capture with anti-spam; admin efficiency via structured inbox

Each PR is designed as a self-contained, testable unit with clear verification steps. The architecture prioritizes Python-first simplicity (WeasyPrint, session-based auth, in-memory rate limiting) while acknowledging future scale needs (Redis, persistent storage, OAuth2) for Phase 2+.

**Key risks**—session storage limits, WeasyPrint installation, lead spam, admin security—are mitigated via explicit trade-offs and monitoring strategies. The plan is ready for implementation using the `/implement_task` workflow.
