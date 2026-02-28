from app.core.config import Settings


def test_parse_cors_origins_empty():
    s = Settings(cors_origins="")
    assert s.cors_origins == []


def test_parse_cors_origins_comma_separated():
    s = Settings(cors_origins="http://a, http://b")
    assert s.cors_origins == ["http://a", "http://b"]


def test_parse_cors_origins_json_string(monkeypatch):
    # When the value is provided via environment, Settings will coerce the JSON
    monkeypatch.setenv("CORS_ORIGINS", '["http://x","http://y"]')
    s = Settings()
    assert isinstance(s.cors_origins, list)
    assert "http://x" in s.cors_origins
    assert "http://y" in s.cors_origins


def test_settings_env_override(tmp_path, monkeypatch):
    # verify environment variables are respected
    monkeypatch.setenv("APP_NAME", "override")
    s = Settings()
    assert s.app_name == "override"
