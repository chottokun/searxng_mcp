# Research: SearXNG Search Parameters

## Decision
The MCP server will initially support the following SearXNG search parameters:
- `q`: The search query string (mandatory).
- `categories`: The search categories to use (e.g., 'news', 'images').
- `time_range`: The time range for the search (e.g., 'day', 'week', 'month').

## Rationale
These parameters represent the most common and high-value search filters for a general-purpose search API. Starting with this core set allows us to deliver value quickly while keeping the initial implementation focused. Additional parameters can be added in the future based on specific user needs and feedback.

## Alternatives Considered
- **Support all SearXNG parameters**: This would significantly increase the complexity of the initial implementation and testing. Many parameters are highly specific and may not be valuable for most users of this MCP server.
- **Support no parameters (query only)**: This would be too limiting and would not take advantage of the power of SearXNG.
