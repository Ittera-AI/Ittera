import logging

from workers.celery.app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="workers.celery.tasks.radar_scan.run_radar_scan", bind=True, max_retries=3)
def run_radar_scan(self):
    """Hourly trend scan task. Fetches trending topics for all active users' niches."""
    try:
        logger.info("Starting radar scan task")
        # TODO: fetch active user niches from DB
        # TODO: call TrendRadar.scan() for each niche
        # TODO: store results in DB
        # TODO: notify users of new trends via websocket/notification
        logger.info("Radar scan task completed")
    except Exception as exc:
        logger.error("Radar scan failed: %s", exc)
        raise self.retry(exc=exc, countdown=60)
