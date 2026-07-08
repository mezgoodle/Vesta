from app.schemas.base import BaseSchema, BaseSchemaInDB


class FactBase(BaseSchema):
    fact_content: str
    category: str | None = None


class FactCreate(FactBase):
    pass


class FactUpdate(BaseSchema):
    fact_content: str | None = None
    category: str | None = None


class FactInDBBase(FactBase, BaseSchemaInDB):
    user_id: int


class FactResponse(FactInDBBase):
    pass
