import re
import ipaddress
import logging
from typing import Optional

logger = logging.getLogger("searxng_mcp.privacy_service")

class PrivacyService:
    """
    Service for sanitizing search queries to prevent information leakage.
    """

    # Regular expressions for common PII
    EMAIL_PATTERN = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    CREDIT_CARD_PATTERN = r"\b(?:\d{4}[ -]?){3}\d{4}\b"

    # Common API key patterns
    GITHUB_TOKEN_PATTERN = r"gh[pousr]_[A-Za-z0-9_]{36,255}"
    OPENAI_API_KEY_PATTERN = r"sk-[a-zA-Z0-9]{48,}"

    # Extract any block of characters consisting only of hex, dots, or colons
    # that is not preceded or followed by those same characters.
    # This prevents partial match fragmentation on IPv6/IPv4 addresses.
    IP_CANDIDATE_PATTERN = r"(?<![0-9a-fA-F.:])[0-9a-fA-F.:]+(?![0-9a-fA-F.:])"

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
        
        # Redact IP addresses using rigorous validation with the ipaddress module
        def ip_replacer(match: re.Match) -> str:
            ip_str = match.group(0)
            
            # Skip strings that are obviously not IPs (e.g., plain words or numbers without separator)
            if "." not in ip_str and ":" not in ip_str:
                return ip_str
                
            try:
                # Validate if it is a correct IP address
                ipaddress.ip_address(ip_str)
                return "[REDACTED_IP]"
            except ValueError:
                # If invalid, leave the content unchanged
                return ip_str

        # Replace IP candidates with verification
        redacted = re.sub(self.IP_CANDIDATE_PATTERN, ip_replacer, redacted)

        redacted = re.sub(self.CREDIT_CARD_PATTERN, "[REDACTED_CC]", redacted)

        return redacted

def get_privacy_service() -> PrivacyService:
    return PrivacyService()
