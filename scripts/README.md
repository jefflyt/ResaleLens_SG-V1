# Scripts Directory

This directory contains utility scripts for managing and testing the ResaleLens ingestion system.

## Active Scripts (3)

### `check_ingestion_status.py`
Check the status of recent ingestion runs.

```bash
uv run python scripts/check_ingestion_status.py
```

**Purpose:** Monitor ingestion health and view recent run history.

---

### `fix_stuck_ingestions.py`
Fix ingestion runs stuck in "IN_PROGRESS" status.

```bash
uv run python scripts/fix_stuck_ingestions.py
```

**Purpose:** Clean up stuck ingestion runs (e.g., after process crashes).

---

### `test_weekly_ingestion.py`
Run complete weekly ingestion sequence for testing.

```bash
uv run python scripts/test_weekly_ingestion.py
```

**Purpose:** 
- Test the complete weekly ingestion workflow
- Verify all 6 jobs run successfully
- Generate performance report
- Uses **incremental mode** to match production behavior

**⚠️ Warning:** This runs actual ingestions against your database. Use with caution.

---

## Archived Scripts

Historical migration and setup scripts are in `scripts/archive/`:
- One-time database migrations
- Initial setup scripts
- Seed data scripts

These are kept for reference but should not be run in production.

---

## Production Ingestion

**Do not use scripts for production ingestions!**

Production ingestions run automatically via the scheduler:
- **When:** Every Sunday at 03:00 SGT
- **How:** APScheduler background jobs
- **Config:** `src/resalelens/scheduler.py`

For manual triggers, use the admin API endpoints:
- `POST /admin/ingest/hdb_transactions`
- `POST /admin/ingest/pois`
- etc.

---

## Script Behavior

### Incremental vs Full Ingestion

**Production Scheduler (Sundays 03:00 SGT):**
- HDB Transactions: **Incremental** (only new records)
- HDB Property Info: **Change detection** (only updated blocks)
- Expected runtime: ~17-19 minutes

**Test Script:**
- Matches production behavior with incremental mode
- Expected runtime: ~17-19 minutes

---

## Best Practices

1. **Check status first:** Use `check_ingestion_status.py` before testing
2. **Fix stuck runs:** Run `fix_stuck_ingestions.py` if needed
3. **Test carefully:** Test script runs real ingestions, not mocks
4. **Monitor production:** Check logs on Sunday mornings after scheduled runs
5. **Use admin API:** For manual production triggers, use API endpoints instead of scripts
