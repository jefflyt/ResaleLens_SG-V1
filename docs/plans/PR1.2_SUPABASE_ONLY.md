# Feature Plan: Supabase-Only Database (Remove SQLite)

> **✅ IMPLEMENTATION STATUS: COMPLETE** (2026-01-10)  
> All core deliverables implemented and verified. Database now uses Supabase exclusively. See [Verification Report](file:///Users/jefflee/.gemini/antigravity/brain/98f7bb22-b5b2-4a13-8154-dd6a3869e5fe/pr1.2_pr2_verification.md) for details.

## 0) Assumptions

1. **Assumption:** User has already created Supabase project and has connection string available
2. **Assumption:** All developers will have access to a Supabase project (shared dev/staging or individual)
3. **Assumption:** Supabase Free Tier is sufficient for MVP development and testing needs

## 1) Clarifying Questions

> [!IMPORTANT]
> **Blocking Questions:**
> 1. Do you already have a Supabase project set up with the connection string?
> 2. Should each developer use their own Supabase project, or share one dev/staging database?
> 3. Should we keep the SQLite code in tests for fast test execution, or also migrate tests to PostgreSQL?

## 2) Feature Summary

**Goal:** Simplify database architecture by removing SQLite completely and using Supabase (PostgreSQL) as the sole database for all environments (development, testing, production).

**User Story:** As a developer, I want to use only Supabase for the database so that my local development environment matches production exactly, eliminating SQLite-specific bugs and simplifying configuration.

**Acceptance Criteria:**
- [ ] SQLite references removed from all code, configs, and documentation
- [ ] `DATABASE_URL` in `.env.example` defaults to Supabase format (with placeholder)
- [ ] `config.py` no longer has SQLite fallback logic
- [ ] All documentation refers only to Supabase/PostgreSQL
- [ ] `README.md` setup instructions require Supabase connection string
- [ ] Tests run against PostgreSQL (or test database container if needed)
- [ ] `scripts/setup_db.py` works with PostgreSQL only
- [ ] `.gitignore` no longer references SQLite database files
- [ ] Alembic migrations verified to work with PostgreSQL
- [ ] Connection test script validates Supabase connection only

**Non-goals (explicit):**
- Not adding Docker/local PostgreSQL container (Supabase-only)
- Not keeping SQLite as fallback or alternative
- Not modifying the database schema (schema remains from PR1)
- Not changing Alembic migration system (already PostgreSQL-compatible)

## 3) Approach Overview

**Proposed UX (high-level):**
- Developer experience: Setup requires Supabase connection string from day 1
- No more "local SQLite for quick start" option
- Clearer error messages if `DATABASE_URL` not set or invalid

**Proposed API (high-level):**
- No API changes (database abstraction through SQLAlchemy remains)
- Better error handling if database connection fails

**Proposed Data Changes (high-level):**
- No schema changes
- Remove `data/*.db` files and directory structure for SQLite
- Keep `data/.gitkeep` for potential future use (CSV dumps, exports)

**Auth/AuthZ Rules (if any):**
- No changes to authentication (still using PR0's User model)

## 4) PR Plan

**PR Title:** Remove SQLite, Use Supabase as Sole Database

**Branch Name:** `pr1.2-supabase-only`

**Scope (in):**
- Remove SQLite references from code and configuration
- Update all documentation to require Supabase
- Simplify `config.py` database URL handling
- Update connection test scripts
- Update `.env.example` with Supabase-only template

**Out of Scope (explicit):**
- Database schema changes (already defined in PR1)
- Docker/local PostgreSQL setup
- Test database improvements beyond PostgreSQL compatibility
- Migration system changes (Alembic already works)
- Performance optimizations

**Key Changes by Layer:**

**Frontend:**
- No changes (frontend doesn't interact with database directly)

**Backend:**
- **`src/resalelens/config.py`**:
  - Remove SQLite fallback: `DATABASE_URL` required, no default to `sqlite:///`
  - Add validation: Ensure `DATABASE_URL` starts with `postgresql://`
  - Better error message if not set

- **`src/resalelens/database.py`**:
  - Review for any SQLite-specific code (likely none due to SQLAlchemy abstraction)
  - Add connection error handling with clear messages

- **`scripts/test_connections.py`**:
  - Remove SQLite detection logic
  - Only check for PostgreSQL/Supabase connection
  - Fail gracefully with setup instructions if connection fails

- **`scripts/validate_env.py`**:
  - Add `DATABASE_URL` to required variables
  - Validate format (must be PostgreSQL connection string)

**Data:**
- No schema changes
- Remove existing SQLite database files from `.gitignore` exceptions
- Clean up `data/` directory (remove `.db` files)

**Infra/Config:**
- **`.env.example`**:
  - Remove SQLite example
  - Make Supabase `DATABASE_URL` required (no default)
  - Add clear comments about getting connection string

- **`.gitignore`**:
  - Remove SQLite-specific patterns (`*.db`, `*.sqlite`, `*.sqlite3`)
  - Keep `data/` directory structure for future use

- **`README.md`**:
  - Add Supabase setup as Step 1 (before `uv sync`)
  - Remove references to "SQLite for local" vs "Supabase for production"
  - Update quick start to require `DATABASE_URL` first

- **`docs/technical/supabase_setup.md`**:
  - Update to reflect Supabase as the only option
  - Add troubleshooting for common connection issues

- **`docs/technical/context.md`** (if exists):
  - Update architecture docs to remove SQLite references

**Edge Cases to Handle:**
1. **Missing DATABASE_URL**: Clear error message with Supabase setup link
2. **Invalid connection string**: Validate format before attempting connection
3. **First-time setup**: Guide users through Supabase project creation
4. **Test execution**: Ensure tests don't fail without explicit Supabase setup instructions

**Migration/Compatibility Notes:**
- **Breaking change**: Existing local SQLite databases will no longer work
- Developers must run `alembic upgrade head` against Supabase after pulling changes
- Existing `.env.local` files need `DATABASE_URL` updated to Supabase
- No data migration needed (fresh start for MVP)

## 5) Testing & Verification

**Automated Tests:**

**Unit:**
- All existing unit tests should pass (using test Supabase database)
- `tests/conftest.py` may need updates for PostgreSQL test database setup
- Consider using separate Supabase project for CI/tests

**Integration:**
- `tests/test_database.py` (if exists) validates PostgreSQL connection
- Ingestion tests run against PostgreSQL

**E2E (only if needed):**
- Not needed for this change (database abstraction unchanged)

**Manual Verification Checklist:**
- [ ] Clone fresh repo → Setup fails with clear message if no `DATABASE_URL`
- [ ] Set `DATABASE_URL` to Supabase → `uv run python scripts/test_connections.py` passes
- [ ] Run `uv run alembic upgrade head` → Tables created in Supabase
- [ ] Run `uv run pytest` → All tests pass
- [ ] Trigger ingestion → Data appears in Supabase dashboard
- [ ] Check Supabase logs → No SQLite-related errors in logs
- [ ] Start dev server → Application works with Supabase
- [ ] Check `README.md` → Setup instructions are clear and accurate

**Commands to Run:**
```bash
# Install:
uv sync

# Set DATABASE_URL in .env.local (required):
# DATABASE_URL=postgresql://postgres.[ref]:[password]@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres

# Validate environment:
uv run python scripts/validate_env.py

# Test connection:
uv run python scripts/test_connections.py

# Run migrations:
uv run alembic upgrade head

# Dev:
uv run uvicorn src.resalelens.main:app --reload

# Test:
uv run pytest

# Lint:
uv run ruff check .
uv run mypy src/
```

## 6) Rollback Plan

**If issues arise:**
1. Revert PR (git revert)
2. Restore SQLite fallback in `config.py`
3. Re-add SQLite patterns to `.gitignore`
4. Update documentation back to dual-database setup

**Data safety:**
- No data loss risk (Supabase data remains intact)
- Local SQLite databases (if any) can be kept as backups
- Alembic migrations are reversible with `alembic downgrade`

## 7) Follow-ups (optional)

**Future enhancements for later PRs:**
- Add Docker Compose with local PostgreSQL for developers without Supabase access
- Implement test database fixtures using pytest-postgresql or Docker test containers
- Add database connection pooling configuration for high-traffic scenarios
- Create database backup/restore scripts for Supabase
- Add database health check endpoint (`/health/db`)

---

## Implementation Notes

### Priority Files to Update (in order)

1. **Configuration** (highest priority):
   - `.env.example`
   - `src/resalelens/config.py`

2. **Documentation**:
   - `README.md`
   - `docs/technical/supabase_setup.md`

3. **Scripts**:
   - `scripts/validate_env.py`
   - `scripts/test_connections.py`

4. **Cleanup**:
   - `.gitignore`
   - Remove `data/*.db` files

5. **Testing**:
   - Update `tests/conftest.py` if needed
   - Run full test suite

### Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Developers without Supabase access blocked | High | Provide clear Supabase setup guide in README |
| Tests fail without PostgreSQL | Medium | Document test database setup in CONTRIBUTING.md |
| CI/CD requires Supabase credentials | Medium | Use Supabase test project with limited access |
| Slower local development (network latency) | Low | Acceptable trade-off for prod parity |

---

**Status:** Ready for review and implementation
