# Supabase Database Setup Guide

This guide walks you through setting up Supabase PostgreSQL as **the database** for ResaleLens SG.

## Overview

ResaleLens uses **Supabase (PostgreSQL) exclusively** for all environments:
- **Development**: Supabase PostgreSQL (Singapore region)
- **Testing**: SQLite in-memory (for fast test execution only)
- **Production**: Supabase PostgreSQL (Singapore region)

This ensures development environment matches production exactly, eliminating database-specific bugs.

## Prerequisites

- Python 3.11+ installed
- `uv` package manager installed
- Supabase account (free tier is sufficient)
- All dependencies installed via `uv sync`

## Step 1: Create Supabase Project

1. **Sign up or log in** to [Supabase](https://app.supabase.com/)

2. **Create a new project**:
   - Click "New Project"
   - Project name: `ResaleLens SG MVP` (or your preferred name)
   - Database password: Generate a strong password (save this securely!)
   - Region: **Southeast Asia (Singapore)** - `ap-southeast-1`
   - Pricing plan: Free tier

3. **Wait for provisioning**: Takes 2-3 minutes. You'll see a "Project is being set up" message.

## Step 2: Get Connection String

1. **Navigate to Database Settings**:
   - In your Supabase project dashboard
   - Go to: Settings → Database

2. **Copy the Connection String**:
   - Find "Connection string" section
   - Select **"URI"** tab
   - **Use Connection Pooling**: Switch to "Connection Pooling" mode (port 6543)
   - Copy the connection string that looks like:
     ```
     postgresql://postgres.[ref]:[YOUR-PASSWORD]@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres
     ```
   - **Important**: Replace `[YOUR-PASSWORD]` with the database password you set during project creation

3. **Verify the format**:
   - Should start with `postgresql://`
   - Should include `ap-southeast-1` (Singapore region)
   - Should use port `:6543` (connection pooling) or `:5432` (direct)
   - Recommended: Use `:6543` for better performance

## Step 3: Configure Environment

1. **Create `.env.local`** (if it doesn't exist):
   ```bash
   cp .env.example .env.local
   ```

2. **Add your Supabase connection string**:
   ```bash
   # Database Configuration (REQUIRED)
   DATABASE_URL="postgresql://postgres.[ref]:[YOUR-PASSWORD]@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres"
   ```

3. **Verify `.env.local` is git-ignored**:
   - Check `.gitignore` includes `.env.local`
   - This prevents accidentally committing secrets

4. **Validate environment**:
   ```bash
   uv run python scripts/validate_env.py
   ```
   Expected: `✅ DATABASE_URL: SET`

## Step 4: Run Migrations

Apply the PR1 database schema to Supabase:

```bash
# Run all migrations
uv run alembic upgrade head
```

**Expected output**:
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> abc123, Create initial schema
```

**Verify migration success**:
```bash
# Check current migration version
uv run alembic current

# View migration history
uv run alembic history
```

## Step 5: Verify Schema Creation

1. **In Supabase Dashboard**:
   - Go to: Table Editor
   - You should see 6 tables created:
     - `users`
     - `transactions`
     - `blocks`
     - `pois`
     - `leads`
     - `ingestion_runs`

2. **Via command line**:
   ```bash
   uv run python -c "from resalelens.database import engine; from sqlalchemy import inspect; print(inspect(engine).get_table_names())"
   ```
   Expected: `['alembic_version', 'blocks', 'ingestion_runs', 'leads', 'pois', 'transactions', 'users']`

## Step 6: Seed the Database

Populate Supabase with development data:

```bash
# Seed database with test data
uv run python scripts/seed_data.py
```

**Expected output**:
```
🌱 Starting database seed...
✅ Created all database tables
✅ Created 3 ingestion runs
✅ Created 15 blocks
✅ Created 30 POIs
✅ Created 100 transactions
✅ Created 10 leads

✅ Database seeded successfully!
```

**Verify data in Supabase**:
- Go to: Table Editor → Select `transactions`
- You should see 100 transaction records
- Check other tables similarly

## Step 7: Test Application

1. **Start the application**:
   ```bash
   uv run uvicorn src.resalelens.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Verify health endpoint**:
   ```bash
   curl http://localhost:8000/health
   ```
   Expected: `{"status": "ok"}`

## Step 8: Run Tests Against Supabase

Verify all tests pass with PostgreSQL:

```bash
# Run full test suite
uv run pytest -v
```

**All tests should pass**. If any fail, check:
- Connection string is correct
- Migrations ran successfully
- Seed data loaded properly



## Database Architecture

### Application Code
**Always uses Supabase PostgreSQL** via `DATABASE_URL` environment variable.

### Tests
**Use SQLite in-memory** for speed (configured in `tests/conftest.py`):
- Tests run 10-100x faster than PostgreSQL
- No cleanup needed (in-memory)
- SQLAlchemy abstracts database differences

### Why Not SQLite for Development?
- **Production parity**: Dev environment matches prod exactly
- **No surprises**: PostgreSQL-specific features work in dev
- **Simpler**: One database to configure and maintain

## Troubleshooting

### Connection Refused
**Symptom**: `could not connect to server: Connection refused`

**Solutions**:
- Verify connection string is correct
- Check Supabase project is active (not paused)
- Ensure your IP is not blocked (Supabase allows all IPs by default)

### Password Authentication Failed
**Symptom**: `password authentication failed for user "postgres"`

**Solutions**:
- Verify password in connection string matches project password
- URL-encode special characters in password if any
- Reset database password in Supabase dashboard if needed

### Migration Fails
**Symptom**: `ERROR: relation "table_name" already exists`

**Solutions**:
- Database may already have tables from previous attempt
- Reset database: Supabase Dashboard → Settings → Database → Reset database
- Or drop all tables manually and re-run migrations

### Seed Script Fails
**Symptom**: `IntegrityError: duplicate key value`

**Solutions**:
- Clear existing data first: manually delete records in Supabase Table Editor
- Or reset database completely

## Production Deployment

For deploying to production (Railway, Render, etc.):

1. **Set environment variable** in deployment platform:
   ```
   DATABASE_URL=postgresql://postgres.[ref]:[password]@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres
   ```

2. **Run migrations** in deployment pipeline:
   ```bash
   uv run alembic upgrade head
   ```

3. **Do NOT commit** `.env.local` to git (it's already in `.gitignore`)

## Next Steps

After successful Supabase setup:

- **PR2+**: All subsequent PRs should target Supabase for data ingestion
- **Data Ingestion**: Run ingestion jobs to populate real HDB data
- **Monitoring**: Use Supabase dashboard to monitor queries, connections

## Support Resources

- **Supabase Docs**: https://supabase.com/docs/guides/database
- **SQLAlchemy PostgreSQL**: https://docs.sqlalchemy.org/en/20/dialects/postgresql.html
- **Alembic Migrations**: https://alembic.sqlalchemy.org/

---

**Questions or issues?** Check the Supabase dashboard logs or review migration files in `src/resalelens/migrations/versions/`.
