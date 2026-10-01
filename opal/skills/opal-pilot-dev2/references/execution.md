# 기존 opd 동작 연결

OPAL 설치 루트 기본값은 ~/.opal이다. 기존 references/harness/modes.md,
worktree.md, task-process.md가 모드/작업본 운영의 원문이다. 사용 시 해당 설치의
관련 계약을 읽는다. 기존 opd 스킬은 비교 근거이며 opd2 전체 단계 엔진이 아니다.

## 신규

scripts/opd2.py resolve-start <예정-task> --new-task [--semi-agentic|--agentic] [--wt|--no-wt]
는 기존 resolver에 --skill opd를 전달한다. 사용하는 결과는 effective_mode,
workspace, actor다. init_args는 기존 opd 행 구성이므로 opd2 초기화에 사용하지 않는다.

wt면 기존 task-process의 채번·프로젝트 준비 후 아래 기존 도구를 호출한다.

~/.opal/tools/worktree-tool/run.sh create --project-root <허브> --task <NNN> --skill opd2 --task-folder <basename>

도구 원문을 receipt JSON으로 보존한다. 발급된 allocator_root, task_home, task_path,
worktree_root만 사용한다. .opal/worktree.json이 없으면 기존 init 초안과 실제 프로젝트
정보로 설정을 확정한다. pending_setup은 실행 결과가 아니므로 따로 환경을 준비한다.

python3 <skill>/scripts/lifecycle.py init <발급-task> --repo <발급-root> --change-id <id> --mode <mode> --workspace worktree --worktree-receipt <receipt>

no-wt는 --workspace hub로 초기화한다. wt 실패를 hub로 폴백하지 않는다.

scripts/worktree.py는 create/status/checkpoint/finalize/remove를 기존 worktree-tool에,
launch/read/recover/close를 기존 worktree-launcher에 그대로 전달한다. 반환 코드와 승인·소유권
검사를 바꾸지 않는다. 예: python3 <skill>/scripts/worktree.py create --project-root <허브> ...

## 재개

opd2 자체 상태(모드/workspace/repo/baseline·evidence·approvals·reviews·retries의 해시 체인
원장)는 <task>/run/opd2-ledger.json이다. lifecycle.py status로 저장 mode/workspace/repo/stage를
읽는다(Store.state()가 원장 마지막 이벤트의 state를 그 자리에서 파생하며 별도 조회 사본 파일은
없다). 명시 모드 변경은 set-mode --mode ... --reason ... --reference ...로 기록한다.
작업본은 변경하지 않는다. 기존 opd2.py resolve-start의 state.json 경로는 legacy 호환
진단용이다.

<task>/state.json(state-tool)이 단계 진행 상태(task_steps)의 유일한 SSOT다. lifecycle.py는
자체 게이트(원장 전이 조건)를 먼저 판정하고, 통과한 전이에서만 대응 task_steps 키를
`state-tool mark <task> --task-step <key> --done`으로 커밋한다 — Store.save()가 kind=='transition'
이벤트마다 이 호출을 수행하며, state-tool mark가 비0 종료면 ValueError를 던져 원장도 커밋하지
않는다("state-tool mark 성공 → 원장 커밋" 순서 고정). 즉 opd2 lifecycle는 기존 state-tool
init/advance/mark를 우회하지 않고 그 위에서 동작한다.

## 소유권·세션 기동

기존 ownership/launcher 계약을 사용한다. 다른 세션 lease를 탈취하지 않는다.
기존 launcher가 opd state.json을 요구할 수 있으므로 현재 설치의 호환 조건을 확인한다.
지원되지 않으면 가짜 opd 상태를 만들지 않고, lease를 가진 현재 세션이 발급 작업본에서
실행하는 기존 허브 실행 경로를 사용한다. 새 세션에는 이 스킬과 canonical task 재개를 전달한다.
Codex 기동은 설치된 codex --help의 --no-daemon 지원을 확인한다.

## 체크포인트·마감

기존 worktree-tool checkpoint를 호출한다. mode는 그대로 전달한다.
단계 매핑: PLAN→PLAN, BUILD→EXECUTE, VERIFY/REVIEW→TEST, CLOSED→CLOSE.
이 매핑은 `worktree-tool checkpoint --stage` 인자 전용이다 — `--stage`는 소유권·branch·staged
scope 검사에만 쓰이는 자유 문자열(enum 아님)이라, pipeline.json 행 stage 어휘(TASK/DESIGN/
PLAN/EXECUTE/VERIFY/CLOSE)와는 독립된 별개 분류이며 opd2가 신설한 `VERIFY` 행 stage와 충돌하지
않는다.
--owned-scope에 소유 파일만 전달한다. semi-agentic checkpoint는 기존 도구의 PLAN/CLOSE
승인 경계를 따른다. --approved는 실제 승인 근거가 있어야 한다.
registry_write_denied면 정확한 허브 메타 권한을 요청하고 같은 명령을 재실행한다.

DONE.md에 기존 finalize의 '## 회고적 학습 후보'를 포함한다. 기존 finalize/status/
merge/remove 계약과 권한을 유지한다. 도구가 opd2 상태를 읽지 못하면 실패와 잔여 작업본을
보고한다. 성공 위장이나 강제 회수는 금지한다.

기존 생성·소유권·checkpoint 도구의 차단 규칙을 재사용한다. 전용 터미널/hook/배포
환경의 설치 상태까지 이 패키지가 보장하지 않는다. 통합 테스트에서 실제 실행 범위를 밝힌다.
