# ANALYSIS: OPAL Console 프로젝트별 환경 설정 화면

> 작성일: 2026-07-14
> 입력: TASK.md (R-1~R-5 요구사항)
> 출력: ANALYSIS.md (BE 쓰기 라우터 신설 + FE 화면 라우팅 + 보안 고려)

---

## 0. 참조 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 기획 | 061 예약 메모리 | `.opal/memory/061_콘솔_설정_화면_예약.md` | 확정 범위 3종(프라임 토글·config·로컬 설정) + 설계 방향(격리·화이트리스트) |
| D-2 | 설계 | 060 DONE | `tasks/060-260713-opd-브레인-프라임-연결풀/DONE.md` | prewarm API 산출 + 브레인 POST 격리 선례 |
| D-3 | 설계 | ARCHITECTURE.md | `docs/ARCHITECTURE.md` §OPAL Console | 콘솔 5 read-only API + 브레인 POST 격리 + 데몬 원칙 |
| D-4 | 설계 | 브레인 풀 설계 | `.opal/brain/pages/concept/brain-prime-connection-pool-design.md` | prewarm 동작 + 풀 구조 |
| D-5 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | @header·배포 경계·구현 규칙 |
| D-6 | 소스 | main.py | `dashboard/backend/main.py` | 라우터 등록 구조 + CORS 설정 + lifespan 훅 (88줄, 99줄) |
| D-7 | 소스 | brain.py | `dashboard/backend/routers/brain.py` | 쓰기 POST 선례: 경로 검증(200행) + 400 처리(64~77행) + 백그라운드 스레드(190~195행) |
| D-8 | 소스 | config.py | `dashboard/backend/config.py` | ConsoleConfig 필드 + _coerce_str_list 패턴 + 머지 읽기(51~67행) |
| D-9 | 소스 | brain_session.py | `dashboard/backend/adapters/brain_session.py` | BrainSessionRegistry.prewarm()(160행) + 스레드 안전성(Lock/Semaphore) |
| D-10 | 소스 | scanner.py | `dashboard/backend/scanner.py` | 프로젝트 스캔 로직 + 경로 발견 (scan_projects, ProjectInfo) |
| D-11 | 소스 | router.tsx | `dashboard/frontend/src/router.tsx` | 6개 라우트 구조 + searchParams 패턴 |
| D-12 | 소스 | AppShell.tsx | `dashboard/frontend/src/components/app-shell/AppShell.tsx` | 6개 네비 항목 + 프로젝트 스위처 + 설정 버튼 위치 |
| D-13 | 소스 | test_config.py | `dashboard/backend/tests/test_config.py` | 타입 가드 테스트 패턴: monkeypatch CONFIG_PATH + 5variant |
| D-14 | 소스 | test_routers.py | `dashboard/backend/tests/test_routers.py` | TestClient + HTTPException(400) 검증 패턴 |
| D-15 | 설계 | PROJECT.md | `docs/PROJECT.md` | 콘솔 구성(6화면) + 프로젝트 구성(FE/BE 전문 에이전트) |

---

## 1. 기존 코드 분석

### 1.1 관련 파일 목록

| 파일 | 역할 | 변경 필요 | 근거(줄번호/위치) |
|------|------|----------|------------------|
| `dashboard/backend/main.py` | FastAPI 앱 생성·라우터 등록·CORS·정적 파일 | **신규 설정 라우터 등록** | D-6:88~99 (라우터 등록 지점, 브레인 POST 격리 선례) |
| `dashboard/backend/config.py` | console.config.json 로드 + 기본값 | **쓰기 함수 신설** | D-8:45~67 (현행 읽기 전용, 머지 보존 쓰기 추가 필요) |
| `dashboard/backend/routers/brain.py` | 쓰기 POST 라우터(단일 선례) | **참고·선례 분석** | D-7:42~77 (경로 검증 헬퍼), D-7:200~206 (백그라운드 스레드 패턴) |
| `dashboard/backend/adapters/brain_session.py` | BrainSessionRegistry | **prewarm() 재사용** | D-9:42~45 (프라임 호출 위치) |
| `dashboard/backend/scanner.py` | 프로젝트 스캔 + AGENT.md 발견 | **화이트리스트 생성 지점** | D-10:41~69 (scan_projects, ProjectInfo) |
| `dashboard/frontend/src/router.tsx` | React Router 설정 | **신규 라우트 추가** | D-11:21~36 (6개 라우트, "환경" 메뉴와 병치) |
| `dashboard/frontend/src/components/app-shell/AppShell.tsx` | 6개 네비·프로젝트 스위처 | **"설정" 네비 항목 추가** | D-12:74~81 (NAV_ITEMS 배열, Activity 아이콘 다음) |
| `dashboard/backend/tests/test_config.py` | config 테스트 | **쓰기 테스트 케이스 추가** | D-13:44~76 (monkeypatch 패턴) |
| `dashboard/backend/tests/test_routers.py` | 라우터 테스트 | **설정 라우터 400/200 케이스 추가** | D-14:62~100 (TestClient + HTTPException 검증) |

### 1.2 아키텍처 패턴

#### 읽기 전용 원칙의 예외 격리 패턴 (→ D-3, D-1)

- **기존 설계**: 콘솔은 읽기 전용 대시보드 — API 5종 모두 GET (D-3 §OPAL Console)
- **유일 예외**: 브레인 POST 라우터 1곳에 격리 — `POST /api/brain/{query,prime}`만 쓰기 허용 (D-7 @header)
- **신규 설정 라우터**: 동일 격리 원칙 적용 → **설정 라우터만 쓰기 허용**, 쓰기 대상 파일을 명시 화이트리스트로 한정 (→ D-1 §설계 방향)

#### 경로 검증 + 400 처리 패턴 (→ D-7)

`dashboard/backend/routers/brain.py`의 선례:

```python
# D-7:42-77 — 경로 검증 헬퍼
def _resolve_project_path(project: str) -> str:
    """project 절대경로 검증 및 반환.
    project가 빈 값이거나 스캔된 프로젝트 목록에 존재하지 않으면 빈 문자열 반환."""
    if not project:
        return ""
    cfg = load_config()
    projects = scan_projects(cfg.scan_roots, cfg.scan_depth, cfg.exclude)
    for p in projects:
        if p.path == project:
            return p.path
    return ""

def _require_project_path(project: str) -> str:
    """프로젝트 검증 후 절대경로 반환. 실패 시 HTTPException(400) raise."""
    if not project:
        raise HTTPException(status_code=400, detail="project가 필수입니다...")
    resolved = _resolve_project_path(project)
    if not resolved:
        raise HTTPException(status_code=400, detail=f"프로젝트를 찾을 수 없습니다...")
    return resolved
```

설정 라우터도 동일 패턴: **경로 검증 → 스캔 프로젝트 화이트리스트 매칭 → 실패 시 400**.

#### 백그라운드 스레드 비블로킹 패턴 (→ D-7, D-6)

`dashboard/backend/routers/brain.py:190~206` — POST 응답은 즉시 반환, 실제 작업은 daemon 스레드에서 수행:

```python
t = threading.Thread(
    target=_prime_background,
    args=(sid, project_path),
    daemon=True,
)
t.start()
return BrainPrimeResponse(priming=True)  # 즉시 반환
```

설정 변경도 동일 원칙: **API는 즉시 반환 → 파일 쓰기는 daemon 스레드에서 비동기 수행**.

### 1.3 의존성 맵

```
dashboard/backend/routers/config (신규)
├── dashboard/backend/config.py (ConsoleConfig + load_config + save_config 신규)
├── dashboard/backend/scanner.py (scan_projects로 화이트리스트 검증)
└── fastapi (HTTPException 400/403)

dashboard/backend/main.py
├── dashboard/backend/routers/config (신규 라우터 등록)
└── dashboard/backend/routers/brain (기존 POST 격리 선례)

dashboard/frontend/src/router.tsx
├── dashboard/frontend/src/pages/settings (신규 페이지, SettingsPage.tsx)
└── dashboard/frontend/src/components/app-shell/AppShell.tsx (네비 추가)

dashboard/backend/tests/test_routers.py
├── httpx.TestClient (기존 패턴)
└── dashboard/backend/routers/config (신규 라우터 테스트)

dashboard/backend/tests/test_config.py (기존)
├── config.save_config (신규 함수 테스트)
└── monkeypatch (격리 패턴)
```

### 1.4 테스트 현황

#### 기존 테스트 구조 (→ D-13, D-14)

- **test_config.py** (5케이스): config 로드·파싱 + monkeypatch CONFIG_PATH 격리 패턴 재사용 가능
- **test_routers.py** (40+ 케이스): TestClient + HTTPException 검증 패턴
- **test_brain.py** (60+ 케이스): BrainSessionRegistry 테스트 + 스레드 안전성

#### 신규 테스트 필요 커버리지

- [ ] R-1 경로 검증: 화이트리스트 외 경로 쓰기 요청 → 403/400 (path traversal 방어)
- [ ] R-1 화이트리스트 한정: `~/.opal/console.config.json` + `{프로젝트}/.opal/setting.local.json` 만 쓰기 허용
- [ ] R-2 prewarm 토글: ON → `prewarm_projects`에 추가 + 즉시 BrainSessionRegistry.prewarm() 호출 + config 머지 저장
- [ ] R-3 console.config 머지: 기존 키 유실 없이 부분 갱신
- [ ] R-4 프로젝트 로컬 설정: 유효한 JSON 구조 검증 + 저장 실패 시 400
- [ ] 라우터 5개 400 케이스: 빈 경로, 존재하지 않는 프로젝트, 유효하지 않은 JSON 페이로드

---

## 2. 외부 조사 결과

### 2.1 FastAPI 쓰기 라우터 패턴

- **Pydantic 요청 모델**: `POST /api/config` 바디는 dict 또는 명시 RequestModel(선택)
- **파일 쓰기 보안**: 절대경로 검증 → 화이트리스트 매칭은 FastAPI 표준 패턴 (→ D-7 brain.py 선례)
- **동시 쓰기 경합**: JSON 파일은 `open(..., 'w')` 단일 호출이 원자(atomic)이므로 일반적으로 Lock 불필요. 다만 읽기-수정-쓰기 사이클이 필요하면 Lock 추가 권장.

### 2.2 Python pathlib + json 머지 패턴

```python
import json
from pathlib import Path

def merge_json_file(path: Path, updates: dict) -> None:
    """기존 JSON 읽기 → 머지 → 쓰기 (부분 갱신)."""
    existing = {}
    if path.exists():
        existing = json.loads(path.read_text())
    existing.update(updates)
    path.write_text(json.dumps(existing, indent=2))
```

이 패턴은 `console.config.json` 머지 쓰기에 직접 적용 가능.

---

## 3. 영향 범위

### 3.1 직접 영향

**신규 파일**:
- `dashboard/backend/routers/config.py` — 설정 라우터 (R-1, R-2, R-3, R-4 구현)
- `dashboard/frontend/src/pages/settings/SettingsPage.tsx` — 설정 화면 (R-5)

**수정 파일**:
- `dashboard/backend/config.py` + 함수 `save_config()` 신설 (R-1 화이트리스트, R-2, R-3, R-4 머지 쓰기)
- `dashboard/backend/main.py` + 라우터 등록 line 99-100 (R-1 라우터 추가)
- `dashboard/frontend/src/router.tsx` + 라우트 추가 (R-5 라우팅)
- `dashboard/frontend/src/components/app-shell/AppShell.tsx` + NAV_ITEMS 확장 (R-5 네비)
- `dashboard/backend/tests/test_config.py` + 쓰기 테스트 케이스 (R-1, R-3, R-4 검증)
- `dashboard/backend/tests/test_routers.py` + 400/200 케이스 (R-1, R-2, R-3, R-4 경계 검증)

### 3.2 간접 영향

**호출자**:
- FE `SettingsPage.tsx` → `apiClient.post('/api/config/...')` 호출
- 콘솔 사용자 — 화면에서 설정 변경 → daemon 스레드로 파일 쓰기

**영향받는 모듈**:
- `dashboard/backend/scanner.py` — 화이트리스트 검증 시 `scan_projects()` 호출 (기존 함수, 변경 없음)
- `dashboard/backend/adapters/brain_session.py` — R-2 토글 ON 시 `BrainSessionRegistry.prewarm()` 호출 (기존 함수, 변경 없음)
- `dashboard/backend/config.py` — 신규 `save_config()` 호출 (config 쓰기 전담)

**기존 API 계약 불변**:
- GET 5개 read-only API (`/api/dashboard`, `/api/projects`, `/api/tasks`, `/api/memory`, `/api/doctor`) — 변경 없음
- POST 브레인 API (`/api/brain/{query,prime,job}`) — 변경 없음
- CORS allow_methods=["GET", "POST"] (기존, 브레인 POST 격리용) — 동일 유지

### 3.3 영향 범위 요약

- [x] **DB 스키마 변경**: 없음 (콘솔은 무상태 대시보드)
- [x] **API 인터페이스 변경**: 신규 4개 POST 라우터 추가 (기존 API 불변)
- [x] **설정/환경변수 변경**: `console.config.json` 프로젝트별 레코드 추가 필요 (기존 키 유실 방지)
- [x] **프로젝트 로컬 설정**: 신규 쓰기 대상 파일 추가 (`.opal/setting.local.json`)
- [x] **빌드/배포 파이프라인 변경**: install 이후 배포 (`~/.opal/dashboard-server/` 재배포)

---

## 4. 핵심 발견 사항

### 4.1 쓰기 라우터 신설 지점

(→ D-6) `dashboard/backend/main.py:99` — **기존 brain.router 등록 다음 라인**에 신규 config.router 등록:

```python
app.include_router(brain.router)    # 기존: 유일한 POST 라우터
app.include_router(config.router)   # 신규: 설정 라우터 (POST 4개)
```

브레인 라우터와 함께 `allow_methods=["GET", "POST"]` CORS 원칙 유지 (D-6:88).

### 4.2 경로 검증 · 400 처리 선례

(→ D-7:42~77) `brain.py`의 `_require_project_path()` 패턴을 **그대로 재사용**:

```python
# 경로 검증 → HTTPException(400) 발행
project_path = _require_project_path(body.project)
```

신규 config 라우터도 동일: **빈 값 또는 스캔 목록 미존재 → 400** (R-1 AC).

### 4.3 config 쓰기 구현 재료

(→ D-8) 현행 `config.py:51~67`은 **읽기 전용**:

```python
def load_config() -> ConsoleConfig:
    """~/.opal/console.config.json 로드. 없으면 기본값 반환."""
    if not CONFIG_PATH.exists():
        return ConsoleConfig()
    with open(CONFIG_PATH, encoding="utf-8") as f:
        data: dict = json.load(f)
    return ConsoleConfig(
        scan_roots=data.get("scan_roots", DEFAULT_SCAN_ROOTS),
        prewarm_projects=_coerce_str_list(data.get("prewarm_projects", [])),
    )
```

신규 `save_config()` 함수는:

1. 기존 config 읽기 (load_config 또는 기존 파일 직접 읽기)
2. 업데이트 부분(예: `prewarm_projects`) 머지
3. CONFIG_PATH에 쓰기 (json.dumps + path.write_text)
4. **기존 키 유실 방지** — `data.update(updates)` 패턴 (R-3 AC)

(→ D-8:62~66 _coerce_str_list 타입 가드도 쓰기 전 유효성 검사에 재사용)

### 4.4 프라임 토글 즉시 효과 (R-2)

(→ D-9, D-4) `BrainSessionRegistry.prewarm(project_path)` 존재:

- **ON 시**: `prewarm_projects`에 추가 + 즉시 `prewarm()` 호출 → 백그라운드 스레드로 선프라임 시작 (재기동 불요)
- **OFF 시**: `prewarm_projects`에서 제거 → 현재 풀은 유지, 다음 재기동부터 대상 제외

→ R-2 AC: "ON 시 즉시 선프라임"은 동기적 호출 1회 + 비블로킹 구현으로 충족.

### 4.5 프로젝트 로컬 설정 쓰기 경계 (R-4)

(→ D-1) 확정 범위에 "프로젝트 로컬 설정까지 확장" — **쓰기 경계가 프로젝트 파일로 확대**:

- **화이트리스트**: `~/.opal/console.config.json` + `{스캔된 프로젝트}/.opal/setting.local.json`
- **경로 탈출 방어**: 절대경로 검증 → `Path(project_path) / ".opal" / "setting.local.json"` 안전 구성
- **JSON 스키마 검증**: `bootstrap`·`models` 필드만 허용 (R-4 AC "유효하지 않은 JSON 구조 거부")

### 4.6 FE 라우팅 — 기존 "환경" 메뉴 vs 신규 "설정" 메뉴

(→ D-11, D-12, D-3) 기존 6개 화면:

- 대시보드 (`/`)
- 프로젝트 (`/projects`)
- 태스크 (`/tasks`)
- 메모리 (`/memory`)
- 환경 (`/doctor`) — 의존성·버전 현황 조회 (read-only)
- 프로젝트 브레인 (`/brain`) — 질의 UI

(→ D-3 §OPAL Console) "환경"은 `doctor.py`로 이미 설정 정보(선택) 표시 — 신규 "설정" 메뉴는 **독립 라우트 (`/settings`) 신설 권장**:

| 항목 | 역할 |
|------|------|
| `/doctor` (기존) | read-only 환경 정보(의존성, 버전) |
| `/settings` (신규) | 설정 편집(프라임 토글, config, 로컬 설정) |

→ TASK §범위 "화면 배치(기존 "환경" 메뉴 확장 vs 신규 메뉴)는 ANALYSIS/PLAN에서 결정" — **신규 라우트 신설 쪽이 관심사 분리 명확**.

---

## 5. 제약/리스크

| 항목 | 설명 | 심각도 | 근거 |
|------|------|--------|------|
| **R-PATH-001** | **경로 탈출(path traversal) 공격 방어 필수** — `/api/config/save`에 임의 경로 주입 시 화이트리스트 외 파일 쓰기 위험 | **Critical** | D-6:141, D-1 §제약 "path traversal·임의 파일 쓰기 방어를 설계에 포함" |
| 대응책 | 절대경로 검증: (1) project 경로 → scan_projects 화이트리스트 매칭(스캔된 프로젝트만) (2) 파일 경로 → `Path(project_path) / ".opal" / "setting.local.json"` 안전 구성(상위 디렉토리 점프 방지) + `resolve().relative_to()` 검증 | - | D-7:42~77 (brain.py 선례) |
|  |  |  |  |
| **R-CONCURRENT-002** | **config 동시 쓰기 경합** — 여러 API 요청이 console.config.json을 동시 수정 시 일부 키 유실 위험 | **High** | D-3 §OPAL Console "SSOT는 각 프로젝트 파일" / D-8 현행 코드에 Lock 없음 |
| 대응책 | `save_config()` 구현 시 threading.Lock 추가 (선택): 단순 파일 쓰기(`open().write_text()`)는 OS 원자 보장이나, 읽기-수정-쓰기 사이클(`json.load` → `update()` → `json.dump`)이 있으므로 Lock 권장. 또는 임시 파일 쓰기 후 atomic rename 이용 | - | Python `json` 표준 + POSIX atomic rename 패턴 |
|  |  |  |  |
| **R-UNAUTH-003** | **무인증 로컬 데몬에 쓰기 API가 생기는 보안 표면 증가** — 127.0.0.1 로컬 바인딩이므로 구독자만 접근 가능하나, 로컬 악의 스크립트 위험 | **Medium** | D-6:146 "[MUST] host=127.0.0.1 — 외부 노출 금지" / D-1 §제약 "무인증 로컬 데몬" |
| 대응책 | (1) 경로 검증 + 화이트리스트 한정(R-PATH-001) (2) 400 응답으로 명시적 거부 (3) 로깅: 거부된 요청 기록 (예: `logger.warning("설정 쓰기 거부: project=%r", project)`) | - | D-7:187, D-6:59 (logging 기존 패턴) |
|  |  |  |  |
| **R-MERGE-004** | **`console.config.json` 머지 보존 쓰기** — scan_roots·scan_depth·exclude 등 기존 설정은 유지하면서 prewarm_projects만 갱신해야 함 | **High** | D-1 §확정 범위 / R-3 AC "기존 키가 유실되지 않는다(머지 보존 테스트 Pass)" |
| 대응책 | `save_config(updates: dict)` 구현: (1) 기존 config 읽기 (2) `existing_data.update(updates)` 머지 (3) json.dump로 쓰기. 테스트: 3개 시나리오 — (a) 신규 키 추가 시 기존 키 유지 (b) 기존 키 변경 (c) 부분 갱신 후 재로드 검증 | - | D-8:62~66 _coerce_str_list 타입 가드 참고 |
|  |  |  |  |
| **R-FSEPOCH-005** | **프로젝트 경로 변경 · 파일 시스템 실패 · 권한 오류** — scan_projects 호출 시 프로젝트가 삭제됐거나 경로 변경 시 비어있는 목록 반환 가능 | **Medium** | D-10:65 (scan_projects는 현재 파일만 검사, 경로 유효성 보증 없음) |
| 대응책 | API 요청 시 `_require_project_path()`로 실시간 검증 (D-7 선례). 저장할 때 프로젝트 경로 재검증 불필요(요청 시만으로 충분) — 파일 쓰기 실패(권한 오류 등)는 예외로 500 응답 | - | D-7:61~76 |
|  |  |  |  |
| **R-SETTING-006** | **`.opal/setting.local.json` 스키마 검증** — bootstrap·models 외 임의 필드 거부 필요 (R-4 AC) | **Medium** | R-4 AC "유효하지 않은 JSON 구조는 저장이 거부된다" |
| 대응책 | Pydantic RequestModel로 스키마 강제: `SettingLocalUpdate { bootstrap?: str, models?: dict }` — 미알려진 필드 검증은 `ConfigDict(extra="forbid")` 설정 | - | FastAPI Pydantic 표준 패턴 |
|  |  |  |  |
| **R-DEPLOY-007** | **배포 경계: 소스와 배포본의 이원화** — 소스(`dashboard/backend/`)에서 수정 후 install 재배포(`~/.opal/dashboard-server/`) 필요 | **High** | D-5 §배포 경계: "~/.opal/ 배포 파일을 직접 편집하지 않는다" / D-1 §제약 "install 재배포로 반영" |
| 대응책 | 모든 수정은 프로젝트 소스(`dashboard/backend/` + `frontend/src/`)에서만 수행. install 실행 후 ~/.opal/dashboard-server/에 자동 반영. 배포본 직접 편집 금지(전환 적용 안 됨) | - | D-5:202~204 |
|  |  |  |  |
| **R-NOCOMIT-008** | **커밋은 캡틴 명시 요청 시에만 수행** — 현재 태스크 범위 내에서 자동 커밋 금지 | **High** | D-1 §제약: "커밋은 캡틴 명시 요청 시에만 수행" |
| 대응책 | EXECUTE 완료 후 대기. PM 또는 캡틴이 "커밋해줘" 명시 요청 시에만 git commit/push 수행 | - | `docs/CONVENTIONS.md` §커밋 규칙 |

---

## 6. 기술 컨텍스트

### 6.1 기술 스택

| 카테고리 | 기술 | 버전/세부 |
|----------|------|----------|
| **BE 프레임워크** | FastAPI | `dashboard/backend/main.py` imports fastapi (현행 v0.1.0 앱) |
| **BE 서버** | uvicorn | `dashboard/backend/main.py:144` — host=127.0.0.1:7823 |
| **BE 언어** | Python | 3.x (dataclass, pathlib 현행 사용) |
| **BE 동시성** | threading | `threading.Lock`, `threading.Semaphore`, daemon threads |
| **BE 파일 I/O** | pathlib + json | `dashboard/backend/config.py` — Path.home()·json.load/dump |
| **FE 프레임워크** | React + TypeScript | `dashboard/frontend/src/` — createBrowserRouter, useSearchParams |
| **FE 라우팅** | React Router | v6+ (D-11:createBrowserRouter) |
| **FE UI** | shadcn/ui + Tailwind | `dashboard/frontend/src/components/ui/` |
| **FE 상태** | TanStack Query + Zustand | `dashboard/frontend/src/store/ui-store.ts`, `useQuery` |
| **테스트** | pytest (BE) + Vitest (FE) | `dashboard/backend/tests/test_*.py` — TestClient(FastAPI) |
| **API 클라이언트** | httpx / fetch | `dashboard/frontend/src/lib/api.ts` — apiClient.post(...) |

### 6.2 추천 스킬

| 스킬 | 용도 |
|------|------|
| `opal-be-agent` | 백엔드 라우터·config 모듈·테스트 구현 |
| `opal-fe-agent` | 프론트엔드 페이지·컴포넌트·라우터 구현 |
| `opal-task-qa` | PLAN 산출물 품질 검증 |
| `verify` | 화면 토글 동작·config 머지·경로 검증 E2E 테스트 |

### 6.3 추천 MCP

| MCP | 용도 |
|-----|------|
| context7 | FastAPI 공식 문서(경로 검증·쓰기 패턴) / Python pathlib·json 모범 사례 조회 |
| WebSearch | React Router v6 searchParams 패턴 / Pydantic validation 최신 정보 (필요 시) |

---

## 7. 다음 단계 지침

### PLAN 스킬에서 다루어야 할 항목

1. **R-1 설정 라우터**: 4개 POST 엔드포인트 상세 설계
   - `/api/config/prewarm` — `{project: str, enabled: bool}` → config 머지
   - `/api/config/console` — `{scan_roots?, scan_depth?, exclude?, prewarm_projects?}` → 부분 갱신
   - `/api/config/project-local` — `{project: str, bootstrap?: str, models?: dict}` → setting.local.json 생성/갱신
   - `/api/config/validate` — 경로/JSON 유효성만 확인(dry-run)

2. **경로 검증 로직**: `_require_project_path()` 확장 + `_validate_project_local_path()` 신설

3. **머지 저장 함수**: `save_config(updates)` 구현 상세 + Lock 전략 선택

4. **FE 설정 화면**: `SettingsPage.tsx` 구조 — 3개 폼(프라임 토글, config 항목, 로컬 설정)

5. **테스트 시나리오**: R-1~R-5의 각 AC별 50+ 케이스 설계 (경로 탈출·동시 쓰기·머지 보존·JSON 스키마 검증)

### 이 ANALYSIS의 제약 영역 (PLAN에서 결정)

- [지정 필요] FE 화면 배치: 기존 "환경" 메뉴 확장 vs 신규 "설정" 라우트 (→ D-12 권고)
- [지정 필요] `/api/config/console`의 엔드포인트 세분화 여부 (1개 vs 3개 라우트)
- [지정 필요] `.opal/setting.local.json` 스키마 — bootstrap·models 외 다른 필드 허용 여부
- [지정 필요] 동시 쓰기 Lock 전략: 간단한 원자 쓰기 vs full threading.Lock
