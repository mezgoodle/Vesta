from app.crud.base import CRUDBase
from app.models.chat import ChatSession
from app.schemas.chat import ChatSessionCreate, ChatSessionUpdate


class CRUDSession(CRUDBase[ChatSession, ChatSessionCreate, ChatSessionUpdate]):
    pass


session = CRUDSession(ChatSession)
