# PLAN: OPAL Console 프로젝트별 환경 설정 화면 — 프라임 풀 토글 + console.config + 프로젝트 로컬 설정

> 작성일: 2026-07-14 | 입력: TASK.md, ANALYSIS.md
> 모드: Multi-Feature | 실행 모드: 복잡

---

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

OPAL Console에 프로젝트별 환경 설정 화면(`/settings`)을 신설하여, ① 프라임 풀 토글 ② `console.config.json` 전반 ③ 프로젝트 로컬 `.opal/setting.local.json`을 화면에서 조회·변경한다. 콘솔 "읽기 전용" 원칙의 예외는 브레인 POST 라우터 격리 선례를 따라 **설정 라우터 1곳에만 쓰기를 허용**하고, 쓰기 대상 파일을 명시 화이트리스트(`~/.opal/console.config.json` + `{스캔된 프로젝트}/.opal/setting.local.json`)로 한정한다 (→ D-1 §설계 방향). 기존 read-only API 5종 + 브레인 POST 계약은 불변으로 유지한다 (→ D-2 §목표 달성).

### 1.2 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | 설정 쓰기 인프라 — 라우터 골격 + 경로검증/화이트리스트 헬퍼 + `config.save_config`/`save_project_local` 원자적 쓰기 | R-1 | P0 | 없음 |
| F-002 | 프라임 풀 토글 엔드포인트 — `POST /api/config/prewarm` + `prewarm()` 즉시 호출 | R-2 | P0 | F-001 |
| F-003 | console.config 전반 관리 — `GET /api/config` + `POST /api/config/console`(머지 보존) | R-3 | P0 | F-001 |
| F-004 | 프로젝트 로컬 설정 편집 — `GET`/`POST /api/config/project-local` + Pydantic `extra="forbid"` | R-4 | P0 | F-001 |
| F-005 | 설정 화면(FE) 신설 — `/settings` 라우트 + `SettingsPage` + 네비/설정 버튼 연결 | R-5 | P0 | F-002, F-003, F-004 |

### 1.3 기능 의존 그래프 (ASCII)

```
F-001 ─┬─ F-002 ─┐
       ├─ F-003 ─┼─ F-005
       └─ F-004 ─┘
```

F-001(쓰기 인프라)이 F-002~F-004 엔드포인트의 공통 토대. F-002~F-004는 서로 독립(다른 엔드포인트·다른 검증 계약)이라 병렬 가능. F-005(FE)는 세 엔드포인트의 API 계약이 고정된 후 착수.

---

## 리스크 가설 표

> PLAN 단계에서 작성. TEST-SCENARIO.md §1의 입력이 됨.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | F-001 경로 검증 + 화이트리스트 (`routers/config.py`) | path traversal — `..`·심볼릭·비스캔 경로로 화이트리스트 외 파일 쓰기 | **P0** | L1(단위) + L2(실 FS) 의무 | S-후보-1 |
| H-2 | F-001 `config.save_config` read-modify-write 사이클 | 동시 쓰기 시 기존 키 유실 / 부분 쓰기로 파일 파손 (JSON 깨짐) | **P0** | L1 + L2(동시성·원자성) 의무 | S-후보-2 |
| H-3 | F-003 `console.config.json` 머지 보존 | `scan_roots`/`scan_depth`/`exclude` 등 기존 키가 `prewarm_projects`만 갱신 시 유실 | P1 | L1(단위) 3시나리오 의무 | S-후보-3 |
| H-4 | F-004 `setting.local.json` 스키마 검증 | `bootstrap`/`models` 외 필드 허용 시 오염 / 유효 JSON 위반 저장 통과 | P1 | L1(단위) 생성·갱신·거부 3경로 | S-후보-4 |
| H-5 | F-002 `prewarm()` 즉시 호출 | 토글 ON 시 config 반영 없이 prewarm만 되거나 / prewarm이 블로킹되어 응답 지연 | P1 | L1 + L2(config 반영 검증) | S-후보-5 |
| H-6 | F-001 라우터 등록 + CORS | 신규 POST 라우터가 기존 5 read-only 라우터의 405 계약을 깨뜨림 / CORS 정책 변경 | **P0** | L2(회귀·기존 API 계약 불변) | S-후보-6 |
| H-7 | F-004 프로젝트 경로 소실 | `scan_projects`가 삭제/이동된 프로젝트에 대해 빈 목록 반환 → 저장 대상 경로 소실 시 500 | P2 | L1(400 방어) | S-후보-4 |
| H-8 | 배포 경계 (전 기능) | 소스(`dashboard/`) 수정 없이 `~/.opal/` 배포본 직접 편집 시 다음 install에 유실 | P1 | 산출물 검사(소스 위치) | S-후보-검토 |

---

## 2. 기능별 분석

### F-001: 설정 쓰기 인프라

#### 2.1.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| BE | `dashboard/backend/routers/config.py` | 설정 쓰기 라우터(신규) — 경로검증·화이트리스트·엔드포인트 | 신규 |
| BE | `dashboard/backend/config.py` | `save_config`/`save_project_local` 원자적 쓰기 함수 추가 | 수정 |
| BE | `dashboard/backend/main.py` | 신규 config 라우터 등록 | 수정 |
| BE | `dashboard/backend/scanner.py` | `scan_projects` 재사용(화이트리스트 검증) — 변경 없음 | - |
| BE | `dashboard/backend/models.py` | 요청/응답 Pydantic 모델 추가 | 수정 |
| BE(test) | `dashboard/backend/tests/test_config.py` | `save_config`/`save_project_local` 쓰기 테스트 | 수정 |
| BE(test) | `dashboard/backend/tests/test_routers.py` | 설정 라우터 400/200·화이트리스트 케이스 | 수정 |

#### 2.1.2 현재 구현

- `config.py`는 **읽기 전용** — `load_config()`만 존재하며 쓰기 함수 없음 (`dashboard/backend/config.py:45-66`). `CONFIG_PATH = Path.home()/".opal"/"console.config.json"` (`config.py:23`), `_coerce_str_list` 타입 가드 존재 (`config.py:38-42`).
- 브레인 라우터의 경로 검증 선례: `_resolve_project_path`(스캔 목록 매칭) + `_require_project_path`(실패 시 400) (`dashboard/backend/routers/brain.py:42-76`).
- 백그라운드 비블로킹 패턴: `threading.Thread(target=..., daemon=True).start()` 후 즉시 반환 (`brain.py:190-197`).
- `scan_projects(roots, depth, exclude)`는 `.opal/AGENT.md` 마커로 OPAL 프로젝트를 발견하며 읽기 전용 (`dashboard/backend/scanner.py:39-72`).

#### 2.1.3 영향 범위

- **상위 의존(호출자)**: FE `SettingsPage` → `apiClient.post('/api/config/...')`.
- **하위 의존(피호출자)**: `config.save_config`/`save_project_local`, `scan_projects`(화이트리스트), `brain_session_registry.prewarm`(F-002).
- **공유 상태**: `~/.opal/console.config.json` — 브레인 lifespan 선프라임(`main.py:57`)과 `opal-cli console scan`이 동일 파일을 읽는다 → 머지 보존 필수(H-3).
- **관련 테스트**: `test_config.py`(monkeypatch CONFIG_PATH 격리), `test_routers.py`(TestClient + 405/400 계약).

---

### F-002: 프라임 풀 토글 엔드포인트

#### 2.2.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| BE | `dashboard/backend/routers/config.py` | `POST /api/config/prewarm` 핸들러 | 수정(F-001 기반) |
| BE | `dashboard/backend/adapters/brain_session.py` | `BrainSessionRegistry.prewarm()` 재사용 — 변경 없음 | - |

#### 2.2.2 현재 구현

- `brain_session_registry.prewarm(project_path)`는 풀 목표치 미달 시 daemon 스레드 1개 기동, 이미 채워졌으면 즉시 반환하는 **비블로킹** 함수 (`dashboard/backend/adapters/brain_session.py:558-571`).
- 기동 시 lifespan이 `cfg.prewarm_projects`를 순회하며 prewarm 호출 (`main.py:42-63`).

#### 2.2.3 영향 범위

- ON 시: `prewarm_projects`에 추가(config 쓰기) + `prewarm()` 1회 호출(즉시 반환). OFF 시: 목록에서 제거만 — 현재 인메모리 풀은 유지(무상태 원칙, 다음 재기동부터 제외). (→ ANALYSIS §4.4)
- prewarm은 내부에서 daemon 스레드로 분리되어 API 응답을 블로킹하지 않음(H-5).

---

### F-003: console.config 전반 관리

#### 2.3.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| BE | `dashboard/backend/routers/config.py` | `GET /api/config` + `POST /api/config/console` | 수정(F-001 기반) |
| BE | `dashboard/backend/config.py` | `save_config(updates: dict)` 머지 보존 | 수정 |

#### 2.3.2 현재 구현

- `load_config()`는 `scan_roots`/`scan_depth`/`exclude`/`prewarm_projects` 4필드를 dataclass로 반환 (`config.py:45-66`). 현재 파일에 쓰기 경로 없음.

#### 2.3.3 영향 범위

- `POST /api/config/console`은 `scan_roots`/`scan_depth`/`exclude`/`prewarm_projects` 중 전달된 키만 부분 갱신 — 나머지 기존 키 유실 금지(H-3). `opal-cli console scan`이 관리하는 동일 파일이므로 스캔이 추가하는 미지 키(future field)도 보존해야 함 → 원본 dict 기반 머지(dataclass 재직렬화 아님).

---

### F-004: 프로젝트 로컬 설정 편집

#### 2.4.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| BE | `dashboard/backend/routers/config.py` | `GET`/`POST /api/config/project-local` | 수정(F-001 기반) |
| BE | `dashboard/backend/config.py` | `save_project_local(project_path, updates)` 원자적 쓰기 | 수정 |
| BE | `dashboard/backend/models.py` | `SettingLocalUpdate`(`extra="forbid"`) 요청 모델 | 수정 |

#### 2.4.2 현재 구현

- 전역 `~/.opal/setting.json` 구조: `{"bootstrap": "on"|"off", "models": {"platform": "auto", "claude": {"light","standard","advanced"}, ...}}` (`~/.opal/setting.json`). 로컬 `.opal/setting.local.json`은 전역 위에 **셀 단위 오버라이드**(로컬 우선, 없는 셀은 전역)이며 현재 이 프로젝트에는 파일 부재.
- 프로젝트 부트스트랩 게이트가 `setting.local.json`의 `bootstrap`·`models`를 전역 위에 머지 (CLAUDE.md OPAL 부트스트랩 §스킵 게이트).

#### 2.4.3 영향 범위

- 쓰기 대상이 콘솔 관리 파일 밖(프로젝트 파일)으로 확장 → 경로 탈출 방어 비중 최대(H-1, R-PATH-001 Critical).
- 스키마: `bootstrap`·`models` 2필드만 화이트리스트. `models` 하위는 셀 오버라이드 계약상 부분 지정이 정상이므로 하위 강제 스키마를 두지 않음(§3.4.2 결정).

---

### F-005: 설정 화면(FE) 신설

#### 2.5.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| FE | `dashboard/frontend/src/pages/settings/SettingsPage.tsx` | 설정 화면(신규) — 3섹션 폼 | 신규 |
| FE | `dashboard/frontend/src/router.tsx` | `/settings` 라우트 추가 | 수정 |
| FE | `dashboard/frontend/src/components/app-shell/AppShell.tsx` | NAV_ITEMS "설정" 추가 + TopBar 설정 버튼 `/settings` 연결 | 수정 |

#### 2.5.2 현재 구현

- 6개 라우트(`/ /projects /tasks /memory /doctor /brain`)를 AppShell로 래핑, 절대경로 식별자는 searchParams(`?project=`) 방식 (`dashboard/frontend/src/router.tsx:22-38`).
- `NAV_ITEMS` 6개 배열 (`AppShell.tsx:74-81`), TopBar에 **이미 Settings 아이콘 버튼이 있으나 현재 no-op**(`AppShell.tsx` TopBar 설정 툴팁 버튼).
- `apiClient<T>(path, options)` fetch 래퍼 — `POST`는 `{method:'POST', body: JSON.stringify(...)}` 형태 (`dashboard/frontend/src/lib/api.ts`). `contextProject`(ui-store)로 프로젝트 스위처 연동 (`DoctorPage` 선례).

#### 2.5.3 영향 범위

- 라우트 7개로 확장. `contextProject` 구독으로 프라임 토글·로컬 설정의 대상 프로젝트를 스위처와 동기화.

---

## 3. 기능별 설계

### F-001: 설정 쓰기 인프라

#### 3.1.1 파일 변경 계획

**신규 생성**
| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `dashboard/backend/routers/config.py` | BE | 설정 쓰기 라우터 + 경로검증·화이트리스트 헬퍼 | (→ D-7:42-76 선례) |

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `dashboard/backend/config.py` | BE | `save_config`/`save_project_local` + `_atomic_write_json` 추가 | `config.py:45-66` |
| 2 | `dashboard/backend/main.py` | BE | `from ...routers import config` + `app.include_router(config.router)` | `main.py:29,99` |
| 3 | `dashboard/backend/models.py` | BE | 설정 요청/응답 모델 추가 | `models.py:189` |

#### 3.1.2 API·데이터 모델·화면 설계

**경로 검증 · 화이트리스트 헬퍼** (brain.py 선례 재사용, → D-7:42-76):

```python
# routers/config.py
def _require_project_path(project: str) -> str:
    """project 검증 후 절대경로 반환. 빈값/비스캔 → HTTPException(400)."""
    # brain.py _require_project_path와 동일 계약 — scan_projects 화이트리스트 매칭

def _resolve_setting_local_path(project_path: str) -> Path:
    """검증된 project_path 하위의 setting.local.json 경로를 안전 구성.
    [MUST] 고정 구성 + resolve() 검증으로 path traversal 차단."""
    base = Path(project_path).resolve()
    target = (base / ".opal" / "setting.local.json").resolve()
    if base not in target.parents:          # target이 base 하위임을 강제
        raise HTTPException(status_code=400, detail="허용되지 않은 설정 파일 경로입니다.")
    return target
```

> [MUST] `.opal/memory/061_콘솔_설정_화면_예약.md` §설계 방향: "설정 라우터만 쓰기 허용, 쓰기 대상 파일을 명시 화이트리스트로 한정." → 쓰기 대상은 `~/.opal/console.config.json`(F-002·F-003) + `{스캔된 프로젝트}/.opal/setting.local.json`(F-004) **2종만**. FE가 보낸 파일 경로 문자열은 절대 신뢰하지 않고, 검증된 `project_path`로부터 서버가 고정 구성한다 (→ R-PATH-001 Critical).

> [MUST] `dashboard/backend/routers/brain.py` @header: "LLM 호출은 이 라우터에만 격리" → 설정 라우터는 LLM/claude 서브프로세스 호출 0회 — 파일 쓰기 + `prewarm()` 호출만 수행한다.

**원자적 쓰기 함수** (config.py, ANALYSIS §2.1 정정 반영):

```python
# config.py — 모듈 레벨
_WRITE_LOCK = threading.Lock()   # read-modify-write 사이클 직렬화

def _atomic_write_json(path: Path, data: dict) -> None:
    """temp 파일 쓰기 후 os.replace로 atomic rename (부분 쓰기·파손 방지)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".tmp.{os.getpid()}")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)        # 동일 파일시스템 내 atomic rename (POSIX 보장)

def save_config(updates: dict) -> dict:
    """console.config.json 머지 보존 쓰기. 기존 키 유실 금지(H-3)."""
    with _WRITE_LOCK:
        existing = {}
        if CONFIG_PATH.exists():
            try:
                existing = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                existing = {}
        existing.update(updates)          # 부분 갱신 — 미전달 키 보존
        _atomic_write_json(CONFIG_PATH, existing)
        return existing

def save_project_local(target: Path, updates: dict) -> dict:
    """setting.local.json 머지 보존 쓰기. target은 라우터가 검증·구성한 Path."""
    with _WRITE_LOCK:
        existing = {}
        if target.exists():
            try:
                existing = json.loads(target.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                existing = {}
        existing.update(updates)
        _atomic_write_json(target, existing)
        return existing
```

> [MUST] 동시 쓰기 전략 — ANALYSIS §2.1의 "`open('w')` 단일 호출이 원자"는 부정확하다(POSIX에서 `truncate+write`는 원자가 아니며, read-modify-write 사이클은 더더욱 아니다). 본 설계는 ① 모듈 레벨 `threading.Lock`으로 사이클 전체를 직렬화 + ② temp 파일 쓰기 후 `os.replace`(atomic rename)로 독자에게 부분 쓰기가 노출되지 않도록 방어한다 (→ D-8 §2.1 정정, R-CONCURRENT-002 대응).

**Pydantic 응답 모델** (models.py):

```python
class ConsoleConfigResponse(BaseModel):
    scan_roots: list[str]
    scan_depth: int
    exclude: list[str]
    prewarm_projects: list[str]

class ConfigWriteResponse(BaseModel):
    ok: bool = True
    config: dict = {}          # 갱신 후 스냅샷
```

- 근거: `models.py:189-238` 기존 Brain 모델 스타일 준수 (`BaseModel` 상속).

#### 3.1.3 환경 변경
해당 없음 (신규 패키지 없음 — `threading`/`json`/`pathlib`/`os` 표준 라이브러리).

#### 3.1.4 배치/마이그레이션
해당 없음.

#### 3.1.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | R-1 AC | 보안 테스트 | 빈 project → 400 |
| TS-002 | R-1 AC | 보안 테스트 | 비스캔 프로젝트 경로 → 400 |
| TS-003 | R-1 AC | 보안 테스트 | `../`·심볼릭 등 화이트리스트 외 경로 주입 → 400 (path traversal 차단) |
| TS-004 | R-1 AC | 기능 테스트 | `_atomic_write_json` — temp 후 os.replace로 원본 갱신, 중간 파손 없음 |
| TS-005 | R-1 AC | 통합 테스트 | 동시 2요청 read-modify-write 후 두 갱신 모두 반영(키 유실 0) |

---

### F-002: 프라임 풀 토글 엔드포인트

#### 3.2.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `dashboard/backend/routers/config.py` | BE | `POST /api/config/prewarm` 핸들러 | `brain.py:190-197` |
| 2 | `dashboard/backend/models.py` | BE | `PrewarmToggleRequest` | `models.py:189` |

#### 3.2.2 API·데이터 모델 설계

**엔드포인트**: `POST /api/config/prewarm`

```python
class PrewarmToggleRequest(BaseModel):
    project: str          # 절대경로. 필수 — 빈값/비스캔 400
    enabled: bool

@router.post("/api/config/prewarm", response_model=ConfigWriteResponse)
def post_prewarm(body: PrewarmToggleRequest) -> ConfigWriteResponse:
    project_path = _require_project_path(body.project)      # 400 게이트
    cfg = load_config()
    projects = list(cfg.prewarm_projects)
    if body.enabled and project_path not in projects:
        projects.append(project_path)
    elif not body.enabled and project_path in projects:
        projects.remove(project_path)
    snapshot = save_config({"prewarm_projects": projects})  # 머지 보존
    if body.enabled:
        brain_session_registry.prewarm(project_path)        # 즉시 선프라임(비블로킹, 재기동 불요)
    return ConfigWriteResponse(config=snapshot)
```

> R-2 AC 충족: ON 시 `prewarm_projects` 추가 + `prewarm()` 1회 호출로 재기동 없이 즉시 선프라임(내부 daemon 스레드로 비블로킹, → `brain_session.py:558-571`). OFF 시 목록 제거만, 현재 인메모리 풀은 유지(무상태 원칙 — 다음 재기동부터 제외, → ANALYSIS §4.4).

#### 3.2.3 환경 변경
해당 없음.

#### 3.2.4 배치/마이그레이션
해당 없음.

#### 3.2.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-010 | R-2 AC | 기능 테스트 | ON → `prewarm_projects`에 project_path 추가 + config 파일 반영 |
| TS-011 | R-2 AC | 기능 테스트 | ON → `brain_session_registry.prewarm` 1회 호출(monkeypatch spy로 검증) |
| TS-012 | R-2 AC | 기능 테스트 | OFF → 목록에서 제거, config 파일 반영 |
| TS-013 | R-2 AC | 회귀 테스트 | 중복 ON 시 목록에 1회만 존재(멱등) |

---

### F-003: console.config 전반 관리

#### 3.3.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `dashboard/backend/routers/config.py` | BE | `GET /api/config` + `POST /api/config/console` | (→ D-8) |
| 2 | `dashboard/backend/models.py` | BE | `ConsoleConfigUpdate`(부분 갱신) | `models.py:189` |

#### 3.3.2 API·데이터 모델 설계

```python
class ConsoleConfigUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")     # 미지 최상위 필드 거부
    scan_roots: list[str] | None = None
    scan_depth: int | None = None
    exclude: list[str] | None = None
    prewarm_projects: list[str] | None = None

@router.get("/api/config", response_model=ConsoleConfigResponse)
def get_config() -> ConsoleConfigResponse:
    cfg = load_config()
    return ConsoleConfigResponse(**asdict(cfg))

@router.post("/api/config/console", response_model=ConfigWriteResponse)
def post_console(body: ConsoleConfigUpdate) -> ConfigWriteResponse:
    updates = body.model_dump(exclude_none=True)  # 전달된 키만
    snapshot = save_config(updates)               # 머지 보존 — 미전달·미지 키 유지(H-3)
    return ConfigWriteResponse(config=snapshot)
```

> R-3 AC 충족: `save_config`는 원본 파일 dict를 읽어 `update()`하므로 `scan_roots`/`scan_depth`/`exclude` 및 `opal-cli console scan`이 관리하는 미지 future 키까지 보존한다 (→ D-8, R-MERGE-004). 3시나리오 테스트: (a) 신규 키 추가 시 기존 유지 (b) 기존 키 변경 (c) 부분 갱신 후 재로드 검증.

> [MUST] `docs/CONVENTIONS.md` §배포 경계: "`~/.opal/` 배포 파일을 직접 편집하지 않는다. 변경은 항상 프로젝트 소스에서 수행한다." → 소스는 `dashboard/backend/` + `dashboard/frontend/src/`에서만 수정하고 install 재배포로 반영한다. 단, **런타임 쓰기 대상**인 `~/.opal/console.config.json`·`{프로젝트}/.opal/setting.local.json`은 코드 배포물이 아닌 사용자 데이터 파일이므로 이 경계의 적용 대상이 아니다(정상 쓰기).

#### 3.3.3 환경 변경
해당 없음.

#### 3.3.4 배치/마이그레이션
해당 없음.

#### 3.3.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-020 | R-3 AC | 기능 테스트 | `GET /api/config` → 4필드 스냅샷 반환 |
| TS-021 | R-3 AC | 기능 테스트 | `prewarm_projects`만 갱신 시 `scan_roots` 등 기존 키 유지(머지 보존) |
| TS-022 | R-3 AC | 기능 테스트 | 파일에 있던 미지 future 키가 갱신 후에도 보존 |
| TS-023 | R-3 AC | 보안 테스트 | 미지 최상위 필드 페이로드 → 422(`extra="forbid"`) |

---

### F-004: 프로젝트 로컬 설정 편집

#### 3.4.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `dashboard/backend/routers/config.py` | BE | `GET`/`POST /api/config/project-local` | (→ D-7:42-76) |
| 2 | `dashboard/backend/config.py` | BE | `save_project_local` 사용 | §3.1.2 |
| 3 | `dashboard/backend/models.py` | BE | `SettingLocalUpdate`(`extra="forbid"`) | R-SETTING-006 |

#### 3.4.2 API·데이터 모델 설계

**스키마 결정** — `bootstrap`·`models` 2필드만 최상위 화이트리스트(`extra="forbid"`). `models` 하위는 셀 단위 오버라이드 계약이라 강제 스키마를 두지 않고 dict로 통과:

```python
class SettingLocalUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")      # bootstrap/models 외 최상위 필드 거부
    project: str                                   # 대상 프로젝트 절대경로(필수)
    bootstrap: Literal["on", "off"] | None = None  # 전역과 동일 도메인값
    models: dict | None = None                     # 셀 단위 오버라이드(부분 지정 정상)

@router.get("/api/config/project-local", response_model=dict)
def get_project_local(project: str = Query(...)) -> dict:
    project_path = _require_project_path(project)
    target = _resolve_setting_local_path(project_path)
    if not target.exists():
        return {"exists": False, "bootstrap": None, "models": None}
    return {"exists": True, **json.loads(target.read_text(encoding="utf-8"))}

@router.post("/api/config/project-local", response_model=ConfigWriteResponse)
def post_project_local(body: SettingLocalUpdate) -> ConfigWriteResponse:
    project_path = _require_project_path(body.project)          # 400 게이트
    target = _resolve_setting_local_path(project_path)          # 화이트리스트 고정 구성
    updates = body.model_dump(exclude_none=True, exclude={"project"})
    snapshot = save_project_local(target, updates)              # 생성/갱신 머지 보존
    return ConfigWriteResponse(config=snapshot)
```

> [MUST] `docs/ARCHITECTURE.md` §OPAL Console 원칙: "읽기 전용(쓰기/편집은 2차) · 데이터 SSOT는 각 프로젝트 파일 · 데몬은 도구 오케스트레이터" → 로컬 설정의 SSOT는 대상 프로젝트의 `.opal/setting.local.json`이며, 콘솔은 이를 편집하는 도구 오케스트레이터로만 동작한다.

> R-4 스키마 결정 근거: 전역 `~/.opal/setting.json`은 `bootstrap`("on"/"off")과 `models.{platform}.{light|standard|advanced}` 구조이고, 로컬은 "바꿀 셀만 덮어쓴다"(로컬 우선·없는 셀 전역, → CLAUDE.md OPAL 부트스트랩 §스킵 게이트). 따라서 `models` 하위에 3레벨 강제 스키마를 두면 셀 단위 부분 오버라이드가 막힌다 → 최상위 2필드만 `extra="forbid"`로 화이트리스트하고 `models` 하위는 dict 통과. 이것이 R-4 AC "유효하지 않은 JSON 구조 거부"(=미지 최상위 필드·잘못된 bootstrap 값 거부)를 충족하면서 오버-검증을 피한다.

#### 3.4.3 환경 변경
해당 없음.

#### 3.4.4 배치/마이그레이션
해당 없음 — `setting.local.json`은 부재 시 신규 생성(마이그레이션 아님).

#### 3.4.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-030 | R-4 AC | 기능 테스트 | 파일 부재 프로젝트 → 저장 시 `.opal/setting.local.json` 신규 생성 |
| TS-031 | R-4 AC | 기능 테스트 | 기존 파일 → `bootstrap`만 갱신, `models` 기존 값 보존(머지) |
| TS-032 | R-4 AC | 보안 테스트 | `bootstrap: "maybe"`(도메인 위반) → 422 |
| TS-033 | R-4 AC | 보안 테스트 | 미지 최상위 필드(`evil: 1`) → 422(`extra="forbid"`) |
| TS-034 | R-4 AC | 보안 테스트 | 비스캔 project → 400, 쓰기 미발생 |
| TS-035 | R-4 AC | 기능 테스트 | `GET /api/config/project-local` → 저장값 재조회 반영 |

---

### F-005: 설정 화면(FE) 신설

#### 3.5.1 파일 변경 계획

**신규 생성**
| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `dashboard/frontend/src/pages/settings/SettingsPage.tsx` | FE | 설정 화면 3섹션 폼 | (→ DoctorPage 선례) |

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `dashboard/frontend/src/router.tsx` | FE | `{ path: "settings", element: <SettingsPage /> }` 추가 | `router.tsx:22-38` |
| 2 | `dashboard/frontend/src/components/app-shell/AppShell.tsx` | FE | NAV_ITEMS "설정" 추가 + TopBar 설정 버튼 → `/settings` NavLink | `AppShell.tsx:74-81` |

#### 3.5.2 화면 설계

##### 화면: 설정
- **ID**: FE-1
- **유형**: settings
- **action**: new
- **경로**: `/settings` (프로젝트별 항목은 `?project=<절대경로>` searchParam + `contextProject` 스위처 연동)
- **파일**: `dashboard/frontend/src/pages/settings/SettingsPage.tsx`, `dashboard/frontend/src/router.tsx`, `dashboard/frontend/src/components/app-shell/AppShell.tsx`
- **shadcn 컴포넌트**: Card, CardHeader, CardTitle, CardContent, Switch, Input, Label, Button, Separator, Alert, Badge, Skeleton, Tooltip
- **UI 작업**: 3섹션 카드 폼 — (1) **프라임 풀 토글**: 스위처 선택 프로젝트에 대한 ON/OFF Switch(즉시 `POST /api/config/prewarm`, optimistic + 재조회) (2) **console.config**: `scan_roots`(문자열 리스트 편집), `scan_depth`, `exclude`, `prewarm_projects` 조회/편집 후 저장(`POST /api/config/console`) (3) **프로젝트 로컬 설정**: 선택 프로젝트의 `bootstrap`(on/off Switch)·`models`(JSON textarea 또는 셀 편집) 조회(`GET /api/config/project-local`)·저장(`POST /api/config/project-local`). 저장 실패(4xx/422)는 Alert로 사유 표시. 프로젝트 미선택 시 (1)(3) 섹션은 "프로젝트를 선택하세요" 안내.
- **API 연동**: `GET /api/config`(초기 로드), `POST /api/config/prewarm`(토글), `POST /api/config/console`(config 저장), `GET /api/config/project-local?project=`(로컬 조회), `POST /api/config/project-local`(로컬 저장). 모두 `apiClient` 경유(`lib/api.ts`), 변경 후 `queryClient.invalidateQueries`로 재조회 반영(R-5 AC).

#### 3.5.3 환경 변경
- Switch 컴포넌트 미존재 시 shadcn Switch 추가(`components/ui/switch.tsx`) — 프로젝트 UI 규칙 준수(ui-designer). 존재 여부는 EXECUTE 착수 시 확인.

#### 3.5.4 배치/마이그레이션
해당 없음.

#### 3.5.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-040 | R-5 AC | 기능 테스트 | `/settings` 진입 시 3섹션 렌더 + `GET /api/config` 로드 |
| TS-041 | R-5 AC | 기능 테스트 | 토글 변경 → API 호출 후 재조회 시 상태 반영 |
| TS-042 | R-5 AC | 기능 테스트 | 로컬 설정 저장 → 재조회 시 값 반영 표시 |
| TS-043 | R-5 AC | 기능 테스트 | 저장 실패(422) → Alert 사유 표시, 화면 비파괴 |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)

| Phase | 기능 | Step | agent | 실행 | 비고 |
|-------|------|------|-------|------|------|
| 1 | F-001~F-004 | 1 | opal-test-agent(red) | 순차 | RED 테스트 선작성(작성자≠구현자) |
| 2 | F-001 | 2, 3, 4 | opal-be-agent | 순차 | config 쓰기 → 라우터 골격/모델 → main 등록 |
| 3 | F-002, F-003, F-004 | 5, 6, 7 | opal-be-agent | 동일 파일(config.py 라우터)→순차 | 엔드포인트 3종 |
| 4 | F-001~F-004 | 8 | opal-test-agent | 순차 | GREEN 확인 + 전체 회귀(235건) |
| 5 | F-005 | 9, 10 | opal-fe-agent | 순차 | 페이지 → 라우팅/네비 |
| 6 | 문서 | 11 | PM 직접 | 순차 | ARCHITECTURE.md 갱신 |

### 4.2 실행 체크리스트
> 총 11개 Step | Phase 6개 | 실행 모드: 복잡

#### Step 1: RED 테스트 작성 (설정 라우터 + config 쓰기)
- [x] 완료
- **소속 기능**: F-001, F-002, F-003, F-004
- **영역**: BE
- **agent**: opal-test-agent
- **파일**: `dashboard/backend/tests/test_config.py`, `dashboard/backend/tests/test_routers.py`
- **작업 내용**: TS-001~005, TS-010~013, TS-020~023, TS-030~035의 실패 테스트를 작성·실행하여 실패(exit≠0)를 증거로 기록. monkeypatch로 `CONFIG_PATH`·`scan_projects` 격리(D-13 패턴), TestClient로 400/422/200 계약 검증(D-14 패턴). 경로 탈출(TS-003)·동시 쓰기(TS-005)·머지 보존(TS-021/022)·스키마 거부(TS-023/032/033) 포함.
- **완료 기준**: 신규 테스트가 미구현 대상에 대해 실패(RED)하고, 실패 로그가 기록된다. 기존 235건은 GREEN 유지.
- **테스트**: TS-001~005, TS-010~013, TS-020~023, TS-030~035
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 2: config.py 원자적 쓰기 함수 구현
- [x] 완료
- **소속 기능**: F-001
- **영역**: BE
- **agent**: opal-be-agent
- **파일**: `dashboard/backend/config.py`
- **작업 내용**: `_WRITE_LOCK`(threading.Lock) + `_atomic_write_json`(temp write + `os.replace`) + `save_config(updates)` + `save_project_local(target, updates)` 추가. 머지 보존(원본 dict `update()`). @header changelog 갱신(task 061).
- **완료 기준**: TS-004·TS-005·TS-021·TS-022·TS-030·TS-031 GREEN. read-modify-write 사이클이 락으로 직렬화되고 부분 쓰기 미노출.
- **테스트**: TS-004, TS-005, TS-021, TS-022, TS-030, TS-031
- **실행 방법**: sub-agent
- **의존**: Step 1

#### Step 3: 설정 라우터 골격 + 경로검증/화이트리스트 헬퍼 + 모델
- [x] 완료
- **소속 기능**: F-001
- **영역**: BE
- **agent**: opal-be-agent
- **파일**: `dashboard/backend/routers/config.py`(신규), `dashboard/backend/models.py`
- **작업 내용**: `_require_project_path`(brain.py 재사용) + `_resolve_setting_local_path`(고정 구성 + `resolve()` 하위 검증, path traversal 차단) 구현. `ConsoleConfigResponse`/`ConfigWriteResponse`/`PrewarmToggleRequest`/`ConsoleConfigUpdate`/`SettingLocalUpdate`(`extra="forbid"`) 모델 추가. 라우터 @header 작성([MUST] LLM 호출 금지 명시).
- **완료 기준**: TS-001·TS-002·TS-003·TS-034 GREEN(400/화이트리스트 방어). 라우터가 LLM 호출 0회.
- **테스트**: TS-001, TS-002, TS-003, TS-034
- **실행 방법**: sub-agent
- **의존**: Step 2

#### Step 4: main.py 라우터 등록
- [x] 완료
- **소속 기능**: F-001
- **영역**: BE
- **agent**: opal-be-agent
- **파일**: `dashboard/backend/main.py`
- **작업 내용**: `from dashboard.backend.routers import config` + `app.include_router(config.router)`(brain 등록 다음 줄). CORS `allow_methods=["GET","POST"]` 불변. @header depends/changelog 갱신.
- **완료 기준**: 앱 기동 OK, 신규 라우트 등록됨. 기존 5 read-only 라우터 405 계약 불변(H-6).
- **테스트**: TS-006(기존 `test_existing_routers_reject_post` 회귀)
- **실행 방법**: sub-agent
- **의존**: Step 3

#### Step 5: POST /api/config/prewarm (프라임 토글)
- [x] 완료
- **소속 기능**: F-002
- **영역**: BE
- **agent**: opal-be-agent
- **파일**: `dashboard/backend/routers/config.py`
- **작업 내용**: `post_prewarm` 핸들러 — 400 게이트 → `save_config({"prewarm_projects": ...})` → ON 시 `brain_session_registry.prewarm(project_path)` 1회 호출(비블로킹). OFF 시 목록 제거.
- **완료 기준**: TS-010~013 GREEN. prewarm 호출이 응답을 블로킹하지 않음.
- **테스트**: TS-010, TS-011, TS-012, TS-013
- **실행 방법**: sub-agent
- **의존**: Step 4

#### Step 6: GET /api/config + POST /api/config/console (config 관리)
- [x] 완료
- **소속 기능**: F-003
- **영역**: BE
- **agent**: opal-be-agent
- **파일**: `dashboard/backend/routers/config.py`
- **작업 내용**: `get_config`(스냅샷) + `post_console`(`model_dump(exclude_none=True)` → `save_config` 머지). 미지 최상위 필드 422.
- **완료 기준**: TS-020~023 GREEN(머지 보존 + extra 거부).
- **테스트**: TS-020, TS-021, TS-022, TS-023
- **실행 방법**: sub-agent
- **의존**: Step 4

#### Step 7: GET/POST /api/config/project-local (로컬 설정)
- [x] 완료
- **소속 기능**: F-004
- **영역**: BE
- **agent**: opal-be-agent
- **파일**: `dashboard/backend/routers/config.py`
- **작업 내용**: `get_project_local`(조회, 부재 시 exists=false) + `post_project_local`(400 게이트 → `_resolve_setting_local_path` → `save_project_local` 머지). `SettingLocalUpdate` 스키마 검증(422).
- **완료 기준**: TS-030~035 GREEN(생성·갱신·거부 3경로 + 재조회).
- **테스트**: TS-030, TS-031, TS-032, TS-033, TS-034, TS-035
- **실행 방법**: sub-agent
- **의존**: Step 4

#### Step 8: GREEN 확인 + 전체 회귀 스위트
- [x] 완료
- **소속 기능**: F-001, F-002, F-003, F-004
- **영역**: BE
- **agent**: opal-test-agent
- **파일**: `dashboard/backend/tests/`
- **작업 내용**: 신규 TS 전건 GREEN 확인 + 전체 pytest 스위트 실행(235건 + 신규 추가건) 회귀 0 확인. RED 테스트 불변성 검증(Step 1 파일 미수정).
- **완료 기준**: 전체 스위트 passed·0 failed. 기존 235건 회귀 0(H-6). flaky 없음.
- **테스트**: 전체 pytest 스위트
- **실행 방법**: sub-agent
- **의존**: Step 5, Step 6, Step 7

#### Step 9: SettingsPage.tsx 구현 (설정 화면)
- [x] 완료
- **소속 기능**: F-005
- **영역**: FE
- **agent**: opal-fe-agent
- **파일**: `dashboard/frontend/src/pages/settings/SettingsPage.tsx`, (필요 시) `dashboard/frontend/src/components/ui/switch.tsx`
- **작업 내용**: §3.5.2 화면 설계대로 3섹션 카드 폼 구현. `apiClient` 경유 5 API 연동 + TanStack Query `invalidateQueries` 재조회. `contextProject` 스위처 연동. 저장 실패 Alert 처리. @header 작성.
- **완료 기준**: TS-040~043 충족. 3섹션 렌더 + 변경→재조회 반영.
- **테스트**: TS-040, TS-041, TS-042, TS-043
- **실행 방법**: sub-agent
- **의존**: Step 8

#### Step 10: router.tsx + AppShell 네비/설정 버튼 연결
- [x] 완료
- **소속 기능**: F-005
- **영역**: FE
- **agent**: opal-fe-agent
- **파일**: `dashboard/frontend/src/router.tsx`, `dashboard/frontend/src/components/app-shell/AppShell.tsx`
- **작업 내용**: `/settings` 라우트 추가. NAV_ITEMS에 "설정"(Settings 아이콘) 추가. TopBar의 기존 no-op 설정 버튼을 `/settings` NavLink로 연결. @header depends/description 갱신.
- **완료 기준**: 네비/설정 버튼 클릭 시 `/settings` 이동. 기존 6화면 라우팅 불변.
- **테스트**: 수동/E2E — 네비 이동 확인
- **실행 방법**: sub-agent
- **의존**: Step 9

#### Step 11: docs/ARCHITECTURE.md 갱신
- [x] 완료
- **소속 기능**: F-001~F-005
- **영역**: 문서
- **agent**: PM 직접
- **파일**: `docs/ARCHITECTURE.md`
- **작업 내용**: §OPAL Console을 "6개 화면 → 7개 화면(설정 추가)"·"5 read-only + 브레인 POST → + 설정 라우터(쓰기 격리·화이트리스트)"로 갱신. 쓰기 예외 격리 원칙·화이트리스트 2종 명시. (BACKEND.md/FRONTEND.md 부재 프로젝트이므로 ARCHITECTURE.md 단일 갱신)
- **완료 기준**: 신규 라우터·화면·화이트리스트가 문서에 반영됨.
- **테스트**: 문서 검토
- **실행 방법**: direct
- **의존**: Step 10

### 4.3 병렬/순차 판별 근거

| 관계 | 근거 |
|------|------|
| Step 1 → Step 2~7 | RED-first: 테스트 선작성(작성자≠구현자) 후 구현 진입 |
| Step 2 → Step 3 → Step 4 | config 쓰기 함수 → 라우터가 이를 import → main이 라우터 등록 (레이어 하위→상위) |
| Step 5 ∥ Step 6 ∥ Step 7 (논리적) | 서로 다른 엔드포인트·독립 검증. 단 **동일 파일(config.py)** 수정이라 물리적으로는 동일 에이전트 순차 처리(파일 충돌 방지) |
| Step 8 ← Step 5,6,7 | 전 엔드포인트 완료 후 통합 회귀 |
| Step 9 → Step 10 | 페이지 구현 후 라우팅 연결 |
| BE(2~8) → FE(9~10) | FE는 고정된 API 계약 소비 |
| Step 11 ← Step 10 | 코드 확정 후 문서 반영 |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA

| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | 경로 검증·화이트리스트·원자적 쓰기 | TS-001~005 | 빈값/비스캔/traversal 400, 동시 쓰기 키 유실 0 |
| F-002 | 프라임 토글 ON/OFF + 즉시 선프라임 | TS-010~013 | config 반영 + prewarm 1회 호출(비블로킹) |
| F-003 | console.config 머지 보존 + 스키마 | TS-020~023 | 기존/미지 키 보존, extra 필드 422 |
| F-004 | 로컬 설정 생성·갱신·거부 + 재조회 | TS-030~035 | 3경로 통과, bootstrap 도메인/extra 위반 422 |
| F-005 | 설정 화면 3섹션 + 재조회 반영 | TS-040~043 | 렌더·변경→반영·실패 Alert |

### 5.2 회귀 테스트
- [ ] 기존 pytest 235건 전건 GREEN 유지(회귀 0)
- [ ] 기존 read-only API 5종 GET 계약 불변 + `test_existing_routers_reject_post`(405) 유지
- [ ] 브레인 POST 3종 계약 불변, CORS `allow_methods=["GET","POST"]` 불변
- [ ] 기존 6화면 FE 라우팅 불변

### 5.3 코드/문서 품질
- [ ] 신규/수정 파일 @header 작성·갱신(`docs/CONVENTIONS.md` §@header 규칙)
- [ ] 소스는 `dashboard/`에서만 수정 — `~/.opal/` 배포본 직접 편집 금지(배포 경계)
- [ ] 커밋은 캡틴 명시 요청 시에만(자동 커밋 금지)
- [ ] docs/ARCHITECTURE.md §OPAL Console 갱신

### 5.4 보안
- [ ] path traversal 방어 — 화이트리스트 2종 외 쓰기 400 (R-PATH-001 Critical)
- [ ] 설정 라우터 LLM/claude 서브프로세스 호출 0회(브레인 라우터 격리 불변)
- [ ] 거부된 쓰기 요청 로깅(`logger.warning`) — R-UNAUTH-003
- [ ] `.env`/인증 파일 커밋 없음, 하드코딩 시크릿 없음
- [ ] host=127.0.0.1 로컬 바인딩 불변(외부 노출 금지)

---

## 6. 복잡도 판별

| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 11개 | 복잡 |
| 변경 파일 수 | 8개(신규 2 + 수정 6) | 복잡 |
| 모듈 범위 | 다중(BE 라우터·config·모델 + FE 페이지·라우팅) | 복잡 |
| 작업 유형 | 신규 개발(쓰기 라우터 + 화면) | 복잡 |
| 외부 의존성 | 신규 패키지 없음(표준 라이브러리) / 신규 라우터 있음 | 복잡 |
| **실행 모드** | **복잡** | |

---

## 7. 실행 아키텍처 (복잡 모드)

### C-1. 에이전트 토폴로지

```
Batch 1: [opal-test-agent(red)]  ── Step 1 (RED 선작성)
Batch 2: [opal-be-agent]         ── Step 2→3→4→(5,6,7)  (동일 config.py·순차, 파일 충돌 방지)
Batch 3: [opal-test-agent]       ── Step 8 (GREEN + 회귀)
Batch 4: [opal-fe-agent]         ── Step 9→10
Batch 5: [PM 직접]               ── Step 11 (문서)
```

- **파일 충돌 방지**: Step 5·6·7은 논리적 독립이나 모두 `routers/config.py` 수정 → 동일 opal-be-agent 순차 배치.
- **작성자≠구현자**: RED(Step 1)·GREEN 검증(Step 8)은 opal-test-agent, 구현(Step 2~7)은 opal-be-agent로 분리(red-first.md §2).

### C-2. 스킬 요구사항

- BE: `op-dev-execute`(구현), `op-dev-test`(RED/GREEN). 기존 스킬로 충족, 갭 없음.
- FE: `op-dev-execute` + `ui-designer`(settings 유형, plan-driven — §3.5.2 화면 설계가 입력 계약).

### C-3. 도구 요구사항

- 신규 CLI/MCP/패키지 없음. pytest(BE) + Vitest/수동(FE). shadcn Switch 미존재 시 추가.

### C-4. 테스트 전략

- **RED-first 적용(BE, F-001~F-004)**: API 계약 + 파일 쓰기(read-modify-write) + path traversal(인가성) = self-confirming 위험 높음 → RED-first 강제(red-first.md §1.5). Step 1에서 실패 테스트 선작성, Step 8에서 GREEN + 불변성 검증.
- **구현-후-검증 허용(FE, F-005)**: UI 화면·컴포넌트 → 탐색·시각 트랙(red-first.md §1.5). Step 9 구현 후 시나리오 검증.
- **회귀**: `pytest dashboard/backend/tests`(235 + 신규) 회귀 0. 기존 read-only/브레인 계약 불변.
- **state-tool 연동**: BE 트랙 `verify --red-check` ON / FE 트랙 OFF.

---

## 8. 기술 컨텍스트

### 8.1 기술 스택

| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| BE | Python, FastAPI, uvicorn, pytest, threading/pathlib/json | op-dev-execute, op-dev-test |
| FE | React, TypeScript, Vite, Tailwind, shadcn/ui, TanStack Query, Zustand | op-dev-execute, ui-designer |

### 8.2 사용 MCP

| MCP | 조회 결과 요약 |
|-----|--------------|
| (미사용) | 기존 코드 선례(brain.py·config.py·DoctorPage)로 설계 충분 — 신규 라이브러리 API 조회 불요 |

### 8.3 참조 문서 (설계 결정 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 기획 | 061 예약 메모리 | `.opal/memory/061_콘솔_설정_화면_예약.md` | 확정 범위 3종 + 쓰기 격리·화이트리스트 설계 방향 |
| D-2 | 설계 | 060 DONE | `tasks/060-260713-opd-브레인-프라임-연결풀/DONE.md` | prewarm API 산출 + 235 스위트 회귀 기준 |
| D-3 | 소스 | brain.py | `dashboard/backend/routers/brain.py` | 경로검증(`_require_project_path` 42-76)·400·백그라운드 스레드(190-197) 선례 + LLM 격리 @header |
| D-4 | 소스 | config.py | `dashboard/backend/config.py` | 현행 읽기 전용(45-66)·CONFIG_PATH(23)·`_coerce_str_list`(38-42) |
| D-5 | 소스 | brain_session.py | `dashboard/backend/adapters/brain_session.py` | `prewarm()`(558-571) 비블로킹 재사용 |
| D-6 | 소스 | main.py | `dashboard/backend/main.py` | 라우터 등록(94-99)·CORS(84-90)·lifespan 선프라임(42-63) |
| D-7 | 소스 | scanner.py | `dashboard/backend/scanner.py` | `scan_projects`(39-72) 화이트리스트 검증 |
| D-8 | 소스 | models.py | `dashboard/backend/models.py` | 기존 BaseModel 스타일(189-238) — 신규 모델 추가 근거 |
| D-9 | 소스 | test_config.py / test_routers.py | `dashboard/backend/tests/` | monkeypatch·TestClient·405/400 검증 패턴 |
| D-10 | 소스 | router.tsx / AppShell.tsx / DoctorPage.tsx / api.ts | `dashboard/frontend/src/` | 라우트·NAV·페이지·apiClient 선례 |
| D-11 | 설계 | ARCHITECTURE.md | `docs/ARCHITECTURE.md` §OPAL Console(233-273) | 콘솔 원칙(읽기전용·SSOT·오케스트레이터)·쓰기 격리 선례 |
| D-12 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | @header·배포 경계·커밋 규칙(149-208) |
| D-13 | 설계 | 전역 setting.json | `~/.opal/setting.json` | setting.local.json 스키마(bootstrap·models 셀 오버라이드) 근거 |
| D-14 | 설계 | red-first.md | `opal/core/references/harness/red-first.md` | RED-first 적용 기준(§1.5) |
| D-15 | 설계 | citation-rules.md | `opal/core/references/harness/citation-rules.md` | 인용·[MUST] 포맷 |

---

## 9. 리스크 및 대응 (기능-리스크 연결)

| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| R-PATH-001 | path traversal — 화이트리스트 외 파일 쓰기 | F-001, F-004 | Critical | 검증된 project_path에서 서버가 경로 고정 구성 + `resolve()` 하위 검증, FE 경로 문자열 불신뢰 (§3.1.2, §3.4.2) |
| R-CONCURRENT-002 | config 동시 쓰기 경합/부분 쓰기 | F-001 | High | 모듈 `threading.Lock` + temp write + `os.replace`(ANALYSIS §2.1 정정, §3.1.2) |
| R-MERGE-004 | console.config 기존/미지 키 유실 | F-003 | High | 원본 dict `update()` 머지, 3시나리오 테스트(§3.3.2) |
| R-SETTING-006 | setting.local 스키마 오염 | F-004 | Medium | `ConfigDict(extra="forbid")` 최상위 2필드 화이트리스트 + bootstrap Literal(§3.4.2) |
| R-UNAUTH-003 | 무인증 로컬 데몬 쓰기 표면 증가 | F-001 | Medium | 화이트리스트 + 400 명시 거부 + 거부 요청 로깅 |
| R-FSEPOCH-005 | 프로젝트 경로 소실/권한 오류 | F-004 | Medium | 요청 시 `_require_project_path` 실시간 검증(400), 쓰기 실패는 500 |
| H-6 | 신규 POST 라우터가 기존 405/CORS 계약 파손 | F-001 | P0 | `test_existing_routers_reject_post` 회귀 유지, CORS 불변(§3.3.2) |
| R-DEPLOY-007 | 소스/배포본 이원화 | 전 기능 | High | `dashboard/` 소스만 수정 + install 재배포. 런타임 데이터 파일(console.config/setting.local)은 경계 대상 아님(§3.3.2) |
| R-NOCOMMIT-008 | 자동 커밋 금지 | 전 기능 | High | EXECUTE 완료 후 대기, 캡틴 명시 요청 시에만 커밋(§5.3) |

> **용어 일관성 검토(citation-rules §7)**: FE↔BE 필드명 정합 확인 — `project`/`enabled`/`scan_roots`/`scan_depth`/`exclude`/`prewarm_projects`/`bootstrap`/`models`는 요청 스키마·config dataclass·전역 setting.json에서 동일 토큰 사용. 불일치 없음 → decision_required 없음.
