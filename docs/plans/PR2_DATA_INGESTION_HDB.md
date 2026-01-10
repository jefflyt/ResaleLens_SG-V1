# PR2: Data Ingestion Pipeline (HDB Transactions & Blocks)

> **✅ IMPLEMENTATION STATUS: COMPLETE** (2026-01-10)  
> All deliverables implemented, tested, and optimized. 222,835 HDB transactions successfully ingested with bulk upsert optimization (170x faster than initial implementation). See [Verification Report](file:///Users/jefflee/.gemini/antigravity/brain/98f7bb22-b5b2-4a13-8154-dd6a3869e5fe/pr1.2_pr2_verification.md) for details.
>
> **Performance:** Bulk upsert with PostgreSQL `INSERT ... ON CONFLICT` reduces database operations from 444K to 223 (1,991x improvement).

**Branch:** `pr2-ingestion-hdb`  
**Date:** 2026-01-05  
**Based on:** MASTER_PLAN.md (Phase 1, PR2)

---

## 1. Feature/Epic Summary

### Objective
Implement automated data ingestion pipeline for HDB resale transactions and block metadata from data.gov.sg, with robust error handling, retry logic, audit logging, and scheduled execution to ensure ResaleLens has fresh, reliable data for Fair Value calculations and Block X-Ray features.

### User Impact
- **Indirect (Foundation):** Users won't interact with ingestion directly, but this enables all core features:
  - Fair Value Engine requires historical transaction data
  - Block X-Ray requires block metadata with geocoding
  - Data Status page will show freshness and health of datasets
- **Admin (Direct):** Admin can manually trigger data refresh and monitor ingestion status via admin panel

### Dependencies
- **Prerequisite:** PR1 (Database Schema) must be merged
  - Requires: `transactions`, `blocks`, and `ingestion_runs` tables
  - Requires: Repository pattern for data access
- **External Services:**
  - data.gov.sg API for HDB resale transactions
  - OneMap API (or alternative) for geocoding block addresses
- **Scheduler:** APScheduler from PR0 for automated weekly runs

### Assumptions
1. **Assumption:** data.gov.sg HDB Resale Prices API is free, publicly accessible, and returns JSON with stable schema
2. **Assumption:** HDB transaction data is published at least monthly; weekly ingestion is sufficient to stay fresh
3. **Assumption:** OneMap API geocoding is free for moderate usage (<1000 requests/day) or has acceptable fallback (manual geocoding or pre-built address database)
4. **Assumption:** Ingestion can safely upsert (insert or update) existing records without data loss
5. **Assumption:** Initial ingestion can process 100k+ transaction records in <30 minutes (acceptable for manual trigger)
6. **Assumption:** Supabase PostgreSQL (from PR1.1) is used for production data ingestion and storage; SQLite remains for local development

> **📌 Production Database:**  
> After PR1.1 is implemented, this PR should ingest data into **Supabase PostgreSQL** for production use. Set `DATABASE_URL` to your Supabase connection string before running ingestion jobs to ensure external customers see real-time data.

---

## 2. Complexity & Fit

### Classification
**Single-PR** — This is a focused backend feature with clear boundaries and no UI complexity.

### Rationale
- **Single data layer:** Only backend ingestion logic, no frontend changes
- **No user-facing features:** Admin trigger endpoint only; ingestion runs in background
- **Clear scope:** Two ingestion modules (transactions + blocks) with shared infrastructure
- **Self-contained:** Can be tested independently with mock API responses
- **Low cross-cutting risk:** Only writes to new tables; doesn't affect existing features (PR0-PR1)
- **Sequential dependencies:** Block ingestion doesn't depend on transaction ingestion; can run independently

### Estimated Effort
1 PR with approximately 10-15 hours of work for a solo founder.

---

## 3. Full-Stack Impact

### Frontend
**No changes planned.** Ingestion is a backend-only feature. Admin UI for ingestion triggers will be added in PR7 (Admin Lead Inbox).

### Backend
- **New Modules:**
  - `src/resalelens/ingestion/hdb_transactions.py` — Fetch, parse, and upsert HDB transaction data
  - `src/resalelens/ingestion/hdb_blocks.py` — Fetch, parse, geocode, and upsert block metadata
  - `src/resalelens/ingestion/utils.py` — Shared utilities (retry decorator, run logging, API client helpers)
  - `src/resalelens/ingestion/__init__.py` — Package marker
- **New Router:**
  - `src/resalelens/routers/admin.py` — Admin-only endpoints for manual ingestion triggers
- **Updated Module:**
  - `src/resalelens/scheduler.py` — Register weekly ingestion jobs (Sundays 03:00 and 03:15 SGT)
- **New Services (optional abstraction):**
  - `src/resalelens/services/ingestion_service.py` — Orchestration layer for ingestion runs (optional; can be part of ingestion modules)

### Data
- **Tables Used:**
  - `transactions` — Insert/upsert HDB resale transaction records
  - `blocks` — Insert/upsert block metadata (address, geocoding, lease_commence_year)
  - `ingestion_runs` — Log all ingestion attempts (start, end, status, rows processed, errors)
- **No Schema Changes:** PR1 already defined all required tables
- **Data Volume Estimates:**
  - Transactions: ~10,000-30,000 new records per month (historical backfill may be 100k+)
  - Blocks: ~10,000-15,000 unique blocks (one-time full refresh, then incremental updates)

### Infra / Config
- **Environment Variables:**
  - `DATA_GOV_SG_API_URL` — Base URL for data.gov.sg API (default: `https://data.gov.sg/api/action/datastore_search`)
  - `DATA_GOV_SG_RESOURCE_ID` — Resource ID for HDB resale prices dataset
  - `ONEMAP_API_KEY` — API key for OneMap geocoding (if required)
  - `ONEMAP_API_URL` — Base URL for OneMap API (default: `https://www.onemap.gov.sg/api/common/elastic/search`)
  - `INGESTION_RETRY_COUNT` — Number of retries on failure (default: 3)
  - `INGESTION_RETRY_DELAY_SECONDS` — Initial retry delay in seconds (default: 5, exponential backoff)
- **Scheduler Config:**
  - HDB Transactions: Every Sunday 03:00 SGT (weekly)
  - HDB Blocks: Every Sunday 03:15 SGT (weekly, after transactions)
- **No CI/CD Changes:** Existing pytest, ruff, mypy workflows cover ingestion modules

---

## 4. PR Roadmap

### PR 2: Data Ingestion Pipeline (HDB Transactions & Blocks)

#### Goal
Enable automated weekly ingestion of HDB resale transactions and block metadata from data.gov.sg, with error handling, retry logic, audit logging, manual admin triggers, and Data Status page readiness.

#### Scope

**In scope:**
- Fetch HDB resale transaction data from data.gov.sg API
- Parse and validate transaction records (date, block, street, flat_type, price, etc.)
- Upsert transactions to database (insert new, update existing based on unique constraint)
- Fetch HDB block/address data (either from data.gov.sg or curated source)
- Geocode block addresses using OneMap API or fallback to pre-built geocoding database
- Upsert blocks to database
- Log all ingestion runs to `ingestion_runs` table (start, end, status, rows processed, error summary)
- Implement retry logic with exponential backoff (3 retries, configurable delay)
- Manual admin trigger endpoint: `POST /admin/ingestion/trigger?dataset=hdb_transactions` and `POST /admin/ingestion/trigger?dataset=hdb_blocks`
- Schedule weekly ingestion jobs via APScheduler (Sundays 03:00 and 03:15 SGT)
- Unit tests for ingestion modules (with mocked API responses)
- Integration tests for database upsert logic
- Manual verification of ingestion with sample data

**Out of scope:**
- POI and MRT ingestion → PR3
- Admin UI for ingestion status/history and manual trigger buttons → PR7 (Admin Dashboard & Lead Inbox)
  - Note: PR2 provides API endpoints (`POST /admin/ingestion/trigger`); PR7 will add UI buttons in admin dashboard
- Data Status page UI → PR6 (Block X-Ray & Data Status Page)
- Fair Value calculation logic → PR4
- Advanced geocoding (e.g., handling unit-level addresses) → Defer to Phase 2+
- Incremental ingestion optimization (delta sync) → MVP uses full refresh; optimize later if needed

#### Backend Changes

**Ingestion Modules:**

1. `src/resalelens/ingestion/__init__.py`
   - Package marker
   - Export main ingestion functions

2. `src/resalelens/ingestion/utils.py`
   - `retry_on_failure` decorator: Retry function calls with exponential backoff
   - `log_ingestion_run` context manager: Create `IngestionRun` record, update on success/failure
   - `fetch_json_with_retry` helper: HTTP client with retry logic for external APIs
   - `parse_date` helper: Parse date strings from various formats (data.gov.sg may vary)
   - `validate_transaction_record` helper: Ensure required fields present and valid

3. `src/resalelens/ingestion/hdb_transactions.py`
   - `ingest_hdb_transactions()` function:
     - Fetch all HDB resale transaction records from data.gov.sg API (paginated if needed)
     - Parse JSON response into Transaction model instances
     - Validate records (skip/log invalid records)
     - Upsert to `transactions` table using `TransactionRepository`
     - Calculate `psm` on-the-fly (not stored; computed property)
     - Link to current `IngestionRun` via `ingestion_run_id`
     - Return summary: rows processed, rows inserted, rows updated, errors
   - Error handling: Log errors to `ingestion_runs.error_summary`; don't crash on individual record failures

4. `src/resalelens/ingestion/hdb_blocks.py`
   - `ingest_hdb_blocks()` function:
     - Extract unique (block, street, town) combinations from ingested transactions or fetch from data.gov.sg block dataset
     - For each block:
       - Geocode address using OneMap API (`https://www.onemap.gov.sg/api/common/elastic/search?searchVal=<address>`)
       - Extract `latitude`, `longitude` from API response
       - Handle geocoding failures: log warning, set lat/lng to null, continue
     - Upsert to `blocks` table using `BlockRepository`
     - Set `last_updated` to current timestamp
     - Return summary: rows processed, rows inserted, rows updated, geocoding failures
   - Rate limiting: Respect OneMap API rate limits (e.g., max 250 req/min); add delay if needed
   - Fallback: If OneMap fails repeatedly, allow manual geocoding or use pre-built lat/lng database

**Admin Router:**

5. `src/resalelens/routers/admin.py`
   - `POST /admin/ingestion/trigger`:
     - Query param: `dataset` (values: `hdb_transactions`, `hdb_blocks`)
     - Endpoint triggers ingestion function asynchronously (or synchronously with timeout for MVP)
     - Returns: `{"status": "started", "run_id": <ingestion_run_id>}` or `{"status": "success", "summary": {...}}`
     - Requires admin authentication (HTTP Basic or session-based from PR0)
   - Error handling: Return 400 if invalid dataset; 500 if ingestion fails to start

**Scheduler Update:**

6. `src/resalelens/scheduler.py`
   - Add two scheduled jobs:
     - `hdb_transactions_weekly`: Runs `ingest_hdb_transactions()` every Sunday 03:00 SGT
     - `hdb_blocks_weekly`: Runs `ingest_hdb_blocks()` every Sunday 03:15 SGT (15-min delay to avoid overlap)
   - Job configuration:
     - Trigger: `CronTrigger(day_of_week='sun', hour=3, minute=0, timezone='Asia/Singapore')` for transactions
     - Trigger: `CronTrigger(day_of_week='sun', hour=3, minute=15, timezone='Asia/Singapore')` for blocks
     - `max_instances=1` to prevent concurrent runs
     - `replace_existing=True` on app restart

**Dependencies:**

7. Add to `pyproject.toml`:
   - `httpx` — Already included in PR0 for testing; use for API requests
   - `tenacity` (optional) — Advanced retry library; can use custom retry decorator instead

#### Frontend Changes
**No frontend changes in this PR.**

#### Data Changes

**No schema changes.** PR1 already created all required tables.

**Data Operations:**
- **Upsert strategy:**
  - Transactions: Use SQLAlchemy's `session.merge()` or `INSERT ... ON CONFLICT UPDATE` (PostgreSQL) / `INSERT OR REPLACE` (SQLite)
  - Unique constraint: (block, street, flat_type, date, storey_range, floor_area_sqm)
  - Blocks: Use same upsert strategy with unique constraint (block, street)
- **Ingestion run logging:**
  - Create `IngestionRun` record at start (`status='in_progress'`)
  - Update on completion (`status='success'`, `completed_at=now()`, `rows_processed=N`)
  - Update on failure (`status='failed'`, `error_summary=<exception details>`)

**Initial Data Load (Manual Trigger):**
- Admin should manually trigger full historical ingestion on first deployment:
  - `POST /admin/ingestion/trigger?dataset=hdb_transactions` (may take 10-30 minutes for 100k+ records)
  - `POST /admin/ingestion/trigger?dataset=hdb_blocks` (may take 5-15 minutes for 10k+ blocks with geocoding)
- Subsequent weekly runs will be incremental if API supports filtering by date; otherwise full refresh (acceptable for MVP)

#### Infra / Config

**Environment Variables (.env.example update):**

Add to `.env.example`:
```
# Data Ingestion
DATA_GOV_SG_API_URL=https://data.gov.sg/api/action/datastore_search
DATA_GOV_SG_RESOURCE_ID=<resource_id_for_hdb_resale_prices>
ONEMAP_API_URL=https://www.onemap.gov.sg/api/common/elastic/search
ONEMAP_API_KEY=  # Leave blank if OneMap doesn't require key
INGESTION_RETRY_COUNT=3
INGESTION_RETRY_DELAY_SECONDS=5
```

**No CI/CD changes.** Existing workflows cover new modules.

#### Testing

**Unit Tests (`tests/ingestion/test_hdb_transactions.py`):**
- Mock data.gov.sg API responses (use `httpx.MockTransport` or `responses` library)
- Test parsing of transaction records (valid and invalid records)
- Test upsert logic (insert new, update existing)
- Test retry logic on API failures (network errors, timeouts, HTTP 500)
- Test error handling (malformed JSON, missing fields)

**Unit Tests (`tests/ingestion/test_hdb_blocks.py`):**
- Mock OneMap geocoding API responses
- Test block extraction from transactions
- Test geocoding success and failure paths
- Test upsert logic for blocks

**Unit Tests (`tests/ingestion/test_utils.py`):**
- Test `retry_on_failure` decorator with configurable retries
- Test `log_ingestion_run` context manager (success and failure cases)
- Test date parsing for various formats

**Integration Tests (`tests/integration/test_ingestion_full.py`):**
- End-to-end ingestion with test database
- Use fixture with sample JSON data (5-10 transactions, 3-5 blocks)
- Verify records inserted into `transactions` and `blocks` tables
- Verify `ingestion_runs` table has correct logs

**Manual Checks:**
- Trigger manual ingestion via admin endpoint
- Check logs for ingestion progress and any errors
- Inspect database: verify transactions and blocks inserted
- Check `ingestion_runs` table for status and error_summary
- Verify geocoding worked (blocks have non-null lat/lng)

#### Verification

**Commands (from docs/technical/context.md):**

Install dependencies (if new packages added):
```
uv sync
```

Run unit tests:
```
uv run pytest tests/ingestion/ -v
```

Run integration tests:
```
uv run pytest tests/integration/test_ingestion_full.py -v
```

Lint and typecheck:
```
uv run ruff check .
uv run mypy src/
```

Start development server:
```
uv run uvicorn src.resalelens.main:app --reload
```

Manual ingestion trigger (requires admin auth):
```
curl -X POST http://localhost:8000/admin/ingestion/trigger?dataset=hdb_transactions \
  -u admin:password

curl -X POST http://localhost:8000/admin/ingestion/trigger?dataset=hdb_blocks \
  -u admin:password
```

Check ingestion runs in database:
```
uv run python -c "
from src.resalelens.database import SessionLocal
from src.resalelens.models import IngestionRun
db = SessionLocal()
runs = db.query(IngestionRun).order_by(IngestionRun.started_at.desc()).limit(5).all()
for run in runs:
    print(f'{run.dataset_name}: {run.status} - {run.rows_processed} rows')
db.close()
"
```

**Manual Verification Checklist:**
1. ✅ Manual trigger for `hdb_transactions` completes without errors
2. ✅ `transactions` table populated with realistic HDB data
3. ✅ `ingestion_runs` table shows successful run with `status='success'` and `rows_processed > 0`
4. ✅ Manual trigger for `hdb_blocks` completes without errors
5. ✅ `blocks` table populated with unique blocks from transactions
6. ✅ Blocks have non-null `latitude` and `longitude` (most should be geocoded successfully)
7. ✅ Retry logic works: simulate API failure (disconnect network or mock 500 error), verify retries logged
8. ✅ Scheduled jobs registered in APScheduler: check logs show job names and next run times
9. ✅ All tests pass (`pytest` shows 0 failures)
10. ✅ Ruff and mypy report no errors

#### Rollback Plan

**Feature Flag:** Not applicable (no user-facing features).

**Revert Strategy:**
- **If PR is reverted:**
  - Ingestion modules will be removed
  - Scheduled jobs will no longer run
  - Admin trigger endpoint will return 404
  - `transactions` and `blocks` tables will be empty (data from ingestion runs will be lost unless backed up)
  - `ingestion_runs` table will retain audit logs (safe to keep)
- **Data Rollback:**
  - If ingestion corrupts data (unlikely with upsert logic), manually delete rows from `transactions` and `blocks` where `created_at > <PR2_merge_time>`
  - Or restore from database backup if available
- **Safe to revert:** Yes, as long as no downstream features (PR4-PR7) have been deployed yet

**Migration Rollback:** Not applicable (no schema changes).

#### Dependencies

**Prerequisite PRs:**
- ✅ PR0 (Project Bootstrap) — Provides FastAPI, SQLAlchemy, APScheduler, pytest
- ✅ PR1 (Database Schema) — Provides `transactions`, `blocks`, `ingestion_runs` tables and repositories

**External Dependencies:**
- data.gov.sg HDB Resale Prices API — Must be accessible and return valid JSON
- OneMap API — Must be accessible for geocoding (or use fallback pre-built database)
- OneMap API Key (if required) — Obtain from OneMap developer portal

**API Validation Results (Validated: 2026-01-10):**

> 📋 **Full details:** See [docs/decisions/PR2_API_VALIDATION.md](file:///Users/jefflee/Documents/AIProjects/ResaleLens_SG-V1/docs/decisions/PR2_API_VALIDATION.md) for complete testing results and schemas.

✅ **data.gov.sg HDB Resale Prices API - READY**
- **Resource ID:** `d_8b84c4ee58e3cfc0ece0d773c8ca6abc`
- **Full Endpoint:** `https://data.gov.sg/api/action/datastore_search?resource_id=d_8b84c4ee58e3cfc0ece0d773c8ca6abc`
- **Authentication:** None required (publicly accessible)
- **Rate Limits:** No apparent limits (tested 10+ consecutive requests successfully)
- **Total Records:** 222,835 HDB resale transactions (Jan 2017 onwards)
- **Response Time:** ~0.4s average
- **Pagination:** Supports `limit` and `offset` parameters
- **Cost:** Free

⚠️ **OneMap Geocoding API - REQUIRES SETUP**
- **Search Endpoint:** `https://www.onemap.gov.sg/api/common/elastic/search`
- **Auth Endpoint:** `https://www.onemap.gov.sg/api/auth/post/getToken`
- **Authentication:** Required (JWT token with 3-day TTL)
- **Rate Limit:** 250 requests per token session
- **Registration:** Free account required at https://www.onemap.gov.sg/apidocs/
- **Cost:** Free tier (suitable for MVP)

**Action Items Before Implementation:**
1. ✅ data.gov.sg API validated - ready to use
2. ⚠️ Register OneMap account (REQUIRED before starting PR2)
3. ⚠️ Implement token management with auto-refresh logic
4. ⚠️ Add OneMap credentials to `.env.local` (email, password)
5. ⚠️ Track request count per token (refresh after 240 requests for safety margin)

#### Risks & Mitigations

**Risk 1: data.gov.sg API Rate Limits or Downtime**
- **Risk:** API may have undocumented rate limits, or API may be down during ingestion window
- **Mitigation:**
  - Implement retry logic with exponential backoff
  - Add rate limiting (e.g., max 10 req/sec) to avoid overwhelming API
  - Log all API failures to `ingestion_runs.error_summary`
  - Allow manual retry via admin trigger if scheduled job fails
  - Consider caching API responses or downloading CSV as fallback

**Risk 2: Geocoding API Failures or Costs**
- **Risk:** OneMap API may fail, have rate limits, or require paid subscription for high volume
- **Mitigation:**
  - Graceful degradation: If geocoding fails, set lat/lng to null and log warning
  - Batch geocoding requests (e.g., 100 blocks at a time) with delays
  - Pre-build geocoding database from known HDB blocks (one-time manual effort)
  - Fallback to approximate geocoding (e.g., town-level centroids) if needed

**Risk 3: Data Quality Issues (Missing or Malformed Records)**
- **Risk:** data.gov.sg may return incomplete or malformed transaction records
- **Mitigation:**
  - Validate all records before inserting (check required fields: date, block, price, etc.)
  - Skip invalid records and log to `error_summary`
  - Ingestion continues even if some records fail
  - Include data quality metrics in `ingestion_runs` (e.g., `rows_skipped`, `validation_errors`)

**Risk 4: Ingestion Performance (Slow Upsert with 100k+ Records)**
- **Risk:** Initial full ingestion may take 30+ minutes, causing timeout or blocking scheduler
- **Mitigation:**
  - Use batch inserts (e.g., 1000 records per transaction) for performance
  - SQLAlchemy's `bulk_insert_mappings` or `executemany` for large batches
  - Run initial ingestion manually via admin trigger (not scheduled)
  - Optimize unique constraint checking (ensure indexes exist from PR1)
  - Consider PostgreSQL `COPY` for extremely large datasets (defer to production optimization)

**Risk 5: Scheduler Conflicts (Overlapping Jobs)**
- **Risk:** If blocks ingestion starts before transactions complete, may process incomplete data
- **Mitigation:**
  - Schedule blocks ingestion 15 minutes after transactions (03:15 vs 03:00)
  - Set `max_instances=1` on APScheduler jobs to prevent overlaps
  - Blocks ingestion can also run independently (doesn't strictly need transactions to finish first)
  - Monitor ingestion durations; adjust schedule if jobs consistently take >15 minutes

**Risk 6: Time Zone Confusion (SGT vs UTC)**
- **Risk:** APScheduler may use UTC instead of SGT, causing jobs to run at wrong time
- **Mitigation:**
  - Explicitly set `timezone='Asia/Singapore'` in CronTrigger
  - Test scheduler in local dev environment (manually set system time or use freezegun for tests)
  - Log all scheduled job times in SGT for clarity

---

## 5. Milestones & Sequence

**Milestone 1: Data Foundation Ready (PR2)**
- What it unlocks: HDB transaction and block data available for Fair Value Engine (PR4) and Block X-Ray (PR6)
- PRs included: PR2
- "Done" means:
  - ✅ `transactions` table has ≥1,000 recent HDB resale records
  - ✅ `blocks` table has ≥500 unique blocks with geocoded lat/lng
  - ✅ Weekly ingestion jobs run automatically every Sunday
  - ✅ Admin can manually trigger ingestion via `/admin/ingestion/trigger`
  - ✅ Ingestion runs logged to `ingestion_runs` with status, rows_processed, errors
  - ✅ All tests pass (unit + integration)
  - ✅ Data quality is validated (no malformed records in DB)

---

## 6. Risks, Trade-offs, and Open Questions

### Major Risks

1. **data.gov.sg API Reliability**
   - **Risk:** API may change schema, deprecate, or become unavailable
   - **Mitigation:** Monitor API for changes; implement schema version checking; have CSV fallback

2. **Geocoding Costs and Accuracy**
   - **Risk:** OneMap may introduce costs or rate limits; geocoding may be inaccurate for some addresses
   - **Mitigation:** Use pre-built geocoding database; validate geocoding accuracy with sample addresses; budget for potential API costs

3. **Initial Ingestion Time**
   - **Risk:** First ingestion may take 1+ hour for 100k+ records, blocking development
   - **Mitigation:** Run initial ingestion as background process; optimize with batch inserts; consider splitting into multiple runs

### Trade-offs

1. **Full Refresh vs Incremental Sync**
   - **Choice:** Full refresh (re-ingest all records) for MVP
   - **Trade-off:** Simpler implementation, higher API usage vs. faster incremental updates
   - **Rationale:** MVP traffic and data volume don't justify incremental complexity; can optimize in Phase 2+

2. **Synchronous vs Asynchronous Manual Triggers**
   - **Choice:** Synchronous triggers (wait for ingestion to complete, return result)
   - **Trade-off:** Simpler for admin, may timeout on large datasets vs. asynchronous with status polling
   - **Rationale:** MVP admin usage is manual and infrequent; synchronous is easier to debug; can add async in PR7

3. **OneMap vs Pre-Built Geocoding Database**
   - **Choice:** OneMap API first, fallback to pre-built database
   - **Trade-off:** Real-time geocoding for new blocks vs. upfront effort to build database
   - **Rationale:** OneMap API is free (for low volume); pre-built database requires manual curation but is more reliable

4. **Error Handling: Fail Fast vs Continue on Error**
   - **Choice:** Continue on individual record errors; only fail if API is unreachable
   - **Trade-off:** Partial ingestion completions vs. all-or-nothing reliability
   - **Rationale:** Partial data is better than no data; skip invalid records, log errors, continue

### Open Questions

1. **data.gov.sg API Resource ID and Schema**
   - **Question:** What is the exact resource ID for HDB Resale Prices dataset? Does the API return all historical data or just recent records?
   - **Action:** Test API endpoint before implementation; document resource ID in `.env.example`
   - **Impact:** Wrong resource ID will block ingestion; may need to adjust pagination or date filtering

2. **OneMap API Key Requirement**
   - **Question:** Does OneMap require API key for geocoding? What are the rate limits?
   - **Action:** Test OneMap API; obtain API key if needed; document in `.env.example`
   - **Impact:** If API key required and not obtained, geocoding will fail; fallback to pre-built database

3. **HDB Block Dataset Availability**
   - **Question:** Is there a separate data.gov.sg dataset for HDB block metadata (addresses, lease_commence_year), or should we extract blocks from transactions?
   - **Recommendation:** Extract unique (block, street, town) from transactions for MVP; use separate dataset if available for better metadata
   - **Impact:** Affects `ingest_hdb_blocks()` implementation; may need to adjust data source

4. **Incremental Ingestion Strategy for Future**
   - **Question:** Should we plan for incremental ingestion (delta sync based on `month` field), or is full refresh acceptable long-term?
   - **Recommendation:** Full refresh for MVP; add incremental sync in Phase 2 if API usage becomes costly or ingestion time exceeds 1 hour
   - **Impact:** Affects future optimization roadmap; no impact on PR2 scope

5. **Admin Authentication Method**
   - **Question:** What authentication method should `/admin/ingestion/trigger` use (HTTP Basic, session-based, API key)?
   - **Assumption:** Use HTTP Basic Auth from PR0's `User` model; can upgrade to OAuth2 in PR7
   - **Impact:** Affects endpoint implementation; minor change if authentication method changes

---

## Summary

PR2 establishes the automated data ingestion foundation for ResaleLens SG, enabling weekly refresh of HDB resale transactions and block metadata from data.gov.sg. This PR includes robust error handling (retry logic, partial failure recovery), audit logging (ingestion_runs table), manual admin triggers, and scheduled weekly jobs.

**Key Features:**
- Fetch HDB transaction data from data.gov.sg API with pagination and retry logic
- Geocode HDB blocks using OneMap API with graceful degradation on failures
- Upsert transactions and blocks to database (insert new, update existing)
- Log all ingestion runs with status, rows processed, and error summaries
- Manual admin trigger endpoint for on-demand data refresh
- Scheduled weekly ingestion jobs (Sundays 03:00 and 03:15 SGT)
- Comprehensive testing (unit tests with mocked APIs, integration tests with test DB)

**Risks Addressed:**
- API reliability: Retry logic + error logging
- Geocoding failures: Null lat/lng fallback + pre-built database option
- Data quality: Validation + skip invalid records
- Performance: Batch inserts + manual initial load
- Scheduler conflicts: 15-min delay + max_instances=1

**Next Steps After PR2:**
- PR3: Data Ingestion Pipeline (POIs & MRT) — Populate `pois` table for Block X-Ray amenity distances
- PR4: Fair Value Engine — Use `transactions` data for comp-based pricing calculations
- PR6: Data Status Page — Display ingestion run history and dataset freshness

PR2 is **ready for implementation** after validating data.gov.sg and OneMap API access. 🚀
