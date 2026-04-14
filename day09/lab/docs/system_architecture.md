# System Architecture — Lab Day 09

**Nhóm:** Z11  
**Ngày:** 14/4/2026  
**Version:** 1.0

---

## 1. Tổng quan kiến trúc

> Mô tả ngắn hệ thống của nhóm: chọn pattern gì, gồm những thành phần nào.

**Pattern đã chọn:** Supervisor-Worker  
**Lý do chọn pattern này (thay vì single agent):**

Nhóm chọn Supervisor-Worker để tách rõ trách nhiệm: supervisor chỉ route + gắn cờ rủi ro, mỗi worker xử lý một nhiệm vụ chuyên biệt (retrieve, policy/tool, synthesis). Cách này giúp debug theo trace dễ hơn (thấy rõ route_reason, worker nào gây lỗi), test độc lập từng worker, và thêm MCP capability mà không phải sửa toàn bộ prompt như kiến trúc single-agent.

---

## 2. Sơ đồ Pipeline

> Vẽ sơ đồ pipeline dưới dạng text, Mermaid diagram, hoặc ASCII art.
> Yêu cầu tối thiểu: thể hiện rõ luồng từ input → supervisor → workers → output.

**Ví dụ (ASCII art):**
```
User Request
     │
     ▼
┌──────────────┐
│  Supervisor  │  ← route_reason, risk_high, needs_tool
└──────┬───────┘
       │
   [route_decision]
       │
  ┌────┴────────────────────┐
  │                         │
  ▼                         ▼
Retrieval Worker     Policy Tool Worker
  (evidence)           (policy check + MCP)
  │                         │
  └─────────┬───────────────┘
            │
            ▼
      Synthesis Worker
        (answer + cite)
            │
            ▼
         Output
```

**Sơ đồ thực tế của nhóm:**

```
User Question
    |
    v
Supervisor (graph.py)
  - quyết định: supervisor_route
  - ghi: route_reason, risk_high, needs_tool
    |
    +--> human_review (nếu risk_high + unknown error pattern "ERR-")
    |        |
    |        +--> retrieval_worker
    |
    +--> policy_tool_worker (khi có keyword policy/access)
    |        |- MCP: search_kb (khi thiếu chunks và needs_tool=True)
    |        |- MCP: get_ticket_info (task có ticket/P1/Jira)
    |        |- MCP: check_access_permission (task có access/level)
    |        v
    |     (nếu chưa có chunks) retrieval_worker
    |
    +--> retrieval_worker (default)
             |
             v
      synthesis_worker (LLM/fallback, cite sources, confidence)
             |
             v
           Output + Trace JSON
```

---

## 3. Vai trò từng thành phần

### Supervisor (`graph.py`)

| Thuộc tính | Mô tả |
|-----------|-------|
| **Nhiệm vụ** | Phân tích task, quyết định route, gắn cờ `risk_high`, quyết định `needs_tool`, ghi trace routing |
| **Input** | `task` từ user và `history` hiện tại |
| **Output** | supervisor_route, route_reason, risk_high, needs_tool |
| **Routing logic** | Keyword-based: policy/access/refund/flash sale/license/level 3 -> `policy_tool_worker`; mặc định -> `retrieval_worker`; nếu `risk_high` và có pattern `err-` -> `human_review` |
| **HITL condition** | Trigger `human_review` khi `risk_high=True` và task chứa mã lỗi không rõ (`ERR-*`) |

### Retrieval Worker (`workers/retrieval.py`)

| Thuộc tính | Mô tả |
|-----------|-------|
| **Nhiệm vụ** | Semantic retrieval từ ChromaDB, trả `retrieved_chunks` + `retrieved_sources`, ghi `worker_io_logs` |
| **Embedding model** | `all-MiniLM-L6-v2` (SentenceTransformer); fallback `text-embedding-3-small` nếu dùng OpenAI |
| **Top-k** | Mặc định `3` (`retrieval_top_k` có thể override từ state) |
| **Stateless?** | Yes |

### Policy Tool Worker (`workers/policy_tool.py`)

| Thuộc tính | Mô tả |
|-----------|-------|
| **Nhiệm vụ** | Phân tích policy bằng rule-based, gọi MCP tools theo nhu cầu, ghi `policy_result`, `mcp_tools_used`, `mcp_result` |
| **MCP tools gọi** | `search_kb`, `get_ticket_info`, `check_access_permission` |
| **Exception cases xử lý** | Flash Sale, digital product/license/subscription, sản phẩm đã kích hoạt/đăng ký; có note cho trường hợp đơn trước 01/02/2026 |

### Synthesis Worker (`workers/synthesis.py`)

| Thuộc tính | Mô tả |
|-----------|-------|
| **LLM model** | Ưu tiên `gpt-4o-mini` (OpenAI), fallback `gemini-1.5-flash`, cuối cùng fallback rule-based text synthesis |
| **Temperature** | `0.1` |
| **Grounding strategy** | Build context trực tiếp từ `retrieved_chunks` + `policy_result`, yêu cầu trả lời chỉ từ context, cite theo source |
| **Abstain condition** | Không có chunks hoặc context không đủ -> trả "Không đủ thông tin trong tài liệu nội bộ" |

### MCP Server (`mcp_server.py`)

| Tool | Input | Output |
|------|-------|--------|
| search_kb | query, top_k | chunks, sources |
| get_ticket_info | ticket_id | ticket details |
| check_access_permission | access_level, requester_role | can_grant, approvers |
| create_ticket (mock) | priority, title, description | ticket_id, url, created_at |

---

## 4. Shared State Schema

> Liệt kê các fields trong AgentState và ý nghĩa của từng field.

| Field | Type | Mô tả | Ai đọc/ghi |
|-------|------|-------|-----------|
| task | str | Câu hỏi đầu vào | supervisor đọc |
| supervisor_route | str | Worker được chọn | supervisor ghi |
| route_reason | str | Lý do route | supervisor ghi |
| risk_high | bool | Cờ rủi ro cao | supervisor ghi, human_review đọc |
| needs_tool | bool | Có cần gọi MCP hay không | supervisor ghi, policy_tool đọc |
| hitl_triggered | bool | Đã kích hoạt human-in-the-loop hay chưa | human_review ghi |
| retrieved_chunks | list | Evidence từ retrieval | retrieval ghi, synthesis đọc |
| retrieved_sources | list | Danh sách file nguồn từ retrieval | retrieval ghi, synthesis/trace đọc |
| policy_result | dict | Kết quả kiểm tra policy | policy_tool ghi, synthesis đọc |
| mcp_tools_used | list | Tool calls đã thực hiện | policy_tool ghi |
| mcp_tool_called | list | Danh sách tên MCP tool đã gọi | policy_tool ghi |
| mcp_result | list | Kết quả output thô từ MCP | policy_tool ghi, trace/eval đọc |
| sources | list | Sources dùng trong câu trả lời cuối | synthesis ghi |
| final_answer | str | Câu trả lời cuối | synthesis ghi |
| confidence | float | Mức tin cậy | synthesis ghi |
| history/workers_called/run_id/latency_ms | list/list/str/int | Trace lịch sử chạy và thời gian xử lý | mọi node ghi, eval đọc |

---

## 5. Lý do chọn Supervisor-Worker so với Single Agent (Day 08)

| Tiêu chí | Single Agent (Day 08) | Supervisor-Worker (Day 09) |
|----------|----------------------|--------------------------|
| Debug khi sai | Khó — không rõ lỗi ở đâu | Dễ hơn — test từng worker độc lập |
| Thêm capability mới | Phải sửa toàn prompt | Thêm worker/MCP tool riêng |
| Routing visibility | Không có | Có route_reason trong trace |
| Khả năng audit tool call | Thường không rõ tool nào chạy | Có `mcp_tool_called`, `mcp_result`, `worker_io_logs` |

**Nhóm điền thêm quan sát từ thực tế lab:**

Từ trace thực tế của nhóm, các câu policy/access (Flash Sale, Level 3 emergency) được route vào `policy_tool_worker` và kích hoạt MCP đúng mục đích. Các câu fact retrieval route vào `retrieval_worker`. Khi câu trả lời sai nhưng route đúng, nhóm xác định nhanh lỗi thuộc retrieval quality/synthesis thay vì routing.

---

## 6. Giới hạn và điểm cần cải tiến

> Nhóm mô tả những điểm hạn chế của kiến trúc hiện tại.

1. Routing hiện tại chủ yếu keyword-based, chưa có classifier ngữ nghĩa nên dễ miss edge cases phrasing lạ.
2. `human_review` mới ở mức placeholder auto-approve, chưa có vòng phê duyệt thật.
3. Confidence hiện là heuristic từ score chunk, chưa phản ánh đầy đủ chất lượng lập luận cuối.
