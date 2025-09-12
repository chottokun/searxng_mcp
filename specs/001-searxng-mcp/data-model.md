# Data Model

This document outlines the data structures used in the SearXNG MCP server.

## Entities

### SearchQuery
Represents an incoming search request from a user.

**Fields**:
- `q` (string, required): The user's search query.
- `categories` (string, optional): A comma-separated list of categories to search in (e.g., "news,images").
- `time_range` (string, optional): The time range for the search (e.g., "day", "week").

### SearchResult
Represents a single search result item returned from SearXNG.

**Fields**:
- `title` (string): The title of the search result.
- `url` (string): The URL of the search result.
- `snippet` (string): A short description or snippet of the content.

### ResultSet
Represents the full response sent back to the user.

**Fields**:
- `results` (array of `SearchResult`): A list of the search results found.
