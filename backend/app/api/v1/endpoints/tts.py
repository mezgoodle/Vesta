from fastapi import APIRouter
from fastapi.responses import Response

from app.api.deps import CurrentUser, TTSServiceDep
from app.schemas.tts import TTSSynthesizeRequest

router = APIRouter()


@router.post("/synthesize")
async def synthesize_speech(
    body: TTSSynthesizeRequest,
    service: TTSServiceDep,
    current_user: CurrentUser,
) -> Response:
    """
    Convert text to speech audio in OGG/OPUS format.

    Args:
        body: Request body containing the text to synthesize.
        service: Injected GoogleTTSService instance.
        current_user: Authenticated user (required).

    Returns:
        Raw OGG/OPUS audio bytes with ``audio/ogg`` content type.
    """
    audio_bytes = await service.synthesize(body.text)

    return Response(
        content=audio_bytes,
        media_type="audio/ogg",
        headers={"Content-Disposition": 'inline; filename="speech.ogg"'},
    )
