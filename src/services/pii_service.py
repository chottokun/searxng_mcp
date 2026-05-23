import re
from typing import List
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_anonymizer import AnonymizerEngine
from src.config import settings
from src.schemas import ResultSet

class PiiService:
    """
    個人情報（PII）および機密ワードの検出・匿名化を行うサービス。
    """
    def __init__(self):
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()
        self._register_custom_recognizers()

    def _register_custom_recognizers(self):
        """
        日本の電話番号、マイナンバー、およびカスタム機密ワードを検出するための
        カスタムRecognizerを登録します。
        """
        # 1. 日本の電話番号 (ハイフンあり・なし)
        jp_phone_pattern = Pattern(
            name="jp_phone_pattern",
            regex=r"0\d{1,4}-\d{1,4}-\d{4}|0\d{9,10}",
            score=0.9
        )
        jp_phone_recognizer = PatternRecognizer(
            supported_entity="PHONE_NUMBER",
            patterns=[jp_phone_pattern],
            supported_language="en"  # デフォルトの英語アナライザー上で動作させるため en に設定
        )
        self.analyzer.registry.add_recognizer(jp_phone_recognizer)

        # 2. マイナンバー (12桁の数字)
        my_number_pattern = Pattern(
            name="my_number_pattern",
            regex=r"\b\d{12}\b",
            score=0.95
        )
        my_number_recognizer = PatternRecognizer(
            supported_entity="MY_NUMBER",
            patterns=[my_number_pattern],
            supported_language="en"
        )
        self.analyzer.registry.add_recognizer(my_number_recognizer)

        # 3. カスタム機密ワード (SENSITIVE_WORDS)
        if settings.SENSITIVE_WORDS:
            sensitive_patterns = []
            for i, word in enumerate(settings.SENSITIVE_WORDS):
                # 日本語にも部分一致でマッチするよう単語境界 \b は使用せず、エスケープした単語そのものにマッチさせます
                sensitive_patterns.append(
                    Pattern(
                        name=f"sensitive_word_{i}",
                        regex=re.escape(word),
                        score=1.0
                    )
                )
            sensitive_recognizer = PatternRecognizer(
                supported_entity="SENSITIVE_WORD",
                patterns=sensitive_patterns,
                supported_language="en"
            )
            self.analyzer.registry.add_recognizer(sensitive_recognizer)

    def inspect_query(self, q: str) -> str:
        """
        検索クエリを検査し、設定に基づいてPIIや機密ワードのブロックまたは匿名化を行います。
        
        Args:
            q: 検査対象のクエリ文字列
            
        Returns:
            匿名化されたクエリ（PII_BLOCK_LEVEL="anonymize"の場合）
            
        Raises:
            ValueError: PIIまたは機密ワードが検出され、PII_BLOCK_LEVEL="block"または機密ワード検出の場合
        """
        if not settings.PII_DETECTION_ENABLED or settings.PII_BLOCK_LEVEL == "off":
            return q

        # 検出対象エンティティのリスト（機密ワードとマイナンバーも含める）
        entities = settings.PII_ENTITIES + ["SENSITIVE_WORD", "MY_NUMBER"]

        results = self.analyzer.analyze(
            text=q,
            language="en",
            entities=entities
        )

        if not results:
            return q

        # 機密ワードが含まれているか確認
        has_sensitive_word = any(res.entity_type == "SENSITIVE_WORD" for res in results)
        
        # 機密ワードが検知された場合、またはPII検知かつブロックレベルが "block" の場合
        if has_sensitive_word or settings.PII_BLOCK_LEVEL == "block":
            detected_types = list(set(res.entity_type for res in results))
            detected_str = ", ".join(detected_types)
            raise ValueError(
                f"送信不可能な個人情報または機密ワードがクエリ内に検出されたため、検索をブロックしました。(検出タイプ: {detected_str})"
            )

        # 匿名化して検索を実行する場合
        if settings.PII_BLOCK_LEVEL == "anonymize":
            anonymized_result = self.anonymizer.anonymize(
                text=q,
                analyzer_results=results
            )
            return anonymized_result.text

        return q

    def mask_results(self, result_set: ResultSet) -> ResultSet:
        """
        検索結果のタイトルとコンテンツに含まれる個人情報や機密情報をマスキングします。
        
        Args:
            result_set: マスキング対象の検索結果セット
            
        Returns:
            マスキング処理済みの検索結果セット
        """
        if not settings.PII_DETECTION_ENABLED or not settings.PII_MASK_RESPONSE:
            return result_set

        entities = settings.PII_ENTITIES + ["SENSITIVE_WORD", "MY_NUMBER"]

        for item in result_set.results:
            # タイトルのマスキング
            if item.title:
                title_results = self.analyzer.analyze(
                    text=item.title,
                    language="en",
                    entities=entities
                )
                if title_results:
                    item.title = self.anonymizer.anonymize(
                        text=item.title,
                        analyzer_results=title_results
                    ).text

            # コンテンツ（スニペット）のマスキング
            if item.content:
                content_results = self.analyzer.analyze(
                    text=item.content,
                    language="en",
                    entities=entities
                )
                if content_results:
                    item.content = self.anonymizer.anonymize(
                        text=item.content,
                        analyzer_results=content_results
                    ).text

        return result_set

def get_pii_service() -> PiiService:
    return PiiService()
