"""CP3: Tool Unit Test Challenge (completed by group Haind).

All former `pytest.skip(TODO)` stubs are now real tests.
Patterns to copy are in test_tools_examples.py. Fixtures are in conftest.py.

Rules:
- Offline only: mock HTTP with `fake_http`, set fake keys with `monkeypatch.setenv`.
- One behaviour per test. Name the test after the behaviour, not the function.
- Done = `pytest tests/ -v` shows 0 skipped, 0 failed.
"""
from __future__ import annotations

from conftest import FakeResponse
from tools import TOOL_FUNCTIONS


# ---------------- clarify ----------------

clarify = TOOL_FUNCTIONS["clarify"]
format_tool = TOOL_FUNCTIONS["format"]
send = TOOL_FUNCTIONS["send"]
lookup = TOOL_FUNCTIONS["lookup"]
fetch = TOOL_FUNCTIONS["fetch"]
timeline = TOOL_FUNCTIONS["timeline"]
social_search = TOOL_FUNCTIONS["social_search"]
policy = TOOL_FUNCTIONS["policy"]


def test_clarify_choice_returns_options_and_awaits_user() -> None:
    result = clarify(question="Bạn muốn nguồn nào?", response_type="choice", options=["Web", "Twitter"])

    assert result["options"] == ["Web", "Twitter"]
    assert result["response_type"] == "choice"
    assert result["question"] == "Bạn muốn nguồn nào?"
    assert result["awaiting_user"] is True


# ---------------- format ----------------

def test_format_sections_groups_items_by_section() -> None:
    items = [
        {"title": "a1", "url": "https://a.com/1", "section": "A"},
        {"title": "b1", "url": "https://b.com/1", "section": "B"},
        {"title": "a2", "url": "https://a.com/2", "section": "A"},
    ]
    result = format_tool(items=items, template="sections", headline="Digest")
    lines = result["markdown"].splitlines()

    assert lines[0] == "# Digest"
    assert lines.count("## A") == 1
    assert lines.count("## B") == 1
    # both A items sit under the single "## A" heading, before "## B"
    a, b = lines.index("## A"), lines.index("## B")
    assert a < b
    assert lines[a + 1].startswith("- a1") and lines[a + 2].startswith("- a2")
    assert result["item_count"] == 3


def test_format_thread_numbers_items() -> None:
    items = [{"title": f"Tin {i}", "url": f"https://example.com/{i}"} for i in range(3)]
    result = format_tool(items=items, template="thread")
    posts = result["markdown"].split("\n\n")

    assert [p.split(" ", 1)[0] for p in posts] == ["1/", "2/", "3/"]
    assert posts[0] == "1/ Tin 0 - [example.com](https://example.com/0)"


def test_format_empty_items_does_not_crash() -> None:
    for template in ("brief", "sections", "bullets", "thread", "daily_ai_vn"):
        for items in (None, []):
            result = format_tool(items=items, template=template)
            assert result["item_count"] == 0, (template, items)
            assert isinstance(result["markdown"], str)


# ---------------- send (guardrail) ----------------

def test_send_confirmed_posts_to_telegram(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:abc")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "-1001")
    calls = fake_http(FakeResponse({"ok": True}))

    result = send(text="Bản tin AI", confirmed=True)

    assert len(calls) == 1
    assert calls[0]["method"] == "POST"
    assert calls[0]["url"] == "https://api.telegram.org/bot123:abc/sendMessage"
    assert calls[0]["json"]["chat_id"] == "-1001"
    assert calls[0]["json"]["text"] == "Bản tin AI"
    assert result == {"tool": "send_telegram", "status": "sent"}


def test_send_confirmed_without_env_returns_error_and_no_request(fake_http) -> None:
    calls = fake_http(FakeResponse({"ok": True}))

    result = send(text="Bản tin AI", confirmed=True)

    assert calls == []
    assert result["error"] == "RuntimeError"
    assert "TELEGRAM_BOT_TOKEN" in result["message"]


# ---------------- lookup ----------------

def test_lookup_without_timeframe_omits_time_range(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")
    calls = fake_http(FakeResponse({"results": []}))

    result = lookup(query="AI", topic="news", timeframe=None)

    assert "time_range" not in calls[0]["json"]
    assert calls[0]["json"]["query"] == "AI"
    assert calls[0]["json"]["topic"] == "news"
    assert result["items"] == [] and result["timeframe"] is None


# ---------------- fetch ----------------

def test_fetch_maps_firecrawl_response(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "fc-test")
    calls = fake_http(FakeResponse({"data": {
        "markdown": "# Hello\nBody text",
        "metadata": {"title": "T", "sourceURL": "https://www.example.com/post?ref=1"},
    }}))

    result = fetch(url="https://www.example.com/post")

    assert calls[0]["url"] == "https://api.firecrawl.dev/v1/scrape"
    assert calls[0]["json"] == {"url": "https://www.example.com/post", "formats": ["markdown"]}
    assert calls[0]["headers"]["Authorization"] == "Bearer fc-test"
    assert result["items"][0] == {
        "title": "T",
        "url": "https://www.example.com/post?ref=1",
        "source": "example.com",
        "summary": "# Hello\nBody text",
    }


def test_fetch_truncates_markdown_to_4000_chars(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "fc-test")
    fake_http(FakeResponse({"data": {"markdown": "x" * 3999 + "END" + "y" * 2000, "metadata": {}}}))

    item = fetch(url="https://example.com")["items"][0]

    assert len(item["summary"]) == 4000
    assert item["summary"].endswith("xE")  # cut inside "END": nothing after char 4000 survives
    assert item["title"] == "https://example.com"  # no metadata -> falls back to the url


# ---------------- timeline / social_search ----------------

def test_timeline_respects_limit_and_skips_items_without_id(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "rk-test")
    raw = [{"text": "no id here", "screen_name": "sama"}] + [
        {"tweet_id": str(1000 + i), "text": f"tweet {i}", "screen_name": "sama"} for i in range(6)
    ]
    calls = fake_http(FakeResponse({"timeline": raw}))

    result = timeline(screenname="sama", limit=3)

    assert calls[0]["url"] == "https://twitter-api45.p.rapidapi.com/timeline.php"
    assert calls[0]["params"] == {"screenname": "sama"}
    assert calls[0]["headers"]["x-rapidapi-key"] == "rk-test"
    assert len(result["items"]) == 3
    assert [item["url"] for item in result["items"]] == [
        "https://x.com/sama/status/1000", "https://x.com/sama/status/1001", "https://x.com/sama/status/1002",
    ]
    assert all(item["source"] == "@sama" for item in result["items"])


def test_social_search_passes_search_type(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "rk-test")
    calls = fake_http(FakeResponse({"timeline": []}))

    top = social_search(query="AI agents", search_type="Top")
    latest = social_search(query="AI agents", search_type="Latest")

    assert calls[0]["url"] == "https://twitter-api45.p.rapidapi.com/search.php"
    assert calls[0]["params"] == {"query": "AI agents", "search_type": "Top"}
    assert calls[1]["params"] == {"query": "AI agents", "search_type": "Latest"}
    assert top["search_type"] == "Top" and latest["search_type"] == "Latest"


# ---------------- policy (local knowledge + trust boundary) ----------------

def test_policy_empty_query_returns_no_results() -> None:
    for query in ("", "   ", "là gì"):  # empty, whitespace, stopwords only
        result = policy(query=query)
        assert result["results"] == [], query
        assert "error" not in result


def test_policy_area_filter_only_returns_that_area() -> None:
    result = policy(query="API key customer data transcript", policy_area="data_privacy", top_k=10)

    assert len(result["results"]) >= 1, "expected at least one data_privacy hit"
    assert {hit["policy_area"] for hit in result["results"]} == {"data_privacy"}
    assert all(hit["doc_id"] == "data-privacy-policy" for hit in result["results"])


def test_policy_instruction_like_lines_go_to_untrusted_text() -> None:
    result = policy(query="citation viral tweet injection probe", policy_area="source_citation", top_k=10)
    probe = [hit for hit in result["results"] if hit["section"] == "Injection probe"]

    assert len(probe) == 1
    hit = probe[0]
    # the quoted, order-giving line is quarantined, never surfaced as a fact
    assert any("viral tweet" in line for line in hit["untrusted_text"])
    assert "viral tweet" not in hit["facts"]
    assert "ignore" not in hit["facts"].lower()
    assert "untrusted" in result["trust_boundary"]


# ---------------- YOUR NEW TOOL(S) ----------------
# Write at least 3 tests per tool your team adds:
#   1. happy path (mocked if it calls an API)
#   2. bad / missing input from the model (empty string, wrong type, out-of-enum value)
#   3. failure path (missing key, HTTP error, timeout) -> returns error dict, does not raise

hacker_news_search = TOOL_FUNCTIONS["hacker_news_search"]

HN_HITS = {"hits": [
    {"objectID": "101", "title": "AI agents in production", "url": "https://www.example.com/agents",
     "points": 120, "num_comments": 45, "author": "alice", "created_at": "2026-11-09T10:00:00Z"},
    {"objectID": "102", "title": "Ask HN: How do you evaluate agents?", "url": None,
     "points": 30, "num_comments": None, "author": "bob", "created_at": "2026-11-08T10:00:00Z"},
    {"title": "Hit without objectID is skipped", "url": "https://x.example"},
    {"objectID": "103", "title": "", "url": "https://empty-title.example"},
]}


def test_hacker_news_search_happy_path_sends_request_and_maps_stories(fake_http) -> None:
    calls = fake_http(FakeResponse(HN_HITS))

    result = hacker_news_search(query="AI agents", limit=5)

    # request we send
    assert len(calls) == 1
    assert calls[0]["method"] == "GET"
    assert calls[0]["url"] == "https://hn.algolia.com/api/v1/search"
    assert calls[0]["params"] == {"query": "AI agents", "tags": "story", "hitsPerPage": 5}
    # how we map the response: invalid hits skipped, Ask HN falls back to the HN thread url
    assert "error" not in result
    assert [item["title"] for item in result["items"]] == ["AI agents in production", "Ask HN: How do you evaluate agents?"]
    assert result["items"][0] == {
        "title": "AI agents in production", "url": "https://www.example.com/agents", "source": "example.com",
        "hn_url": "https://news.ycombinator.com/item?id=101", "points": 120, "num_comments": 45,
        "author": "alice", "created_at": "2026-11-09T10:00:00Z",
    }
    assert result["items"][1]["url"] == "https://news.ycombinator.com/item?id=102"
    assert result["items"][1]["num_comments"] == 0


def test_hacker_news_search_date_sort_and_timeframe_build_filter(monkeypatch, fake_http) -> None:
    monkeypatch.setattr("tools.hacker_news_search.tool.time.time", lambda: 1_000_000)
    calls = fake_http(FakeResponse({"hits": []}))

    result = hacker_news_search(query="LLM", sort="date", timeframe="day")

    assert calls[0]["url"] == "https://hn.algolia.com/api/v1/search_by_date"
    assert calls[0]["params"]["numericFilters"] == f"created_at_i>{1_000_000 - 86_400}"
    assert result["items"] == [] and result["timeframe"] == "day"


def test_hacker_news_search_bad_input_from_model_returns_error_without_request(fake_http) -> None:
    calls = fake_http(FakeResponse(HN_HITS))

    for bad in (
        {"query": ""},                              # empty string
        {"query": "   "},                           # whitespace only
        {"query": None},                            # wrong type
        {"query": "AI", "sort": "popular"},         # out of enum
        {"query": "AI", "timeframe": "decade"},     # out of enum
        {"query": "AI", "limit": "five"},           # non-numeric
    ):
        result = hacker_news_search(**bad)
        assert result["tool"] == "hacker_news_search"
        assert result["error"] == "ValueError", bad

    assert calls == []  # nothing invalid ever reaches the API


def test_hacker_news_search_coerces_string_limit_and_clamps_range(fake_http) -> None:
    calls = fake_http(FakeResponse({"hits": []}))

    hacker_news_search(query="AI", limit="3")
    hacker_news_search(query="AI", limit=0)
    hacker_news_search(query="AI", limit=500)

    assert [c["params"]["hitsPerPage"] for c in calls] == [3, 1, 20]


def test_hacker_news_search_http_error_returns_error_dict(fake_http) -> None:
    fake_http(FakeResponse(status_code=429))

    result = hacker_news_search(query="AI agents")

    assert result == {"tool": "hacker_news_search", "error": "HTTPError", "message": "HTTP 429"}


def test_hacker_news_search_timeout_returns_error_dict(fake_http) -> None:
    import requests

    fake_http(requests.Timeout("read timed out"))

    result = hacker_news_search(query="AI agents")

    assert result["error"] == "Timeout"
    assert "timed out" in result["message"]


# ---------------------------------------------------------------------------
# Bonus tools: github_repo_search, wikipedia_summary, huggingface_model_search
# ---------------------------------------------------------------------------
import requests  # noqa: E402

github_repo_search = TOOL_FUNCTIONS["github_repo_search"]
wikipedia_summary = TOOL_FUNCTIONS["wikipedia_summary"]
huggingface_model_search = TOOL_FUNCTIONS["huggingface_model_search"]

GH_PAYLOAD = {"total_count": 2, "items": [
    {"full_name": "acme/agents", "html_url": "https://github.com/acme/agents", "description": "Agent framework",
     "stargazers_count": 900, "language": "Python", "updated_at": "2026-11-01T00:00:00Z"},
    {"full_name": None, "html_url": "https://github.com/x/y"},
]}


def test_github_repo_search_happy_path_builds_query_and_maps_repos(fake_http) -> None:
    calls = fake_http(FakeResponse(GH_PAYLOAD))
    result = github_repo_search(query="AI agents", language="Python", sort="stars", limit=5)
    assert len(calls) == 1
    assert calls[0]["url"] == "https://api.github.com/search/repositories"
    assert calls[0]["params"] == {"q": "AI agents language:Python", "per_page": 5, "sort": "stars", "order": "desc"}
    assert "Authorization" not in calls[0]["headers"]
    assert result["total_count"] == 2
    assert result["items"] == [{"title": "acme/agents", "url": "https://github.com/acme/agents", "source": "github.com",
                                "summary": "Agent framework", "stars": 900, "language": "Python",
                                "updated_at": "2026-11-01T00:00:00Z"}]


def test_github_repo_search_best_match_omits_sort_and_uses_token(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    calls = fake_http(FakeResponse({"items": []}))
    result = github_repo_search(query="vector database", sort="best_match", limit="50")
    assert calls[0]["params"] == {"q": "vector database", "per_page": 20}
    assert calls[0]["headers"]["Authorization"] == "Bearer test-token"
    assert result["items"] == []


def test_github_repo_search_bad_input_returns_error_without_request(fake_http) -> None:
    calls = fake_http(FakeResponse(GH_PAYLOAD))
    for kwargs in ({"query": ""}, {"query": None}, {"query": "x", "sort": "forks"}, {"query": "x", "limit": "many"},
                   {"query": "x", "language": 3}):
        result = github_repo_search(**kwargs)
        assert result["tool"] == "github_repo_search"
        assert result["error"] == "ValueError"
    assert calls == []


def test_github_repo_search_http_error_and_timeout_return_error_dict(fake_http) -> None:
    fake_http(FakeResponse({}, status_code=403))
    assert github_repo_search(query="x")["error"] == "HTTPError"
    fake_http(requests.Timeout("slow"))
    assert github_repo_search(query="x")["error"] == "Timeout"


WIKI_PAYLOAD = {"query": {"pages": {"1": {"title": "Retrieval-augmented generation",
                                          "fullurl": "https://en.wikipedia.org/wiki/Retrieval-augmented_generation",
                                          "extract": " RAG is a technique. "}}}}


def test_wikipedia_summary_happy_path_sends_one_request_and_maps_page(fake_http) -> None:
    calls = fake_http(FakeResponse(WIKI_PAYLOAD))
    result = wikipedia_summary(query="RAG", sentences=2)
    assert len(calls) == 1
    assert calls[0]["url"] == "https://en.wikipedia.org/w/api.php"
    assert calls[0]["params"]["gsrsearch"] == "RAG"
    assert calls[0]["params"]["exsentences"] == 2
    assert calls[0]["headers"]["User-Agent"].startswith("AI20k-Day03")
    assert result["found"] is True
    assert result["items"] == [{"title": "Retrieval-augmented generation",
                                "url": "https://en.wikipedia.org/wiki/Retrieval-augmented_generation",
                                "source": "en.wikipedia.org", "summary": "RAG is a technique."}]


def test_wikipedia_summary_vi_and_not_found(fake_http) -> None:
    calls = fake_http(FakeResponse({"batchcomplete": ""}))
    result = wikipedia_summary(query="khái niệm không tồn tại", lang="vi", sentences=99)
    assert calls[0]["url"] == "https://vi.wikipedia.org/w/api.php"
    assert calls[0]["params"]["exsentences"] == 10
    assert result["found"] is False
    assert result["items"] == []


def test_wikipedia_summary_bad_input_returns_error_without_request(fake_http) -> None:
    calls = fake_http(FakeResponse(WIKI_PAYLOAD))
    for kwargs in ({"query": "  "}, {"query": "x", "lang": "fr"}, {"query": "x", "sentences": None}):
        result = wikipedia_summary(**kwargs)
        assert result["tool"] == "wikipedia_summary"
        assert result["error"] == "ValueError"
    assert calls == []


def test_wikipedia_summary_network_error_returns_error_dict(fake_http) -> None:
    fake_http(requests.ConnectionError("down"))
    result = wikipedia_summary(query="RAG")
    assert result["error"] == "ConnectionError"
    assert result["tool"] == "wikipedia_summary"


HF_PAYLOAD = [
    {"id": "openai/whisper-large-v3", "pipeline_tag": "automatic-speech-recognition", "library_name": "transformers",
     "downloads": 5000, "likes": 300},
    {"pipeline_tag": "text-generation"},
]


def test_huggingface_model_search_happy_path_with_task_filter(fake_http) -> None:
    calls = fake_http(FakeResponse(HF_PAYLOAD))
    result = huggingface_model_search(query="whisper", task="automatic-speech-recognition", limit=3)
    assert calls[0]["url"] == "https://huggingface.co/api/models"
    assert calls[0]["params"] == {"search": "whisper", "sort": "downloads", "direction": -1, "limit": 3,
                                  "pipeline_tag": "automatic-speech-recognition"}
    assert result["items"] == [{"title": "openai/whisper-large-v3", "url": "https://huggingface.co/openai/whisper-large-v3",
                                "source": "huggingface.co", "task": "automatic-speech-recognition",
                                "library": "transformers", "downloads": 5000, "likes": 300}]


def test_huggingface_model_search_bad_input_returns_error_without_request(fake_http) -> None:
    calls = fake_http(FakeResponse(HF_PAYLOAD))
    for kwargs in ({"query": ""}, {"query": "x", "sort": "stars"}, {"query": "x", "task": ["asr"]}, {"query": "x", "limit": True}):
        result = huggingface_model_search(**kwargs)
        assert result["tool"] == "huggingface_model_search"
        assert result["error"] == "ValueError"
    assert calls == []


def test_huggingface_model_search_bad_shape_and_http_error(fake_http) -> None:
    fake_http(FakeResponse({"error": "rate limited"}))
    result = huggingface_model_search(query="x")
    assert result["error"] == "ValueError"
    assert "unexpected" in result["message"]
    fake_http(FakeResponse([], status_code=500))
    assert huggingface_model_search(query="x")["error"] == "HTTPError"
