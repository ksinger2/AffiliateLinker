"""Base agent class."""

from abc import ABC, abstractmethod
from loguru import logger
from src.database import get_session, SystemLog


class BaseAgent(ABC):
    """Base class for all agents."""

    name: str = "base"

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.db = get_session()

    def log(self, action: str, details: str = "", level: str = "INFO"):
        """Log agent activity to database."""
        log_entry = SystemLog(
            agent=self.name,
            action=action,
            details=details,
            level=level
        )
        self.db.add(log_entry)
        self.db.commit()

        if level == "ERROR":
            logger.error(f"[{self.name}] {action}: {details}")
        elif level == "WARNING":
            logger.warning(f"[{self.name}] {action}: {details}")
        else:
            logger.info(f"[{self.name}] {action}: {details}")

    @abstractmethod
    async def run(self):
        """Run the agent's main task."""
        pass

    @abstractmethod
    async def status(self) -> dict:
        """Get agent status."""
        pass
