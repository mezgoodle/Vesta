"""Google Cloud Text-to-Speech service for converting text to natural speech."""

import asyncio
import logging
import re

from fastapi import HTTPException
from google.api_core.exceptions import GoogleAPIError
from google.cloud import texttospeech
from google.oauth2 import service_account

from app.core.config import settings

# Maximum text length allowed by Google TTS API
MAX_TEXT_LENGTH = 5000

# Default language and voice style for Chirp 3 HD
DEFAULT_LANGUAGE_CODE = "uk-UA"
VOICE_STYLE = "Chirp3-HD-Despina"


class GoogleTTSService:
    """
    Service for converting text to speech using Google Cloud Text-to-Speech API.

    Produces OGG/OPUS audio optimized for Telegram voice messages.
    Uses Chirp 3 HD voices with dynamic language support.
    The same voice style (Despina) works across all supported languages.

    See: https://cloud.google.com/text-to-speech/docs/chirp3-hd

    This service can be used:
    - Via FastAPI Depends() injection in endpoints (use ``google_tts_service`` factory).
    - By direct import from other backend services (use ``google_tts_service_instance``).
    """

    def __init__(self) -> None:
        """
        Initialize the Google TTS client with service account credentials.

        Requires ``GOOGLE_APPLICATION_CREDENTIALS`` to be set in settings
        with the path to the GCP service account JSON key file.
        """
        self.client = texttospeech.TextToSpeechClient(
            credentials=service_account.Credentials.from_service_account_file(
                settings.GOOGLE_APPLICATION_CREDENTIALS
            )
        )
        self.logger = logging.getLogger(self.__class__.__name__)

        # Audio config is the same for all languages
        self.audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.OGG_OPUS,
            speaking_rate=0.75,
            
        )

        self.logger.info("GoogleTTSService initialized successfully")

    @staticmethod
    def _clean_text(text: str) -> str:
        """
        Sanitize text for TTS by removing Markdown formatting and emojis.

        Strips:
        - Markdown bold (``**``), italic (``_``), headers (``#``), backticks
        - Emoji characters (Unicode ranges)
        - Excessive whitespace

        Args:
            text: Raw text potentially containing Markdown and emojis.

        Returns:
            Clean plain text suitable for speech synthesis.
        """
        # Remove Markdown headers (e.g., "## Title" -> "Title")
        cleaned = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)

        # Remove bold/italic markers: **, __, *, _
        cleaned = re.sub(r"\*{1,2}|_{1,2}", "", cleaned)

        # Remove inline code and code blocks
        cleaned = re.sub(r"```[\s\S]*?```", "", cleaned)
        cleaned = re.sub(r"`([^`]*)`", r"\1", cleaned)

        # Remove strikethrough
        cleaned = re.sub(r"~~(.*?)~~", r"\1", cleaned)

        # Remove links but keep text: [text](url) -> text
        cleaned = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", cleaned)

        # Remove emojis (broad Unicode emoji ranges)
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # Emoticons
            "\U0001F300-\U0001F5FF"  # Symbols & Pictographs
            "\U0001F680-\U0001F6FF"  # Transport & Map
            "\U0001F1E0-\U0001F1FF"  # Flags
            "\U00002702-\U000027B0"  # Dingbats
            "\U000024C2-\U0001F251"  # Enclosed characters
            "\U0001F900-\U0001F9FF"  # Supplemental Symbols
            "\U0001FA00-\U0001FA6F"  # Chess Symbols
            "\U0001FA70-\U0001FAFF"  # Symbols Extended-A
            "\U00002600-\U000026FF"  # Misc symbols
            "\U0000200D"  # Zero Width Joiner
            "\U0000FE0F"  # Variation Selector
            "]+",
            flags=re.UNICODE,
        )
        cleaned = emoji_pattern.sub("", cleaned)

        # Collapse multiple whitespace into single space
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        return cleaned

    @staticmethod
    def _detect_language(text: str) -> str:
        """
        Auto-detect language based on character script.

        If more than 30% of alphabetic characters are Cyrillic,
        assumes Ukrainian. Otherwise defaults to English.

        Args:
            text: The text to analyze.

        Returns:
            BCP-47 language code ("uk-UA" or "en-US").
        """
        alpha_chars = [c for c in text if c.isalpha()]
        if not alpha_chars:
            return DEFAULT_LANGUAGE_CODE

        cyrillic_count = sum(
            1 for c in alpha_chars if "\u0400" <= c <= "\u04FF"
        )
        if cyrillic_count > len(alpha_chars) * 0.3:
            return "uk-UA"
        return "en-US"

    def _build_voice(
        self, language_code: str,
    ) -> texttospeech.VoiceSelectionParams:
        """
        Build VoiceSelectionParams for the given language.

        The voice style (Charon) is consistent across languages;
        only the locale prefix changes (e.g., uk-UA, en-US).

        Args:
            language_code: BCP-47 language code (e.g., "uk-UA", "en-US").

        Returns:
            VoiceSelectionParams configured for the requested language.
        """
        voice_name = f"{language_code}-{VOICE_STYLE}"
        return texttospeech.VoiceSelectionParams(
            language_code=language_code,
            name=voice_name,
        )

    async def synthesize(
        self, text: str,
    ) -> bytes:
        """
        Convert text to speech audio in OGG/OPUS format.

        The text is first sanitized (Markdown/emojis removed), then sent
        to the Google Cloud TTS API via ``asyncio.to_thread`` to avoid
        blocking the event loop.

        Language is auto-detected from the text if not explicitly provided.

        Args:
            text: The text to synthesize into speech.

        Returns:
            Raw audio bytes in OGG/OPUS format.

        Raises:
            HTTPException(400): If text is empty or exceeds the character limit.
            HTTPException(502): If the Google TTS API call fails.
        """
        if not text or not text.strip():
            raise HTTPException(status_code=400, detail="Text is required for synthesis")

        # Debug: log raw received text to diagnose encoding issues
        self.logger.debug("Received text for synthesis: %r", text)

        if len(text) > MAX_TEXT_LENGTH:
            raise HTTPException(
                status_code=400,
                detail=f"Text exceeds maximum length of {MAX_TEXT_LENGTH} characters",
            )

        cleaned_text = self._clean_text(text)

        if not cleaned_text:
            raise HTTPException(
                status_code=400,
                detail="Text is empty after sanitization (only contained Markdown/emojis)",
            )

        # Auto-detect language if not provided
        resolved_language = self._detect_language(cleaned_text)

        synthesis_input = texttospeech.SynthesisInput(text=cleaned_text)
        voice = self._build_voice(resolved_language)

        try:
            self.logger.info(
                "Synthesizing speech",
                extra={
                    "json_fields": {
                        "text_length": len(cleaned_text),
                        "language_code": resolved_language,
                        "voice": voice.name,
                        "encoding": "OGG_OPUS",
                    }
                },
            )

            response = await asyncio.to_thread(
                self.client.synthesize_speech,
                input=synthesis_input,
                voice=voice,
                audio_config=self.audio_config,
            )

            audio_bytes: bytes = response.audio_content

            self.logger.info(
                "Speech synthesized successfully",
                extra={
                    "json_fields": {
                        "audio_size_bytes": len(audio_bytes),
                    }
                },
            )

            return audio_bytes

        except GoogleAPIError as e:
            self.logger.error(
                "Google TTS API error during synthesis",
                extra={"json_fields": {"error": str(e)}},
            )
            raise HTTPException(
                status_code=502,
                detail=f"Google TTS API error: {str(e)}",
            ) from e
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(
                "Unexpected error during speech synthesis",
                extra={"json_fields": {"error": str(e)}},
            )
            raise HTTPException(
                status_code=500,
                detail=f"Unexpected error during speech synthesis: {str(e)}",
            ) from e


# Singleton instance — importable by other backend services
google_tts_service_instance = GoogleTTSService()


def google_tts_service() -> GoogleTTSService:
    """Factory for FastAPI Depends() injection."""
    return google_tts_service_instance
