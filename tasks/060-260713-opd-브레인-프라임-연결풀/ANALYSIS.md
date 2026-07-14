# ANALYSIS: OPAL Console 브레인 프라임 연결 풀 — 지정 프로젝트 선프라임 + 새 대화 웜 핸들 배정

> 작성일: 2026-07-13
> 입력: TASK.md
> 출력: ANALYSIS.md

## 0. 참조 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | brain_session (세션 상태기계) | `dashboard/backend/adapters/brain_session.py` | 풀 신설 대상 — 락 패턴·상태기계·레지스트리 단일 생성 지점 확인 |
| D-2 | 소스 | opbr_adapter (claude 호출) | `dashboard/backend/adapters/opbr_adapter.py` | prime_and_ask 계약(cold/resume, cwd 격리) 불변 확인 |
| D-3 | 소스 | brain 라우터 | `dashboard/backend/routers/brain.py` | prime/query 진입 흐름과 최소 변경 지점 확인 |
| D-4 | 소스 | config (콘솔 설정 로더) | `dashboard/backend/config.py` | prewarm_projects 키 추가 대상 + 기존 소비처 영향 확인 |
| D-5 | 소스 | main (FastAPI 앱) | `dashboard/backend/main.py` | 기동 훅 부재 확인 + lifespan 신설 지점 |
| D-6 | 소스 | console scan 머지 스크립트 | `opal/tools/opal-cli/lib/console.sh:180-235` | config 신규 키 보존 여부 확인(수정 대상 아님) |
| D-7 | 소스 | test_brain (기존 테스트) | `dashboard/backend/tests/test_brain.py` | 픽스처·모킹 패턴 재사용 가능성 확인 |
| D-8 | 소스 | 콘솔 데몬 기동 커맨드 | `opal/tools/opal-cli/lib/console.sh:75-77` | uvicorn 호출 방식(--app-dir) → lifespan 호환성 확인 |
| D-9 | 설계 | 059 태스크 (ID 분리·[ASSISTANT] 캡) | `tasks/059-260713-opds-에이전트마커-3단-세션주입/` | conversation_id↔claude 핸들 분리 설계 배경 |
| D-10 | 설계 | ARCHITECTURE.md §OPAL Console | `docs/ARCHITECTURE.md §OPAL Console` | Console BE 구조·배포 모델 정합성 확인 |
| D-11 | 외부 | FastAPI 공식 문서 — lifespan | [FastAPI — Lifespan Events](https://fastapi.tiangolo.com/advanced/events/) | `@app.on_event` deprecated 확인 + `lifespan=` 파라미터가 권장 대체 패턴임을 확인 (context7 `/fastapi/fastapi` 조회, 설치버전 0.137.1과 호환) |

## 1. 기존 코드 분석

### 1.1 관련 파일 목록

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| `dashboard/backend/adapters/brain_session.py` | 대화별 세션 상태기계(`ConversationBrainSession`) + 레지스트리(`BrainSessionRegistry`) | 수정 (풀 클래스 신설 + `_get_or_create` 웜 핸들 주입) | `brain_session.py:53-101`(세션 클래스), `brain_session.py:468-501`(레지스트리·생성 지점) |
| `dashboard/backend/adapters/opbr_adapter.py` | `prime_and_ask` claude 서브프로세스 계약 | 미변경(참조만) | `opbr_adapter.py:93-227` |
| `dashboard/backend/routers/brain.py` | prime/query/status/job API 진입점 5종 | 변경 불요 또는 최소(레지스트리 내부 위임 유지 시 무변경) | `routers/brain.py:158-259`(prime/query 엔드포인트) |
| `dashboard/backend/config.py` | `console.config.json` 로더·`ConsoleConfig` dataclass | 수정 (`prewarm_projects` 필드 추가) | `config.py:26-53` |
| `dashboard/backend/main.py` | FastAPI 앱 생성·라우터 등록 | 수정 (`lifespan` contextmanager 신설) | `main.py:33-37`(app 생성부, 훅 부재) |
| `dashboard/backend/tests/test_brain.py` | 브레인 단위·통합 테스트 (2377줄) | 수정(추가) — 풀 테스트 클래스 신설 + 픽스처 확장 | `test_brain.py:71-86`(fixture), `test_brain.py:1519-1630`(라우터 테스트 패턴) |
| `opal/tools/opal-cli/lib/console.sh` | `console scan` config 생성·머지 | 미변경(검증 근거만) | `console.sh:196-235` |
| `dashboard/backend/models.py` | Pydantic 응답 스키마 | 미변경(API 계약 불변 — TASK 확정방향 §7) | `models.py:189-230` |

### 1.2 아키텍처 패턴

- **레이어드 구조**: `routers/brain.py`(라우터) → `adapters/brain_session.py`(상태·동시성) → `adapters/opbr_adapter.py`(subprocess 얇은 프록시). 풀 신설도 이 레이어 경계를 유지해야 한다 — subprocess 호출 세부(cold/resume 플래그, cwd)는 `opbr_adapter.py`에만 남기고, 풀은 `brain_session.py` 레이어에 위치시킨다.
- **모듈 레벨 싱글턴 레지스트리**: `brain_session_registry = BrainSessionRegistry()` (`brain_session.py:601`) — 데몬 프로세스 내 단일 인스턴스 공유. 풀도 동일 패턴(모듈 레벨 싱글턴)을 따르는 것이 기존 관례와 정합적이다.
- **"락-해제-블로킹호출-재획득" 락 관용구**: `ConversationBrainSession.prime()`(`brain_session.py:206-234`), `_cold_and_ask()`(`:316-339`), `_warm_ask()`(`:342-363`) 세 곳 모두 동일 패턴을 반복한다 — ①lock 하에서 상태를 `priming`으로 표시 ②lock 해제 후 블로킹 subprocess 호출(최대 180s) 실행 ③lock 재획득 후 결과 커밋. 풀의 백그라운드 리필도 이 관용구를 그대로 재사용해야 데드락을 피할 수 있다.
- **이중 락 계층**: 전역 `BrainSessionRegistry._lock`(dict 접근 보호, `brain_session.py:481`)과 세션별 `ConversationBrainSession._lock`(개별 상태 보호, `:86`)이 분리되어 있다 — `_get_or_create()`(`:486-501`)는 레지스트리 락만 짧게 보유하고 세션 생성(비블로킹) 후 즉시 반환, 세션 메서드(`prime`/`ask`) 호출은 레지스트리 락 밖에서 이루어진다. 두 락이 동시에 중첩 보유되는 지점이 없다.
- **상태기계**: `idle → priming → ready/error`, `reset()`으로 언제든 `idle` 복귀. 풀 항목도 유사한 명시적 상태(예: `idle`(비어있음)/`priming`/`ready`(체크아웃 가능))를 두는 것이 기존 관례와 일관적이다.

### 1.3 의존성 맵

```
main.py
  └─ (신규) config.load_config()          ← prewarm_projects 읽기
  └─ (신규) adapters.brain_session          ← lifespan에서 풀 등록 호출
  └─ routers.{dashboard,projects,tasks,memory,doctor,brain}  (기존, 무변경)

routers/brain.py
  ├─ adapters.brain_session.brain_session_registry  (prime/status/query/job 위임)
  ├─ config.load_config()                            (project 경로 검증)
  ├─ scanner.scan_projects()
  └─ models (BrainAuthResponse 등 5개 스키마)

adapters/brain_session.py
  └─ adapters.opbr_adapter.prime_and_ask()  (유일한 외부 실행 지점)

adapters/opbr_adapter.py
  └─ subprocess, json, re, os, time, logging (외부 라이브러리 의존 없음)

config.py
  └─ (의존 없음 — 리프 모듈)
```

- `config.py`를 소비하는 곳은 `main.py`(신규 예정) 포함 6개 지점 확인: `routers/memory.py:18,32,88`, `routers/projects.py:22,36`, `routers/dashboard.py:20,122`, `routers/tasks.py:29,81,320`, `routers/brain.py:24,51` — 모두 `cfg.scan_roots`/`cfg.scan_depth`/`cfg.exclude`를 이름으로 접근(위치 기반 아님)하므로 `ConsoleConfig`에 필드 추가는 이들에 영향 없음.
- `main.py`와 `brain_session.py`·`config.py` 사이에는 기존 순환 의존이 없다 — `brain_session.py`/`config.py` 모두 `main.py`를 import하지 않으므로 lifespan에서 두 모듈을 import해도 순환 위험 없음.

### 1.4 테스트 현황

- `dashboard/backend/tests/test_brain.py` 총 2377줄, 15개 테스트 클래스(`TestExtractJsonFence`, `TestOpbrAdapterCmd`, `TestOpbrAdapterColdWarm`, `TestConversationBrainSessionCold/Warm/Reset/Crash/State`, `TestBrainSessionRegistry`, `TestSessionIdHandleSeparation`, `TestBrainRouterPrime/Query/Errors/Status`, `TestBrainJobPolling` 등)로 브레인 도메인 커버리지가 두텁다 (`test_brain.py:1-32` @header exports 목록).
- **모킹 원칙 확인**: 모든 테스트가 `subprocess.run` 또는 `opbr_adapter.prime_and_ask`를 `unittest.mock.patch`로 대체 — 실 claude 호출 0회(H-8, `test_brain.py:6` @header "[MUST] 서브프로세스 전부 mock — 실 claude/brain-tool 호출 0회").
- **autouse 픽스처**: `reset_brain_registry`(`test_brain.py:77-86`)가 매 테스트 전후로 `brain_session_registry._sessions`를 클리어 — 새 풀이 별도 모듈 레벨 싱글턴(예: `brain_prime_pool`)으로 신설되면 이 픽스처가 풀 상태까지 커버하지 못하므로 확장 또는 병행 픽스처가 필요(§5 R5).
- **라우터 레벨 패턴**: `TestBrainRouterPrime`(`:1519-1630`)이 `client.post("/api/brain/prime", ...)`와 `_mock_scan_projects_with()` 헬퍼로 project 검증을 우회하는 방식을 확립 — 풀 체크아웃이 관여하는 새 대화 흐름 테스트도 동일 헬퍼 재사용 가능.
- **lifespan 테스트 관례 부재**: 현재 `main.py`에 기동 훅이 없으므로 `client` 픽스처(`test_brain.py:71-74`, `TestClient(app)`)가 lifespan을 트리거하는 방식(`with TestClient(app) as client:`)의 선례가 없음 — F-3 테스트 작성 시 신규 패턴 도입 필요(§6.3).

## 2. 외부 조사 결과

### 2.1 라이브러리/API 조사

- FastAPI 설치 버전 확인: `pip3 show fastapi` → `0.137.1` (로컬 venv).
- context7(`/fastapi/fastapi`) 조회 결과, `@app.on_event("startup"/"shutdown")`와 `on_startup=`/`on_shutdown=` 생성자 파라미터는 모두 **deprecated** 표시(`applications.py` 소스 인용: `"on_event is deprecated, use lifespan event handlers instead."`)이며, `lifespan=` 파라미터가 공식 대체 패턴으로 문서화되어 있다 — `@asynccontextmanager async def lifespan(app): ...; yield; ...` 형태로 `FastAPI(lifespan=lifespan)` 생성자에 전달한다.
- 위 조사에 따라 F-3 구현은 `@app.on_event` 방식이 아닌 `lifespan` contextmanager 방식을 채택해야 최신 FastAPI 권장 패턴과 정합한다.

### 2.2 버전 호환성

- FastAPI 0.137.1은 `lifespan` 파라미터를 완전 지원(0.93+부터 안정화된 API, 현재 설치 버전에서 이상 없음).
- uvicorn 기동 방식 확인: `opal-cli console.sh:75-77`가 `nohup <venv>/bin/uvicorn --app-dir <dashboard-server> dashboard.backend.main:app`로 실행 — `--lifespan off` 등의 플래그가 없으므로 uvicorn 기본값(`lifespan="auto"`)이 적용되어 신설 lifespan 훅이 별도 CLI 변경 없이 자동 실행된다. 배포 스크립트(install) 변경도 불필요(TASK 범위 제외 항목과 정합).

## 3. 영향 범위

### 3.1 직접 영향

- `dashboard/backend/config.py` — `ConsoleConfig`에 `prewarm_projects: list[str] = []` 필드 추가, `load_config()`에 파싱 로직 추가.
- `dashboard/backend/adapters/brain_session.py` — 프로젝트별 웜 핸들 풀 클래스(또는 `BrainSessionRegistry` 확장) 신설, `_get_or_create()`에 웜 핸들 주입 로직 연결.
- `dashboard/backend/main.py` — `app = FastAPI(...)` 생성자에 `lifespan=` 파라미터 추가, 별도 `lifespan` 비동기 컨텍스트 매니저 함수 신설.
- `dashboard/backend/routers/brain.py` — F-4(a) 요구사항 충족을 위해 필요 시 최소 변경(레지스트리가 내부에서 풀을 흡수하면 무변경 가능성 높음, §4 근거 2).
- `dashboard/backend/tests/test_brain.py` — 풀 신규 테스트 클래스 추가 + 기존 `reset_brain_registry` 픽스처 확장.

### 3.2 간접 영향

- `dashboard/backend/routers/memory.py`, `projects.py`, `dashboard.py`, `tasks.py` — `load_config()`를 이름 기반 속성 접근으로 사용하므로 `ConsoleConfig` 필드 추가에 의한 회귀 없음(§1.3 근거).
- `~/.opal/console.config.json` — 신규 키 `prewarm_projects` 추가 대상이나, `console.sh:210-235`의 머지 스크립트는 `scan_roots`만 조작하고 그 외 키를 `data`(로드된 JSON 전체)에 보존하므로 `opal-cli console scan` 재실행 시에도 안전(D-6).
- `docs/ARCHITECTURE.md §OPAL Console` — "세션" 행(`ARCHITECTURE.md:260`)이 현재 prime-on-intent·5트리거 리셋만 기술하고 풀 개념이 없음 — F-5 완료 후 문서 동기화 필요성 존재(코드 변경 자체의 영향 범위는 아니므로 리스크로만 기재).

### 3.3 영향 범위 요약

- [ ] DB 스키마 변경 — 해당 없음(인메모리 전용, backend 무상태 원칙 유지)
- [x] API 인터페이스 변경 — 아니오, 단 **설정 스키마**(config.py 내부 dataclass) 확장 있음. FE-facing API 5종 계약은 불변(TASK 확정방향 §7)
- [x] 설정/환경변수 변경 — `console.config.json`에 `prewarm_projects` 키 신설
- [ ] 빌드/배포 파이프라인 변경 — 해당 없음(기존 `uvicorn --app-dir` 기동 경로 그대로 재사용, D-8)

## 4. 핵심 발견 사항

1. `ConversationBrainSession.prime()`/`_cold_and_ask()`/`_warm_ask()` 세 메서드 모두 "락 하에서 상태 표시 → 락 해제 후 블로킹 subprocess(최대 180s) → 락 재획득 후 커밋" 관용구를 반복 사용한다(`brain_session.py:206-234, 316-339, 342-363`). 풀의 백그라운드 리필이 이 관용구를 어기고 풀 구조 락을 쥔 채로 subprocess를 호출하면, 그 사이 다른 체크아웃 요청이 최대 56초간 블로킹되는 실질적 데드락 유사 상황이 발생한다 — 풀 구현은 반드시 "락 하에서 pop(비블로킹) → 락 해제 → subprocess 실행 → 락 재획득 후 append" 순서를 지켜야 한다.
2. `BrainSessionRegistry._get_or_create()`(`brain_session.py:486-501`)가 `ConversationBrainSession` 생성의 유일한 진입점이다 — 여기에 "project_path에 대응하는 풀 핸들이 있으면 체크아웃하여 새 세션에 주입" 로직을 넣으면, `routers/brain.py`의 prime/query 엔드포인트는 무변경으로 F-4(a)(c) 요구사항(API 계약 불변)을 자연히 만족시킬 수 있다.
3. `main.py`는 현재 어떤 형태의 기동 훅도 갖고 있지 않다(`@app.on_event`/`lifespan` grep 결과 0건). 로컬 설치된 FastAPI 0.137.1은 `@app.on_event`를 deprecated로 표시하며 `lifespan=` contextmanager를 공식 대체로 문서화한다(context7 `/fastapi/fastapi` 조회) — 따라서 F-3은 `lifespan` 방식으로 구현해야 최신 관례와 정합한다.
4. `opal-cli console.sh:75-77`의 uvicorn 기동 커맨드(`--app-dir <dir> dashboard.backend.main:app`, `--lifespan` 플래그 없음)는 uvicorn 기본값(`lifespan="auto"`)을 그대로 사용하므로, 신설 lifespan 훅은 배포 스크립트나 CLI 변경 없이 즉시 적용된다 — TASK 범위 제외 항목("install 배포 스크립트 변경 없음")과 정합.
5. `console.sh:210-235`의 config 머지 스크립트는 `scan_roots` 키만 갱신하고 나머지 최상위 키는 로드한 `data` dict 그대로 보존한다(`data["scan_roots"] = final` 한 줄만 덮어씀) — `prewarm_projects` 신규 키를 config.py 스키마에 추가해도 `console scan` 재실행 시 유실되지 않음이 코드로 확인된다.
6. 기존 테스트는 전부 `opbr_adapter.prime_and_ask`/`subprocess.run`을 mock하고, `reset_brain_registry` autouse 픽스처(`test_brain.py:77-86`)로 `brain_session_registry._sessions`만 클리어한다 — 풀이 별도 모듈 레벨 싱글턴으로 신설되면 이 픽스처가 커버하지 못해 테스트 간 풀 상태가 누적될 위험이 있다(§5 R5). 풀을 `BrainSessionRegistry`의 속성으로 통합하거나 픽스처를 확장해야 한다.

## 5. 제약/리스크

| # | 항목 | 설명 | 심각도 | 근거 |
|---|------|------|--------|------|
| R1 | 락 순서/중첩 데드락 | 풀 구조 락(신설)과 레지스트리 락(`_lock`, `brain_session.py:481`)·세션 락(`_lock`, `:86`)의 획득 순서가 뒤섞이면 데드락 위험. 특히 백그라운드 리필 스레드가 풀 락을 쥔 채 56초 subprocess를 호출하면 신규 체크아웃 요청이 전부 블로킹됨 | High | `brain_session.py:206-234`(참조 관용구), TASK 확정방향 §3·§5 |
| R2 | lifespan 기동 지연 | lifespan 컨텍스트 매니저 본문에서 프라임 subprocess를 동기적으로 `await`/블로킹 호출하면 서버 기동 자체가 지연되어 F-3 AC("미지정 시 프라임 0회·기동 지연 없음", 지정 시에도 즉시 응답 가능해야 함)를 위반할 수 있음. 기존 `routers/brain.py:190-195`의 `_prime_background`처럼 daemon 스레드로 분리해야 함 | High | TASK F-3 AC, `routers/brain.py:189-195`(기존 패턴) |
| R3 | 동시 프라임 상한 미구현 시 구독 사용량 급증 | 확정 설계 §4(동시 프라임 상한 1~2)를 세마포어 등으로 강제하지 않으면, 기동 시 다중 `prewarm_projects` 프라임 + 체크아웃 리필이 동시에 몰려 구독 `claude -p` 호출이 무제한 병렬 실행됨 | Medium | TASK 확정 설계방향 §4, `opbr_adapter.py:23-25`([MUST] 구독 경로 전용) |
| R4 | config 타입 검증 부재 | `load_config()`(`config.py:43-53`)는 현재 `data.get(key, default)` 단순 폴백만 수행 — `prewarm_projects`가 배열이 아닌 값(문자열 등)으로 잘못 기재되면 즉시 예외 없이 하위 로직(풀 초기화 순회)에서 런타임 오류로 전파될 수 있음. F-1 AC("잘못된 타입 시 기본 `[]`")가 명시적 타입 가드를 요구 | Medium | TASK F-1 AC, `config.py:43-53` |
| R5 | 테스트 픽스처 미확장 시 상태 오염 | `reset_brain_registry`(`test_brain.py:77-86`)가 `_sessions` dict만 클리어 — 풀이 별도 싱글턴이면 테스트 순서에 따라 풀 상태가 누적되어 플레이키 테스트 발생 가능 | Medium | `test_brain.py:77-86` |
| R6 | 문서 동기화 지연 | `docs/ARCHITECTURE.md §OPAL Console` "세션" 행(`:260`)이 prime-on-intent·5트리거 리셋만 기술하며 풀 개념이 없음 — F-5 완료 후에도 문서 갱신이 누락되면 아키텍처 문서와 실제 구현 간 불일치 발생 | Low | `docs/ARCHITECTURE.md §OPAL Console` |

## 6. 기술 컨텍스트

### 6.1 기술 스택

| 카테고리 | 기술 | 버전 |
|----------|------|------|
| 언어 | Python | 3.11+ |
| 프레임워크 | FastAPI | 0.137.1 (pip3 show 확인) |
| ASGI 서버 | uvicorn | `~/.opal/.venv/bin/uvicorn` (venv 공유, `console.sh:35`) |
| 동시성 | threading (Lock, Thread, Semaphore 예정) | 표준 라이브러리 |
| 테스트 | pytest + FastAPI `TestClient` | 기존 `test_brain.py` 패턴 |
| 외부 프로세스 | claude CLI (`claude -p --session-id/--resume --output-format json`) | 구독 인증(subscription), API 키 미사용 |

### 6.2 추천 스킬

| 스킬 | 용도 |
|------|------|
| (해당 없음) | 이번 태스크는 프로젝트 내부 Python/FastAPI 표준 패턴 확장이며 별도 프레임워크 스킬 도입 불요 |

### 6.3 추천 MCP

| MCP | 용도 |
|-----|------|
| context7 | FastAPI `lifespan` 최신 API 확인(완료 — §2.1), 필요 시 PLAN 단계에서 `threading.Semaphore` 동시 상한 패턴 재확인 |
