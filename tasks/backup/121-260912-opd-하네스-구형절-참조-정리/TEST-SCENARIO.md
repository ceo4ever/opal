---
template: sdlc-v2
---
# TEST-SCENARIO: opal-harness.md 구형 절 참조 정리

> 입력: [TASK.md](TASK.md), [PLAN.md](PLAN.md) | 작성자: PM

## Setup

- 환경: 코드 작업본 `.opal-worktrees/task_121`(브랜치 `feat/OP-TASK-121`, base `main`). 문서 변경만이므로 별도 서비스·데이터가 필요 없다.
- 공통 데이터: 없음.
- 대역 사용과 한계: 사용하지 않음. 인용 해석 여부는 grep과 실제 절 존재 확인으로 판정하며, 회귀는 실제 pytest 실행으로 판정한다.
- 실행 조건: 자동 실행.

## Scenarios

| ID | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|
| S-1 | AC-1, AC-4, C-3 | 전환된 인용처 2곳 | `tools.md`와 `opal-project-init/SKILL.md`의 포인터가 가리키는 절을 owner 문서에서 찾는다 | 두 포인터가 실존 절을 가리킨다. `worktree.md`의 `## 모드 축과 직교하는 별개 축`·`## --wt 미사용 시 = 현행 동작 100% 유지`와 `task-process.md` 스텝 4.5가 실재한다. 규범 문장이 인용처로 복제되지 않았다 | 결정론 검사 — grep + 절 존재 확인 | 구현 후 |
| S-2 | AC-2, H-1 | 저장소 활성 문서 전체 | `grep -rn "opal-harness.md §2.5"`를 `opal/`·`docs/`·`skills/`에 실행(역사 `tasks/`와 `docs/proposals/` 제외) | 매칭 0건이다. 매핑 행 제거 직전에도 같은 검사가 0건이어야 제거에 진입한다 | 결정론 검사 — grep | 구현 후 |
| S-3 | AC-3, C-1 | 개정된 `opal-harness.md` | 구형 절 참조 호환 매핑 표를 읽어 `§2.5` 행 부재와 다른 행 보존을 확인 | `§2.5` 매칭 0건이고 표 자체는 남아 있으며 다른 매핑 행이 변경되지 않았다 | 결정론 검사 — 문서 확인 + git diff | 구현 후 |
| S-4 | AC-5, H-2 | `worktree-tool` 스위트 | `pytest opal/tools/worktree-tool/tests/test_worktree_tool.py -q` 실행 | 83 passed / 실패 0. `test_s24`의 구형 절 참조 호환 매핑 단언이 깨지지 않는다 | integration — 실제 pytest | 구현 후 |
| S-5 | C-4 | 변경된 Markdown 3파일 | `변경이력`·`Changelog`·`개정 이력` 절이 신규 생성됐는지 검사 | 신규 수기 누적 이력 절 0건 | 결정론 검사 — grep | 구현 후 |
| S-6 | C-2 | 배포본과 프로젝트 소스 | 작업 중 `~/.opal/` 수정 흔적을 확인 | 배포본 직접 편집 0건. 변경은 전부 프로젝트 소스에서 이뤄졌다 | 결정론 검사 — 수정 시각·경로 확인 | 구현 후 |
