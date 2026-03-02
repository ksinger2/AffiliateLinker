"""Scheduler for automated agent tasks."""

import asyncio
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger


class Scheduler:
    """Manages scheduled jobs for all agents."""

    def __init__(self, manager):
        self.manager = manager
        self.scheduler = AsyncIOScheduler()
        self._setup_jobs()

    def _setup_jobs(self):
        """Set up all scheduled jobs."""
        # Morning product discovery (6 AM)
        self.scheduler.add_job(
            self._run_discovery,
            CronTrigger(hour=6, minute=0),
            id="morning_discovery",
            name="Morning Product Discovery"
        )

        # Posting times throughout the day
        posting_hours = [8, 12, 20, 21, 22, 23]
        for hour in posting_hours:
            for minute in [0, 30]:
                self.scheduler.add_job(
                    self._run_posting,
                    CronTrigger(hour=hour, minute=minute),
                    id=f"post_{hour}_{minute}",
                    name=f"Post at {hour}:{minute:02d}"
                )

        # Evening strategy review (6 PM)
        self.scheduler.add_job(
            self._run_strategy,
            CronTrigger(hour=18, minute=0),
            id="evening_strategy",
            name="Evening Strategy Review"
        )

        # Weekly strategy deep dive (Monday 9 AM)
        self.scheduler.add_job(
            self._run_weekly_strategy,
            CronTrigger(day_of_week="mon", hour=9, minute=0),
            id="weekly_strategy",
            name="Weekly Strategy Analysis"
        )

        # Health check every hour
        self.scheduler.add_job(
            self._health_check,
            CronTrigger(minute=0),
            id="health_check",
            name="Hourly Health Check"
        )

    async def _run_discovery(self):
        """Run product discovery job."""
        logger.info("Running scheduled product discovery")
        try:
            await self.manager.researcher.run()
        except Exception as e:
            logger.error(f"Discovery job failed: {e}")

    async def _run_posting(self):
        """Run posting job."""
        logger.info("Running scheduled posting")
        try:
            await self.manager.account_mgr.run()
        except Exception as e:
            logger.error(f"Posting job failed: {e}")

    async def _run_strategy(self):
        """Run strategy analysis."""
        logger.info("Running scheduled strategy analysis")
        try:
            await self.manager.strategist.run()
        except Exception as e:
            logger.error(f"Strategy job failed: {e}")

    async def _run_weekly_strategy(self):
        """Run weekly deep strategy analysis."""
        logger.info("Running weekly strategy deep dive")
        try:
            await self.manager.strategist.run()
        except Exception as e:
            logger.error(f"Weekly strategy job failed: {e}")

    async def _health_check(self):
        """Run health check."""
        try:
            health = await self.manager._check_health()
            if not health["healthy"]:
                logger.warning(f"Health check issues: {health['issues']}")
        except Exception as e:
            logger.error(f"Health check failed: {e}")

    def start(self):
        """Start the scheduler."""
        self.scheduler.start()
        logger.info("Scheduler started")

    def stop(self):
        """Stop the scheduler."""
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")

    def get_jobs(self) -> list:
        """Get list of scheduled jobs."""
        return [
            {
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None
            }
            for job in self.scheduler.get_jobs()
        ]
