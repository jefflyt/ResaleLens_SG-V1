## Phase 2: HDB Property Information Features

**Status:** Ready for implementation after PR6 completion

### Overview
Leverage the newly ingested HDB Property Information dataset to enhance Block X-Ray with official building characteristics, amenities, and unit mix data.

### Data Available
From HDB Property Information dataset (13,200+ blocks):
- **Building characteristics:** Max floor level, year completed, total units
- **Amenities:** Commercial space, market/hawker center, MSCP, precinct pavilion
- **Unit mix:** Breakdown by room type (1-5 room, executive, multi-gen, studio, rental)

### Proposed Enhancements

#### 1. Building Age & Characteristics Display
**Location:** Block X-Ray page, building info section

**Features:**
- Display year completed and building age
- Show max floor level
- Display total units in block
- Visual indicators for building age (e.g., "Built 1985 (39 years old)")

**Implementation:**
```python
# In block_xray_service.py
building_age = current_year - block.year_completed if block.year_completed else None
```

#### 2. Amenity Icons & Filters
**Location:** Block X-Ray page, amenities section

**Features:**
- Icon badges for facilities (🏪 Commercial, 🍜 Hawker, 🚗 Carpark, 🏛️ Pavilion)
- Highlight blocks with amenities in search results
- Filter search by amenities (e.g., "Show only blocks with hawker centers")

**UI Example:**
```
Facilities in this block:
✅ Commercial space
✅ Market/Hawker center  
✅ Multi-storey carpark
❌ Precinct pavilion
```

#### 3. Unit Mix Visualization
**Location:** Block X-Ray page, unit composition section

**Features:**
- Pie chart or bar chart showing unit distribution
- Percentage breakdown by flat type
- Identify block character (e.g., "Mostly 3-room flats - family-oriented")

**Example:**
```
Unit Mix (Total: 142 units)
- 3-room: 138 units (97%)
- 5-room: 2 units (1%)
- 4-room: 1 unit (1%)
- 2-room: 1 unit (1%)
```

#### 4. Fair Value Age Adjustment
**Location:** Fair Value calculation engine

**Features:**
- Factor building age into Fair Value calculations
- Apply depreciation curve based on year_completed
- Adjust comparable selection to prefer similar-age blocks

**Formula:**
```python
age_factor = 1.0 - (building_age * 0.005)  # 0.5% depreciation per year
adjusted_fair_value = base_fair_value * age_factor
```

### Implementation Priority

**High Priority (MVP+):**
1. Building age display - Simple, high value
2. Amenity icons - Visual appeal, easy to implement
3. Unit mix chart - Unique insight, moderate effort

**Medium Priority (Phase 2):**
4. Fair Value age adjustment - Requires validation with real data
5. Amenity filters - Requires search UI updates

**Low Priority (Phase 3):**
6. Advanced analytics (e.g., amenity premium analysis)
7. Comparative amenity scoring

### Technical Requirements

**Frontend:**
- Update `templates/block_xray.html` with new sections
- Add Chart.js for unit mix visualization
- Create amenity icon components

**Backend:**
- Update `block_xray_service.py` to include property info
- Add age calculation utility
- Update Fair Value engine (if implementing age adjustment)

**Testing:**
- Verify property data enrichment coverage (>90% of blocks)
- Test graceful handling of missing property data
- Validate age calculations
- Test unit mix chart rendering

### Success Metrics
- >90% of blocks have property info enrichment
- Building age displayed for all blocks with year_completed
- Unit mix visualization shows for >80% of blocks
- User engagement: >30% of Block X-Ray views interact with amenity icons

---

## Implementation Notes

**Data Quality:**
- Property info ingestion matches ~90% of blocks (fuzzy street matching)
- Unmatched blocks show graceful "Data unavailable" messages
- All new fields are nullable to handle missing data

**Performance:**
- Property data cached with Block X-Ray results (1-hour TTL)
- No additional database queries needed (data already in blocks table)
- Unit mix chart rendered client-side (Chart.js)

**Future Enhancements:**
- Amenity proximity scoring (combine with POI distances)
- Historical unit mix changes (if HDB provides time-series data)
- Amenity-based price premium analysis
