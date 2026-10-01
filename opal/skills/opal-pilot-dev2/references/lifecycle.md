# 생명주기와 상태

INTENT → DESIGN → PLAN → BUILD → VERIFY → REVIEW → RELEASE → OBSERVE → CLOSED.
delivery=build는 REVIEW 뒤 CLOSED/ready_for_merge, release는 OBSERVE 뒤 CLOSED/observed.

| 단계 | 전이 근거 |
|---|---|
| INTENT | intent 구조·AC·미결 질문 해소·필요 승인 |
| DESIGN | intent 해시를 참조하는 spec·정책 적용·필요 승인 |
| PLAN | spec 해시를 참조하는 plan·파일 범위·독립 역할·검증 명령·필요 승인 |
| BUILD | 승인된 모든 명령의 Builder 성공 로그 |
| VERIFY | 동일 코드와 계약의 독립 Verifier 성공 로그 |
| REVIEW | 최신 독립 리뷰 pass·검증·DONE 또는 릴리스 승인 |
| RELEASE | 승인된 배포 실행 증거·확인 |
| OBSERVE | 관측 실행 증거·운영 확인·DONE |

<task>/run/opd2-ledger.json은 opd2 자체 상태(모드·workspace·repo·baseline·evidence·approvals·
reviews·retries)가 담긴 append-only 논리 journal이다(Store.save()). 파일 lock
(`<task>/run/.opd2-ledger.lock`)과 atomic replace로 쓰고, 각 이벤트의 seq/previous/hash로
이전 이벤트 해시를 연결한다. 별도 조회 사본 파일은 두지 않는다 — lifecycle.py status는
Store.state()로 원장 마지막 이벤트의 state를 그 자리에서 파생한다. journal 손상(해시·seq
불일치)은 중단한다. 해시 체인은 우발적 손상 탐지이며 파일 소유자에 대한 암호학적 인증은
아니다. <task>/state.json·STATE.md·AGENTIC-LOG.md는 opd2가 직접 쓰지 않는다 — 단계 진행
상태(task_steps)의 SSOT와 그 사람용 투영은 state-tool이 소유하며, Store.save()가 전이마다
`state-tool mark`를 호출해 그 갱신을 위임한다.
STATE.md는 사람이 보는 현황이다. agentic은 초기화부터, semi-agentic은 BUILD 진입부터
AGENTIC-LOG.md를 도구가 렌더링한다. 두 Markdown 파일도 projection이므로 직접 상태를 수정하지 않는다.
응답의 transition_action=continue/complete/await_user/blocked와 report_type을 소비한다.

transition은 한 단계만 이동한다. 실패 exit 2이면 상태 유지.
검증 실패는 수정 요청 후 rewind --gate BUILD. 요구 변경은 INTENT, 설계 변경은 DESIGN,
계획 변경은 PLAN으로 rewind한다. 이후 증거·승인·리뷰는 무효화한다.
최초 baseline은 유지하며 전체 변경 범위를 검사한다. 재작업은 누적 3회까지다.

block --reason은 차단을 기록하고 unblock --reference ... --reason ...은 해결 근거를 기록한다.
정상 전이는 계속 진행한다. 실제 외부 계약·권한 결정은 모드에 관계없이 차단한다.

## PLAN 사전심사 상한과 지적 추적

- 상한: 사전심사 fail 기록이 3건이 되면 도구가 `await_user: PLAN pre-review fail limit (3)
  reached; user release required`로 상한 대기에 들어간다. 상한 대기 중에는 `review --call`,
  `transition`(및 `verify-mark`), `rewind`, `unblock`을 거부한다. 이 상한은 rewind 상한
  (`retries <= 3`)과 별개다.
- 해제: `plan-review-reset --actor <실명> --reference <사용자 메시지> --reason ...`만 상한을
  푼다. `--actor`는 실명 사용자여야 하며 `coordinator`·`builder`·`verifier`·`reviewer`는 거부된다.
  `--reference`는 실제 사용자 메시지다.
- 기록 필드: 사전심사 기록은 `findings`(새 지적), `resolutions`(이전 지적 해소 보고),
  `open_findings`(그 기록 이후 남은 미해소 지적)를 가진다. 원장의 `plan_review_floor`는
  집계·추적의 시작 지점이며 해제 시 현재 기록 수로 올라간다(기록 이력은 보존). rewind는 사전심사 기록과 `plan_review_floor`를
  초기화한다. 새 키가 없는 변경 전 기록은 집계·추적에서 제외한다.
- 한계: `resolved` 보고의 내용상 진위는 도구가 검증하지 못하고 독립 Reviewer의 판단에
  맡긴다. 도구가 보증하는 것은 보고의 완전성(전건 보고·id 일치)이다.

## AC-4 실측 — lease·Stop·checkpoint·finalize

AC-4의 lease·Stop·checkpoint·finalize는 opd2 전용 코드 없이 FW 공통 메커니즘으로 자동
적용됨 — 근거: (1) lease — `opal/tools/state-tool/state_tool.py:3991`(cmd_advance)·`:4298`
(cmd_mark)이 상태 전이 진입 경계에서 `_claim_task_lease_if_needed(task_path)`(정의 `:846`)를
skill 조건 없이 호출하며, lifecycle.py의 Store.save()가 전이마다 호출하는 `state-tool mark`
(`scripts/lifecycle.py:172-177`)가 이 경로를 그대로 탄다. (2) Stop — `~/.opal/tools/
ownership-tool/ownership_tool/stop_evaluator.py`·`stop_hook.py`에 "skill" 조건 분기가 전혀
없다(grep 0건) — registry·state.json 기반 판정이며 skill 이름으로 종료 허용 여부를 가르지
않는다. (3) checkpoint/finalize — `opal/tools/worktree-tool/worktree_tool.py`의
`cmd_checkpoint`(`:2296`)·`cmd_finalize`(`:2878`) 본문에도 "skill" 조건 분기가 없다.
`--stage`(`:3102`, `p_checkpoint.add_argument("--stage", required=True)`)는 enum이 아닌 자유
문자열이며 소유권 1:1·branch 일치·staged scope 검사에만 쓰이고, registry(meta.json) 발급값
기반 공통 경로로 전 태스크에 동일 적용된다. TEST-SCENARIO.md S-11(Stop 차단+재개 안내)·
S-12(checkpoint 커밋 성공)가 이 실측 결과에 대응한다.
