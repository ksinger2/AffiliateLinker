"""Strategist Agent - Researches and optimizes growth strategies."""

import os
from datetime import datetime
from loguru import logger
from src.agents.base import BaseAgent
from src.database import Strategy, Product, Post, Metric, get_session


class StrategistAgent(BaseAgent):
    """Agent that researches strategies and provides recommendations."""

    name = "strategist"

    def __init__(self, config: dict = None):
        super().__init__(config)
        self.research_frequency = config.get("research_frequency", "weekly")
        self.competitors_to_track = config.get("competitors_to_track", 10)
        self.strategy_dir = "strategy"

    async def run(self):
        """Run strategy research and analysis."""
        self.log("start", "Starting strategy analysis")

        # Analyze current performance
        performance = await self._analyze_performance()

        # Generate recommendations
        recommendations = await self._generate_recommendations(performance)

        # Save strategy documents
        await self._save_strategy_docs(performance, recommendations)

        self.log("complete", f"Generated {len(recommendations)} recommendations")
        return recommendations

    async def _analyze_performance(self) -> dict:
        """Analyze current performance metrics."""
        # Get product stats
        total_products = self.db.query(Product).count()
        pending_products = self.db.query(Product).filter_by(status="pending").count()
        posted_products = self.db.query(Product).filter_by(status="posted").count()

        # Get post stats
        total_posts = self.db.query(Post).count()
        total_impressions = sum(p.impressions or 0 for p in self.db.query(Post).all())
        total_clicks = sum(p.clicks or 0 for p in self.db.query(Post).all())
        total_saves = sum(p.saves or 0 for p in self.db.query(Post).all())

        # Calculate rates
        ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
        save_rate = (total_saves / total_impressions * 100) if total_impressions > 0 else 0

        # Get top performing categories
        category_performance = {}
        for post in self.db.query(Post).all():
            product = post.product
            if product:
                cat = product.category
                if cat not in category_performance:
                    category_performance[cat] = {"clicks": 0, "impressions": 0}
                category_performance[cat]["clicks"] += post.clicks or 0
                category_performance[cat]["impressions"] += post.impressions or 0

        return {
            "total_products": total_products,
            "pending_products": pending_products,
            "posted_products": posted_products,
            "total_posts": total_posts,
            "total_impressions": total_impressions,
            "total_clicks": total_clicks,
            "total_saves": total_saves,
            "ctr": ctr,
            "save_rate": save_rate,
            "category_performance": category_performance
        }

    async def _generate_recommendations(self, performance: dict) -> list[dict]:
        """Generate actionable recommendations based on performance."""
        recommendations = []

        # Low pipeline warning
        if performance["pending_products"] < 10:
            recommendations.append({
                "priority": "high",
                "category": "pipeline",
                "title": "Low Product Pipeline",
                "action": "Increase product discovery rate or expand to new niches",
                "reason": f"Only {performance['pending_products']} products pending"
            })

        # CTR optimization
        if performance["ctr"] < 2.0 and performance["total_impressions"] > 100:
            recommendations.append({
                "priority": "medium",
                "category": "content",
                "title": "Improve Click-Through Rate",
                "action": "Test more compelling titles and descriptions",
                "reason": f"Current CTR is {performance['ctr']:.2f}%, target is 2%+"
            })

        # Category expansion
        if len(performance["category_performance"]) < 5:
            recommendations.append({
                "priority": "low",
                "category": "growth",
                "title": "Expand to More Categories",
                "action": "Add products from beauty, fitness, or tools categories",
                "reason": "More categories = more audience reach"
            })

        # Posting frequency
        if performance["total_posts"] < 50:
            recommendations.append({
                "priority": "medium",
                "category": "growth",
                "title": "Increase Posting Frequency",
                "action": "Aim for 10-15 pins per day consistently",
                "reason": "More posts = more visibility and saves"
            })

        return recommendations

    async def _save_strategy_docs(self, performance: dict, recommendations: list):
        """Save strategy documents to strategy/ directory."""
        os.makedirs(self.strategy_dir, exist_ok=True)

        # Weekly report
        report_content = self._generate_weekly_report(performance, recommendations)
        report_path = os.path.join(self.strategy_dir, "weekly_report.md")
        with open(report_path, "w") as f:
            f.write(report_content)

        # Save recommendations to database
        for rec in recommendations:
            strategy = Strategy(
                category=rec["category"],
                title=rec["title"],
                content=f"{rec['action']}\n\nReason: {rec['reason']}",
                priority={"high": 3, "medium": 2, "low": 1}.get(rec["priority"], 1)
            )
            self.db.add(strategy)
        self.db.commit()

        self.log("docs_saved", f"Saved report to {report_path}")

    def _generate_weekly_report(self, performance: dict, recommendations: list) -> str:
        """Generate weekly report markdown."""
        report = f"""# Weekly Strategy Report

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M")}

## Performance Summary

| Metric | Value |
|--------|-------|
| Total Products | {performance['total_products']} |
| Pending Products | {performance['pending_products']} |
| Posted Products | {performance['posted_products']} |
| Total Posts | {performance['total_posts']} |
| Impressions | {performance['total_impressions']:,} |
| Clicks | {performance['total_clicks']:,} |
| Saves | {performance['total_saves']:,} |
| CTR | {performance['ctr']:.2f}% |
| Save Rate | {performance['save_rate']:.2f}% |

## Recommendations

"""
        for i, rec in enumerate(recommendations, 1):
            report += f"""### {i}. {rec['title']}

**Priority:** {rec['priority'].upper()}
**Category:** {rec['category']}

**Action:** {rec['action']}

**Reason:** {rec['reason']}

---

"""
        return report

    async def status(self) -> dict:
        """Get strategist status."""
        active_strategies = self.db.query(Strategy).filter_by(applied=0).count()

        return {
            "agent": self.name,
            "active_strategies": active_strategies,
            "research_frequency": self.research_frequency,
            "last_report": self._get_last_report_date()
        }

    def _get_last_report_date(self) -> str:
        """Get date of last strategy report."""
        report_path = os.path.join(self.strategy_dir, "weekly_report.md")
        if os.path.exists(report_path):
            mtime = os.path.getmtime(report_path)
            return datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
        return "Never"
