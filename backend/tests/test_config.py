from app.core.config import settings


def test_settings_load():
    """Verify application configuration defaults load properly."""
    assert settings.PROJECT_NAME == "AQUORA — Urban Flood Intelligence & Response Platform"
    assert settings.API_V1_STR == "/api/v1"
    assert settings.LOG_LEVEL in ["INFO", "DEBUG", "WARNING", "ERROR"]
    assert len(settings.CORS_ORIGINS) > 0
