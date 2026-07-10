# test-tool

> OPAL 테스트 단계별 도구 결정론적 집행기 — 4서브명령(resolve/check/unit/integration) + scenario-* 5서브명령(scenario-init/scenario-lock/scenario-mark/scenario-status/scenario-red)

## 개요

`test-tool`은 `test-tools.yaml`을 읽어 FE/BE×단계별 도구를 실행·판정하는 **얇은 래퍼**다.  
러너(pytest/vitest/cmux/eslint 등)를 재구현하지 않는다 — yaml 해석 → 명령 실행(subprocess) → JSON 증거 반환.

- **단계1 (단위/EXECUTE)**: `unit` 서브명령 — lint→typecheck→unit stop-on-fail
- **단계2 (통합/TEST)**: `integration` 서브명령 — cmux-tool 에러코드 소비 → playwright 폴백

> **[MUST] 루프 한도 비보유**: test-tool은 1회 실행·판정만 수행한다.  
> 재시도 루프는 오케스트레이터 책임이다. 한도 수치는 `opal-harness.md §1` 참조.

---

## 실행 경로

```bash
bash ~/.opal/tools/test-tool/run.sh <서브명령> [옵션]
# 또는 소스에서:
bash opal/tools/test-tool/run.sh <서브명령> [옵션]
```

**의존**: `.venv python` (OPAL 설치) + PyYAML + `cmux-tool` (E2E, PATH에 있어야 함)

---

## 서브명령

### `resolve`

`test-tools.yaml` resolution_order(project→global→추론)를 해석하여 tier×scope 도구셋 JSON 반환.

```bash
bash run.sh resolve [--stack py|ts] [--project-root PATH]
```

**출력 JSON**:
```json
{
  "ok": true,
  "command": "resolve",
  "tiers": {
    "unit": { "fe": {...}, "be": {...} },
    "integration": { "e2e": [...], "api_db": {...} }
  },
  "source": "project",
  "stack": { "language": "typescript", "framework": "nextjs", "runtime": "node" }
}
```

**exit code**: `0` / `yaml_parse_failed(2)` / `no_runner(3)`

---

### `check`

도구 설치 상태 게이트 검사 — `required` 미설치 시 차단.

```bash
bash run.sh check [--tier unit|integration] [--category CATEGORY] [--project-root PATH]
```

**출력 JSON**:
```json
{
  "ok": true,
  "command": "check",
  "results": [
    { "name": "eslint", "installed": true, "required": true },
    { "name": "jest-axe", "installed": false, "required": false }
  ],
  "blocked": false
}
```

**exit code**: `0` / `required_missing(4)`

---

### `unit`

lint → typecheck → unit 계층 stop-on-fail 단발 실행.

```bash
bash run.sh unit [--scope fe|be] [--changed-files FILE...] [--project-root PATH]
```

**출력 JSON**:
```json
{
  "ok": true,
  "command": "unit",
  "layers": [
    { "name": "lint",      "cmd": "eslint .",     "status": "pass", "stdout": "", "exit": 0 },
    { "name": "typecheck", "cmd": "tsc --noEmit", "status": "pass", "stdout": "", "exit": 0 },
    { "name": "unit",      "cmd": "vitest run",   "status": "pass", "stdout": "", "exit": 0 }
  ],
  "stopped_at": null
}
```

**[MUST] stop-on-fail**: lint 실패 시 typecheck/unit 미실행 + `stopped_at=lint` 기록.  
**[MUST] 단발 실행**: watch 플래그(`--watch`/`-w`) 사용 금지.

**exit code**: `0` / `layer_failed(5)`

---

### `integration`

cmux-tool 에러코드 소비 → playwright 폴백 결정 + E2E mode A 실행.

```bash
bash run.sh integration [--scope fe|be] [--url URL] [--project-root PATH]
```

**출력 JSON**:
```json
{
  "ok": true,
  "command": "integration",
  "e2e": {
    "driver": "cmux",
    "status": "pass",
    "url": "http://localhost:3000"
  },
  "api_db": { "status": "skip" },
  "escalate": false
}
```

**[MUST] mode A**: `--surface` 미전달 → 신규 surface 강제 (사용자 surface B/C 재사용 금지).  
**[MUST] SUT 경계**: 앱 가동 전제 검사만 — 기동 책임 비보유. `open_failed`/`wait_failed` 시 에스컬레이션.

**exit code**: `0` / `e2e_failed(6)` / `escalation(7)`

---

### `scenario-init`

`test-scenario.json` 생성 (spec존, `locked=false`) — 태스크별 테스트 시나리오 SSOT.

```bash
bash run.sh scenario-init --task-path <PATH> [--scenarios <JSON배열>]
```

**출력 JSON**:
```json
{ "ok": true, "command": "scenario-init", "task_id": "056-dryrun", "scenarios_count": 2 }
```

**출력 JSON (red_confirmed 시드 입력 시)**:
```json
{ "ok": true, "command": "scenario-init", "task_id": "056-dryrun", "scenarios_count": 1, "warning": "red_confirmed seed ignored (forced false): ['S1'] — RED 증거는 scenario-red로만 기록할 수 있다(056/ADD-1)" }
```

**[MUST] red_confirmed 시드 무력화(056/ADD-1)**: `--scenarios` 입력에 `red_confirmed: true`가 있어도 항상 `false`로 강제 생성한다 — RED 미관찰 상태를 init 시드로 우회 선언하는 경로를 봉쇄한다. 시드 시도가 있었으면 응답에 `warning` 필드를 추가한다(무시하되 침묵하지 않음). `red_confirmed`는 오직 `scenario-red`로만 true가 될 수 있다.

**exit code**: `0` / `scenario_spec_invalid_json(11)`

---

### `scenario-red`

`red_confirmed`를 **RED 증거와 함께 tool-gated로 갱신**한다 — RED 실관찰 없이 `red_confirmed`를 선언하는 우회 경로를 봉쇄한다(enforce-don't-advise 보강, `.opal/brain/pages/concept/oppl-scenario-red-confirmed-gap.md`).

```bash
bash run.sh scenario-red --task-path <PATH> --id <S-ID> --evidence <RED 실패 출력 요약>
```

**출력 JSON**:
```json
{ "ok": true, "command": "scenario-red", "scenario_id": "S1", "red_confirmed": true, "red_at": "2026-07-10T17:09:00+09:00" }
```

**[MUST] `--evidence` 필수**: 인자 미전달 시 argparse가 즉시 거부한다(증거 없는 red_confirmed 갱신 자체를 불가능하게 만든다).  
**[MUST] locked 이후 거부**: `locked==true`이면 `scenario_already_locked` 거부 — RED 확인은 항상 동결(`scenario-lock`) 이전에 완료되어야 한다.

**exit code**: `0` / `scenario_not_initialized(10)` / `scenario_already_locked(12)`

---

### `scenario-lock`

전 시나리오 `red_confirmed==true`일 때만 `locked=true` (RED-first 동결 게이트, self-confirming 방지).

```bash
bash run.sh scenario-lock --task-path <PATH>
```

**출력 JSON**:
```json
{ "ok": true, "command": "scenario-lock", "locked": true, "locked_at": "2026-07-10T16:36:00+09:00" }
```

**[MUST] RED-first 게이트**: 시나리오 중 하나라도 `red_confirmed==false`이면 거부한다 — 구현 전 실패 확인 없이 동결하면 self-confirming 테스트로 검증 게이트가 무력화된다.

**exit code**: `0` / `scenario_not_initialized(10)` / `red_not_confirmed(8)`

---

### `scenario-mark`

`locked==true` 이후에만 result존(`result`/`evidence`/`marked_at`) 기록을 허용한다.

```bash
bash run.sh scenario-mark --task-path <PATH> --id <S-ID> --result pass|fail [--evidence <문자열>]
```

**출력 JSON**:
```json
{ "ok": true, "command": "scenario-mark", "scenario_id": "S1", "result": "pass" }
```

**exit code**: `0` / `scenario_not_initialized(10)` / `scenario_not_locked(9)`

---

### `scenario-status`

spec/result 요약 — RED 확인 수·통과율.

```bash
bash run.sh scenario-status --task-path <PATH>
```

**출력 JSON**:
```json
{ "ok": true, "command": "scenario-status", "locked": true, "total": 2, "red_confirmed": 2, "passed": 1, "failed": 0 }
```

**exit code**: `0` / `scenario_not_initialized(10)`

---

## 에러 코드

| 코드 | exit | 원인 | 처리 |
|------|------|------|------|
| `venv_missing` | 1 | OPAL .venv 없음 | install-mac.sh 재실행 |
| `yaml_parse_failed` | 2 | test-tools.yaml YAML 문법 오류 | yaml 수정 후 재시도 |
| `no_runner` | 3 | yaml 없음 + 추론 불가 | test-tools.yaml 생성 |
| `required_missing` | 4 | required 도구 미설치 | 도구 설치 후 재시도 |
| `layer_failed` | 5 | unit 계층 stop-on-fail | 실패 계층 수정 후 재시도 |
| `e2e_failed` | 6 | E2E 실패 (폴백도 실패) | SUT 상태·네트워크 확인 |
| `escalation` | 7 | cmux 에스컬레이션 에러코드 (폴백 금지) | 에러코드별 원인 수정 |
| `red_not_confirmed` | 8 | scenario-lock 시 red_confirmed 미충족 시나리오 존재 | 구현 전 실패(RED) 확인 후 재시도 |
| `scenario_not_locked` | 9 | scenario-mark 호출 시점에 locked==false | scenario-lock 선행 후 재시도 |
| `scenario_not_initialized` | 10 | test-scenario.json 부재 | scenario-init 선행 |
| `scenario_spec_invalid_json` | 11 | scenario-init `--scenarios` JSON 파싱 실패 | JSON 문법 수정 후 재시도 |
| `scenario_already_locked` | 12 | scenario-red 호출 시점에 locked==true (동결 후 spec존 변경 시도) | 잠금 전에 scenario-red 호출 필요 |

> `scenario-*` 5서브명령 에러코드는 `lib/scenario.py`의 `SCENARIO_ERROR_CODES`(전용 SSOT)에서 관리하며, 위 5종은 기존 0~7 계열과 충돌 없이 8~12로 배정됐다(격리 원칙 — PLAN.md §3.2.2, 056/ADD-1).

### cmux-tool 에러코드 분류

**폴백 트리거 4종** (→ playwright 자동 전환):
- `not_in_cmux` — CMUX_SURFACE_ID 미설정
- `cmux_not_installed` — cmux 명령 없음
- `surface_parse_failed` — open 출력 파싱 실패
- `open_failed` — cmux browser open 실패

**에스컬레이션 5종** (→ 폴백 금지, exit 7):
- `usage` — 인자 오류
- `invalid_surface` — surface 핸들 형식 오류
- `goto_failed` — URL/navigate 오류
- `wait_failed` — 페이지 로드 타임아웃
- `eval_failed` — 명령 실행 실패

> SSOT: `cmux-tool/README.md §에러코드` 테이블.

---

## resolution_order

1. `{project}/.opal/test-tools.yaml` — 프로젝트별 오버라이드 (최우선)
2. `OPAL_TEST_TOOLS_GLOBAL` 환경변수 경로 — 글로벌 기본값
3. `package.json` / `pyproject.toml` 추론 — 내부 폴백

스키마 참조: `opal/core/references/test-tools-schema.yaml`  
템플릿 참조: `opal/templates/test-tools.yaml`

---

## 트리거 조건

| 단계 | 서브명령 | 수행 주체 |
|------|---------|---------|
| EXECUTE (단위) | `unit --scope fe|be` | 구현 워커 자가검증 |
| TEST (통합) | `integration --scope fe|be --url URL` | opal-test-agent |
| 단계 진입 전 | `check --tier unit|integration` | 워커/에이전트 |
| 도구셋 확인 | `resolve` | PM/오케스트레이터 |

---

## 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-06-23 | 초기 구현 — 4서브명령(resolve/check/unit/integration) + cmux-tool 에러코드 소비 어댑터 + stop-on-fail 러너 (T039 Step3 GREEN) |
| v1.1 | 2026-07-10 16:36 | scenario-* 4서브명령(scenario-init/scenario-lock/scenario-mark/scenario-status) 추가 — `lib/scenario.py`로 격리(기존 4서브명령 미간섭), test-scenario.json SSOT(spec존/result존), RED-first 동결 게이트(exit 8~11) (056) |
| v1.2 | 2026-07-10 | `scenario-red` 서브명령 신설 — red_confirmed를 RED 증거와 함께 tool-gated로 갱신(--evidence 필수, locked 후 거부 scenario_already_locked exit 12), enforce-don't-advise 보강. scenario-init의 red_confirmed 시드 입력은 항상 무시(false 강제)+응답 warning으로 변경 — RED 미관찰 우회 선언 경로 봉쇄 (056/ADD-1) |
