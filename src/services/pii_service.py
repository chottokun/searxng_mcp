import re
from functools import lru_cache
from typing import List
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from src.config import settings
from src.schemas import ResultSet

class PiiService:
    """
    個人情報（PII）および機密ワードの検出・匿名化を行うサービス。
    日本語（ja_core_news_sm）および英語（en_core_web_sm）のspaCyモデルを組み合わせ、
    日・英両言語の混在クエリでも高い精度で検出を行います。
    """
    def __init__(self):
        # 多言語（英語・日本語）に対応したNLPエンジンの設定
        nlp_config = {
            "nlp_engine_name": "spacy",
            "models": [
                {"lang_code": "en", "model_name": "en_core_web_sm"},
                {"lang_code": "ja", "model_name": "ja_core_news_sm"}
            ]
        }
        provider = NlpEngineProvider(nlp_configuration=nlp_config)
        nlp_engine = provider.create_engine()
        
        self.analyzer = AnalyzerEngine(nlp_engine=nlp_engine)
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
        for lang in ["en", "ja"]:
            jp_phone_recognizer = PatternRecognizer(
                supported_entity="PHONE_NUMBER",
                patterns=[jp_phone_pattern],
                supported_language=lang
            )
            self.analyzer.registry.add_recognizer(jp_phone_recognizer)

        # 2. マイナンバー (12桁の数字)
        # 日本語テキスト内でも単語境界に依存せず正しくマッチするよう、(?<!\d)...(?!\d) を使用します
        my_number_pattern = Pattern(
            name="my_number_pattern",
            regex=r"(?<!\d)\d{12}(?!\d)",
            score=0.95
        )
        for lang in ["en", "ja"]:
            my_number_recognizer = PatternRecognizer(
                supported_entity="MY_NUMBER",
                patterns=[my_number_pattern],
                supported_language=lang
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
            for lang in ["en", "ja"]:
                sensitive_recognizer = PatternRecognizer(
                    supported_entity="SENSITIVE_WORD",
                    patterns=sensitive_patterns,
                    supported_language=lang
                )
                self.analyzer.registry.add_recognizer(sensitive_recognizer)

    def _analyze_multilingual(self, text: str, entities: List[str]) -> list:
        """
        英語（en）と日本語（ja）の両方のNLPモデル・認識器で解析を行い、結果を統合します。
        スパン（位置）が重複する場合、より高スコアまたは詳細なエンティティを優先してマージします。
        """
        if not text:
            return []

        results_en = self.analyzer.analyze(
            text=text,
            language="en",
            entities=entities
        )
        results_ja = self.analyzer.analyze(
            text=text,
            language="ja",
            entities=entities
        )

        merged = list(results_en)

        for res_ja in results_ja:
            overlap = False
            for res_en in merged:
                # 完全に重なっているか、一部重複している場合
                if not (res_ja.end <= res_en.start or res_ja.start >= res_en.end):
                    overlap = True
                    # スコアが高い方を優先する。同スコアの場合は詳細な日本語NERモデルを優先
                    if res_ja.score >= res_en.score:
                        merged.remove(res_en)
                        merged.append(res_ja)
                    break
            if not overlap:
                merged.append(res_ja)

        # IP_ADDRESS 検出の厳密な検証（誤検出の排除）
        validated_results = []
        for res in merged:
            if res.entity_type == "IP_ADDRESS":
                start = res.start
                end = res.end
                
                # スパンの直前・直後が IP アドレスの一部になり得る文字（16進数、コロン、ドット）の場合は
                # 部分一致による誤検知とみなして除外します。
                if start > 0 and text[start-1] in "0123456789abcdefABCDEF:.":
                    continue
                if end < len(text) and text[end] in "0123456789abcdefABCDEF:.":
                    continue
                
                ip_str = text[start:end]
                # もしコロンもドットも含まない単なる単語ならスキップ
                if "." not in ip_str and ":" not in ip_str:
                    continue
                try:
                    import ipaddress
                    ipaddress.ip_address(ip_str)
                    validated_results.append(res)
                except ValueError:
                    # 無効なIPアドレスなので誤検知として除外
                    continue
            else:
                validated_results.append(res)

        return validated_results

    def _protect_invalid_ips(self, text: str) -> tuple[str, dict[str, str]]:
        """
        IPアドレスの形式（ドット区切りの4つの数値、またはコロンを含む16進文字列）を持つが、
        バリデーションで無効と判断された文字列を、一時的に無害なプレースホルダーに退避させます。
        これにより、Presidio 等の NLP エンジンによる誤検知を防止します。
        """
        if not text:
            return text, {}

        placeholder_map = {}
        counter = 0

        # IPv4の見た目: 数字.数字.数字.数字
        IPV4_LIKE = r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"
        
        # IPv6の見た目: コロンを含む16進数の塊（前後に他のIP文字が続かないこと）
        IPV6_LIKE = (
            r"(?<![0-9a-fA-F.:])(?:[0-9a-fA-F]{1,4}:){1,7}[0-9a-fA-F]{1,4}(?![0-9a-fA-F.:])|"
            r"(?<![0-9a-fA-F.:])(?:[0-9a-fA-F]{1,4}:){1,7}:(?![0-9a-fA-F.:])|"
            r"(?<![0-9a-fA-F.:]):(?::[0-9a-fA-F]{1,4}){1,7}(?![0-9a-fA-F.:])|"
            r"(?<![0-9a-fA-F.:])::[0-9a-fA-F]{1,4}(?![0-9a-fA-F.:])|"
            r"(?<![0-9a-fA-F.:])::(?![0-9a-fA-F.:])"
        )
        
        def replacer(match: re.Match) -> str:
            nonlocal counter
            ip_str = match.group(0)
            try:
                import ipaddress
                ipaddress.ip_address(ip_str)
                # 有効なIPアドレスなら置換しない
                return ip_str
            except ValueError:
                # 無効なIPアドレスは一時的に退避
                placeholder = f"__INVALID_IP_{counter}__"
                placeholder_map[placeholder] = ip_str
                counter += 1
                return placeholder

        # IPv4とIPv6に該当する無効なIP候補を保護
        protected_text = text
        protected_text = re.sub(IPV4_LIKE, replacer, protected_text)
        protected_text = re.sub(IPV6_LIKE, replacer, protected_text)
        return protected_text, placeholder_map

    def _restore_invalid_ips(self, text: str, placeholder_map: dict[str, str]) -> str:
        """
        退避された無効なIPアドレスのプレースホルダーを元の文字列に復元します。
        """
        restored = text
        for placeholder, original in placeholder_map.items():
            restored = restored.replace(placeholder, original)
        return restored

    def _redact_secrets_and_ips(self, text: str) -> str:
        """
        GitHubトークン、OpenAI APIキー、およびIPアドレス（検証付き）をマスクします。
        """
        if not text:
            return text

        # 1. API キー & クレジットカードのマスク
        GITHUB_TOKEN_PATTERN = r"gh[pousr]_[A-Za-z0-9_]{36,255}"
        OPENAI_API_KEY_PATTERN = r"sk-[a-zA-Z0-9]{48,}"
        CREDIT_CARD_PATTERN = r"\b(?:\d{4}[ -]?){3}\d{4}\b"
        
        redacted = text
        redacted = re.sub(GITHUB_TOKEN_PATTERN, "[REDACTED_TOKEN]", redacted)
        redacted = re.sub(OPENAI_API_KEY_PATTERN, "[REDACTED_KEY]", redacted)
        redacted = re.sub(CREDIT_CARD_PATTERN, "[REDACTED_CC]", redacted)

        # 2. IPアドレスのマスク (Lookaround + ipaddress 検証)
        # 前後にIPアドレスを構成しうる文字が続かない英数字・記号の塊を抽出
        IP_CANDIDATE_PATTERN = r"(?<![0-9a-fA-F.:])[0-9a-fA-F.:]+(?![0-9a-fA-F.:])"
        
        def ip_replacer(match: re.Match) -> str:
            ip_str = match.group(0)
            if "." not in ip_str and ":" not in ip_str:
                return ip_str
            try:
                import ipaddress
                ipaddress.ip_address(ip_str)
                return "[REDACTED_IP]"
            except ValueError:
                return ip_str

        redacted = re.sub(IP_CANDIDATE_PATTERN, ip_replacer, redacted)
        return redacted

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

        # API キーと IPアドレスを先行してマスク
        sanitized_q = self._redact_secrets_and_ips(q)

        # 無効な IPアドレス（誤検出の原因）を一時的に保護
        protected_q, ip_map = self._protect_invalid_ips(sanitized_q)

        # 検出対象エンティティのリスト（機密ワードとマイナンバーも含める）
        entities = settings.PII_ENTITIES + ["SENSITIVE_WORD", "MY_NUMBER"]

        # 日・英の両言語モデルで重複なく解析
        results = self._analyze_multilingual(protected_q, entities)

        if not results:
            return self._restore_invalid_ips(protected_q, ip_map)

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
                text=protected_q,
                analyzer_results=results
            )
            return self._restore_invalid_ips(anonymized_result.text, ip_map)

        return self._restore_invalid_ips(protected_q, ip_map)

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
            # API キー & IP アドレスを先行してマスク
            if item.title:
                item.title = self._redact_secrets_and_ips(item.title)
            if item.content:
                item.content = self._redact_secrets_and_ips(item.content)

            # 無効な IPアドレス（誤検出の原因）を一時的に保護
            title_map = {}
            content_map = {}
            if item.title:
                item.title, title_map = self._protect_invalid_ips(item.title)
            if item.content:
                item.content, content_map = self._protect_invalid_ips(item.content)

            # タイトルのマスキング
            if item.title:
                title_results = self._analyze_multilingual(item.title, entities)
                if title_results:
                    item.title = self.anonymizer.anonymize(
                        text=item.title,
                        analyzer_results=title_results
                    ).text

            # コンテンツ（スニペット）のマスキング
            if item.content:
                content_results = self._analyze_multilingual(item.content, entities)
                if content_results:
                    item.content = self.anonymizer.anonymize(
                        text=item.content,
                        analyzer_results=content_results
                    ).text

            # 無効な IPアドレスを復元
            if item.title:
                item.title = self._restore_invalid_ips(item.title, title_map)
            if item.content:
                item.content = self._restore_invalid_ips(item.content, content_map)

        return result_set

@lru_cache(maxsize=1)
def get_pii_service() -> PiiService:
    return PiiService()
