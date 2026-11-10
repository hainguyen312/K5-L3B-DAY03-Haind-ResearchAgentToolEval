from __future__ import annotations

import time
from typing import Any

import requests

from tools._shared import TIMEOUT, domain, err

API = "https://hn.algolia.com/api/v1"
TIMEFRAME_SECONDS = {"day": 86_400, "week": 7 * 86_400, "month": 30 * 86_400, "year": 365 * 86_400}
SORTS = {"relevance": "search", "date": "search_by_date"}
MAX_LIMIT = 20


def search_hacker_news(
    query: str = "",
    sort: str = "relevance",
    timeframe: str | None = None,
    limit: int = 5,
) -> dict[str, Any]:
    """Search Hacker News stories via the public Algolia API (no key needed).

    Returns {"tool", "query", "sort", "timeframe", "items": [...]} or an error dict; never raises.
    """
    try:
        query = (query or "").strip() if isinstance(query, str) else ""
        if not query:
            raise ValueError("query must be a non-empty string")
        sort = (sort or "relevance").strip().lower()
        if sort not in SORTS:
            raise ValueError(f"sort must be one of {sorted(SORTS)}, got {sort!r}")
        if timeframe in ("", "all", "any"):
            timeframe = None
        if timeframe is not None and timeframe not in TIMEFRAME_SECONDS:
            raise ValueError(f"timeframe must be one of {sorted(TIMEFRAME_SECONDS)} or null, got {timeframe!r}")
        try:
            limit = int(limit if limit is not None else 5)
        except (TypeError, ValueError):
            raise ValueError(f"limit must be an integer, got {limit!r}") from None
        limit = max(1, min(limit, MAX_LIMIT))

        params: dict[str, Any] = {"query": query, "tags": "story", "hitsPerPage": limit}
        if timeframe:
            params["numericFilters"] = f"created_at_i>{int(time.time()) - TIMEFRAME_SECONDS[timeframe]}"

        response = requests.get(f"{API}/{SORTS[sort]}", params=params, timeout=TIMEOUT)
        response.raise_for_status()
        hits = response.json().get("hits", [])

        items = []
        for hit in hits:
            story_id = hit.get("objectID")
            if not story_id or not hit.get("title"):
                continue
            hn_url = f"https://news.ycombinator.com/item?id={story_id}"
            url = hit.get("url") or hn_url  # Ask HN / Show HN text posts have no external url
            items.append({
                "title": hit["title"],
                "url": url,
                "source": domain(url),
                "hn_url": hn_url,
                "points": hit.get("points") or 0,
                "num_comments": hit.get("num_comments") or 0,
                "author": hit.get("author"),
                "created_at": hit.get("created_at"),
            })
            if len(items) >= limit:
                break
        return {"tool": "hacker_news_search", "query": query, "sort": sort, "timeframe": timeframe, "items": items}
    except Exception as exc:
        return err("hacker_news_search", exc)
