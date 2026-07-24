from pydantic import Field

from app.schemas.base import BaseSchema, BaseSchemaInDB


class FactBase(BaseSchema):
    fact_content: str = Field(..., max_length=1000, description="The fact content")
    category: str | None = Field(
        None, max_length=100, description="Optional classification category"
    )


class FactCreate(FactBase):
    pass


class FactUpdate(BaseSchema):
    fact_content: str | None = Field(
        None, max_length=1000, description="The updated fact content"
    )
    category: str | None = Field(
        None, max_length=100, description="Optional classification category"
    )


class FactInDBBase(FactBase, BaseSchemaInDB):
    user_id: int


class FactResponse(FactInDBBase):
    pass
