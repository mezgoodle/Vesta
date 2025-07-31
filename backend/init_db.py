#!/usr/bin/env python3
"""
Database initialization script.
"""

from app.core.database import create_db_and_tables
from app.core.settings import get_settings


def main():
    """Initialize the database."""
    print("Initializing database...")
    settings = get_settings()
    print(f"Database URL: {settings.database_url}")

    create_db_and_tables()
    print("Database tables created successfully!")


if __name__ == "__main__":
    main()
