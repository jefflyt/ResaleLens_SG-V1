# Feature Plan: Block X-Ray UI Enhancements

## 0) Assumptions
- Chart.js library is already loaded in the template (confirmed in line 6 of block_xray.html)
- Current implementation uses Jinja2 templates with inline CSS
- Block X-Ray data structure from `BlockXRayData` schema is complete and accurate

## 1) Clarifying Questions
None - current implementation is functional and data structure is well-defined.

## 2) Feature Summary

**Goal**: Transform the Block X-Ray page from a basic data list into an interactive, visually engaging analytics dashboard that helps users quickly understand block characteristics and make informed decisions.

**User Story**: As a potential HDB buyer, I want to view comprehensive block information in an intuitive, visually appealing dashboard so that I can quickly assess whether a block meets my needs without reading through dense text.

**Acceptance Criteria**:
- [ ] Transaction trends display as an interactive line chart (not just empty placeholder)
- [ ] Unit composition shows as a visual donut/pie chart with percentages
- [ ] Building information cards use clear visual hierarchy (bold values, muted labels)
- [ ] Nearby amenities are categorized by type (Schools, Transport, Shopping, etc.)
- [ ] Price stability indicator uses color-coded badges (green=stable, yellow=moderate, red=volatile)
- [ ] Page layout uses responsive grid system for better information density
- [ ] All charts are interactive with hover tooltips showing detailed information
- [ ] Mobile-responsive design maintains readability on smaller screens
- [ ] Page loads in under 2 seconds with all visualizations rendered
- [ ] "Back to Results" or "Search Another Block" navigation button is prominently displayed

**Non-goals**:
- PDF export functionality (covered in PR7B)
- Comparison with other blocks (covered in PR7A)
- Historical price predictions or AI-powered insights
- Integration with external mapping services (future enhancement)

## 3) Approach Overview

**Proposed UX**:
- **Hero Header**: Gradient background with block address, town, and postal code
- **Summary Cards Row**: 3-column grid showing Building Info, Lease Info, and Price Stability at a glance
- **Visualizations Section**: Full-width charts for Transaction Trends and Unit Composition
- **Facilities & Amenities**: Side-by-side cards with categorized lists and icons
- **Action Bar**: Sticky footer with "Back to Search" and "View Fair Value" buttons

**Proposed API**: No API changes required - uses existing `/api/block/{block_id}` endpoint

**Proposed Data Changes**: None - all data is already available in `BlockXRayData` schema

**Auth/AuthZ Rules**: None - Block X-Ray is publicly accessible

## 4) PR Plan

**PR Title**: Enhance Block X-Ray UI with Interactive Charts and Improved Layout

**Branch Name**: feature/block-xray-ui-improvements

**Scope (in)**:
- Implement transaction trends line chart using Chart.js
- Add unit composition donut chart with interactive tooltips
- Redesign layout with CSS Grid for better information density
- Improve typography with clear label-value hierarchy
- Categorize amenities by type (Schools, Transport, Shopping, Healthcare, Recreation)
- Add color-coded price stability badges
- Implement responsive design for mobile devices
- Add navigation buttons ("Back to Search", "Calculate Fair Value")

**Out of Scope (explicit)**:
- PDF export (PR7B)
- Block comparison (PR7A)
- Map integration
- Backend data changes
- New API endpoints

**Key Changes by Layer**:

**Frontend**:
- `templates/block_xray.html`:
  - Restructure HTML with semantic sections and CSS Grid layout
  - Add Chart.js configuration for transaction trends line chart
  - Add Chart.js configuration for unit composition donut chart
  - Implement amenity categorization logic in template
  - Add responsive CSS media queries
  - Enhance color scheme and typography
  - Add action buttons with proper routing

**Backend**: No changes required

**Data**: No changes required

**Infra/Config**: No changes required

**Edge Cases to Handle**:
- Missing transaction trends data (< 5 transactions) - show "Insufficient data" message
- No unit composition data - hide chart section
- Empty amenities list - show "No nearby amenities" message
- Null `last_updated` field - display "N/A" (already handled)
- Very long street names - truncate with ellipsis on mobile
- Blocks with 10+ amenities - implement "Show more" toggle

**Migration/Compatibility Notes**:
- No database migrations required
- Backward compatible - existing Block X-Ray links continue to work
- Chart.js is already loaded, no new dependencies

## 5) Testing & Verification

**Automated Tests**:
- **Unit**: None required (pure frontend changes)
- **Integration**: None required (no API changes)
- **E2E**: Manual browser testing sufficient

**Manual Verification Checklist**:
- [ ] Navigate to `/api/block/1323` → Block X-Ray page loads with new layout
- [ ] Transaction trends chart displays with quarterly data points → Hover shows PSM values
- [ ] Unit composition donut chart shows room type distribution → Hover shows unit counts
- [ ] Building info cards display in 3-column grid on desktop → Single column on mobile
- [ ] Amenities are grouped by category → Each category shows icon and count
- [ ] Price stability badge shows correct color (green/yellow/red) based on volatility
- [ ] "Back to Search" button → Returns to home page
- [ ] "Calculate Fair Value" button → Pre-fills form with block address
- [ ] Resize browser to mobile width → Layout adapts responsively
- [ ] Test with block that has no transaction trends → Shows "Insufficient data" message

**Commands to Run**:
- **Install**: `uv sync` (no new dependencies)
- **Dev**: `uv run uvicorn src.resalelens.main:app --reload --host 0.0.0.0 --port 8000`
- **Test**: Manual browser testing at `http://localhost:8000/api/block/1323`
- **Lint**: `uv run ruff check templates/` (if applicable)

## 6) Rollback Plan

If issues arise:
1. Revert commit: `git revert <commit-hash>`
2. Redeploy previous version
3. No database rollback needed (no schema changes)
4. Users will see old Block X-Ray layout (functional but less polished)

## 7) Follow-ups

**Future Enhancements** (separate PRs):
- **Interactive Map**: Show block location and nearby amenities on embedded map
- **Lease Calculator**: Interactive slider to project remaining lease value over time
- **Price Trend Forecast**: ML-based prediction of future PSM trends
- **Neighborhood Insights**: Compare block stats with town/national averages
- **Save to Shortlist**: One-click save for comparison (PR7A integration)
- **Share Block**: Generate shareable link with QR code
