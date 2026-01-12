# Epic Plan: PR3 - Data Ingestion Pipeline (POIs & MRT)

## 1. Feature/Epic Summary

**Objective:**
Implement automated ingestion for MRT/LRT stations and amenity Points of Interest (POIs) to complete the foundational dataset infrastructure required for Block X-Ray and neighborhood analysis features. This PR builds upon PR2's HDB transaction/block ingestion to provide the location-based context data essential for fair value assessment and block intelligence.

**User Impact:**
- Enables future Block X-Ray feature (PR6) to display accurate MRT/amenity distances
- Provides data foundation for persona-based filtering (families need schools/parks, first-timers prioritize MRT access)
- Completes the automated data refresh framework needed for data transparency features
- No direct user-facing features in this PR; this is infrastructure work

**Dependencies:**
- **PR0 (Bootstrap):** FastAPI skeleton, APScheduler setup, Alembic migrations framework
- **PR1 (Database Schema):** `pois` table, `ingestion_runs` table, repository pattern infrastructure
- **PR2 (HDB Ingestion):** Ingestion utility functions (retry decorator, run logging), scheduler registration patterns

**Assumptions:**
1. **Assumption:** MRT/LRT station data is available via data.gov.sg or OneMap API with stable schemas
2. **Assumption:** POI data (supermarkets, clinics, parks, malls, hawkers) can be sourced from OneMap or curated CSV files
3. **Assumption:** Monthly ingestion frequency is sufficient for MRT/POI data (infrastructure changes infrequently)
4. **Assumption:** Precomputing block-to-POI distances during ingestion is an optimization that can be deferred or made optional (straight-line Haversine distance is acceptable for MVP)
5. **Assumption:** OneMap API rate limits allow bulk POI queries during ingestion (mitigate with throttling if needed)

---

## 2. Complexity & Fit

**Classification:** Single-PR

**Rationale:**
- **Single data layer:** Only backend ingestion modules and scheduler configuration required; no frontend, no API endpoints (except admin manual trigger), no user flows
- **Follows established patterns:** PR2 already established the ingestion module structure, retry logic, and scheduler integration; PR3 replicates this pattern for MRT/POI datasets
- **Limited scope creep risk:** MRT and POI ingestion are clearly bounded datasets with well-defined schemas
- **Testable independently:** Ingestion can be verified via manual triggers, database inspection, and ingestion_runs audit logs
- **Low cross-layer impact:** Does not affect Fair Value engine, user-facing UI, or existing features; purely additive infrastructure
- **Estimated effort:** 20–30 hours (ingestion modules, tests, scheduler configuration, verification)

**Estimated PRs:** 1

---

## 3. Full-Stack Impact

**Frontend:**
- No changes planned. This is a backend-only PR focused on data ingestion infrastructure.

**Backend:**
- **Ingestion Modules:**
  - New module: `src/resalelens/ingestion/mrt.py` for MRT/LRT station ingestion
  - New module: `src/resalelens/ingestion/pois.py` for amenity POI ingestion (supermarkets, clinics, parks, malls, hawkers)
  - Update: `src/resalelens/ingestion/utils.py` if additional retry/throttling logic is needed for OneMap API
- **Scheduler:**
  - Update: `src/resalelens/scheduler.py` to register two new monthly APScheduler jobs (MRT on 1st @ 03:30 SGT, POIs on 1st @ 03:45 SGT)
- **Admin Router:**
  - Update: `src/resalelens/routers/admin.py` to add manual trigger endpoints for MRT and POI ingestion (`POST /admin/ingestion/trigger?dataset=mrt`, `POST /admin/ingestion/trigger?dataset=pois`)
- **Data Access:**
  - Utilize existing `POIRepository` from PR1 for database operations (upsert POIs)

**Data:**
- **Tables involved:** `pois` (primary), `ingestion_runs` (audit log)
- **Migrations needed:** None (PR1 already created `pois` table with columns: `poi_id`, `poi_type`, `name`, `latitude`, `longitude`, `last_updated`)
- **Optional enhancement (can be deferred):**
  - If precomputed distances are implemented: create `block_pois` table with schema `(block_id, poi_id, distance_m, last_updated)` and corresponding indexes
  - If deferred: distance calculations happen on-demand in PR6 (Block X-Ray) using Haversine formula
- **Data compatibility:**
  - Upsert logic ensures idempotency (POI records are created or updated based on unique `poi_id` or `(poi_type, name, latitude, longitude)` tuple)
  - No backward compatibility concerns; additive only

**Infra / Config:**
- **Environment variables:**
  - `ONEMAP_API_KEY` (if OneMap requires authentication; verify during implementation)
  - `ONEMAP_API_BASE_URL` (default: `https://www.onemap.gov.sg/api/`)
  - `POI_INGESTION_THROTTLE_MS` (optional: milliseconds delay between API calls to respect rate limits; default: 100ms)
- **Scheduler configuration:**
  - Monthly cron triggers: MRT ingestion on 1st @ 03:30 SGT, POI ingestion on 1st @ 03:45 SGT
  - Jobs run in-process via APScheduler (no external queue needed for MVP)
- **Logging:**
  - Structured logs for ingestion start/completion, API call latency, errors, retry attempts
  - Ingestion_runs table records for audit trail

---

## 4. PR Roadmap

### PR 3: Data Ingestion Pipeline (POIs & MRT)
**Branch:** `pr3-data-ingestion-pois-mrt`  
**Status:** ✅ COMPLETE  
**Created:** 2026-01-09  
**Completed:** 2026-01-12  
**Dependencies:** PR1 (Database Schema), PR2 (HDB Data Ingestion), PR0 (Bootstrap)
**Goal**
Implement automated monthly ingestion for MRT/LRT stations and amenity POIs (supermarkets, clinics, parks, malls, hawkers) to complete the foundational location-based dataset infrastructure. Enable admin to manually trigger ingestion, and log all runs to the `ingestion_runs` audit table.

**Scope**

**In scope:**
- MRT/LRT station ingestion module (`src/resalelens/ingestion/mrt.py`):
  - Fetch station data from data.gov.sg or OneMap API
  - Parse station names, types (MRT/LRT), latitude, longitude
  - Upsert to `pois` table with `poi_type = 'MRT'` or `'LRT'`
  - Log ingestion run to `ingestion_runs` table
- Amenity POI ingestion module (`src/resalelens/ingestion/pois.py`):
  - Fetch POI data for supermarkets, clinics, parks, malls, hawkers (OneMap or CSV source)
  - Parse POI names, types, latitude, longitude
  - Upsert to `pois` table with appropriate `poi_type` values
  - Log ingestion run to `ingestion_runs` table
- APScheduler job registration for monthly ingestion (1st @ 03:30 SGT for MRT, 03:45 SGT for POIs)
- Manual trigger endpoints for admin (`POST /admin/ingestion/trigger?dataset=mrt`, `POST /admin/ingestion/trigger?dataset=pois`)
- Retry logic (3 retries with exponential backoff) on ingestion failures
- Unit and integration tests for ingestion modules

**Out of scope:**
- Precomputing block-to-POI distances (deferred; can be added as optional optimization in this PR or later)
- Routing/travel-time calculations (deferred to PR6 when Block X-Ray consumes this data)
- User-facing UI or API endpoints to query POIs (deferred to PR6)
- Data visualization or mapping features (deferred to future PRs)
- School POI ingestion (may be added in Phase 2 if required for family persona filters)
- Admin UI for ingestion status and manual trigger buttons → PR7 (Admin Dashboard & Lead Inbox)
  - Note: PR3 provides API endpoints (`POST /admin/ingestion/trigger?dataset=mrt|pois`); PR7 will add UI buttons in admin dashboard

**Backend Changes**

**Ingestion Modules:**
- **`src/resalelens/ingestion/mrt.py`:**
  - `fetch_mrt_stations()` — Call data.gov.sg or OneMap API to retrieve MRT/LRT station list
  - `parse_mrt_data(response)` — Extract station name, type (MRT/LRT), lat, lon
  - `ingest_mrt_stations()` — Orchestrate fetch → parse → upsert → log run
  - Use `@retry_on_failure` decorator from `utils.py` for API call resilience
  - Log run to `ingestion_runs` table (dataset_name='mrt', status='success'|'failed', rows_processed, error_summary)

- **`src/resalelens/ingestion/pois.py`:**
  - `fetch_pois_by_type(poi_type)` — Call OneMap or load CSV for given poi_type (supermarket, clinic, park, mall, hawker)
  - `parse_poi_data(response, poi_type)` — Extract name, lat, lon
  - `ingest_pois()` — Orchestrate fetch for all poi_types → parse → upsert → log run
  - Handle multiple poi_types in a single ingestion run (iterate over ['supermarket', 'clinic', 'park', 'mall', 'hawker'])
  - Use `@retry_on_failure` decorator for API calls
  - Log run to `ingestion_runs` table (dataset_name='pois', status, rows_processed, error_summary)

**Scheduler:**
- **`src/resalelens/scheduler.py`:**
  - Add monthly cron job `ingest_mrt_job` triggered on 1st @ 03:30 SGT (timezone='Asia/Singapore')
  - Add monthly cron job `ingest_pois_job` triggered on 1st @ 03:45 SGT
  - Register jobs in `configure_scheduler()` function
  - Ensure jobs invoke `ingest_mrt_stations()` and `ingest_pois()` respectively

**Admin Router:**
- **`src/resalelens/routers/admin.py`:**
  - Update `POST /admin/ingestion/trigger` endpoint to accept `dataset=mrt` and `dataset=pois`
  - Call appropriate ingestion function (`ingest_mrt_stations()` or `ingest_pois()`) based on dataset parameter
  - Return ingestion run result (run_id, status, rows_processed)
  - Require admin authentication (reuse existing auth middleware from PR2)

**Data Access:**
- **Utilize existing `POIRepository` from PR1:**
  - `upsert_pois(pois: List[POI])` — Bulk insert/update POI records with conflict resolution on poi_id or (poi_type, name, lat, lon)
  - `get_pois_by_type(poi_type: str)` — Query POIs by type (for testing/verification)

**Frontend Changes**
- No changes. This PR is backend-only.

**Data Changes**

**Migrations:**
- None required. PR1 already created the `pois` table with schema:
  - `poi_id` (primary key, UUID or auto-increment)
  - `poi_type` (string: 'MRT', 'LRT', 'supermarket', 'clinic', 'park', 'mall', 'hawker')
  - `name` (string: station or POI name)
  - `latitude` (float)
  - `longitude` (float)
  - `last_updated` (timestamp)
- PR1 includes indexes on `(poi_type, latitude, longitude)` for efficient spatial queries

**Optional Enhancement (Precomputed Distances):**
- If precomputed block-to-POI distances are implemented in this PR:
  - Create migration: `add_block_pois_table.py`
  - Schema: `block_pois` table with columns:
    - `id` (primary key)
    - `block_id` (foreign key to `blocks.id`)
    - `poi_id` (foreign key to `pois.poi_id`)
    - `distance_m` (float: Haversine distance in meters)
    - `last_updated` (timestamp)
  - Indexes: `(block_id, poi_id)`, `(block_id, distance_m)` for ranking queries
  - After POI ingestion completes, trigger batch distance computation:
    - For each block, calculate Haversine distance to all POIs
    - Insert/update `block_pois` records
    - This is a one-time bulk computation run after POI ingestion
- **Decision:** Recommend deferring precomputation to optimization phase unless Block X-Ray (PR6) performance requires it. Distance can be computed on-demand in PR6 using cached results.

**Backward Compatibility:**
- Fully backward-compatible. This PR only adds data; no schema changes to existing tables.
- Existing HDB transaction/block data from PR2 remains unaffected.

**Infra / Config**

**Environment Variables:**
- Add to `.env.example` and `config.py`:
  - `ONEMAP_API_KEY` (optional; default: empty if OneMap is open access)
  - `ONEMAP_API_BASE_URL` (default: `https://www.onemap.gov.sg/api/`)
  - `POI_INGESTION_THROTTLE_MS` (default: 100; milliseconds delay between API calls)
  - `MRT_DATA_SOURCE` (default: `onemap`; options: `onemap`, `data_gov_sg`)

**Scheduler Configuration:**
- Monthly cron triggers (APScheduler CronTrigger):
  - MRT: `day=1, hour=3, minute=30, timezone='Asia/Singapore'`
  - POIs: `day=1, hour=3, minute=45, timezone='Asia/Singapore'`

**Logging:**
- Structured JSON logs for:
  - Ingestion start/end timestamps
  - Dataset name (mrt, pois)
  - Rows processed
  - API call count and latency
  - Retry attempts
  - Errors (with stack traces)
- Example log entry:
  ```json
  {
    "timestamp": "2026-01-04T03:30:15+08:00",
    "level": "INFO",
    "message": "MRT ingestion started",
    "dataset": "mrt",
    "run_id": "abc123"
  }
  ```

**Testing**

**Unit Tests:**
- **`tests/ingestion/test_mrt.py`:**
  - Test `parse_mrt_data()` with mock API responses (valid, empty, malformed)
  - Test `fetch_mrt_stations()` with mocked HTTP client (success, timeout, 500 error)
  - Test retry logic (simulate transient failures, verify 3 retries)
  - Verify ingestion_run log creation and status updates

- **`tests/ingestion/test_pois.py`:**
  - Test `parse_poi_data()` for each poi_type with mock responses
  - Test `fetch_pois_by_type()` with mocked HTTP client
  - Test multi-type ingestion (all 5 poi_types processed correctly)
  - Verify retry logic and run logging

**Integration Tests:**
- **`tests/test_ingestion_integration.py`:**
  - Test end-to-end MRT ingestion with test database:
    - Mock API response with 10 MRT stations
    - Call `ingest_mrt_stations()`
    - Verify 10 POI records inserted with poi_type='MRT'
    - Verify ingestion_run record created with status='success', rows_processed=10
  - Test POI ingestion with test database:
    - Mock responses for supermarkets, clinics, parks, malls, hawkers
    - Call `ingest_pois()`
    - Verify correct number of POI records inserted for each type
    - Verify ingestion_run record
  - Test upsert idempotency:
    - Run ingestion twice with same data
    - Verify row count remains constant (no duplicates)
  - Test failure handling:
    - Mock API 500 error
    - Verify retry attempts logged
    - Verify ingestion_run status='failed' and error_summary populated

**Manual Checks:**
- Start dev server: `uv run uvicorn src.resalelens.main:app --reload`
- Trigger manual MRT ingestion: `POST /admin/ingestion/trigger?dataset=mrt` (requires admin auth)
- Verify `pois` table populated with MRT/LRT stations: `SELECT COUNT(*) FROM pois WHERE poi_type IN ('MRT', 'LRT')`
- Trigger manual POI ingestion: `POST /admin/ingestion/trigger?dataset=pois`
- Verify `pois` table populated with amenities: `SELECT poi_type, COUNT(*) FROM pois GROUP BY poi_type`
- Check `ingestion_runs` table for successful run records
- Wait for monthly scheduler (or manually advance time in testing) and verify scheduled jobs execute

**Verification**

**Commands to run:**
- **Install:** `uv sync`
- **Dev server:** `uv run uvicorn src.resalelens.main:app --reload`
- **Test:** `uv run pytest tests/ingestion/ -v`
- **Lint:** `uv run ruff check .`
- **Typecheck:** `uv run mypy src/`
- **DB migrate:** `uv run alembic upgrade head` (no new migrations in this PR, but verify clean state)
- **Manual ingestion trigger (MRT):** `curl -X POST http://localhost:8000/admin/ingestion/trigger?dataset=mrt -u admin:password`
- **Manual ingestion trigger (POIs):** `curl -X POST http://localhost:8000/admin/ingestion/trigger?dataset=pois -u admin:password`

**Manual Verification Checklist:**
1. **MRT Ingestion:**
   - [ ] Manual trigger completes successfully within 30 seconds
   - [ ] `ingestion_runs` table shows run record with status='success'
   - [ ] `pois` table contains MRT/LRT stations (expected count: ~130 MRT stations + ~40 LRT stations in Singapore)
   - [ ] Sample query returns valid data: `SELECT * FROM pois WHERE poi_type='MRT' LIMIT 5`
2. **POI Ingestion:**
   - [ ] Manual trigger completes successfully within 60 seconds (may be slower due to multiple API calls)
   - [ ] `ingestion_runs` table shows run record with status='success'
   - [ ] `pois` table contains POIs for all types: `SELECT poi_type, COUNT(*) FROM pois WHERE poi_type IN ('supermarket', 'clinic', 'park', 'mall', 'hawker') GROUP BY poi_type`
   - [ ] Sample query returns valid data for each type
3. **Scheduler Registration:**
   - [ ] Start dev server and check logs for scheduler registration messages: `"Registered job: ingest_mrt_job"`, `"Registered job: ingest_pois_job"`
   - [ ] Query APScheduler job list (via admin endpoint or logs) to confirm monthly cron triggers
4. **Error Handling:**
   - [ ] Simulate API failure (mock or disconnect network), verify retry logic executes 3 times
   - [ ] Verify `ingestion_runs` table shows status='failed' and error_summary populated
5. **Data Quality:**
   - [ ] Spot-check 5 random MRT stations: verify names, coordinates (compare with OneMap or Google Maps)
   - [ ] Spot-check POIs: verify supermarkets (e.g., FairPrice, Cold Storage), clinics, parks are present
6. **Performance:**
   - [ ] MRT ingestion completes in < 30s (target: 10–20s for ~170 stations)
   - [ ] POI ingestion completes in < 60s (may vary by API rate limits; monitor and optimize with throttling if needed)

**Rollback Plan**

**Feature flag / kill switch:**
- None required. Ingestion jobs run in background and do not affect user-facing features in this PR.
- If ingestion fails, previous data remains in `pois` table (no destructive operations).
- Admin can disable scheduled jobs by setting environment variable `ENABLE_SCHEDULED_INGESTION=false` in `config.py` (add this flag in PR3 for operational control).

**Revert strategy:**
- If PR3 is reverted:
  - APScheduler jobs for MRT/POI are unregistered (no scheduled ingestion runs)
  - `pois` table retains any previously ingested data (no data loss)
  - Manual trigger endpoints are removed (admin cannot trigger MRT/POI ingestion)
  - No impact on HDB transaction/block ingestion (PR2 remains functional)
- **Data rollback:**
  - If ingested POI data is incorrect, admin can manually delete: `DELETE FROM pois WHERE poi_type IN ('MRT', 'LRT', 'supermarket', 'clinic', 'park', 'mall', 'hawker')`
  - Then re-run manual ingestion trigger with corrected source
- **Migration rollback (if optional `block_pois` table is added):**
  - If precomputation is implemented: `uv run alembic downgrade -1` to drop `block_pois` table
  - No foreign key constraints break (block_pois is independent)

**Dependencies**
- **PRs that must be merged before this one:**
  - **PR0 (Bootstrap):** APScheduler setup, Alembic migrations, FastAPI app skeleton
  - **PR1 (Database Schema):** `pois` table, `ingestion_runs` table, `POIRepository`, retry decorator in `utils.py`
  - **PR2 (HDB Ingestion):** Ingestion pattern established, `@retry_on_failure` decorator, run logging utility, admin manual trigger endpoint pattern
- **External dependencies:**
  - OneMap API or data.gov.sg API access (verify API availability and authentication requirements during implementation)
  - Admin authentication working (from PR2)

**Risks & Mitigations**

**Main Risks:**

1. **OneMap API Rate Limits**
   - **Risk:** Bulk POI queries may hit rate limits (e.g., 250 requests/minute), causing ingestion failures or delays.
   - **Mitigation:**
     - Implement throttling: `time.sleep(POI_INGESTION_THROTTLE_MS / 1000)` between API calls
     - Batch requests if OneMap supports bulk queries
     - Fallback to CSV ingestion if API is unreliable (curate POI CSV manually or from alternative source)
     - Monitor API response times and adjust throttling dynamically
     - Retry logic (3 retries) handles transient rate limit errors (429 status)

2. **Data Quality / Schema Changes in External APIs**
   - **Risk:** OneMap or data.gov.sg API may change response schemas, breaking parsing logic.
   - **Mitigation:**
     - Version API requests (if supported) or document API version used
     - Schema validation: fail fast with clear error messages if expected fields are missing
     - Fallback to last successful dataset if new ingestion fails (users see "Using last successful snapshot" on Data Status page in PR6)
     - Add integration tests with real API responses (capture samples as fixtures)

3. **Incomplete POI Coverage**
   - **Risk:** OneMap may not have comprehensive POI data for all types (e.g., missing hawker centres in certain areas).
   - **Mitigation:**
     - Document known gaps in `docs/technical/context.md`
     - Allow admin to supplement with manual CSV uploads (add CSV ingestion path as optional enhancement)
     - Clearly label POI data sources on Data Status page (PR6) so users understand provenance

4. **Precomputed Distance Performance Impact**
   - **Risk:** If precomputed block-to-POI distances are implemented, bulk computation may take significant time (e.g., 5,000 blocks × 500 POIs = 2.5M distance calculations).
   - **Mitigation:**
     - Defer precomputation to async background job after POI ingestion (don't block ingestion completion)
     - Use spatial indexing (PostGIS in production PostgreSQL) or KD-tree for efficient nearest-neighbor queries
     - Recommend deferring precomputation to optimization phase; compute distances on-demand in PR6 with caching

5. **Timezone Issues in Scheduler**
   - **Risk:** APScheduler cron jobs may not respect Singapore timezone correctly, causing ingestion to run at incorrect times.
   - **Mitigation:**
     - Explicitly set `timezone='Asia/Singapore'` in CronTrigger
     - Add unit test to verify job next_run_time is correct (mock current time and verify scheduled time)
     - Log scheduler timezone on startup for debugging

---

## 5. Milestones & Sequence

**Milestone 1: MRT/POI Ingestion Infrastructure Complete**
- **PRs Included:** PR3
- **What it unlocks:** Foundational location-based dataset (MRT/LRT stations, amenity POIs) is available in database
- **Definition of "Done":**
  - MRT/LRT ingestion module implemented and tested
  - Amenity POI ingestion module implemented and tested (supermarkets, clinics, parks, malls, hawkers)
  - Monthly APScheduler jobs registered and verified
  - Admin manual trigger endpoints working
  - `pois` table populated with valid data (spot-checked)
  - `ingestion_runs` audit logs capture all ingestion attempts
  - All tests passing (unit, integration)
  - CI pipeline green (lint, typecheck, tests)
  - Ready for Block X-Ray (PR6) to consume POI data for distance calculations

---

## 6. Risks, Trade-offs, and Open Questions

### Major Risks

1. **OneMap API Reliability and Rate Limits**
   - **Technical Risk:** API may be slow, unreliable, or rate-limited, blocking ingestion.
   - **Mitigation:** Throttling, retry logic, CSV fallback, monitoring, and graceful degradation (use last successful snapshot).

2. **Data Quality and Completeness**
   - **Product Risk:** Incomplete or stale POI data may reduce Block X-Ray usefulness (e.g., missing supermarkets in certain areas).
   - **Mitigation:** Document data sources and gaps; allow manual CSV supplements; surface data freshness on Data Status page.

3. **Precomputation Performance Overhead**
   - **Technical Risk:** Bulk distance computation may be too slow for in-process APScheduler jobs.
   - **Mitigation:** Defer precomputation; make it async/background; or skip entirely and compute distances on-demand in PR6.

4. **Timezone Configuration Errors**
   - **Technical Risk:** Scheduler may run jobs at incorrect times if timezone is misconfigured.
   - **Mitigation:** Explicit timezone setting, unit tests, startup logging.

### Trade-offs

1. **OneMap API vs. Curated CSV for POI Data**
   - **Choice:** Start with OneMap API; add CSV fallback if needed.
   - **Trade-off:** API provides automatic updates but introduces external dependency and rate limit risk. CSV is static but reliable.
   - **Rationale:** API-first approach aligns with automation goals; CSV fallback mitigates risk without blocking progress.

2. **Precomputed Distances vs. On-Demand Calculation**
   - **Choice:** Defer precomputation to optimization phase; compute distances on-demand in PR6.
   - **Trade-off:** On-demand is simpler and faster to implement but may have higher query latency. Precomputed is faster for users but adds complexity and storage overhead.
   - **Rationale:** MVP should prioritize simplicity and speed to market; optimize later if Block X-Ray performance is insufficient.

3. **Monthly vs. Weekly Ingestion for POIs**
   - **Choice:** Monthly ingestion for MRT/POI data.
   - **Trade-off:** Monthly reduces API call costs and server load but may miss new POIs (e.g., new MRT stations, malls). Weekly is more current but adds overhead.
   - **Rationale:** POI infrastructure (MRT, malls, clinics) changes infrequently; monthly is sufficient for MVP. Can increase frequency in Phase 2 if users request fresher data.

4. **In-Process APScheduler vs. External Job Queue (Celery)**
   - **Choice:** In-process APScheduler for MVP.
   - **Trade-off:** Simpler setup and no external dependencies, but less fault-tolerant and not horizontally scalable.
   - **Rationale:** Monthly POI ingestion volume is low; in-process is sufficient. Migrate to Celery in Phase 4 if job volume or reliability requirements increase.

### Open Questions

1. **OneMap API Authentication and Access**
   - **Question:** Does OneMap API require an API key or registration? What are the rate limits?
   - **Action:** Research OneMap API documentation during implementation; register for API key if needed; document in `docs/technical/context.md`.
   - **Impact on plan:** If OneMap requires paid tier or has strict rate limits, may need to pivot to CSV ingestion or alternative POI source.

2. **POI Data Schema and Categories**
   - **Question:** What are the exact poi_type values and field schemas returned by OneMap? Do we need to map OneMap categories to our simplified categories (supermarket, clinic, park, mall, hawker)?
   - **Action:** Document OneMap schema mapping in `src/resalelens/ingestion/pois.py` comments; add unit tests for schema mapping logic.
   - **Impact on plan:** Schema mismatches may require additional parsing/normalization logic.

3. **MRT Data Source Choice**
   - **Question:** Is data.gov.sg or OneMap the more reliable source for MRT/LRT station data?
   - **Action:** Test both APIs during implementation; choose the more reliable and complete source; make source configurable via `MRT_DATA_SOURCE` environment variable.
   - **Impact on plan:** If both sources are unreliable, may need to curate static MRT CSV (acceptable fallback since MRT network changes infrequently).

4. **Should Schools Be Included in PR3?**
   - **Question:** Should school POI ingestion be included in this PR, or deferred to Phase 2 (family persona filters)?
   - **Recommendation:** Defer to Phase 2 unless PSD family persona filters require schools for MVP.
   - **Rationale:** Schools add complexity (primary vs secondary, ranking/quality data, catchment areas). Start with simpler POI types in PR3; add schools in Phase 2 with persona filter implementation.
   - **Impact on plan:** If schools are required for MVP, add school ingestion module in PR3 (similar pattern to other POIs).

5. **Optimal Precomputation Strategy**
   - **Question:** If precomputed distances are implemented, should computation run synchronously after POI ingestion, or as a separate async job?
   - **Recommendation:** If implemented in PR3, run as separate async job triggered after POI ingestion completes. Do not block POI ingestion completion.
   - **Impact on plan:** Adds complexity (async job orchestration); recommend deferring precomputation entirely to optimization phase.

---

**Next Steps:**
1. Review this plan with stakeholders to confirm scope and resolve open questions
2. Create feature branch: `git checkout -b pr3-ingestion-pois-mrt`
3. Implement MRT ingestion module with tests
4. Implement POI ingestion module with tests
5. Update scheduler and admin router
6. Run full test suite and verification checklist
7. Submit PR for review

---

*This plan follows the `/plan_epic` workflow structure and is ready for implementation using `/implement_task`.*
