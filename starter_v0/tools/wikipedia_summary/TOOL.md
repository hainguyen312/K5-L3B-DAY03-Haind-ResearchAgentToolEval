---
name: wikipedia_summary
track: bonus
kind: live_api
provider: Wikipedia API (en/vi.wikipedia.org, public, no key)
requires_env: []
inputs: [query, lang, sentences]
outputs: [items]
side_effect: false
---
# wikipedia_summary

Tóm tắt định nghĩa/khái niệm từ Wikipedia ("RAG là gì?"). Không dùng cho tin tức mới (lookup) hay paper (papers).

Input xấu (query rỗng, giá trị ngoài enum, sai kiểu) và lỗi HTTP/timeout đều trả
`{"tool": "wikipedia_summary", "error": ..., "message": ...}`; tool không bao giờ raise.
`limit`/`sentences` nhận chuỗi số và được kẹp vào khoảng hợp lệ.
