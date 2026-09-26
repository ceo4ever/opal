---
template: sdlc-v2
---
# TASK: OPPB Environment Probe 구조적 블로커 해결

## Problem

태스크 144는 P2 probe에서 수용 판정용 `verify_command`를 제외하고 Supervisor 검증 책임을 유지해 역할 혼동을 해결했다. 그 결과 태스크 142의 현행 관측 전용 명령 8건은 격리 clone에서 모두 성공하고 환경 profile도 봉인된다. 그러나 probe 자체는 여전히 명령마다 `git archive HEAD` snapshot을 새로 만들고 폐기한다. 따라서 export-ignore된 tracked 입력을 읽는 관측 명령은 `probe_command_failed`가 되고, bootstrap이 만든 준비환경을 다음 build 명령이 소비할 수 없다.

두 결함은 현재 `test_probe.py` 8건이 다루지 않는다. 실제 공개 CLI로 만든 격리 fixture에서 export-ignore된 tracked fixture 확인 명령은 exit 23, bootstrap 산출물 소비 명령은 exit 24로 재현됐지만 기존 8건은 모두 통과했다. 태스크 142를 우연히 자족적인 명령 집합으로만 봉인하는 우회가 아니라, 원본 worktree를 오염시키지 않는 전체 tracked-tree 격리 snapshot과 bootstrap 준비 baseline 계약으로 남은 구조적 blocker를 해결해야 한다.

## Proposed outcome

Environment Probe가 export-ignore 여부와 무관하게 accepted HEAD의 전체 tracked tree를 격리 snapshot으로 물질화하고, bootstrap 명령을 순차 준비한 baseline을 후속 관측 명령이 소비할 수 있게 한다. 각 비-bootstrap 명령은 서로의 쓰기를 보지 않는 독립 snapshot에서 실행돼 명령별 관측 귀속을 유지한다. 명령별 timeout을 계약으로 선언할 수 있고, 태스크 144가 확정한 관측/판정 역할 분리는 그대로 유지된다.

소스·계약·공개 CLI 회귀 테스트·설치본을 함께 갱신하고, 설치본으로 태스크 142의 현행 P2 probe 명령을 원본 worktree 밖 격리 clone에서 성공·봉인한다. 작업 전후 태스크 142 원본의 파일 해시와 Git 상태는 동일해야 한다.

## Affected users and systems

영향 대상은 `oppb-runtime-tool` Environment Probe 구현과 공개 CLI 테스트, `op-oppb-project-slice`의 probe 명령 계약, OPPB P2.2 설계 문서와 설치 산출물이다. 직접 소비자는 태스크 142의 P2 `environment_seal`이며, 태스크 142 원본 worktree·상태·산출물은 읽기 전용으로 보존한다.

## Constraints

- C-1: 태스크 142 worktree와 그 안의 HANDOFF·state·설계 산출물·`.oppb-*`·봉인 profile을 수정하지 않는다.
- C-2: 실제 프로젝트 worktree에서 probe 명령을 직접 실행하지 않는다. accepted HEAD 기반 격리 snapshot에서만 실행한다.
- C-3: 태스크 144의 역할 분리를 유지한다. `verify_command`와 수용 판정용 전체 테스트는 probe에 다시 등재하지 않으며, 검증 면제로 해석하지 않는다.
- C-4: 각 비-bootstrap 명령은 같은 bootstrap 준비 baseline을 소비하되 서로의 출력은 보지 않아야 한다. 명령별 관측 귀속을 합치지 않는다.
- C-5: 원본 project branch·HEAD·공유 index·tracked/untracked/ignored 파일을 변경하지 않는다. ref 전진·commit·checkout·reset·clean을 호출하지 않는다.
- C-6: 기존 late discovery, `scope_violation` 승격, budget charge와 CLI exit 계약을 재정의하지 않는다.
- C-7: 구현은 Python 표준 라이브러리와 Git CLI만 사용하고 플랫폼 분기를 추가하지 않는다.
- C-8: 수정 PLAN을 사용자가 승인하기 전에는 소스·계약·테스트·설치본을 변경하지 않는다.

## Acceptance criteria

- AC-1: 공개 CLI RED fixture에서 현행 코드는 export-ignore된 tracked 입력 명령을 `probe_command_failed`로 거부하고, 수정 후 같은 명령을 성공·봉인한다.
- AC-2: snapshot은 `git archive`의 export 속성을 적용하지 않고 accepted `HEAD`의 전체 tracked tree를 물질화한다. 실행 전후 원본 branch·HEAD·공유 index·파일 해시와 Git status가 동일하다.
- AC-3: 둘 이상의 bootstrap 명령은 선언 순서로 준비 baseline을 만들고, 후속 관측 명령은 그 산출물을 소비한다. bootstrap별 출력은 해당 command id로 한 번만 귀속된다.
- AC-4: 비-bootstrap 명령 두 건은 동일 bootstrap baseline에서 각각 분기하며 서로의 생성물을 볼 수 없다. 각 출력과 실패는 자기 command id에만 귀속된다.
- AC-5: `commands[].timeout_seconds` 선택 계약을 지원한다. 생략 시 기존 180초를 유지하고, 유효하지 않은 값은 실행 전에 `commands_invalid`로 거부하며, timeout 실패는 해당 command id를 보존한다.
- AC-6: `op-oppb-project-slice`와 OPPB P2.2 문서는 전체 tracked-tree snapshot, bootstrap baseline, 명령별 timeout을 현행 계약으로 설명하면서 `verify_command` 미등재와 Supervisor 판정 책임을 유지한다.
- AC-7: `test_probe.py`에 export-ignore, bootstrap 전달, sibling 격리·귀속, timeout, 원본 worktree 무오염 회귀가 실제 Git 저장소·공개 CLI 기반으로 추가되고 전체 `oppb-runtime-tool` 회귀가 통과한다.
- AC-8: 소스 설치 후 `~/.opal/tools/oppb-runtime-tool/probe.py`와 관련 스킬의 계약이 소스와 일치하고, 설치본 공개 CLI로 신규 회귀 fixture가 통과한다.
- AC-9: 태스크 142의 현행 `.oppb-probe-commands.json`을 원본 밖 격리 clone에서 설치본 probe로 실행해 전 명령 exit 0과 profile 봉인을 확인한다. 태스크 142 원본의 capsule·profile 해시와 Git status는 작업 전후 동일하다.
- AC-10: 태스크 144가 해결한 관측/판정 역할 분리와 현재 8명령 seal 성공 기준선에 회귀가 없고, 기존 late discovery·`scope_violation`·exit 계약 테스트가 통과한다.
