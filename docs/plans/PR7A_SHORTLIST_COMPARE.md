# PR7a: Shortlist & Compare

**Branch:** `pr7a-shortlist-compare`

**Goal:** Enable users to build a shortlist of blocks/units and view them side-by-side in a comparison table, facilitating informed decision-making.

---

## Scope

### In Scope
- Session-based shortlist storage (cookie or server-side session)
- "Add to Shortlist" buttons on results and Block X-Ray pages
- Shortlist widget in header/nav showing count
- Compare page (`/compare`) showing up to 3 items side-by-side with Fair Value, lease, MRT/amenities
- HTMX interactions for add/remove (or simple form POST + HTMX swap)

### Out of Scope
- Persistent shortlist storage (deferred to Phase 2 with user accounts)
- PDF export (PR7b)
- Callback request (PR7c)
- Admin features (PR7c)

---

## Dependencies

### Required PRs (must be merged first)
- PR0 (Bootstrap): FastAPI app skeleton, CI, commands
- PR1 (Database Schema): ORM models and migrations framework
- PR2 (HDB Ingestion): Transaction and block data
- PR3 (POI/MRT Ingestion): Amenity data for Block X-Ray
- PR4 (Fair Value Engine): Core pricing logic
- PR5 (Fair Value UI): Results page and API
- PR6 (Block X-Ray & Data Status): Block intelligence and data transparency

### External Dependencies
- `starlette` session middleware (already included in FastAPI)

---

## Backend Changes

### APIs to Add/Modify

**Shortlist Management:**
- `POST /api/shortlist/add` — Add block/unit to session-based shortlist
  - Request body: `{block, street, flat_type, fair_value, confidence, lease_remaining}`
  - Response: `200 OK` + `{count: <n>, message: "Added to shortlist"}`
  - Max 10 items per shortlist
- `POST /api/shortlist/remove` — Remove from shortlist
  - Request body: `{item_id}` (index in shortlist array)
  - Response: `200 OK` + `{count: <n>, message: "Removed from shortlist"}`
- `GET /api/shortlist` — Retrieve current shortlist items
  - Response: `200 OK` + `{items: [...], count: <n>}`
- `GET /api/shortlist/count` — Get shortlist count only
  - Response: `200 OK` + `{count: <n>}`

**Compare Page:**
- `GET /compare` — Render compare page with shortlist data (server-side)
  - Fetches shortlist from session
  - Enriches with Block X-Ray data (MRT, amenities)
  - Renders comparison table

### Services to Create

**`src/resalelens/services/shortlist.py`:**
- `add_to_shortlist(session, item_data)` → Updated shortlist
  - Validates max 10 items
  - Stores in session as JSON array: `[{"block": "123", "street": "Main St", "flat_type": "4-ROOM", "fair_value": 450000, ...}, ...]`
- `remove_from_shortlist(session, item_id)` → Updated shortlist
- `get_shortlist(session)` → List of shortlist items
- `get_shortlist_count(session)` → Integer count
- `clear_shortlist(session)` → Empty shortlist

### Router Updates

**`src/resalelens/routers/api.py`:**
- Add shortlist endpoints (add, remove, get, count)

**`src/resalelens/routers/public.py`:**
- Add compare page route (`GET /compare`)

### Session Management

**Configuration:**
- Use FastAPI's `SessionMiddleware` from `starlette.middleware.sessions`
- Session storage: Signed cookies (HTTP-only, Secure, SameSite=Lax)
- Session TTL: 24 hours
- Secret key: `SECRET_KEY` from `.env.local` (already configured in PR0)

**Session data structure:**
```json
{
  "shortlist": [
    {
      "block": "123",
      "street": "Main Street",
      "flat_type": "4-ROOM",
      "fair_value": 450000,
      "confidence": 85,
      "lease_remaining": 85,
      "mrt_distance": 500,
      "added_at": "2026-01-10T14:30:00"
    }
  ]
}
```

---

## Frontend Changes

### Templates to Create/Modify

**`templates/results.html` (modify):**
- Add "Add to Shortlist" button below Fair Value card
- Button uses HTMX: `<button hx-post="/api/shortlist/add" hx-vals='{"block": "{{block}}", ...}' hx-swap="outerHTML">Add to Shortlist</button>`
- On success, swap with "Added ✓" message + "View Shortlist" link

**`templates/block_xray.html` (modify):**
- Add "Add to Shortlist" button in header section
- Same HTMX pattern as results page

**`templates/base.html` (modify):**
- Add shortlist badge in header/nav:
  ```html
  <a href="/compare" class="shortlist-badge">
    <span class="icon">📊</span>
    <span hx-get="/api/shortlist/count" hx-trigger="load, shortlist-updated from:body" hx-swap="innerHTML">0</span>
  </a>
  ```
- Badge updates dynamically when items are added/removed (via HTMX event)

**`templates/compare.html` (new):**
- Side-by-side comparison table
- Columns:
  - Block / Address
  - Fair Value (band with P25-P75)
  - Confidence Score
  - Lease Remaining (years + visual indicator)
  - Nearest MRT (distance/time)
  - Amenities Summary (supermarket, clinic, park distances)
  - Remove button
- Responsive: stacked cards on mobile, table on desktop
- Empty state: "Add at least 2 blocks to compare" (if shortlist < 2)
- Max 3 items shown; if shortlist > 3, show first 3 with "Remove others to add more"

### Styling

**CSS additions (`static/styles.css`):**
- `.shortlist-badge` — Prominent badge in header with count bubble
- `.compare-table` — Responsive table/card layout
- `.compare-table th, .compare-table td` — Column styling
- `.lease-indicator` — Visual bar showing lease remaining (e.g., green >80 years, yellow 60-80, red <60)
- `.metric-card` — Card layout for mobile stacked view
- Empty state styling

**Visual design:**
- Shortlist badge: Blue accent with white count bubble
- Comparison table: Clean, scannable layout with alternating row colors
- Favorable metrics: Green highlights (high confidence, long lease, close MRT)
- Unfavorable metrics: Yellow/red highlights (low confidence, short lease, far MRT)

### HTMX Integration

**Add to Shortlist:**
```html
<button 
  hx-post="/api/shortlist/add" 
  hx-vals='{"block": "{{block}}", "street": "{{street}}", "flat_type": "{{flat_type}}", "fair_value": {{fair_value}}, ...}'
  hx-swap="outerHTML"
  hx-target="this">
  Add to Shortlist
</button>
```

**Success response:**
```html
<div class="shortlist-success">
  Added ✓ <a href="/compare">View Shortlist</a>
</div>
```

**Event triggering:**
- After successful add/remove, trigger custom event: `hx-trigger="shortlist-updated"`
- Shortlist badge listens for this event and updates count

---

## Data Changes

No database schema changes required; session storage only.

---

## Infra / Config

### Dependencies
- `starlette` (already included in FastAPI)

### Environment Variables
- `SECRET_KEY` (already configured in PR0 for session signing)

### Configuration Updates

**`src/resalelens/main.py`:**
```python
from starlette.middleware.sessions import SessionMiddleware
from src.resalelens.config import settings

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    max_age=86400,  # 24 hours
    https_only=settings.ENV == "production",
    same_site="lax"
)
```

---

## Testing

### Unit Tests

**`tests/services/test_shortlist.py`:**
- `test_add_to_shortlist_success` — Add item, verify in session
- `test_add_to_shortlist_duplicate` — Add same block twice, verify only one entry
- `test_add_to_shortlist_max_items` — Add 11 items, verify max 10 enforced (oldest removed)
- `test_remove_from_shortlist` — Remove item by index, verify removal
- `test_get_shortlist_empty` — Empty shortlist returns `[]`
- `test_get_shortlist_count` — Verify count matches number of items

### Integration/API Tests

**`tests/test_api.py`:**
- `test_shortlist_add_endpoint` — POST to `/api/shortlist/add`, verify 200 + updated count in response
- `test_shortlist_add_max_enforcement` — Add 11 items, verify 10 in session
- `test_shortlist_remove_endpoint` — POST to `/api/shortlist/remove`, verify item removed
- `test_shortlist_get_endpoint` — GET `/api/shortlist`, verify all items returned
- `test_compare_page_with_shortlist` — GET `/compare` with 3 items in session, verify rendering
- `test_compare_page_empty_shortlist` — GET `/compare` with empty session, verify empty state message

### Manual Checks
1. Add 3 blocks from results page → Verify shortlist badge updates to 3
2. Navigate to Block X-Ray, add another block → Badge shows 4
3. Click "Compare" in header → Verify `/compare` shows 4 blocks side-by-side
4. Click "Remove" on one block → Verify it disappears and comparison updates
5. Clear browser session/cookies → Verify shortlist resets to 0
6. Add blocks until max (10) → Verify 11th block replaces oldest
7. Test on mobile → Verify comparison view stacks as cards

---

## Verification

### Commands

**Install dependencies:**
```bash
uv sync
```

**Run development server:**
```bash
uv run uvicorn src.resalelens.main:app --reload
```

**Run tests:**
```bash
uv run pytest tests/services/test_shortlist.py tests/test_api.py::test_shortlist_add_endpoint -v
```

**Lint:**
```bash
uv run ruff check .
```

**Type check:**
```bash
uv run mypy src/
```

**Format:**
```bash
uv run ruff format .
```

### Manual Verification Checklist

1. **Add to Shortlist (Results Page)**
   - Navigate to `/` (home)
   - Run a Fair Value check
   - Click "Add to Shortlist" on results page
   - **Expected**: Button replaced with "Added ✓" message
   - **Expected**: Shortlist badge in header shows count: 1

2. **Add to Shortlist (Block X-Ray)**
   - Navigate to a Block X-Ray page (`/block/<block_id>`)
   - Click "Add to Shortlist"
   - **Expected**: Badge count increments to 2

3. **Shortlist Badge Updates**
   - Add 3 total blocks
   - **Expected**: Badge shows "3"
   - Badge is clickable and links to `/compare`

4. **Compare Page - Multiple Items**
   - Click "Compare" in header/nav
   - **Expected**: Navigate to `/compare`
   - **Expected**: Side-by-side table/cards showing 3 blocks
   - **Expected**: Columns: Block/Address, Fair Value, Confidence, Lease, MRT, Amenities
   - **Expected**: Each row has "Remove" button

5. **Remove from Shortlist**
   - On compare page, click "Remove" on one block
   - **Expected**: Block disappears from comparison
   - **Expected**: Badge count decrements to 2
   - **Expected**: No full page reload (HTMX swap)

6. **Empty State**
   - Remove all blocks from shortlist
   - Navigate to `/compare`
   - **Expected**: Message: "Add at least 2 blocks to compare"

7. **Session Persistence**
   - Add 3 blocks, close browser tab
   - Reopen browser, navigate to site
   - **Expected**: Shortlist persists (if within 24h session TTL)

8. **Max Items Enforcement**
   - Add 10 blocks to shortlist
   - Add 11th block
   - **Expected**: Badge shows 10 (oldest block removed)

9. **Mobile Responsiveness**
   - Open `/compare` on mobile viewport
   - **Expected**: Table converts to stacked cards
   - **Expected**: All metrics visible and readable

---

## Rollback Plan

### Revert Strategy
- Revert PR7a merge commit
- No database schema changes; no migrations to rollback
- Session storage is ephemeral; no data cleanup needed

### Feature Flag / Kill Switch
Not applicable for MVP (no feature flags)

---

## Risks & Mitigations

### Risk 1: Session Storage Size Limits
**Risk:** Browser cookies have size limits (~4KB); 10-item shortlist with full data may exceed this.

**Mitigation:**
- Store only essential data in session (block, street, flat_type, fair_value, confidence)
- Fetch full Block X-Ray data on-demand when rendering `/compare` page
- Alternative: Use server-side session storage (Redis) in Phase 4 if cookie size becomes an issue

### Risk 2: Session Expiry/Loss
**Risk:** Users lose shortlist if they clear cookies or session expires (24h).

**Mitigation:**
- Set session TTL to 24 hours (sufficient for typical research session)
- PR7b (PDF Export) allows users to preserve state before session expiry
- Phase 2 will add persistent storage with user accounts

### Risk 3: HTMX Browser Compatibility
**Risk:** Older browsers may not support HTMX dynamic swaps.

**Mitigation:**
- HTMX degrades gracefully to standard form POST
- Ensure buttons work without JavaScript (progressive enhancement)
- Test on common browsers (Chrome, Safari, Firefox, Edge)

### Risk 4: Duplicate Blocks in Shortlist
**Risk:** User adds same block multiple times (e.g., with different flat types).

**Mitigation:**
- Allow duplicates if attributes differ (block + flat_type as composite key)
- Show clear labels in comparison (e.g., "Block 123, 4-ROOM" vs "Block 123, 5-ROOM")

---

## Definition of Done

- [ ] Session middleware configured and active
- [ ] Shortlist service implements add/remove/get/count operations
- [ ] API endpoints functional: `POST /api/shortlist/add`, `POST /api/shortlist/remove`, `GET /api/shortlist`, `GET /api/shortlist/count`
- [ ] "Add to Shortlist" buttons on results and Block X-Ray pages
- [ ] Shortlist badge in header updates dynamically via HTMX
- [ ] Compare page (`/compare`) renders side-by-side comparison of up to 3 items
- [ ] Remove buttons work on compare page (HTMX swap, no full reload)
- [ ] Empty state message shown when shortlist < 2 items
- [ ] Max 10 items enforced (oldest removed when limit exceeded)
- [ ] Unit tests pass (`pytest tests/services/test_shortlist.py`)
- [ ] Integration tests pass (`pytest tests/test_api.py`)
- [ ] Manual verification checklist completed
- [ ] Lint passes (`ruff check .`)
- [ ] Type check passes (`mypy src/`)
- [ ] Mobile responsive (compare page stacks on mobile)
- [ ] CI pipeline passes (all checks green)

---

## Next Steps

After PR7a is merged, proceed to:
- **PR7b: PDF Export** — Generate downloadable PDF reports from shortlist
- **PR7c: Callback & Admin Inbox** — Lead capture and admin management
