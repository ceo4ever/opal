# test-tool

> OPAL 테스트 단계별 도구 결정론적 집행기 — 4서브명령(resolve/check/unit/integration) + scenario-* 서브명령(scenario-init/scenario-lock/scenario-mark/scenario-status/scenario-red/scenario-fidelity-check/scenario-conformance/scenario-coverage-check/scenario-coverage-build)
> 소스: `opal/tools/test-tool/` | 배포: `~/.opal/tools/test-tool/`

## 개요

`test-tool`은 `test-tools.yaml`을 읽어 FE/BE×단계별 도구를 실행·판정하는 **얇은 래퍼**다.  
러너(pytest/vitest/cmux/eslint 등)를 재구현하지 않는다 — yaml 해석 → 명령 실행(subprocess) → JSON 증거 반환.

- **단계1 (단위/EXECUTE)**: `unit` 서브명령 — lint→typecheck→unit stop-on-fail
- **단계2 (통합/TEST)**: `integration` 서브명령 — E2E contract 상태·증적 판정 + API/DB 통합 증거 반환

> **[MUST] 루프 한도 비보유**: test-tool은 1회 실행·판정만 수행한다.  
> 재시도 루프는 오케스트레이터 책임이다. 한도 수치는 `opal-harness.md §1` 참조.

---

## 실행 경로

```bash
bash ~/.opal/tools/test-tool/run.sh <서브명령> [옵션]
# 또는 소스에서:
bash opal/tools/test-tool/run.sh <서브명령> [옵션]
```

**의존**: `.venv python` (OPAL 설치) + PyYAML. E2E executor는 `test-tools.yaml`와 E2E contract의 profile/executor 선언을 따른다. 브라우저 후보 기본 순서는 agent-browser(orca-managed) → cmux(owned-surface) → agent-browser(standalone) → Ego Lite → Playwright(opt-in)다.

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
  "source_path": "/abs/path/to/project/.opal/test-tools.yaml",
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

lint → typecheck → unit → a11y 계층 stop-on-fail 단발 실행. 도구 항목의 `check`(설치 확인)와 `run`/`run_files`(실제 검사)를 분리 실행한다.

```bash
bash run.sh unit [--scope fe|be] [--changed-files FILE...] [--project-root PATH]
```

**도구 항목 필드 의미(D-1)**:

| 필드 | 의미 |
|---|---|
| `check` | 설치 확인 명령. exit 0이면 설치된 것으로 본다. **검사 명령이 아니다** — `run` 대체 실행에 쓰지 않는다. |
| `install` | 설치 안내 명령(문서용, 자동 실행 없음). |
| `run` | 실제 검사 명령. 프로젝트 전체 범위로 실행한다. |
| `run_files` (선택) | `{files}` 자리표시자를 가진 파일 단위 검사 명령. |
| `file_globs` (선택) | `run_files`에 넘길 파일을 고르는 glob 목록. 생략 시 프로젝트 안에 실재하는 요청 파일을 모두 넘긴다. 파일 단위 실행은 `run_files`가 없을 때 지원하지 않는다. |
| `required` (기본 true) | 이 계층 결과가 전체 `incomplete` 판정에 영향을 준다. |

**실행 순서(D-2)**: 계층마다 첫 번째 도구만 쓴다.

1. `run`도 `run_files`도 없으면 아무 명령도 실행하지 않는다 → 계층 `not_configured`/`run_missing`.
2. `check`가 있으면 먼저 실행한다. 실패(exit≠0)하면 `run`은 실행하지 않는다 → 계층 `tool_unavailable`/`install_check_failed`.
3. `run`(또는 파일 범위가 있으면 `run_files`)을 실행한다. exit 0이면 `pass`, 아니면 `fail`.

**검사 범위(D-3)**: `--changed-files`가 있으면 요청 파일을 `requested_files`에 기록한다. 도구에 `run_files`가 있으면 프로젝트 안에 실재하고 `file_globs`에 맞는 파일만 그 도구에 넘긴다. 매칭 파일이 0개면 명령을 실행하지 않고 계층 `not_applicable`/`no_matching_files`. `run_files`가 없는 도구는 `run`을 프로젝트 전체로 실행하고 계층 `scope.reason`을 `file_scope_unsupported`로 남긴다(C-5 — 파일 단위를 지원하지 않는 도구에 인자를 붙이지 않는다). `--changed-files`가 없거나 비면 전체 도구가 프로젝트 전체 범위로 실행된다.

계층 `scope` 형태: `{kind: "files"|"project", requested: [...], checked: [...], excluded: [{path, reason}], reason}`. `excluded[].reason` ∈ `missing`(파일 부재) · `outside_project`(프로젝트 밖) · `pattern_mismatch`(glob 불일치).

**계층 상태값(D-4, 폐쇄 목록)**: `pass` · `fail` · `tool_unavailable` · `not_configured` · `not_applicable` · `not_run`. 한 필수 계층이 `fail`이면 이후 계층은 실행하지 않고 `not_run`/`stopped_after_failure`로 응답에 남긴다(cmd는 `null`).

**전체 상태값(D-4)**: `pass` · `fail` · `incomplete`.

- `fail`: 필수 계층에 `fail`이 있다. `error: "layer_failed"`.
- `incomplete`: 필수 계층에 `tool_unavailable`·`not_configured`가 있거나(`reason: "required_layer_unverified"`), 실행된 계층이 없거나(`reason: "no_layers_declared"`), 통과(`pass`) 계층이 0개다(`reason: "no_check_executed"`). `error: "unit_incomplete"`.
- `pass`: 그 외. `ok`는 `status == "pass"`일 때만 `true`.

**필수 여부(D-5)**: `required: false`인 계층의 `tool_unavailable`·`not_configured`는 전체를 `incomplete`로 만들지 않고 계층 상태로만 남는다. `required` 키가 없으면 필수로 본다.

**exit·오류 코드(D-6)**: `pass` → exit `0`. `fail` → exit `5`, `error: "layer_failed"`. `incomplete` → exit `21`, `error: "unit_incomplete"`. 설정 해석 실패(resolve 단계)는 기존대로 exit `1`.

**응답 예시(D-7)**:
```json
{
  "ok": true,
  "status": "pass",
  "layers": [
    {
      "name": "lint",
      "tool": "ruff",
      "required": true,
      "status": "pass",
      "check": { "cmd": "ruff --version", "exit": 0, "status": "pass" },
      "cmd": "ruff check .",
      "exit": 0,
      "stdout": "All checks passed!",
      "scope": { "kind": "project", "requested": [], "checked": [], "excluded": [], "reason": null }
    },
    {
      "name": "typecheck",
      "tool": "mypy",
      "required": true,
      "status": "pass",
      "check": { "cmd": "mypy --version", "exit": 0, "status": "pass" },
      "cmd": "mypy .",
      "exit": 0,
      "stdout": "Success: no issues found in 2 source files",
      "scope": { "kind": "project", "requested": [], "checked": [], "excluded": [], "reason": null }
    },
    {
      "name": "unit",
      "tool": "pytest",
      "required": true,
      "status": "pass",
      "check": { "cmd": "pytest --version", "exit": 0, "status": "pass" },
      "cmd": "pytest",
      "exit": 0,
      "stdout": "1 passed",
      "scope": { "kind": "project", "requested": [], "checked": [], "excluded": [], "reason": null }
    }
  ],
  "stopped_at": null,
  "requested_files": [],
  "command": "unit",
  "scope": "be",
  "cwd": "/abs/path/to/project",
  "config": { "source": "project", "path": "/abs/path/to/project/.opal/test-tools.yaml" }
}
```

계층 필드: `name`(계층명) · `tool`(도구 이름) · `required` · `status` · `reason`(비통과 시) · `check`(`{cmd, exit, status}`, 실행 시에만) · `cmd`(실제 실행한 run 명령, 미실행이면 `null`) · `exit` · `stdout` · `scope`. 최상위 필드: `status` · `reason`(비통과 시) · `scope`(요청 범위 `fe`/`be`) · `cwd`(절대경로) · `config: {source, path}` · `requested_files` · `layers` · `stopped_at`.

**구형 설정 이관(D-9)**: `check`에 실제 검사 명령을 넣은 구형 설정은 `run`이 없으므로 `not_configured`/`run_missing`(exit 21)이 된다. `check`를 임의로 `run`에 복사하지 않는다(C-2) — 사용자가 명시적으로 편집해야 한다.

이관 전:
```yaml
lint:
  - name: eslint
    check: "npx eslint ."
    required: true
```

이관 후:
```yaml
lint:
  - name: eslint
    check: "npx eslint --version"   # 설치 확인
    run: "npx eslint ."             # 실제 검사
    run_files: "npx eslint {files}" # 선택 — 파일 단위 실행
    file_globs: ["*.js", "*.jsx", "*.ts", "*.tsx", "*.mjs", "*.cjs"]
    required: true
```

---

### `integration`

E2E contract v2 결과를 반환한다. profile은 요구사항의 공개 표면으로 결정되며, 도구 가용성으로 UI 행동을 API-only 실행으로 낮추지 않는다.

`integration`과 `scenario-mark --verdict-json`은 profile `browser` / `api` / `hybrid` / `collaborative` / `manual` 5종을 보존한다(SSOT: `lib/e2e_contract.py`의 `PROFILES`).

```bash
bash run.sh integration [--scope fe|be] [--url URL] [--expect-text TEXT] \
  [--ego-install-choice manual|r2|cancel] [--project-root PATH]
```

**출력 JSON**:
```json
{
  "ok": false,
  "command": "integration",
  "status": "fail",
  "error": "e2e_failed",
  "e2e": {
    "driver": "ego-lite",
    "status": "fail",
    "url": "http://localhost:3000"
  },
  "api_db": { "status": "skip" },
  "contract_version": "2.0"
}
```

**[MUST] mode A**: `--surface` 미전달 → 신규 surface 강제 (사용자 surface B/C 재사용 금지).  
**[MUST] SUT 경계**: 앱 가동 전제 검사만 — 기동 책임 비보유.
**[MUST] pass gate**: `pass`와 `real-usage`는 구조화 assertion `expected`/`actual`과 profile 또는 시나리오의 `required_evidence`/`observed_evidence`를 모두 요구한다. open/navigate/close 또는 자유 형식 사람 완료 선언만으로 통과하지 않는다.

설정의 `priority` 순서로 Ego Lite, cmux, Playwright를 실제 호출한다. 다음 후보 전환은 현재 후보가 `provider_unavailable`일 때만 허용된다. Ego Lite 미설치는 자동으로 건너뛰지 않고 `awaiting_human`과 `manual`·`r2`·`cancel`, URL/assertion resume 정보를 반환한다. 사용자가 `cancel`을 명시한 경우에만 Ego 후보가 `provider_unavailable`이 되어 cmux로 이어진다.

| status | exit | 의미 |
|---|---:|---|
| `pass` | 0 | 모든 assertion과 증적 조건 통과 |
| `fail` | 6 | 제품 동작 또는 assertion 실패 |
| `infra_error` | 7 | 서버·포트·driver·증적 저장 등 인프라 오류 |
| `executor_unavailable` | 18 | 필수 executor 또는 모든 허용 후보 부재 |
| `blocked` | 19 | 인증·외부 승인 등 자동 진행 불가 |
| `awaiting_human` | 20 | operational state: 사람 handoff 대기, 같은 run으로 재개 |

`provider_unavailable`은 Browser 후보 내부 상태이며 process exit으로 직접 노출하지 않는다. 후보 소진 시 final `executor_unavailable`이 된다.

---

### `e2e run` (127)

```
test-tool e2e run --scenario <id> --task-path <path> --target <source-main|source-worktree|installed>
                  [--worktree-root <path>] [--opal-home <path>]
                  [--artifact-root <path>] [--run-id <id>]
```

대상 소스 트리를 해석하고 포트를 임대해 SUT를 기동한 뒤 health 통과를 확인하고 시나리오를
실행한다. `--scenario`·`--task-path`·`--target` 3개는 필수다. exit은 `status_to_exit(status)`
결과이며 값은 `{0,6,7,18,19,20}`을 벗어나지 않는다.

SUT 기동은 대상 트리의 `.opal/e2e/environment.json` 설정을 그대로 따른다. 설정에 선언된
서비스를 의존 순서로 1회씩 기동하고(`{host}`·`{port}`·`{python}`·`{project_root}`·
`{service.<id>.url}`·`{service.<id>.port}` 치환, 리터럴 중괄호는 `{{`·`}}`), 선언된 health를
수행하며 health가 없으면 포트 대기로 대체한다. `run.json.urls`의 키는 서비스 id이고, api
표면의 base URL·health_path가 api executor에 전달된다. 설정이 없거나 무효하거나 표면
해석에 실패하면 하네스가 임의로 기동을 시도하지 않고 `blocked`(run.json의 `detail_code`가
`e2e_env_config_missing`/`e2e_env_config_invalid`/`e2e_env_surface_missing`/
`e2e_env_surface_ambiguous`)로 안내한다.

`--task-path/test-scenario.json`에 같은 id가 없으면 `<project>/docs/e2e/journeys/<id>.md`를
직접 읽는다. 여정의 `{fragment: <id>, with: {...}}` step은 `docs/e2e/fragments/<id>.md`의
실제 연산과 필수 사후 조건으로 전개된다. 조각의 `fill`·`type` 값은 `value_ref`가 가리키는
환경 변수에서 실행 직전에 읽으며, 조각 문서에 원문 값을 둘 수 없다. 전개 연산은 축약된
조각 호출 한 행이 아니라 실제 연산별 `actions.jsonl` 행으로 남는다.

- 대상 3종: `source-main`(허브 체크아웃) · `source-worktree`(작업본, `--worktree-root`) ·
  `installed`(`--opal-home`. install을 호출하지 않으며 사용자 실제 `~/.opal`과 같은 경로면 거부)
- 산출물 기본값은 프로젝트의 `.e2e/artifacts/`이며 최근 20개 run만 보존한다. `.e2e/`는
  저장소 전체 무시 경계라 `git status`를 오염시키지 않는다. `OPAL_E2E_ARTIFACT_DIR` 또는
  `OPAL_E2E_ARTIFACT_ROOT`로 격리 경로를 명시할 수 있다.
- 사용자 Console 포트(7823)는 임대 풀에서 제외된다

프로젝트 여정 실행이 `pass`하면 `.e2e/freshness.json`에 여정 해시, 참조 조각 해시 집합,
`surface_id`, 대상 commit, 선택 driver의 `driver`+`session_mode`, 실제 달성 충실도를
기록한다. 다음 실행은 이 값이 일치하고 기존 `run.json`이 여전히 완전한 `pass` 증적이며
달성 충실도가 현재 요구치 이상일 때만 실행을 생략한다. `.opal/e2e/order.json` 변경으로
선택 driver가 달라지면 이전 증적은 재사용되지 않는다. 생략은 새 `pass`를 만들지 않고
원장의 `events[]`에 `kind: evidence_reuse`, `description: 이전 증적 재인용`, 기존 run과
증적 경로를 기록한다. 따라서 후속 status/DONE 소비자는 생략을 미실행으로 숨기지 않는다.

### `e2e env-inspect` / `e2e env-validate` / `e2e env-check`

```
test-tool e2e env-inspect --project-root <path>
test-tool e2e env-validate --project-root <path> [--file <path>]
test-tool e2e env-check --project-root <path> [--artifact-root <path>]
```

프로젝트 E2E 환경 설정(`.opal/e2e/environment.json`)을 검토·검증·준비 판정하는 3개
서브명령이다. `opal-e2e` 스킬의 `setup` 모드가 이 순서로 호출한다.

- `env-inspect`: 프로젝트를 제한된 깊이로 읽기 전용으로 훑어 `config`(설정 존재·유효성
  요약), `surface_candidates`(web/api/desktop 후보), `drivers`(설치된 browser driver),
  `secret_hints`(`.env.example` 변수 이름)를 반환한다. 쓰기 연산과 바이트코드 캐시를 남기지
  않는다. exit `0` 고정.
- `env-validate`: `--file`(초안) 또는 `.opal/e2e/environment.json`을 `lib/e2e/environment.py`
  스키마로 검증한다. 유효하면 exit `0`과 `summary`(services/surfaces 개수), 부재·무효면
  exit `1`과 `error`(`e2e_env_config_missing`/`e2e_env_config_invalid`) + `violations`.
- `env-check`: 설정의 표면별 준비 상태를 실제 서비스 기동·health·executor 확인으로
  판정한다. 최상위 `ready`(bool)와 `secrets`, 표면별 `surfaces[{id, kind, status, checks,
  cause, remediation}]`를 반환한다. `status`는 `ready`/`not_ready`이고 `checks`는
  `service_start`/`health`/`executor` 등 개별 확인 이름이다. 모든 표면이 준비되면
  `ready: true`와 exit `0`, 아니면 exit `1`이다. 이 판정은 test-tool만 소유하며, 호출한
  스킬은 결과를 재계산하지 않고 그대로 보고한다.

3개 서브명령 모두 소스 경로(`~/.opal/.venv/bin/python opal/tools/test-tool/test_tool.py`)
검증으로 끝낸다. `~/.opal/`(설치본) 재배포는 이 작업의 범위가 아니며 main merge 뒤
사용자 승인을 받은 `./scripts/install-mac.sh` 실행으로만 이뤄진다. 병합 전에 설치본을
먼저 바꾸면 설정 파일이 없는 다른 main 체크아웃의 E2E가 `blocked`로 바뀌어 다른 세션에
영향을 줄 수 있다.

### `e2e resume` (127)

```
test-tool e2e resume --run-id <id> --token <resume-token> --submission <path> [--artifact-root <path>]
```

`awaiting_human`(exit 20)으로 정지한 run을 사람 제출로 재개한다. **사람 제출만으로는 `pass`가
되지 않으며** 재개 후 `validate_pass_requirements`를 다시 통과해야 최종 판정이 난다.

### `e2e status` / `e2e clean` (127)

`status`는 지정 run의 상태·증적 경로·소유 자원을 반환한다. `clean`은 `owned.json` 대장에
등재된 자원만 회수하고 `user_owned=true`는 `skipped[]`로 제외한다. 패턴 매칭
(`pkill`·`pgrep`·`killall`)을 쓰지 않으며 `$OPAL_HOME/run/console.pid`를 보지 않는다.

> 드라이버 후보 순서·충실도 등급·증적 계약의 원문은 이 도구가 소유한다. 파이프라인 문서는
> 정의를 복제하지 않고 참조한다.

### `e2e driver-verify`

```bash
test-tool e2e driver-verify --driver <name>
```

등록된 browser driver의 계약 8연산(`probe/open/snapshot/act/wait/assert/capture/close`)을
순서대로 실제 dispatch하고 최소 출력 형태를 검사한다. 일부 연산만 구현한 driver와
바이너리가 없어 `provider_unavailable`인 driver는 통과하지 않는다(exit `1`). 모든 등록
variant가 8연산을 실제 수행한 경우에만 `ok=true`, `outcome=pass`로 종료한다(exit `0`).

`e2e run`도 시나리오의 browser step이 요구하는 연산을 실행 전에 추출한다. 해당 연산을
구현하지 않은 후보는 `excluded_by=capability_missing`과 `missing_operations:...` 사유로
제외되므로, 실행 중 `driver_operation_unimplemented`로 처음 실패하지 않는다.

프로젝트 전용 브라우저는 Python 모듈 대신 `.opal/e2e/drivers/*.json` 한 장으로 등록할 수
있다. 매니페스트는 `driver`, `session_mode`, binary 탐색 규칙과 계약 8연산의 `argv`(또는
`act.map`)를 선언한다. 8연산 중 하나라도 빠지면 등록 자체가 거부되며, 실제 사용 전 위
`driver-verify`가 live command 출력까지 통과하는지 확인한다. 각 command의 마지막 stdout
줄은 §B.2 최소 출력 형태의 JSON 객체여야 한다. 특수 프로토콜은 기존 Python driver로
유지할 수 있다.

후보 순서는 프로젝트의 `.opal/e2e/order.json`에 `candidate_order` 배열로 재정의한다.
각 원소는 `driver`, `session_mode`, `opt_in`을 가지며 이 배열은 그대로
`resolve_candidates(candidate_order=...)`에 전달된다. 파일이 없을 때만 C-DRV-3 기본값을
사용하고, 잘못된 파일을 조용히 기본값으로 대체하지 않는다.

### `e2e promote-check`

```bash
test-tool e2e promote-check --journey <id> \
  (--run-id <id> | --artifact-dir <path> | --run-json <path>) [--artifact-root <path>]
```

태스크 초안을 `docs/e2e/`로 승격할 자격만 읽기 전용으로 판정한다. 같은 journey id의
`run.json`이 `status=pass`, pass exit, `executed=true`, `evidence_complete=true`,
`missing_evidence=[]`를 모두 만족해야 `eligible=true`와 exit `0`을 반환한다. 그 밖에는
`eligible=false`와 exit `1`이다. 이 명령은 파일을 복사하지 않고, 호출자 산문이나 별도
합격 플래그를 입력으로 받지 않는다.

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

v2 시나리오 계약(profile/executor/status/schema) 검증에 실패하면 `scenario_contract_invalid(17)`로 거부한다.

**[MUST] red_confirmed 시드 무력화(056/ADD-1)**: `--scenarios` 입력에 `red_confirmed: true`가 있어도 항상 `false`로 강제 생성한다 — RED 미관찰 상태를 init 시드로 우회 선언하는 경로를 봉쇄한다. 시드 시도가 있었으면 응답에 `warning` 필드를 추가한다(무시하되 침묵하지 않음). `red_confirmed`는 오직 `scenario-red`로만 true가 될 수 있다.

`red_required`는 구현 전 RED가 필요한 시나리오에만 `true`로 준다. 필드가 없는 기존 입력은 호환성을 위해 `true`로 처리한다.

**exit code**: `0` / `scenario_spec_invalid_json(11)` / `scenario_contract_invalid(17)`

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

`red_required==true`인 시나리오가 모두 `red_confirmed==true`일 때 `locked=true`로 만든다.

```bash
bash run.sh scenario-lock --task-path <PATH>
```

**출력 JSON**:
```json
{ "ok": true, "command": "scenario-lock", "locked": true, "locked_at": "2026-07-10T16:36:00+09:00" }
```

**[MUST] RED-first 게이트**: RED 대상으로 선택한 시나리오 중 하나라도 `red_confirmed==false`이면 거부한다. `red_required==false`인 구현 후·회귀 시나리오는 잠금을 막지 않는다.

**exit code**: `0` / `scenario_not_initialized(10)` / `red_not_confirmed(8)`

---

### `scenario-mark`

`locked==true` 이후에만 result존(`result`/`evidence`/`marked_at`) 기록을 허용한다. E2E v2 결과는 `--verdict-json`을 우선 사용한다.

```bash
bash run.sh scenario-mark --task-path <PATH> --id <S-ID> --result pass|fail|blocked [--evidence <문자열>] [--fidelity mock|real-http|real-usage]
bash run.sh scenario-mark --task-path <PATH> --id <S-ID> --verdict-json <JSON>
bash run.sh scenario-mark --task-path <PATH> --id <S-ID> --resume-run-id <RUN> --resume-token <TOKEN> --submission <JSON>
```

**출력 JSON**:
```json
{ "ok": true, "command": "scenario-mark", "scenario_id": "S1", "result": "pass" }
```

**[MUST] `--fidelity` 미지정 시 `mock` 기본값(069/M-5)**: 실제 관찰된 증거 충실도를 기록하는 result존 필드. 실제 충실도를 기록하지 않은 결과는 목(mock) 수준으로 간주한다(보수적 기본값).
**[MUST] real-usage gate**: `required_fidelity=real-usage`인 pass는 `--verdict-json` 또는 resume submission의 구조화 assertion/evidence 검증을 통과해야 한다.
**[MUST] human resume**: `awaiting_human`은 operational state이며 exit 20으로 반환된다. 사람 제출은 `run_id`와 `resume_token`이 일치하고 verifier가 expected/actual 및 evidence를 확인한 뒤 final status로 전이한다.

**exit code**: `0` / `e2e_failed(6)` / `e2e_infra_error(7)` / `resume_verification_failed(6)` / `scenario_not_locked(9)` / `scenario_not_initialized(10)` / `scenario_contract_invalid(17)` / `executor_unavailable(18)` / `e2e_blocked(19)` / `e2e_awaiting_human(20)`

---

### `scenario-status`

spec/result 요약 — RED 확인 수·통과율.

```bash
bash run.sh scenario-status --task-path <PATH>
```

**출력 JSON**:
```json
{ "ok": true, "command": "scenario-status", "locked": true, "total": 2, "red_confirmed": 1, "red_required": 1, "red_confirmed_required": 1, "passed": 1, "failed": 0, "blocked": 0, "awaiting_human": 1, "status_counts": { "pass": 1, "fail": 0, "executor_unavailable": 0, "infra_error": 0, "blocked": 0, "awaiting_human": 1 } }
```

기존 `passed` / `failed` / `blocked` 필드는 호환을 위해 유지한다. v2 상태 요약은 additive `status_counts`와 top-level `awaiting_human` count로 확인한다. v2 계약 검증에 실패하면 `scenario_contract_invalid(17)`로 거부한다.

**exit code**: `0` / `scenario_not_initialized(10)` / `scenario_contract_invalid(17)`

---

### `scenario-fidelity-check` (069)

시나리오별 **요구 충실도 부분 게이트** — `required_fidelity`(spec존, 미지정 시 `mock`)와 `fidelity`(result존, 미지정 시 `mock`)의 증거 충실도 사다리(`mock`(0) < `real-http`(1) < `real-usage`(2))를 비교한다.

```bash
bash run.sh scenario-fidelity-check --task-path <PATH>
```

**판정**: 각 시나리오에 대해 `result=="pass" AND FIDELITY_ORDER[fidelity] >= FIDELITY_ORDER[required_fidelity]`를 만족하지 못하면 `unmet`에 편입한다.

**출력 JSON (통과)**:
```json
{ "ok": true, "command": "scenario-fidelity-check", "all_met": true, "total": 2, "met": 2 }
```

**출력 JSON (거부)**:
```json
{ "ok": false, "command": "scenario-fidelity-check", "error": "fidelity_unmet", "detail": ["S1"] }
```

**[MUST] 전부-게이트가 아닌 시나리오별 부분 게이트(M-3)**: `scenario-lock`(RED-first 전부-게이트)과 독립적으로 동작한다 — 혼합 트랙(mock 요구 시나리오와 real-usage 요구 시나리오가 하나의 test-scenario.json에 공존)에서 각자 충족하면 통과한다(task:061 전부-게이트 붕괴 재발 방지).

**exit code**: `0` / `scenario_not_initialized(10)` / `fidelity_unmet(13)`

---

### `scenario-conformance` (069)

계약 표면(surface) **전수 conformance 판정** — `surfaces.json`(표면 분모, 읽기 전용)을 소비하며 `backlog.json`은 일절 미접촉한다(축 분리, H-7).

```bash
bash run.sh scenario-conformance --task-path <PATH> [--surfaces <surfaces.json 경로>]
```

**판정**: surfaces.json의 각 표면 `id`에 대해, `surface_ref==id AND result=="pass"`인 시나리오가 존재하고 그 `fidelity`가 문턱(`auth=="required"`면 `real-http` 강제, 그 외는 해당 시나리오의 `required_fidelity` 기본 `mock`) 이상이어야 검증된 것으로 인정한다.

**출력 JSON (통과)**:
```json
{ "ok": true, "command": "scenario-conformance", "all_surfaces_green": true, "surface_count": 3 }
```

**출력 JSON (거부)**:
```json
{ "ok": false, "command": "scenario-conformance", "error": "surface_unverified", "detail": ["agents", "budgets"], "all_surfaces_green": false }
```

**출력 JSON (surfaces.json 부재 — 스킵)**:
```json
{ "ok": true, "command": "scenario-conformance", "applicable": false }
```

**[MUST] surfaces.json 부재 시 스킵(M-5)**: `--surfaces` 미지정 시 기본 경로(`<task-path>/surfaces.json`)를 사용하며, 지정 여부와 무관하게 파일이 없으면 `applicable:false` exit 0으로 스킵한다 — 기존 프로젝트·비-API 프로젝트 무영향.

**exit code**: `0` / `scenario_not_initialized(10)` / `surface_unverified(14)`

---

### `scenario-coverage-build` (111)

sdlc-v2 `TASK.md` / `PLAN.md` / `TEST-SCENARIO.md`를 기존 `scenario-coverage-check`가 소비하는 정규화 JSON으로 변환한다.

```bash
bash run.sh scenario-coverage-build --task-folder <PATH> --template sdlc-v2
```

**입력 계약**:

- `TASK.md`: 첫 YAML frontmatter `template: sdlc-v2`, `Acceptance criteria`의 `AC-N`, `Constraints`의 `C-N`
- `PLAN.md`: 첫 YAML frontmatter `template: sdlc-v2`, `Risks` 절의 optional `H-N`. 추가 검증이 필요한 위험이 없으면 H는 0건일 수 있다.
- `TEST-SCENARIO.md`: 첫 YAML frontmatter `template: sdlc-v2`, `Scenarios` 표의 `S-N`과 `검증 대상` 토큰
- `TEST-SCENARIO.md` Setup의 test substitute 기록은 대체 대상·이유·한계 설명용이다. `scenario-coverage-build/check`는 substitute 결과를 실제 integration/E2E/manual 증거로 승격하지 않는다.

**출력 파일**: `<task-folder>/.scenario-coverage-input.json`

**변환 규칙**:

- AC/C → `requirements[]`
- H가 있으면 `hypotheses[]`, 없으면 빈 배열
- S 행 → `scenarios[]`
- W는 실행 작업 단위이므로 `features[]`에 넣지 않음
- legacy F가 있는 문서에서만 `features[]`를 채움

**출력 JSON**:
```json
{
  "ok": true,
  "command": "scenario-coverage-build",
  "template": "sdlc-v2",
  "coverage_input": "tasks/111/.scenario-coverage-input.json",
  "counts": { "requirements": 4, "features": 0, "hypotheses": 2, "scenarios": 2 }
}
```

**거부 조건**: unknown ref, 필수 AC/C 추출 실패, PLAN Risks 절 누락, S 0건, 중복 S-ID, 문서 부재/파손, sdlc-v2 frontmatter 누락. H는 optional이지만, PLAN Risks에 H가 있으면 `scenario-coverage-check`가 미커버 H를 실패시킨다.

**exit code**: `0` / `coverage_input_invalid(17)`

---

### `scenario-coverage-check` (073)

정규화 페이로드(`goal/requirements/features/hypotheses/scenarios`)의 R/F/H ↔ 시나리오 매핑 누락을 결정론으로 판정한다. sdlc-v2 문서는 먼저 `scenario-coverage-build`로 입력을 생성한다.

```bash
bash run.sh scenario-coverage-check --coverage-input <PATH>
```

**exit code**: `0` / `coverage_unmet(16)` / `coverage_input_invalid(17)`

---

## 에러 코드

| 코드 | exit | 원인 | 처리 |
|------|------|------|------|
| `venv_missing` | 1 | OPAL .venv 없음 | install-mac.sh 재실행 |
| `yaml_parse_failed` | 2 | test-tools.yaml YAML 문법 오류 | yaml 수정 후 재시도 |
| `no_runner` | 3 | yaml 없음 + 추론 불가 | test-tools.yaml 생성 |
| `required_missing` | 4 | required 도구 미설치 | 도구 설치 후 재시도 |
| `layer_failed` | 5 | unit 계층 stop-on-fail | 실패 계층 수정 후 재시도 |
| `unit_incomplete` | 21 | unit 필수 계층 미검증(설치 확인 실패·미설정) 또는 통과 계층 0개 | 계층별 `reason` 확인 후 설정 보완·도구 설치 |
| `e2e_failed` | 6 | 제품 동작 또는 assertion 실패 | 실패 시나리오 수정·재검증 |
| `e2e_infra_error` | 7 | E2E 서버·포트·driver·증적 저장 등 인프라 오류 | 실행 환경·로그 확인 |
| `red_not_confirmed` | 8 | scenario-lock 시 RED 대상의 red_confirmed 미충족 | 해당 RED 대상의 구현 전 실패 확인 후 재시도 |
| `scenario_not_locked` | 9 | scenario-mark 호출 시점에 locked==false | scenario-lock 선행 후 재시도 |
| `scenario_not_initialized` | 10 | test-scenario.json 부재 | scenario-init 선행 |
| `scenario_spec_invalid_json` | 11 | scenario-init `--scenarios` JSON 파싱 실패 | JSON 문법 수정 후 재시도 |
| `scenario_already_locked` | 12 | scenario-red 호출 시점에 locked==true (동결 후 spec존 변경 시도) | 잠금 전에 scenario-red 호출 필요 |
| `fidelity_unmet` | 13 | scenario-fidelity-check 시 `fidelity < required_fidelity`(또는 result!=pass)인 시나리오 존재 | 요구 충실도 이상으로 재검증 후 scenario-mark --fidelity 재기록 |
| `surface_unverified` | 14 | scenario-conformance 시 조건(대상 fidelity 이상 pass) 충족 시나리오가 없는 표면 존재 | 해당 표면의 surface_ref 시나리오를 요구 충실도 이상으로 재검증 |
| `surfaces_file_not_found` | 15 | (정보용 배정) surfaces.json 부재 — 069/M-5 결정에 따라 실제로는 오류가 아닌 `applicable:false` 스킵으로 처리됨 | 해당 없음(스킵 정상 동작) |
| `coverage_unmet` | 16 | scenario-coverage-check 시 요구/기능/가설 미커버 존재 | TEST-SCENARIO 매핑 보강 후 재시도 |
| `coverage_input_invalid` | 17 | scenario-coverage-build/check 입력 문서·JSON 파싱/스키마 실패 | TASK/PLAN/TEST-SCENARIO 또는 coverage input 수정 후 재시도 |
| `scenario_contract_invalid` | 17 | test-scenario.json v2 profile/executor/status/schema 계약 위반 | scenario spec/result 계약 수정 후 재시도 |
| `executor_unavailable` | 18 | 필수 E2E executor 또는 허용 후보 소진 | executor 설정·설치·capability 확인 |
| `e2e_blocked` | 19 | 인증·외부 승인·사람 입력 등 자동 진행 불가 | 필요한 외부 조치 후 재개 |
| `e2e_awaiting_human` | 20 | 사람 handoff 대기 | structured submission으로 같은 run 재개 |
| `resume_verification_failed` | 6 | human handoff resume token/run/evidence 검증 실패 | 같은 run-id/resume-token과 구조화 submission 확인 |
| `e2e_env_config_missing` | 1 (env-validate/env-check) · detail_code(e2e run, exit 19) | `.opal/e2e/environment.json` 부재 | `e2e env-inspect`로 검토 후 설정 작성 |
| `e2e_env_config_invalid` | 1 (env-validate/env-check) · detail_code(e2e run, exit 19) | 환경 설정이 스키마 검증 불통과 | `violations` 참조해 설정 수정 후 재시도 |
| `e2e_env_surface_missing` | detail_code(e2e run, exit 19) | 시나리오 profile이 요구하는 종류의 표면이 설정에 없음 | 해당 종류의 표면을 설정에 추가 |
| `e2e_env_surface_ambiguous` | detail_code(e2e run, exit 19) | 같은 종류 표면이 여럿이고 `surface_ref`로 특정할 수 없음 | 시나리오에 `surface_ref` 지정 |

> `scenario-*` 에러코드는 `lib/scenario.py`의 `SCENARIO_ERROR_CODES`(전용 SSOT)에서 관리하며, 5~12는 기존 0~7 계열과 충돌 없이 배정됐고(격리 원칙 — PLAN.md §3.2.2, 056/ADD-1), 069는 13~15, 073/111은 16~17을 이어서 배정한다.

### Legacy E2E 입력 변환

기존 cmux/browser adapter 입력의 `fallback`, `escalated`, `escalate`, `escalation`은 신규 출력이 아니라 migration 입력 alias다.

| legacy 입력 | 신규 상태 |
|---|---|
| `fallback` + `not_in_cmux` / `cmux_not_installed` | Browser 후보 `provider_unavailable` |
| `fallback` + `open_failed` / `surface_parse_failed` | `infra_error` |
| `has_cmux=false` | `infra_error` |
| `escalated` + `usage` / `invalid_surface` / `goto_failed` / `eval_failed` | `infra_error` |
| `escalated` + `wait_failed` + `wait_kind=assertion_condition` | `fail` |
| `escalated` + `wait_failed` + 기타 `wait_kind` 또는 누락 | `infra_error` |
| 알 수 없는 error 또는 reason 없는 generic `fallback` | `infra_error` |

신규 E2E JSON에는 generic fallback/escalation 의미의 키를 만들지 않는다.

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
| v1.3 | 2026-07-18 22:42 | 증거 충실도 사다리(`FIDELITY_ORDER`: mock<real-http<real-usage) 도입 — `required_fidelity`/`fidelity`/`surface_ref` 필드(optional additive, 미지정 시 mock 기본값) + `scenario-fidelity-check`(시나리오별 부분 게이트, fidelity_unmet exit 13) + `scenario-conformance`(표면 전수 conformance, surfaces.json 분모·읽기 전용, surface_unverified exit 14, surfaces.json 부재 시 applicable:false 스킵) 신규 서브명령. backlog.json 미접촉(축 분리 불변) (069) |
| v1.4 | 2026-09-09 14:18 KST | `scenario-coverage-build --task-folder ... --template sdlc-v2` 추가 — sdlc-v2 TASK AC/C, PLAN H, TEST S를 `.scenario-coverage-input.json`으로 결정론 변환하고 W를 features에서 제외. 기존 `scenario-coverage-check` 입력·exit 계약은 유지 (task 111/W-5) |
| v1.5 | 2026-09-09 14:58 KST | sdlc-v2 builder가 중복 S-ID를 `coverage_input_invalid`로 거부하도록 계약을 보강하고, Setup의 test substitute 기록이 실제 integration/E2E/manual 증거를 대체하지 못함을 명시 (task 111/W-5 보완) |
| v1.6 | 2026-09-09 15:07 KST | sdlc-v2 PLAN Risks H를 optional로 변경. H 0건은 정상 build/check 통과하고, H가 존재하는 경우의 미커버 실패 계약은 유지 (task 111/W-5 보완) |
| v1.7 | 2026-09-14 | `tools.md` test-tool 절 흡수 — `integration` 절에 E2E contract v2 profile 5종(`browser`/`api`/`hybrid`/`collaborative`/`manual`, SSOT `lib/e2e_contract.py` `PROFILES`) 명시 + 상단 소스·배포 경로 1줄 추가. 나머지 절 내용(트리거 조건·루프 한도 비보유·status/exit 표·legacy 입력 변환)은 이미 README가 보유해 중복 흡수 없음 (131 W-14) |
