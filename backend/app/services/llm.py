import httpx

from app.core.config import settings
from app.services.base import BaseLLMService


class OpenAILLMService(BaseLLMService):
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.client = httpx.AsyncClient(timeout=30.0)

    async def generate_text(self, prompt: str) -> str:
        # TODO: Implement actual OpenAI API call
        # response = await self.client.post(
        #     "https://api.openai.com/v1/chat/completions",
        #     headers={"Authorization": f"Bearer {self.api_key}"},
        #     json={
        #         "model": "gpt-4",
        #         "messages": [{"role": "user", "content": prompt}]
        #     }
        # )
        # return response.json()["choices"][0]["message"]["content"]

        return f"Mock response for: {prompt}"

    async def close(self):
        await self.client.aclose()
