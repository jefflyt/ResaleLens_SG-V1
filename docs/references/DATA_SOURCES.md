# ResaleLens Data Sources Reference

**Version:** 1.0  
**Last Updated:** 2026-01-14  
**Status:** Official Reference Documentation

---

## Table of Contents

1. [Overview](#overview)
2. [Data Sources](#data-sources)
   - [data.gov.sg - HDB Resale Transactions](#1-datagovsg---hdb-resale-transactions)
   - [data.gov.sg - HDB Property Information](#2-datagovsg---hdb-property-information)
   - [OneMap API - Geocoding](#3-onemap-api---geocoding)
   - [OneMap API - Points of Interest](#4-onemap-api---points-of-interest)
   - [OneMap API - Postal Codes](#5-onemap-api---postal-codes-planned)
3. [Derived Data](#derived-data)
4. [API Authentication & Rate Limiting](#api-authentication--rate-limiting)
5. [Ingestion Architecture](#ingestion-architecture)
6. [Data Quality & Validation](#data-quality--validation)
7. [Environment Configuration](#environment-configuration)
8. [Monitoring & Observability](#monitoring--observability)
9. [Attribution & Licensing](#attribution--licensing)
10. [References](#references)

---

## Overview

ResaleLens SG integrates data from multiple Singapore government and public APIs to provide comprehensive HDB resale property insights. All data is stored in **Supabase PostgreSQL** and updated automatically via scheduled ingestion jobs.

### Current Data Volume (as of 2026-01-14)

| Category | Records | Status |
|----------|---------|--------|
| HDB Transactions | 218,372 | ✅ Active |
| HDB Blocks | 9,675 | ✅ Active |
| POIs | 1,916 | ✅ Active |
| Block-POI Relationships | 635,259 | ✅ Active |
| HDB Property Information | 0 | ⚠️ Available but not ingested |

**Total:** 865,222 records

---

## Data Sources

### 1. data.gov.sg - HDB Resale Transactions

#### API Information

| Property | Value |
|----------|-------|
| **Dataset Name** | Resale flat prices based on registration date from Jan-2017 onwards |
| **Base URL** | `https://data.gov.sg/api/action/datastore_search` |
| **Resource ID** | `d_8b84c4ee58e3cfc0ece0d773c8ca6abc` |
| **Full Endpoint** | `https://data.gov.sg/api/action/datastore_search?resource_id=d_8b84c4ee58e3cfc0ece0d773c8ca6abc` |
| **Authentication** | ❌ None required (public API) |
| **Rate Limits** | No documented limits (tested 60 req/min safely) |
| **Cost** | ✅ Free |
| **Provider** | Singapore Housing & Development Board (HDB) via GovTech |
| **Data Freshness** | Updated monthly |
| **Total Records Available** | 222,835+ (as of Jan 2026) |

#### Data Schema

**Supabase Table:** `transactions`

| Source Field | Database Column | Type | Description | Validation |
|--------------|----------------|------|-------------|------------|
| `month` | `date` | Date | Transaction month (YYYY-MM) | Parsed to first day of month |
| `town` | `town` | String(100) | HDB town name | Required |
| `flat_type` | `flat_type` | String(50) | Flat type (e.g., "3 ROOM") | Required |
| `block` | `block` | String(50) | Block number | Required |
| `street_name` | `street` | String(255) | Street address | Required |
| `storey_range` | `storey_range` | String(50) | Storey range (e.g., "10 TO 12") | Required |
| `floor_area_sqm` | `floor_area_sqm` | Numeric(10,2) | Floor area in sqm | Must be > 0 |
| `flat_model` | `flat_model` | String(100) | Flat model type | Required |
| `lease_commence_date` | `lease_commence_date` | Integer | Year lease commenced | Must be ≥ 1960 |
| `resale_price` | `price` | Numeric(12,2) | Resale price in SGD | Must be > 0 |

**Computed/Enriched Fields:**
- `latitude`, `longitude` - Added via OneMap geocoding
- `psm` - Computed property: `price / floor_area_sqm`
- `block_id` - Foreign key to `blocks` table

#### Sample Response

```json
{
  "success": true,
  "result": {
    "resource_id": "d_8b84c4ee58e3cfc0ece0d773c8ca6abc",
    "records": [
      {
        "_id": 1,
        "month": "2017-01",
        "town": "ANG MO KIO",
        "flat_type": "2 ROOM",
        "block": "406",
        "street_name": "ANG MO KIO AVE 10",
        "storey_range": "10 TO 12",
        "floor_area_sqm": "44",
        "flat_model": "Improved",
        "lease_commence_date": "1979",
        "resale_price": "232000"
      }
    ],
    "total": 222835
  }
}
```

#### Ingestion Status

| Metric | Value |
|--------|-------|
| **Latest Ingestion** | 2026-01-13 13:58 SGT |
| **Records Ingested** | 218,372 |
| **Data Coverage** | Jan 2017 - Present |
| **Schedule** | Weekly (Sundays 03:00 SGT) |
| **Method** | APScheduler + Manual admin trigger |
| **Unique Constraint** | (block, street, flat_type, date, storey_range, floor_area_sqm) |

#### Admin Endpoint

```bash
# Full refresh (all records)
POST http://localhost:8000/admin/ingestion/trigger?dataset=hdb_transactions

# Incremental (new records only, not yet implemented)
POST http://localhost:8000/admin/ingestion/trigger?dataset=hdb_transactions&incremental=true
```

#### Rate Limiting Configuration

```bash
# Conservative default: 1 request per second
DATA_GOV_SG_REQUESTS_PER_MINUTE=60

# Optional: Limit records for testing
INGESTION_MAX_RECORDS=1000  # 0 = unlimited
```

**Implementation:**
- Automatic delay: `60 / requests_per_minute` seconds between requests
- Pagination: 1,000 records per page (~223 API calls for full dataset)
- Estimated full ingestion time: ~4 minutes at 60 req/min

---

### 2. data.gov.sg - HDB Property Information

#### API Information

| Property | Value |
|----------|-------|
| **Dataset Name** | HDB Property Information |
| **Base URL** | `https://data.gov.sg/api/action/datastore_search` |
| **Resource ID** | `d_38fdbf555b3be2628cb8f1c90524b5e9` |
| **Authentication** | ❌ None required (public API) |
| **Rate Limits** | Same as transactions API |
| **Cost** | ✅ Free |
| **Provider** | Housing & Development Board (HDB) |
| **Data Freshness** | Updated periodically |

#### Data Schema

**Supabase Table:** `blocks` (enrichment fields)

This API enriches the `blocks` table with 27 additional fields:

##### Building Characteristics (3 fields)
| Database Column | Type | Description |
|----------------|------|-------------|
| `max_floor_lvl` | Integer | Maximum floor level in block |
| `year_completed` | Integer | Year building was completed |
| `total_dwelling_units` | Integer | Total number of residential units |

##### Facility Flags (6 fields)
| Database Column | Type | Description |
|----------------|------|-------------|
| `residential` | Boolean | Has residential units (default: true) |
| `commercial` | Boolean | Has commercial units |
| `market_hawker` | Boolean | Has market/hawker centre |
| `multistorey_carpark` | Boolean | Has multistorey carpark |
| `precinct_pavilion` | Boolean | Has precinct pavilion |
| `miscellaneous` | Boolean | Has other facilities |

##### Unit Mix - Sold Units (8 fields)
| Database Column | Type | Description |
|----------------|------|-------------|
| `1room_sold` | Integer | Number of 1-room flats sold |
| `2room_sold` | Integer | Number of 2-room flats sold |
| `3room_sold` | Integer | Number of 3-room flats sold |
| `4room_sold` | Integer | Number of 4-room flats sold |
| `5room_sold` | Integer | Number of 5-room flats sold |
| `exec_sold` | Integer | Number of executive flats sold |
| `multigen_sold` | Integer | Number of multi-generation flats sold |
| `studio_apartment_sold` | Integer | Number of studio apartments sold |

##### Unit Mix - Rental Units (4 fields)
| Database Column | Type | Description |
|----------------|------|-------------|
| `1room_rental` | Integer | Number of 1-room rental units |
| `2room_rental` | Integer | Number of 2-room rental units |
| `3room_rental` | Integer | Number of 3-room rental units |
| `other_room_rental` | Integer | Number of other rental units |

#### Ingestion Status

⚠️ **Available but Not Yet Ingested**

| Metric | Value |
|--------|-------|
| **Schema Status** | ✅ Columns exist in `blocks` table |
| **Ingestion Script** | ✅ Implemented (`src/resalelens/ingestion/hdb_property_info.py`) |
| **Admin Endpoint** | ✅ Available |
| **Records to Ingest** | ~9,675 (one per block) |
| **Action Required** | Trigger manual ingestion |

#### Admin Endpoint

```bash
POST http://localhost:8000/admin/ingestion/trigger?dataset=hdb_property_info
```

---

### 3. OneMap API - Geocoding

#### API Information

| Property | Value |
|----------|-------|
| **API Name** | OneMap Search API (Geocoding) |
| **Base URL (Search)** | `https://www.onemap.gov.sg/api/common/elastic/search` |
| **Base URL (Auth)** | `https://www.onemap.gov.sg/api/auth/post/getToken` |
| **Authentication** | ✅ Required (JWT token with 3-day TTL) |
| **Rate Limits** | 250 requests per token session |
| **Cost** | ✅ Free tier |
| **Provider** | Singapore Land Authority (SLA) |
| **Account Required** | Yes - [Register here](https://www.onemap.gov.sg/apidocs/) |

#### Authentication Flow

**1. Token Generation:**

```bash
curl -X POST https://www.onemap.gov.sg/api/auth/post/getToken \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your_registered_email@example.com",
    "password": "your_password"
  }'
```

**Response:**
```json
{
  "access_token": "eyJ...[JWT token]",
  "expiry_timestamp": "1641234567890"
}
```

**2. Token Usage:**
- Include in `Authorization` header: `Bearer <token>`
- Token expires after 3 days
- Auto-refresh after 240 requests (safety margin)

#### Geocoding Request

**Endpoint:**
```
https://www.onemap.gov.sg/api/common/elastic/search?searchVal=<address>&returnGeom=Y&getAddrDetails=Y
```

**Example:**
```bash
curl "https://www.onemap.gov.sg/api/common/elastic/search?searchVal=BLK+108+ANG+MO+KIO+AVE+4&returnGeom=Y&getAddrDetails=Y" \
  -H "Authorization: Bearer <token>"
```

**Response:**
```json
{
  "found": 1,
  "results": [
    {
      "SEARCHVAL": "BLK 108 ANG MO KIO AVE 4",
      "BLK_NO": "108",
      "ROAD_NAME": "ANG MO KIO AVENUE 4",
      "POSTAL": "560108",
      "LATITUDE": "1.372123",
      "LONGITUDE": "103.845456"
    }
  ]
}
```

#### Data Schema

**Supabase Table:** `blocks` (latitude/longitude enrichment)

| Source Field | Database Column | Type | Description |
|--------------|----------------|------|-------------|
| `LATITUDE` | `latitude` | Numeric(10,7) | WGS84 latitude |
| `LONGITUDE` | `longitude` | Numeric(10,7) | WGS84 longitude |
| `POSTAL` | `postal_code` | String(10) | 6-digit postal code |

#### Ingestion Status

✅ **Active and Current**

| Metric | Value |
|--------|-------|
| **Latest Ingestion** | 2026-01-13 14:06 SGT |
| **Blocks Geocoded** | 9,675 |
| **Success Rate** | ~100% |
| **Schedule** | Weekly (Sundays 03:15 SGT) |
| **Method** | Part of `hdb_blocks` ingestion |

#### Rate Limiting Implementation

**Guardrails:**
- Token refresh after 240 requests (250 limit with 10-request safety margin)
- 2-second pause every 100 geocoding requests
- Retry logic: 2 attempts per address
- Graceful failure: Returns `null` coordinates if geocoding fails

**Estimated Processing:**
- 9,675 blocks ÷ 250 requests per token = ~39 token refreshes
- With pauses: ~5-10 minutes total

---

### 4. OneMap API - Points of Interest

#### API Information

Same API as geocoding (see above), but used for POI discovery via search queries.

#### POI Categories

**Supabase Table:** `pois`

| Category | Search Queries | POI Type | Count | Description |
|----------|---------------|----------|-------|-------------|
| **Transport - MRT** | "MRT STATION" | `MRT` | 755 | MRT stations |
| **Transport - LRT** | "LRT STATION" | `LRT` | 44 | LRT stations |
| **Education** | "PRIMARY SCHOOL", "SECONDARY SCHOOL" | `school` | 314 | Primary & secondary schools |
| **Healthcare** | "CLINIC", "POLYCLINIC" | `clinic` | 312 | Medical facilities & polyclinics |
| **Shopping** | "MALL", "SHOPPING CENTRE", "PLAZA" | `mall` | 255 | Shopping centers & malls |
| **Supermarkets** | "NTUC", "FAIRPRICE", "SHENG SIONG", "COLD STORAGE", "GIANT", "DON DON DONKI", etc. | `supermarket` | 37 | Major supermarket chains |
| **Food** | "HAWKER CENTRE", "FOOD CENTRE", "MARKET AND FOOD CENTRE" | `hawker` | 129 | Hawker centers & food courts |
| **Recreation** | "PARK CONNECTOR", "NEIGHBOURHOOD PARK" | `park` | 70 | Parks & park connectors |

**Total POIs:** 1,916

#### Data Schema

| Source Field | Database Column | Type | Description |
|--------------|----------------|------|-------------|
| `SEARCHVAL` | `name` | String(255) | POI name |
| `LATITUDE` | `latitude` | Numeric(10,7) | WGS84 latitude (required) |
| `LONGITUDE` | `longitude` | Numeric(10,7) | WGS84 longitude (required) |
| *(assigned)* | `poi_type` | Enum(POIType) | Category enum value |
| *(auto)* | `last_updated` | DateTime | Last ingestion timestamp |

#### Ingestion Status

✅ **Active and Current**

| Metric | Value |
|--------|-------|
| **Latest Ingestion** | 2026-01-13 15:09 SGT |
| **Records Ingested** | 1,916 POIs |
| **Duplicates Skipped** | 520 |
| **Total Found** | 2,436 |
| **Schedule** | Monthly (1st of month, 03:30 SGT) |
| **Unique Constraint** | (name, poi_type) |

#### Admin Endpoint

```bash
POST http://localhost:8000/admin/ingestion/trigger?dataset=pois
```

---

### 5. data.gov.sg - HDB Existing Building (Postal Codes)

#### Status

⚠️ **Planned - To be Implemented in PR5.1**

#### API Information

| Property | Value |
|----------|-------|
| **Dataset Name** | HDB Existing Building |
| **Dataset ID** | `d_16b157c52ed637edd6ba1232e026258d` |
| **Format** | GeoJSON |
| **Base URL** | `https://api-open.data.gov.sg/v1/public/api/datasets/{dataset_id}/poll-download` |
| **Full Endpoint** | `https://api-open.data.gov.sg/v1/public/api/datasets/d_16b157c52ed637edd6ba1232e026258d/poll-download` |
| **Authentication** | ❌ None required (public dataset) |
| **Rate Limits** | No documented limits |
| **Cost** | ✅ Free (Open Data Licence) |
| **Provider** | Housing & Development Board (HDB) via GovTech |
| **Use Case** | Enable postal code → block lookup for Fair Value UI (PR5.1) |
| **Created** | 31 Jul 2023 |

#### Why This Source?

**Optimal for Postal Codes:**
- ✅ **Complete coverage** - All HDB blocks with postal codes
- ✅ **Authoritative source** - Direct from HDB
- ✅ **Structured mapping** - Block number → postal code
- ✅ **No rate limits** - Single dataset download
- ✅ **No authentication** - Public access
- ✅ **Efficient** - One API call vs 9,675+ geocoding calls

**Better than OneMap Alternative:**
- OneMap geocoding API does include postal codes (`POSTAL` field)
- But requires 9,675 API calls with rate limits (250/token)
- HDB Existing Building GeoJSON is purpose-built for this use case

#### Data Schema

**Source Format (GeoJSON):**
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Polygon",
        "coordinates": [...]
      },
      "properties": {
        "blk_no": "514",
        "road_name": "BEDOK NORTH AVENUE 2",
        "postal": "650514",
        "address": "514 BEDOK NORTH AVENUE 2"
      }
    }
  ]
}
```

**Supabase Table:** `blocks` (postal_code enrichment)

| Source Field | Database Column | Type | Description |
|--------------|----------------|------|-------------|
| `properties.postal` | `postal_code` | String(10) | 6-digit Singapore postal code |
| `properties.blk_no` | `block` | String(50) | Block number (for matching) |
| `properties.road_name` | `street` | String(255) | Street name (for matching) |

**Derived Field:**
| Database Column | Derivation | Description |
|----------------|------------|-------------|
| `postal_sector` | `postal_code[:2]` | First 2 digits for sector-based searches |

#### Implementation Plan (PR5.1)

**Method:** Parse GeoJSON and match to existing blocks

1. **Download GeoJSON:**
   - Call poll-download endpoint
   - Extract download URL from response
   - Fetch GeoJSON data

2. **Parse Features:**
   - Extract block, street, postal code from each feature
   - Normalize street names for matching

3. **Match & Update:**
   - Match `blk_no` + `road_name` to `blocks.block` + `blocks.street`
   - Update `blocks.postal_code` where match found
   - Extract postal sector (first 2 digits)

4. **Handle Edge Cases:**
   - Multiple blocks per postal code (rare)
   - Blocks without postal codes
   - Postal code format validation

#### Postal Code Logic (PR5.1)

**Singapore HDB Postal Code System:**
- **6 digits** total (e.g., `650514`, `310021`)
- **First 2 digits** = Postal sector/district
- **Last 3 digits** often match block number for HDB (e.g., `650514` → block `514`)

**Lookup Strategy:**
1. **Direct Match:** Search by exact postal code
2. **HDB Inference:** Use last 3 digits as block number hint
3. **Sector Fallback:** Search within same sector (first 2 digits)

**Example Postal Sectors:**
- `56####` - Ang Mo Kio
- `31####` - Toa Payoh  
- `74####` - Queenstown
- `65####` - Bedok

#### Benefits

Once implemented, postal codes will enable:

1. **User-Friendly Input:** Easier than remembering full address
2. **Reverse Lookup:** Postal code → block/street → Fair Value
3. **Mobile Optimization:** Numeric keyboard for 6-digit input
4. **Data Integration:** Match with other postal code datasets
5. **Validation:** Cross-reference with Singapore postal system

#### Estimated Implementation Effort

- **Code Changes:** 2-3 hours (new ingestion script)
- **Testing:** 1-2 hours (validation, edge cases)
- **Verification:** Check postal codes match Singapore format
- **Estimated Records:** ~9,675 blocks to enrich

#### Admin Endpoint (Future)

Once implemented in PR5.1:

```bash
POST http://localhost:8000/admin/ingestion/trigger?dataset=hdb_postal_codes
```

#### Alternative: Capture from OneMap During Geocoding

**Future enhancement** for `hdb_blocks.py`:

```python
# During geocoding, also capture postal code
response = onemap_client.search(address)
if response["found"] > 0:
    result = response["results"][0]
    latitude = result["LATITUDE"]
    longitude = result["LONGITUDE"]
    postal_code = result.get("POSTAL")  # Add this
```

**Pros:**
- No additional API calls
- Automatically updated during weekly geocoding
- Verifies postal codes from authoritative source

**Cons:**
- Still requires one-time backfill from HDB GeoJSON
- Postal codes only for newly geocoded blocks

**Recommendation:** Use HDB GeoJSON for initial population, then capture from OneMap for ongoing updates.

---

## Derived Data

### Block-POI Distance Calculations

#### Overview

**Source:** Derived from `blocks` + `pois` tables using Haversine distance calculation

**Supabase Table:** `block_pois` (junction table)

#### Algorithm

**Haversine Formula** (great-circle distance):

```python
def calculate_haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371000  # Earth radius in meters
    
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_phi / 2) ** 2 +
         math.cos(phi1) * math.cos(phi2) * 
         math.sin(delta_lambda / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c
```

**Threshold:** 2,000 meters (2km radius)

#### Data Schema

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `block_id` | Foreign Key | Reference to `blocks.id` | Required |
| `poi_id` | Foreign Key | Reference to `pois.id` | Required |
| `distance_m` | Numeric(10,2) | Distance in meters | Must be ≥ 0, ≤ 2000 |
| `created_at` | DateTime | Relationship creation timestamp | Auto |

**Unique Constraint:** (block_id, poi_id)

#### Ingestion Status

✅ **Active and Current**

| Metric | Value |
|--------|-------|
| **Latest Ingestion** | 2026-01-13 15:15 SGT |
| **Relationships Created** | 635,259 |
| **Blocks Covered** | 9,675 (100%) |
| **Orphaned Blocks** | 0 |
| **Avg POIs per Block** | 65.7 |
| **Schedule** | After POI ingestion |
| **Processing Time** | ~25-30 minutes |

#### Distance Statistics

| Metric | Value |
|--------|-------|
| **Min Distance** | 0.0m (POI at same location) |
| **Max Distance** | 2,000.0m (threshold) |
| **Average Distance** | 1,246.23m |

#### POI Type Distribution

| POI Type | Total Links | % of Total | Avg per Block |
|----------|-------------|------------|---------------|
| MRT | 191,537 | 30.2% | 19.8 |
| Schools | 149,137 | 23.5% | 15.4 |
| Clinics | 111,333 | 17.5% | 11.5 |
| Malls | 74,614 | 11.7% | 7.7 |
| Hawkers | 42,096 | 6.6% | 4.4 |
| Parks | 26,648 | 4.2% | 2.8 |
| LRT | 25,527 | 4.0% | 2.6 |
| Supermarkets | 14,367 | 2.3% | 1.5 |

#### Optimization

**Performance:**
- Pre-calculated and stored (not computed on-demand)
- Bounding box optimization reduces calculations
- Batch processing: 100 blocks per commit
- Progress logging every 100 blocks

**Upsert Strategy:**
- Replaces all relationships on each run
- Uses PostgreSQL `INSERT ... ON CONFLICT` for efficiency

#### Admin Endpoint

```bash
POST http://localhost:8000/admin/ingestion/trigger?dataset=block_pois
```

**Parameters:**
- `max_distance_m` (default: 2000) - Maximum distance threshold
- `batch_size` (default: 100) - Blocks per batch

---

## API Authentication & Rate Limiting

### data.gov.sg APIs

#### Authentication
- **Required:** ❌ None (public access)
- **API Key:** Not required
- **Rate Limits:** No documented limits

#### Rate Limiting Implementation

**Configuration:**
```bash
# Conservative default: 1 request per second
DATA_GOV_SG_REQUESTS_PER_MINUTE=60

# Optional: Limit records for testing
INGESTION_MAX_RECORDS=1000  # 0 = unlimited
```

**Implementation Details:**
- Automatic delay calculation: `60 / requests_per_minute` seconds
- Sleep between paginated requests
- Pagination: 1,000 records per page
- Early termination if `INGESTION_MAX_RECORDS` reached

**Performance Estimates:**
- **Full ingestion (222K):** ~4 minutes at 60 req/min
- **Testing mode (1K):** ~20 seconds
- **Conservative but safe:** Prevents API blocking

### OneMap API

#### Authentication

**Registration Required:**
1. Create account at [onemap.gov.sg/apidocs](https://www.onemap.gov.sg/apidocs/)
2. Register application to get credentials (email + password)
3. Generate JWT token via POST to auth endpoint

**Token Management:**
```python
# Token has 3-day TTL
{
  "access_token": "eyJ...",
  "expiry_timestamp": "1641234567890"
}
```

**Auto-Refresh Logic:**
- Token refresh after 240 requests (250 limit with safety margin)
- Automatic re-authentication on 401 errors
- Token cached for 3-day duration

#### Rate Limiting Implementation

**Strict Guardrails:**

| Guardrail | Value | Reason |
|-----------|-------|--------|
| **Token Session Limit** | 250 requests | OneMap API hard limit |
| **Token Refresh Trigger** | 240 requests | 10-request safety margin |
| **Batch Pause** | 2 seconds every 100 requests | Prevent rapid-fire requests |
| **Retry Attempts** | 2 per address | Handle transient failures |
| **Graceful Failure** | Return `null` coordinates | Partial data > no data |

**Configuration:**
```bash
ONEMAP_EMAIL=your_registered_email@example.com
ONEMAP_PASSWORD=your_password
ONEMAP_API_URL=https://www.onemap.gov.sg/api/common/elastic/search
ONEMAP_AUTH_URL=https://www.onemap.gov.sg/api/auth/post/getToken
```

**Processing Time:**
- 9,675 blocks ÷ 250/token ≈ 39 token refreshes
- 2-second pauses + token refresh overhead
- **Total:** ~5-10 minutes for full geocoding

### Retry Logic (All APIs)

**Configuration:**
```bash
INGESTION_RETRY_COUNT=3
INGESTION_RETRY_DELAY_SECONDS=5
```

**Implementation:**
- Exponential backoff: `delay * (2 ** attempt)`
- Retries on: Network errors, HTTP 500+, timeouts
- Skips on: HTTP 400 (bad request), validation errors
- Logs all retries to `ingestion_runs.error_summary`

---

## Ingestion Architecture

### Scheduler Configuration

All ingestion jobs managed by **APScheduler** (`src/resalelens/scheduler.py`):

| Dataset | Frequency | Schedule | Timezone | Duration Est. | Dependencies |
|---------|-----------|----------|----------|---------------|--------------|
| **HDB Transactions** | Weekly | Sundays 03:00 | SGT | ~4 min | None |
| **HDB Blocks** | Weekly | Sundays 03:15 | SGT | ~5-10 min | None |
| **POIs** | Monthly | 1st, 03:30 | SGT | ~3 min | None |
| **Block-POIs** | Monthly | 1st, 03:45 | SGT | ~25-30 min | Requires POIs |

**Scheduler Settings:**
- `max_instances=1` - Prevents concurrent runs
- `replace_existing=True` - Updates on app restart
- `misfire_grace_time=3600` - 1-hour grace period

### Batch Processing

**Transactions:**
- Commit after each 1,000-record page
- Progress logging every page
- Prevents memory overflow

**Blocks:**
- Commit every 100 blocks
- Progress logging every 100 blocks
- Token refresh every 240 geocoding requests

**POIs:**
- Commit after each search category batch
- Duplicate detection: Skip existing (name, poi_type)
- Progress logging per category

**Block-POIs:**
- Batch commit every 100 blocks
- Bounding box optimization
- Progress logging every 100 blocks

### Ingestion Run Tracking

**Supabase Table:** `ingestion_runs`

All ingestion attempts logged with:

| Field | Type | Description |
|-------|------|-------------|
| `dataset_name` | String | Dataset identifier |
| `started_at` | DateTime | When ingestion began |
| `completed_at` | DateTime | When ingestion finished |
| `status` | Enum | `in_progress`, `success`, `failed` |
| `rows_processed` | Integer | Number of records processed |
| `error_summary` | Text | Error details if failed |

**Recent Run History:**
```
✅ block_pois_distances: 635,259 rows - 2026-01-13 15:15
✅ onemap_pois: 1,916 rows - 2026-01-13 15:09
✅ hdb_blocks: 9,676 rows - 2026-01-13 14:06
✅ hdb_transactions: 222,955 rows - 2026-01-13 13:58
```

### Production Database Protection

**Guardrails Module** (`src/resalelens/ingestion/guardrails.py`):

1. **Environment Validation:**
   - Checks for placeholder values in `.env`
   - Warns if critical config missing
   - Blocks ingestion if invalid

2. **Production Warning:**
   - Detects Supabase production database
   - Requires user confirmation for manual triggers
   - Shows before/after state preview

3. **State Tracking:**
   - Captures row counts before ingestion
   - Shows delta after completion
   - Audit trail for all changes

---

## Data Quality & Validation

### Validation Rules

#### Transactions Table

**Required Fields:**
- `date`, `block`, `street`, `flat_type`, `storey_range`, `floor_area_sqm`, `price`, `lease_commence_date`, `town`, `flat_model`

**Constraints:**
- ✅ `floor_area_sqm > 0`
- ✅ `price > 0`
- ✅ `latitude` between -90 and 90
- ✅ `longitude` between -180 and 180
- ✅ Unique: (block, street, flat_type, date, storey_range, floor_area_sqm)

#### Blocks Table

**Required Fields:**
- `block`, `street`, `town`

**Constraints:**
- ✅ `latitude` between -90 and 90 (if not null)
- ✅ `longitude` between -180 and 180 (if not null)
- ✅ `lease_commence_year >= 1960` (if not null)
- ✅ Unique: (block, street)

#### POIs Table

**Required Fields:**
- `name`, `poi_type`, `latitude`, `longitude`

**Constraints:**
- ✅ `poi_type` must be valid enum value
- ✅ `latitude` and `longitude` required (not null)
- ✅ Coordinates within valid ranges
- ✅ Unique: (name, poi_type)

#### Block-POIs Table

**Constraints:**
- ✅ `distance_m >= 0`
- ✅ `distance_m <= 2000` (threshold)
- ✅ Valid foreign keys to `blocks` and `pois`
- ✅ Unique: (block_id, poi_id)

### Error Handling Strategy

**Philosophy:** Partial data is better than no data

**Implementation:**
1. **Skip Invalid Records:** Continue ingestion, log errors
2. **Graceful Degradation:** Set nullable fields to `null` on failure
3. **Retry Logic:** 3 attempts with exponential backoff
4. **Error Logging:** All errors saved to `ingestion_runs.error_summary`
5. **Progress Preservation:** Batch commits ensure partial success

**Example:**
- If 1,000 transactions fetched, 998 valid, 2 invalid:
  - Insert 998 valid records
  - Log 2 validation errors
  - Mark run as `success` with error summary
  - Continue to next batch

---

## Environment Configuration

### Required Variables

```bash
# Database (Supabase Production)
DATABASE_URL=postgresql://user:password@host:port/database

# data.gov.sg API
DATA_GOV_SG_API_URL=https://data.gov.sg/api/action/datastore_search
DATA_GOV_SG_RESOURCE_ID=d_8b84c4ee58e3cfc0ece0d773c8ca6abc
DATA_GOV_SG_PROPERTY_RESOURCE_ID=d_38fdbf555b3be2628cb8f1c90524b5e9

# OneMap API
ONEMAP_API_URL=https://www.onemap.gov.sg/api/common/elastic/search
ONEMAP_AUTH_URL=https://www.onemap.gov.sg/api/auth/post/getToken
ONEMAP_EMAIL=your_registered_email@example.com
ONEMAP_PASSWORD=your_password

# Rate Limiting
DATA_GOV_SG_REQUESTS_PER_MINUTE=60  # 1 req/sec
INGESTION_MAX_RECORDS=0              # 0 = unlimited

# Retry Configuration
INGESTION_RETRY_COUNT=3
INGESTION_RETRY_DELAY_SECONDS=5
```

### Testing Configuration

For local testing with limited data:

```bash
# Limit records ingested
INGESTION_MAX_RECORDS=1000

# Faster rate for local testing
DATA_GOV_SG_REQUESTS_PER_MINUTE=120  # 2 req/sec
```

---

## Monitoring & Observability

### Admin Endpoints

All datasets can be manually triggered:

```bash
# HDB Transactions
POST /admin/ingestion/trigger?dataset=hdb_transactions

# HDB Blocks (includes geocoding)
POST /admin/ingestion/trigger?dataset=hdb_blocks

# HDB Property Information
POST /admin/ingestion/trigger?dataset=hdb_property_info

# POIs
POST /admin/ingestion/trigger?dataset=pois

# Block-POI Distances
POST /admin/ingestion/trigger?dataset=block_pois
```

### Ingestion Logs

**Console Output Shows:**
- Batch progress (e.g., "Processed 5000/222835")
- Rate limiting pauses
- Geocoding successes/failures
- Token refresh events
- State deltas (before/after counts)

**Database Logs:**
- Query `ingestion_runs` table for history
- Filter by `dataset_name`, `status`, `started_at`
- Check `error_summary` for failure details

### Data Quality Checks

**Verification Script:** `scripts/verify_block_pois.py`

Runs comprehensive checks:
- Total record counts
- Coverage statistics (blocks with/without POIs)
- Distance statistics (min/max/avg)
- POI type distribution
- Orphaned block analysis
- Sample data inspection

**Example Output:**
```
Blocks coverage: 9675/9675 (100.0%)
Orphaned blocks (0 POIs within 2km): 0
Avg POIs per covered block: 65.7

POI Type Distribution (Linked):
  MRT: 191,537 links
  school: 149,137 links
  clinic: 111,333 links
```

---

## Attribution & Licensing

### data.gov.sg

- **Provider:** Singapore Government Technology Agency (GovTech)
- **License:** [Singapore Open Data License](https://data.gov.sg/open-data-licence)
- **Attribution Required:** ✅ Yes
- **Attribution Text:** "Data from data.gov.sg"
- **Website:** [data.gov.sg](https://data.gov.sg)

**Display Attribution:**
- Footer of all pages showing HDB data
- Data Status page
- API documentation

### OneMap

- **Provider:** Singapore Land Authority (SLA)
- **License:** [OneMap API Terms of Service](https://www.onemap.gov.sg/legal/opendatalicence)
- **Attribution Required:** ✅ Yes
- **Attribution Text:** "Map data © contributors, Singapore Land Authority"
- **Website:** [onemap.gov.sg](https://www.onemap.gov.sg)

**Display Attribution:**
- Any page showing map data
- Pages displaying POI information
- Footer of Block X-Ray page

---

## References

### Official Documentation

- **data.gov.sg Developer Portal:** [data.gov.sg/developer](https://data.gov.sg/developer)
- **OneMap API Docs:** [onemap.gov.sg/apidocs](https://www.onemap.gov.sg/apidocs/)
- **Singapore Open Data License:** [data.gov.sg/open-data-licence](https://data.gov.sg/open-data-licence)

### Internal Documentation

- **API Validation Report:** [docs/decisions/PR2_API_VALIDATION.md](../decisions/PR2_API_VALIDATION.md)
- **Rate Limiting Guardrails:** [docs/decisions/PR2_RATE_LIMITING_GUARDRAILS.md](../decisions/PR2_RATE_LIMITING_GUARDRAILS.md)
- **Database Schema:** [docs/plans/PR1_DATABASE_SCHEMA.md](../plans/PR1_DATABASE_SCHEMA.md)
- **HDB Data Ingestion Plan:** [docs/plans/PR2_DATA_INGESTION_HDB.md](../plans/PR2_DATA_INGESTION_HDB.md)
- **POI Ingestion Plan:** [docs/plans/PR3_DATA_INGESTION_POIS_MRT.md](../plans/PR3_DATA_INGESTION_POIS_MRT.md)

### Implementation Files

- **Ingestion Modules:** `src/resalelens/ingestion/`
  - `hdb_transactions.py` - HDB transaction ingestion
  - `hdb_blocks.py` - Block geocoding
  - `hdb_property_info.py` - Property information enrichment
  - `pois.py` - POI discovery and ingestion
  - `block_pois.py` - Distance calculation
  - `utils.py` - Shared utilities
  - `guardrails.py` - Safety checks

- **Scheduler:** `src/resalelens/scheduler.py`
- **Admin Router:** `src/resalelens/routers/admin.py`
- **Models:** `src/resalelens/models.py`

### Related Decisions

- **Data Validation Strategy:** [docs/decisions/DATA_VALIDATION_STRATEGY.md](../decisions/DATA_VALIDATION_STRATEGY.md)
- **Database Schema Normalization:** [docs/plans/PR1.3_DATABASE_SCHEMA_NORMALIZATION.md](../plans/PR1.3_DATABASE_SCHEMA_NORMALIZATION.md)

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-14 | Initial official reference documentation |

---

**Document Status:** ✅ Official Reference  
**Maintained By:** ResaleLens Development Team  
**Review Cycle:** Quarterly or after major API changes
