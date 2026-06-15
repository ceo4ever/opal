# PLAN: OPAL Console — 로컬 OPAL 프로젝트 통합 관리 대시보드 (1차 뷰어)

> 작성일: 2026-06-15 | 입력: TASK.md, ANALYSIS.md, WIREFRAME.md
> 모드: Multi-Feature | 실행 모드: 복잡

---

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

로컬에서 OPAL로 작업하는 모든 프로젝트를 한 웹 화면에서 조망하는 읽기 전용 대시보드(OPAL Console)를 구축한다. FastAPI 데몬이 OPAL 도구의 read-only 커맨드와 마크다운 파서로 데이터를 수집(데이터 SSOT를 새로 만들지 않음, → D-1 C-9)하고, React + shadcn/ui 프론트엔드가 5개 화면(대시보드/프로젝트/태스크/메모리/환경)을 렌더한다. 소스는 `{프로젝트}/dashboard/`, 배포는 install 경유로 `~/.opal/dashboard-server/`에 배치되며 `opal-cli console`로 기동한다.

**[MUST] 1차 범위 한정** — `tasks/021/TASK.md` C-2: "1차 = 전체 뷰어(읽기 전용) — 모든 쓰기/편집은 2차로 분리". → state-tool/brain-tool **쓰기 커맨드(init/advance/mark/add-page 등) 호출 설계 금지**. 어댑터는 read-only 커맨드만 래핑한다.

**[MUST] 브레인 제외** — `tasks/021/TASK.md` C-11: "브레인(지식 그래프·검색·lint) 전용 화면은 1차 범위 제외 — 2차 이관. 대시보드 stale brain 알림도 1차 제외. 1차 화면 5개(대시보드/프로젝트/태스크/메모리/환경)". → brain 화면·`brain_adapter`·`brain_parser`·brain lint 배지·stale brain 알림·ReactFlow 지식 그래프를 **PLAN에서 전면 제외**한다. ANALYSIS.md §2.3·§9, WIREFRAME.md §3-(5)에 남은 브레인 설계는 무시한다.

### 1.2 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | 프로젝트 스캐너 (BE) | R-1 | P0 | 없음 |
| F-002 | 도구 어댑터 계층 (BE, read-only) | R-2 | P0 | 없음 |
| F-003 | 마크다운 파서 (BE) | R-3 | P0 | 없음 |
| F-004 | 백엔드 API 데몬 (FastAPI) | R-4 | P0 | F-001, F-002, F-003 |
| F-005 | FE 앱 셸 + 디자인 토큰 (3색 전역화) | R-5, C-12 | P0 | 없음 |
| F-006 | 대시보드 화면 | R-5 | P0 | F-004, F-005 |
| F-007 | 프로젝트 화면 (도입 현황 맵) | R-5 | P0 | F-004, F-005 |
| F-008 | 태스크 칸반 보드 (읽기 전용) + 산출물 뷰어 | R-5, R-6 | P0 | F-004, F-005 |
| F-009 | 메모리 화면 | R-5 | P0 | F-004, F-005 |
| F-010 | 환경(doctor) 화면 | R-5 | P0 | F-004, F-005 |
| F-011 | 자동 설치 + 기동 CLI | R-7 | P0 | F-004, F-005 |

> R-8(ANALYSIS UI 와이어프레임)은 ANALYSIS 단계에서 WIREFRAME.md로 이미 충족됨 — 본 PLAN 범위 외.

### 1.3 기능 의존 그래프 (ASCII)

```
F-001 (스캐너) ─┐
F-002 (어댑터) ─┼─→ F-004 (API 데몬) ─┬─→ F-006 (대시보드) ─┐
F-003 (파서)   ─┘                     ├─→ F-007 (프로젝트) ─┤
                                      ├─→ F-008 (태스크)   ─┼─→ F-011 (설치+CLI)
F-005 (앱셸+토큰) ────────────────────┼─→ F-009 (메모리)   ─┤
                                      └─→ F-010 (환경)     ─┘
```

---

## 리스크 가설 표

> PLAN 단계에서 작성. TEST-SCENARIO.md §1의 입력이 됨.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | F-011 venv 의존성 | `fastapi[standard]` 추가 시 기설치 starlette 1.0.0과 버전 충돌 → BE 기동 실패 | P0 | L2(실 venv `pip --dry-run`) | TS-401 |
| H-2 | F-002 doctor 어댑터 | `doctor.sh` 텍스트 출력 포맷이 향후 변경 → 정규식 파싱 깨짐 → 환경 화면 빈 데이터 | P1 | L2(실 doctor 호출) | TS-201 |
| H-3 | F-002 어댑터 에러 처리 | 도구 `ok:false`·exit≠0·타임아웃을 에러로 구분하지 못하면 화면이 무한 로딩/오류 | P1 | L2(에러 주입) | TS-202 |
| H-4 | F-001 스캐너 성능 | scan_root 깊이 무제한 → `node_modules` 등 대형 트리 진입 → 응답 지연/행 | P1 | L2(maxdepth 가드 + exclude) | TS-101 |
| H-5 | F-005 디자인 토큰 | `--primary/--secondary/--tertiary`가 :root 1곳에 없거나 hex 하드코딩 잔존 → C-12 색 교체 불가 | P0 | L1(grep hex 스캔) + L3(시각) | TS-501 |
| H-6 | F-004 데이터 SSOT | 데몬이 프로젝트 파일을 쓰기/이동/캐시 오염 → SSOT 불변 위반 | P0 | L2(파일 mtime 불변 검증) | TS-301 |
| H-7 | F-004 보안 바인딩 | 데몬이 0.0.0.0 바인딩 → 로컬 데몬 외부 노출 | P0 | L2(바인딩 host=127.0.0.1 검증) | TS-302 |
| H-8 | F-011 Windows 동기화 | macOS만 구현되고 `windows.ps1` 미동기화 → Windows 설치 시 콘솔 누락 | P2 | L1(스크립트 정합성 리뷰) | TS-402 |
| H-9 | F-008 칸반 읽기 전용 | dnd-kit 드래그가 활성 상태로 남으면 1차 읽기 전용 제약 위반 | P1 | L3(드래그 비활성 시각 검증) | TS-801 |

**용어 일관성 검토 (citation-rules §7)**: state.json `current_status` enum(`in_progress|done|blocked|additional_work|additional_work_done`, → D-5)과 칸반 4컬럼(`대기/진행중/블로킹/완료`) 간 매핑은 F-004 BE에서 정규화하여 단일 계약으로 노출한다(§3 F-008). FE/BE 필드명 불일치는 §3 API 스키마로 통일하므로 decision_required 에스컬레이션 불요.

---

## 2. 기능별 분석

> ANALYSIS.md 존재 → 각 F-NNN 분석은 ANALYSIS 참조하여 간략 작성.

### F-001: 프로젝트 스캐너 (BE)

#### 2.1.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| BE | `dashboard/backend/scanner.py` | scan_root 하위 `.opal/AGENT.md` 마커로 OPAL 프로젝트 발견 | 신규 |
| 환경 | `~/.opal/console.config.json` | scan_roots·scan_depth·exclude 설정 (런타임 생성/읽기) | 신규 |

#### 2.1.2 현재 구현
그린필드 — 기존 스캐너 없음. 발견 마커는 `.opal/AGENT.md` 존재(→ D-2 부트스트랩 Step 6.5, ANALYSIS §2). 실측: workspace depth=1 스캔으로 6개 발견, ai-framework만 OPAL 적용(ANALYSIS §4-3).

#### 2.1.3 영향 범위
- 피호출: F-004 `/api/projects` 라우터.
- 읽기 전용 — 발견 대상 프로젝트 파일을 변경하지 않는다(H-6).

### F-002: 도구 어댑터 계층 (BE, read-only)

#### 2.2.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| BE | `dashboard/backend/adapters/base.py` | subprocess 공통 실행·타임아웃·에러 정규화 | 신규 |
| BE | `dashboard/backend/adapters/state_adapter.py` | state-tool `show --format json` 호출 | 신규 |
| BE | `dashboard/backend/adapters/scan_adapter.py` | code-scan `scan --json` 호출 | 신규 |
| BE | `dashboard/backend/adapters/skill_adapter.py` | skill-registry `list` 호출 | 신규 |
| BE | `dashboard/backend/adapters/doctor_adapter.py` | opal-cli `doctor` 텍스트 파싱 | 신규 |

> brain_adapter는 **C-11에 따라 제외**.

#### 2.2.2 현재 구현
호출 대상 도구는 read-only 커맨드 보유(→ D-5/D-7, ANALYSIS §2.1). state-tool은 venv python 래퍼(`run.sh:1-12`, → D-6). doctor만 텍스트 → 정규식 파싱(ANALYSIS §2.1 doctor 패턴).

#### 2.2.3 영향 범위
- 피호출: F-004 전 라우터. 상위 도구 인터페이스 불변(읽기만).
- 에러 계약: `ok:false`·exit≠0·timeout 3종 구분(H-3).

### F-003: 마크다운 파서 (BE)

#### 2.3.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| BE | `dashboard/backend/parsers/memory_parser.py` | MEMORY.md 메모리 표·히스토리 표 파싱 | 신규 |
| BE | `dashboard/backend/parsers/memory_file_parser.py` | `memory/*.md` 블록쿼트 메타 파싱 | 신규 |
| BE | `dashboard/backend/parsers/project_parser.py` | PROJECT.md·AGENT.md 메타(PM프로필·기술스택·문서) 파싱 | 신규 |
| BE | `dashboard/backend/parsers/markdown_reader.py` | TASK/PLAN/DONE.md 원문 read (산출물 뷰어) | 신규 |

> brain_parser(frontmatter)는 **C-11에 따라 제외**.

#### 2.3.2 현재 구현
MEMORY.md = md 표(등록일시·카테고리·상태·파일·설명) + 히스토리 표(ANALYSIS §2.1 MEMORY.md). `memory/*.md`는 frontmatter 미사용, `> 키: 값` 블록쿼트(ANALYSIS §2.1). 정규식 추출로 충분.

#### 2.3.3 영향 범위
- 피호출: F-004 `/api/memory`·`/api/projects/{id}`·`/api/tasks/{...}/artifact`.

### F-004: 백엔드 API 데몬 (FastAPI)

#### 2.4.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| BE | `dashboard/backend/main.py` | FastAPI app + uvicorn 엔트리 + CORS + /health | 신규 |
| BE | `dashboard/backend/config.py` | console.config.json 로드·기본값 추론 | 신규 |
| BE | `dashboard/backend/cache.py` | in-memory TTL 캐시(mtime 무효화) | 신규 |
| BE | `dashboard/backend/routers/{dashboard,projects,tasks,memory,doctor}.py` | 5개 화면 라우터 | 신규 |
| BE | `dashboard/backend/models.py` | Pydantic 응답 스키마 | 신규 |
| 환경 | `opal/tools/requirements.txt` | `fastapi[standard]>=0.110.0` 추가 | 수정 |

#### 2.4.2 현재 구현
venv에 starlette 1.0.0·uvicorn 0.42.0·pydantic 2.12.5 기설치(ANALYSIS §4-1). FastAPI 본체만 추가. 캐싱: TTL 30초 + `os.path.getmtime()` 무효화(ANALYSIS §U-5).

#### 2.4.3 영향 범위
- 호출: F-005 FE TanStack Query. 피호출: F-001~F-003.
- **[MUST] 보안** — `tasks/021/TASK.md` §제약: "로컬 데몬은 localhost 바인딩 기본, 외부 노출 금지". → host=`127.0.0.1`(H-7).

### F-005: FE 앱 셸 + 디자인 토큰 (3색 전역화)

#### 2.5.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| FE | `dashboard/frontend/` | Vite + React + TS + Tailwind + shadcn 스캐폴딩 | 신규 |
| FE | `dashboard/frontend/src/index.css` | :root 디자인 토큰(3색 + 상태색 + 다크/라이트) | 신규 |
| FE | `dashboard/frontend/src/components/app-shell/` | 사이드바(5 네비) + 상단바 + 프로젝트 스위처 | 신규 |
| FE | `dashboard/frontend/src/lib/api.ts` | API 클라이언트 + TanStack Query 설정 | 신규 |
| FE | `dashboard/frontend/src/store/` | Zustand UI 상태(테마·컨텍스트 프로젝트) | 신규 |

#### 2.5.2 현재 구현
그린필드. shadcn `sidebar-07`+`sidebar-16` 조합 셸(WIREFRAME §2.1). 네비는 5개(브레인 제외).

#### 2.5.3 영향 범위
- 피호출: F-006~F-010 전 화면이 셸·토큰·API 클라이언트 공유.

### F-006 ~ F-010: 5개 화면

#### 2.6.1 관련 파일 맵 (공통)
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| FE | `dashboard/frontend/src/pages/dashboard/` | F-006 집계 카드·차트·알림·최근활동 | 신규 |
| FE | `dashboard/frontend/src/pages/projects/` | F-007 목록·도입현황·상세 패널 | 신규 |
| FE | `dashboard/frontend/src/pages/tasks/` | F-008 칸반 보드·카드·Drawer 산출물 뷰어 | 신규 |
| FE | `dashboard/frontend/src/pages/memory/` | F-009 카테고리 리스트·히스토리 타임라인 | 신규 |
| FE | `dashboard/frontend/src/pages/doctor/` | F-010 doctor 체크 패널·MCP·스킬 | 신규 |

#### 2.6.2 현재 구현
그린필드. shadcn 매핑은 WIREFRAME §3-(1)~(4),(6) + §7. 차트는 Recharts(shadcn chart), 칸반은 dnd-kit(드래그 비활성).

#### 2.6.3 영향 범위
- 호출: F-004 API. 공유: F-005 셸·토큰·상태색 체계(WIREFRAME §6.2).

### F-011: 자동 설치 + 기동 CLI

#### 2.7.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 공통 | `scripts/install-mac.sh` | `install_dashboard()` 신설 + 호출 + clean_dirs 추가 | 수정 |
| 공통 | `scripts/install/macos.sh` | (필요 시) 콘솔 단계 호출 정합성 | 수정 |
| 공통 | `scripts/install/windows.ps1` | `Install-Dashboard` 동기화 | 수정 |
| 공통 | `opal/tools/opal-cli/run.sh` | dispatcher case에 `console` 추가 + usage | 수정 |
| 공통 | `opal/tools/opal-cli/lib/console.sh` | `cmd_console()` — start/stop/status/open | 신규 |

#### 2.7.2 현재 구현
- 실측: dispatcher case `install|update|doctor|uninstall|mcp)` (`run.sh:109`), 패턴 `source lib/${subcommand}.sh` → `cmd_${subcommand}` (`run.sh:113-117`). lib 디렉토리 현황: doctor/install/mcp/uninstall/update.sh.
- 실측: `install_dir()` (`install-mac.sh:196`), `clean_dirs=("skills" "agents" "references" "templates" "tools")` (`install-mac.sh:866`), `install_opal_bin` 호출 (`install-mac.sh:1059`).
- 실측: Windows 실제 설치 로직은 `scripts/install/windows.ps1` (install.ps1은 one-liner 부트스트랩).

#### 2.7.3 영향 범위
- `~/.opal/dashboard-server/` 생성(간접). `~/.opal/.venv`에 FastAPI 추가(H-1).

---

## 3. 기능별 설계

### F-001: 프로젝트 스캐너

#### 3.1.1 파일 변경 계획
**신규 생성**
| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `dashboard/backend/scanner.py` | BE | OPAL 프로젝트 발견 | (→ D-2, ANALYSIS §U-2) |
| 2 | `~/.opal/console.config.json` | 환경 | 스캔 설정 | (→ ANALYSIS §U-2) |

#### 3.1.2 API·데이터 모델·화면 설계
```python
# scanner.py
def scan_projects(roots: list[str], depth: int, exclude: list[str]) -> list[ProjectInfo]:
    """roots 하위를 os.walk + maxdepth 가드로 탐색.
    .opal/AGENT.md 발견 시 OPAL 프로젝트로 등록 후 하위 탐색 중단(prune).
    exclude 디렉토리는 진입 금지(H-4)."""

# models.py (Pydantic)
class ProjectInfo(BaseModel):
    name: str
    path: str
    is_opal: bool          # .opal/AGENT.md 존재
    task_count: int        # tasks/*/ 개수 (OPAL만)
    last_updated: str | None  # 최신 state.json mtime
```
- **[MUST] scan_depth maxdepth 가드** — `tasks/021/ANALYSIS.md` §5: "스캔 루트 깊이 무제한 → 대형 트리 진입 → 응답 지연". → `depth` 초과 시 prune, `exclude`에 `node_modules/.git/.venv/__pycache__` 기본 포함(→ D-3, H-4).
- 기본 scan_root: `$HOME/workspace`, 부재 시 빈 목록 + 설정 안내(ANALYSIS §U-2).

#### 3.1.3 환경 변경
`~/.opal/console.config.json` 첫 기동 시 기본값으로 생성. 패키지 변경 없음.

#### 3.1.4 배치/마이그레이션
해당 없음.

#### 3.1.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-101 | R-1 AC | 통합 테스트 | scan_root에 OPAL N개 있을 때 `/api/projects`가 N개 반환, 비OPAL은 `is_opal:false`. exclude/maxdepth로 node_modules 미진입 |

### F-002: 도구 어댑터 계층

#### 3.2.1 파일 변경 계획
**신규 생성**
| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `dashboard/backend/adapters/base.py` | BE | subprocess 공통 + 에러 정규화 | (→ ANALYSIS §1.3) |
| 2 | `dashboard/backend/adapters/state_adapter.py` | BE | state-tool show | (→ D-5) |
| 3 | `dashboard/backend/adapters/scan_adapter.py` | BE | code-scan scan | (→ D-7) |
| 4 | `dashboard/backend/adapters/skill_adapter.py` | BE | skill-registry list | (→ ANALYSIS §2.1) |
| 5 | `dashboard/backend/adapters/doctor_adapter.py` | BE | doctor 텍스트 파싱 | (→ ANALYSIS §2.1) |

#### 3.2.2 API·데이터 모델·화면 설계
```python
# base.py
class ToolError(Exception): ...   # ok:false | exit≠0 | timeout 구분
def run_tool(cmd: list[str], timeout: float = 10.0) -> dict:
    """subprocess.run(capture, timeout). exit≠0 또는 timeout → ToolError.
    JSON 파싱 후 {ok:false} → ToolError. 정상 → dict."""

# state_adapter.py
def get_state(task_dir: str) -> dict:
    # run_tool(["bash", f"{OPAL}/tools/state-tool/run.sh", "show",
    #           "--task", task_dir, "--format", "json"])
```
- **[MUST] read-only 한정** — `tasks/021/TASK.md` §결정적 제약: "쓰기는 도구 경유 강제 … 1차 뷰어는 읽기 전용". → 어댑터는 `show/scan/list/doctor`만 호출, `init/advance/mark/add-page` 금지.
- state.json enum은 실측 스키마 준수(→ D-5: current_status 5종, rows[].status 5종, rows[].stage 16종).
- 에러 3종 구분(H-3): `ToolError`를 라우터에서 `503/504` + 화면 에러 상태로 변환.

#### 3.2.3 환경 변경
해당 없음 (도구는 기설치).

#### 3.2.4 배치/마이그레이션
해당 없음.

#### 3.2.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-201 | R-2 AC | 통합 테스트 | 실 도구 호출 시 정상 JSON 파싱·반환. doctor 4섹션 파싱 결과가 항목 리스트로 구조화 |
| TS-202 | R-2 AC | 통합 테스트 | exit≠0·`ok:false`·timeout 3종이 각각 ToolError로 구분되어 503/504 응답 |

### F-003: 마크다운 파서

#### 3.3.1 파일 변경 계획
**신규 생성**
| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `dashboard/backend/parsers/memory_parser.py` | BE | MEMORY.md 표 파싱 | (→ ANALYSIS §2.1) |
| 2 | `dashboard/backend/parsers/memory_file_parser.py` | BE | memory/*.md 메타 | (→ ANALYSIS §2.1) |
| 3 | `dashboard/backend/parsers/project_parser.py` | BE | PROJECT/AGENT.md 메타 | (→ D-1, D-4) |
| 4 | `dashboard/backend/parsers/markdown_reader.py` | BE | 산출물 .md 원문 read | (→ ANALYSIS §2.2) |

#### 3.3.2 API·데이터 모델·화면 설계
```python
# memory_parser.py
def parse_memory_index(memory_md: str) -> MemoryIndex:
    """## 메모리 섹션 md 표 → rows[{date,category,status,file,desc}].
    ## 작업 히스토리 표 → history[{date,task,stage,path,start,end}]."""

# project_parser.py
def parse_project(project_path: str) -> ProjectDetail:
    """AGENT.md → PM 프로필(역할·페르소나·금지사항).
    PROJECT.md → 기술스택·문서 목록."""
```
- 파싱 실패(표 누락 등)는 빈 배열 + 경고 필드로 graceful 처리(화면 빈 상태로 폴백).
- **[MUST] 읽기 전용** — `tasks/021/TASK.md` §제약: "데몬은 각 프로젝트 파일을 변형/이동/캐시 오염시키지 않는다(읽기만)". → 파서는 open(read)만(H-6).

#### 3.3.3 환경 변경
PyYAML 기설치(requirements.txt) — frontmatter 필요 시 재사용. 추가 없음.

#### 3.3.4 배치/마이그레이션
해당 없음.

#### 3.3.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-301 | R-3 AC | 통합 테스트 | MEMORY.md 메모리 표·히스토리 표가 구조화 JSON 반환. memory/*.md 메타 추출. 파일 mtime 불변(H-6) |

### F-004: 백엔드 API 데몬 (FastAPI)

#### 3.4.1 파일 변경 계획
**신규 생성**
| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `dashboard/backend/main.py` | BE | FastAPI app·uvicorn·CORS·/health | (→ D-10) |
| 2 | `dashboard/backend/config.py` | BE | console.config.json 로드 | (→ ANALYSIS §U-2) |
| 3 | `dashboard/backend/cache.py` | BE | TTL 캐시 | (→ ANALYSIS §U-5) |
| 4 | `dashboard/backend/routers/dashboard.py` | BE | 집계 라우터 | (→ WIREFRAME §3-(1)) |
| 5 | `dashboard/backend/routers/projects.py` | BE | 프로젝트 라우터 | (→ WIREFRAME §3-(2)) |
| 6 | `dashboard/backend/routers/tasks.py` | BE | 태스크/칸반/산출물 라우터 | (→ WIREFRAME §3-(3)) |
| 7 | `dashboard/backend/routers/memory.py` | BE | 메모리 라우터 | (→ WIREFRAME §3-(4)) |
| 8 | `dashboard/backend/routers/doctor.py` | BE | 환경 라우터 | (→ WIREFRAME §3-(6)) |
| 9 | `dashboard/backend/models.py` | BE | Pydantic 응답 스키마 | - |

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/requirements.txt` | 환경 | `fastapi[standard]>=0.110.0` 추가 | (→ ANALYSIS §4-1) |

#### 3.4.2 API·데이터 모델·화면 설계

**엔드포인트 목록 (화면별, 전부 GET — 읽기 전용)**

| 메서드 | 경로 | 화면 | 응답 요약 | 데이터 소스 |
|--------|------|------|----------|------------|
| GET | `/health` | - | `{status, version}` | - |
| GET | `/api/dashboard` | 대시보드 | 집계 4메트릭 + 상태분포 + 활동추이 + 주의알림 + 최근활동 | 전 프로젝트 state.json |
| GET | `/api/projects` | 프로젝트 | ProjectInfo[] (도입현황 포함) | scanner |
| GET | `/api/projects/{id}` | 프로젝트 | ProjectDetail (PM프로필·문서·스택) | project_parser |
| GET | `/api/projects/{id}/doc?name=` | 프로젝트 | 문서 원문 md | markdown_reader |
| GET | `/api/tasks?project=` | 태스크 | TaskCard[] (칸반 컬럼 그룹핑됨) | state.json |
| GET | `/api/tasks/{project}/{taskId}` | 태스크 | 파이프라인 단계 현황 + 산출물 목록 | state-tool show |
| GET | `/api/tasks/{project}/{taskId}/artifact?name=` | 태스크 | 산출물 md 원문 | markdown_reader |
| GET | `/api/memory?project=` | 메모리 | MemoryIndex (메모리+히스토리) | memory_parser |
| GET | `/api/doctor?project=` | 환경 | doctor 4섹션 + MCP + 스킬 | doctor/skill adapter |

> brain 엔드포인트(`/api/brain*`)는 **C-11에 따라 제외**.

**칸반 컬럼 정규화 (U-3 확정 — 상태 4컬럼 단일 보드)**
```python
# tasks.py — current_status → 칸반 컬럼 매핑 (단일 계약, 용어 일관성 §7)
COLUMN_MAP = {
    "in_progress": "in_progress",        # 진행중
    "blocked": "blocked",                # 블로킹
    "additional_work": "in_progress",    # 추가작업 → 진행중에 합류
    "additional_work_done": "done",
    "done": "done",
    # 미착수(state 없음) → "pending"(대기)
}
class TaskCard(BaseModel):
    task_id: str; title: str; skill: str; mode: str
    column: Literal["pending","in_progress","blocked","done"]
    current_stage: str; progress: int; updated_at: str; artifact_count: int
```
- **[MUST] 칸반 단일 보드 확정** — `tasks/021/PLAN.md` 전제(캡틴 승인): "상태 4컬럼 단일 보드(대기/진행중/블로킹/완료) + 단계는 태스크 상세 Drawer 가로 스테퍼. 1차 읽기 전용(드래그 비활성)". → 단계(stage) 보드는 Drawer 스테퍼로 대체(WIREFRAME §4.1).
- **[MUST] localhost 바인딩** — `tasks/021/TASK.md` §제약: "로컬 데몬은 localhost 바인딩 기본, 외부 노출 금지". → `uvicorn.run(host="127.0.0.1", port=7823)` (H-7).
- 캐시: `cache.py` `{key:(data,expires_at)}` + 소스 파일 mtime 비교 무효화, TTL=30초(ANALYSIS §U-5).
- CORS: dev 모드 `http://localhost:5173`(Vite) 허용, 배포 모드는 동일 오리진(정적 서빙).

#### 3.4.3 환경 변경
`requirements.txt`에 `fastapi[standard]>=0.110.0` 1줄. **[MUST] venv 호환 선검증** — `tasks/021/ANALYSIS.md` §5: "starlette 1.0.0 + fastapi 0.136.x 버전 충돌 가능 — pip dry-run 필수". → EXECUTE 초반 Step에서 `pip install fastapi[standard] --dry-run` 검증(H-1, TS-401).

#### 3.4.4 배치/마이그레이션
해당 없음.

#### 3.4.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-302 | R-4 AC | 보안 테스트 | 데몬이 127.0.0.1에만 바인딩, 외부 IP 접근 거부 |
| TS-310 | R-4 AC | 통합 테스트 | 5개 화면 엔드포인트가 모두 200 + 스키마 일치 응답. /health 200 |

### F-005: FE 앱 셸 + 디자인 토큰 (3색 전역화)

#### 3.5.1 파일 변경 계획
**신규 생성**
| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `dashboard/frontend/` (Vite 스캐폴딩) | FE | React+TS+Tailwind+shadcn init | (→ D-9) |
| 2 | `dashboard/frontend/src/index.css` | FE | :root 토큰 (3색+상태색+다크/라이트) | (→ WIREFRAME §1.1) |
| 3 | `dashboard/frontend/src/components/app-shell/AppShell.tsx` | FE | 사이드바(5)+상단바+스위처 | (→ WIREFRAME §2) |
| 4 | `dashboard/frontend/src/lib/api.ts` | FE | API 클라이언트 + QueryClient | (→ ANALYSIS §U-4) |
| 5 | `dashboard/frontend/src/store/ui-store.ts` | FE | Zustand 테마·프로젝트 컨텍스트 | (→ ANALYSIS §2.3) |
| 6 | `dashboard/frontend/src/router.tsx` | FE | 5 라우트 정의 | (→ WIREFRAME §2.3) |

**디자인 토큰 명세 (C-12 — 3색 전역변수화)**
```css
/* index.css :root — 단 한 곳에서 3색 교체 (C-12) */
:root {
  /* === 시그니처 3색 (여기만 바꾸면 전 화면 일괄 반영) === */
  --primary: 252 100% 68%;       /* violet #7C5CFF (권고 초기값) */
  --secondary: 175 70% 41%;      /* teal 계열 (서브 시그니처 초기값 제안) */
  --tertiary: 32 95% 55%;        /* amber 계열 (3번째/accent 초기값 제안) */

  /* shadcn 표준 토큰은 위 3색에서 파생/참조 */
  --background: 0 0% 100%; --foreground: 240 6% 6%;
  --card: 0 0% 100%; --border: 240 6% 90%;
  --ring: var(--primary);

  /* OPAL 상태색 5종 (칸반·스테퍼·doctor·알림 공용 — WIREFRAME §6.2) */
  --status-todo: 215 16% 65%;    --status-running: 217 91% 60%;
  --status-done: 152 60% 45%;    --status-blocked: 350 80% 60%;
  --status-stale: 38 92% 50%;

  --radius: 0.625rem;
}
.dark { /* 동일 토큰명, 명도 보정값만 재정의 (다크 기본 모드) */ }
```
- **[MUST] 토큰 경유·hex 하드코딩 금지** — `tasks/021/TASK.md` C-12: "시그니처 --primary·서브 --secondary·3번째 --tertiary 3색을 :root 한 곳의 전역 CSS 변수로 정의해 쉽게 교체 가능하게. 모든 UI 색상은 토큰 경유, 하드코딩 hex 금지". → Tailwind theme를 토큰에 바인딩, 컴포넌트는 `bg-primary` 등 토큰 클래스만 사용(H-5).
- 테마 토글(라이트/다크/시스템) → localStorage 영속(WIREFRAME §1.1).
- 폰트 확정: Geist Sans(UI) + Geist Mono(코드/경로/ID) — `tabular-nums`(WIREFRAME §1.2, 캡틴 승인).

##### 화면: 앱 셸 (글로벌 레이아웃)
- **ID**: FE-0
- **유형**: dashboard
- **action**: new
- **경로**: `/` (셸 래퍼)
- **파일**: `dashboard/frontend/src/components/app-shell/AppShell.tsx`, `index.css`, `router.tsx`
- **shadcn 컴포넌트**: sidebar(07+16), breadcrumb, command(⌘K), kbd, dropdown-menu, button, badge, separator, tooltip, sonner
- **UI 작업**: 좌측 5개 네비(대시보드/프로젝트/태스크/메모리/환경) + 프로젝트 스위처(★전 프로젝트) + 상단바(검색·테마토글·새로고침·연결상태·설정). 브레인 네비 제외.
- **API 연동**: `/health`(연결상태), `/api/projects`(스위처 목록)

#### 3.5.2 환경 변경
package.json 신규: react 18, vite 5, tailwindcss 4, @tanstack/react-query v5, zustand 4, recharts 2, @dnd-kit/core+sortable 6, react-router, lucide-react, react-markdown+remark-gfm. **ReactFlow 제외**(C-11).

#### 3.5.3 배치/마이그레이션
해당 없음.

#### 3.5.4 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-501 | C-12 AC | 산출물 검사 | `--primary/--secondary/--tertiary`가 :root 1곳 정의. 컴포넌트 코드에 hex 하드코딩 0건(grep). --primary 값 변경 시 전 화면 강조색 일괄 변경 |
| TS-502 | R-5 AC | 기능 테스트 | 셸 렌더 + 5 네비 라우팅 동작. 다크/라이트 토글 + localStorage 영속 |

### F-006: 대시보드 화면

#### 3.6.1 파일 변경 계획
**신규 생성**
| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `dashboard/frontend/src/pages/dashboard/DashboardPage.tsx` 외 하위 컴포넌트 | FE | 집계·차트·알림·최근활동 | (→ WIREFRAME §3-(1)) |

#### 3.6.2 API·데이터 모델·화면 설계
##### 화면: 대시보드
- **ID**: FE-1
- **유형**: dashboard
- **action**: new
- **경로**: `/`
- **파일**: `pages/dashboard/DashboardPage.tsx`, `SectionCards.tsx`, `ActivityChart.tsx`, `StatusPieChart.tsx`, `AlertList.tsx`, `RecentTable.tsx`
- **shadcn 컴포넌트**: card, badge, chart-area-interactive, chart-pie-donut-text, toggle-group, item, data-table(tanstack), skeleton
- **UI 작업**: 4메트릭(OPAL 프로젝트/진행중 태스크/블로커/추가작업) section-cards + 활동추이(7d/30d/90d) + 단계분포 파이 + 주의알림(블로커·오래된 진행중) + 최근활동 테이블. **stale brain 알림·brain lint 카드 제외**(C-11).
- **API 연동**: `/api/dashboard`

#### 3.6.3~3.6.4 환경/배치: 해당 없음.
#### 3.6.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-601 | R-5 AC | 기능 테스트 | 대시보드가 실 데이터로 4메트릭·차트·알림 렌더. brain 관련 위젯 부재 |

### F-007: 프로젝트 화면

#### 3.7.1 파일 변경 계획
**신규 생성**
| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `dashboard/frontend/src/pages/projects/` | FE | 목록·도입현황·상세 패널 | (→ WIREFRAME §3-(2)) |

#### 3.7.2 화면 설계
##### 화면: 프로젝트
- **ID**: FE-2
- **유형**: crud (읽기 전용)
- **action**: new
- **경로**: `/projects`, `/projects/:id`
- **파일**: `ProjectsPage.tsx`, `ProjectList.tsx`, `AdoptionSummary.tsx`, `ProjectDetailPanel.tsx`, `MarkdownDrawer.tsx`
- **shadcn 컴포넌트**: item/data-table, resizable, tabs, card, avatar, badge, progress, input, select, drawer, scroll-area
- **UI 작업**: 좌 목록(OPAL적용/미적용 badge + 검색·필터) + 도입현황 progress + 우 상세(개요/PM프로필/문서/스택 탭) + 문서 클릭 → 마크다운 Drawer. 미적용 프로젝트 회색 처리.
- **API 연동**: `/api/projects`, `/api/projects/{id}`, `/api/projects/{id}/doc`

#### 3.7.3~3.7.4: 해당 없음.
#### 3.7.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-701 | R-1/R-5 AC | 기능 테스트 | 목록에 OPAL/미적용 구분 표시. 상세 패널에 PM프로필·문서·스택 렌더. 문서 Drawer 마크다운 |

### F-008: 태스크 칸반 보드 (읽기 전용) + 산출물 뷰어

#### 3.8.1 파일 변경 계획
**신규 생성**
| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `dashboard/frontend/src/pages/tasks/` | FE | 칸반·카드·Drawer·스테퍼·뷰어 | (→ WIREFRAME §3-(3),§4) |

#### 3.8.2 화면 설계
##### 화면: 태스크 (칸반)
- **ID**: FE-3
- **유형**: monitor
- **action**: new
- **경로**: `/tasks?project=`, `/tasks/:project/:taskId`
- **파일**: `TasksPage.tsx`, `KanbanBoard.tsx`, `KanbanColumn.tsx`, `TaskCard.tsx`, `TaskDrawer.tsx`, `PipelineStepper.tsx`, `ArtifactViewer.tsx`
- **shadcn 컴포넌트**: card, badge, progress, toggle-group, empty, drawer/sheet, tabs, scroll-area, skeleton, separator (dnd-kit 1차 비활성)
- **UI 작업**: 상태 4컬럼(대기/진행중/블로킹/완료) 단일 보드 + 카드(ID·제목·진행률·스킬/모드 badge·단계). 카드 클릭 → Drawer(가로 파이프라인 스테퍼 + TASK/PLAN/DONE 등 산출물 탭 마크다운 뷰어). **[MUST] 읽기 전용** — dnd-kit sensors 비활성·`🔒 읽기 전용` badge 상시·grab 커서 미사용(WIREFRAME §4.4, H-9). 프로젝트 미선택 시 empty + 선택 그리드.
- **API 연동**: `/api/tasks?project=`, `/api/tasks/{project}/{taskId}`, `/api/tasks/{project}/{taskId}/artifact`

#### 3.8.3~3.8.4: 해당 없음.
#### 3.8.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-801 | R-6 AC | 기능 테스트 | 카드가 상태 컬럼에 배치. 드래그 시도해도 이동 안 됨(읽기 전용). 카드 클릭 → Drawer 스테퍼+산출물 마크다운 |

### F-009: 메모리 화면

#### 3.9.1 파일 변경 계획
**신규 생성**
| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `dashboard/frontend/src/pages/memory/` | FE | 카테고리 리스트·필터·타임라인 | (→ WIREFRAME §3-(4)) |

#### 3.9.2 화면 설계
##### 화면: 메모리
- **ID**: FE-4
- **유형**: report
- **action**: new
- **경로**: `/memory?project=`
- **파일**: `MemoryPage.tsx`, `MemoryList.tsx`, `HistoryTimeline.tsx`, `MemoryDrawer.tsx`
- **shadcn 컴포넌트**: item, badge, select, toggle-group, hover-card, scroll-area, drawer + 커스텀 타임라인
- **UI 작업**: 좌 메모리 리스트(카테고리 badge·검색·태그칩 필터) + 우 작업 히스토리 타임라인. 메모리 클릭 → Drawer 마크다운.
- **API 연동**: `/api/memory?project=`

#### 3.9.3~3.9.4: 해당 없음.
#### 3.9.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-901 | R-5 AC | 기능 테스트 | 메모리 카테고리/태그 필터 동작. 히스토리 타임라인 렌더. 상세 Drawer 마크다운 |

### F-010: 환경(doctor) 화면

#### 3.10.1 파일 변경 계획
**신규 생성**
| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `dashboard/frontend/src/pages/doctor/` | FE | doctor 체크·MCP·스킬 | (→ WIREFRAME §3-(6)) |

#### 3.10.2 화면 설계
##### 화면: 환경 (doctor)
- **ID**: FE-5
- **유형**: monitor
- **action**: new
- **경로**: `/doctor`
- **파일**: `DoctorPage.tsx`, `CheckSection.tsx`, `McpCards.tsx`, `SkillList.tsx`
- **shadcn 컴포넌트**: card, accordion, item, badge, alert, tooltip, skeleton
- **UI 작업**: 전체 상태 헤더(정상/경고/실패) + 카테고리 섹션(의존성/MCP/부트스트래퍼) accordion + 개별 체크 ✅⚠❌ + 실패 시 alert. MCP 등록 카드 + 스킬 목록.
- **API 연동**: `/api/doctor?project=`

#### 3.10.3~3.10.4: 해당 없음.
#### 3.10.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-1001 | R-5 AC | 기능 테스트 | doctor 4섹션 체크 항목·MCP·스킬 렌더. 실패 항목 alert 노출 |

### F-011: 자동 설치 + 기동 CLI

#### 3.11.1 파일 변경 계획
**신규 생성**
| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `opal/tools/opal-cli/lib/console.sh` | 공통 | cmd_console (start/stop/status/open) | `opal/tools/opal-cli/run.sh:113-117` |

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/opal-cli/run.sh` | 공통 | dispatcher case에 `console` 추가 + usage 1줄 | `opal/tools/opal-cli/run.sh:109` |
| 2 | `scripts/install-mac.sh` | 공통 | `install_dashboard()` 신설 + `install_opal()` 내 호출 + clean_dirs에 `dashboard-server` 추가 | `scripts/install-mac.sh:196,866,1059` |
| 3 | `scripts/install/windows.ps1` | 공통 | `Install-Dashboard` 동기화 | `scripts/install/windows.ps1` |

#### 3.11.2 API·설계
```bash
# run.sh:109 case 변경
install|update|doctor|uninstall|mcp|console)   # console 추가

# lib/console.sh
cmd_console() {
  case "$1" in
    start)  "$HOME/.opal/.venv/bin/uvicorn" --app-dir "$HOME/.opal/dashboard-server/backend" \
              main:app --host 127.0.0.1 --port 7823 & ;;   # localhost 바인딩(H-7)
    stop)   pkill -f "dashboard-server/backend" ;;
    status) curl -s http://127.0.0.1:7823/health ;;
    open)   open http://127.0.0.1:7823 2>/dev/null || xdg-open http://127.0.0.1:7823 ;;
  esac
}
```
```bash
# install-mac.sh: install_dashboard() (install_opal_bin 호출부 근처에 호출 추가)
install_dashboard() {
  local src="$FRAMEWORK_ROOT/dashboard"; local dst="$USER_HOME/.opal/dashboard-server"
  [[ -d "$src" ]] || { info "dashboard/ 미존재 — 스킵"; return; }
  if command -v node &>/dev/null && [[ -d "$src/frontend" ]]; then
    (cd "$src/frontend" && npm install --silent && npm run build)
    install_dir "$src/frontend/dist" "$dst/dist" "Console FE dist"     # install_dir: install-mac.sh:196
  fi
  [[ -d "$src/backend" ]] && install_dir "$src/backend" "$dst/backend" "Console BE"
}
# clean_dirs(install-mac.sh:866)에 "dashboard-server" 추가
```
- **[MUST] CLI 서브커맨드 확정 = console** — `tasks/021/PLAN.md` 전제(캡틴 승인) + ANALYSIS §U-8: "opal-cli console (start/stop/status/open), 기본 포트는 PLAN에서 확정". → **기본 포트 7823 확정**.
- **[MUST] 배포 경계** — `docs/CONVENTIONS.md` §배포 경계: "`~/.opal/` 배포 파일을 직접 편집하지 않는다. 변경은 항상 프로젝트 소스에서 수행". → 소스는 `dashboard/`·`scripts/`·`opal/tools/`만 수정, `~/.opal/dashboard-server/`는 install이 생성.
- **[MUST] 플랫폼 분기 격리** — `docs/CONVENTIONS.md` §플랫폼 분기 격리: "플랫폼별 차이는 어댑터 계층에서만 흡수". → macOS/Windows 설치 차이는 install 스크립트에만, `console.sh`의 `open`/`xdg-open` 분기는 CLI 어댑터 내부 한정.

#### 3.11.3 환경 변경
빌드 도구: Node 18+ (Vite). install 시 `node --version` 체크 경고(ANALYSIS §5).

#### 3.11.4 배치/마이그레이션
install 실행이 빌드+배포. 별도 마이그레이션 없음.

#### 3.11.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-401 | R-7/H-1 | 통합 테스트 | `pip install fastapi[standard] --dry-run`이 starlette 1.0.0과 충돌 없이 통과 |
| TS-402 | R-7 AC | 통합 테스트 | install-mac.sh 실행 시 `~/.opal/dashboard-server/{dist,backend}` 배포. `opal-cli console start` → 7823 기동 → `open`으로 브라우저 표시 |
| TS-403 | H-8 | 회귀 테스트 | windows.ps1에 Install-Dashboard 동기화 반영(스크립트 리뷰) |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)

| Phase | 기능 | Step | agent | 실행 | 비고 |
|-------|------|------|-------|------|------|
| 1 | F-004(환경) | 1 | opal-be-agent | 순차(선행) | venv 호환 선검증(H-1) — 실패 시 전체 블로킹 |
| 1 | F-001,002,003 | 2,3,4 | opal-be-agent | 병렬 가능 | 독립 BE 모듈 (스캐너/어댑터/파서) |
| 1 | F-005(스캐폴딩) | 5 | opal-task-agent | 병렬 가능 | dashboard/ 디렉토리 + Vite/shadcn init |
| 2 | F-004(데몬) | 6 | opal-be-agent | 순차 | F-001~003 완료 후 라우터 통합 |
| 2 | F-005(셸+토큰) | 7 | opal-fe-agent | 순차 | 스캐폴딩 후 셸·토큰 |
| 3 | F-006~010 | 8,9,10,11,12 | opal-fe-agent | 병렬 가능 | 5개 화면 — 셸·API 완료 후 독립 |
| 4 | F-011 | 13,14 | opal-task-agent | 순차 | FE/BE 완료 후 설치+CLI |
| 4 | 문서 | 15 | PM 직접 | 순차 | docs/ 갱신 |

### 4.2 실행 체크리스트
> 총 15개 Step | Phase 4개 | 실행 모드: 복잡

#### Step 1: venv FastAPI 호환 선검증 + requirements.txt
- [x] 완료
- **소속 기능**: F-004
- **영역**: 환경
- **agent**: opal-be-agent
- **파일**: `opal/tools/requirements.txt`
- **작업 내용**: `~/.opal/.venv/bin/pip install fastapi[standard]>=0.110.0 --dry-run`로 starlette 1.0.0 호환 검증 후 통과 시 requirements.txt에 1줄 추가. 충돌 시 즉시 블로커 보고(호환 버전 핀 협의).
- **완료 기준**: dry-run 충돌 0건 + requirements.txt 반영
- **테스트**: TS-401
- **실행 방법**: sub-agent
- **의존**: 없음 (Phase 1 선행 — H-1)

#### Step 2: 프로젝트 스캐너 (scanner.py + config.py)
- [x] 완료
- **소속 기능**: F-001
- **영역**: BE
- **agent**: opal-be-agent
- **파일**: `dashboard/backend/scanner.py`, `dashboard/backend/config.py`
- **작업 내용**: os.walk + maxdepth 가드 + exclude로 `.opal/AGENT.md` 마커 발견. console.config.json 로드·기본값(`$HOME/workspace`, depth=2).
- **완료 기준**: 임의 경로에서 OPAL/비OPAL 구분 목록 반환, node_modules 미진입
- **테스트**: TS-101
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 3: 도구 어댑터 계층 (base + 4 어댑터)
- [x] 완료
- **소속 기능**: F-002
- **영역**: BE
- **agent**: opal-be-agent
- **파일**: `dashboard/backend/adapters/{base,state_adapter,scan_adapter,skill_adapter,doctor_adapter}.py`
- **작업 내용**: subprocess read-only 호출 + ok:false/exit≠0/timeout 3종 에러 정규화. doctor 텍스트 정규식 파싱. **쓰기 커맨드 금지**.
- **완료 기준**: 4개 도구 정상 JSON 파싱 + 에러 3종 구분
- **테스트**: TS-201, TS-202
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 4: 마크다운 파서 (4 파서)
- [x] 완료
- **소속 기능**: F-003
- **영역**: BE
- **agent**: opal-be-agent
- **파일**: `dashboard/backend/parsers/{memory_parser,memory_file_parser,project_parser,markdown_reader}.py`
- **작업 내용**: MEMORY.md 표·히스토리, memory/*.md 메타, PROJECT/AGENT.md, 산출물 원문 read. 읽기 전용.
- **완료 기준**: 각 파서 구조화 JSON 반환 + 파일 mtime 불변
- **테스트**: TS-301
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 5: FE 스캐폴딩 (Vite+React+TS+Tailwind+shadcn init)
- [x] 완료
- **소속 기능**: F-005
- **영역**: 공통
- **agent**: opal-task-agent
- **파일**: `dashboard/frontend/` (package.json, vite/tailwind/tsconfig, shadcn components.json)
- **작업 내용**: Vite 스캐폴딩 + Tailwind 4 + shadcn init + 의존성(TanStack Query/Zustand/Recharts/dnd-kit/router/lucide/react-markdown). **ReactFlow 제외**.
- **완료 기준**: `npm run dev` 기동 + shadcn add 가능 상태
- **테스트**: 빌드 성공
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 6: FastAPI 데몬 통합 (main + 라우터 5 + 캐시 + 모델)
- [x] 완료
- **소속 기능**: F-004
- **영역**: BE
- **agent**: opal-be-agent
- **파일**: `dashboard/backend/{main,cache,models}.py`, `dashboard/backend/routers/{dashboard,projects,tasks,memory,doctor}.py`
- **작업 내용**: 5개 화면 GET 엔드포인트 + /health. host=127.0.0.1:7823. 칸반 4컬럼 정규화. TTL 캐시. CORS dev/prod 분기.
- **완료 기준**: 5 엔드포인트 200 + 스키마 일치 + 127.0.0.1 바인딩
- **테스트**: TS-302, TS-310
- **실행 방법**: sub-agent
- **의존**: Step 1,2,3,4

#### Step 7: FE 앱 셸 + 디자인 토큰 (3색 전역화)
- [x] 완료
- **소속 기능**: F-005
- **영역**: FE
- **agent**: opal-fe-agent
- **파일**: `dashboard/frontend/src/index.css`, `components/app-shell/`, `lib/api.ts`, `store/ui-store.ts`, `router.tsx`
- **작업 내용**: :root 3색+상태색 토큰(다크 기본/라이트), Tailwind 토큰 바인딩, 5 네비 셸, 스위처, 상단바, QueryClient, 테마 토글. hex 하드코딩 금지.
- **완료 기준**: 셸 렌더 + 5 라우팅 + 다크/라이트 토글 + 토큰 1곳 정의 + hex 0건
- **테스트**: TS-501, TS-502
- **실행 방법**: sub-agent
- **의존**: Step 5

#### Step 8: 대시보드 화면 (F-006)
- [x] 완료
- **소속 기능**: F-006
- **영역**: FE
- **agent**: opal-fe-agent
- **파일**: `dashboard/frontend/src/pages/dashboard/`
- **작업 내용**: section-cards 4메트릭 + Recharts 활동추이/단계분포 + 주의알림 + 최근활동 테이블. brain 위젯 제외.
- **완료 기준**: `/api/dashboard` 실 데이터 렌더, brain 위젯 부재
- **테스트**: TS-601
- **실행 방법**: sub-agent
- **의존**: Step 6, 7

#### Step 9: 프로젝트 화면 (F-007)
- [x] 완료
- **소속 기능**: F-007
- **영역**: FE
- **agent**: opal-fe-agent
- **파일**: `dashboard/frontend/src/pages/projects/`
- **작업 내용**: 목록+도입현황+상세(탭)+문서 Drawer. 미적용 회색 처리.
- **완료 기준**: OPAL/미적용 구분 + 상세 + 문서 마크다운
- **테스트**: TS-701
- **실행 방법**: sub-agent
- **의존**: Step 6, 7

#### Step 10: 태스크 칸반 + 산출물 뷰어 (F-008)
- [x] 완료
- **소속 기능**: F-008
- **영역**: FE
- **agent**: opal-fe-agent
- **파일**: `dashboard/frontend/src/pages/tasks/`
- **작업 내용**: 상태 4컬럼 보드 + 카드 + Drawer(가로 스테퍼 + 산출물 탭 마크다운). dnd-kit 드래그 비활성 + 🔒 읽기 전용 badge.
- **완료 기준**: 카드 컬럼 배치 + 드래그 불가 + Drawer 스테퍼/산출물
- **테스트**: TS-801
- **실행 방법**: sub-agent
- **의존**: Step 6, 7

#### Step 11: 메모리 화면 (F-009)
- [x] 완료
- **소속 기능**: F-009
- **영역**: FE
- **agent**: opal-fe-agent
- **파일**: `dashboard/frontend/src/pages/memory/`
- **작업 내용**: 카테고리 리스트+태그 필터 + 히스토리 타임라인 + 상세 Drawer.
- **완료 기준**: 필터 동작 + 타임라인 + 마크다운
- **테스트**: TS-901
- **실행 방법**: sub-agent
- **의존**: Step 6, 7

#### Step 12: 환경(doctor) 화면 (F-010)
- [x] 완료
- **소속 기능**: F-010
- **영역**: FE
- **agent**: opal-fe-agent
- **파일**: `dashboard/frontend/src/pages/doctor/`
- **작업 내용**: doctor 4섹션 accordion + 체크 아이콘 + MCP 카드 + 스킬 목록 + 실패 alert.
- **완료 기준**: doctor/MCP/스킬 렌더 + 실패 alert
- **테스트**: TS-1001
- **실행 방법**: sub-agent
- **의존**: Step 6, 7

#### Step 13: opal-cli console 서브커맨드 (run.sh + lib/console.sh)
- [x] 완료
- **소속 기능**: F-011
- **영역**: 공통
- **agent**: opal-task-agent
- **파일**: `opal/tools/opal-cli/run.sh`, `opal/tools/opal-cli/lib/console.sh`
- **작업 내용**: dispatcher case에 `console` 추가 + usage 1줄 + cmd_console(start/stop/status/open, 포트 7823, 127.0.0.1).
- **완료 기준**: `opal-cli console status` 동작 (데몬 기동 시)
- **테스트**: TS-402(부분)
- **실행 방법**: sub-agent
- **의존**: Step 6

#### Step 14: install 스크립트 (macOS install_dashboard + Windows 동기화)
- [x] 완료
- **소속 기능**: F-011
- **영역**: 공통
- **agent**: opal-task-agent
- **파일**: `scripts/install-mac.sh`, `scripts/install/windows.ps1`
- **작업 내용**: install_dashboard() 신설 + install_opal_bin 근처 호출 + clean_dirs에 dashboard-server 추가. windows.ps1에 Install-Dashboard 동기화.
- **완료 기준**: install 실행 시 `~/.opal/dashboard-server/{dist,backend}` 배포 + opal-cli console 기동
- **테스트**: TS-402, TS-403
- **실행 방법**: sub-agent
- **의존**: Step 8~13

#### Step 15: docs/ 갱신 (ARCHITECTURE/PROJECT)
- [ ] 완료
- **소속 기능**: F-004, F-011
- **영역**: 문서
- **agent**: PM 직접
- **파일**: `docs/ARCHITECTURE.md`, `docs/PROJECT.md`
- **작업 내용**: OPAL Console 레이어(dashboard/ 소스 + dashboard-server 배포) + opal-cli console 서브커맨드를 시스템 구조·문서 허브에 반영.
- **완료 기준**: 신규 컴포넌트가 docs에 반영
- **테스트**: 문서 정합성 리뷰
- **실행 방법**: direct
- **의존**: Step 14

### 4.3 병렬/순차 판별 근거
| 관계 | 근거 |
|------|------|
| Step 1 → 나머지 | venv 호환 실패 시 BE 전체 블로킹(H-1) — 선행 게이트 |
| Step 2 ∥ 3 ∥ 4 ∥ 5 | 독립 모듈/디렉토리 (스캐너/어댑터/파서/FE 스캐폴딩) |
| Step 2,3,4 → 6 | 데몬이 스캐너·어댑터·파서를 import |
| Step 5 → 7 | 셸은 스캐폴딩(의존성·shadcn) 선행 필요 |
| Step 6,7 → 8~12 | 화면이 API + 셸·토큰·API 클라이언트 공유 |
| Step 8 ∥ 9 ∥ 10 ∥ 11 ∥ 12 | 독립 페이지 디렉토리 — 파일 충돌 없음 |
| Step 8~13 → 14 | install은 빌드 산출물(FE dist) + BE 소스 완성 필요 |
| Step 14 → 15 | docs는 구현 확정 후 갱신 |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA
| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | 프로젝트 발견 정확도 | TS-101 | OPAL N개 정확 반환 + 비OPAL 구분 + node_modules 미진입 |
| F-002 | 어댑터 정상/에러 | TS-201, TS-202 | 4도구 JSON 파싱 + 에러 3종 구분 |
| F-003 | 파서 구조화 | TS-301 | MEMORY/memory 구조화 + mtime 불변 |
| F-004 | API + 보안 바인딩 | TS-302, TS-310 | 5 엔드포인트 200 + 127.0.0.1 바인딩 |
| F-005 | 토큰 3색 전역화 | TS-501, TS-502 | :root 1곳 정의 + hex 0건 + 색 교체 일괄 반영 + 다크/라이트 |
| F-006 | 대시보드 렌더 | TS-601 | 4메트릭·차트·알림 + brain 위젯 부재 |
| F-007 | 프로젝트 화면 | TS-701 | 도입현황 + 상세 + 문서 |
| F-008 | 칸반 읽기 전용 | TS-801 | 컬럼 배치 + 드래그 불가 + Drawer 산출물 |
| F-009 | 메모리 화면 | TS-901 | 필터 + 타임라인 + 마크다운 |
| F-010 | 환경 화면 | TS-1001 | doctor/MCP/스킬 + 실패 alert |
| F-011 | 설치 + CLI | TS-401, TS-402, TS-403 | dry-run 통과 + 배포 + console 기동 + Windows 동기화 |

### 5.2 회귀 테스트
- [x] 기존 opal-cli 5개 서브커맨드(install/update/doctor/uninstall/mcp) 정상 동작 (console 추가가 회귀 유발 없음) <!-- Step 13: dispatcher case에 console만 추가, 기존 패턴 변경 없음 -->
- [x] install-mac.sh 기존 배포(skills/agents/...) 정상 (install_dashboard 추가가 기존 단계 무영향) <!-- Step 14: install_dashboard는 install_opal_bin 직후 독립 호출, 기존 단계 미수정 -->
- [x] 각 프로젝트의 state.json/MEMORY.md 무변경 (읽기 전용 — H-6) <!-- console.sh는 읽기/기동만, install_dashboard는 dashboard-server 배포만 -->

### 5.3 코드/문서 품질
- [x] 프로젝트 컨벤션 준수 (Python snake_case, FE kebab/PascalCase) <!-- Step 7: FE PascalCase 컴포넌트/kebab 파일명 준수 확인 -->
- [x] @header 규칙 (Python 파일 상단 헤더) <!-- Step 6: main/cache/models/routers/* 전부 @header 작성 완료 -->
- [ ] docs/ARCHITECTURE·PROJECT 갱신 (Step 15)
- [x] 변경이력 기록 (수정 스크립트·도구 변경이력 표) <!-- Step 13: run.sh v1.1 추가; Step 14: install-mac.sh v2.9, windows.ps1 v1.11.0 추가 -->

### 5.4 보안
- [x] 데몬 host=127.0.0.1 (외부 노출 금지 — H-7) <!-- Step 6: main.py uvicorn.run(host="127.0.0.1") + test_host_binding_is_localhost PASS -->
- [x] 쓰기 도구 커맨드 미호출 (read-only — TASK §결정적 제약) <!-- Step 6: 라우터 전부 GET + state.json read-only open()만 사용 -->
- [x] 프로젝트 파일 무변경 (SSOT 불변 — H-6) <!-- Step 6: 모든 파서/어댑터 read-only — test_all_parsers_mtime_invariant_real_files PASS -->
- [x] .env/시크릿 하드코딩 0건 + .gitignore에 node_modules/dist/__pycache__ <!-- Step 5: node_modules/dist 확인 완료. __pycache__는 BE 단계(Step 1-4) 확인 -->

---

## 6. 복잡도 판별
| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 15개 | 복잡 |
| 변경 파일 수 | 40+개 (신규 35+ / 수정 4) | 복잡 |
| 모듈 범위 | 다중 (FE/BE/설치/CLI) | 복잡 |
| 작업 유형 | 신규 개발(그린필드) | 복잡 |
| 외부 의존성 | 신규 패키지(FastAPI·shadcn·dnd-kit 등) + 신규 CLI 서브커맨드 | 복잡 |
| **실행 모드** | **복잡** | |

---

## 7. 실행 아키텍처 (복잡 모드)

### C-1. 에이전트 토폴로지
- **Batch 1** (병렬): opal-be-agent(Step 1 선행 → 2,3,4), opal-task-agent(Step 5 FE 스캐폴딩).
- **Batch 2** (병렬): opal-be-agent(Step 6 데몬), opal-fe-agent(Step 7 셸+토큰).
- **Batch 3** (병렬): opal-fe-agent(Step 8~12, 5개 화면 — 파일 충돌 없어 단일 에이전트 순차 또는 분할 병렬).
- **Batch 4** (순차): opal-task-agent(Step 13,14 설치+CLI) → PM(Step 15 docs).
- **파일 충돌 방지**: BE는 opal-be-agent로 응집, FE 화면은 페이지 디렉토리 분리로 충돌 없음, 설치/CLI는 opal-task-agent 단일.

### C-2. 스킬 요구사항
- EXECUTE: `op-dev-execute` (FE는 ui-designer plan-driven 모드 연동 — §3.N.2 화면 설계가 입력 계약).
- 갭 없음 (기존 스킬로 커버).

### C-3. 도구 요구사항
- CLI: Node 18+, npm (Vite 빌드), `~/.opal/.venv` python/uvicorn/pip.
- MCP: context7(FastAPI/React/shadcn/dnd-kit/TanStack docs), shadcn(컴포넌트 카탈로그), playwright(E2E 화면 검증).
- 패키지: `fastapi[standard]` (BE), FE npm 의존성 일괄.

### C-4. 테스트 전략 (opal-test-agent)
- BE 모드: pytest + httpx (어댑터/파서/라우터 TS-101~310).
- FE/E2E 모드: playwright MCP — 5개 화면 렌더(TS-501~1001) + 칸반 드래그 비활성(TS-801) + 색 교체(TS-501).
- 설치/CLI: bash 통합(`--dry-run` TS-401, install 배포 TS-402).
- 코드 품질: ruff(BE), eslint/tsc(FE), grep hex 스캔(TS-501).

---

## 8. 기술 컨텍스트

### 8.1 기술 스택
| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| FE | React 18 + TS 5 + Vite 5 + Tailwind 4 + shadcn/ui | ui-designer, vercel-labs/shadcn |
| FE 상태 | TanStack Query v5 + Zustand 4 | react-best-practices |
| FE 칸반/차트 | @dnd-kit 6 (비활성) + Recharts 2 | - |
| BE | Python 3.14 + FastAPI 0.136 + uvicorn 0.42 + pydantic 2.12 | modern-python |
| 설치/CLI | Bash(install-mac.sh) + PowerShell(windows.ps1) + opal-cli | - |

### 8.2 사용 MCP
| MCP | 조회 결과 요약 |
|-----|--------------|
| shadcn | sidebar-07/16, dashboard-01, chart-*, data-table, drawer/sheet 등 매핑 확정(WIREFRAME §0) |
| context7 | FastAPI/React/shadcn/dnd-kit/TanStack 최신 API (EXECUTE 시 참조) |
| playwright | 화면 렌더 E2E 검증 (TEST 단계) |

### 8.3 참조 문서 (설계 결정 근거)
| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | PROJECT.md | `docs/PROJECT.md` | 프로젝트 구조·2-레이어·C-9 SSOT 원칙 |
| D-2 | 설계 | AGENT.md (부트스트랩) | `~/.opal/AGENT.md` | `.opal/AGENT.md` 마커 판별(Step 6.5) |
| D-3 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | 배포 경계·플랫폼 분기·snake_case |
| D-4 | 설계 | AGENT.md (PM) | `.opal/AGENT.md` | 배포 경계 금지사항 |
| D-5 | 소스 | state.schema.json | `~/.opal/tools/state-tool/schema/state.schema.json` | current_status/status/stage enum |
| D-6 | 소스 | state-tool run.sh | `opal/tools/state-tool/run.sh:1-12` | venv python 래퍼 호출 |
| D-7 | 소스 | code-scan | `~/.opal/tools/code-scan/code-scan.js` | scan --json 스키마 |
| D-8 | 소스 | opal-cli run.sh | `opal/tools/opal-cli/run.sh:109,113-117` | dispatcher case 확장 지점 |
| D-9 | 소스 | install-mac.sh | `scripts/install-mac.sh:196,866,1059` | install_dir·clean_dirs·호출 지점 |
| D-10 | 외부 | FastAPI | [FastAPI](https://fastapi.tiangolo.com) | 데몬 패턴·host 바인딩 |
| D-11 | 외부 | shadcn/ui | [shadcn/ui](https://ui.shadcn.com) | 컴포넌트·블록 |
| D-12 | 기획 | TASK.md | `tasks/021-260615-opd-opal-console/TASK.md` | 요구사항·제약·C-2/C-11/C-12 |
| D-13 | 기획 | ANALYSIS.md | `tasks/021-260615-opd-opal-console/ANALYSIS.md` | 실측 스키마·U-1~U-8 권고 |
| D-14 | 기획 | WIREFRAME.md | `tasks/021-260615-opd-opal-console/WIREFRAME.md` | 화면 레이아웃·shadcn 매핑·상태색 |

> 인용 형식: `opal/core/references/harness/citation-rules.md` §3.1. 유형: 기획/설계/소스/외부.

---

## 9. 리스크 및 대응 (기능-리스크 연결)
| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| 1 | venv starlette↔fastapi 충돌 | F-004 | P0 | Step 1 pip --dry-run 선검증, 충돌 시 버전 핀 블로커 보고(H-1) |
| 2 | doctor 텍스트 파싱 취약 | F-002 | P1 | 버전 고정 정규식 + 파싱 실패 graceful 폴백(H-2) |
| 3 | 어댑터 에러 미구분 | F-002 | P1 | base.py 3종 에러 정규화 → 503/504(H-3) |
| 4 | 스캔 성능/행 | F-001 | P1 | maxdepth + exclude 가드(H-4) |
| 5 | 색 교체 불가/hex 잔존 | F-005 | P0 | :root 1곳 토큰 + grep hex 0건 검증(H-5, TS-501) |
| 6 | SSOT 파일 오염 | F-003,004 | P0 | read-only open만 + mtime 불변 검증(H-6) |
| 7 | 외부 노출 | F-004 | P0 | 127.0.0.1 바인딩(H-7) |
| 8 | Windows 미동기화 | F-011 | P2 | Step 14에 windows.ps1 동기화 포함(H-8) |
| 9 | 칸반 드래그 잔존 | F-008 | P1 | dnd-kit sensors 비활성 + 읽기 전용 badge(H-9) |

---

## 품질 체크리스트
- [x] 이 PLAN만 보고 바로 구현 가능 (파일 경로·시그니처·엔드포인트·토큰 명세)
- [x] 기능 목록(§1.2)이 R-1~R-7 커버 (R-8은 WIREFRAME으로 충족)
- [x] Multi-Feature §2·§3 F-NNN 구조화
- [x] 관련 파일 맵 6영역 분류
- [x] §3.N.5 테스트 시나리오 TS↔AC 매핑
- [x] §4.2 각 Step 소속 F-ID·영역·agent 명시
- [x] §5.1 기능-QA 매트릭스 모든 F 커버
- [x] FE 화면 §3.N.2 "##### 화면" 포맷 (FE-0~5)
- [x] ANALYSIS 제약/리스크 반영 (§5 → H-1~H-9)
- [x] 관련 코드 실측 (run.sh:109, install-mac.sh:196/866/1059)
- [x] 인라인 인용 + §8.3 참조 테이블
- [x] [MUST] 포맷 (C-2/C-11/C-12·배포 경계·플랫폼 분기·보안)
- [x] C-11 브레인 전면 제외 반영 (어댑터/파서/화면/위젯)
