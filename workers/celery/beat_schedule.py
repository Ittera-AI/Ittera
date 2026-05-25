"""
Celery Beat schedule — periodic background tasks.

  ENABLE_PLACEHOLDER_TASKS=true   → enables the demo/placeholder tasks
                                    (radar scan, performance sync, weekly reports)
  ENABLE_LINKEDIN_SYNC=true       → enables the 24h LinkedIn post re-sync for all
                                    active users (Sprint 2 — always safe to enable
                                    once real LinkedIn credentials are configured)
"""

import os

from celery.schedules import crontab

_enable_placeholder_tasks = os.getenv("ENABLE_PLACEHOLDER_TASKS", "false").lower() == "true"
_enable_linkedin_sync = os.getenv("ENABLE_LINKEDIN_SYNC", "false").lower() == "true"

# ── Placeholder / demo tasks ──────────────────────────────────────────────────
_placeholder_tasks: dict = (
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

# ── Sprint 2: LinkedIn periodic re-sync ───────────────────────────────────────
# Runs sync_all_linkedin_users at 3am UTC daily.
# Keeps post data and Report Context (Layer 3) fresh.
# Only enabled when ENABLE_LINKEDIN_SYNC=true.
_linkedin_tasks: dict = (
    {
        "linkedin-sync-all-users-daily": {
            "task": "workers.celery.tasks.scraper.sync_all_linkedin_users",
            "schedule": crontab(hour=3, minute=0),  # 3am UTC daily
        },
    }
    if _enable_linkedin_sync
    else {}
)

BEAT_SCHEDULE = {**_placeholder_tasks, **_linkedin_tasks}
