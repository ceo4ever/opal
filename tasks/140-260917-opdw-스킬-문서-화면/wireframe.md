# OPAL Docs 스킬 문서 화면 — 와이어프레임

> 작성일: 2026-09-17 | 작성자: AI | 버전: v1.0

## 1. 서비스 개요

- **서비스명**: OPAL Console — OPAL Docs
- **서비스 유형**: 기존 로컬 관리 대시보드 안의 읽기 전용 문서 카탈로그
- **대상 사용자**: 적합한 `//` 스킬을 찾는 신규 사용자, 호출 규격·파이프라인을 확인하는 숙련 사용자, 레지스트리 완전성을 점검하는 OPAL 유지보수자
- **핵심 사용자 과업**:
  1. 이름·alias·설명·자연어 용도로 스킬을 찾는다.
  2. 파일럿·독립·오퍼레이터·내부 단계와 도메인으로 후보를 좁힌다.
  3. 공유 가능한 상세 URL에서 호출법, 옵션, 예시, 파이프라인과 관련 스킬을 읽는다.
  4. 터미널 프롬프트 문자가 없는 명령 예시를 한 번에 복사한다.
- **운영 원칙**: 조회만 제공한다. 실행·설치·소스 수정 액션은 두 화면 모두 제공하지 않는다(C-5).
- **디자인 우선순위**: 현재 OPAL Console AppShell·전역 토큰·Geist typography·`p-6` 페이지 간격·Card/Badge/Alert/Skeleton·Markdown prose/code 스타일을 우선한다. shadcn 문서 레퍼런스는 문서 탐색 정보 구조만 참고하며 별도 테마나 문서 프레임워크를 추가하지 않는다(C-1).

### 1.1 입력 근거와 적용 결정

| 근거 | 관찰 | 화면 결정 |
|---|---|---|
| `TASK.md` AC-1~AC-8, C-1~C-7 | 카탈로그·상세·완전성·상태·배포 요구 | 본 문서의 화면/데이터/상태/추적표로 전부 연결 |
| 현재 `AppShell.tsx` | shadcn Sidebar, 48px TopBar, 7개 전역 메뉴, 모바일 Sheet | 기존 셸에 `OPAL Docs` 1개 메뉴만 추가; 내부 문서 탐색은 콘텐츠 영역에 한정 |
| 현재 `index.css` | `--brand-*`, shadcn semantic token, Geist, dark/light | 모든 색은 기존 토큰만 사용; 신규 hex/독립 색상 금지 |
| 현재 `MarkdownView` | GFM, h1~h3 TOC, prose/table/code 스타일 | 상세 설명/Usage 등은 동일 typography와 코드 표면을 재사용·확장 |
| 제공 이미지 및 shadcn CLI 문서 | 좌측 섹션 탐색, 넓은 본문, code copy, 섹션 앵커 | 상세 데스크톱에 로컬 탐색+본문+sticky TOC; 모바일은 탐색 Sheet와 접이식 TOC |
| Hada 참고 페이지 | 빠르게 훑는 제목·요약·메타 정보 구조 | 목록 카드에서 이름/설명/alias/분류를 상단에 압축 표시 |

## 2. 전체 구조

### 2.1 레이아웃 유형

기존 **AppShell Sidebar + TopBar + Content**를 그대로 사용한다. OPAL Docs는 새로운 전역 레이아웃을 만들지 않는다.

- 데스크톱: 전역 Sidebar(기존) + 콘텐츠. 카탈로그는 단일 열 헤더/필터 + 반응형 카드 그리드, 상세는 콘텐츠 안에서 `문서 탐색 220px / 본문 minmax(0, 760px) / TOC 180px`의 3열이다.
- 태블릿: 상세의 우측 TOC를 본문 상단 Accordion으로 이동하고 `탐색 / 본문` 2열로 축소한다.
- 모바일(`<768px`): 기존 전역 Sidebar는 Sheet 동작을 유지한다. OPAL Docs의 로컬 탐색도 별도 Sheet로 열고, 본문·필터·카드는 1열이다.
- 콘텐츠 최대 폭: 카탈로그 `max-w-7xl`, 상세 `max-w-[1200px]`; 좌우는 `mx-auto`, 페이지 여백 `p-4 sm:p-6`.
- 카드/코드: `border-border`, `bg-card`, `bg-muted`, `rounded-lg`/기존 radius를 사용한다. 상태는 텍스트·아이콘을 함께 써 색에만 의존하지 않는다.

### 2.2 네비게이션 구조

- 기존 전역 네비게이션
  - 대시보드 → `/`
  - 프로젝트 → `/projects`
  - 태스크 → `/tasks`
  - 메모리 → `/memory`
  - 환경 → `/doctor`
  - 프로젝트 브레인 → `/brain`
  - **OPAL Docs** (`BookOpen`) → `/docs/skills` → SCR-001
  - 설정 → `/settings`
- OPAL Docs 로컬 네비게이션
  - 모든 스킬 → `/docs/skills`
  - 그룹별 빠른 탐색: 파일럿 / 독립 / 오퍼레이터 / 내부 단계
  - 최근 상세에서 목록 복귀: URL에 보존된 `q`, `group`, `domain` query를 사용

### 2.3 화면 흐름도와 공유 URL

```text
[전역 Sidebar: OPAL Docs]
             │
             ▼
 SCR-001 카탈로그  /docs/skills?q=&group=&domain=
   │ 검색/필터(클라이언트 URL 동기화)
   │ 카드 클릭 또는 Enter
   ▼
 SCR-002 상세      /docs/skills/:skillId
   │ 예: /docs/skills/opal-pilot-project-build
   │ alias 직접 접근 예: /docs/skills/oppb ── 200 canonical resolve
   │                                      └─ URL은 canonical로 replace 가능
   ├─ 관련 스킬 클릭 → SCR-002(다른 canonical skillId)
   ├─ 목록으로 → history back 또는 보존 query의 SCR-001
   └─ 미존재 alias/name → SCR-002 안의 404 상태 + 목록 링크
```

공유 가능한 상세 식별자는 **canonical name**이다. alias URL도 허용하되 API가 `canonical_name`을 반환하고 프론트가 `/docs/skills/{canonical_name}`으로 `replace`하여 한 스킬에 URL 하나가 남도록 한다. 목록 상태는 query string에 저장해 새로고침·뒤로가기·링크 공유 시 복원한다.

## 3. 화면 목록

| ID | 화면명 | 유형 | 경로 | 메뉴 그룹 | 설명 |
|---|---|---|---|---|---|
| SCR-001 | 스킬 카탈로그 | crud(읽기 전용) | `/docs/skills` | OPAL Docs | 전체 스킬 검색·그룹/도메인 필터·카드 탐색 |
| SCR-002 | 스킬 상세 문서 | detail | `/docs/skills/:skillId` | OPAL Docs | 호출법·옵션·예시·파이프라인·관련 스킬·원본 경로 열람 |

## 4. 화면별 상세 설계

### 4.1 스킬 카탈로그 (SCR-001)

- **유형**: crud(조회 전용)
- **경로**: `/docs/skills?q={text}&group={group}&domain={domain}`
- **진입점**: 전역 Sidebar `OPAL Docs`, 상세의 `모든 스킬` 링크, 공유 URL
- **페이지 제목**: `OPAL Docs`
- **보조 문구**: `목적에 맞는 스킬을 찾고 호출 방법을 확인하세요.`

#### 데스크톱 레이아웃 (≥1024px)

```text
┌─ 기존 OPAL AppShell ──────────────────────────────────────────────────────────┐
│ Sidebar(전역)        │ TopBar(기존 검색/상태/새로고침/테마/설정)               │
│  ...                 ├────────────────────────────────────────────────────────┤
│  ▣ OPAL Docs(active) │ Content p-6 / max-w-7xl                               │
│  설정                │                                                        │
│                      │  OPAL Docs                              [총 55개]       │
│                      │  목적에 맞는 스킬을 찾고 호출 방법을 확인하세요.         │
│                      │                                                        │
│                      │  [⌕ 스킬명, alias, 설명 또는 하고 싶은 일을 검색…]      │
│                      │                                                        │
│                      │  그룹 [전체][파일럿][독립][오퍼레이터][내부 단계]       │
│                      │  도메인 [전체 ▼]                     [필터 초기화]       │
│                      │  "배포 전 보안 점검" 결과 3개                          │
│                      │                                                        │
│                      │  ┌──────────────────────┐ ┌──────────────────────┐      │
│                      │  │ opal-pilot-gc        │ │ op-gc-security       │      │
│                      │  │ //opgc  [파일럿]     │ │ [내부 단계]          │      │
│                      │  │ 보안·컨벤션 점검... │ │ 보안 검사...         │      │
│                      │  │ quality       →      │ │ quality        →     │      │
│                      │  └──────────────────────┘ └──────────────────────┘      │
│                      │  ┌──────────────────────┐ ...                            │
└──────────────────────┴────────────────────────────────────────────────────────┘
```

#### 모바일 레이아웃 (<768px)

```text
┌─────────────────────────────────┐
│ ☰  [기존 TopBar]        상태 ⋮  │
├─────────────────────────────────┤
│ OPAL Docs              총 55개  │
│ 목적에 맞는 스킬을 찾으세요.    │
│                                 │
│ [⌕ 이름·alias·용도 검색...]     │
│ [필터 (2)]        [초기화]      │
│ [파일럿 ×] [quality ×]          │
│ "보안 점검" 결과 3개           │
│                                 │
│ ┌─────────────────────────────┐ │
│ │ opal-pilot-gc        →      │ │
│ │ //opgc [파일럿] [quality]   │ │
│ │ 보안·컨벤션 체크 경량...   │ │
│ └─────────────────────────────┘ │
│ ┌─────────────────────────────┐ │
│ │ op-gc-security ...          │ │
│ └─────────────────────────────┘ │
└─────────────────────────────────┘

[필터 버튼 → bottom Sheet]
┌─────────────────────────────────┐
│ 필터                         ×  │
│ 그룹                           │
│ ○ 전체 ○ 파일럿 ○ 독립 ...    │
│ 도메인                         │
│ [전체 ▼]                       │
│            [초기화] [적용 3]   │
└─────────────────────────────────┘
```

#### 컴포넌트 계층

```text
SkillsCatalogPage
├─ PageHeader
│  ├─ title/description
│  └─ Badge(total)
├─ SkillSearchToolbar
│  ├─ Input(type=search)
│  ├─ ToggleGroup(group, desktop)
│  ├─ Select(domain, desktop)
│  ├─ Button(reset)
│  └─ Sheet(SkillFilters, mobile)
├─ ActiveFilterChips
├─ ResultSummary(aria-live=polite)
└─ SkillCatalogRegion
   ├─ SkillCard[] → Link(canonical detail URL)
   ├─ CatalogSkeleton[]
   ├─ EmptyState
   └─ ErrorState
```

#### 구성 요소

| 영역 | UI 요소 | shadcn 컴포넌트 | 데이터/설명 |
|---|---|---|---|
| header | 제목·설명·전체 건수 | Badge | `meta.total`; 제목은 h1 |
| search | 통합 검색 | Input + Search icon | `q`; name/aliases/description/use_cases를 대소문자 무시 검색 |
| filter | 그룹 필터 | ToggleGroup | `all`, `pilot`, `standalone`, `operator`, `internal-stage`; 단일 선택 |
| filter | 도메인 필터 | Select | API `facets.domains`; `all` 포함 |
| filter-mobile | 필터 Sheet | Sheet, Button, Select, ToggleGroup | 적용 전 임시값, 적용 시 URL/query 갱신 |
| summary | 검색 결과 요약 | 일반 text, Badge | 검색어와 결과 수; `aria-live="polite"` |
| content | 스킬 카드 | Card, Badge | canonical name, 대표 alias, 설명, display group, domain, pipeline 유무 |
| state | 로딩 | Skeleton | 헤더 1 + 필터 1 + 카드 6; 기존 카드와 동일 크기 |
| state | 빈 결과 | Card, Button | `조건에 맞는 스킬이 없습니다`; 검색/필터 초기화 |
| state | API 오류 | Alert, Button | 사용자 메시지 + `다시 시도`; 기술 stack trace 미표시 |

#### 기능 및 인터랙션

| 이벤트 | 동작 | 결과 |
|---|---|---|
| 검색 입력 | 200ms debounce 후 `q` URL 갱신; API 또는 받은 목록 필터 | 이름·alias·설명·자연어 `use_cases` 동시 검색(AC-2) |
| 그룹 선택 | `group` query 갱신 | 해당 display group만 표시 |
| 도메인 선택 | `domain` query 갱신 | 해당 도메인만 표시 |
| 필터 초기화 | `q/group/domain` 제거 | 전체 목록 복원, 검색창 포커스 |
| 카드 클릭/Enter | canonical name으로 이동 | `/docs/skills/:canonicalName`; 목록 query를 location state 또는 back stack에 보존 |
| 다시 시도 | query refetch | 성공 시 카드, 실패 시 동일 오류 상태 |
| 브라우저 뒤/앞 | query string을 상태로 재수화 | 검색/필터/스크롤 위치 복원 |

#### 검색·필터 의미 계약

- `name`: canonical name 및 source frontmatter raw name.
- `aliases`: `oppb` 같은 주 alias와 논리 alias 배열 모두.
- `description`: 레지스트리 설명 + SKILL frontmatter description.
- `use_cases`: SKILL의 트리거 문구, “반드시 사용해야 하는 상황”, “사용 기준/사용 시점”에서 추출한 검색 전용 자연어 문자열. UI 카드에는 필요 시 일치 구문만 보조 표시하며 정규식 원문은 노출하지 않는다.
- `group`: 사용자 관점의 폐쇄 4분류. `pilot`, `standalone`, `operator`, `internal-stage`; `all`은 UI 전용.
- `domain`: 레지스트리 domain 우선, 없으면 group/prefix/dispatch 관계로 결정론 파생. 필터 옵션은 응답 facet에서 생성해 FE 하드코딩을 피한다(C-2).
- 그룹과 도메인은 AND, 검색 대상 필드는 OR로 평가한다.

### 4.2 스킬 상세 문서 (SCR-002)

- **유형**: detail
- **경로**: `/docs/skills/:skillId` (`skillId`는 canonical name 또는 alias)
- **진입점**: 카탈로그 카드, 관련 스킬 링크, 공유 URL 직접 접근
- **본문 원칙**: 섹션 데이터가 없으면 거짓 샘플을 생성하지 않는다. `Quick Start`/`Usage`처럼 핵심인데 추출 불가하면 `이 스킬에는 별도 {섹션명}이 명시되어 있지 않습니다.`로 표시하고, 선택적 섹션은 생략할 수 있다(AC-3).

#### 데스크톱 레이아웃 (≥1024px)

```text
┌─ 기존 OPAL AppShell ─────────────────────────────────────────────────────────────┐
│ Sidebar(전역) │ TopBar(기존)                                                     │
│ ▣ OPAL Docs   ├───────────────────────────────────────────────────────────────────┤
│               │ Content p-6 / centered                                           │
│               │ ┌─DocsNav 220─┬──── Main 0..760 ─────────┬─ On this page 180 ─┐ │
│               │ │ [⌕ 스킬 찾기]│ OPAL Docs / 파일럿       │ Quick Start         │ │
│               │ │ 모든 스킬    │                         │ Usage              │ │
│               │ │ 파일럿       │ opal-pilot-project-build│ Arguments / Options│ │
│               │ │  • OPPB ●    │ 프로젝트 빌드...        │ 사용 시점          │ │
│               │ │ 독립         │ [파일럿][dev] [//oppb]  │ Examples           │ │
│               │ │ 오퍼레이터   │ source: opal/skills/... │ Pipeline           │ │
│               │ │ 내부 단계    │                         │ Related skills     │ │
│               │ │              │ Quick Start             │                    │ │
│               │ │              │ ┌─────────────────────┐ │                    │ │
│               │ │              │ │ //oppb "프로젝트..."│ │                    │ │
│               │ │              │ │              [복사] │ │                    │ │
│               │ │              │ └─────────────────────┘ │                    │ │
│               │ │              │ Usage / Options / ...   │                    │ │
│               │ │              │ Pipeline                │                    │ │
│               │ │              │ [TASK]→[PLAN]→[...]      │                    │ │
│               │ └──────────────┴─────────────────────────┴────────────────────┘ │
└───────────────┴───────────────────────────────────────────────────────────────────┘
```

#### 모바일 레이아웃 (<768px)

```text
┌─────────────────────────────────┐
│ ☰  [기존 TopBar]        상태 ⋮  │
├─────────────────────────────────┤
│ [문서 탐색]   OPAL Docs / ...   │
│                                 │
│ opal-pilot-project-build        │
│ 프로젝트 빌드 오케스트레이터    │
│ [파일럿] [dev] [//oppb]         │
│ source: opal/skills/...         │
│                                 │
│ [이 페이지에서 보기 (8) ▼]     │
│                                 │
│ Quick Start                     │
│ ┌─────────────────────────────┐ │
│ │ //oppb "프로젝트 빌드"     │ │
│ │                    [복사]   │ │
│ └─────────────────────────────┘ │
│ Usage                           │
│ ... (세로 스크롤)              │
│ Pipeline                        │
│ [P0]→[P1]→[P2]→[P3]→[P4]→[P5]│
└─────────────────────────────────┘

[문서 탐색 → left Sheet]
┌─────────────────────────────────┐
│ 스킬 문서                    ×  │
│ [⌕ 스킬 찾기]                  │
│ [모든 스킬]                    │
│ 파일럿                         │
│  • opal-pilot-project-build ●  │
│ 내부 단계                      │
│  • op-oppb-project-slice       │
└─────────────────────────────────┘
```

#### 컴포넌트 계층

```text
SkillDetailPage
├─ DocsNavigation
│  ├─ Input(search shortcut)
│  ├─ Link(all skills)
│  └─ ScrollArea(GroupedSkillLinks)
├─ MobileDocsNavigation → Sheet(DocsNavigation)
├─ SkillArticle
│  ├─ Breadcrumb
│  ├─ SkillHeader(title, description, badges, source path)
│  ├─ MobileToc → Accordion
│  ├─ DocSection(Quick Start)
│  ├─ DocSection(Usage)
│  ├─ DocSection(Arguments / Options)
│  ├─ DocSection(사용 시점)
│  ├─ DocSection(Examples → CopyableCodeBlock[])
│  ├─ DocSection(Pipeline → PipelineSteps)
│  └─ DocSection(Related skills → RelatedSkillCard[])
├─ DesktopToc → nav(sticky)
├─ DetailSkeleton
├─ DetailErrorState / SourceMissingState
└─ NotFoundState
```

#### 구성 요소

| 영역 | UI 요소 | shadcn 컴포넌트 | 데이터/설명 |
|---|---|---|---|
| local-nav | 그룹별 스킬 탐색 | ScrollArea, Input, Button/Link, Sheet | 현재 스킬 `aria-current=page`; 전역 Sidebar와 시각 계층 구분 |
| header | breadcrumb·제목·설명 | Breadcrumb(미설치 시 링크+Separator), Badge | title=`canonical_name`; aliases, group, domain |
| header | 원본 경로 | Button variant link 또는 text | `source.path`; 경로 복사만 허용, 파일 쓰기/열기 액션 없음 |
| toc | 페이지 목차 | nav / Accordion | 실제 존재하는 섹션만; anchor URL hash 동기화 |
| body | Quick Start | CopyableCodeBlock | 가장 짧고 유효한 `//alias ...` 예시. `$`, `>`, regex anchor 미포함(C-4) |
| body | Usage | MarkdownView 스타일 prose | 호출 syntax; 인라인 code는 기존 muted 스타일 |
| body | Arguments / Options | Table | name, type/value, required, default, description; 정보 없으면 명시적 없음 |
| body | 사용 시점 | MarkdownView 스타일 prose | triggers/use criteria를 사용자 문장으로 정리 |
| body | 복사 가능한 예시 | Card/Code block, Button, Tooltip | 예시별 복사 버튼; 복사 결과 live region |
| body | 파이프라인 | Badge + Separator 또는 가로 ScrollArea | 구조화 steps. 모바일은 가로 스크롤, 텍스트 대체 제공 |
| body | 관련 스킬 | Card/Link, Badge | `related_skills`; 클릭 시 canonical 상세 이동 |
| state | 로딩 | Skeleton | local nav, title, code, 본문 블록 형태 보존 |
| state | 일반 조회 오류 | Alert, Button | 다시 시도 + 모든 스킬 링크 |
| state | 원본 부재 | Alert variant destructive | 메타는 표시 가능; 본문 영역에 `원본 SKILL.md를 읽을 수 없습니다`, source path, 재시도 |
| state | 404 | Card/Alert, Button | `스킬을 찾을 수 없습니다`; 요청 식별자 표시; `/docs/skills` 이동 |

#### 기능 및 인터랙션

| 이벤트 | 동작 | 결과 |
|---|---|---|
| 공유 URL 직접 진입 | `GET /api/docs/skills/:skillId` | canonical/alias 해석 후 상세 렌더; 미존재는 전용 404 |
| alias로 진입 | 응답 canonical 확인 후 route replace | 중복 페이지 없이 canonical URL 유지(AC-5) |
| 섹션 목차 클릭 | 해당 id로 smooth scroll, hash 갱신 | 키보드 포커스도 대상 heading으로 이동 |
| 복사 클릭 | `navigator.clipboard.writeText(example.command)` | 아이콘/라벨이 2초간 `복사됨`; `aria-live=polite` 알림 |
| 복사 실패 | fallback 없이 실패 피드백 | `복사 실패 — 명령을 직접 선택하세요`; 내용 선택 가능 유지 |
| 관련 스킬 클릭 | canonical route 이동 | 페이지 scroll top, 새 상세 로드 |
| 목록으로 클릭 | 이전 목록 query 복원 | 카탈로그 검색/필터와 가능하면 스크롤 위치 복원 |
| 문서 탐색 열기(모바일) | Sheet open | 첫 포커스 검색창, 닫기 시 trigger로 포커스 복귀 |

#### 상세 콘텐츠 표시 규칙

1. **제목/설명/분류**: canonical name을 h1, 원문 설명을 lead, `display_group`·`domain`·aliases를 Badge로 표시한다.
2. **Quick Start**: `examples[].kind=quick-start` 우선, 없으면 안전하게 파생 가능한 alias/name 호출 한 줄. 인자를 추정해야 한다면 파생하지 않고 없음 문구를 표시한다.
3. **Usage**: SKILL의 명시 Usage/입력 형식/호출 형식에서 추출한다. 원문 Markdown을 허용하되 sanitize된 데이터만 렌더한다.
4. **Arguments/Options**: 구조화된 표를 사용한다. 적용되지 않으면 `별도 인자 또는 옵션이 없습니다.`라고 표시한다.
5. **사용 시점**: frontmatter triggers와 본문의 사용 기준을 사람이 읽는 문장으로 제공한다. 정규식은 검색 인덱스에만 쓰고 사용자 대면 예시에는 노출하지 않는다.
6. **예시**: source fenced code 중 사용자 호출 예시만 포함한다. 셸 프롬프트 `$`/`>`는 제거하고 명령 자체는 변경하지 않는다.
7. **파이프라인**: registry/pipeline.json의 구조화 정보가 있을 때만 단계 Badge를 표시한다. 없으면 섹션을 생략하거나 `정의된 파이프라인이 없습니다.`로 명시한다.
8. **관련 스킬**: `dispatched_by`, pipeline 단계, 본문의 명시 링크를 canonical resolver로 정규화한 뒤 중복 제거한다.
9. **원본 경로**: 저장소 기준 상대경로를 표시한다. 배포본 절대경로와 로컬 사용자 홈은 노출하지 않는다.

## 5. 데이터·API 계약

### 5.1 읽기 전용 라우트

| Method | Route | 용도 | 쓰기/실행 |
|---|---|---|---|
| GET | `/api/docs/skills?q=&group=&domain=` | 정규화된 카탈로그 + facet 조회 | 없음 |
| GET | `/api/docs/skills/{skill_id}` | canonical name 또는 alias 상세 조회 | 없음 |

백엔드 라우터는 기존 FastAPI 앱에 읽기 전용 GET으로만 추가한다. `skill-registry`, source `SKILL.md`, 선택적 `pipeline.json`을 읽되 설치·실행·수정 명령은 호출하지 않는다. TTL/mtime 캐시를 사용할 경우 레지스트리와 원본 파일 변경 시 무효화한다.

### 5.2 목록 응답 계약

```ts
type SkillDisplayGroup = "pilot" | "standalone" | "operator" | "internal-stage";

interface SkillCatalogResponse {
  items: SkillCatalogItem[];
  meta: { total: number; filtered: number; query: string };
  facets: {
    groups: Array<{ value: SkillDisplayGroup; label: string; count: number }>;
    domains: Array<{ value: string; label: string; count: number }>;
  };
}

interface SkillCatalogItem {
  canonical_name: string;
  source_name: string;
  aliases: string[];
  description: string;
  use_cases: string[];
  display_group: SkillDisplayGroup;
  registry_group: string;
  domain: string | null;
  pipeline_summary: string | null;
  source_path: string;
}
```

### 5.3 상세 응답 계약

```ts
interface SkillDetailResponse extends SkillCatalogItem {
  resolved_from: { kind: "canonical" | "alias"; value: string };
  quick_start: ExampleBlock | null;
  usage_markdown: string | null;
  arguments: Array<{
    name: string;
    type: string | null;
    required: boolean | null;
    default: string | null;
    description: string;
  }>;
  options: Array<{
    name: string;
    type: string | null;
    required: boolean | null;
    default: string | null;
    description: string;
  }>;
  when_to_use_markdown: string | null;
  examples: ExampleBlock[];
  pipeline: null | {
    summary: string;
    steps: Array<{ id: string; label: string; kind: string | null }>;
  };
  related_skills: Array<{
    canonical_name: string;
    label: string;
    relation: "dispatches" | "dispatched-by" | "uses" | "related";
  }>;
  source: {
    path: string;
    available: boolean;
    content_hash: string | null;
  };
}

interface ExampleBlock {
  id: string;
  label: string;
  language: "text" | "bash";
  command: string; // 프롬프트 문자 없는 복사 원문
  kind: "quick-start" | "example";
}
```

### 5.4 오류 계약

```json
{
  "error": {
    "code": "skill_not_found | registry_unavailable | parse_error",
    "message": "사용자에게 표시할 안전한 메시지",
    "skill_id": "요청값 또는 null",
    "retryable": false
  }
}
```

| HTTP | code | 화면 처리 |
|---|---|---|
| 404 | `skill_not_found` | SCR-002 404 상태; 목록 이동 제공 |
| 500 | `registry_unavailable` | 목록/상세 오류 상태; 다시 시도 |
| 500 | `parse_error` | 해당 원본 경로와 일반 메시지만 표시; stack/path 절대값 비노출 |

본문 원본 부재는 오류 응답이 아니라 200 성공 응답의 `source.available=false`로 표현한다(§5.3). 가능한 메타는 유지하고 본문 영역에 원본 부재 Alert를 표시한다.

빈 목록은 오류가 아니다. 전체 소스 집합 자체가 0개이면 `아직 문서화된 스킬이 없습니다`, 검색 결과만 0개이면 `조건에 맞는 스킬이 없습니다`로 구분한다.

## 6. 레지스트리 완전성 및 canonical 정규화

### 6.1 수집·대조 알고리즘

```text
source set
  = glob(opal/skills/*/SKILL.md) ∪ glob(skills/*/SKILL.md)
  → 각 폴더명, frontmatter.name, triggers, description 읽기
  → canonical resolver 적용

registry set
  = opal-skills-registry.json groups[*][*]
  → name/alias/paths/dispatched_by/pipeline/domain 읽기

semantic missing
  = canonical(source set) - canonical(registry set)
완료 조건: semantic missing == []
```

- canonical key의 기본은 실제 스킬 폴더명이다.
- 레지스트리 `paths`의 SKILL 폴더가 하나로 해석되면 그 폴더명을 canonical로 사용한다.
- frontmatter raw name은 `source_name`, 레지스트리 name과 모든 alias는 `aliases`로 합친다.
- 하나의 canonical key로 병합한 뒤 aliases/use_cases/관련 관계를 union하고 카드/상세는 1건만 생성한다.
- 같은 alias가 여러 canonical에 연결되면 자동 선택하지 않고 완전성 검증 실패(`ambiguous_alias`)로 보고한다.

### 6.2 필수 누락·불일치 해소 명세

| source | canonical | 표시 그룹 | alias/관계 | 중복 방지 |
|---|---|---|---|---|
| `opal/skills/opal-pilot-project-build/SKILL.md` | `opal-pilot-project-build` | pilot | `oppb`; P0~P5 pipeline | 신규 레지스트리 1건 |
| `opal/skills/op-oppb-project-slice/SKILL.md` | `op-oppb-project-slice` | internal-stage | dispatched by OPPB, P2 | 신규 레지스트리 1건 |
| `opal/skills/op-oppb-knowledge-finalize/SKILL.md` | `op-oppb-knowledge-finalize` | internal-stage | dispatched by OPPB, P5 | 신규 레지스트리 1건 |
| 폴더 `opal-onboarding`, raw name `onboarding`, registry `opal-onboarding` | `opal-onboarding` | operator | `onboarding`, `onb` | 세 이름을 1 canonical에 merge |
| 폴더 `opal-skill-manager`, raw name `skill-manager`, registry `opal-skill-manager` | `opal-skill-manager` | operator | `skill-manager`, `osm` | 세 이름을 1 canonical에 merge |

OPPB 내부 단계는 사용자 직접 호출 카드처럼 오해되지 않도록 `내부 단계` Badge와 `OPPB가 P2/P5에서 디스패치` 관계를 표시한다(C-3). 검색과 직접 URL에서는 계속 발견 가능해야 하며 숨기지 않는다.

### 6.3 그룹 분류 규칙

1. canonical이 `opal-pilot-*`이면 `pilot`.
2. source root가 `skills/`이면 `standalone`.
3. `dispatched_by`/`stage`가 있거나 registry group이 `op-dev`, `op-task`, `op-gc`, `op-data`, `op-sdd`, `op-brain`, `op-oppb`이면 `internal-stage`.
4. 그 외 사용자 호출 가능한 `opal` 그룹은 `operator`.

분류 충돌 시 더 구체적인 `internal-stage` 관계를 우선하되 검증 로그에 근거를 남긴다. 표시 그룹은 FE 상수가 아니라 API 필드로 제공한다.

### 6.4 구현/배포 검증 표면

- 소스 검사: source SKILL 55개(raw 기준)와 registry canonical을 기계 대조하여 의미상 누락 0건.
- 중복 검사: canonical별 카드 수 1, alias→canonical 단일 매핑.
- 필수 fixture: `oppb`, `op-oppb-project-slice`, `op-oppb-knowledge-finalize`, `onboarding`, `opal-onboarding`, `skill-manager`, `opal-skill-manager`.
- 배포 검사: 프로젝트 소스를 수정한 뒤 install 경유 배포본 `~/.opal/references/opal-skills-registry.json`과 배포된 `~/.opal/skills/*/SKILL.md`를 같은 verifier로 대조한다(C-6, AC-8).
- 화면 회귀: 기존 7개 route와 신규 2개 route, 새로고침 SPA fallback, 모바일 Sheet, 복사 동작을 확인한다(AC-7).

## 7. 상태 명세

| 상태 | SCR-001 | SCR-002 | 접근성/행동 |
|---|---|---|---|
| Loading | 검색/필터 자리 + 카드 Skeleton 6개 | nav/title/code/body Skeleton | `aria-busy=true`; 기존 내용이 있으면 유지하며 재조회 표시만 |
| Empty source | `아직 문서화된 스킬이 없습니다` | 해당 없음 | 원인 설명, 필터 버튼 미표시 |
| Empty result | `조건에 맞는 스킬이 없습니다` + 초기화 | 로컬 nav 검색만 빈 결과 표시 | 검색어 유지, 초기화 가능 |
| Error | Alert `스킬 목록을 불러오지 못했습니다` + 재시도 | Alert `스킬 문서를 불러오지 못했습니다` + 재시도/목록 | `role=alert`; 자동 무한 재시도 금지 |
| Source missing | 해당 카드는 완전성 검증상 비정상 표시 가능 | 헤더 메타 유지 + 원본 부재 Alert | 거짓 본문 생성 금지 |
| 404 | 해당 없음 | 요청 식별자 + `스킬을 찾을 수 없습니다` + 모든 스킬 | document title도 `찾을 수 없음 · OPAL Docs` |
| Copy success/fail | 해당 없음 | 버튼 `복사됨`/오류 문구 | polite live region; 색만으로 상태 전달 금지 |
| Offline/API down | 전역 연결 배지와 목록 Alert 병행 | 전역 연결 배지와 상세 Alert 병행 | `opal-cli console start` 안내는 기존 문구와 정합 |

## 8. 공통 컴포넌트

| 컴포넌트 | shadcn 기반 | 사용 화면 | 설명 |
|---|---|---|---|
| `PageHeader` | Badge | SCR-001, SCR-002 | 기존 Console의 작은 h1 패턴과 설명/메타 |
| `SkillSearchToolbar` | Input, ToggleGroup, Select, Button, Sheet | SCR-001 | URL 동기화 검색·필터 |
| `SkillCard` | Card, Badge | SCR-001 | 전체 카드가 접근 가능한 Link |
| `DocsNavigation` | ScrollArea, Input, Button | SCR-002 | 콘텐츠 내부 로컬 탐색; 모바일 Sheet 재사용 |
| `DocSection` | Separator + 기존 prose | SCR-002 | h2 anchor와 선택적 본문 |
| `CopyableCodeBlock` | Card, Button, Tooltip | SCR-002 | 기존 muted code 스타일 + 복사 상태 |
| `PipelineSteps` | Badge, Separator, ScrollArea | SCR-002 | 구조화 단계와 텍스트 대체 |
| `QueryStatePanel` | Alert, Button, Skeleton | SCR-001, SCR-002 | 로딩·빈·오류·404 일관 처리 |

## 9. shadcn/ui 매핑 및 설치 범위

| 컴포넌트 | 사용 화면 | 현재 저장소 상태/방침 |
|---|---|---|
| badge | SCR-001, SCR-002 | 기존 재사용 |
| button | SCR-001, SCR-002 | 기존 재사용 |
| card | SCR-001, SCR-002 | 기존 재사용 |
| input | SCR-001, SCR-002 | 기존 재사용 |
| select | SCR-001 | 기존 재사용 |
| sheet | SCR-001, SCR-002 | 기존 재사용; 모바일 탐색/필터 |
| skeleton | SCR-001, SCR-002 | 기존 재사용 |
| alert | SCR-001, SCR-002 | 기존 재사용 |
| scroll-area | SCR-002 | 기존 재사용 |
| separator | SCR-002 | 기존 재사용 |
| toggle-group | SCR-001 | 기존 재사용 |
| tooltip | SCR-002 | 기존 재사용 |
| accordion | SCR-002 | 기존 재사용; 모바일 TOC |
| breadcrumb | SCR-002 | 미설치 시 기존 Button/Separator 조합 우선; 새 의존성 설치가 필요하면 shadcn 소스 컴포넌트만 추가 |

외부 문서 런타임 의존성은 추가하지 않는다. 별도 설치 명령은 원칙적으로 없으며 현재 저장소 컴포넌트를 우선 조합한다(C-1).

## 10. 접근성 및 반응형 세부

- 페이지마다 h1은 하나, 본문 섹션은 h2, 하위 항목은 h3 순서를 지킨다.
- 검색 Input에는 보이는 Label 또는 `aria-label="스킬 검색"`; 결과 영역은 `aria-live="polite"`.
- 카드 전체를 단일 Link로 만들고 중첩 interactive 요소를 두지 않는다. `focus-visible:ring-2 ring-ring`을 사용한다.
- 모든 아이콘 전용 버튼은 접근 가능한 이름을 갖는다: `필터 열기`, `예시 복사`, `문서 탐색 열기`, `다시 시도`.
- Badge의 그룹/상태는 텍스트를 포함하며 색만으로 구분하지 않는다.
- Sheet/Accordion의 shadcn focus trap·Escape·trigger focus return을 유지한다.
- 목차 이동 후 heading에 `tabIndex=-1`로 프로그램 포커스를 보내고 hash를 갱신한다. `scroll-margin-top`은 TopBar 높이 이상으로 둔다.
- 코드 블록은 가로 스크롤 가능하고 command는 selectable text다. 복사 실패해도 수동 복사가 가능하다.
- 터치 대상은 최소 40×40px, 모바일 카드 간격 12px 이상, 본문 양옆 padding 16px 이상.
- `prefers-reduced-motion`에서는 smooth scroll을 사용하지 않는다.
- 데스크톱 상세의 local nav와 TOC만 sticky이며, AppShell의 주 스크롤 컨테이너 안에서 겹치지 않게 `top-4`를 사용한다.
- 긴 canonical name/source path는 `overflow-wrap:anywhere`, 파이프라인은 가로 ScrollArea를 사용해 뷰포트를 밀지 않는다.

## 11. 구현 추적표

| 요구 | 화면/계약 반영 | 검증 관점 |
|---|---|---|
| AC-1 | §2.2 전역 메뉴, §2.3/§3 목록·상세 route | 메뉴 활성 상태, 상세 URL 새로고침·공유 |
| AC-2 | §4.1 검색 대상·그룹 4종·domain 필터 | name/alias/description/use_cases fixture별 결과 |
| AC-3 | §4.2 모든 필수 섹션과 없음 규칙 | 데이터 존재/부재 fixture, 복사 원문 |
| AC-4 | §6 source↔registry canonical 대조, OPPB 3종 | semantic missing 0 |
| AC-5 | §6.2 onboarding/skill-manager 병합 | canonical당 카드 1, alias 동일 상세 |
| AC-6 | §7 loading/empty/error/source missing/404 | 각 state component test |
| AC-7 | §6.4 FE/BE/route 회귀 검증 표면 | build/lint/component/backend test |
| AC-8 | §6.4 install 경유 배포·배포본 누락 0 | 설치본 registry/source verifier |
| C-1 | §1.1, §2.1, §9 기존 AppShell/token/shadcn 재사용 | 신규 외부 runtime/hex 0 |
| C-2 | §4.1 facets, §5 API, §6 파생 알고리즘 | FE metadata hardcode 0 |
| C-3 | §4.1/§6.3 display group, 내부 단계 Badge | 어느 그룹도 누락 0 |
| C-4 | §4.2 example 규칙, `ExampleBlock.command` | `$`, `>`, regex anchor 없는 복사값 |
| C-5 | §1 운영 원칙, §5 GET only | 실행·설치·수정 action/endpoint 0 |
| C-6 | §6.4 소스 수정→install 검증 | `~/.opal` 직접 편집 0 |
| C-7 | §4 모바일 ASCII, §10 접근성 | keyboard/mobile/copy E2E |

## 12. 비범위

- 스킬 실행, 설치, 삭제, 편집 UI
- 원본 `SKILL.md` 전체를 그대로 편집하는 기능
- 전역 ⌘K 검색 구현 또는 기존 TopBar 동작 변경
- 외부 커뮤니티 스킬 카탈로그 통합
- 별도 문서 프레임워크, 검색 엔진, 신규 색상 체계 도입
