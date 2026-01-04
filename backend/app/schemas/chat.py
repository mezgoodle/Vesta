from app.schemas.base import BaseSchema, BaseSchemaInDB


class ChatHistoryBase(BaseSchema):
    role: str
    content: str
    user_id: int


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


class ChatResponse(BaseSchema):
    response: str
    user_message_id: int
    assistant_message_id: int
