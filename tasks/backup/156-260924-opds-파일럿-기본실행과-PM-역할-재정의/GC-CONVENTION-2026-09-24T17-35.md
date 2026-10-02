# GC CONVENTION REPORT — 2026-09-24T17-35

## 1. 헤더

- 실행 일시: 2026-09-24 17:35 (opal-convention-checker, read-only)
- 범위: `all` / 대상 파일 33개 (worker.dispatch target_files 전량)
- 에이전트: opal-convention-checker
- 기준 문서: `docs/CONVENTIONS.md` 존재 — 해당 문서 + `opal-doc-standard.md` §5 + `header-standard.md` §2.1 적용
- APPLY 수행 여부: N (read-only 진단, 수정 없음)

---

## 2. 요약 지표

| 지표 | 값 |
|------|-----|
| 총 이슈 수 | 1 |
| 심각도 분포 | Critical 0 / High 0 / Medium 0 / Low 1 / Info 0 |
| 자동 수정 가능 | 0 |
| 수동 조치 필요 | 1 |
| 파일별 상위 | `opal/tools/state-tool/state_tool.py` (1건) |
| 카테고리별 빈도 | documentation (1 파일) — 빈도 트리거 미발동(N=1 < 3) |
| Critical/High 수 | 0 |
| 문서 업데이트 제안 수 | 0 |

---

## 3. 수정 대상 (체크리스트)

### Low (1건)

- [ ] GC-101 [opal/tools/state-tool/state_tool.py:7] `@header.description`에 서로 다른 태스크 번호 인용 7개 이상 누적(118/135/136/137/138/147/150)
  - 카테고리: 문서화 (header_history)
  - 위반 기준: 프로젝트(`opal/core/references/header-standard.md` §2.1, §4.2 — TASK_TAG_THRESHOLD=2)
  - 설명: `code-scan.js`의 비차단 경고 조건(동일 필드 내 서로 다른 태스크 번호 ≥2)을 이미 초과한 상태. 이번 태스크(156) diff는 기존 문자열을 그대로 유지·확장했을 뿐 새 태그를 추가하지 않아 이번 변경이 신규로 만든 위반은 아니나, 검사 대상 스냅숏 시점에는 여전히 존재.
  - 해결 방안: description을 "현재 사실"만 남기도록 재작성하고 시점별 근거는 git log·`tasks/{NNN}-*/DONE.md`로 이관. 자산 출신 단발 인용 1개만 허용.
  - 자동 수정: N
  - 참조: `opal/core/references/header-standard.md` §2.1, §4.2

---

## 4. 문서 업데이트 제안 (§9·§10, 트리거 발동 시만)

해당 없음 — 빈도 트리거(N≥3 파일)·새 카테고리 트리거 모두 미발동.

---

## 5. 문서 작성 유도 (해당 시)

- `docs/CONVENTIONS.md` 존재 확인 — 작성 유도 생략.

---

## 부록 — 검사 절차 근거

- 대상 33개 파일은 `run/changed-files.txt`를 그대로 사용(재선별 없음). `checked_files == target_files` 일치 확인.
- `git diff main --check -- <target_files>` → 공백/줄끝 오류 0건.
- `python3 -m py_compile` — 대상 5개 `.py` 파일(`state_tool.py`, `worktree_tool.py`, `test_pilot_isolation.py`, `test_start_resolution.py`, `test_state_tool_*.py`, `test_worktree_tool.py`) 컴파일 성공.
- `state_tool.py`·`worktree_tool.py` 전체 diff(`git diff main`) 라인 단위 검토 — 새로 추가된 함수(`cmd_resolve_start`, `_project_root_worktree_reason`, `NEW_TASK_DEFAULTS` 등)는 네이밍(snake_case)·에러 코드 등록 방식·`err_response`(NoReturn) 사용이 인접 코드 패턴과 일치. 명명·죽은 코드·미사용 import 위반 미발견.
- `docs/CONVENTIONS.md`·`README.md`·`docs/PROJECT.md`·`docs/ARCHITECTURE.md` diff 검토 — 허브+링크 모델·인용 규칙(`{경로}:{라인}` 또는 `docs 문서명 §섹션`) 준수. 본문 중 `(Task 156)` 형태의 단발 태스크 인용은 기존 코드베이스 전반(`# 156 DEC-1:` 등)에 이미 널리 쓰이는 허용 패턴과 동일하여 별건 위반으로 보지 않음(단발 인용은 header-standard.md §4.2가 허용).
- baseline 미지정(`none`) — 전건 `new`로 표기.
