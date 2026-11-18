import logging
from apscheduler.schedulers.background import BackgroundScheduler
from app.config import settings
from app.database import SessionLocal
from app.services.followup_service import evaluate_due_followups, generate_followup_email
from app.services.reply_service import poll_gmail_replies

logger = logging.getLogger("scheduler")

scheduler = BackgroundScheduler()


def run_hourly_followup_job():
    """Evaluate due follow-ups every hour and generate drafts for pending follow-ups."""
    logger.info("Executing scheduled hourly follow-up check...")
    db = SessionLocal()
    try:
        due = evaluate_due_followups(db)
        logger.info("Found %d leads due for follow-up.", len(due))
        for item in due:
            try:
                generate_followup_email(db, item["influencer_id"])
                logger.info("Generated follow-up draft for lead #%d (%s)", item["influencer_id"], item["username"])
            except Exception as e:
                logger.error("Error generating follow-up for influencer %s: %s", item["influencer_id"], e)
    except Exception as e:
        logger.error("Error running follow-up job: %s", e)
    finally:
        db.close()


def run_reply_polling_job():
    """Poll Gmail threads for new inbound messages every few minutes."""
    logger.info("Executing scheduled Gmail reply polling...")
    db = SessionLocal()
    try:
        count = poll_gmail_replies(db)
        if count > 0:
            logger.info("Processed %d new inbound replies.", count)
    except Exception as e:
        logger.error("Error running reply polling job: %s", e)
    finally:
        db.close()


def start_scheduler():
    if not scheduler.running:
        scheduler.add_job(
            run_hourly_followup_job,
            "interval",
            hours=settings.FOLLOWUP_CHECK_INTERVAL_HOURS,
            id="followup_job",
            replace_existing=True
        )
        scheduler.add_job(
            run_reply_polling_job,
            "interval",
            minutes=settings.REPLY_POLL_INTERVAL_MINUTES,
            id="reply_polling_job",
            replace_existing=True
        )
        scheduler.start()
        logger.info("APScheduler background tasks initialized.")


def shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler stopped.")
