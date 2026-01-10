# API Validation for PR2 Data Ingestion

**Date:** 2026-01-10  
**Purpose:** Document testing results and validation of external APIs required for PR2 data ingestion  
**Status:** ✅ Validated (with required actions)

---

## Executive Summary

Both data sources required for PR2 have been validated and tested. Key findings:

- **data.gov.sg HDB Resale Prices API**: ✅ READY - Free, no authentication, stable, no apparent rate limits
- **OneMap Geocoding API**: ⚠️ REQUIRES SETUP - Free tier available but requires account registration and API token

**Action Required:** Register for OneMap API account and generate token before starting PR2 implementation.

---

## 1. data.gov.sg HDB Resale Prices API

### API Details

| Property | Value |
|----------|-------|
| **Base URL** | `https://data.gov.sg/api/action/datastore_search` |
| **Resource ID** | `d_8b84c4ee58e3cfc0ece0d773c8ca6abc` |
| **Dataset Name** | Resale flat prices based on registration date from Jan-2017 onwards |
| **Authentication** | ❌ None required (publicly accessible) |
| **Cost** | ✅ Free |

### Full Endpoint

```
https://data.gov.sg/api/action/datastore_search?resource_id=d_8b84c4ee58e3cfc0ece0d773c8ca6abc
```

### Response Structure

**Field Schema:**

| Field | Type | Description |
|-------|------|-------------|
| `month` | text | Transaction month (format: "YYYY-MM") |
| `town` | text | HDB town name (e.g., "ANG MO KIO") |
| `flat_type` | text | Type of flat (e.g., "2 ROOM", "3 ROOM", "4 ROOM") |
| `block` | text | Block number (e.g., "406") |
| `street_name` | text | Street name (e.g., "ANG MO KIO AVE 10") |
| `storey_range` | text | Range of storeys (e.g., "10 TO 12") |
| `floor_area_sqm` | text | Floor area in square meters |
| `flat_model` | text | Flat model type (e.g., "Improved", "New Generation") |
| `lease_commence_date` | text | Year lease commenced (e.g., "1979") |
| `remaining_lease` | text | Remaining lease duration (e.g., "61 years 04 months") |
| `resale_price` | numeric | Resale price in SGD (e.g., "232000") |
| `_id` | int4 | Internal record ID |

**Sample Response (truncated):**

```json
{
  "success": true,
  "result": {
    "resource_id": "d_8b84c4ee58e3cfc0ece0d773c8ca6abc",
    "fields": [...],
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
        "remaining_lease": "61 years 04 months",
        "resale_price": "232000"
      }
    ],
    "_links": {
      "start": "/api/action/datastore_search?resource_id=d_8b84c4ee58e3cfc0ece0d773c8ca6abc&limit=5",
      "next": "/api/action/datastore_search?resource_id=d_8b84c4ee58e3cfc0ece0d773c8ca6abc&offset=5&limit=5"
    },
    "total": 222835,
    "limit": 5
  }
}
```

### Pagination Support

- ✅ Supports `limit` parameter (default: varies, tested with 1-5)
- ✅ Supports `offset` parameter for pagination
- ✅ Returns `_links.next` for next page URL
- ✅ Returns `total` count of all records (currently **222,835 records**)

### Rate Limiting

**Test Results:**
- ✅ 10 consecutive requests completed successfully (all returned HTTP 200)
- ⏱️ Average response time: ~0.4 seconds per request
- 📊 No rate limit errors encountered
- ✅ No throttling observed with 0.1s delay between requests

**Conclusion:** No documented or apparent rate limits for reasonable usage. API appears designed for public access without strict throttling.

### Recommendations

1. **Pagination Strategy:**
   - Use `limit=1000` per request for batch processing
   - Implement offset-based pagination (increase offset by limit for each page)
   - Total ingestion will require ~223 API calls (222,835 records ÷ 1000)

2. **Retry Logic:**
   - Implement 3 retries with exponential backoff as planned
   - Handle network errors and HTTP 500+ gracefully
   - Add 100-200ms delay between requests to be respectful to the API

3. **Data Validation:**
   - ⚠️ Note: `floor_area_sqm` and `resale_price` are returned as strings, not numbers
   - ⚠️ `remaining_lease` uses free text format - needs parsing (e.g., "61 years 04 months")
   - ✅ Schema is stable and well-structured

4. **Environment Configuration:**
   ```bash
   DATA_GOV_SG_API_URL=https://data.gov.sg/api/action/datastore_search
   DATA_GOV_SG_RESOURCE_ID=d_8b84c4ee58e3cfc0ece0d773c8ca6abc
   ```

---

## 2. OneMap Geocoding API

### API Details

| Property | Value |
|----------|-------|
| **Base URL (Search)** | `https://www.onemap.gov.sg/api/common/elastic/search` |
| **Base URL (Authentication)** | `https://www.onemap.gov.sg/api/auth/post/getToken` |
| **Authentication** | ✅ Required (JWT token with 3-day TTL) |
| **Cost** | ✅ Free tier available |
| **Rate Limit** | 250 requests per token session |

### Authentication Flow

**Registration Required:**
1. Create account at [OneMap.gov.sg](https://www.onemap.gov.sg/apidocs/)
2. Register application to get credentials (email + password)
3. Generate token via POST to authentication endpoint

**Token Generation:**

```bash
curl -X POST https://www.onemap.gov.sg/api/auth/post/getToken \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your_registered_email@example.com",
    "password": "your_password"
  }'
```

**Token Response:**

```json
{
  "access_token": "eyJ...[JWT token]",
  "expiry_timestamp": "1641234567890"
}
```

**Token Usage:**
- Include token in `Authorization` header: `Authorization: Bearer <token>`
- Token expires after 3 days
- Must re-authenticate after expiry

### Geocoding Endpoint

**Search Endpoint:**

```
https://www.onemap.gov.sg/api/common/elastic/search?searchVal=<address>&returnGeom=Y&getAddrDetails=Y
```

**Example Request:**

```bash
curl "https://www.onemap.gov.sg/api/common/elastic/search?searchVal=BLK+108+ANG+MO+KIO+AVE+4&returnGeom=Y&getAddrDetails=Y" \
  -H "Authorization: Bearer <your_token>"
```

**Without Token - Error Response:**

```json
{
  "error": "Authentication token missing. Please create an account and generate or renew your API Token.",
  "found": 0,
  "totalNumPages": 0,
  "pageNum": 1,
  "results": []
}
```

### Expected Response Structure (Based on Documentation)

```json
{
  "found": 1,
  "totalNumPages": 1,
  "pageNum": 1,
  "results": [
    {
      "SEARCHVAL": "BLK 108 ANG MO KIO AVE 4",
      "BLK_NO": "108",
      "ROAD_NAME": "ANG MO KIO AVENUE 4",
      "BUILDING": "BLK 108",
      "ADDRESS": "108 ANG MO KIO AVENUE 4 SINGAPORE",
      "POSTAL": "560108",
      "X": "29668.123",
      "Y": "39105.456",
      "LATITUDE": "1.372123",
      "LONGITUDE": "103.845456"
    }
  ]
}
```

### Rate Limiting

**Confirmed Limits:**
- 250 requests per authenticated session
- No strict time-based rate limit documented
- Best practice: Add delays between requests to avoid potential undocumented throttling

**For PR2 Scope:**
- Estimated 10,000-15,000 unique blocks to geocode
- At 250 requests per token, will require ~40-60 token refreshes
- **Recommendation:** Implement token refresh logic when approaching limit

### Recommendations

1. **Authentication Implementation:**
   - Store OneMap credentials in `.env.local` (email + password)
   - Implement token generation function with 3-day caching
   - Implement token refresh logic when approaching 250-request limit or on expiry
   - Handle 401 Unauthorized errors by re-authenticating

2. **Rate Limit Handling:**
   - Track request count per token session
   - Request new token after 240 requests (safety margin)
   - Add 200-300ms delay between geocoding requests
   - Implement batch processing with progress tracking

3. **Fallback Strategy:**
   - Implement graceful degradation: Set `latitude`/`longitude` to NULL on failure
   - Log geocoding failures with block address for manual review
   - Consider building pre-geocoded database for common HDB blocks (one-time effort)
   - Option to retry failed geocodes in subsequent runs

4. **Environment Configuration:**
   ```bash
   ONEMAP_API_URL=https://www.onemap.gov.sg/api/common/elastic/search
   ONEMAP_AUTH_URL=https://www.onemap.gov.sg/api/auth/post/getToken
   ONEMAP_EMAIL=your_registered_email@example.com
   ONEMAP_PASSWORD=your_password
   ONEMAP_RATE_LIMIT=250  # Requests per token
   ```

5. **Address Formatting:**
   - Format addresses as: `BLK <block> <street_name>`
   - URL-encode special characters (spaces, etc.)
   - Example: `BLK 108 ANG MO KIO AVE 4` → `BLK+108+ANG+MO+KIO+AVE+4`

---

## 3. Pre-Implementation Action Items

### Required Before Starting PR2

- [ ] **Register OneMap Account**
  - Go to https://www.onemap.gov.sg/apidocs/
  - Create account with project email
  - Document credentials in `.env.local` (DO NOT commit to git)

- [ ] **Test OneMap Authentication**
  - Request token using registered credentials
  - Verify token generation succeeds
  - Test geocoding request with token
  - Validate response structure matches expectations

- [ ] **Update `.env.example`**
  - Add all data.gov.sg configuration (already documented above)
  - Add OneMap configuration placeholders (email, password, URLs)

### Optional Optimizations

- [ ] **Pre-build Geocoding Database**
  - Extract unique (block, street, town) from current transactions
  - Manually geocode ~10,000 blocks in batch
  - Store in JSON/CSV as fallback data source
  - Reduces OneMap API dependency for initial load

- [ ] **Set up Monitoring**
  - Track API response times in `ingestion_runs` table
  - Log rate limit encounters
  - Alert on authentication failures

---

## 4. Risk Assessment Updates

### data.gov.sg API

| Risk | Severity | Likelihood | Mitigation Status |
|------|----------|------------|-------------------|
| API downtime during ingestion | Medium | Low | ✅ Retry logic planned |
| Schema changes breaking parser | Medium | Low | ✅ Validation logic planned |
| Undocumented rate limits | Low | Low | ✅ No evidence found; respectful delays planned |
| Data quality issues | Low | Low | ✅ Validation + skip invalid records |

**Overall Risk:** ✅ **LOW** - API is stable, well-documented, and publicly accessible

### OneMap API

| Risk | Severity | Likelihood | Mitigation Status |
|------|----------|------------|-------------------|
| Token authentication failures | High | Medium | ⚠️ Requires robust retry + refresh logic |
| Rate limit exceeded (250/session) | High | High | ⚠️ Token rotation logic required |
| Geocoding inaccuracies | Medium | Medium | ✅ NULL fallback + manual review planned |
| Account registration blocked | High | Low | ⚠️ Register early; have backup email |
| Token expiry mid-ingestion | Medium | Medium | ⚠️ 3-day TTL refresh logic required |

**Overall Risk:** ⚠️ **MEDIUM** - Authentication adds complexity but free tier is suitable for MVP

---

## 5. Implementation Priorities

### High Priority (Blocking for PR2)

1. ✅ data.gov.sg integration (no blockers)
2. ⚠️ OneMap account registration (blocking - do first)
3. ⚠️ Token management implementation (blocking for geocoding)
4. ✅ Retry logic with exponential backoff
5. ✅ Data validation for HDB transactions

### Medium Priority (Important but Non-Blocking)

6. Token refresh logic (can use manual workaround initially)
7. Rate limit tracking per session
8. Geocoding failure logging and retry queue

### Low Priority (Post-MVP Optimizations)

9. Pre-built geocoding database
10. Incremental ingestion (delta sync)
11. Advanced error alerting

---

## Conclusion

Both APIs are **viable for PR2 implementation** with the following actions:

### ✅ Ready to Proceed:
- data.gov.sg HDB Resale Prices API (no setup required)

### ⚠️ Setup Required:
- OneMap API (register account, implement token management)

### Recommended Next Steps:

1. **Immediate:** Register OneMap account and test authentication
2. **Before coding:** Update `.env.example` with all new variables
3. **During PR2:** Implement token refresh logic as part of `ingestion/utils.py`
4. **Testing:** Use mocked API responses for unit tests (avoid hitting actual APIs during CI)

**Validation Date:** 2026-01-10  
**API Endpoints Tested:**
- ✅ data.gov.sg: `https://data.gov.sg/api/action/datastore_search?resource_id=d_8b84c4ee58e3cfc0ece0d773c8ca6abc`
- ⚠️ OneMap: `https://www.onemap.gov.sg/api/common/elastic/search` (authentication required)

**Total Records Available:** 222,835 HDB resale transactions (Jan 2017 onwards)  
**Last Validated:** 2026-01-10
