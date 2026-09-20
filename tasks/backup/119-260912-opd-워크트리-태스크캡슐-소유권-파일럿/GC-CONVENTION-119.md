# GC CONVENTION REPORT — 2026-09-12T16-39-50

## 1. 헤더

- 실행 일시: 시작 2026-09-12 16:32:00 / 완료 2026-09-12 16:39:50 / 소요 약 8분
- 범위: `staged` — 태스크 119(20c38a4..25b8a8c, 코드 8파일) + 파일럿 121(86d8dcd, 코드 3파일) 변경분만. 태스크 캡슐(`tasks/119-*`, `tasks/121-*`)은 문서 컨벤션만 적용
- 에이전트: opal-convention-checker
- 기준 문서: `docs/CONVENTIONS.md` (허브+링크 미적용 — OPAL 자체는 단일 문서 모델, 문서 하단 "허브+링크 모델" 참고 절이 이를 명시) — 유일 기준으로 로드
- APPLY 수행 여부: N (수동 대기 — 본 에이전트는 진단 전담, 읽기 전용)
- **참고 문서 경로 갱신 알림**: 디스패치에 지정된 `checklist_path`/`template_path`(`~/.opal/skills/opal-pilot-gc/references/base-convention-checklist.md`, `report-convention-template.md`)가 더 이상 존재하지 않는다. 태스크 120("GC 검사 역량 공통 스킬 분리")이 두 파일을 각각 `~/.opal/skills/op-gc-convention/references/convention-categories.md`, `~/.opal/skills/op-gc-convention/references/report-template.md`로 이관했다(120은 본 검사 범위 밖). 이번 실행은 새 경로의 대체 문서를 로드해 진행했다 — PM은 opal-pilot-gc 디스패치 파라미터의 경로를 갱신 검토 바란다. `getsentry/code-review` 보조 참조 스킬은 이 환경의 `~/.opal/community-skills/`에 설치돼 있지 않아 카테고리 8(코드 품질) 보조 대조는 생략했다(강제 기준이 아니므로 체크 실패 아님).

---

## 2. 요약 지표

| 지표 | 값 |
|------|-----|
| 총 이슈 수 | 2 |
| 심각도 분포 | Critical 0 / High 0 / Medium 1 / Low 0 / Info 1 |
| 자동 수정 가능 | 0 |
| 수동 조치 필요 | 2 |
| 파일별 상위 Top 5 | `opal/tools/worktree-tool/tests/test_worktree_tool.py` (1건) / 커밋 메시지(비파일, 1건) |
| 카테고리별 빈도 | 문서화 (1 파일) / 코드 품질(커밋 규칙 관련, 1건) |
| Critical/High 수 | 0 |
| 문서 업데이트 제안 수 | 1 (새 카테고리 1건, 빈도 트리거 미발동) |

**PM Gate 판정: 통과 (Critical·High 0건).**

---

## 3. 수정 대상 (체크리스트)

### Critical (0건)

### High (0건)

(중점 확인 항목 중 "121이 `opal-harness.md`의 `§2.5` 매핑 행을 제거했으므로 그 번호를 인용하는 곳이 남아 있으면 즉시 High" 조건을 검사했다. 검사 범위 3파일(`opal-harness.md`, `tools.md`, `opal-project-init/SKILL.md`) 내 `§2.5` 잔존 0건, 새 인용처 `harness/worktree.md §모드 축과 직교하는 별개 축`·`§\`--wt\` 미사용 시 = 현행 동작 100% 유지`·`harness/task-process.md 스텝 4.5`가 모두 실존 절임을 확인했다. High 트리거 없음.)

### Medium (1건)

- [ ] GC-C001 [`opal/tools/worktree-tool/tests/test_worktree_tool.py:1-8`] `@header` `description`이 이번 커밋에서 추가된 T119 S-7/S-8(상태 의존 canonical path 해석 회귀 테스트, 약 120줄)을 반영하지 않음
  - 카테고리: 문서화 (`@header` 현재 사실 규칙)
  - 위반 기준: 프로젝트(`docs/CONVENTIONS.md` §구현 규칙 > `@header` 규칙 — "코드 `@header`에는 현재 사실만 기재한다")
  - 설명: `description`은 092/112/118 TEST-SCENARIO 커버리지만 기재하고 있고, 119가 추가한 `attribution_state` 상태 의존 해석(S-7 active 3상태 차단 유지, S-8 `closed` 상태 hub_merged 해석·finalize 멱등) 테스트 스위트는 언급이 없다. 118까지의 선례(각 태스크 추가 시 description에 해당 TEST-SCENARIO 번호를 누적 기재)와 비교하면 이번 커밋만 그 갱신이 누락됐다. 파일 자체는 diff에서 `@header` 블록 변경 없이(1~8행 무변경) 본문만 편집됐다(`git diff 20c38a4 25b8a8c` 확인).
  - 해결 방안: `description`에 "119 TEST-SCENARIO.md S-7/S-8(`attribution_state` 상태 의존 canonical path 해석 — active 차단 유지·`closed` hub_merged 해석·finalize 멱등)을 추가한다"는 문장을 이어 붙인다.
  - 자동 수정: N (문장 작성 필요 — 단순 치환 아님)
  - 참조: `opal/core/references/header-standard.md` §2.1 (docs/CONVENTIONS.md §@header 규칙이 인용하는 원문 소유 문서)

### Low (0건)

### Info (1건)

- [ ] GC-I001 [커밋 `a5bfb77`] 커밋 메시지 `type`이 `merge`로, `docs/CONVENTIONS.md` §커밋 규칙 > Type 표(`feat`/`fix`/`refactor`/`chore`/`docs` 5종)에 없는 값이다
  - 카테고리: 코드 품질 (커밋 규칙 — getsentry 참조 아님, CONVENTIONS.md 자체 규정)
  - 위반 기준: 프로젝트(`docs/CONVENTIONS.md` §커밋 규칙 > Type)
  - 설명: `a5bfb77`는 `feat/OP-TASK-119`를 `main`에 병합하는 실제 2-parent merge 커밋(`git show --format=%P` 확인: 부모 `81363d1`, `25b8a8c`)이며 메시지가 `merge(119): ...` 형식이다. 그러나 이 패턴은 119/121이 새로 만든 관행이 아니다 — `git log --all --merges`로 확인한 결과 `merge(095)`·`merge(107)`·`merge(108)`·`merge(109)`·`merge(118)` 등 기존 저장소 전역에서 동일 `merge(NNN):` 관행이 반복적으로 쓰였다(빈도 5건 이상, N=3 임계 초과 — 새 카테고리라기보다 오래된 기존 관행이 문서화만 누락된 상태). `docs/CONVENTIONS.md` §커밋 규칙 Type 표가 이 관행을 아직 반영하지 않았을 뿐이다.
  - 해결 방안: 이번 태스크의 결함이 아니므로 "위반"보다 문서 갱신 후보로 분류한다(§4 참조). 즉시 조치 불요.
  - 자동 수정: N
  - 참조: TBD — 저장소 자체 관행(git 로그) 근거, 외부 린트 규칙 없음. Conventional Commits 스펙의 `merge` 미표준 타입 논의: https://www.conventionalcommits.org/en/v1.0.0/#specification

---

## 4. 문서 업데이트 제안 (트리거 발동 시만)

<!-- 새 카테고리 트리거 -->
- [ ] GC-DP-C001 [새 카테고리 트리거] "merge 커밋 type" → `docs/CONVENTIONS.md` §커밋 규칙 > Type 표에 `merge` 행 신설 제안
  - 근거: 저장소 전역 `git log --all --merges`에서 `merge(NNN): ...` 형식이 최소 5회 이상 반복 관측됨(095/107/108/109/118/119). Type 표에 없는 값이 지속 사용 중이므로 실사용을 문서에 반영하는 편이 실태와 규범의 괴리를 줄인다.
  - 제안 내용: `| merge | 브랜치/워크트리 병합 커밋 (git merge 2-parent) |` 행 추가. 병합 주체(사용자)가 커밋을 만들고 PM은 대행하지 않는다는 §브랜치 전략·guards.md 원칙과 상충하지 않음(형식 문서화일 뿐, 실행 주체 규정과 무관).

(빈도 트리거: 발동 없음 — Medium 1건은 파일 1개에서만 관측되어 N=3 미달)

---

## 5. 문서 작성 유도 (해당 시)

`docs/CONVENTIONS.md` 존재 — 작성 유도 생략.

---

## 부록 — 검사 절차 기록

- 검사 대상 커밋: `git diff --name-only 20c38a4 25b8a8c`(119, 8파일 확인 일치) / `git show --name-only 86d8dcd`(121, 3파일 확인 일치)
- 커밋 메시지 형식 검사 대상: `25b8a8c feat(119)`, `f1f96ee chore(119)`, `a5bfb77 merge(119)`, `86d8dcd docs(121)` — `feat`/`chore`/`docs` 3건은 `{type}({scope}): {한국어 설명}` 형식 완전 부합. `merge` 1건은 위 Info 항목 참조.
- "하나의 태스크 = 하나의 커밋" 원칙: 119는 feat+chore+merge 3커밋으로 구성되나, `--wt` 워크트리 플로우 자체가 "브랜치 커밋 + merge 커밋" 구조를 구조적으로 요구하며(harness/worktree.md §merge 경로), 118/095/094 등 기존 워크트리·병합 태스크도 동일 패턴이다. 원칙은 "(원칙)"으로 명시된 권고이고 워크트리 병합은 이미 확립된 예외 패턴이므로 위반으로 판정하지 않았다.
- `@header` 정합성: `worktree_tool.py`의 `exports`(`cmd_finalize` 포함, 제거된 `_assert_task_path_unambiguous`는 원래도 비공개 함수라 exports 대상 아님)와 `description`이 `_resolve_canonical_task_path` 승격·`closed` 상태 멱등 반환·`hub_merged` 해석을 모두 정확히 반영함을 코드 대조로 확인(불일치 없음). `test_worktree_tool.py`만 Medium 1건(위 참조).
- Citation 정합성: `harness/worktree.md`의 `§모드 축과 직교하는 별개 축`·`§\`--wt\` 미사용 시 = 현행 동작 100% 유지`·`§canonical path 발급 계약`·`§상태 의존 해석`·`§merge 경로`, `harness/task-process.md`의 "스텝 4.5" 전부 실존 절임을 grep으로 실측 확인. `tools.md:1028`·`opal-project-init/SKILL.md:84`의 `§2.5` 인용은 121 diff 이전 원문과 라인 번호까지 정확히 일치(TASK.md 인용 정확성 확인).
- 도구·배포 경계: 변경 파일 전부 프로젝트 소스(`opal/`, `.opal/worktree.json`, `docs/`) 내부이며 `~/.opal/` 직접 편집 흔적 없음.
- 플랫폼 분기: `worktree_tool.py`·`opal-harness.md`·`tools.md`·`opal-project-init/SKILL.md` diff에 Cursor/Gemini/Antigravity/Claude 조건분기 신설 없음(Co-Authored-By 서명 1건은 무관).
- State 규칙: 검사 대상 8+3 코드 파일에 `state.json`/`test-scenario.json` 직접 편집 흔적 없음(대상 목록에 해당 파일 자체가 없음). 121 캡슐 `state.json`은 state-tool 표준 스키마(`schema_version`/`created_at`/`row_id`/`owner` 필드 구조)와 부합해 수기 편집 정황 없음.
- 문서 이력: 8+3개 대상 파일 diff에 `변경이력`/`Changelog`/`history`/`revisions` 계열 신규 헤더 절 추가 없음.
- 알려진 정당 예외 확인: `test_worktree_tool.py`의 `[T119]` 주석 3건(스텝 4.5 문안, 작업 경로 블록, `§2.5` 대체 단언 교체 근거) 모두 위반 아님으로 확인·제외.
- 임시 fixture: 본 검사는 `git show`/`git diff`/`grep` 읽기 전용 조회만 사용했다. `/private/tmp` 하위에 파일을 생성하지 않았으며, 잔존 파일 0건이다(생성한 적이 없으므로 삭제 대상 자체가 없음 — `ls /private/tmp/claude-501/.../scratchpad/` 기준 이번 실행이 추가한 파일 없음).
