# OPPB Runtime Tool — G2 API 동결 기록

> PLAN **D3**이 정의한 G2 완료조건의 산출물이다. 이 문서와 같은 디렉토리의 스키마 4종이
> **G3 착수의 유일한 입력 계약**이다. G3 진행 중 이 계약을 바꾸려면 구현을 먼저 고치지 말고
> W-11로 돌아와 아래 §재동결 절차를 수행한다(PLAN §Risks **H-3**).

## 1. 동결 좌표

| 항목 | 값 |
|---|---|
| 동결 시각 (UTC) | `2026-09-14T09:58:42Z` |
| 동결 기준 commit | `612db93d61ed72961002ca4cfd4431239d4d012e` (`612db93` — `feat(opal-agent): attempt 재부착·고아 판정 진입점과 시작 시점 record`) |
| 브랜치 / worktree | `.opal-worktrees/task_132` |
| 상류 main 대조 | `git log --oneline main ^HEAD` 결과 **0건** — main(`3aaca21`)은 HEAD에 전부 포함돼 있고 동결 시점에 앞서간 상류 커밋이 없다 |
| 동결 대상 구현 | `controller.py` · `supervisor.py` · `evidence.py` · `oppb_runtime_tool.py` (동결 시점 기준 아직 미커밋 — G2 체크포인트 커밋에 함께 들어간다) |

## 2. 파일별 sha256

| 파일 | sha256 | bytes |
|---|---|---|
| `oppb-state.schema.json` | `f4edbaba9f85b6f2d6ecca2541b904f071752b918799d77bedc14f89b167133d` | 17300 |
| `oppb-event.schema.json` | `8a78a0c70f04dcea7334d42a20005f9e3ab547a8a4787ecc4c621af91e66fd98` | 5321 |
| `oppb-command.schema.json` | `875a10785f3221992cbc9879f123fc404202cda381faafec6cfb3377fb91df4c` | 11362 |
| `oppb-evidence.schema.json` | `2bc84ff52e1860fd917204538bf2243ae2c4ac76f0316eb7f965cfe671a91c22` | 5135 |

재확인 명령 (W-18이 이 값의 무변경을 재확인한다):

```bash
cd <repo-root>/opal/tools/oppb-runtime-tool/schema
shasum -a 256 oppb-state.schema.json oppb-event.schema.json \
              oppb-command.schema.json oppb-evidence.schema.json
```

## 3. 동결 범위

| 스키마 | 동결하는 계약 |
|---|---|
| `oppb-state.schema.json` | `workgraph.json`(루트) + `acceptance.json` · `execution-packet.json` · `run.json` · `supervisor.json` · `attempt-spec.json` · `result.json`(`$defs`). 미니 태스크 상태 8종, dispatch 역할 3종, lease 4축, 예산 차감 축, revision lock 규율 |
| `oppb-event.schema.json` | `events.jsonl` 한 줄. 이벤트 이름 5종 폐쇄 집합과 이벤트별 필드 |
| `oppb-command.schema.json` | CLI 서브커맨드 7종 · 플래그 6종 · 서브커맨드 4종 · 오류 코드 52종 · 응답 봉투 · exit code 3종 · `workgraph load --spec` 입력 형식 |
| `oppb-evidence.schema.json` | `evidence/<scope>/<evidence_id>.json` 필수 필드·형식과 4단 거부 조건, `evidence submit`·`task accept` 응답 필드 |

**동결 범위 밖 — 의도적 제외**

- `attempts/<task>/<attempt>/attempt.attempt.json` (attempt record). 이 파일의 필드 집합은
  `opal-agent`의 `classify_attempt()` 입력 계약이고 소유자도 `opal-agent`다. OPPB Supervisor는
  같은 모양을 채워 넣을 뿐이므로 G2가 동결할 대상이 아니다.
- 내부 함수·클래스 시그니처. PLAN **H-6**에 따라 테스트도 스키마도 공개 CLI와 run root 파일
  계약 수준에서만 계약을 건다.

## 4. 이 스키마의 지위

- **문서이자 동결 대상이지 런타임 검증기가 아니다.** `oppb-runtime-tool`은 표준 라이브러리
  전용이고 `jsonschema`를 import하지 않는다. 실제 집행은 `evidence._validate_schema` 등
  구현 코드가 한다.
- 스키마는 **실측에서 뽑았다.** 아래 §5의 실행 결과가 근거이며, 현재 구현이 만들지 않는
  필드는 넣지 않았다. G3·G4가 추가할 필드를 미리 선언하지 않는다.
- 형식 준거는 `opal/tools/state-tool/schema/state.schema.json`(JSON Schema draft-07).

## 5. D3 완료조건 — 동결 시점 확인 결과

D3은 4항 전부 green일 때만 G2가 끝난 것으로 본다. 전부 이 문서 작성 시점에 재현했다.

| # | 조건 | 명령 | 결과 |
|---|---|---|---|
| 1 | 스키마 4종 존재 + sha256 고정 | 위 §2 | **충족** — 4파일 생성, sha256 기록 |
| 2 | `state.json`↔`workgraph.json` 상호 직접 쓰기 0 | `python3 -m pytest opal/tools/oppb-runtime-tool/tests/test_controller.py -q` | **5 passed** |
| 3 | 상한 포화 시 첫 slot을 Verifier에 배정 + 비정상 종료·재시작에서 재부착/수확 후 자동 tick 재개 | `python3 -m pytest opal/tools/oppb-runtime-tool/tests/test_supervisor.py -q` | **5 passed** |
| 4 | schema·code head·scope hash 불일치 evidence를 색인 전 거부 | `python3 -m pytest opal/tools/oppb-runtime-tool/tests/test_evidence.py -q` | **7 passed** |
| + | 진입 가드(run root·cache root 미추적 보장) | `python3 -m pytest opal/tools/oppb-runtime-tool/tests/test_oppb_init.py -q` | **18 passed** |
| + | **W-2 OPPL 회귀 — 기존 Pilot 무변경** | `python3 -m pytest opal/tools/opal-agent/tests/ opal/tools/state-tool/tests/ -q` | **546 passed, 3 skipped, 111 subtests passed** |

### 5.1 스키마 정합 검증

스키마가 구현·실산출물과 어긋나지 않음을 두 방향으로 확인했다.

1. **코드 대조** — 스키마의 폐쇄 집합을 구현 심볼에서 직접 읽어 비교했다. 전부 일치:
   `TASK_STATES`(8) · `ROLES`(3) · `LEASE_AXES`(4) · `COMMANDS`(7) · `DISPATCH` 키(7) ·
   `FLAGS`(6) · `ERROR_CODES`(52) · `evidence._REQUIRED_FIELD_TYPES`(8) ·
   `supervisor.append_event` 발행 이벤트 이름(5).
2. **실산출물 대조** — 격리된 임시 git 저장소에서 `init` → `workgraph load` → `start` →
   `evidence submit` → `task accept`를 실제로 완주시켜 나온 run root 산출물 전수를
   스키마로 검증했다. 4개 스키마 모두 draft-07 유효, 문서 **30건 전부 통과**
   (`workgraph.json` · `acceptance.json` · `run.json` · `supervisor.json` ·
   attempt 4건의 packet/spec/result 12개 · `events.jsonl` 11줄 · evidence 1건),
   명령 표면 8종 통과 + 음성 사례(필수 플래그 누락, 미지 명령) 거부 확인.

> 검증에 쓴 `jsonschema`는 OPAL `.venv`에 이미 있는 것을 **1회성 확인 용도로만** 썼다.
> 도구 런타임에 의존성을 추가하지 않았고 구현은 표준 라이브러리 전용 그대로다.

### 5.2 H-7 재실측 — `opal-agent` 공개 심볼

PLAN **H-7**이 W-11 시점에 요구한 재실측이다. 과거 실측치로 확정하지 않는다.

- `opal/tools/opal-agent/opal_agent.py` — **1935줄**, sha256
  `cedcfa5a0456784d935df615548ee609650586b95399da9a67467b45132753e7`
- `@header.exports` **17종**:
  `call_agent` · `resolve_session_event` · `analyze_stream` · `reconcile_attempts` ·
  `classify_attempt` · `load_attempt_record` · `AgentConfig` · `AgentResult` ·
  `StreamVerdict` · `PROVIDERS` · `EXIT_CLASSES` · `EPILOGUE_ALLOWLIST` ·
  `ATTEMPT_DISPOSITIONS` · `SUBCOMMANDS` · `OpalAgentError` · `ClaudeNotFoundError` ·
  `OpalAgentTimeout`
- **상류 변경 없음.** W-38 조사 중 관측된 1461줄 → 1935줄 이동은 이미 이 브랜치 HEAD에
  반영돼 있고, 동결 시점에 main이 앞서간 커밋은 0건이다.

## 6. 재동결 절차 (H-3 경로)

G3(W-12~W-17) 진행 중 이 API를 바꿔야 하는 상황이 오면 **G3에서 즉석으로 고치지 않는다.**

1. **중단** — 변경이 필요한 W를 중단하고 사유(어느 스키마의 어느 필드가, 왜 부족한지)를 기록한다.
2. **W-11 재진입** — PM에 W-11 재진입을 요청한다. 구현 변경이 선행하면 그 구현도 W-11 범위로 들어온다.
3. **실측 우선** — 스키마를 상상으로 고치지 않는다. 구현을 먼저 확정하고 §5.1의 두 방향
   대조(코드 심볼 · 실제 run 산출물)를 다시 통과시킨다.
4. **sha256 갱신** — 바뀐 스키마의 sha256을 §2 표에 갱신하고, §7 이력에 재동결 1행을 추가한다.
   동결 시각·기준 commit도 함께 갱신한다.
5. **D3 재확인** — §5의 테스트 4종 + W-2 OPPL 회귀를 다시 돌려 전부 green임을 기록한다.
6. **G3 재개** — 위가 끝난 뒤에만 중단했던 W를 재개한다. W-18은 **재동결 후의 sha256**을
   기준으로 무변경을 재확인한다.

구현이 스키마와 어긋난 경우의 기본 방향은 반대다 — **스키마를 실측에 맞춘다.** 구현이
틀렸다고 판단되면 임의로 고치지 말고 블로커로 올린다.

## 7. 동결 이력

| # | 시각 (UTC) | 기준 commit | 사유 |
|---|---|---|---|
| 1 | 2026-09-14T09:58:42Z | `612db93` | 최초 동결 — W-11 / PLAN D3 |
