# Faster Postal Code Ingestion Alternatives

## Current Problem
- **13,352 OneMap API calls** (1 per postal code)
- Rate limiting: ~1-2 seconds per call
- **Total time: 4-7 hours** ⏰ TOO SLOW!

## Alternative Approaches (MUCH FASTER)

### Option 1: Use GeoJSON Street Name (FASTEST - if available)
**Speed: 2-3 minutes**
- The GeoJSON might already have street names in other fields
- Check if `STREET_NAME`, `ROAD_NAME`, or `ADDRESS` fields exist
- No API calls needed!

### Option 2: Bulk Reverse Geocoding (FAST)
**Speed: 10-15 minutes**
- GeoJSON has coordinates for each building
- Use OneMap reverse geocoding API (coordinates → address)
- Can batch multiple requests
- Fewer API calls than current approach

### Option 3: Direct Block Number Matching (INSTANT)
**Speed: Seconds**
- Use GeoJSON's `BLK_NO` field directly
- Match against database blocks by town + block number only
- No street name needed
- Accept lower accuracy for speed

### Option 4: Pre-built Postal Code Database (INSTANT)
**Speed: Seconds**
- Check if data.gov.sg has a pre-built postal code → address mapping
- Download once, match locally
- No API calls during ingestion

### Option 5: Accept Current Coverage (INSTANT)
**Speed: 0 seconds**
- We already have 46% coverage (4,448 blocks)
- This covers many active blocks
- Good enough for MVP
- Improve later with monthly scheduled updates

## Recommendation
Let me check **Option 1** first (GeoJSON fields), then **Option 4** (pre-built DB), then **Option 3** (direct matching).
