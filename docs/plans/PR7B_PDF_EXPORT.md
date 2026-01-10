# PR7b: PDF Export

**Branch:** `pr7b-pdf-export`

**Goal:** Enable users to download professionally formatted PDF reports of their research with shortlist, filters, metrics, timestamps, and disclaimers.

---

## Scope

### In Scope
- PDF generation service using WeasyPrint (Python-based HTML/CSS to PDF)
- PDF template with print-friendly CSS
- Endpoint: `GET /export/pdf`
- PDF content: cover page, filters, shortlist items (Fair Value, Block X-Ray, top 5 comps), dataset timestamps, disclaimer
- "Download PDF" button on compare page

### Out of Scope
- Callback request (PR7c)
- Admin features (PR7c)
- PDF customization (user branding, notes) — Phase 2+
- Async/background PDF generation — Phase 4

---

## Dependencies

### Required PRs
PR0, PR1, PR2, PR3, PR4, PR5, PR6, **PR7a (Shortlist & Compare)**

### External Dependencies
- **WeasyPrint** (`pip install weasyprint`)
- **System dependencies**:
  - macOS: `brew install pango cairo`
  - Ubuntu: `apt-get install libpango-1.0-0 libcairo2 libpangocairo-1.0-0`

---

## Backend Changes

### API Endpoints

**`GET /export/pdf`**
- Query params: `shortlist` (comma-separated block IDs), `filters` (JSON)
- Returns: PDF file with `Content-Disposition: attachment`
- Errors: `400` if shortlist empty, `500` if generation fails

### Services

**`src/resalelens/services/pdf_export.py`:**
```python
from weasyprint import HTML, CSS

def generate_pdf_report(shortlist_items, filters, data_status) -> bytes:
    """Generate PDF from Jinja2 template."""
    template = env.get_template('pdf_report.html')
    html = template.render(
        shortlist=shortlist_items,
        filters=filters,
        data_status=data_status,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M SGT")
    )
    return HTML(string=html).write_pdf(stylesheets=[CSS('static/styles_pdf.css')])
```

**Key functions:**
- `generate_pdf_report()` → PDF bytes
- `enrich_shortlist_for_pdf()` → Fetch Block X-Ray data + top 5 comps

### Router Updates

**`src/resalelens/routers/public.py`:**
- Add `/export/pdf` route handler
- Parse shortlist from session or query param
- Call `generate_pdf_report()`, return as downloadable file

---

## Frontend Changes

### Templates

**`templates/compare.html` (modify):**
```html
<a href="/export/pdf" class="btn btn-primary" download>
  📄 Download PDF Report
</a>
```

**`templates/pdf_report.html` (new):**
Sections:
1. **Cover Page**: Title, "Generated on" timestamp
2. **Filters Summary**: Persona, budget, towns, flat types
3. **Shortlist Items** (for each block):
   - Fair Value range (P25-P75), confidence, label
   - Lease remaining, nearest MRT, amenities
   - Top 5 comps table (date, price, PSM, storey, distance)
4. **Data Status**: Dataset "Last updated" timestamps
5. **Disclaimer**: "This is an analytics estimate, not a professional valuation"

### Styling

**`static/styles_pdf.css` (new):**
- `@page { size: A4; margin: 2cm; }`
- Print-friendly fonts (Helvetica/Arial)
- Table borders and spacing
- Page breaks between blocks
- Highlighted disclaimer section

---

## Testing

### Unit Tests (`tests/services/test_pdf_export.py`)
- `test_generate_pdf_report_success` — Returns PDF bytes
- `test_pdf_includes_disclaimer` — Disclaimer in output
- `test_pdf_timestamps` — "As of" and dataset timestamps present

### Integration Tests (`tests/test_api.py`)
- `test_export_pdf_endpoint` — Returns PDF with correct headers
- `test_export_pdf_empty_shortlist` — 400 error when empty

### Manual Verification
1. Add 3 blocks to shortlist
2. Navigate to `/compare`, click "Download PDF"
3. Verify PDF downloads as `ResaleLens_Report_YYYY-MM-DD.pdf`
4. Open PDF → Check all sections present and formatted correctly
5. Verify print quality (margins, fonts, page breaks)

---

## Verification Commands

```bash
# Install system dependencies (macOS)
brew install pango cairo

# Sync Python packages
uv sync

# Run tests
uv run pytest tests/services/test_pdf_export.py -v

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
| WeasyPrint installation complexity | Test on target platform; provide platform-specific docs |
| Slow PDF generation (>5s) | Limit comps to 5 per block; add loading spinner |
| Rendering errors | Use simple CSS; test edge cases (missing data, long text) |
| Large PDF file size | Limit to 10 blocks; compress images |

---

## Definition of Done

- [ ] WeasyPrint installed and tested
- [ ] PDF service, template, and stylesheet created
- [ ] `/export/pdf` endpoint functional
- [ ] "Download PDF" button on compare page
- [ ] PDF includes: cover, filters, shortlist, comps, timestamps, disclaimer
- [ ] Print-friendly (A4, margins, page breaks)
- [ ] Tests pass (unit + integration)
- [ ] Manual verification complete
- [ ] Generation time < 5s
- [ ] CI passes
- [ ] README updated with WeasyPrint install instructions

---

## Next Steps
**PR7c: Callback & Admin Inbox** — Lead capture and admin management
