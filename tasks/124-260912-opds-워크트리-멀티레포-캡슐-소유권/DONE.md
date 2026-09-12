# DONE: 워크트리 multi-repo 캡슐 소유권 — 계약 이관과 worktree-tool 구현

## 결과

multi-repo 프로젝트가 `--worktree`를 쓸 수 있게 됐다. `task_artifacts.repo: "."`를 선언하면 slot
root 자체가 루트 저장소의 worktree가 되고 그 아래에 코드 저장소 worktree들이 허브와 동형으로
배치된다. 태스크 캡슐은 루트 저장소 브랜치에 담기므로 코드 변경과 실행 증거가 한 브랜치로 묶인다.

**닫혀 있던 경로를 열었다.** 선행 제안서 §8은 캡슐 소유 repo가 `repos[]`의 한 원소라고 암묵
전제했는데, `_find_independent_git_dirs()`가 루트를 후보에서 명시적으로 제외하므로 캡슐을
추적하는 주체가 루트인 구조에서는 지목할 대상이 없었다. 예약값 `"."`를 도입해 이 구멍을 메웠다.
`repos[]`의 타입과 의미는 바꾸지 않았다 — "worktree를 만들 코드 저장소 목록"과 "캡슐을 소유하는
저장소"는 다른 역할이므로 필드를 나눴다.

**조건 하나를 실측으로 찾아 추가했다.** slot root가 full checkout이라, 루트가 `repos[]` 경로를
ignore하지 않으면 자식 worktree가 생기는 순간 루트 slot이 `?? workspace/`로 영구 dirty가 된다.
`cmd_remove`는 제거 이전에 전 entry의 가드를 먼저 돌므로 역순 회수를 도입해도 루트가 항상
`GUARD_DIRTY`에 걸려 `--force` 없는 회수가 차단된다. R-5("루트가 각 `repos[]` 경로를 ignore한다",
판정 `check-ignore -q`)를 신설해 명시 차단으로 바꿨다. 실사용 대상 pug는 루트 `.gitignore:3`이
`workspace/`를 같은 이유로 이미 등재하고 있어, 없던 제약을 만든 것이 아니라 관례를 조건으로
고정한 것이다.

**판정 순서가 계약이 됐다.** `git check-ignore -q <rel>`은 그 경로에 추적 파일이 하나라도 있으면
rc=1을 반환한다. R-5를 추적 겹침보다 먼저 판정하면 겹침 위반이 `TASK_ARTIFACT_REPO_INVALID`로
먼저 걸려 `TASK_ARTIFACT_REPO_OVERLAP`에 도달하지 못한다. 순서를 **R-1~R-4 → 추적 겹침 → R-5**로
고정했다. `check-ignore --no-index` 대안은 추적 중인 경로도 통과시켜 R-5의 의미를 "실효 ignore"에서
"ignore 규칙 존재"로 약화시키므로 쓰지 않는다.

**회수가 복구 가능해졌다.** 중첩 구조에서는 자식이 루트 worktree 안에 있어 루트를 먼저 제거할 수
없다. 회수·롤백을 생성의 역순(자식 → 루트)으로 돌리고, 각 `git worktree remove`의 반환코드를
확인해 하나라도 실패하면 메타와 slot을 보존한 채 `WORKTREE_REMOVE_FAILED`를 반환한다. 경로 실재 ×
Git 등록 2축 판정으로 부분 회수 이후 재시도가 `--force` 없이 동작한다. 불일치 2종은 자동 복구하지
않는다 — `git worktree prune`은 해당 repo의 모든 stale 관리정보를 지워 다른 태스크 슬롯까지
파괴하고, Git이 모르는 디렉토리의 내용은 사용자 파일일 수 있다.

**유지된 것** — monorepo와 비워크트리 실행은 설정·출력·동작 어느 축에서도 변하지 않는다. 신규
계약은 전부 multi-repo 분기 안에 갇혀 있고, 회수 계약의 한정은 메타에 동결된 `layout` 값으로
판정한다. `remove`가 `load_config`를 호출한 적이 없으므로 회수 시점 재해석은 DEC-3이 봉인한
결함류를 되살린다.

**적용 경계** — 제안서 §11의 1~3단계다. `repos[]` 원소를 캡슐 repo로 지정하는 경로는 canonical
resolver의 허브 후보 경로 고정과 `task_path` 불변식의 `tasks` 세그먼트 고정을 함께 풀어야 하므로
후속 제안 소관이다. pug 실환경 파일럿(§11의 4~5단계)도 범위 밖이며, 이번 태스크의 모든 판정은
**fixture 한정**이다.

## 변경 파일

- `opal/tools/worktree-tool/worktree_tool.py`
- `opal/tools/worktree-tool/tests/test_worktree_tool.py`
- `opal/core/references/harness/worktree.md`
- `docs/proposals/opal-worktree-multirepo-ownership.md` → `docs/proposals/archives/` (`git mv`)
- `docs/proposals/archives/opal-worktree-task-ownership.md`
- `tasks/124-260912-opds-워크트리-멀티레포-캡슐-소유권/REGRESSION-EVIDENCE.md` (신설)
- `tasks/124-260912-opds-워크트리-멀티레포-캡슐-소유권/TEST.md` (신설)
- `tasks/124-260912-opds-워크트리-멀티레포-캡슐-소유권/GC-CONVENTION-2026-09-12T19-51-08-124.md` (신설)
- `tasks/124-260912-opds-워크트리-멀티레포-캡슐-소유권/gc-findings-convention-2026-09-12T19-51-08-124.json` (신설)

## 검증

- 시나리오 전수 — `test-tool scenario-status` → `locked: true, total 28, passed 28, failed 0,
  blocked 0`. `red_required` 19건 전건이 구현 전 실패 증거를 가진 뒤 GREEN으로 전환됐다
  (`red_confirmed_required: 19/19`). 증거는 시나리오별 개별 실행이며 전체 스위트 1회 통과를
  28건으로 뭉뚱그리지 않았다.
- 도구 스위트 — `python3 -m pytest opal/tools/worktree-tool/tests/ -q` → **118 passed, 0 failed**
  (착수 전 28 failed / 90 passed). 기존 83건 무수정 통과이며, 지정 회귀 4건은 함수 본문 md5가
  HEAD 사본과 전건 SAME임을 확인해 "수정 없이 통과"를 실증했다.
- monorepo·비워크트리 바이트 동일(C-2·C-3) — 데이터 루트를 고정 pristine 스냅샷으로 두고 단일
  배포 경로에 base·after를 순차 install해 도구 코드만 스왑했다. 14명령 × (stdout·stderr·exit) =
  **42/42 바이트 동일, 정규화 0회**. `init` 초안은 monorepo 8키 집합·순서·값이 791바이트 동일이고
  신규 3키가 노출되지 않는다. 비공허성도 함께 실증(배포본 3파일 sha256이 전부 DIFF이고 after
  배포본에 신규 식별자 11회·base 0회인 상태에서 출력 동일). 상세: `REGRESSION-EVIDENCE.md`.
- monorepo 실패 표면 — slot 디렉토리만 삭제해 "경로 부재 + 등록 잔존"을 만든 뒤 `remove`를
  `--force` 유무 2경로로 실행해 base↔after 6쌍 동일. legacy 응답(`WORKTREE_NOT_FOUND` /
  `ok: true, removed: []`)이 유지되며 multi-repo 신설 `WORKTREE_REMOVE_FAILED`·`mismatch`가
  나타나지 않는다. 구현 중 이 표면이 한 번 바뀌었다 되돌려졌으므로 별도 측정 항목으로 고정했다.
- H-3 미실현 확증 — `validate_worktree_config` 반환 키가 실제로 8→10으로 늘었는데도 `list`·`init`
  포함 6명령 출력이 바이트 동일하다. PLAN의 정적 판단이 실행 출력으로 확인됐다.
- 제안서↔구현 대조(C-1) — §4·§5·§6의 21개 계약 항목을 `worktree_tool.py` 좌표와 1:1 대조.
  불일치 0건, 구현에만 있는 계약 0건. 진행 중 개정 2건(R-5 신설·판정 순서 확정)은 구현보다 제안서를
  먼저 고쳤다.
- 컨벤션 — `opal-convention-checker` 결과 Critical 0 / High 0, verdict `PASS_WITH_ADVISORIES`
  (`GC-CONVENTION-2026-09-12T19-51-08-124.md`). 지적된 `@header` 변경 서술 중 이번 태스크가 추가한
  4건은 현재 사실 서술로 정정 완료.
- `@header` — `code-scan scan opal/tools/worktree-tool/` → `3 file(s)`,
  `code-scan validate --changed` → `OK — coverage 100% (2/2)`.
- 배포 경계(C-8) — 실 `~/.opal/`에 배포하지 않았다. 회귀 측정 install은 격리 `HOME`의 임시 경로에만
  수행하고 삭제했으며 잔여물 0건이다. 배포본 `worktree_tool.py` sha256이 HEAD와 동일하고 워크트리
  변경본과 상이함을 확인했다.

## 회고적 학습 후보

.opal/brain/pages/concept/ignore-is-a-separate-axis-from-tracking.md
.opal/brain/pages/concept/judgment-order-is-part-of-the-contract.md
.opal/brain/pages/concept/scope-new-contracts-to-the-branch-that-needs-them.md
.opal/brain/pages/concept/silent-skip-makes-every-check-pass.md

## 참고

**후속 — monorepo 회수의 데이터 손실 경로** — monorepo `cmd_remove`는 `git worktree remove`의
반환값을 버리고 곧바로 `_delete_meta`를 실행한다. 제거에 실패한 슬롯이 메타를 잃고 도구로 복구
불가가 되며, 이는 TASK Problem이 multi-repo에 대해 기술한 실패와 같은 형태다. 닫으려면 returncode
확인·전건 성공 후 삭제·2축 멱등 판정 **셋을 함께** 옮겨야 한다 — 2축 판정이 실패 이후의 복구
수단이므로 returncode 확인만 옮기면 막히기만 하고 복구는 안 된다. 이번에는 "신규 계약은 전부
multi-repo 분기 안에 갇힌다"는 안전 논거를 우선해 이연했다.

**후속 — `code-scan`의 fail-open 2종** — ① `scan`이 파싱 불가 `@header`를 **보고 없이 건너뛴다**.
이번에 `worktree_tool.py`가 따옴표 미이스케이프로 코드맵에서 통째로 빠져 있었고(HEAD부터 존재),
그 상태에서 `validate --changed`가 `coverage 50% (1/2)`로 OK를 냈다. ② `--changed`가 공백 구분
인자를 조용히 1건만 처리하고 `0/1`을 OK로 보고한다(CSV가 정답). 둘 다 검사가 통과했다는 신호가
검사 대상이 비었다는 사실을 덮는 같은 형태다. 이번 태스크는 ①의 원인인 2문자만 고쳤고 도구
자체는 손대지 않았다.

**후속 — `@header` `description` 총량과 선행 누적** — 현재 5,465자로 "파일의 역할 한 줄 요약"
계약(`header-standard.md`)과 어긋난다. 092·112·118·119가 태스크마다 한 절씩 덧붙인 결과이며
124도 같은 방식으로 append했다. 정리하려면 선행 태스크 서술까지 재작성해야 해 이번 범위 밖으로
뒀다.

**후속 — worker role 계약의 stale receipt 경로** — `opal-convention-checker`가 stale receipt를
받고 role 계약 §3의 즉시 `blocked` 대신 동일 이벤트를 재load·재검증한 뒤 진행했다. 문면 위반이나
실질은 더 안전하며 워커가 스스로 신고했다. 드리프트가 워커 문서를 건드리지 않은 경우까지 전면
왕복을 강제하는 계약에 "재load·재검증 후 계속" 경로가 없다 — 프레임워크 개선 후보다.

**PM 실행 결함 2건** — ① `dispatch-process.md` Step 0의 "매 워커 디스패치 직전에 새로 수행"을
어기고 단일 receipt를 재사용해, 타 세션 배포로 manifest가 바뀐 뒤 디스패치 3건이 stale receipt를
받았다. 문서 집합은 동일하고 변경분이 PM 지침 한정이라 산출물 실질에는 영향이 없었다. ② RED 증거
19건을 `scenario-init` 재호출로 초기화한 뒤 재기록 플래그를 잘못 써(`--scenario`, 정답 `--id`)
실패했고 확인 전에 백업을 지워 증거 텍스트를 잃었다. RED 작성자를 재개해 재관측·재기록으로
복구했다. 상세 경위는 `AGENTIC-LOG.md` 26~27·46~48.

**한계 — fixture 한정 판정** — AC-1~AC-16 전건이 fixture에서 판정됐다. 태스크 092의 교훈대로
단위 테스트 전건 GREEN 상태에서 실환경이 차단성 결함을 잡아낸 전례가 있으므로, pug 실환경 완주
전까지 이 계약은 실사용 검증된 것으로 간주하지 않는다.
