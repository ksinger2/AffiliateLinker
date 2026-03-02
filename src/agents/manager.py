"""Manager Agent - Orchestrates all agents and monitors system health."""

import asyncio
from datetime import datetime
from loguru import logger
from src.agents.base import BaseAgent
from src.agents.product_researcher import ProductResearcherAgent
from src.agents.account_manager import AccountManagerAgent
from src.agents.strategist import StrategistAgent
from src.database import Product, Post, Metric, SystemLog, get_session


class ManagerAgent(BaseAgent):
    """Agent that orchestrates and monitors all other agents."""

    name = "manager"

    # Automation levels
    LEVEL_MANUAL = 0
    LEVEL_AUTO_DISCOVERY = 1
    LEVEL_AUTO_POST_APPROVAL = 2
    LEVEL_AUTO_POST = 3
    LEVEL_AUTO_STRATEGY = 4
    LEVEL_FULL_AUTO = 5

    def __init__(self, config: dict = None):
        super().__init__(config)
        self.automation_level = config.get("automation_level", self.LEVEL_AUTO_POST_APPROVAL)

        # Initialize sub-agents
        self.researcher = ProductResearcherAgent(config.get("product_researcher", {}))
        self.account_mgr = AccountManagerAgent(config.get("account_manager", {}))
        self.strategist = StrategistAgent(config.get("strategist", {}))

        self.alerts = config.get("alerts", {
            "low_pipeline_threshold": 10,
            "post_failure_threshold": 3,
            "engagement_drop_percent": 30
        })

    async def run(self):
        """Run the main orchestration loop."""
        self.log("start", f"Manager starting at automation level {self.automation_level}")

        # Check system health
        health = await self._check_health()
        if not health["healthy"]:
            self.log("alert", f"Health issues: {health['issues']}", level="WARNING")

        # Run agents based on automation level
        results = {}

        if self.automation_level >= self.LEVEL_AUTO_DISCOVERY:
            results["discovery"] = await self._run_discovery()

        if self.automation_level >= self.LEVEL_AUTO_POST_APPROVAL:
            results["approval"] = await self._auto_approve_products()

        if self.automation_level >= self.LEVEL_AUTO_POST:
            results["posting"] = await self._run_posting()

        if self.automation_level >= self.LEVEL_AUTO_STRATEGY:
            results["strategy"] = await self._run_strategy()

        # Generate daily metrics
        await self._record_daily_metrics()

        self.log("complete", f"Cycle complete: {results}")
        return results

    async def _check_health(self) -> dict:
        """Check system health and return status."""
        issues = []

        # Check pipeline
        pending = self.db.query(Product).filter_by(status="pending").count()
        if pending < self.alerts["low_pipeline_threshold"]:
            issues.append(f"Low product pipeline: {pending}")

        # Check recent failures
        recent_errors = (
            self.db.query(SystemLog)
            .filter(SystemLog.level == "ERROR")
            .filter(SystemLog.timestamp >= datetime.now().replace(hour=0, minute=0))
            .count()
        )
        if recent_errors > self.alerts["post_failure_threshold"]:
            issues.append(f"High error rate: {recent_errors} errors today")

        return {
            "healthy": len(issues) == 0,
            "issues": issues,
            "pipeline_size": pending,
            "errors_today": recent_errors
        }

    async def _run_discovery(self) -> dict:
        """Run product discovery."""
        try:
            products_found = await self.researcher.run()
            return {"status": "success", "products_found": products_found}
        except Exception as e:
            self.log("error", f"Discovery failed: {e}", level="ERROR")
            return {"status": "error", "error": str(e)}

    async def _auto_approve_products(self) -> dict:
        """Auto-approve products that meet criteria."""
        pending = (
            self.db.query(Product)
            .filter_by(status="pending")
            .all()
        )

        approved = 0
        for product in pending:
            # Auto-approve if meets quality thresholds
            if product.rating >= 4.0 and product.review_count >= 50:
                product.status = "approved"
                approved += 1

        self.db.commit()
        return {"approved": approved}

    async def _run_posting(self) -> dict:
        """Run posting cycle."""
        try:
            posts_made = await self.account_mgr.run()
            return {"status": "success", "posts_made": posts_made}
        except Exception as e:
            self.log("error", f"Posting failed: {e}", level="ERROR")
            return {"status": "error", "error": str(e)}

    async def _run_strategy(self) -> dict:
        """Run strategy analysis."""
        try:
            recommendations = await self.strategist.run()
            return {"status": "success", "recommendations": len(recommendations)}
        except Exception as e:
            self.log("error", f"Strategy failed: {e}", level="ERROR")
            return {"status": "error", "error": str(e)}

    async def _record_daily_metrics(self):
        """Record daily metrics snapshot."""
        today = datetime.now().date()

        # Check if today's metrics already exist
        existing = (
            self.db.query(Metric)
            .filter(Metric.date >= datetime(today.year, today.month, today.day))
            .first()
        )

        if existing:
            return  # Already recorded

        # Calculate metrics
        products_today = (
            self.db.query(Product)
            .filter(Product.discovered_at >= datetime(today.year, today.month, today.day))
            .count()
        )

        posts_today = (
            self.db.query(Post)
            .filter(Post.posted_at >= datetime(today.year, today.month, today.day))
            .count()
        )

        total_impressions = sum(p.impressions or 0 for p in self.db.query(Post).all())
        total_clicks = sum(p.clicks or 0 for p in self.db.query(Post).all())
        total_saves = sum(p.saves or 0 for p in self.db.query(Post).all())

        metric = Metric(
            date=datetime.now(),
            products_discovered=products_today,
            posts_made=posts_today,
            total_impressions=total_impressions,
            total_clicks=total_clicks,
            total_saves=total_saves
        )
        self.db.add(metric)
        self.db.commit()

    async def status(self) -> dict:
        """Get comprehensive system status."""
        researcher_status = await self.researcher.status()
        account_status = await self.account_mgr.status()
        strategist_status = await self.strategist.status()
        health = await self._check_health()

        return {
            "agent": self.name,
            "automation_level": self.automation_level,
            "healthy": health["healthy"],
            "issues": health["issues"],
            "agents": {
                "product_researcher": researcher_status,
                "account_manager": account_status,
                "strategist": strategist_status
            }
        }

    async def set_automation_level(self, level: int):
        """Set the automation level."""
        if 0 <= level <= 5:
            self.automation_level = level
            self.log("config", f"Automation level set to {level}")
        else:
            raise ValueError(f"Invalid automation level: {level}")

    async def force_post(self, asin: str):
        """Force post a specific product immediately."""
        product = self.db.query(Product).filter_by(asin=asin).first()
        if not product:
            raise ValueError(f"Product not found: {asin}")

        product.status = "approved"
        self.db.commit()

        return await self.account_mgr._post_product(product)

    async def pause(self):
        """Pause all automated operations."""
        self.automation_level = self.LEVEL_MANUAL
        self.log("control", "System paused")

    async def resume(self, level: int = None):
        """Resume automated operations."""
        self.automation_level = level or self.LEVEL_AUTO_POST_APPROVAL
        self.log("control", f"System resumed at level {self.automation_level}")
