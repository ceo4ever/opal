# GC CONVENTION REPORT — 2026-09-15T10-28

## 1. 헤더

- 실행 일시: 시작 2026-09-15 10:32 / 완료 2026-09-15 10:32 / 소요 1분 미만
- 범위: `Framework` / 대상 파일 6개
- 에이전트: `opal-convention-checker`
- 기준 문서: `docs/CONVENTIONS.md`(T0), `.opal/code-scan.json`(T0), Ruff 공식 기본 규칙(T1)
- baseline: `none` — 현재 finding 17건 모두 `new`
- APPLY 수행 여부: N (read-only 진단)

## 2. 요약 지표

| 지표 | 값 |
|------|-----|
| 총 이슈 수 | 17 |
| 심각도 분포 | Critical 0 / High 0 / Medium 0 / Low 16 / Info 1 |
| 자동 수정 가능 | 4 |
| 수동 조치 필요 | 13 |
| 파일별 상위 Top 5 | `opal/tools/state-tool/tests/test_state_tool.py` (13건) / `opal/tools/state-tool/state_tool.py` (4건) |
| 카테고리별 빈도 | 죽은 코드 11 / 네이밍 2 / 미사용 import 2 / import 순서 2 |
| Critical/High 수 | 0 |
| 문서 업데이트 제안 수 | 3 (새 카테고리 3건) |

판정은 `PASS_WITH_ADVISORIES`다. 6개 파일을 모두 검사했고 결측 capability와 blocking finding은 없다. 이번 변경 diff가 추가한 Ruff 진단은 없었으며, 아래 17건은 대상 파일 전체 검사에서 관측된 기존 항목이다.

## 3. 수정 대상 (체크리스트)

### Critical (0건)

### High (0건)

### Medium (0건)

### Low (16건)

- [ ] GC-001 [`opal/tools/state-tool/state_tool.py:515`] 모호한 변수명 `l`
  - 카테고리: 네이밍 / 위반 기준: Ruff E741(T1) / 설명: `l`은 `1` 또는 `I`와 혼동될 수 있다.
  - 해결 방안: `line` 등 역할을 드러내는 이름으로 변경 / 자동 수정: N
  - 참조: https://docs.astral.sh/ruff/rules/ambiguous-variable-name

- [ ] GC-002 [`opal/tools/state-tool/state_tool.py:1196`] 미사용 지역 변수 `status`
  - 카테고리: 죽은 코드 / 위반 기준: Ruff F841(T1) / 설명: 대입 결과가 소비되지 않는다.
  - 해결 방안: 대입을 제거하거나 의도한 검증에 사용 / 자동 수정: N
  - 참조: https://docs.astral.sh/ruff/rules/unused-variable

- [ ] GC-003 [`opal/tools/state-tool/state_tool.py:2071`] 미사용 지역 변수 `prev_status`
  - 카테고리: 죽은 코드 / 위반 기준: Ruff F841(T1) / 설명: 대입 결과가 소비되지 않는다.
  - 해결 방안: 대입을 제거하거나 상태 전이 검증에 사용 / 자동 수정: N
  - 참조: https://docs.astral.sh/ruff/rules/unused-variable

- [ ] GC-005 [`opal/tools/state-tool/tests/test_state_tool.py:53`] 미사용 import `MagicMock`
  - 카테고리: 미사용 import / 위반 기준: Ruff F401(T1) / 설명: 테스트가 해당 import를 참조하지 않는다.
  - 해결 방안: import 목록에서 제거 / 자동 수정: Y
  - 참조: https://docs.astral.sh/ruff/rules/unused-import

- [ ] GC-006 [`opal/tools/state-tool/tests/test_state_tool.py:58`] 모듈 상단이 아닌 import
  - 카테고리: import 순서 / 위반 기준: Ruff E402(T1) / 설명: 경로 조작 뒤 `state_tool`을 import한다.
  - 해결 방안: 로더를 리팩터링하거나 선행 경로 설정이 필수라면 사유와 함께 명시 억제 / 자동 수정: N
  - 참조: https://docs.astral.sh/ruff/rules/module-import-not-at-top-of-file

- [ ] GC-007 [`opal/tools/state-tool/tests/test_state_tool.py:1025`] 미사용 지역 변수 `original_ids`
  - 카테고리: 죽은 코드 / 위반 기준: Ruff F841(T1) / 설명: fixture 값이 assertion에 쓰이지 않는다.
  - 해결 방안: 대입을 제거하거나 의도한 assertion을 추가 / 자동 수정: N
  - 참조: https://docs.astral.sh/ruff/rules/unused-variable

- [ ] GC-008 [`opal/tools/state-tool/tests/test_state_tool.py:1289`] 미사용 예외 컨텍스트 변수 `cm`
  - 카테고리: 죽은 코드 / 위반 기준: Ruff F841(T1) / 설명: 캡처한 예외를 사용하지 않는다.
  - 해결 방안: `as cm`을 제거하거나 예외 내용을 검증 / 자동 수정: N
  - 참조: https://docs.astral.sh/ruff/rules/unused-variable

- [ ] GC-009 [`opal/tools/state-tool/tests/test_state_tool.py:1375`] 미사용 예외 컨텍스트 변수 `cm`
  - 카테고리: 죽은 코드 / 위반 기준: Ruff F841(T1) / 설명: 캡처한 예외를 사용하지 않는다.
  - 해결 방안: `as cm`을 제거하거나 예외 내용을 검증 / 자동 수정: N
  - 참조: https://docs.astral.sh/ruff/rules/unused-variable

- [ ] GC-010 [`opal/tools/state-tool/tests/test_state_tool.py:1403`] 미사용 예외 컨텍스트 변수 `cm`
  - 카테고리: 죽은 코드 / 위반 기준: Ruff F841(T1) / 설명: 캡처한 예외를 사용하지 않는다.
  - 해결 방안: `as cm`을 제거하거나 예외 내용을 검증 / 자동 수정: N
  - 참조: https://docs.astral.sh/ruff/rules/unused-variable

- [ ] GC-011 [`opal/tools/state-tool/tests/test_state_tool.py:1821`] 미사용 지역 변수 `log_rows_before`
  - 카테고리: 죽은 코드 / 위반 기준: Ruff F841(T1) / 설명: before 값이 assertion에 쓰이지 않는다.
  - 해결 방안: 대입을 제거하거나 전후 비교에 사용 / 자동 수정: N
  - 참조: https://docs.astral.sh/ruff/rules/unused-variable

- [ ] GC-012 [`opal/tools/state-tool/tests/test_state_tool.py:1823`] 미사용 지역 변수 `md_after`
  - 카테고리: 죽은 코드 / 위반 기준: Ruff F841(T1) / 설명: 생성된 Markdown 값이 assertion에 쓰이지 않는다.
  - 해결 방안: 대입을 제거하거나 결과 검증에 사용 / 자동 수정: N
  - 참조: https://docs.astral.sh/ruff/rules/unused-variable

- [ ] GC-013 [`opal/tools/state-tool/tests/test_state_tool.py:3419`] 한 줄에 여러 import
  - 카테고리: import 순서 / 위반 기준: Ruff E401(T1) / 설명: `tempfile`, `shutil`, `pathlib`을 한 줄에서 import한다.
  - 해결 방안: import별로 한 줄씩 분리 / 자동 수정: Y
  - 참조: https://docs.astral.sh/ruff/rules/multiple-imports-on-one-line

- [ ] GC-014 [`opal/tools/state-tool/tests/test_state_tool.py:4041`] 미사용 지역 import `tempfile`
  - 카테고리: 미사용 import / 위반 기준: Ruff F401(T1) / 설명: 지역 import가 참조되지 않는다.
  - 해결 방안: import 제거 / 자동 수정: Y
  - 참조: https://docs.astral.sh/ruff/rules/unused-import

- [ ] GC-015 [`opal/tools/state-tool/tests/test_state_tool.py:4921`] 미사용 지역 변수 `exit_code`
  - 카테고리: 죽은 코드 / 위반 기준: Ruff F841(T1) / 설명: 예외 코드 대입 결과가 소비되지 않는다.
  - 해결 방안: 대입을 제거하거나 exit code를 검증 / 자동 수정: N
  - 참조: https://docs.astral.sh/ruff/rules/unused-variable

- [ ] GC-016 [`opal/tools/state-tool/tests/test_state_tool.py:8887`] 모호한 변수명 `l`
  - 카테고리: 네이밍 / 위반 기준: Ruff E741(T1) / 설명: `l`은 `1` 또는 `I`와 혼동될 수 있다.
  - 해결 방안: `line` 등 역할을 드러내는 이름으로 변경 / 자동 수정: N
  - 참조: https://docs.astral.sh/ruff/rules/ambiguous-variable-name

- [ ] GC-017 [`opal/tools/state-tool/tests/test_state_tool.py:9042`] 미사용 지역 변수 `qa_data`
  - 카테고리: 죽은 코드 / 위반 기준: Ruff F841(T1) / 설명: helper 반환값이 assertion에 쓰이지 않는다.
  - 해결 방안: 대입을 제거하거나 반환값을 검증 / 자동 수정: N
  - 참조: https://docs.astral.sh/ruff/rules/unused-variable

### Info (1건)

- [ ] GC-004 [`opal/tools/state-tool/state_tool.py:2122`] placeholder 없는 f-string
  - 카테고리: 죽은 코드 / 위반 기준: Ruff F541(T1) / 설명: 보간이 없는 문자열에 `f` 접두사가 붙어 있다.
  - 해결 방안: 일반 문자열 literal로 변경 / 자동 수정: Y
  - 참조: https://docs.astral.sh/ruff/rules/f-string-missing-placeholders

## 4. 문서 업데이트 제안

- [ ] GC-DP-C001 [새 카테고리 트리거] `죽은 코드` → `docs/CONVENTIONS.md`에 미사용 변수·불필요한 f-string의 집행 수준을 명시할지 검토한다.
- [ ] GC-DP-C002 [새 카테고리 트리거] `미사용 import` → `docs/CONVENTIONS.md`에 미사용 import 정책을 명시할지 검토한다.
- [ ] GC-DP-C003 [새 카테고리 트리거] `import 순서` → `docs/CONVENTIONS.md`에 모듈 상단 배치·복수 import 정책을 명시할지 검토한다.

빈도 트리거는 발동하지 않았다. 동일 fingerprint가 3개 이상 파일에서 발견된 항목은 없다.

## 5. 문서 작성 유도

- `docs/CONVENTIONS.md` 존재 확인 — 작성 유도 생략.

## 6. 검증 증거

- `worker.dispatch` receipt: `ok:true`, `verified_document_count:4`
- `python3 -m py_compile` 대상 Python 4개: exit 0
- Ruff 대상 Python 4개: 17 diagnostics; 변경 diff에서 추가된 진단 0건
- `code-scan validate --scope framework`: OK, coverage 25.7% (78/303)
- `TestBootSummary`: 7/7 통과
- `test_event_loader_extended.py`: 11/11 통과
- 대상 6개 모두 EOF 개행 있음, 탭 들여쓰기·줄 끝 공백 없음
