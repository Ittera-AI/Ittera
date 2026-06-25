"""
Celery Beat schedule — periodic background tasks.

  ENABLE_PLACEHOLDER_TASKS=true   → enables the demo/placeholder tasks
                                    (radar scan, performance sync, weekly reports)
  ENABLE_LINKEDIN_SYNC=true       → enables the 24h LinkedIn post re-sync for all
                                    active users (Sprint 2 — always safe to enable
                                    once real LinkedIn credentials are configured)
  ENABLE_ANALYTICS_TASKS=true     → enables analytics snapshot computation
                                    (runs daily at 1am UTC to cache analytics data)
"""

import os

from celery.schedules import crontab

_enable_placeholder_tasks = os.getenv("ENABLE_PLACEHOLDER_TASKS", "false").lower() == "true"
_enable_linkedin_sync = os.getenv("ENABLE_LINKEDIN_SYNC", "false").lower() == "true"
_enable_analytics_tasks = os.getenv("ENABLE_ANALYTICS_TASKS", "true").lower() == "true"
_enable_learning_loop = os.getenv("ENABLE_LEARNING_LOOP", "false").lower() == "true"

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

# ── Analytics Tasks ─────────────────────────────────────────────────────────────
# Pre-computes daily analytics snapshots for efficient dashboard queries.
# Enabled by default (set ENABLE_ANALYTICS_TASKS=false to disable).
_analytics_tasks: dict = (
    {
        "analytics-snapshot-daily": {
            "task": "workers.celery.tasks.compute_analytics.compute_all_users_snapshots",
            "schedule": crontab(hour=1, minute=0),  # 1am UTC daily (before LinkedIn sync)
        },
        "analytics-cleanup-monthly": {
            "task": "workers.celery.tasks.compute_analytics.delete_old_snapshots",
            "schedule": crontab(hour=4, minute=0, day_of_month=1),  # 1st of month 4am UTC
            "kwargs": {"retention_days": 365},  # Keep 1 year of snapshots
        },
    }
    if _enable_analytics_tasks
    else {}
)

# ── Smart Scheduler Tasks ───────────────────────────────────────────────────────
# AI-powered optimal timing for content scheduling.
# Reviews and optimizes upcoming scheduled posts daily.
_enable_scheduler_tasks = os.getenv("ENABLE_SCHEDULER_TASKS", "true").lower() == "true"

_scheduler_tasks: dict = (
    {
        "schedule-optimization-daily": {
            "task": "workers.celery.tasks.smart_scheduler.daily_schedule_optimization",
            "schedule": crontab(hour=6, minute=0),  # 6am UTC daily
        },
    }
    if _enable_scheduler_tasks
    else {}
)

# ── Self-Learning Content Loop cadence ──────────────────────────────────────────
# Beat-scheduled heartbeat that fans out insight synthesis for every active
# user+platform, in case event-driven runs were missed. Runs at 5am UTC so it
# lands after the 1am analytics snapshot, 2am performance sync, and 3am LinkedIn
# sync. Only enabled when ENABLE_LEARNING_LOOP=true.
_learning_loop_tasks: dict = (
    {
        "insight-cycle-daily": {
            "task": "workers.celery.tasks.learning_loop.run_insight_cycle_all_users",
            "schedule": crontab(hour=5, minute=0),  # 5am UTC daily
        },
    }
    if _enable_learning_loop
    else {}
)

BEAT_SCHEDULE = {
    **_placeholder_tasks,
    **_linkedin_tasks,
    **_analytics_tasks,
    **_scheduler_tasks,
    **_learning_loop_tasks,
}
BEAT_SCHEDULE["publishing-queue-every-five-minutes"] = {
    "task": "workers.celery.tasks.publisher.process_publishing_queue",
    "schedule": crontab(minute="*/5"),
}
