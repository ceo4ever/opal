# PLAN: OPAL Console 브레인 프라임 연결 풀 — 지정 프로젝트 선프라임 + 새 대화 웜 핸들 배정

> 작성일: 2026-07-14 | 입력: TASK.md, ANALYSIS.md
> 모드: Multi-Feature | 실행 모드: 복잡

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

OPAL Console 백엔드에 **프로젝트별 웜 핸들 풀**을 신설한다. `console.config.json`의 `prewarm_projects`에 지정한 프로젝트를 서버 기동 시 백그라운드 선프라임하여 풀에 적재하고(F-1·F-3), 새 대화 세션이 처음 생성될 때 풀에서 웜 핸들을 체크아웃하여 주입한다(F-2·F-4). 체크아웃 시 백그라운드 리필로 풀을 다시 채운다. 목표는 새 대화 첫 질의의 콜드 대기(실측 ~56s, `dashboard/backend/adapters/opbr_adapter.py:6` @header)를 웜 수준(`--resume`, ~수초)으로 단축하는 것이다. FE·기존 브레인 API 5종 계약은 불변이며, 풀은 인메모리 전용(backend 무상태 원칙 유지)이다.

### 1.2 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | config 확장 (prewarm_projects + 타입 가드) | TASK F-1 | P0 | 없음 |
| F-002 | 프라임 풀 신설 (선프라임·lock 체크아웃·백그라운드 리필·동시 상한) | TASK F-2 | P0 | 없음 |
| F-003 | 기동 선프라임 (lifespan 훅) | TASK F-3 | P0 | F-001, F-002 |
| F-004 | 새 대화 웜 핸들 배정 + 콜드 폴백 | TASK F-4 | P0 | F-002 |
| F-005 | 실기동 검증 (선프라임→웜 배정 흐름) | TASK F-5 | P1 | F-001, F-002, F-003, F-004 |

### 1.3 기능 의존 그래프 (ASCII)

```
F-001 (config) ─┐
                ├─→ F-003 (lifespan 선프라임) ─┐
F-002 (풀) ─────┤                              ├─→ F-005 (실기동 검증)
                └─→ F-004 (웜 배정/폴백) ──────┘
```

---

## 리스크 가설 표

> PLAN 단계에서 작성. TEST-SCENARIO.md §1의 입력이 됨. ANALYSIS §5 R1~R6 계승·구체화.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | F-002 리필 스레드 (R1) | 풀 락을 쥔 채 56s subprocess 호출 시 후속 체크아웃 전면 블로킹(데드락 유사) | P0 | L2(동시성 통합) | TS-204, TS-205 |
| H-2 | F-002 락 계층 (R1 확장) | 레지스트리 락 보유 중 세션 락 획득 시 기존 무중첩 불변(ANALYSIS §1.3) 위반 → 교착 | P0 | L1(단위)+L2 | TS-206 |
| H-3 | F-002 세마포어 (R3) | 동시 프라임 상한 미강제 시 구독 `claude -p` 무제한 병렬 → 사용량 급증 | P1 | L1(동시성 단위) | TS-203 |
| H-4 | F-001 타입 가드 (R4) | `prewarm_projects`가 비-list(문자열 등)일 때 하위 순회에서 런타임 오류 | P1 | L1(단위) | TS-101, TS-102 |
| H-5 | F-004 웜 핸들 stale (신규) | 오래된 풀 핸들의 `--resume` 실패 → 첫 질의 오류 | P1 | L1(단위, mock resume 실패) | TS-403 |
| H-6 | F-003 lifespan 블로킹 (R2) | lifespan 본문에서 프라임 동기 호출 시 서버 기동 지연 | P1 | L2(TestClient lifespan)+L3(실기동) | TS-301, TS-501 |
| H-7 | F-002/F-004 테스트 픽스처 (R5) | `reset_brain_registry`가 풀 상태 미클리어 → 테스트 간 상태 누적 플레이키 | P2 | L1(픽스처 회귀) | TS-207 |
| H-8 | 전 범위 (R6) | `docs/ARCHITECTURE.md §OPAL Console` "세션" 행이 풀 개념 미반영 → 문서-구현 불일치 | P2 | L3(문서 리뷰) | TS-701 |

---

## 2. 기능별 분석

### F-001: config 확장 (prewarm_projects + 타입 가드)

#### 2.1.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| BE | `dashboard/backend/config.py` | `ConsoleConfig` dataclass + `load_config()` 로더 | 수정 |
| 환경 | `~/.opal/console.config.json` | 소비 대상 설정 파일 (신규 키 `prewarm_projects` 수용) | 미변경(런타임 데이터) |

#### 2.1.2 현재 구현
`ConsoleConfig`는 `scan_roots`/`scan_depth`/`exclude` 3필드 dataclass이며 `load_config()`는 `data.get(key, default)` 단순 폴백만 수행한다(`config.py:26-53`). 타입 검증은 `scan_depth`의 `int()` 캐스팅 외에는 없다(`config.py:51`). 리프 모듈로 의존이 없다(`config.py:8` @header depends `[]`).

#### 2.1.3 영향 범위
`load_config()` 소비처 6곳(`routers/memory.py`, `projects.py`, `dashboard.py`, `tasks.py`, `brain.py`, 신규 `main.py`)은 모두 이름 기반 속성 접근이므로 필드 추가에 회귀 없음(ANALYSIS §1.3). `console.sh:210-235` 머지 스크립트는 `scan_roots`만 갱신하고 나머지 키를 보존하므로 신규 키가 `console scan` 재실행 시 유실되지 않음(ANALYSIS §4 발견 5, → D-6).

---

### F-002: 프라임 풀 신설

#### 2.2.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| BE | `dashboard/backend/adapters/brain_session.py` | `BrainSessionRegistry` 풀 속성·메서드 신설 + `ConversationBrainSession.adopt_warm_handle` 신설 | 수정 |
| BE | `dashboard/backend/adapters/opbr_adapter.py` | `prime_and_ask` 호출(cold 프라임) | 미변경(참조만) |

#### 2.2.2 현재 구현
`BrainSessionRegistry`는 `_lock`(dict 보호) + `_sessions` dict 싱글턴이다(`brain_session.py:468-501, 601`). `ConversationBrainSession`은 세션별 `_lock`으로 상태를 보호하며(`brain_session.py:86`), `prime()`/`_cold_and_ask()`/`_warm_ask()`가 "락 하 상태표시 → 락 해제 후 블로킹 subprocess → 락 재획득 후 커밋" 관용구를 공유한다(`brain_session.py:206-234, 316-339, 342-363`). 콜드 프라임은 `_cold_prime_with_retry()`가 새 `uuid4`를 발급하여 `opbr_adapter.prime_and_ask(cold=True)`를 호출하는 방식이다(`brain_session.py:275-308`).

#### 2.2.3 영향 범위
풀은 `BrainSessionRegistry` 속성으로 통합한다(별도 모듈 싱글턴 아님 — R5/H-7 회피, ANALYSIS §5 R5). 신규 `_pool_lock`은 기존 `_lock`(레지스트리)·세션 `_lock`과 **일방향 순서**(`_lock`→`_pool_lock` 허용, 역순·세션락 중첩 금지)를 지켜 R1/H-2를 차단한다. subprocess 호출은 어떤 락도 쥐지 않은 채 수행한다(관용구 계승).

---

### F-003: 기동 선프라임 (lifespan 훅)

#### 2.3.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| BE | `dashboard/backend/main.py` | FastAPI 앱 생성 + `lifespan` contextmanager 신설 | 수정 |
| 환경 | `opal/tools/opal-cli/lib/console.sh` | uvicorn 기동(`--lifespan` 플래그 없음 → 기본 auto) | 미변경(검증 근거만, → D-6) |

#### 2.3.2 현재 구현
`main.py`는 `app = FastAPI(title=..., version=...)`만 생성하고 어떤 기동 훅도 없다(`main.py:33-37`, `@app.on_event`/`lifespan` grep 0건 — ANALYSIS §4 발견 3). uvicorn은 `console.sh:75-77`에서 `--app-dir ... dashboard.backend.main:app`로 기동되며 `--lifespan` 플래그가 없어 기본값(`lifespan="auto"`)이 적용된다 — 신설 lifespan이 배포·CLI 변경 없이 자동 실행된다(ANALYSIS §4 발견 4).

#### 2.3.3 영향 범위
`main.py`가 `config.load_config`·`adapters.brain_session`을 import하나, 두 모듈 모두 `main.py`를 import하지 않으므로 순환 의존 없음(ANALYSIS §1.3). FastAPI 0.137.1은 `lifespan=` 파라미터를 완전 지원하며 `@app.on_event`는 deprecated이다(ANALYSIS §2.1, → D-11).

---

### F-004: 새 대화 웜 핸들 배정 + 콜드 폴백

#### 2.4.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| BE | `dashboard/backend/adapters/brain_session.py` | `BrainSessionRegistry._get_or_create()` 웜 주입 연결 | 수정 |
| BE | `dashboard/backend/routers/brain.py` | prime/query/status 진입점 | 미변경(레지스트리 내부 흡수 — ANALYSIS §4 발견 2) |

#### 2.4.2 현재 구현
`_get_or_create()`는 `ConversationBrainSession` 생성의 유일한 진입점이며, 레지스트리 `_lock`을 짧게 보유하고 세션 생성(비블로킹) 후 즉시 반환한다(`brain_session.py:486-501`). prime/ask/submit_job/status가 모두 이를 경유한다(`brain_session.py:503-580`). 웜 핸들이 주입되면 첫 질의는 `ask()`의 웜 분기(`_warm_ask`, `--resume`)를 그대로 탄다(`brain_session.py:260-273, 342-363`) — ask 분기 로직 변경 불요(TASK 배경분석).

#### 2.4.3 영향 범위
`routers/brain.py`는 무변경 유지(F-4(c) API 계약 불변, ANALYSIS §4 발견 2). 주입은 `_get_or_create()`가 **신규 세션을 생성한 경우에만** 발생하며, 레지스트리 락 해제 후 세션 락으로 `adopt_warm_handle`을 호출하여 무중첩 불변을 지킨다(H-2). 풀이 비면 세션은 `idle`로 남아 기존 콜드 경로로 폴백한다(F-4(b) 회귀 없음).

---

### F-005: 실기동 검증

#### 2.5.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 환경 | `~/.opal/console.config.json` | `prewarm_projects`에 본 프로젝트 지정 | 런타임 설정(코드 아님) |
| 배치 | 로컬 콘솔 데몬 (`opal-cli console`) | 기동→로그→새 대화 질의 elapsed 관측 | 검증 절차 |

#### 2.5.2 현재 구현
콘솔 데몬 로그는 `/tmp/opal-console.log`로 출력된다(`main.py:23-28` basicConfig). 브레인 질의 elapsed는 `[brain] job 완료 ... elapsed=%.1fs` 로그로 관측 가능하다(`brain_session.py:428-431`).

#### 2.5.3 영향 범위
TEST 단계에서 수행하는 L3(실기동) 검증이며 코드 산출물은 없다. 검증 절차는 §3.5.2에 기술한다.


---

## 3. 기능별 설계

> [MUST] `dashboard/backend/adapters/opbr_adapter.py:23`: "--safe-mode·--bare·anthropic SDK·ANTHROPIC_API_KEY 절대 사용 금지" — 풀 프라임도 구독 `claude -p` 경로만 사용. opbr_adapter 미변경.
> [MUST] `dashboard/backend/adapters/brain_session.py:6`: "backend 무상태 원칙 — Q&A 내용 저장 안 함. 세션 핸들만(휘발성 프로세스 상태) 보유, DB·파일 영속 금지" — 풀도 인메모리 한정.
> [MUST] `docs/CONVENTIONS.md` §@header 규칙: "코드 파일을 생성·수정할 때 파일 상단에 @header 블록을 작성한다" — 수정 4파일 모두 @header 갱신 의무.

### F-001: config 확장

#### 3.1.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `dashboard/backend/config.py` | BE | `ConsoleConfig.prewarm_projects` 필드 + `load_config()` 타입 가드 파싱 + @header exports/description 갱신 | `config.py:26-53`, R4/H-4 |

#### 3.1.2 API·데이터 모델·화면 설계
- `ConsoleConfig`에 필드 추가 — `[MUST]` 기본값 빈 리스트: `prewarm_projects: list[str] = field(default_factory=list)` (기존 `field` import 재사용, `config.py:16`).
- `load_config()`에 타입 가드 헬퍼를 추가한다 (R4/H-4 명시적 요구):
  ```python
  def _coerce_str_list(value: object) -> list[str]:
      """list[str]이 아니면 빈 리스트로 폴백. 원소 중 str만 취해 안전 순회 보장."""
      if not isinstance(value, list):
          return []
      return [v for v in value if isinstance(v, str)]
  ```
- `load_config()` 반환에 `prewarm_projects=_coerce_str_list(data.get("prewarm_projects", []))` 추가 (`config.py:49-52` 반환 블록 확장).
- AC 충족: 키 부재→`[]`, 빈 배열→`[]`, 잘못된 타입(문자열/dict)→`[]`, 정상 배열→원소 중 문자열만 로드.

#### 3.1.3 환경 변경
해당 없음 (표준 라이브러리만 사용).

#### 3.1.4 배치/마이그레이션
해당 없음.

#### 3.1.5 테스트 시나리오 (AC ↔ TS 매핑)
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-101 | F-1 AC | 기능 테스트 | 키 부재·빈 배열 → `prewarm_projects == []` |
| TS-102 | F-1 AC | 기능 테스트 | 문자열·dict 등 비-list 값 → `[]`로 폴백(예외 없음) |
| TS-103 | F-1 AC | 기능 테스트 | 정상 배열(경로 2개) → 리스트 그대로 로드, 비-str 원소는 제외 |

---

### F-002: 프라임 풀 신설

#### 3.2.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `dashboard/backend/adapters/brain_session.py` | BE | `BrainSessionRegistry` 풀 속성·`prewarm`/`_prime_into_pool`/`checkout_warm_handle` 신설 + `ConversationBrainSession.adopt_warm_handle` 신설 + 상수 2종 + @header 갱신 | `brain_session.py:468-501`, R1/R3/R5 |

#### 3.2.2 API·데이터 모델·화면 설계

**신규 상수** (`brain_session.py` 모듈 레벨, `:35-41` 부근):
- `DEFAULT_POOL_SIZE: int = 1` (확정 방향 §2 — 프로젝트당 웜 핸들 1개)
- `DEFAULT_MAX_CONCURRENT_PRIME: int = 2` (확정 방향 §4 — 동시 프라임 상한, R3/H-3)
- `PREWARM_QUESTION: str = "프로젝트 브레인 세션을 초기화합니다."` (기존 `prime()` 프라임 질의 재사용, `brain_session.py:219`)

**`BrainSessionRegistry.__init__` 확장** (`brain_session.py:476-484`):
```python
def __init__(self, max_turns=DEFAULT_MAX_TURNS, idle_timeout_s=DEFAULT_IDLE_TIMEOUT_S,
             pool_size: int = DEFAULT_POOL_SIZE,
             max_concurrent_prime: int = DEFAULT_MAX_CONCURRENT_PRIME) -> None:
    # ... 기존 필드 ...
    self.pool_size = pool_size
    self._pool_lock = threading.Lock()                        # 풀 전용 락 (레지스트리 _lock과 분리)
    self._pool: dict[str, list[str]] = {}                     # project_path → [claude_session_id, ...]
    self._pool_inflight: dict[str, int] = {}                  # project_path → 리필 진행 중 카운트
    self._prime_semaphore = threading.Semaphore(max_concurrent_prime)  # 동시 프라임 상한 (R3)
```

**락 순서 계약** [MUST]: `_lock`(레지스트리)→`_pool_lock`(풀) 방향만 허용. `_pool_lock` 보유 중 `_lock`·세션 `_lock` 획득 금지. 어떤 락도 subprocess 호출 중 보유 금지(R1/H-1, H-2). 세마포어는 상태 보호용이 아니라 동시성 상한 장치이므로 subprocess 구간에서 보유 가능(R3).

**`prewarm(self, project_path: str) -> None`** — 풀 목표치 미달 시 백그라운드 리필 스레드 1개 기동:
```python
def prewarm(self, project_path: str) -> None:
    with self._pool_lock:                     # 비블로킹 구간만 락 보유
        have = len(self._pool.get(project_path, [])) + self._pool_inflight.get(project_path, 0)
        if have >= self.pool_size:
            return                            # 이미 채워짐/채우는 중 — 과잉 프라임 방지(size 1)
        self._pool_inflight[project_path] = self._pool_inflight.get(project_path, 0) + 1
    threading.Thread(target=self._prime_into_pool, args=(project_path,), daemon=True).start()
```

**`_prime_into_pool(self, project_path: str) -> None`** — 락 없이 subprocess 실행 후 락 재획득하여 append (R1 관용구):
```python
def _prime_into_pool(self, project_path: str) -> None:
    with self._prime_semaphore:               # 동시 프라임 상한 강제 (R3/H-3)
        try:
            handle = str(uuid.uuid4())        # opbr_adapter는 uuid 생성 안 함 — BE가 발급
            result = opbr_adapter.prime_and_ask(
                question=PREWARM_QUESTION, project_path=project_path,
                session_id=handle, cold=True, timeout=COLD_TIMEOUT_S)   # 락 미보유 구간
            sid = result.get("session_id") or handle
            with self._pool_lock:
                self._pool.setdefault(project_path, []).append(sid)     # 락 재획득 후 append
            logger.info("[brain] prewarm 완료 project=%s pool=%d", project_path, len(self._pool[project_path]))
        except Exception as exc:
            logger.warning("[brain] prewarm 실패 project=%s error=%s", project_path, exc)  # 실패 시 폴백(콜드)
        finally:
            with self._pool_lock:
                self._pool_inflight[project_path] = max(0, self._pool_inflight.get(project_path, 0) - 1)
```

**`checkout_warm_handle(self, project_path: str) -> str | None`** — lock 하 pop(비블로킹) → 락 해제 → 백그라운드 리필 트리거 (R1 관용구, 확정 방향 §5):
```python
def checkout_warm_handle(self, project_path: str) -> str | None:
    with self._pool_lock:
        handles = self._pool.get(project_path)
        sid = handles.pop() if handles else None   # 동시 체크아웃 직렬화 → 중복 배정 차단(F-2(b)/H-?)
    if sid is not None:
        self.prewarm(project_path)                 # 락 해제 후 리필(내부에서 subprocess는 락 밖)
    return sid
```

**`ConversationBrainSession.adopt_warm_handle(self, claude_session_id: str) -> None`** — 웜 핸들을 세션에 이식(세션 `_lock` 하, `prime()` 성공 커밋과 동형 — `brain_session.py:221-228`):
```python
def adopt_warm_handle(self, claude_session_id: str) -> None:
    with self._lock:
        self._claude_session_id = claude_session_id
        self._created_at = time.monotonic()
        self._last_used = time.monotonic()
        self._turn_count = 1              # 프라임 질의 1회 반영(prime()와 동일)
        self._priming = False
        self._state = "ready"
        self._last_error = ""
```

- 동시성 계약: `checkout_warm_handle`의 `pop()`이 `_pool_lock`으로 직렬화되므로 동시 체크아웃 2건은 서로 다른 핸들 또는 `None`을 받는다(F-2(b)). `_prime_semaphore`가 동시 프라임 수를 `max_concurrent_prime` 이하로 강제한다(F-2(c)).

#### 3.2.3 환경 변경
해당 없음 (`threading.Semaphore`는 표준 라이브러리, ANALYSIS §6.1).

#### 3.2.4 배치/마이그레이션
해당 없음.

#### 3.2.5 테스트 시나리오 (AC ↔ TS 매핑)
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-201 | F-2 AC(a) | 기능 테스트 | `prewarm()` 호출(mock prime) 후 풀에 핸들 1개 적재 |
| TS-202 | F-2 AC(a) | 기능 테스트 | `checkout_warm_handle()`가 핸들 반환 + 풀 비워짐 + 리필 트리거(prewarm 재호출) |
| TS-203 | F-2 AC(c) | 동시성 테스트 | N개 prewarm 동시 기동 시 관측 최대 동시 prime ≤ `max_concurrent_prime`(2) |
| TS-204 | F-2 AC(b) | 동시성 테스트 | 동시 체크아웃 2건 — 같은 핸들 중복 배정 0건(서로 다르거나 하나는 None) |
| TS-205 | H-1 | 통합 테스트 | 리필 중(subprocess 진행) 다른 체크아웃이 블로킹 없이 즉시 반환(락 밖 subprocess 검증) |
| TS-206 | H-2 | 단위 테스트 | subprocess 진행 중 pool/registry/세션 락 무중첩(교착 미발생, 타임아웃 내 완료) |
| TS-207 | H-7 | 회귀 테스트 | `reset_brain_registry` 확장 후 테스트 간 풀 상태 초기화 확인 |

---

### F-003: 기동 선프라임 (lifespan 훅)

#### 3.3.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `dashboard/backend/main.py` | BE | `lifespan` asynccontextmanager 신설 + `FastAPI(lifespan=...)` 연결 + @header 갱신 | `main.py:33-37`, R2/H-6, → D-11 |

#### 3.3.2 API·데이터 모델·화면 설계
- FastAPI 0.137.1 권장 패턴 `lifespan` contextmanager 채택 ([FastAPI — Lifespan Events](https://fastapi.tiangolo.com/advanced/events/), → D-11):
  ```python
  from contextlib import asynccontextmanager
  from dashboard.backend.config import load_config
  from dashboard.backend.adapters.brain_session import brain_session_registry

  @asynccontextmanager
  async def lifespan(app: FastAPI):
      cfg = load_config()
      targets = cfg.prewarm_projects            # F-1 필드
      if targets:
          logger.info("[brain] 기동 선프라임 대상 %d개: %s", len(targets), targets)
          for project_path in targets:
              brain_session_registry.prewarm(project_path)   # 비블로킹 — 내부에서 daemon 스레드 기동
      else:
          logger.info("[brain] prewarm_projects 미지정 — 선프라임 생략")
      yield
      # shutdown: 인메모리 풀은 프로세스 종료와 함께 소멸(무상태 원칙) — 별도 정리 불요
  ```
- `[MUST]` lifespan 본문에서 프라임을 **블로킹 호출 금지** — `prewarm()`이 daemon 스레드로 분리하므로 lifespan은 즉시 `yield`한다(R2/H-6, 확정 방향 §3 "기동 지연 없음").
- `app = FastAPI(..., lifespan=lifespan)`로 연결(`main.py:33-37` 생성자 확장). uvicorn 기본 `lifespan="auto"`로 자동 실행(ANALYSIS §4 발견 4).

#### 3.3.3 환경 변경
해당 없음 (`console.sh` uvicorn 커맨드 무변경 — `--lifespan` 플래그 부재로 자동 적용).

#### 3.3.4 배치/마이그레이션
해당 없음.

#### 3.3.5 테스트 시나리오 (AC ↔ TS 매핑)
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-301 | F-3 AC | 통합 테스트 | `with TestClient(app):` 진입 시 `prewarm_projects`(mock) 각 프로젝트당 `prewarm` 1회 호출 |
| TS-302 | F-3 AC | 통합 테스트 | `prewarm_projects=[]`(mock)이면 `prewarm` 0회 호출, 기동 정상 완료 |
| TS-303 | H-6 | 통합 테스트 | lifespan 진입이 프라임 subprocess 완료를 기다리지 않고 즉시 반환(prewarm이 mock으로 non-blocking 확인) |

---

### F-004: 새 대화 웜 핸들 배정 + 콜드 폴백

#### 3.4.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `dashboard/backend/adapters/brain_session.py` | BE | `_get_or_create()`에 신규 세션 웜 주입 로직 연결 | `brain_session.py:486-501`, ANALYSIS §4 발견 2 |

#### 3.4.2 API·데이터 모델·화면 설계
- `_get_or_create()`를 확장하되 **레지스트리 락 해제 후** 웜 주입(무중첩 불변 유지, H-2):
  ```python
  def _get_or_create(self, session_id: str, project_path: str) -> ConversationBrainSession:
      with self._lock:
          is_new = session_id not in self._sessions
          if is_new:
              self._sessions[session_id] = ConversationBrainSession(
                  conversation_id=session_id, project_path=project_path,
                  max_turns=self.max_turns, idle_timeout_s=self.idle_timeout_s)
          session = self._sessions[session_id]
      # 락 밖: 신규 세션이면 풀에서 웜 핸들 체크아웃 후 이식 (없으면 콜드 폴백)
      if is_new:
          warm_sid = self.checkout_warm_handle(project_path)   # _pool_lock (레지스트리 락 미보유)
          if warm_sid is not None:
              session.adopt_warm_handle(warm_sid)              # 세션 _lock (레지스트리 락 미보유)
      return session
  ```
- 웜 주입 성공 시 세션 `state=ready`·`is_warm=True` → 첫 `ask()`가 `_warm_ask`(`--resume`) 경로를 탄다(F-4(a), `brain_session.py:267-273`).
- 풀 empty → `warm_sid is None` → 세션 `idle` 유지 → 첫 `ask()`가 콜드 경로(F-4(b) 회귀 없음).
- `routers/brain.py` 무변경 → 요청/응답 스키마 불변(F-4(c), ANALYSIS §4 발견 2).
- stale 핸들 방어(H-5): 이식된 웜 핸들의 `--resume`가 실패하면 기존 `_warm_ask`의 ⓓ 투명 재프라임(새 uuid4 콜드 1회)이 그대로 흡수한다(`brain_session.py:359-363`) — 추가 코드 불요.

#### 3.4.3 환경 변경
해당 없음.

#### 3.4.4 배치/마이그레이션
해당 없음.

#### 3.4.5 테스트 시나리오 (AC ↔ TS 매핑)
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-401 | F-4 AC(a) | 기능 테스트 | 풀에 핸들 존재 시 새 session_id의 `status().state == "ready"`(콜드 프라임 없이) |
| TS-402 | F-4 AC(a) | 기능 테스트 | 웜 주입 세션의 첫 `ask()`가 `--resume`(cold=False) 경로 호출(mock 인자 검증) |
| TS-403 | F-4 AC(a)/H-5 | 기능 테스트 | 이식 핸들 resume 실패(mock RuntimeError) → 투명 콜드 재프라임으로 answer 반환 |
| TS-404 | F-4 AC(b) | 회귀 테스트 | 풀 empty 시 새 session_id는 `idle` → 첫 ask가 콜드(cold=True) 경로 |
| TS-405 | F-4 AC(c) | 회귀 테스트 | `POST /api/brain/query`·`/prime`·`GET /status` 응답 스키마 기존과 동일(라우터 무변경) |

---

### F-005: 실기동 검증

#### 3.5.1 파일 변경 계획
코드 산출물 없음 (TEST 단계 L3 절차).

#### 3.5.2 실기동 검증 절차 (TEST 단계 참조용)
1. `~/.opal/console.config.json`의 `prewarm_projects`에 본 프로젝트 절대경로 지정 — 예: `["/Volumes/Data/AIStudio/workspace/ai-framework"]`.
2. `opal-cli console stop && opal-cli console start`로 데몬 재기동.
3. `/tmp/opal-console.log`에서 `[brain] 기동 선프라임 대상 ... ` + `[brain] prewarm 완료 project=... pool=1` 로그 확인(선프라임 완료).
4. 콘솔 브레인 UI에서 **새 대화**를 시작하고 첫 질의 전송.
5. 로그의 `[brain] ask WARM 경로` + `[brain] job 완료 ... elapsed=` 값이 웜 수준(콜드 ~56s 대비 유의미 단축)인지 관측 → F-5 AC 충족.
6. 대조군: `prewarm_projects=[]`로 재기동 시 선프라임 로그 0건, 첫 질의가 `ask COLD 경로`인지 확인(폴백 회귀 없음).

#### 3.5.5 테스트 시나리오 (AC ↔ TS 매핑)
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-501 | F-5 AC | 통합(실기동) | 지정 프로젝트 선프라임 로그 기록 + 새 대화 첫 질의 elapsed 웜 수준 |
| TS-502 | F-5 AC | 통합(실기동) | 미지정 시 선프라임 0회 + 콜드 폴백 정상 |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)
| Phase | 기능 | Step | agent | 실행 | 비고 |
|-------|------|------|-------|------|------|
| 1 | F-001, F-002 | 1, 2 | opal-be-agent | 순차(동일 에이전트) | config·풀 신설 — 독립 파일이나 BE 단일 워커 그룹핑 |
| 2 | F-004 | 3 | opal-be-agent | 순차 | `brain_session.py` 동일 파일 → Step 2 후 |
| 3 | F-003 | 4 | opal-be-agent | 순차 | F-001·F-002 API 필요 |
| 4 | F-001~F-004 | 5 | opal-be-agent | 순차 | 단위/통합 테스트 (전 기능 대상) |
| 5 | 문서 | 6 | PM 직접 | 순차 | ARCHITECTURE.md 동기화 |
| 6 | F-005 | 7 | opal-test-agent | 순차 | 실기동 L3 (TEST 단계) |

### 4.2 실행 체크리스트
> 총 7개 Step | Phase 6개 | 실행 모드: 복잡

#### Step 1: config에 prewarm_projects 필드 + 타입 가드 추가
- [ ] 완료
- **소속 기능**: F-001
- **영역**: BE
- **agent**: opal-be-agent
- **파일**: `dashboard/backend/config.py`
- **작업 내용**: `ConsoleConfig`에 `prewarm_projects: list[str] = field(default_factory=list)` 추가. `_coerce_str_list()` 타입 가드 헬퍼 추가. `load_config()` 반환에 `prewarm_projects=_coerce_str_list(data.get("prewarm_projects", []))` 연결. @header `exports`/`description` 갱신.
- **완료 기준**: 키 부재·빈 배열·비-list 값 모두 `[]`로 폴백하고 정상 배열은 str 원소만 로드된다. `python -c` import 무오류.
- **테스트**: TS-101, TS-102, TS-103
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 2: BrainSessionRegistry 프라임 풀 신설 + adopt_warm_handle
- [ ] 완료
- **소속 기능**: F-002
- **영역**: BE
- **agent**: opal-be-agent
- **파일**: `dashboard/backend/adapters/brain_session.py`
- **작업 내용**: 상수 `DEFAULT_POOL_SIZE`/`DEFAULT_MAX_CONCURRENT_PRIME`/`PREWARM_QUESTION` 추가. `BrainSessionRegistry.__init__`에 `pool_size`·`_pool_lock`·`_pool`·`_pool_inflight`·`_prime_semaphore` 추가. `prewarm()`·`_prime_into_pool()`·`checkout_warm_handle()` 메서드 신설(§3.2.2 시그니처·락 관용구 준수). `ConversationBrainSession.adopt_warm_handle()` 신설. @header 갱신(풀 설명·changelog).
- **완료 기준**: [MUST] subprocess는 어떤 락도 미보유 상태에서 호출(R1). `_pool_lock`이 `_lock`·세션 `_lock`과 역순 획득 없음(H-2). 세마포어로 동시 프라임 ≤ 2 강제(R3).
- **테스트**: TS-201, TS-202, TS-203, TS-204, TS-205, TS-206
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 3: _get_or_create 웜 핸들 주입 + 콜드 폴백 연결
- [ ] 완료
- **소속 기능**: F-004
- **영역**: BE
- **agent**: opal-be-agent
- **파일**: `dashboard/backend/adapters/brain_session.py`
- **작업 내용**: `_get_or_create()`를 §3.4.2 형태로 확장 — 레지스트리 락 해제 후 신규 세션에 한해 `checkout_warm_handle()` → `adopt_warm_handle()` 이식. 풀 empty 시 idle 유지(콜드 폴백). `routers/brain.py`는 무변경.
- **완료 기준**: 신규 세션은 풀 존재 시 콜드 없이 ready, 첫 ask가 `--resume`. 풀 empty 시 기존 콜드 동작 동일. 레지스트리 락 보유 중 세션 락 미획득(H-2).
- **테스트**: TS-401, TS-402, TS-403, TS-404, TS-405
- **실행 방법**: sub-agent
- **의존**: Step 2 (동일 파일·풀 API 필요)

#### Step 4: main.py lifespan 기동 선프라임 신설
- [ ] 완료
- **소속 기능**: F-003
- **영역**: BE
- **agent**: opal-be-agent
- **파일**: `dashboard/backend/main.py`
- **작업 내용**: `@asynccontextmanager lifespan()` 신설 — `load_config().prewarm_projects` 순회하며 `brain_session_registry.prewarm()` 호출(비블로킹), 미지정 시 생략 로그. `FastAPI(..., lifespan=lifespan)` 연결. @header 갱신(기동 훅·depends config/brain_session 추가).
- **완료 기준**: [MUST] lifespan 본문 프라임 블로킹 금지 — 즉시 yield(R2). `prewarm_projects` 각 프로젝트당 prewarm 1회, 빈 배열 시 0회.
- **테스트**: TS-301, TS-302, TS-303
- **실행 방법**: sub-agent
- **의존**: Step 1(config 필드), Step 2(registry.prewarm)

#### Step 5: 단위·통합 테스트 신설 + reset_brain_registry 픽스처 확장
- [ ] 완료
- **소속 기능**: F-001, F-002, F-003, F-004
- **영역**: BE
- **agent**: opal-be-agent
- **파일**: `dashboard/backend/tests/test_brain.py`
- **작업 내용**: config 테스트(TS-101~103), 풀 테스트 클래스 `TestBrainPrimePool`(TS-201~207), 웜 배정 테스트 `TestBrainWarmInjection`(TS-401~405), lifespan 테스트 `TestBrainLifespanPrewarm`(TS-301~303, `with TestClient(app) as client:` 패턴). `reset_brain_registry` autouse 픽스처를 확장하여 `_pool`·`_pool_inflight` 클리어(R5/H-7). @header exports/description 갱신. [MUST] 서브프로세스 전부 mock — 실 claude 호출 0회.
- **완료 기준**: `pytest dashboard/backend/tests/test_brain.py` 전체 GREEN + 기존 테스트 회귀 0. 동시성 테스트(TS-203/204/205) 안정 통과.
- **테스트**: TS-101~103, TS-201~207, TS-301~303, TS-401~405
- **실행 방법**: sub-agent
- **의존**: Step 1, 2, 3, 4

#### Step 6: docs/ARCHITECTURE.md §OPAL Console 동기화
- [ ] 완료
- **소속 기능**: 문서 (R6/H-8 대응)
- **영역**: 문서
- **agent**: PM 직접
- **파일**: `docs/ARCHITECTURE.md`
- **작업 내용**: §OPAL Console "세션" 행에 프라임 연결 풀(지정 프로젝트 선프라임·웜 핸들 배정·백그라운드 리필·동시 프라임 상한)과 `prewarm_projects` config 키를 반영. 엔드포인트/이력 행은 불변.
- **완료 기준**: 아키텍처 문서가 신설 풀 구조·config 키를 정확히 기술한다.
- **테스트**: TS-701 (문서 리뷰)
- **실행 방법**: direct
- **의존**: Step 1, 2, 3, 4 완료 후

#### Step 7: 실기동 검증 (선프라임→웜 배정)
- [ ] 완료
- **소속 기능**: F-005
- **영역**: 배치
- **agent**: opal-test-agent
- **파일**: (검증 절차 — §3.5.2)
- **작업 내용**: `prewarm_projects`에 본 프로젝트 지정 → 데몬 재기동 → `/tmp/opal-console.log` 선프라임 로그 확인 → 새 대화 첫 질의 elapsed 관측 → 대조군(빈 배열) 콜드 폴백 확인.
- **완료 기준**: 선프라임 완료 로그 기록 + 새 대화 첫 질의가 웜 수준(콜드 대비 유의미 단축) + 미지정 시 폴백 정상.
- **테스트**: TS-501, TS-502
- **실행 방법**: sub-agent (TEST 단계)
- **의존**: Step 5 완료(GREEN) 후

### 4.3 병렬/순차 판별 근거
| 관계 | 근거 |
|------|------|
| Step 2 → Step 3 | 동일 파일(`brain_session.py`) 순차 수정 — 파일 충돌 방지 |
| Step 1·Step 2 → Step 4 | lifespan이 config 필드·registry.prewarm API에 의존 |
| Step 1~4 → Step 5 | 테스트는 전 구현 완료 후 |
| Step 4 → Step 6 | 구조 확정 후 문서 동기화 |
| Step 5 → Step 7 | 단위 GREEN 후 실기동 |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA
| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | prewarm_projects 파싱·타입 가드 | TS-101, TS-102, TS-103 | 부재·빈·비-list→`[]`, 정상 배열 로드 |
| F-002 | 풀 적재·체크아웃·리필·동시성·상한 | TS-201~206 | 체크아웃 시 pop+리필, 중복 배정 0, 동시 프라임 ≤ 2, 무교착 |
| F-003 | lifespan 선프라임 비블로킹 | TS-301, TS-302, TS-303 | 지정 수만큼 prewarm, 빈 배열 0회, 기동 지연 없음 |
| F-004 | 웜 주입 ready·resume·콜드 폴백·계약 불변 | TS-401~405 | 풀 존재 시 ready+resume, empty 시 콜드, 스키마 불변 |
| F-005 | 실기동 선프라임→웜 배정 | TS-501, TS-502 | 선프라임 로그 + 웜 elapsed 단축 + 폴백 정상 |

### 5.2 회귀 테스트
- [ ] 기존 `test_brain.py` 15개 클래스 전체 GREEN (브레인 API 5종 계약 불변)
- [ ] `reset_brain_registry` 확장 후 기존 테스트 순서 무관 안정 통과
- [ ] `config.py` 필드 추가 후 소비처 6곳 회귀 없음(이름 기반 접근)

### 5.3 코드/문서 품질
- [ ] 수정 4파일(`config.py`·`brain_session.py`·`main.py`·`test_brain.py`) @header 갱신
- [ ] `docs/ARCHITECTURE.md §OPAL Console` 세션 행 동기화 (Step 6)
- [ ] 프로젝트 컨벤션 준수 (`docs/CONVENTIONS.md` @header·인용 규칙)

### 5.4 보안
- [ ] [MUST] API 키·anthropic SDK 미사용 — 풀 프라임도 구독 `claude -p`만 (`opbr_adapter.py:23`)
- [ ] 풀·세션 핸들 인메모리 한정 — DB·파일 영속 0 (`brain_session.py:6` 무상태 원칙)
- [ ] `~/.opal/` 배포 소스 직접 수정 없음 — `dashboard/` 프로젝트 소스만 변경
- [ ] 코드에 하드코딩 토큰/시크릿 없음

---

## 6. 복잡도 판별
| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 7개 | 복잡 |
| 변경 파일 수 | 4개 (config·brain_session·main·test_brain) | 복잡 |
| 모듈 범위 | 다중 (config·adapters·router·tests) | 복잡 |
| 작업 유형 | 신규 개발 (풀·lifespan 신설) | 복잡 |
| 외부 의존성 | 없음 (표준 라이브러리 threading만) | 단순 |
| **실행 모드** | **복잡** | |

---

## 7. 실행 아키텍처 (복잡 모드)

### C-1. 에이전트 토폴로지
- **Batch 1**: `opal-be-agent` — Step 1(config) → Step 2(풀) → Step 3(웜 주입) → Step 4(lifespan). 단일 에이전트 순차. 근거: Step 2·3이 동일 파일(`brain_session.py`)이라 파일 충돌 방지 위해 같은 에이전트에 그룹핑, Step 4가 Step 1·2 API에 의존.
- **Batch 2**: `opal-be-agent` — Step 5(테스트). Batch 1 완료 후.
- **Batch 3**: PM 직접 — Step 6(문서 동기화). Batch 1 완료 후(Batch 2와 병행 가능).
- **Batch 4**: `opal-test-agent` — Step 7(실기동). Batch 2 GREEN 후.

```
[BE: S1→S2→S3→S4] ──→ [BE: S5(test)] ──→ [test-agent: S7(실기동)]
        └──────────→ [PM: S6(docs)]
```

### C-2. 스킬 요구사항
- 기존 스킬로 충족 — 이번 태스크는 프로젝트 내부 Python/FastAPI 표준 패턴 확장(ANALYSIS §6.2). 신규 스킬 불요. EXECUTE는 op-dev-execute, TEST는 op-dev-test(BE 모드).

### C-3. 도구 요구사항
- CLI/패키지 신규 없음 — `threading`(표준), pytest(기존), `opal-cli console`(기동 검증). MCP: 필요 시 context7로 `lifespan`/`Semaphore` 재확인(ANALYSIS §6.3, 이미 §2.1에서 확인 완료).

### C-4. 테스트 전략
- **기능/동시성 테스트**: `pytest dashboard/backend/tests/test_brain.py -q` — 신규 `TestBrainPrimePool`·`TestBrainWarmInjection`·`TestBrainLifespanPrewarm` + config 테스트. 동시성 테스트는 `threading` + prime_and_ask mock으로 최대 동시 실행 카운트 측정(TS-203/204/205).
- **회귀 테스트**: 동일 명령으로 기존 15개 클래스 GREEN 확인.
- **코드 품질**: import 무오류(`python -c "import dashboard.backend.main"`), @header 갱신 확인.
- **보안**: `grep -ri "api_key\|anthropic\|--safe-mode\|--bare" dashboard/backend/adapters/` 신규 위반 0 확인.
- **실기동(L3)**: §3.5.2 절차 (opal-test-agent).

---

## 8. 기술 컨텍스트

### 8.1 기술 스택
| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| 언어 | Python 3.11+ | (프로젝트 표준) |
| 프레임워크 | FastAPI 0.137.1 (lifespan) | 해당 없음 (표준 패턴) |
| ASGI | uvicorn (`~/.opal/.venv`) | - |
| 동시성 | threading (Lock, Thread, Semaphore) | - |
| 테스트 | pytest + FastAPI TestClient | - |
| 외부 프로세스 | claude CLI (구독 `claude -p`) | - |

### 8.2 사용 MCP
| MCP | 조회 결과 요약 |
|-----|--------------|
| context7 (`/fastapi/fastapi`) | ANALYSIS §2.1에서 `@app.on_event` deprecated·`lifespan=` 권장 확인 완료 — PLAN 단계 추가 조회 불요 |

### 8.3 참조 문서 (설계 결정 근거)
| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | brain_session | `dashboard/backend/adapters/brain_session.py` | 풀 신설 대상·락 관용구·`_get_or_create`·무상태 원칙 |
| D-2 | 소스 | opbr_adapter | `dashboard/backend/adapters/opbr_adapter.py` | `prime_and_ask` 계약·[MUST] 구독 경로(미변경) |
| D-3 | 소스 | brain 라우터 | `dashboard/backend/routers/brain.py` | prime/query/status 진입점(무변경 확인) |
| D-4 | 소스 | config | `dashboard/backend/config.py` | `prewarm_projects` 추가 지점·타입 가드 |
| D-5 | 소스 | main | `dashboard/backend/main.py` | lifespan 신설 지점 |
| D-6 | 소스 | console scan 머지 | `opal/tools/opal-cli/lib/console.sh:196-235` | 신규 키 보존 근거(미변경) |
| D-7 | 소스 | test_brain | `dashboard/backend/tests/test_brain.py` | 픽스처·모킹 패턴·라우터 테스트 재사용 |
| D-8 | 설계 | ARCHITECTURE.md §OPAL Console | `docs/ARCHITECTURE.md` | Console BE 구조·세션 행 동기화 대상 |
| D-9 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | @header·인용·변경이력 규칙 |
| D-10 | 설계 | ANALYSIS | `tasks/060-260713-opd-브레인-프라임-연결풀/ANALYSIS.md` | 분석·리스크 R1~R6·핵심 발견 |
| D-11 | 외부 | FastAPI Lifespan Events | [FastAPI — Lifespan Events](https://fastapi.tiangolo.com/advanced/events/) | `@app.on_event` deprecated·`lifespan=` 권장 패턴 |

---

## 9. 리스크 및 대응 (기능-리스크 연결)
| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| R1/H-1 | 리필 스레드가 풀 락 보유 중 subprocess 호출 → 체크아웃 전면 블로킹 | F-002 | P0 | "락 하 pop → 락 해제 → subprocess → 락 재획득 append" 관용구 강제(§3.2.2), TS-205 |
| R1/H-2 | 레지스트리 락 보유 중 세션 락 획득 → 무중첩 불변 위반 교착 | F-002/F-004 | P0 | 웜 주입을 레지스트리 락 해제 후 수행(§3.4.2), 락 순서 계약 [MUST], TS-206 |
| R3/H-3 | 동시 프라임 상한 미강제 → 구독 사용량 급증 | F-002 | P1 | `threading.Semaphore(2)`로 강제, TS-203 |
| R4/H-4 | config 비-list 값 → 하위 순회 런타임 오류 | F-001 | P1 | `_coerce_str_list()` 타입 가드, TS-102 |
| H-5 | 오래된 웜 핸들 resume 실패 | F-004 | P1 | 기존 `_warm_ask` ⓓ 투명 재프라임이 흡수(추가 코드 불요), TS-403 |
| R2/H-6 | lifespan 블로킹 → 기동 지연 | F-003 | P1 | `prewarm()` daemon 스레드 분리, 즉시 yield, TS-303/501 |
| R5/H-7 | 테스트 픽스처 미확장 → 풀 상태 오염 | F-002/F-004 | P2 | `reset_brain_registry`에 `_pool`/`_pool_inflight` 클리어 추가, TS-207 |
| R6/H-8 | 아키텍처 문서 풀 개념 미반영 | 문서 | P2 | Step 6 ARCHITECTURE.md 동기화, TS-701 |

