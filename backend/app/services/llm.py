from google.genai import Client
from google.genai.types import ThinkingConfig

from app.core.config import settings


class LLMService:
    def __init__(self):
        self.api_key = settings.GOOGLE_API_KEY
        self.client = Client(api_key=self.api_key)
        self.model = settings.GOOGLE_MODEL_NAME

    def generate_text(self, prompt: str) -> str:
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=ThinkingConfig(thinking_config=0),
        )
        return response.text

    def close(self):
        self.client.close()
