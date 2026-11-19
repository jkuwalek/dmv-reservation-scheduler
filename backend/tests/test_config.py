import pytest

from dmvwatch.config import Settings


def test_settings_read_from_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DMVWATCH_DATABASE_URL", "postgresql+asyncpg://u:p@db:5432/x")
    monkeypatch.setenv("DMVWATCH_REDIS_URL", "redis://cache:6379/0")
    settings = Settings()
    assert settings.database_url == "postgresql+asyncpg://u:p@db:5432/x"
    assert settings.redis_url == "redis://cache:6379/0"


def test_sweep_interval_has_a_sane_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DMVWATCH_DATABASE_URL", "postgresql+asyncpg://u:p@db:5432/x")
    monkeypatch.setenv("DMVWATCH_REDIS_URL", "redis://cache:6379/0")
    assert Settings().sweep_interval_seconds == 300


def test_a_missing_database_url_is_an_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DMVWATCH_DATABASE_URL", raising=False)
    monkeypatch.setenv("DMVWATCH_REDIS_URL", "redis://cache:6379/0")
    with pytest.raises(ValueError):
        Settings()
