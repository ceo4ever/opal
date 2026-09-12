---
template: sdlc-v2
---
# TEST-SCENARIO: GC 검사 역량의 공통 스킬 분리

> 입력: [TASK.md](TASK.md), [PLAN.md](PLAN.md) | 작성자: PM

## Setup

- 환경: macOS, 프로젝트 루트 `/Volumes/Data/AIStudio/workspace/ai-framework`. python3·node·git 사용 가능. 검증 명령은 모두 프로젝트 루트에서 실행한다.
- 공통 데이터: 검사 실행 검증(S-2·S-5·S-7·S-9)은 `opal/skills/opal-pilot-gc/SKILL.md` 1개 파일만을 `target_files`로 주는 최소 입력을 사용하고, 산출물은 태스크 폴더 하위 임시 출력 디렉터리에 쓴다.
- 대역 사용과 한계: 사용하지 않음. 검사 스킬은 LLM 워커가 수행하므로 S-2·S-5·S-7·S-9는 실제 에이전트 디스패치로 확인하며, 문서 문안 검사(grep)로 대신하지 않는다.
- 실행 조건: S-17만 `scripts/install-mac.sh` 실행 후 확인하므로 배포 승인이 필요하다. 나머지는 자동 실행한다.

## Scenarios

| ID | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|
| S-1 | AC-1, C-4 | W-2~W-4 완료 상태 | `ls opal/skills/op-gc-security/SKILL.md opal/skills/op-gc-convention/SKILL.md opal/skills/op-gc-report/SKILL.md` 및 `node opal/tools/skill-registry/skill-registry.js validate` 실행 | 세 SKILL.md가 모두 존재하고 이름이 `op-gc-*` 규칙을 따르며, registry validate가 unregistered·dangling 0건으로 종료 | integration, 셸 | 구현 후 |
| S-2 | AC-1 | W-2 완료, `opal-pilot-gc` 미실행 | `op-gc-security/SKILL.md`만 경로로 주고 워커를 직접 디스패치해 `target_files`=`opal/skills/opal-pilot-gc/SKILL.md` 1건을 검사시킨다 | Pilot 태스크 채번·state.json 생성 없이 `GC-SECURITY-{ts}.md`와 `gc-findings-security-{ts}.json`이 지정 출력 디렉터리에 생성된다 | integration, 에이전트 디스패치 | 구현 후 |
| S-3 | AC-2, C-6 | W-6 완료 | `git diff --exit-code -- opal/skills/opal-pilot-gc/references/pipeline.json`, `grep -n -e close.done_md -e "--owner user" -e "CLOSE로 진행할까요" opal/skills/opal-pilot-gc/SKILL.md`, `python3 -m unittest discover -s opal/tools/state-tool/tests -t .` 실행 | pipeline.json diff 0(exit 0), 세 Gate 문안 전건 매칭, state-tool 테스트 전건 통과 | integration, 셸 | 구현 후 |
| S-4 | AC-3, C-5 | W-5 완료 | `grep -rn -e base-security-checklist -e base-convention-checklist -e report-security-template -e report-convention-template opal/ docs/ scripts/`와 `grep -n -e OWASP -e "CWE-" -e SANS -e fingerprint -e auto_fixable opal/agents/opal-security-checker/AGENT.md opal/agents/opal-convention-checker/AGENT.md` 실행 | 두 grep 모두 0건(구형 잔존 0). 같은 두 AGENT.md에 `skill_path`가 각 1건 이상 존재(신형 채택) | integration, 셸 | 구현 후 |
| S-5 | AC-4 | W-2 완료. 대상 목록에 staged가 아닌 파일 1건과 untracked 파일 1건을 섞어 준다 | 워커에 `target_files` 2건을 주고 검사시킨 뒤 결과 JSON의 `checked_files`를 입력과 비교 | `checked_files`가 입력 `target_files`와 정확히 같고 git 상태로 축소되지 않는다. 축소가 발생하면 `status`가 `partial`이고 사유가 `missing_capabilities`에 남는다 | integration, 에이전트 디스패치 | 구현 후 |
| S-6 | AC-5 | W-2, W-3 완료 | S-2와 같은 방식으로 보안·컨벤션 검사를 각 1회 실행하고 두 결과 JSON의 finding 객체 키 집합을 비교 | 두 JSON의 finding이 동일한 필드 이름을 쓰고, `severity`·`confidence`·`disposition`·`source_tier`가 각각 독립 필드로 존재한다 | integration, 에이전트 디스패치 | 구현 후 |
| S-7 | AC-6 | W-4 완료. 한 check 결과의 `status`를 `partial`로 두고 `missing_capabilities`를 1건 이상 채운 입력 | `op-gc-report`에 두 check JSON과 `baseline: none`을 주고 실행 | `gc-report.json`의 `verdict`가 `INCOMPLETE`이며 PASS 계열이 아니다. `GC-REPORT-{ts}.md`에 검사 결측이 별도 항목으로 표시된다 | integration, 에이전트 디스패치 | 구현 후 |
| S-8 | AC-7 | W-4 완료. 직전 실행의 `gc-report.json`을 baseline으로 주고, finding 중 1건은 동일 `fingerprint`, 1건은 신규, 1건은 baseline에만 존재 | `op-gc-report`를 baseline 경로와 함께 실행 | `gc-report.json`의 `delta`가 신규 1·잔존 1·해결 1로 분류되고 Markdown 보고서에 같은 구분이 표시된다 | integration, 에이전트 디스패치 | 구현 후 |
| S-9 | AC-8, H-4 | W-3 완료. `docs/CONVENTIONS.md`가 없는 임시 프로젝트 루트를 대상으로 지정 | `op-gc-convention` 워커를 디스패치해 파일 1건을 검사시킨다 | 검사가 중단되지 않고 보고서가 생성된다. `status`가 `partial`, 모든 finding의 `disposition`이 `advisory`, `missing_capabilities`에 기준 문서 결측이 기록되며, 어떤 advisory도 차단 사유로 계산되지 않는다 | integration, 에이전트 디스패치 | 구현 후 |
| S-10 | AC-9 | W-8 완료 | `docs/PROJECT.md` §주요 컴포넌트 (GC 파이프라인) 표와 `docs/ARCHITECTURE.md`의 스킬·에이전트 목록을 실제 파일 트리와 대조 | 신설 3종이 모두 등재되고, `opal-pilot-gc`가 thin wrapper로, 두 checker가 공통 스킬 실행 role로 기술되며, 표에 없는 유령 컴포넌트가 없다 | manual 문서 대조, 셸 | 구현 후 |
| S-11 | C-1 | S-2 실행 직후 | 검사 실행 전후로 `git status --porcelain`을 비교 | 검사 대상 소스 파일에 변경이 없고, 새로 생긴 파일은 지정 출력 디렉터리의 보고서뿐이다 | integration, 셸 | 구현 후 |
| S-12 | C-2 | W-2, W-3 완료 | 두 SKILL.md의 기준 선택 순서 절을 읽고 `docs/SECURITY.md`·`docs/CONVENTIONS.md`가 1순위인지, 공식 표준이 프로젝트 기준을 덮어쓰는 문안이 있는지 확인 | 프로젝트 문서가 1순위로 명시되고, 공식 표준이 프로젝트 기준을 대체한다는 문안이 없다 | manual 문서 검토 | 구현 후 |
| S-13 | C-3 | W-2, W-3, W-4 완료 | 세 SKILL.md에서 외부 자료 취득·실행 관련 지시를 검토하고 `grep -n -e "curl" -e "npm install" -e "pip install" -e "실행한다"` 로 후보를 추출 | 외부에서 받은 스킬·스크립트를 설치하거나 실행하라는 지시가 없고, 외부 자료는 읽기 전용 기준으로만 사용한다는 `[MUST]`가 존재한다 | manual 문서 검토, 셸 | 구현 후 |
| S-14 | C-7 | 전체 W 완료, `scripts/install-mac.sh` 실행 전 | `git status --porcelain`과 `ls ~/.opal/skills/` 결과에서 `op-gc` 접두 디렉터리 유무 확인 | 변경 파일이 전부 `opal/`·`docs/`·`scripts/`·`tasks/` 이하이고, install 실행 전 배포본에는 신설 스킬이 없다(직접 편집하지 않았음) | integration, 셸 | 구현 후 |
| S-15 | H-1 | W-3(파일 이동)과 W-7(경로 갱신) 완료 | `python3 scripts/tests/task113_bootstrap_audit.py --mode source` 실행 | exit 0으로 통과하며 이관된 체크리스트 경로를 정상적으로 읽는다 | integration, 셸 | 구현 후 |
| S-16 | H-2 | W-6 완료 | `python3 -m unittest discover -s opal/tools/memory-tool/tests -t .` 실행 | 전건 통과. 특히 `opal-pilot-gc/SKILL.md`의 `task-number --bump` 문구 존재를 요구하는 케이스가 실패하지 않는다 | integration, 셸 | 구현 후 |
| S-17 | AC-2, AC-4, H-3 | 전체 W 완료 후 `scripts/install-mac.sh` 실행 완료 | `//opgc --scope staged`를 1회 실행한다 | SCAN→CHECK→REPORT→CLOSE 4단계가 전환 전과 같은 순서·Gate로 진행되고, CHECK가 `~/.opal/skills/op-gc-*/SKILL.md`를 스킬 부재 없이 로드하며, SCAN이 확정한 파일 목록과 보고서의 `checked_files`가 일치한다 | E2E, 실제 pilot 실행 | 설치 후 |
