# Báo cáo cá nhân — NguyenDucHai-2A202603899

## 1. Thông tin thành viên

- Họ tên: Nguyễn Đức Hải
- MSSV: 2A202603899
- Email: [26ai.haind4@vinuni.edu.vn](mailto:26ai.haind4@vinuni.edu.vn)
- GitHub: hainguyen312
- Nhóm: Haind (L3B) — nhóm 1 thành viên

## 2. Phần việc phụ trách

Làm toàn bộ bài (nhóm 1 người): CP1 setup + baseline, CP2 tối ưu prompt/tool declaration v1–v5, CP3 tool mới + unit test, CP4 eval nhóm, CP5 UI + live chat + báo cáo.

## 3. Đóng góp cụ thể

- **CP1 — Baseline:** cấu hình provider OpenAI (`gpt-4o-mini`) và key tool trong `.env`, chạy preflight + `pytest`, chạy base eval v0 (0.65), gán loại lỗi cho 7 case FAIL (bảng B2).
- **CP2 — v1–v5** (`starter_v0/artifacts/system_prompt.md`, `tools.yaml`, `version_log.csv`):
  - v1: bỏ chỉ dẫn "đoán thay vì hỏi" → 0.95.
  - v2: xác nhận trước khi gửi → sửa R12 (metric giữ 0.95 vì R13 FAIL lại).
  - v3: hoàn thiện prompt (routing, phạm vi, nhiều phần, multi-turn) + viết lại description cả 10 tool → sửa R13 nhưng gây regression M06.
  - v4: thêm 1 rule "đổi/bỏ nguồn → chỉ gọi tool mới" → 1.00.
  - v5: thêm tool mới, kiểm tra không regression → 1.00.
- **CP3 — Tool mới** `hacker_news_search` (`starter_v0/tools/hacker_news_search/`): tìm story Hacker News qua Algolia API, chuẩn hoá/chặn input xấu từ model, trả error dict thay vì raise; đăng ký trong `tools/__init__.py` + `tools.yaml`; 6 unit test.
- **Test challenge:** điền toàn bộ 14 stub trong `tests/test_tools_todo.py` cho tool có sẵn → `pytest` 87 passed, 0 failed, 0 skipped.
- **CP4 — Eval nhóm** (`starter_v0/data/eval_group.json`): 10 case (5 single + 5 multi), 3 case route tới tool mới; run v5 10/10 và run đối chứng với prompt starter 7/10 (bắt được lỗi boundary/scope).
- **CP5 — UI** `starter_v0/app.py` (Streamlit), live chat bằng `chat.py`, báo cáo nhóm Phần A + B.

## 4. Bằng chứng

- File/commit/PR:
  - Run: `starter_v0/runs/v0…v5_B_base_openai_*.json`, `runs/v5_B_group_openai_20261110T190910067991.json`, `runs/v0prompt-control_B_group_openai_20261110T191001764846.json`
  - Version log: `starter_v0/artifacts/version_log.csv`
  - Tool mới + test: `starter_v0/tools/hacker_news_search/`, `starter_v0/tests/test_tools_todo.py`
  - UI: `starter_v0/app.py`; transcript: `starter_v0/transcripts/*.transcript.json`
  - Commit: _(điền hash commit khi nộp)_

AI/công cụ đã dùng và cách tự kiểm tra kết quả:

- **Claude Code (Claude Opus 5.5)** chỉ dùng để:
  - Phân tích run JSON và gợi ý giả thuyết về nguyên nhân lỗi.
  - Viết nháp code tool mới và unit test.
- **Tự làm:** đọc đề/rubric, quyết định sửa prompt/tool declaration, làm UI Streamlit, viết báo cáo.

**Cách tự kiểm tra**

- Mọi metric trong báo cáo lấy trực tiếp từ `summary` của run JSON thật (không gõ tay). Chỉ dùng run có `provider_error_cases = 0` và `measured_cases = total_cases`. Hash trong `version_log.csv` được đối chiếu với `artifact_version` trong run.
- Đổi tên tool `hn_search` → `hacker_news_search` cho dễ hiểu.
- Review code tool và test do Claude viết:
  - Chạy `pytest` toàn suite.
  - Cố tình làm hỏng code tool (bỏ filter thời gian) để chắc test FAIL.
  - Quét bằng `ast` để chắc test nào cũng có assert so sánh và không gọi mạng thật.
- Eval nhóm:
  - Chạy đối chứng với prompt starter để chắc case không quá dễ.
  - Chạy lặp 2 lần để xem kết quả có ổn định.

## 5. Tự đánh giá

**Điểm làm tốt**

- Làm một mình nhưng hoàn thành đủ 5 checkpoint. Mọi kết quả đều có run JSON, version log và transcript làm bằng chứng.
- Tối ưu có kiểm soát: mỗi version sửa một điểm, nên truy được thay đổi nào sửa case nào và gây regression ở đâu (v3 sửa R13 nhưng làm hỏng M06, v4 sửa lại bằng một rule).
- Số liệu đáng tin: metric lấy trực tiếp từ run hợp lệ, hash version được đối chiếu với run.
- Tool `hacker_news_search` trả error dict thay vì raise. Unit test không gọi mạng thật và đã được kiểm chứng là bắt được lỗi thật.
- Run đối chứng của eval nhóm (prompt starter 7/10, v5 10/10) cho thấy các case phân biệt được prompt tốt và prompt kém.

**Hạn chế**

- v1 lần đầu gộp nhiều thay đổi nên phải làm lại; lẽ ra cần tách thay đổi từ đầu.
- v2 không tăng metric (R13 FAIL lại) do chưa kiểm tra độ ổn định của case.
- Bộ eval nhỏ và chỉ thử trên một model (gpt-4o-mini), nên mức 1.00 chưa chứng minh được khả năng tổng quát. Độ ổn định mới đánh giá qua 2 lần chạy.
- Có dùng Claude Code để phân tích run và viết nháp code/test. Tôi đã tự review và kiểm chứng, nhưng phần này không hoàn toàn do tôi tự viết.
