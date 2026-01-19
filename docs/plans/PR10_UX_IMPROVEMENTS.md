# PR10: UI/UX Improvements - Critical Fixes

## Overview

This PR addresses critical UI/UX issues identified in the UX audit to improve usability, accessibility, and complete customer journey navigation.

**Priority:** High  
**Effort:** Medium (2-3 days)  
**Risk:** Low (frontend-only, no backend logic changes)

---

## User Review Required

> [!IMPORTANT]
> The storey range dropdown will use standard HDB storey ranges (01-03, 04-06, etc. up to 49-51). Should we include higher floors for newer tall blocks?

> [!NOTE]
> The Block X-Ray link requires passing block and street from results. The existing `/block-xray/{block}/{street}` route will be used.

---

## Proposed Changes

### Templates Layer

---

#### [MODIFY] [base.html](file:///Users/jefflee/Documents/AIProjects/ResaleLens_SG-V1/templates/base.html)

**Fix navigation and add mobile menu:**

1. Remove broken `#about` anchor link
2. Add mobile hamburger button (hidden on desktop)
3. Add `role="navigation"` for accessibility
4. Add active page indicator via Jinja2 conditional

```diff
-<li><a href="#features">Features</a></li>
-<li><a href="#about">About</a></li>
+<li><a href="/data-status">Data Status</a></li>
```

**Add hamburger button markup:**
```html
<button class="hamburger" aria-label="Toggle menu" onclick="toggleMobileMenu()">
  <span></span><span></span><span></span>
</button>
```

---

#### [MODIFY] [index.html](file:///Users/jefflee/Documents/AIProjects/ResaleLens_SG-V1/templates/index.html)

**1. Replace storey range text input with dropdown:**

```diff
-<input type="text" id="storey_range" name="storey_range" required placeholder="e.g., 04 TO 06" />
+<select id="storey_range" name="storey_range" required>
+  <option value="">Select storey range</option>
+  <option value="01 TO 03">01 - 03</option>
+  <option value="04 TO 06">04 - 06</option>
+  <option value="07 TO 09">07 - 09</option>
+  <option value="10 TO 12">10 - 12</option>
+  <option value="13 TO 15">13 - 15</option>
+  <option value="16 TO 18">16 - 18</option>
+  <option value="19 TO 21">19 - 21</option>
+  <option value="22 TO 24">22 - 24</option>
+  <option value="25 TO 27">25 - 27</option>
+  <option value="28 TO 30">28 - 30</option>
+  <option value="31 TO 33">31 - 33</option>
+  <option value="34 TO 36">34 - 36</option>
+  <option value="37 TO 39">37 - 39</option>
+  <option value="40 TO 42">40 - 42</option>
+  <option value="43 TO 45">43 - 45</option>
+  <option value="46 TO 48">46 - 48</option>
+  <option value="49 TO 51">49 - 51</option>
+</select>
```

**2. Add accessible tab pattern (ARIA):**

```diff
-<div class="input-mode-tabs">
-  <button id="postal-code-tab" class="tab-button active" onclick="switchInputMode('postal-code')">
+<div class="input-mode-tabs" role="tablist">
+  <button id="postal-code-tab" class="tab-button active" 
+          role="tab" aria-selected="true" aria-controls="postal-code-mode"
+          tabindex="0" onclick="switchInputMode('postal-code')">
```

**3. Add missing flat types:**

```diff
 <option value="EXECUTIVE">EXECUTIVE</option>
+<option value="1 ROOM">1 ROOM</option>
+<option value="2 ROOM">2 ROOM</option>
+<option value="MULTI-GENERATION">MULTI-GENERATION</option>
```

---

#### [MODIFY] [results.html](file:///Users/jefflee/Documents/AIProjects/ResaleLens_SG-V1/templates/results.html)

**Enable Block X-Ray navigation:**

```diff
-<button class="btn btn-secondary" disabled title="Coming soon in PR6">View Block X-Ray</button>
+<a class="btn btn-secondary" href="/block-xray/{{ explainability.filters_applied.block }}/{{ explainability.filters_applied.street | urlencode }}">
+  View Block X-Ray
+</a>
```

**Improve "Check Another Unit" behavior:**

```diff
-onclick="document.querySelector('form').reset(); document.querySelector('#results-container').innerHTML = '';"
+onclick="resetAndScrollToForm()"
```

Add JavaScript function:
```javascript
function resetAndScrollToForm() {
  document.querySelector('#fair-value-form').reset();
  document.querySelector('#results-container').innerHTML = '';
  document.querySelector('.fair-value-form').scrollIntoView({ behavior: 'smooth' });
}
```

---

### Styles Layer

---

#### [MODIFY] [styles.css](file:///Users/jefflee/Documents/AIProjects/ResaleLens_SG-V1/static/styles.css)

**1. Improve text contrast for accessibility:**

```diff
-  --text-light: #6b7280;
+  --text-light: #4b5563;  /* WCAG AA compliant */
```

**2. Add mobile hamburger menu styles:**

```css
/* Mobile Menu */
.hamburger {
  display: none;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.5rem;
}

.hamburger span {
  display: block;
  width: 24px;
  height: 3px;
  background-color: var(--text-color);
  margin: 4px 0;
  transition: var(--transition-fast);
}

@media (max-width: 768px) {
  .hamburger {
    display: block;
  }
  
  .nav-links {
    display: none;
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    background: var(--bg-color);
    flex-direction: column;
    padding: 1rem;
    box-shadow: var(--shadow-lg);
  }
  
  .nav-links.open {
    display: flex;
  }
}
```

**3. Add focus styles for accessibility:**

```css
.tab-button:focus,
.btn:focus,
input:focus,
select:focus {
  outline: none;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.3);
}
```

---

## Files Changed Summary

| File | Change Type | Description |
|------|-------------|-------------|
| `templates/base.html` | Modify | Fix nav links, add hamburger menu |
| `templates/index.html` | Modify | Storey dropdown, ARIA tabs, flat types |
| `templates/results.html` | Modify | Enable Block X-Ray link |
| `static/styles.css` | Modify | Contrast, mobile menu, focus styles |

---

## Verification Plan

### Automated Tests

**Existing API tests (should still pass):**
```bash
uv run pytest tests/test_api_fair_value.py -v
```

The storey_range change is frontend-only; the backend `parse_storey_range()` already accepts "01 TO 03" format strings.

---

### Manual Verification

**Test 1: Storey Range Dropdown**
1. Run dev server: `uv run python -m resalelens.main`
2. Navigate to `http://localhost:8000`
3. Verify storey range is now a dropdown (not text input)
4. Select various storey ranges and submit Fair Value form
5. Confirm results appear correctly

**Test 2: Block X-Ray Navigation**
1. Complete a Fair Value search
2. In results, click "View Block X-Ray" button
3. Verify it navigates to `/block-xray/{block}/{street}` page
4. Verify Block X-Ray data loads correctly

**Test 3: Navigation Fixes**
1. Check that nav links work (Home, Data Status)
2. Verify no broken `#about` link
3. On mobile (resize browser < 768px), verify hamburger menu appears
4. Click hamburger to open/close mobile menu

**Test 4: Accessibility**
1. Tab through the Fair Value form
2. Verify focus ring appears on tabs, inputs, buttons
3. Verify tab buttons can be activated via keyboard (Enter/Space)

---

## Rollback Plan

All changes are template/CSS only. Rollback by reverting the 4 modified files. No database or backend changes.

---

## Dependencies

None. This PR can be implemented independently.
