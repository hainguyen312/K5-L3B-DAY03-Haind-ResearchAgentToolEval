---
name: huggingface_model_search
track: bonus
kind: live_api
provider: Hugging Face Hub API (huggingface.co/api/models, public, no key)
requires_env: []
inputs: [query, task, sort, limit]
outputs: [items]
side_effect: false
---
# huggingface_model_search

Tìm model pretrained trên Hugging Face ("model speech-to-text"). Không dùng cho tin tức về công ty Hugging Face (lookup), paper (papers) hay repo code (github_repo_search).

Input xấu (query rỗng, giá trị ngoài enum, sai kiểu) và lỗi HTTP/timeout đều trả
`{"tool": "huggingface_model_search", "error": ..., "message": ...}`; tool không bao giờ raise.
`limit`/`sentences` nhận chuỗi số và được kẹp vào khoảng hợp lệ.
