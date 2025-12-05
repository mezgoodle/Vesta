from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """Base Pydantic model with common configuration."""

    model_config = ConfigDict(from_attributes=True)


class BaseSchemaInDB(BaseSchema):
    """Base schema for DB models including common fields."""

    id: int
    created_at: datetime
    updated_at: datetime | None = None
