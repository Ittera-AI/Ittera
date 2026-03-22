import logging

from workers.celery.app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="workers.celery.tasks.weekly_reports.send_weekly_reports", bind=True, max_retries=2)
def send_weekly_reports(self):
    """Weekly task to send performance summary reports to users."""
    try:
        logger.info("Starting weekly report generation task")
        # TODO: aggregate past week's performance data per user
        # TODO: generate report using AI coach insights
        # TODO: send email reports via configured email provider
        logger.info("Weekly reports sent successfully")
    except Exception as exc:
        logger.error("Weekly reports failed: %s", exc)
        raise self.retry(exc=exc, countdown=600)
