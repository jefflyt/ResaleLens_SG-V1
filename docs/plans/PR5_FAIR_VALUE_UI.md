# Epic Plan: PR5 - Fair Value API & Results UI

**Branch:** `pr5-fair-value-ui`  
**Status:** Planning  
**Created:** 2026-01-09  
**Dependencies:** PR4 (Fair Value Engine)

---

## 1. Feature/Epic Summary

### Objective
Expose the Fair Value Engine (built in PR4) to end users through a public API endpoint and an intuitive, transparent results page. Users will be able to input a unit of interest (block, flat type, floor area, storey range) and receive a Fair Value band with confidence scoring, comparable transactions, and full explainability of how the value was calculated.

### User Impact
**Primary Users:** HDB resale buyers (first-time buyers, families, upgraders) who need to assess whether a unit is fairly priced based on historical transaction data.

**User Journey (Journey A from PSD):** "Is this unit fairly priced?"
1. User navigates to home page
2. User enters block/address + flat attributes (flat type, floor area, storey range)
3. User submits form
4. System displays Fair Value band (price range and psm), confidence score, user-facing label, comparable transactions table, and explainability
5. User reviews comps and explainability to understand value assessment
6. User can proceed to Block X-Ray for deeper analysis or add to shortlist

**Value Delivered:**
- **Transparency:** Users see exactly which transactions were used and what adjustments were made
- **Trust:** Confidence scoring and explainability build credibility (target: ≥70% rate explanation as "clear")
- **Actionable Insights:** User-facing labels (Fair, Slightly high, High risk) guide decision-making
- **Data Freshness:** "Last updated" timestamp shows when transaction data was last refreshed

### Dependencies

**Hard Dependencies:**
- **PR4 (Fair Value Engine):** Core calculation logic (comp selection, normalization, confidence scoring) must be complete and tested
- **PR1 (Database Schema):** `transactions`, `blocks`, `ingestion_runs` tables must exist
- **PR2 (HDB Transaction Ingestion):** Transaction data must be ingested and available in DB
- **PR0 (Bootstrap):** FastAPI app, Jinja2 templating, routing infrastructure

**Soft Dependencies:**
- **PR3 (POI/MRT Ingestion):** Not required for Fair Value itself, but "Last updated" logic may reference ingestion_runs for all datasets

### Assumptions

**Assumption 1:** The Fair Value Engine service from PR4 exposes a clean Python API that can be called from route handlers (e.g., `fair_value_service.calculate(block, flat_type, ...)` returns a structured result)

**Assumption 2:** Input validation (block exists, flat_type is valid, floor_area/storey_range are reasonable) is handled by the Fair Value Engine or via Pydantic schemas

**Assumption 3:** Users are comfortable with a server-rendered page (Jinja2 template) rather than a single-page app; HTMX will provide smooth form submission without full page reload

**Assumption 4:** "Last updated" timestamp for transactions can be queried from the `ingestion_runs` table (most recent successful run for dataset "hdb_transactions")

**Assumption 5:** Performance target of p95 < 2.5s can be met by the Fair Value Engine without additional caching at API layer (caching may be added in PR4 or later)

---

## 2. Complexity & Fit

### Classification: **Single-PR**

### Rationale

- **Single user flow:** Input form → submit → display results (linear journey)
- **Two main layers:** Backend (API endpoint, route handler) + Frontend (input form, results page)
- **No data model changes:** Uses existing `transactions`, `blocks`, `ingestion_runs` tables from PR1/PR2
- **Well-defined scope:** Straightforward integration of PR4's Fair Value Engine with API + UI wrapper
- **Low risk of breaking existing functionality:** Additive feature; does not modify existing routes or services
- **Clear deliverable:** When this PR merges, users can run Fair Value checks end-to-end

### Estimated PRs: **1**

This is a focused, self-contained PR that connects an existing backend service (Fair Value Engine) to a public-facing API and UI. It does not require phased rollout or feature flagging.

---

## 3. Full-Stack Impact

### Frontend

**Pages/Components Impacted:**
- **Home page (`templates/index.html`):** Add Fair Value input form
  - Fields: Block/street name (text input with autocomplete or dropdown), flat type (dropdown), floor area sqm (number input), storey range (dropdown or text), time window (dropdown, optional advanced option)
  - Submit button triggers form POST to `/api/fair-value` (via HTMX or standard form)
  - Entry point for Fair Value journey
- **New Results page (`templates/results.html`):** Display Fair Value results
  - Fair Value band (price range, psm range)
  - Confidence score (visual gauge or percentage)
  - User-facing label (Fair, Slightly high, Slightly low, High risk) with color coding
  - Comparable transactions table (sortable, paginated if > 20 comps)
    - Columns: Date, Price, Floor Area (sqm), Storey Range, Flat Model, Distance (if applicable)
  - Explainability section (collapsible or accordion)
    - Filters applied (same block / radius / town-level)
    - Adjustments made (storey normalization, outlier removal)
    - Fallback used (if any)
    - Comp count and variance
  - "Last updated" timestamp (transactions dataset)
  - Call-to-action buttons: "View Block X-Ray", "Add to Shortlist" (stubs for now, functional in PR6/PR7)

**New UI States Required:**
- **Loading state:** Show spinner or skeleton while Fair Value is calculating (HTMX swap delay or JavaScript)
- **Empty state:** If no comps found, show message: "No comparable transactions found. Try widening time window or radius."
- **Error state:** If input is invalid or calculation fails, show user-friendly error with actionable guidance (e.g., "Invalid block address. Please check and try again.")

**Navigation/Entry Points:**
- Home page is primary entry point for Fair Value check
- Results page may be accessed via direct URL with query params (future: shareable links)
- Results page includes navigation back to home ("Check Another Unit") and forward to Block X-Ray

### Backend

**APIs to Add:**
- **POST /api/fair-value**
  - Request body (JSON or form-encoded):
    - `block` (string, required): Block number or street name
    - `street` (string, optional): Street name (if block alone is ambiguous)
    - `flat_type` (string, required): e.g., "3 ROOM", "4 ROOM", "5 ROOM"
    - `floor_area_sqm` (float, required): Floor area in sqm
    - `storey_range` (string, required): e.g., "01 TO 03", "10 TO 12"
    - `time_window` (integer, optional, default 12): Months to look back for comps
  - Response (JSON):
    - `fair_value_band`: { `min_price`, `max_price`, `min_psm`, `max_psm` }
    - `confidence_score`: float (0-100)
    - `user_label`: string ("Fair", "Slightly high", etc.)
    - `comps`: list of comparable transactions (date, price, sqm, storey_range, flat_model, distance)
    - `explainability`: { `filters_applied`, `adjustments`, `fallback_used`, `comp_count`, `variance` }
    - `last_updated`: ISO timestamp of latest transactions ingestion
  - Validation: Return 400 if required fields missing or invalid
  - Error handling: Return 404 if block not found, 500 if calculation fails with error details

**Routes to Add (Public):**
- **GET /results** (or **POST /fair-value** for form submission)
  - Accepts form submission from home page
  - Calls Fair Value service
  - Renders `results.html` template with Fair Value data
  - Or, if using HTMX, returns partial HTML fragment to swap into page

**Services/Modules Impacted:**
- **Fair Value Service (from PR4):** No changes to service itself; this PR consumes the service via API contract
- **Data Status Service:** Query `ingestion_runs` table to get "Last updated" timestamp for HDB transactions

**Validation/Auth/Error Handling:**
- **Input validation:** Use Pydantic schemas to validate POST body (e.g., `FairValueRequest`)
- **Block/street validation:** Check if block exists in `blocks` table; return 404 if not found
- **Flat type validation:** Ensure flat_type is one of the valid HDB types
- **Floor area / storey range sanity checks:** Reject unrealistic values (e.g., floor area < 30 or > 300 sqm)
- **No authentication required:** Public-facing endpoint (anti-spam measures are out of scope for this PR; deferred to callback request in PR7)
- **Error messages:** Return user-friendly messages for 400/404 errors; log detailed errors server-side for 500s

### Data

**Entities/Tables/Fields Involved:**
- **transactions (from PR1):** Read-only queries for comparable transactions (block, street, flat_type, storey_range, floor_area_sqm, price, date, ...)
- **blocks (from PR1):** Read-only to validate block/street exists and get geocoordinates (if needed for distance calculation)
- **ingestion_runs (from PR1):** Read-only to get "Last updated" timestamp for HDB transactions dataset

**Migrations/Backfills Needed:**
- **No schema changes:** This PR only reads from existing tables

**Compatibility Strategy:**
- Not applicable (no schema evolution)

### Infra / Config

**Environment Variables:**
- No new environment variables required

**Feature Flags:**
- Not needed (single-PR, low-risk additive feature)

**CI/CD Considerations:**
- Ensure existing CI pipeline (lint, typecheck, tests) passes
- Add integration tests for POST /api/fair-value endpoint
- Add UI rendering test for results page template

---

## 4. PR Roadmap

### PR5: Fair Value API & Results UI

#### Goal
Enable end users to input unit details on the home page, submit a Fair Value check, and receive a transparent, explainable Fair Value assessment with comparable transactions and confidence scoring.

#### Scope

**In Scope:**
- API endpoint: POST /api/fair-value (JSON response)
- Public route: POST /fair-value or GET /results (form submission, renders results page)
- Home page input form (block, flat_type, floor_area, storey_range, optional time_window)
- Results page template displaying:
  - Fair Value band (price and psm)
  - Confidence score
  - User-facing label
  - Comps table
  - Explainability section
  - "Last updated" timestamp
- Input validation and user-friendly error handling
- Loading/empty/error UI states
- Integration tests for API endpoint
- Manual verification of end-to-end user flow

**Out of Scope:**
- Block X-Ray integration (deferred to PR6; results page may include stub button for future navigation)
- Shortlist/compare functionality (deferred to PR7; results page may include stub "Add to Shortlist" button)
- Advanced persona-based filtering (deferred to PR7 or Phase 2)
- Shareable URLs with query params (deferred to PR7 or Phase 2)
- Rate limiting or anti-spam measures (deferred to PR7 for callback requests)
- Performance caching at API layer (may be in PR4 Fair Value Service; if needed, defer to optimization PR later)

#### Backend Changes

**APIs (METHOD /path) to Add:**
- **POST /api/fair-value**
  - Request: JSON body with block, flat_type, floor_area_sqm, storey_range, time_window (optional)
  - Response: JSON with fair_value_band, confidence_score, user_label, comps, explainability, last_updated
  - Validation: Pydantic schema (FairValueRequest)
  - Error handling: 400 for validation errors, 404 for block not found, 500 for calculation errors

**Routes (Public) to Add:**
- **POST /fair-value** (or GET /results with query params)
  - Form submission handler
  - Calls Fair Value service
  - Renders `templates/results.html` with Fair Value data
  - (Alternative: use HTMX to POST to /api/fair-value and swap results into page)

**Services/Business Logic Modules:**
- **Router: src/resalelens/routers/api.py**
  - Add POST /api/fair-value endpoint
  - Call Fair Value service from PR4
  - Query ingestion_runs for "Last updated" timestamp
  - Return JSON response
- **Router: src/resalelens/routers/public.py**
  - Add POST /fair-value or GET /results route
  - Call Fair Value service
  - Render results.html template
- **Schemas: src/resalelens/schemas/fair_value.py**
  - FairValueRequest (Pydantic model for input validation)
  - FairValueResponse (Pydantic model for API response)

**Auth, Validation, Error Handling:**
- No authentication required (public endpoint)
- Pydantic validation for all input fields
- Custom validation: block exists in DB, flat_type is valid, floor_area/storey_range are realistic
- User-friendly error messages for 400/404; detailed logging for 500s

#### Frontend Changes

**Pages/Components to Create or Modify:**

**Create:**
- **templates/results.html**
  - Extends base.html
  - Displays Fair Value band (styled card or hero section)
  - Confidence score (visual gauge or percentage badge)
  - User-facing label (color-coded banner: green for "Fair", yellow for "Slightly high/low", red for "High risk")
  - Comps table (HTML table or cards, sortable by date/price)
  - Explainability section (accordion or collapsible details)
  - "Last updated" footer with timestamp
  - CTA buttons: "Check Another Unit" (back to home), "View Block X-Ray" (stub link), "Add to Shortlist" (stub button)

**Modify:**
- **templates/index.html**
  - Add Fair Value input form (prominent placement, hero section or primary card)
  - Form fields: Block/street (text input or dropdown), flat type (dropdown), floor area (number input), storey range (dropdown), time window (optional, default 12 months)
  - Form action: POST /fair-value or HTMX hx-post="/api/fair-value" hx-target="#results-container" hx-swap="innerHTML"
  - Form validation: HTML5 required attributes, client-side feedback (optional)

**Styling:**
- **static/styles.css**
  - Style Fair Value band card (modern, clean, mobile-responsive)
  - Color-coded labels: green (#10b981 or similar), yellow (#f59e0b), red (#ef4444)
  - Confidence score gauge (CSS progress bar or SVG)
  - Comps table styling (zebra striping, hover states, responsive on mobile)
  - Explainability accordion/collapsible (smooth transitions)
  - Loading spinner (CSS or inline SVG)

**Navigation Flows:**
- Home → Results (via form submission)
- Results → Home (via "Check Another Unit" button)
- Results → Block X-Ray (via "View Block X-Ray" button, stub for now)

**UI States:**
- **Loading:** Show spinner over form or replace form with skeleton during calculation
- **Empty:** If no comps found, show friendly message with CTA to widen time window
- **Error:** If validation fails or block not found, show inline error message with corrective guidance

#### Data Changes

**No schema changes required.**

**Tables Queried (Read-Only):**
- `transactions`: Retrieve comparable transactions (via Fair Value Engine)
- `blocks`: Validate block exists, get geocoordinates if needed
- `ingestion_runs`: Get most recent successful run for dataset "hdb_transactions" to populate "Last updated"

#### Infra / Config

**No infrastructure or configuration changes required.**

**CI/CD Additions:**
- Existing CI pipeline (lint, format, typecheck, tests) will run on this PR
- No new CI steps needed

#### Testing

**Unit Tests:**
- **Backend:**
  - `tests/test_api.py`:
    - Test POST /api/fair-value with valid inputs → returns 200 with expected JSON structure
    - Test POST /api/fair-value with missing required fields → returns 400 with validation errors
    - Test POST /api/fair-value with invalid block → returns 404
    - Test POST /api/fair-value with edge case inputs (e.g., extreme floor area) → handles gracefully
  - `tests/test_routers_public.py`:
    - Test POST /fair-value (form submission) → renders results.html with Fair Value data
    - Test form submission with invalid data → renders error message
- **Frontend:**
  - `tests/test_templates.py`:
    - Test results.html renders correctly with sample Fair Value data (mock data)
    - Test results.html handles empty comps (no comps found scenario)
    - Test results.html displays "Last updated" timestamp

**Integration/API Tests:**
- **End-to-end API test:**
  - POST /api/fair-value with known block and flat_type (use seeded test data from PR2 ingestion)
  - Verify response contains fair_value_band, confidence_score, comps list, explainability
  - Verify last_updated timestamp is recent (from ingestion_runs)
- **Form submission test:**
  - Simulate form POST to /fair-value with valid data
  - Verify response renders results page with expected content

**UI/E2E Tests (Manual for MVP):**
- Navigate to home page
- Fill out Fair Value form with test block/flat_type
- Submit form
- Verify results page renders with Fair Value band, confidence, comps, explainability
- Verify "Last updated" timestamp is displayed
- Click "Check Another Unit" → verify returns to home page

**Manual Checks:**
- **Happy path:** Enter valid block (e.g., from seeded data), submit form, review results page for correctness
- **Empty state:** Enter block with no recent transactions, verify "No comps found" message
- **Error handling:** Enter invalid block, verify 404 error message
- **Mobile responsiveness:** Test on mobile device or browser DevTools responsive mode
- **Performance:** Time Fair Value calculation; verify p95 < 2.5s (measure with logs or browser network tab)

#### Verification

**Commands to Run:**

- **Install dependencies:** `uv sync`
- **Start dev server:** `uv run uvicorn src.resalelens.main:app --reload`
- **Run tests:** `uv run pytest`
- **Lint:** `uv run ruff check .`
- **Format check:** `uv run ruff format --check .`
- **Typecheck:** `uv run mypy src/`
- **DB migrate (if needed):** `uv run alembic upgrade head` (no new migrations expected for this PR)

**Manual Verification Checklist:**

1. **Home page form:**
   - [ ] Navigate to http://localhost:8000/
   - [ ] Verify Fair Value input form is visible and styled correctly
   - [ ] All form fields (block, flat_type, floor_area, storey_range) are present
   - [ ] Submit button is functional

2. **Form submission:**
   - [ ] Enter valid test data (use block from seeded data or PR2 ingestion)
   - [ ] Submit form
   - [ ] Verify no JavaScript errors in browser console
   - [ ] Verify loading state is shown (if implemented)

3. **Results page:**
   - [ ] Verify results page loads successfully
   - [ ] Fair Value band (price and psm) is displayed prominently
   - [ ] Confidence score is shown (percentage or gauge)
   - [ ] User-facing label is displayed with correct color coding
   - [ ] Comps table is rendered with transactions (date, price, sqm, storey, model)
   - [ ] Explainability section is visible and can be expanded/collapsed (if accordion)
   - [ ] "Last updated" timestamp is displayed and matches recent ingestion run

4. **Error handling:**
   - [ ] Submit form with invalid block → verify 404 error message is shown
   - [ ] Submit form with missing required fields → verify 400 validation errors are shown
   - [ ] Verify error messages are user-friendly and actionable

5. **Mobile responsiveness:**
   - [ ] Open results page on mobile device or DevTools responsive mode
   - [ ] Verify layout is readable and comps table is responsive (scrollable or stacked)

6. **Performance:**
   - [ ] Measure Fair Value calculation time (browser network tab or server logs)
   - [ ] Verify p95 < 2.5s (test with multiple requests if possible)

7. **Navigation:**
   - [ ] Click "Check Another Unit" button → verify returns to home page
   - [ ] Verify stub buttons ("View Block X-Ray", "Add to Shortlist") are present but not functional (note in PR description)

#### Rollback Plan

**Feature Flag / Kill Switch:**
- Not applicable (single-PR, additive feature)
- If needed, can disable Fair Value form on home page by commenting out form HTML in template (emergency rollback)

**Revert Strategy:**
- This PR is purely additive (new API endpoint, new route, new template)
- No existing functionality is modified
- If PR introduces a critical bug, revert the merge commit
- No data migrations to roll back (read-only queries)

**Considerations:**
- Ensure PR4 (Fair Value Engine) remains stable and tested; this PR depends on it
- If Fair Value Engine has bugs, fix in PR4 and re-merge PR5 (or hot-patch in PR5 if minor)

#### Dependencies

**PRs that Must Be Merged Before This One:**
- **PR0 (Bootstrap):** FastAPI app, Jinja2 templates, routing infrastructure, CI pipeline
- **PR1 (Database Schema):** `transactions`, `blocks`, `ingestion_runs` tables exist
- **PR2 (HDB Transaction Ingestion):** Transaction data is ingested and available in DB
- **PR4 (Fair Value Engine):** Core calculation service is implemented and tested

**External Dependencies:**
- None (all data is local; no external API calls for this PR)

#### Risks & Mitigations

**Risk 1: Fair Value Engine Performance**
- **Risk:** Fair Value calculation may exceed p95 < 2.5s target, degrading user experience
- **Mitigation:** 
  - Performance testing in PR4; optimize comp queries with DB indexes
  - Add caching to Fair Value service (LRU cache for identical requests within 1-hour TTL)
  - If performance is still an issue, add loading state with progress indicator to manage user expectations

**Risk 2: Sparse Comps / No Results**
- **Risk:** Some blocks may have very few or no transactions, leading to "No comps found" error and poor user experience
- **Mitigation:**
  - Fair Value Engine (PR4) implements fallback ladder (same block → radius → town-level)
  - Results page includes clear messaging: "No comps found. Try widening time window or radius."
  - Future enhancement (Phase 2): Allow user to adjust time window or radius interactively

**Risk 3: Input Validation Edge Cases**
- **Risk:** User enters malformed or ambiguous block/street names, leading to errors or incorrect results
- **Mitigation:**
  - Validate block exists in `blocks` table before calling Fair Value service
  - Return user-friendly 404 error if block not found
  - Future enhancement: Add autocomplete or dropdown for block/street selection to reduce ambiguity

**Risk 4: UI Rendering Issues on Mobile**
- **Risk:** Comps table may not render well on small screens, reducing mobile usability
- **Mitigation:**
  - Use responsive design (CSS Grid/Flexbox)
  - Test on mobile DevTools responsive mode before merging
  - Consider alternative layout (e.g., card-based comps list instead of table) for mobile breakpoints

---

## 5. Milestones & Sequence

### Milestone 1: Fair Value API Ready
**PRs Included:** PR5  
**What It Unlocks:** Backend API for Fair Value calculation is publicly accessible; external tools or future SPAs can integrate  
**Done Means:** POST /api/fair-value endpoint returns JSON response with Fair Value data for valid inputs; integration tests pass

### Milestone 2: Fair Value User Journey Complete
**PRs Included:** PR5  
**What It Unlocks:** End users can complete Journey A ("Is this unit fairly priced?") end-to-end via web UI  
**Done Means:** User can input block/flat details on home page, submit form, and view Fair Value results with comps and explainability; manual verification checklist passes; p95 < 2.5s

---

## 6. Risks, Trade-offs, and Open Questions

### Major Risks

**Risk 1: Dependency on PR4 Stability**
- **Description:** This PR tightly depends on Fair Value Engine (PR4). If PR4 has bugs or changes API contract, PR5 breaks.
- **Mitigation:** Ensure PR4 is thoroughly tested and stable before starting PR5. Define clear service contract (input/output schemas) in PR4. If PR4 API changes, update PR5 integration accordingly.

**Risk 2: "Last Updated" Timestamp Logic**
- **Description:** "Last updated" timestamp depends on ingestion_runs table being correctly populated. If ingestion fails or stalls, timestamp may be stale, eroding user trust.
- **Mitigation:** Query ingestion_runs for most recent successful run for dataset "hdb_transactions". If no recent run (> 48 hours), display "Data delayed" badge (similar to Data Status page in PR6). Log warning if "Last updated" is stale.

**Risk 3: UX Clarity of Explainability**
- **Description:** Users may not understand explainability terms (e.g., "2.5 MAD outlier removal", "P25-P75 band"). If explanation is too technical, it defeats the trust-building goal.
- **Mitigation:** Use plain language in explainability section (e.g., "Removed extreme outliers to ensure fair comparison"). Include tooltips or help icons for technical terms. Conduct user testing (Phase 2) to refine messaging.

### Trade-offs

**Trade-off 1: Server-Rendered Results vs. Client-Side SPA**
- **Choice:** Server-rendered Jinja2 template for results page
- **Trade-off:** Simpler deployment and SEO-friendly vs. richer interactivity (e.g., sortable comps table, interactive filters)
- **Rationale:** Consistent with Python-first philosophy from MASTER_PLAN; HTMX can provide interactivity without full SPA complexity. If more interactivity is needed (e.g., real-time filtering), can add HTMX enhancements in future PR.

**Trade-off 2: Form POST to /fair-value vs. HTMX Inline Swap**
- **Choice:** TBD during implementation (either works)
- **Trade-off:** Standard form POST (full page reload) is simpler; HTMX inline swap (no page reload) is smoother UX
- **Rationale:** HTMX is preferred for better UX (no page reload), but standard form POST is acceptable for MVP. Recommend HTMX if time permits; fall back to standard POST if HTMX adds complexity.

**Trade-off 3: Comps Table vs. Card-Based Layout**
- **Choice:** HTML table for comps (desktop), responsive cards for mobile (optional)
- **Trade-off:** Table is more data-dense and familiar; cards are more mobile-friendly
- **Rationale:** Start with table for simplicity; add CSS media queries to switch to card layout on mobile breakpoints if needed. Test mobile usability during manual verification.

### Open Questions

**Question 1: Block/Street Input Format**
- **Question:** Should users enter block + street as separate fields, or as a single autocomplete/search field?
- **Impact:** Separate fields are simpler to validate but less user-friendly. Autocomplete requires frontend JavaScript or HTMX integration with search endpoint.
- **Recommendation:** Start with separate fields (block number, street name) for MVP simplicity. Defer autocomplete to Phase 2 or later enhancement PR.

**Question 2: Time Window Default and Visibility**
- **Question:** Should time window be a visible input field (dropdown with 6/12/24 months), or hidden with a default of 12 months?
- **Impact:** Visible field gives users control but adds complexity to form. Hidden default simplifies UX but may limit users who want to adjust comp range.
- **Recommendation:** Default to 12 months; hide time window in MVP (assume Fair Value Engine uses 12-month default). Add advanced options (collapsible section) in future PR if user feedback requests it.

**Question 3: Comps Table Sorting and Pagination**
- **Question:** Should comps table support client-side sorting (e.g., by date, price) and pagination if > 20 comps?
- **Impact:** Sorting and pagination improve UX for large comp lists but add frontend complexity (JavaScript or HTMX).
- **Recommendation:** Default sort by date (most recent first). No pagination for MVP (assume comp count is typically < 20 after outlier removal). If comp counts are large in practice, add pagination in follow-up PR.

**Question 4: CTA Buttons ("View Block X-Ray", "Add to Shortlist")**
- **Question:** Should stub CTA buttons be included in results page, or omitted until PR6/PR7 when functionality is ready?
- **Impact:** Stub buttons preview future functionality and improve navigation consistency, but may confuse users if non-functional.
- **Recommendation:** Include stub buttons with disabled state or tooltip ("Coming soon") to preview future features and maintain consistent layout. Update in PR6/PR7 when functional.

**Question 5: Error Handling for Fair Value Service Failures**
- **Question:** If Fair Value Engine throws an unexpected exception (e.g., DB connection failure), should we show a generic error or detailed message?
- **Impact:** Generic error ("Something went wrong, please try again") is safer but less actionable. Detailed error helps debugging but may expose internals.
- **Recommendation:** Show user-friendly generic error ("Unable to calculate Fair Value. Please try again later."). Log detailed error server-side with request ID. Include request ID in error message for user to reference if contacting support (future).

---

## Summary

PR5 (Fair Value API & Results UI) is a **single-PR feature** that exposes the Fair Value Engine (from PR4) to end users through a public API and an intuitive, transparent results page. This PR completes **Journey A ("Is this unit fairly priced?")** from the PSD, enabling users to input a unit of interest and receive a Fair Value assessment with confidence scoring, comparable transactions, and full explainability.

**Key Deliverables:**
- POST /api/fair-value endpoint (JSON response)
- Fair Value input form on home page
- Results page with Fair Value band, confidence, comps table, explainability, and "Last updated" timestamp
- Loading/empty/error UI states
- Integration tests and manual verification

**Success Criteria:**
- User can complete Fair Value check end-to-end (home → form submission → results)
- Results page displays Fair Value data clearly and transparently
- p95 response time < 2.5s
- CI pipeline passes (lint, typecheck, tests)

**Next Steps:**
- Implement PR5 using `/implement_task`
- Conduct manual verification and performance testing
- Merge to main, proceed to PR6 (Block X-Ray & Data Status)
