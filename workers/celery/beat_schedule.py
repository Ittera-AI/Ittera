import os

from celery.schedules import crontab

_enable_placeholder_tasks = os.getenv("ENABLE_PLACEHOLDER_TASKS", "false").lower() == "true"

BEAT_SCHEDULE = (
    {
        "radar-scan-hourly": {
            "task": "workers.celery.tasks.radar_scan.run_radar_scan",
            "schedule": crontab(minute=0),  # every hour
        },
        "performance-sync-daily": {
            "task": "workers.celery.tasks.performance_sync.sync_performance_data",
            "schedule": crontab(hour=2, minute=0),  # 2am UTC daily
        },
        "weekly-reports-monday": {
            "task": "workers.celery.tasks.weekly_reports.send_weekly_reports",
            "schedule": crontab(hour=8, minute=0, day_of_week=1),  # Monday 8am UTC
        },
    }
    if _enable_placeholder_tasks
    else {}
)
