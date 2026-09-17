"""
Tests for production database configuration and PostgreSQL URL normalization.
"""

import pytest
from app.core.config import Settings
from app.db.session import engine


def test_postgres_url_normalization_postgres_prefix():
    """Verify postgres:// is converted to postgresql+asyncpg://"""
    raw_url = "postgres://aquora:secret@host.internal:5432/aquora_db"
    settings = Settings(DATABASE_URL=raw_url)
    assert settings.DATABASE_URL == "postgresql+asyncpg://aquora:secret@host.internal:5432/aquora_db"


def test_postgres_url_normalization_postgresql_prefix():
    """Verify postgresql:// is converted to postgresql+asyncpg://"""
    raw_url = "postgresql://aquora:secret@host.internal:5432/aquora_db"
    settings = Settings(DATABASE_URL=raw_url)
    assert settings.DATABASE_URL == "postgresql+asyncpg://aquora:secret@host.internal:5432/aquora_db"


def test_postgres_url_normalization_asyncpg_prefix_unchanged():
    """Verify postgresql+asyncpg:// is left unchanged"""
    raw_url = "postgresql+asyncpg://aquora:secret@host.internal:5432/aquora_db"
    settings = Settings(DATABASE_URL=raw_url)
    assert settings.DATABASE_URL == raw_url


def test_engine_initialization_exists():
    """Verify database engine object is instantiated."""
    assert engine is not None
