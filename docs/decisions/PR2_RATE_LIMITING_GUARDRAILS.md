# Decision: API Rate Limiting & Ingestion Guardrails

**Date:** 2026-01-10  
**Status:** ✅ Implemented  
**Context:** PR2 Data Ingestion Pipeline

---

## Context

The PR2 Data Ingestion Pipeline fetches data from two external APIs:
1. **data.gov.sg** - HDB resale transaction data (~222K records)
2. **OneMap** - Geocoding API for HDB block addresses (~10-15K addresses)

Without proper rate limiting and guardrails, our ingestion could:
- Overwhelm external APIs (leading to blocking/bans)
- Exceed API rate limits unintentionally
- Cause long-running processes that block development
- Risk data corruption on production databases

---

## Decision

Implement configurable rate limiting and safety guardrails for all data ingestion processes.

### 1. data.gov.sg API Rate Limiting

**Configuration:**
- `DATA_GOV_SG_REQUESTS_PER_MINUTE` (default: 60 = 1 request/second)
- `INGESTION_MAX_RECORDS` (default: 0 = unlimited, useful for testing)

**Implementation:**
- Automatic delay calculation: `60 / requests_per_minute`
- Sleep between paginated requests
- Early termination if max records reached

**Reasoning:**
- Conservative 1 req/sec default prevents API blocking
- Configurable for faster ingestion if API allows
- Max records limit enables safe testing without full dataset

### 2. OneMap API Rate Limiting

**Built-in Safeguards:**
- Token refresh after 240 requests (250 limit with 10-request safety margin)
- 2-second pause every 100 geocoding requests
- Graceful failure: null coordinates if geocoding fails
- Retry logic: 2 attempts per address

**Reasoning:**
- OneMap has strict 250 requests/token limit
- Pauses prevent rapid-fire requests that might trigger limits
- Null fallback ensures partial data is better than no data

### 3. Batch Processing

**Implementation:**
- **Transactions**: Commit after each 1,000-record page
- **Blocks**: Commit every 100 blocks
- Progress logging every batch

**Reasoning:**
- Prevents memory overflow on large datasets
- Enables resumable ingestion (committed data persists)
- Progress visibility for monitoring

### 4. Retry Logic

**Configuration:**
- `INGESTION_RETRY_COUNT` (default: 3)
- `INGESTION_RETRY_DELAY_SECONDS` (default: 5)
- Exponential backoff on failures

**Reasoning:**
- Handles transient network errors
- Prevents immediate failure on temporary API issues
- Exponential backoff respects rate limits

### 5. Production Database Protection

**Guardrails Module Features:**
- Environment validation (checks for placeholder values)
- Production database warning (requires user confirmation)
- Pre/post ingestion state tracking (shows delta)

**Reasoning:**
- Prevents accidental production data modification
- Provides visibility into changes before they happen
- Audit trail for all ingestion runs

---

## Alternatives Considered

### 1. No Rate Limiting (Rejected)
**Pros:** Faster ingestion  
**Cons:** Risk of API blocking, unpredictable behavior  
**Verdict:** Too risky for external APIs we don't control

### 2. Fixed Delays Only (Rejected)
**Pros:** Simple implementation  
**Cons:** Not flexible, may be too slow or too fast  
**Verdict:** Configurable is better for different environments

### 3. Async/Queue-Based Ingestion (Deferred to Future)
**Pros:** Non-blocking, better scalability  
**Cons:** Complex implementation, overkill for MVP  
**Verdict:** Synchronous is sufficient for weekly scheduled jobs

---

## Implementation Details

### Environment Configuration (.env.local)
```bash
# Rate Limiting
DATA_GOV_SG_REQUESTS_PER_MINUTE=60  # Conservative: 1 req/sec
INGESTION_MAX_RECORDS=0              # 0 = unlimited

# Retry Configuration
INGESTION_RETRY_COUNT=3
INGESTION_RETRY_DELAY_SECONDS=5

# OneMap Token (no rate limit config needed - auto-managed)
ONEMAP_API_TOKEN=your-token-here
```

### Code Implementation
- **File:** `src/resalelens/ingestion/hdb_transactions.py`
  - Rate calculation: `60.0 / requests_per_minute`
  - Sleep: `time.sleep(delay_between_requests)`
  - Max records check after each batch

- **File:** `src/resalelens/ingestion/hdb_blocks.py`
  - Token refresh: Automatic at 240 requests
  - Pause: `time.sleep(2)` every 100 requests

- **File:** `src/resalelens/ingestion/guardrails.py`
  - Environment validation
  - Production warnings
  - State tracking

---

## Consequences

### Positive
✅ Protected from API rate limit violations  
✅ Configurable for different environments (dev/test/prod)  
✅ Safe testing with max records limit  
✅ Auditable with state tracking  
✅ Resumable with batch commits  

### Negative
⚠️ Slower full ingestion (~4 min for 222K records vs <1 min unlimited)  
⚠️ More configuration to manage  
⚠️ Requires understanding of rate limits for tuning  

### Mitigations
- Conservative defaults prevent issues out-of-box
- Documentation guides on tuning for performance
- Testing mode (`INGESTION_MAX_RECORDS`) for rapid iteration

---

## Performance Estimates

### Full Production Ingestion
- **Transactions (222K):** ~4 minutes at 60 req/min
- **Blocks (10-15K):** ~5-10 minutes with geocoding
- **Total:** ~15 minutes for full weekly refresh

### Testing Mode (10K records)
- **Transactions (10K):** ~20 seconds
- **Blocks (1K):** ~2 minutes
- **Total:** ~3 minutes for development testing

---

## Monitoring & Observability

### Ingestion Runs Table
All runs logged with:
- Dataset name
- Status (in_progress, success, failed)
- Rows processed
- Error summary
- Start/end timestamps

### Progress Logging
Console output shows:
- Batch progress (e.g., "Processed 5000/222835")
- Rate limiting pauses
- Geocoding successes/failures
- State deltas (before/after counts)

---

## Future Considerations

### Phase 2+ Improvements (Not in PR2)
- [ ] Incremental sync (delta updates only)
- [ ] Async/background job processing
- [ ] Admin UI with progress bars
- [ ] Automatic rate limit detection & adjustment
- [ ] Email alerts on ingestion failures

---

## References

- **data.gov.sg API**: https://data.gov.sg/api/action/datastore_search
- **OneMap API Docs**: https://www.onemap.gov.sg/apidocs/
- **PR2 Plan**: `docs/plans/PR2_DATA_INGESTION_HDB.md`
- **Implementation**: `src/resalelens/ingestion/`

---

## Related Decisions

- [PR2 API Validation](./PR2_API_VALIDATION.md) - OneMap API format fix
- [Environment Configuration](../.cursorrules) - .env.local standard

**Status: Implemented and Verified ✅**
