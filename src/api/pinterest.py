"""Pinterest API client."""

import os
import httpx
from typing import Optional
from dataclasses import dataclass
from loguru import logger


@dataclass
class PinterestBoard:
    """Pinterest board data."""
    id: str
    name: str
    description: str
    pin_count: int


@dataclass
class PinterestPin:
    """Pinterest pin data."""
    id: str
    title: str
    description: str
    link: str
    image_url: str
    board_id: str
    created_at: str


class PinterestAPI:
    """Client for Pinterest API v5."""

    def __init__(
        self,
        access_token: str = None,
        app_id: str = None,
        app_secret: str = None
    ):
        self.access_token = access_token or os.getenv("PINTEREST_ACCESS_TOKEN")
        self.app_id = app_id or os.getenv("PINTEREST_APP_ID")
        self.app_secret = app_secret or os.getenv("PINTEREST_APP_SECRET")
        self.base_url = "https://api.pinterest.com/v5"

        if not self.access_token:
            logger.warning("Pinterest access token not configured")

    def _headers(self) -> dict:
        """Get API request headers."""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

    async def get_user(self) -> dict:
        """Get authenticated user info."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/user_account",
                headers=self._headers()
            )
            response.raise_for_status()
            return response.json()

    async def list_boards(self) -> list[PinterestBoard]:
        """List all boards for the authenticated user."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/boards",
                headers=self._headers()
            )
            response.raise_for_status()
            data = response.json()

            return [
                PinterestBoard(
                    id=board["id"],
                    name=board["name"],
                    description=board.get("description", ""),
                    pin_count=board.get("pin_count", 0)
                )
                for board in data.get("items", [])
            ]

    async def create_board(self, name: str, description: str = "") -> PinterestBoard:
        """Create a new board."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/boards",
                headers=self._headers(),
                json={
                    "name": name,
                    "description": description,
                    "privacy": "PUBLIC"
                }
            )
            response.raise_for_status()
            board = response.json()

            return PinterestBoard(
                id=board["id"],
                name=board["name"],
                description=board.get("description", ""),
                pin_count=0
            )

    async def create_pin(
        self,
        board_id: str,
        title: str,
        description: str,
        link: str,
        image_url: str
    ) -> PinterestPin:
        """Create a new pin."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/pins",
                headers=self._headers(),
                json={
                    "board_id": board_id,
                    "title": title,
                    "description": description,
                    "link": link,
                    "media_source": {
                        "source_type": "image_url",
                        "url": image_url
                    }
                }
            )
            response.raise_for_status()
            pin = response.json()

            return PinterestPin(
                id=pin["id"],
                title=pin.get("title", ""),
                description=pin.get("description", ""),
                link=pin.get("link", ""),
                image_url=image_url,
                board_id=board_id,
                created_at=pin.get("created_at", "")
            )

    async def get_pin_analytics(self, pin_id: str, days: int = 30) -> dict:
        """Get analytics for a pin."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/pins/{pin_id}/analytics",
                headers=self._headers(),
                params={
                    "start_date": "2024-01-01",  # TODO: Calculate from days
                    "end_date": "2024-12-31",
                    "metric_types": ["IMPRESSION", "OUTBOUND_CLICK", "PIN_CLICK", "SAVE"]
                }
            )
            response.raise_for_status()
            return response.json()

    async def delete_pin(self, pin_id: str) -> bool:
        """Delete a pin."""
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.base_url}/pins/{pin_id}",
                headers=self._headers()
            )
            return response.status_code == 204
