from typing import Any

import httpx

from app.core.config import settings
from app.services.base import BaseHomeService


class HomeAssistantService(BaseHomeService):
    """Service for interacting with Home Assistant via REST API."""

    def __init__(self):
        """Initialize the Home Assistant service client."""
        self.base_url = settings.HOME_ASSISTANT_URL
        self.token = settings.HOME_ASSISTANT_TOKEN
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        self.client = httpx.AsyncClient(headers=self.headers, timeout=10.0)

    async def get_state(self, entity_id: str) -> dict[str, Any]:
        """
        Get the current state of a Home Assistant entity.

        Args:
            entity_id: The ID of the entity (e.g., 'light.living_room')

        Returns:
            Dictionary containing the state object
        """
        # TODO: Implement actual HA API call
        # url = f"{self.base_url}/api/states/{entity_id}"
        # response = await self.client.get(url)
        # response.raise_for_status()
        # return response.json()
        return {"entity_id": entity_id, "state": "on", "attributes": {}}

    async def turn_on(self, entity_id: str) -> None:
        """
        Turn on a Home Assistant entity.

        Args:
            entity_id: The ID of the entity to turn on
        """
        # TODO: Implement actual HA API call
        # url = f"{self.base_url}/api/services/homeassistant/turn_on"
        # await self.client.post(url, json={"entity_id": entity_id})
        print(f"Turning on {entity_id}")

    async def turn_off(self, entity_id: str) -> None:
        """
        Turn off a Home Assistant entity.

        Args:
            entity_id: The ID of the entity to turn off
        """
        # TODO: Implement actual HA API call
        # url = f"{self.base_url}/api/services/homeassistant/turn_off"
        # await self.client.post(url, json={"entity_id": entity_id})
        print(f"Turning off {entity_id}")

    async def close(self):
        """Close the HTTP client session."""
        await self.client.aclose()
