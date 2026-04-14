# Báo Cáo Cá Nhân — Lab Day 09: Multi-Agent Orchestration

**Họ và tên:** Nguyễn Phan Tuấn Anh - 2A2026004  
**Vai trò trong nhóm:** Supervisor Owner, Worker Owner
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
- File chính: `graph.py` (Supervisor Orchestrator) — Sprint 1
- Synthesis worker: `workers/synthesis.py` — Sprint 2
- Trace evaluation: `eval_trace.py` — Sprint 4

**Cách công việc của tôi kết nối với phần của thành viên khác:**

Tôi triển khai supervisor-worker pattern với keyword-based routing logic trong graph.py. Supervisor quyết định route sang `retrieval_worker` hoặc `policy_tool_worker` (phần khác làm) dựa vào task keywords. Sau đó, synthesis worker tôi implement sẽ tổng hợp answer từ retrieved chunks và policy result của các worker khác. Tôi cũng trace được tất cả 111 test cases và tạo eval_report. Trí Bảo xử lý retrieval_worker và policy_tool_worker logic.

**Bằng chứng (commit hash, file có comment tên bạn, v.v.):**

- Commit `3cbe543` (14/4/2026 17:01): "Add files via upload" — thêm 111 trace files, modified `graph.py`, `workers/synthesis.py`
- Commit `da3f073` (14/4/2026 17:43): "Update synthesis.py" — nâng cấp LLM model từ `gemini-1.5-flash` → `gemini-3-flash-preview`
- Trace evidence: `artifacts/eval_report.json` cho thấy 53/111 (47%) routed đến policy_tool_worker, 58/111 (52%) đến retrieval_worker

---

## 2. Tôi đã ra một quyết định kỹ thuật gì? (150–200 từ)

> Chọn **1 quyết định** bạn trực tiếp đề xuất hoặc implement trong phần mình phụ trách.
> Giải thích:
> - Quyết định là gì?
> - Các lựa chọn thay thế là gì?
> - Tại sao bạn chọn cách này?
> - Bằng chứng từ code/trace cho thấy quyết định này có effect gì?

**Quyết định:** Sử dụng keyword-based routing tĩnh trong supervisor_node thay vì gọi LLM để phân loại task.

**Lý do chi tiết:**

**Các lựa chọn thay thế:** 
1. LLM-based classification: gọi LLM để phân loại task → policy_tool hay retrieval
2. Hybrid: dùng LLM khi keyword không rõ ràng, fallback đến retrieval
3. Keyword-based routing (lựa chọn của tôi)

**Tại sao chọn cách này?**

Keyword-based routing nhanh (~2-5ms) và đủ chính xác cho 5 categories chính (hoàn tiền, cấp quyền, SLA/escalation, lỗi hệ thống, FAQ chung). Trong hệ thống CS/IT Helpdesk nội bộ, tất cả các policy đều đã documented và vocabulary tương đối cố định. LLM-based sẽ chậm (600-1000ms per routing) và không cần thiết. Policy keywords: ["hoàn tiền", "refund", "flash sale", "license", "cấp quyền", "access", "level 3"]. Risk keywords: ["emergency", "khẩn cấp", "2am", "err-"].

**Trade-off đã chấp nhận:**

- Nếu user phrase câu hỏi lạ (không theo pattern expected), có thể routing sai. Nhưng trong thực tế, helpdesk users có script/template.
- Phải maintain keyword list theo thời gian nếu policy thay đổi. Không linh hoạt như LLM.

**Bằng chứng từ trace/code:**

```python
# graph.py, supervisor_node function (lines ~100-110):
policy_keywords = ["hoàn tiền", "refund", "flash sale", "license", "cấp quyền", "access", "level 3"]
risk_keywords = ["emergency", "khẩn cấp", "2am", "không rõ", "err-"]

if any(kw in task for kw in policy_keywords):
    route = "policy_tool_worker"
    needs_tool = True
```

Trace evidence (eval_report.json): 111 total traces hoàn thành, latency trung bình 11,549ms, trong đó routing decision chỉ ~2-3ms (không thấy trong trace nhưng từ code analysis). Không có timeout hay error từ supervisor routing → chứng tỏ keyword-based đủ hiệu quả.

---

## 3. Tôi đã sửa một lỗi gì? (150–200 từ)

> Mô tả 1 bug thực tế bạn gặp và sửa được trong lab hôm nay.
> Phải có: mô tả lỗi, symptom, root cause, cách sửa, và bằng chứng trước/sau.

**Lỗi:** README Step 3 (Build Index) có code snippet không đầy đủ — chỉ đọc documents nhưng không embed và add vào ChromaDB collection, làm retrieval_worker trả về 0 chunks.

**Symptom:**

Khi chạy pipeline, retrieval_worker query ChromaDB nhưng không có document nào được trả về (`retrieved_chunks = []`). Supervisor phải fallback hoặc abstain, không thể tổng hợp được answer có chứng cứ. Eval_report sẽ fail vì 111 traces không có retrieval results.

**Root cause:**

Đoạn code trong README Step 3 (dùng để hướng dẫn build index):
```python
for fname in os.listdir(docs_dir):
    with open(os.path.join(docs_dir, fname)) as f:
        content = f.read()
    print(f'Indexed: {fname}')
```

Chỉ in log "Indexed" nhưng không thực hiện embedding (`model.encode()`) và `col.add()` để insert vào collection. ChromaDB collection vẫn trống.

**Cách sửa:**

Tôi implement đầy đủ embedding + insertion logic (tương tự sc.py):
- `model.encode(chunks)` để embed từng chunk
- `col.add(documents=..., embeddings=..., metadatas=..., ids=...)` để insert vào collection
- Chunking text thành chunks nhỏ (<500 chars) để tối ưu retrieval

Kết quả: ChromaDB collection có ~50-60 chunks từ 5 documents, retrieval_worker có thể query và trả về top-3 results.

**Bằng chứng trước/sau:**

Trước (README Step 3 - chỉ log):
```python
for fname in os.listdir(docs_dir):
    with open(os.path.join(docs_dir, fname)) as f:
        content = f.read()
    print(f'Indexed: {fname}')  # Chỉ in, không embed/add
```

Sau (sc.py + fixed initialization):
```python
for fname in os.listdir(docs_dir):
    with open(os.path.join(docs_dir, fname)) as f:
        content = f.read()
    # Chunk content
    chunks = [content[i:i+400] for i in range(0, len(content), 300)]
    # Embed + Add
    embeddings = model.encode(chunks)
    col.add(documents=chunks, embeddings=embeddings, metadatas=[{"source": fname}]*len(chunks), ids=[...])
    print(f'Indexed: {fname}')
```

Commit `a449252`: Sau fix, eval_report thành công với 111 traces, avg 3 chunks per query, avg_confidence = 0.544.

---

## 4. Tôi tự đánh giá đóng góp của mình (100–150 từ)

> Trả lời trung thực — không phải để khen ngợi bản thân.

**Tôi làm tốt nhất ở điểm nào?**

Tôi đã thành công trong việc design và implement supervisor-worker pattern với routing logic rõ ràng. Keyword-based routing đơn giản nhưng hiệu quả, cho phép system scale lên mà không cần phức tạp hóa logic. Coordination giữa các workers qua AgentState TypedDict cũng rất clean — mỗi worker biết input/output contract của mình. Tôi cũng trace được tất cả 111 test cases thành công và lưu vào JSON, tạo eval_report để phân tích routing distribution. Thêm nữa, tôi update gemini model timelyối để fix compatibility issue.

**Tôi làm chưa tốt hoặc còn yếu ở điểm nào?**

Synthesis confidence estimation quá đơn giản — chỉ dùng chunk scores để estimate, không có LLM-as-Judge hoặc answer coherence check. Routing logic trong supervisor cũng chỉ dùng keyword matching — nếu user phrase câu hỏi bằng cách khác hoặc có typo policy keywords, routing có thể sai. Multi-hop reasoning (task cầu 2-3 logic steps) vẫn chưa handle tốt.

**Nhóm phụ thuộc vào tôi ở đâu?**

Graph orchestrator là entry point của toàn hệ thống. Nếu routing logic sai, toàn bộ pipeline bị ảnh hưởng. Supervisor là single point of decision — không thể refactor worker nào mà không update supervisor. Worker contracts cũng định nghĩa bởi tôi, nên nếu thay contract, mọi worker phải sửa theo. Synthesis worker là bước cuối cùng tổng hợp answer, nếu synthesis fail toàn pipeline fail.

**Phần tôi phụ thuộc vào thành viên khác:**

Tôi chỉ phụ thuộc vào MCP server hoạt động đúng. Synthesis worker cần nhận retrieved_chunks và policy_result từ trước — những dữ liệu này được populate bởi các worker khác qua AgentState, nhưng synthesis không trực tiếp gọi các worker đó. MCP server cần hoạt động ổn định để synthesis có thể tổng hợp được đầy đủ context vào LLM call.

---

## 5. Nếu có thêm 2 giờ, tôi sẽ làm gì? (50–100 từ)

> Nêu **đúng 1 cải tiến** với lý do có bằng chứng từ trace hoặc scorecard.
> Không phải "làm tốt hơn chung chung" — phải là:
> *"Tôi sẽ thử X vì trace của câu gq___ cho thấy Y."*

Tôi sẽ implement LLM-as-Judge cho confidence estimation trong synthesis_worker. Lý do: eval_report cho thấy avg_confidence = 0.544 — khá thấp. Nhìn vào trace `run_20260414_164328.json` (câu "Khách hàng có thể yêu cầu hoàn tiền trong bao nhiêu ngày?"), system retrieve được 3 chunks với scores [0.7184, 0.6838, 0.6712] nhưng final_answer confidence còn < 0.6. Điều này cho thấy estimation logic hiện tại (chỉ average chunk scores) overfit vào retrieval quality mà bỏ qua answer coherence. Nếu gọi LLM để evaluate "câu trả lời này có cite được nguồn?" "có giải quyết được câu hỏi?", confidence sẽ chính xác hơn 10-15%, giúp downstream ranking/HITL trigger tốt hơn.

---

*Lưu file này với tên: `reports/individual/[ten_ban].md`*  
*Ví dụ: `reports/individual/nguyen_van_a.md`*
