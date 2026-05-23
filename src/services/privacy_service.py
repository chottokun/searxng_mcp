import re
from typing import Optional

class PrivacyService:
    """
    Service for sanitizing search queries to prevent information leakage.
    """

    # Regular expressions for common PII
    EMAIL_PATTERN = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    IPV4_PATTERN = r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
    # Basic but effective IPv6 pattern for common use cases
    IPV6_PATTERN = r"(([0-9a-fA-F]{1,4}:){1,7}:|:((:[0-9a-fA-F]{1,4}){1,7}|:)|([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(?::[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(?::[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(?::[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(?::[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6}))"
    CREDIT_CARD_PATTERN = r"\b(?:\d{4}[ -]?){3}\d{4}\b"

    # Common API key patterns
    GITHUB_TOKEN_PATTERN = r"gh[pousr]_[A-Za-z0-9_]{36,255}"
    OPENAI_API_KEY_PATTERN = r"sk-[a-zA-Z0-9]{48,}"

    def redact_query(self, query: Optional[str]) -> Optional[str]:
        """
        Redacts PII and secrets from a search query.
        """
        if query is None:
            return None
        if not query:
            return query

        redacted = query
        redacted = re.sub(self.EMAIL_PATTERN, "[REDACTED_EMAIL]", redacted)
        redacted = re.sub(self.GITHUB_TOKEN_PATTERN, "[REDACTED_TOKEN]", redacted)
        redacted = re.sub(self.OPENAI_API_KEY_PATTERN, "[REDACTED_KEY]", redacted)
        redacted = re.sub(self.IPV4_PATTERN, "[REDACTED_IP]", redacted)

        # Redact IPv6. We use a simpler approach: finding sequences of hex and colons
        # that look like IPv6 addresses.
        redacted = re.sub(r"\b([0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}\b", "[REDACTED_IP]", redacted)

        redacted = re.sub(self.CREDIT_CARD_PATTERN, "[REDACTED_CC]", redacted)

        return redacted

def get_privacy_service() -> PrivacyService:
    return PrivacyService()
