# Postal Code Data Source Verification

**Date:** 2026-01-14  
**Status:** ✅ Verified  
**Decision:** Use data.gov.sg HDB Existing Building GeoJSON as primary postal code source

---

## Verification Summary

### ✅ Codebase Status: CORRECT

The ResaleLens codebase is correctly configured to use **HDB Existing Building GeoJSON** as the primary postal code data source, as specified in PR5.1.

---

## Findings

### 1. Schema Ready ✅

**Location:** `src/resalelens/models.py:181`

```python
postal_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
```

- `postal_code` column exists in `blocks` table
- Currently `NULL` for all records (not yet ingested)
- Ready for PR5.1 implementation

### 2. No Conflicting Implementation ✅

**Verified Locations:**
- ❌ No `hdb_postal_codes.py` in `src/resalelens/ingestion/` (not yet implemented)
- ❌ No postal code ingestion in `hdb_blocks.py` (OneMap geocoding doesn't capture `POSTAL` field)
- ❌ No postal code admin endpoint in `routers/admin.py`

**Status:** Clean slate - no conflicting implementation exists

### 3. Configuration Missing (Expected) ⚠️

**Location:** `.env.example`

Current state:
- ✅ `DATA_GOV_SG_API_URL` configured
- ✅ `DATA_GOV_SG_RESOURCE_ID` configured (HDB transactions)
- ❌ No `DATA_GOV_SG_POSTAL_RESOURCE_ID` configured

**Required addition for PR5.1:**
```bash
# HDB Existing Building (Postal Codes)
DATA_GOV_SG_POSTAL_RESOURCE_ID=d_16b157c52ed637edd6ba1232e026258d
```

### 4. Admin Endpoint Not Configured ⚠️

**Location:** `src/resalelens/routers/admin.py`

Current supported datasets:
- `hdb_transactions`
- `hdb_blocks`
- `hdb_property_info`
- `pois`
- `block_pois`

**Missing:** `hdb_postal_codes`

---

## Data Source Comparison

### Option 1: HDB Existing Building GeoJSON (✅ CHOSEN)

| Aspect | Details |
|--------|---------|
| **Dataset ID** | `d_16b157c52ed637edd6ba1232e026258d` |
| **Provider** | HDB via data.gov.sg |
| **Format** | GeoJSON |
| **Coverage** | All HDB blocks |
| **Rate Limits** | None (public dataset) |
| **Authentication** | Not required |
| **API Calls** | 1 (single download) |
| **Implementation** | Not yet implemented |

**Advantages:**
- ✅ Purpose-built for block → postal code mapping
- ✅ Complete authoritative data
- ✅ Single API call vs 9,675
- ✅ No rate limits or auth complexity
- ✅ Direct GeoJSON parsing

### Option 2: OneMap Geocoding API (❌ NOT RECOMMENDED)

| Aspect | Details |
|--------|---------|
| **Provider** | Singapore Land Authority (SLA) |
| **Format** | JSON (search results) |
| **Coverage** | Singapore-wide |
| **Rate Limits** | 250 requests per token |
| **Authentication** | Required (JWT) |
| **API Calls** | 9,675 (one per block) |
| **Implementation** | Geocoding exists, but doesn't capture postal codes |

**Disadvantages:**
- ❌ Requires 9,675 API calls with rate limits
- ❌ Authentication complexity
- ❌ Token refresh overhead (~39 refreshes)
- ❌ Time-consuming (~25-30 minutes)
- ❌ Not purpose-built for this use case

---

## PR5.1 Implementation Checklist

Based on verification, PR5.1 should implement:

### Backend Changes

- [ ] Create `src/resalelens/ingestion/hdb_postal_codes.py`
  - Download GeoJSON from data.gov.sg
  - Parse `properties.postal`, `properties.blk_no`, `properties.road_name`
  - Match to existing blocks
  - Update `blocks.postal_code`
  - Extract postal sector (first 2 digits)

- [ ] Update `src/resalelens/routers/admin.py`
  - Add `hdb_postal_codes` to supported datasets
  - Import and call `ingest_hdb_postal_codes()`

- [ ] Update `src/resalelens/ingestion/__init__.py`
  - Export `ingest_hdb_postal_codes`

### Configuration Changes

- [ ] Update `.env.example`
  ```bash
  # HDB Existing Building (Postal Codes)
  DATA_GOV_SG_POSTAL_RESOURCE_ID=d_16b157c52ed637edd6ba1232e026258d
  ```

### Database Changes

- [ ] Add index on `postal_code`
  ```sql
  CREATE INDEX idx_blocks_postal_code ON blocks(postal_code);
  ```

- [ ] Optional: Add `postal_sector` computed column
  ```python
  @hybrid_property
  def postal_sector(self) -> str | None:
      if self.postal_code and len(self.postal_code) >= 2:
          return self.postal_code[:2]
      return None
  ```

### Frontend Changes (Per PR5.1)

- [ ] Add postal code input toggle in `templates/index.html`
- [ ] Create `GET /api/block-lookup?postal_code={code}` endpoint
- [ ] Client-side postal code validation (6 digits)
- [ ] JavaScript auto-lookup functionality

### Testing

- [ ] Unit tests for GeoJSON parsing
- [ ] Integration tests for postal code ingestion
- [ ] Block lookup API tests
- [ ] Edge case handling (duplicates, missing data)

---

## Future Enhancement: OneMap as Secondary Source

Once HDB GeoJSON postal codes are ingested, **consider** adding postal code capture to OneMap geocoding as a **verification/fallback mechanism**:

**Location:** `src/resalelens/ingestion/hdb_blocks.py`

```python
# After line where latitude/longitude are extracted
postal_code = result.get("POSTAL")  # Add this line
if postal_code:
    # Store or verify against HDB GeoJSON data
```

**Benefits:**
- Cross-verification of postal codes
- Auto-update for new blocks
- No additional API calls (already geocoding)

**Limitation:**
- Only captures postal codes for newly geocoded blocks
- Requires one-time backfill from HDB GeoJSON

---

## Conclusion

✅ **Codebase is correctly positioned to use HDB GeoJSON as primary postal code source**

- Schema is ready (`postal_code` column exists)
- No conflicting implementation
- Clean implementation path for PR5.1
- Configuration follows best practices

**Next Step:** Implement PR5.1 following the checklist above.

---

## References

- **PR5.1 Plan:** [docs/plans/PR5.1_POSTAL_CODE_INPUT.md](../plans/PR5.1_POSTAL_CODE_INPUT.md)
- **Data Sources Reference:** [docs/references/DATA_SOURCES.md](../references/DATA_SOURCES.md)
- **HDB GeoJSON Dataset:** https://data.gov.sg/datasets?topics=housing&resultId=d_16b157c52ed637edd6ba1232e026258d
- **Database Schema:** [docs/plans/PR1_DATABASE_SCHEMA.md](../plans/PR1_DATABASE_SCHEMA.md)

---

**Verified By:** AI Assistant  
**Verification Date:** 2026-01-14  
**Confidence:** High ✅
