# Archived Scripts

This directory contains historical scripts that were used for one-time migrations, setup, and data seeding. They are kept for reference but should **not be run in production**.

## Migration Scripts

### Database Schema Migrations
- `add_postal_sector_column.py` - Added postal_sector column to blocks table
- `add_sgt_columns.py` - Added SGT timestamp columns to ingestion_runs
- `setup_sgt_trigger.py` - Set up database triggers for SGT columns

### Data Migrations
- `backfill_transaction_block_ids.py` - Backfilled block_id for existing transactions
- `populate_blocks_from_transactions.py` - Initial blocks table population

## Setup Scripts

- `setup_db.py` - Initial database creation (use Alembic migrations instead)
- `seed_data.py` - Development database seeding with test data

## Utility Scripts

- `clean_test_db.py` - Test database cleanup

---

## Important Notes

⚠️ **Do not run these scripts in production!**

- These scripts were designed for one-time use during development
- Database schema changes should now use Alembic migrations
- Data backfills should be done through admin API or custom scripts

---

## For Reference Only

These scripts are preserved for:
- Understanding historical database changes
- Reference for future similar migrations
- Documentation of data transformation logic
