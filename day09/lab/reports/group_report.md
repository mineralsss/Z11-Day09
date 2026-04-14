# Báo Cáo Nhóm — Lab Day 09: Multi-Agent Orchestration

**Tên nhóm:** Z11  
**Thành viên:**
| Tên | Vai trò | Email |
|-----|---------|-------|
| Nguyễn Phan Tuấn Anh | Supervisor Owner | tuananh171312@outlook.com |
| Nguyễn Phan Tuấn Anh | Worker Owner | tuananh171312@outlook.com |
| Lê Nguyễn Chí Bảo | MCP Owner | tribao5556@gmail.com |
| Lê Nguyễn Chí Bảo | Trace & Docs Owner | tribao5556@gmail.com |

**Ngày nộp:** 14/4/2026  
**Repo:** https://github.com/mineralsss/Z11-Day09.git  
**Độ dài khuyến nghị:** 600–1000 từ

---

> **Hướng dẫn nộp group report:**
> 
> - File này nộp tại: `reports/group_report.md`
> - Deadline: Được phép commit **sau 18:00** (xem SCORING.md)
> - Tập trung vào **quyết định kỹ thuật cấp nhóm** — không trùng lặp với individual reports
> - Phải có **bằng chứng từ code/trace** — không mô tả chung chung
> - Mỗi mục phải có ít nhất 1 ví dụ cụ thể từ code hoặc trace thực tế của nhóm

---

## 1. Kiến trúc nhóm đã xây dựng (150–200 từ)

> Mô tả ngắn gọn hệ thống nhóm: bao nhiêu workers, routing logic hoạt động thế nào,
> MCP tools nào được tích hợp. Dùng kết quả từ `docs/system_architecture.md`.

**Hệ thống tổng quan:**

Nhóm xây dựng hệ thống theo pattern **Supervisor–Worker** gồm 3 worker chính (`retrieval_worker`, `policy_tool_worker`, `synthesis_worker`) và 1 nhánh `human_review` cho case rủi ro cao. Luồng trong `graph.py` là: nhận câu hỏi → supervisor route theo rule → chạy worker tương ứng → luôn qua synthesis để tạo `final_answer`, `sources`, `confidence`.

Điểm chính của kiến trúc là trace-first: state giữ đầy đủ `route_reason`, `workers_called`, `mcp_tools_used`, `mcp_tool_called`, `mcp_result`, `history`, `latency_ms`. Nhờ vậy Sprint 4 có thể phân tích định lượng từ trace thay vì chỉ nhận xét cảm tính. Theo `artifacts/eval_report.json`, hệ thống có route phân bố `policy_tool_worker` 52% và `retrieval_worker` 47%, MCP usage 47%, HITL 4%.

**Routing logic cốt lõi:**
> Mô tả logic supervisor dùng để quyết định route (keyword matching, LLM classifier, rule-based, v.v.)

Supervisor dùng rule-based keyword routing. Các câu có từ khóa policy/access/refund/flash sale/license/level route sang `policy_tool_worker` và bật `needs_tool=True`. Từ khóa rủi ro (`emergency`, `khẩn cấp`, `2am`, `err-`) bật `risk_high`; riêng `err-` sẽ route `human_review`. Các câu còn lại route mặc định `retrieval_worker`. `route_reason` luôn ghi rõ có/không chọn MCP để dễ debug.

**MCP tools đã tích hợp:**
> Liệt kê tools đã implement và 1 ví dụ trace có gọi MCP tool.

- `search_kb`: tìm knowledge chunks theo query + top_k.
- `get_ticket_info`: lấy thông tin ticket mock (ví dụ `P1-LATEST`).
- `check_access_permission`: kiểm tra điều kiện cấp quyền theo level + emergency.

Ví dụ trace thực tế: trong `artifacts/grading_eval.json`, record `gq09` gọi đủ 3 tool `search_kb`, `get_ticket_info`, `check_access_permission`.

---

## 2. Quyết định kỹ thuật quan trọng nhất (200–250 từ)

> Chọn **1 quyết định thiết kế** mà nhóm thảo luận và đánh đổi nhiều nhất.
> Phải có: (a) vấn đề gặp phải, (b) các phương án cân nhắc, (c) lý do chọn phương án đã chọn.

**Quyết định:** Chuẩn hóa mọi external capability qua MCP `dispatch_tool` thay vì gọi function/domain logic trực tiếp trong worker.

**Bối cảnh vấn đề:**

Nhóm cần vừa đảm bảo có tool integration thật sự, vừa đáp ứng yêu cầu trace MCP chi tiết. Nếu gọi trực tiếp retrieval/policy functions trong `policy_tool_worker`, pipeline vẫn chạy nhưng không tách lớp giao tiếp rõ ràng và khó mở rộng về sau.

**Các phương án đã cân nhắc:**

| Phương án | Ưu điểm | Nhược điểm |
|-----------|---------|-----------|
| Gọi function trực tiếp trong worker | Nhanh, ít code trung gian | Coupling cao, khó audit tool-call, khó mở rộng |
| Qua `mcp_server.dispatch_tool` (đã chọn) | Chuẩn hóa input/output, trace rõ theo tool, dễ thêm tool mới | Cần kiểm soát schema chặt, tăng overhead orchestration |

**Phương án đã chọn và lý do:**

Nhóm chọn `dispatch_tool` vì phù hợp mục tiêu Day 09: **modular + observable**. Cách này giúp policy worker chỉ giữ vai trò orchestration, còn logic tool nằm ở MCP server. Với Sprint 4, nhóm có thể thống kê trực tiếp `mcp_tools_used`, `mcp_tool_called`, `mcp_result` từ trace. Đổi lại, khi mapping input chưa chặt sẽ phát sinh lỗi runtime (đã thấy ở một số record grading), nhưng đây là vấn đề có thể sửa bằng schema validation.

**Bằng chứng từ trace/code:**
> Dẫn chứng cụ thể (VD: route_reason trong trace, đoạn code, v.v.)

```python
# workers/policy_tool.py
mcp_result = _call_mcp_tool("search_kb", {"query": task, "top_k": 3})
state["mcp_tools_used"].append(mcp_result)
state["mcp_tool_called"].append("search_kb")
state["mcp_result"].append(mcp_result.get("output"))
```

```json
// artifacts/grading_eval.json, gq09
"mcp_tools_used": [
  {"tool": "search_kb", ...},
  {"tool": "get_ticket_info", ...},
  {"tool": "check_access_permission", ...}
]
```

---

## 3. Kết quả grading questions (150–200 từ)

> Sau khi chạy pipeline với grading_questions.json (public lúc 17:00):
> - Nhóm đạt bao nhiêu điểm raw?
> - Câu nào pipeline xử lý tốt nhất?
> - Câu nào pipeline fail hoặc gặp khó khăn?

**Tổng điểm raw ước tính:** **-15 / 96** (theo `artifacts/grading_eval.json`, `total_awarded_points`)

**Câu pipeline xử lý tốt nhất:**
- ID: **gq10** — Lý do tốt: đạt **Full (10 điểm)**, kết luận đúng “Flash Sale không được hoàn tiền”, nêu đúng logic ngoại lệ override điều kiện lỗi nhà sản xuất.

**Câu pipeline fail hoặc partial:**
- ID: **gq09** — Fail ở đâu: câu multi-hop không cover được cả SLA P1 notification và Level 2 emergency access.  
  Root cause: integration lỗi ở tool path (`search_kb` trả mock_data; `get_ticket_info`/`check_access_permission` báo lỗi input/schema), nên evidence đầu vào cho synthesis không đủ.

**Câu gq07 (abstain):** Nhóm xử lý thế nào?

Pipeline đã abstain đúng hướng: trả “Không đủ thông tin trong tài liệu nội bộ”, không bịa số liệu phạt (không hallucinate). Tuy nhiên vẫn 0 điểm vì thiếu phần gợi ý liên hệ bộ phận liên quan (judge đánh giá chưa đủ tiêu chí).

**Câu gq09 (multi-hop khó nhất):** Trace ghi được 2 workers không? Kết quả thế nào?

Có. Trace ghi rõ `policy_tool_worker -> synthesis_worker` và log đủ MCP tool calls. Tuy vậy output cuối vẫn bị Penalty do failure ở phần tool result và không đạt criteria multi-hop.

---

## 4. So sánh Day 08 vs Day 09 — Điều nhóm quan sát được (150–200 từ)

> Dựa vào `docs/single_vs_multi_comparison.md` — trích kết quả thực tế.

**Metric thay đổi rõ nhất (có số liệu):**

Theo tài liệu so sánh và `artifacts/eval_report.json`:  
- Avg latency tăng từ **2244ms (Day 08)** lên **10100ms (Day 09)**.  
- Avg confidence Day 09 là **0.484** (conservative hơn).  
- MCP usage rate đạt **35/73 (47%)**, HITL rate **3/73 (4%)**.

**Điều nhóm bất ngờ nhất khi chuyển từ single sang multi-agent:**

Dù điểm grading chưa cao, khả năng debug tăng mạnh. Nhóm có thể xác định nhanh lỗi thuộc route/retrieval/tool/synthesis nhờ `route_reason`, `workers_called`, `mcp_result`, thay vì phải đọc toàn bộ pipeline như mô hình single-agent.

**Trường hợp multi-agent KHÔNG giúp ích hoặc làm chậm hệ thống:**

Với câu hỏi fact đơn giản chỉ cần retrieval + synthesis, multi-agent tạo thêm orchestration overhead nhưng chưa tăng rõ accuracy. Trong các case này, single-agent vẫn có lợi thế tốc độ.

---

## 5. Phân công và đánh giá nhóm (100–150 từ)

> Đánh giá trung thực về quá trình làm việc nhóm.

**Phân công thực tế:**

| Thành viên | Phần đã làm | Sprint |
|------------|-------------|--------|
| Nguyễn Phan Tuấn Anh | Thiết kế AgentState, supervisor routing, route_reason và graph flow | 1 |
| Nguyễn Phan Tuấn Anh | Implement retrieval/policy/synthesis core logic và test độc lập worker | 2 |
| Lê Nguyễn Chí Bảo | Implement MCP server + tích hợp MCP vào policy worker + trace MCP fields | 3 |
| Lê Nguyễn Chí Bảo | Chạy grading/eval trace, tổng hợp metrics và hoàn thiện docs/report | 4 |

**Điều nhóm làm tốt:**

Phân vai theo sprint rõ ràng, MCP không chỉ chạy được mà còn phục vụ phân tích trace định lượng. Nhóm cũng dùng trace làm căn cứ sửa lỗi thay vì sửa cảm tính.

**Điều nhóm làm chưa tốt hoặc gặp vấn đề về phối hợp:**

Chưa khóa interface schema đủ sớm giữa policy worker và MCP tools, nên khi chạy grading một số case phát sinh lỗi input mapping.

**Nếu làm lại, nhóm sẽ thay đổi gì trong cách tổ chức?**

Thêm pre-grading checklist bắt buộc: test từng MCP tool bằng input thật, smoke test các câu đại diện (policy, access, abstain, multi-hop), rồi mới chạy batch grading.

---

## 6. Nếu có thêm 1 ngày, nhóm sẽ làm gì? (50–100 từ)

> 1–2 cải tiến cụ thể với lý do có bằng chứng từ trace/scorecard.

Nhóm sẽ ưu tiên 2 việc:  
1) Harden MCP interface (schema validation + input normalization) để loại lỗi tool runtime đã thấy ở gq09.  
2) Nâng routing từ keyword sang lightweight classifier và bổ sung regression tests cho nhóm câu abstain/multi-hop, vì scorecard hiện cho thấy điểm rơi chính đang ở các case này.

---

*File này lưu tại: `reports/group_report.md`*  
*Commit sau 18:00 được phép theo SCORING.md*
