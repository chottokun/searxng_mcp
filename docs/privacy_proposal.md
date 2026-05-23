# Proposal: Information Leakage Prevention for SearXNG MCP Server

To ensure that sensitive information is not leaked during search operations, we propose a multi-layered privacy-preserving architecture.

## 1. Query Redaction (PII Masking)
The primary source of information leakage is the search query itself. Users might accidentally include sensitive data. We will implement a `PrivacyService` that scans search queries for:
- **Email Addresses**: `[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}`
- **IP Addresses (IPv4 and IPv6)**: To prevent leaking internal or target infrastructure details.
- **Credit Card Numbers**: Detecting common 13-16 digit patterns.
- **API Keys / Secrets**: Detecting common patterns for keys (e.g., `sk-`, `ghp_`).

Any detected PII will be replaced with a generic placeholder (e.g., `[REDACTED_EMAIL]`) before being forwarded to the SearXNG instance.

## 2. Resource Management & Transport Security
- **Shared HTTP Client**: Use a single `httpx.AsyncClient` managed by the FastAPI lifespan to ensure proper connection pooling and TLS handling.
- **Internal Communication**: Ensure communication between the MCP server and SearXNG happens over a secure internal network or HTTPS if external.

## 3. Log Masking
The application logs should never contain the original search query if it contained PII. The `PrivacyService` will be used to sanitize log messages before they are written.

## 4. Metadata Stripping
When forwarding requests to SearXNG, we will ensure that:
- The user's original IP address is not forwarded (SearXNG does this by default if configured as a proxy, but we will verify).
- User-Agent strings are generic or stripped.

## Implementation Plan
1. Create `src/services/privacy_service.py` to handle regex-based redaction.
2. Integrate `PrivacyService` into `SearxngService`.
3. Update `SearxngService` to use a shared client for better security and performance.
4. Add unit and integration tests to verify that PII is indeed redacted before leaving the system.
