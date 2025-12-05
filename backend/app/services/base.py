from abc import ABC, abstractmethod
from typing import Any


class BaseLLMService(ABC):
    """Abstract base class for LLM services."""

    @abstractmethod
    async def generate_text(self, prompt: str) -> str:
        """Generate text from a prompt."""


class BaseHomeService(ABC):
    """Abstract base class for Home Automation services."""

    @abstractmethod
    async def get_state(self, entity_id: str) -> dict[str, Any]:
        """Get the state of an entity."""

    @abstractmethod
    async def turn_on(self, entity_id: str) -> None:
        """Turn on an entity."""

    @abstractmethod
    async def turn_off(self, entity_id: str) -> None:
        """Turn off an entity."""
