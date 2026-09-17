from app.core.config import settings


def test_settings_load():
    """Verify application configuration defaults load properly."""
    assert settings.PROJECT_NAME == "AQUORA — Urban Flood Intelligence & Response Platform"
    assert settings.API_V1_STR == "/api/v1"
    assert settings.LOG_LEVEL in ["INFO", "DEBUG", "WARNING", "ERROR"]
    assert len(settings.CORS_ORIGINS) > 0
    assert "https://aquora-nine.vercel.app" in settings.CORS_ORIGINS


def test_cors_origins_parsing():
    """Verify parse_cors_origins handles JSON arrays, lists, comma-separated strings, single quotes, and trailing slashes."""
    from app.core.config import Settings

    # Case 1: JSON array string with trailing slash
    s1 = Settings(CORS_ORIGINS='["http://localhost:5173", "https://aquora-nine.vercel.app/"]')
    assert s1.CORS_ORIGINS == ["http://localhost:5173", "https://aquora-nine.vercel.app"]

    # Case 2: Comma separated string
    s2 = Settings(CORS_ORIGINS="http://localhost:5173, https://aquora-nine.vercel.app")
    assert s2.CORS_ORIGINS == ["http://localhost:5173", "https://aquora-nine.vercel.app"]

    # Case 3: Single quoted array string
    s3 = Settings(CORS_ORIGINS="['http://localhost:5173', 'https://aquora-nine.vercel.app/']")
    assert s3.CORS_ORIGINS == ["http://localhost:5173", "https://aquora-nine.vercel.app"]

    # Case 4: Single origin string
    s4 = Settings(CORS_ORIGINS="https://aquora-nine.vercel.app/")
    assert s4.CORS_ORIGINS == ["https://aquora-nine.vercel.app"]

