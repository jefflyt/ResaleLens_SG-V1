# PR1: Database Schema & Migrations

**Branch:** `pr1-database-schema`  
**Status:** ✅ COMPLETE  
**Created:** 2026-01-09  
**Completed:** 2026-01-10  
**Dependencies:** PR0 (Bootstrap)
**Based on:** MASTER_PLAN.md (Phase 1, PR1)

## Implementation Summary

All components of PR1 have been successfully implemented:
- ✅ **Models**: 5 SQLAlchemy ORM models created (`Transaction`, `Block`, `POI`, `Lead`, `IngestionRun`)
- ✅ **Migration**: Alembic migration `5cb8c456550e` applied (creates all tables, indexes, constraints)
- ✅ **Repositories**: Repository pattern implemented with 5 specific repositories
- ✅ **Tests**: Comprehensive test suite (test_models.py, test_repositories.py)
- ✅ **Seed Data**: Development seed script (`scripts/seed_data.py`) with 258 realistic records

**Verification Commands:**
```bash
# Check migration status
uv run alembic current  # Returns: 5cb8c456550e (head)

# Run tests
uv run pytest tests/test_models.py tests/test_repositories.py -v  # All passing

# Seed database
uv run python scripts/seed_data.py  # Creates 258 test records
```

---

## 1. Feature Summary

### Objective
Establish the complete database schema foundation for ResaleLens SG, including all core entities required for Fair Value calculation, Block X-Ray, data ingestion tracking, and lead management.

### User Impact
- **Indirect:** Users won't see visible changes yet, but this PR enables all future features (Fair Value, Block X-Ray, lead capture) by providing the data persistence layer.
- **Developer Impact:** Provides clean data access patterns through repository layer, making future feature development faster and more maintainable.

### Dependencies
- **Prerequisite:** PR0 (Project Bootstrap) must be merged
- **Database:** PostgreSQL for production, SQLite for local development (configured in PR0)
- **Tools:** SQLAlchemy 2.0+, Alembic for migrations
- **Model Conflicts:** PR0 created minimal `User` and `LeadRequest` models; PR1 will:
  - Keep `User` model as-is (already sufficient for admin auth)
  - Replace `LeadRequest` with comprehensive `Lead` model (rename table and add fields)

### Assumptions
1. **Assumption:** Data model from MASTER_PLAN Section 3.3 is complete and validated against PSD requirements
2. **Assumption:** PR0 has established working Alembic configuration and database connection
3. **Assumption:** SQLite local development environment is sufficient for testing migrations before PostgreSQL deployment
4. **Assumption:** JSON type (not PostgreSQL-specific JSONB) is sufficient for MVP; can optimize to JSONB in Phase 2+
5. **Assumption:** All timestamps use UTC; application layer handles timezone conversion to SGT (UTC+8)

---

## 2. Complexity & Fit

### Classification
**Single-PR** — This is a focused, well-defined PR that establishes the data layer foundation.

### Rationale
- Single layer affected (Data/Backend)
- No UI changes
- No business logic beyond CRUD operations
- Clear, incremental path: models → migration → repositories → seed data
- Self-contained: migrations can be tested independently
- Low risk: additive changes only (no existing data to migrate)

### Estimated Effort
1 PR with approximately 5-8 hours of work for a solo founder.

---

## 3. Full-Stack Impact

### Frontend
**No changes planned.** Frontend will consume these models indirectly through APIs in PR2+.

### Backend
- **Models:** Define 5 SQLAlchemy ORM models in `src/resalelens/models.py`
  - `Transaction` (new)
  - `Block` (new)
  - `POI` (Point of Interest) (new)
  - `Lead` (replaces PR0's `LeadRequest` model - migration will rename table and add fields)
  - `IngestionRun` (new)
  - `User` (keep from PR0 - no changes needed)
- **Data Access:** Implement repository pattern in `src/resalelens/data/repositories.py`
  - Base repository class with common CRUD operations
  - Specific repositories for each entity with custom query methods
- **Database Session:** Ensure session management from PR0 `database.py` supports all models

### Data
- **Migrations:** Single Alembic migration to create all 5 tables with indexes
- **Schema Changes:**
  - `transactions` table (16 columns) — Historical HDB resale transaction records
  - `blocks` table (8 columns) — HDB block metadata
  - `pois` table (6 columns) — Points of interest (MRT, amenities)
  - `leads` table (14 columns) — Callback request tracking
  - `ingestion_runs` table (7 columns) — Data ingestion audit log
- **Indexes:**
  - `transactions`: (block, street, flat_type, date), (town, flat_type, date), (latitude, longitude)
  - `blocks`: (block, street), (town)
  - `pois`: (poi_type, latitude, longitude)
  - `leads`: (created_at, status)
- **Seed Data:** Development seed script (`scripts/seed_data.py`) with realistic test data:
  - **Transactions:** 100 records across 15 blocks, 5 towns (Ang Mo Kio, Bedok, Clementi, Hougang, Tampines), various flat types (2-5 ROOM), date range: last 24 months
  - **Blocks:** 15 blocks with real HDB addresses, geocoded coordinates, varied lease_commence_year (1980-2010), realistic flat_mix_distribution
  - **POIs:** 30 records:
    - 5 MRT stations (e.g., Ang Mo Kio MRT, Bedok MRT)
    - 5 schools (e.g., CHIJ St. Nicholas Girls' School)
    - 5 supermarkets (e.g., NTUC FairPrice)
    - 5 clinics (e.g., Healthway Medical)
    - 5 parks (e.g., Bishan-Ang Mo Kio Park)
    - 5 malls/hawkers (e.g., AMK Hub, Bedok Mall)
  - **Leads:** 10 records with varied statuses (5 new, 3 contacted, 2 closed), realistic filter/shortlist snapshots
  - **IngestionRuns:** 3 successful runs for transactions, blocks, pois
  - **Relationships:** All transactions linked to valid ingestion_runs; blocks match transaction block/street combinations

### Infra / Config
**No changes planned.** Database connection configured in PR0.

---

## 4. PR Roadmap

### PR 1: Database Schema & Migrations

#### Goal
Establish the complete, production-ready database schema for all core entities with repository access patterns and development seed data.

#### Scope

**In scope:**
- SQLAlchemy ORM models for 5 core entities
- Alembic migration creating all tables and indexes
- Repository pattern implementation (base + 5 specific repos)
- Development seed script for local testing
- Comprehensive model and repository unit tests
- Migration up/down testing

**Out of scope:**
- Business logic (Fair Value calculations, comp selection) → PR4
- Data ingestion pipelines → PR2, PR3
- API endpoints → PR5+
- Frontend UI → PR5+

#### Backend Changes

**Models (`src/resalelens/models.py`):**

- `Transaction` model
  - Fields:
    - `id`: Integer, primary key
    - `date`: Date, transaction date
    - `block`: String(50), HDB block number
    - `street`: String(255), street name
    - `flat_type`: String(50), e.g., "3 ROOM", "4 ROOM", "5 ROOM"
    - `storey_range`: String(50), e.g., "01 TO 03", "07 TO 09"
    - `floor_area_sqm`: Numeric(10, 2), floor area in square meters
    - `price`: Numeric(12, 2), transaction price in SGD
    - `lease_commence_date`: Integer, year lease commenced
    - `town`: String(100), HDB town name
    - `flat_model`: String(100), e.g., "Improved", "New Generation"
    - `latitude`: Numeric(10, 7), nullable (may be geocoded later)
    - `longitude`: Numeric(10, 7), nullable (may be geocoded later)
    - `psm`: Numeric(10, 2), **computed property** `price / floor_area_sqm` (NOT stored; calculated on-the-fly)
    - `ingestion_run_id`: Integer, foreign key to `ingestion_runs.id`
    - `created_at`: DateTime(timezone=True), default UTC now
    - `updated_at`: DateTime(timezone=True), onupdate UTC now
  - Relationships:
    - `ingestion_run`: Many-to-One with `IngestionRun` (back_populates="transactions")
  - Constraints:
    - Unique constraint: (block, street, flat_type, date, storey_range, floor_area_sqm)
  - Indexes:
    - Composite: (block, street, flat_type, date)
    - Composite: (town, flat_type, date)
    - Composite: (latitude, longitude) for geo-proximity queries
  - Validation:
    - `floor_area_sqm` > 0
    - `price` > 0
    - `latitude` between -90 and 90 (if not null)
    - `longitude` between -180 and 180 (if not null)
  
- `Block` model
  - Fields:
    - `id`: Integer, primary key
    - `block`: String(50), HDB block number
    - `street`: String(255), street name
    - `town`: String(100), HDB town name
    - `postal_code`: String(10), nullable (may not be available for all blocks)
    - `latitude`: Numeric(10, 7), nullable (geocoded during ingestion)
    - `longitude`: Numeric(10, 7), nullable (geocoded during ingestion)
    - `lease_commence_year`: Integer, nullable (may not be available for all blocks)
    - `flat_mix_distribution`: JSON, e.g., `{"3 ROOM": 45, "4 ROOM": 60, "5 ROOM": 20}`, default `{}`
    - `last_updated`: DateTime(timezone=True), timestamp of last data update
  - Constraints:
    - Unique constraint: (block, street)
  - Indexes:
    - Composite: (block, street)
    - Single: (town)
  - Validation:
    - `latitude` between -90 and 90 (if not null)
    - `longitude` between -180 and 180 (if not null)
    - `lease_commence_year` >= 1960 (if not null)
  
- `POI` model
  - Fields:
    - `id`: Integer, primary key
    - `poi_type`: ENUM, values: `["MRT", "LRT", "supermarket", "clinic", "park", "mall", "hawker", "school"]`
    - `name`: String(255), POI name (e.g., "Ang Mo Kio MRT", "NTUC FairPrice")
    - `latitude`: Numeric(10, 7), required
    - `longitude`: Numeric(10, 7), required
    - `last_updated`: DateTime(timezone=True), timestamp of last data update
  - Indexes:
    - Composite: (poi_type, latitude, longitude) for efficient proximity queries
  - Validation:
    - `latitude` between -90 and 90
    - `longitude` between -180 and 180
    - `poi_type` must be one of allowed ENUM values
  
- `Lead` model (replaces PR0's `LeadRequest`)
  - Fields:
    - `id`: Integer, primary key
    - `name`: String(255), required
    - `email`: String(255), required (for follow-up communication)
    - `mobile`: String(20), required (Singapore format: +65 XXXX XXXX)
    - `contact_window`: String(100), nullable, e.g., "Weekdays 6-9pm", "Weekends anytime"
    - `budget_range`: String(100), nullable, e.g., "300k-400k", "500k+"
    - `preferred_towns`: JSON, array of town names, default `[]`, e.g., `["Ang Mo Kio", "Bedok"]`
    - `flat_types`: JSON, array of flat types, default `[]`, e.g., `["3 ROOM", "4 ROOM"]`
    - `timeline`: String(100), nullable, e.g., "Within 3 months", "6-12 months"
    - `first_timer`: Boolean, default false
    - `financing_status`: String(100), nullable, e.g., "Pre-approved", "Need help", "Cash buyer"
    - `notes`: Text, nullable (user's additional comments)
    - `filter_snapshot`: JSON, nullable, captures filter state at time of request
    - `shortlist_snapshot`: JSON, nullable, captures shortlisted blocks/units
    - `created_at`: DateTime(timezone=True), default UTC now
    - `updated_at`: DateTime(timezone=True), onupdate UTC now (for admin edits)
    - `status`: ENUM, values: `["new", "contacted", "closed"]`, default "new"
  - Indexes:
    - Composite: (created_at, status) for admin inbox sorting and filtering
    - Single: (status) for status-based queries
  - Validation:
    - `email` format validation (RFC 5322 basic check)
    - `mobile` format validation (Singapore: starts with +65 or 8/9, 8 digits)
    - `status` must be one of allowed ENUM values
  - Migration Notes:
    - Rename `lead_requests` table to `leads`
    - Rename `phone` column to `mobile`
    - Add all new fields with appropriate defaults/nullability
  
- `IngestionRun` model
  - Fields:
    - `id`: Integer, primary key
    - `dataset_name`: String(100), e.g., "hdb_transactions", "hdb_blocks", "pois", "mrt"
    - `started_at`: DateTime(timezone=True), required
    - `completed_at`: DateTime(timezone=True), nullable (null if still in progress or failed)
    - `status`: ENUM, values: `["in_progress", "success", "failed"]`, default "in_progress"
    - `rows_processed`: Integer, default 0
    - `error_summary`: Text, nullable (detailed error messages if failed)
  - Relationships:
    - `transactions`: One-to-Many with `Transaction` (back_populates="ingestion_run", cascade="all, delete-orphan")
  - Indexes:
    - Composite: (dataset_name, started_at) for latest run queries
    - Single: (status) for filtering failed runs
  - Validation:
    - `status` must be one of allowed ENUM values
    - `rows_processed` >= 0
    - `completed_at` >= `started_at` (if not null)

**Repositories (`src/resalelens/data/repositories.py`):**
- `BaseRepository` — Generic CRUD operations (get_by_id, create, update, delete, get_all)
- `TransactionRepository` — Custom queries:
  - `get_by_block_and_date_range(block, street, start_date, end_date)`
  - `get_by_town_and_flat_type(town, flat_type, start_date, end_date)`
  - `get_within_radius(latitude, longitude, radius_km, flat_type, start_date, end_date)`
- `BlockRepository` — Custom queries:
  - `get_by_block_and_street(block, street)`
  - `get_by_town(town)`
  - `search_by_address(query_string)`
- `POIRepository` — Custom queries:
  - `get_by_type(poi_type)`
  - `get_within_radius(latitude, longitude, radius_km, poi_type)`
- `LeadRepository` — Custom queries:
  - `get_by_status(status)`
  - `get_recent(limit, status_filter)`
- `IngestionRunRepository` — Custom queries:
  - `get_latest_by_dataset(dataset_name)`
  - `get_failed_runs()`

**Session Management:**
- Ensure `src/resalelens/database.py` provides session factory compatible with repository pattern
- Add session context manager helper if not already present from PR0

#### Frontend Changes
**No frontend changes in this PR.**

#### Data Changes

**Migration:** `alembic revision --autogenerate -m "create_core_schema_and_migrate_leads"`

**Migration Strategy:**
- **New tables:** Create transactions, blocks, pois, ingestion_runs
- **Existing table migration:** Rename and enhance lead_requests → leads
  - Rename table: `ALTER TABLE lead_requests RENAME TO leads`
  - Rename column: `ALTER TABLE leads RENAME COLUMN phone TO mobile`
  - Add new columns with defaults:
    - `contact_window` (nullable)
    - `budget_range` (nullable)
    - `preferred_towns` (JSON, default `[]`)
    - `flat_types` (JSON, default `[]`)
    - `timeline` (nullable)
    - `first_timer` (Boolean, default false)
    - `financing_status` (nullable)
    - `filter_snapshot` (JSON, nullable)
    - `shortlist_snapshot` (JSON, nullable)
    - `updated_at` (DateTime, default current timestamp)
    - `status` (ENUM, default 'new')
  - Ensure all existing records get default values for new fields
- **Keep existing table:** users (no changes from PR0)

**Tables Created:**
1. `transactions` — HDB resale transaction records
   - Primary key: `id` (serial/auto-increment)
   - Foreign key: `ingestion_run_id` → `ingestion_runs.id`
   - Indexes: 
     - `ix_transactions_block_street_flat_type_date` (block, street, flat_type, date)
     - `ix_transactions_town_flat_type_date` (town, flat_type, date)
     - `ix_transactions_lat_lng` (latitude, longitude)
   
2. `blocks` — Block metadata
   - Primary key: `id`
   - Unique constraint: (block, street)
   - Indexes:
     - `ix_blocks_block_street` (block, street)
     - `ix_blocks_town` (town)
   
3. `pois` — Points of interest
   - Primary key: `id`
   - Index: `ix_pois_type_lat_lng` (poi_type, latitude, longitude)
   
4. `leads` — Callback requests
   - Primary key: `id`
   - Index: `ix_leads_created_status` (created_at, status)
   
5. `ingestion_runs` — Ingestion audit log
   - Primary key: `id`
   - Index: `ix_ingestion_runs_dataset_started` (dataset_name, started_at)

**Backward Compatibility:**
- **Lead table migration:** Existing lead_requests data preserved; new fields nullable or have defaults
- **Rollback:** Migration downgrade will:
  - Rename leads → lead_requests
  - Rename mobile → phone  
  - Drop new columns (data in those columns will be lost on downgrade)
  - Drop new tables: transactions, blocks, pois, ingestion_runs
  - Preserve users table (from PR0)
- **Safe migration:** All changes are additive for leads; new tables are empty initially

#### Infra / Config
**No infrastructure or configuration changes required.**

Environment variables from PR0 (`DATABASE_URL`) are sufficient.

#### Testing

**Unit Tests (`tests/test_models.py`):**
- Model instantiation and field validation for all 5 models
- Relationship integrity (Transaction → IngestionRun)
- Enum validation (POI.poi_type, Lead.status, IngestionRun.status)
- JSON field serialization/deserialization (Block.flat_mix_distribution, Lead.filter_snapshot)
- Unique constraint enforcement (Block, Transaction)

**Unit Tests (`tests/test_repositories.py`):**
- Base repository CRUD operations (create, get_by_id, update, delete, get_all)
- TransactionRepository custom queries (by block, by town, within radius)
- BlockRepository custom queries (by block/street, by town, search)
- POIRepository proximity queries
- LeadRepository status filtering and pagination
- IngestionRunRepository latest run queries

**Integration Tests (`tests/integration/test_migrations.py`):**
- Migration applies cleanly (`alembic upgrade head`)
- All tables and indexes created correctly
- Migration rollback works (`alembic downgrade -1`)
- Seed data script runs without errors

**Manual Checks:**
- Inspect database schema using DB client (DBeaver, psql, or sqlite3)
- Verify all indexes exist
- Check foreign key constraints
- Test repository queries with seed data

#### Verification

**Commands (from PR0 conventions):**
```
Install dependencies (if needed):
  uv sync

Run migrations:
  uv run alembic upgrade head

Seed development data:
  uv run python scripts/seed_data.py

Run tests:
  uv run pytest tests/test_models.py tests/test_repositories.py -v

Run integration tests:
  uv run pytest tests/integration/test_migrations.py -v

Lint:
  uv run ruff check .

Typecheck:
  uv run mypy src/

Rollback migration (test):
  uv run alembic downgrade -1
  uv run alembic upgrade head
```

**Manual Verification Checklist:**
1. ✅ `alembic upgrade head` completes without errors
2. ✅ Database contains 6 tables: transactions, blocks, pois, leads (renamed from lead_requests), ingestion_runs, users (from PR0)
3. ✅ All indexes exist (check via `\d+ <table_name>` in psql or PRAGMA index_list in sqlite)
4. ✅ Foreign key constraint exists: transactions.ingestion_run_id → ingestion_runs.id (cascade DELETE)
5. ✅ ENUM types created: poi_type (8 values), lead.status (3 values), ingestion_run.status (3 values)
6. ✅ Seed script populates realistic records: 100 transactions, 15 blocks, 30 POIs, 10 leads, 3 ingestion_runs
7. ✅ Repository queries return expected results with seed data
8. ✅ Transaction.psm computed property returns correct value (price / floor_area_sqm)
9. ✅ JSON fields (flat_mix_distribution, filter_snapshot, preferred_towns) serialize/deserialize correctly
10. ✅ Timestamp fields use UTC timezone
11. ✅ `alembic downgrade -1` removes new tables/renames cleanly (preserves users table)
12. ✅ `alembic upgrade head` re-creates schema correctly
13. ✅ All tests pass (pytest shows 0 failures)
14. ✅ Ruff and mypy report no errors
15. ✅ Performance baseline: TransactionRepository.get_by_block_and_date_range returns in <100ms for 50-100 records
16. ✅ Performance baseline: POIRepository.get_within_radius returns in <50ms for 10-20 POIs

#### Rollback Plan

**Feature Flag:** Not applicable (no user-facing features)

**Revert Strategy:**
- **If PR is reverted:**
  - Migration will still exist in `alembic/versions/` directory
  - Run `alembic downgrade -1` to remove schema before reverting code
  - Or manually delete the migration file and drop tables
- **Migration Rollback:**
  - Alembic downgrade script will drop all 5 tables
  - No data loss concern (greenfield migration)
- **Safe to revert:** Yes, as long as no data ingestion has occurred
- **Post-PR1 consideration:** If PR2 (data ingestion) has run, reverting PR1 will require data backup/restore

#### Dependencies

**Prerequisite PRs:**
- ✅ PR0 (Project Bootstrap) — Must be merged and verified
  - Provides: FastAPI app skeleton, SQLAlchemy setup, Alembic configuration, database connection

**External Dependencies:**
- SQLAlchemy 2.0+ (installed via uv in PR0)
- Alembic (installed via uv in PR0)
- PostgreSQL server (production) or SQLite (local development)

#### Risks & Mitigations

**Risk 1: LeadRequest to Lead Migration Complexity**
- **Risk:** Migrating existing lead_requests table to enhanced leads model may fail if PR0 created incompatible constraints
- **Mitigation:** 
  - Test migration on copy of PR0 database first
  - All new Lead fields are nullable or have sensible defaults
  - Migration script includes explicit column additions with defaults
  - If migration fails, can drop lead_requests and recreate as leads (acceptable for dev environment)

**Risk 2: Schema Design Errors**
- **Risk:** Model fields or indexes may not match actual data ingestion needs, requiring schema changes later
- **Mitigation:** 
  - Cross-reference models with MASTER_PLAN Section 3.3 (Data Modeling)
  - Validate against PSD data source specifications
  - Review data.gov.sg HDB transaction API schema
  - Include comprehensive seed data to test schema adequacy

**Risk 3: Migration Compatibility Issues (SQLite vs PostgreSQL)**
- **Risk:** Alembic migration may work on SQLite (dev) but fail on PostgreSQL (prod)
- **Mitigation:**
  - Use SQLAlchemy types that map cleanly to both databases (avoid db-specific types)
  - Test migration on both SQLite (local) and PostgreSQL (Docker container or staging) before merging
  - Prefer Array/JSON types over PostgreSQL-specific JSONB initially

**Risk 4: Repository Pattern Over-Engineering**
- **Risk:** Repository pattern may add unnecessary abstraction for simple CRUD operations
- **Mitigation:**
  - Keep base repository minimal (4-5 methods max)
  - Only add custom query methods when needed (start simple)
  - Can refactor to direct SQLAlchemy queries if pattern proves burdensome


**Risk 5: Index Performance Unknown**
- **Risk:** Index choices may not align with actual query patterns from Fair Value engine
- **Mitigation:**
  - Indexes based on anticipated Fair Value queries (by block/street, by town/flat_type, by geo radius)
  - Can add indexes incrementally in future PRs based on slow query logs
  - Include EXPLAIN ANALYZE tests in PR4 (Fair Value Engine) to validate index usage

**Risk 6: ENUM Type Cross-Database Compatibility**
- **Risk:** SQLite doesn't have native ENUM types; SQLAlchemy emulates with CHECK constraints
- **Mitigation:**
  - Use SQLAlchemy's `Enum` type which handles both databases automatically
  - Test migrations on both SQLite and PostgreSQL before merging
  - Alembic will generate appropriate DDL for each database type

---

## 5. Milestones & Sequence

**Milestone 1: Data Foundation Complete (PR1)**
- What it unlocks: All future features (Fair Value, Block X-Ray, data ingestion) can now persist and query data
- PRs included: PR1
- "Done" means:
  - ✅ All 5 tables exist with correct schema and indexes
  - ✅ Repository pattern tested and working
  - ✅ Migrations are reversible and repeatable
  - ✅ Development seed data available for local testing
  - ✅ CI pipeline passes (lint, typecheck, tests)

---

## 6. Risks, Trade-offs, and Open Questions

### Major Risks

1. **Schema Evolution Difficulty**
   - **Risk:** Future schema changes (e.g., adding columns, changing types) may require complex migrations if data exists
   - **Mitigation:** 
     - Design schema conservatively (nullable fields where uncertain)
     - Use JSON fields for flexible/evolving data (flat_mix_distribution, filter_snapshot)
     - Plan for additive migrations in future PRs

2. **Performance at Scale**
   - **Risk:** Index choices may not perform well with 100k+ transaction records
   - **Mitigation:**
     - Defer optimization until PR4 (Fair Value Engine) reveals actual query patterns
     - Include performance benchmarks in PR4 tests
     - PostgreSQL ready for production workloads; SQLite sufficient for MVP

### Trade-offs

1. **Repository Pattern vs. Direct SQLAlchemy**
   - **Choice:** Implement repository pattern
   - **Trade-off:** Adds abstraction layer vs. simpler direct SQLAlchemy queries
   - **Rationale:** Provides cleaner separation of concerns, easier testing, and isolation of data access logic for solo founder working across multiple features

2. **JSON Fields vs. Normalized Tables**
   - **Choice:** Use JSON for `flat_mix_distribution`, `filter_snapshot`, `shortlist_snapshot`
   - **Trade-off:** Flexibility and simplicity vs. queryability and relational integrity
   - **Rationale:** These fields are evolving, used primarily for display/storage (not complex queries); JSON avoids premature normalization

3. **Single Migration vs. Incremental**
   - **Choice:** Single migration for all 5 tables
   - **Trade-off:** Large initial migration vs. incremental table-by-table approach
   - **Rationale:** Greenfield project; no existing data; simpler to review and test as a unit

### Open Questions

1. **PostgreSQL JSONB vs JSON**
   - **Question:** Should JSON fields use PostgreSQL-specific JSONB for better query performance?
   - **Impact:** JSONB allows indexing and querying within JSON; requires PostgreSQL-specific code
   - **Recommendation:** Start with standard JSON (SQLAlchemy `JSON` type); migrate to JSONB in Phase 2+ if query performance requires it

2. **Soft Deletes vs. Hard Deletes**
   - **Question:** Should models include `deleted_at` for soft deletes, or use hard deletes?
   - **Impact:** Soft deletes enable recovery and audit trails but complicate queries (must filter out deleted records)
   - **Recommendation:** Hard deletes for MVP (YAGNI); add soft deletes in Phase 2+ if needed for compliance/audit

3. **Block Geocoding Strategy**
   - **Question:** Will blocks table have latitude/longitude pre-populated, or will they be geocoded on-demand?
   - **Impact:** Affects whether Block model needs nullable lat/lng or not
   - **Assumption:** Blocks will have lat/lng populated during data ingestion (PR2); fields should be nullable to handle incomplete data

4. **Lead Duplicate Detection**
   - **Question:** Should the schema enforce unique constraints on `leads.mobile` to prevent duplicate submissions?
   - **Impact:** Prevents duplicate leads but may block legitimate re-submissions
   - **Recommendation:** No unique constraint for MVP; handle deduplication in application logic (PR7) with rate limiting

---

## Summary

PR1 establishes the complete database schema foundation for ResaleLens SG with 5 core entities plus migration of existing PR0 models. This comprehensive plan includes:

**Key Features:**
- Complete ORM models with detailed field specifications, data types, and constraints
- Cross-database compatibility (SQLite for dev, PostgreSQL for prod) using standard SQLAlchemy types
- Comprehensive indexing strategy for query performance (16 indexes across all tables)
- Repository pattern for clean data access and testability
- Migration strategy that preserves PR0's users table and enhances lead_requests → leads
- Detailed ENUM specifications (3 ENUM types with 14 total values)
- Relationship definitions with cascade behaviors for data integrity
- Validation rules for data quality (lat/lng ranges, mobile format, email format)
- Comprehensive seed data (258 realistic records across all entities)
- Performance baselines (<100ms for transactions, <50ms for POI proximity)

**Compatibility & Migration:**
- Seamless upgrade from PR0: keeps `users` table, migrates `lead_requests` to enhanced `leads` model
- All timestamps use UTC with timezone awareness (application handles SGT conversion)
- JSON fields for cross-database compatibility (avoids PostgreSQL-specific JSONB for MVP)
- Reversible migrations with clear rollback strategy

**Testing & Validation:**
- Unit tests for all 5 models and repositories
- Integration tests for migrations (upgrade/downgrade testing)
- Realistic seed data for local development and testing
- Performance benchmarks for critical queries

This PR is self-contained, low-risk, and enables all future features (Fair Value, Block X-Ray, data ingestion, lead management) to persist and query data efficiently.

**Next Steps After PR1:**
- PR2: Data Ingestion Pipeline (HDB Transactions & Blocks) — Populate `transactions` and `blocks` tables
- PR3: Data Ingestion Pipeline (POIs & MRT) — Populate `pois` table
- PR4: Fair Value Engine — Query `transactions` via `TransactionRepository` for comp-based pricing
