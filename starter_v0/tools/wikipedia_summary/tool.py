from __future__ import annotations

from typing import Any

import requests

from tools._bonus_util import clamp_int, require_text
from tools._shared import TIMEOUT, err

LANGS = {"en", "vi"}
HEADERS = {"User-Agent": "AI20k-Day03-Research-Agent/1.0 (educational lab)"}


def wikipedia_summary(query: str = "", lang: str = "en", sentences: int = 3) -> dict[str, Any]:
    tool = "wikipedia_summary"
    try:
        q = require_text(query, "query")
        if lang not in LANGS:
            raise ValueError(f"lang must be one of {sorted(LANGS)}")
        n = clamp_int(sentences, "sentences", 1, 10)
        params = {
            "action": "query", "format": "json", "generator": "search", "gsrsearch": q, "gsrlimit": 1,
            "prop": "extracts|info", "exintro": 1, "explaintext": 1, "exsentences": n, "inprop": "url",
        }
        resp = requests.get(f"https://{lang}.wikipedia.org/w/api.php", params=params, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        pages = (resp.json().get("query") or {}).get("pages") or {}
        items = [{
            "title": p.get("title"),
            "url": p.get("fullurl"),
            "source": f"{lang}.wikipedia.org",
            "summary": (p.get("extract") or "").strip(),
        } for p in pages.values() if p.get("title")]
        return {"tool": tool, "query": query, "lang": lang, "found": bool(items), "items": items}
    except Exception as exc:  # noqa: BLE001
        return err(tool, exc)
