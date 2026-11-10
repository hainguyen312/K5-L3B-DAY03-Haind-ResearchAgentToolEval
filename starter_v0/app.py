"""Streamlit UI for the Research Agent (group Haind, CP5).

Run from starter_v0/:
    streamlit run app.py
Env:
    AGENT_PROVIDER (default: openai), AGENT_VERSION (default: v5), AGENT_MODEL (optional)

Reuses the exact multi-turn tool loop of chat.py and writes transcripts in the same
format to transcripts/ui_<version>_<provider>_<timestamp>.transcript.json.

- Tool calls and raw tool results (including errors) are always shown — never hidden.
- When the agent asks for confirmation (clarify yes_no) or a choice, the answer buttons
  appear inside the same assistant bubble; the reply and the agent's follow-up are
  appended to that bubble instead of opening a new chat bubble. Each reply is still a
  separate turn in the transcript (field "via": "inline_button").
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any

import streamlit as st

from chat import (
    ARTIFACTS_DIR,
    ROOT,
    now_iso,
    run_model_tool_loop,
    safe_slug,
    trim_history,
    write_transcript,
)
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version

PROVIDER = os.getenv("AGENT_PROVIDER", "openai")
VERSION = os.getenv("AGENT_VERSION", "v5")
MODEL = os.getenv("AGENT_MODEL") or None
SYSTEM_PROMPT_PATH = ARTIFACTS_DIR / "system_prompt.md"
TOOLS_PATH = ARTIFACTS_DIR / "tools.yaml"
HISTORY_WINDOW = 5
MAX_TOOL_ROUNDS = 4

CONFIRM_YES = "Có, mình xác nhận."
CONFIRM_NO = "Không, đừng thực hiện."

SAMPLE_QUESTIONS = [
    ("📰", "Tin tức AI hôm nay có gì nổi bật?"),
    ("🟠", "Dân dev trên Hacker News đang bàn gì về AI agents tuần này?"),
    ("🐦", "Cho mình 5 tweet nổi bật nhất về Gemini."),
    ("📨", "Làm bản tin AI hôm nay rồi đăng lên Telegram"),
]

TOOL_ICONS = {
    "clarify": "❓", "timeline": "👤", "social_search": "🐦", "lookup": "🌐", "fetch": "📄",
    "format": "📝", "send": "📨", "policy": "📘", "papers": "🎓", "paper_text": "📑",
    "hacker_news_search": "🟠",
}

st.set_page_config(page_title="Research Agent · Haind", page_icon="🔎", layout="centered")

st.markdown(
    """
    <style>
      #MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"] {display: none;}
      .block-container {padding-top: 1.6rem; padding-bottom: 6rem; max-width: 820px;}
      .hero {text-align: center; padding: 2.2rem 1rem 1.2rem;}
      .hero h1 {font-size: 2.1rem; margin: 0 0 .35rem; letter-spacing: -0.02em;}
      .hero p {color: #64748b; margin: 0; font-size: 1.02rem;}
      .chips {display: flex; flex-wrap: wrap; gap: .4rem; justify-content: center; margin-top: 1rem;}
      .chip {background: #eef2ff; color: #3730a3; border-radius: 999px; padding: .18rem .7rem; font-size: .8rem;}
      .topbar {display: flex; align-items: center; justify-content: space-between; margin-bottom: .6rem;}
      .topbar .title {font-weight: 700; font-size: 1.15rem;}
      .topbar .meta {color: #64748b; font-size: .8rem;}
      .reply-pill {display: inline-block; background: #ecfdf5; color: #065f46; border: 1px solid #a7f3d0;
                   border-radius: 999px; padding: .15rem .75rem; font-size: .85rem; margin: .35rem 0 .5rem;}
      .reply-pill.no {background: #fef2f2; color: #991b1b; border-color: #fecaca;}
      .ask-label {color: #92400e; font-size: .8rem; font-weight: 600; text-transform: uppercase;
                  letter-spacing: .04em; margin-bottom: .15rem;}
      [data-testid="stChatMessage"] {border-radius: 14px; padding: .9rem 1rem;}
      [data-testid="stExpander"] details {border-radius: 10px;}
      div[data-testid="stButton"] button {border-radius: 10px;}
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------- agent + transcript

@st.cache_resource
def load_agent_config() -> dict[str, Any]:
    provider = make_provider(PROVIDER)
    return {
        "provider": provider,
        "system_prompt": SYSTEM_PROMPT_PATH.read_text(encoding="utf-8"),
        "tools": to_openai_tools(load_tool_declarations(TOOLS_PATH)),
        "model": MODEL or getattr(provider, "default_model", None),
        "artifact_version": build_artifact_version(VERSION, SYSTEM_PROMPT_PATH, TOOLS_PATH),
    }


def new_session() -> None:
    cfg = load_agent_config()
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    transcript_id = "_".join(["ui", safe_slug(VERSION), safe_slug(PROVIDER), timestamp])
    st.session_state.transcript_path = ROOT / "transcripts" / f"{transcript_id}.transcript.json"
    st.session_state.transcript = {
        "transcript_id": transcript_id,
        **artifact_version_dict(cfg["artifact_version"]),
        "provider": PROVIDER,
        "model": cfg["model"],
        "system_prompt": str(SYSTEM_PROMPT_PATH),
        "tools": str(TOOLS_PATH),
        "history_window": HISTORY_WINDOW,
        "max_tool_rounds": MAX_TOOL_ROUNDS,
        "interface": "streamlit",
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "turns": [],
    }
    st.session_state.history = []  # user/assistant text pairs, same as chat.py


def handle_user_message(user_text: str, via: str = "chat_input") -> None:
    cfg = load_agent_config()
    transcript = st.session_state.transcript
    turn_record: dict[str, Any] = {
        "turn_index": len(transcript["turns"]) + 1,
        "started_at": now_iso(),
        "user": user_text,
        "via": via,
        "status": "started",
        "assistant_text": None,
        "rounds": [],
        "tool_events": [],
    }
    messages = [
        {"role": "system", "content": cfg["system_prompt"]},
        *trim_history(st.session_state.history, HISTORY_WINDOW),
        {"role": "user", "content": user_text},
    ]
    try:
        result = run_model_tool_loop(
            provider=cfg["provider"],
            messages=messages,
            tools=cfg["tools"],
            model=MODEL,
            max_tool_rounds=MAX_TOOL_ROUNDS,
        )
        turn_record.update(result)
        st.session_state.history += [
            {"role": "user", "content": user_text},
            {"role": "assistant", "content": result["assistant_text"]},
        ]
    except Exception as exc:  # show it, never swallow it
        turn_record.update({"status": "provider_error", "error": f"{type(exc).__name__}: {exc}"})
    turn_record["ended_at"] = now_iso()
    transcript["turns"].append(turn_record)
    write_transcript(st.session_state.transcript_path, transcript)


# ---------------------------------------------------------------- rendering

def pending_question(turn: dict[str, Any]) -> dict[str, Any] | None:
    """The clarify result the agent is waiting on, if this turn paused for the user."""
    if turn.get("status") != "waiting_for_user":
        return None
    for event in reversed(turn.get("tool_events", [])):
        result = event.get("result")
        if isinstance(result, dict) and result.get("awaiting_user"):
            return result
    return None


def render_tool_events(turn: dict[str, Any]) -> None:
    for round_ in turn.get("rounds", []):
        for event in round_.get("tool_results", []):
            name = event.get("tool", "?")
            if name == "clarify":
                continue  # the question itself is rendered as the agent's message
            result = event.get("result", {})
            is_error = isinstance(result, dict) and "error" in result
            args = event.get("args", {})
            arg_text = ", ".join(f"{k}={json.dumps(v, ensure_ascii=False)}" for k, v in args.items())
            if len(arg_text) > 90:
                arg_text = arg_text[:87] + "…"
            label = f"{'❌' if is_error else TOOL_ICONS.get(name, '🔧')} **{name}**  `{arg_text}`"
            with st.expander(label, expanded=is_error):
                if is_error:
                    st.error(f"**{result.get('error')}** — {result.get('message', '')}")
                st.caption("Arguments")
                st.json(args, expanded=True)
                st.caption("Kết quả tool (thô)")
                st.json(result, expanded=False)


def render_agent_part(turn: dict[str, Any]) -> None:
    render_tool_events(turn)
    status = turn.get("status")
    if status == "provider_error":
        st.error(f"Provider error — {turn.get('error')}")
        return
    if status == "max_tool_rounds":
        st.warning("Agent dừng vì chạm giới hạn số vòng gọi tool.")
    question = pending_question(turn)
    if question:
        kind = {"yes_no": "Cần bạn xác nhận", "choice": "Chọn một phương án"}.get(question.get("response_type"), "Agent cần thêm thông tin")
        st.markdown(f'<div class="ask-label">{kind}</div>', unsafe_allow_html=True)
    st.markdown(turn.get("assistant_text") or "_(không có nội dung trả lời)_")


def render_inline_reply(turn: dict[str, Any]) -> None:
    text = turn["user"]
    cls = "reply-pill no" if text == CONFIRM_NO else "reply-pill"
    icon = "✕" if text == CONFIRM_NO else "✓"
    st.markdown(f'<span class="{cls}">{icon} Bạn đã chọn: {text}</span>', unsafe_allow_html=True)


def render_inline_buttons(turn: dict[str, Any]) -> None:
    question = pending_question(turn)
    if not question:
        return
    key = f"t{turn['turn_index']}"
    if question.get("response_type") == "yes_no":
        col_yes, col_no, _ = st.columns([1, 1, 2])
        if col_yes.button("✓ Có, xác nhận", key=f"{key}_yes", type="primary", use_container_width=True):
            st.session_state.pending = {"text": CONFIRM_YES, "via": "inline_button"}
            st.rerun()
        if col_no.button("✕ Không", key=f"{key}_no", use_container_width=True):
            st.session_state.pending = {"text": CONFIRM_NO, "via": "inline_button"}
            st.rerun()
    elif question.get("response_type") == "choice" and question.get("options"):
        options = question["options"]
        cols = st.columns(min(len(options), 3))
        for index, option in enumerate(options):
            if cols[index % len(cols)].button(option, key=f"{key}_opt{index}", use_container_width=True):
                st.session_state.pending = {"text": option, "via": "inline_button"}
                st.rerun()
    else:
        st.caption("↓ Trả lời ở ô chat bên dưới")


def group_turns(turns: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    """Inline-button replies continue the previous exchange instead of starting a new bubble."""
    groups: list[list[dict[str, Any]]] = []
    for turn in turns:
        if turn.get("via") == "inline_button" and groups:
            groups[-1].append(turn)
        else:
            groups.append([turn])
    return groups


def render_conversation(turns: list[dict[str, Any]], *, busy: bool) -> None:
    groups = group_turns(turns)
    for g_index, group in enumerate(groups):
        with st.chat_message("user", avatar="🧑"):
            st.markdown(group[0]["user"])
        with st.chat_message("assistant", avatar="🔎"):
            for t_index, turn in enumerate(group):
                if t_index > 0:
                    render_inline_reply(turn)
                render_agent_part(turn)
            is_last = g_index == len(groups) - 1
            if is_last and busy:
                pending = st.session_state.get("pending")
                if pending and pending.get("via") == "inline_button":
                    render_inline_reply({"user": pending["text"]})
                    with st.spinner("Agent đang xử lý…"):
                        process_pending()
            elif is_last:
                render_inline_buttons(group[-1])


def process_pending() -> None:
    pending = st.session_state.pop("pending", None)
    if pending:
        handle_user_message(pending["text"], via=pending.get("via", "chat_input"))
        st.rerun()


# ---------------------------------------------------------------- page

if "transcript" not in st.session_state:
    new_session()
cfg = load_agent_config()
turns = st.session_state.transcript["turns"]

with st.sidebar:
    st.markdown("### 🔎 Research Agent")
    st.caption("Nhóm Haind · Day 03 Prompt Engineering & Tool Calling")
    if st.button("＋ Cuộc trò chuyện mới", use_container_width=True, type="primary"):
        new_session()
        st.rerun()
    st.divider()
    st.markdown("**Agent làm được gì**")
    st.markdown(
        "- 🌐 Tin tức / web\n- 🐦 Tweet theo tài khoản hoặc từ khóa\n- 🟠 Hacker News\n"
        "- 📄 Đọc URL · 🎓 arXiv · 📘 policy nội bộ\n- 📝 Bản tin · 📨 Telegram *(luôn hỏi xác nhận)*"
    )
    st.divider()
    with st.expander("Thông tin phiên"):
        st.markdown(
            f"**Provider:** `{PROVIDER}`  \n**Model:** `{cfg['model']}`  \n"
            f"**Artifact:** `{cfg['artifact_version'].artifact_version}`  \n"
            f"**Transcript:** `{st.session_state.transcript_path.relative_to(ROOT)}`"
        )

if not turns and "pending" not in st.session_state:
    st.markdown(
        """
        <div class="hero">
          <h1>🔎 Research Agent</h1>
          <p>Hỏi về tin AI & công nghệ — agent tự chọn tool, hỏi lại khi thiếu thông tin,
             và luôn xin xác nhận trước khi đăng bài.</p>
          <div class="chips">
            <span class="chip">Web news</span><span class="chip">X / Twitter</span>
            <span class="chip">Hacker News</span><span class="chip">arXiv</span>
            <span class="chip">Policy nội bộ</span><span class="chip">Telegram</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    cols = st.columns(2)
    for index, (icon, question) in enumerate(SAMPLE_QUESTIONS):
        if cols[index % 2].button(f"{icon}  {question}", key=f"sample{index}", use_container_width=True):
            st.session_state.pending = {"text": question, "via": "sample"}
            st.rerun()
else:
    st.markdown(
        f'<div class="topbar"><span class="title">🔎 Research Agent</span>'
        f'<span class="meta">{cfg["model"]} · {VERSION}</span></div>',
        unsafe_allow_html=True,
    )

pending = st.session_state.get("pending")
busy_inline = bool(pending and pending.get("via") == "inline_button")
render_conversation(turns, busy=busy_inline)

# a new exchange (typed or sample question): show the user bubble right away, then run
if pending and not busy_inline:
    with st.chat_message("user", avatar="🧑"):
        st.markdown(pending["text"])
    with st.chat_message("assistant", avatar="🔎"):
        with st.spinner("Agent đang chọn tool và chạy…"):
            process_pending()

waiting = bool(turns) and pending_question(turns[-1]) is not None
placeholder = "Hoặc gõ câu trả lời của bạn…" if waiting else "Hỏi agent… ví dụ: Tin tức AI hôm nay có gì nổi bật?"
if prompt := st.chat_input(placeholder):
    st.session_state.pending = {"text": prompt, "via": "chat_input"}
    st.rerun()
