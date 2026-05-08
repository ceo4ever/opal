# Examples

Two complete worked examples to draw from. When the user describes a new system, find the closest example and adapt — don't start from scratch.

## Example 1 — Consumer SaaS (vertical AI agent)

**Context:** AI booking manager for hair salons. 24/7 KakaoTalk responses, reservation handling, no-show prevention. Target: salons with 2–5 designers. BM: ₩240k/month subscription.

**Header values:**
- Title: `미용실 AI 예약 매니저`
- Subtitle: `— 6 layer system blueprint`
- Lede: `카카오톡 채널 1개로 시작해 멀티 에이전트 오케스트레이션, 매장별 RAG, 휴먼-인-더-루프까지. 12주 안에 빌드 가능한 AI Native SaaS의 참조 아키텍처.`
- Meta: `TARGET 미용실 (1차)` / `BM 월 9.9~79만 SaaS` / `STACK Claude · pgvector · Next.js` / `MVP 12주`

**Layers:**

| L | Name | Tag | Nodes |
|---|------|-----|-------|
| 1 | Customer Channel | 고객이 메시지를 보내는 진입점 | 카카오톡 채널 (MVP) / 네이버 톡톡 (LATER) / 웹 위젯 (LATER) |
| 2 | Orchestration | 의도 분류 & 라우팅 | 메시지 라우터 + 의도 분류기 (MVP) |
| 3 | AI Agents | 멀티 에이전트 — 각자 다른 책임 | 예약 에이전트 (MVP) / FAQ 에이전트 (MVP) / 리마인드 에이전트 (LATER) |
| 4 | Brain & Data | 지식 저장소 — 셋이 다른 역할 | 매장 RAG (MVP) / 예약 DB (MVP) / 대화 메모리 (LATER) |
| 5 | External Services | 외부 API 연동 | LLM 라우터 (MVP) / 알림톡 API (LATER) / 결제 + 관측 (MVP) |
| 6 | Operator Console | 원장님이 직접 보는 화면 | 원장 대시보드 (MVP) / 휴먼 인 더 루프 (MVP) |

**Roadmap tracks:**
- ▶ Week 3-6 — MVP 빌드 (카톡 1채널, 의도 라우터, 두 에이전트, 기본 데이터, 대시보드)
- ▶ Week 7-12 — 베타 중 추가 (리마인드, 알림톡, 메모리, 위험 알림)
- ▶ 6+ 개월 — 미룰 것 (음성, 다지점, 마케팅 자동화, 인접 업종 확장)

## Example 2 — Enterprise AI Platform (B2B internal tool)

**Context:** Internal knowledge platform for a financial services firm. Indexes regulatory documents, internal SOPs, market data. Target: 1,200 internal analysts. BM: internal cost center.

**Header values:**
- Title: `Compliance Copilot`
- Subtitle: `— Internal knowledge & analysis platform`
- Lede: `Regulatory documents, internal SOPs, and market context unified into a single agent surface. SOC 2-ready, on-prem deployable, with human review gates on all client-facing outputs.`
- Meta: `OWNER Risk & Compliance Eng` / `USERS 1,200 analysts` / `STACK Bedrock · OpenSearch · Snowflake` / `SLA 99.9%`

**Layers:**

| L | Name | Tag | Nodes |
|---|------|-----|-------|
| 1 | Surfaces | Where analysts initiate queries | Web app (DONE) / Slack bot (MVP) / Excel add-in (LATER) |
| 2 | Gateway | Auth, audit, rate limit | API gateway + audit logger (DONE) |
| 3 | Reasoning | Multi-step agents per task | Research agent (DONE) / Drafting agent (MVP) / Review agent (MVP) |
| 4 | Knowledge | Indexed corpora | Regulations index (DONE) / SOPs index (DONE) / Market data warehouse (DONE) |
| 5 | Foundation | Models & infra | Bedrock (Claude/Titan) (DONE) / Embeddings pipeline (DONE) / Eval harness (MVP) |
| 6 | Governance | Compliance gates | Output review queue (MVP) / Lineage & audit (DONE) |

**Roadmap tracks:**
- ▶ Q1 2026 — Foundation (drafting & review agents, eval harness, output review queue)
- ▶ Q2 2026 — Scale (Slack bot rollout, multi-tenant SOPs, latency reduction)
- ▶ H2 2026 — Expansion (Excel add-in, structured output schemas, broker integrations)

## How to adapt examples

1. **Match the closest pattern.** Consumer SaaS = Example 1. B2B internal tool / enterprise platform = Example 2.
2. **Keep the layer count.** Both examples are 6 layers — that's the sweet spot.
3. **Vary box grid sizes per layer.** L2 typically `boxes-1` (single router). L1, L3, L4, L5 typically `boxes-3`. L6 typically `boxes-2`.
4. **Customize meta panel labels.** Consumer-facing → TARGET / BM. Internal → OWNER / USERS / SLA.
5. **Status badges shift across project lifecycle.**
   - Greenfield project → mostly MVP + LATER
   - Existing system being documented → mostly DONE + a few MVP for next quarter
   - Mid-project → mix of all three

## Common variations

**Fewer than 6 layers:** if the system genuinely has fewer layers, remove the unused `.layer` blocks and `.connector` divs. Don't pad with empty layers. Update the legend to match.

**More than 6 layers:** don't go above 6. If pressure exists, ask whether two layers can merge (e.g. "Brain" and "Data" are often the same layer) or whether the diagram should be split into two — one architectural overview and one detailed sub-system.

**No roadmap section:** for documentation of an existing system, the roadmap may not apply. Remove the entire `<section class="roadmap">` block. Make sure the footer still has appropriate context.
