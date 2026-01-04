# ResaleLens SG — Enhanced Product Spec (PSD v2)

**Purpose:** Build-ready specification for an HDB resale “fair value + block intelligence” product for Singapore buyers.

**Version:** v2  
**Date:** 2026-01-04  
**Owner:** Jeff

---

## 1) Overview and problem
HDB resale buyers need a fast, credible way to answer two questions:
1) **Is this unit / block fairly priced based on real comps?**
2) **Does this block fit my needs (commute, schools, amenities), based on verifiable data?**

Most portals show raw historical transactions but do not:
- Normalize comparable transactions into a **Fair Value band** with confidence scores.
- Provide block-level transparency (lease clock, transaction trends, amenities, noise proxies, MRT/school proximity).
- Offer persona-based filters with explicit rules (e.g., "Budget-conscious", "Family with kids").
- Enable one-click PDF exports or callback requests **without requiring login**.

> **📌 Data Scope Clarification:**  
> ResaleLens SG analyzes **historical HDB resale transaction data** (completed sales from data.gov.sg), **NOT active property listings for sale**. There is no integration with PropertyGuru, 99.co, or other listing portals.

---

## 2) Goals and success criteria

### 2.1 Product goals (Phase 1)
1. Provide a **Fair Value band** for a chosen unit (user inputs unit attributes + comparable historical transactions).
2. Illuminate block-level context (lease, amenities, MRT/schools, transaction volatility, noise-risk proxies).
3. Enable persona-based shortlisting (first-time buyers, families, multi-gen, upgraders) via explicit rules.
4. Enable buyers to **request an agent callback** and **download a generated PDF report** of their research, without requiring a buyer login.

### 2.2 Success metrics
- **Activation:** ≥30% of visitors run at least 1 Fair Value check.
- **Engagement:** median ≥3 blocks/units evaluated per session.
- **Trust:** ≥70% rate Fair Value explanation as “clear” (in-product micro survey).
- **Leads:** ≥2–5% submit a callback request.
- **Exports:** ≥10% download a PDF report.
- **Performance:** p95 Fair Value response < 2.5s; map UI usable on mobile.

---

## 3) Scope and definitions

### 3.1 MVP scope boundaries
- MVP supports **block-level and transaction-level analytics** based on historical data, not true unit-level condition/view (reno quality, facing, noise on-site).
- "Unit-level" refers to **user-provided unit attributes** (storey range, floor area, flat model, lease commence) used for comp matching and normalization against historical transactions.

### 3.2 Key definitions
- **Fair Value band:** estimated range based on comps, shown as total price and price-per-sqm.
- **Confidence score (0–100):** derived from comp count, variance, and recency; not a guarantee.
- **Comps:** transactions selected via similarity + proximity, using a fallback ladder.

### 3.3 Disclaimer
This is an **analytics estimate** for decision support. It is not a professional valuation.

---

## 4) Target users and personas

### 4.1 Primary users
- **First-time buyers:** need budget clarity, grant guidance (as an estimator), and commute.
- **Families with kids:** school radius, parks, amenities.
- **Multi-generational families:** elder-friendly walkability, essential amenities, access proxies where available.
- **Upgraders / second-time buyers:** need affordability clarity, timing, and block-level stability signals.

### 4.2 Secondary users
- **Admin (you):** manages callback requests and follow-up.
- **Agents (Phase 2):** access a simple workspace to save and reopen work-in-progress customer entries.

---

## 5) Core user journeys

### Journey A: "Is this unit fairly priced?"
1. User enters block/address + flat type + attributes (storey range, floor area) for a unit of interest.
2. System geocodes, fetches comparable historical transactions (fallback ladder: same block → nearby radius → town-level).
3. System returns Fair Value band + confidence + comps.
4. User shortlists and compares options.

### Journey B: “Find blocks that fit my life”
1. User chooses a persona + constraints (budget, town, flat type).
2. User selects priorities (near MRT, near a chosen school, near parks, etc.).
3. System returns ranked blocks with explainability.

### Journey C: “Request callback + export PDF”
1. User filters and evaluates blocks.
2. User shortlists options.
3. User requests a callback (short form).
4. User downloads a generated PDF report as a snapshot for reference.

---

## 6) Features

### 6.1 Fair Value Engine (MVP)
**Inputs**
- Location: block/address (geocoded).
- Flat attributes: flat type, floor area, storey range, flat model (if available), lease commence/year.
- Time window default: last 12 months (expandable).

**Outputs**
- Fair Value band (P25–P75) for total price and price-per-sqm.
- Confidence score with reasons (e.g., “12 comps, low variance, recent”).
- Comps table: date, price, sqm, storey range, model, distance.
- Explainability: filters applied, adjustments applied, fallback used.

**Comp selection ladder (fallback)**
1. Same block + same flat type (12 months).
2. Same block + same flat type (24 months).
3. Nearby radius (e.g., 500–800m) + same town + same flat type (12/24 months).
4. Town-level + same flat type (12/24 months).

**Normalization (simple and transparent)**
- Baseline: price-per-sqm.
- Adjustments (only when supported by the comp set):
  - Storey-range adjustment using median deltas.
  - Floor area handled primarily via psm normalization.
- Outlier handling:
  - Remove comps outside [P5, P95] psm or beyond 2.5 MAD.

**User-facing labels**
- Fair / Slightly high / Slightly low / High risk (adaptive thresholds based on comp variance).

**Edge cases**
- If comps < 5: widen band, lower confidence, recommend expanding window/radius.
- If model/attributes missing: degrade gracefully and explain.

---

### 6.2 Block X-Ray (MVP)
A structured panel grounded in data.

**Block profile**
- Remaining lease + lease commence year
- Flat mix distribution (if available)
- Transaction trend (median psm over time)
- Volatility indicator (variance)

**Neighborhood radar**
- Distance and/or travel time to:
  - MRT/LRT stations
  - Supermarkets
  - Polyclinics/hospitals
  - Parks/playgrounds
  - Markets/malls/hawker centres
- Noise-risk proxies (clearly labeled as proxies):
  - Distance to expressways / major roads
  - Distance to rail lines

**UX requirement:** every metric shows **source** and **last updated**.

---

### 6.3 Persona Filters (rules-based)
Personas are presets over explicit constraints.

Examples:
- **First-time buyer:** budget band, grant estimator (requires user inputs), prioritize stable segments (lower variance) and stronger confidence.
- **Family with young kids:** within X minutes to parks + within 1km of user-selected schools.
- **Multi-gen:** minimize walk time to essentials; prioritize access proxies where available.
- **Upgrader:** prioritize stability + commute + schools.

---

### 6.4 Shortlist, Compare, and PDF export
- Save blocks/units to a shortlist.
- Compare up to 3 options side-by-side (Fair Value, lease, commute/amenities summary).
- Export a **generated PDF report** (no login).

**PDF requirements (generated, not a screenshot)**
- Template-driven generator (e.g., React PDF renderer) for consistent output.
- Includes:
  - Filters used
  - Shortlist items + key metrics
  - “As of” timestamp and dataset “last updated” markers
  - Disclaimer (not a valuation)

---

### 6.5 Callback request and Admin Lead Inbox (Phase 1)
Goal: buyer-side friction stays low; leads are retrievable and structured for follow-up.

#### 6.5.1 Buyer callback request (no login)
**Trigger points:** results, Block X-Ray, shortlist/compare.

**Required fields**
- Name
- Mobile number
- Preferred contact window (weekday/weekend + AM/PM)
- Budget range
- Preferred towns/areas (multi-select)
- Flat type(s)
- Timeline (0–3m / 3–6m / 6–12m)

**Optional fields**
- First-timer vs second-timer
- Financing status (IPA / in progress / not started)
- Notes

**Auto-attached context**
- Filter snapshot
- Shortlist snapshot
- Timestamp + data “last updated” markers

**Handling (Phase 1 choice)**
- **DB-first:** store each request in a Leads table for admin review.
- Optional: send an email notification to you.

**Anti-spam:** basic validation + rate limiting + lightweight bot protection.

#### 6.5.2 Admin Lead Inbox
- Admin-only list view.
- Lead detail view with attached snapshots.
- Minimal note field + simple status (e.g., New / Contacted / Closed).

---

## 7) AI Property Consultant (optional, constrained)
If included, AI must only answer using computed outputs and known datasets.

**Allowed**
- Summarize Fair Value and Block X-Ray signals.
- Explain what drove the result.

**Disallowed**
- Guessing (“vibes”), uncited claims, or claims not supported by datasets.
- “Top schools” assertions unless the basis is explicitly defined.

---

## 8) Data sources and update policy

### 8.1 Required datasets (MVP)
- HDB resale transactions (primary)
- HDB block/address reference + geocoding
- MRT/LRT station locations
- Amenities POIs (supermarkets, malls/markets, clinics, parks)
- Routing/travel time provider (OneMap or similar), or distance-only fallback

### 8.2 Ingestion cadence and schedule (automated)
Data ingestion runs automatically on a fixed schedule (configurable during implementation). All times are in **Asia/Singapore (SGT)**.

**Default schedules (MVP)**
- **HDB resale transactions:** Weekly on **Sunday 03:00 SGT**
- **HDB block/address reference + geocoding dataset:** Weekly on **Sunday 03:15 SGT**
- **MRT/LRT station locations:** Monthly on the **1st, 03:30 SGT**
- **Amenities POIs:** Monthly on the **1st, 03:45 SGT**
- **Routing data:** Not ingested; computed on-demand with caching (see architecture)

**Operational rules**
- Each ingestion run writes a run record (start/end time, status, rows processed, error summary).
- Failures retry automatically (e.g., 3 retries with backoff). If still failing, the previous successfully ingested dataset remains in use.
- Manual re-run is available for admin.

### 8.3 Data transparency in the product (trust feature)
Users can always see what data is powering the results and how fresh it is.

**In-product surfaces**
- **Global “Data Status” page** (footer link): shows all datasets, sources, last successful ingest time, next scheduled run, and current status.
- **Per-metric “Last updated” labels** on Block X-Ray and results cards.
- **PDF export** includes:
  - “As of” timestamp (when the report was generated)
  - Dataset “Last updated” timestamps

**Data Status page content (minimum)**
For each dataset:
- Dataset name
- Source (label; optionally a reference link)
- Last successful ingest (timestamp)
- Next scheduled ingest (timestamp)
- Status (Healthy / Delayed / Failed)
- Notes (e.g., “Using last successful snapshot from …”)

### 8.4 Data freshness rules (MVP)
- If **transactions** are older than 48 hours since the last successful ingest: show **“Data delayed”** badge and explain that the latest published updates may not be reflected yet.
- If any dataset fails ingestion: continue using the last successful snapshot and surface a **non-alarming warning** on the Data Status page.

### 8.5 Data contract in UI
- Every card displays **Last updated**.
- Every PDF includes **As of** and dataset timestamps.

---

## 9) Non-functional requirements
- **Performance:** p95 Fair Value < 2.5s; p95 search/filter < 1.5s.
- **Reliability:** routing failures fall back to straight-line distance.
- **Cost controls:** caching + rate limiting.
- **Privacy:** consent for contact; lead retention policy (e.g., 90 days) unless you decide otherwise.
- **Security:** admin/agent surfaces require authentication; least-privilege access.
- **Data freshness and transparency:** Data Status page + per-metric timestamps + PDF timestamps; alert and badge when ingestion is delayed.
- **Observability:** latency logs, error tracking, ingestion run logs, dataset freshness monitoring.

---

## 10) Architecture (high level)
- **Frontend:** map/search/compare + PDF export + Data Status page.
- **Backend:** ingestion pipeline, Fair Value compute, POI/routing, lead capture, admin inbox.
- **Automation:** scheduled ingestion jobs (cron/scheduler) + retries + run logging.
- **Storage:** transactions, POIs, routing cache, leads, **ingestion_runs** (audit log).

---

## 11) UX structure (screens)
1. Home / Search
2. Unit Input
   - Block/address input (autocomplete if possible).
   - Flat type selector (user inputs unit of interest, not from a listing database).
3. Results (Fair Value + Explainability + Comps)
4. Block X-Ray
5. Compare
6. Callback request form
7. PDF export
8. Admin Lead Inbox
9. Data Status (data sources + last ingest + next scheduled run)

---

## 12) MVP acceptance criteria

### Fair Value
- Returns band + confidence + comps when available.
- If comps < 5: clearly labeled low confidence and shows fallback guidance.

### Block X-Ray
- Shows lease, MRT distance/time (or distance), amenity indicators, and trend.
- Each metric displays last updated.

### Callback request + Admin Lead Inbox
- Callback requests persist to DB (and optionally email you) within 1 minute.
- Admin can view lead, see snapshots, and add a note.

### PDF export
- Generated PDF includes filters, shortlist, key metrics, timestamps, and disclaimers.
- PDF includes dataset “Last updated” timestamps.

### Data transparency
- Data Status page exists and shows (for each dataset): source label, last successful ingest, next scheduled ingest, and current status.
- If transactions ingestion is delayed beyond 48 hours, the product surfaces a “Data delayed” badge and explains that the latest published updates may not be reflected yet.

---

## 13) Pricing and monetization (initial)
- Buyer side free in Phase 1.
- Later options: agent subscription and/or pay-per-lead (only after defining qualified lead rules).

---

## 14) Roadmap

### Phase 1 (MVP)
- Fair Value + Explainability
- Block X-Ray
- Persona presets
- Shortlist + Compare
- Callback request (DB-first; optional email)
- Generated PDF export
- Admin Lead Inbox

### Phase 2
- **Agent Workspace (Saved Jobs):** agent-only login to save and reopen work-in-progress customer entries.
- Commute-time lens (user workplaces)
- Alerts (price drop, new comps)
- Share-link persistence enhancements
- Market context module (non-ML): descriptive trend indicators based on published indices/releases (no forward prediction)

### Phase 3
- Forecasting / ML experiments (optional): only after stable pipelines + evaluation + clear disclaimers.
- More robust pricing models (e.g., hedonic regression) with explainability.

---

## 15) Risks and mitigations
- **Sparse comps:** fallback ladder + confidence + wide band.
- **Routing cost/limits:** caching + distance fallback.
- **Trust/regulatory:** clear disclaimers + transparent methodology.
- **Stale data / delayed ingestion:** Data Status page + freshness rules + visible badges; continue using last successful snapshot.
- **Lead spam:** validation + rate limiting.
- **Scope creep:** keep Phase 2 agent features as “Saved Jobs,” not a CRM.
