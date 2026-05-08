# Copywriting

What separates a memorable architecture diagram from a forgettable one is the language. Most architecture diagrams fail because they read like a marketing brochure or a feature list. This guide makes the diagram feel like an engineer's actual notes.

## Voice and tone

- **Engineer-to-engineer.** Assume the reader codes. They don't need "powerful" or "cutting-edge."
- **Specific over generic.** "Postgres + pgvector for RAG over store policies" beats "Advanced AI knowledge base."
- **Trade-offs visible.** When a node has a known limitation or a deferred concern, mention it. "Single-channel for MVP, Naver Talk in v2." Honesty signals seniority.
- **Korean / English mix is fine** when the system has Korean-language users. Don't force translation. "카톡 채널 1개 — Kakao Biz API + Webhook" reads naturally.

## Header / meta panel

The top-right meta panel has 4 fields. Use these as the default labels:

| Field | What goes here | Example |
|-------|----------------|---------|
| TARGET | Customer segment | "디자이너 2~5명 미용실" |
| BM | Business model | "월 24만 SaaS" |
| STACK | Tech summary in 4–6 words | "Claude / Postgres / Next.js" |
| MVP | Timeline | "12주" |

Keep each line short — the panel is monospace 11px, max ~40 characters per line. If the field doesn't apply (e.g. an internal tool has no BM), replace the label with something useful: ENV, OWNER, REGION, SLA.

The H1 title formula:

```
{System name}
— {one-line capability or differentiator}
```

The em dash + italic accent pattern is part of the visual signature. Use it.

## Node titles

- 1–4 words
- Specific component name, not a generic category
- No marketing adjectives

| Bad | Good |
|-----|------|
| Powerful AI Brain | 매장 RAG |
| Smart Routing System | 메시지 라우터 |
| Customer Communication | 카카오톡 채널 |
| Cutting-Edge Database | 예약 DB |
| Robust Authentication | OAuth 2.0 / JWT |

## Node descriptions

The 1–2 sentence body of each node card. Format conventions:

**Pattern A — what it does + how:**
> "디자이너·시술·시간 매칭. 슬롯 충돌 검증. 변경/취소까지 트랜잭션 처리."

**Pattern B — what + why it matters:**
> "매장 톤 학습. 1개월치 카톡 데이터로 Few-shot. 차별화 핵심."

**Pattern C — what + boundaries:**
> "분류·간단응대는 Haiku/4o-mini, 복잡응대는 Sonnet/4o. 매장당 월 LLM 비용 ≤ 1만원 가드레일."

Use periods to separate clauses (creates a "field notes" rhythm). When a phrase is critical (the "차별화 핵심" or a guarantee), wrap it in `<b style="color:var(--accent)">` to draw the eye. Use this sparingly — once per layer at most.

**Length rules:**
- Maximum 140 characters per description
- 2 short sentences beats 1 long one
- If a node needs more explanation than fits, the node is too granular — merge with another, or split the layer

## Tech chips

The chip row at the bottom of each card. Rules:

- **Use real names.** "PostgreSQL" not "SQL Database". "Anthropic Claude" not "LLM Provider".
- **1 to 4 chips.** More than 4 is noise.
- **Order by importance.** Primary tech first, then supporting libraries, then infra.
- **Mix tech + concept where useful.** "RAG", "Few-shot", "Tool calling" are valid chips when the technique is the differentiator.

Examples:

| Layer type | Chips |
|------------|-------|
| Channel | `Kakao Biz API`, `Webhook` |
| Router | `Claude Haiku`, `규칙 기반 폴백`, `FastAPI` |
| Agent | `RAG`, `Tool calling`, `LangGraph` |
| Vector | `pgvector`, `OpenAI Embed` |
| Relational | `PostgreSQL`, `Prisma` |
| Cache | `Redis`, `Postgres` |
| LLM router | `Anthropic`, `OpenAI`, `LiteLLM` |
| Notification | `NHN Toast`, `Solapi` |
| Payments | `Toss`, `Stripe` |
| Observability | `Langfuse` |
| Frontend | `Next.js`, `Tailwind`, `Recharts` |
| Safety | `Keyword guard`, `Confidence check` |

## Layer tag (the small caption under the layer name)

A 3–7 word phrase explaining what the layer is for. Not a slogan, not a promise.

| Bad | Good |
|-----|------|
| Cutting-edge AI capabilities | 멀티 에이전트 — 각자 다른 책임 |
| Beautiful customer experience | 고객이 메시지를 보내는 진입점 |
| Powerful data infrastructure | 지식 저장소 — 셋이 다른 역할 |
| Enterprise-grade security | 위험 응대 차단 + 감사 로그 |

## Role tags (the small monospace label inside each card)

A 1–2 word category for the node's role. Lowercase, hyphen-separated when needed.

Common patterns:
- `primary`, `secondary`, `tertiary` — channel ordering
- `mvp`, `later`, `optional` — when a status badge isn't enough
- `transactional`, `conversational`, `scheduled` — for agents
- `vector`, `relational`, `memory` — for data stores
- `cost-critical`, `safety-critical`, `infra` — for cross-cutting concerns
- `read-only`, `write-heavy` — for data access patterns

## Roadmap track titles

The 3-track Now/Next/Later section. Use timeframes that match the project, not generic labels:

```
▶ Week 3-6 — MVP 빌드
▶ Week 7-12 — 베타 중 추가
▶ 6+ 개월 — 미룰 것
```

```
▶ Q1 2026 — Foundation
▶ Q2 2026 — Scale
▶ H2 2026 — Expansion
```

The third track is named "미룰 것" / "Defer" / "Later" intentionally — naming what you're NOT building is a sign of focus.

## Footer

Two lines, monospace 11px, gray. Format:

```
{project_slug} / system_architecture / v0.1
{one-line context — target customer, plan tier, version note}
```

The slug uses underscores like a filename. The version makes it obvious this is iterating, not a final declaration.

## Final smell test

Read the whole diagram out loud. If any sentence sounds like it could be on a vendor's homepage, rewrite it. The diagram should sound like the engineer who built it is walking a colleague through it at the whiteboard.
