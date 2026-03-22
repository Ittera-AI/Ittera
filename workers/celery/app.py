from celery import Celery

from workers.celery.beat_schedule import BEAT_SCHEDULE

celery_app = Celery(
    "iterra",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1",
    include=[
        "workers.celery.tasks.radar_scan",
        "workers.celery.tasks.performance_sync",
        "workers.celery.tasks.weekly_reports",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule=BEAT_SCHEDULE,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)

if __name__ == "__main__":
    celery_app.start()
