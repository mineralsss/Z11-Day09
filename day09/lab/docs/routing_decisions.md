# Routing Decisions Log — Lab Day 09

**Nhóm:** Z11  
**Ngày:** 14/4/2026

> **Hướng dẫn:** Ghi lại ít nhất **3 quyết định routing** thực tế từ trace của nhóm.
> Không ghi giả định — phải từ trace thật (`artifacts/traces/`).
> 
> Mỗi entry phải có: task đầu vào → worker được chọn → route_reason → kết quả thực tế.

---

## Routing Decision #1

**Task đầu vào:**
> SLA xử lý ticket P1 là bao lâu?

**Worker được chọn:** `retrieval_worker`  
**Route reason (từ trace):** `default route to retrieval for general knowledge query | no MCP needed`  
**MCP tools được gọi:** `[]`  
**Workers called sequence:** `retrieval_worker -> synthesis_worker`

**Kết quả thực tế:**
- final_answer (ngắn): "SLA xử lý ticket P1 là 5 ngày làm việc [1]."
- confidence: `0.60`
- Correct routing? Yes

**Nhận xét:** _(Routing này đúng hay sai? Nếu sai, nguyên nhân là gì?)_

Đúng hướng route (truy vấn fact retrieval), không cần policy/MCP. Tuy nhiên câu trả lời còn sai nội dung SLA P1 (nêu 5 ngày), cho thấy lỗi nằm ở retrieval chunk quality/synthesis, không phải ở quyết định route.

---

## Routing Decision #2

**Task đầu vào:**
> Khách hàng Flash Sale yêu cầu hoàn tiền vì sản phẩm lỗi — được không?

**Worker được chọn:** `policy_tool_worker`  
**Route reason (từ trace):** `task contains policy/access keyword | choose MCP tools`  
**MCP tools được gọi:** `search_kb`  
**Workers called sequence:** `policy_tool_worker -> synthesis_worker`

**Kết quả thực tế:**
- final_answer (ngắn): "Flash Sale không được hoàn tiền dù sản phẩm lỗi do nhà sản xuất."
- confidence: `0.64`
- Correct routing? Yes

**Nhận xét:**

Đây là case policy + exception nên route sang policy_tool_worker là hợp lý. MCP search_kb kéo đúng nguồn `policy_refund_v4.txt`, giúp trả lời bám policy và có căn cứ.

---

## Routing Decision #3

**Task đầu vào:**
> Cần cấp quyền Level 3 để khắc phục P1 khẩn cấp. Quy trình là gì?

**Worker được chọn:** `policy_tool_worker`  
**Route reason (từ trace):** `task contains policy/access keyword | risk_high flagged | choose MCP tools`  
**MCP tools được gọi:** `search_kb, get_ticket_info, check_access_permission`  
**Workers called sequence:** `policy_tool_worker -> synthesis_worker`

**Kết quả thực tế:**
- final_answer (ngắn): "Cần phê duyệt + cấp quyền tạm thời 24h + tạo ticket chính thức + ghi Security Audit."
- confidence: `0.66`
- Correct routing? Yes

**Nhận xét:**

Case này vừa access-control vừa emergency nên cần tool orchestration. Route hiện tại tốt vì kích hoạt cả 3 MCP tools và tổng hợp được quy trình có thể hành động.

---

## Routing Decision #4 (tuỳ chọn — bonus)

**Task đầu vào:**
> SLA xử lý ticket P1 là bao lâu? (trace cũ `run_20260414_152817`)

**Worker được chọn:** `retrieval_worker`  
**Route reason:** `default route`

**Nhận xét: Đây là trường hợp routing khó nhất trong lab. Tại sao?**

Khó ở chỗ route đúng nhưng output có thể vẫn sai do chunk retrieval không chuẩn hoặc synthesis chọn nhầm chi tiết. Nhóm rút ra rằng đánh giá routing phải tách biệt với đánh giá correctness của final answer.

---

## Tổng kết

### Routing Distribution

| Worker | Số câu được route | % tổng |
|--------|------------------|--------|
| retrieval_worker | 1 | 33.3% |
| policy_tool_worker | 2 | 66.7% |
| human_review | 0 | 0% |

### Routing Accuracy

> Trong số 3 câu đại diện được phân tích trong tài liệu này, supervisor route đúng toàn bộ.

- Câu route đúng: 3 / 3
- Câu route sai (đã sửa bằng cách nào?): 0
- Câu trigger HITL: 0

### Lesson Learned về Routing

> Quyết định kỹ thuật quan trọng nhất nhóm đưa ra về routing logic là gì?  
> (VD: dùng keyword matching vs LLM classifier, threshold confidence cho HITL, v.v.)

1. Ưu tiên keyword-based routing + risk flag để kiểm soát tính nhất quán trước khi nâng cấp lên classifier bằng LLM.
2. Khi `needs_tool=true`, route vào policy_tool_worker để gom logic gọi MCP, tránh để retrieval_worker gọi tool trực tiếp.

### Route Reason Quality

> Nhìn lại các `route_reason` trong trace — chúng có đủ thông tin để debug không?  
> Nếu chưa, nhóm sẽ cải tiến format route_reason thế nào?

`route_reason` đã đủ hữu ích vì ghi rõ tín hiệu quyết định (`policy/access keyword`, `risk_high`, `choose MCP`). Bản cải tiến tiếp theo: chuẩn hoá thành format key-value, ví dụ `signals=[policy_keyword,risk_high], decision=policy_tool_worker, mcp=true` để dễ thống kê tự động.
