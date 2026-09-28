---
template: sdlc-v2
---
# TASK: 워크트리 registry 메타의 태스크별 폴더 분리와 워크트리 세션 쓰기 권한·기동 전 점검

## Problem

Codex로 실행한 워크트리 세션(태스크 162)이 허브 registry 메타 `.opal-worktrees/.meta/task_162.json`을 쓰지 못해 CLOSE 단계의 finalize에서 멈췄다. 원인은 Codex 샌드박스가 워크트리 폴더만 쓰기를 허용하는데, 메타는 워크트리 밖 형제 폴더에 모든 태스크의 파일이 한 폴더에 모여 있는 구조라는 점이다.

- 메타 경로는 태스크 번호만 다른 단일 폴더의 파일이다(`opal/tools/worktree-tool/worktree_tool.py:938-939`, `opal/tools/ownership-tool/ownership_tool/ownership_core.py:74-76`).
- 메타 쓰기는 같은 폴더에 임시 파일을 만든 뒤 교체하므로 파일 하나가 아니라 폴더 쓰기 권한이 필요하다(`opal/tools/worktree-tool/worktree_tool.py:1025-1031`).
- 따라서 폴더를 열어 주면 다른 태스크의 메타까지 쓸 수 있고, 열지 않으면 자식 세션이 자기 태스크 메타를 쓰지 못한다. 현재 하네스는 막힐 때마다 권한 상승을 요청하는 절차만 둔다(`opal/core/references/harness/worktree.md:140`).
- 권한 부족은 작업을 다 한 뒤 CLOSE에서야 드러나며, 기동 시점에는 아무것도 점검하지 않는다. Codex 기동 명령의 치환 토큰도 발화와 태스크 경로 2종뿐이라 쓰기 경로를 전달할 수단이 없다(`opal/tools/worktree-launcher/worktree_launcher/settings.py:46-47`).

## Proposed outcome

워크트리 태스크마다 registry 메타가 자기 전용 폴더를 갖고, 워크트리 세션은 작업이 끝날 때까지 그 폴더에만 쓰기 권한을 받는다. 이후 태스크별로 쓸 파일이 늘어나도 그 폴더 아래에 두면 권한 문제가 생기지 않는다. 런처는 세션을 띄우기 전에 필요한 권한을 점검하고, 부족하면 작업을 시작하기 전에 원인과 함께 멈춘다.

## Affected users and systems

- 사용자: `--wt` 태스크를 Codex 등 샌드박스가 있는 에이전트로 실행하는 캡틴
- 시스템: `worktree-tool`(메타 생성·조회·checkpoint·finalize·remove), `ownership-tool`(registry 해석·stop 판정), `state-tool`의 registry 조회, `worktree-launcher`(기동 명령·기동 전 점검), 설치 스크립트, 하네스 문서(`worktree.md`, `task-process.md`)
- 포함: 메타 저장 구조 변경, 워크트리 세션에 대한 태스크 메타 폴더 쓰기 권한 부여, 기동 전 점검
- 제외: git checkpoint·finalize 커밋의 권한 처리(허브 위임 방식은 후속 태스크). 이번 범위에서 git 쓰기는 기존 권한 상승 요청 절차를 유지한다

## Constraints

- C-1: 워크트리 세션에 `.meta/` 루트, 다른 태스크의 메타 폴더, 공유 `.git/`에 대한 쓰기 권한을 주지 않는다.
- C-2: 플랫폼별 차이(샌드박스 쓰기 경로 옵션 등)는 런처 설정과 설치 어댑터 계층에만 둔다. 샌드박스가 없는 세션(Claude)의 동작은 바뀌지 않는다.
- C-3: lease 저장 위치, canonical path 발급 계약, `allocator_root` 추론 금지 등 `opal/core/references/harness/worktree.md`의 기존 계약을 유지한다.
- C-4: 프로젝트 소스를 수정한 뒤 정식 install로 재배포하고 배포본으로 검증한다. `~/.opal/`을 직접 수정하지 않는다.
- C-5: 설치 스크립트나 도구에 Windows 미러가 있으면 같은 계약을 적용한다.

## Acceptance criteria

- AC-1: 새로 만든 워크트리 태스크의 registry 메타가 해당 태스크 전용 폴더 안에 저장되고, 메타 쓰기의 임시 파일과 lock 파일도 그 폴더 안에만 생긴다.
- AC-2: 메타 경로를 직접 조합하는 코드가 소스에 남지 않고, 모든 소비자가 단일 경로 계산을 거친다(구 구조 경로 조합 0건).
- AC-3: Codex 워크트리 세션 기동 명령에 해당 태스크 메타 폴더만 추가 쓰기 경로로 포함되고, `.meta/` 루트와 다른 태스크 폴더는 포함되지 않는다.
- AC-4: 실제 Codex 워크트리 세션(workspace-write 샌드박스)에서 자기 태스크 메타 폴더 쓰기는 성공하고 다른 태스크 메타 폴더 쓰기는 거부된다(실측).
- AC-5: 런처가 기동 전에 메타 폴더 준비 상태와 에이전트의 쓰기 경로 옵션 지원 여부를 점검하고, 실패하면 터미널을 띄우지 않고 원인 코드와 함께 종료한다.
- AC-6: 기동 전 점검은 공유 `.git` 쓰기 불가를 차단이 아닌 경고로 보고한다.
- AC-7: 하네스 문서가 메타 폴더 구조, 워크트리 세션 쓰기 권한 범위, 기동 전 점검 계약을 기술하고, 구 구조를 현재 사실로 기술한 문장이 남지 않는다.
- AC-8: 배포본 기준으로 AC-3, AC-4, AC-5를 공개 진입점에서 다시 확인한다.
