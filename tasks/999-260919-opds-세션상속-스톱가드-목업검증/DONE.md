# DONE: 세션 상속과 Stop 가드 목업 검증

## 결과

세션 식별자가 부모 실행 경계부터 Bash subprocess, state-tool run-log, state-transition lease, Stop evaluator까지 끊기지 않고 이어지도록 **두 개의 독립 결함**을 고쳤고, 그 결과를 실사용 경로로 입증했다.

**결함 1 — env 프리앰블에 `export`가 없었다.** SessionStart hook이 플랫폼 env 파일에 `OPAL_SESSION_ID=<id>`를 썼는데, 이 파일은 dotenv가 아니라 부모 쉘이 `source`하는 쉘 스크립트 프리앰블이다. `export` 접두가 없어 값이 쉘 변수로만 남고 자식 프로세스에 전달되지 않았다. 그 결과 `state-tool`이 `ownership_session_id_missing`으로 lease claim을 건너뛰었고, run-log `actor.session_id`가 `null`이 되었으며, lease의 `claim_source`가 `session_start`에 머물러 **Stop evaluator의 강제 차단 자격이 성립하지 않았다**. 이제 `export OPAL_SESSION_ID=<shlex.quote한 id>`를 쓴다.

**결함 2 — 워크트리 세션이 부트 후 허브 registry에 자기 ID를 등록하지 않았다.** launcher는 터미널을 띄우는 시점에 아직 태어나지 않은 세션의 ID를 알 수 없어 `owner_session_id`를 `null`로 기록하고, 그 뒤 registry를 채우는 주체가 어디에도 없었다. `worktree-tool checkpoint`의 소유권 검사가 `OPAL_SESSION_ID`와 registry `owner_session_id` 두 항을 모두 요구하므로, **agentic 워크트리 세션의 체크포인트 커밋 권한이 구조적으로 도달 불가능**했다. 이제 lease를 잡은 워크트리 세션이 `worktree-tool ownership-set` CLI 경유로 부트 owner 등록을 1회 위임한다.

**유지한 것**: `state-tool`은 `OPAL_SESSION_ID`만 소비하는 중립 계약 그대로다(플랫폼 고유 변수명은 `claude_adapter`가 단독 소유). registry meta 파일 직접 쓰기는 여전히 하지 않고 전이는 CLI 경유만이며, 파일 쓰기·lock·원자 교체는 `worktree-tool`이 소유해 dual-writer가 생기지 않는다. hook은 전 경로 fail-safe exit 0이고, `ownership-set` 호출에는 45초 상한을 둬 멈춘 CLI가 세션 부팅을 막지 못하게 했다. env 파일 미제공·쓰기 실패 경로와 허브 cwd lease 0건 동작은 불변이다.

**적용한 경계**: 코드 수정은 워크트리 소스에만 했고 배포는 install 경유만 했다(소유자 승인 1회). 체크포인트는 `feat/OP-TASK-999` 브랜치에만 만들었고 `main` commit·merge·push는 하지 않았다. 태스크 999 외 슬롯의 registry·lease·run-log는 건드리지 않았다.

## 변경 파일

- `opal/tools/ownership-tool/ownership_tool/session_start_hook.py`
- `opal/tools/ownership-tool/tests/test_session_start.py`
- `opal/tools/ownership-tool/README.md`
- `.opal/brain/pages/entity/ownership-tool.md`

## 검증

- **회귀 4스위트 (PM 직접 재실행)**: `ownership-tool` 62 passed · `state-tool` 535 passed + 339 subtests, 3 skipped (329.45s) · `worktree-tool` 146 passed (115.30s) · `worktree-launcher` 110 passed, 1 skipped. 합계 **853 passed / 0 failed / 4 skipped**, 4스위트 모두 exit 0.
- **RED→GREEN**: `test-tool scenario-red` 2건(S-2r·S-12r) 기록 후 `scenario-lock` 통과, 구현 후 전건 GREEN. RED 작성자(`opal-test-agent`)와 구현자(`opal-task-agent`)를 분리했다.
- **목표-커버 게이트**: `scenario-coverage-check` exit 0(`all_covered`) + `opal-evaluator-agent` `scenario-rubric` verdict **pass**(목표 2 / 채택·잔존 2 / 경계·부정 1, 평균 1.67) 두 증거.
- **실사용 프로브**(공개 hook 진입점과 실제 봉투만 사용, 테스트 내부 주입 없음): `classification=current_session_owned`, `evidence.forced_count=1`, `decision_kind=block_continue` — `PROBE-STOP.md`.
- **lease 승격**: `claim_source` `session_start`→`state_transition`, `generation`·`claimed_at`·`owner_session_id` 3필드 불변 — `PROBE-AFTER.md`.
- **registry 실물 반영**: 허브 `owner_session_id` `null`→세션 ID(lease와 바이트 일치), `generation` 2→3 단조 증가, receipt 2종 보존, 멱등 재실행 시 `generation` 불변 — `PROBE-OWNERSHIP.md`.
- **체크포인트 권한**: `worktree-tool checkpoint --mode agentic --stage execute` 1회 성공, `commit=a93a5ad8f0b55f9f5aef0cd39b209c4bcf2a7ac6`가 registry `checkpoint_shas[]`에 append. `main` 무변경·push 0건 — `PROBE-CHECKPOINT.md`.
- **컨벤션 자동 진단**: `opal-convention-checker` **PASS_WITH_ADVISORIES, Critical 0 / High 0**. advisory 2건(@header 현재 사실)은 이번 태스크에서 보완했고, 1건(`import sys` 미사용)은 선존이라 범위 밖으로 남겼다.
- 시나리오 31건: **29 pass / 0 fail / 2 blocked**. 원본은 `test-scenario.json`이 소유한다.

## 회고적 학습 후보

.opal/brain/pages/concept/env-preamble-needs-export-to-reach-child-processes.md
.opal/brain/pages/concept/auto-issued-ownership-needs-a-boot-time-registrant.md
.opal/brain/pages/entity/ownership-tool.md
.opal/brain/pages/concept/stop-force-requires-state-transition-claim.md

## 참고

**미검증으로 남긴 축 (소유자 결정 — 후속 경계)**

- **S-3b · S-4b**: 재배포 이후 부팅하는 **진짜 새 Orca 세션**에서의 종단 확인. 이 태스크를 수행한 PM 세션은 수정 **이전에** 부팅해 플랫폼이 이미 구 포맷 env 프리앰블을 썼으므로 현재 세션 안에서 재현할 수 없고, 워크트리에 두 번째 세션을 띄우면 `execution_ownership`·lease가 충돌한다. AC-3·AC-4 자체는 S-3·S-4가 이미 충족했으며 두 시나리오는 **실세션 재확인 축**이다. 이 워크트리에서 다음에 부팅하는 세션이 수정본이므로 그때 자연 확인된다.

**후속 태스크 권고 — 하나의 계약 결정으로 묶을 것**

`PROBE-GAPS.md`가 실측한 4경로(세션 재시작 직후 / 상태 전이 없는 재개 / state view 부재 / block cap 미설정)는 D-M 2항 판정으로 **전건 후속 경계**다(이번 구현 0건). 개별 수정으로 다루면 안 된다 — 근본은 하나다.

- 공개 Stop hook은 `evaluate(payload, project_root=...)`만 호출하고 `show_json`·`env`를 넘기지 않는다. 그래서 `evidence.fingerprint`가 **구조적으로 생길 수 없고**, `allow_no_progress_same_fingerprint`는 도달 불가 분기다.
- 여기에 `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP`이 운영 기본 미설정이라, 현재 **`block_continue` 루프를 끊는 장치가 사실상 0개**다.
- 부수 위험: cap 파싱이 `"0"`→`0`을 허용하는데 `None`(상한 검사 생략)과 `0`(항상 도달)은 의미가 정반대인데 둘 다 "설정 안 한 듯한 값"에서 나온다.

→ 후속은 개별 갭 수선이 아니라 **"Stop 가드가 진행 여부를 무엇으로 판정하는가"** 한 계약 결정으로 접근해야 한다. `claude_adapter.py`가 이미 "자체 기본 상한을 두지 않는다(H-7)"를 확정해 뒀으므로 상한 도입은 그 결정의 번복이다.

**그 밖의 이월**

- `opal/tools/ownership-tool/tests/test_session_start.py`의 미사용 `import sys`(선존, low). `(미구현)` 표기는 형제 테스트 6종이 공유하는 선존 패턴이라 일괄 정리를 별건으로 둔다.
- PLAN H-4의 `dist/` 탐지가 `git status --porcelain`만 보도록 적혀 있었으나, `dashboard/frontend/dist/`는 gitignore 대상이라 porcelain에 잡히지 않는다. 실제로 재배포가 생성했고 파일시스템 확인으로만 탐지됐다 — 향후 같은 판정은 `existsSync` 축으로 적어야 한다.
- `opal-pilot-dev` SKILL STEP 4의 행 단위 actor 분기 서술이 `harness/actor.md` §`--pm` 미사용 시 조항과 충돌한다. 이번엔 SSOT인 `actor.md`를 따랐다.
- "수정 전 부팅 세션은 재부팅 또는 env 파일 재적용 전까지 `checkpoint`를 통과할 수 없다"는 운영 사실이 실증됐다(`PROBE-CHECKPOINT.md`). 운영 문서 반영 후보.
