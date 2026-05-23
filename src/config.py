from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    環境変数からロードされるアプリケーション設定。
    """
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    # SearXNGの設定
    SEARXNG_URL: str = "http://localhost:8080"
    SEARXNG_TIMEOUT: float = 10.0

    # 個人情報（PII）検出および機密ワードフィルタリングの設定
    PII_DETECTION_ENABLED: bool = True
    
    # PII検知時の動作レベル: "block" (検索を拒否してエラーを返す) または "anonymize" (匿名化して検索を実行する) または "off" (無効)
    PII_BLOCK_LEVEL: str = "block"
    
    # 検索結果に含まれる個人情報をマスキングしてAIに返却するかどうか
    PII_MASK_RESPONSE: bool = False
    
    # 検出・ブロック対象とする特定の機密ワードリスト（小文字で定義、部分一致でフィルタリング）
    SENSITIVE_WORDS: list[str] = []
    
    # Presidioで検出対象とするPIIエンティティのリスト
    PII_ENTITIES: list[str] = [
        "PERSON",
        "EMAIL_ADDRESS",
        "PHONE_NUMBER",
        "IP_ADDRESS",
        "CREDIT_CARD",
        "LOCATION"
    ]

    # CORS 設定
    ALLOW_ORIGINS: list[str] = ["*"]

settings = Settings()
