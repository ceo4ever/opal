# OPAL Agent Browser E2E 하네스 설계 제안서

> 상태: 제안
> 작성: 알투(PM)
> 작성일: 2026-09-12
> 목적: main repo와 worktree의 실제 소스를 격리 실행하고, Orca-managed 세션을 우선으로 standalone·cmux 실행 경로를 교체 가능하게 사용하는 E2E 하네스 제안
> 범위: 방향과 핵심 계약을 정하는 제안서. 구현 계획(PLAN), 코드 변경, Playwright 제거 실행은 포함하지 않는다.

---

## 1. 제안 요약

OPAL의 E2E는 특정 브라우저 제품에 결합하지 않고 다음 두 책임을 분리해야 한다.

1. **SUT Harness**: 검증할 소스 트리에서 서버를 기동하고 health, 포트, 프로세스, 로그를 관리한다.
2. **Browser Driver**: 실제 브라우저에서 사용자 행동을 수행하고 assertion과 증적을 반환한다.

Orca와 standalone agent-browser를 별도 provider로 만들지 않는다. Orca 앱은 `agent-browser` 실행 파일을 번들하고 `orca exec --command "<agent-browser command>"` 경로를 제공하므로, 둘은 같은 driver의 세션 소유권 모드로 취급한다.

```text
agent-browser driver / orca-managed session
  → cmux driver / owned surface
  → agent-browser driver / standalone session
  → Playwright driver(optional compatibility)
```

Orca가 관리하는 작업에서는 worktree-scoped 세션을 1순위로 사용한다. cmux는 소유 surface를 만들 수 있을 때 2순위다. 같은 agent-browser driver의 standalone session은 Orca·cmux가 없는 로컬·CI 환경의 기본 headless fallback을 담당한다. Playwright는 기존 소비자 이전이 끝날 때까지 호환 driver로 유지하되 기본 설치에서는 단계적으로 제외한다.

```text
실행 컨텍스트 결정
  → 전용 포트 임대
  → 선택한 소스 트리에서 SUT 기동
  → health gate
  → driver·session mode 탐지·선택
  → snapshot → action → re-snapshot → assertion
  → 증적·판정 저장
  → 소유 자원만 정리
```

핵심 불변식은 **실제 assertion과 필수 증적이 모두 없으면 E2E를 pass로 판정하지 않는 것**이다.

---

## 2. 배경과 문제 정의

### 2.1 설치본 서버는 source E2E 대상이 아니다

현재 `opal-cli console start`는 명령을 실행한 현재 디렉터리가 아니라 `OPAL_HOME`의 배포본인 `~/.opal/dashboard-server`를 사용한다. main repo나 worktree에서 명령을 실행해도 해당 브랜치의 소스 변경을 검증하지 않는다.

따라서 다음 세 대상을 명시적으로 분리해야 한다.

| target | 검증 대상 | 서버 소스 | 용도 |
|---|---|---|---|
| `source-main` | main working tree | main repo의 `dashboard/` | 병합 전후 source E2E |
| `source-worktree` | 특정 child worktree | 해당 worktree의 `dashboard/` | 태스크 변경 격리 검증 |
| `installed` | 설치·배포 산출물 | 격리된 `OPAL_HOME`의 `dashboard-server/` | 설치본 smoke·release 검증 |

사용자가 이용 중인 기본 `127.0.0.1:7823` Console은 user-owned 자원으로 간주한다. source E2E가 이를 재사용하거나 중단하거나 덮어쓰면 안 된다.

### 2.2 현재 포트 설정은 병렬 worktree E2E를 지원하지 않는다

현재 Console 프런트엔드의 API 주소는 `http://127.0.0.1:7823`으로 고정되어 있다. `.opal/worktree.json`의 `portOffset`은 메타데이터로 전달될 뿐 포트 임대, 환경 주입, 충돌 방지를 집행하지 않는다.

이 상태에서는 다음 문제가 발생한다.

- main과 여러 worktree가 동시에 같은 포트를 사용한다.
- 프런트가 다른 worktree 또는 설치본 backend를 바라볼 수 있다.
- 기존 daemon 종료 로직이 다른 E2E 실행이나 사용자 서버까지 종료할 수 있다.
- 테스트가 통과해도 실제 변경 소스를 검증했다는 보장이 없다.

### 2.3 현재 E2E 결과에는 false positive 경로가 있다

현행 `test-tool`의 Playwright fallback은 실제 브라우저 실행 결과가 아니라 후속 MCP action 요청을 반환한다. 호출자는 이 `fallback` 상태를 성공 범주로 취급할 수 있다. cmux 경로 역시 surface를 열고 URL로 이동한 뒤 닫는 흐름이 중심이며, 시나리오별 의미 assertion과 필수 증적을 강제하지 않는다.

따라서 “브라우저를 열었다”와 “사용자 목표가 동작했다”를 분리하고, 후자만 E2E pass로 인정해야 한다.

### 2.4 현행 근거

| 확인 사항 | 코드 근거 |
|---|---|
| `opal-cli console`이 배포본과 고정 포트 `7823`을 사용 | `opal/tools/opal-cli/lib/console.sh:34-40`, `:75-80` |
| Console stop이 process ownership 없이 광범위한 process pattern을 종료 | `opal/tools/opal-cli/lib/console.sh:87-92` |
| 프런트 API 주소가 `127.0.0.1:7823`으로 고정 | `dashboard/frontend/src/lib/api.ts:14` |
| worktree 생성 결과가 `portOffset`을 반환하지만 실제 lease를 수행하지 않음 | `opal/tools/worktree-tool/worktree_tool.py:971-996` |
| Playwright fallback 요청이 `status=fallback`이며 `ok=true`로 처리 가능 | `opal/tools/test-tool/lib/e2e_adapter.py:119-134`, `:172-180` |
| cmux가 open·navigate·close 후 semantic assertion 없이 pass 반환 | `opal/tools/test-tool/lib/e2e_adapter.py:225-260` |

---

## 3. 목표와 비목표

### 3.1 목표

- main과 worktree의 **실제 변경 소스**를 검증한다.
- 여러 worktree가 동시에 E2E를 수행해도 서버·포트·브라우저 상태가 충돌하지 않는다.
- Orca-managed 세션에 최적화하되 새로운 브라우저 실행기는 driver 또는 session mode로 수용한다.
- TEST-SCENARIO의 사용자 행동과 기대 결과를 실제 브라우저 assertion으로 검증한다.
- 재현 가능한 공통 증적과, 실행 mode가 지원하고 시나리오가 요구한 screenshot·console·network 증적을 남긴다.
- driver/session 부재와 제품 실패를 구분해 잘못된 fallback을 차단한다.
- Playwright의 기본 설치 비용을 최종적으로 제거한다.

### 3.2 비목표

- Playwright 또는 각 브라우저 제품의 기능을 OPAL 내부에서 재구현하지 않는다.
- 모든 driver/session mode의 고유 기능을 최소 공통 기능으로 제한하지 않는다.
- 사용자가 실행 중인 브라우저 탭, cmux surface, Orca worktree, Console daemon을 임의로 정리하지 않는다.
- 이번 제안에서 기존 `TEST-SCENARIO.md`나 `test-scenario.json` 스키마를 즉시 교체하지 않는다.
- 브라우저 driver 선택만으로 테스트 서버의 생명주기 문제를 해결했다고 간주하지 않는다.

---

## 4. 설계 원칙

### 4.1 서버와 브라우저의 소유권을 분리한다

SUT Harness가 서버 생명주기와 target URL을 소유하고 Browser Driver는 전달받은 URL만 사용한다. Browser Driver가 임의로 main daemon을 찾거나 서버를 기동하지 않는다.

### 4.2 실행한 소스 트리를 증명한다

각 run은 `project_root`, `worktree_root`, commit, dirty 여부, backend/frontend 명령, 실제 URL을 기록한다. `source-worktree`에서는 모든 실행 경로를 canonical worktree root에서 해석한다.

### 4.3 고정 포트를 사용하지 않는다

source E2E는 실행마다 backend와 frontend 포트를 임대한다. 임대는 사용 가능 포트 탐색만으로 끝내지 않고 lock 또는 예약 socket으로 경쟁 조건을 방지한다.

### 4.4 pass는 assertion과 증적으로만 만든다

다음 조건이 모두 충족되어야 pass다.

- SUT health gate 통과
- 시나리오의 모든 필수 action 성공
- 기대 상태를 확인하는 semantic assertion 통과
- 필수 증적 저장 성공
- 시나리오가 요구하고 실행 mode가 제공하는 console/network 검사 통과

Driver가 `open`, `navigate`, `snapshot`만 수행한 결과는 pass가 아니다.

### 4.5 fallback은 capability 부재에만 허용한다

현재 실행 mode에서 제품 동작 실패, assertion 실패, 인증 실패, 데이터 불일치가 발생하면 다른 mode로 재시도해 성공으로 덮지 않는다. 다음 후보 전환은 `provider_unavailable`일 때만 허용한다.

### 4.6 소유한 자원만 정리한다

하네스가 생성한 PID/process group, browser tab/session/profile, cmux surface, 포트 lease만 종료한다. 광범위한 `pkill`과 사용자 소유 surface 정리는 금지한다.

### 4.7 공통 계약과 확장 capability를 함께 둔다

공통 시나리오는 표준 driver contract로 실행한다. capability는 `native`, `exec`, `none` 실행 경로와 probe 결과를 함께 선언하고, 시나리오가 필요로 할 때만 요구한다. Orca의 console/network 지원은 네이티브라고 가정하지 않고 `orca exec` 경유 명령을 실제 probe한 경우에만 활성화한다.

---

## 5. 제안 아키텍처

### 5.1 구성요소

| 구성요소 | 책임 | 소유하지 않는 것 |
|---|---|---|
| E2E Orchestrator | run 생성, target/driver/session mode 결정, 단계 제어, 최종 verdict | 브라우저별 명령 구현 |
| Runtime Manager | 포트 임대, env 구성, 서버 기동·health·로그·종료 | 사용자 daemon |
| Scenario Adapter | TEST-SCENARIO를 action/assertion으로 정규화 | 실제 브라우저 조작 |
| Session Resolver | `orca-managed`, `cmux-owned`, `standalone` 후보 탐지와 소유권 확정 | 제품 성공 판정 |
| Driver Adapter | agent-browser·cmux·Playwright 명령 변환과 결과 정규화 | session별 중복 adapter |
| Evidence Collector | snapshot·screenshot·console·network·server log 수집 | 제품 성공 추정 |
| Verdict Gate | assertion·증적·오류를 종합해 상태 결정 | 다음 실행 후보 선택 |

기존 `test-tool`은 E2E Orchestrator의 결정론적 진입점으로 확장하는 안을 우선한다. 별도 도구는 책임 분리가 실제로 필요하다는 구현 분석 결과가 있을 때만 신설한다.

### 5.2 실행 상태 머신

```text
created
  → context_resolved
  → ports_leased
  → sut_starting
  → sut_ready
  → driver_ready
  → scenario_running
  → evidence_captured
  → passed | failed | blocked | infra_error
  → cleanup_complete | cleanup_warning
```

중간 상태를 건너뛴 pass는 허용하지 않는다. cleanup은 verdict를 바꾸기보다 별도 결과로 기록하되, 프로세스 누출처럼 다음 실행을 오염시키는 실패는 `infra_error`로 승격한다.

### 5.3 디렉터리와 산출물

제안 실행 결과 구조는 다음과 같다.

```text
${TMPDIR}/opal-e2e-runs/{project-id}/{run-id}/
├── run.json
├── actions.jsonl
├── assertions.json
├── server/
│   ├── backend.log
│   └── frontend.log
├── browser/
│   ├── before.snapshot
│   ├── after.snapshot
│   ├── console.jsonl
│   └── network.jsonl
└── screenshots/
    └── {scenario-id}-{step}.png
```

실행 증적은 기본적으로 repository 밖의 OS 임시 디렉터리에 저장한다. 태스크 안에 보존해야 하는 요약 증적만 명시적으로 복사한다. repository 내부 `.e2e-runs/` 또는 `.test-run/`을 지원한다면 구현과 같은 변경에서 `.gitignore`를 함께 갱신해 untracked 오염을 차단한다.

---

## 6. 서버 실행 모델

### 6.1 `source-main`

- main repo의 backend와 frontend를 별도 임대 포트에서 기동한다.
- 사용자 설치본 `7823` daemon은 그대로 둔다.
- dirty working tree 여부와 변경 파일을 run metadata에 기록한다.
- 개발 서버 또는 production preview 중 어떤 경로를 사용할지는 시나리오 profile로 명시한다.

### 6.2 `source-worktree`

- worktree-tool이 발급한 canonical `worktree_root`에서 서버를 기동한다.
- dependency setup도 해당 worktree 안에서 수행한다.
- 포트는 task 번호를 단순 가산해 추측하지 않고 run-time lease로 확정한다.
- Orca-managed mode에서는 `orca worktree list`로 확인한 대상에 모든 브라우저 명령의 `--worktree <selector>`를 명시한다.
- cmux-owned와 standalone mode에는 worktree별로 발급된 정확한 URL과 격리 session을 전달한다.

### 6.3 `installed`

- 실제 사용자 `~/.opal`을 재설치 대상으로 사용하지 않는다.
- 임시 `OPAL_HOME`에 install artifact를 배포해 smoke test한다.
- 설치본과 source 검증 결과를 같은 verdict로 합치지 않는다.
- release gate가 필요하면 `source`와 `installed`를 각각 통과해야 한다.

### 6.4 프런트엔드 URL·CORS 계약

프런트 API 주소는 실행 profile에 따라 다음 단일 규칙으로 정리한다.

| profile | API URL | 이유 |
|---|---|---|
| production/installed | 빈 문자열 `""` | 호출자가 `/api/...`와 `/health` 완전 경로를 넘기므로 현재 오리진 루트에 그대로 결합 |
| dev/source E2E | 시작 시 주입한 `VITE_API_BASE_URL` | Vite dev/build 과정에서 임대한 backend 주소로 치환 |

`API_BASE_URL`은 `import.meta.env.VITE_API_BASE_URL ?? ""` 형태를 기준으로 한다. `/api` prefix를 base에 넣으면 `/api/api/projects`, `/api/health`가 되어 기존 호출을 깨므로 금지한다. `VITE_API_BASE_URL`은 브라우저 runtime 설정이 아니라 Vite 시작·build 시점 설정이다. 설치본 정적 파일의 runtime port 문제를 이 변수로 해결하지 않는다. backend는 현재 모듈 상수인 CORS origin을 env에서 읽도록 변경하되, dev/source E2E의 정확한 frontend origin만 추가하고 production은 동일 오리진을 유지한다.

### 6.5 환경 계약

다음 변수명은 구현 PLAN에서 기존 설정과 충돌 여부를 확인한 뒤 확정한다.

| 제안 변수 | 용도 |
|---|---|
| `OPAL_E2E_RUN_ID` | 실행 식별자 |
| `OPAL_E2E_TARGET` | `source-main`, `source-worktree`, `installed` |
| `OPAL_E2E_BACKEND_PORT` | 임대한 backend 포트 |
| `OPAL_E2E_FRONTEND_PORT` | 임대한 frontend 포트 |
| `VITE_API_BASE_URL` | frontend가 사용할 실제 backend URL |
| `OPAL_E2E_ARTIFACT_DIR` | 증적 저장 위치 |

backend CORS는 E2E frontend origin만 실행 시점에 추가한다. 개발 편의를 이유로 임의 origin 전체 허용을 도입하지 않는다.

### 6.6 Port Lease 계약

현재 repository에는 port lease 구현이 없으므로 신규 Runtime Manager의 명시적 책임으로 둔다. `portOffset`은 호환용 hint일 뿐 allocator로 승격하지 않는다.

```text
cross-process allocator lock 획득
  → 127.0.0.1 candidate port bind 검사
  → run-id·owner-pid·port를 atomic lease record로 기록
  → strict port로 child 즉시 기동
  → EADDRINUSE면 record 폐기 후 제한 횟수 재할당
  → health 통과 뒤 lease 확정
  → owned process 종료 확인 뒤 release
```

OPAL 실행끼리는 allocator lock과 lease record로 충돌을 막는다. 비협조적인 외부 프로세스와의 bind 경쟁은 strict-port 기동 실패와 재할당으로 처리한다. lease record만 남고 owner PID가 없으면 다음 실행이 stale lease로 회수할 수 있어야 한다.

---

## 7. Browser Driver·Session 계약

### 7.1 공통 인터페이스

| operation | 입력 | 최소 출력 |
|---|---|---|
| `probe` | runtime context | driver, session mode, availability, version, capability routes |
| `open` | URL, isolation key | owned browser/session handle |
| `snapshot` | handle | 구조화 snapshot, current URL |
| `act` | handle, action | action 결과, 변경된 URL |
| `wait` | handle, condition | 충족 여부, elapsed time |
| `assert` | handle, assertion | expected, actual, pass/fail |
| `capture` | handle, evidence spec | artifact paths, console/network |
| `close` | owned handle | cleanup 결과 |

구현 언어의 클래스나 프로토콜을 먼저 확정하지 않는다. 우선 JSON 입출력 계약을 고정하고 기존 shell/Python 도구가 이를 소비하도록 한다.

### 7.2 capability와 실행 경로 probe

```json
{
  "driver": "agent-browser",
  "session_mode": "orca-managed",
  "capabilities": {
    "snapshot": {"available": true, "route": "native"},
    "screenshot": {"available": true, "route": "native"},
    "console": {"available": false, "route": "exec", "probed": true},
    "network": {"available": false, "route": "exec", "probed": true},
    "isolated_profile": {"available": true, "route": "session"}
  }
}
```

`route=native`는 현재 Orca CLI의 typed command가 실제 존재할 때만 사용한다. `route=exec`는 `orca exec --command`로 해당 agent-browser 명령을 비파괴 probe해 성공한 경우에만 `available=true`가 된다. help 문자열이나 번들 파일 존재만으로 실행 capability를 추정하지 않는다.

시나리오가 요구한 capability가 없으면 해당 실행 후보는 실행 전에 `provider_unavailable`을 반환한다. 실행 중 assertion이나 필수 증적을 생략해 capability 부족을 보정하지 않는다.

### 7.3 표준 상태

| 상태 | 의미 | fallback |
|---|---|:---:|
| `pass` | 모든 assertion과 증적 조건 통과 | 불필요 |
| `fail` | 제품 동작 또는 assertion 실패 | 금지 |
| `provider_unavailable` | 실행 전 provider/runtime/capability 부재 | 허용 |
| `infra_error` | 서버, 포트, 브라우저 crash, 증적 저장 등 인프라 실패 | 기본 금지 |
| `blocked` | 인증·외부 승인·사람 입력 등 자동 진행 불가 | 금지 |

`infra_error`를 다음 실행 mode로 전환할지는 오류별 정책으로 명시하되 기본값은 금지한다. mode를 바꾸면 재현 조건도 달라지므로 자동으로 제품 성공으로 해석할 수 없기 때문이다.

### 7.4 현행 상태 마이그레이션

기존 `status=escalated`와 `escalate=true`는 신규 상태가 정착될 때까지 입력 호환만 제공하고 결과 계약에서는 제거한다.

| 현행 결과·error | 신규 상태 | fallback | 비고 |
|---|---|:---:|---|
| `fallback` | `provider_unavailable` | 허용 | 실제 다음 driver가 실행되기 전이므로 pass 금지 |
| `escalated` + `usage` | `infra_error` | 금지 | 호출자 계약 오류 |
| `escalated` + `invalid_surface` | `infra_error` | 금지 | session handle 오류 |
| `escalated` + `goto_failed` | `infra_error` | 금지 | URL·navigation 실행 오류. 제품 assertion 실패와 분리 |
| `escalated` + `wait_failed` | `infra_error` 또는 `fail` | 금지 | error code가 아니라 하네스가 기록한 `wait_kind`로 판정 |
| `escalated` + `eval_failed` | `infra_error` | 금지 | driver 명령 실행 오류 |

`wait_failed`는 cmux-tool의 단일 error code만으로 원인을 나눌 수 없다. 하네스가 wait을 발행할 때 `wait_kind=navigation_ready|transport|assertion_condition`을 action log에 기록하고, 앞의 두 종류는 `infra_error`, semantic assertion condition timeout은 `fail`로 판정한다. `wait_kind`가 없는 legacy 결과는 fail-safe로 `infra_error`다.

#### 신규 상태와 process exit code

| 신규 상태 | process exit code | 공개 error | 처리 |
|---|---:|---|---|
| `pass` | 0 | 없음 | 성공 종료 |
| `fail` | 6 | `e2e_failed` | 기존 E2E 실패 코드 유지 |
| `provider_unavailable` | 후보 탐색 중 exit 없음 / 전 후보 소진 시 18 | `browser_unavailable` | 다음 후보가 있으면 내부 상태로만 소비 |
| `infra_error` | 7 | `e2e_infra_error` | 기존 escalation exit 7을 일반화해 호환 유지 |
| `blocked` | 19 | `e2e_blocked` | 사람 입력·인증·외부 승인 필요 |

exit 18·19는 현재 test-tool의 0~17 범위 다음에 배정한다. 기존 테스트는 한 번에 삭제하지 않는다. 먼저 legacy 입력 → 신규 상태·exit code 변환 테스트를 추가하고, `escalation` error는 이행기 alias로 exit 7을 유지한다. 모든 호출자가 신규 상태를 소비한 뒤 `escalate` boolean, `escalated` 문자열, `escalation` alias를 제거한다.

---

## 8. Driver·Session별 적용안

### 8.1 agent-browser driver — Orca-managed·standalone 공용

Orca 앱에 번들된 `agent-browser`와 standalone `agent-browser`는 하나의 driver adapter를 공유한다. 차이는 엔진이 아니라 session owner, 실행 route, worktree scope다.

| session mode | owner | 선택 조건 | 명령 경로 |
|---|---|---|---|
| `orca-managed` | Orca worktree | runtime과 target worktree 사용 가능 | typed Orca command 우선, 미지원 기능은 probe된 `orca exec` |
| `standalone` | E2E run | Orca·cmux 후보 사용 불가 또는 CI profile | 직접 `agent-browser --session <run-id>` |

Orca-managed mode는 worktree별 Chromium과 탭 격리를 활용하므로 Orca 작업의 1순위다. standalone mode는 같은 driver 계약을 재사용해 별도 adapter 중복 없이 로컬·CI fallback을 담당한다.

적용 원칙:

- 모든 명령에 대상 worktree를 명시한다.
- `snapshot → act → re-snapshot` 순서를 지키고 navigation 뒤 오래된 ref를 재사용하지 않는다.
- E2E가 연 탭과 profile만 닫는다.
- Orca runtime이 없거나 대상 worktree를 찾지 못한 경우에만 다음 실행 후보로 전환한다.
- Orca GUI 조작이 아니라 embedded browser CLI 계약을 사용한다.
- console/network는 native 지원으로 가정하지 않고 `orca exec` 경유 probe 결과가 true일 때만 수집한다.
- `orca serve`는 headless Orca runtime 후보로 검증하되 Linux CI의 기본 전제로 두지 않는다.

출처: [Orca Browser overview](https://www.onorca.dev/docs/browser/overview), [Orca CLI reference](https://www.onorca.dev/docs/cli/reference)

실측 근거: 현재 macOS Orca 앱에 `/Applications/Orca.app/Contents/Resources/agent-browser-darwin-arm64`가 존재하며 agent-browser `0.27.0`으로 확인됐다. 현재 `orca --help`에서는 console/network typed command가 확인되지 않아 본 제안은 이를 native capability로 선언하지 않는다.

### 8.2 cmux driver — 2순위

기존 `cmux-tool`의 JSON error code와 mode A/B/C 소유권 모델을 재사용한다. 자동 E2E 기본은 하네스가 surface를 열고 닫는 mode A로 제한한다. 사용자 소유 surface를 재사용하는 mode B/C는 명시적 interactive run에서만 허용한다.

보강해야 할 부분:

- open·navigate 성공을 pass로 보지 않는다.
- snapshot 기반 action과 시나리오 assertion을 필수화한다.
- screenshot/console/network를 제공하지 못하는 경우 capability에 `none`으로 명시한다.
- `user_owned=true`인 surface는 cleanup하지 않는다.

### 8.3 standalone session — 기본 headless fallback

standalone mode는 §8.1과 같은 agent-browser driver를 직접 실행한다. `agent-browser`는 CLI와 daemon 구조로 브라우저를 제어하고, snapshot ref 기반 agent workflow를 지원한다. Playwright Python package 없이 동작하며 Chrome for Testing 설치 또는 기존 Chrome 계열 브라우저 탐지를 지원하므로 Orca·cmux가 없는 환경의 fallback으로 적합하다.

바이너리는 다음 순서로 해석한다.

```text
1. PATH의 agent-browser
2. 현재 OS·architecture와 일치하는 Orca bundle
3. OPAL managed cache의 pinned agent-browser
4. 모두 없을 때만 pinned version 신규 설치
```

버전 SSOT는 driver manifest 한 곳에 두며 초기 pin은 현재 실측 bundle과 같은 `0.27.0`으로 한다. 각 후보는 실행 전 `--version`을 확인하고 exact pin 또는 manifest의 명시적 compatibility allowlist에 맞을 때만 채택한다. 불일치 후보는 다음 경로로 넘어가며 자동 upgrade하지 않는다. 신규 설치와 browser download는 마지막 단계에서만 수행한다.

적용 원칙:

- run-id 기반 named session/profile로 실행을 격리한다.
- 선택된 binary path·version·해석 source를 run metadata에 기록한다.
- PATH 또는 Orca bundle이 pin을 충족하면 OPAL binary를 추가 설치하지 않는다.
- CI에서는 고정 버전과 cache 정책을 사용한다.
- session 종료가 해당 run에만 영향을 주는지 adapter 테스트로 검증한다.

출처: [agent-browser 공식 README](https://github.com/vercel-labs/agent-browser/blob/main/README.md), [agent-browser 설치 문서](https://github.com/vercel-labs/agent-browser/blob/main/docs/src/app/installation/page.mdx)

### 8.4 Playwright — 이행기 optional driver

Playwright는 곧바로 삭제하지 않는다. 현재 다음 경로가 Playwright를 소비한다.

- `test-tool` E2E fallback
- `playwright-tool`
- `opal-wtm-agent`의 web-to-markdown fallback
- Playwright MCP 설정
- 설치 스크립트의 Python package와 Chromium 설치

이 소비자를 이전하기 전에 package와 browser binary 설치를 제거하면 E2E 외 기능이 회귀한다. 따라서 “지원 제거”와 “기본 설치 제거”를 분리한다.

### 8.5 지원 OS·CI matrix

다음 matrix를 초기 release gate로 정의한다. Orca·cmux는 설치 가능한 모든 CI의 전제가 아니며 standalone mode가 이 공백을 담당한다.

| OS·architecture | 실행 환경 | 필수 mode | 적용 gate |
|---|---|---|---|
| macOS arm64 | Orca 설치 로컬 통합 환경 | `orca-managed` | Orca-first 기능 채택 전 |
| macOS arm64 | headless CI | `standalone` | agent-browser fallback 채택 전 |
| Linux x64 | headless CI | `standalone` | agent-browser fallback 채택 전 |
| Windows x64 | headless CI | `standalone` | Playwright 기본 설치 제거 전 |
| macOS arm64 | cmux 설치 로컬 통합 환경 | `cmux-owned` | cmux driver 변경 시 |

다른 architecture는 공식 지원 범위에 추가될 때 matrix 행과 pinned binary 검증을 함께 추가한다. `orca serve`는 별도 실험 행으로 검증할 수 있지만 위 필수 CI 행을 대체하지 않는다.

---

## 9. 시나리오와 assertion 계약

### 9.1 시나리오 최소 구조

기존 TEST-SCENARIO를 다음 실행 모델로 정규화한다.

```yaml
id: S-E2E-001
target: source-worktree
requires:
  - snapshot
  - screenshot
setup:
  path: /projects
steps:
  - action: click
    target: "프로젝트 카드"
  - wait:
      url_matches: "/projects/.+"
assertions:
  - visible_text: "프로젝트 개요"
  - url_matches: "/projects/.+"
evidence:
  - after_snapshot
  - screenshot
```

YAML은 설명 예시이며 기존 JSON SSOT와 실제 필드 매핑은 구현 PLAN에서 확정한다.

### 9.2 assertion 우선순위

1. 사용자에게 보이는 상태: 텍스트, 역할, URL, 활성 상태
2. 브라우저 동작 결과: navigation, dialog, download, form state
3. 필요한 경우 API/network 결과
4. 내부 DOM/CSS selector는 안정적인 사용자 의미 표현이 없을 때만 사용

AI agent가 화면을 보고 “정상으로 보인다”고 서술하는 것은 assertion이 아니다. expected와 actual이 구조화되어야 한다.

### 9.3 ref 수명

snapshot ref를 사용하는 driver는 navigation, click, rerender 뒤 ref가 무효가 될 수 있다. action 뒤 re-snapshot을 기본으로 하고, driver adapter가 오래된 ref 사용을 감지하면 `infra_error`가 아니라 해당 action 실패로 명확히 반환한다.

---

## 10. 증적과 판정 계약

### 10.1 `run.json` 최소 필드

```json
{
  "run_id": "e2e-20260912-001",
  "scenario_id": "S-E2E-001",
  "target": "source-worktree",
  "project_root": "/path/to/project",
  "worktree_root": "/path/to/worktree",
  "driver": "agent-browser",
  "session_mode": "orca-managed",
  "driver_version": "resolved-at-runtime",
  "urls": {
    "frontend": "http://127.0.0.1:49152",
    "backend": "http://127.0.0.1:49153"
  },
  "status": "pass",
  "assertion_summary": {"passed": 3, "failed": 0},
  "evidence_complete": true,
  "cleanup": "complete"
}
```

### 10.2 필수 증적

증적 요구는 다음 순서로 판정한다.

```text
시나리오 required capability 확인
  → 실행 전 driver/session probe
  → 미지원이면 provider_unavailable로 다음 driver/session 후보
  → 지원 후보에서 시나리오 실행
  → 공통 필수 증적 + 시나리오 필수 증적 판정
  → 실패 시 제공 가능한 진단 증적을 best-effort 수집
```

| 증적 | 필수 수준 | 조건 |
|---|---|---|
| 실행 metadata | 공통 필수 | 모든 run |
| backend/frontend log | 공통 필수 | 서버를 하네스가 기동한 run |
| action log | 공통 필수 | 모든 browser run |
| assertion expected/actual | 공통 필수 | 모든 assertion |
| 시작·종료 snapshot | 시나리오 필수 | UI 변경 시나리오가 `snapshot`을 요구할 때 |
| screenshot | 시나리오 필수 또는 진단 best-effort | 시나리오가 요구하면 사전 probe 필수. fail/blocked/infra_error에서는 지원 시 수집하되 미지원 자체로 기존 실패 상태를 바꾸지 않음 |
| console/network | 시나리오 필수 | capability probe가 성공하고 시나리오가 요구할 때 |
| cleanup 결과 | 공통 필수 | 모든 run |

공통 필수 증적은 metadata, server log, action log, assertion 결과, cleanup이다. 브라우저 고유 증적은 시나리오의 `requires`에 선언된 경우에만 pass gate가 된다. `test-tool scenario-mark`의 `real-usage` 충실도는 실제 사용자 경로와 해당 run의 필수 증적이 확인된 뒤에만 기록한다.

### 10.3 민감정보 처리

- 인증 token, cookie, Authorization header, query secret은 증적 저장 전에 redaction한다.
- screenshot에 개인정보가 포함될 수 있는 시나리오는 masking 또는 별도 보존 정책을 적용한다.
- browser profile은 run 종료 후 삭제하며 사용자 profile을 재사용하지 않는다.
- raw network body는 기본 수집하지 않고 실패 분석에 필요한 allowlist endpoint만 선택한다.

---

## 11. 오류와 fallback 정책

```text
probe 실패
  ├─ runtime/명령/capability 없음 → provider_unavailable → 다음 driver/session 후보
  └─ 설정·권한·계약 오류         → blocked 또는 infra_error → 중단

실행 시작 후 실패
  ├─ assertion 실패              → fail → 중단
  ├─ 제품 오류                   → fail → 중단
  ├─ 브라우저 crash              → infra_error → 중단·재시도 정책 적용
  └─ 사용자 승인/로그인 필요      → blocked → 중단
```

같은 시나리오를 다른 driver/session에서 진단 목적으로 다시 실행할 수는 있다. 다만 최초 실패를 덮어쓰지 않고 별도 run으로 저장하며, 최종 판정에 두 결과를 모두 표시한다.

---

## 12. Playwright 기본 설치 제거 전략

### 12.1 판단

**Playwright 기본 설치는 제거할 수 있지만 지금 즉시 제거하지 않는다.** agent-browser driver의 standalone session이 최종 fallback 역할을 검증하고 E2E 외 소비자를 모두 이전한 뒤 기본 설치에서 제외한다.

### 12.2 단계

| 단계 | 변경 | 완료 조건 |
|---|---|---|
| P1 | driver/session contract와 agent-browser 공용 adapter 도입 | Orca-managed real-usage E2E가 assertion+증적과 함께 통과 |
| P2 | cmux adapter를 같은 계약으로 이전 | 기존 mode 소유권·에러 코드 회귀 없음 |
| P3 | agent-browser standalone mode와 CI fallback 활성화 | Orca·cmux 없는 환경에서 같은 adapter로 실제 E2E 통과 |
| P4 | web-to-markdown과 MCP 소비자 이전 결정 | Playwright 소비자 inventory 0 또는 명시적 opt-in |
| P5 | 설치 스크립트에서 Playwright/Chromium 기본 설치 제거 | clean install·upgrade·uninstall 검증 통과 |
| P6 | optional driver로 격리 또는 완전 제거 결정 | 유지 비용과 실제 사용 근거 검토 |

### 12.3 제거 게이트

다음 조건이 모두 충족되기 전에는 기본 설치를 제거하지 않는다.

- §8.5의 macOS·Linux·Windows 필수 matrix가 모두 통과
- 각 headless 환경에서 pinned standalone agent-browser 최소 E2E suite 통과
- `playwright-tool`과 `opal-wtm-agent` fallback 이전 완료
- Playwright MCP 자동 등록 정책 이전 완료
- install/update/doctor 문서와 진단 로직 갱신
- 기존 Playwright cache 제거가 사용자 소유 자산을 삭제하지 않도록 migration 제공

제거 이후에도 사용자가 명시적으로 선택하는 `browser.playwright` optional driver는 일정 기간 유지할 수 있다.

---

## 13. 도입 순서

### Phase 1 — false positive 차단

- 현재 fallback 요청을 pass로 취급하지 않도록 상태 계약을 수정한다.
- cmux open·navigate만으로 pass가 되지 않게 assertion gate를 추가한다.
- 기존 E2E 호출자의 기대 상태와 회귀 테스트를 정비한다.

### Phase 2 — Runtime Manager

- source-main/source-worktree/installed target을 분리한다.
- API base URL, frontend/backend port, CORS를 runtime env로 주입한다.
- port lease, health, PID/process group, log, cleanup을 구현한다.
- 기본 7823 daemon 비간섭 테스트를 추가한다.

### Phase 3 — agent-browser 공용 driver·Orca 최적화

- agent-browser 공용 driver와 `orca-managed`/`standalone` session resolver를 구현한다.
- Orca worktree 선택과 typed/exec capability probe를 구현한다.
- snapshot/action/re-snapshot과 stale ref 방지를 적용한다.
- screenshot과 probe된 optional 증적을 연결한다.
- Orca가 없는 환경의 `provider_unavailable`을 검증한다.

### Phase 4 — 다중 driver/session

- cmux adapter를 공통 계약으로 이전한다.
- 같은 agent-browser adapter의 standalone mode로 로컬·CI fallback을 확립한다.
- 동일 시나리오의 driver/session conformance suite를 실행한다.

### Phase 5 — Playwright 기본 설치 제거

- E2E 외 소비자를 이전한다.
- requirements, install script, MCP, docs, doctor를 갱신한다.
- clean install과 upgrade migration을 검증한 뒤 default dependency에서 제거한다.

---

## 14. 구현 태스크 분리 제안

| 순서 | 태스크 | 주요 범위 | 독립 완료 기준 |
|---:|---|---|---|
| 1 | E2E verdict 정합성 | `test-tool`, tests | 실행 없는 fallback과 assertion 없는 navigate가 pass 불가, 신규 상태↔exit code 보존 |
| 2 | Console runtime 설정화 | Console FE/BE | 동적 port/API URL/CORS로 source server 병렬 실행 |
| 3 | E2E Runtime Manager | harness/tool | target별 start-health-stop와 소유권 기반 cleanup |
| 4 | Driver·session contract | harness/tool/schema | 공통 상태·capability·evidence·wait_kind·legacy migration 계약 검증 |
| 5 | agent-browser 공용 driver | adapter/tests/CI | Orca-managed와 standalone이 하나의 adapter로 real-usage E2E 통과 |
| 6 | cmux driver 이전 | adapter/tests | mode A/B/C 소유권 유지 + semantic assertion |
| 7 | Playwright 기본 설치 제거 | WTM/MCP/install/docs | 모든 소비자 이전 및 clean install 회귀 통과 |

태스크 1~4는 계약과 기반 작업이므로 선행한다. agent-browser driver에서 Orca-managed mode를 가장 먼저 완성하되, Runtime Manager 없이 driver부터 연결하면 설치본이나 다른 worktree를 잘못 검증할 위험이 있으므로 순서를 바꾸지 않는다.

---

## 15. 수용 기준

이 제안의 구현 완료는 다음 관찰 가능한 결과로 판정한다.

1. main과 두 개 이상의 worktree E2E를 동시에 실행해도 포트와 서버가 충돌하지 않는다.
2. 각 run이 자신이 검증한 source root, URL, process, browser session을 증적으로 남긴다.
3. 사용자가 실행 중인 `127.0.0.1:7823` Console과 사용자 소유 browser surface가 영향받지 않는다.
4. 실행 중 Orca runtime과 target worktree가 있을 때만 `orca-managed` mode로 대상 worktree의 embedded browser를 사용한다.
5. Orca runtime 부재는 `provider_unavailable`로 분류되어 cmux-owned 또는 agent-browser standalone mode로 전환된다.
6. assertion 실패는 다른 driver/session 결과로 덮어쓰지 않고 최종 fail로 남는다.
7. assertion 또는 필수 증적이 빠진 실행은 pass가 될 수 없다.
8. standalone agent-browser가 Orca runtime 없이 §8.5의 지원 OS·CI matrix에서 실제 E2E를 통과한다.
9. Playwright 기본 설치 제거 후 web-to-markdown, MCP, install/update 경로의 회귀가 없다.
10. 실패 run만으로도 공통 필수 증적과 해당 session이 제공하는 진단 증적에서 원인을 추적할 수 있다.

---

## 16. 결정 제안

다음 방향을 채택안으로 제안한다.

1. **Orca-first session, shared agent-browser driver**: Orca-managed와 standalone에 중복 adapter를 만들지 않는다.
2. **source server isolation 우선**: browser adapter보다 Runtime Manager와 동적 포트 계약을 먼저 구현한다.
3. **standalone session을 최종 기본 fallback으로 채택**: 같은 agent-browser driver가 Orca·cmux 없는 환경을 담당한다.
4. **Playwright 기본 설치는 단계적 제거**: 지원을 즉시 삭제하지 않고 모든 소비자 이전 뒤 opt-in으로 전환한다.
5. **증거 없는 pass 금지**: 실제 assertion과 증적을 `real-usage` 판정의 필수 조건으로 집행한다.

이 제안이 승인되면 구현 단계에서는 태스크 1~7을 한 번에 묶지 않고, verdict 정합성 → runtime isolation → agent-browser 공용 driver 순으로 작은 독립 태스크를 생성한다.
