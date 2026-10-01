# sdlc-v2 TEST-SCENARIO 작성 가이드

> TASK 첫 frontmatter가 `template: sdlc-v2`일 때만 읽는다.

## 입력

- TASK `Proposed outcome`, `Acceptance criteria`의 AC-N, `Constraints`의 C-N
- PLAN `Risks`에 존재하는 H-N과 `Work items`의 변경 대상·실행 그룹
- PM이 주입한 프로젝트 문서와 실제 실행 capability

AC/C가 없으면 추론으로 채우지 않고 TASK 보완으로 되돌린다. Risks에 추가 검증이 필요한 위험이
없으면 H를 만들지 않는다.

## Setup

여러 시나리오가 공유하는 환경, 데이터, 서비스, 사용자 협업 조건만 한 번 적는다.
사람 조치가 필요한 시나리오는 로그인·DDL·권한·관찰 등 선행 조건, 실행 주체, 제출할 증거를 명시한다. TEST 시작 시 전체 handoff를 한 묶음으로 먼저 요청할 수 있어야 한다. 실행 순서는 `opal/core/references/harness/test-cycle.md` §진입과 병행 실행이 소유한다.

병렬로 실행해도 되는 시나리오는 Setup에 `병렬 그룹: S-a, S-b, ...` 한 줄로 선언한다.

- 서로 선행 관계가 없고 공유 자원(포트·`~/.opal`·같은 파일·태스크 상태 파일)을 쓰지 않는 시나리오만 작성자가 선언한다.
- 선언이 없는 시나리오는 순차 실행이다.
- `test-scenario.json` 스키마에 필드를 추가하지 않는다. 실행 규칙은 `opal/core/references/harness/test-cycle.md`가 소유한다.

test substitute를 쓰면 대체 대상·이유·한계와 실제 연동으로 별도 확인할 부분을 적는다.
substitute 결과는 실제 integration, E2E, manual 증거를 대신하지 않는다.

## Scenarios

| 열 | 작성 내용 |
|---|---|
| ID | 중복 없는 `S-N` |
| 유형 | `unit`·`integration`·`contract`·`regression`·`e2e`·`check` 중 하나. 새로 작성하는 문서는 이 열을 반드시 채운다. 이 열이 없는 기존 문서는 유형 검사 없이 기존 변환을 유지한다 |
| 검증 대상 | 하나 이상의 AC-N/C-N, 필요한 경우 H-N |
| 조건 | 입력과 사전 상태 |
| 행동 | 실행 명령, 사용자 조작, 또는 검증 동작 |
| 기대 결과 | 관찰 가능한 통과 기준 |
| 방법·환경 | 실제 사용할 unit, integration, E2E, manual 방법과 환경 |
| 시점 | 구현 전 RED, 구현 후, 설치 후, 배포 후 중 필요한 시점. `유형`이 `check`인 행은 RED 대상이 아니므로 `구현 전 RED`를 쓰지 않는다 |

### 별도 행동 시나리오를 만드는 기준

다음을 모두 만족할 때만 별도 행동 시나리오로 작성한다.

- 공개 인터페이스 또는 사용자가 관찰할 수 있는 결과를 검증한다.
- 다른 시나리오와 구별되는 고유 결함 신호가 있다.
- 실패했을 때 깨진 요구나 위험을 독립적으로 설명할 수 있다.
- 같은 실행으로 이미 충분히 검증되지 않는다.
- 실제 변경 위험에 맞는 테스트 계층을 사용한다.

다른 시나리오에 완전히 포함되고 별도로 찾아내는 결함이 없다면 만들지 않는다.

### 합치는 기준

다음이 같고 한 번의 출력으로 각 기대 결과를 판정할 수 있으면 한 시나리오로 합친다.

- 실행 명령 또는 사용자 행동
- 실행 환경과 대상 SHA
- 준비 데이터와 사전 상태

기대 결과가 여러 개면 시나리오를 나누지 않고 assertion을 나눈다. 각 assertion의
`expected`와 `actual`은 별도로 기록한다.

다음 중 하나가 있으면 별도로 유지할 수 있다.

- 실행 환경 또는 배포 표면이 다름
- 실행 주체나 사람 handoff가 다름
- 실패 격리 또는 복구 절차가 다름
- 한 실행의 증거로 다른 기대 결과를 판정할 수 없음

### Check로 작성하는 기준

다음은 행동 시나리오가 아니라 `유형: check`다.

- source grep 또는 정적 구조 검사
- 문서·레지스트리·설정 존재 확인
- lint, typecheck, build, 보안·컨벤션 검사
- AC/C가 전체 회귀 증거 자체를 직접 요구하는 경우의 확인
- 파일이나 명령 결과의 사실 여부를 확인하는 검증

Check도 AC/C/H를 검증할 수 있다. 별도 목록을 만들지 않고 기존 `scenarios[]`와 S-ID를
유지하되 `유형: check`로 구분한다. Check는 RED 대상이 아니다.

lint·typecheck·build·보안·컨벤션 검사와 전체 회귀는 최종 TEST Gate가 이미 수행하므로
관성적으로 S-ID를 만들지 않는다. AC/C가 해당 검사 자체를 직접 요구할 때만 Check로 연결한다.

### 테스트 계층 선택 기준

결과를 충분히 증명하는 가장 저렴한 계층을 선택한다.

- 순수 로직과 작은 계약은 unit 또는 contract
- 여러 컴포넌트의 실제 연결이 결과를 좌우하면 integration
- 화면·인증·설치본·외부 시스템 등 실제 경로가 결과를 좌우하면 E2E
- 특정 과거 결함이나 기존 공개 계약의 재발 여부를 겨냥하면 regression
- 자동화할 수 없는 관찰은 방법·환경에 manual과 구조화 handoff를 명시

실제 연동이 필요한 검증을 mock이나 manual 표기로 낮추지 않는다. 반대로 unit으로 충분한 결과를
관성적으로 E2E까지 올리지 않는다.

### 에이전트·외부 서비스 실호출 기준

- 에이전트·외부 서비스 실호출은 모델의 판단·응답 자체가 AC의 수용 기준일 때만 시나리오로 쓴다.
- 전달 경로, 입력 조립, 출력 형식, 기록은 기록된 결과 파일을 입력으로 한 결정론 시나리오(`integration`·`contract`)로 쓴다.
- 실호출 시나리오는 `방법·환경` 열에 `[실호출 1회]`와 근거 AC-N을 적는다.
- 한 시나리오 안에서 호출은 1회만 한다. 반복 측정은 시나리오가 아니라 측정 작업이다.
- 실행 주체와 실행 규칙(헤드리스 호출 불가 시 `blocked` 포함)은 `opal/core/references/harness/test-cycle.md` §실호출 시나리오가 소유한다.

`regression`은 특정 기존 계약이나 과거 결함을 겨냥한 행동 검증이다. 여러 계약을 한꺼번에
확인하는 전체 회귀 스위트는 `regression` 시나리오가 아니라 최종 Gate 검사이며, AC/C가 직접
요구할 때만 Check로 기록한다.

### 경계 시나리오 기준

실제로 가능한 실패이고 발생 가능성 또는 영향 중 하나가 유의미할 때만 작성한다. 가능성과 영향이
모두 낮은 가상 edge case는 blocking 시나리오로 만들지 않는다. 위험은 별도 카탈로그가 아니라
PLAN `Risks`의 H-N을 사용한다.

### AC/C/H와의 관계

AC/C/H 연결 완전성은 유지하지만, 연결 개수와 시나리오 개수는 같지 않다.

- 하나의 시나리오 또는 Check가 여러 AC/C/H를 검증할 수 있다.
- 하나의 AC/C/H가 필요한 경우 여러 검증 항목으로 입증될 수 있다.
- 검증 대상 연결은 기존 `검증 대상` 열을 단일 연결 지점으로 사용한다.
- AC/C/H마다 기계적으로 새 S-ID를 만들지 않는다.

작성 완료 조건은 "AC/C/H 수만큼 시나리오가 존재함"이 아니라 "모든 AC/C/H가 최소한의
검증 항목으로 충분히 입증됨"이다.

E2E 시나리오는 `test-scenario.json` 변환 시 구조화 계약을 함께 가져야 한다.

- `surface_kind`: `web_ui`, `api`, `hybrid`, `collaborative`, `manual` 중 하나
- `profile`: `browser`, `api`, `hybrid`, `collaborative`, `manual` 중 하나. 도구 가용성으로 낮추지 않는다.
- `actors`: `user`, `service`, `human`, `agent` 등 검증 주체
- `steps[]`: 각 step의 `id`와 `executor`(`browser`, `api`, `human`)
- `assertions[]`: semantic assertion의 `id`와 `expected`
- `required_evidence[]`: pass 또는 `real-usage`에 필요한 증적 이름
- `handoff`: Collaborative/Manual 대기·재개가 필요한 경우 `handoff_id`, `instruction`, `expected_observation`, `required_evidence`, `timeout_seconds`, `resume_token`, `server_policy`, `submission_path` 8개 필드를 모두 가진다.

여러 human step이 있으면 각 step의 선행 조치와 제출 증거를 분리해 적되, 한 번의 TEST 진입 요청에 함께 실을 수 있도록 작성한다. 자동 시나리오의 실행을 사람 제출 완료에 종속시키지 않는다.

`pass`와 `real-usage`는 assertion expected/actual과 required/observed evidence가 모두 충족된 구조화 verdict로만 기록한다.
사람 협업은 자유형식 완료 선언으로 pass가 되지 않으며, 최초 대기는 `awaiting_human`이고 구조화 submission 검증 뒤 최종 상태로 전이한다. 실행 전 result zone의 `handoff_state`는 `null`일 수 있다. `scenario-mark --verdict-json`이 `awaiting_human`을 기록할 때 `handoff` 기본값과 runtime `handoff_state`를 병합해 위 8개 필드를 완성하고 `run_id`를 함께 저장한다. 재개는 같은 run-id/resume-token의 `--submission`으로만 수행하며, submission은 사람의 완료 선언이 아니라 verifier가 검사할 expected/actual과 observed evidence 입력이다.

한 시나리오가 여러 AC/C/H를 함께 검증해도 된다. 별도 매핑표를 만들지 않고 `검증 대상` 열을
단일 연결 지점으로 사용한다. 복잡한 절차만 `### S-N` 하위 절로 펼친다.
`시점`에 `구현 전 RED`를 적은 행만 실행 전에 `test-scenario.json`의 `red_required: true`로 변환된다.

검증 방법은 변경 경계에 맞춘다.

- 공개 인터페이스와 관찰 가능한 결과를 검증한다.
- 화면, 인증, 외부 API처럼 실제 경로가 결과를 좌우하면 integration 또는 E2E를 둔다.
- 자동화가 불가능한 확인만 manual로 두고 Setup에 실행 조건을 적는다.
- 실제로 가능한 실패·경계 조건만 포함한다. 낮은 가능성과 낮은 영향을 동시에 가진 경우는 만들지 않는다.

## 출력

```markdown
---
template: sdlc-v2
---
# TEST-SCENARIO: {태스크 제목}

> 입력: [TASK.md](TASK.md), [PLAN.md](PLAN.md) | 작성자: PM

## Setup

- 환경: {실행 환경·필수 서비스}
- 공통 데이터: {필요할 때만}
- 대역 사용과 한계: {사용하지 않음 | 대상·이유·한계·실제 확인 지점}
- 실행 조건: {자동 실행 | 사용자 협업 조건}
- 병렬 그룹: {S-a, S-b, ... | 선언 없음(순차)}

## Scenarios

| ID | 유형 | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|---|
| S-1 | unit | AC-1, C-1 | {조건} | {행동} | {판정 기준} | {방법·환경} | {시점} |
```

## 완료 검사

- 모든 AC/C와 존재하는 H가 최소 한 시나리오의 `검증 대상`에 연결됨(연결 개수와 시나리오 개수가 같을 필요는 없음)
- S-ID가 1건 이상이며 중복되지 않음
- 조건·행동·기대 결과가 실행 전에 판정 가능함
- 실제 연동이 필요한 검증을 substitute나 manual 표기로 숨기지 않음
- 결과·증거·단계 승인 상태를 본문에 기록하지 않음
- RED가 필요한 행과 구현 후 검증 행의 시점이 구분됨. `유형: check` 행에는 `구현 전 RED`가 없음
- 새로 작성하는 문서는 `유형` 열의 모든 값이 허용 6값 중 하나임

결정론 coverage build/check와 판단 루브릭은 `op-scenario-gate`가 한 번 수행한다.

## 변경이력

| 버전 | 일시 | 변경내용 |
|---|---|---|
| v1.0 | 2026-04-15 | 초기 작성 — 작성 프로세스와 도구 매핑 |
| v2.9 | 2026-09-02 17:22 KST | 소유자 호칭 플레이스홀더 전환 (L2 직접 수정) |
| v3.0 | 2026-09-09 14:18 KST | sdlc-v2 출력을 `Setup / Scenarios`로 단순화하고 토큰·상태·증거 소유권 반영 (task 111/W-5) |
| v3.1 | 2026-09-09 14:58 KST | test substitute 경계와 중복 S-ID 거부 조건 반영 (task 111/W-5 보완) |
| v3.2 | 2026-09-09 15:07 KST | PLAN Risks H를 optional로 변경 (task 111/W-5 보완) |
| v3.3 | 2026-09-09 15:33 KST | 작성 규칙과 템플릿의 단일 SSOT로 축소. 고정 계층·도구표와 중복 coverage 실행을 제거하고 시나리오 통합 작성을 허용 (task 111/W-13) |
