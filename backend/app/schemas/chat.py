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
    session_id: int | None = None


class ChatResponse(BaseSchema):
    response: str
    user_message_id: int
    assistant_message_id: int
    session_id: int


class ChatSessionBase(BaseSchema):
    title: str = "New Chat"
    summary: str | None = None


class ChatSessionCreate(ChatSessionBase):
    user_id: int


class ChatSession(ChatSessionBase, BaseSchemaInDB):
    user_id: int


class ChatSessionUpdate(BaseSchema):
    title: str | None = None
    summary: str | None = None
