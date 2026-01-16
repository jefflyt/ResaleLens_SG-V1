# Epic Plan: PR9 - Postal Code UX Enhancements

## 1. Feature/Epic Summary

**Objective**:
Enhance the postal code input experience with autocomplete, nearby suggestions with map view, and favorite postal codes functionality to make Fair Value lookups faster and more intuitive for returning users.

**User Impact**:
- **Faster input**: Autocomplete reduces typing and errors
- **Better discovery**: Map view helps users find nearby properties when exact postal code is unknown
- **Convenience**: Favorite postal codes enable one-click access for frequently checked properties
- **Improved UX**: Visual map interface makes spatial relationships clearer

**Dependencies**:
- PR5.1 (Postal Code Input) - COMPLETED ✅
- Postal code database fully populated (100% coverage achieved)
- Block lookup API endpoint operational

**Assumptions**:
- Users frequently check the same postal codes (e.g., their own property, properties they're monitoring)
- Map visualization adds value for understanding neighborhood context
- Autocomplete performance is acceptable with 9,675 postal codes
- Users are comfortable with browser local storage for favorites

## 2. Complexity & Fit

**Classification**: Multi-PR

**Rationale**:
- Three distinct features with different complexity levels
- PR5.2 (Autocomplete) is frontend-heavy with minimal backend changes
- PR5.3 (Map view) requires new mapping library integration and geospatial queries
- PR5.4 (Favorites) needs client-side storage and UI state management
- Each feature provides standalone value and can be deployed independently
- Allows incremental rollout and user feedback between features

**Estimated PRs**: 3 PRs (one per feature enhancement)

## 3. Full-Stack Impact

**Frontend**:
- New autocomplete component with typeahead functionality
- Map integration (Leaflet.js or similar) for nearby suggestions
- Favorites UI (star/bookmark icons, favorites list)
- Local storage management for favorites
- New UI states (autocomplete dropdown, map overlay, favorites panel)

**Backend**:
- Postal code search/autocomplete API endpoint
- Geospatial query for nearby blocks (within radius)
- No new database tables (uses existing blocks table)
- Possible caching layer for autocomplete performance

**Data**:
- No schema changes required
- Leverage existing `postal_code`, `postal_sector`, `latitude`, `longitude` columns
- May add database indexes for geospatial queries

**Infra / Config**:
- No new environment variables
- May need CDN for map tiles (OpenStreetMap)
- Feature flags for gradual rollout (optional)

## 4. PR Roadmap

### PR 9.1: Postal Code Autocomplete with Typeahead

**Goal**:
Provide real-time autocomplete suggestions as users type postal codes, reducing input errors and speeding up the lookup process.

**Scope**:
- **In scope**:
  - Autocomplete dropdown for postal code input field
  - Backend API endpoint for postal code search
  - Debounced search (300ms delay)
  - Keyboard navigation (arrow keys, Enter, Escape)
  - Display format: "650514 - Block 514 Ang Mo Kio Ave 8"
  - Limit to 10 suggestions
  - Highlight matching characters
- **Out of scope**:
  - Map view (deferred to PR 9.2)
  - Favorites (deferred to PR 9.3)
  - Fuzzy matching (exact prefix match only)
  - Search by block number or street name

**Backend Changes**:
- **New API**: `GET /api/postal-codes/search?q={query}&limit=10`
  - Returns: `[{postal_code, block, street, town}]`
  - Query: Prefix match on postal_code
  - Limit: Max 10 results
  - Performance: Use `idx_blocks_postal_code` index
- **Caching**: Consider Redis/in-memory cache for frequent queries (optional)

**Frontend Changes**:
- **Component**: `PostalCodeAutocomplete.js` (or inline in existing form)
- **Features**:
  - Debounced input handler (300ms)
  - Dropdown with suggestions
  - Keyboard navigation (↑↓ arrows, Enter, Esc)
  - Click to select
  - Highlight matching prefix
- **CSS**: Dropdown styling, hover states, selected state
- **Accessibility**: ARIA labels, keyboard support

**Data Changes**:
- No schema changes
- Verify `idx_blocks_postal_code` index exists and is performant

**Infra / Config**:
- No changes required

**Testing**:
- **Unit tests**:
  - Debounce logic
  - Keyboard navigation handlers
  - API response parsing
- **Integration tests**:
  - `GET /api/postal-codes/search` with various queries
  - Empty results handling
  - Limit enforcement
- **Manual checks**:
  - Type "650" → see suggestions
  - Arrow key navigation works
  - Enter selects suggestion
  - Escape closes dropdown
  - Mobile: Dropdown doesn't obscure input

**Verification**:
- **Commands**:
  - Install: `uv sync`
  - Dev: `uv run uvicorn src.resalelens.main:app --reload`
  - Test: `uv run pytest tests/test_postal_autocomplete.py -v`
  - Lint: `uv run ruff check src/resalelens/routers/api.py`
- **Manual verification**:
  1. Open Fair Value page
  2. Click postal code tab
  3. Type "65" → dropdown appears with suggestions
  4. Use arrow keys → highlight changes
  5. Press Enter → postal code populated, dropdown closes
  6. Type "999" → "No results" message
  7. Click outside → dropdown closes

**Rollback Plan**:
- Remove autocomplete endpoint from API routes
- Revert frontend changes to postal code input
- No data changes to rollback

**Dependencies**:
- PR5.1 completed (postal code input exists)
- Postal code database populated

**Risks & Mitigations**:
- **Risk**: Autocomplete too slow with 9,675 records
  - **Mitigation**: Use database index, limit results to 10, add caching if needed
- **Risk**: Mobile keyboard covers dropdown
  - **Mitigation**: Position dropdown above input on mobile, test on real devices

---

### PR 9.2: Nearby Postal Code Suggestions with Map View

**Goal**:
When a postal code is not found, show nearby blocks on an interactive map to help users discover the correct postal code visually.

**Scope**:
- **In scope**:
  - Interactive map overlay (Leaflet.js)
  - Geospatial query for blocks within radius
  - Map markers for nearby blocks
  - Click marker → populate postal code
  - Zoom/pan controls
  - Show user's searched location (if lat/lng available)
  - Fallback to postal sector if exact postal code not found
- **Out of scope**:
  - Directions/routing
  - Street view integration
  - Custom map tiles (use OpenStreetMap)
  - Saved map preferences

**Backend Changes**:
- **New API**: `GET /api/blocks/nearby?postal_code={code}&radius=500`
  - Returns: `[{postal_code, block, street, town, latitude, longitude}]`
  - Logic:
    1. Try exact postal code match
    2. If not found, use postal sector to find center point
    3. Query blocks within radius (default 500m)
  - Use PostGIS or simple distance calculation
- **Geospatial query**:
  - Calculate distance using Haversine formula
  - Or use PostGIS `ST_Distance_Sphere` if available

**Frontend Changes**:
- **Library**: Leaflet.js (lightweight, open-source)
- **Component**: `NearbyBlocksMap.js`
- **Features**:
  - Map overlay (modal or inline)
  - Markers for each nearby block
  - Popup on marker click with block details
  - "Select" button in popup → populate form
  - Close button
- **CSS**: Map container, markers, popups
- **Responsive**: Full-screen on mobile

**Data Changes**:
- No schema changes
- Verify `latitude` and `longitude` columns are populated
- May add geospatial index if using PostGIS

**Infra / Config**:
- **Map tiles**: OpenStreetMap (free, no API key)
- **CDN**: Leaflet.js CSS/JS from CDN or npm

**Testing**:
- **Unit tests**:
  - Distance calculation function
  - Nearby blocks filtering logic
- **Integration tests**:
  - `GET /api/blocks/nearby` with various postal codes
  - Radius parameter handling
  - Empty results (e.g., postal code in non-HDB area)
- **Manual checks**:
  - Enter invalid postal code → map appears
  - Map shows nearby blocks
  - Click marker → popup shows details
  - Click "Select" → form populated, map closes
  - Mobile: Map is full-screen and usable

**Verification**:
- **Commands**:
  - Install: `uv sync` (adds Leaflet.js dependency)
  - Dev: `uv run uvicorn src.resalelens.main:app --reload`
  - Test: `uv run pytest tests/test_nearby_blocks.py -v`
  - Lint: `uv run ruff check src/resalelens/routers/api.py`
- **Manual verification**:
  1. Enter postal code "999999" (invalid)
  2. Click "Show nearby blocks" button
  3. Map overlay appears
  4. See markers for blocks in default sector
  5. Click marker → popup with block details
  6. Click "Select this block" → form populated
  7. Map closes

**Rollback Plan**:
- Remove map overlay UI
- Remove `/api/blocks/nearby` endpoint
- No data changes to rollback

**Dependencies**:
- PR5.1 completed
- Blocks table has `latitude` and `longitude` populated

**Risks & Mitigations**:
- **Risk**: Geospatial queries are slow
  - **Mitigation**: Limit radius to 500m, add spatial index, cache results
- **Risk**: Map library increases bundle size
  - **Mitigation**: Lazy-load Leaflet.js only when map is opened
- **Risk**: Blocks without lat/lng coordinates
  - **Mitigation**: Filter out blocks with null coordinates, show message if no results

---

### PR 9.3: Save Favorite Postal Codes for Quick Access

**Goal**:
Allow users to save frequently-checked postal codes for one-click access, improving convenience for returning users.

**Scope**:
- **In scope**:
  - Star/bookmark icon next to postal code input
  - Click to add/remove from favorites
  - Favorites dropdown/panel
  - Click favorite → populate postal code
  - Store favorites in browser localStorage
  - Limit to 10 favorites
  - Visual indicator for favorited postal codes
- **Out of scope**:
  - Server-side storage (no user accounts)
  - Sync across devices
  - Favorite notes/labels
  - Favorite categories

**Backend Changes**:
- No backend changes required (client-side only)

**Frontend Changes**:
- **Component**: `FavoritesManager.js`
- **Features**:
  - Star icon next to postal code input
  - Click star → add to favorites (if not already)
  - Click star again → remove from favorites
  - Favorites dropdown (show on click or hover)
  - Display: "650514 - Block 514 Ang Mo Kio"
  - Click favorite → populate postal code input
  - Delete button for each favorite
  - "Clear all" button
- **Storage**: `localStorage.setItem('postalCodeFavorites', JSON.stringify(favorites))`
- **Limit**: Max 10 favorites (show message if limit reached)
- **CSS**: Star icon, favorites panel, hover states

**Data Changes**:
- No database changes

**Infra / Config**:
- No changes required

**Testing**:
- **Unit tests**:
  - Add favorite (localStorage updated)
  - Remove favorite (localStorage updated)
  - Load favorites on page load
  - Limit enforcement (max 10)
- **Integration tests**:
  - Not applicable (client-side only)
- **Manual checks**:
  - Add favorite → star turns gold
  - Click star again → removed
  - Refresh page → favorites persist
  - Click favorite → postal code populated
  - Add 10 favorites → 11th shows error
  - Clear all → favorites empty

**Verification**:
- **Commands**:
  - Install: `uv sync`
  - Dev: `uv run uvicorn src.resalelens.main:app --reload`
  - Test: `uv run pytest tests/test_favorites_ui.py -v` (if UI tests exist)
- **Manual verification**:
  1. Enter postal code "650514"
  2. Click star icon → turns gold
  3. Open favorites dropdown → see "650514"
  4. Refresh page → favorite still there
  5. Click favorite → postal code populated
  6. Click star again → removed from favorites
  7. Add 10 favorites → 11th shows "Max 10 favorites" message

**Rollback Plan**:
- Remove favorites UI components
- Clear localStorage (or leave as-is, harmless)

**Dependencies**:
- PR5.1 completed

**Risks & Mitigations**:
- **Risk**: localStorage not available (private browsing)
  - **Mitigation**: Detect localStorage availability, show message if unavailable
- **Risk**: User clears browser data → favorites lost
  - **Mitigation**: Accept as limitation, document in UI (no server-side storage)

## 5. Milestones & Sequence

**Milestone 1: Faster Input (PR 9.1)**
- **PRs**: PR 9.1 (Autocomplete)
- **User value**: Reduced typing, fewer errors, faster lookups
- **Done**: Users can type partial postal code and select from dropdown

**Milestone 2: Better Discovery (PR 9.2)**
- **PRs**: PR 9.2 (Map view)
- **User value**: Visual discovery of nearby properties when exact postal code unknown
- **Done**: Users can see nearby blocks on map and select visually

**Milestone 3: Convenience for Returning Users (PR 9.3)**
- **PRs**: PR 9.3 (Favorites)
- **User value**: One-click access to frequently-checked postal codes
- **Done**: Users can save and quickly access favorite postal codes

## 6. Risks, Trade-offs, and Open Questions

**Major Risks**:
1. **Performance**: Autocomplete with 9,675 records may be slow
   - **Mitigation**: Database indexing, result limiting, caching, debouncing
2. **Map library bundle size**: Leaflet.js adds ~150KB
   - **Mitigation**: Lazy-load map library only when needed
3. **Geospatial query complexity**: Distance calculations may be slow
   - **Mitigation**: Limit radius, use spatial indexes, cache results
4. **Browser compatibility**: localStorage may not be available
   - **Mitigation**: Feature detection, graceful degradation

**Trade-offs**:
- **Client-side favorites vs server-side**: Chose client-side for simplicity (no auth required), but favorites don't sync across devices
- **OpenStreetMap vs Google Maps**: Chose OSM for zero cost and no API key, but less familiar UI
- **Autocomplete prefix match vs fuzzy**: Chose prefix for simplicity and performance, but less forgiving of typos

**Open Questions**:
1. **Should autocomplete search by block number or street name too?**
   - Impact: Would require full-text search, more complex backend
   - Decision: Start with postal code only, gather user feedback
2. **Should map view be default for "not found" or require user click?**
   - Impact: UX flow and performance (lazy-loading)
   - Decision: Require click to avoid loading map unnecessarily
3. **Should favorites have labels/notes?**
   - Impact: More complex UI and storage
   - Decision: Start simple (postal code only), add if users request
4. **Should we support SingPost API for real-time validation?**
   - Impact: External dependency, API costs, rate limits
   - Decision: Defer to future (mentioned in PR5.1 follow-ups)
