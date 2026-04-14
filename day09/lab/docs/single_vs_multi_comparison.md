# Single Agent vs Multi-Agent Comparison — Lab Day 09

**Nhóm:** Z11  
**Ngày:** 14/4/2026

> **Hướng dẫn:** So sánh Day 08 (single-agent RAG) với Day 09 (supervisor-worker).
> Phải có **số liệu thực tế** từ trace — không ghi ước đoán.
> Chạy cùng test questions cho cả hai nếu có thể.

---

## 1. Metrics Comparison

> Điền vào bảng sau. Lấy số liệu từ:
> - Day 08: chạy `python eval.py` từ Day 08 lab
> - Day 09: chạy `python eval_trace.py` từ lab này

| Metric | Day 08 (Single Agent) | Day 09 (Multi-Agent) | Delta | Ghi chú |
|--------|----------------------|---------------------|-------|---------|
| Avg confidence | 0.92 | 0.484 | -0.436 | Day 09 conservative hơn (nhiều case fallback/abstain) |
| Avg latency (ms) | 2244 | 10100 | +7856 | Multi-agent + MCP tăng latency |
| Abstain rate (%) | 20% (2/10) | N/A | N/A | `eval_report.json` chưa xuất metric abstain cho Day 09 |
| Multi-hop accuracy | 83.3% (5/6) | N/A | N/A | `eval_report.json` chưa có accuracy theo multi-hop của Day 09 |
| Routing visibility | ✗ Không có | ✓ Có route_reason | N/A | |
| Debug time (estimate) | ~25 phút | ~8 phút | -17 phút | Ước tính từ 1 lần debug thực tế của nhóm |
| MCP usage rate | 0% | 47% (35/73) | +47 điểm % | Day 09 mở rộng tool-call qua MCP |

> **Lưu ý:** Nếu không có Day 08 kết quả thực tế, ghi "N/A" và giải thích.

---

## 2. Phân tích theo loại câu hỏi

### 2.1 Câu hỏi đơn giản (single-document)

| Nhận xét | Day 08 | Day 09 |
|---------|--------|--------|
| Accuracy | Tốt với fact đơn giản | Không vượt trội rõ ràng (phụ thuộc retrieval quality) |
| Latency | Nhanh hơn (2244ms trung bình) | Chậm hơn (10100ms trung bình) |
| Observation | Pipeline ngắn, trả lời nhanh | Có trace rõ route/worker, dễ kiểm tra lỗi theo bước |

**Kết luận:** Multi-agent có cải thiện không? Tại sao có/không?

Với câu đơn giản, multi-agent không cho lợi ích accuracy rõ rệt nhưng đổi lại có khả năng quan sát và debug tốt hơn. Nếu mục tiêu chính là tốc độ cho FAQ đơn giản, single-agent vẫn lợi thế.

### 2.2 Câu hỏi multi-hop (cross-document)

| Nhận xét | Day 08 | Day 09 |
|---------|--------|--------|
| Accuracy | 83.3% (5/6) | N/A |
| Routing visible? | ✗ | ✓ |
| Observation | Khó thấy lỗi ở bước nào | Có thể xem `supervisor_route`, `route_reason`, `workers_called`, `mcp_result` để tách lỗi route/retrieval/synthesis |

**Kết luận:**

Multi-agent có lợi thế rõ ở khả năng phân tách trách nhiệm và debug multi-hop; tuy nhiên cần bổ sung benchmark accuracy multi-hop Day 09 trên cùng bộ 6 câu để kết luận định lượng.

### 2.3 Câu hỏi cần abstain

| Nhận xét | Day 08 | Day 09 |
|---------|--------|--------|
| Abstain rate | 20% (2/10) | N/A |
| Hallucination cases | N/A (không có log chi tiết) | N/A |
| Observation | Có khả năng abstain nhưng thiếu trace chi tiết vì sao | Có route trace và confidence nhưng chưa tổng hợp riêng chỉ số abstain |

**Kết luận:**

Cần bổ sung thống kê abstain/hallucination trực tiếp từ file trace Day 09 để so sánh công bằng với Day 08.

---

## 3. Debuggability Analysis

> Khi pipeline trả lời sai, mất bao lâu để tìm ra nguyên nhân?

### Day 08 — Debug workflow
```
Khi answer sai → phải đọc toàn bộ RAG pipeline code → tìm lỗi ở indexing/retrieval/generation
Không có trace → không biết bắt đầu từ đâu
Thời gian ước tính: ~25 phút
```

### Day 09 — Debug workflow
```
Khi answer sai → đọc trace → xem supervisor_route + route_reason
  → Nếu route sai → sửa supervisor routing logic
  → Nếu retrieval sai → test retrieval_worker độc lập
  → Nếu synthesis sai → test synthesis_worker độc lập
Thời gian ước tính: ~8 phút
```

**Câu cụ thể nhóm đã debug:** _(Mô tả 1 lần debug thực tế trong lab)_

Case: câu "SLA xử lý ticket P1 là bao lâu?" có lần route đúng (`retrieval_worker`) nhưng answer sai. Nhờ trace Day 09, nhóm xác định nhanh vấn đề nằm ở retrieval chunk/synthesis (không phải routing), rồi chỉnh logic retrieval và kiểm tra lại worker độc lập.

---

## 4. Extensibility Analysis

> Dễ extend thêm capability không?

| Scenario | Day 08 | Day 09 |
|---------|--------|--------|
| Thêm 1 tool/API mới | Phải sửa toàn prompt | Thêm MCP tool + route rule |
| Thêm 1 domain mới | Phải retrain/re-prompt | Thêm 1 worker mới |
| Thay đổi retrieval strategy | Sửa trực tiếp trong pipeline | Sửa retrieval_worker độc lập |
| A/B test một phần | Khó — phải clone toàn pipeline | Dễ — swap worker |

**Nhận xét:**

Day 09 dễ mở rộng hơn rõ rệt: thêm tool mới chỉ cần implement trong `mcp_server.py` + cập nhật route rule, không phải đụng toàn bộ prompt orchestration.

---

## 5. Cost & Latency Trade-off

> Multi-agent thường tốn nhiều LLM calls hơn. Nhóm đo được gì?

| Scenario | Day 08 calls | Day 09 calls |
|---------|-------------|-------------|
| Simple query | 1 LLM call | 1 LLM call (synthesis) |
| Complex query | 1 LLM call | 1 LLM call + 1-3 MCP calls |
| MCP tool call | N/A | Có (mức dùng toàn hệ: 47%) |

**Nhận xét về cost-benefit:**

Trade-off chính: Day 09 tốn latency và orchestration overhead, nhưng đổi lại khả năng quan sát/kiểm soát pipeline tốt hơn, đặc biệt khi debug hoặc mở rộng nghiệp vụ có policy + tool integration.

---

## 6. Kết luận

> **Multi-agent tốt hơn single agent ở điểm nào?**

1. Debug dễ hơn nhờ trace chi tiết theo từng bước (`route_reason`, `workers_called`, `worker_io_logs`).
2. Dễ mở rộng capability qua MCP và tách worker theo domain mà không phá vỡ toàn pipeline.

> **Multi-agent kém hơn hoặc không khác biệt ở điểm nào?**

1. Latency cao hơn đáng kể; với query đơn giản thì chi phí orchestration có thể không đáng.

> **Khi nào KHÔNG nên dùng multi-agent?**

Khi hệ thống chỉ cần trả lời FAQ đơn giản, domain ổn định, không cần tool integration/HITL và ưu tiên tốc độ thấp độ trễ.

> **Nếu tiếp tục phát triển hệ thống này, nhóm sẽ thêm gì?**

Thêm benchmark chuẩn hoá cùng bộ câu hỏi cho Day 08/Day 09 (đặc biệt multi-hop + abstain), và nâng routing từ keyword sang classifier để giảm route sai do phrasing.
