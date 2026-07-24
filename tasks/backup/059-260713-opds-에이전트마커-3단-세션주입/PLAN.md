# PLAN: opal-agent 부트스트랩 마커 3-way 확장 + caller-supplied session id 지원

> 작성일: 2026-07-13 | 입력: TASK.md (ANALYSIS.md 없음 — PLAN 워커가 직접 코드 분석)
> 모드: Multi-Feature (F-001~F-003)

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

opal-agent 도구(`opal_agent.py`)의 `--opal-bootstrap`을 2-way(on|off)에서 3-way(on|assistant|off)로 확장하여 `[ASSISTANT]` 중간 tier(비서 tier 캡) 서브에이전트 호출을 지원하고, claude provider에 신규(cold) 세션의 caller-supplied session id 주입(`--session-id`)을 추가한다. 두 변경 모두 **어댑터 계층 내부**에서 흡수하며, on/off 기존 의미·기본값(on)·기존 호출 시그니처는 전부 불변(하위호환)이다. 브레인 소비자(`opbr_adapter.py`) 이관의 선행 갭을 한 번에 닫되, opbr_adapter 실제 이관은 후속 태스크로 분리한다.

### 1.2 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | 부트스트랩 마커 3-way 확장 ([ASSISTANT] 지원 + on/off 하위호환) | R-1, R-2 | P0 | 없음 |
| F-002 | caller-supplied cold session id 주입 (claude `--session-id`) | R-3 | P0 | 없음 |
| F-003 | 문서 갱신 (README + opal_agent.py 헤더 변경이력) | R-4 | P0 | F-001, F-002 |

> R-5(동작검증·실측)는 별도 기능이 아니라 TEST 단계 QA 활동으로 흡수한다 (§5.1 F-001 QA-3 / §TEST-SCENARIO S-9).

### 1.3 기능 의존 그래프 (ASCII)

```
F-001 (마커 3-way) ─┐
                     ├─ F-003 (문서 갱신)
F-002 (cold session)─┘
```

F-001·F-002는 동일 파일(`opal_agent.py`)의 독립 영역을 수정하므로 논리적으로 병렬 가능하나, 파일 충돌 방지를 위해 동일 워커가 순차 처리한다(§4.3).

---

## 리스크 가설 표

> PLAN 단계에서 작성. TEST-SCENARIO.md §1의 입력이 됨.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | `_mark()` 3-way (F-001) | on/off 기존 동작 회귀 — on=마커없음/off=`[WORKER]` 첫 줄 불변식 | P1 | L1(단위·조립 프롬프트 검증) 의무 | S-1, S-2 |
| H-2 | cold/warm 상호배타 (F-002) | `new_session_id`·`session_id` 동시 지정 시 claude에 `--session-id`·`--resume` 동시 전달 → CLI 충돌/미정의 | P1 | L1(단위·예외 발생 검증) 의무 | S-5 |
| H-3 | 미지원 provider 경고 (F-002) | gemini/codex/grok/cursor/antigravity에 `new_session_id` 지정 시 조용히 드롭 → 호출자(브레인) 세션 미생성 미인지 | P1 | L1(단위·stderr 경고 검증) 의무 | S-6 |
| H-4 | 마커 최외곽 불변식 (F-001) | cursor/antigravity의 system_prompt 접붙임 이후 `[ASSISTANT]`가 최외곽 첫 줄이 아니면 tier 캡 실패 → tier 오염 | P1 | L1(cursor/antigravity 조립 프롬프트 첫 줄) + L3(claude 실측) | S-3, S-9 |
| H-5 | `session_id` 필드 의미 오버로드 회피 (F-002) | 기존 `session_id`(resume)에 cold 의미를 덧씌우면 기존 호출자 회귀 | P1 | 설계로 제거(별도 파라미터 `new_session_id` 채택) → 잔여 낮음 | S-4 |

**가설 도출 근거**: H-1·H-4는 TASK 완료기준 ①③(마커 첫 줄 정확성·회귀 0)에서, H-2·H-3는 R-3 AC(상호배타·미지원 경고)에서, H-5는 R-2(하위호환)에서 도출.

---

## 2. 기능별 분석

### F-001: 부트스트랩 마커 3-way 확장

#### 2.1.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 도구 | `opal/tools/opal-agent/opal_agent.py` | `_mark()`·`AgentConfig.opal_bootstrap`·CLI `--opal-bootstrap` 정의 | 수정 |
| 에이전트(참조) | `opal/core/AGENT.md` | `[ASSISTANT 규칙]`·3단 스킵 사다리 의미 SSOT | 참조만(수정 금지) |
| 소비자(참조) | `dashboard/backend/adapters/opbr_adapter.py` | `[ASSISTANT]\n//opbr ...` 프롬프트 계약 레퍼런스 | 참조만(후속 이관) |

#### 2.1.2 현재 구현

- `AgentConfig.opal_bootstrap: str = "on"` — 주석 `"on" | "off"` (`opal_agent.py:91`).
- `_mark()`은 정적 헬퍼로 `opal_bootstrap == "off"`일 때만 `f"[WORKER]\n{prompt}"`를 반환하고, 그 외엔 프롬프트 그대로 반환한다 (`opal_agent.py:145-149`).
- `_mark()`은 **모든 어댑터**의 `build_invocation()`에서 호출된다: claude(`:161`), gemini(`:200`), codex(`:253,255`), grok(`:333`), cursor(`:382` — system_prompt 접붙임 **이후**), antigravity(`:431` — 접붙임 이후). 즉 "최외곽 첫 줄" 불변식이 이미 전 provider에 보장됨 (`opal_agent.py:382,431` 주석).
- CLI `--opal-bootstrap`은 `choices=("on", "off")`, `default="on"` (`opal_agent.py:611-614`).
- `[ASSISTANT]`의 의미 SSOT: 첫 줄 `[ASSISTANT]`이면 Phase A(비서 tier)만 로드, `.opal/AGENT.md`가 있어도 Phase B(PM tier) 승격 억제, `//` 커맨드는 정상 발동 (`opal/core/AGENT.md:9,13`).

#### 2.1.3 영향 범위

- **상위 의존(호출자)**: `call_agent(..., opal_bootstrap=...)`(`opal_agent.py:498,529`) → `main()`이 CLI 인자 전달(`:667`). 스킬/오케스트레이터가 run.sh로 CLI 호출. run.sh는 인자 passthrough라 무변경 (`run.sh:12` `exec ... "$@"`).
- **하위 의존(피호출자)**: 각 어댑터 `build_invocation()`이 `_mark()` 호출. dict/elif 어느 방식이든 반환 계약(str) 불변이므로 어댑터 코드 무변경.
- **공유 상태**: 없음(순수 함수).
- **관련 테스트**: 없음 — `opal/tools/opal-agent/`에 테스트 파일 부재(신규 필요).

### F-002: caller-supplied cold session id 주입

#### 2.2.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 도구 | `opal/tools/opal-agent/opal_agent.py` | `AgentConfig`·`ProviderAdapter`·`ClaudeAdapter`·`call_agent`·`_run`·CLI | 수정 |
| 소비자(참조) | `dashboard/backend/adapters/opbr_adapter.py` | cold=`--session-id`/warm=`--resume` 계약 레퍼런스 (`:112-113,144-150`) | 참조만 |

#### 2.2.2 현재 구현

- `AgentConfig.session_id: str | None = None` — 주석 "resume 이어가기" (`opal_agent.py:88`).
- `ClaudeAdapter.build_invocation`: `if config.session_id: cmd += ["--resume", config.session_id]` (`opal_agent.py:173-174`). **cold 세션 지정 수단 없음.**
- claude CLI 실측(`claude --help`): `--session-id <uuid>` "Use a specific session ID for the conversation (must be a valid UUID)" — 신규 세션에 caller-supplied id 지정. `-r, --resume [value]`는 기존 세션 재개. 두 플래그는 별개.
- 브레인 소비자 계약: cold=True → `--session-id <FE제공 id>`, cold=False → `--resume <id>`, session_id는 항상 호출자 제공 (`opbr_adapter.py:112-113,144-150`).
- `parse_result`은 이미 `data.get("session_id")`를 추출(`opal_agent.py:184`) — cold 프라임 시 claude JSON이 지정 id를 echo하므로 반환 계약 무변경.
- `ProviderAdapter`는 capability 플래그 패턴 보유: `supports_resume`·`supports_effort` (`opal_agent.py:123-124`). effort 미지원 경고는 `main()`에서만 수행(`:645-650`).

#### 2.2.3 영향 범위

- **상위 의존**: `call_agent` 시그니처에 `new_session_id` kwarg 추가(순수 additive, 기본값 None → 하위호환). `main()`이 CLI `--session-id` 전달.
- **하위 의존**: claude만 `--session-id` 조립. 나머지 어댑터는 `new_session_id`를 참조하지 않음(effort 미지원 provider와 동일 패턴 — 조립 시 무시).
- **공유 상태**: 없음. 상호배타/경고 검증은 `_run()` 단일 chokepoint에서 수행.
- **관련 테스트**: F-001과 동일 신규 테스트 파일에 흡수.

---

## 3. 기능별 설계

### F-001: 부트스트랩 마커 3-way 확장

#### 3.1.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/opal-agent/opal_agent.py` | 도구 | `AgentConfig.opal_bootstrap` 주석 3-way화 / `_mark()` assistant 분기 / CLI choices·help 확장 | (→ D-1:91,145-149,611) |

#### 3.1.2 API·데이터 모델·설계

**마커 매핑 상수 + `_mark()` 재작성** (`ProviderAdapter` 정적, `opal_agent.py:145-149` 대체):

```python
# 부트스트랩 스킵 사다리 ↔ 첫 줄 마커 1:1 대응 (core AGENT.md:9 3단 사다리)
_BOOTSTRAP_MARKERS = {"off": "[WORKER]", "assistant": "[ASSISTANT]"}

@staticmethod
def _mark(prompt: str, config: AgentConfig) -> str:
    marker = _BOOTSTRAP_MARKERS.get(config.opal_bootstrap)   # "on" → None
    return f"{marker}\n{prompt}" if marker else prompt
```

- dict 매핑을 채택한다 — elif 체인 대비 확장적이고, "on"은 매핑 부재(None)로 마커 없음을 자연 표현 (설계 결정, → D-1:145-149).
- `[MUST]` `opal/core/AGENT.md` §첫줄마커(:9): "`[WORKER]` → 전부 스킵 / `[ASSISTANT]` → 비서 tier만(Phase A) / (무마커) → 비서+PM(Phase A+B)". 3-way 값과 이 사다리를 1:1 대응시킨다 (→ D-3:9).
- 최외곽 첫 줄 불변식 유지: `_mark()`은 각 어댑터에서 system_prompt 접붙임(cursor `:381`/antigravity `:429`) **이후** 호출되므로 `[ASSISTANT]`가 최외곽 첫 줄이 됨 (→ D-1:382,431).

**`AgentConfig.opal_bootstrap`** (`opal_agent.py:91` 주석 갱신):

```python
opal_bootstrap: str = "on"   # "on"(풀 부트스트랩) | "assistant"([ASSISTANT] Phase A만) | "off"([WORKER] 전부 스킵)
```

**CLI `--opal-bootstrap`** (`opal_agent.py:611-614`):

```python
"--opal-bootstrap", choices=("on", "assistant", "off"), default="on",
help="서브에이전트 OPAL 부트스트랩 (기본 on). assistant=[ASSISTANT] 첫 줄(비서 tier·Phase A만) / off=[WORKER] 첫 줄(전부 스킵)",
```

- [MUST] `docs/CONVENTIONS.md` §플랫폼 분기 격리: "플랫폼별 차이는 어댑터 계층에서만 흡수한다." — `_mark()`은 `ProviderAdapter` 기반 정적 헬퍼로 공통 API 표면에 provider 하드코딩 없음 (→ D-5 §플랫폼 분기 격리).
- [MUST] `opal_agent.py:7`: "무의존성(Python 3.10+ 표준 라이브러리만)." — dict/f-string만 사용, 외부 패키지 없음.

#### 3.1.3 환경 변경
해당 없음.

#### 3.1.4 배치/마이그레이션
해당 없음. (배포는 `./scripts/install-mac.sh` 재배포 — TEST 단계, → D-5 §배포 경계)

#### 3.1.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | R-1 AC | 기능(단위) | `opal_bootstrap="assistant"`로 조립 시 claude 조립 프롬프트(`-p` 인자) 첫 줄이 정확히 `[ASSISTANT]` |
| TS-002 | R-2 AC | 회귀(단위) | on=마커 없음(프롬프트 불변)·off=`[WORKER]` 첫 줄 / CLI 기본값 on |
| TS-003 | R-1 AC | 기능(단위) | cursor·antigravity에서 system_prompt 접붙임 후에도 조립 프롬프트 첫 줄이 `[ASSISTANT]` (최외곽 불변식) |
| TS-004 | R-1 회귀 | 회귀(단위) | CLI `--opal-bootstrap assistant` 파싱 통과, `bad` 등 미허용 값은 argparse 거부 |

### F-002: caller-supplied cold session id 주입

#### 3.2.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/opal-agent/opal_agent.py` | 도구 | `AgentConfig.new_session_id` 필드 / `ProviderAdapter.supports_session_assign` / `ClaudeAdapter` cold·warm 분기 / `call_agent` kwarg / `_run` 상호배타·경고 / CLI `--session-id` | (→ D-1:88,123,173-174,498,534,611) |

#### 3.2.2 API·데이터 모델·설계

**설계 결정 M-3 — 별도 파라미터 `new_session_id` 채택** (오버로드 회피):

```python
# AgentConfig (opal_agent.py:88 아래에 추가)
session_id: str | None = None       # (기존 불변) warm resume — --resume
new_session_id: str | None = None   # cold 세션 지정(caller-supplied). claude만 지원(--session-id). session_id와 상호 배타
```

- `session_id`(resume) 의미를 그대로 두어 기존 호출자 회귀 0 (H-5 제거). cold는 신규 파라미터로 분리 — claude의 두 별개 플래그(`--session-id` vs `--resume`)와 1:1 대응 (설계 결정, → D-1:173-174).
- `[MUST]` claude CLI 실측(`claude --help`): "`--session-id <uuid>` Use a specific session ID for the conversation (must be a valid UUID)" — cold 세션에 caller-supplied id 지정 수단.

**capability 플래그** (`ProviderAdapter`, `opal_agent.py:123-124` 인접):

```python
supports_session_assign: bool = False   # cold --session-id(caller-supplied) 지원 여부
```

`ClaudeAdapter`만 `supports_session_assign = True` (`opal_agent.py:159` 인접). 나머지 어댑터는 기본 False.

**`ClaudeAdapter.build_invocation` 세션 분기** (`opal_agent.py:173-174` 대체):

```python
if config.new_session_id:
    cmd += ["--session-id", config.new_session_id]   # cold prime
elif config.session_id:
    cmd += ["--resume", config.session_id]            # warm resume
```

- 상호배타는 `_run()`에서 선검증되므로 elif는 방어적 이중화. (→ D-4:144-150 opbr cold/warm 계약과 정합)

**`_run()` 검증·경고** (`opal_agent.py:534` 진입부, adapter dispatch 이전):

```python
if config.new_session_id and config.session_id:
    raise OpalAgentError(
        "new_session_id(cold)와 session_id(warm resume)는 동시 지정할 수 없습니다."
    )
if config.new_session_id and not adapter.supports_session_assign:
    print(
        f"[opal-agent 경고] provider '{config.provider}'는 caller-supplied "
        f"session id(--session-id)를 지원하지 않아 무시됩니다.",
        file=sys.stderr,
    )
```

- **설계 결정 M-5 — 경고·상호배타를 `_run()`에 배치** (effort 경고는 `main()`에만 위치 `:645-650`). 근거: cold session 드롭은 correctness-critical(호출자 registry에 미생성 세션 id가 남아 브레인 재개 실패)이므로 라이브러리·CLI 양 표면을 모두 커버하는 단일 chokepoint(`_run`)에서 경고해야 한다. effort(품질 knob)와 성격이 달라 의도적 비대칭이며, §9 R-2에 트레이드오프 기재.
- [MUST] `docs/CONVENTIONS.md` §플랫폼 분기 격리: capability 플래그·경고는 어댑터 속성 기반이라 공통 API에 provider 하드코딩 없음 (→ D-5).

**`call_agent` 시그니처** (`opal_agent.py:485-499`): `new_session_id: str | None = None` kwarg 추가 → `AgentConfig(...)` 전달. 순수 additive.

**CLI `--session-id`** (`opal_agent.py:608` `--resume` 인접):

```python
# --resume(dest=session_id)와 상호배타 — argparse 그룹으로 CLI 레벨 방어
sess = parser.add_mutually_exclusive_group()
sess.add_argument("--resume", dest="session_id", help="이어갈 session_id (warm resume)")
sess.add_argument("--session-id", dest="new_session_id",
                  help="신규(cold) 세션에 지정할 caller-supplied session id (claude만, 유효 UUID)")
```

`main()`이 `call_agent(..., new_session_id=args.new_session_id)` 전달 (`opal_agent.py:655-668`).

- **설계 결정 M-6 — 이중 방어**: argparse mutually_exclusive_group(CLI UX)와 `_run()` 검증(라이브러리 호출자)을 병행. `_run` 검증이 상호배타 SSOT.

#### 3.2.3 환경 변경
해당 없음.

#### 3.2.4 배치/마이그레이션
해당 없음.

#### 3.2.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-005 | R-3 AC | 기능(단위) | claude에 `new_session_id="uuid-x"` 지정 시 조립 커맨드에 `--session-id uuid-x` 포함, `--resume` 부재 |
| TS-006 | R-3 회귀 | 회귀(단위) | claude에 `session_id="uuid-y"`(warm) 지정 시 `--resume uuid-y` 유지, `--session-id` 부재 |
| TS-007 | R-3 AC | 기능(단위) | `new_session_id`·`session_id` 동시 지정 시 `OpalAgentError` 발생(상호배타) |
| TS-008 | R-3 AC | 기능(단위) | 미지원 provider(예: gemini)에 `new_session_id` 지정 시 stderr 경고 출력 + 조립 커맨드에 `--session-id` 부재 |
| TS-009 | R-3 회귀 | 회귀(단위) | CLI `--resume`·`--session-id` 동시 전달 시 argparse가 거부(exit≠0) |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)

| Phase | 기능 | Step | agent | 실행 | 비고 |
|-------|------|------|-------|------|------|
| 1 | F-001, F-002 | 1 | opal-test-agent | 단독 | RED 테스트 선작성 (red-first §1) |
| 2 | F-001, F-002 | 2, 3 | opal-task-agent | 순차 | 동일 파일 `opal_agent.py` — 파일 충돌 방지 순차 |
| 3 | F-003 | 4 | opal-task-agent | 순차 | 구현 완료 후 문서 갱신 |
| 4 | R-5 검증 | 5 | opal-test-agent | 순차 | 재배포 + 실측 프로브 (TEST) |

### 4.2 실행 체크리스트

> 총 5개 Step | Phase 4개 | 실행 모드: 단순

#### Step 1: RED 테스트 작성 (마커 3-way + cold session)
- [ ] 완료
- **소속 기능**: F-001, F-002
- **영역**: 공통(테스트)
- **agent**: opal-test-agent (mode: red)
- **파일**: `opal/tools/opal-agent/tests/test_opal_agent.py` (신규)
- **작업 내용**: TEST-SCENARIO.md TS-001~TS-009를 표준 라이브러리 `unittest`로 작성. `ClaudeAdapter().build_invocation(config, "claude").cmd`·`_mark()` 조립 결과를 공개 관찰 출력으로 assert(subprocess 미실행). state-tool 테스트 컨벤션(@header + stdlib only) 준수. RED 시점 FAIL(exit≠0) 증거 기록.
- **완료 기준**: 테스트 실행 시 현행 코드에서 FAIL(assistant choices 미허용·`--session-id` 미조립) — RED 증거 확보
- **테스트**: TS-001~TS-009
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 2: 마커 3-way 확장 구현 (F-001)
- [ ] 완료
- **소속 기능**: F-001
- **영역**: 도구
- **agent**: opal-task-agent
- **파일**: `opal/tools/opal-agent/opal_agent.py`
- **작업 내용**: `_BOOTSTRAP_MARKERS` 상수 신설 + `_mark()` dict 기반 재작성(§3.1.2), `AgentConfig.opal_bootstrap` 주석 3-way화(:91), CLI `--opal-bootstrap` choices에 `assistant` 추가·help 갱신(:611-614). @header 규칙 적용(파일 상단 변경이력은 Step 4에서 통합).
- **완료 기준**: TS-001~TS-004 PASS. on/off 조립 결과 불변(회귀 0).
- **테스트**: TS-001, TS-002, TS-003, TS-004
- **실행 방법**: sub-agent
- **의존**: Step 1

#### Step 3: cold session id 주입 구현 (F-002)
- [ ] 완료
- **소속 기능**: F-002
- **영역**: 도구
- **agent**: opal-task-agent
- **파일**: `opal/tools/opal-agent/opal_agent.py`
- **작업 내용**: `AgentConfig.new_session_id` 필드(:88 인접), `ProviderAdapter.supports_session_assign`(:123) + `ClaudeAdapter.supports_session_assign=True`, `ClaudeAdapter` cold/warm 분기(:173-174 대체), `call_agent` kwarg(:485-531), `_run` 상호배타 예외+미지원 경고(:534 진입부), CLI `--session-id` mutually_exclusive_group(:608 인접), `main()` 전달(:655-668).
- **완료 기준**: TS-005~TS-009 PASS. 기존 warm resume(`--resume`) 동작 불변.
- **테스트**: TS-005, TS-006, TS-007, TS-008, TS-009
- **실행 방법**: sub-agent
- **의존**: Step 2 (동일 파일 순차)

#### Step 4: 문서 갱신 (F-003)
- [ ] 완료
- **소속 기능**: F-003
- **영역**: 문서(도구 로컬)
- **agent**: opal-task-agent
- **파일**: `opal/tools/opal-agent/README.md`, `opal/tools/opal-agent/opal_agent.py`(헤더 변경이력)
- **작업 내용**: (a) opal_agent.py 모듈 헤더 변경이력에 `v2.5 2026-07-13 HH:mm --opal-bootstrap 3-way(assistant) + caller-supplied cold --session-id (059)` 추가 + 모듈 docstring provider 표/caveat에 3-way·session-id 반영. (b) README: 플래그표(:139-149)에 `--opal-bootstrap` 값 `assistant` 반영 + `--session-id` 행 추가, provider별 매핑 표(:33)에 cold `--session-id` 주석, §OPAL 부트스트랩 스킵(:185-192)에 3단 사다리 설명, cold session 사용 예 추가, 변경이력에 v2.5 행.
- **완료 기준**: README에 `assistant` 값·`--session-id` 사용 예 존재, 양쪽 변경이력에 v2.5(KST 일시 + 059) 추가. `[MUST]` `docs/CONVENTIONS.md` §변경이력 작성 의무 준수.
- **테스트**: 산출물 검사(TS-010: 문서 정적 검증)
- **실행 방법**: sub-agent
- **의존**: Step 2, Step 3

#### Step 5: 재배포 + 실측 동작검증 (R-5)
- [ ] 완료
- **소속 기능**: F-001 (동작검증)
- **영역**: 공통(TEST)
- **agent**: opal-test-agent
- **파일**: (실행만 — `./scripts/install-mac.sh` 재배포 후 `~/.opal/tools/opal-agent/run.sh` 실측)
- **작업 내용**: `[MUST]` `docs/CONVENTIONS.md` §배포 경계 — 소스 수정 후 install 재배포. `run.sh --opal-bootstrap assistant --provider claude "부트스트랩 보고해줘"` 실측 프로브로 비서 tier 캡 증거(`⬜ harness ⬜ PM`) 확보(task 051 방식). 인증/환경 제약 시 DEFERRED + 대체 근거(조립 커맨드 검증) 기록.
- **완료 기준**: 실측 응답에 `⬜ harness ⬜ PM` 관측 또는 PM tier 미로드 확인. 불가 시 DEFERRED 처리(FAIL 아님).
- **테스트**: TS-011(S-9 실측)
- **실행 방법**: sub-agent
- **의존**: Step 4

### 4.3 병렬/순차 판별 근거

| 관계 | 근거 |
|------|------|
| Step 1 → Step 2 | RED-first: RED 실패 증거 후 GREEN 진입 (red-first.md §1) |
| Step 2 → Step 3 | 동일 파일 `opal_agent.py` 순차 수정 — 파일 충돌 방지(같은 워커) |
| Step 3 → Step 4 | 문서는 구현 확정 후 갱신 (헤더 변경이력·README 시그니처 반영) |
| Step 4 → Step 5 | 실측은 재배포 후 — 소스+문서 확정 산출물 기준 검증 |

> docs/ 갱신 Step 판단: 본 변경은 tool 로컬 문서(README·헤더)에 국한되며, TASK §범위가 `opal_agent.py`·README로 확정(→ TASK.md:35)되어 `docs/` 갱신 Step은 불요. 단, `docs/ARCHITECTURE.md`에 opal-agent provider/부트스트랩 3단 사다리 언급이 존재하면 후속 갱신을 PM이 검토(§보고 불일치 항목).

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA

| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | assistant 마커 최외곽 첫 줄 주입 | TS-001, TS-003 | 전 provider 조립 프롬프트 첫 줄 == `[ASSISTANT]` |
| F-001 | on/off 하위호환 회귀 0 | TS-002, TS-004 | on=불변·off=`[WORKER]`·기본값 on |
| F-001 | 실측 비서 tier 캡 | TS-011 | `⬜ harness ⬜ PM` 관측(또는 DEFERRED+대체근거) |
| F-002 | cold `--session-id` 조립 | TS-005 | 조립 커맨드에 `--session-id <id>` 포함 |
| F-002 | warm `--resume` 유지 + 상호배타 | TS-006, TS-007 | resume 불변 + 동시 지정 시 예외 |
| F-002 | 미지원 provider 경고 | TS-008, TS-009 | stderr 경고 + `--session-id` 미조립 / CLI 거부 |
| F-003 | 문서·변경이력 갱신 | TS-010 | README assistant/session-id + 양쪽 v2.5 변경이력 |

### 5.2 회귀 테스트
- [ ] on/off·warm resume 기존 동작 불변 (TS-002, TS-006)
- [ ] 기존 `call_agent`/CLI 호출 시그니처 무변경 통과 (additive kwarg만)
- [ ] 타 provider(gemini/codex/grok/cursor/antigravity) build_invocation 무영향

### 5.3 코드/문서 품질
- [ ] 무의존성 유지 — stdlib만 (→ D-1:7)
- [ ] @header/변경이력 규칙 준수 (→ D-5 §@header·§변경이력 작성 의무)
- [ ] 플랫폼 분기 어댑터 계층 격리 — 공통 API provider 하드코딩 없음 (→ D-5 §플랫폼 분기 격리)

### 5.4 보안
- [ ] session id는 shell=False subprocess 인자 배열로만 전달(인젝션 방지) — 기존 `_run` subprocess.run(list) 유지 (`opal_agent.py:552`)
- [ ] 하드코딩 시크릿/토큰 없음, session id는 caller 제공값 passthrough

---

## 6. 복잡도 판별

| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 5개 | 단순 |
| 변경 파일 수 | 3개 (opal_agent.py, README.md, tests/test_opal_agent.py) | 단순 |
| 모듈 범위 | 단일 모듈 (opal-agent) | 단순 |
| 작업 유형 | 개선 (기존 기능 확장) | 단순 |
| 외부 의존성 | 없음 (stdlib) | 단순 |
| **실행 모드** | **단순** | |

> 단순 모드 — §7 실행 아키텍처 생략. 실행 방법은 opds EXECUTE 디스패치 규약에 따라 sub-agent(전문 워커)로 위임.

---

## 8. 기술 컨텍스트

### 8.1 기술 스택

| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| 도구 | Python 3.10+ (stdlib only, 무의존) | (community-skills `trailofbits/modern-python` 미적용 — uv/ruff/외부패키지 금지 제약과 상충, stdlib 컨벤션 우선) |
| 테스트 | Python `unittest` (stdlib) + pytest 러너 | state-tool 테스트 컨벤션 |
| 배포 | Bash — install-mac.sh 재배포 | - |

### 8.2 사용 MCP

| MCP | 조회 결과 요약 |
|-----|--------------|
| (없음) | claude CLI 플래그는 `claude --help` 실측으로 확인(`--session-id <uuid>`·`--resume`·`--fork-session` 존재). context7 불요(내부 도구 계약). |

### 8.3 참조 문서 (설계 결정 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | opal_agent.py | `opal/tools/opal-agent/opal_agent.py` | 현행 2-way 마커(`:91,145-149,611`)·resume 전용 세션(`:173-174`)·call_agent/_run 구조 |
| D-2 | 소스 | opal-agent README | `opal/tools/opal-agent/README.md` | 플래그표(`:139-149`)·§부트스트랩 스킵(`:185-192`)·변경이력 갱신 대상 |
| D-3 | 설계 | core AGENT.md | `opal/core/AGENT.md` | `[ASSISTANT 규칙]`·3단 스킵 사다리 SSOT(`:9,13`)·완료보고 캡 표기(`:84`)·051 실측 방법 |
| D-4 | 소스 | opbr_adapter.py | `dashboard/backend/adapters/opbr_adapter.py` | 브레인 cold=`--session-id`/warm=`--resume` 계약(`:112-113,144-150`)·`[ASSISTANT]` 프롬프트(`:127-130`) |
| D-5 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | 배포 경계·변경이력 의무·@header·플랫폼 분기 격리 규칙 |
| D-6 | 외부 | claude CLI --help | (로컬 실측 `claude --help`) | `--session-id <uuid>`·`--resume`·`--fork-session` 플래그 실측 근거 |

---

## 9. 리스크 및 대응 (기능-리스크 연결)

| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| R-1 | on/off 회귀 (마커 불변식 훼손) | F-001 | P1 | dict 매핑 "on"→None로 마커 없음 보존 + TS-002 회귀 테스트 의무 (H-1) |
| R-2 | 경고 배치 비대칭 (session=_run vs effort=main) | F-002 | P2 | 의도적 — cold 드롭은 correctness-critical이라 라이브러리+CLI 양표면 커버(§3.2.2 M-5). 리뷰어 오인 방지 위해 코드 주석·본 표에 명기 |
| R-3 | cold+warm 동시 지정 오용 | F-002 | P1 | `_run` OpalAgentError(SSOT) + argparse 그룹 이중 방어 (H-2, TS-007/009) |
| R-4 | 미지원 provider 조용한 드롭 | F-002 | P1 | supports_session_assign 기반 stderr 경고 (H-3, TS-008) |
| R-5 | R-5 실측 인증/환경 제약으로 미검증 | F-001 | P2 | DEFERRED + 대체 근거(조립 커맨드 단위 검증) 허용 (task 057 선례) |
| R-6 | ARCHITECTURE.md 3단 사다리/provider 언급 미갱신 | F-003 | P2 | 범위 밖 — PM에 후속 갱신 검토 보고(불일치 항목) |
