"""Unit tests for GoogleTTSService."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from google.api_core.exceptions import GoogleAPIError

from app.services.google_tts import GoogleTTSService


@pytest.fixture
def mock_tts_client():
    """Mock the TextToSpeechClient and service account credentials."""
    with (
        patch("app.services.google_tts.texttospeech.TextToSpeechClient") as mock_cls,
        patch("app.services.google_tts.service_account.Credentials.from_service_account_file"),
    ):
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_settings():
    """Mock settings to provide test credentials path."""
    with patch("app.services.google_tts.settings") as mock:
        mock.GOOGLE_APPLICATION_CREDENTIALS = "test-credentials.json"
        yield mock


@pytest.fixture
def service(mock_tts_client, mock_settings) -> GoogleTTSService:
    """Create a GoogleTTSService instance with mocked dependencies."""
    return GoogleTTSService()


# --- synthesize() tests ---


@pytest.mark.asyncio
async def test_synthesize_success(service: GoogleTTSService, mock_tts_client):
    """Test successful speech synthesis returns audio bytes."""
    expected_audio = b"\x00\x01\x02\x03fake-ogg-opus-audio"
    mock_response = MagicMock()
    mock_response.audio_content = expected_audio
    mock_tts_client.synthesize_speech.return_value = mock_response

    result = await service.synthesize("Привіт, це тестове повідомлення")

    assert result == expected_audio
    mock_tts_client.synthesize_speech.assert_called_once()


@pytest.mark.asyncio
async def test_synthesize_empty_text(service: GoogleTTSService):
    """Test that empty text raises HTTP 400."""
    with pytest.raises(HTTPException) as exc:
        await service.synthesize("")
    assert exc.value.status_code == 400
    assert "required" in exc.value.detail.lower()


@pytest.mark.asyncio
async def test_synthesize_whitespace_only(service: GoogleTTSService):
    """Test that whitespace-only text raises HTTP 400."""
    with pytest.raises(HTTPException) as exc:
        await service.synthesize("   ")
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_synthesize_text_too_long(service: GoogleTTSService):
    """Test that text exceeding 5000 chars raises HTTP 400."""
    long_text = "a" * 5001
    with pytest.raises(HTTPException) as exc:
        await service.synthesize(long_text)
    assert exc.value.status_code == 400
    assert "maximum length" in exc.value.detail.lower()


@pytest.mark.asyncio
async def test_synthesize_text_at_limit(service: GoogleTTSService, mock_tts_client):
    """Test that text at exactly 5000 chars is accepted."""
    mock_response = MagicMock()
    mock_response.audio_content = b"audio"
    mock_tts_client.synthesize_speech.return_value = mock_response

    result = await service.synthesize("a" * 5000)
    assert result == b"audio"


@pytest.mark.asyncio
async def test_synthesize_api_error(service: GoogleTTSService, mock_tts_client):
    """Test that Google API errors result in HTTP 502."""
    mock_tts_client.synthesize_speech.side_effect = GoogleAPIError("quota exceeded")

    with pytest.raises(HTTPException) as exc:
        await service.synthesize("Test text")
    assert exc.value.status_code == 502
    assert "Google TTS API error" in exc.value.detail


@pytest.mark.asyncio
async def test_synthesize_unexpected_error(service: GoogleTTSService, mock_tts_client):
    """Test that unexpected errors result in HTTP 500."""
    mock_tts_client.synthesize_speech.side_effect = RuntimeError("unexpected")

    with pytest.raises(HTTPException) as exc:
        await service.synthesize("Test text")
    assert exc.value.status_code == 500
    assert "Unexpected error" in exc.value.detail


@pytest.mark.asyncio
async def test_synthesize_emoji_only_text(service: GoogleTTSService):
    """Test that text containing only emojis raises HTTP 400 after sanitization."""
    with pytest.raises(HTTPException) as exc:
        await service.synthesize("😀🎉🔥")
    assert exc.value.status_code == 400
    assert "empty after sanitization" in exc.value.detail.lower()


# --- _clean_text() tests ---


def test_clean_text_markdown_bold(service: GoogleTTSService):
    """Test that bold markers are removed."""
    assert service._clean_text("This is **bold** text") == "This is bold text"


def test_clean_text_markdown_italic(service: GoogleTTSService):
    """Test that italic markers are removed."""
    assert service._clean_text("This is _italic_ text") == "This is italic text"


def test_clean_text_markdown_headers(service: GoogleTTSService):
    """Test that Markdown headers are removed."""
    result = service._clean_text("## Section Title\nSome content")
    assert result == "Section Title Some content"


def test_clean_text_inline_code(service: GoogleTTSService):
    """Test that inline code backticks are removed but content is kept."""
    assert service._clean_text("Use `print()` here") == "Use print() here"


def test_clean_text_code_blocks(service: GoogleTTSService):
    """Test that code blocks are completely removed."""
    text = "Before\n```python\nprint('hello')\n```\nAfter"
    result = service._clean_text(text)
    assert "print" not in result
    assert "Before" in result
    assert "After" in result


def test_clean_text_links(service: GoogleTTSService):
    """Test that Markdown links are replaced with link text only."""
    result = service._clean_text("Visit [Google](https://google.com) now")
    assert result == "Visit Google now"


def test_clean_text_emojis(service: GoogleTTSService):
    """Test that emojis are stripped."""
    result = service._clean_text("Hello 😀 World 🌍")
    assert "😀" not in result
    assert "🌍" not in result
    assert "Hello" in result
    assert "World" in result


def test_clean_text_combined(service: GoogleTTSService):
    """Test sanitization of text with mixed Markdown and emojis."""
    text = "# **Title** 🎉\n_Some_ `code` here"
    result = service._clean_text(text)
    assert "**" not in result
    assert "#" not in result
    assert "🎉" not in result
    assert "`" not in result
    assert "Title" in result
    assert "Some" in result
    assert "code" in result


def test_clean_text_whitespace_normalization(service: GoogleTTSService):
    """Test that excessive whitespace is collapsed."""
    result = service._clean_text("Hello    World\n\n\nTest")
    assert result == "Hello World Test"


def test_clean_text_strikethrough(service: GoogleTTSService):
    """Test that strikethrough markers are removed."""
    assert service._clean_text("This is ~~deleted~~ text") == "This is deleted text"


# --- _detect_language() tests ---


def test_detect_language_cyrillic(service: GoogleTTSService):
    """Test that Cyrillic text is detected as Ukrainian."""
    assert service._detect_language("Привіт, як справи?") == "uk-UA"


def test_detect_language_latin(service: GoogleTTSService):
    """Test that Latin text is detected as English."""
    assert service._detect_language("Hello, how are you?") == "en-US"


def test_detect_language_mixed_mostly_cyrillic(service: GoogleTTSService):
    """Test that mixed text with mostly Cyrillic is detected as Ukrainian."""
    assert service._detect_language("Привіт hello друже") == "uk-UA"


def test_detect_language_no_alpha(service: GoogleTTSService):
    """Test that text with no alphabetic characters defaults to Ukrainian."""
    assert service._detect_language("123 456!") == "uk-UA"
