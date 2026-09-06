# PLAN: OPAL 아키텍처 다이어그램 재작성 — 지식 자산·환류 루프 1급 승격 + 사실 정합 복구

> 작성일: 2026-08-10 15:29 KST | 작업 유형: 개선 | 적용 스킬: opp / 모드: agentic
> 입력: TASK.md
> 출력: PLAN.md
> 대상: `docs/architecture-diagram/opal_framework_architecture.html` (v0.5 → v0.6, 단일 파일 덮어쓰기)

---

## 1. 현황 조사

### 참조 문서 (PLAN 작성 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | 현행 다이어그램 (v0.5, 696줄) | `docs/architecture-diagram/opal_framework_architecture.html` | 재작성 대상 — 구조·CSS 토큰·NODE_DATA 스키마·결함 위치 |
| D-2 | 설계 | ARCHITECTURE.md | `docs/ARCHITECTURE.md` | 계층 구성·2레이어·배포 모델·메모리 SSOT (수치 일부 stale) |
| D-3 | 기획 | PROJECT.md | `docs/PROJECT.md` | 프로젝트 원칙·컴포넌트 표·전문 에이전트 매핑·문서 레지스트리 |
| D-4 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | 언어/네이밍 규칙·@header 규칙·Citation 규칙·변경이력 의무 |
| D-5 | 소스 | 다이어그램 생성 스킬 (html-sa) | `skills/system-architecture-html/SKILL.md` | 생성 규약(자기완결·품질 바)과 재작성 산출물의 정합 판단 |
| D-6 | 설계 | 하네스 §9 OPAL Tools | `opal/core/references/opal-harness.md` | 등록 도구 목록·서브명령 수 근거 (도구 18종) |
| D-7 | 설계 | PM 행동 프로세스 §13·§14·§15 | `opal/core/references/opal-pm.md` | 코드맵/brain/MEMORY 참조 시점 + 역할 분담 근거 (R-4) |
| D-8 | 설계 | PM 디스패치 전 프로세스 | `opal/core/references/pm/dispatch-process.md` | 코드맵 무조건 조회·brain 3시점·동일 파일 단일 디스패치 규칙 |
| D-9 | 소스 | opp 오케스트레이터 SKILL | `opal/skills/opal-pilot-project/SKILL.md` | CLOSE 훅 op-brain-ingest 적재 경로 (R-3 환류 출발점) |
| D-10 | 소스 | memory-tool README | `opal/tools/memory-tool/README.md` | 메모리 라이프사이클·promote 졸업 워크플로우 (R-5) |
| D-11 | 설계 | 관측 규약 | `opal/core/references/harness/observability.md` | 히스토리 append 호출 형식 (환류 ① 근거) |
| D-12 | 소스 | 워커 에이전트 frontmatter 15종 | `opal/agents/*/AGENT.md` | 에이전트 수·분류·model 레벨 실측 SSOT |
| D-13 | 소스 | cmux-tool README | `opal/tools/cmux-tool/README.md` | 렌더 검증 1순위 도구의 서브명령·모드·한계 |
| D-14 | 소스 | playwright-tool 본체 | `opal/tools/playwright-tool/main.py` | 폴백 도구 실제 능력 확인 (콘솔/스크린샷 미지원 판정) |
| D-15 | 설계 | 인용 규칙 | `opal/core/references/harness/citation-rules.md` | PLAN 단계 인용 의무 수준(§4)·[MUST] 포맷(§2.4) |
| D-16 | 설계 | 헌법 | `opal/core/PRINCIPLES.md` | 사용자 주권 — PLAN 단계 코드 미변경 근거 |

### 필수 제약 ([MUST] 원문 인용)

- [MUST] `opal/core/PRINCIPLES.md` §Core Stance: "User sovereignty: never create or modify code until the owner approves." (`opal/core/PRINCIPLES.md:13`) → **이 PLAN 단계에서는 대상 HTML을 일절 수정하지 않는다.**
- [MUST] `opal/core/references/harness/citation-rules.md` §0: "상상·추정·기억 기반 기재 금지 — 모든 분석·설계 결정은 문서 근거(경로/URL + 섹션/줄번호)를 인용해야 한다."
- [MUST] `docs/CONVENTIONS.md` §Citation Rules: "`[MUST]` 토큰이 붙은 항목은 인용 누락 시 산출물 부적합 처리." (`docs/CONVENTIONS.md:182`)
- [MUST] `docs/CONVENTIONS.md` §언어 규칙: "문서 본문 = 한국어 (기술 용어는 영어 병기) / 코드·변수·필드명 = English" (`docs/CONVENTIONS.md:9-11`) → 다이어그램 본문 카피는 한국어, `data-id`·NODE_DATA 키·CSS 토큰은 영어 kebab/camel 유지.
- [MUST] `docs/CONVENTIONS.md` §네이밍 규칙: "kebab-case 사용" (`docs/CONVENTIONS.md:18`) → 신규 CSS 클래스·`data-id`는 kebab-case (`loop-band`, `tool-pipeline`, `op-scenario-gate`).
- [MUST] `docs/CONVENTIONS.md` §변경이력 작성 의무: "일시는 `YYYY-MM-DD HH:mm` (KST), 버전은 semver, 변경내용은 태스크 번호를 괄호로 포함" (`docs/CONVENTIONS.md:201`) → HTML은 변경이력 표를 갖지 않으므로 **파일 상단 HTML 주석 1행**으로 대체 기재한다(§2.6 S8).
- [MUST] `opal/core/references/pm/dispatch-process.md:157`: "동일 파일을 2개 이상 Step이 변경하면 분할하지 않고 같은 디스패치에 묶어 순차 편집한다(동시 편집 시 후행 저장이 선행 편집을 덮어쓰는 충돌 방지)." → §3 Phase 1(S1~S9)은 **단일 디스패치 순차 실행**.
- [MUST] TASK.md §제약 조건: "인라인 CSS/JS 유지. 외부 스크립트·CDN 라이브러리 추가 금지" / "파일명·경로를 바꾸지 않는다 · 별도 백업 파일을 만들지 않는다" (`tasks/086-260810-opp-아키텍처-다이어그램-재작성/TASK.md:81-82`)
- [MUST] TASK.md §제약 조건 [실측 우선]: "컴포넌트 수치·이름은 `opal/agents/`·`opal/skills/`·`opal/tools/` 실측을 SSOT로 한다" (`TASK.md:83`)

### 관련 파일

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| `docs/architecture-diagram/opal_framework_architecture.html` | 재작성 대상 (유일 변경 파일) | **O** | `:1-696` 전체 |
| ↳ `:11-17` `:root` 토큰 | 계층 색 9종 + 라이트/모달 팔레트 | O | `--c-l1`~`--c-l9` (`:14-15`) |
| ↳ `:50-59` `.band-lN` | 구조도 밴드 배경 7종 + `.band-direct` | O | `:52-59` |
| ↳ `:76-81` `.cross` | 지식·도구 횡단 세로 스트립 1개 | O (3분할) | `:77-81`, `:325` |
| ↳ `:123-131` `.layer-lN` | 상세 뷰 계층별 노드 색 규칙 9줄 | O (+L10) | `:123-131` |
| ↳ `:177-194` `@media(max-width:920px)` | 반응형 규칙 | O | `:184` 밴드 화살표 숨김 패턴 |
| ↳ `:209-334` 구조도 뷰 | 8밴드 + 하네스 박스 + 횡단 스트립 + legend | O | `:222-333` |
| ↳ `:339-487` 상세 뷰 | 9계층 + 로드맵 3트랙 + 푸터 | O | `:371-467`, `:469-480`, `:482-485` |
| ↳ `:498-655` `NODE_DATA` | 모달 데이터 37키 | O | `:498-655` |
| ↳ `:657-693` IIFE | 탭 전환·모달 오픈·키보드 | X (보존) | `:672-683` |
| `docs/ARCHITECTURE.md` | 계층·컴포넌트 근거 | X (범위 외) | `TASK.md:84` |
| `docs/PROJECT.md` | 컴포넌트·문서 레지스트리 | X (범위 외 — CLOSE 이관 후보) | `docs/PROJECT.md:164-172` |
| `skills/system-architecture-html/SKILL.md` | 생성 규약 | X (범위 외) | `TASK.md:65` |

### 현재 상태

**구조**: 단일 HTML 696줄 자기완결. 외부 의존은 Google Fonts 링크 2개(`:7-9`)뿐이며 이는 html-sa 품질 바에서 명시적으로 허용된다 — "Self-contained — only external dependency is Google Fonts (acceptable, ubiquitous)" (`skills/system-architecture-html/SKILL.md:159`). 인라인 `<style>` 1블록(`:10-195`) + 인라인 `<script>` 1블록(`:497-694`).

**2뷰 + 모달 인터랙션**: 탭 2개(`:202-203`)가 `.view.active` 토글(`:29-30`)로 뷰를 전환하고, `[data-id]` 요소 전체에 click/keydown 리스너를 부착해 `NODE_DATA[id]`를 모달에 렌더한다(`:686-689`). **`openModal`은 키 부재 시 `if(!d) return;`으로 조용히 종료한다(`:674`)** — 즉 `data-id`↔`NODE_DATA` 키 누락은 콘솔 에러로 드러나지 않고 "클릭해도 아무 일 없음"으로만 나타난다. 이것이 R-6 AC를 브라우저 콘솔만으로 검증할 수 없는 구조적 이유이며, 결정론적 키 대조 게이트가 필수인 근거다(§2.5).

**현행 정합 상태(실측)**: `data-id` 37개 ↔ `NODE_DATA` 키 37개로 현재는 양방향 누락 0건이다(2026-08-10 실측). 재작성이 이 불변식을 깨는 것이 최대 리스크다(H-2).

**계층 번호 3중 불일치(신규 발견)**: 상세 뷰는 L4=오케스트레이터·L5=하네스(`:400`, `:418`)인데, 구조도는 L4=직접 실행 스킬·L5=오케스트레이터(`:254`, `:273`)이고, 모달 데이터는 `opd`를 "L5 · 오케스트레이터"(`:543`)·`operator`를 "L4 · 직접 실행"(`:579`)으로 표기한다. 모달은 두 뷰가 공유하는 단일 데이터이므로 **계층 번호는 뷰 독립적인 정본(canonical) 1종이어야 한다**. 현행은 어느 뷰를 기준으로 봐도 최소 1개 노드의 층 표기가 틀린다.

**지식 자산 표현**: 구조도에서는 우측 세로 스트립 1개(`:325`), 상세에서는 L8 도구 계층의 4번째 노드 1개(`:454`)로 축소되어 있고, L8은 L9(배포) 직전 — 즉 "흐름의 끝"이다. 귀환선·환류 표현은 두 뷰 모두 0개다(하강 커넥터 `↓`만 존재, `:132-134`).

### 실측 대조표 (2026-08-10 재검증 — PM 대조표와 전건 일치)

| 항목 | 다이어그램(v0.5) | 실측값 | 실측 근거 |
|------|------------------|--------|----------|
| Pilot | 9 (`:401`, `:476`) | **10** (`oppl` 누락) | `ls -d opal/skills/opal-pilot-*` → 10 |
| 워커 에이전트 | 13 (`:439`) | **15** | `ls opal/agents` → 15 (D-12) |
| 에이전트 분류 | 전문6/범용4/체커2/변환1 | 전문6 / 범용5 / 체커·심판3 / 변환1 | D-12 |
| 단계 스킬 (op-*) | 20 = 7+4+5+3+1 (`:429-434`) | **21** (`op-scenario-gate` 누락) | `ls -d opal/skills/op-*` → 21 |
| 도구 | 10종 표기 (`:451-453`) | **18종** | `ls opal/tools` → 18 디렉토리 + `check-env.js`·`requirements.txt` |
| operator 직접실행 스킬 | 7종 (`:581-582`) | **11종** | `ls -d opal/skills/opal-* \| grep -v pilot` → 11 |
| standalone 독립 스킬 | 8종 (`:585`) | **8종** (일치) | `ls skills/` → 8 |
| 메모리 SSOT | `.opal/MEMORY` (`:454`) | `.opal/MEMORY.json` + `memory/*.md` | `docs/ARCHITECTURE.md:94`, `docs/PROJECT.md:170` |
| wtm 폴백 | 3단 WebFetch→cmux→playwright (`:444`, `:627`) | **2단** cmux → playwright | `opal/agents/opal-wtm-agent/AGENT.md` description, D-13 §폴백 트리거 |
| code-scan | "전 파일 @header 실시간 스캔" (`:452`) | **15서브명령** + `.opal/code-map/` 작성층 + `_shards/` 샤딩 + `headerSource` 단일 키 | `opal-harness.md:254`, `docs/CONVENTIONS.md:174-175` |
| 버전 | v0.5 (`:343`, `:483`) | v0.6 | R-7 |
| 계층 수 표기 | "9-레이어"(`:203`)·"9개 계층"(`:345`)·"9-layer"(`:484`) | 10 (지식 계층 신설 후) | §2.1 |

### 추가 발견 — v0.5 사실 불일치 2건 증분 (M-10·M-11)

TASK.md §배경 분석 B의 M-1~M-9 외에, PLAN 조사 중 아래 2건을 추가 검출했다. R-1의 AC("불일치 0건")를 만족하려면 함께 교정해야 한다.

| # | 항목 | 다이어그램 표기 | 실측값 | 근거 |
|---|------|---------------|--------|------|
| **M-10** | operator 직접실행 스킬 인벤토리 | opi·opbr·onb·next·osc·oac·osm 7종 (`:581-582`) | **11종** — 위 7종 + `opal-help`·`opal-improve`(opim)·`opal-action-status`(opas)·`opal-workspace-sync` | `ls -d opal/skills/opal-*` 실측, `docs/PROJECT.md:111`(opas)·`:133`(opim) |
| **M-11** | 로드맵 "진행" 트랙 | "code-scan @header 커버리지 확충" 등 (`:477`) | 077(작성층)·082(샤딩)·083(샤드 정책)·085(릴리스 검증경로) 완료 → 현행 트랙으로 승격 필요 | `docs/ARCHITECTURE.md:402-403`, `docs/PROJECT.md:179-180` |

### 영향 범위

| 영향 대상 | 영향 | 판정 |
|----------|------|------|
| 대상 HTML 자체 | 전면 재편(CSS 토큰·2뷰 DOM·NODE_DATA·로드맵·푸터) | 이 태스크 범위 |
| IIFE 스크립트 로직 | 무변경 — 신규 노드는 `[data-id]` 선택자에 자동 편입(`:686`) | 보존(R-6) |
| 외부 문서 참조 | 이 HTML의 계층 번호를 인용하는 **활성 문서 0건** (grep 결과: 과거 태스크 기록 3건만) | 리스크 낮음(H-1) |
| `~/.opal/` 배포 | 프로젝트 문서이므로 install 재배포 불요 | `TASK.md:85` |
| `docs/ARCHITECTURE.md`·`docs/PROJECT.md` | stale 수치 잔존(§5.3) — 갱신은 범위 외, CLOSE 이관 | `TASK.md:84` |

---

## 2. 구현 계획

### 파일 변경 계획

#### 신규 생성
| # | 파일 경로 | 역할 | 근거 |
|---|----------|------|------|
| — | (없음) | 단일 파일 덮어쓰기 원칙 — 백업 파일 생성 금지 | `TASK.md:82` |

#### 수정
| # | 파일 경로 | 변경 내용 | 근거 |
|---|----------|----------|------|
| 1 | `docs/architecture-diagram/opal_framework_architecture.html` | 10계층 재편 + 지식 3자산 독립 노드 + 환류 루프 시각 요소 + 도구 계층 18종 재편 + 사실 11건 교정(M-1~M-11) + NODE_DATA 46키 재편 + v0.6·로드맵 갱신 | R-1~R-7 전건 |

#### 삭제
| # | 파일 경로 | 사유 |
|---|----------|------|
| — | (없음) | — |

### 구현 순서

| 순서 | 작업 | 대상 구간 | 예상 난이도 |
|------|------|----------|-----------|
| 1 | 실측 스냅샷 재확인 · 치환 대조표 확정 | (읽기 전용) | 낮음 |
| 2 | `:root` 토큰 + `.layer-lN`/`.band-lN` + 환류·지식 CSS | `:11-195` | 중간 |
| 3 | 구조도(map) 뷰 재편 | `:209-334` | 높음 |
| 4 | 상세(detail) 계층 재배치 + L3 지식 계층 신설 + legend | `:339-370`, `:371-467` | 높음 |
| 5 | 상세 도구 계층(L9) 재편 + Pilot·단계·워커 수치 교정 | `:400-456` | 중간 |
| 6 | 환류 밴드 + 상향 커넥터 + 도착 앵커 | `:467` 직후, `:105-134` | 중간 |
| 7 | NODE_DATA 재편 (신규 11 / 삭제 2 / layer 문자열 정합) | `:498-655` | 높음 |
| 8 | 버전 v0.6 · 10-layer 문자열 · 로드맵 3트랙 · 상단 이력 주석 | `:1`, `:203`, `:343`, `:345`, `:469-485` | 낮음 |
| 9 | 결정론 검증 (키 대조·잔존 문자열·수치 grep) | 전체 | 낮음 |
| 10 | 렌더 실측 (2뷰·콘솔·모달) | 전체 | 중간 |

> 의존 방향: CSS 토큰(2) → 뷰 DOM(3~6) → 모달 데이터(7) → 문자열·이력(8) → 검증(9~10). 토큰이 뷰보다 먼저인 이유는 뷰 마크업이 `.layer-lN`/`.band-lN` 클래스를 참조하기 때문이다.

---

### 핵심 설계

#### 2.1 레이어 재편 — 지식 계층 독립 분리와 정본 번호 체계

**문제 정의**: (a) 지식 자산이 L8(배포 직전)에 있어 "흐름의 끝"으로 오독된다(`TASK.md:26` F-4). (b) 상세 뷰·구조도·모달의 계층 번호가 3중으로 어긋난다(§1 현재 상태).

**설계 결정 1 — 지식 계층을 L3(라우팅 앞)에 신설한다.**

근거: 지식 자산은 "흐름의 끝에서 만들어지는 산출물"이 아니라 **흐름이 시작될 때 가장 먼저 읽히는 상태값**이다. 실제 참조 순서가 이를 증명한다 —
- MEMORY: 부트스트랩 Phase B(PM 승격) 시점에 `memory-tool show --brief` 브리핑 (→ D-7 §15, `opal-pm.md:297`; `docs/ARCHITECTURE.md:61` "PROJECT/MEMORY 브리핑")
- brain: 작업·분석·설계 착수 **전** (→ D-7 §14, `opal-pm.md:262`) — 라우팅 이후 전 계층에 걸쳐 재참조
- 코드맵: 코드 변경·탐색 작업의 디스패치 **전 무조건** (→ D-8, `dispatch-process.md:113`)

즉 L1 진입 → L2 거버넌스 → **L3 지식(축적된 상태를 먼저 읽는다)** → L4 라우팅 → … 순서는 실제 시간 순서와 일치한다. 하강 흐름의 위쪽에 배치함으로써 F-4(역순 배치)가 구조적으로 해소되고, 동시에 계층 라벨에 "횡단 — 전 계층이 재참조" 태그를 달아 단일 지점 오독도 차단한다.

**설계 결정 2 — 하네스를 오케스트레이터 앞(L5)으로 옮겨 두 뷰의 포함 관계와 번호 순서를 일치시킨다.**

현행은 상세 뷰에서 L4 Pilot → L5 하네스인데, 구조도에서는 하네스 점선 박스가 오케스트레이터~워커를 **감싼다**(`:264-309`). 감싸는 쪽의 번호가 감싸이는 쪽보다 커서 두 표현이 모순이었다. 하네스를 L5로 올리면 `L5 하네스 ⊃ {L6 오케스트레이터, L7 단계 스킬, L8 워커}`가 되어 구조도의 박스 표현과 상세 뷰의 번호 순서가 정합한다. 배경 분석 C의 "하네스 박스가 오케스트레이터~워커를 감싸고 직접 실행 스킬은 우회하는 표현 보존"(`TASK.md:48`)을 번호 체계까지 확장한 것이다.

**정본 10계층 (두 뷰 + NODE_DATA 공통 SSOT)**

| # | 계층명 | 구성 노드 | 색 토큰(권고값) | 구조도 표현 | 상세 표현 |
|---|--------|----------|----------------|------------|----------|
| L1 | 진입 · 부트스트랩 | Claude Code / Cursor / Gemini·Antigravity / Codex (4) | `--c-l1:#7CA9FF` (유지) | `.band-l1` | `.layer-l1` `boxes-2` |
| L2 | 거버넌스 · 정체성 | PRINCIPLES / identity / 역할 체계 (3) | `--c-l2:#9C8CFF` (유지) | `.band-l2` | `.layer-l2` `boxes-3` |
| **L3** | **지식 자산 (횡단 기반)** ★신규 | **코드맵 / brain / MEMORY (3)** | `--c-l3:#5FCFE0` (구 `--c-l8` 값 승계) | 우측 세로 3분할 컬럼 `.cross-col` | `.layer-l3` `boxes-3` |
| L4 | 라우팅 | // 커맨드 / 자연어 / skill-registry (3) | `--c-l4:#FF8FA3` (구 l3) | `.band-l4` | `.layer-l4` `boxes-3` |
| L5 | 하네스 (관할 경계) | 3-way 모드 / Guards / Gates·State·Observ. (3) | `--c-l5:#FFB454` (유지) | 점선 박스 헤더 `LAYER 05` | `.layer-l5` `boxes-3` |
| L6 | 오케스트레이터 / Pilot · 직접 실행 | Pilot 10 (관할) + operator·standalone·community 3 (우회) | `--c-l6:#5BD3B0` (구 l4) | 박스 내 `.band-l6` + 박스 밖 `.band-direct` (동일 번호 2밴드, 관할/우회 수식어로 구분) | `.layer-l6` `boxes-3` (13노드) |
| L7 | 단계 스킬 (op-*) | 6그룹 = 21스킬 | `--c-l7:#F7C66B` (구 l6) | 박스 내 `.band-l7` | `.layer-l7` `boxes-3` |
| L8 | 워커 에이전트 | 4그룹 = 15에이전트 | `--c-l8:#A8D86F` (구 l7) | 박스 내 `.band-l8` | `.layer-l8` `boxes-2` |
| L9 | 도구 · 집행 수단 | 4그룹 = 18도구 | `--c-l9:#CE92DB` (유지) | `.band-l9` | `.layer-l9` `boxes-2` |
| L10 | 배포 · 어댑터 · Console | 2-Layer / 어댑터 / 채널 / Console (4) | `--c-l10:#C9CDD6` ★신규 토큰 | `.band-l10` | `.layer-l10` `boxes-2` |

**CSS 영향 범위 (계층 수 9→10)**

| 대상 | 현행 | 변경 |
|------|------|------|
| `:root` 계층 토큰 | `--c-l1`~`--c-l9` (`:14-15`) | `--c-l1`~`--c-l10` — 값은 위 표대로 재배정(슬롯 이동 방식, 신규 hex는 L10 1건) |
| `.layer-lN` 규칙 | 9줄 (`:123-131`) | 10줄 (`.layer-l10` 1줄 추가) |
| 상세 legend | 9항목 (`:356-364`) | 10항목 — L3 항목을 "지식 자산 (횡단)"으로 신설, 나머지 라벨 시프트 |
| 구조도 `.band-lN` | l1~l7 + direct (`:52-59`) | l1~l4·l6~l10 + direct (하네스는 밴드 없이 박스) — 파스텔 값 재배정, 지식(L3) 신규 시안 파스텔 `#D2F4FA`/inset `#A5E4F0` |
| 인라인 `var(--c-lN)` 직접 사용 | `:373`(`--c-l1`), `:454`(`--c-l8`) | `:373` 유지(L1 불변), `:454`는 노드 자체가 L3로 이동하므로 `var(--c-l3)`로 재지정 |
| 계층 수 문자열 | `:203` "상세 9-레이어" / `:345` "9개 계층" / `:484` "9-layer 구성도" | 각각 10으로 교정 |

> 색 배정 규칙 [설계 제약]: **지식=시안(cyan) / 환류=바이올렛(violet)** 시그니처를 두 뷰에서 동일 계열로 고정하고, 인접 계층 간 유사 색을 금지한다. 구조도의 기존 보라(`--cross-know` 계열 `#E7DCFB`/`#C9B6F2`, `:81`)는 **환류 전용**으로 의미를 재배정한다 — 보라가 "지식"과 "환류" 두 의미를 겸하지 않게 하여 legend 판독을 1:1로 만든다.

#### 2.2 환류 루프 표현 방식 (R-3 — 최우선)

**후보 비교**

| 안 | 방식 | 장점 | 단점 | 판정 |
|----|------|------|------|------|
| A | 인라인 SVG 오버레이 곡선 | 자유 곡선·정밀 | 노드 위치를 JS로 측정해 좌표를 계산해야 하고(resize 리스너 필요) 스크롤·반응형에서 어긋난다. **JS 추가 = 콘솔 에러 리스크 증가 → R-6 AC와 상충** | 기각 |
| B | CSS 의사요소 절대배치 레일 | 무JS | `.wrap`(max-width:1280 + padding:32) 밖으로 나가면 클리핑, 920px 이하 처리 부담 | 부분 채택(상세 뷰 미적용) |
| C | 전용 환류 밴드(레이블+스텝 칩) | 출발·경로·도착을 **텍스트로 명시** → AC 판정이 결정론적, 반응형 안전 | 밴드만으로는 "선/화살표" 인상이 약함 | 채택(기반) |
| **D** | **C + flex 레일 컬럼 하이브리드** | 무JS·무절대배치. 구조도는 좌측 flex 컬럼이 실제 귀환 레일이 되고, 상세는 밴드 + 상향 커넥터가 방향을 표현. 반응형은 기존 `flex-direction:column` 전환(`:179`)에 자연 편승 | 곡선이 아닌 직선 레일 | **채택** |

**선택 근거**: R-6 AC가 "콘솔 에러 0건"을 요구하므로 신규 JS를 한 줄도 추가하지 않는 안이 지배적으로 유리하다(A 기각의 결정적 이유). 또한 R-3 AC의 판정 조건은 "귀환 시각 요소 존재 + 출발(CLOSE)·도착(부트스트랩/디스패치 전 조회) 레이블 식별"이므로, 곡선의 미려함보다 **레이블의 명시성**이 AC 충족에 직결된다.

**구조도(map) 구현 — 좌측 환류 레일 컬럼**

`.map-body`는 이미 `display:flex`(`:44`)이므로 좌측에 flex 아이템 1개를 추가하면 절대배치 없이 전체 높이 레일이 만들어진다.

```
.map-body → [.loop-col(신규)] + [.map-col(기존)] + [.cross-col(기존 .cross → 3분할)]

.loop-col{width:34px;flex-shrink:0;position:relative;display:flex;align-items:center;justify-content:center;
  border:1.6px dashed var(--loop-m);border-right:none;border-radius:12px 0 0 12px;
  background:rgba(231,220,251,.32)}
.loop-col span{writing-mode:vertical-rl;transform:rotate(180deg);   /* 아래→위 = 귀환 방향 */
  font-size:11px;font-weight:700;letter-spacing:.06em;color:var(--loop-m)}
.loop-col::before{content:"▲";position:absolute;top:-9px;left:50%;transform:translateX(-50%);
  font-size:10px;color:var(--loop-m)}                                /* 상향 화살촉(도착) */
.loop-col::after{content:"CLOSE";position:absolute;bottom:7px;left:50%;transform:translateX(-50%) rotate(-90deg);
  font-family:'JetBrains Mono',monospace;font-size:8.5px;color:var(--loop-m)}  /* 출발 레이블 */
```

- 레일 라벨(클릭 가능, `data-id="loop"`): `환류 — CLOSE → brain·MEMORY 적재 → 다음 세션이 먼저 읽음`
- 도착 앵커: 레일 상단 화살촉이 L3 지식 밴드 높이에 닿도록 `.map-col` 상단 정렬 유지. 추가로 L3 라벨 옆에 `◀ 환류 도착` 캡션을 배치해 텍스트로도 도착점을 고정한다.
- 반응형(≤920px): 기존 `.map-body{flex-direction:column}`(`:179`)에 편승 — `.loop-col{width:auto;border-right:1.6px dashed;border-bottom:none;border-radius:12px 12px 0 0}` + `.loop-col span{writing-mode:horizontal-tb;transform:none}` + `::before/::after` 재배치. 기존 `.cross span,.cross small{writing-mode:horizontal-tb}`(`:183`) 패턴과 동형이라 규칙 추가 위치가 자명하다.

**상세(detail) 구현 — 환류 밴드 + 상향 커넥터**

`.arch` 종료 직후(`:467` 다음) `.loop-band` 섹션 1개를 삽입한다. 그리드를 `.layer`와 동일한 `150px 1fr`(`:106`)로 맞춰 계층 레일과 좌측 정렬을 일치시킨다.

```
.view-detail .connector-up{...}                    /* ↑ + 점선 — 하강 커넥터(:132-134)의 방향 반전판 */
.view-detail .connector-up::before{content:"↑";color:var(--loop)}
.view-detail .loop-band{display:grid;grid-template-columns:150px 1fr;gap:24px;
  border:1.6px dashed var(--loop);border-radius:10px;padding:20px 22px;margin-top:8px;
  background:rgba(183,156,255,.055)}
.view-detail .loop-steps{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
.view-detail .loop-step{background:var(--bg-elev);border:1px solid var(--line);border-left:2px solid var(--loop);
  border-radius:8px;padding:14px 16px}
```

- 좌측 레일: `▲ 환류 (FEEDBACK)` / `L10 → L3 귀환` / 태그 "하강 흐름과 반대 방향 — Loops의 증명"
- 우측 3스텝 카드(`data-id="loop"`로 밴드 전체 클릭 가능):
  1. **적재 (CLOSE 훅)** — PM Gate 통과 + DONE.md 생성 직후 `op-brain-ingest` 워커 디스패치 → 검증된 산출물만 brain 누적, brain 부재 시 no-op (→ D-9, `opal/skills/opal-pilot-project/SKILL.md:127-135`). 히스토리는 `memory-tool append --kind history` (→ D-11, `harness/observability.md:28`)
  2. **승격 (졸업)** — `memory-tool promote`로 메모리 → `docs`/`brain` 영구 거처 이관. "메모리는 임시 보관소"(→ D-10, `opal/tools/memory-tool/README.md:6`, `:120`)
  3. **다음 세션이 먼저 읽음** — 부트스트랩 메모리 브리핑(→ D-7 §15) → 디스패치 전 코드맵 무조건 조회(→ D-8 `:113`) → 설계 착수 전 brain search(→ D-7 §14)
- 배치: `.arch` 마지막 계층(L10) 뒤에 `.connector-up` → `.loop-band` → `.connector-up` 순으로 두어 **아래에서 위로 되돌아가는 방향**을 화살표로 명시하고, L3 지식 계층의 `.layer-tag`에 `◀ 환류 도착 — 다음 세션이 이 계층부터 읽는다` 문구를 넣어 도착점을 텍스트로 고정한다.
- 반응형(≤920px): `.loop-band{grid-template-columns:1fr}` + `.loop-steps{grid-template-columns:1fr}` — 기존 `.layer{grid-template-columns:1fr}`·`.boxes-3{grid-template-columns:1fr}`(`:190-191`) 규칙에 나란히 추가.

> 신규 토큰: `--loop:#B79CFF`(다크/상세) · `--loop-m:#7C5CC4`(라이트/구조도). 두 뷰가 동일 계열 보라를 쓰므로 뷰를 옮겨도 "환류"라는 의미가 유지된다.

#### 2.3 지식 자산 3노드 명세 (R-2 · R-4 · R-5)

R-2 AC는 각 노드에 (a)역할 (b)SSOT 경로 (c)관리 도구를, R-4 AC는 참조 시점 최소 1개를, R-5 AC는 MEMORY의 승격 관계를 요구한다. 아래를 **노드 본문 + 모달 detail 양쪽에** 기재한다.

| 자산 | (a) 역할 | (b) SSOT 경로 | (c) 관리 도구 | 참조 시점 (R-4) | 근거 |
|------|---------|--------------|--------------|----------------|------|
| **코드맵 (Code Map)** | **WHAT** — 코드 구조·exports·depends의 **전수·실시간** 사실 | 파일 `@header`(인라인) 또는 `.opal/code-map/` 매니페스트. 기록 소스는 `.opal/code-scan.json` 전역 `headerSource`(`inline`\|`manifest`) **단일 키**가 결정하며 미설정 시 전 명령 차단 | `code-scan` **15서브명령** — 조회 8 + 작성층(discover/scaffold/target/validate/feature) + 샤드층(split/init) | **코드 변경·코드 탐색 작업의 디스패치 전 무조건 호출** | 역할·신선도: D-7 `opal-pm.md:243-246` / 소스 단일키: `docs/CONVENTIONS.md:174-175` / 15서브명령: D-6 `opal-harness.md:254` / 참조 시점: D-8 `dispatch-process.md:113` |
| **brain (Project Brain)** | **WHY·HOW** — 설계 배경·과거 결정의 **선별·stale 가능** 스냅샷 | `.opal/brain/` (index + 페이지). `//opbr init`으로 생성되는 **프로젝트 자산** | `brain-tool` **8서브명령** (init/add-page/index/log/search/sync-header/lint/validate) | **작업·분석·설계 착수 전 / 워커 디스패치 프롬프트 작성 시 / 사용자 질의 — 3시점.** search 후보 목록 → 상위 선별 → **선택 페이지만** 주입(전량 로드 금지) | 역할: D-7 `opal-pm.md:243-246` / 자산 위치: `docs/PROJECT.md:83` / 8서브명령: D-6 `opal-harness.md:252` / 3시점·후보 흐름: D-8 `dispatch-process.md:124-141`, D-7 `opal-pm.md:262` |
| **MEMORY (프로젝트 메모리)** | **운영 기억** — 히스토리·피드백·선호·결정. **임시 보관소**이며 성숙 지식은 졸업한다 | `.opal/MEMORY.json`(인덱스 JSON SSOT) + `memory/*.md`(본문). 변경은 `memory-tool`만 | `memory-tool` **9서브명령** (init/append/update/promote/prune/show/review/delete/task-number) | **부트스트랩 Phase B(PM 승격) 직후 `memory-tool show --brief` 브리핑** | SSOT: `docs/ARCHITECTURE.md:94`, `docs/PROJECT.md:170` / 9서브명령: D-6 `opal-harness.md:258`, D-10 `README.md:4` / 브리핑: D-7 `opal-pm.md:297`, `docs/ARCHITECTURE.md:61` |

**MEMORY 라이프사이클 (R-5)** — MEMORY 노드 본문에 관계 화살표 텍스트로, 모달 detail에 4항목으로 기재:
- `promote` → **`docs`/`brain` 영구 거처 졸업 (★1순위)** — "메모리는 임시 보관소. 성숙한 지식은 `promote`로 영구 거처(`docs`/`brain`)로 졸업한다" (→ D-10 `opal/tools/memory-tool/README.md:6`, `:120`)
- 히스토리 **FIFO 5** + 요약 길이캡(`summary` ≤80자) (→ D-6 `opal-harness.md:258`, D-10 `README.md:43`)
- `status` 라이프사이클: `active/promoted/superseded/dead/candidate` → `delete`로 dead·superseded 무손실 정리 (→ D-10 `README.md:43`, `:94`)
- 매 변경 명령 응답에 `review` 블록 자동 첨부 → 검토가 ambient하게 강제 (→ `opal/core/references/harness/memory-learning.md:72`)

> **[MUST] 도구 ≠ 자산 분리 원칙** (F-3 해소): L9는 **집행 수단(CLI)**, L3는 **축적 상태(파일)** 이다. `code-scan`/`brain-tool`/`memory-tool` 3도구는 L9 "지식 집행 도구" 그룹에 두고, 코드맵/brain/MEMORY 3자산은 L3에 둔다. 두 계층의 3:3 대응을 노드 카피에 명시하여("이 자산을 집행하는 도구는 L9 지식 집행 도구") 범주 혼합이 재발하지 않게 한다.

#### 2.4 NODE_DATA 스키마 정합 (data-id ↔ 키 매핑표)

**스키마 불변 [MUST]**: `{t, badge, layer, tag, desc, detail[], chips[]}`를 유지한다(`docs/architecture-diagram/opal_framework_architecture.html:498-655`). `badge`는 `core|stable|later` 3택만 허용된다 — `badgeClass`/`badgeText` 룩업이 이 3키만 갖기 때문이다(`:670-671`). 새 값 도입 시 `undefined` 클래스가 렌더된다.

**항목 포맷 불변 [MUST]**: 각 항목을 `2칸 들여쓰기 + {키}:{` 형태로 유지한다. §2.5 결정론 게이트의 키 추출 정규식(`^  "?[A-Za-z0-9_-]+"?:\{`)이 이 포맷에 의존한다(하이픈 포함 키는 현행처럼 따옴표로 감싼다 — `"op-dev"`, `:592`).

| data-id | 상태 | `layer` 문자열 (정본) | 노출 뷰 | 비고 |
|---------|------|---------------------|--------|------|
| claude / cursor / gemini / codex | 유지 | `L1 · 진입·부트스트랩` | both | 변경 없음 |
| principles / identity / roles | 유지 | `L2 · 거버넌스·정체성` | both | 변경 없음 |
| **codemap** | ★신규 | `L3 · 지식 자산 (횡단)` | both | §2.3 코드맵 |
| **brain** | ★신규 | `L3 · 지식 자산 (횡단)` | both | §2.3 brain |
| **memory** | ★신규 | `L3 · 지식 자산 (횡단)` | both | §2.3 MEMORY + 라이프사이클 |
| ~~knowledge~~ | **삭제** | — | — | 3자산으로 분해(F-1) — 구조도 `.cross`(`:325`)와 함께 제거 |
| cmd / nl / registry | 유지 | `L3 · 라우팅` → **`L4 · 라우팅`** | both | layer 문자열만 교정 |
| harness | 유지 | `실행 관할 · L5` + "L6~L8 포함" | both(구조도 박스 헤더) | `:647` desc의 "L5→L6→L7" 서술을 "L6→L7→L8"로 교정 |
| opd / opds / opdw / opp / opwt / oppd / opsdd / opdd / opgc | 유지 | `L5 · 오케스트레이터` → **`L6 · 오케스트레이터`** | both | **`:543` 등 기존 오표기 정합화** |
| **oppl** | ★신규 | `L6 · 오케스트레이터` | both | M-1 — 2-루프 수렴(설계 루프→실행 루프), 종료조건 5종, 3-SSOT tool-gated (`docs/PROJECT.md:105`) |
| operator / standalone / community | 유지 | `L4 · 직접 실행` → **`L6 · 직접 실행 (하네스 우회)`** | both | operator는 M-10(7→11종) 반영 |
| op-dev / op-task / op-sdd / op-data | 유지 | `L6 · 단계 스킬` → **`L7 · 단계 스킬`** | both | 수치 7/4/5/3 유지(실측 일치) |
| op-brain | 유지 | `L7 · 단계 스킬` | both | 키 유지(불필요한 리네임 회피), 라벨은 `op-brain-ingest (1)` |
| **op-scenario-gate** | ★신규 | `L7 · 단계 스킬` | both | M-4 — 목표-커버 루프 컨트롤(coverage-check→evaluator→종료조건) (`docs/PROJECT.md:146`) |
| ag-spec | 유지 | `L7` → **`L8 · 워커 에이전트`** | both | 6종·model 실측 반영(§2.5 주의) |
| ag-generic | 유지 | `L8 · 워커 에이전트` | both | 4 → **5** (loop-action 추가) |
| ~~ag-checker~~ → **ag-judge** | **리네임** | `L8 · 워커 에이전트` | both | 2 → **3** (evaluator 추가), 그룹명 "체커 · 심판" |
| ag-util | 유지 | `L8 · 워커 에이전트` | both | M-7 — 3단 → **2단 폴백** |
| ~~tool-pipeline 이전 3노드~~ | **재편** | — | — | 아래 4키로 교체 |
| **tool-pipeline** | ★신규 | `L9 · 도구 · 집행 수단` | both | state-tool(9cmd)·skill-registry·backlog-tool·test-tool·opal-agent (5) |
| **tool-knowledge** | ★신규 | `L9 · 도구 · 집행 수단` | both | code-scan(15cmd)·brain-tool(8cmd)·memory-tool(9cmd) (3) — L3 3자산과 1:1 대응 |
| **tool-convert** | ★신규 | `L9 · 도구 · 집행 수단` | both | cmux-tool·playwright-tool·xlsx-tool (3) |
| **tool-env** | ★신규 | `L9 · 도구 · 집행 수단` | both | opal-cli·doctor·tool-scan·date·git-sync-tool·improve-tool·opal-action-monitor (7) |
| twolayer / adapter / channel / console | 유지 | `L8 · 배포·어댑터` → **`L10 · 배포·어댑터·Console`** | both | channel은 085 DL-CONTRACT 반영 |
| **loop** | ★신규 | `환류 · L10 → L3 귀환` | both | 3스텝(적재·승격·먼저 읽기) |

**집계**: 현행 37키 − 삭제 2키(knowledge·ag-checker) = 유지 **35키** + 신규 11키(codemap·brain·memory·loop·oppl·op-scenario-gate·ag-judge·tool-pipeline·tool-knowledge·tool-convert·tool-env) = **46키**.

| 구분 | 키 내역 | 수 |
|------|---------|----|
| 유지 | claude·cursor·gemini·codex(4) / principles·identity·roles(3) / cmd·nl·registry(3) / harness(1) / opd~opgc(9) / operator·standalone·community(3) / op-dev·op-task·op-sdd·op-data(4) / op-brain(1) / ag-spec·ag-generic·ag-util(3) / twolayer·adapter·channel·console(4) | **35** |
| 삭제 | knowledge · ag-checker | **−2** |
| 신규 | codemap · brain · memory · loop · oppl · op-scenario-gate · ag-judge · tool-pipeline · tool-knowledge · tool-convert · tool-env | **+11** |
| **합계** | 37 − 2 + 11 | **46** |

> **[MUST] 총계는 참고값이고 판정 기준은 양방향 일치다.** `data-id` 집합과 `NODE_DATA` 키 집합이 **완전 일치(`comm -3` 출력 0줄)** 하는 것이 유일한 통과 조건이다. **총계(46)를 맞추기 위해 키를 삭제하거나 노드를 지우는 방향의 조정을 금지한다** — 위 매핑표의 유지/삭제/신규 판정이 SSOT이며, 실측 총계가 46과 다르면 매핑표와 대조해 어느 행이 누락·초과인지 식별하고 PM에 보고한다.

**기존 오표기 정합화 대상(전수)**: `:543` `opd`="L5 · 오케스트레이터"(실제 L4) 및 동일 패턴 `:547`·`:551`·`:555`·`:559`·`:563`·`:567`·`:571`·`:575`, `:579`·`:583`·`:587`(operator·standalone·community="L4"), `:592`~`:608`(단계 스킬="L6"), `:613`~`:625`(에이전트="L7"), `:630`~`:642`(배포="L8"). → 정본 번호로 일괄 재기재.

#### 2.5 사실 정합 복구 명세 (R-1 · M-1~M-11)

| # | 대상 노드/문자열 | 현행 | 교정값 | 근거 |
|---|-----------------|------|--------|------|
| M-1 | L6 layer-tag(`:401`) · 로드맵 현행 트랙(`:476`) · 신규 `oppl` 노드 | "Pilot 9" | **Pilot 10** + `oppl` 노드 신설 (`oppl` alias, `docs/CONVENTIONS.md:48`) | `ls -d opal/skills/opal-pilot-*` |
| M-2 | L8 layer-tag(`:439`) | "(13)" | **(15)** | D-12 |
| M-3 | 워커 4그룹 badge·alias (`:441-444`, `:303-306`) | 6/4/2/1 | **6 / 5 / 3 / 1** | D-12 |
| M-4 | 단계 스킬 그룹 (`:291-295`, `:429-434`) | 5그룹 20 | **6그룹 21** — op-dev 7 / op-task 4 / op-sdd 5(4+`op-spec-validator`) / op-data 3 / op-brain-ingest 1 / **op-scenario-gate 1** | `ls -d opal/skills/op-*` |
| M-5 | 도구 노드 (`:451-453`) | 10종 | **18종 전량** 4그룹 열거(§2.4) | `ls opal/tools`, D-6 |
| M-6 | MEMORY SSOT chip (`:454`, `:653-654`) | `.opal/MEMORY` | `.opal/MEMORY.json` + `memory/*.md` | `docs/ARCHITECTURE.md:94` |
| M-7 | `ag-util` (`:444`, `:626-628`) | "WebFetch → cmux → playwright 3단" | **cmux(1순위) → playwright(폴백) 2단**, WebFetch 완전 제거 | `opal/agents/opal-wtm-agent/AGENT.md`, D-13 §폴백 트리거 4종 |
| M-8 | code-scan 서술 (`:452`) | "전 파일 @header 실시간 스캔" | **15서브명령 + `.opal/code-map/` 작성층 + `_shards/` 샤딩 + `headerSource` 단일 키(미설정 시 전 명령 차단)** | `opal-harness.md:254`, `docs/CONVENTIONS.md:174-175` |
| M-9 | 버전 (`:343`, `:483`) | v0.5 (2건) | **v0.6** (잔존 0건) | R-7 |
| **M-10** | `operator` 노드 (`:412`, `:579-582`) | 7종 | **11종** — opi·onb·next·osc·oac·osm·opbr + **help·opim(improve)·opas(action-status)·workspace-sync** | `ls -d opal/skills/opal-*` |
| **M-11** | 로드맵 3트랙 (`:476-478`) | 077~085 미반영 | 현행=릴리스 DL-CONTRACT(085)·코드맵 샤딩(083) 승격 / 진행=코드맵 커버리지·Console 쓰기·Homebrew / 후순위=npm·Windows 실행검증·oppd deprecate 검토 | `docs/ARCHITECTURE.md:325`·`:402-403`, `docs/PROJECT.md:101`·`:179-180` |

**[MUST] 에이전트 model 레벨은 소스 frontmatter 실측을 따른다** — `docs/ARCHITECTURE.md`가 stale하다:
- `opal-be-agent`: 소스 `model: advanced` ↔ `docs/ARCHITECTURE.md:165` "standard" (문서 stale) → 다이어그램은 **be · adv** 유지(현행 `:441` chip이 옳다)
- `opal-task-agent`: 소스 `model: advanced` ↔ `docs/ARCHITECTURE.md:151` "standard" (문서 stale) → **task · adv**
- 실측 분류: 전문6 = plan·be·planning(adv) / fe·db·test(std) · 범용5 = task·task-action·sdd-action·loop-action(adv) / task-qa(light) · 체커·심판3 = security·evaluator(adv) / convention(std) · 변환1 = wtm(light) (→ D-12)

**[설계 제약] 도구 서브명령 수는 근거가 단일한 것만 병기한다** — `backlog-tool`은 `opal-harness.md:257`이 7서브명령, `docs/PROJECT.md:108`이 8서브명령(coverage-check 포함)으로 어긋나고 `test-tool`도 동일 양상이다(§5.3 D-INC-3). 문서 간 drift를 다이어그램에 수입하지 않기 위해 **code-scan(15)·state-tool(9)·brain-tool(8)·memory-tool(9)** 4종만 수치를 병기하고, backlog/test는 이름과 역할만 기재한다.

#### 2.6 렌더 검증 방법 (R-6)

R-6 AC는 ①2뷰 정상 렌더 ②노드 클릭 시 모달 오픈 ③`data-id`↔`NODE_DATA` 키 누락 0건 ④콘솔 에러 0건이다. **③은 브라우저로 검출되지 않는다** — `openModal`이 `if(!d) return;`(`:674`)으로 조용히 반환하므로 콘솔에 아무것도 남지 않는다. 따라서 검증을 2계층으로 분리한다.

**L1 — 결정론 게이트 (브라우저 불요, 실패 시 즉시 재작업)**

```bash
F=docs/architecture-diagram/opal_framework_architecture.html
# (1) [판정 기준] data-id ↔ NODE_DATA 키 양방향 대조 — 출력 0줄이어야 통과
grep -o 'data-id="[^"]*"' "$F" | sed 's/data-id="//;s/"//' | sort -u > /tmp/086-ids.txt
grep -oE '^  "?[A-Za-z0-9_-]+"?:\{' "$F" | tr -d ' "{:' | sort -u > /tmp/086-keys.txt
comm -3 /tmp/086-ids.txt /tmp/086-keys.txt        # ← 통과 조건: 반드시 빈 출력
wc -l < /tmp/086-ids.txt                          # ← 참고값(예상 46). 불일치해도 이 값으로 키를 지우지 말고 §2.4 매핑표와 대조 후 PM 보고
# (2) 버전 잔존 — 0이어야 통과
grep -c 'v0\.5' "$F"
# (3) 계층 수 문자열 — "9-레이어"/"9개 계층"/"9-layer" 잔존 0
grep -nE '9-레이어|9개 계층|9-layer' "$F"
# (4) 수치 정합 — 문자열별 개별 카운트(각 ≥1이어야 통과). 광범위 매칭 토큰은 문맥으로 좁힌다
grep -c 'Pilot 10' "$F"                           # Pilot 수
grep -c '단계 스킬 21' "$F"                        # 단계 스킬 수 (맨숫자 '21' 금지 — hex·좌표 오탐)
grep -cE '워커 에이전트.*\(15\)' "$F"              # 워커 계층 layer-tag 수치
grep -c '에이전트 15' "$F"                         # 로드맵 현행 트랙 수치
grep -c '18종' "$F"                               # 도구 수
grep -c 'MEMORY\.json' "$F"                       # 메모리 SSOT
grep -c '2단 폴백' "$F"                            # wtm 폴백
grep -c '11종' "$F"                               # operator 직접실행 스킬 수 (M-10)
# (4-b) 금지 문자열 잔존 — 전부 0이어야 통과
grep -cE '3단 폴백|WebFetch|Pilot 9|\(13\)' "$F"
# (5) 계층 토큰·규칙 수 — 각 10
grep -oE '\-\-c\-l[0-9]+:' "$F" | sort -u | wc -l
grep -cE '\.view-detail \.layer-l[0-9]+ \.node\{' "$F"
```

> 위 (1)의 키 추출은 §2.4 "항목 포맷 불변" 제약에 의존한다. 포맷을 바꾸면 게이트가 오탐하므로 **NODE_DATA 항목은 반드시 2칸 들여쓰기 + `키:{`로 유지한다**.

**L2 — 렌더 실측 (1순위 cmux-tool → 폴백 Playwright MCP)**

`cmux-tool`은 `--surface <handle>` B/C 모드로 사용자 브라우저를 재사용하며 `snapshot`·`eval`·`click`·`wait`를 제공한다(→ D-13 `:39-76`, `:142-144`). 절차:

```bash
CT=~/.opal/tools/cmux-tool/run.sh
URL="file://$(pwd)/docs/architecture-diagram/opal_framework_architecture.html"
$CT navigate "$URL" --surface <handle>            # 구조도 뷰(기본 active)
$CT wait --load-state complete --surface <handle> --timeout-ms 10000
$CT snapshot --surface <handle> --compact          # 증거 1: 구조도 렌더
# 브라우저 내 키 정합 실증 (L1과 독립된 2차 증거)
$CT eval --surface <handle> --script "(()=>{const ids=[...document.querySelectorAll('[data-id]')].map(e=>e.dataset.id);return JSON.stringify({n:ids.length,miss:ids.filter(i=>!(i in NODE_DATA))})})()"
$CT click ".tab[data-view='detail']" --surface <handle>
$CT snapshot --surface <handle> --compact          # 증거 2: 상세 뷰 렌더
# 모달 실증 — 신규 노드 4종
$CT click "[data-id='codemap']" --surface <handle>; $CT eval --script "document.getElementById('modal').classList.contains('open')" --surface <handle>
# (brain / memory / loop 동일 반복, 각 클릭 후 Escape 또는 #modalClose 클릭)
```

- `eval`의 `miss` 배열이 `[]`이면 ③을 브라우저 런타임에서도 확증한다(`n`은 참고값 — 예상 46).
- **콘솔 에러 0건(④)은 cmux-tool로 수집할 수 없다** — 서브명령 집합에 console 계열이 없다(→ D-13 `:39-76`). 또한 TASK.md가 폴백으로 지정한 `playwright-tool`도 `url → Markdown` 수집 전용이며 콘솔·스크린샷을 제공하지 않는다(→ D-14 `opal/tools/playwright-tool/main.py:1-11`, `:230-243` — 인자는 `url/--mode/--output/--timeout` 4개뿐).
- 따라서 ④의 폴백 수단을 **Playwright MCP**로 지정한다. 등록된 MCP 서버이며(`docs/ARCHITECTURE.md:297`) `browser_navigate` → `browser_console_messages`(에러만 필터) → `browser_click` → `browser_take_screenshot` 순으로 2뷰·콘솔·모달을 한 경로에서 실측할 수 있다.
- > **[캡틴 승인 대기 항목]** 이 폴백 수단 교체(`playwright-tool` → Playwright MCP)는 TASK.md §기술 스택(`TASK.md:90`)의 문면과 다르다. PM이 캡틴에게 에스컬레이션 중이며(§5.3 D-INC-1), 승인 전까지 본 절의 Playwright MCP 기술을 유지한다. 미승인 시 대안은 ④를 cmux-tool `eval` 기반 간접 증거(스크립트 실행 성공 = `typeof NODE_DATA === 'object'` 확인)로 격하하는 것이며, 이때 AC 문면("콘솔 에러 0건")의 직접 실측은 불가함을 DONE.md에 명시해야 한다.

**검증 주체 분리**: L1·L2는 편집 워커가 아니라 **PM이 직접** 수행한다 — "Producer(PM+캡틴)≠Evaluator ... 매반복 분리"(`docs/PROJECT.md:150`) 원칙을 이 태스크의 산출물 검증에도 적용해, 편집한 주체가 자기 산출물을 자기 기준으로 통과시키는 self-confirming을 차단한다.

---

## 3. 실행 체크리스트

> 총 11개 Step | Phase 2개

| Phase | Step | 실행 | 비고 |
|-------|------|------|------|
| 1 | S1 → S9 | **순차 (단일 디스패치)** | 대상 파일이 1개(HTML)이므로 분할 금지 — [MUST] `pm/dispatch-process.md:157` 동일 파일 다중 Step은 같은 디스패치에서 순차 편집 |
| 2 | S10 → S11 | 순차 | 검증 주체 분리(PM 직접) — `docs/PROJECT.md:150` Producer≠Evaluator |

### Step 1: 실측 스냅샷 재확인 · 치환 대조표 확정
- [x] 완료
- **파일**: (읽기 전용 — 산출 없음)
- **작업 내용**: `ls -d opal/skills/opal-pilot-*` / `ls opal/agents` / `ls -d opal/skills/op-*` / `ls opal/tools` / `ls -d opal/skills/opal-* | grep -v pilot` / `ls skills/`를 실행해 §1 실측 대조표(10/15/21/18/11/8)와 대조한다. 에이전트 model은 `grep -m1 '^model:' opal/agents/*/AGENT.md`로 확인한다.
- **완료 기준**: 6개 수치가 §1 표와 전건 일치. 불일치 1건이라도 나오면 편집을 중단하고 PM에 보고(값이 바뀐 것이므로 PLAN 수치를 먼저 갱신해야 한다).
- **테스트**: 명령 출력 6건을 EXECUTE 로그에 기록.
- **의존**: 없음
- **agent**: `opal-task-agent`

### Step 2: `:root` 토큰 · 계층 CSS 확장 (10계층 + 환류/지식)
- [x] 완료
- **파일**: `docs/architecture-diagram/opal_framework_architecture.html` (`:11-195`)
- **작업 내용**: (a) `--c-l1`~`--c-l10` 재배정(§2.1 표) + `--loop`·`--loop-m` 신규 2토큰. (b) `.layer-l10` 규칙 1줄 추가(`:131` 다음). (c) `.band-lN` 파스텔 재배정 + 지식용 `#D2F4FA`/`#A5E4F0` 신설, `.cross-know` 보라는 환류 전용으로 의미 이전. (d) `.loop-col`·`.cross-col`·`.loop-band`·`.loop-steps`·`.loop-step`·`.connector-up` 클래스 신설(§2.2 스케치). (e) `@media (max-width:920px)` 블록에 `.loop-col` 방향 전환·`.loop-band`/`.loop-steps` 1열 붕괴 규칙 추가.
- **완료 기준**: `--c-l{1..10}` 10개 토큰 존재 · `.view-detail .layer-l10 .node` 규칙 존재 · 신규 6클래스 정의 존재 · 920px 미디어쿼리에 신규 3규칙 존재. 외부 리소스 추가 0건(`<link>`/`<script src>` 개수 불변).
- **테스트**: §2.6 L1 (5) 토큰·규칙 카운트 = 각 10.
- **의존**: S1
- **agent**: `opal-task-agent`

### Step 3: 구조도(map) 뷰 재편 — 지식 3노드 · 환류 레일 · 번호 · 수치
- [x] 완료
- **파일**: 동일 (`:209-334`)
- **작업 내용**: (a) `.map-body` 좌측에 `.loop-col`(`data-id="loop"`) 삽입, 우측 `.cross`(`:325`) 단일 스트립을 `.cross-col` 안 3노드(`data-id="codemap"/"brain"/"memory"`)로 분할하고 각 노드에 참조 시점 캡션 1줄. (b) 밴드 행 순서를 정본 10계층으로 재배치 — 지식은 우측 횡단 컬럼이 담당하므로 본문 컬럼은 L1·L2·L4·[박스: L5 헤더 → L6 Pilot → L7 단계 → L8 워커]·L6 직접실행(박스 밖)·L9 도구·L10 배포. (c) 모든 `.mlabel .num`을 정본 번호로 교정. (d) `oppl` 노드 추가(Pilot 10), 단계 스킬 6번째 노드 `op-scenario-gate` 추가, 워커 alias 6/5/3/1, `ag-checker`→`ag-judge`, 도구 밴드 4노드 신설. (e) legend 갱신 — 지식(시안)·환류(보라)·하네스(점선)·CORE 4항목 + 지식/환류 의미 분리 명시.
- **완료 기준**: 구조도에 `codemap`·`brain`·`memory`·`loop`·`oppl`·`op-scenario-gate`·`ag-judge`·`tool-*` 4종 `data-id`가 존재하고, `data-id="knowledge"`·`data-id="ag-checker"`가 0건. `.mlabel .num` 텍스트가 정본 번호와 1:1.
- **테스트**: `grep -c 'data-id="knowledge"'` = 0 / `grep -o 'LAYER [0-9]*' | sort -u` 가 정본 집합과 일치.
- **의존**: S2
- **agent**: `opal-task-agent`

### Step 4: 상세(detail) 계층 재배치 + L3 지식 계층 신설 + legend 10항목
- [x] 완료
- **파일**: 동일 (`:339-370`, `:371-467`)
- **작업 내용**: (a) `.arch` 내부 계층 블록을 정본 순서로 이동 — 신규 L3(지식) 삽입, 하네스 블록을 Pilot 앞으로 이동, 나머지 `.layer-lN` 클래스·`.layer-num`·`.layer-name` 재기재. (b) L3 블록 신설: `boxes-3`에 지식 3노드, 각 노드에 §2.3의 (a)역할·(b)SSOT·(c)관리 도구를 `node-desc`로, 참조 시점을 `node-tech` chip으로, `layer-tag`에 "횡단 — 전 계층이 재참조" + `◀ 환류 도착 — 다음 세션이 이 계층부터 읽는다". (c) legend 10항목으로 확장(`:356-364`). (d) `.subtitle`(`:345`) "9개 계층" → "10개 계층"으로, 문장에 "하강 흐름 + 환류 귀환" 1구절 추가.
- **완료 기준**: `.layer-l1`~`.layer-l10` 블록이 각 1개씩 정본 순서로 존재. L3 3노드에 SSOT 경로·관리 도구·참조 시점이 모두 문자열로 존재. legend 항목 10개.
- **테스트**: `grep -o 'layer layer-l[0-9]*'` 순서 = L1..L10 / **`grep -o '<div class="legend-item">' "$F" | wc -l` = 13**(계층 10 + badge 3). ⚠ `grep -c 'legend-item'`은 CSS 규칙 줄(`:102`)이 혼입되어 현행값 13 → 확장 후 14가 되므로 **판정에 쓰지 않는다**(현행 정밀 카운트 실측 = 12).
- **의존**: S3
- **agent**: `opal-task-agent`

### Step 5: 상세 도구 계층(L9) 재편 + Pilot·단계·워커 사실 교정
- [x] 완료
- **파일**: 동일 (`:400-456` 상당 구간)
- **작업 내용**: (a) 구 L8(도구·지식 자산) 4노드를 §2.4의 `tool-pipeline`/`tool-knowledge`/`tool-convert`/`tool-env` 4노드로 교체하고 18종을 chip으로 전량 열거, "지식 집행 도구 3종은 L3 3자산과 1:1 대응" 문구 삽입, 구 "지식 자산 3종" 노드 제거(L3로 승격됨). (b) L6에 `oppl` 노드 추가 + layer-tag "Pilot 10 = 하네스 관할 / 하단 3 = 우회". (c) L7에 `op-scenario-gate` 노드 추가(6노드·합 21), op-sdd 노드 desc에 `op-spec-validator` 포함 명시. (d) L8 layer-tag "(15)" + 4그룹 badge 6/5/3/1 + `ag-judge` 리네임 + `ag-util` 2단 폴백 + model 레벨은 소스 실측(§2.5). (e) `operator` 노드 11종 열거(M-10), `channel` 노드에 085 DL-CONTRACT 1줄.
- **완료 기준**: 도구 18종 이름이 모두 문자열로 존재(18/18) · "3단 폴백"·"WebFetch" 잔존 0건 · "(13)"·"Pilot 9" 잔존 0건 · operator 노드에 11종 열거.
- **테스트**: `for t in state-tool skill-registry backlog-tool test-tool opal-agent code-scan brain-tool memory-tool cmux-tool playwright-tool xlsx-tool opal-cli doctor tool-scan date git-sync-tool improve-tool opal-action-monitor; do grep -q "$t" "$F" || echo "MISS $t"; done` → 출력 0줄.
- **의존**: S4
- **agent**: `opal-task-agent`

### Step 6: 환류 밴드 + 상향 커넥터 + 도착 앵커 삽입
- [x] 완료
- **파일**: 동일 (`.arch` 종료 직후 = 현행 `:467` 상당)
- **작업 내용**: §2.2 상세 뷰 설계대로 `.connector-up` → `.loop-band`(`data-id="loop"`, 좌측 레일 + 3스텝 카드) → `.connector-up`를 삽입한다. 3스텝 본문은 §2.2의 ①적재(CLOSE 훅·op-brain-ingest·brain 부재 시 no-op·history append) ②승격(promote → docs/brain) ③다음 세션이 먼저 읽음(브리핑 → 코드맵 → brain)으로 작성한다. 하강 커넥터(`.connector`)와 색·화살표 방향이 명확히 구분되어야 한다.
- **완료 기준**: 상세 뷰에 `loop-band` 1개 + `connector-up` 2개 존재. 밴드 내 문자열에 `CLOSE`·`op-brain-ingest`·`promote`·`부트스트랩`·`디스패치 전`이 모두 존재(출발·경로·도착 레이블 식별 가능). 구조도에는 S3의 `.loop-col`이 존재.
- **테스트**: `grep -c 'loop-band'` ≥ 1 · `grep -c 'connector-up'` = 2 · 두 뷰 각각에 환류 요소 1개 이상.
- **의존**: S5
- **agent**: `opal-task-agent`

### Step 7: NODE_DATA 재편 (신규 11 / 삭제 2 / layer 문자열 정합)
- [x] 완료
- **파일**: 동일 (`:498-655`)
- **작업 내용**: §2.4 매핑표대로 (a) 신규 11키 추가 — `codemap`·`brain`·`memory`는 §2.3 표의 (a)(b)(c)+참조 시점+(memory는 라이프사이클 4항목)을 `desc`/`detail[]`/`chips[]`에 담고, `loop`는 3스텝을, `oppl`·`op-scenario-gate`·`ag-judge`·`tool-*` 4종은 §2.5 실측값을 담는다. (b) `knowledge`·`ag-checker` 2키 삭제. (c) 전 키의 `layer` 문자열을 정본 번호로 재기재(§2.4 오표기 전수 목록). (d) `badge`는 `core|stable|later` 3택 유지(`:670-671`), 항목 포맷은 2칸 들여쓰기 + `키:{` 유지.
- **완료 기준**: **`comm -3` 출력 0줄(양방향 일치 — 유일 판정 기준)** · 키/`data-id` 총계 **46 예상(참고값 — 이 숫자에 맞추려고 키를 삭제하지 않는다)** · `badge` 값 3택 위반 0건 · `layer` 문자열에 구 번호(예: `opd`의 "L5") 잔존 0건. 총계가 46과 다르면 §2.4 매핑표 46행과 1:1 대조해 누락/초과 행을 특정하고 PM에 보고한다.
- **테스트**: §2.6 L1 (1) 게이트 + `grep -oE 'badge:"[a-z]+"' | sort -u` = core/stable/later 3종.
- **의존**: S6
- **agent**: `opal-task-agent`

### Step 8: 버전 v0.6 · 10-layer 문자열 · 로드맵 3트랙 · 상단 변경이력 주석
- [x] 완료
- **파일**: 동일 (`:1` 직후, `:203`, `:343`, `:345`, `:469-485`)
- **작업 내용**: (a) eyebrow(`:343`)·푸터(`:483`) v0.5 → **v0.6**. (b) 탭 라벨(`:203`) "상세 9-레이어" → "상세 10-레이어", 푸터(`:484`) "9-layer 구성도" → "10-layer 구성도". (c) 로드맵 3트랙을 M-11대로 현행화 — 현행: Pilot 10·에이전트 15·단계 스킬 21·도구 18 동작 / 릴리스 DL-CONTRACT 검증경로(085) / 코드맵 매니페스트 샤딩(082·083) / 멀티플랫폼 어댑터 / 진행: 코드맵 `@header` 커버리지 확충 · Console 쓰기 화면 · Homebrew tap · brain 커버리지 / 후순위: npm 통합 · Windows(ps1) 실행 검증 · oppd deprecate 검토 · WBS 검증기 도구 게이트화. (d) `<!DOCTYPE html>` 다음 줄에 HTML 주석 1행 추가: `<!-- v0.6 | 2026-08-10 HH:mm KST | 지식 자산 3종 독립 계층화 + 환류 루프 시각화 + 실측 정합 복구 (086) -->` — `docs/CONVENTIONS.md:201` 변경이력 포맷을 HTML 매체에 맞춰 적용.
- **완료 기준**: `grep -c 'v0\.5'` = 0 · `v0.6` ≥ 2 · "9-레이어/9개 계층/9-layer" 잔존 0 · 로드맵 3트랙 항목이 083·085를 포함 · 상단 주석 1행 존재.
- **테스트**: §2.6 L1 (2)(3).
- **의존**: S7
- **agent**: `opal-task-agent`

### Step 9: 결정론 검증 게이트 (편집 워커 자체 점검)
- [x] 완료
- **파일**: 동일 (읽기 전용 검사)
- **작업 내용**: §2.6 L1의 (1)~(5) 5개 명령을 실행하고 출력을 그대로 EXECUTE 로그에 남긴다. 실패 항목이 있으면 해당 Step으로 돌아가 수정 후 재실행한다(최대 3회 — 초과 시 blocked 반환).
- **완료 기준**: (1) `comm -3` 빈 출력 **[판정]** + 총계 46 **[참고]** · (2) 0 · (3) 빈 출력 · (4) 8개 카운트 각 ≥1 · (4-b) 금지 문자열 0 · (5) 각 10.
- **테스트**: 명령 출력 5건 첨부.
- **의존**: S8
- **agent**: `opal-task-agent`

### Step 10: 렌더 실측 (2뷰 · 콘솔 에러 0 · 모달 오픈)
- [ ] 완료
- **파일**: 동일 (읽기 전용 실행)
- **작업 내용**: §2.6 L2 절차를 수행한다. 1순위 `cmux-tool`(navigate → wait → snapshot ×2뷰 → eval 키 정합 → click 모달 4종). 콘솔 에러 수집은 Playwright MCP(`browser_navigate` → `browser_console_messages` 에러 필터 → `browser_click` → `browser_take_screenshot`)로 보완한다. 반응형은 MCP `browser_resize`(920px 이하 1회)로 환류 요소·지식 노드가 유지되는지 확인한다.
- **완료 기준**: 구조도·상세 각 1회 이상 렌더 증거 확보 · `browser_console_messages` 에러 0건 · `codemap`/`brain`/`memory`/`loop` 4종 모달 오픈 확인 · `eval` 결과 **`miss:[]`**(판정) 및 `n` 46(참고) · 920px에서 좌측 레일이 상단 밴드로 전환되고 지식 3노드가 표시됨.
- **테스트**: 스냅샷/스크린샷 + 콘솔 메시지 출력 첨부.
- **의존**: S9
- **agent**: **PM 직접** (검증 주체 분리 — `docs/PROJECT.md:150`)

### Step 11: docs/ 갱신 판단
- [ ] 완료
- **파일**: (판단 기록만 — 문서 수정 없음)
- **작업 내용**: 이 태스크의 변경이 `docs/` 본문에 영향을 주는지 판정한다. TASK.md가 `docs/ARCHITECTURE.md` 본문 갱신을 명시적으로 범위 외로 확정했고(`TASK.md:84` "범위 외 파생 갱신 금지 — CLOSE 단계의 관련 문서 갱신 판단으로 이관"), 다이어그램은 참조 문서가 아니라 시각 산출물이므로 **이 태스크에서는 no-op**으로 판정한다. 단 §5.3의 D-INC 4건(문서 stale)을 CLOSE 이관 목록으로 기록한다.
- **완료 기준**: no-op 판정 근거 1줄 + CLOSE 이관 항목 4건이 DONE.md에 기록됨.
- **테스트**: DONE.md에 이관 목록 존재.
- **의존**: S10
- **agent**: **PM 직접**

> **에이전트 배정 근거**: 대상이 HTML+CSS+Vanilla JS 단일 파일이므로 `opal-fe-agent`(EXECUTE/FE, standard)가 후보였으나, ① `docs/PROJECT.md:158-160` §프로젝트 구성이 FE 전문 에이전트의 적용 범위를 `dashboard/frontend/`로 한정하고 프레임워크 자산(`opal/`·`skills/`·`agents/`)의 담당을 `opal-task-agent (범용)`로 지정한다. ② 이 편집의 과반은 시각 구현이 아니라 **프레임워크 사실 정합**(수치·명칭·계층 의미·도구 18종·에이전트 model 레벨)이며 오판 시 AC 직접 위반이 된다. ③ 계층 재편·NODE_DATA 46키 재작성은 문서 교차 참조 부담이 커 advanced 모델이 필요하다(`opal-fe-agent`는 standard, `opal-task-agent`는 advanced — D-12 실측). 따라서 편집 Step 전량을 `opal-task-agent` 단일 디스패치에 배정하고, FE 성격(디자인 토큰·반응형 제약)은 PM이 §2.1·§2.2 CSS 스케치를 컨텍스트로 주입해 보강한다.

---

## 4. QA 체크리스트

### 기능 테스트
- [ ] 구조도 뷰가 렌더되고 10계층 라벨이 정본 번호로 표시된다 (R-6)
- [ ] 상세 뷰가 렌더되고 L1~L10 계층이 정본 순서로 표시된다 (R-6)
- [ ] 탭 전환이 동작한다 (구조도 ↔ 상세, `.view.active` 토글)
- [ ] 지식 3자산 노드(`codemap`·`brain`·`memory`) 클릭 시 모달이 열리고 (a)역할 (b)SSOT (c)관리 도구 (d)참조 시점이 모두 보인다 (R-2·R-4)
- [ ] MEMORY 모달에 `promote` 승격 관계가 명시되어 있다 (R-5)
- [ ] 환류 요소(`loop`) 클릭 시 3스텝(적재·승격·먼저 읽기)이 보인다 (R-3)
- [ ] 신규 노드(`oppl`·`op-scenario-gate`·`ag-judge`·`tool-*`4) 클릭 시 모달이 열린다 (R-6)
- [ ] `comm -3` 키 대조 출력 0줄 (R-6 — 브라우저로 검출 불가한 항목) / 총계 46키는 참고값
- [ ] 콘솔 에러 0건 (R-6)
- [ ] 920px 이하에서 환류 요소·지식 3노드가 유지되고 가로 스크롤이 발생하지 않는다 (R-6)

### 일관성 테스트
- [ ] `data-id`·NODE_DATA 키·CSS 클래스가 kebab-case (→ D-4 `:18`)
- [ ] 두 뷰 + 모달의 계층 번호가 정본 1종으로 통일되어 어긋난 표기 0건 (§1 현재 상태의 3중 불일치 해소)
- [ ] 실측 수치 6종(10/15/21/18/11/8)이 다이어그램·PLAN·소스 디렉토리 3자 간 일치 (R-1)
- [ ] "3단 폴백"·"WebFetch"·`.opal/MEMORY`(‌.json 없는 표기)·"Pilot 9"·"(13)" 잔존 0건 (R-1)
- [ ] 지식=시안 / 환류=보라 색 시그니처가 두 뷰에서 동일 계열로 유지된다 (§2.1 색 규칙)
- [ ] 도구(L9)와 자산(L3)의 범주 분리가 유지되고, 지식 집행 도구 3종 ↔ 자산 3종 대응이 명시된다 (F-3)
- [ ] 외부 스크립트·CDN 추가 0건 — `<script src>` 0개, `<link href>`는 기존 Google Fonts 3개 그대로 (`TASK.md:81`)
- [ ] 파일 경로·파일명 불변, 백업 파일 생성 0건 (`TASK.md:82`)

### 문서 품질
- [ ] 한국어 본문 + 영어 코드/필드명 규칙 (→ D-4 `:9-11`)
- [ ] 노드 카피가 마케팅 문구가 아니라 엔지니어 서술체 (→ D-5 `:169` "Don't write marketing copy in node descriptions")
- [ ] `badge` 값이 `core|stable|later` 3택을 벗어나지 않는다 (`:670-671`)
- [ ] 버전 문자열 v0.6 일치, v0.5 잔존 0건 (R-7)
- [ ] 상단 변경이력 주석에 KST 일시 + 태스크 번호(086) 포함 (→ D-4 `:201`)
- [ ] 로드맵 3트랙이 083·085를 반영 (R-7)

---

## 5. 리스크 및 대응

### 5.1 리스크 등록

| # | 리스크 | 영향 | 대응 방안 |
|---|--------|------|----------|
| R-1 | `data-id`↔`NODE_DATA` 키 누락이 **콘솔 에러 없이** 조용히 실패(`:674` `if(!d) return;`) | 모달 무반응 = R-6 AC 위반이 렌더 검증만으로는 미검출 | §2.6 L1 (1) 결정론 대조를 **차단 게이트**로 승격(S9). 브라우저 `eval`로 2차 확증(S10) |
| R-2 | 계층 번호 재배치 중 일부 노드의 `layer` 문자열 누락 → 3중 불일치 재발 | 모달과 뷰의 층 표기 모순 | §2.4에 오표기 전수 목록(줄번호)을 명시했고, S7 완료 기준에 "구 번호 잔존 0건" grep 포함 |
| R-3 | CSS 토큰 슬롯 이동으로 인라인 `var(--c-lN)` 참조가 어긋남(`:373`, `:454`) | 색 오배정(시각 결함) | §2.1 표에 인라인 사용처 2건을 명시하고 `:454`는 `--c-l3` 재지정으로 처리 |
| R-4 | 환류 레일이 920px 이하에서 겹치거나 가로 스크롤 유발 | 반응형 결함 | 절대배치를 배제하고 flex 컬럼 + 기존 `flex-direction:column` 전환에 편승(§2.2 D안). S10에서 `browser_resize` 실측 |
| R-5 | 도구 18종 chip 과밀로 카드 레이아웃 붕괴 | 판독성 저하 | 4그룹으로 분산(5/3/3/7)하고 `boxes-2` 그리드 유지. chip은 도구명 중심, 서브명령 수는 4종만 병기 |
| R-6 | 실측값이 EXECUTE 시점에 변동(스킬·도구 추가) | 수치 불일치 재발 | S1에서 재실측 후 PLAN 값과 대조, 불일치 시 편집 중단·PM 보고 |
| R-7 | `playwright-tool`이 콘솔 로그·스크린샷을 지원하지 않아 R-6 AC ④의 지정 폴백 경로가 성립하지 않음 | "콘솔 에러 0건" 실측 불가 | Playwright MCP로 폴백 수단 교체(§2.6). `decision_required`로 PM 에스컬레이션(D-INC-1) |
| R-8 | 로드맵 현행화가 최신 태스크 상태를 잘못 반영 | R-7 AC 부분 미달 | 083·085 근거를 `docs/ARCHITECTURE.md:325`·`:402-403`, `docs/PROJECT.md:179-180`으로 고정 인용 |
| R-9 | 단일 파일 대량 편집 중 중간 저장 실패로 부분 상태 잔존 | 렌더 깨짐 | Step 단위 증분 저장 + S9 게이트. 백업 파일 금지이므로 복원은 `git checkout -- <file>` (git 이력, `TASK.md:82`) |

### 5.2 리스크 가설 표 (검증 계층 권고)

| # | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|---|----------|-----------------|----------|--------------|--------------|
| H-1 | 계층 번호 정본화 | 외부 문서의 "L8 지식 자산" 류 인용 | 없음 — 활성 참조 0건(grep 결과 과거 태스크 기록 3건만) | L1 grep | 다이어그램 계층 번호를 인용하는 활성 문서 0건 재확인 |
| H-2 | NODE_DATA 46키 재편 | `data-id` ↔ 키 1:1 계약 (`:673-674`) | 모달 무반응(조용한 실패) | **L1 결정론 + L2 브라우저 eval 2중** | 46노드 전수 클릭 시 모달 오픈율 100% |
| H-3 | `badge` 값 | `badgeClass`/`badgeText` 3키 룩업 (`:670-671`) | `class="m-badge undefined"` 렌더 | L1 grep | badge 값 집합 = {core, stable, later} |
| H-4 | 신규 CSS 클래스 6종 | 기존 `.layer`/`.band` 그리드 계약 | 레이아웃 붕괴 | L2 렌더 + resize | 1440px·920px·480px 3폭에서 가로 스크롤 0 |
| H-5 | 환류 요소 삽입 | 하강 커넥터와의 시각 구분 | Loops 오독 지속(R-3 미달) | L2 스냅샷 + 사람 판독 | 스냅샷에서 귀환 방향·출발/도착 레이블 식별 가능 |
| H-6 | 자기완결성 | 외부 리소스 금지 계약 (`TASK.md:81`) | 오프라인 렌더 실패 | L1 grep | `<script src>` 0개 · `<link href>` = 기존 3개 |
| H-7 | 실측 수치 11건 | 소스 디렉토리 SSOT | 문서 신뢰 하락(재발) | L1 grep + S1 재실측 | 6개 카운트 명령 출력 = 다이어그램 표기 |
| H-8 | IIFE 무변경 | 탭·모달·키보드 리스너 (`:657-693`) | 인터랙션 전면 상실 | L2 클릭·Escape | 탭 2회 전환 + 모달 Escape 닫힘 동작 |

### 5.3 문서/코드 불일치 보고 (범위 외 — PM 보고 + CLOSE 이관)

실제 구성(디렉토리·소스 frontmatter) 기준으로 설계했고, 아래 문서 stale은 이 태스크에서 고치지 않는다.

| # | 불일치 | 실측/실제 | 문서 표기 | 조치 |
|---|--------|----------|----------|------|
| D-INC-1 | `playwright-tool` 능력 | `url → Markdown` 수집 전용 (인자 4개, 콘솔·스크린샷 없음) — `opal/tools/playwright-tool/main.py:1-11`, `:230-243` | `TASK.md:90` "렌더 검증: playwright-tool(폴백) — 콘솔 로그 수집" | 폴백을 Playwright MCP로 교체(§2.6). **`decision_required` 에스컬레이션** |
| D-INC-2 | 에이전트 model 2건 | `opal-be-agent`=advanced, `opal-task-agent`=advanced (소스 frontmatter) | `docs/ARCHITECTURE.md:151`·`:165` "standard" (+ PM 디스패치 매핑표도 be=standard) | 다이어그램은 소스 실측 표기. 문서 갱신은 CLOSE 이관 |
| D-INC-3 | 도구 서브명령 수 | `backlog-tool` 8(coverage-check 포함)·`test-tool` scenario-* 확장 — `docs/PROJECT.md:108-109` | `opal-harness.md:257` "7 서브명령", `:253` "9서브명령" | 다이어그램에 수치 미표기(drift 수입 차단). 문서 정합은 CLOSE 이관 |
| D-INC-4 | 독립 스킬 수 | `skills/` 실측 **8** | `docs/ARCHITECTURE.md:78` "5개", `:337` "6개" / `docs/PROJECT.md` 표 6종 | 다이어그램은 8종 표기(현행 `:585` 이미 8종). 문서 갱신 CLOSE 이관 |
| D-INC-5 | 서브에이전트 수 | `opal/agents/` 실측 **15** | `docs/ARCHITECTURE.md:39`·`:79`·`:373` "12개" | 다이어그램은 15. 문서 갱신 CLOSE 이관 |
| D-INC-6 | 다이어그램 문서 레지스트리 미등록 | `docs/architecture-diagram/opal_framework_architecture.html` | `docs/PROJECT.md:164-172` §프로젝트 문서 표에 부재 | 등록 여부 판단을 CLOSE 이관(범위 외 파생 갱신 금지 — `TASK.md:84`) |
| D-INC-7 | wtm 폴백 표기 | 2단(cmux → playwright) | `~/.opal/references/agents.md:254` "Phase 1(WebFetch)" (PM 사전 통지분) | 배포본 문서 — 이 태스크 범위 외, PM 보고만 |

---

## 6. R-1~R-7 커버리지 매트릭스

| 요구사항 | AC 요지 | 담당 Step | 검증 방법 |
|---------|--------|----------|----------|
| **R-1** 사실 정합 복구 | Pilot 10·에이전트 15·단계스킬 21·도구 18·MEMORY.json·wtm 2단, 불일치 0건 | S1(실측), S3(구조도), S5(상세), S7(모달), S8(로드맵) | S9 L1 (4) 문자열별 개별 카운트 8종 각 ≥1 + (4-b) 금지 문자열("3단 폴백/WebFetch/Pilot 9/(13)") 카운트 0 + S1 재실측 대조 (M-10·M-11 증분 포함) |
| **R-2** 지식 자산 독립 표현 | 3자산 독립 노드 + (a)역할 (b)SSOT (c)관리 도구 | S3(구조도 3노드), S4(상세 L3), S7(모달 3키) | S10 모달 3종 오픈 후 (a)(b)(c) 문자열 확인 + QA §일관성 "도구≠자산 분리" |
| **R-3** 환류 루프 시각화 | 두 뷰 모두 귀환 시각 요소 + 출발(CLOSE)·도착 레이블 | S2(CSS), S3(map `.loop-col`), S6(detail `.loop-band`+`connector-up`) | S9 `grep -c loop-band`/`connector-up` + S10 두 뷰 스냅샷에서 귀환 방향·레이블 판독 |
| **R-4** 참조 시점 앵커 | 3자산 각각 최소 1개 참조 시점 표기 | S4(L3 chip), S7(모달 detail) | S10 모달에서 "디스패치 전 무조건"·"설계 착수 전 3시점"·"부트스트랩 브리핑" 3건 확인 |
| **R-5** 메모리 라이프사이클 | MEMORY → brain·docs 승격 관계 명시 | S4(노드 본문), S7(`memory` 모달 detail 4항목) | S10 `memory` 모달에서 `promote`·docs/brain·FIFO5·status 라이프사이클 확인 |
| **R-6** 기존 기능·구조 보존 | 2뷰 렌더 + 모달 키 누락 0 + 콘솔 에러 0 + 단일 HTML | S2·S3·S4·S6(구조), S7(키), S9(결정론), S10(렌더) | S9 L1 (1) `comm -3` 0줄[판정]·(5) + S10 L2(스냅샷 2뷰·`eval miss:[]`·`browser_console_messages` 0건·resize) + QA "외부 리소스 0" |
| **R-7** 버전·이력 갱신 | v0.6 일치(v0.5 잔존 0) + 로드맵 3트랙 현행화 | S8 | S9 L1 (2)(3) + 로드맵에 083·085 반영 확인 |

**누락 0건** — R-1~R-7 전건이 최소 1개 Step과 1개 검증 방법에 대응된다.

---

## 부록: EXECUTE 워커에게 넘길 고정 제약 (재해석 금지)

1. [MUST] 대상 파일 1개만 수정. 경로·파일명 불변. 백업 파일 생성 금지. (`TASK.md:82`)
2. [MUST] 인라인 CSS/JS 유지. 외부 스크립트·CDN 추가 금지(기존 Google Fonts 3링크는 유지). (`TASK.md:81`)
3. [MUST] IIFE 스크립트(`:657-693`) 로직 무변경. 신규 노드는 `[data-id]` 선택자에 자동 편입된다.
4. [MUST] NODE_DATA 스키마 `{t,badge,layer,tag,desc,detail[],chips[]}` 불변, `badge`는 `core|stable|later` 3택, 항목은 2칸 들여쓰기 + `키:{` 포맷 유지.
4-b. [MUST] 키 정합의 판정 기준은 **`data-id` 집합 = NODE_DATA 키 집합(`comm -3` 출력 0줄)** 이며, 총계(46)는 **참고값**이다. **총계를 맞추기 위해 키·노드를 삭제하거나 임의 추가하는 조정을 금지한다** — §2.4 매핑표 46행(유지 35 / 신규 11 / 삭제 2)이 SSOT이고, 실측 총계가 다르면 매핑표와 1:1 대조해 원인 행을 특정한 뒤 PM에 보고한다.
5. [MUST] 수치·이름은 S1 재실측값만 사용. 문서 값을 그대로 옮기지 않는다. (`TASK.md:83`)
6. [MUST] 증분 저장 — Step 단위로 저장하고 다음 Step으로 이동. 말미 일괄 저장 금지.
7. [MUST] 계층 번호는 §2.1 정본 10계층 1종만 사용. 두 뷰와 모달이 동일 번호를 쓴다.
