from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


def start_scheduler(scan_fn):
    """Start the APScheduler with a daily 7AM scan."""
    if scheduler.running:
        return

    scheduler.add_job(
        scan_fn,
        trigger=CronTrigger(hour=7, minute=0),
        id="daily_scan",
        replace_existing=True,
        name="Daily Job Scan"
    )

    scheduler.start()
    logger.info("Scheduler started — daily scan at 7:00 AM")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
