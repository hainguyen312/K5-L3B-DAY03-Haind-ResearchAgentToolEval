# Team

## Thông tin nhóm

- Tên nhóm: Haind
- Lớp: L3B
- Repo nhóm: `K5-L3B-DAY03-Haind-ResearchAgentToolEval` (xem [SUBMISSION.md](SUBMISSION.md))
- URL repo, nhánh nộp, commit chốt: https://github.com/hainguyen312/K5-L3B-DAY03-Haind-ResearchAgentToolEval · nhánh `main` · commit chốt: 

## Thành viên

| STT | Họ tên         | MSSV        | Email                                                         | GitHub       | Vai trò                    |
| --: | -------------- | ----------- | ------------------------------------------------------------- | ------------ | -------------------------- |
| 1   | Nguyễn Đức Hải | 2A202603899 | [26ai.haind4@vinuni.edu.vn](mailto:26ai.haind4@vinuni.edu.vn) | hainguyen312 | Trưởng nhóm (làm một mình) |

## Cá nhân

Mỗi thành viên đồng thời tạo một báo cáo riêng trong `report/` theo dạng:

```text
report/team/MSSV_HoTen.md
```

Ví dụ: `report/team/20241234_NguyenVanAn.md`.

Sao chép mục dưới đây cho từng thành viên.

## NguyenDucHai-2A202603899

Báo cáo cá nhân: [`report/team/2A202603899_NguyenDucHai.md`](report/team/2A202603899_NguyenDucHai.md)

### Phần việc phụ trách

- Toàn bộ bài (nhóm 1 thành viên): CP1 → CP5.

### Đóng góp cụ thể

- CP1: setup provider OpenAI `gpt-4o-mini`, baseline v0 (0.65), phân tích lỗi B2.
- CP2: prompt + tool declaration v1–v5 (base 0.65 → 1.00), `version_log.csv`, bảng B1.
- CP3: tool mới `hacker_news_search` + 6 unit test; điền 14 stub test của tool có sẵn (`pytest` 87 passed, 0 skipped).
- CP4: 10 case `eval_group.json` (3 case route tới tool mới), run group + run đối chứng.
- CP5: UI Streamlit `starter_v0/app.py`, live chat `chat.py`, báo cáo nhóm Phần A + B.

### Bằng chứng

- `starter_v0/runs/`, `starter_v0/transcripts/`, `starter_v0/artifacts/version_log.csv`
- `starter_v0/tools/hacker_news_search/`, `starter_v0/tests/test_tools_todo.py`, `starter_v0/app.py`
- `report/team/group_report.md`, lịch sử commit trên nhánh `main`
