import os
import pytest
from src.config import Settings

def test_sensitive_words_loading_from_env(mocker):
    # Mock environment variable
    mocker.patch.dict(os.environ, {"SENSITIVE_WORDS": '["env_confidential", "env_secret"]'})

    # Create a new Settings instance to load from mocked environment
    # Note: Settings(model_config=...) might need careful handling if we want to bypass .env file
    # But since .env doesn't exist in the environment, it should be fine.
    new_settings = Settings()

    assert "env_confidential" in new_settings.SENSITIVE_WORDS
    assert "env_secret" in new_settings.SENSITIVE_WORDS
    assert len(new_settings.SENSITIVE_WORDS) == 2

def test_sensitive_words_default_empty():
    # Ensure default is empty when no env var is set
    # We might need to ensure the env var is NOT set for this test
    if "SENSITIVE_WORDS" in os.environ:
        del os.environ["SENSITIVE_WORDS"]

    new_settings = Settings()
    assert new_settings.SENSITIVE_WORDS == []
