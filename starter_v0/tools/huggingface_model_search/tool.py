from __future__ import annotations

from typing import Any

import requests

from tools._bonus_util import clamp_int, require_text
from tools._shared import TIMEOUT, err

API = "https://huggingface.co/api/models"
SORTS = {"downloads", "likes", "lastModified"}


def search_huggingface_models(query: str = "", task: str | None = None, sort: str = "downloads", limit: int = 5) -> dict[str, Any]:
    tool = "huggingface_model_search"
    try:
        q = require_text(query, "query")
        if sort not in SORTS:
            raise ValueError(f"sort must be one of {sorted(SORTS)}")
        if task is not None and not isinstance(task, str):
            raise ValueError("task must be a string")
        n = clamp_int(limit, "limit", 1, 20)
        params: dict[str, Any] = {"search": q, "sort": sort, "direction": -1, "limit": n}
        if task and task.strip():
            params["pipeline_tag"] = task.strip()
        resp = requests.get(API, params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, list):
            raise ValueError("unexpected Hugging Face response shape")
        items = [{
            "title": m["id"],
            "url": f"https://huggingface.co/{m['id']}",
            "source": "huggingface.co",
            "task": m.get("pipeline_tag"),
            "library": m.get("library_name"),
            "downloads": m.get("downloads", 0),
            "likes": m.get("likes", 0),
        } for m in data if isinstance(m, dict) and m.get("id")]
        return {"tool": tool, "query": query, "task": task, "sort": sort, "items": items[:n]}
    except Exception as exc:  # noqa: BLE001
        return err(tool, exc)
