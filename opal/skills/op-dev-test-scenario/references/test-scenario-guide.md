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

test substitute를 쓰면 대체 대상·이유·한계와 실제 연동으로 별도 확인할 부분을 적는다.
substitute 결과는 실제 integration, E2E, manual 증거를 대신하지 않는다.

## Scenarios

| 열 | 작성 내용 |
|---|---|
| ID | 중복 없는 `S-N` |
| 검증 대상 | 하나 이상의 AC-N/C-N, 필요한 경우 H-N |
| 조건 | 입력과 사전 상태 |
| 행동 | 실행 명령, 사용자 조작, 또는 검증 동작 |
| 기대 결과 | 관찰 가능한 통과 기준 |
| 방법·환경 | 실제 사용할 unit, integration, E2E, manual 방법과 환경 |
| 시점 | 구현 전 RED, 구현 후, 설치 후, 배포 후 중 필요한 시점 |

E2E 시나리오는 `test-scenario.json` 변환 시 구조화 계약을 함께 가져야 한다.

- `surface_kind`: `web_ui`, `api`, `hybrid`, `collaborative`, `manual` 중 하나
- `profile`: `browser`, `api`, `hybrid`, `collaborative`, `manual` 중 하나. 도구 가용성으로 낮추지 않는다.
- `actors`: `user`, `service`, `human`, `agent` 등 검증 주체
- `steps[]`: 각 step의 `id`와 `executor`(`browser`, `api`, `human`)
- `assertions[]`: semantic assertion의 `id`와 `expected`
- `required_evidence[]`: pass 또는 `real-usage`에 필요한 증적 이름
- `handoff`: Collaborative/Manual 대기·재개가 필요한 경우 `handoff_id`, `instruction`, `expected_observation`, `required_evidence`, `timeout_seconds`, `resume_token`, `server_policy`, `submission_path` 8개 필드를 모두 가진다.

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

## Scenarios

| ID | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|
| S-1 | AC-1, C-1 | {조건} | {행동} | {판정 기준} | {방법·환경} | {시점} |
```

## 완료 검사

- 모든 AC/C와 존재하는 H가 최소 한 시나리오의 `검증 대상`에 연결됨
- S-ID가 1건 이상이며 중복되지 않음
- 조건·행동·기대 결과가 실행 전에 판정 가능함
- 실제 연동이 필요한 검증을 substitute나 manual 표기로 숨기지 않음
- 결과·증거·단계 승인 상태를 본문에 기록하지 않음
- RED가 필요한 행과 구현 후 검증 행의 시점이 구분됨

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
