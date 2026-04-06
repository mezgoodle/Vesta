from pydantic import BaseModel, Field


class TTSSynthesizeRequest(BaseModel):
    """Request body for the TTS synthesis endpoint."""

    text: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Text to convert to speech (max 5000 characters)",
    )
