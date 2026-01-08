"""Job scheduler setup using APScheduler."""

import logging

from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger(__name__)

# Initialize scheduler
scheduler = BackgroundScheduler()


def sample_scheduled_job() -> None:
    """
    Sample scheduled job that runs periodically.
    
    This is a placeholder for future data ingestion jobs.
    """
    logger.info("Sample scheduled job executed")


def start_scheduler() -> None:
    """Start the APScheduler background scheduler."""
    # Add sample job (runs every hour)
    scheduler.add_job(
        sample_scheduled_job,
        trigger="interval",
        hours=1,
        id="sample_job",
        name="Sample Scheduled Job",
        replace_existing=True,
    )
    
    # Start the scheduler
    scheduler.start()
    logger.info("APScheduler started successfully")


def shutdown_scheduler() -> None:
    """Shutdown the APScheduler gracefully."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("APScheduler shut down successfully")
