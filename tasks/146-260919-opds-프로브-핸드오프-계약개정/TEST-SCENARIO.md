---
template: sdlc-v2
---
# TEST-SCENARIO: OPPB Environment Probe 구조적 블로커 해결

> 입력: [TASK.md](TASK.md), [PLAN.md](PLAN.md) | 작성자: PM

## Setup

- 환경: 태스크 146 worktree의 소스와 승인 후 설치되는 `~/.opal` 설치본을 사용한다. probe 명령은 실제 프로젝트 worktree가 아니라 `/tmp` 아래 실제 Git fixture 또는 태스크 142의 원본 밖 격리 clone에서 공개 CLI `run.sh probe`로만 실행한다.
- 공통 데이터: `.gitattributes`에 `/tasks/ export-ignore`를 둔 tracked fixture, 순차 bootstrap이 ignored `dep-cache/ready`를 만드는 fixture, 서로 다른 sentinel을 쓰는 두 비-bootstrap 명령, 태스크 142 현행 `.oppb-probe-commands.json`, 태스크 142 capsule·profile·state와 Git status의 작업 전 SHA-256 기준선.
- 대역 사용과 한계: 사용하지 않는다. Python 내부 심볼 mock/patch 없이 실제 Git 저장소, subprocess, 공개 CLI, 실제 source/install 경로를 사용한다.
- 실행 조건: 자동 실행. 구현 전 RED는 승인 후 W-1에서만 실행하며, 이 문서 작성과 PLAN 승인 대기 중에는 소스·계약·테스트·설치본 및 태스크 142를 변경하지 않는다.

## Scenarios

| ID | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|
| S-1 | AC-1, AC-7, C-2, C-5, C-8 | tracked `tasks/fixture/input.txt`와 `/tasks/ export-ignore`를 가진 실제 Git fixture가 있고 현행 probe 코드를 사용함 | 공개 CLI로 입력 파일 존재를 요구하는 관측 명령을 seal한다 | 현행 코드는 `probe_command_failed`와 그 command id를 반환해 결함을 재현한다. 원 fixture의 branch·HEAD·공유 index·status·파일 hash는 실행 전후 동일하다 | `test_probe.py` subprocess/public CLI, `/tmp` real-git fixture, mock 없음 | 구현 전 RED |
| S-2 | AC-2, AC-7, C-2, C-5, C-7, H-1 | S-1과 같은 fixture에 snapshot 수정이 적용됨 | 같은 관측 명령을 seal하고 원 fixture의 ref·HEAD·index hash·status·tracked/untracked/ignored 파일 hash를 전후 비교한다 | export-ignore된 tracked 입력까지 accepted HEAD snapshot에 존재해 seal이 성공한다. 원본에는 ref 전진·commit·checkout·reset·clean이나 파일 변화가 없고 공유 index도 동일하다 | 공개 CLI integration test와 Git/hash 결정론 검사 | 구현 후 |
| S-3 | AC-3, AC-7, C-2, C-4, C-8 | bootstrap-1이 디렉터리를 만들고 bootstrap-2가 준비물을 완성하며 build가 그 준비물을 요구하는 실제 Git fixture와 현행 probe 코드가 있음 | 공개 CLI로 선언 순서의 bootstrap 두 건과 build를 seal한다 | 현행 코드는 준비 산출물 비전달로 build command id의 `probe_command_failed`를 반환한다 | `test_probe.py` subprocess/public CLI, `/tmp` real-git fixture | 구현 전 RED |
| S-4 | AC-3, AC-4, AC-7, C-4, H-2, H-3 | S-3 fixture와, build-A가 sentinel을 만들고 build-B가 그 sentinel 부재를 요구하는 sibling fixture에 수정 코드가 적용됨 | bootstrap 두 건과 두 비-bootstrap 명령을 seal하고 profile의 command별 outputs·status·failure 귀속을 검사한다 | bootstrap은 선언 순서로 누적되어 build가 준비물을 소비한다. 각 bootstrap delta는 자기 command id에 정확히 한 번 귀속된다. 두 비-bootstrap은 동일 준비 baseline에서 독립 분기해 서로의 sentinel을 보지 않으며 결과는 자기 command id에만 귀속된다 | 공개 CLI integration test, 생성 profile JSON assertion | 구현 후 |
| S-5 | AC-5, AC-7, C-6, C-7, H-4 | timeout 생략, explicit 180, 작은 양의 정수, bool·0·음수·문자열 값을 가진 command specs가 있음 | 각 spec의 seal 또는 입력 hash 계산 경로를 공개 CLI로 실행하고 timeout command를 실제 subprocess로 만료시킨다 | 생략은 180초 기본이며 explicit 180과 canonical freshness가 동등하다. 유효한 override는 실행과 hash에 반영된다. invalid 값은 명령 실행 전 `commands_invalid`로 거부된다. 만료 실패는 `probe_command_failed`에 해당 command id를 보존한다 | 실제 CLI/subprocess 기반 parameterized integration test, 짧은 timeout | 구현 후 |
| S-6 | AC-6, AC-10, C-3, C-6, H-5 | runtime 구현과 계약 문서 변경이 준비됨 | `op-oppb-project-slice/SKILL.md` §3.2와 proposal P2.2를 코드·테스트 계약에 대조하고 금지·잔존 문장을 검사한다 | 두 문서가 전체 tracked-tree snapshot, bootstrap 준비 baseline, 비-bootstrap sibling 격리, `timeout_seconds`를 동일하게 설명한다. `verify_command`·전체 테스트는 probe 등재 대상이 아니며 Supervisor 판정 책임과 late-discovery/`scope_violation`/exit 계약은 유지된다 | `rg`/구조 대조 및 관련 회귀 테스트 | 구현 후 |
| S-7 | AC-7, AC-10, C-1, C-2, C-3, C-5, C-6, C-7 | S-1~S-6 변경이 source에 적용됨 | `test_probe.py`와 `opal/tools/oppb-runtime-tool/tests/` 전체를 실행하고 변경 경로를 검사한다 | 신규 snapshot/bootstrap/isolation/timeout/무오염 테스트와 기존 late discovery·`scope_violation`·budget·CLI exit 테스트가 모두 통과한다. mock/patch와 task142 변경은 없고 구현 변경은 PLAN W-1~W-3 범위에 한정된다 | 실제 pytest 전체 회귀, `git diff --name-only`, task142 기준선 hash/status 대조 | 구현 후 |
| S-8 | AC-8, AC-10, C-2, C-3, C-5, C-7, H-6 | source 회귀가 통과하고 사용자 승인 후 `scripts/install-mac.sh`로 설치됨 | source/install `probe.py` hash, slice skill 핵심 계약, run.sh 실행 권한을 비교하고 소스 밖 `/tmp` fixture에서 설치본 절대경로 CLI로 S-2·S-4·S-5 핵심 사례를 실행한다 | 설치본이 source와 일치하고 신규 fixture를 성공·봉인한다. 실행 경로가 source를 우연히 참조하지 않으며 task144 역할 분리가 유지된다 | 설치 후 sha256/권한 검사와 installed CLI integration | 설치 후 |
| S-9 | AC-9, AC-10, C-1, C-2, C-3, C-5, H-1, H-4, H-5, H-6 | 태스크 142 원본의 capsule·profile·state hash와 Git status 기준선, 원본 밖 격리 clone, 설치본 CLI가 준비됨 | clone에서 태스크 142 현행 `.oppb-probe-commands.json` 8건을 설치본으로 seal하고 profile을 검사한 뒤 원본 기준선을 다시 계산한다 | 8명령이 모두 exit 0이고 profile이 봉인된다. verify command는 probe에 추가되지 않는다. 태스크 142 원본 파일·profile·state hash와 Git status는 전후 완전히 동일하다 | `/tmp` external clone의 installed public CLI, JSON assertion, 원본 read-only hash/status 비교 | 설치 후 |
