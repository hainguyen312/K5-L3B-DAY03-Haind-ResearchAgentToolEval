from __future__ import annotations

import os
from typing import Any

import requests

from tools._bonus_util import clamp_int, require_text
from tools._shared import TIMEOUT, err

API = "https://api.github.com/search/repositories"
SORTS = {"stars", "updated", "best_match"}


def search_github_repos(query: str = "", language: str | None = None, sort: str = "stars", limit: int = 5) -> dict[str, Any]:
    tool = "github_repo_search"
    try:
        q = require_text(query, "query")
        if sort not in SORTS:
            raise ValueError(f"sort must be one of {sorted(SORTS)}")
        if language is not None and not isinstance(language, str):
            raise ValueError("language must be a string")
        n = clamp_int(limit, "limit", 1, 20)
        if language and language.strip():
            q = f"{q} language:{language.strip()}"
        params: dict[str, Any] = {"q": q, "per_page": n}
        if sort != "best_match":
            params.update(sort=sort, order="desc")
        headers = {"Accept": "application/vnd.github+json"}
        if os.getenv("GITHUB_TOKEN"):
            headers["Authorization"] = f"Bearer {os.getenv('GITHUB_TOKEN')}"
        resp = requests.get(API, params=params, headers=headers, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        items = [{
            "title": r.get("full_name"),
            "url": r.get("html_url"),
            "source": "github.com",
            "summary": r.get("description") or "",
            "stars": r.get("stargazers_count", 0),
            "language": r.get("language"),
            "updated_at": r.get("updated_at"),
        } for r in data.get("items", []) if r.get("full_name") and r.get("html_url")]
        return {"tool": tool, "query": query, "language": language, "sort": sort,
                "total_count": data.get("total_count", 0), "items": items[:n]}
    except Exception as exc:  # noqa: BLE001 - tools return error dicts, never raise
        return err(tool, exc)
