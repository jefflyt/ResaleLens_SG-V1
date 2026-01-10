# PR7c: Callback Request & Admin Lead Inbox

**Branch:** `pr7c-callback-admin-inbox`

**Goal:** Enable users to submit callback requests with structured lead capture, implement anti-spam measures, and provide admin-only lead management inbox with authentication.

---

## Scope

### In Scope
- Callback request form (modal/inline) with required/optional fields per PSD §6.5.1
- Lead capture API: `POST /api/callback-request` (stores in `leads` table)
- Rate limiting: max 3 requests/IP/24h (in-memory)
- Anti-spam: honeypot field + optional hCaptcha
- Auto-attach: filter snapshot + shortlist snapshot (JSON)
- Admin authentication: session-based login (bcrypt) at `/admin/login`
- Admin Lead Inbox: `/admin/leads` (list) and `/admin/leads/<id>` (detail)
- Lead management: view, add notes, update status (New/Contacted/Closed)
- Optional email notification to admin on new lead

### Out of Scope
- Lead export/download — Phase 2
- User confirmation email — Phase 2
- CRM integration — Phase 3+
- Advanced anti-spam (reCAPTCHA v3) — add if spam becomes issue

---

## Dependencies

### Required PRs
PR0-PR6, **PR7a (Shortlist & Compare)** — Callback form attaches shortlist snapshot

### External Dependencies
- `bcrypt` (password hashing)
- `python-multipart` (form data parsing)
- `aiosmtplib` (optional, email notifications)
- hCaptcha (optional, bot protection)

---

## Backend Changes

### API Endpoints

**Callback Request:**
- `POST /api/callback-request`
  - Body: `{name, mobile, contact_window, budget_range, preferred_towns, flat_types, timeline, first_timer?, financing_status?, notes?, filter_snapshot, shortlist_snapshot}`
  - Returns: `201 Created` + `{lead_id}` OR `429 Too Many Requests`

**Admin Auth:**
- `POST /admin/login` — Login with bcrypt password check; create session
- `POST /admin/logout` — Destroy session
- `GET /admin/login` — Login page (if not authenticated)

**Admin Leads:**
- `GET /admin/leads` — List all leads (sortable by created_at, status; paginated)
- `GET /admin/leads/<id>` — Lead detail with snapshots
- `POST /admin/leads/<id>/update` — Update status/notes

### Services

**`src/resalelens/services/lead_capture.py`:**
- `create_lead(lead_data)` — Validate, store in DB, trigger optional email
- `send_admin_notification(lead)` — Send email (optional, SMTP)

**`src/resalelens/services/auth.py`:**
- `authenticate_admin(username, password)` — Verify bcrypt hash
- `create_session(user_id)` — Set session cookie
- `get_current_admin(session)` — Retrieve admin from session

### Middleware

**`src/resalelens/middleware/rate_limit.py`:**
- Track IP-based request counts (in-memory dict with TTL)
- Structure: `{"<ip>": {"count": 3, "expires_at": <timestamp>}}`
- Return `429` if count ≥ 3

**`src/resalelens/middleware/auth.py`:**
- Check session for `/admin/*` routes (except `/admin/login`)
- Redirect to `/admin/login` if not authenticated

### Validation
- Mobile: SG format (`+65 XXXX XXXX` or `XXXXXXXX`)
- Required: name, mobile, contact_window, budget_range, preferred_towns, flat_types, timeline
- Honeypot: Hidden field `website`; reject if filled (return 200 but don't store)

---

## Frontend Changes

### Templates

**Callback Request Form (`templates/callback_form.html`):**
Modal/inline with fields:
- Name (text, required)
- Mobile (tel, required)
- Contact window (select: Weekday AM/PM, Weekend AM/PM, Anytime)
- Budget range (select: < $300k, $300k-$500k, $500k-$700k, > $700k)
- Preferred towns (multi-select)
- Flat types (multi-select: 2-ROOM, 3-ROOM, 4-ROOM, 5-ROOM, EXECUTIVE)
- Timeline (select: 0-3m, 3-6m, 6-12m, 12+m)
- First-timer (checkbox, optional)
- Financing status (select, optional: IPA approved, In progress, Not started)
- Notes (textarea, optional, max 500 chars)
- Hidden honeypot: `<input type="text" name="website" style="display:none">`

HTMX: `hx-post="/api/callback-request"` with `hx-swap="outerHTML"` → success message

**Admin Login (`templates/admin/login.html`):**
- Username (email), password
- CSRF token, submit button

**Admin Leads List (`templates/admin/leads_list.html`):**
- Table: Lead ID, Name, Mobile, Budget, Timeline, Created At, Status
- Sortable by created_at (desc default)
- Click row → `/admin/leads/<id>`

**Admin Lead Detail (`templates/admin/lead_detail.html`):**
- Lead info (all fields)
- Filter snapshot (formatted JSON or bullet list)
- Shortlist snapshot (list of blocks)
- Status dropdown (New/Contacted/Closed) + Update button
- Admin notes textarea + Save button

### Styling
- Callback form: mobile-friendly modal, inline validation errors
- Admin inbox: table layout, responsive (stacked on mobile), semantic colors (New=blue, Contacted=yellow, Closed=gray)

---

## Data Changes

No schema changes; `leads` and `users` tables defined in PR1.

**Seed data:**
- `scripts/create_admin.py` — Prompt for username/password, hash with bcrypt, insert into `users`

---

## Infra / Config

### Environment Variables
- `ADMIN_USERNAME` (e.g., `admin@resalelens.sg`)
- `ADMIN_PASSWORD_HASH` (bcrypt hash from `create_admin.py`)
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` (optional)
- `HCAPTCHA_SECRET_KEY` (optional)
- `ENABLE_EMAIL_NOTIFICATIONS` (bool, default: false)

### Dependencies (`pyproject.toml`)
```toml
dependencies = [
    "bcrypt>=4.0",
    "python-multipart>=0.0.5",
    "aiosmtplib>=2.0",  # optional
]
```

---

## Testing

### Unit Tests

**`tests/services/test_lead_capture.py`:**
- `test_create_lead_success` — Valid data, verify DB insert
- `test_create_lead_missing_field` — Validation error
- `test_create_lead_honeypot` — Honeypot filled, lead not stored
- `test_send_admin_notification` — Mock SMTP, verify email sent

**`tests/services/test_auth.py`:**
- `test_authenticate_admin_success` — Correct password, session created
- `test_authenticate_admin_wrong_password` — Failure
- `test_get_current_admin` — Valid session returns admin

**`tests/middleware/test_rate_limit.py`:**
- `test_rate_limit_allows_3` — 3 requests succeed
- `test_rate_limit_blocks_4th` — 4th returns 429
- `test_rate_limit_resets_after_24h` — Counter resets

### Integration Tests (`tests/test_api.py`)
- `test_callback_request_success` — POST valid data, verify 201 + DB entry
- `test_callback_request_rate_limit` — 4 requests, verify 4th = 429
- `test_admin_login_success` — POST credentials, verify session cookie
- `test_admin_leads_list_requires_auth` — Redirect if not logged in
- `test_admin_lead_detail` — Verify detail view renders
- `test_admin_update_lead_status` — POST update, verify saved

### Manual Verification

1. **Callback Request:**
   - Submit form with all required fields → Success message
   - Check DB: `SELECT * FROM leads ORDER BY created_at DESC LIMIT 1;`
   - Verify filter_snapshot and shortlist_snapshot populated

2. **Rate Limiting:**
   - Submit 3 requests → All succeed
   - 4th request → Error: "Maximum requests exceeded"

3. **Honeypot:**
   - Fill hidden `website` field → Success message shown BUT no DB entry

4. **Admin Login:**
   - Navigate to `/admin/leads` (not logged in) → Redirect to `/admin/login`
   - Login with correct credentials → Redirect to `/admin/leads`
   - Wrong password → Error message

5. **Admin Inbox:**
   - View leads list (sorted by created_at desc)
   - Click lead → Detail page shows all info + snapshots
   - Update status to "Contacted" → Verify saved
   - Add admin note → Verify saved

6. **Email (if enabled):**
   - Set `ENABLE_EMAIL_NOTIFICATIONS=true`
   - Submit callback → Verify email received

---

## Verification Commands

```bash
# Create admin user
uv run python scripts/create_admin.py

# Run tests
uv run pytest tests/services/test_lead_capture.py tests/services/test_auth.py tests/middleware/test_rate_limit.py -v

# Dev server
uv run uvicorn src.resalelens.main:app --reload

# Lint & type check
uv run ruff check .
uv run mypy src/
```

---

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Lead spam | Rate limit (3/IP/24h) + honeypot + optional hCaptcha |
| Session hijacking | HTTP-only, Secure, SameSite=Lax cookies; CSRF tokens; 8h TTL |
| Admin password exposure | Bcrypt hash in env (acceptable for solo MVP); Phase 2 secrets manager |
| Email deliverability | Use reputable SMTP; DB-first ensures no lost leads; retry logic |
| Rate limit accuracy | In-memory OK for single server; Redis in Phase 4 for distributed |

---

## Definition of Done

- [ ] Callback form created with all required/optional fields
- [ ] `/api/callback-request` endpoint functional
- [ ] Rate limiting active (max 3/IP/24h)
- [ ] Honeypot field working (silent rejection)
- [ ] Leads stored in DB within 1 minute
- [ ] Admin login/logout functional
- [ ] Admin inbox shows leads (sorted by created_at desc)
- [ ] Admin can view detail, update status, add notes
- [ ] Email notifications work (if enabled)
- [ ] Tests pass (unit + integration)
- [ ] Manual verification complete
- [ ] `scripts/create_admin.py` script works
- [ ] CI passes
- [ ] README updated with admin setup instructions

---

## Summary

PR7c completes the buyer journey by enabling callback requests with anti-spam protection and provides admin lead management via authenticated inbox. This closes the loop on Phase 1 MVP user journeys (A, B, C from PSD).
