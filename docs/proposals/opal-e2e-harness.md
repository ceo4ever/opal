<!--
@header {
  "module": "opal-e2e-harness-proposal",
  "layer": "spec",
  "domain": "opal-tools",
  "description": "Browser·API·Hybrid·사용자 협업형 E2E의 실행 격리, 판정, 증적 및 driver 이행 계약 제안",
  "exports": ["E2E profile 계약", "Runtime Manager 계약", "Browser driver·session 계약", "Playwright 제거 게이트"]
}
-->

# OPAL 범용 E2E 하네스 설계 제안서

> 상태: 검토
> 진행: 구현 태스크 1/9 완료 — 태스크 125 `E2E profile·verdict 계약`; 태스크 2~9 미착수
> 선행본: `docs/proposals/archives/opal-agent-browser-e2e-harness.md`를 범용 E2E 계약으로 확장·대체
> 작성: 알투(PM)
> 작성일: 2026-09-12
> 목적: main repo와 worktree의 실제 소스를 격리 실행하고 Browser·API·Hybrid·사용자 협업형 E2E를 공통 판정·증적 계약으로 수행하는 하네스 제안
> 범위: 방향과 핵심 계약을 정하는 제안서. 구현 계획(PLAN), 코드 변경, Playwright 제거 실행은 포함하지 않는다.

---

## 1. 제안 요약

OPAL의 E2E는 브라우저 자동화가 아니라 **공개 진입점에서 실제 시스템 결과까지 이어지는 사용자 목표 검증**이다. 공개 진입점은 Browser, API, CLI 또는 사람의 조작일 수 있다. 따라서 다음 세 책임을 분리한다.

1. **SUT Harness**: 검증할 소스 트리에서 서버를 기동하고 health, 포트, 프로세스, 로그를 관리한다.
2. **Scenario Orchestrator**: 요구사항의 실제 표면을 기준으로 Browser·API·Hybrid·Collaborative·Manual 실행 profile을 선택하고 순서를 제어한다.
3. **Executor**: Browser Driver, API Client, Human Handoff가 action·assertion·증적을 각자의 방식으로 수행한다.

| profile | 공개 진입점 | 대표 실행 |
|---|---|---|
| `browser` | 사용자가 보는 UI | Browser action → UI assertion |
| `api` | 외부 HTTP API | HTTP request → response·후속 상태 assertion |
| `hybrid` | UI와 API가 연결된 흐름 | API setup → Browser 핵심 행동 → API/state 검증 |
| `collaborative` | 자동화와 사람 조작이 함께 필요한 흐름 | Agent action → human handoff → resume → verifier |
| `manual` | 자동화할 수 없는 실제 사용자 흐름 | Human action → 구조화 증적 → verifier |

Browser profile에서는 Orca와 standalone agent-browser를 별도 provider로 만들지 않는다. Orca 앱은 `agent-browser` 실행 파일을 번들하고 `orca exec --command "<agent-browser command>"` 경로를 제공하므로, 둘은 같은 driver의 세션 소유권 모드로 취급한다.

```text
Browser profile 후보:
agent-browser / orca-managed
  → cmux / owned surface
  → agent-browser / standalone
  → Playwright(optional compatibility)
```

Orca가 관리하는 작업에서는 worktree-scoped 세션을 1순위로 사용한다. API profile은 브라우저를 설치하지 않는다. Collaborative profile은 사용자 응답을 기다리는 실행 상태를 보존하고 같은 run을 재개한다.

```text
실행 컨텍스트 결정
  → 전용 포트 임대
  → 선택한 소스 트리에서 SUT 기동
  → health gate
  → scenario profile·executor 결정
  → action → assertion 또는 human handoff/resume
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

### 2.5 Browser 외 E2E 계약 공백

현행 `test-tool integration`은 `e2e`와 `api_db` 필드를 갖지만 실행 어댑터는 Browser fallback에 집중되어 있다. API-only E2E의 request/response·후속 상태 계약, Browser와 API를 잇는 Hybrid 순서, 사용자 handoff의 pause/resume 계약은 없다.

이 공백을 두면 UI 요구사항을 API 호출만으로 통과시키거나, 사용자의 MFA·OAuth 완료 응답을 검증 없이 pass로 승격시키는 반대 방향의 false positive가 생긴다. 따라서 Browser Driver 개선은 범용 E2E Orchestrator 아래에서 수행해야 한다.

---

## 3. 목표와 비목표

### 3.1 목표

- main과 worktree의 **실제 변경 소스**를 검증한다.
- 여러 worktree가 동시에 E2E를 수행해도 서버·포트·브라우저 상태가 충돌하지 않는다.
- Browser·API·Hybrid·Collaborative·Manual E2E를 하나의 시나리오·판정·증적 모델로 관리한다.
- 요구사항의 공개 표면과 일치하는 executor를 선택해 낮은 충실도의 우회 검증을 차단한다.
- Orca-managed 세션에 최적화하되 새로운 브라우저 실행기는 driver 또는 session mode로 수용한다.
- TEST-SCENARIO의 사용자 행동과 기대 결과를 UI·HTTP response·외부 상태·사람 증적에 맞는 assertion으로 검증한다.
- 재현 가능한 공통 증적과, 실행 mode가 지원하고 시나리오가 요구한 `screenshot`·`console`·`errors`·`network_har` 증적을 남긴다.
- driver/session 부재와 제품 실패를 구분해 잘못된 fallback을 차단한다.
- Playwright의 기본 설치 비용을 최종적으로 제거한다.

### 3.2 비목표

- Playwright 또는 각 브라우저 제품의 기능을 OPAL 내부에서 재구현하지 않는다.
- 모든 driver/session mode의 고유 기능을 최소 공통 기능으로 제한하지 않는다.
- 사용자가 실행 중인 브라우저 탭, cmux surface, Orca worktree, Console daemon을 임의로 정리하지 않는다.
- UI 요구사항을 API-only 실행으로 대체하거나 API 요구사항에 불필요한 Browser를 강제하지 않는다.
- 사람의 단순 완료 응답을 결정론적 assertion이나 필수 증적의 대체물로 인정하지 않는다.
- 이번 제안에서 기존 `TEST-SCENARIO.md`나 `test-scenario.json` 스키마를 즉시 교체하지 않는다.
- 브라우저 driver 선택만으로 테스트 서버의 생명주기 문제를 해결했다고 간주하지 않는다.

---

## 4. 설계 원칙

### 4.1 서버와 executor의 소유권을 분리한다

SUT Harness가 서버 생명주기와 target URL을 소유하고 executor는 전달받은 endpoint만 사용한다. Browser Driver나 API Executor가 임의로 main daemon을 찾거나 서버를 기동하지 않는다. 각 executor는 자신이 생성한 browser session, API fixture, human handoff만 소유한다.

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
- 시나리오가 요구하고 실행 mode가 제공하는 `console`·`errors`·`network_har` 검사 통과

Driver가 `open`, `navigate`, `snapshot`만 수행한 결과는 pass가 아니다.

### 4.5 fallback은 capability 부재에만 허용한다

현재 실행 mode에서 제품 동작 실패, assertion 실패, 인증 실패, 데이터 불일치가 발생하면 다른 mode로 재시도해 성공으로 덮지 않는다. 다음 후보 전환은 `provider_unavailable`일 때만 허용한다.

### 4.6 소유한 자원만 정리한다

하네스가 생성한 PID/process group, browser tab/session/profile, cmux surface, API fixture, 포트 lease만 종료한다. 광범위한 `pkill`, 사용자 소유 surface, 외부 API 데이터의 임의 정리는 금지한다.

비간섭은 양방향이다. E2E가 사용자 `7823` Console을 종료해서도 안 되고, 사용자가 `opal-cli console stop`을 실행해도 E2E backend가 종료되어서는 안 된다. 따라서 Console stop은 process pattern이 아니라 `$OPAL_HOME`별 PID file과 실행 identity를 확인해 해당 배포 daemon만 종료해야 한다.

### 4.7 공통 계약과 확장 capability를 함께 둔다

공통 시나리오는 표준 driver contract로 실행한다. capability는 `native`, `exec`, `none` 실행 경로와 probe 결과를 함께 선언하고, 시나리오가 필요로 할 때만 요구한다. Orca의 `console`·`errors`·`network_har` 지원은 네이티브라고 가정하지 않고 `orca exec` 경유 명령을 실제 probe한 경우에만 활성화한다.

### 4.8 요구사항의 공개 표면이 profile을 결정한다

도구 가용성이 아니라 검증하려는 사용자 계약이 실행 profile을 결정한다.

- 사용자가 UI에서 수행해야 하는 요구사항은 `browser` 또는 `hybrid`여야 한다.
- API가 공식 제품 표면인 요구사항은 `api`만으로 E2E가 성립할 수 있다.
- Hybrid에서 API는 setup·cleanup·교차 검증에 사용할 수 있지만 핵심 UI 행동을 대체하면 안 된다.
- MFA·OAuth 승인·실물 기기·주관적 육안 판단처럼 자동화할 수 없는 단계가 있을 때만 `collaborative` 또는 `manual`을 사용한다.

### 4.9 사람 협업은 실행 상태이며 최종 verdict가 아니다

사람의 입력을 기다리는 동안 run은 `awaiting_human` 상태로 일시 정지한다. 이는 `pass/fail/blocked`와 같은 최종 판정이 아니다. handoff가 요구한 입력과 증적이 돌아오면 동일한 run-id와 resume token으로 재개해 verifier가 최종 상태를 결정한다.

---

## 5. 제안 아키텍처

### 5.1 구성요소

| 구성요소 | 책임 | 소유하지 않는 것 |
|---|---|---|
| E2E Orchestrator | run 생성, target/profile/executor 결정, 단계 제어, 최종 verdict | executor별 명령 구현 |
| Runtime Manager | 포트 임대, env 구성, 서버 기동·health·로그·종료 | 사용자 daemon |
| Profile Resolver | 요구사항 표면으로 Browser·API·Hybrid·Collaborative·Manual 선택 | 가용 도구에 맞춘 충실도 하향 |
| Scenario Adapter | TEST-SCENARIO를 actor별 action/assertion/handoff로 정규화 | 실제 action 수행 |
| Browser Session Resolver | `orca-managed`, `cmux-owned`, `standalone` 후보 탐지와 소유권 확정 | 제품 성공 판정 |
| Browser Driver | agent-browser·cmux·Playwright 명령 변환과 결과 정규화 | API·사람 단계 실행 |
| API Executor | HTTP request, auth, response·후속 상태 assertion | UI 행동 대체 |
| Human Handoff | 사용자 작업 요청, pause·resume token, 제출 증적 정규화 | 사용자 응답만으로 pass 선언 |
| Evidence Collector | 공통·Browser·API·Human 증적 수집 | 제품 성공 추정 |
| Verdict Gate | assertion·증적·오류를 종합해 상태 결정 | 다음 실행 후보 선택 |

기존 `test-tool`은 E2E Orchestrator의 결정론적 진입점으로 확장하는 안을 우선한다. 별도 도구는 책임 분리가 실제로 필요하다는 구현 분석 결과가 있을 때만 신설한다.

### 5.2 실행 상태 머신

```text
created
  → context_resolved
  → ports_leased
  → sut_starting
  → sut_ready
  → profile_resolved
  → executor_ready
  → scenario_running
  → awaiting_human → scenario_running
  → evidence_captured
  → pass | fail | executor_unavailable | blocked | infra_error
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
│   ├── errors.jsonl
│   └── network.har
├── api/
│   ├── requests.jsonl
│   └── responses.jsonl
├── human/
│   ├── handoff.json
│   └── submission.json
└── screenshots/
    └── {scenario-id}-{step}.png
```

실행 증적은 기본적으로 repository 밖의 OS 임시 디렉터리에 저장한다. 태스크 안에 보존해야 하는 요약 증적만 명시적으로 복사한다. repository 내부 `.e2e-runs/` 또는 `.test-run/`을 지원한다면 구현과 같은 변경에서 `.gitignore`를 함께 갱신해 untracked 오염을 차단한다.

시나리오 capability와 artifact의 대응은 `console` → `console.jsonl`, `errors` → `errors.jsonl`, `network_har` → `network.har`로 고정한다.

---

## 6. 서버 실행 모델

### 6.1 `source-main`

- main repo의 backend와 frontend를 별도 임대 포트에서 기동한다.
- 사용자 설치본 `7823` daemon은 그대로 둔다.
- `opal-cli console stop`이 source E2E backend를 종료하지 않도록 배포 daemon과 E2E process identity를 분리한다.
- dirty working tree 여부와 변경 파일을 run metadata에 기록한다.
- 개발 서버 또는 production preview 중 어떤 경로를 사용할지는 시나리오 profile로 명시한다.

### 6.2 `source-worktree`

- worktree-tool이 발급한 canonical `worktree_root`에서 서버를 기동한다.
- dependency setup도 해당 worktree 안에서 수행한다.
- 포트는 task 번호를 단순 가산해 추측하지 않고 run-time lease로 확정한다.
- Orca-managed mode의 격리 키는 `worktree scope + browserPageId + profile id`다. `--worktree <selector>`는 검색 범위이고 단독 격리 키가 아니다.
- run 시작 시 전용 tab/profile을 만들고 `orca tab list --json`에서 얻은 `browserPageId`를 모든 후속 명령의 `--page <id>`로 재사용한다.
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

source E2E의 기본 frontend는 Vite dev server이며 repository `dist/`를 만들지 않는다. production asset 검증이 필요한 별도 profile만 `vite build --outDir ${OPAL_E2E_ARTIFACT_DIR}/dist`를 사용하고 그 경로에서 preview한다. backend의 package-relative `../../dist`와 source tree의 공유 `dist/`에는 E2E 포트가 bake된 산출물을 쓰지 않는다. `installed` profile만 격리된 임시 `OPAL_HOME` 안의 배포 dist를 사용한다.

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

## 7. E2E Profile·Executor 계약

### 7.1 Profile 선택 계약

| requirement surface | 허용 profile | 금지되는 대체 |
|---|---|---|
| Web UI 사용자 행동 | `browser`, `hybrid` | API-only로 핵심 행동 우회 |
| 공개 HTTP API | `api`, 필요 시 `hybrid` | 이유 없는 Browser 강제 |
| UI 행동과 backend 결과 연결 | `hybrid` | Browser 또는 API 한쪽만 검증 |
| MFA·OAuth 승인·실물 기기 조작 | `collaborative` | 인증 우회·mock 승격 |
| 자동화 불가 전체 사용자 흐름 | `manual` | 자유 형식 완료 선언 |

Profile Resolver는 TEST-SCENARIO의 `surface_ref`, 요구사항 문구, 명시된 actor를 입력으로 사용한다. 적합한 executor가 없으면 충실도를 낮춰 실행하지 않고 `executor_unavailable`로 종료하거나, 사람 수행이 계약에 포함된 경우에만 `awaiting_human`으로 전환한다.

### 7.2 공통 시나리오 구조

```yaml
id: S-E2E-001
profile: hybrid
target: source-worktree
actors: [api, browser]
entrypoint: /projects
steps:
  - id: setup-project
    executor: api
    action: POST /api/projects/fixture
  - id: open-project
    executor: browser
    action: click
    target: "프로젝트 카드"
assertions:
  - verifier: ui
    visible_text: "프로젝트 개요"
  - verifier: response
    request: GET /api/projects/detail
    status: 200
evidence: [actions, assertions, after_snapshot, api_response]
```

각 step은 `executor=browser|api|human`을 명시한다. `profile`은 허용된 executor 조합과 충실도 규칙을 결정하고, executor 가용성이 profile을 역으로 바꾸지 않는다.

### 7.3 공통 Executor 인터페이스

| operation | 입력 | 최소 출력 |
|---|---|---|
| `probe` | runtime context, required capabilities | availability, version, capabilities |
| `prepare` | run-id, target, isolation key | owned handle, setup evidence |
| `act` | handle, typed action | action result, observed state |
| `assert` | handle, assertion | expected, actual, pass/fail |
| `capture` | handle, evidence spec | artifact paths, redaction result |
| `cleanup` | owned handle | cleanup result |

### 7.4 API Executor 계약

API Executor는 실제 SUT의 공개 HTTP endpoint를 호출한다. mock server로 대체한 결과는 E2E가 아니다.

- request method, URL, redacted headers/body, timeout을 action log에 기록한다.
- status, schema, response body의 필요한 필드와 후속 observable state를 assertion한다.
- retry는 명시된 일시적 transport 오류에만 적용하고 제품의 4xx/5xx를 숨기지 않는다.
- setup·cleanup API와 검증 대상 API를 구분해 핵심 행동 우회를 탐지한다.
- API가 생성한 fixture는 run-id로 namespace하고 owned resource만 정리한다.
- DB 직접 조회는 API 결과의 후속 state verifier로만 사용하며 공개 API 행동을 대체하지 않는다.

### 7.5 Collaborative·Manual 계약

사람 단계는 다음 구조화 handoff를 생성한다.

```yaml
handoff_id: H-001
actor: human
instruction: "브라우저에서 OAuth 동의를 완료하세요."
expected_observation: "OPAL Console로 redirect되고 프로젝트명이 표시됨"
required_evidence: [final_url, screenshot]
timeout_seconds: 600
resume_token: opaque-run-scoped-token
```

- `collaborative`는 자동화 가능한 전후 단계를 executor가 수행하고 사람에게 필요한 최소 단계만 넘긴다.
- `manual`도 자유 형식 응답 대신 instruction, expected observation, evidence, verifier를 가져야 한다.
- 대기 중에는 `awaiting_human`으로 pause하고 run journal을 저장한 뒤 process exit 20으로 호출자에게 제어를 돌려준다. 서버·lease 유지 또는 안전 종료 정책을 handoff에 기록한다.
- timeout은 자동 `fail`이 아니라 `blocked`로 종료하며 동일 resume token의 만료 여부를 기록한다.
- 사용자 제출은 증적 입력일 뿐 pass 선언이 아니다. 가능한 assertion은 deterministic verifier가 다시 확인한다.
- 재개는 `resume --run-id <id> --token <token> --submission <path>` 형태의 결정론적 입력 계약을 사용한다.

### 7.6 Browser Driver 공통 인터페이스

| operation | 입력 | 최소 출력 |
|---|---|---|
| `probe` | runtime context | driver, session mode, availability, version, capability routes |
| `open` | URL, isolation key | owned browser/session handle |
| `snapshot` | handle | 구조화 snapshot, current URL |
| `act` | handle, action | action 결과, 변경된 URL |
| `wait` | handle, condition | 충족 여부, elapsed time |
| `assert` | handle, assertion | expected, actual, pass/fail |
| `capture` | handle, evidence spec | artifact paths, `console`·`errors`·`network_har` |
| `close` | owned handle | cleanup 결과 |

구현 언어의 클래스나 프로토콜을 먼저 확정하지 않는다. 우선 JSON 입출력 계약을 고정하고 기존 shell/Python 도구가 이를 소비하도록 한다.

### 7.7 capability와 실행 경로 probe

```json
{
  "driver": "agent-browser",
  "session_mode": "orca-managed",
  "capabilities": {
    "snapshot": {"available": true, "route": "native"},
    "screenshot": {"available": true, "route": "native"},
    "console": {"available": false, "route": "exec", "probed": false},
    "errors": {"available": false, "route": "exec", "probed": false},
    "network_har": {"available": false, "route": "exec", "probed": false},
    "isolated_profile": {"available": true, "route": "native"}
  }
}
```

`route=native`는 현재 Orca CLI의 typed command가 실제 존재할 때만 사용한다. `route=exec`는 `orca exec --command`로 해당 agent-browser 명령을 비파괴 probe해 성공한 경우에만 `available=true`가 된다. help 문자열이나 번들 파일 존재만으로 실행 capability를 추정하지 않는다.

`probed=false`인 optional capability는 보수적으로 `available=false`다. agent-browser가 `console`·`errors`·`network_har` 명령을 제공하더라도 현재 Orca page에 대한 `orca exec` 경유 probe가 성공하기 전에는 증적 capability로 승격하지 않는다.

시나리오가 요구한 capability가 없으면 해당 실행 후보는 실행 전에 `provider_unavailable`을 반환한다. 단, tested range 밖 binary의 호환성 probe 실패는 §8.3에 따라 `infra_error`다. 실행 중 assertion이나 필수 증적을 생략해 capability 부족을 보정하지 않는다.

### 7.8 결과와 실행 상태

`awaiting_human`은 pause/resume을 위한 operational state다. run journal과 resume token을 보존하고 exit 20(`e2e_awaiting_human`)으로 반환하며 성공으로 취급하지 않는다. 최종 결과는 아래 다섯 상태 중 하나다.

| 상태 | 의미 | fallback |
|---|---|:---:|
| `pass` | 모든 assertion과 증적 조건 통과 | 불필요 |
| `fail` | 제품 동작 또는 assertion 실패 | 금지 |
| `executor_unavailable` | 필수 executor 또는 모든 허용 후보 부재 | 금지 |
| `infra_error` | 서버, 포트, 브라우저 crash, 증적 저장 등 인프라 실패 | 기본 금지 |
| `blocked` | 인증·외부 승인·사람 입력 등 자동 진행 불가 | 금지 |

`infra_error`를 다음 실행 mode로 전환할지는 오류별 정책으로 명시하되 기본값은 금지한다. mode를 바꾸면 재현 조건도 달라지므로 자동으로 제품 성공으로 해석할 수 없기 때문이다.

Browser Driver 내부의 `provider_unavailable`은 다음 browser 후보를 선택하기 위한 중간 결과다. 모든 후보가 소진되면 상위 E2E Orchestrator가 최종 `executor_unavailable`로 변환한다.

### 7.9 현행 상태 마이그레이션

기존 `status=escalated`와 `escalate=true`는 신규 상태가 정착될 때까지 입력 호환만 제공하고 결과 계약에서는 제거한다.

| 현행 경로·error | 신규 상태 | fallback | 비고 |
|---|---|:---:|---|
| `fallback` + `not_in_cmux` | Browser 후보 `provider_unavailable` | 허용 | cmux runtime context 부재 |
| `fallback` + `cmux_not_installed` | Browser 후보 `provider_unavailable` | 허용 | cmux capability 부재 |
| `fallback` + `open_failed` | `infra_error` | 금지 | 가용 provider의 runtime/open 실패 |
| `fallback` + `surface_parse_failed` | `infra_error` | 금지 | 가용 provider의 출력 계약 파손 |
| `has_cmux=false` legacy 분기 | `infra_error` | 금지 | 호출 시점의 runner 설정 누락. 후보 미선택은 상위 resolver가 호출 전에 처리 |
| `escalated` + `usage` | `infra_error` | 금지 | 호출자 계약 오류 |
| `escalated` + `invalid_surface` | `infra_error` | 금지 | session handle 오류 |
| `escalated` + `goto_failed` | `infra_error` | 금지 | URL·navigation 실행 오류. 제품 assertion 실패와 분리 |
| `escalated` + `wait_failed` | `infra_error` 또는 `fail` | 금지 | error code가 아니라 하네스가 기록한 `wait_kind`로 판정 |
| `escalated` + `eval_failed` | `infra_error` | 금지 | driver 명령 실행 오류 |
| 알 수 없는 error code | `infra_error` | 금지 | fail-safe 기본값. 신규 코드의 자동 fallback 금지 |
| reason 없는 generic `fallback` | `infra_error` | 금지 | 성격을 증명할 수 없으므로 capability 부재로 간주하지 않음 |

`wait_failed`는 cmux-tool의 단일 error code만으로 원인을 나눌 수 없다. 하네스가 wait을 발행할 때 `wait_kind=navigation_ready|transport|assertion_condition`을 action log에 기록하고, 앞의 두 종류는 `infra_error`, semantic assertion condition timeout은 `fail`로 판정한다. `wait_kind`가 없는 legacy 결과는 fail-safe로 `infra_error`다. 기존 `FALLBACK_CODES` 집합은 폐기하고 reason별 위 표를 결정론적으로 적용한다.

#### 신규 상태와 process exit code

| 신규 상태 | process exit code | 공개 error | 처리 |
|---|---:|---|---|
| `pass` | 0 | 없음 | 성공 종료 |
| `fail` | 6 | `e2e_failed` | 기존 E2E 실패 코드 유지 |
| `executor_unavailable` | 18 | `executor_unavailable` | Browser 후보 `provider_unavailable`은 내부 상태이며 process를 종료하지 않음 |
| `infra_error` | 7 | `e2e_infra_error` | 기존 escalation exit 7을 일반화해 호환 유지 |
| `blocked` | 19 | `e2e_blocked` | 사람 입력·인증·외부 승인 필요 |

operational `awaiting_human`에는 exit 20과 `e2e_awaiting_human`을 배정한다. 현재 사용 중인 exit code는 0~14·16·17이며, 15는 기존 범위의 예약 결번으로 재사용하지 않는다. 신규 상태는 현재 최댓값 17 다음인 18~20에 배정한다. 기존 테스트는 한 번에 삭제하지 않는다. 먼저 legacy 입력 → 신규 상태·exit code 변환 테스트를 추가하고, `escalation` error는 이행기 alias로 exit 7을 유지한다. 모든 호출자가 신규 상태를 소비한 뒤 `escalate` boolean, `escalated` 문자열, `escalation` alias를 제거한다.

---

## 8. Driver·Session별 적용안

### 8.1 agent-browser driver — Orca-managed·standalone 공용

Orca 앱에 번들된 `agent-browser`와 standalone `agent-browser`는 하나의 driver adapter를 공유한다. 차이는 엔진이 아니라 session owner, 실행 route, worktree scope다.

| session mode | owner | isolation key | 명령 경로 |
|---|---|---|---|
| `orca-managed` | Orca worktree의 E2E run | `worktree + browserPageId + profile id` | typed Orca command 우선, 미지원 기능은 probe된 `orca exec` |
| `standalone` | E2E run | `session name + generated profile dir` | 직접 `agent-browser --session <run-id>` |

Orca-managed mode는 worktree별 Chromium과 탭 격리를 활용하므로 Orca 작업의 1순위다. standalone mode는 같은 driver 계약을 재사용해 별도 adapter 중복 없이 로컬·CI fallback을 담당한다.

적용 원칙:

- 모든 명령에 대상 worktree scope와 run 전용 `--page <browserPageId>`를 명시한다.
- profile create/set/clone/delete typed command로 run 전용 profile을 만들고 소유 profile id를 기록한다.
- `snapshot → act → re-snapshot` 순서를 지키고 navigation 뒤 오래된 ref를 재사용하지 않는다.
- E2E가 연 page와 profile만 닫고 같은 worktree의 다른 탭은 건드리지 않는다.
- Orca runtime이 없거나 대상 worktree를 찾지 못한 경우에만 다음 실행 후보로 전환한다.
- Orca GUI 조작이 아니라 embedded browser CLI 계약을 사용한다.
- `console`·`errors`·`network_har`는 Orca typed 지원으로 가정하지 않고 `orca exec` 경유 agent-browser probe 결과가 true일 때만 수집한다.
- Orca-managed session에 agent-browser launch-scope `--config`·`--allowed-domains`를 적용할 수 있는지는 E3에서 비파괴 probe로 확인한다. 확인 전에는 ambient config 격리를 보장하거나 pass 전제로 삼지 않고, 검증된 run 전용 page/profile을 session 격리 수단으로 사용한다.
- network 증적은 자체 JSONL보다 agent-browser의 `network har start|stop`이 만든 HAR를 기본 포맷으로 사용한다.
- `orca serve`는 headless Orca runtime 후보로 검증하되 Linux CI의 기본 전제로 두지 않는다.

출처: [Orca Browser overview](https://www.onorca.dev/docs/browser/overview), [Orca CLI reference](https://www.onorca.dev/docs/cli/reference)

실측 근거: 현재 macOS Orca 앱에 `/Applications/Orca.app/Contents/Resources/agent-browser-darwin-arm64`가 존재하며 agent-browser `0.27.0`으로 확인됐다. Orca CLI `1.4.200` 기준 Browser Automation typed command에는 `tab profile create|delete|set|show|clone|use-default`, `screenshot`, `eval`, `wait`, `set headers|credentials`가 있고 Browser Options에는 `--page <id>`·`--profile <id>`·`--worktree <selector>`가 있다. CLI는 동시 실행에서 `tab list --json`의 `tabs[].browserPageId`를 `--page`로 재사용하도록 안내한다. `orca exec`의 유효 flag는 `--command`, `--environment`, `--json`, `--page`, `--pairing-code`, `--worktree`이며 `console`·`errors`·`network_har`에 대응하는 typed command는 확인되지 않았다(2026-09-12 로컬 실측).

### 8.2 cmux driver — 2순위

기존 `cmux-tool`의 JSON error code와 mode A/B/C 소유권 모델을 재사용한다. 자동 E2E 기본은 하네스가 surface를 열고 닫는 mode A로 제한한다. 사용자 소유 surface를 재사용하는 mode B/C는 명시적 interactive run에서만 허용한다.

보강해야 할 부분:

- open·navigate 성공을 pass로 보지 않는다.
- snapshot 기반 action과 시나리오 assertion을 필수화한다.
- `screenshot`·`console`·`errors`·`network_har`를 제공하지 못하는 경우 해당 capability에 `none`을 명시한다.
- `user_owned=true`인 surface는 cleanup하지 않는다.

### 8.3 standalone session — 기본 headless fallback

standalone mode는 §8.1과 같은 agent-browser driver를 직접 실행한다. `agent-browser`는 CLI와 daemon 구조로 브라우저를 제어하고, snapshot ref 기반 agent workflow를 지원한다. Playwright Python package 없이 동작하며 Chrome for Testing 설치 또는 기존 Chrome 계열 브라우저 탐지를 지원하므로 Orca·cmux가 없는 환경의 fallback으로 적합하다.

바이너리는 다음 순서로 해석한다.

```text
1. PATH의 agent-browser
2. 현재 OS·architecture와 일치하는 Orca bundle
3. OPAL managed cache의 CI-pinned agent-browser
4. 모두 없을 때만 CI-pinned version 신규 설치
```

버전 SSOT는 driver manifest 한 곳에 `minimum_version`, `tested_range`, `ci_pin`을 둔다. 초기 기준은 실측 bundle을 따라 minimum `0.27.0`, tested range `0.27.x`, CI pin `0.27.0`으로 시작한다. `minimum_version` 미만 binary는 capability probe를 시도하지 않고 binary 후보에서 제외하며, 제외 사유와 version을 run metadata에 기록한다. 이는 실행 전 binary 해석 단계의 후보 제외이지 실행 실패 fallback이 아니다. 모든 binary 후보가 이 사유로 소진되면 상위 Orchestrator가 최종 `executor_unavailable`로 판정한다. PATH·Orca bundle이 minimum 이상이지만 tested range 밖이면 후보를 탈락시키지 않고 warning과 version metadata를 남긴 뒤 필수 capability probe로 판정한다. **tested range 밖 binary에 한해** probe 실패를 호환성 `infra_error`로 승격하고 다음 후보로 조용히 fallback하지 않는다. range 안 binary의 capability probe 실패는 §7.7과 §11에 따라 해당 Browser 후보의 `provider_unavailable`로 처리한다. OPAL managed cache와 CI만 `ci_pin`을 exact 적용하고 자동 upgrade하지 않는다.

적용 원칙:

- run-id 기반 named session/profile로 실행을 격리한다.
- `${OPAL_E2E_ARTIFACT_DIR}/agent-browser.json`을 생성하고 항상 `--config <absolute-path>`로 지정해 사용자·worktree의 ambient config 자동 탐색을 차단한다.
- child env에서는 기존 `AGENT_BROWSER_*` 설정을 제거한 뒤 하네스가 소유한 값만 주입하고, CLI `--allowed-domains`를 임대한 localhost와 시나리오가 선언한 외부 origin으로 제한한다.
- 선택된 binary path·version·해석 source를 run metadata에 기록한다.
- PATH 또는 Orca bundle이 minimum·capability probe를 충족하면 OPAL binary를 추가 설치하지 않는다.
- CI에서는 고정 버전과 cache 정책을 사용한다.
- session 종료가 해당 run에만 영향을 주는지 adapter 테스트로 검증한다.

출처: [agent-browser 공식 README](https://github.com/vercel-labs/agent-browser/blob/main/README.md), [agent-browser 설치 문서](https://github.com/vercel-labs/agent-browser/blob/main/docs/src/app/installation/page.mdx)

### 8.4 Playwright — 이행기 optional driver

Playwright는 곧바로 삭제하지 않는다. 제거 inventory는 다음 9개 migration area를 전수 기준으로 사용한다.

| area | 현재 소비자 | 이전 시 확인할 계약 |
|---:|---|---|
| 1 | `test-tool/lib/e2e_adapter.py` | fallback·verdict 실행 경로 |
| 2 | `test-tool/lib/resolver.py`, `test-tools-schema.yaml` | L3b runner 우선순위·설정 스키마 |
| 3 | `playwright-tool/` | web 수집 CLI 기능 대체 또는 opt-in 격리 |
| 4 | `opal-wtm-agent` | cmux→Playwright fallback을 새 driver 정책으로 이전 |
| 5 | `core/mcps/playwright.json`, 플랫폼 MCP 등록 | MCP 정의·설치·cache 소유권 |
| 6 | `requirements.txt`, install script | Python package·Chromium·cache 설치 제거 |
| 7 | `doctor/` | dependency와 공식 MCP 진단 오탐 제거 |
| 8 | oppl `verification.md`·`journey-flow.md`, oppd `verification-loop-guide.md` | L3b·real-usage 실행 규정의 경쟁 SSOT 제거 |
| 9 | `core/references/tools.md`·`agents.md`·`mcps.md`·관련 registry | 사용자 문서·catalog·예시 정합성 |

특히 `real-usage`의 의미는 `test-tool` fidelity 계약이 소유하고, pilot 문서는 해당 계약을 참조만 해야 한다. “cmux 우선/playwright 폴백”은 driver 선택 정책이지 fidelity 정의가 아니므로 oppl·oppd 문서에서 정의 문구를 제거한다. community skill의 Playwright 항목은 외부 선택지 catalog이므로 기본 설치 소비자와 구분해 유지·수정·삭제를 별도 판단한다.

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

### 9.1 Profile별 assertion

| profile | 최소 assertion | 보조 assertion |
|---|---|---|
| `browser` | 사용자에게 보이는 UI 상태·URL·상호작용 결과 | `console`·`errors`·`network_har` |
| `api` | HTTP status·response schema·필수 body 값 | 후속 API·DB state |
| `hybrid` | 핵심 UI 결과와 연결된 API/state 결과 모두 | `console`·`errors`·`network_har` |
| `collaborative` | 사람 단계 이후 자동 확인 가능한 최종 상태 | 사용자 제출 screenshot·URL |
| `manual` | 구조화 expected/actual과 독립 검토 결과 | screenshot·recording |

YAML 예시는 §7.2가 소유한다. 기존 JSON SSOT와 실제 필드 매핑은 구현 PLAN에서 확정한다.

### 9.2 assertion 우선순위

1. 요구사항의 공개 표면에서 직접 관찰되는 결과
2. 같은 실행에서 발생한 후속 observable state
3. 구현 내부 상태는 앞의 결과를 보강할 때만 사용
4. Browser의 DOM/CSS selector나 API의 DB 직접 조회는 공개 결과를 표현할 방법이 없을 때만 사용

AI agent나 사용자가 “정상으로 보인다”고 서술하는 것은 assertion이 아니다. executor 종류와 무관하게 expected와 actual이 구조화되어야 한다.

### 9.3 ref 수명

snapshot ref를 사용하는 driver는 navigation, click, rerender 뒤 ref가 무효가 될 수 있다. action 뒤 re-snapshot을 기본으로 하고, driver adapter가 오래된 ref 사용을 감지하면 `infra_error`가 아니라 해당 action 실패로 명확히 반환한다.

### 9.4 자동화율과 충실도를 분리한다

자동화가 많다고 E2E 충실도가 높은 것은 아니다. 요구사항의 실제 actor와 공개 표면을 그대로 통과했는지가 기준이다.

| 실행 | `real-usage` 가능 조건 |
|---|---|
| Browser | 실제 UI 핵심 행동과 semantic assertion 완료 |
| API | API가 요구사항의 공개 표면이고 실제 SUT·후속 상태 검증 완료 |
| Hybrid | 핵심 UI 행동을 우회하지 않고 API/state 교차 검증 완료 |
| Collaborative | 필요한 사람 단계와 자동 verifier, 필수 증적 완료 |
| Manual | 실제 사용자가 전체 경로를 수행하고 구조화 증적을 독립 검토 |

API로 UI 행동을 대체하거나 mock·설명만으로 사람 단계를 대체한 실행은 `real-usage`로 승격하지 않는다.

---

## 10. 증적과 판정 계약

### 10.1 `run.json` 최소 필드

```json
{
  "run_id": "e2e-20260912-001",
  "scenario_id": "S-E2E-001",
  "profile": "hybrid",
  "actors": ["api", "browser"],
  "target": "source-worktree",
  "project_root": "/path/to/project",
  "worktree_root": "/path/to/worktree",
  "executors": [
    {"type": "api", "client": "opal-http"},
    {
      "type": "browser",
      "driver": "agent-browser",
      "session_mode": "orca-managed",
      "driver_version": "resolved-at-runtime"
    }
  ],
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
  → profile별 executor probe
  → Browser 후보 미지원이면 다음 driver/session 후보
  → 필수 executor 전체 부재면 executor_unavailable
  → 지원 executor에서 시나리오 실행 또는 awaiting_human
  → 공통 필수 증적 + 시나리오 필수 증적 판정
  → 실패 시 제공 가능한 진단 증적을 best-effort 수집
```

| 증적 | 필수 수준 | 조건 |
|---|---|---|
| 실행 metadata | 공통 필수 | 모든 run |
| backend/frontend log | 공통 필수 | 서버를 하네스가 기동한 run |
| action log | 공통 필수 | 모든 executor step |
| assertion expected/actual | 공통 필수 | 모든 assertion |
| API request/response | profile 필수 | `api`·`hybrid`의 HTTP step. secret은 redaction |
| human handoff/submission | profile 필수 | `collaborative`·`manual`의 사람 step |
| 시작·종료 snapshot | 시나리오 필수 | UI 변경 시나리오가 `snapshot`을 요구할 때 |
| screenshot | 시나리오 필수 또는 진단 best-effort | 시나리오가 요구하면 사전 probe 필수. fail/blocked/infra_error에서는 지원 시 수집하되 미지원 자체로 기존 실패 상태를 바꾸지 않음 |
| `console` | 시나리오 필수 | console capability probe가 성공하고 시나리오가 요구할 때 |
| `errors` | 시나리오 필수 | page error capability probe가 성공하고 시나리오가 요구할 때 |
| `network_har` | 시나리오 필수 | HAR capability probe가 성공하고 시나리오가 요구할 때 |
| cleanup 결과 | 공통 필수 | 모든 run |

공통 필수 증적은 metadata, server log, actor별 action log, assertion 결과, cleanup이다. Browser·API·Human 고유 증적은 profile 또는 시나리오의 `requires`에 선언된 경우 pass gate가 된다. `test-tool scenario-mark`의 `real-usage` 충실도는 실제 사용자 경로와 해당 run의 필수 증적이 확인된 뒤에만 기록한다.

### 10.3 민감정보 처리

- 인증 token, cookie, `Authorization`·`Cookie`·`Set-Cookie` header, query secret은 HAR을 포함한 모든 증적을 저장하기 전에 redaction한다.
- screenshot에 개인정보가 포함될 수 있는 시나리오는 masking 또는 별도 보존 정책을 적용한다.
- browser profile은 run 종료 후 삭제하며 사용자 profile을 재사용하지 않는다.
- raw network body는 기본 수집하지 않고 실패 분석에 필요한 allowlist endpoint만 선택한다.
- 필수 증적의 redaction 또는 안전한 저장에 실패하면 해당 증적을 원문으로 남기지 않고 run을 `infra_error`로 판정한다.

---

## 11. 오류와 fallback 정책

```text
profile resolve
  ├─ 필수 executor 없음          → executor_unavailable
  └─ 사람 단계가 계약에 포함됨    → awaiting_human → resume

Browser 후보 탐색·probe
  ├─ minimum_version 미만 binary → probe 없이 후보 제외·metadata 기록 → 다음 binary 후보
  │  └─ 같은 사유로 모든 binary 후보 소진 → executor_unavailable
  ├─ runtime/명령/capability 부재 → provider_unavailable → 다음 Browser 후보
  ├─ tested range 안 binary의 capability probe 실패 → provider_unavailable → 다음 Browser 후보
  ├─ tested range 밖 binary의 호환성 probe 실패 → infra_error → 중단
  └─ 설정·권한·계약 오류 → blocked 또는 infra_error → 중단

실행 시작 후 실패
  ├─ UI/API/state assertion 실패  → fail → 중단
  ├─ 제품 오류                    → fail → 중단
  ├─ Browser/API transport 오류   → infra_error → 중단·명시된 재시도만 적용
  ├─ 사람 handoff timeout         → blocked → resume 가능 상태 보존
  └─ 사용자 승인/로그인 불가       → blocked → 중단
```

같은 시나리오를 다른 executor/driver/session에서 진단 목적으로 다시 실행할 수는 있다. 다만 최초 실패를 덮어쓰지 않고 별도 run으로 저장하며, 최종 판정에 두 결과를 모두 표시한다. 요구사항 표면이 달라지는 profile 전환은 fallback이 아니라 별도 저충실도 진단 run이다.

---

## 12. Playwright 기본 설치 제거 전략

### 12.1 판단

**Playwright 기본 설치는 제거할 수 있지만 지금 즉시 제거하지 않는다.** agent-browser driver의 standalone session이 최종 fallback 역할을 검증하고 E2E 외 소비자를 모두 이전한 뒤 기본 설치에서 제외한다.

### 12.2 단계

| 단계 | 변경 | 완료 조건 |
|---|---|---|
| PW-1 | driver/session contract와 agent-browser 공용 adapter 도입 | Orca-managed real-usage E2E가 assertion+증적과 함께 통과 |
| PW-2 | cmux adapter를 같은 계약으로 이전 | 기존 mode 소유권·에러 코드 회귀 없음 |
| PW-3 | agent-browser standalone mode와 CI fallback 활성화 | Orca·cmux 없는 환경에서 같은 adapter로 실제 E2E 통과 |
| PW-4 | 9개 migration area 이전 결정 | Playwright 소비자 inventory 0 또는 명시적 opt-in |
| PW-5 | 설치 스크립트에서 Playwright/Chromium 기본 설치 제거 | clean install·upgrade·uninstall 검증 통과 |
| PW-6 | optional driver로 격리 또는 완전 제거 결정 | 유지 비용과 실제 사용 근거 검토 |

### 12.3 제거 게이트

다음 조건이 모두 충족되기 전에는 기본 설치를 제거하지 않는다.

- §8.5의 macOS·Linux·Windows 필수 matrix가 모두 통과
- 각 headless 환경에서 pinned standalone agent-browser 최소 E2E suite 통과
- `playwright-tool`과 `opal-wtm-agent` fallback 이전 완료
- `resolver.py`·test-tools schema의 runner 우선순위 이전 완료
- Playwright MCP 자동 등록 정책 이전 완료
- oppl·oppd의 L3b·real-usage 문구가 공통 fidelity 계약을 참조하도록 이전 완료
- install/update/doctor 문서와 진단 로직 갱신
- shared reference·catalog의 유지/수정/삭제 판정 완료
- 기존 Playwright cache 제거가 사용자 소유 자산을 삭제하지 않도록 migration 제공

제거 이후에도 사용자가 명시적으로 선택하는 `browser.playwright` optional driver는 일정 기간 유지할 수 있다.

---

## 13. 도입 순서

### E1 — false positive 차단

- Browser·API·Hybrid·Collaborative·Manual profile과 executor 선택 계약을 추가한다.
- 현재 fallback 요청을 pass로 취급하지 않도록 상태 계약을 수정한다.
- cmux open·navigate만으로 pass가 되지 않게 assertion gate를 추가한다.
- `awaiting_human` pause/resume과 최종 5상태·exit code 계약을 고정한다.
- 기존 E2E 호출자의 기대 상태와 회귀 테스트를 정비한다.

### E2 — Runtime Manager

- source-main/source-worktree/installed target을 분리한다.
- API base URL, frontend/backend port, CORS를 runtime env로 주입한다.
- port lease, health, PID/process group, log, cleanup을 구현한다.
- Console stop의 광역 process pattern 종료를 `$OPAL_HOME`별 PID file·실행 identity 확인으로 교체하고 양방향 비간섭 테스트를 추가한다.
- source E2E는 Vite dev를 기본으로 하고 production asset 검증은 artifact 전용 `dist`에서만 수행한다.

### E3 — Browser Executor·Orca 최적화

- agent-browser 공용 driver와 `orca-managed`/`standalone` session resolver를 구현한다.
- Orca worktree를 scope로 사용하고 run 전용 `browserPageId`·profile을 격리 키로 집행한다.
- typed/exec capability와 Orca-managed launch-scope 격리 가능 여부를 probe하고 결과를 metadata에 기록한다.
- standalone에는 explicit generated config·allowed domains를 집행하고 공통 version metadata 정책을 구현한다.
- snapshot/action/re-snapshot과 stale ref 방지를 적용한다.
- screenshot과 probe된 console·errors·HAR 증적을 redaction pipeline에 연결한다.
- Orca가 없는 환경의 `provider_unavailable`을 검증한다.

### E4 — 다중 driver/session

- cmux adapter를 공통 계약으로 이전한다.
- 같은 agent-browser adapter의 standalone mode로 로컬·CI fallback을 확립한다.
- 동일 시나리오의 driver/session conformance suite를 실행한다.

### E5 — API·Human Executor

- API request/response·후속 state assertion과 owned fixture cleanup을 구현한다.
- Hybrid profile의 API setup → Browser action → API/state verifier 연결을 구현한다.
- Collaborative·Manual handoff, timeout, resume token, 구조화 증적을 구현한다.
- API-only가 UI 요구사항을 통과하지 못하는 surface fidelity gate를 추가한다.

### E6 — Playwright 기본 설치 제거

- E2E 외 소비자를 이전한다.
- requirements, install script, MCP, docs, doctor를 갱신한다.
- clean install과 upgrade migration을 검증한 뒤 default dependency에서 제거한다.

---

## 14. 구현 태스크 분리 제안

| 순서 | 태스크 | 주요 범위 | 독립 완료 기준 |
|---:|---|---|---|
| 1 | E2E profile·verdict 계약 | `test-tool`, fidelity owner, pilot consumers, tests | 5개 profile, reason별 fallback, awaiting_human, 상태↔exit code, real-usage SSOT 정합 |
| 2 | Console runtime·process ownership | Console FE/BE, `console.sh` | 동적 port/API URL/CORS, 격리 dist, PID identity 기반 stop으로 양방향 비간섭 |
| 3 | E2E Runtime Manager | harness/tool | target별 start-health-stop와 소유권 기반 cleanup |
| 4 | Browser driver·session contract | harness/tool/schema | page/profile 격리, capability·HAR·wait_kind·legacy migration 계약 검증 |
| 5 | agent-browser 공용 driver | adapter/tests/CI | Orca-managed·standalone 공용 adapter, Orca launch-scope probe, standalone explicit config·allowed domains, version probe 통과 |
| 6 | cmux driver 이전 | adapter/tests | mode A/B/C 소유권 유지 + semantic assertion |
| 7 | API·Hybrid executor | adapter/tests | API E2E와 API setup→Browser→state 검증, UI 우회 금지 |
| 8 | Human handoff executor | harness/schema/tests | Collaborative·Manual pause/resume·증적·timeout 검증 |
| 9 | Playwright 기본 설치 제거 | 9개 migration area | 모든 소비자·경쟁 SSOT 이전 및 clean install 회귀 통과 |

태스크 1~4는 계약과 기반 작업이므로 선행한다. agent-browser driver에서 Orca-managed mode를 첫 실제 E2E executor로 완성한 뒤 API·Human executor를 같은 상위 계약에 연결한다. Runtime Manager 없이 executor부터 연결하면 설치본이나 다른 worktree를 잘못 검증할 위험이 있으므로 순서를 바꾸지 않는다.

---

## 15. 수용 기준

이 제안의 구현 완료는 다음 관찰 가능한 결과로 판정한다.

1. main·두 개 이상의 worktree·동일 worktree의 두 E2E run을 동시에 실행해도 port, page, profile, server가 충돌하지 않는다.
2. 각 run이 profile, actors, source root, URL, process, executor/session을 증적으로 남긴다.
3. E2E가 사용자 `127.0.0.1:7823` Console을 종료하지 않고, `opal-cli console stop`도 E2E backend를 종료하지 않는다.
4. Orca-managed run은 worktree scope 안에서 전용 `browserPageId`와 profile id를 사용하고 소유 page/profile만 정리한다.
5. Orca runtime 부재는 Browser 후보 `provider_unavailable`로 분류되어 cmux-owned 또는 agent-browser standalone mode로 전환된다.
6. assertion 실패는 다른 driver/session 결과로 덮어쓰지 않고 최종 fail로 남는다.
7. assertion 또는 필수 증적이 빠진 실행은 pass가 될 수 없다.
8. standalone agent-browser가 Orca runtime 없이 §8.5의 지원 OS·CI matrix에서 실제 E2E를 통과하고, tested range 밖 host version은 경고·probe 후 사용되며 조용히 fallback하지 않는다.
9. Playwright 기본 설치 제거 후 web-to-markdown, MCP, install/update 경로의 회귀가 없다.
10. 실패 run만으로도 공통 필수 증적과 `snapshot`·`console`·`errors`·`network_har` 등 해당 session의 진단 증적에서 원인을 추적할 수 있다.
11. 공개 API 요구사항은 Browser 없이 request/response와 후속 상태까지 실제 SUT에서 검증된다.
12. Hybrid profile은 핵심 UI 행동을 API로 우회하지 않고 UI 결과와 backend 상태를 함께 검증한다.
13. Collaborative·Manual run은 `awaiting_human`에서 같은 run으로 재개되고 사용자 완료 선언만으로 pass되지 않는다.
14. standalone agent-browser run은 explicit generated config와 allowed domains를 사용해 사용자·worktree ambient config 영향을 받지 않는다. Orca-managed run은 E3 probe 결과를 metadata에 남기고, probe가 입증한 경우에만 launch-scope 격리를 지원한다고 선언하며 항상 run 전용 page/profile 격리를 사용한다.
15. source E2E build 산출물은 artifact dir에만 생성되고 repository 또는 설치본 dist를 변경하지 않는다.

---

## 16. 결정 제안

다음 방향을 채택안으로 제안한다.

1. **Surface-first E2E**: 도구 가용성이 아니라 Browser·API·Human으로 드러나는 실제 사용자 계약이 profile을 결정한다.
2. **Orca-first Browser session, shared agent-browser driver**: Orca-managed와 standalone에 중복 adapter를 만들지 않는다.
3. **source server isolation 우선**: 모든 executor보다 Runtime Manager와 동적 포트 계약을 먼저 구현한다.
4. **Hybrid는 우회가 아니라 교차 검증**: API setup은 허용하되 핵심 UI 행동을 대체하지 않는다.
5. **Human handoff는 pause/resume**: 사용자 응답을 verdict로 쓰지 않고 구조화 증적 뒤 verifier가 판정한다.
6. **Playwright 기본 설치는 단계적 제거**: 지원을 즉시 삭제하지 않고 모든 소비자 이전 뒤 opt-in으로 전환한다.
7. **증거 없는 pass 금지**: 실제 assertion과 profile별 증적을 `real-usage` 판정의 필수 조건으로 집행한다.

구현 단계에서는 태스크 1~9를 한 번에 묶지 않고, profile·verdict 계약 → runtime isolation → Orca-managed Browser → API·Human executor 순으로 작은 독립 태스크를 생성한다.
