# DONE: opal-harness.md 구형 절 참조 정리

## 결과

`opal-harness.md`의 구형 절 참조 호환 매핑에서 `§2.5 워크스페이스 축` 행이 제거됐다. 그 행에 의존하던 인용 두 곳이 owner 문서를 직접 가리키도록 바뀌었기 때문이다 — `tools.md`는 축 정의와 `--wt` 미사용 보장을 `harness/worktree.md`의 두 절로, 생성·복구 절차를 `harness/task-process.md` 스텝 4.5로 나눠 지목한다. `opal-project-init/SKILL.md`는 축 정의만 필요하므로 `worktree.md` §모드 축과 직교하는 별개 축 하나를 가리킨다.

태스크 118이 이 행을 제거하려다 살아 있는 인용 때문에 보류했던 항목이다. 인용을 먼저 owner로 돌리고 나서 행을 걷어내는 순서로 해소했다.

**유지된 것** — 매핑 표의 다른 행은 변경되지 않았다. 규범 원문을 인용처로 복제하지 않고 포인터만 교체했다.

이 태스크는 **워크트리 태스크 캡슐 소유권 계약의 첫 실사용 사례**다. 번호 발급 → worktree 생성 → 워크트리 안 태스크 폴더 생성 → TASK.md → `state init` 순서로 만들어졌고, 코드 변경과 태스크 기록이 같은 브랜치에 있다.

## 변경 파일

- `opal/core/references/opal-harness.md`
- `opal/core/references/tools.md`
- `opal/skills/opal-project-init/SKILL.md`

## 검증

- AC-1·AC-4 — 교체된 포인터가 실존 절을 가리킨다. `worktree.md`의 `## 모드 축과 직교하는 별개 축`(`:9`)·`## --wt 미사용 시 = 현행 동작 100% 유지`(`:18`)와 `task-process.md` 스텝 4.5가 모두 실재한다.
- AC-2 — `grep -rn "opal-harness.md §2.5"`를 `opal/`·`docs/`·`skills/`에 실행해 **0건**(역사 `tasks/` 기록과 `docs/proposals/` 제외).
- AC-3 — `opal-harness.md`의 `§2.5` 매칭 **0건**. 다른 매핑 행은 무변경.
- AC-5 — `pytest opal/tools/worktree-tool/tests/test_worktree_tool.py -q` → **83 passed**. `test_s24`의 구형 절 참조 호환 매핑 단언이 깨지지 않았다.

## 회고적 학습 후보

없음

## 참고

이 태스크는 태스크 119(Phase 2)의 파일럿 대상으로 생성됐다. 수명주기 검증 결과는 `tasks/119-260912-opd-워크트리-태스크캡슐-소유권-파일럿/PILOT-EVIDENCE.md`가 소유한다.
