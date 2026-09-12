# GC CONVENTION REPORT — 2026-09-12T11-28

## 1. 헤더

- 실행 일시: 2026-09-12 11:28 (KST)
- 범위: 태스크 118 변경분(36건) / 검사 대상 코드 루트 `.opal-worktrees/task_118/` (브랜치 `feat/OP-TASK-118`, base `e8b6c4f`)
- 대상 파일: `git status --porcelain` 36건 중 컨벤션 적용 대상 30건(문서·코드·테스트) 검사
- 에이전트: opal-convention-checker
- 기준 문서: `{코드루트}/docs/CONVENTIONS.md` (존재 — 단일 문서 모델, 허브+링크 미적용)
- APPLY 수행 여부: N (읽기 전용 진단 — 본 에이전트는 수정하지 않음)

---

## 2. 요약 지표

| 지표 | 값 |
|------|-----|
| 총 이슈 수 | 3 |
| 심각도 분포 | Critical 0 / High 0 / Medium 1 / Low 2 / Info 0 |
| 자동 수정 가능 | 3 |
| 수동 조치 필요 | 0 |
| 파일별 상위 Top 5 | `dashboard/backend/tests/test_routers.py` (1건) / `opal/tools/state-tool/tests/test_state_tool.py` (1건) / `docs/proposals/opal-worktree-task-ownership.md` (1건) |
| 카테고리별 빈도 | 문서화 (3 파일) |
| Critical/High 수 | 0 |
| 문서 업데이트 제안 수 | 0 (빈도 임계값 N=3 미충족 — fingerprint 3건이 서로 다른 근거라 동일 위반으로 집계되지 않음. 새 카테고리 없음) |

**PM Gate 통과 조건(Critical·High 0건) 충족.**

---

## 3. 수정 대상 (체크리스트)

### Critical (0건)

### High (0건)

### Medium (1건)

- [ ] GC-C001 [`dashboard/backend/tests/test_routers.py:80`] `@header.depends`에 삭제된 모듈 `paths`가 잔존
  - 카테고리: 문서화
  - 위반 기준: 프로젝트(`docs/CONVENTIONS.md` §@header 규칙, "코드 `@header`에는 현재 사실만 기재한다")
  - 설명: 이 태스크는 `dashboard/backend/paths.py`를 삭제하고 같은 파일(`test_routers.py`)에서 `from dashboard.backend.paths import hub_root` import도 제거했다. 그러나 파일 상단 `@header`의 `"depends"` 배열에는 `"paths"` 항목이 그대로 남아 실제 코드와 불일치한다. 같은 커밋에서 동일 사유로 수정된 `test_adapters.py`·`test_parsers.py`는 `depends`에서 `"paths.hub_root"`를 정확히 제거했으므로, 이 파일만 누락된 것으로 판단된다.
  - 해결 방안: `"depends"` 배열에서 `"paths"` 항목 삭제.
  - 자동 수정: Y
  - 참조: `docs/CONVENTIONS.md` §217-223 (@header 규칙)

### Low (2건)

- [ ] GC-C002 [`opal/tools/state-tool/tests/test_state_tool.py:6240`] 신규 테스트 클래스 `TestFinalizeAttributionHistoryLink`가 `@header.exports`에 누락
  - 카테고리: 문서화
  - 위반 기준: 프로젝트(`docs/CONVENTIONS.md` §@header 규칙)
  - 설명: 이 태스크가 신설한 최상위 테스트 클래스 3종(`TestFinalizeAttributionHistoryLink`, `TestS9CloseMarkNoImmediateMemoryAppend`, `TestS10FinalizeAttribution`) 중 뒤 2개만 `@header`의 `"exports"` 목록에 추가됐고 `TestFinalizeAttributionHistoryLink`는 빠졌다. 다만 이 파일의 `exports` 목록은 이전부터 전체 테스트 클래스를 모두 나열하지 않는 부분 목록 관행이라(`TestG7StatusTransitions` 등 기존 다수 클래스도 미기재) 심각도를 Low로 판단했다.
  - 해결 방안: `"exports"` 배열에 `"TestFinalizeAttributionHistoryLink"` 추가(다른 두 신규 클래스와 일관되게).
  - 자동 수정: Y
  - 참조: `docs/CONVENTIONS.md` §217-223 (@header 규칙)

- [ ] GC-C003 [`docs/proposals/opal-worktree-task-ownership.md:3`] 제안서 상태 행이 4개 지정 어휘 형식을 따르지 않음
  - 카테고리: 문서화
  - 위반 기준: 프로젝트(`docs/CONVENTIONS.md` §제안서 생명주기 — "상태는 문서 상단 `> 상태:` 행에 위 4개 어휘로만 표기한다")
  - 설명: 현재 `> 상태: 6차 개정 제안`으로 기재되어 있어 규정된 4개 어휘(`제안`/`검토`/`적용완료`/`폐기`) 단독 표기가 아니다. 이 태스크의 diff는 기존 `5차 개정 제안`을 `6차 개정 제안`으로만 증분했으며, 비표준 패턴 자체는 이전 개정부터 있던 것으로 이 태스크가 새로 만든 위반은 아니다. 다음 개정 기회에 정리를 권장한다.
  - 해결 방안: `> 상태: 제안` (또는 `검토`)으로 정정하고, 개정 차수는 별도 각주나 본문 이력절로 이동.
  - 자동 수정: Y (단순 텍스트 치환)
  - 참조: `docs/CONVENTIONS.md` §128-142 (제안서 생명주기)

### Info (0건)

---

## 4. 문서 업데이트 제안 (트리거 미발동)

빈도 트리거(N=3 이상 파일에서 동일 fingerprint) · 새 카테고리 트리거 모두 미발동. 3건 모두 "문서화" 카테고리로 동일 상위 분류지만 근거 규칙과 위반 패턴이 서로 달라(depends 배열 누락 / exports 배열 누락 / 상태 어휘 위반) 동일 fingerprint로 집계되지 않았다.

---

## 5. 문서 작성 유도

해당 없음 — `docs/CONVENTIONS.md` 존재 확인, 초안 생성 유도 생략.

---

## 부록 — 확인했으나 위반이 아닌 항목 (근거 명시)

- **`@header` 심볼 갱신**: `worktree_tool.py`(`cmd_finalize` 추가), `state_tool.py`(`find_project_root`→`task_root` 개명, `cmd_finalize_attribution`/`link_memory_history`/`task_root` exports 반영), `memory_tool.py`(`_is_worktree_target`/`finalize_title_equivalence` 추가), `brain_tool.py`(`hub_root` 제거 + `finalize_brain_root`/`require_write_root` 추가), `code-scan.js`(`hubRootFromPath` 제거)까지 description·exports가 실제 코드와 일치함을 diff 대조로 확인. 위반 없음.
- **제거된 심볼 잔재**: 저장소 전체에서 `hub_root`/`hubRootFromPath`/`_hub_root`/`find_project_root`를 재검색한 결과, 남은 참조는 (1) 지시된 정당 예외인 부재 단언 가드 2건(`brain-tool/tests/test_brain_tool.py:2528-2529`, `code-scan/tests/test-hub-root.js:153,156-157`), (2) `docs/proposals/opal-worktree-task-ownership.md`의 AS-IS 비교 서술(제안서 성격상 정상)뿐이었다. 위반 없음.
- **Citation 무결성**: `harness/worktree.md`가 절 구성을 `## task root와 allocator root 계약` · `## canonical path 발급 계약` · `## cone 확장 계약`으로 재편했고, 이를 인용하는 `docs/CONVENTIONS.md`·`opal-harness.md`·`task-process.md`·`observability.md`·`memory-learning.md`·`event-loader/README.md`·`code-scan.js`·`doctor.py`·`worktree_tool.py`의 인용 문구를 모두 대조 — dangling 0건. `opal-harness.md:56`의 `§2.5 워크스페이스 축` 매핑 행은 지시된 정당 예외로 보존 확인(`tools.md:1028`·`opal-project-init/SKILL.md:84`가 그 행을 인용).
- **`memory-learning.md` §변경이력**: git diff로 대조한 결과 해당 절은 이번 diff의 unified hunk에 나타나지 않음 — 선존재분이며 이 태스크가 신규 생성하지 않음. 위반 아님.
- **도구·배포 경계**: 변경 파일 전부가 `opal/`·`dashboard/`·`docs/` 프로젝트 소스이며 `~/.opal/` 직접 편집 흔적 없음.
- **플랫폼 분기**: 변경분 전체에서 Claude/Cursor/Gemini 등 플랫폼 조건 분기 신규 추가 없음.
- **State 규칙**: `state.json`·`test-scenario.json` 직접 편집 흔적 없음(변경 목록에 미포함).
- **커밋 메시지**: 아직 커밋 전이므로 해당 없음.
