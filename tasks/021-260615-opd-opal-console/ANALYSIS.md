# ANALYSIS: OPAL Console — 로컬 OPAL 프로젝트 통합 관리 대시보드 (1차 뷰어)

> 작성일: 2026-06-15
> 입력: TASK.md
> 출력: ANALYSIS.md

---

## 0. 참조 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| R-1 | 기획 | TASK.md | `tasks/021-260615-opd-opal-console/TASK.md` | 작업 목표·요구사항·확정 방향·미확정 사항 |
| R-2 | 설계 | PROJECT.md | `docs/PROJECT.md` | 프로젝트 구조·컴포넌트 레지스트리 |
| R-3 | 설계 | ARCHITECTURE.md | `docs/ARCHITECTURE.md` | 2-레이어 모델·배포 경계·디렉토리 구조 |
| R-4 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | 배포 경계·플랫폼 분기 격리 규칙 |
| R-5 | 소스 | state.schema.json | `~/.opal/tools/state-tool/schema/state.schema.json` | state.json 필드 정의·enum 목록 |
| R-6 | 소스 | state-tool/run.sh | `~/.opal/tools/state-tool/run.sh` | venv Python 호출 방식 |
| R-7 | 소스 | brain-tool/run.sh | `~/.opal/tools/brain-tool/run.sh` | venv Python 호출 방식 |
| R-8 | 소스 | opal-cli/run.sh | `~/.opal/tools/opal-cli/run.sh` | dispatcher 패턴 (신규 서브커맨드 추가 지점) |
| R-9 | 소스 | install-mac.sh | `scripts/install-mac.sh` | install 함수 구조·배포 패턴 |
| R-10 | 소스 | install.ps1 | `scripts/install.ps1` | Windows 동기화 지점 |
| R-11 | 소스 | brain/pages/* | `.opal/brain/pages/concept/*.md` | frontmatter 실제 필드 확인 |
| R-12 | 소스 | MEMORY.md | `.opal/MEMORY.md` | 메모리 인덱스 표 구조·카테고리 |
| R-13 | 소스 | requirements.txt | `opal/tools/requirements.txt` | venv 기설치 패키지 목록 |
| R-14 | 외부 | FastAPI | [PyPI fastapi](https://pypi.org/project/fastapi/) | 최신 버전 0.136.3 (2026-05-23) 확인 |
| R-15 | 외부 | dnd-kit + shadcn | [GitHub](https://github.com/Georgegriff/react-dnd-kit-tailwind-shadcn-ui) | shadcn + dnd-kit 칸반 레퍼런스 구현 |
| R-16 | 외부 | TanStack Query | [TanStack Docs](https://tanstack.com/query/v5/docs/framework/react/guides/does-this-replace-client-state) | 서버 상태 관리 패턴 |
| R-17 | 외부 | ReactFlow | [reactflow.dev](https://reactflow.dev/) | brain 지식 그래프 노드-엣지 시각화 |
| R-18 | 외부 | Recharts 2026 | [LogRocket](https://blog.logrocket.com/best-react-chart-libraries-2026/) | 대시보드 집계 차트 (48.9M weekly npm) |

---

## 1. 기존 코드 분석

### 1.1 관련 파일 목록

이 태스크는 **그린필드** 신규 구현이다. `dashboard/` 디렉토리가 현재 존재하지 않으며 새로 생성한다. 연동 대상 기존 도구 파일은 아래와 같다.

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| `~/.opal/tools/state-tool/run.sh` | venv Python 래퍼 — state_tool.py 실행 | 없음 (읽기 전용) | `run.sh:1-15` |
| `~/.opal/tools/state-tool/schema/state.schema.json` | state.json 스키마 SSOT | 없음 | 전체 파일 |
| `~/.opal/tools/brain-tool/run.sh` | venv Python 래퍼 — brain_tool.py 실행 | 없음 (읽기 전용) | `run.sh:1-14` |
| `~/.opal/tools/opal-cli/run.sh` | CLI dispatcher — 5종 서브커맨드 | **신규 `console` 추가** | `run.sh:109,127` |
| `~/.opal/tools/opal-cli/lib/` | 서브커맨드별 lib 파일 | **`console.sh` 신규** | `run.sh:110-118` |
| `scripts/install-mac.sh` | OPAL 설치 스크립트 | **대시보드 빌드+배포 단계 추가** | `install-mac.sh:1059` |
| `scripts/install.ps1` | Windows 설치 스크립트 | **동기화 필요** | `install.ps1:1-80` |
| `opal/tools/requirements.txt` | Python venv 의존성 | **`fastapi[standard]` 추가** | 전체 파일 |
| `dashboard/` (신규) | FE + BE 소스 루트 | **신규 생성** | `TASK.md:C-4` |

### 1.2 아키텍처 패턴

**현행 OPAL 2-레이어 모델** (`docs/ARCHITECTURE.md §Global Layer / §Project Layer`):

- Global Layer `~/.opal/`: 프레임워크 자산 (스킬·에이전트·도구·venv)
- Project Layer `{프로젝트}/`: 프로젝트별 데이터 (TASK.md·state.json·brain·memory)

**OPAL Console 추가 레이어** (`TASK.md:C-9` — "데몬은 도구 오케스트레이터"):

```
dashboard/                             (소스 SSOT — 프로젝트 루트)
├── frontend/                          React + Vite + shadcn
└── backend/                           FastAPI 데몬 소스
    ├── main.py
    ├── routers/                       6개 화면별 라우터
    ├── adapters/                      OPAL 도구 subprocess 어댑터
    └── parsers/                       마크다운 파서

~/.opal/dashboard-server/              (배포 산출물 — install로만 생성)
├── dist/                              Vite 빌드 산출물
└── backend/                           FastAPI 소스 (venv는 ~/.opal/.venv 공유)
```

### 1.3 의존성 맵

```
FastAPI 데몬
├── adapters/state_adapter.py   → subprocess(run.sh show --format json) → state-tool
├── adapters/brain_adapter.py   → subprocess(run.sh search|lint)        → brain-tool
├── adapters/scan_adapter.py    → subprocess(code-scan.js scan --json)  → Node.js
├── adapters/skill_adapter.py   → subprocess(skill-registry.js list)    → Node.js
├── adapters/doctor_adapter.py  → subprocess(opal-cli doctor)           → Bash
└── parsers/
    ├── memory_parser.py        → 직접 파일 Read + 정규식 (표 파싱)
    ├── brain_parser.py         → 직접 파일 Read + PyYAML frontmatter
    └── state_md_parser.py      → STATE.md 마크다운 표 파싱

React App
└── TanStack Query
    └── fetch /api/{dashboard|projects|tasks|memory|brain|doctor}
        └── FastAPI 라우터 → 어댑터/파서 계층
```

### 1.4 테스트 현황

- `dashboard/` 미존재 — 기존 테스트 없음 (그린필드)
- OPAL 도구 자체 테스트: `~/.opal/tools/state-tool/tests/`, `~/.opal/tools/brain-tool/tests/` (pytest)
- FE 테스트: Vitest 권고 (Vite 생태계 표준)
- BE 테스트: pytest + httpx 권고 (FastAPI testclient)

---

## 2. 외부 조사 결과

### 2.1 데이터 소스 실측 스키마

#### state-tool `show --format json` 스키마

실측 근거: `~/.opal/tools/state-tool/schema/state.schema.json` Read

| 필드 | 타입 | 비고 |
|------|------|------|
| `task_id` | string | `^[0-9]{3}-[0-9]{6}-[a-z]+-.*$` |
| `skill` | enum | `opp\|opd\|opds\|opdw\|opwt\|opgc\|oppd\|opsdd` |
| `mode` | enum | `interactive\|agentic` |
| `current_status` | enum | `in_progress\|done\|blocked\|additional_work\|additional_work_done` |
| `created_at` / `updated_at` | string | `YYYY-MM-DD HH:mm` |
| `rows[].row_id` | integer | 1-based |
| `rows[].stage` | enum | 16종 (TASK·PLAN·EXECUTE·TEST·CLOSE 등) |
| `rows[].status` | enum | `pending\|in_progress\|done\|failed\|na` |
| `rows[].owner` | enum/null | `PM\|worker\|user\|auto` |

#### brain-tool JSON 응답 스키마

실측 근거: `~/.opal/tools/brain-tool/run.sh search "architecture"` 실행

**search 응답**:
```json
{ "ok": true, "command": "search", "query": "...", "total": N,
  "matches": [{ "page": "절대경로", "title": "...", "type": "concept|null",
                "score": N, "snippet": "..." }] }
```

**lint 응답**:
```json
{ "ok": true, "command": "lint", "issues_count": N,
  "issues": [{ "kind": "broken_link|missing_link", "page": "...", "detail": "..." }] }
```

**validate 응답**:
```json
{ "ok": false, "command": "validate", "valid": false, "violations_count": N,
  "violations": [{ "page": "str|null", "rule": "...", "detail": "..." }] }
```

#### brain 페이지 frontmatter 필드

실측 근거: `~/.opal/.venv/bin/python3` + PyYAML 파싱

```yaml
type: concept       # 페이지 타입
title: string       # 제목
tags: [string]      # 태그 목록
sources: [string]   # "doc:path" 또는 "task:NNN" 형식
related: [string]   # 연결 페이지명 (wikilink 제외)
created: YYYY-MM-DD
updated: YYYY-MM-DD
status: draft|published
```

#### skill-registry `list` JSON

실측 근거: `node ~/.opal/tools/skill-registry/skill-registry.js list`

```json
[{ "name": "string", "group": "string", "alias": "string|null",
   "description": "string", "domain": "string|null" }]
```

#### opal-cli `doctor` 텍스트 파싱 전략

실측 근거: `opal-cli doctor` 실행 결과 전체

출력 구조 패턴:
- 섹션 헤더: `\[\d+\/\d+\] (.+)` → 섹션명 추출
- 통과 항목: `^\s+✓ (.+)` → 항목명
- 실패 항목: `^\s+✗ (.+)` → 항목명
- 경고 항목: `^\s+⚠ (.+)` → 항목명
- 판정 라인: `^판정: (.+) \((\d+) ✓, (\d+) ⚠, (\d+) ✗` → 집계

#### MEMORY.md 파싱 대상

실측 근거: `.opal/MEMORY.md` Read

| 파싱 대상 | 위치 | 키 필드 |
|-----------|------|---------|
| 메모리 테이블 | `## 메모리` 섹션 하위 md 표 | 등록일시·카테고리·상태·파일·설명 |
| 히스토리 표 | `## 작업 히스토리 (최대 10개, FIFO)` 하위 | 등록일자·작업·단계·경로·시작·완료 |
| 메타 | `> last_task_number:`, `> 최종 갱신:` | 태스크 번호·갱신 시각 |

#### memory/*.md 메타 구조

실측 근거: `.opal/memory/preferences_default_semi_agentic.md` Read

현행 메모리 파일은 YAML frontmatter 미사용. `# h1 제목` + `> 등록일: ...`, `> 카테고리: ...` 블록쿼트 패턴. 정규식 `^> 키: 값` 추출로 파싱 가능.

### 2.2 데이터 소스 분류 및 화면 매핑

| 소스 | 형식 | 화면 |
|------|------|------|
| `tasks/*/state.json` | JSON (SSOT) | 대시보드·태스크(칸반) |
| `tasks/*/TASK.md`, `PLAN.md`, `DONE.md` | Markdown | 태스크(산출물 뷰어) |
| `.opal/MEMORY.md` | Markdown 표 | 메모리 |
| `.opal/memory/*.md` | Markdown (블록쿼트 메타) | 메모리 |
| `.opal/brain/index.md` | Markdown 위키링크 표 | 브레인 |
| `.opal/brain/pages/*/*.md` | Markdown + YAML frontmatter | 브레인 |
| `docs/PROJECT.md`, `.opal/AGENT.md` | Markdown | 프로젝트 |
| `state-tool show --format json` | JSON | 태스크(파이프라인) |
| `brain-tool search\|lint\|validate` | JSON | 브레인 |
| `skill-registry list` | JSON | 환경 |
| `opal-cli doctor` | Text (파싱 필요) | 환경 |

### 2.3 라이브러리/API 조사

#### FastAPI (U-1 관련)

- 최신 버전: 0.136.3 (2026-05-23) — `pypi.org/project/fastapi/` 실측
- `~/.opal/.venv` 기설치 실측 (`pip list`): starlette 1.0.0, uvicorn 0.42.0, pydantic 2.12.5, sse-starlette 3.3.4
- **FastAPI 본체 미설치** → `requirements.txt`에 `fastapi[standard]>=0.110.0` 추가로 venv 재활용

#### dnd-kit + shadcn/ui

- `@dnd-kit/core` + `@dnd-kit/sortable` — shadcn/ui + Tailwind 조합 레퍼런스 구현 확인 (`github.com/Georgegriff/react-dnd-kit-tailwind-shadcn-ui`)
- 1차(읽기 전용 칸반): DndContext 래핑 + sensors 비활성화로 드래그 불가 상태에서도 구조 유지 → 2차 전환 비용 최소화

#### TanStack Query v5 + Zustand

- 2026 표준 조합: TanStack Query(서버 상태) + Zustand(UI 클라이언트 상태) — `tanstack.com` docs + pkgpulse 2026 조사
- TanStack Query `refetchInterval` 옵션으로 폴링 구현 가능

#### ReactFlow (XyFlow)

- brain `related` 링크 → 노드-엣지 지식 그래프 전담
- XyFlow로 리브랜딩됨, npm `reactflow` 패키지 유효, MIT 라이선스

#### Recharts

- 대시보드 집계 차트(상태 분포, 히스토리 타임라인) 전담
- 48.9M weekly npm — 2026 React 차트 1위 (`blog.logrocket.com/best-react-chart-libraries-2026/`)
- shadcn/ui 공식 차트 블록(chart.tsx)이 Recharts 기반

### 2.4 버전 호환성

| 라이브러리 | 권고 버전 |
|-----------|----------|
| React | 18.x |
| Vite | 5.x |
| shadcn/ui | latest |
| Tailwind CSS | 4.x |
| TypeScript | 5.x |
| @dnd-kit/core + sortable | 6.x |
| TanStack Query | v5 |
| Zustand | 4.x |
| ReactFlow | 11.x (xyflow 12.x) |
| Recharts | 2.x |
| FastAPI | 0.136.x |
| Python venv | 3.14.3 (기설치) |

---

## 3. 영향 범위

### 3.1 직접 영향

| 변경 대상 | 유형 | 내용 |
|-----------|------|------|
| `dashboard/` | 신규 | FE(React+Vite) + BE(FastAPI) 소스 루트 |
| `scripts/install-mac.sh` | 수정 | `install_dashboard()` 신설 + `install_opal()` 호출 추가 (`install-mac.sh:1059`) |
| `scripts/install.ps1` | 수정 | Windows 동기화 |
| `opal/tools/requirements.txt` | 수정 | `fastapi[standard]>=0.110.0` 추가 |
| `opal/tools/opal-cli/run.sh` | 수정 | `console` 서브커맨드 case 추가 (`run.sh:109`) |
| `opal/tools/opal-cli/lib/console.sh` | 신규 | `cmd_console()` — start/stop/status/open |

### 3.2 간접 영향

- `~/.opal/dashboard-server/`: install 실행 시 생성/갱신 (clean_dirs에 추가 필요)
- `~/.opal/.venv`: FastAPI 추가 설치 — starlette·uvicorn 이미 설치, 충돌 여부 사전 검증 필요
- 각 프로젝트의 `tasks/*/state.json`, `.opal/brain/`, `.opal/MEMORY.md`: **읽기 전용** 접근 — 기존 파일 무변경

### 3.3 영향 범위 요약

- [ ] DB 스키마 변경 — 해당 없음
- [x] API 인터페이스 변경 — 신규 FastAPI 엔드포인트 생성 (기존 OPAL 도구 인터페이스 불변)
- [x] 설정/환경변수 변경 — `~/.opal/console.config.json` 신규 추가 (U-2)
- [x] 빌드/배포 파이프라인 변경 — install-mac.sh에 빌드+배포 단계 추가

---

## 4. 핵심 발견 사항

1. **venv 즉시 재활용 가능**: `~/.opal/.venv`에 starlette 1.0.0 + uvicorn 0.42.0 + sse-starlette 3.3.4 + pydantic 2.12.5가 이미 설치됨. `requirements.txt`에 `fastapi[standard]>=0.110.0` 추가 1줄로 BE 데몬 환경 완성. 단, starlette 1.0.0 ↔ fastapi 0.136.x 호환 여부는 `pip install --dry-run`으로 검증 필요.

2. **opal-cli dispatcher 확장이 단순**: `run.sh:109` case 라인에 `console` 추가 + `lib/console.sh` 신규 파일로 충분. 기존 패턴(`lib/${subcommand}.sh` + `cmd_${subcommand}`)과 완전히 일치.

3. **스캔 실측 결과 — OPAL 프로젝트 1개**: `/Volumes/Data/AIStudio/workspace/` 하위 6개 중 ai-framework만 OPAL 초기화. 나머지 5개 (`ai-auto-content`, `ai-cs-manager`, `ai-product-detail`, `ai-stock-analysis`, `open-design`) 미초기화 → "OPAL 도입 현황 맵" 기능이 즉시 차별화 가치 발휘 가능.

4. **brain lint 경고 36건 현존**: `brain-tool lint` 실행 결과 broken_link·missing_link 36건 확인. 브레인 화면 lint 경고 배지 기능이 즉시 실용적이다.

5. **sse-starlette 기설치**: U-4 SSE 실시간 갱신을 위한 라이브러리가 venv에 이미 존재. 1차 폴링 구현 후 2차 SSE 전환 비용이 낮다.

---

## 5. 제약/리스크

| 항목 | 설명 | 심각도 | 근거 |
|------|------|--------|------|
| 배포 경계 | `~/.opal/` 직접 편집 금지, install 경유 강제 | High | `docs/CONVENTIONS.md §배포 경계` |
| 쓰기 도구 금지 | state-tool/brain-tool 쓰기 커맨드 미사용 — 1차 읽기 전용으로 자연 회피 | High | `TASK.md §결정적 제약` |
| venv 호환 검증 | starlette 1.0.0 + fastapi 0.136.x 버전 충돌 가능 — pip dry-run 필수 | Medium | `~/.opal/.venv/bin/pip list` 실측 |
| 스캔 루트 미설정 | 기본 스캔 루트 없으면 Console 첫 실행 불가 | Medium | `TASK.md §U-2` |
| doctor 파싱 취약 | `doctor.sh` 내부 변경 시 파싱 깨짐 — 버전 고정 파싱 전략 필요 | Low | `~/.opal/tools/opal-cli/lib/doctor.sh` |
| Windows 동기화 | install.ps1은 PowerShell 구조 — npm build 호출 방식 차이 | Low | `scripts/install.ps1:1-80` |
| Node.js 버전 | Vite 5.x는 Node 18+ 필요 — install 시 버전 체크 추가 필요 | Low | `docs/ARCHITECTURE.md §Node.js 도구` |

---

## 6. 기술 컨텍스트

### 6.1 기술 스택

| 카테고리 | 기술 | 버전 | 비고 |
|----------|------|------|------|
| FE 언어 | TypeScript | 5.x | Vite 기본 |
| FE 런타임 | React | 18.x | shadcn 권고 |
| FE 빌드 | Vite | 5.x | - |
| FE UI | shadcn/ui + Tailwind CSS | latest / 4.x | C-3 확정 |
| FE 상태(서버) | TanStack Query | v5 | 캐싱·폴링 |
| FE 상태(클라이언트) | Zustand | 4.x | UI 상태 |
| FE 칸반 | @dnd-kit/core + sortable | 6.x | C-6 확정 |
| FE 차트 | Recharts | 2.x | 대시보드 집계 |
| FE 그래프 | ReactFlow (xyflow) | 11.x | 브레인 지식 그래프 |
| BE 언어 | Python | 3.14.3 | 기설치 (.venv) |
| BE 프레임워크 | FastAPI | 0.136.x | requirements.txt 추가 |
| BE ASGI | uvicorn | 0.42.0 | 기설치 |
| BE SSE 지원 | sse-starlette | 3.3.4 | 기설치 — U-4 SSE 준비됨 |
| 설치 (macOS) | Bash install-mac.sh | v2.8 현행 | 대시보드 단계 추가 |
| 설치 (Windows) | PowerShell install.ps1 | v1.0.6 | 동기화 필요 |
| CLI | opal-cli run.sh | v1.0.3 | `console` 서브커맨드 추가 |

### 6.2 추천 스킬

| 스킬 | 용도 |
|------|------|
| op-dev-plan | PLAN 단계 — FE/BE 구현 계획 수립 |
| op-dev-wireframe | 화면별 와이어프레임 상세 설계 (R-8) |
| op-dev-execute | EXECUTE 단계 — FE(opal-fe-agent)/BE(opal-be-agent) 분리 |
| op-dev-test-scenario | TEST-SCENARIO.md 작성 |

### 6.3 추천 MCP

| MCP | 용도 |
|-----|------|
| context7 | React/shadcn/dnd-kit/TanStack Query/FastAPI 공식 문서 |
| shadcn | shadcn/ui 컴포넌트·대시보드 블록 카탈로그 조회 |
| playwright | 브라우저 E2E 검증 (대시보드 화면 렌더링 확인) |

---

## 7. 미확정 사항 U-1~U-8 권고

### U-1 백엔드 프레임워크 최종 확정

**권고: FastAPI 확정 (starlette/uvicorn 기설치 재활용)**

근거: `~/.opal/.venv pip list` 실측 → starlette 1.0.0, uvicorn 0.42.0, pydantic 2.12.5 이미 설치. `requirements.txt`에 `fastapi[standard]>=0.110.0` 1줄 추가로 완성. 단, starlette 1.0.0과 fastapi 0.136.x 호환성을 `pip install fastapi[standard] --dry-run`으로 PLAN 전 검증 필요.

### U-2 스캔 루트 설정 방식

**권고: `~/.opal/console.config.json` 설정 파일 + 기본값 추론**

```json
{
  "scan_roots": ["~/workspace"],
  "scan_depth": 2,
  "exclude": [".git", "node_modules", ".venv", "__pycache__"]
}
```

- 기본값: `$HOME/workspace` (또는 Console 첫 기동 시 설정 화면 제공)
- 탐색 알고리즘: `os.walk` + maxdepth 가드 + `.opal/AGENT.md` 발견 즉시 하위 탐색 중단
- 성능: 실측 workspace에서 depth=1 스캔으로 6개 프로젝트 발견 — 충분히 빠름

### U-3 칸반 컬럼 정의

**권고: 프로젝트 보드(컬럼=current_status) + 태스크 보드(컬럼=stage) 탭 전환**

**프로젝트 보드 컬럼 정의안** (`state.schema.json current_status enum` 기반):

| 컬럼 ID | 표시명 | current_status 값 |
|---------|--------|-------------------|
| `in_progress` | 진행 중 | `in_progress` |
| `blocked` | 블로커 | `blocked` |
| `additional_work` | 추가작업 | `additional_work`, `additional_work_done` |
| `done` | 완료 | `done` |

**태스크 보드**: rows[].stage 기반 컬럼 (TASK·PLAN·EXECUTE·TEST·CLOSE 등) — 카드에 item·status_label·timestamp 표시

### U-4 실시간 갱신 방식

**권고: 폴링 (1차) + SSE 준비 (2차)**

- 1차: TanStack Query `refetchInterval: 30_000` (30초) + 수동 새로고침 버튼
- 2차: `GET /api/events` SSE 엔드포인트 (sse-starlette 3.3.4 기설치로 구현 비용 낮음)
- 수동 새로고침 버튼은 1차 필수 UX (에이전트 실행 직후 즉시 확인 시나리오)

### U-5 데이터 수집 캐싱 전략

**권고: BE in-memory TTL 캐시 (TTL=30초) + FE TanStack Query staleTime**

- BE: `{project_path: {data, expires_at}}` dict + `os.path.getmtime()` mtime 비교로 무효화
- FE: `staleTime: 30_000`, `cacheTime: 300_000`
- subprocess 호출 빈도 제어: state.json은 파이프라인 단계 진입 시에만 변경 → 캐시 효과 큼

### U-6 그래프/차트 라이브러리

**권고: Recharts(집계 차트) + ReactFlow(지식 그래프) 분리**

| 용도 | 라이브러리 | 이유 |
|------|-----------|------|
| 태스크 상태 분포 (파이·바 차트) | Recharts | shadcn chart.tsx 기반, 48.9M weekly |
| 히스토리 타임라인 (라인 차트) | Recharts | 동일 |
| brain 지식 그래프 (노드-엣지) | ReactFlow | wiki related 링크 전담, MIT |
| 코드 의존성 맵 (선택) | ReactFlow | 동일 라이브러리 재사용 |

Visx는 학습비용 대비 이득 없음 — 기각.

### U-7 추가 기능 1차 포함 범위 우선순위

**1차 필수 (R-1~R-7 충족)**:
1. 대시보드 (전 프로젝트 집계 + 알림)
2. 프로젝트 목록 + OPAL 도입 현황 맵
3. 태스크 칸반 보드 (읽기 전용 + 산출물 뷰어)
4. 메모리 카테고리·히스토리 타임라인
5. 브레인 검색 + lint 경고 배지
6. 환경(doctor) 체크 패널

**1차 포함 권고 (단순 구현 가능)**:
- 통합 검색 헤더 바 (brain-tool search API 재활용)

**2차 분리 권고 (구현 비용 高 또는 쓰기 연동 필요)**:
- 칸반 드래그앤드롭 상태전환 (state-tool 쓰기 연동)
- 메모리/브레인 편집 기능
- 코드 의존성 맵 (ReactFlow 대형 그래프)

### U-8 데몬 기동 CLI 서브커맨드 이름

**권고: `opal-cli console`**

| 후보 | 판정 |
|------|------|
| `console` | **채택** — 서비스명(OPAL Console) 일치, lib/console.sh 자연스러움 |
| `dashboard` | 기각 — 소스 경로 `dashboard/`와 혼동 |
| `serve` | 기각 — OPAL 고유성 부족 |
| `ui` | 기각 — 광범위 |

서브커맨드 구조 권고:
```bash
opal-cli console start    # 데몬 기동 (기본 포트 7823)
opal-cli console stop     # 데몬 중지
opal-cli console status   # 상태 확인
opal-cli console open     # 브라우저 열기
```

---

## 8. 설치/기동 구조 상세 분석

### 8.1 install-mac.sh 콘솔 배포 삽입 지점

**위치**: `install_opal()` 함수 내 `install_opal_bin` 호출 직후 (`install-mac.sh:1059`)

```bash
# ── OPAL Console 대시보드 빌드+배포 ──
install_dashboard
```

**`install_dashboard()` 함수 구조 (신규)**:
```bash
install_dashboard() {
    local dashboard_src="$FRAMEWORK_ROOT/dashboard"
    local dashboard_dst="$USER_HOME/.opal/dashboard-server"

    [[ -d "$dashboard_src" ]] || { info "dashboard/ 미존재 — 스킵"; return; }

    # FE 빌드
    if command -v node &>/dev/null && [[ -d "$dashboard_src/frontend" ]]; then
        (cd "$dashboard_src/frontend" && npm install --silent && npm run build)
        install_dir "$dashboard_src/frontend/dist" "$dashboard_dst/dist" "Console FE dist"
    fi

    # BE 소스 복사 (venv는 ~/.opal/.venv 공유)
    [[ -d "$dashboard_src/backend" ]] && \
        install_dir "$dashboard_src/backend" "$dashboard_dst/backend" "Console BE"
}
```

**clean_dirs 수정**: `clean_dirs=("skills" "agents" "references" "templates" "tools")` → `"dashboard-server"` 추가

### 8.2 opal-cli `console` 서브커맨드 추가 지점

`opal/tools/opal-cli/run.sh` 수정 2곳:

1. `run.sh:109` — case 라인:
   ```bash
   # 변경 전:
   install|update|doctor|uninstall|mcp)
   # 변경 후:
   install|update|doctor|uninstall|mcp|console)
   ```

2. `usage()` 함수 내 서브커맨드 목록 1줄 추가:
   ```bash
   console [start|stop|status|open]  OPAL Console 대시보드 기동/관리
   ```

3. `opal/tools/opal-cli/lib/console.sh` 신규 파일 (`cmd_console()` 구현):
   ```bash
   # start: ~/.opal/.venv/bin/uvicorn main:app --port 7823 &
   # stop: pkill -f "dashboard-server/backend/main.py"
   # status: curl -s localhost:7823/health | python3 -m json.tool
   # open: open http://localhost:7823 (macOS) / xdg-open (Linux)
   ```

### 8.3 Windows (install.ps1) 동기화 필요 지점

1. `windows.ps1` (실제 설치 로직 파일) — `Install-Dashboard` 함수 추가
2. `npm.cmd` 호출 (Windows npm 래퍼)
3. `Start-Process` 백그라운드 uvicorn 기동 방식

Windows 동기화는 macOS 구현 완료 후 별도 단계로 진행 권고 (`docs/CONVENTIONS.md §플랫폼 분기 격리`).

---

## 9. UI 와이어프레임 제안 (R-8 요구사항)

> 화면별 레이아웃 상세(컴포넌트·스펙)는 별도 WIREFRAME 산출물(op-dev-wireframe 워커)로 작성. 본 절은 구조·데이터 소스 연결 정의에 집중.

### 9.1 전체 레이아웃 구조

```
┌──────────────────────────────────────────────────────────────┐
│ OPAL Console                     [통합 검색 ____]    ⚙ 설정  │
├───────────────┬──────────────────────────────────────────────┤
│  사이드바      │  메인 콘텐츠 영역                             │
│               │                                              │
│  🏠 대시보드   │                                              │
│  📁 프로젝트   │                                              │
│  📋 태스크(칸반)│                                              │
│  🧠 메모리     │                                              │
│  💡 브레인     │                                              │
│  🔧 환경       │                                              │
│               │                                              │
│  ─────────    │                                              │
│  현재 프로젝트  │                                              │
│  선택기        │                                              │
└───────────────┴──────────────────────────────────────────────┘
```

### 9.2 화면별 구성 요약

| 화면 | 핵심 컴포넌트 | 주요 데이터 소스 |
|------|-------------|----------------|
| **대시보드** | 집계 카드 4개 + Recharts 상태 분포 파이 + 알림(블로커·stale brain) | 전 프로젝트 state.json + brain lint |
| **프로젝트** | OPAL/미적용 구분 그리드 + 프로젝트 상세 드로어 | 디스크 스캔 + PROJECT.md + AGENT.md |
| **태스크(칸반)** | 프로젝트 보드(status 컬럼) + 태스크 보드(stage 컬럼) 탭 + 카드 클릭 → 산출물 뷰어 | state.json + TASK/PLAN/DONE.md |
| **메모리** | 카테고리 탭 필터 + 메모리 카드 목록 + 히스토리 Recharts 타임라인 | MEMORY.md 표 + memory/*.md |
| **브레인** | 검색바 + 결과 카드 + ReactFlow 지식 그래프 + lint 경고 배지 | brain-tool search/lint + pages/*.md |
| **환경** | doctor 4섹션 체크 패널 + MCP 등록 카드 + 스킬 목록 | opal-cli doctor + skill-registry |

---

## 10. 분석 품질 자체 체크리스트

- [x] TASK.md의 모든 요구사항(R-1~R-8)이 분석에 반영되었는가
- [x] 관련 파일 목록이 실제 파일 Read / 도구 실행 결과로 확인되었는가
- [x] 의존성 맵이 subprocess 호출 체인 기반으로 작성되었는가
- [x] 영향 범위가 직접+간접 모두 식별되었는가
- [x] 기술 스택이 실제 pip list / 설정 파일에서 추출되었는가
- [x] 외부 조사가 WebSearch로 수행되었는가 (FastAPI·dnd-kit·Recharts·ReactFlow)
- [x] 제약/리스크에 구체적 근거가 기재되어 있는가
- [x] §0 참조 문서 테이블이 작성되어 있는가 (유형/경로/URL/이유 포함)
- [x] §1.1 관련 파일 목록에 근거(줄번호) 컬럼이 채워져 있는가
- [x] §5 제약/리스크에 근거(경로·섹션)가 기재되어 있는가
- [x] U-1~U-8 전부에 대한 조사 기반 권고가 포함되어 있는가
- [x] UI 와이어프레임 제안(R-8, C-8)이 포함되어 있는가
