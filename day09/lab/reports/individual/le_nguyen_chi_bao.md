# Báo Cáo Cá Nhân — Lab Day 09: Multi-Agent Orchestration

**Họ và tên:** Lê Nguyễn Chí Bảo  
**Vai trò trong nhóm:** MCP Owner + Trace & Docs Owner  
**Ngày nộp:** 14/4/2026  
**Độ dài yêu cầu:** 500–800 từ

---

> **Lưu ý quan trọng:**
> - Viết ở ngôi **"tôi"**, gắn với chi tiết thật của phần bạn làm
> - Phải có **bằng chứng cụ thể**: tên file, đoạn code, kết quả trace, hoặc commit
> - Nội dung phân tích phải khác hoàn toàn với các thành viên trong nhóm
> - Deadline: Được commit **sau 18:00** (xem SCORING.md)
> - Lưu file với tên: `reports/individual/[ten_ban].md` (VD: `nguyen_van_a.md`)

---

## 1. Tôi phụ trách phần nào? (100–150 từ)

> Mô tả cụ thể module, worker, contract, hoặc phần trace bạn trực tiếp làm.
> Không chỉ nói "tôi làm Sprint X" — nói rõ file nào, function nào, quyết định nào.

**Module/file tôi chịu trách nhiệm:**
- File chính: `mcp_server.py`, `workers/policy_tool.py`, `eval_trace.py`
- Functions tôi implement: `dispatch_tool`, `_call_mcp_tool`, các phần ghi trace MCP trong `policy_tool.run`, `run_grading_questions`, `analyze_traces`, `compare_single_vs_multi`

**Cách công việc của tôi kết nối với phần của thành viên khác:**

Nhận output từ supervisor/workers để bổ sung lớp tool orchestration qua MCP, là cầu nối giữa routing (Sprint 1–2) và đo lường hệ thống (Sprint 4): policy worker gọi MCP tools, còn trace/eval ghi lại toàn bộ call-chain để debug. Nếu phần này thiếu, nhóm vẫn chạy được pipeline nhưng không đạt yêu cầu Sprint 3 (tool integration + trace) và Sprint 4 (metrics/report).

**Bằng chứng (commit hash, file có comment tên bạn, v.v.):**

Trong code hiện tại có đầy đủ fields do tôi phụ trách: `mcp_tools_used`, `mcp_tool_called`, `mcp_result` (trong `workers/policy_tool.py`) và các báo cáo `artifacts/grading_run.jsonl`, `artifacts/eval_report.json`, `artifacts/grading_eval.json`.

---

## 2. Tôi đã ra một quyết định kỹ thuật gì? (150–200 từ)

> Chọn **1 quyết định** bạn trực tiếp đề xuất hoặc implement trong phần mình phụ trách.
> Giải thích:
> - Quyết định là gì?
> - Các lựa chọn thay thế là gì?
> - Tại sao bạn chọn cách này?
> - Bằng chứng từ code/trace cho thấy quyết định này có effect gì?

**Quyết định:** Tôi chọn chuẩn hóa toàn bộ external capability qua MCP dispatch (`mcp_server.dispatch_tool`) thay vì gọi trực tiếp từng function domain trong policy worker.

**Lý do:**

Tôi có hai lựa chọn:  
1) worker gọi trực tiếp retrieval/ticket/access logic (ít lớp trung gian, làm nhanh),  
2) worker chỉ gọi tool qua một chuẩn MCP call object gồm `tool`, `input`, `output`, `error`, `timestamp`.  

Tôi chọn phương án 2 vì mục tiêu Day 09 là **orchestration + observability**. Khi dùng chuẩn MCP call object, tôi có thể ghi trace đồng nhất cho mọi tool và phân tích được usage theo tỷ lệ ở Sprint 4. Điều này cũng giúp mở rộng tool mới mà không đụng sâu vào orchestration layer.

**Trade-off đã chấp nhận:**

Độ phức tạp tăng, và nếu mapping input/schema không chặt thì dễ phát sinh runtime error trong grading.

**Bằng chứng từ trace/code:**

```python
# workers/policy_tool.py
mcp_result = _call_mcp_tool("search_kb", {"query": task, "top_k": 3})
state["mcp_tools_used"].append(mcp_result)
state["mcp_tool_called"].append("search_kb")
state["mcp_result"].append(mcp_result.get("output"))
```

```json
// artifacts/eval_report.json
"mcp_usage_rate": "35/73 (47%)",
"hitl_rate": "3/73 (4%)"
```

---

## 3. Tôi đã sửa một lỗi gì? (150–200 từ)

> Mô tả 1 bug thực tế bạn gặp và sửa được trong lab hôm nay.
> Phải có: mô tả lỗi, symptom, root cause, cách sửa, và bằng chứng trước/sau.

**Lỗi:** Policy worker trước đó không ghi đủ metadata cho MCP call nên trace thiếu tính debug, đồng thời phần graph có chỗ dễ ghi đè output worker làm khó theo dõi nguyên nhân lỗi.

**Symptom (pipeline làm gì sai?):**

Khi chạy các câu policy/access khó, tôi thấy kết quả không ổn định và thiếu dữ liệu để trả lời câu hỏi “lỗi nằm ở routing hay tool-call”. Trace chỉ có một phần log, thiếu danh sách tool name và output chi tiết theo từng lần gọi.

**Root cause (lỗi nằm ở đâu — indexing, routing, contract, worker logic?):**

Root cause nằm ở **worker contract implementation và trace schema** trong `workers/policy_tool.py`: chưa có các trường tách biệt để audit từng call (`mcp_tool_called`, `mcp_result`). Thêm vào đó, luồng graph có đoạn wrapper dễ làm mờ output thực của worker.

**Cách sửa:**

Tôi bổ sung state keys `mcp_tool_called`, `mcp_result`, append nhất quán cho từng tool call (`search_kb`, `get_ticket_info`, `check_access_permission`), đồng thời giữ output worker “as-is” để trace phản ánh đúng dữ liệu thực.

**Bằng chứng trước/sau:**
> Dán trace/log/output trước khi sửa và sau khi sửa.

Trước khi sửa, trace không đủ thông tin để truy “tool nào gây lỗi”. Sau khi sửa, trong `artifacts/grading_eval.json` record `gq09`, tôi thấy đầy đủ 3 MCP calls với input/output/error từng call; nhờ đó xác định rõ lỗi nằm ở tool input/schema thay vì routing.

---

## 4. Tôi tự đánh giá đóng góp của mình (100–150 từ)

> Trả lời trung thực — không phải để khen ngợi bản thân.

**Tôi làm tốt nhất ở điểm nào?**

Tôi làm tốt nhất ở việc biến Sprint 3 thành nền tảng cho Sprint 4: không chỉ “gọi được MCP” mà còn để lại trace có thể đo lường và debug. Tôi chủ động kết nối phần kỹ thuật với phần báo cáo số liệu (`eval_report`, `grading_eval`) để nhóm có bằng chứng cụ thể.

**Tôi làm chưa tốt hoặc còn yếu ở điểm nào?**

Tôi chưa harden schema validation đủ sớm ở `dispatch_tool`, nên grading xuất hiện lỗi input mapping trong một số case khó. Điều này ảnh hưởng trực tiếp đến score.

**Nhóm phụ thuộc vào tôi ở đâu?** _(Phần nào của hệ thống bị block nếu tôi chưa xong?)_

Nhóm phụ thuộc vào tôi ở khâu MCP integration và trace analytics. Nếu phần tôi chưa xong, pipeline không đạt yêu cầu Sprint 3 và Sprint 4 gần như không có dữ liệu tin cậy để phân tích.

**Phần tôi phụ thuộc vào thành viên khác:** _(Tôi cần gì từ ai để tiếp tục được?)_

Tôi phụ thuộc vào phần supervisor/worker core (Sprint 1–2) để có luồng route ổn định và output worker đúng contract trước khi tôi chạy grading/eval.

---

## 5. Nếu có thêm 2 giờ, tôi sẽ làm gì? (50–100 từ)

> Nêu **đúng 1 cải tiến** với lý do có bằng chứng từ trace hoặc scorecard.
> Không phải "làm tốt hơn chung chung" — phải là:
> *"Tôi sẽ thử X vì trace của câu gq___ cho thấy Y."*

Tôi sẽ thêm lớp **input normalization + schema validation cứng trong `dispatch_tool`** vì trace của `gq09` cho thấy tool-call hiện fail ở input/schema (`get_ticket_info`, `check_access_permission`) dù route đúng. Nếu chặn lỗi từ gateway này, tôi kỳ vọng giảm đáng kể các case Penalty do thiếu evidence, đặc biệt ở nhóm câu multi-hop.

---

*Lưu file này với tên: `reports/individual/[ten_ban].md`*  
*Ví dụ: `reports/individual/nguyen_van_a.md`*
