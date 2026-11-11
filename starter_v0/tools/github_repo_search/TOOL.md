---
name: github_repo_search
track: bonus
kind: live_api
provider: GitHub Search API (api.github.com, public; optional GITHUB_TOKEN)
requires_env: []
inputs: [query, language, sort, limit]
outputs: [items]
side_effect: false
---
# github_repo_search

Tìm repo mã nguồn mở trên GitHub ("repo Python về AI agents nhiều sao nhất"). Không dùng cho tin tức (lookup), paper (papers) hay model (huggingface_model_search).

Input xấu (query rỗng, giá trị ngoài enum, sai kiểu) và lỗi HTTP/timeout đều trả
`{"tool": "github_repo_search", "error": ..., "message": ...}`; tool không bao giờ raise.
`limit`/`sentences` nhận chuỗi số và được kẹp vào khoảng hợp lệ.
