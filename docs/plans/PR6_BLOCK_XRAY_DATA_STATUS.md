# Epic Plan: PR6 - Block X-Ray & Data Status Page

> [!WARNING]
> **Implementation Status (2026-01-16): ⚠️ PARTIAL**
> 
> **Completed:**
> - ✅ Block X-Ray service with property info (via PR6.1)
> - ✅ Block X-Ray page (`/block/{block_id}`)
> - ✅ HDB property info (age, lease, floors, units)
> - ✅ Block facilities display
> - ✅ Nearby amenities (POI integration)
> - ✅ Unit composition with chart
> 
> **NOT Implemented:**
> - ❌ Data Status service (`data_status.py`)
> - ❌ Data Status page (`/data-status`)
> - ❌ Transaction trend analysis
> - ❌ Volatility indicator
> - ❌ Footer link to Data Status

## 1. Feature/Epic Summary

### Objective
Implement a comprehensive Block X-Ray page that provides detailed block-level intelligence (lease information, HDB property details, transaction trends, MRT/amenity distances) and create a public Data Status page that transparently shows dataset freshness, sources, and ingestion health to build user trust.

### User Impact
- **Buyers** gain deep insights into specific HDB blocks beyond just price, including remaining lease, historical transaction trends, proximity to key amenities, and MRT stations
- **Transparency** builds trust through public visibility into data freshness and ingestion status
- **Informed decisions** are enabled by comprehensive block intelligence presented with clear "Last updated" timestamps
- **Market awareness** is improved through transaction trend visualizations and volatility indicators

### Dependencies
- **PR4 (Fair Value Engine):** Required for transaction data queries and price-per-sqm calculations used in trend analysis
- **PR3 (POIs & MRT ingestion):** Required for POI and MRT station data used in distance calculations
- **PR2 (HDB ingestion):** Required for block metadata and transaction data
- **PR1 (Database Schema):** Required for `blocks`, `transactions`, `pois`, and `ingestion_runs` tables

### Assumptions
- **Assumption:** `BlockPOI` table with pre-computed distances is available (verified: 635,259 relationships exist)
- **Assumption:** Transaction trend analysis aggregated by quarter or year is sufficient for MVP; real-time daily trends can be deferred
- **Assumption:** "Data delayed" threshold of >48 hours is appropriate for showing warning badges
- **Assumption:** HDB property information fields (max_floor_lvl, year_completed, etc.) are available in blocks table (verified: 9,674/9,675 blocks populated)

## 2. Complexity & Fit

### Classification
Single-PR

### Rationale
- **Single feature domain:** Both Block X-Ray and Data Status are transparency/data-intelligence features that share common concerns (dataset freshness, "Last updated" timestamps)
- **Limited backend layers:** Primarily service layer (aggregation, distance calculation) and presentation layer (templates, API endpoints)
- **No major data model changes:** Uses existing tables (`blocks`, `transactions`, `pois`, `ingestion_runs`); no new migrations required
- **Clear scope boundary:** Well-defined in MASTER_PLAN.md with explicit in-scope and out-of-scope items
- **Testable independently:** Block X-Ray and Data Status can each be tested and verified independently
- **Low risk:** Additive feature with no impact on existing Fair Value functionality

### Estimated PRs
1 (this PR)

## 3. Full-Stack Impact

### Frontend
- **Pages/components impacted:**
  - New Block X-Ray page (`templates/block_xray.html`) with rich block intelligence display
  - New Data Status page (`templates/data_status.html`) showing dataset freshness and ingestion health
  - Update base template (`templates/base.html`) footer to include link to Data Status page
  - CSS styling for Block X-Ray cards, transaction trend charts, and Data Status table
- **New UI states required:**
  - Loading state for Block X-Ray data (skeleton or spinner)
  - Error state if block not found or data unavailable
  - "Data delayed" badge on Data Status page when datasets are >48h stale
  - "Last updated" timestamp labels on all Block X-Ray metrics
- **Navigation/entry points:**
  - Link from Fair Value results page to Block X-Ray (for the unit's block)
  - Direct URL access via `/block/<block_id>`
  - Footer link to `/data-status` from all pages (via base template)

### Backend
- **APIs to add/modify:**
  - `GET /api/block-xray/<block_id>` — Returns Block X-Ray data (lease, trends, distances, volatility)
  - `GET /block/<block_id>` — Renders Block X-Ray page
  - `GET /data-status` — Renders Data Status page
  - `GET /api/data-status` (optional) — Returns data status JSON for potential future use
- **Services/modules impacted:**
  - **NEW:** `src/resalelens/services/block_xray.py` — Core Block X-Ray logic (lease calculation, trend aggregation, distance queries, volatility)
  - **NEW:** `src/resalelens/services/data_status.py` — Query `ingestion_runs`, compute freshness, determine status (Healthy/Delayed/Failed)
  - **MODIFY:** `src/resalelens/services/utils.py` — Add distance calculation functions (Haversine, nearest POI lookup)
- **Validation/auth/error-handling concerns:**
  - Validate `block_id` parameter (must exist in `blocks` table)
  - Handle cases where block has no transactions (graceful message: "No transaction history available")
  - Handle missing POI/MRT data (show "Distance unavailable" or fallback message)
  - No authentication required (public-facing pages)
  - Standard error handling for invalid block IDs (404 Not Found)

### Data
- **Entities/tables/fields involved:**
  - `blocks` — `lease_commence_year`, `latitude`, `longitude`, `postal_code`, `max_floor_lvl`, `year_completed`, `total_dwelling_units`, facility flags (read)
  - `transactions` — All fields for trend analysis (filter by `block`, `street`, group by `date` or quarter, calculate median `psm`)
  - `pois` — `poi_type`, `name`, `latitude`, `longitude` (for POI details)
  - `block_pois` — `block_id`, `poi_id`, `distance_m` (for pre-computed distances)
  - `ingestion_runs` — `dataset_name`, `started_at`, `completed_at`, `status`, `rows_processed`, `error_summary` (read for Data Status page)
- **Migrations/backfills needed:**
  - **None required** — All tables exist with data populated (9,675 blocks, 218,372 transactions, 1,916 POIs, 635,259 block-POI relationships)
- **Compatibility strategy if evolving schema:**
  - Not applicable (no schema changes)

### Infra / Config
- **Environment variables:**
  - No new environment variables required (all data available in database)
- **Feature flags:**
  - None required for MVP (straightforward feature rollout)
- **CI/CD considerations:**
  - Existing CI pipeline (`ruff check`, `ruff format --check`, `mypy`, `pytest`) will cover new code
  - No new CI steps required

## 4. PR Roadmap

### PR 6: Block X-Ray & Data Status Page

#### Goal
Deliver transparent, data-backed block intelligence and a public Data Status page that builds user trust by showing dataset freshness and ingestion health.

#### Scope

**In scope:**
- Block X-Ray service with:
  - Remaining lease calculation (current year - `lease_commence_year`)
  - HDB property information (max floor level, year completed, total units, facilities)
  - Transaction trend: median price-per-sqm over time (aggregated by quarter or year)
  - Volatility indicator: variance or standard deviation of price-per-sqm
  - Nearest MRT/LRT station distance (from `block_pois` table)
  - Amenity distances (nearest supermarket, clinic, park, mall, hawker center from `block_pois` table)
- Block X-Ray page (`/block/<block_id>`) with:
  - All above metrics displayed in cards or sections
  - "Last updated" timestamp for each metric (based on transactions or POIs `last_updated`)
  - Responsive design, mobile-friendly
  - Link back to Fair Value results or search
- Data Status page (`/data-status`) showing:
  - All datasets (HDB transactions, blocks, MRT/LRT, POIs)
  - Source label (e.g., "data.gov.sg", "OneMap", "Curated CSV")
  - Last successful ingestion timestamp
  - Next scheduled ingestion time
  - Status badge (Healthy / Delayed / Failed)
  - "Data delayed" badge if transactions dataset is >48 hours stale
- API endpoints for Block X-Ray and Data Status
- Link to Data Status page in footer (base template)

**Out of scope:**
- Interactive charts with zoom/pan (defer to Phase 2; use static/simple charts for MVP)
- Predictive trend forecasting (defer to Phase 3)
- Flat mix distribution (data not available in current schema)
- Noise-risk proxies (expressway/road data not available; defer to Phase 2)
- OneMap routing API integration (straight-line distances sufficient for MVP)
- User-specific filters or saved views (defer to Phase 2)

#### Backend Changes

**Services:**
- **NEW:** `src/resalelens/services/block_xray.py`
  - `get_block_xray(block_id: str) -> BlockXRayData`
    - Query `blocks` table for lease commence year, HDB property info (max_floor_lvl, year_completed, total_dwelling_units, facilities)
    - Calculate remaining lease: `current_year - lease_commence_year`
    - Query `transactions` for block, group by quarter/year, compute median psm
    - Compute volatility (variance or std dev of psm)
    - Query `block_pois` table for nearest MRT/LRT (pre-computed distances)
    - Query `block_pois` table for nearest amenities by type (supermarket, clinic, park, mall, hawker)
    - Return structured `BlockXRayData` object with all metrics + timestamps
- **NEW:** `src/resalelens/services/data_status.py`
  - `get_data_status() -> List[DatasetStatus]`
    - Query `ingestion_runs` table for each dataset (HDB transactions, blocks, MRT/LRT, POIs)
    - Get latest successful run (`status='success'`, max `completed_at`)
    - Determine next scheduled ingestion (hardcoded for MVP: weekly Sunday 03:00 for transactions, monthly 1st 03:30 for POIs)
    - Compute freshness: if `completed_at` is >48h old for transactions, mark as "Delayed"
    - Return list of `DatasetStatus` objects (dataset_name, source, last_ingest, next_ingest, status)

**Routers:**
- **MODIFY:** `src/resalelens/routers/api.py`
  - Add `GET /api/block-xray/<block_id>` endpoint
    - Call `block_xray_service.get_block_xray(block_id)`
    - Return JSON response with BlockXRayData
    - Handle 404 if block not found
- **MODIFY:** `src/resalelens/routers/public.py`
  - Add `GET /block/<block_id>` endpoint (render Block X-Ray page)
    - Call `block_xray_service.get_block_xray(block_id)`
    - Render `templates/block_xray.html` with data
    - Handle 404 if block not found
  - Add `GET /data-status` endpoint (render Data Status page)
    - Call `data_status_service.get_data_status()`
    - Render `templates/data_status.html` with dataset status list

**Schemas (Pydantic models):**
- **NEW:** `src/resalelens/schemas/block_xray.py`
  - `BlockXRayData` — Structured response model with fields:
    - `block_id: str`
    - `block: str`
    - `street: str`
    - `town: str`
    - `postal_code: Optional[str]`
    - `lease_commence_year: int`
    - `remaining_lease_years: int`
    - `max_floor_lvl: Optional[int]`
    - `year_completed: Optional[int]`
    - `total_dwelling_units: Optional[int]`
    - `facilities: Dict[str, bool]` (residential, commercial, market_hawker, multistorey_carpark, etc.)
    - `transaction_trend: List[TrendPoint]` (quarter/year + median psm)
    - `volatility: float` (variance or std dev)
    - `nearest_mrt: POIDistance` (name, distance_m)
    - `amenities: Dict[str, POIDistance]` (e.g., `{"supermarket": POIDistance(...)}`)
    - `last_updated: Dict[str, datetime]` (e.g., `{"transactions": ..., "pois": ...}`)
  - `TrendPoint` — `period: str, median_psm: float`
  - `POIDistance` — `name: str, distance_m: float`
- **NEW:** `src/resalelens/schemas/data_status.py`
  - `DatasetStatus` — `dataset_name: str, source: str, last_ingest: Optional[datetime], next_ingest: Optional[datetime], status: str` ("Healthy", "Delayed", "Failed")

**Validation/Auth:**
- Block ID validation: check existence in `blocks` table
- No authentication required (public endpoints)

**Error Handling:**
- 404 if block not found
- Graceful handling of missing BlockPOI data (show "Distance unavailable")
- Handle blocks with no HDB property info (show "N/A" for missing fields)

#### Frontend Changes

**Pages/components to create:**
- **NEW:** `templates/block_xray.html`
  - Hero section: Block address (with postal code), lease info (commence year, remaining years)
  - HDB Property Info section: Max floor level, year completed, total units, on-site facilities
  - Transaction trend section: line chart or table (period + median psm)
  - Volatility badge (e.g., "Low volatility" or "High volatility" based on threshold)
  - MRT/LRT section: Nearest station name, distance (meters), "Last updated" timestamp
  - Amenities section: Cards for supermarket, clinic, park, mall, hawker (name, distance in meters)
  - "Last updated" timestamp for transactions and POIs at bottom of page
  - Link back to search or Fair Value results
- **NEW:** `templates/data_status.html`
  - Table with columns: Dataset Name, Source, Last Ingest, Next Ingest, Status
  - Status badges: Green for "Healthy", Yellow for "Delayed", Red for "Failed"
  - "Data delayed" badge if HDB transactions >48h stale
  - Footer note explaining ingestion schedules (weekly for transactions, monthly for POIs/MRT)
- **MODIFY:** `templates/base.html`
  - Add footer link to `/data-status` (e.g., "Data Transparency" or "Data Status")

**UI states:**
- Loading skeleton for Block X-Ray data (while API call is pending)
- Error state for 404 (block not found): "Block not found. Please check the address."
- Empty state if no transaction history: "No transaction history available for this block."
- "Distance unavailable" labels for missing BlockPOI data
- "N/A" labels for missing HDB property info fields

**Styling:**
- Use CSS Grid/Flexbox for Block X-Ray layout (cards for each metric)
- Responsive design (mobile-first)
- Color palette: Slate grays for neutrals, blue/violet for highlights, semantic colors (green for healthy, yellow for delayed, red for failed)
- Simple line chart for transaction trend (use Chart.js or similar lightweight library, or SVG for MVP)
- Badges for status (rounded, colored, clear labels)

#### Data Changes
- **None** — Uses existing schema (blocks, transactions, pois, block_pois, ingestion_runs)
- No migrations required
- All required data is already populated (verified: 9,675 blocks, 218,372 transactions, 1,916 POIs, 635,259 block-POI relationships)

#### Infra / Config
- No new environment variables required
- No feature flags required
- No CI/CD changes required (existing pipeline covers this PR)

#### Testing

**Unit tests:**
- `test_block_xray_service.py`:
  - `test_get_block_xray_success` — Verify Block X-Ray data is computed correctly for a known block
  - `test_get_block_xray_no_transactions` — Verify graceful handling when block has no transactions
  - `test_remaining_lease_calculation` — Verify lease calculation (current year - commence year)
  - `test_hdb_property_info_display` — Verify HDB property fields (max_floor_lvl, year_completed, facilities) are included
  - `test_transaction_trend_aggregation` — Verify median psm is computed correctly per quarter/year
  - `test_volatility_calculation` — Verify variance/std dev is computed correctly
  - `test_nearest_mrt_from_block_poi` — Verify BlockPOI table query returns correct nearest MRT
  - `test_nearest_amenity_from_block_poi` — Verify nearest amenity per type from BlockPOI table
  - `test_block_not_found` — Verify 404 error when block does not exist
  - `test_missing_hdb_property_info` — Verify graceful handling when HDB property fields are null
- `test_data_status_service.py`:
  - `test_get_data_status_all_healthy` — Verify all datasets marked "Healthy" when recent
  - `test_get_data_status_transactions_delayed` — Verify "Delayed" badge when transactions >48h old
  - `test_get_data_status_ingestion_failed` — Verify "Failed" badge when latest run status is "failed"
  - `test_next_scheduled_ingest` — Verify next ingestion time is computed correctly (hardcoded schedule)

**Integration/API tests:**
- `test_block_xray_api.py`:
  - `test_get_block_xray_api_success` — `GET /api/block-xray/<block_id>` returns 200 with correct data
  - `test_get_block_xray_api_not_found` — `GET /api/block-xray/<invalid_id>` returns 404
  - `test_block_xray_page_renders` — `GET /block/<block_id>` returns 200 and renders template
- `test_data_status_api.py`:
  - `test_data_status_page_renders` — `GET /data-status` returns 200 and renders table
  - `test_data_status_shows_delayed_badge` — Verify "Data delayed" badge appears when transactions >48h old

**UI/e2e tests (manual for MVP, can automate later):**
- Navigate to `/block/<block_id>`, verify all sections display correctly
- Verify "Last updated" timestamps are present and accurate
- Navigate to `/data-status`, verify all datasets listed with correct statuses
- Simulate delayed ingestion (set last ingest to 3 days ago in DB), verify "Data delayed" badge

**Manual checks:**
- Visual regression: Block X-Ray page looks good on desktop and mobile
- Accessibility: Check color contrast for status badges, semantic HTML
- Performance: Block X-Ray page loads in <1s (p95 target - improved from 2s due to BlockPOI pre-computed distances)

#### Verification

**Commands to run:**
- Install: `uv sync`
- Dev server: `uv run uvicorn src.resalelens.main:app --reload`
- Tests: `uv run pytest tests/test_block_xray_service.py tests/test_data_status_service.py tests/test_block_xray_api.py tests/test_data_status_api.py`
- Lint: `uv run ruff check .`
- Typecheck: `uv run mypy src/`
- Format check: `uv run ruff format --check .`
- Build: Not required for MVP (FastAPI serves dynamically)
- DB migrate: Not required (no schema changes)

**Manual verification checklist:**
1. Start dev server: `uv run uvicorn src.resalelens.main:app --reload`
2. Navigate to `http://localhost:8000/block/<test_block_id>` (use a block ID from existing data, e.g., block ID 1)
   - **Expected:** Block X-Ray page displays with all sections
3. Verify each metric is present:
   - Block address with postal code
   - Remaining lease years (calculated from lease_commence_year)
   - HDB property info: max floor level, year completed, total units, on-site facilities
   - Transaction trend (median psm over time, grouped by quarter/year)
   - Volatility indicator (variance or std dev badge)
   - Nearest MRT distance (from BlockPOI table, in meters)
   - Nearest amenities: supermarket, clinic, park, mall, hawker (from BlockPOI table, in meters)
   - "Last updated" timestamps for transactions and POIs
4. Test missing data handling:
   - Find a block with no HDB property info (if any)
   - **Expected:** "N/A" displayed for missing fields, page still renders correctly
5. Navigate to `http://localhost:8000/data-status`
   - **Expected:** Data Status page displays with table showing HDB transactions, blocks, MRT/LRT, POIs datasets
   - Verify each row shows: Dataset Name, Source, Last Ingest, Next Ingest, Status
6. Simulate delayed data:
   - Manually update `ingestion_runs` table: set `completed_at` for HDB transactions to 3 days ago
   - Reload `/data-status`
   - **Expected:** "Data delayed" badge appears for HDB transactions, status is "Delayed"
7. Test invalid block ID:
   - Navigate to `http://localhost:8000/block/INVALID_BLOCK_ID`
   - **Expected:** 404 error page or friendly "Block not found" message
8. Check footer link:
   - Navigate to home page or any page
   - **Expected:** Footer contains link to "Data Status" page
9. Mobile responsiveness:
   - Resize browser to mobile viewport (375px width)
   - **Expected:** Block X-Ray page and Data Status page are readable and usable on mobile
10. Performance check:
    - Use browser dev tools Network tab
    - Reload Block X-Ray page
    - **Expected:** Page load time <1s (p95 target, improved due to BlockPOI pre-computed distances)

#### Rollback Plan

**Feature flag / kill switch strategy:**
- Not applicable for MVP (no feature flag infrastructure yet)
- If deployment causes issues, revert this PR

**Revert strategy:**
- **What happens if the PR is reverted?**
  - Block X-Ray and Data Status routes will return 404
  - Footer link to Data Status page will break (need to remove or comment out in base template)
  - No database rollback needed (no schema changes)
  - Fair Value and other existing features remain unaffected
- **Special considerations:**
  - None — this PR is additive and does not modify existing data or functionality

#### Dependencies

**PRs that must be merged before this one:**
- **PR1 (Database Schema):** Required for `blocks`, `transactions`, `pois`, `ingestion_runs` tables
- **PR2 (HDB Ingestion):** Required for populated `blocks` and `transactions` tables
- **PR3 (POIs & MRT Ingestion):** Required for populated `pois` table
- **PR4 (Fair Value Engine):** Required for transaction queries and price-per-sqm logic (reusable components)

**External dependencies:**
- None (all data available in database via BlockPOI table)

#### Risks & Mitigations

**Main risks:**
1. **Sparse transaction data for some blocks**
   - **Risk:** Blocks with few or no transactions will have empty trend charts, reducing Block X-Ray value
   - **Mitigation:** Show graceful "No transaction history available" message; display other metrics (lease, HDB property info, MRT/amenities) which are still valuable
   - **Current status:** ✅ Mitigated - 218,372 transactions available across 9,675 blocks
2. **Missing HDB property info for some blocks**
   - **Risk:** Some blocks may have null values for max_floor_lvl, year_completed, or other HDB property fields
   - **Mitigation:** Display "N/A" for missing fields; ensure page renders correctly with partial data
   - **Current status:** ⚠️ Monitor - 9,674/9,675 blocks have property info (99.99% coverage)
3. **Missing BlockPOI relationships**
   - **Risk:** Some block-POI relationships may be missing if distance calculation failed during ingestion
   - **Mitigation:** Display "Distance unavailable" for missing POI types; ensure at least MRT data is available
   - **Current status:** ✅ Mitigated - 635,259 block-POI relationships exist (comprehensive coverage)
4. **Delayed ingestion not detected**
   - **Risk:** If `ingestion_runs` table is not updated correctly, Data Status page may show incorrect "Healthy" status
   - **Mitigation:** Ensure ingestion pipeline (PR2, PR3) correctly logs to `ingestion_runs`; add integration test to verify logging
   - **Current status:** ✅ Ready - 29 ingestion runs tracked
5. **UI complexity for mobile**
   - **Risk:** Block X-Ray page with many metrics may be cluttered or hard to navigate on mobile
   - **Mitigation:** Use responsive design with collapsible sections or tabs; prioritize key metrics (lease, MRT, trend) above-the-fold

**Mitigations summary:**
- Graceful degradation for missing data ("N/A" labels, "Distance unavailable")
- No caching needed (BlockPOI table provides instant lookups)
- Clear labeling for all metrics
- Responsive design for mobile usability
- Comprehensive testing for data integrity and performance

## 5. Milestones & Sequence

Since this is a single-PR epic, there is only one milestone:

### Milestone 1: Block X-Ray & Data Transparency (PR6)
**What it unlocks:**
- Buyers can explore detailed block-level intelligence beyond just price
- Users can verify data freshness and trust the platform's transparency
- Foundation for future features (comparison, shortlist, PDF export) that leverage Block X-Ray data

**PRs included:**
- PR6: Block X-Ray & Data Status Page

**What "done" means:**
- Block X-Ray page is live and accessible at `/block/<block_id>`
- Data Status page is live and accessible at `/data-status`
- All metrics (lease, HDB property info, trend, MRT/amenities) display correctly with "Last updated" timestamps
- Data Status page accurately reflects ingestion health and shows "Data delayed" badge when appropriate
- CI pipeline passes (lint, typecheck, tests)
- Manual verification checklist completed
- p95 response time <1s for Block X-Ray page (improved from 2s target due to BlockPOI)

## 6. Risks, Trade-offs, and Open Questions

### Major Risks

1. **Sparse Transaction Data**
   - **Risk:** Blocks with few or no recent transactions will have incomplete or missing trend charts, reducing the value of Block X-Ray for those blocks
   - **Mitigation:** Show graceful "No transaction history available" message; ensure other metrics (lease, HDB property info, MRT, amenities) still provide value; consider town-level trend fallback in future PR
   - **Current Status:** ✅ Low risk - 218,372 transactions across 9,675 blocks provides good coverage

2. **Missing HDB Property Info**
   - **Risk:** Some blocks may have incomplete HDB property information (max_floor_lvl, year_completed, etc.)
   - **Mitigation:** Display "N/A" for missing fields; ensure UI handles partial data gracefully
   - **Current Status:** ✅ Very low risk - 99.99% coverage (9,674/9,675 blocks)

3. **Data Status Page Accuracy**
   - **Risk:** If `ingestion_runs` table is not correctly populated, Data Status page may show incorrect statuses, eroding trust
   - **Mitigation:** Ensure PR2 and PR3 ingestion pipelines correctly log to `ingestion_runs` with accurate `completed_at` and `status`; add integration tests to verify logging
   - **Current Status:** ✅ Ready - 29 ingestion runs tracked

### Trade-offs

1. **BlockPOI Pre-computed Distances vs On-Demand Calculation**
   - **Choice:** Use existing `BlockPOI` table with pre-computed distances
   - **Trade-off:** Relies on ingestion pipeline to maintain BlockPOI data vs. on-demand flexibility
   - **Rationale:** BlockPOI table already exists with 635,259 relationships; provides instant lookups with no caching complexity; significantly better performance than on-demand Haversine

2. **Static Charts vs Interactive Charts**
   - **Choice:** Use simple static or minimally interactive charts (e.g., Chart.js with basic line chart) for transaction trends
   - **Trade-off:** Faster development and simpler frontend vs. richer UX with zoom/pan/tooltips
   - **Rationale:** MVP prioritizes delivering core data over interactive UX; can enhance with D3.js or similar in Phase 2

3. **Quarterly vs Monthly Transaction Trends**
   - **Choice:** Aggregate transaction trends by quarter (or year for older data)
   - **Trade-off:** Smoother charts and less noise vs. more granular monthly trends
   - **Rationale:** Quarterly aggregation is sufficient for spotting trends; monthly may be too sparse for low-transaction blocks

4. **HDB Property Info Inclusion**
   - **Choice:** Include HDB property information fields (max_floor_lvl, year_completed, facilities) in Block X-Ray
   - **Trade-off:** Richer block intelligence vs. slightly more complex UI
   - **Rationale:** Data is already available (99.99% coverage); provides significant value to buyers; minimal implementation cost

### Open Questions

1. **Transaction Trend Aggregation Period**
   - **Question:** Should transaction trends be aggregated by quarter, by year, or dynamically (monthly for recent data, yearly for older data)?
   - **Impact on plan:** Affects complexity of aggregation logic and chart display
### Open Questions

1. **Transaction Trend Aggregation Period**
   - **Question:** Should transaction trends be aggregated by quarter, by year, or dynamically (monthly for recent data, yearly for older data)?
   - **Impact on plan:** Affects complexity of aggregation logic and chart display
   - **Recommendation:** Use quarterly aggregation for MVP (past 2 years), yearly for data older than 2 years; can make dynamic in future PR

2. **Data Status Next Ingestion Time** ✅ RESOLVED
   - **Question:** How do we compute "Next scheduled ingestion" for Data Status page? Read from APScheduler config or hardcode schedule?
   - **Resolution:** Hardcode schedule for MVP (weekly Sunday 03:00 for transactions, monthly 1st 03:30 for POIs) based on MASTER_PLAN §5 PR2-PR3; can read from APScheduler dynamically in future enhancement
   - **Impact on plan:** Implementation simplified - no APScheduler introspection needed

3. **Flat Mix Distribution Availability** ✅ RESOLVED
   - **Question:** Is `flat_mix_distribution` reliably available in the HDB blocks dataset, or is this data sparse?
   - **Resolution:** Field exists but is empty (verified: sample block shows `{}`). Feature removed from PR6 scope.
   - **Impact on plan:** Flat mix distribution section removed from Block X-Ray UI

4. **Noise-Risk Proxies Data Source** ✅ RESOLVED
   - **Question:** Where do we source expressway/major road locations for noise-risk proxies?
   - **Resolution:** Data not available in current POI dataset. Feature deferred to Phase 2.
   - **Impact on plan:** Noise-risk proxies section removed from PR6 scope

5. **Distance Calculation Strategy** ✅ RESOLVED
   - **Question:** Should distances be calculated on-demand with Haversine or pre-computed?
   - **Resolution:** Use existing `BlockPOI` table with 635,259 pre-computed distances. No Haversine calculations needed.
   - **Impact on plan:** Significantly improved performance (<1s vs <2s target); no caching complexity

---

## Summary

PR6 delivers two key transparency features: **Block X-Ray** (comprehensive block intelligence with HDB property details) and **Data Status Page** (dataset freshness and ingestion health). This single-PR epic is well-scoped, testable, and builds user trust through transparent "Last updated" timestamps and ingestion status visibility.

**Key Deliverables:**
- Block X-Ray page (`/block/<block_id>`) with:
  - Lease information (commence year, remaining years)
  - HDB property details (max floor level, year completed, total units, on-site facilities)
  - Transaction trends (median price-per-sqm over time)
  - Volatility indicator
  - Nearest MRT/LRT distance (from BlockPOI table)
  - Amenity distances: supermarket, clinic, park, mall, hawker (from BlockPOI table)
- Data Status page (`/data-status`) with all datasets, last ingest, next ingest, and health status
- "Data delayed" badge when transactions >48h stale
- Footer link to Data Status page from all pages

**Data Availability (Verified):**
- ✅ 9,675 blocks with 100% postal code and coordinate coverage
- ✅ 218,372 transactions for comprehensive trend analysis
- ✅ 1,916 POIs across all required types
- ✅ 635,259 pre-computed block-POI distances
- ✅ 29 ingestion runs tracked

**Dependencies:** PR1, PR2, PR3, PR4 must be complete (all verified as complete)

**Performance:** <1s p95 latency target (improved from original 2s due to BlockPOI pre-computed distances)

**Risks:** Mitigated through graceful degradation for missing data ("N/A" labels, "Distance unavailable"), no caching needed (BlockPOI provides instant lookups), and clear labeling

**Features Deferred to Phase 2:**
- Flat mix distribution (data not available)
- Noise-risk proxies (expressway/road data not available)
- Interactive charts with zoom/pan
- OneMap routing API integration

**Next Steps:**
- Implement Block X-Ray service using BlockPOI table queries
- Implement Data Status service with hardcoded ingestion schedule
- Create frontend templates with HDB property info sections
- Comprehensive testing (unit, integration, manual verification)
- Verify p95 latency <1s for Block X-Ray page


---

See also: [PR6.1: HDB Property Information Features](file:////Users/jefflee/Documents/AIProjects/ResaleLens_SG-V1/docs/plans/PR6.1_BLOCK_XRAY_PROPERTY_INFO.md)
