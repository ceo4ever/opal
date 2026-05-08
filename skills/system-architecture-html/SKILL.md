---
name: system-architecture-html
description: |
  **시스템·인프라 레이어 구조 다이어그램을 단일 자기완결 HTML로 생성**.
  반드시 이 스킬을 사용해야 하는 상황: "시스템 아키텍처 HTML로 만들어줘", "아키텍처 다이어그램 HTML",
  "system architecture diagram HTML", `//html-sa`, `//system-architecture-html`.
  Triggers (한국어): "시스템 아키텍처 HTML", "아키텍처 다이어그램 HTML", "기술 스택 다이어그램 HTML", "시스템 아키텍처를 HTML로 만들어줘".
  Triggers (English): "architecture diagram HTML", "system architecture HTML", "make my architecture into HTML", "tech stack diagram", "infrastructure diagram HTML".
  Create production-grade system architecture diagrams as standalone HTML files. Use this skill whenever the user asks for a system architecture, technical architecture diagram, layered system diagram, software architecture, infrastructure diagram, service blueprint, or AI system architecture as HTML/web format.
  ER/시퀀스 다이어그램은 mermaid·erd-modeler 사용. 화면 목업은 html-mockup 사용.
  Output is ALWAYS a single self-contained .html file with no external dependencies (except optionally Google Fonts) — printable, shareable, and portfolio-ready.
  필수 입력: 시스템명, 레이어 구성. 보장 출력: `outputs/<system_name>_architecture.html` 단일 파일.
license: Proprietary
---

# System Architecture HTML

A skill for generating production-grade system architecture diagrams as standalone HTML files. The output is engineered to feel like "a senior engineer's whiteboard captured in code" — precise, layered, color-coded, with build-priority badges and a roadmap section.

## 0. 호출 환경

| 항목 | 값 |
|------|---|
| 호출 명령 | `//html-sa` 또는 `//system-architecture-html` |
| 별칭 | `html-sa` |
| 호출 가능 모드 | 비서(Assistant) / 태스크(Task) / PM / 오케스트레이터 — 모드 무관 |
| 특이 사항 | OPAL 프로젝트 여부 불문 (비-OPAL cwd에서도 동작 — 출력 경로만 환경 감지 결과에 따라 변동) |

## When to use

Trigger this skill when the user wants a **system/technical architecture rendered as HTML** — not as an SVG widget, not as a Markdown doc, not as a description in chat. Common triggers:

- "시스템 아키텍처를 HTML로 만들어줘"
- "Architecture diagram as HTML"
- "Turn this stack into a webpage"
- "Make my architecture into a single HTML I can share"
- A follow-up after Claude has already drawn an SVG architecture — the user wants it as a standalone shareable file

**Do not use this skill for:**
- Inline SVG diagrams (use the visualizer instead)
- Sequence/flow diagrams without architectural layers (use mermaid or visualizer)
- ER diagrams or data models (use mermaid `erDiagram`)
- Pure landing pages or marketing pages (use frontend-design skill)

## What the output looks like

A single `.html` file with:
1. **Header** — title with serif/italic flourish, eyebrow tag, project meta panel (target / BM / stack / timeline)
2. **Legend** — layer color codes + status badges (e.g. MVP / LATER / DONE)
3. **Architecture grid** — N stacked layers, each with:
   - Left rail: layer number, layer name, short tag describing layer purpose
   - Right area: 1–4 nodes as cards with title, status badge, description, tech chips
   - Dashed connector arrow between layers
4. **Roadmap section (optional but default-on)** — 3-track build plan (Now / Next / Later)
5. **Footer** — version, author, one-liner

The aesthetic is **dark IDE / engineering doc**: deep charcoal background, monospace meta text (JetBrains Mono), sans body (Inter Tight), one accent color (default coral `#FF5A1F`), thin 0.5px borders, hairline dashed dividers between layers. No gradients except subtle radial atmospherics. No drop shadows except on hover.

## Process

Follow these steps in order. Steps 1–2 are new OPAL context absorption steps.

### 1. 환경 감지 (Environment detection)

| 순서 | 조건 | 판정 |
|------|------|------|
| 1 | cwd에 `.opal/AGENT.md` 존재? | Yes → OPAL 프로젝트 |
| 2 | cwd 또는 상위에 `tasks/{NNN}-*/TASK.md` 패턴 존재? | Yes → 태스크 폴더 |
| 3 | STATE.md 또는 MEMORY.md 존재? | Yes → 세션 컨텍스트 폴백 |
| 4 | 위 모두 없음 | 비-OPAL / 컨텍스트 없음 |

### 2. 컨텍스트 흡수 (Context absorption)

감지 결과에 따라 아래 자원을 Read하여 아키텍처 설계 힌트를 추출한다. 환경별 행은 1차 흡수, 모든 환경 행은 추가 흡수(존재하는 만큼만).

#### 2-1. 환경별 흡수 (1차)

| 환경 | 흡수 자원 | 추출 내용 |
|------|---------|---------|
| OPAL 프로젝트 + 태스크 폴더 | `TASK.md`, `ANALYSIS.md` (있으면), `PLAN.md` (있으면), `docs/PROJECT.md`, `docs/ARCHITECTURE.md` | 시스템 명칭, 레이어 후보, 노드 후보, MVP/LATER 분류 힌트, 기술 스택 |
| OPAL 프로젝트 (태스크 폴더 없음) | `docs/PROJECT.md`, `docs/ARCHITECTURE.md`, `STATE.md`, `MEMORY.md` | 프로젝트 개요 + 컴포넌트 관계 |
| 비-OPAL | (없음) | 흡수 스킵 → 인터뷰(Step 3)에서 전체 수집 |

#### 2-2. 코드베이스 흡수 (모든 환경 — 존재하는 자원만)

| 자원 | 조건 | 추출 내용 |
|------|------|---------|
| `.opal/code-scan.json` (OPAL 프로젝트) | 파일 존재 + `node ~/.opal/tools/code-scan/run.sh scan` 호출 가능 | `code-scan domain` / `code-scan layer` / `code-scan exports` 메타 → 도메인·레이어·exports 후보 자동 추출 |
| 의존성 매니페스트 | `package.json` / `pyproject.toml` / `requirements.txt` / `go.mod` / `Cargo.toml` / `pom.xml` / `build.gradle` 중 하나 이상 존재 | 기술 스택 chips 자동 채움 (예: React 19, FastAPI 0.115, sqlite-vec) |
| 디렉토리 트리 | 모든 환경 (cwd 기준) | `find . -maxdepth 3 -type d -not -path '*/node_modules/*' -not -path '*/.git/*'` 또는 동등 → 레이어/컴포넌트 후보 보조 추론 |

> **추출 우선순위**: 2-1 환경별 흡수가 우선. 2-2는 보강용. 충돌 시 2-1을 신뢰하고 2-2는 chips·세부 노드 보강에만 사용.

#### 2-3. 추론 통지 규칙

추론 가능한 항목(시스템 명칭, 레이어 수, 메타 패널 4종, 기술 스택 chips, 노드 후보 등)은 인터뷰에서 스킵하고 1줄 통지로 대체:
`"{항목}은 컨텍스트에서 {추론값}으로 자동 결정. 변경하시려면 알려주세요."`

### 3. Interview (ONLY if information is missing)

If the user has already described their system in detail in the conversation, skip this step and use what's there. Otherwise, capture these before drafting:

- **System name and one-line purpose** (e.g. "미용실 AI 예약 매니저 — 24시간 카톡 응대 SaaS")
- **Target users / customer** (helps frame the meta panel)
- **Number of layers** — typically 4–7. Default to 6 if unsure.
- **What goes in each layer** — node names, brief descriptions, tech stack
- **Build priority per node** — what's MVP, what's later
- **Color theme preference** — default to coral, but ask if the brand has a different accent

If the user provides minimal info, propose a 6-layer default skeleton and confirm before drafting:
1. Channel / Entry — where users / data enters
2. Orchestration / Routing — request distribution and intent classification
3. Core Logic / Agents — the actual work
4. Data / Brain — knowledge stores, databases, vector indexes
5. External Services — third-party APIs and infrastructure
6. Operator / Monitoring — dashboards, observability, human-in-the-loop

### 4. Draft the HTML

Use `references/template.html` as the starting point. It's a complete working skeleton — copy it, then customize:

- Replace meta panel content (target, BM, stack, MVP timeline)
- Replace title and subtitle in `<h1>` and `.subtitle`
- For each layer: update `.layer-num`, `.layer-name`, `.layer-tag`, and the nodes inside `.boxes`
- Match the number of `.boxes-1` / `.boxes-2` / `.boxes-3` grids to actual node counts per layer
- Adjust color variables in `:root` if a different brand accent is needed
- Update or remove the roadmap section based on user needs

Read `references/design-system.md` BEFORE customizing — it defines the layer color palette, typography rules, and component patterns that make the diagram cohesive. Skipping it produces something that looks "almost right but generic."

Read `references/copywriting.md` for guidance on writing node descriptions and tech chips that read like an actual engineer wrote them, not like AI marketing copy. This is what separates a memorable diagram from a forgettable one.

### 5. Save and present

환경 감지(Step 1) 결과에 따라 저장 경로를 결정한다:

| 환경 | 저장 경로 |
|------|---------|
| OPAL 태스크 폴더 | `tasks/{NNN}-*/outputs/<system_name>_architecture.html` (cwd가 태스크 폴더면 `outputs/<system_name>_architecture.html`) |
| OPAL 프로젝트 (태스크 외) | `<cwd>/outputs/<system_name>_architecture.html` 또는 `docs/architecture/<system_name>.html` |
| 비-OPAL / 사용자 직접 지정 | 인터뷰로 묻거나 `<cwd>/<system_name>_architecture.html` 기본값 사용 |

- snake_case 파일명 규칙은 유지한다.
- Write 도구로 파일 저장 후, 응답 본문에 절대 경로 1줄 안내: "저장 완료: {절대경로} — 브라우저에서 바로 열 수 있습니다."
- In the response, briefly explain:
  - The layers and what each does (1 line each)
  - Which nodes are MVP vs Later / DONE
  - Suggested next steps (e.g. sequence diagram, dashboard mockup, landing page)

Keep the explanation tight — the diagram is the deliverable, not the prose.

## Quality bar

Before finalizing, the output should pass these checks:

- **Open in browser without errors** — no broken fonts, no missing assets
- **Print-friendly** — `@media print` rules adjust to white background, black text, removes shadows
- **Mobile responsive** — all 3-column grids collapse to 1 column under 900px
- **Self-contained** — only external dependency is Google Fonts (acceptable, ubiquitous)
- **Color-coded layers** — every node has a left-border accent matching its layer color
- **Status badges visible** — MVP / LATER / DONE pills are present on every node
- **No "AI slop" tells** — no purple gradient, no Inter as body font, no generic stock SaaS layout

## Common mistakes to avoid

- **Don't use Inter for body.** Use Inter Tight or Plus Jakarta Sans. Inter is the AI-default tell.
- **Don't add multiple gradients.** One radial atmospheric in body::before is enough.
- **Don't make every layer 3 columns.** Vary `.boxes-1` / `.boxes-2` / `.boxes-3` based on node count — a "router" layer often has 1 node, "agents" layer often has 3.
- **Don't write marketing copy in node descriptions.** "Cutting-edge AI-powered solution" is wrong. "RAG over매장정보 — 메뉴/가격/정책. pgvector + OpenAI Embed" is right.
- **Don't omit the build priority badges.** Even if the user didn't ask, classify each node — it makes the diagram immediately useful as a project plan.

## Reference files

- `references/template.html` — Complete working HTML skeleton. Copy this as the starting point.
- `references/design-system.md` — Color palette, typography rules, spacing system, component patterns.
- `references/copywriting.md` — How to write node descriptions, tech chips, and meta panel that read like an engineer wrote them.
- `references/examples.md` — Two complete example architectures (consumer SaaS, enterprise AI platform) to draw from.
