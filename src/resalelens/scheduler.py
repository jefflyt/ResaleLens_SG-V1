"""Job scheduler setup using APScheduler."""

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from .database import SessionLocal
from .ingestion import (
    ingest_block_pois,
    ingest_hdb_blocks,
    ingest_hdb_postal_codes,
    ingest_hdb_property_info,
    ingest_hdb_transactions,
    ingest_pois,
    ingest_transaction_backfill,
)

logger = logging.getLogger(__name__)

# Initialize scheduler
scheduler = BackgroundScheduler()


def run_hdb_transactions_ingestion() -> None:
    """Scheduled job for HDB transactions ingestion."""
    logger.info("Starting scheduled HDB transactions ingestion...")
    db = SessionLocal()
    try:
        summary = ingest_hdb_transactions(db)
        logger.info(f"HDB transactions ingestion completed: {summary}")
    except Exception as e:
        logger.error(f"HDB transactions ingestion failed: {e}")
    finally:
        db.close()


def run_hdb_blocks_ingestion() -> None:
    """Scheduled job for HDB blocks ingestion."""
    logger.info("Starting scheduled HDB blocks ingestion...")
    db = SessionLocal()
    try:
        summary = ingest_hdb_blocks(db)
        logger.info(f"HDB blocks ingestion completed: {summary}")
    except Exception as e:
        logger.error(f"HDB blocks ingestion failed: {e}")
    finally:
        db.close()


def run_hdb_property_info_ingestion() -> None:
    """Scheduled job for HDB property information ingestion."""
    logger.info("Starting scheduled HDB property info ingestion...")
    db = SessionLocal()
    try:
        summary = ingest_hdb_property_info(db)
        logger.info(f"HDB property info ingestion completed: {summary}")
    except Exception as e:
        logger.error(f"HDB property info ingestion failed: {e}")
    finally:
        db.close()


def run_pois_ingestion() -> None:
    """Scheduled job for POI ingestion (MRT, LRT, supermarkets, clinics, etc.)."""
    logger.info("Starting scheduled POI ingestion...")
    db = SessionLocal()
    try:
        summary = ingest_pois(db)
        logger.info(f"POI ingestion completed: {summary}")
    except Exception as e:
        logger.error(f"POI ingestion failed: {e}")
    finally:
        db.close()


def run_block_pois_calculation() -> None:
    """Scheduled job for block-POI distance calculation."""
    logger.info("Starting scheduled block-POI distance calculation...")
    db = SessionLocal()
    try:
        summary = ingest_block_pois(db)
        logger.info(f"Block-POI distance calculation completed: {summary}")
    except Exception as e:
        logger.error(f"Block-POI distance calculation failed: {e}")
    finally:
        db.close()


def run_transaction_backfill() -> None:
    """Scheduled job for transaction backfill (block_id, latitude, longitude)."""
    logger.info("Starting scheduled transaction backfill...")
    db = SessionLocal()
    try:
        summary = ingest_transaction_backfill(db)
        logger.info(f"Transaction backfill completed: {summary}")
    except Exception as e:
        logger.error(f"Transaction backfill failed: {e}")
    finally:
        db.close()


def run_hdb_postal_codes_ingestion() -> None:
    """Scheduled job for HDB postal codes ingestion."""
    logger.info("Starting scheduled HDB postal codes ingestion...")
    db = SessionLocal()
    try:
        summary = ingest_hdb_postal_codes(db, skip_existing=False)
        logger.info(f"HDB postal codes ingestion completed: {summary}")
    except Exception as e:
        logger.error(f"HDB postal codes ingestion failed: {e}")
    finally:
        db.close()


def start_scheduler() -> None:
    """Start the APScheduler background scheduler with HDB ingestion jobs."""
    # HDB Transactions: Every Sunday 03:00 SGT
    scheduler.add_job(
        run_hdb_transactions_ingestion,
        trigger=CronTrigger(day_of_week="sun", hour=3, minute=0, timezone="Asia/Singapore"),
        id="hdb_transactions_weekly",
        name="HDB Transactions Weekly Ingestion",
        max_instances=1,
        replace_existing=True,
    )

    # HDB Blocks: Every Sunday 03:15 SGT (15 min after transactions)
    scheduler.add_job(
        run_hdb_blocks_ingestion,
        trigger=CronTrigger(day_of_week="sun", hour=3, minute=15, timezone="Asia/Singapore"),
        id="hdb_blocks_weekly",
        name="HDB Blocks Weekly Ingestion",
        max_instances=1,
        replace_existing=True,
    )

    # Transaction Backfill: Every Sunday 03:30 SGT (15 min after blocks)
    scheduler.add_job(
        run_transaction_backfill,
        trigger=CronTrigger(day_of_week="sun", hour=3, minute=30, timezone="Asia/Singapore"),
        id="transaction_backfill_weekly",
        name="Transaction Backfill Weekly",
        max_instances=1,
        replace_existing=True,
    )

    # POIs: Monthly on 1st @ 03:30 SGT (MRT, LRT, supermarkets, clinics, parks, malls, hawkers, schools)
    scheduler.add_job(
        run_pois_ingestion,
        trigger=CronTrigger(day=1, hour=3, minute=30, timezone="Asia/Singapore"),
        id="pois_monthly",
        name="POI Monthly Ingestion",
        max_instances=1,
        replace_existing=True,
    )

    # Block-POI Distances: Monthly on 1st @ 03:45 SGT (15 min after POI ingestion)
    scheduler.add_job(
        run_block_pois_calculation,
        trigger=CronTrigger(day=1, hour=3, minute=45, timezone="Asia/Singapore"),
        id="block_pois_monthly",
        name="Block-POI Distance Monthly Calculation",
        max_instances=1,
        replace_existing=True,
    )

    # HDB Property Info: Monthly on 1st @ 04:00 SGT
    scheduler.add_job(
        run_hdb_property_info_ingestion,
        trigger=CronTrigger(day=1, hour=4, minute=0, timezone="Asia/Singapore"),
        id="hdb_property_info_monthly",
        name="HDB Property Info Monthly Ingestion",
        max_instances=1,
        replace_existing=True,
    )

    # HDB Postal Codes: Monthly on 1st @ 04:15 SGT (after property info)
    scheduler.add_job(
        run_hdb_postal_codes_ingestion,
        trigger=CronTrigger(day=1, hour=4, minute=15, timezone="Asia/Singapore"),
        id="hdb_postal_codes_monthly",
        name="HDB Postal Codes Monthly Ingestion",
        max_instances=1,
        replace_existing=True,
    )

    # Start the scheduler
    scheduler.start()
    logger.info("APScheduler started with ingestion jobs")
    logger.info("  - HDB Transactions: Sundays 03:00 SGT (weekly)")
    logger.info("  - HDB Blocks: Sundays 03:15 SGT (weekly)")
    logger.info("  - Transaction Backfill: Sundays 03:30 SGT (weekly)")
    logger.info("  - POIs: 1st of month 03:30 SGT (monthly)")
    logger.info("  - Block-POI Distances: 1st of month 03:45 SGT (monthly)")
    logger.info("  - HDB Property Info: 1st of month 04:00 SGT (monthly)")
    logger.info("  - HDB Postal Codes: 1st of month 04:15 SGT (monthly)")


def shutdown_scheduler() -> None:
    """Shutdown the APScheduler gracefully."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("APScheduler shut down successfully")
