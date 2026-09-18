---
template: sdlc-v2
---
# PLAN: opal-harness.md 구형 절 참조 정리

> 입력: [TASK.md](TASK.md)

## 참조 문서

| # | 유형 | 문서 | 경로 | 참조 이유 |
|---|------|------|------|----------|
| D-1 | 설계 | harness/worktree.md | `opal/core/references/harness/worktree.md` | 전환 대상 포인터가 가리킬 owner 절 |
| D-2 | 설계 | harness/task-process.md | `opal/core/references/harness/task-process.md` | 생성·복구 절차 owner(스텝 4.5) |
| D-3 | 소스 | opal-harness.md | `opal/core/references/opal-harness.md` | 구형 절 참조 호환 매핑 표 |

## Approach

**code-scan 선조회 결과** — `code-scan depends opal/core/references/opal-harness.md` 실행 결과 `depended by: (none)`이다. 즉 `@header` `depends`로 이 문서를 선언한 모듈이 없고, 이 태스크가 다루는 결합은 전부 **Markdown 본문의 문자열 인용**이다. 따라서 변경 영향 판정은 코드맵이 아니라 grep 전수(S-2)가 소유한다. `code-scan search "하네스"`는 `No files found` — `.opal/code-scan.json`의 스캔 scope가 `opal/`·`dashboard/` 코드 파일이고 `references/`의 Markdown은 `@header` 대상이 아니기 때문이며, 이 역시 변경 대상이 코드가 아님을 뒷받침한다.


인용을 먼저 owner 문서로 돌린 뒤 매핑 행을 걷어내는 순서로 수행한다. 역순으로 하면 행을 지우는 순간 두 인용이 dangling이 되고, 이것이 태스크 118이 제거를 보류한 이유다.

인용처마다 필요한 절이 다르다. `tools.md`는 축 정의와 `--wt` 미사용 보장, 그리고 생성·복구 절차를 함께 참조하므로 두 owner 문서를 나눠 지목한다. `opal-project-init/SKILL.md`는 축 정의만 필요하므로 한 절만 가리킨다. 규범 원문을 인용처로 복제하지 않고 포인터만 바꾼다(C-3).

## Decisions and contracts

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| D-1. 인용처별 지목 대상 분리 | `tools.md`는 `harness/worktree.md` §모드 축과 직교하는 별개 축 · §`--wt` 미사용 시 = 현행 동작 100% 유지와 `harness/task-process.md` 스텝 4.5를 함께 가리킨다. `opal-project-init/SKILL.md`는 §모드 축과 직교하는 별개 축 하나만 가리킨다 | 두 인용의 문맥이 다르다 — `tools.md`는 worktree-tool 사용 규약 전반을, SKILL은 `.gitignore` 선반영의 근거로 축 정의만 필요로 한다. 같은 포인터를 쓰면 SKILL 독자가 불필요한 절까지 따라가게 된다 |
| D-2. 매핑 행 제거 시점 | 인용 0건을 grep으로 확인한 **뒤** 제거한다 | 태스크 118이 같은 행을 제거하려다 인용 2건 때문에 보류했다. 순서를 뒤집으면 dangling이 생긴다 |
| D-3. 다른 매핑 행 불변 | `opal-harness.md` 구형 절 참조 호환 매핑의 나머지 행은 건드리지 않는다 | C-1. 다른 번호를 인용하는 문서가 있는지는 이 태스크 범위 밖이다 |

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. 인용처 2곳 owner 전환 | PM 직접 | `opal/core/references/tools.md`, `opal/skills/opal-project-init/SKILL.md` | `tools.md:1028`의 `opal-harness.md §2.5` 포인터를 `harness/worktree.md`의 두 절과 `harness/task-process.md` 스텝 4.5로 교체한다. `opal-project-init/SKILL.md:84`는 `harness/worktree.md` §모드 축과 직교하는 별개 축 하나로 교체한다. 규범 문장을 복제하지 않는다 | 없음 | P1 | AC-1, AC-4, C-3 |
| W-2. 매핑 행 제거 | PM 직접 | `opal/core/references/opal-harness.md` | 구형 절 참조 호환 매핑에서 `§2.5 워크스페이스 축` 행 1줄을 제거한다. 제거 전 `grep -rn "opal-harness.md §2.5"`로 활성 문서 인용 0건을 확인한다. 다른 행은 무변경 | W-1 | P2 | AC-2, AC-3, C-1 |
| W-3. 회귀 확인 | PM 직접 | 없음(검증 전용) | `pytest opal/tools/worktree-tool/tests/test_worktree_tool.py -q`로 `test_s24`의 구형 절 참조 호환 매핑 단언이 깨지지 않음을 확인한다 | W-2 | P3 | AC-5 |

## Risks

| 위험 | 깨질 수 있는 동작·계약 | 영향 | 설계 대응 |
|---|---|---|---|
| H-1. 매핑 행 제거가 미확인 인용을 끊는다 | 태스크 118 실측 당시 인용은 2건이었으나 그 뒤 다른 문서가 `§2.5`를 새로 인용했을 수 있다 | 활성 문서가 해석 불가능한 절 번호를 가리키게 된다 | W-2가 제거 **직전**에 grep을 다시 실행해 0건을 확인한다. 인용이 남아 있으면 제거하지 않고 보고한다 |
| H-2. `test_s24`가 매핑 표 존재에 의존한다 | 태스크 119가 이 단언을 "구형 절 참조 호환 매핑 존재"로 교체했다. 표 자체가 비면 단언이 깨진다 | worktree-tool 스위트가 실패한다 | 제거 대상은 표가 아니라 **행 하나**다. W-3이 스위트로 실증한다 |

## Release and recovery

- **적용 순서**: P1(W-1 인용 전환) → P2(W-2 행 제거) → P3(W-3 회귀 확인). 역순 불가 — D-2 근거.
- **검증 범위**: 결정론 검사(grep 인용 0건·매핑 행 부재·포인터 실존)와 `worktree-tool` 스위트 1종. 문서 변경이므로 동작검증 대상은 스위트 통과 여부뿐이다.
- **실패 시**: W-2 이후 스위트가 깨지면 W-2만 되돌린다(행 1줄 복원). W-1은 독립적으로 유효하므로 유지한다. 인용이 0건이 아니면 W-2에 진입하지 않는다.
- **검증 종료 지점**: AC-1~AC-5가 결정론 검사와 스위트로 모두 확인된 시점.
