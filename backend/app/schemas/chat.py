import base64

from pydantic import Field

from app.schemas.base import BaseSchema, BaseSchemaInDB
from app.schemas.enums import ChatRole


class ChatHistoryBase(BaseSchema):
    role: ChatRole
    content: str
    user_id: int
    session_id: int


class ChatHistoryCreate(ChatHistoryBase):
    pass


class ChatHistoryUpdate(BaseSchema):
    content: str | None = None


class ChatHistoryInDBBase(ChatHistoryBase, BaseSchemaInDB):
    pass


class ChatHistory(ChatHistoryInDBBase):
    pass


class ChatRequest(BaseSchema):
    user_id: int
    message: str
    want_voice: bool = False
    session_id: int | None = None


class ChatResponse(BaseSchema):
    response: str
    user_message_id: int
    assistant_message_id: int
    session_id: int
    voice_audio: str | None = None

    @classmethod
    def with_voice(
        cls,
        voice_bytes: bytes | None,
        **kwargs,
    ) -> "ChatResponse":
        """Construct response, encoding voice bytes to Base64 if present."""
        voice_audio = (
            base64.b64encode(voice_bytes).decode("utf-8") if voice_bytes else None
        )
        return cls(voice_audio=voice_audio, **kwargs)


class ChatSessionBase(BaseSchema):
    title: str = "New Chat"
    summary: str | None = None


class ChatSessionCreate(ChatSessionBase):
    user_id: int


class ChatSession(ChatSessionBase, BaseSchemaInDB):
    user_id: int
    messages: list[ChatHistory] = Field(default_factory=list)


class ChatSessionUpdate(BaseSchema):
    title: str | None = None
    summary: str | None = None
