"""
Database configuration and session management.
"""

from sqlmodel import Session, SQLModel, create_engine

from app.core.settings import get_settings

settings = get_settings()

# Create database engine
engine = create_engine(
    settings.database_url,
    echo=settings.database_echo,
    connect_args={"check_same_thread": False}
    if settings.database_url.startswith(("sqlite://", "sqlite:///"))
    else {},
)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
