# Feature Plan: PR5.1 - Postal Code Input for Fair Value

## 0) Assumptions (max 3)
- PR5 (Fair Value UI with block + street input) is already implemented and working
- HDB Existing Building GeoJSON dataset from data.gov.sg is available and contains postal codes mapped to block numbers
- Users find postal codes easier to remember/enter than full block number + street name combinations

## 1) Clarifying Questions (only if blocking)
- None blocking - this is a straightforward UX enhancement

## 2) Feature Summary
- **Goal**: Allow users to input just a postal code instead of block number + street name for Fair Value lookups, making the form simpler and faster to use.
- **User Story**: As a HDB owner/buyer, I want to enter just my postal code (e.g., "650514") so that I can get Fair Value faster without needing to remember the exact block number and street name.
- **Acceptance Criteria** (5-10 bullets):
  - [ ] Postal code dataset from data.gov.sg is ingested into database
  - [ ] Blocks table is enriched with postal codes
  - [ ] Postal sector (first 2 digits) extracted and indexed
  - [ ] Fair Value form accepts postal code as alternative input  
  - [ ] **Direct lookup**: Exact postal code match returns correct block
  - [ ] **HDB inference**: Last 3 digits infer block number (e.g., 650514 → 514)
  - [ ] **Sector fallback**: If exact match fails, search same sector for suggestions
  - [ ] Form validates postal code format (6 digits, HDB range)
  - [ ] Error message with nearby suggestions if postal code not found
  - [ ] Backwards compatible - existing block + street input still works
  - [ ] User can switch between postal code mode and manual mode
  - [ ] Mobile-friendly postal code input (numeric keyboard)
  - [ ] Tests cover exact match, inference, and sector fallback
- **Non-goals** (explicit):
  - No autocomplete or typeahead for postal codes (future enhancement)
  - No bulk Fair Value lookups (single postal code only)
  - No integration with SingPost API (use static dataset only)

## 3) Approach Overview
- **Proposed UX** (high-level):
  - Add "Enter Postal Code" tab/toggle above existing form
  - When postal code mode active: Show single 6-digit input field
  - On postal code entry: Auto-lookup and populate block + street, then proceed to Fair Value
  - Fallback to manual entry if postal code not found
  - Keep existing block + street inputs as alternative method
  
- **Proposed API** (high-level):
  - New ingestion: `POST /admin/ingestion/trigger?dataset=hdb_postal_codes`
  - Enrichment: Update existing blocks with postal codes from GeoJSON
  - Lookup endpoint: `GET /api/block-lookup?postal_code={code}` returns block + street
  - Fair Value endpoint unchanged - still accepts block + street

- **Proposed Data Changes** (high-level):
  - Blocks table: `postal_code` column already exists, populate it
  - Add index on `postal_code` for fast lookups
  - New ingestion script: `src/resalelens/ingestion/hdb_postal_codes.py`
  
- **Auth/AuthZ Rules** (if any):
  - Block lookup endpoint is public (no auth required)
  - Postal code ingestion requires admin access (same as other ingestion)

## 4) PR Plan
- **PR Title**: PR5.1 - Add Postal Code Input for Fair Value
- **Branch Name**: `feature/pr5.1-postal-code-input`
- **Scope (in)**:
  - HDB postal code ingestion from data.gov.sg GeoJSON
  - Postal code enrichment for blocks table
  - Block lookup API endpoint
  - UI toggle between postal code and manual entry
  - Form validation and error handling
  - Unit and integration tests
  
- **Out of Scope (explicit)**:
  - Postal code autocomplete/typeahead
  - Reverse geocoding (lat/lng to postal code)
  - Address standardization
  - Postal code history/changes over time
  - Non-HDB postal codes
  
- **Key Changes by Layer**:
  - **Frontend**:
    - Add postal code input tab/toggle in `templates/index.html`
    - Add client-side validation for 6-digit format
    - JavaScript to auto-lookup block + street on postal code entry
    - Loading state while fetching block details
    - Error message if postal code not found
    - Update CSS for tabbed interface
    
  - **Backend**:
    - New ingestion: `src/resalelens/ingestion/hdb_postal_codes.py`
    - Fetch GeoJSON from data.gov.sg API
    - Parse features and extract block + postal code mappings
    - **Extract postal code sector** (first 2 digits) for sector-based lookups
    - Update blocks table where matches found
    - New endpoint: `GET /api/block-lookup?postal_code={code}`
    - Returns `{block, street, town, postal_code}` or 404
    - **Leverage postal code logic**:
      - **Direct match**: If exact 6-digit postal code found, return block immediately
      - **HDB block inference**: For HDB postal codes, last 3 digits often match block number (e.g., 650514 → block 514)
      - **Sector fallback**: If exact match fails, search within same sector (first 2 digits) for similar blocks
      - **Nearby suggestions**: Return blocks in same sector if exact match not found
    
  - **Data**:
    - Populate `postal_code` column in blocks table
    - Add `postal_sector` computed column (first 2 digits)
    - Add indexes: 
      - `CREATE INDEX idx_blocks_postal_code ON blocks(postal_code)`
      - `CREATE INDEX idx_blocks_postal_sector ON blocks(postal_sector)`
    - Handle duplicates (some postal codes map to multiple blocks)
    
  - **Infra/Config**:
    - No new environment variables needed
    - GeoJSON endpoint is public (no API key required)
    
- **Edge Cases to Handle**:
  - **Postal code maps to multiple blocks** (rare) - return all matches, let user choose
  - **Postal code not in dataset** - use HDB block inference (last 3 digits) + sector search
  - **Invalid postal code format** - client-side validation before API call
  - **Old postal codes that changed** - accept limitation (use current data only)
  - **Blocks without postal codes** - manual entry still available
  - **Non-HDB postal codes** - gracefully reject (e.g., 01xxxx for CBD)
  - **Sector-based fuzzy match**: If 650514 not found but 650515 exists in same sector, suggest it
  
- **Migration/Compatibility Notes**:
  - No breaking changes - postal code input is additive
  - Existing Fair Value API unchanged
  - Existing block + street flow remains default
  - No database migrations needed (`postal_code` column exists)

## 5) Testing & Verification
- **Automated Tests**:
  - **Unit**:
    - Test postal code parsing from GeoJSON
    - Test postal code validation (6 digits, numeric)
    - Test block lookup logic
    - Test duplicate postal code handling
  - **Integration**:
    - Test postal code ingestion end-to-end
    - Test `GET /api/block-lookup` with valid/invalid codes
    - Test Fair Value submission via postal code
    - Test blocks table enrichment
  - **E2E** (only if needed):
    - Not needed - manual verification sufficient
    
- **Manual Verification Checklist**:
  - [ ] Run postal code ingestion → blocks enriched with postal codes
  - [ ] Query blocks table → verify postal codes populated
  - [ ] Enter postal code "650514" → auto-populates block "514"
  - [ ] Submit Fair Value with postal code → returns results
  - [ ] Enter invalid postal code "999999" → shows error message
  - [ ] Enter malformed postal code "12345a" → validation error
  - [ ] Toggle to manual entry → block + street inputs work
  - [ ] Mobile view → numeric keyboard appears for postal code
  - [ ] Performance → lookup < 100ms
  
- **Commands to Run**:
  - **Install**: `uv sync` (no new dependencies)
  - **Dev**: `uv run uvicorn src.resalelens.main:app --reload`
  - **Ingest**: `curl -X POST "http://localhost:8000/admin/ingestion/trigger?dataset=hdb_postal_codes"`
  - **Test**: `uv run pytest tests/test_postal_code_lookup.py -v`
  - **Lint**: `uv run ruff check src/resalelens/ingestion/hdb_postal_codes.py`

## 6) Rollback Plan
- Remove postal code input UI (revert `index.html` changes)
- Drop postal code index if performance issues
- Fair Value still works with manual block + street entry
- No data deletion needed - postal codes are additive metadata

## 7) Follow-ups (optional)
- **PR5.2**: Postal code autocomplete with typeahead
- **PR5.3**: Suggest nearby postal codes if exact match not found
- **PR5.4**: Allow users to save favorite postal codes
- **Future**: Integrate with SingPost real-time postal code validation API
