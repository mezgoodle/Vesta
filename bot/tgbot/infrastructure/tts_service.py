"""Bot-side client for the backend TTS synthesis endpoint."""

import aiohttp
from aiohttp import ClientError

from tgbot.infrastructure.base_service import BaseAPIService


class TTSService(BaseAPIService):
    """
    Service for converting text to speech via the backend TTS endpoint.

    Returns raw OGG/OPUS audio bytes that can be sent as a Telegram voice message
    using ``BufferedInputFile``.
    """

    def __init__(self, base_url: str | None = None, timeout: int = 30) -> None:
        """
        Initialize the TTS service.

        Args:
            base_url: Base URL of the backend API. Defaults to config value.
            timeout: Request timeout in seconds (higher than default for audio gen).
        """
        super().__init__(base_url, timeout)

    async def synthesize(self, text: str) -> bytes | None:
        """
        Convert text to speech by calling the backend TTS endpoint.

        Args:
            text: The text to convert to speech.

        Returns:
            Raw OGG/OPUS audio bytes, or None if the request fails.
        """
        url = f"{self.base_url}{self.API_PREFIX}/tts/synthesize"
        request_headers = self._get_headers()

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    url,
                    json={"text": text},
                    headers=request_headers,
                ) as response:
                    if response.status == 200:
                        audio_bytes = await response.read()
                        self.logger.debug(
                            f"TTS synthesis successful, {len(audio_bytes)} bytes"
                        )
                        return audio_bytes

                    # Log error details
                    error_detail = await response.text()
                    self.logger.error(
                        f"TTS synthesis failed with status {response.status}: "
                        f"{error_detail}"
                    )
                    return None

        except ClientError as e:
            self.logger.error(f"Connection error during TTS synthesis: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error during TTS synthesis: {e}")
            return None


tts_service = TTSService()
