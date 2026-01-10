from app.crud.base import CRUDBase
from app.models.chat import ChatSession
from app.schemas.chat import ChatSessionCreate, ChatSessionUpdate


class CRUDChatSession(CRUDBase[ChatSession, ChatSessionCreate, ChatSessionUpdate]):
    pass


chat_session = CRUDChatSession(ChatSession)
