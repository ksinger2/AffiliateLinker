#!/usr/bin/env python3
"""AffiliateLinker - Automated Pinterest Affiliate System."""

import asyncio
import os
import sys
import yaml
from pathlib import Path
from dotenv import load_dotenv
from loguru import logger

# Load environment variables
load_dotenv()

# Configure logging
logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add("data/app.log", rotation="1 day", retention="7 days", level="DEBUG")


def load_config() -> dict:
    """Load configuration from settings.yaml."""
    config_path = Path("config/settings.yaml")
    if config_path.exists():
        with open(config_path) as f:
            return yaml.safe_load(f)
    return {}


async def main():
    """Main entry point."""
    from src.database import init_db
    from src.agents import ManagerAgent
    from src.scheduler import Scheduler

    logger.info("Starting AffiliateLinker")

    # Initialize database
    init_db()
    logger.info("Database initialized")

    # Load configuration
    config = load_config()

    # Initialize manager agent
    manager = ManagerAgent(config.get("manager", {}))

    # Parse command
    if len(sys.argv) < 2:
        print_usage()
        return

    command = sys.argv[1]

    if command == "run":
        # Run once
        results = await manager.run()
        logger.info(f"Run complete: {results}")

    elif command == "start":
        # Start scheduler for continuous operation
        scheduler = Scheduler(manager)
        scheduler.start()
        logger.info("System running. Press Ctrl+C to stop.")

        try:
            while True:
                await asyncio.sleep(60)
        except KeyboardInterrupt:
            scheduler.stop()
            logger.info("System stopped")

    elif command == "status":
        # Show system status
        status = await manager.status()
        print_status(status)

    elif command == "discover":
        # Run product discovery
        products = await manager.researcher.run()
        logger.info(f"Discovered {products} products")

    elif command == "post":
        # Run posting
        posts = await manager.account_mgr.run()
        logger.info(f"Posted {posts} pins")

    elif command == "strategy":
        # Run strategy analysis
        recs = await manager.strategist.run()
        logger.info(f"Generated {len(recs)} recommendations")

    elif command == "dashboard":
        # Launch dashboard
        os.system("streamlit run src/dashboard/app.py")

    else:
        print_usage()


def print_usage():
    """Print usage information."""
    print("""
AffiliateLinker - Automated Pinterest Affiliate System

Usage:
    python main.py <command>

Commands:
    run         Run all agents once
    start       Start continuous scheduler
    status      Show system status
    discover    Run product discovery only
    post        Run posting only
    strategy    Run strategy analysis
    dashboard   Launch Streamlit dashboard

Setup:
    1. Copy .env.example to .env and fill in your API keys
    2. Edit config/settings.yaml for preferences
    3. Run: python main.py start
""")


def print_status(status: dict):
    """Print formatted status."""
    print("\n=== AffiliateLinker Status ===\n")
    print(f"Automation Level: {status['automation_level']}/5")
    print(f"System Healthy: {'✓' if status['healthy'] else '✗'}")

    if status['issues']:
        print(f"\nIssues:")
        for issue in status['issues']:
            print(f"  - {issue}")

    print(f"\n--- Product Researcher ---")
    pr = status['agents']['product_researcher']
    print(f"  Total Products: {pr['total_products']}")
    print(f"  Pending: {pr['pending_products']}")

    print(f"\n--- Account Manager ---")
    am = status['agents']['account_manager']
    print(f"  Posts Today: {am['posts_today']}/{am['target_posts']}")
    print(f"  Next Post: {am['next_posting_time']}")

    print(f"\n--- Strategist ---")
    st = status['agents']['strategist']
    print(f"  Active Strategies: {st['active_strategies']}")
    print(f"  Last Report: {st['last_report']}")
    print()


if __name__ == "__main__":
    asyncio.run(main())
