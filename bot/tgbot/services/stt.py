import asyncio
import logging
from typing import Optional

from google.api_core.client_options import ClientOptions
from google.api_core.exceptions import GoogleAPIError
from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types.cloud_speech import (
    AutoDetectDecodingConfig,
    RecognitionConfig,
    RecognizeRequest,
    RecognizeResponse,
)
from google.oauth2 import service_account

from tgbot.config import config


class GoogleSTTService:
    """
    Google Cloud Speech-to-Text service for converting voice messages to text.

    Supports Ukrainian (uk-UA) as primary language and English (en-US) as alternative.
    """

    def __init__(self):
        """
        Initialize the Google Speech-to-Text client.

        Uses GOOGLE_APPLICATION_CREDENTIALS if it points to a valid file,
        otherwise falls back to Application Default Credentials (ADC) on GCP.
        """
        import os
        import json
        import google.auth

        self.location_code = "us"
        credentials = None
        self.project_id = config.GCP_PROJECT_ID

        if config.GOOGLE_APPLICATION_CREDENTIALS and os.path.exists(
            config.GOOGLE_APPLICATION_CREDENTIALS
        ):
            credentials = service_account.Credentials.from_service_account_file(
                config.GOOGLE_APPLICATION_CREDENTIALS
            )
            # Try to load project_id from the service account key file if not set in config
            try:
                with open(config.GOOGLE_APPLICATION_CREDENTIALS, "r") as f:
                    sa_info = json.load(f)
                    if not self.project_id and "project_id" in sa_info:
                        self.project_id = sa_info["project_id"]
            except Exception:
                pass

        # Fallback to default google credentials to get project ID (e.g. on Cloud Run)
        if not self.project_id:
            try:
                _, default_project_id = google.auth.default()
                if default_project_id:
                    self.project_id = default_project_id
            except Exception as e:
                self.logger.warning("Could not automatically determine GCP project ID", exc_info=e)

        self.client = SpeechClient(
            credentials=credentials,
            client_options=ClientOptions(
                api_endpoint=f"{self.location_code}-speech.googleapis.com"
            ),
        )
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = RecognitionConfig(
            auto_decoding_config=AutoDetectDecodingConfig(),
            language_codes=["en-US", "uk-UA"],
            model="chirp_3",
        )
        self.logger.info(f"GoogleSTTService initialized successfully with project: {self.project_id}")

    async def recognize(self, audio_bytes: bytes) -> Optional[str]:
        """
        Recognize speech from audio bytes.

        Args:
            audio_bytes: Raw audio data in bytes (OGG/OPUS format from Telegram).

        Returns:
            Recognized text as string, or None if recognition failed or audio is empty.

        Raises:
            No exceptions are raised; errors are logged and None is returned.
        """
        if not audio_bytes:
            self.logger.warning("Empty audio bytes provided for recognition")
            return None

        try:
            request = RecognizeRequest(
                recognizer=f"projects/{self.project_id}/locations/{self.location_code}/recognizers/_",
                config=self.config,
                content=audio_bytes,
            )

            # Perform synchronous recognition
            self.logger.debug("Starting speech recognition...")
            response: RecognizeResponse = await asyncio.to_thread(
                self.client.recognize, request=request
            )

            # Extract the best result
            if not response.results:
                self.logger.info("No speech recognized in the audio")
                return None

            # Get the first (most confident) result
            result = response.results[0]
            if not result.alternatives:
                self.logger.info("No alternatives found in recognition result")
                return None

            # Get the transcript from the best alternative
            transcript = result.alternatives[0].transcript
            confidence = result.alternatives[0].confidence

            self.logger.debug(
                f"Speech recognized successfully (confidence: {confidence:.2f}): {transcript[:50]}..."
            )

            return transcript.strip()

        except GoogleAPIError as e:
            self.logger.error("Google API error during speech recognition", exc_info=e)
            return None
        except Exception as e:
            self.logger.error("Unexpected error during speech recognition", exc_info=e)
            return None


stt_service = GoogleSTTService()
