---
type: concept
title: 워크트리 세션 기동은 허브가 만들고 state init 이후에 띄운다
tags:
- worktree
- 세션
- 런처
- 소유권
sources:
- tasks/145-260919-opds-워크트리-터미널-런처-orca-배선/DONE.md
- opal/core/references/harness/task-process.md
- opal/core/references/harness/worktree.md
- task:164
related: [worktree-tool, worktree-locates-hub-by-issued-copy]
created: '2026-09-19'
updated: '2026-09-28'
status: draft
---
## 개요

워크트리 전용 세션을 띄울 때 **무엇을 누가 어느 순서로 하는가**는 임의 선택이 아니다. 허브가 만들고 워크트리가 이어받으며, 기동 시점은 `state init` **이후**로 고정된다. 역순은 구조적으로 성립하지 않는다.

## 순서가 고정되는 이유

워크트리 세션은 부팅 직후 `state.json`을 읽어 자기 태스크를 인지한다. 따라서 `state init` **전에** 터미널을 띄우면 첫 턴이 읽을 상태가 없다. 태스크 145에서 배선 지점을 스텝 4.5(워크트리 생성 직후)가 아니라 **스텝 5.5**(state init 직후)로 신설한 근거가 이것이다.

## 역순(터미널 먼저)이 성립하지 않는 이유

"새 터미널을 먼저 열고 거기서 워크트리를 만든다"는 구성은 `harness/worktree.md` D-20("워크트리는 허브를 추론하지 않는다")과 충돌한다. 워크트리가 아직 없으므로 그 세션은 사실상 **허브 세션 하나가 더 생긴 것**이고, 채번과 registry 쓰기를 두 허브 세션이 나눠 갖게 되어 태스크 번호 경합이 재발한다(실제 사건: 커밋 `effa610` "태스크 번호 143→144 재번호 — 다른 세션과 충돌").

## 시작 발화는 기동 명령 인자가 소유한다

터미널에서 LLM이 떠도 **첫 턴을 유발하는 무언가**가 필요하다. 이때 별도 캡슐 파일(`handoff.json` 류)이나 터미널 입력 채널(`terminal send`)을 만들 이유가 없다.

- **식별은 이미 해결돼 있다** — 워크트리와 canonical task는 1:1이고, `state.json`과 부트 브리핑이 다음 행을 소유한다.
- **파일은 첫 턴을 유발하지 못한다** — SessionStart hook은 세션 등록·`OPAL_SESSION_ID` 기록·lease claim만 하고 컨텍스트를 주입하지 않으며 전 경로 fail-safe exit 0이다.
- **입력 채널은 터미널마다 계약이 다르다** — orca는 `terminal send`(프롬프트 제출), cmux는 `send`+`send-key enter`(키 입력 에뮬레이션), 일반 터미널(iTerm·Terminal.app)은 채널 자체가 없다. "준비됐다"의 정의도 서로 달라 공통 계약을 만들 수 없다.

결론은 기동 argv에 발화를 실어 보내는 것이다. `--command 'claude "<태스크 경로> 이어서 수행"'` 한 번이면 orca·cmux·generic 셋 모두에서 동일하게 성립하고 타이밍 의존이 사라진다.

## 쓰기 범위와 기동 전 점검 (164)

- 워크트리 세션이 받는 추가 쓰기 경로는 **자기 태스크 메타 폴더 하나**다. `.meta/` 루트, 다른 태스크 폴더, 공유 `.git`은 주지 않는다. 샌드박스가 있는 에이전트(Codex)는 기동 명령 템플릿의 `{meta_dir}` 토큰으로 이 경로를 받고, 샌드박스가 없는 에이전트(Claude)의 기동 명령은 바뀌지 않는다(`opal/tools/worktree-launcher/worktree_launcher/settings.py:38`).
- 런처는 lease 이관과 터미널 기동 **전에** 점검한다. 메타 폴더가 준비돼 있고 쓸 수 있는지를 먼저 보고, 명령이 쓰기 경로 옵션을 쓰면 그 옵션이 에이전트 도움말에 있는지 확인한다. 실패하면 원인 코드와 함께 터미널을 띄우지 않고 끝나며 어댑터·lease를 건드리지 않는다(`opal/tools/worktree-launcher/worktree_launcher/cli.py:211,224`).
- 공유 `.git` 쓰기가 없다는 사실은 차단이 아니라 경고다. 체크포인트·finalize 커밋은 기존 권한 상승 요청 절차를 그대로 쓴다.
- 격리는 실제 배치에서만 증명된다. 세션 작업 디렉터리가 허브 루트이거나 허브가 임시 디렉터리 아래에 있으면 `.meta/` 전체가 기본 쓰기 영역에 들어가 격리가 거짓으로 실패·성공한다. 실측 조건은 작업 디렉터리=워크트리, `.meta/`=워크트리 밖 형제 경로, 임시 디렉터리 밖 허브로 고정해야 한다 (근거: task:164 AGENTIC-LOG #28).

## 회수 경계

- 워크트리 세션은 `completed_unmerged`까지만 진행한다.
- `main` merge·push·worktree 제거는 사용자 승인 뒤 **허브 세션**이 수행한다. 정책이자 git 제약이다 — 허브가 `main`을 체크아웃 중이면 워크트리는 `main`을 다시 체크아웃할 수 없다.
- 회수 시 터미널 스윕은 3중 가드(dirty → unpushed → unmerged) **통과 뒤**, `git worktree remove` **앞**에 둔다. 가드보다 앞에 두면 회수가 거부됐을 때 사용자 터미널만 날아간다.
- 허브가 워크트리 세션의 종료를 아는 수단은 registry `attribution_state`(`completed_unmerged`) 조회 하나다. 별도 통지 채널을 만들지 않는다.

## 남은 빈틈 (145 시점)

`execution_ownership.owner_session_id`가 `None`으로 남는다. 허브가 launch 시점에 새 세션의 id를 알 수 없기 때문이다. registry 전이는 receipt 2종만 요구해 성공하지만, 체크포인트 게이트는 `owner_session_id == OPAL_SESSION_ID`를 요구하므로 **워크트리 세션이 자율 커밋 자격을 얻지 못한다.** 워크트리 세션이 자기 id로 소유권을 확정하는 경로가 필요하다.

## 관련 페이지

- [[worktree-tool]]
- [[worktree-locates-hub-by-issued-copy]]
