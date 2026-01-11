# Data Validation & Cleaning Strategy

**Date:** 2026-01-11  
**Status:** ✅ Implemented  
**Related PRs:** PR2 (Data Ingestion HDB)

## Context

The ResaleLens ingestion pipeline processes HDB resale transaction data from data.gov.sg and geocodes block addresses using OneMap API. Data quality and consistency are critical for accurate Fair Value calculations and Block X-Ray features.

## Decision

Implement comprehensive data validation and cleaning at multiple stages of the ingestion pipeline to ensure data quality, handle API inconsistencies, and prevent corrupted data from entering the database.

---

## Implementation

### 1. Field Presence Validation

**Location:** `src/resalelens/ingestion/utils.py::validate_transaction_record()`

**Purpose:** Ensure all required fields are present and non-empty before processing

**Required Fields (10 total):**
- `month` - Transaction date
- `block` - HDB block number
- `street_name` - Street name
- `flat_type` - Flat type (e.g., "3 ROOM", "4 ROOM")
- `storey_range` - Storey range (e.g., "07 TO 09")
- `floor_area_sqm` - Floor area in square meters
- `resale_price` - Transaction price
- `lease_commence_date` - Year lease commenced
- `town` - HDB town name
- `flat_model` - Flat model (e.g., "Improved")

**Validation Logic:**
```python
for field in required_fields:
    if field not in record or record[field] is None or record[field] == "":
        return False  # Skip invalid record
```

**Impact:** Invalid records are skipped and counted in `summary["skipped"]`

---

### 2. Date Parsing & Normalization

**Location:** `src/resalelens/ingestion/utils.py::parse_date()`

**Purpose:** Handle multiple date formats from data.gov.sg API

**Supported Formats:**
1. `YYYY-MM-DD` (e.g., "2024-01-15")
2. `YYYY-MM` (e.g., "2024-01") - assumes first day of month
3. `DD/MM/YYYY` (e.g., "15/01/2024")

**Error Handling:**
- Raises `ValueError` for unsupported formats
- Wrapped in try-catch during ingestion
- Failed conversions increment `summary["errors"]`

**Rationale:** data.gov.sg may return dates in different formats depending on the dataset version or API endpoint

---

### 3. Data Type Conversion

**Location:** `src/resalelens/ingestion/hdb_transactions.py` (lines 126-142)

**Purpose:** Convert string data from API to appropriate database types

**Conversions:**
- `floor_area_sqm`: `str` → `float`
- `resale_price`: `str` → `float`
- `lease_commence_date`: `str` → `int`
- `month`: `str` → `date` (via `parse_date()`)

**Error Handling:**
- All conversions wrapped in try-except
- Failed conversions skip the record
- Errors logged to console and `summary["errors"]`

**Rationale:** API returns all values as strings; database requires proper types for calculations and constraints

---

### 4. Street Name Normalization

**Problem:** HDB data uses abbreviations (e.g., "ST", "AVE") while OneMap uses full names (e.g., "STREET", "AVENUE"), causing geocoding failures and block matching issues.

#### 4.1 Geocoding Normalization

**Location:** `src/resalelens/ingestion/hdb_blocks.py::OneMapClient._expand_abbreviations()`

**Purpose:** Improve OneMap geocoding success rate by trying multiple address formats

**Strategy:**
1. Try original address: "123 ANG MO KIO ST"
2. If fails, try expanded: "123 ANG MO KIO STREET"

**Supported Abbreviations (19 total):**

| Abbreviation | Full Form | Example |
|--------------|-----------|---------|
| ST | STREET | ANG MO KIO ST → ANG MO KIO STREET |
| AVE | AVENUE | BEDOK NTH AVE 3 → BEDOK NORTH AVENUE 3 |
| DR | DRIVE | BUKIT BATOK DR → BUKIT BATOK DRIVE |
| RD | ROAD | CLEMENTI RD → CLEMENTI ROAD |
| CRES | CRESCENT | SERANGOON CRES → SERANGOON CRESCENT |
| PL | PLACE | HOUGANG PL → HOUGANG PLACE |
| TER | TERRACE | MARINE TER → MARINE TERRACE |
| CL | CLOSE | TAMPINES CL → TAMPINES CLOSE |
| CTRL | CENTRAL | TOA PAYOH CTRL → TOA PAYOH CENTRAL |
| PK | PARK | YISHUN PK → YISHUN PARK |
| HTS | HEIGHTS | BUKIT MERAH HTS → BUKIT MERAH HEIGHTS |
| GDN | GARDEN | PASIR RIS GDN → PASIR RIS GARDEN |
| GDNS | GARDENS | JURONG GDNS → JURONG GARDENS |
| LOR | LORONG | LOR CHUAN → LORONG CHUAN |
| JLN | JALAN | JLN KAYU → JALAN KAYU |
| UPP | UPPER | UPP SERANGOON RD → UPPER SERANGOON ROAD |
| LWR | LOWER | LWR DELTA RD → LOWER DELTA ROAD |
| NTH | NORTH | BEDOK NTH AVE → BEDOK NORTH AVENUE |
| STH | SOUTH | BUKIT BATOK STH AVE → BUKIT BATOK SOUTH AVENUE |

**Implementation:**
```python
abbreviations = {
    " ST ": " STREET ",
    " AVE ": " AVENUE ",
    # ... 17 more
}

expanded = address.upper()
for abbr, full in abbreviations.items():
    expanded = expanded.replace(abbr, full)
```

**Impact:** Geocoding success rate increased from ~60% to ~85% (estimated)

#### 4.2 Block Matching Normalization

**Location:** `src/resalelens/ingestion/hdb_property_info.py::normalize_street_name()`

**Purpose:** Match blocks from different data sources (HDB transactions vs HDB property info)

**Strategy:**
1. Convert to uppercase
2. Trim whitespace
3. Expand abbreviations (same 19 as above)

**Usage:**
```python
normalized_street = normalize_street_name(street)
if normalize_street_name(b.street) == normalized_street:
    # Match found!
```

**Rationale:** Different HDB datasets use inconsistent abbreviations; normalization ensures reliable matching

---

### 5. Deduplication

#### 5.1 In-Batch Deduplication

**Location:** `src/resalelens/ingestion/hdb_transactions.py` (lines 151-172)

**Purpose:** Prevent PostgreSQL cardinality violations from duplicate records in same API response

**Unique Key:** `(block, street, flat_type, date, storey_range, floor_area_sqm)`

**Logic:**
```python
seen_keys = set()
for txn in transactions_batch:
    key = (txn["block"], txn["street"], txn["flat_type"], 
           txn["date"], txn["storey_range"], txn["floor_area_sqm"])
    
    if key not in seen_keys:
        seen_keys.add(key)
        deduplicated_batch.append(txn)
    else:
        summary["skipped"] += 1
```

**Impact:** Prevents database errors; duplicates counted as skipped

#### 5.2 Database-Level Deduplication

**Method:** PostgreSQL `INSERT ... ON CONFLICT DO UPDATE`

**Unique Constraint:** Same 6-field key as in-batch deduplication

**Behavior:**
- **If record exists:** UPDATE with new values (price, flat_model, ingestion_run_id, updated_at)
- **If record is new:** INSERT as new row

**Rationale:** Handles re-ingestion of same data (e.g., monthly updates from data.gov.sg)

---

### 6. Incremental Sync

**Location:** `src/resalelens/ingestion/hdb_transactions.py` (lines 57-67)

**Purpose:** Skip already-ingested records to improve performance

**Logic:**
```python
if incremental:
    max_date = session.query(func.max(Transaction.date)).scalar()
    if date_obj.date() <= max_date:
        summary["skipped"] += 1
        continue
```

**Benefits:**
- Faster ingestion (only new data)
- Reduces API calls
- Prevents re-processing old data

**Trade-off:** May miss updates to old records (acceptable for MVP)

---

### 7. Ingestion Guardrails

**Location:** `src/resalelens/ingestion/guardrails.py::IngestionGuardrails`

#### 7.1 Environment Validation

**Purpose:** Ensure required credentials are set before starting ingestion

**Required Variables:**
- `DATA_GOV_SG_RESOURCE_ID`
- `ONEMAP_EMAIL`
- `ONEMAP_PASSWORD`

**Behavior:** Aborts ingestion if any variable is missing

#### 7.2 Production Warning

**Purpose:** Prevent accidental data modification in production

**Detection:** Checks if `DATABASE_URL` starts with `postgresql`

**Behavior:**
- Displays warning with database URL
- Prompts user for confirmation: "Continue? (yes/no)"
- Aborts if user declines

#### 7.3 Database State Logging

**Purpose:** Track changes made by ingestion for audit and debugging

**Logged Metrics:**
- **Before ingestion:** Counts of transactions, blocks, ingestion_runs
- **After ingestion:** Same counts with deltas

**Example Output:**
```
📊 Database state before ingestion:
   Transactions: 218,252
   Blocks: 0
   Ingestion runs: 3

📊 Database state after ingestion:
   Transactions: 222,835 (+4,583)
   Blocks: 11,234 (+11,234)
   Ingestion runs: 4 (+1)
```

---

### 8. Rate Limiting

**Location:** `src/resalelens/ingestion/hdb_transactions.py` (lines 52-54, 199-202)

**Purpose:** Respect API rate limits to prevent throttling or bans

**Configuration:**
- `DATA_GOV_SG_REQUESTS_PER_MINUTE` (default: 60)
- Delay calculated: `60.0 / requests_per_minute`

**Implementation:**
```python
if has_more and delay_between_requests > 0:
    print(f"Rate limiting: sleeping {delay_between_requests:.2f}s")
    time.sleep(delay_between_requests)
```

**Impact:** Prevents API rate limit violations; ingestion takes longer but is more reliable

---

### 9. Error Tracking & Audit Logging

**Metrics Tracked:**
- `total_fetched` - Total records fetched from API
- `inserted` - New records inserted (or upserted)
- `skipped` - Invalid/duplicate records skipped
- `errors` - Records that failed to process

**Logged To:**
1. **Console Output** - Real-time progress for monitoring
2. **`ingestion_runs` Table** - Permanent audit trail
   - `rows_processed` - Total records processed
   - `status` - `in_progress`, `success`, or `failed`
   - `error_summary` - Detailed error messages (if failed)

**Example Summary:**
```python
{
    "total_fetched": 1000,
    "inserted": 950,
    "skipped": 45,
    "errors": 5,
    "incremental": False,
    "since_date": None
}
```

---

## Validation Gaps (Future Enhancements)

### Not Currently Implemented

1. **Range Validation**
   - No checks for reasonable price ranges (e.g., $50k - $2M)
   - No checks for floor_area_sqm ranges (e.g., 30-200 sqm)
   - No checks for lease_commence_date ranges (e.g., 1960-2024)

2. **String Normalization**
   - No trimming of leading/trailing whitespace
   - No case normalization for town names
   - No special character handling

3. **Outlier Detection**
   - No statistical outlier detection (e.g., price/sqm > 3 std deviations)
   - No flagging of suspicious records for manual review

4. **Geocoding Validation**
   - No validation that lat/lng are within Singapore bounds (1.1°N - 1.5°N, 103.6°E - 104.0°E)
   - No reverse geocoding to verify address matches coordinates

5. **EDA (Exploratory Data Analysis)**
   - No automated EDA reports after ingestion
   - No data quality dashboards
   - No distribution analysis (price, floor area, etc.)

### Recommendations for Future PRs

**Priority 1:** Add range validation (PR2.1 or PR8)
- Validate price: $50k - $2M
- Validate floor_area_sqm: 30-200 sqm
- Validate lease_commence_date: 1960-2024

**Priority 2:** Add string normalization (PR2.1)
- Trim whitespace
- Normalize case for town names
- Handle special characters

**Priority 3:** Add post-ingestion EDA (PR8 - Admin Dashboard)
- Generate summary statistics
- Flag outliers for review
- Display data quality metrics in admin dashboard

---

## Consequences

### Positive

✅ **High Data Quality** - Invalid records are rejected before entering database  
✅ **Reliable Geocoding** - Street name normalization improves OneMap success rate  
✅ **No Duplicates** - In-batch and database-level deduplication prevents duplicate records  
✅ **Audit Trail** - Comprehensive logging enables debugging and compliance  
✅ **Production Safety** - Guardrails prevent accidental data corruption  
✅ **API Compliance** - Rate limiting prevents throttling or bans  

### Negative

⚠️ **Performance Overhead** - Validation and normalization add processing time  
⚠️ **Data Loss** - Invalid records are skipped (not stored for manual review)  
⚠️ **Complexity** - Multiple validation layers increase code complexity  

### Neutral

ℹ️ **Manual Review Required** - Geocoding failures need manual investigation  
ℹ️ **Incremental Sync Limitation** - May miss updates to old records  

---

## Alternatives Considered

### 1. No Validation (Rejected)
**Pros:** Faster ingestion, simpler code  
**Cons:** Corrupted data in database, unreliable Fair Value calculations  
**Decision:** Rejected - data quality is critical for MVP

### 2. Validation After Ingestion (Rejected)
**Pros:** Faster initial ingestion  
**Cons:** Invalid data enters database, requires cleanup scripts  
**Decision:** Rejected - prevention is better than cleanup

### 3. Manual Data Cleaning (Rejected)
**Pros:** More control over data quality  
**Cons:** Not scalable, error-prone, time-consuming  
**Decision:** Rejected - automated validation is more reliable

---

## References

- **Implementation:** `src/resalelens/ingestion/`
  - `utils.py` - Validation and parsing functions
  - `hdb_transactions.py` - Transaction ingestion with validation
  - `hdb_blocks.py` - Block ingestion with geocoding normalization
  - `hdb_property_info.py` - Block matching with street normalization
  - `guardrails.py` - Safety checks and environment validation

- **Tests:** `tests/ingestion/`
  - `test_utils.py` - Validation function tests
  - `test_hdb_transactions.py` - Ingestion logic tests

- **Related Decisions:**
  - `PR2_API_VALIDATION.md` - API endpoint validation and testing
  - `PR1_DATABASE_SCHEMA.md` - Database constraints and unique keys

---

**Last Updated:** 2026-01-11  
**Author:** ResaleLens Team  
**Status:** ✅ Implemented in PR2
