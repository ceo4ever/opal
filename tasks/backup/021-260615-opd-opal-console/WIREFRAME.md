# WIREFRAME — OPAL Console (1차 뷰어)

> 작성일: 2026-06-15 | 단계: ANALYSIS | 산출물: UI 와이어프레임 제안
> 입력: TASK.md (C-1~C-10, 6개 화면, R-6 칸반) + shadcn MCP 레지스트리 실조사
> 대상: 캡틴 검토용 — PLAN 전 UI 방향 확정
> 디자인 지향: Linear / Vercel / Raycast 류의 절제된 세련미 (밀도 높은 개발자 도구)

---

## 0. shadcn/ui 레지스트리 실조사 결과 (근거)

본 와이어프레임의 컴포넌트 매핑은 추측이 아니라 연결된 shadcn MCP(`@shadcn` 레지스트리)로 실제 조사한 결과에 기반한다.

### 조사로 확인된 핵심 자산

| 분류 | 확인된 아이템 | 본 콘솔에서의 용도 |
|------|--------------|-------------------|
| 앱 셸 블록 | `sidebar-07` (아이콘 축소형), `sidebar-16` (sticky 헤더), `sidebar-08` (inset+보조 네비), `dashboard-01` | 글로벌 레이아웃의 기준 골격 |
| 대시보드 블록 | `dashboard-01` (= sidebar + **section-cards** + `chart-area-interactive` + **tanstack data-table** + dnd-kit) | 대시보드 화면 통째로 차용 |
| 차트 블록 (전 패밀리) | `chart-area-interactive`, `chart-area-gradient`, `chart-bar-*`, `chart-line-*`, `chart-pie-donut-text`, `chart-radial-*`, `chart-radar-*` | 추이/집계/진행률/도입현황 |
| 데이터 테이블 | `data-table-demo` (`@tanstack/react-table` + table + dropdown-menu + checkbox + input) | 프로젝트/태스크/메모리 테이블 |
| UI 컴포넌트 | `card`, `badge`, `item`(리스트 행), `empty`(빈 상태), `skeleton`, `spinner`, `command`(⌘K 팔레트), `drawer`/`sheet`(상세 패널), `resizable`(분할 뷰), `tabs`, `scroll-area`, `tooltip`, `hover-card`, `kbd`(키 힌트), `breadcrumb`, `separator`, `progress`, `avatar`, `select`, `toggle-group`, `collapsible`, `accordion`, `alert`, `sonner`(토스트) | 화면 전반 |

> 참고: 칸반 드래그용 `@dnd-kit/*`는 dashboard-01 의존성으로 이미 따라온다. **1차는 읽기 전용이므로 dnd-kit의 드래그는 비활성**하고, 카드의 hover/press 인터랙션만 사용한다(§5).
> 그래프 시각화(브레인 related 네트워크)는 shadcn 표준 차트(recharts)로는 force-graph가 없어 PLAN에서 별도 라이브러리(react-force-graph / reactflow / cytoscape) 확정이 필요하다(U-6). 와이어프레임은 배치만 정의.

---

## 1. 디자인 시스템 방향

shadcn 테마 변수(CSS custom properties) 체계를 그대로 채택한다. 모든 컬러는 토큰 경유 — 하드코딩 hex 금지.

### 1.1 컬러 토큰 (다크/라이트 양립 — 필수)

shadcn 표준 토큰을 베이스로 하고, OPAL 상태색 5종을 추가 토큰으로 확장한다.

| 토큰 | 라이트 | 다크 | 용도 |
|------|--------|------|------|
| `--background` / `--foreground` | near-white / near-black | near-black(#0A0A0B 계열) / near-white | 앱 배경·본문 |
| `--card` / `--card-foreground` | white | elevated dark(#111114) | 카드 표면 |
| `--muted` / `--muted-foreground` | gray-100 / gray-500 | gray-900 / gray-400 | 보조 텍스트·구분 |
| `--border` | gray-200 | white/8% | 1px 헤어라인 (밀도의 핵심) |
| `--primary` | OPAL 시그니처(오팔 톤: teal↔violet 중 1택, 권고: violet `#7C5CFF`) | 동일 hue, 명도 보정 | 강조·활성 네비 |
| `--accent` | hover 표면 | white/5% | hover 배경 |
| `--ring` | primary 30% | primary 40% | 키보드 포커스 링 |

**OPAL 상태색 확장 토큰** (상태 뱃지·칸반·타임라인 공용, §6.2와 일치):

| 토큰 | 의미 | 라이트 | 다크 |
|------|------|--------|------|
| `--status-todo` | ⬜ 대기 | slate-400 | slate-500 |
| `--status-running` | 🔄 진행중 | blue-500 | blue-400 |
| `--status-done` | ✅ 완료 | emerald-500 | emerald-400 |
| `--status-blocked` | ❌ 블로킹 | rose-500 | rose-400 |
| `--status-stale` | ⚠️ stale/경고 | amber-500 | amber-400 |
| `--chart-1..5` | 차트 시리즈 | shadcn 차트 토큰 그대로 | 동일 |

기본 모드는 **다크** (개발자 도구 정체성). 라이트는 완전 지원. 테마 토글은 상단 바(§2.2)에 위치, 선택값 localStorage 영속.

### 1.2 타이포 스케일

- 본문/UI: **Geist Sans** (또는 Inter) — Vercel 톤. 숫자는 `font-variant-numeric: tabular-nums` (표·메트릭 정렬).
- 코드/경로/ID/frontmatter: **Geist Mono** (또는 JetBrains Mono).
- 스케일(밀도 우선, 작게): `text-xs 12 / text-sm 13~14(기본 UI) / text-base 15 / text-lg 18(섹션 제목) / text-2xl 24(페이지 H1) / text-3xl 30(대시보드 메트릭 숫자)`.
- 본문 행간 `leading-relaxed`는 마크다운 뷰어에만. UI 라벨은 `leading-tight`.

### 1.3 Spacing / Radius / 밀도

- spacing 베이스 4px. 카드 패딩 `p-4~p-6`, 리스트 행 높이 `h-9~h-10`(밀도형), 테이블 행 `h-10`.
- radius: `--radius: 0.625rem`(10px) 기본, 카드 `rounded-xl`, 뱃지/버튼 `rounded-md`, 칩 `rounded-full`.
- **밀도 원칙**: 정보 밀도 높게 — 여백보다 1px `--border` 헤어라인으로 영역 구분(Linear 방식). 큰 그림자 금지, `shadow-xs`만 또는 border-only.

### 1.4 아이콘 / 그래픽

- 아이콘: **lucide-react** (shadcn 기본) + 일부 `@tabler/icons-react`(dashboard-01 의존). 1.5px stroke, 16px 기본.
- 마크다운 렌더: `react-markdown` + `remark-gfm`(표/체크박스), 코드블록은 `shiki` 하이라이트(다크 테마 일치).

---

## 2. 앱 셸 / 글로벌 레이아웃 / IA

### 2.1 골격 — `sidebar-07` + `sidebar-16` 조합

`SidebarProvider` + 아이콘 축소형 좌측 네비(`sidebar-07`) + sticky 사이트 헤더(`sidebar-16`)를 합친다. 메인은 `SidebarInset`.

```
┌──────────────────────────────────────────────────────────────────────────┐
│ [≡] OPAL Console      [⌘ 검색…]            🌗테마  ⟳새로고침  ●연결됨  ⚙   │ ← 상단바(sticky header)
├────────────┬─────────────────────────────────────────────────────────────┤
│  ◇ OPAL    │                                                              │
│            │                                                              │
│ ▸ 대시보드 │                     MAIN  (SidebarInset)                     │
│ ▸ 프로젝트 │                                                              │
│ ▸ 태스크   │                  화면별 콘텐츠 영역                          │
│ ▸ 메모리   │                                                              │
│ ▸ 브레인   │                                                              │
│ ▸ 환경     │                                                              │
│ ────────── │                                                              │
│ [전 프로젝트│                                                              │
│  ▼ 프로젝트셀]                                                            │
│  ◷ 마지막   │                                                              │
│    스캔 …   │                                                              │
└────────────┴─────────────────────────────────────────────────────────────┘
```

- **좌측 사이드바** = `sidebar-07`(collapse-to-icon). 6개 메인 네비는 `SidebarMenu` + `SidebarMenuButton`(active=primary). 접으면 아이콘만 + tooltip 라벨.
  - 상단: 앱 로고 + (선택) 프로젝트 스위처 `DropdownMenu`(sidebar-07의 team-switcher 패턴 재사용).
  - 하단(`SidebarFooter`): "마지막 스캔 시각" + 연결 상태 칩.
- **상단 바** = `sidebar-16` sticky header. `SidebarTrigger`(≡) + `Breadcrumb`(현재 위치) + 가운데/우측 `Command` 트리거 + 우측 액션군.

### 2.2 상단 바 구성

| 영역 | 컴포넌트 | 동작 |
|------|----------|------|
| 좌 | `SidebarTrigger`(≡) + `Breadcrumb` | 사이드바 토글 / 현재 경로(예: 태스크 / ai-framework / 021-…) |
| 중앙 | `Button`(검색 트리거) + `Kbd`(⌘K) → `CommandDialog` | 전역 검색 팔레트(프로젝트·태스크·brain 페이지·메모리 통합 점프) |
| 우 | 테마토글(`DropdownMenu`: 라이트/다크/시스템) · 새로고침(`Button` ghost + `spinner`) · 연결상태(`Badge` ●) · 설정(`DropdownMenu`) | 데이터 재수집 / 데몬 연결 표시 |

> 검색 팔레트 = `command` 컴포넌트. "전 프로젝트 보기"에서도 어떤 프로젝트의 무엇이든 한 번에 점프 — 개발자 도구다움의 핵심 디테일.

### 2.3 네비게이션 트리 (6 화면)

```
OPAL Console
├─ 대시보드        (/)                전 프로젝트 집계 — 컨텍스트: 항상 ALL
├─ 프로젝트        (/projects)        목록 → /projects/:id 상세(우측 패널)
├─ 태스크          (/tasks)           칸반 — 컨텍스트 의존(단일 프로젝트 권장)
│   └─ 태스크 상세 (/tasks/:proj/:taskId) → Drawer(파이프라인+산출물 뷰어)
├─ 메모리          (/memory)          컨텍스트 의존
├─ 브레인          (/brain)           컨텍스트 의존 → /brain/:slug 페이지 뷰어
└─ 환경            (/doctor)          전 프로젝트 or 단일
```

### 2.4 "전 프로젝트" ↔ "단일 프로젝트 컨텍스트" 전환

- **프로젝트 스위처**(사이드바 상단 `DropdownMenu`)에 항상 최상단 `★ 전 프로젝트` 옵션 + 그 아래 프로젝트 목록.
- 화면별 컨텍스트 규칙:
  - **대시보드 / 환경**: 전 프로젝트 집계가 기본(스위처가 "전 프로젝트"여도 정상).
  - **태스크 / 메모리 / 브레인**: 단일 프로젝트 데이터가 본질 → 컨텍스트가 "전 프로젝트"면 상단에 `Alert`("프로젝트를 선택하세요") + 프로젝트 선택 그리드를 인라인 표시(빈 상태 대체).
- 컨텍스트 선택값은 URL 쿼리(`?project=ai-framework`)와 동기화 → 딥링크·새로고침 보존.

---

## 3. 화면별 와이어프레임

> 데이터 표기는 TASK.md "1차 뷰어 화면 구성" 데이터 소스 표를 따른다.

### (1) 대시보드 — 전 프로젝트 현황 (`dashboard-01` 차용)

dashboard-01 블록의 3단 구조(section-cards → 인터랙티브 차트 → data-table)를 OPAL 데이터로 재배치.

```
대시보드  (전 프로젝트)
┌──────────────┬──────────────┬──────────────┬──────────────┐
│ OPAL 프로젝트 │ 진행중 태스크 │ 블로커        │ Stale Brain   │  ← section-cards (card×4)
│   7          │   3          │   1 ⚠         │   2 ⚠         │     큰 숫자 + 추세 Badge
│ +2 미적용     │ ↑ 이번주     │ 즉시 확인     │ lint 경고     │
└──────────────┴──────────────┴──────────────┴──────────────┘
┌───────────────────────────────────────┬──────────────────────┐
│ 태스크 활동 추이 (최근 90일)           │ 단계 분포             │
│   [chart-area-interactive]            │  [chart-pie-donut-text]│
│   ▔▔▔╱▔╲▔╱▔▔ 7d|30d|90d 토글         │  ⬜🔄✅❌ 비율          │
└───────────────────────────────────────┴──────────────────────┘
┌────────────────────────────────────────────────────────────────┐
│ ⚠ 주의 알림  (블로커 · stale brain · 오래된 진행중)            │  ← Card + item 리스트
│  ● [ai-framework] 태스크 021 BE 단계 BLOCKED — 2일째           │     상태색 좌측 바
│  ● [ai-framework] brain "deploy-boundary" stale (30일 미갱신)  │     클릭→해당 화면 점프
│  ● [proj-x] 진행중 태스크 5일째 무변동                          │
└────────────────────────────────────────────────────────────────┘
┌────────────────────────────────────────────────────────────────┐
│ 최근 활동 (전 프로젝트)            [data-table: 프로젝트|태스크|단계|상태|갱신]│
└────────────────────────────────────────────────────────────────┘
```

| 영역 | shadcn 매핑 | 데이터 소스 |
|------|------------|------------|
| 상단 4메트릭 | `card`(section-cards 패턴) + `badge` 추세 | 스캔 → 각 state.json 집계 + brain lint |
| 활동 추이 | `chart-area-interactive` (7d/30d/90d `toggle-group`) | state.json 타임스탬프 |
| 단계 분포 | `chart-pie-donut-text` (중앙에 총 태스크 수) | state.json rows 상태 집계 |
| 주의 알림 | `card` + `item` 리스트, 좌측 `--status-*` 바, 행 hover | state.json(blocked/stale) + brain lint + git |
| 최근 활동 | `data-table`(tanstack) 정렬/필터 | 전 프로젝트 state.json merge |

### (2) 프로젝트 — 도입 현황 맵 + 상세 (목록 + `resizable` 우측 패널)

```
프로젝트
┌─────────────────────────────────────────┬───────────────────────────────┐
│ 검색[___]  필터: [OPAL적용▾][정렬:갱신▾]  │  ai-framework            ●적용 │
│ ┌─────────────────────────────────────┐ │  /Volumes/…/ai-framework  📋   │
│ │ ● ai-framework      OPAL ✅  태스크3 │◀│ ┌───────────────────────────┐ │
│ │   /…/ai-framework        갱신 2분전  │ │ │[개요][PM프로필][문서][스택]│ │ ← Tabs
│ ├─────────────────────────────────────┤ │ └───────────────────────────┘ │
│ │ ○ ai-auto-content   미적용 ⚪        │ │  PM 프로필                     │
│ │   /…/ai-auto-content   구버전        │ │   역할 / 페르소나 / 금지사항   │
│ ├─────────────────────────────────────┤ │  ─────────────────             │
│ │ ○ ai-product-detail 미적용 ⚪        │ │  기술 스택  [badge][badge]…   │
│ └─────────────────────────────────────┘ │  문서  ▸PROJECT ▸ARCH ▸CONV   │
│  도입 현황: 적용 1 / 미적용 6 [progress] │   (클릭→마크다운 뷰어 Drawer)  │
└─────────────────────────────────────────┴───────────────────────────────┘
```

| 영역 | shadcn 매핑 | 데이터 소스 |
|------|------------|------------|
| 좌: 프로젝트 목록 | `item` 리스트(또는 `data-table`) + `badge`(적용/미적용) + `input` 검색 + `select` 필터 | 프로젝트 스캐너(R-1) |
| 도입 현황 요약 | `progress` + 비율 라벨 (또는 `chart-radial-text`) | 적용/미적용 카운트 |
| 우: 상세 패널 | `resizable` 분할 + `tabs`(개요/PM프로필/문서/스택) | AGENT.md · PROJECT.md |
| PM 프로필 | `card` + `avatar` + 정의 리스트 | .opal/AGENT.md 파싱 |
| 기술 스택 | `badge` 그룹 | PROJECT.md / code-scan |
| 문서 링크 | `item` 행 → 클릭 시 마크다운 뷰어(`drawer`) | PROJECT/ARCHITECTURE/CONVENTIONS.md |

> 비OPAL("미적용") 프로젝트는 회색 처리 + "OPAL 미적용" `badge`, 상세는 경로만. C(도입 현황 맵)의 가치 강조.

### (3) 태스크 (칸반) — 읽기 전용 보드 + 산출물 뷰어 Drawer

```
태스크   (ai-framework)        보기:[칸반|테이블]  필터:[모드▾][검색__]   읽기전용 🔒
┌──────────────┬──────────────┬──────────────┬──────────────┐
│ ⬜ 대기 (2)  │ 🔄 진행중 (3)│ ❌ 블로킹 (1)│ ✅ 완료 (12) │ ← 컬럼 = 상태
├──────────────┼──────────────┼──────────────┼──────────────┤
│ ┌──────────┐ │ ┌──────────┐ │ ┌──────────┐ │ ┌──────────┐ │
│ │021 콘솔   │ │ │020 아키텍 │ │ │019 README │ │ │018 …      │ │
│ │ opd  ▓▓░ 60%│ │opi ▓▓▓ 80%│ │ opd ▓░░ 30%│ │ ✅ 100%   │ │ ← 카드
│ │ EXECUTE   │ │ │ ARCH      │ │ │ ⚠ blocked │ │           │ │
│ └──────────┘ │ └──────────┘ │ └──────────┘ │ └──────────┘ │
│ ┌──────────┐ │ ┌──────────┐ │              │   …          │
│ │005 게이트 │ │ │…         │ │              │              │
│ └──────────┘ │ └──────────┘ │              │              │
└──────────────┴──────────────┴──────────────┴──────────────┘
        ▲ 카드 클릭 → 우측 Drawer 슬라이드
┌─────────────────────────────────────────── Drawer/Sheet ──┐
│ 021 OPAL Console            opd · semi-agentic  [×]        │
│ 파이프라인 단계 현황                                       │
│  ✅ANALYSIS → 🔄PLAN → ⬜EXECUTE → ⬜VERIFY → ⬜DONE       │ ← stepper
│  ─────────────────────────────────────────                │
│  [TASK.md][PLAN.md][DONE.md][WIREFRAME.md]  ← Tabs         │
│  ┌───────────────────────────────────────┐               │
│  │  # TASK … (렌더된 마크다운, scroll-area) │               │
│  └───────────────────────────────────────┘               │
└────────────────────────────────────────────────────────────┘
```

| 영역 | shadcn 매핑 | 데이터 소스 |
|------|------------|------------|
| 보기 토글(칸반/테이블) | `toggle-group` | — |
| 컬럼 | flex 컬럼 + 헤더에 `badge` 카운트 + `--status-*` 점 | state.json 상태 그룹핑 |
| 카드 | `card`(밀도형) + `badge`(모드/스킬) + `progress`(진행률) + 단계 라벨 | state.json rows |
| 빈 컬럼 | `empty` 컴포넌트(아이콘 + "태스크 없음") | — |
| 상세 패널 | `drawer`(또는 우측 `sheet`) | — |
| 단계 스테퍼 | 커스텀(`separator`+상태 점) 또는 가로 `item` | state.json 단계별 상태 |
| 산출물 뷰어 | `tabs`(파일별) + `scroll-area` + 마크다운 렌더 + `skeleton` 로딩 | tasks/*/*.md |

칸반 상세 설계는 §4 참조.

### (4) 메모리 — 카테고리 리스트/필터 + 히스토리 타임라인

```
메모리   (ai-framework)
┌───────────────────────────────────┬──────────────────────────────┐
│ 검색[____]  카테고리:[전체▾]      │  작업 히스토리                │
│ ┌───────────────────────────────┐ │  ┌──────────────────────────┐│
│ │#feedback 배포 경계 금지        │ │  │ ● 2026-06-15 021 콘솔 …   ││
│ │  ~/.opal 직접 편집 금지…       │ │  │ │ 2026-06-14 020 아키 …    ││
│ ├───────────────────────────────┤ │  │ ● 2026-06-13 019 README …││ ← 타임라인
│ │#feedback 권고 후 진행 선호     │ │  │ │ 2026-06-12 …             ││   (item + 좌측 라인)
│ │  AskUserQuestion보다 권고안…   │ │  │ ●                         ││
│ └───────────────────────────────┘ │  └──────────────────────────┘│
│  [태그칩 필터: feedback decision] │                              │
└───────────────────────────────────┴──────────────────────────────┘
```

| 영역 | shadcn 매핑 | 데이터 소스 |
|------|------------|------------|
| 메모리 리스트 | `item` 리스트 + `badge`(카테고리) + `hover-card`(상세 미리보기) | MEMORY.md 인덱스 표 + memory/*.md frontmatter |
| 카테고리/태그 필터 | `select` + `toggle-group`(태그 칩) + `input` 검색 | frontmatter tags |
| 작업 히스토리 | 커스텀 타임라인(`item` + 좌측 `--border` 라인 + 상태 점) + `scroll-area` | MEMORY.md 작업 히스토리 표 |
| 메모리 상세 | 클릭 → `drawer` 마크다운 뷰어 | memory/*.md |

### (5) 브레인 — 지식 그래프 + 검색 + lint + 페이지 뷰어

`resizable` 3분할: 좌(검색/리스트) · 중(그래프) · 우(페이지 뷰어). 좁은 화면에선 탭 전환.

```
브레인   (ai-framework)                          lint: ⚠ 2 경고
┌──────────────┬───────────────────────────┬──────────────────────┐
│ 검색[_____]  │   지식 그래프 (related)    │ deploy-boundary       │
│ 페이지 (24)  │        ○─────○            │ type: convention      │
│ ▸ deploy-…   │       ╱│      │            │ tags: deploy, rule    │
│ ▸ state-tool │      ○ ○──────○ ●stale    │ ──────────────────    │
│ ▸ brain-tool │       ╲│     ╱             │ # 배포 경계           │
│ ▸ …          │        ○────○             │ ~/.opal 직접편집 금지 │
│ ──────────── │   (노드=페이지, 선=related)│ (마크다운, scroll)    │
│ ⚠ lint 경고  │   노드색 = type, ⚠=stale  │ related: state-tool…  │
│ • 고아 페이지2│                           │  (클릭→그래프 하이라이트)│
│ • 깨진 링크 1 │                           │                       │
└──────────────┴───────────────────────────┴──────────────────────┘
```

| 영역 | shadcn 매핑 | 데이터 소스 |
|------|------------|------------|
| 페이지 검색/리스트 | `input`(`command` 연동) + `item` 리스트 + `badge`(type) | brain search + index.md |
| 지식 그래프 | **PLAN에서 라이브러리 확정(U-6)** — 컨테이너는 `card`. 노드=페이지(색=type), 엣지=related, ⚠아이콘=stale | brain pages frontmatter `related` |
| lint 경고 패널 | `card` + `alert`/`item` 리스트(고아·깨진 링크·stale) | brain-tool lint JSON |
| 페이지 뷰어 | `tabs`(렌더/원문) + `scroll-area` + frontmatter를 `badge` 칩으로 + related 링크(클릭→그래프 포커스) | brain pages/*.md |

> 그래프는 1차 핵심 가치이므로 자리는 확정하되, force-graph 라이브러리(react-force-graph / cytoscape / reactflow)는 PLAN 결정. 초기엔 노드 클릭→우측 뷰어 연동 + 호버 하이라이트만.

### (6) 환경 (doctor) — 체크 결과 시각화

```
환경 (doctor)        대상:[전 프로젝트▾]   전체: ✅ 정상  (1 ⚠ 경고)
┌────────────────────────────────────────────────────────────────┐
│ 의존성                                                          │
│  ✅ Node.js 20.x   ✅ Python 3.12 venv   ✅ git   ⚠ jq 미설치   │ ← 체크리스트
├────────────────────────────────────────────────────────────────┤
│ MCP 서버                                                        │
│  ✅ shadcn   ✅ context7   ✅ playwright   ✅ sequential-thinking│
├────────────────────────────────────────────────────────────────┤
│ OPAL 부트스트래퍼 / 도구                                        │
│  ✅ ~/.opal/AGENT.md   ✅ state-tool   ✅ brain-tool   ✅ code-scan│
└────────────────────────────────────────────────────────────────┘
```

| 영역 | shadcn 매핑 | 데이터 소스 |
|------|------------|------------|
| 전체 상태 헤더 | `badge`(정상/경고/실패) + 요약 | doctor 집계 |
| 카테고리 그룹 | `card` 섹션(의존성/MCP/부트스트래퍼) + `accordion`(상세 펼침) | opal-cli doctor 파싱 |
| 개별 체크 | `item` 행 + 상태 아이콘(✅⚠❌) + `tooltip`(버전/경로/해결법) | doctor 텍스트 파싱 |
| 실패 항목 | `alert`(destructive) + 권장 조치 텍스트 | doctor |

---

## 4. 칸반 보드 상세 (R-6)

### 4.1 컬럼 정의 + 근거 (U-3 권고)

U-3은 "프로젝트 보드(태스크를 상태 컬럼에) vs 태스크 보드(단계를 컬럼에)"의 택1/병행. **권고: 1차는 "상태 컬럼" 보드 1종**으로 단순하게.

| 컬럼 | 상태 매핑(state.json) | 근거 |
|------|----------------------|------|
| ⬜ 대기 | 시작 전 / 미착수 | 백로그 가시화 |
| 🔄 진행중 | 진행 단계 존재(실행/검증 등) | 현재 작업 초점 |
| ❌ 블로킹 | blocked 마커 | 즉시 주의 — 별도 컬럼으로 분리(대시보드 알림과 연동) |
| ✅ 완료 | DONE | 완료 이력(접힘/페이지네이션로 밀도 관리) |

- "단계를 컬럼에" 보드는 **태스크 상세 Drawer의 가로 스테퍼**(§3-(3))로 대체 → 화면 1개로 두 관점 모두 충족.
- 컬럼 헤더: 라벨 + `badge`(카운트) + `--status-*` 점. 완료 컬럼은 기본 접힘 옵션.

### 4.2 카드 anatomy

```
┌────────────────────────────┐
│ 021 OPAL Console        ⋯  │ ← 태스크 ID + 제목 (truncate), ⋯=메뉴(1차: 상세열기만)
│ ▓▓▓▓▓▓░░░░  60%            │ ← progress (진행률)
│ [opd] [semi-agentic]  EXECUTE│ ← badge(스킬) badge(모드) + 현재 단계 라벨
│ ◷ 2분 전 · 📄 4              │ ← 갱신 시각 + 산출물 수 (muted, 작게)
└────────────────────────────┘
```

- 좌측 2px `--status-*` 바 = 상태 즉시 인지. 카드는 `card` + 내부 밀도형 패딩(`p-3`).
- 블로킹 카드: `--status-blocked` 좌측 바 + ⚠ 아이콘 강조.

### 4.3 빈 상태

- 컬럼 비면 `empty` 컴포넌트(흐린 아이콘 + "대기 중 태스크 없음").
- 프로젝트 미선택(컨텍스트=전 프로젝트): 보드 대신 `empty` + "프로젝트를 선택하세요" + 프로젝트 선택 그리드.
- 태스크 0개 프로젝트: `empty` + "아직 태스크가 없습니다".

### 4.4 읽기 전용을 시각적으로 표현하는 방법 (C-6)

1차는 드래그 금지(dnd-kit 의존성은 따라오지만 `disabled`). 읽기 전용 신호:

- 상단 우측 `🔒 읽기 전용` `badge`(상시) + `tooltip`("상태 전환은 2차에서 지원").
- 카드 hover: 드래그 핸들 대신 `cursor-pointer` + 미세 lift(`hover:bg-accent`, `hover:-translate-y-px`) → "클릭=상세".
- `grab`/`grabbing` 커서 미사용. 드롭존 하이라이트 없음.
- 카드 클릭 = Drawer 상세 오픈(드래그가 아니라 클릭이 주 동작임을 인터랙션으로 학습시킴).

> **2차 확장 지점**: dnd-kit 드래그 활성 → 상태 전환 시 state-tool `advance/mark` run.sh 래핑 호출(쓰기 도구 경유 강제, TASK §4 제약).

---

## 5. 반응형 / 접근성

### 5.1 반응형 (데스크톱 우선)

| 폭 | 동작 |
|----|------|
| ≥1280 (기본) | 사이드바 펼침 + 분할 패널(`resizable`) 정상 |
| 1024~1280 | 사이드바 아이콘 축소(`sidebar-07`), 상세는 분할 유지 |
| 768~1024 | 사이드바 오프캔버스(`sheet`), 상세 패널 → `drawer` 오버레이로 전환, 칸반 가로 스크롤 |
| <768 | 단일 컬럼, 네비=하단/햄버거, 칸반=세로 아코디언(상태별 `collapsible`), 브레인 그래프=탭 전환 |

- 분할 뷰(`resizable`)는 좁아지면 자동으로 단일 + `drawer`로 폴백.

### 5.2 접근성 / 키보드

- shadcn = Radix 기반 → 포커스 트랩/ARIA 기본 확보. `--ring` 포커스 링 항상 가시.
- ⌘K / Ctrl+K → `CommandDialog`(전역 점프). `Kbd`로 단축키 힌트 노출.
- 칸반 카드: `tabIndex` + Enter=상세 열기, 화살표=카드 이동(읽기 전용이라 포커스 이동만).
- Drawer/Sheet: Esc 닫기, 포커스 복원.
- 컬러만으로 상태 구분 금지 → 항상 아이콘(✅⚠❌)+라벨 병기(색맹 대응).
- 다크/라이트 모두 대비 AA 충족하도록 토큰 명도 검증(PLAN 체크).

---

## 6. 세련됨을 만드는 디테일

### 6.1 마이크로 인터랙션

- 네비 active: 좌측 2px primary 인디케이터 + 배경 `--accent` 페이드(150ms).
- 카드/행 hover: `bg-accent` + 미세 lift(translate-y -1px), 그림자 대신 border 강조.
- 숫자 메트릭: 진입 시 count-up 애니메이션(짧게), `tabular-nums`로 정렬.
- 페이지 전환: 콘텐츠 영역만 fade/slide(60ms) — 셸 고정으로 안정감.
- 토스트(`sonner`): "스캔 완료 · 7개 프로젝트" 등 비차단 피드백.

### 6.2 상태 색상 체계 (전 화면 단일 규칙)

| 마커 | 의미 | 토큰 | 적용처 |
|------|------|------|--------|
| ⬜ | 대기/미착수 | `--status-todo` | 칸반·스테퍼·뱃지 |
| 🔄 | 진행중 | `--status-running` | 동일 |
| ✅ | 완료/정상 | `--status-done` | 칸반·doctor·스테퍼 |
| ❌ | 블로킹/실패 | `--status-blocked` | 칸반·doctor·알림 |
| ⚠ | stale/경고 | `--status-stale` | brain lint·알림·doctor |

> 이 매핑이 대시보드 알림·칸반·타임라인·브레인·doctor 전부에서 동일하게 적용 = 시스템 일관성(세련됨의 근원).

### 6.3 로딩 / 스켈레톤

- 카드·테이블·차트 로드 중 `skeleton`(레이아웃 시프트 0).
- 데이터 재수집(상단 새로고침): 인라인 `spinner` + 영역별 skeleton(전체 화면 블로킹 금지).
- 마크다운 뷰어 fetch: skeleton 단락.

### 6.4 빈 상태 일러스트 방향

- `empty` 컴포넌트 기반, 단색 lucide 아이콘(예: 프로젝트 없음=`folder-search`, 태스크 없음=`inbox`, brain 비어있음=`brain-circuit`) + 1줄 설명. 과한 일러스트 금지(개발자 도구 톤).
- 비OPAL 프로젝트만 있을 때: "OPAL 미적용 프로젝트만 발견됨" + (2차 확장 지점: `opal init` 안내 — 1차는 텍스트만).

### 6.5 기타 디테일

- 경로·ID·frontmatter는 mono 폰트 + 클릭 복사(`tooltip` "복사됨").
- `hover-card`로 프로젝트/메모리/brain 항목 미리보기(클릭 전 컨텍스트).
- 1px 헤어라인 + 미세 elevation = Linear/Vercel 밀도감.

---

## 7. 주요 shadcn 컴포넌트 / 블록 매핑 요약

| 화면/영역 | shadcn 블록·컴포넌트 |
|-----------|---------------------|
| 앱 셸 | `sidebar-07` + `sidebar-16` (Provider/Inset/Trigger), `breadcrumb`, `command`(⌘K), `kbd` |
| 대시보드 | `dashboard-01`(section-cards), `card`, `badge`, `chart-area-interactive`, `chart-pie-donut-text`, `toggle-group`, `item`, `data-table`(tanstack) |
| 프로젝트 | `item`/`data-table`, `resizable`, `tabs`, `card`, `avatar`, `badge`, `progress`/`chart-radial-text`, `input`, `select`, `drawer` |
| 태스크(칸반) | `card`, `badge`, `progress`, `toggle-group`, `empty`, `drawer`/`sheet`, `tabs`, `scroll-area`, `skeleton`, `separator` (드래그=dnd-kit, 1차 비활성) |
| 메모리 | `item`, `badge`, `select`, `toggle-group`, `hover-card`, `scroll-area`, `drawer`, 커스텀 타임라인 |
| 브레인 | `resizable`, `input`/`command`, `item`, `badge`, `tabs`, `scroll-area`, `card`, `alert` + (그래프 라이브러리 PLAN 확정) |
| 환경 | `card`, `accordion`, `item`, `badge`, `alert`, `tooltip` |
| 공통 | `dropdown-menu`, `tooltip`, `skeleton`, `spinner`, `sonner`, `separator`, `scroll-area`, `button`, `theme(다크/라이트)` |

---

## 8. PLAN으로 넘길 미해결/확정 필요 (와이어프레임 관점)

- **U-6 그래프 라이브러리** — 브레인 지식 그래프(react-force-graph / cytoscape / reactflow 중). 와이어프레임은 배치/연동만 확정, 구현 라이브러리는 미정.
- **U-3 칸반 컬럼** — 본 와이어프레임 권고(상태 4컬럼 + 단계는 Drawer 스테퍼). 캡틴 확정 필요.
- **OPAL 시그니처 컬러** — `--primary` hue(violet 권고 vs teal). 캡틴 취향 확정.
- **U-4 실시간 갱신** — 1차는 수동 새로고침(상단 버튼) 권고. 폴링/SSE는 2차.
- 폰트(Geist vs Inter/JetBrains) 최종 선택.
