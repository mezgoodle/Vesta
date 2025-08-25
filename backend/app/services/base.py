from typing import Any, Generic, Optional, TypeVar

from sqlmodel import Session

from app.repositories.base import BaseRepository

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")
RepositoryType = TypeVar("RepositoryType", bound=BaseRepository)


class BaseService(
    Generic[ModelType, CreateSchemaType, UpdateSchemaType, RepositoryType]
):
    def __init__(self, repository: RepositoryType) -> None:
        self.repository = repository

    def get(self, db: Session, id: int) -> Optional[ModelType]:
        return self.repository.get(db, id)

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> list[ModelType]:
        return self.repository.get_multi(db, skip=skip, limit=limit)

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        return self.repository.create(db, obj_in=obj_in)

    def update(
        self, db: Session, *, id: int, obj_in: UpdateSchemaType | dict[str, Any]
    ) -> Optional[ModelType]:
        db_obj = self.repository.get(db, id)
        if not db_obj:
            return None
        return self.repository.update(db, db_obj=db_obj, obj_in=obj_in)

    def delete(self, db: Session, *, id: int) -> Optional[ModelType]:
        return self.repository.delete(db, id=id)
