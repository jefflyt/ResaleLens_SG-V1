›# PR1.1: Supabase Database Setup for MVP

**Status:** ✅ **DOCUMENTATION COMPLETE** (2026-01-10) | ⏳ **Manual Setup Pending**  
**Branch:** `pr1.1-supabase-database`  
**Date:** 2026-01-10  
**Based on:** PR1 Database Schema completed  
**Type:** Infrastructure / Configuration

## Implementation Summary

All documentation and configuration files have been created:
- ✅ **Setup Guide**: [docs/technical/supabase_setup.md](../technical/supabase_setup.md) - Comprehensive step-by-step guide
- ✅ **README Updated**: Added Supabase quick setup section with commands
- ✅ **Environment Templates**: Improved `.env.example` and created `.env.production`
- ✅ **Git Security**: Added `.env.production` to `.gitignore`
- ✅ **Code Verification**: Confirmed `config.py` and `database.py` already support PostgreSQL

**Pending Manual Steps** (User Action Required):
1. Create Supabase project at https://app.supabase.com (Singapore region)
2. Add `DATABASE_URL` to `.env.local`
3. Run migrations: `uv run alembic upgrade head`
4. Seed database: `uv run python scripts/seed_data.py`
5. Run tests against Supabase: `uv run pytest -v`

**See:** [Supabase Setup Guide](file:///Users/jefflee/Documents/AIProjects/ResaleLens_SG-V1/docs/technical/supabase_setup.md) for complete instructions.

---

## 0) Assumptions

1. **Assumption:** PR1 Database Schema has been completed with all models, migrations, and repositories tested on SQLite
2. **Assumption:** Supabase free tier (500MB database, Singapore region) is sufficient for MVP validation with external customers
3. **Assumption:** The existing Alembic migrations and SQLAlchemy models are cross-database compatible (no SQLite-specific code)

> **📌 Important Note:**  
> After PR1.1 is implemented, **all subsequent PRs (PR2+)** should use Supabase PostgreSQL as the target database for data ingestion, testing, and validation. Local development can continue using SQLite, but production features should be verified against Supabase to ensure external customers have access to real-time data.

---

## 1) Clarifying Questions

**None blocking** — implementation is straightforward configuration change.

---

## 2) Feature Summary

### Goal
Set up Supabase PostgreSQL as the production database for MVP external customer validation, while maintaining SQLite for local development.

### User Story
As a **solo founder**, I want **a production-grade PostgreSQL database in the cloud** so that **external customers can validate my MVP with persistent, reliable data access**.

### Acceptance Criteria

- [ ] Supabase project created in Singapore region
- [ ] PostgreSQL connection string obtained and secured
- [ ] Environment variable configuration supports both SQLite (local) and PostgreSQL (production)
- [ ] All Alembic migrations run successfully on Supabase PostgreSQL
- [ ] Seed data script successfully populates Supabase database
- [ ] All existing tests pass against Supabase PostgreSQL
- [ ] Connection pooling configured for production reliability
- [ ] Database credentials stored securely (not committed to git)
- [ ] Documentation updated with Supabase setup instructions
- [ ] Local development continues to use SQLite seamlessly

### Non-goals (explicit)

- **NOT** implementing database backups (Supabase provides automatic backups)
- **NOT** setting up read replicas (overkill for MVP)
- **NOT** migrating real user data (greenfield deployment)
- **NOT** implementing connection retry logic (handled by SQLAlchemy + Supabase)
- **NOT** changing any model definitions or migration files

---

## 3) Approach Overview

### Proposed UX
No user-facing changes. This is purely backend infrastructure.

### Proposed API
No API changes. Existing FastAPI endpoints work identically with PostgreSQL.

### Proposed Data Changes
- **Schema:** Identical to SQLite (already designed for cross-database compatibility)
- **Connection:** Add PostgreSQL connection string via environment variable
- **Migrations:** Run existing Alembic migrations on Supabase
- **Seed Data:** Populate with existing seed script

### Auth/AuthZ Rules
- Database connection requires Supabase connection string credentials
- Credentials stored in `.env.local` (git-ignored)
- No application-level auth changes

---

## 4) PR Plan

### PR Title
`feat(infra): Add Supabase PostgreSQL for MVP production database`

### Branch Name
`pr1.1-supabase-database`

### Scope (in)

1. **Supabase Project Setup:**
   - Create new Supabase project in Singapore region
   - Obtain PostgreSQL connection string
   - Configure connection pooling settings

2. **Configuration Updates:**
   - Update `.env.example` with Supabase connection string template
   - Add `.env.production` example for production deployment
   - Update `README.md` with Supabase setup instructions
   - Add database connection validation in `database.py`

3. **Migration Execution (Schema Deployment):**
   - Run `alembic upgrade head` on Supabase PostgreSQL
   - **Verify creation of all PR1 schema elements:**
     - **Tables:** `users`, `transactions`, `blocks`, `pois`, `leads`, `ingestion_runs`
     - **Indexes:**
       - `transactions`: (block, street, flat_type, date), (town, flat_type, date), (lat, lng)
       - `blocks`: (block, street), (town)
       - `pois`: (poi_type, lat, lng)
       - `leads`: (created_at, status)
     - **Constraints:**
       - `transactions`: `uq_transaction_details` (composite unique)
       - `blocks`: `uq_block_street` (composite unique)
       - Foreign Keys: `transactions.ingestion_run_id` -> `ingestion_runs.id`
   - Verify schema matches SQLite schema exactly via `alembic history`

4. **Testing:**
   - Run full test suite against Supabase PostgreSQL
   - Verify all repositories work correctly
   - Test migration rollback

5. **Documentation:**
   - Add Supabase setup guide to `docs/technical/`
   - Update `README.md` with environment variable configuration
   - Document local vs production database usage

### Out of Scope (explicit)

- Migration of existing data (greenfield setup)
- Database performance tuning (defer to post-MVP)
- Backup/restore procedures (Supabase provides this)
- Connection pooling configuration changes (use defaults)
- Database monitoring setup (use Supabase dashboard)
- Any model or migration file changes

### Key Changes by Layer

#### Frontend
- **No changes:** Frontend is database-agnostic

#### Backend
- **`src/resalelens/database.py`:**
  - No code changes needed (already uses `DATABASE_URL` from config)
  - Verify connection pooling settings are appropriate for PostgreSQL
  
- **`src/resalelens/config.py`:**
  - No code changes needed (already reads `DATABASE_URL` from env)

#### Data
- **No schema changes:** Existing models already compatible
- **Migration execution:** Run `alembic upgrade head` on Supabase
- **Seed data:** Run `scripts/seed_data.py` against Supabase

#### Infra/Config
- **`.env.example`:** Add Supabase connection string template
- **`.env.production` (new):** Template for production environment variables
- **`.gitignore`:** Ensure `.env.production` is ignored
- **`README.md`:** Add Supabase setup section
- **`docs/technical/supabase_setup.md` (new):** Detailed setup guide

### Edge Cases to Handle

1. **Connection Failures:**
   - SQLAlchemy already handles connection retries
   - Supabase provides automatic failover
   - Document connection string validation

2. **Migration Conflicts:**
   - Verify no SQLite-specific syntax in migrations
   - Test migrations on clean Supabase database
   - Keep migration rollback tested

3. **Seed Data Idempotency:**
   - Seed script should handle existing data gracefully
   - Use upsert logic where appropriate
   - Clear database before seeding if needed

4. **Environment Variable Confusion:**
   - Clear documentation on which env file to use when
   - Validation that correct database is being used
   - Log database URL (masked) on startup

### Migration/Compatibility Notes

- **Backward Compatible:** SQLite development continues unchanged
- **Database Detection:** Application detects database type from `DATABASE_URL`
- **No Breaking Changes:** All existing code works with both databases
- **Migration Path:** Developers switch by changing one environment variable

---

## 5) Testing & Verification

### Automated Tests

#### Unit
- **No new unit tests needed:** Existing model tests run against Supabase
- **Command:** `DATABASE_URL=<supabase_url> uv run pytest tests/test_models.py -v`

#### Integration
- **Repository tests:** Run all repository tests against Supabase
- **Migration tests:** Verify upgrade/downgrade on Supabase
- **Command:** `DATABASE_URL=<supabase_url> uv run pytest tests/test_repositories.py -v`

#### E2E
**Not needed** — database is infrastructure layer only

### Manual Verification Checklist

- [ ] **Supabase Project Created**
  - Navigate to app.supabase.com → Verify project exists in Singapore region
  - Expected: Project dashboard shows "Healthy" status

- [ ] **Connection String Obtained**
  - Copy PostgreSQL connection string from Supabase dashboard
  - Format: `postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres`
  - Expected: Connection string includes Singapore region endpoint

- [ ] **Migration Successful**
  - Run: `DATABASE_URL=<supabase_url> uv run alembic upgrade head`
  - Expected: All migrations apply without errors
  - Verify: Check Supabase Table Editor shows 6 tables

- [ ] **Seed Data Loaded**
  - Run: `DATABASE_URL=<supabase_url> uv run python scripts/seed_data.py`
  - Expected: 258 records created (3 ingestion runs, 15 blocks, 30 POIs, 100 transactions, 10 leads)
  - Verify: Query each table in Supabase SQL Editor

- [ ] **Tests Pass**
  - Run: `DATABASE_URL=<supabase_url> uv run pytest -v`
  - Expected: All 21 tests pass

- [ ] **Local Development Unchanged**
  - Run: `uv run pytest -v` (without DATABASE_URL override)
  - Expected: Tests run against SQLite, all pass

- [ ] **Application Startup**
  - Run: `DATABASE_URL=<supabase_url> uv run uvicorn src.resalelens.main:app --reload`
  - Expected: App starts, logs show PostgreSQL connection
  - Verify: Access `/health` endpoint returns 200 OK

- [ ] **Schema Verification**
  - Compare SQLite and PostgreSQL schemas
  - Run: `DATABASE_URL=<supabase_url> uv run alembic history`
  - Expected: Same migration history as SQLite

- [ ] **Connection Pooling**
  - Check Supabase dashboard → Database → Connection Pooling
  - Expected: Transaction mode enabled, max connections configured

- [ ] **Documentation Updated**
  - Review `README.md` for Supabase setup section
  - Review `docs/technical/supabase_setup.md` for detailed guide
  - Expected: Clear, copy-pasteable instructions

### Commands to Run

#### Setup Supabase Database
```bash
# 1. Set Supabase connection string in .env.local
echo "DATABASE_URL=postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres" >> .env.local

# 2. Run migrations
uv run alembic upgrade head

# 3. Seed database
uv run python scripts/seed_data.py

# 4. Verify tables
# Use Supabase SQL Editor or:
uv run python -c "from resalelens.database import engine; print(engine.table_names())"
```

#### Test Against Supabase
```bash
# Run all tests
uv run pytest -v

# Run specific test suites
uv run pytest tests/test_models.py -v
uv run pytest tests/test_repositories.py -v

# Check migration status
uv run alembic current
uv run alembic history
```

#### Local Development (SQLite)
```bash
# Remove or comment out DATABASE_URL from .env.local
# Or use default SQLite:
uv run uvicorn src.resalelens.main:app --reload
```

#### Verify Database Connection
```bash
# Test PostgreSQL connection
uv run python -c "from resalelens.database import engine; print(engine.url)"
```

---

## 6) Rollback Plan

### If Supabase Setup Fails

1. **Remove Supabase `DATABASE_URL`** from `.env.local`
2. **Revert to SQLite:** Application automatically uses default SQLite database
3. **No code changes needed:** All changes are configuration-only

### If Migration Fails on Supabase

1. **Rollback migration:** `uv run alembic downgrade base`
2. **Fix migration issue** (if SQLite-specific syntax found)
3. **Delete and recreate Supabase project** if needed (data is not critical for greenfield)
4. **Re-run migrations** after fix

### Emergency Rollback

- **Quick rollback:** Remove `DATABASE_URL` from environment
- **Data preservation:** Export data from Supabase SQL Editor before deletion
- **No downtime risk:** Development continues on SQLite unaffected

---

## 7) Follow-ups (optional)

### Phase 2 Enhancements
- **Connection Pooling Tuning:** Optimize pool size based on actual traffic
- **Read Replicas:** Add if read-heavy queries become bottleneck
- **Monitoring:** Set up custom alerts for slow queries, connection errors
- **Backup Automation:** Configure automated backup schedules (beyond Supabase defaults)

### Production Deployment
- **Environment Variables:** Set `DATABASE_URL` in deployment platform (Railway, Render, etc.)
- **SSL Configuration:** Verify SSL is enforced for Supabase connections
- **Connection String Rotation:** Periodic password rotation for security

### Database Optimization
- **Index Analysis:** Use Supabase performance insights to add missing indexes
- **Query Optimization:** Profile slow queries with `EXPLAIN ANALYZE`
- **JSONB Migration:** Convert JSON fields to JSONB for better query performance

---

## Implementation Steps Summary

### Step 1: Create Supabase Project (5 minutes)
1. Sign up at supabase.com (if needed)
2. Create new project: "ResaleLens SG MVP"
3. Select Singapore region
4. Choose free tier
5. Wait for provisioning (2-3 minutes)

### Step 2: Configure Connection (2 minutes)
1. Copy PostgreSQL connection string from Supabase dashboard
2. Add to `.env.local`: `DATABASE_URL=postgresql://...`
3. Verify connection string format

### Step 3: Run Migrations (5 minutes)
1. Run: `uv run alembic upgrade head`
2. Verify success in Supabase Table Editor
3. Check all 6 tables created

### Step 4: Seed Data (2 minutes)
1. Run: `uv run python scripts/seed_data.py`
2. Verify 258 records in Supabase dashboard
3. Spot-check sample data

### Step 5: Test & Verify (10 minutes)
1. Run full test suite against Supabase
2. Test migration rollback
3. Verify local SQLite still works
4. Test application startup

### Step 6: Documentation (15 minutes)
1. Update `.env.example` with Supabase template
2. Add setup guide to `README.md`
3. Create `docs/technical/supabase_setup.md`
4. Document environment variable usage

**Total Estimated Time:** 45 minutes hands-on, plus Supabase provisioning time

---

## Success Metrics

- ✅ Supabase project live in Singapore region
- ✅ All 6 tables created with correct schema
- ✅ 258 seed records populated
- ✅ All 21 tests passing against PostgreSQL
- ✅ Local development unchanged (SQLite works)
- ✅ Connection string secured in git-ignored file
- ✅ Documentation complete and tested

---

## References

- **Supabase Docs:** https://supabase.com/docs/guides/database
- **SQLAlchemy PostgreSQL:** https://docs.sqlalchemy.org/en/20/dialects/postgresql.html
- **PR1 Database Schema:** `docs/plans/PR1_DATABASE_SCHEMA.md`
- **Alembic Migrations:** https://alembic.sqlalchemy.org/
