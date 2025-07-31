"""Base service for business logic operations."""

from typing import Any, Dict, Generic, List, Optional, TypeVar

from sqlmodel import Session

from app.repositories.base import BaseRepository

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")
RepositoryType = TypeVar("RepositoryType", bound=BaseRepository)


class BaseService(
    Generic[ModelType, CreateSchemaType, UpdateSchemaType, RepositoryType]
):
    """Base service class for business logic operations."""

    def __init__(self, repository: RepositoryType):
        """Initialize service with repository."""
        self.repository = repository

    def get(self, db: Session, id: int) -> Optional[ModelType]:
        """Get a single record by ID."""
        return self.repository.get(db, id)

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """Get multiple records with pagination."""
        return self.repository.get_multi(db, skip=skip, limit=limit)

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        """Create a new record."""
        return self.repository.create(db, obj_in=obj_in)

    def update(
        self, db: Session, *, id: int, obj_in: UpdateSchemaType | Dict[str, Any]
    ) -> Optional[ModelType]:
        """Update an existing record."""
        db_obj = self.repository.get(db, id)
        if not db_obj:
            return None
        return self.repository.update(db, db_obj=db_obj, obj_in=obj_in)

    def delete(self, db: Session, *, id: int) -> Optional[ModelType]:
        """Delete a record by ID."""
        return self.repository.delete(db, id=id)
