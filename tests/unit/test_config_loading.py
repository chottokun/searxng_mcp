import os
import pytest
from src.config import Settings

def test_sensitive_words_loading_from_env(mocker):
    """
    環境変数 SENSITIVE_WORDS に指定されたJSON文字列が正しくリストとしてロードされることをテストします。
    """
    # 環境変数をモック
    mocker.patch.dict(os.environ, {"SENSITIVE_WORDS": '["env_confidential", "env_secret"]'})

    # 新しいSettingsインスタンスを作成し、環境変数から読み込ませる
    new_settings = Settings()

    assert "env_confidential" in new_settings.SENSITIVE_WORDS
    assert "env_secret" in new_settings.SENSITIVE_WORDS
    assert len(new_settings.SENSITIVE_WORDS) == 2

def test_sensitive_words_default_empty():
    """
    環境変数が指定されていない場合、SENSITIVE_WORDS のデフォルト値が空のリストであることをテストします。
    """
    # テスト環境に環境変数がある場合は一時的に削除
    if "SENSITIVE_WORDS" in os.environ:
        del os.environ["SENSITIVE_WORDS"]

    new_settings = Settings()
    assert new_settings.SENSITIVE_WORDS == []
