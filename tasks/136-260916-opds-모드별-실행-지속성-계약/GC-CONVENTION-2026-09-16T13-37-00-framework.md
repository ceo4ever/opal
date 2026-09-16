# GC CONVENTION REPORT — 2026-09-16T13-37-00

## 1. 헤더

- 실행 일시: 시작 2026-09-16 13:37:00 / 완료 2026-09-16 13:40:34 / 소요 3분 34초
- 범위: `Framework` / 대상 파일 20개 / `check_enabled: true`
- 에이전트: `opal-convention-checker`
- 기준 문서: `docs/CONVENTIONS.md`, `docs/PROJECT.md`, `.opal/code-scan.json`
- baseline: `none`
- APPLY 수행 여부: N — read-only 진단
- 검사 실행 상태: `pass`
- 최종 판정: `FAIL` — blocking finding 1건

## 2. 요약 지표

| 지표 | 값 |
|------|-----|
| check_enabled | true |
| 검사 파일 | 20 / 20 |
| 총 이슈 수 | 2 |
| 심각도 분포 | Critical 0 / High 0 / Medium 1 / Low 1 / Info 0 |
| 집행 수준 | Blocking 1 / Advisory 1 / Informational 0 |
| 자동 수정 가능 | 1 |
| 수동 조치 필요 | 1 |
| 파일별 상위 | `opal/tools/state-tool/state_tool.py` (2건) |
| 카테고리별 빈도 | 문서화 (1개 파일) |
| Critical/High 수 | 0 |
| 문서 업데이트 제안 수 | 0 |

검사는 모든 지정 파일을 읽었고 기준 문서나 도구 결측이 없으므로 실행 상태는 `pass`다. 다만 프로젝트 SSOT의 `[MUST]` 규칙을 위반한 blocking finding이 있어 통합 판정은 `FAIL`이다.

## 3. 수정 대상

### Critical (0건)

없음.

### High (0건)

없음.

### Medium (1건)

- [ ] GC-001 [`opal/tools/state-tool/state_tool.py:7`] `@header.description`이 변경된 CLOSE 완료 조건을 이전 의미로 서술
  - 카테고리: 문서화
  - 위반 기준: 프로젝트(`docs/CONVENTIONS.md` §구현 규칙 > @header 규칙 — 코드 `@header`에는 현재 사실만 기재)
  - 근거: 헤더는 “CLOSE 마지막 행 mark”가 `completed_unmerged`를 확정한다고 서술하지만, 같은 파일의 `_is_close_final_row()`와 변경된 schema는 신규 pipeline에서 명시적 `close.final`만 완료로 인정하고 `close.final`이 없는 legacy pipeline만 마지막 CLOSE 행을 하위호환으로 인정한다.
  - 영향: code-scan과 워커가 헤더를 현재 구조 요약으로 소비할 때 신규 pipeline의 CLOSE tail을 조기 완료 가능한 것으로 오해할 수 있다.
  - 해결 방안: 해당 문장을 “명시적 `close.final`에서 완료를 확정하며, `close.final`이 없는 legacy pipeline만 마지막 CLOSE 행을 final로 인정한다”는 현재 계약으로 교체한다.
  - 자동 수정: N
  - 검증: `opal/tools/code-scan/run.sh scan opal/tools/state-tool/state_tool.py --full` 출력과 `_is_close_final_row()`·`state.schema.json` 설명이 같은 완료 조건을 서술하는지 대조한다.
  - 참조: `docs/CONVENTIONS.md` §구현 규칙 > @header 규칙

### Low (1건)

- [ ] GC-002 [`opal/tools/state-tool/state_tool.py:7`] code-scan이 누적 이력형 헤더를 `header_history`로 관측
  - 카테고리: 문서화
  - 위반 기준: 프로젝트(`docs/CONVENTIONS.md` §구현 규칙 > @header 규칙)
  - 근거: `opal/tools/code-scan/run.sh validate --changed ... --json`이 `header_history` 1건(`detail: 118,128,512`, `tasks: 3`)을 반환했다. 도구의 비차단 경고 성격을 유지해 advisory로 기록한다.
  - 영향: 현재 사실 요약에 태스크·변경 이력이 누적되어 헤더가 비대해지고 구조 탐색 신호 대 잡음비가 낮아진다.
  - 해결 방안: 이력성 태스크 번호와 과거 변경 설명을 제거하고 현재 공개 계약·책임만 간결하게 남긴다. 이력은 git 로그와 태스크 DONE 문서에서 유지한다.
  - 자동 수정: Y
  - 검증: 같은 `code-scan validate --changed opal/tools/state-tool/state_tool.py --json`을 재실행해 `header_history`가 0인지 확인한다.
  - 참조: `docs/CONVENTIONS.md` §구현 규칙 > @header 규칙

### Info (0건)

없음.

## 4. 검사 근거

- 대상 20개 경로의 존재와 프로젝트 루트 내부 위치를 전건 확인했다.
- `git diff --check -- <target_files>`: 오류 없음.
- Hook·pipeline 10종·state schema JSON을 `python3 -m json.tool`로 파싱: 전건 성공.
- Python 대상 5개를 `python3 -m py_compile`로 검사: 성공.
- Bash 대상 2개를 `bash -n`으로 검사: 성공.
- code-scan changed validation: coverage 5/5(100%), `header_history` 1건, 그 외 orphan/uncovered/conflict/draft/exports_not_found 0건.

## 5. 문서 업데이트 제안

동일 fingerprint가 3개 이상 파일에서 발견되지 않았고 `docs/CONVENTIONS.md`에 없는 새 카테고리도 없어 제안 없음.

## 6. 문서 작성 유도

`docs/CONVENTIONS.md` 존재 — 작성 유도 생략.
