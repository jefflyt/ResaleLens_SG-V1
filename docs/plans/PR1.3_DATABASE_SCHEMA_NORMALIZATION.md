# PR1.3: Database Schema Normalization & POI Integration

**Status:** 🔵 **PLANNED** (2026-01-11)  
**Branch:** `pr1.3-schema-normalization`  
**Date:** 2026-01-11  
**Based on:** Database Schema Review Analysis

---

## 1. Feature/Epic Summary

### Objective
Normalize the database schema to eliminate data duplication and establish proper relationships between transactions, blocks, and POIs through foreign keys and junction tables. This migration improves data integrity, query performance, and enables efficient Block X-Ray feature implementation.

### User Impact
- **Indirect (Foundation):** Users won't see visible changes, but this enables:
  - Faster Block X-Ray queries with pre-calculated POI distances
  - More reliable data integrity through foreign key constraints
  - Reduced storage footprint (~95% reduction in duplicate location data)
  - Better query performance for Fair Value calculations
- **Developer Impact:** Cleaner data model, easier to maintain, faster queries, and reduced risk of data inconsistencies

### Dependencies
- **Prerequisite:** PR1 (Database Schema) must be completed
  - Requires: `transactions`, `blocks`, and `pois` tables
  - Requires: Repository pattern for data access
- **Prerequisite:** PR2 (Data Ingestion HDB) should be completed
  - Ensures blocks table is populated for foreign key migration
  - Transactions data needed for validation
- **Optional:** PR3 (POI Ingestion) can run before or after PR1.3
  - If before: POI data available for junction table population
  - If after: Junction table populated during PR3 ingestion

### Assumptions
1. **Assumption:** All existing transactions can be matched to blocks via (block, street) string matching
2. **Assumption:** Supabase PostgreSQL supports `ON CONFLICT` for efficient upserts
3. **Assumption:** POI distance calculations use Haversine formula (acceptable accuracy for MVP)
4. **Assumption:** Pre-calculating POI distances during ingestion is acceptable (vs real-time calculation)
5. **Assumption:** Keeping original `block` and `street` columns in transactions for backward compatibility is acceptable during transition period

---

## 2. Complexity & Fit

### Classification
**Multi-PR** — This epic involves schema migrations, data backfills, and repository updates that should be split for safety and testability.

### Rationale
- **Data migration risk:** Adding foreign keys to existing data requires careful validation
- **Multiple layers affected:** Database schema, repositories, ingestion logic
- **Backward compatibility:** Need transition period to update all queries
- **Testing complexity:** Each migration should be independently testable
- **Rollback safety:** Smaller PRs easier to revert if issues arise

### Estimated PRs
3 PRs recommended for safe, incremental migration

---

## 3. Full-Stack Impact

### Frontend
**No changes planned.** This is a backend-only schema optimization.

### Backend
- **Models (`src/resalelens/models.py`):**
  - Add `block_id` foreign key to `Transaction` model
  - Create new `BlockPOI` model for junction table
  - Add relationships: `Transaction.block`, `Block.transactions`, `Block.nearby_pois`, `POI.nearby_blocks`
- **Repositories:**
  - Update `TransactionRepository` to use `block_id` for queries
  - Create `BlockPOIRepository` with proximity query methods
  - Add methods: `get_pois_near_block()`, `get_blocks_near_poi()`, `upsert_block_poi_distances()`
- **Ingestion Modules:**
  - Update `hdb_transactions.py` to populate `block_id` during ingestion
  - Update `hdb_blocks.py` to calculate and populate POI distances
  - Add POI distance calculation utility function

### Data
- **Schema Changes:**
  - Add `block_id` column to `transactions` table (foreign key to `blocks.id`)
  - Create `block_pois` junction table (block_id, poi_id, distance_m)
  - Add indexes: `ix_transactions_block_id`, `ix_block_pois_block_id_distance`, `ix_block_pois_poi_id`
- **Data Migrations:**
  - Backfill `transactions.block_id` by matching on (block, street)
  - Populate `block_pois` with pre-calculated distances for existing blocks and POIs
- **Backward Compatibility:**
  - Keep `block` and `street` columns in transactions (mark as deprecated)
  - Can remove in Phase 2+ after all queries migrated

### Infra / Config
**No infrastructure changes required.** Uses existing database connection and migration tools.

---

## 4. PR Roadmap

### PR 1.3a: Add Foreign Key from Transactions to Blocks

#### Goal
Establish referential integrity between transactions and blocks by adding `block_id` foreign key, eliminating duplicate location data storage.

#### Scope

**In scope:**
- Add `block_id` column to `transactions` table (nullable initially)
- Create Alembic migration to add column and foreign key constraint
- Backfill `block_id` by matching transactions to blocks on (block, street)
- Make `block_id` NOT NULL after backfill
- Add index on `block_id` for query performance
- Update `Transaction` model with `block_id` field and `block` relationship
- Update `Block` model with `transactions` relationship
- Add unit tests for model relationships
- Verify all transactions successfully matched to blocks

**Out of scope:**
- Removing `block`, `street`, `town`, `latitude`, `longitude` columns from transactions (deferred to Phase 2+)
- Updating repository queries to use `block_id` (deferred to PR 1.3c)
- POI integration (deferred to PR 1.3b)

#### Backend Changes

**Models (`src/resalelens/models.py`):**

Update `Transaction` model:
- Add field: `block_id: Mapped[int | None] = mapped_column(ForeignKey("blocks.id"), nullable=True)`
- Add relationship: `block: Mapped["Block"] = relationship("Block", back_populates="transactions")`
- Update `__table_args__` to add index: `Index("ix_transactions_block_id", "block_id")`

Update `Block` model:
- Add relationship: `transactions: Mapped[list["Transaction"]] = relationship("Transaction", back_populates="block")`

**No repository changes in this PR** — Queries continue using string matching for now.

#### Data Changes

**Migration:** `alembic revision --autogenerate -m "add_block_id_to_transactions"`

Migration steps:
1. Add `block_id` column (nullable)
2. Backfill `block_id` using SQL:
   ```sql
   UPDATE transactions t
   SET block_id = b.id
   FROM blocks b
   WHERE t.block = b.block AND t.street = b.street
   ```
3. Verify all transactions matched: `SELECT COUNT(*) FROM transactions WHERE block_id IS NULL`
4. If unmatched transactions exist:
   - Log warning with unmatched (block, street) combinations
   - Create missing blocks or investigate data quality issues
5. Make `block_id` NOT NULL: `ALTER TABLE transactions ALTER COLUMN block_id SET NOT NULL`
6. Add foreign key constraint: `ALTER TABLE transactions ADD CONSTRAINT fk_transactions_block_id FOREIGN KEY (block_id) REFERENCES blocks(id)`
7. Add index: `CREATE INDEX ix_transactions_block_id ON transactions(block_id)`

**Rollback strategy:**
- Migration downgrade drops `block_id` column and constraint
- Original `block` and `street` columns preserved

#### Infra / Config
**No changes required.**

#### Testing

**Unit Tests (`tests/test_models.py`):**
- Test `Transaction.block` relationship loads correctly
- Test `Block.transactions` relationship returns all transactions for block
- Test foreign key constraint prevents orphaned transactions
- Test cascade behavior (if block deleted, what happens to transactions?)

**Integration Tests (`tests/integration/test_transaction_block_migration.py`):**
- Create test blocks and transactions
- Run migration (upgrade)
- Verify all transactions have `block_id` populated
- Verify foreign key constraint enforced
- Test migration rollback (downgrade)
- Verify `block_id` column removed after downgrade

**Data Quality Tests:**
- Query for unmatched transactions: `SELECT DISTINCT block, street FROM transactions WHERE block_id IS NULL`
- Verify count: `SELECT COUNT(*) FROM transactions WHERE block_id IS NOT NULL` matches total transaction count

#### Verification

**Commands:**

Install dependencies:
```
uv sync
```

Create migration:
```
uv run alembic revision --autogenerate -m "add_block_id_to_transactions"
```

Review migration file:
```
cat src/resalelens/migrations/versions/<migration_id>_add_block_id_to_transactions.py
```

Run migration:
```
uv run alembic upgrade head
```

Verify schema:
```
uv run python -c "
from src.resalelens.database import SessionLocal
from sqlalchemy import inspect
db = SessionLocal()
inspector = inspect(db.bind)
columns = inspector.get_columns('transactions')
for col in columns:
    if col['name'] == 'block_id':
        print(f'block_id column: {col}')
fks = inspector.get_foreign_keys('transactions')
print(f'Foreign keys: {fks}')
db.close()
"
```

Verify backfill:
```
uv run python -c "
from src.resalelens.database import SessionLocal
from src.resalelens.models import Transaction
db = SessionLocal()
total = db.query(Transaction).count()
matched = db.query(Transaction).filter(Transaction.block_id.isnot(None)).count()
print(f'Total transactions: {total}')
print(f'Matched to blocks: {matched}')
print(f'Unmatched: {total - matched}')
db.close()
"
```

Run tests:
```
uv run pytest tests/test_models.py tests/integration/test_transaction_block_migration.py -v
```

Lint and typecheck:
```
uv run ruff check .
uv run mypy src/
```

**Manual Verification Checklist:**
1. ✅ Migration creates `block_id` column
2. ✅ All transactions have `block_id` populated (no NULLs)
3. ✅ Foreign key constraint exists: `fk_transactions_block_id`
4. ✅ Index exists: `ix_transactions_block_id`
5. ✅ `Transaction.block` relationship works (test in Python REPL)
6. ✅ `Block.transactions` relationship works
7. ✅ Original `block` and `street` columns still exist (backward compatibility)
8. ✅ All tests pass
9. ✅ Migration rollback works (downgrade and verify column removed)

#### Rollback Plan

**Feature Flag:** Not applicable (schema change).

**Revert Strategy:**
- Run `alembic downgrade -1` to remove `block_id` column
- Original `block` and `street` columns preserved, so no data loss
- All existing queries continue working (no code changes in this PR)
- Safe to revert at any time before PR 1.3c (repository updates)

#### Dependencies

**Prerequisite PRs:**
- ✅ PR1 (Database Schema) — Provides `transactions` and `blocks` tables
- ✅ PR2 (Data Ingestion HDB) — Ensures blocks table populated for matching

**External Dependencies:** None

#### Risks & Mitigations

**Risk 1: Unmatched Transactions**
- **Risk:** Some transactions may not match any block due to data inconsistencies (typos, missing blocks)
- **Mitigation:**
  - Run data quality check before migration: identify unmatched (block, street) combinations
  - Create missing blocks automatically or manually before migration
  - Log all unmatched transactions for investigation
  - Migration fails if any transactions remain unmatched (prevents data integrity issues)

**Risk 2: Migration Performance**
- **Risk:** Backfilling 200k+ transactions may take several minutes
- **Mitigation:**
  - Use single SQL UPDATE statement (fast in PostgreSQL)
  - Run migration during low-traffic window
  - Test migration on copy of production database first
  - Monitor migration progress with logging

**Risk 3: Foreign Key Constraint Violations**
- **Risk:** If blocks are deleted after migration, transactions become orphaned
- **Mitigation:**
  - Set foreign key `ON DELETE RESTRICT` (default) to prevent block deletion if transactions exist
  - Or use `ON DELETE CASCADE` to delete transactions when block deleted (not recommended for MVP)
  - Document block deletion policy: blocks should never be deleted, only marked inactive

---

### PR 1.3b: Create Block-POI Junction Table

#### Goal
Enable efficient proximity queries between blocks and POIs by creating a junction table with pre-calculated distances.

#### Scope

**In scope:**
- Create `block_pois` junction table with columns: `id`, `block_id`, `poi_id`, `distance_m`, `created_at`
- Add foreign key constraints to `blocks` and `pois` tables
- Add indexes for efficient queries: `(block_id, distance_m)`, `(poi_id)`
- Add unique constraint: `(block_id, poi_id)`
- Create `BlockPOI` model with relationships to `Block` and `POI`
- Create `BlockPOIRepository` with methods: `get_pois_near_block()`, `get_blocks_near_poi()`, `upsert_distances()`
- Add utility function: `calculate_haversine_distance(lat1, lng1, lat2, lng2)` for distance calculations
- Populate junction table with distances for all existing blocks and POIs
- Unit tests for model and repository
- Integration tests for distance calculations

**Out of scope:**
- Updating Block X-Ray feature to use junction table (deferred to PR6 updates)
- Real-time POI distance calculations (use pre-calculated values)
- Advanced spatial queries (PostGIS) — deferred to Phase 2+

#### Backend Changes

**Models (`src/resalelens/models.py`):**

Create new `BlockPOI` model:
```
class BlockPOI(Base):
    __tablename__ = "block_pois"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    block_id: Mapped[int] = mapped_column(ForeignKey("blocks.id"), nullable=False)
    poi_id: Mapped[int] = mapped_column(ForeignKey("pois.id"), nullable=False)
    distance_m: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    block: Mapped["Block"] = relationship("Block", back_populates="nearby_pois")
    poi: Mapped["POI"] = relationship("POI", back_populates="nearby_blocks")
    
    __table_args__ = (
        UniqueConstraint("block_id", "poi_id", name="uq_block_poi"),
        Index("ix_block_pois_block_id_distance", "block_id", "distance_m"),
        Index("ix_block_pois_poi_id", "poi_id"),
        CheckConstraint("distance_m >= 0", name="check_distance_positive"),
    )
```

Update `Block` model:
- Add relationship: `nearby_pois: Mapped[list["BlockPOI"]] = relationship("BlockPOI", back_populates="block")`

Update `POI` model:
- Add relationship: `nearby_blocks: Mapped[list["BlockPOI"]] = relationship("BlockPOI", back_populates="poi")`

**Repositories (`src/resalelens/data/repositories.py`):**

Create `BlockPOIRepository`:
```
class BlockPOIRepository(BaseRepository[BlockPOI]):
    def get_pois_near_block(
        self, block_id: int, max_distance_m: float = 1000, poi_type: str | None = None
    ) -> list[BlockPOI]:
        # Return POIs within max_distance_m of block, optionally filtered by poi_type
        # Ordered by distance ascending
    
    def get_blocks_near_poi(
        self, poi_id: int, max_distance_m: float = 1000
    ) -> list[BlockPOI]:
        # Return blocks within max_distance_m of POI
        # Ordered by distance ascending
    
    def upsert_distances(self, block_id: int, poi_distances: list[dict]) -> int:
        # Bulk upsert distances for a block
        # poi_distances format: [{"poi_id": 1, "distance_m": 450}, ...]
        # Returns count of records inserted/updated
```

**Utilities (`src/resalelens/utils/geo.py`):**

Create new utility module:
```
def calculate_haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    # Calculate distance in meters using Haversine formula
    # Returns distance as float (meters)
```

#### Data Changes

**Migration:** `alembic revision --autogenerate -m "create_block_pois_junction_table"`

Migration steps:
1. Create `block_pois` table with all columns and constraints
2. Populate junction table with distances:
   ```sql
   -- For each block, calculate distance to all POIs
   -- Insert into block_pois where distance <= 2000m (2km radius)
   -- Use Haversine formula or PostGIS if available
   ```
3. Verify population: `SELECT COUNT(*) FROM block_pois`

**Data Population Strategy:**
- Calculate distances for all block-POI pairs where distance <= 2km
- Estimated records: 15,000 blocks × 30 POIs × 0.1 (within 2km) = ~45,000 records
- Use batch inserts for performance (1000 records per transaction)

**Rollback strategy:**
- Migration downgrade drops `block_pois` table
- No impact on existing `blocks` or `pois` tables

#### Infra / Config
**No changes required.**

#### Testing

**Unit Tests (`tests/test_models.py`):**
- Test `BlockPOI` model creation
- Test `Block.nearby_pois` relationship
- Test `POI.nearby_blocks` relationship
- Test unique constraint on (block_id, poi_id)
- Test distance validation (must be >= 0)

**Unit Tests (`tests/test_repositories.py`):**
- Test `BlockPOIRepository.get_pois_near_block()` with various distances and POI types
- Test `BlockPOIRepository.get_blocks_near_poi()`
- Test `BlockPOIRepository.upsert_distances()` with bulk data

**Unit Tests (`tests/utils/test_geo.py`):**
- Test `calculate_haversine_distance()` with known coordinates
- Verify accuracy against online calculators (e.g., Singapore MRT stations)
- Test edge cases: same location (distance=0), antipodal points

**Integration Tests (`tests/integration/test_block_poi_population.py`):**
- Create test blocks and POIs
- Calculate and insert distances
- Verify distances are accurate (within 1% tolerance)
- Test query performance: `get_pois_near_block()` returns in <50ms

#### Verification

**Commands:**

Create migration:
```
uv run alembic revision --autogenerate -m "create_block_pois_junction_table"
```

Run migration:
```
uv run alembic upgrade head
```

Verify table created:
```
uv run python -c "
from src.resalelens.database import SessionLocal
from sqlalchemy import inspect
db = SessionLocal()
inspector = inspect(db.bind)
tables = inspector.get_table_names()
print('block_pois' in tables)
columns = inspector.get_columns('block_pois')
print(f'Columns: {[c[\"name\"] for c in columns]}')
db.close()
"
```

Verify population:
```
uv run python -c "
from src.resalelens.database import SessionLocal
from src.resalelens.models import BlockPOI
db = SessionLocal()
count = db.query(BlockPOI).count()
print(f'Total block-POI distances: {count}')
# Sample distances
samples = db.query(BlockPOI).limit(5).all()
for bp in samples:
    print(f'Block {bp.block_id} -> POI {bp.poi_id}: {bp.distance_m}m')
db.close()
"
```

Test distance calculation:
```
uv run python -c "
from src.resalelens.utils.geo import calculate_haversine_distance
# Ang Mo Kio MRT to Bishan MRT (known distance ~2.5km)
dist = calculate_haversine_distance(1.3700, 103.8494, 1.3509, 103.8484)
print(f'AMK to Bishan: {dist:.0f}m (expected ~2500m)')
"
```

Run tests:
```
uv run pytest tests/test_models.py tests/test_repositories.py tests/utils/test_geo.py tests/integration/test_block_poi_population.py -v
```

**Manual Verification Checklist:**
1. ✅ `block_pois` table created with all columns
2. ✅ Foreign key constraints exist to `blocks` and `pois`
3. ✅ Indexes created: `ix_block_pois_block_id_distance`, `ix_block_pois_poi_id`
4. ✅ Unique constraint enforced: `uq_block_poi`
5. ✅ Junction table populated with distances (count > 0)
6. ✅ Distance calculations accurate (spot-check 5-10 known locations)
7. ✅ `get_pois_near_block()` returns POIs ordered by distance
8. ✅ Query performance acceptable (<50ms for typical queries)
9. ✅ All tests pass

#### Rollback Plan

**Feature Flag:** Not applicable (schema change).

**Revert Strategy:**
- Run `alembic downgrade -1` to drop `block_pois` table
- No impact on existing features (Block X-Ray not yet using junction table)
- Safe to revert at any time before Block X-Ray updates

#### Dependencies

**Prerequisite PRs:**
- ✅ PR1 (Database Schema) — Provides `blocks` and `pois` tables
- ⚠️ PR2 (Data Ingestion HDB) — Recommended for blocks data
- ⚠️ PR3 (Data Ingestion POIs) — Recommended for POIs data (can populate later if not available)

**External Dependencies:** None

#### Risks & Mitigations

**Risk 1: Distance Calculation Accuracy**
- **Risk:** Haversine formula may not be accurate for very short distances (<100m) or across Earth's curvature
- **Mitigation:**
  - Haversine is sufficient for MVP (accuracy within 0.5% for distances <10km)
  - Can upgrade to PostGIS or Vincenty formula in Phase 2+ if needed
  - Validate calculations against known distances (MRT stations)

**Risk 2: Large Data Volume**
- **Risk:** Junction table may grow large (100k+ records) if all block-POI pairs calculated
- **Mitigation:**
  - Only store distances <= 2km (reasonable walking distance)
  - Estimated 45k records for MVP (manageable)
  - Add pagination to repository queries
  - Monitor table size and add distance threshold if needed

**Risk 3: Stale Distance Data**
- **Risk:** If blocks or POIs are updated (geocoding corrections), distances become stale
- **Mitigation:**
  - Add `updated_at` column to `block_pois` (future enhancement)
  - Recalculate distances during POI/block ingestion updates
  - Document refresh strategy: full recalculation weekly or on-demand

---

### PR 1.3c: Update Repositories to Use Foreign Keys

#### Goal
Refactor repository queries to use `block_id` foreign key instead of string matching, improving query performance and code maintainability.

#### Scope

**In scope:**
- Update `TransactionRepository` methods to use `block_id` for filtering
- Update `BlockRepository` methods to leverage `transactions` relationship
- Add new query methods: `get_transactions_by_block_id()`, `get_block_with_transactions()`
- Update ingestion modules to populate `block_id` during transaction ingestion
- Update tests to use `block_id` in assertions
- Performance benchmarks: compare query times before/after migration

**Out of scope:**
- Removing deprecated `block` and `street` columns from transactions (deferred to Phase 2+)
- Updating Fair Value Engine queries (deferred to PR4 updates)
- Frontend changes (no user-facing impact)

#### Backend Changes

**Repositories (`src/resalelens/data/repositories.py`):**

Update `TransactionRepository`:
```
# OLD: get_by_block_and_date_range(block: str, street: str, start_date, end_date)
# NEW: get_by_block_id_and_date_range(block_id: int, start_date, end_date)

# Add new method:
def get_by_block_id(self, block_id: int) -> list[Transaction]:
    # Return all transactions for a block
    # Uses block_id foreign key (fast index lookup)

# Update existing method:
def get_within_radius(self, latitude, longitude, radius_km, flat_type, start_date, end_date):
    # Refactor to join blocks table via block_id instead of lat/lng on transactions
```

Update `BlockRepository`:
```
# Add new method:
def get_with_transactions(self, block_id: int) -> Block:
    # Eager load transactions relationship
    # Uses joinedload for single query

# Add new method:
def get_transaction_count(self, block_id: int) -> int:
    # Return count of transactions for block
    # Efficient COUNT query using block_id
```

**Ingestion Modules (`src/resalelens/ingestion/hdb_transactions.py`):**

Update `ingest_hdb_transactions()`:
```
# Before inserting transaction:
# 1. Look up block by (block, street) to get block_id
# 2. Set transaction.block_id = block.id
# 3. Insert transaction with block_id populated

# Handle missing blocks:
# - If block not found, create block first (or log error and skip transaction)
```

#### Data Changes

**No schema changes.** This PR only updates application code.

#### Infra / Config
**No changes required.**

#### Testing

**Unit Tests (`tests/test_repositories.py`):**
- Test `TransactionRepository.get_by_block_id()` returns correct transactions
- Test `TransactionRepository.get_by_block_id_and_date_range()` filters correctly
- Test `BlockRepository.get_with_transactions()` eager loads relationship
- Test `BlockRepository.get_transaction_count()` returns accurate count
- Compare query performance: old string matching vs new foreign key queries

**Integration Tests (`tests/integration/test_repository_migration.py`):**
- Create test blocks and transactions with `block_id` populated
- Run old and new repository methods
- Verify results are identical
- Measure query times (new methods should be 2-5x faster)

**Performance Benchmarks:**
- Query 100 transactions by block using old method (string matching)
- Query 100 transactions by block using new method (foreign key)
- Assert new method is faster (target: <50ms vs <200ms)

#### Verification

**Commands:**

Run tests:
```
uv run pytest tests/test_repositories.py tests/integration/test_repository_migration.py -v
```

Performance benchmark:
```
uv run python scripts/benchmark_repository_queries.py
```

Verify ingestion populates block_id:
```
# Trigger test ingestion
curl -X POST http://localhost:8000/admin/ingestion/trigger?dataset=hdb_transactions

# Check that new transactions have block_id
uv run python -c "
from src.resalelens.database import SessionLocal
from src.resalelens.models import Transaction
db = SessionLocal()
recent = db.query(Transaction).order_by(Transaction.created_at.desc()).limit(10).all()
for t in recent:
    print(f'Transaction {t.id}: block_id={t.block_id}')
db.close()
"
```

**Manual Verification Checklist:**
1. ✅ `TransactionRepository.get_by_block_id()` works correctly
2. ✅ `BlockRepository.get_with_transactions()` eager loads transactions
3. ✅ Query performance improved (measure with benchmarks)
4. ✅ Ingestion modules populate `block_id` for new transactions
5. ✅ All tests pass
6. ✅ No regressions in existing features (Fair Value, Block X-Ray)

#### Rollback Plan

**Feature Flag:** Not applicable (code changes only).

**Revert Strategy:**
- Revert code changes to use old repository methods
- No schema changes, so safe to revert at any time
- Original `block` and `street` columns still available as fallback

#### Dependencies

**Prerequisite PRs:**
- ✅ PR 1.3a (Add Foreign Key) — Provides `block_id` column
- ⚠️ PR 1.3b (Junction Table) — Optional, can run independently

**External Dependencies:** None

#### Risks & Mitigations

**Risk 1: Query Regressions**
- **Risk:** New queries may have bugs or return different results than old queries
- **Mitigation:**
  - Comprehensive integration tests comparing old vs new results
  - Run both old and new queries in parallel during transition period
  - Monitor production logs for query errors after deployment

**Risk 2: Performance Degradation**
- **Risk:** New queries may be slower if indexes not properly configured
- **Mitigation:**
  - Verify indexes exist on `block_id` (created in PR 1.3a)
  - Run performance benchmarks before deployment
  - Use EXPLAIN ANALYZE to verify query plans

---

## 5. Milestones & Sequence

### Milestone 1: Referential Integrity Established (PR 1.3a)
- What it unlocks: Transactions linked to blocks via foreign keys, eliminating duplicate location data
- PRs included: PR 1.3a
- "Done" means:
  - ✅ All transactions have `block_id` populated
  - ✅ Foreign key constraint enforced
  - ✅ Migration tested and reversible
  - ✅ No data loss or integrity issues

### Milestone 2: POI Proximity Data Available (PR 1.3b)
- What it unlocks: Pre-calculated POI distances enable fast Block X-Ray queries
- PRs included: PR 1.3b
- "Done" means:
  - ✅ `block_pois` junction table created and populated
  - ✅ Distance calculations accurate (validated against known locations)
  - ✅ Proximity queries return results in <50ms
  - ✅ Repository methods available for Block X-Ray feature

### Milestone 3: Optimized Query Performance (PR 1.3c)
- What it unlocks: Faster queries for Fair Value and Block X-Ray features
- PRs included: PR 1.3c
- "Done" means:
  - ✅ Repository queries use foreign keys instead of string matching
  - ✅ Query performance improved (2-5x faster)
  - ✅ Ingestion modules populate `block_id` automatically
  - ✅ All tests pass with no regressions

---

## 6. Risks, Trade-offs, and Open Questions

### Major Risks

1. **Data Migration Complexity**
   - **Risk:** Backfilling `block_id` may fail if transactions don't match blocks
   - **Mitigation:** Pre-migration data quality check, create missing blocks, fail-safe migration script

2. **Performance Impact During Migration**
   - **Risk:** Large UPDATE statements may lock tables or take too long
   - **Mitigation:** Run migrations during low-traffic window, test on production copy first, use batched updates if needed

3. **Backward Compatibility**
   - **Risk:** Existing queries may break if `block` and `street` columns removed too early
   - **Mitigation:** Keep original columns during transition period, update queries incrementally, remove in Phase 2+

### Trade-offs

1. **Normalization vs Storage**
   - **Choice:** Normalize schema with foreign keys and junction table
   - **Trade-off:** More complex queries (joins required) vs reduced storage and better integrity
   - **Rationale:** Benefits outweigh costs — storage savings, data integrity, and query performance improvements justify added complexity

2. **Pre-calculated vs Real-time POI Distances**
   - **Choice:** Pre-calculate and store distances in junction table
   - **Trade-off:** Stale data if POIs move vs real-time calculation overhead
   - **Rationale:** POIs rarely change location; pre-calculation provides instant queries for Block X-Ray

3. **Keep vs Remove Original Columns**
   - **Choice:** Keep `block`, `street`, `town`, `latitude`, `longitude` in transactions table
   - **Trade-off:** Storage overhead vs backward compatibility and safety net
   - **Rationale:** Transition period needed; can remove in Phase 2+ after all queries migrated

### Open Questions

1. **POI Distance Threshold**
   - **Question:** What maximum distance should we store in `block_pois` table (1km, 2km, 5km)?
   - **Impact:** Affects table size and query results
   - **Recommendation:** Start with 2km (reasonable walking distance); adjust based on user feedback

2. **Foreign Key Cascade Behavior**
   - **Question:** Should deleting a block cascade delete transactions, or restrict deletion?
   - **Recommendation:** Use `ON DELETE RESTRICT` to prevent accidental data loss; blocks should never be deleted in production

3. **Migration Timing**
   - **Question:** Should PR 1.3 run before or after PR3 (POI Ingestion)?
   - **Recommendation:** PR 1.3a and 1.3c can run anytime after PR2; PR 1.3b should run after PR3 for full POI data

4. **Deprecated Column Removal Timeline**
   - **Question:** When should we remove `block`, `street`, `town`, `latitude`, `longitude` from transactions?
   - **Recommendation:** Phase 2+ (after 3-6 months of production use with no issues)

---

## Summary

PR1.3 normalizes the database schema to eliminate data duplication and establish proper relationships between transactions, blocks, and POIs. This epic is split into 3 incremental PRs for safety and testability:

**PR 1.3a: Add Foreign Key** — Link transactions to blocks via `block_id`, reducing duplicate location data by ~95%

**PR 1.3b: Create Junction Table** — Enable fast POI proximity queries with pre-calculated distances in `block_pois` table

**PR 1.3c: Update Repositories** — Refactor queries to use foreign keys for 2-5x performance improvement

**Key Benefits:**
- ✅ Data integrity through foreign key constraints
- ✅ 95% reduction in duplicate location data
- ✅ 2-5x faster queries for Fair Value and Block X-Ray
- ✅ Pre-calculated POI distances for instant Block X-Ray results
- ✅ Cleaner, more maintainable data model

**Risks Addressed:**
- Data migration validation and rollback plans
- Performance testing and benchmarks
- Backward compatibility during transition period
- Comprehensive testing at each stage

**Next Steps After PR1.3:**
- PR4: Fair Value Engine can leverage optimized queries
- PR6: Block X-Ray can use `block_pois` junction table for instant proximity results
- Phase 2+: Remove deprecated columns after transition period

This epic is **ready for implementation** after PR1 and PR2 are completed. 🚀
