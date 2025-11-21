from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class BaseLLMService(ABC):
    """Abstract base class for LLM services."""
    
    @abstractmethod
    async def generate_text(self, prompt: str) -> str:
        """Generate text from a prompt."""
        pass

class BaseHomeService(ABC):
    """Abstract base class for Home Automation services."""
    
    @abstractmethod
    async def get_state(self, entity_id: str) -> Dict[str, Any]:
        """Get the state of an entity."""
        pass

    @abstractmethod
    async def turn_on(self, entity_id: str) -> None:
        """Turn on an entity."""
        pass

    @abstractmethod
    async def turn_off(self, entity_id: str) -> None:
        """Turn off an entity."""
        pass
