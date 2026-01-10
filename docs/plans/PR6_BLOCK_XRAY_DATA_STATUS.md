# Epic Plan: PR6 - Block X-Ray & Data Status Page

## 1. Feature/Epic Summary

### Objective
Implement a comprehensive Block X-Ray page that provides detailed block-level intelligence (lease information, transaction trends, MRT/amenity distances, noise-risk proxies) and create a public Data Status page that transparently shows dataset freshness, sources, and ingestion health to build user trust.

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
- **Assumption:** OneMap API or Haversine distance calculation is available for MRT/amenity distance computation; fallback to straight-line distance if routing is unavailable
- **Assumption:** Transaction trend analysis aggregated by quarter or year is sufficient for MVP; real-time daily trends can be deferred
- **Assumption:** "Data delayed" threshold of >48 hours is appropriate for showing warning badges
- **Assumption:** Noise-risk proxies (distance to expressways/major roads) can be computed using POI data or curated datasets; they are clearly labeled as proxies, not definitive assessments
- **Assumption:** Block X-Ray data can be precomputed during ingestion for performance, or computed on-demand with caching for MVP

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
  - `blocks` — `lease_commence_year`, `latitude`, `longitude`, `flat_mix_distribution` (read)
  - `transactions` — All fields for trend analysis (filter by `block`, `street`, group by `date` or quarter, calculate median `psm`)
  - `pois` — `poi_type`, `name`, `latitude`, `longitude` (for nearest MRT, supermarket, clinic, park, mall, hawker)
  - `ingestion_runs` — `dataset_name`, `started_at`, `completed_at`, `status`, `rows_processed`, `error_summary` (read for Data Status page)
- **Migrations/backfills needed:**
  - **None required** — Uses existing schema from PR1
  - **Optional enhancement (future):** `block_pois` table for precomputed distances (can defer to later optimization PR)
- **Compatibility strategy if evolving schema:**
  - Not applicable (no schema changes)

### Infra / Config
- **Environment variables:**
  - `ONEMAP_API_KEY` (optional, for routing API if used; fallback to Haversine if unavailable) — already defined in MASTER_PLAN §3.6
  - No new environment variables required for MVP
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
  - Flat mix distribution display (from `blocks.flat_mix_distribution`)
  - Transaction trend: median price-per-sqm over time (aggregated by quarter or year)
  - Volatility indicator: variance or standard deviation of price-per-sqm
  - Nearest MRT/LRT station distance (Haversine or OneMap routing)
  - Amenity distances (nearest supermarket, clinic, park, mall, hawker center)
  - Noise-risk proxies (distance to expressways/major roads, rail lines) — labeled as proxies
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
- Precomputed `block_pois` table optimization (defer to future performance PR)
- OneMap routing API integration (use Haversine distance fallback for MVP; can enhance later)
- Advanced noise-risk modeling (use simple distance proxies for MVP)
- User-specific filters or saved views (defer to Phase 2)

#### Backend Changes

**Services:**
- **NEW:** `src/resalelens/services/block_xray.py`
  - `get_block_xray(block_id: str) -> BlockXRayData`
    - Query `blocks` table for lease commence year, flat mix
    - Calculate remaining lease: `current_year - lease_commence_year`
    - Query `transactions` for block, group by quarter/year, compute median psm
    - Compute volatility (variance or std dev of psm)
    - Query `pois` for nearest MRT/LRT (Haversine distance)
    - Query `pois` for nearest amenities by type (supermarket, clinic, park, mall, hawker)
    - Compute noise-risk proxies (distance to expressways, rail lines if available in POI data)
    - Return structured `BlockXRayData` object with all metrics + timestamps
- **NEW:** `src/resalelens/services/data_status.py`
  - `get_data_status() -> List[DatasetStatus]`
    - Query `ingestion_runs` table for each dataset (HDB transactions, blocks, MRT/LRT, POIs)
    - Get latest successful run (`status='success'`, max `completed_at`)
    - Determine next scheduled ingestion (based on APScheduler config or fixed schedule)
    - Compute freshness: if `completed_at` is >48h old for transactions, mark as "Delayed"
    - Return list of `DatasetStatus` objects (dataset_name, source, last_ingest, next_ingest, status)
- **MODIFY:** `src/resalelens/services/utils.py`
  - Add `haversine_distance(lat1, lon1, lat2, lon2) -> float` — Calculate distance in km
  - Add `get_nearest_poi(block_lat, block_lon, poi_type: str, pois: List[POI]) -> Tuple[str, float]` — Return nearest POI name and distance

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
    - `lease_commence_year: int`
    - `remaining_lease_years: int`
    - `flat_mix_distribution: Optional[dict]` (e.g., `{"3-room": 50, "4-room": 100}`)
    - `transaction_trend: List[TrendPoint]` (quarter/year + median psm)
    - `volatility: float` (variance or std dev)
    - `nearest_mrt: POIDistance` (name, distance_km)
    - `amenities: Dict[str, POIDistance]` (e.g., `{"supermarket": POIDistance(...)}`)
    - `noise_risk_proxies: Dict[str, float]` (e.g., `{"expressway": 1.5}`)
    - `last_updated: Dict[str, datetime]` (e.g., `{"transactions": ..., "pois": ...}`)
  - `TrendPoint` — `period: str, median_psm: float`
  - `POIDistance` — `name: str, distance_km: float`
- **NEW:** `src/resalelens/schemas/data_status.py`
  - `DatasetStatus` — `dataset_name: str, source: str, last_ingest: Optional[datetime], next_ingest: Optional[datetime], status: str` ("Healthy", "Delayed", "Failed")

**Validation/Auth:**
- Block ID validation: check existence in `blocks` table
- No authentication required (public endpoints)

**Error Handling:**
- 404 if block not found
- Graceful handling of missing POI/MRT data (show "Unavailable")
- Log errors for distance calculation failures (fallback to "N/A")

#### Frontend Changes

**Pages/components to create:**
- **NEW:** `templates/block_xray.html`
  - Hero section: Block address, lease info (commence year, remaining years)
  - Flat mix distribution (if available): pie chart or table
  - Transaction trend section: line chart or table (period + median psm)
  - Volatility badge (e.g., "Low volatility" or "High volatility" based on threshold)
  - MRT/LRT section: Nearest station name, distance, "Last updated" timestamp
  - Amenities section: Cards for supermarket, clinic, park, mall, hawker (name, distance)
  - Noise-risk proxies: Labeled as proxies, show distances to expressways/rail lines
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
- "Unavailable" labels for missing POI/MRT data

**Styling:**
- Use CSS Grid/Flexbox for Block X-Ray layout (cards for each metric)
- Responsive design (mobile-first)
- Color palette: Slate grays for neutrals, blue/violet for highlights, semantic colors (green for healthy, yellow for delayed, red for failed)
- Simple line chart for transaction trend (use Chart.js or similar lightweight library, or SVG for MVP)
- Badges for status (rounded, colored, clear labels)

#### Data Changes
- **None** — Uses existing schema from PR1
- No migrations required for MVP

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
  - `test_transaction_trend_aggregation` — Verify median psm is computed correctly per quarter/year
  - `test_volatility_calculation` — Verify variance/std dev is computed correctly
  - `test_nearest_mrt_calculation` — Verify Haversine distance to nearest MRT is correct
  - `test_nearest_amenity_calculation` — Verify nearest amenity per type is correct
  - `test_block_not_found` — Verify 404 error when block does not exist
- `test_data_status_service.py`:
  - `test_get_data_status_all_healthy` — Verify all datasets marked "Healthy" when recent
  - `test_get_data_status_transactions_delayed` — Verify "Delayed" badge when transactions >48h old
  - `test_get_data_status_ingestion_failed` — Verify "Failed" badge when latest run status is "failed"
  - `test_next_scheduled_ingest` — Verify next ingestion time is computed correctly
- `test_utils.py`:
  - `test_haversine_distance` — Verify Haversine calculation with known lat/lon pairs
  - `test_get_nearest_poi` — Verify nearest POI is selected correctly

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
- Performance: Block X-Ray page loads in <2s (p95 target)

#### Verification

**Commands to run:**
- Install: `uv sync`
- Dev server: `uv run uvicorn src.resalelens.main:app --reload`
- Tests: `uv run pytest tests/test_block_xray_service.py tests/test_data_status_service.py tests/test_block_xray_api.py tests/test_data_status_api.py tests/test_utils.py`
- Lint: `uv run ruff check .`
- Typecheck: `uv run mypy src/`
- Format check: `uv run ruff format --check .`
- Build: Not required for MVP (FastAPI serves dynamically)
- DB migrate: Not required (no schema changes)

**Manual verification checklist:**
1. Start dev server: `uv run uvicorn src.resalelens.main:app --reload`
2. Seed test data (if needed): `uv run python scripts/seed_data.py`
3. Navigate to `http://localhost:8000/block/<test_block_id>` (use a block ID from seed data)
   - **Expected:** Block X-Ray page displays with lease info, transaction trend chart, MRT/amenity distances, and "Last updated" timestamps
4. Verify each metric is present:
   - Remaining lease years
   - Flat mix distribution (if available)
   - Transaction trend (median psm over time)
   - Volatility indicator
   - Nearest MRT distance
   - Nearest amenities (supermarket, clinic, park, mall, hawker)
   - Noise-risk proxies (if available)
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
    - **Expected:** Page load time <2s (p95 target)

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
- None for MVP (OneMap API is optional; fallback to Haversine if unavailable)

#### Risks & Mitigations

**Main risks:**
1. **Sparse transaction data for some blocks**
   - **Risk:** Blocks with few or no transactions will have empty trend charts, reducing Block X-Ray value
   - **Mitigation:** Show graceful "No transaction history available" message; display other metrics (lease, MRT/amenities) which are still valuable
2. **Missing POI/MRT data**
   - **Risk:** If POI ingestion fails or is incomplete, Block X-Ray will show "Unavailable" for amenities, reducing feature completeness
   - **Mitigation:** Clearly label missing data as "Unavailable" or "Coming soon"; prioritize MRT data as most critical
3. **Performance of distance calculations**
   - **Risk:** Computing distances on-demand for every request may be slow (p95 >2s), especially if many POIs
   - **Mitigation:** Cache Block X-Ray results for 1 hour (or until next ingestion); precompute nearest POI per block during ingestion in future optimization PR
4. **Delayed ingestion not detected**
   - **Risk:** If `ingestion_runs` table is not updated correctly, Data Status page may show incorrect "Healthy" status
   - **Mitigation:** Ensure ingestion pipeline (PR2, PR3) correctly logs to `ingestion_runs`; add integration test to verify logging
5. **UI complexity for mobile**
   - **Risk:** Block X-Ray page with many metrics may be cluttered or hard to navigate on mobile
   - **Mitigation:** Use responsive design with collapsible sections or tabs; prioritize key metrics (lease, MRT, trend) above-the-fold

**Mitigations summary:**
- Graceful degradation for missing data
- Caching for performance
- Clear labeling and messaging for proxies and unavailable data
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
- All metrics (lease, trend, MRT/amenities) display correctly with "Last updated" timestamps
- Data Status page accurately reflects ingestion health and shows "Data delayed" badge when appropriate
- CI pipeline passes (lint, typecheck, tests)
- Manual verification checklist completed
- p95 response time <2s for Block X-Ray page

## 6. Risks, Trade-offs, and Open Questions

### Major Risks

1. **Sparse Transaction Data**
   - **Risk:** Blocks with few or no recent transactions will have incomplete or missing trend charts, reducing the value of Block X-Ray for those blocks
   - **Mitigation:** Show graceful "No transaction history available" message; ensure other metrics (lease, MRT, amenities) still provide value; consider town-level trend fallback in future PR

2. **Distance Calculation Performance**
   - **Risk:** On-demand Haversine distance calculation for all POIs per request may exceed p95 latency target (<2s)
   - **Mitigation:** Cache Block X-Ray results for 1 hour; precompute nearest POI distances during ingestion in future optimization PR; limit POI queries to nearest 5-10 per type

3. **Missing POI Data**
   - **Risk:** If POI ingestion (PR3) is incomplete or fails, Block X-Ray will show many "Unavailable" amenities, reducing feature completeness and user trust
   - **Mitigation:** Prioritize MRT data as most critical; clearly label missing data; add fallback messaging ("Data being updated"); ensure PR3 ingestion is robust before merging PR6

4. **OneMap API Reliability**
   - **Risk:** If OneMap routing API is used and experiences downtime or rate limits, distance calculations will fail
   - **Mitigation:** Use Haversine distance as primary method for MVP (no external API dependency); defer OneMap routing to future enhancement PR

5. **Data Status Page Accuracy**
   - **Risk:** If `ingestion_runs` table is not correctly populated, Data Status page may show incorrect statuses, eroding trust
   - **Mitigation:** Ensure PR2 and PR3 ingestion pipelines correctly log to `ingestion_runs` with accurate `completed_at` and `status`; add integration tests to verify logging

### Trade-offs

1. **Haversine Distance vs OneMap Routing**
   - **Choice:** Use Haversine (straight-line) distance for MVP
   - **Trade-off:** Simplicity and no external API dependency vs. more accurate walking/driving distance
   - **Rationale:** Haversine is sufficient for "nearest X" proximity; routing can be added in Phase 2 for commute-time lens feature

2. **Static Charts vs Interactive Charts**
   - **Choice:** Use simple static or minimally interactive charts (e.g., Chart.js with basic line chart) for transaction trends
   - **Trade-off:** Faster development and simpler frontend vs. richer UX with zoom/pan/tooltips
   - **Rationale:** MVP prioritizes delivering core data over interactive UX; can enhance with D3.js or similar in Phase 2

3. **On-Demand Calculation vs Precomputed Distances**
   - **Choice:** Calculate Block X-Ray data on-demand (with caching) for MVP
   - **Trade-off:** Simpler implementation and no schema changes vs. faster response times with precomputed `block_pois` table
   - **Rationale:** Caching provides acceptable performance for MVP; precomputation can be added in future optimization PR if needed

4. **Quarterly vs Monthly Transaction Trends**
   - **Choice:** Aggregate transaction trends by quarter (or year for older data)
   - **Trade-off:** Smoother charts and less noise vs. more granular monthly trends
   - **Rationale:** Quarterly aggregation is sufficient for spotting trends; monthly may be too sparse for low-transaction blocks

### Open Questions

1. **Transaction Trend Aggregation Period**
   - **Question:** Should transaction trends be aggregated by quarter, by year, or dynamically (monthly for recent data, yearly for older data)?
   - **Impact on plan:** Affects complexity of aggregation logic and chart display
   - **Recommendation:** Use quarterly aggregation for MVP (past 2 years), yearly for data older than 2 years; can make dynamic in future PR

2. **Noise-Risk Proxies Data Source**
   - **Question:** Where do we source expressway/major road locations for noise-risk proxies? Is this available in OneMap POI data or do we need a curated dataset?
   - **Impact on plan:** If data is unavailable, may need to defer noise-risk proxies to future PR or use placeholder
   - **Recommendation:** Check OneMap POI data for road/expressway types; if unavailable, defer to Phase 2 or show "Coming soon" label

3. **Flat Mix Distribution Availability**
   - **Question:** Is `flat_mix_distribution` reliably available in the HDB blocks dataset, or is this data sparse?
   - **Impact on plan:** If unavailable, need to handle gracefully (hide section or show "Data unavailable")
   - **Recommendation:** Verify during PR2 (HDB ingestion); if sparse, make this section optional in Block X-Ray UI

4. **Data Status Next Ingestion Time**
   - **Question:** How do we compute "Next scheduled ingestion" for Data Status page? Read from APScheduler config or hardcode schedule?
   - **Impact on plan:** Affects implementation of `data_status_service.get_data_status()`
   - **Recommendation:** Hardcode schedule for MVP (weekly Sunday 03:00 for transactions, monthly 1st 03:30 for POIs) based on MASTER_PLAN §5 PR2-PR3; can read from APScheduler dynamically in future enhancement

5. **Caching Strategy for Block X-Ray**
   - **Question:** Should Block X-Ray results be cached in Redis, in-memory (functools.lru_cache), or in DB?
   - **Impact on plan:** Affects performance and complexity
   - **Recommendation:** Use `functools.lru_cache` with 1-hour TTL for MVP (simple, no external dependencies); migrate to Redis in Phase 4 if needed

---

## Summary

PR6 delivers two key transparency features: **Block X-Ray** (comprehensive block intelligence) and **Data Status Page** (dataset freshness and ingestion health). This single-PR epic is well-scoped, testable, and builds user trust through transparent "Last updated" timestamps and ingestion status visibility.

**Key Deliverables:**
- Block X-Ray page (`/block/<block_id>`) with lease, trends, MRT/amenities, volatility, and noise-risk proxies
- Data Status page (`/data-status`) with all datasets, last ingest, next ingest, and health status
- "Data delayed" badge when transactions >48h stale
- Footer link to Data Status page from all pages

**Dependencies:** PR1, PR2, PR3, PR4 must be complete

**Risks:** Mitigated through graceful degradation for missing data, caching for performance, and clear labeling

**Next Steps:**
- Verify PR4 completion before starting PR6
- Implement Block X-Ray service, Data Status service, and frontend templates
- Comprehensive testing (unit, integration, manual verification)
- Verify p95 latency <2s for Block X-Ray page
