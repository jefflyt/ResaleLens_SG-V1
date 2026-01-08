# PR7 Planning Note: Admin Dashboard & Lead Inbox Enhancements

## Overview
PR7 should include a comprehensive admin dashboard with authentication, lead management, and data ingestion controls.

---

## 1. Admin Authentication

**Login System:**
- **Login page:** `/admin/login`
  - Email/username + password form
  - Session-based authentication (secure HTTP-only cookies)
  - CSRF protection
  - Redirect to `/admin/dashboard` on successful login
  
- **Auth Strategy:**
  - Session-based auth with bcrypt-hashed passwords
  - `admin` role required for all `/admin/*` routes
  - Logout endpoint: `/admin/logout`
  - Session expiry: configurable (default: 24 hours)

- **User Model (may already exist from PR0/PR1):**
  - `id`, `email`, `hashed_password`, `role`, `created_at`
  - Seed script to create initial admin user

---

## 2. Admin Dashboard (`/admin/dashboard`)

**Central admin control panel with three main sections:**

### 2.1 Data Ingestion Status Panel
- **Dataset Cards (4 cards):**
  - HDB Transactions
  - HDB Blocks
  - MRT Stations
  - POIs (Amenities)

- **Each card displays:**
  - Dataset name and icon
  - Last successful ingestion timestamp
  - Next scheduled run time
  - Current status badge (✅ Healthy / ⚠️ Delayed / ❌ Failed)
  - Rows currently in database
  - Manual trigger button: "🔄 Refresh Now"

- **"Refresh All" button:**
  - Triggers all 4 ingestion jobs sequentially
  - Shows progress indicator while running
  - Returns summary of all runs

- **Recent Ingestion Runs Table:**
  - Last 10 ingestion runs (all datasets)
  - Columns: Dataset, Started At, Duration, Status, Rows Processed, Actions (View Details)
  - Sortable by timestamp
  - Status indicators with color coding

### 2.2 Lead Management Summary
- **Statistics cards:**
  - Total leads count
  - New leads (status='New') with badge
  - Contacted leads count
  - Closed leads count

- **Recent leads preview:**
  - Last 5 leads with name, mobile, submitted timestamp, status
  - "View All Leads" button → navigates to `/admin/leads`

### 2.3 System Health (Optional for MVP)
- Database size
- Total records count (transactions, blocks, pois)
- Data freshness indicators (how many days since last ingestion for each dataset)
- API health status (OneMap, data.gov.sg) - optional

---

## 3. Admin Lead Inbox (`/admin/leads`)

**From MASTER_PLAN (already scoped in original PR7):**
- List view of all leads (sortable by date, status)
- Detail view with attached snapshots (filter snapshot, shortlist snapshot)
- Minimal note field + status update (New, Contacted, Closed)
- Admin auth required

**Enhancements to add:**
- Filter by status (New / Contacted / Closed)
- Search by name, mobile, or preferred towns
- Export leads to CSV
- Bulk status update (select multiple leads and mark as Contacted/Closed)
- Lead detail page shows:
  - Contact info (name, mobile, contact window)
  - Preferences (budget, towns, flat types, timeline)
  - Filter snapshot (what filters they used)
  - Shortlist snapshot (which blocks they saved)
  - Notes field (admin can add private notes)
  - Activity log (status changes with timestamps)

---

## 4. Admin Navigation

**Top nav bar for admin pages:**
- Logo / App name
- Nav links:
  - Dashboard (home)
  - Leads
  - Data Status (links to existing public `/data-status` page from PR6)
  - Logout
- User indicator: "Logged in as: admin@example.com"

---

## 5. Manual Ingestion Trigger UI (HTMX Integration)

**Button interaction flow:**
1. Admin clicks "🔄 Refresh HDB Transactions" button
2. HTMX sends `POST /admin/ingestion/trigger?dataset=hdb_transactions` with admin auth
3. Button shows spinner/loading state: "⏳ Refreshing..."
4. Server responds with ingestion run result
5. UI updates card with new timestamp and status
6. Show success toast: "✅ HDB Transactions refreshed successfully (1,234 rows processed)"
7. Or error toast: "❌ Ingestion failed: [error message]"

**HTMX Attributes:**
```html
<button 
  hx-post="/admin/ingestion/trigger?dataset=hdb_transactions"
  hx-target="#hdb-transactions-card"
  hx-swap="outerHTML"
  hx-indicator="#spinner-hdb-transactions"
  class="btn btn-primary">
  🔄 Refresh Now
</button>
```

**Response template:**
Server returns updated card HTML fragment with new status and timestamp.

---

## 6. Templates Required

**New templates for PR7:**
- `templates/admin/login.html` — Admin login form
- `templates/admin/base.html` — Base template with admin nav bar
- `templates/admin/dashboard.html` — Main admin dashboard with ingestion cards and lead summary
- `templates/admin/leads_list.html` — All leads list view (sortable, filterable)
- `templates/admin/lead_detail.html` — Single lead detail view with notes
- `templates/admin/ingestion_run_detail.html` — Ingestion run details (optional)
- `templates/admin/components/dataset_card.html` — Reusable card component for each dataset
- `templates/admin/components/ingestion_run_row.html` — Reusable table row for recent runs

---

## 7. Backend Changes for PR7

**Admin Router (`src/resalelens/routers/admin.py`) - Enhancements:**
- `GET /admin/login` — Render login page
- `POST /admin/login` — Authenticate and create session
- `POST /admin/logout` — Destroy session, redirect to login
- `GET /admin/dashboard` — Render dashboard (requires auth)
  - Query `ingestion_runs` for recent runs and next scheduled times
  - Query `leads` for summary stats (counts by status)
  - Render dashboard template with data
- `POST /admin/ingestion/trigger` — Already exists from PR2/PR3; add HTMX response support
  - Return HTML fragment (dataset card) instead of JSON if `HX-Request` header present
  - Include HTMX response headers for client-side UI updates

**Services:**
- `src/resalelens/services/admin_service.py` — Dashboard data aggregation
  - `get_ingestion_summary()` — Query all datasets for last run, next run, status
  - `get_lead_summary()` — Query leads for counts by status

**Middleware:**
- `src/resalelens/middleware/auth.py` — Session validation middleware
  - Check session cookie on all `/admin/*` routes (except `/admin/login`)
  - Redirect to `/admin/login` if not authenticated

---

## 8. Testing for PR7 Admin Dashboard

**Unit Tests:**
- Test login endpoint (valid/invalid credentials)
- Test logout endpoint (session destroyed)
- Test dashboard data aggregation service
- Test ingestion trigger with HTMX header (returns HTML fragment)

**Integration Tests:**
- Login flow: POST credentials → session created → redirect to dashboard
- Dashboard loads with correct data (mocked ingestion_runs and leads)
- Manual ingestion trigger via UI (HTMX): button click → API call → UI updates
- Lead list view: filter by status, search by name
- Lead detail view: update status, add notes

**Manual Verification:**
- Log in as admin → lands on dashboard
- Click "Refresh HDB Transactions" → see loading spinner → see success toast → card updates with new timestamp
- Navigate to Leads → see all leads → click on lead → see detail page with snapshots
- Log out → redirected to login page → cannot access `/admin/dashboard` (redirects back to login)

---

## 9. Security Considerations

- **Session Security:**
  - HTTP-only cookies (prevent XSS)
  - Secure flag in production (HTTPS only)
  - SameSite=Lax (CSRF mitigation)
  - Session expiry and renewal

- **Password Security:**
  - Bcrypt hashing (cost factor 12+)
  - No plaintext passwords in logs or database

- **CSRF Protection:**
  - CSRF tokens on all POST forms
  - FastAPI CSRF middleware or manual token validation

- **Rate Limiting:**
  - Limit login attempts (e.g., 5 per IP per 15 minutes)
  - Limit manual ingestion triggers (e.g., 10 per hour)

---

## 10. Styling and UX

**Design Guidelines:**
- Clean, modern admin UI using **vanilla CSS** (CSS Grid/Flexbox for layouts)
  - Python-first principle: No build pipeline, no CSS frameworks with JavaScript dependencies
  - Option: Lightweight CSS-only framework like PicoCSS only if vanilla CSS development is too slow (PicoCSS has no JavaScript, just drop-in CSS)
- Color-coded status indicators:
  - ✅ Green for success/healthy
  - ⚠️ Yellow/orange for delayed/warning
  - ❌ Red for failed/error
- Loading states for all async actions (spinners, disabled buttons)
- Toast notifications for actions (success/error messages) - implement with vanilla JavaScript or HTMX extensions
- Responsive design (mobile-friendly admin panel) using CSS media queries

**Accessibility:**
- Proper ARIA labels
- Keyboard navigation support
- Screen reader friendly

---

## 11. Documentation Updates

**Update `docs/technical/context.md`:**
- Add admin dashboard documentation
- Document admin login credentials setup
- Document manual ingestion trigger workflow

**Update `README.md`:**
- Add section on accessing admin dashboard
- Document how to create initial admin user

---

## Summary

PR7 transforms from a simple lead inbox into a **full admin control center** with:
✅ Admin authentication and session management
✅ Dashboard with data ingestion status and manual trigger buttons
✅ Lead management with enhanced filtering and search
✅ HTMX-powered UI for seamless interactions
✅ Comprehensive testing and security

**Dependencies:**
- PR2 and PR3 must be merged (provide ingestion API endpoints)
- PR6 should be merged (Data Status page already exists for reference)

**Next Steps:**
1. Use this note when creating the detailed PR7 epic plan
2. Consider using `/plan_feature` workflow for PR7 planning
3. Implement authentication first, then dashboard, then enhanced lead features

---

*Created: 2026-01-09*
*This note will guide the creation of the full PR7 plan using `/plan_feature` or `/plan_epic`.*
