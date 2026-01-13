# Data Sources Inventory

**Last Updated:** 2026-01-14  
**Purpose:** Complete inventory of all external data sources used in ResaleLens SG and their ingestion status in Supabase  
**Database:** Supabase PostgreSQL

---

## Overview

ResaleLens SG integrates data from **3 primary external APIs** to provide comprehensive HDB resale insights:

| Data Source | Purpose | Status | Records in Supabase |
|-------------|---------|--------|---------------------|
| **data.gov.sg** | HDB transaction data | ✅ Active | 218,372 transactions |
| **data.gov.sg** | HDB property information | ✅ Available* | Not yet ingested |
| **OneMap API** | Geocoding & POI data | ✅ Active | 1,916 POIs + 635,259 relationships |

\* *Available via admin endpoint but not yet triggered*

**Total Data Volume:** 865,222 records across 4 tables

---

## 1. data.gov.sg - HDB Resale Transactions

### API Details

| Property | Value |
|----------|-------|
| **API Name** | Resale flat prices based on registration date from Jan-2017 onwards |
| **Base URL** | `https://data.gov.sg/api/action/datastore_search` |
| **Resource ID** | `d_8b84c4ee58e3cfc0ece0d773c8ca6abc` |
| **Authentication** | ❌ None required (public API) |
| **Rate Limits** | No documented limits |
| **Cost** | ✅ Free |
| **Data Freshness** | Updated monthly by HDB |

### Full Endpoint

```
https://data.gov.sg/api/action/datastore_search?resource_id=d_8b84c4ee58e3cfc0ece0d773c8ca6abc
```

### Data Ingested

**Supabase Table:** `transactions`

| Source Field | Database Column | Type | Description |
|--------------|----------------|------|-------------|
| `month` | `date` | Date | Transaction date (first day of month) |
| `town` | `town` | String(100) | HDB town name |
| `flat_type` | `flat_type` | String(50) | Flat type (e.g., "3 ROOM", "4 ROOM") |
| `block` | `block` | String(50) | Block number |
| `street_name` | `street` | String(255) | Street name |
| `storey_range` | `storey_range` | String(50) | Storey range (e.g., "10 TO 12") |
| `floor_area_sqm` | `floor_area_sqm` | Numeric(10,2) | Floor area in sqm |
| `flat_model` | `flat_model` | String(100) | Flat model type |
| `lease_commence_date` | `lease_commence_date` | Integer | Year lease commenced |
| `resale_price` | `price` | Numeric(12,2) | Resale price in SGD |
| *(computed)* | `latitude` | Numeric(10,7) | Geocoded latitude (via OneMap) |
| *(computed)* | `longitude` | Numeric(10,7) | Geocoded longitude (via OneMap) |
| *(computed)* | `psm` | *Computed Property* | Price per square meter |

### Ingestion Status

✅ **Active and Current**

- **Latest Ingestion:** 2026-01-13 13:58 SGT
- **Records Ingested:** 218,372 transactions
- **Data Coverage:** Jan 2017 - Present
- **Schedule:** Weekly (Sundays 03:00 SGT)
- **Ingestion Method:** Automated via APScheduler + Manual admin trigger

### Admin Endpoint

```bash
POST http://localhost:8000/admin/ingestion/trigger?dataset=hdb_transactions
```

**Query Parameters:**
- `incremental`: `true` to fetch only new records since last run (default: `false`)

---

## 2. data.gov.sg - HDB Property Information

### API Details

| Property | Value |
|----------|-------|
| **API Name** | HDB Property Information |
| **Base URL** | `https://data.gov.sg/api/action/datastore_search` |
| **Resource ID** | `d_38fdbf555b3be2628cb8f1c90524b5e9` |
| **Authentication** | ❌ None required (public API) |
| **Rate Limits** | No documented limits |
| **Cost** | ✅ Free |
| **Data Freshness** | Updated periodically by HDB |

### Data Available (Not Yet Ingested)

**Supabase Table:** `blocks` (enriched fields)

The following 27 fields can be ingested to enrich block metadata:

#### Building Characteristics
- `max_floor_lvl` - Maximum floor level
- `year_completed` - Year building was completed
- `total_dwelling_units` - Total number of units

#### Facility Flags
- `residential` - Has residential units
- `commercial` - Has commercial units
- `market_hawker` - Has market/hawker centre
- `multistorey_carpark` - Has multistorey carpark
- `precinct_pavilion` - Has precinct pavilion
- `miscellaneous` - Has other facilities

#### Unit Mix - Sold Units
- `1room_sold` - Number of 1-room sold
- `2room_sold` - Number of 2-room sold
- `3room_sold` - Number of 3-room sold
- `4room_sold` - Number of 4-room sold
- `5room_sold` - Number of 5-room sold
- `exec_sold` - Number of executive sold
- `multigen_sold` - Number of multi-generation sold
- `studio_apartment_sold` - Number of studio apartments sold

#### Unit Mix - Rental Units
- `1room_rental` - Number of 1-room rental
- `2room_rental` - Number of 2-room rental
- `3room_rental` - Number of 3-room rental
- `other_room_rental` - Number of other rental units

### Ingestion Status

⚠️ **Available but Not Yet Ingested**

- **Schema:** ✅ Columns exist in `blocks` table
- **Ingestion Script:** ✅ Implemented at `src/resalelens/ingestion/hdb_property_info.py`
- **Admin Endpoint:** ✅ Available
- **Action Required:** Trigger manual ingestion

### Admin Endpoint

```bash
POST http://localhost:8000/admin/ingestion/trigger?dataset=hdb_property_info
```

---

## 3. OneMap API - Geocoding

### API Details

| Property | Value |
|----------|-------|
| **API Name** | OneMap Search API |
| **Base URL (Search)** | `https://www.onemap.gov.sg/api/common/elastic/search` |
| **Base URL (Auth)** | `https://www.onemap.gov.sg/api/auth/post/getToken` |
| **Authentication** | ✅ Required (JWT token with 3-day TTL) |
| **Rate Limits** | 250 requests per token session |
| **Cost** | ✅ Free |
| **Account Required** | Yes - Register at [onemap.gov.sg/apidocs](https://www.onemap.gov.sg/apidocs/) |

### Data Ingested

**Supabase Tables:** `blocks` (latitude/longitude enrichment)

| Source Field | Database Column | Type | Description |
|--------------|----------------|------|-------------|
| `LATITUDE` | `latitude` | Numeric(10,7) | WGS84 latitude |
| `LONGITUDE` | `longitude` | Numeric(10,7) | WGS84 longitude |

**Note:** While OneMap also returns a `POSTAL` field, postal codes are ingested from the **HDB Existing Building GeoJSON dataset** (data.gov.sg) as the primary source. See PR5.1 for postal code implementation.

### Ingestion Status

✅ **Active and Current**

- **Latest Ingestion:** 2026-01-13 14:06 SGT
- **Blocks Geocoded:** 9,675 blocks
- **Success Rate:** ~100% (blocks with coordinates)
- **Schedule:** Weekly (Sundays 03:15 SGT)
- **Ingestion Method:** Automated via APScheduler + Manual admin trigger

### Admin Endpoint

```bash
POST http://localhost:8000/admin/ingestion/trigger?dataset=hdb_blocks
```

**Note:** Geocoding runs as part of `hdb_blocks` ingestion

---

## 4. OneMap API - Points of Interest (POIs)

### API Details

| Property | Value |
|----------|-------|
| **API Name** | OneMap Search API |
| **Base URL** | `https://www.onemap.gov.sg/api/common/elastic/search` |
| **Authentication** | ✅ Required (JWT token) |
| **Rate Limits** | 250 requests per token session |
| **Cost** | ✅ Free |

### POI Categories Ingested

**Supabase Table:** `pois`

| Category | Search Query | POI Type | Count |
|----------|-------------|----------|-------|
| **Transport** | "MRT STATION" | `MRT` | 755 |
| **Transport** | "LRT STATION" | `LRT` | 44 |
| **Education** | "PRIMARY SCHOOL" | `school` | 314 |
| **Education** | "SECONDARY SCHOOL" | `school` | *(included above)* |
| **Healthcare** | "CLINIC" | `clinic` | 312 |
| **Healthcare** | "POLYCLINIC" | `clinic` | *(included above)* |
| **Shopping** | "MALL", "SHOPPING CENTRE", "PLAZA" | `mall` | 255 |
| **Supermarkets** | "NTUC", "FAIRPRICE", "SHENG SIONG", etc. | `supermarket` | 37 |
| **Food** | "HAWKER CENTRE", "FOOD CENTRE" | `hawker` | 129 |
| **Recreation** | "PARK CONNECTOR", "NEIGHBOURHOOD PARK" | `park` | 70 |

**Total POIs:** 1,916

### Data Schema

| Source Field | Database Column | Type | Description |
|--------------|----------------|------|-------------|
| `SEARCHVAL` | `name` | String(255) | POI name |
| `LATITUDE` | `latitude` | Numeric(10,7) | WGS84 latitude |
| `LONGITUDE` | `longitude` | Numeric(10,7) | WGS84 longitude |
| *(assigned)* | `poi_type` | Enum | POI category type |

### Ingestion Status

✅ **Active and Current**

- **Latest Ingestion:** 2026-01-13 15:09 SGT
- **Records Ingested:** 1,916 POIs
- **Duplicates Skipped:** 520
- **Total Found:** 2,436
- **Schedule:** Monthly (1st of month, 03:30 SGT)
- **Ingestion Method:** Automated via APScheduler + Manual admin trigger

### Admin Endpoint

```bash
POST http://localhost:8000/admin/ingestion/trigger?dataset=pois
```

---

## 5. Block-POI Distance Calculations (Derived Data)

### Data Source

**Source:** Derived from `blocks` + `pois` tables using Haversine distance calculation

### Data Ingested

**Supabase Table:** `block_pois`

| Field | Type | Description |
|-------|------|-------------|
| `block_id` | Foreign Key | Reference to `blocks.id` |
| `poi_id` | Foreign Key | Reference to `pois.id` |
| `distance_m` | Numeric(10,2) | Distance in meters |

### Distance Calculation Method

**Algorithm:** Haversine formula for great-circle distance

```python
def calculate_haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371000  # Earth radius in meters
    # ... [standard Haversine implementation]
```

**Threshold:** 2,000 meters (2km radius)

### Ingestion Status

✅ **Active and Current**

- **Latest Ingestion:** 2026-01-13 15:15 SGT
- **Relationships Created:** 635,259 block-POI pairs
- **Blocks Covered:** 9,675 (100% coverage)
- **Orphaned Blocks:** 0
- **Average POIs per Block:** 65.7
- **Distance Statistics:**
  - Min: 0.0m (POI at same location)
  - Max: 2,000.0m (threshold)
  - Avg: 1,246.23m

### POI Type Distribution in Relationships

| POI Type | Total Links | Description |
|----------|-------------|-------------|
| MRT | 191,537 | MRT station accessibility |
| Schools | 149,137 | Primary & secondary schools |
| Clinics | 111,333 | Medical facilities |
| Malls | 74,614 | Shopping centers |
| Hawkers | 42,096 | Hawker centers & food courts |
| Parks | 26,648 | Parks & park connectors |
| LRT | 25,527 | LRT station accessibility |
| Supermarkets | 14,367 | Grocery stores |

### Schedule

- **Trigger:** After POI ingestion completes
- **Method:** Recalculates all distances on each run
- **Upsert Strategy:** Insert or update existing relationships

### Admin Endpoint

```bash
POST http://localhost:8000/admin/ingestion/trigger?dataset=block_pois
```

---

## Ingestion Schedule Summary

All ingestion jobs are managed by **APScheduler** and configured in `src/resalelens/scheduler.py`:

| Dataset | Frequency | Schedule | Timezone | Dependencies |
|---------|-----------|----------|----------|--------------|
| HDB Transactions | Weekly | Sundays 03:00 | SGT | None |
| HDB Blocks | Weekly | Sundays 03:15 | SGT | None (runs independently) |
| POIs | Monthly | 1st of month, 03:30 | SGT | None |
| Block-POIs | Monthly | 1st of month, 03:45 | SGT | Requires POIs |

**Manual Triggers:** All datasets can be manually triggered via admin endpoints at any time.

---

## Data Quality & Validation

### Ingestion Run Tracking

All ingestion runs are logged in the `ingestion_runs` table:

| Field | Description |
|-------|-------------|
| `dataset_name` | Name of the dataset ingested |
| `started_at` | Timestamp when ingestion began |
| `completed_at` | Timestamp when ingestion completed |
| `status` | `success`, `failed`, or `in_progress` |
| `rows_processed` | Number of records processed |
| `error_summary` | Error details if failed |

### Recent Ingestion History

Latest successful runs as of 2026-01-14:

```
✅ block_pois_distances: 635,259 rows - 2026-01-13 15:15 SGT
✅ onemap_pois: 1,916 rows - 2026-01-13 15:09 SGT
✅ hdb_blocks: 9,676 rows - 2026-01-13 14:06 SGT
✅ hdb_transactions: 222,955 rows - 2026-01-13 13:58 SGT
```

### Data Validation Rules

**Transactions Table:**
- ✅ Unique constraint on (block, street, flat_type, date, storey_range, floor_area_sqm)
- ✅ Price and floor area must be positive
- ✅ Latitude/longitude within valid ranges

**Blocks Table:**
- ✅ Unique constraint on (block, street)
- ✅ Geocoded coordinates validated against Singapore bounds
- ✅ Lease commence year ≥ 1960

**POIs Table:**
- ✅ Valid POI type enum
- ✅ Geocoded coordinates required
- ✅ Duplicate detection by (name, poi_type)

**Block-POIs Table:**
- ✅ Unique constraint on (block_id, poi_id)
- ✅ Distance ≥ 0
- ✅ Maximum distance 2,000m enforced

---

## Environment Configuration

Required environment variables for data source access:

```bash
# data.gov.sg API
DATA_GOV_SG_API_URL=https://data.gov.sg/api/action/datastore_search
DATA_GOV_SG_RESOURCE_ID=d_8b84c4ee58e3cfc0ece0d773c8ca6abc
DATA_GOV_SG_PROPERTY_RESOURCE_ID=d_38fdbf555b3be2628cb8f1c90524b5e9

# OneMap API
ONEMAP_API_URL=https://www.onemap.gov.sg/api/common/elastic/search
ONEMAP_AUTH_URL=https://www.onemap.gov.sg/api/auth/post/getToken
ONEMAP_EMAIL=<your_registered_email>
ONEMAP_PASSWORD=<your_password>

# Ingestion Configuration
INGESTION_RETRY_COUNT=3
INGESTION_RETRY_DELAY_SECONDS=5
```

---

## API Credits & Attribution

### data.gov.sg
- **Provider:** Singapore Government Technology Agency (GovTech)
- **License:** Singapore Open Data License
- **Attribution Required:** Yes - "Data from data.gov.sg"
- **Website:** [data.gov.sg](https://data.gov.sg)

### OneMap
- **Provider:** Singapore Land Authority (SLA)
- **License:** OneMap API Terms of Service
- **Attribution Required:** Yes - "Data from OneMap"
- **Website:** [onemap.gov.sg](https://www.onemap.gov.sg)

---

## Data Retention & Updates

### Retention Policy
- **Transactions:** Retain all historical records indefinitely
- **Blocks:** Update existing records, retain all versions via `last_updated` timestamp
- **POIs:** Update existing records, retain all versions via `last_updated` timestamp
- **Block-POIs:** Recalculate and replace on each run (upsert strategy)

### Update Strategy
- **Transactions:** Full refresh (re-ingest all records)
- **Blocks:** Full refresh with geocoding
- **POIs:** Full refresh with duplicate detection
- **Block-POIs:** Full recalculation

**Rationale:** Simple implementation for MVP; incremental sync can be added in future phases.

---

## Next Steps

### Immediate Actions Required

1. **Ingest HDB Property Information**
   ```bash
   POST http://localhost:8000/admin/ingestion/trigger?dataset=hdb_property_info
   ```
   This will enrich the `blocks` table with 27 additional fields.

2. **Monitor Ingestion Health**
   - Check `ingestion_runs` table for failed runs
   - Set up alerts for ingestion failures
   - Track data freshness on Data Status page (PR6)

### Future Enhancements

- [ ] Implement incremental ingestion for transactions (delta sync)
- [ ] **Add postal code ingestion from HDB Existing Building GeoJSON** (PR5.1)
- [ ] Build pre-geocoded database for faster initial loads
- [ ] Add data quality metrics dashboard
- [ ] Implement automatic OneMap token refresh
- [ ] Add data export functionality for backup

---

## References

- **API Validation Report:** [docs/decisions/PR2_API_VALIDATION.md](file:///Users/jefflee/Documents/AIProjects/ResaleLens_SG-V1/docs/decisions/PR2_API_VALIDATION.md)
- **Database Schema:** [docs/plans/PR1_DATABASE_SCHEMA.md](file:///Users/jefflee/Documents/AIProjects/ResaleLens_SG-V1/docs/plans/PR1_DATABASE_SCHEMA.md)
- **Data Ingestion Plans:**
  - [PR2: HDB Data Ingestion](file:///Users/jefflee/Documents/AIProjects/ResaleLens_SG-V1/docs/plans/PR2_DATA_INGESTION_HDB.md)
  - [PR3: POI & MRT Ingestion](file:///Users/jefflee/Documents/AIProjects/ResaleLens_SG-V1/docs/plans/PR3_DATA_INGESTION_POIS_MRT.md)

---

**Document Version:** 1.0  
**Last Verified:** 2026-01-14  
**Database:** Supabase PostgreSQL (Production)
