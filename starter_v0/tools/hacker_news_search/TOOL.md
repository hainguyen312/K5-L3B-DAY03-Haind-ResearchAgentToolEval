---
name: hacker_news_search
track: bonus
kind: live_api
provider: Hacker News Algolia API (hn.algolia.com, public, no key)
requires_env: []
inputs: [query, sort, timeframe, limit]
outputs: [items]
side_effect: false
---
# hacker_news_search

Searches Hacker News **stories** through the public Algolia API
(`https://hn.algolia.com/api/v1/search` or `/search_by_date`). No API key.

Use it when the user wants what the developer / tech community is discussing:
"trên Hacker News", "HN", "dân dev bàn gì về ...". Not for general news (use
`lookup`) or tweets (`social_search` / `timeline`).

Args:

- `query` (required): keyword/topic, e.g. `"AI agents"`.
- `sort`: `relevance` (default, `/search`) or `date` (newest first, `/search_by_date`).
- `timeframe`: `day` / `week` / `month` / `year`, or omitted for all time. Implemented
  as `numericFilters=created_at_i>now-N`.
- `limit`: 1–20, default 5. Numeric strings like `"5"` are accepted; values are clamped.

Each item: `title`, `url` (external link, or the HN thread for Ask/Show HN posts),
`source`, `hn_url`, `points`, `num_comments`, `author`, `created_at`. Hits without
`objectID` or `title` are skipped.

Errors (empty query, out-of-enum `sort`/`timeframe`, non-numeric `limit`, HTTP
errors, timeouts) return `{"tool": "hacker_news_search", "error": ..., "message": ...}`;
the tool never raises.
