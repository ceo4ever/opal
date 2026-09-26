# GC CONVENTION REPORT — 2026-09-20T12-00-00

## 1. 헤더

- 실행 일시: 시작 2026-09-20 12:08:00 / 완료 2026-09-20 12:09:00 / 소요 1분 0초
- 범위: `Framework` / 대상 파일 4개
- 에이전트: `opal-convention-checker`
- 기준 문서: `docs/CONVENTIONS.md`, `docs/PROJECT.md`
- 기준선: 별도 Python formatter/linter 설정 없음; 프로젝트 SSOT 강제 규칙과 Ruff 기본 진단(T2 advisory)을 분리
- APPLY 수행 여부: N (read-only 진단)
- baseline: `none`

## 2. 요약 지표

| 지표 | 값 |
|------|-----|
| 총 이슈 수 | 17 |
| 심각도 분포 | Critical 0 / High 0 / Medium 0 / Low 17 / Info 0 |
| blocking | 0 |
| advisory | 17 |
| 자동 수정 가능 | 4 |
| 수동 조치 필요 | 13 |
| 파일별 | `state_tool.py` 4건 / `test_state_tool.py` 13건 / 나머지 0건 |
| Critical/High 수 | 0 |
| 문서 업데이트 제안 수 | 0 |

최종 판정: **PASS_WITH_ADVISORIES**. `docs/CONVENTIONS.md`가 강제하는 Python 파일명, `@header`, 줄 끝 공백·EOF 개행 규칙은 모두 충족했다. Ruff는 프로젝트 실행 설정이 아닌 외부 보조 점검이므로 관측 17건을 모두 Low/advisory로 유지한다. 현재 diff의 추가 행에서 새 Ruff 진단은 관측되지 않았다.

## 3. 수정 대상 (체크리스트)

### Critical (0건)

### High (0건)

### Medium (0건)

### Low (17건)

- [ ] GC-001~GC-004 [`opal/tools/state-tool/state_tool.py`] Ruff 기본 진단 4건
  - 카테고리: 죽은 코드 / 네이밍 / 코드 품질
  - 위반 기준: T2 Ruff 참조 진단 (`F841` 2, `E741` 1, `F541` 1); 프로젝트 강제 규칙 아님
  - 설명: 1759, 1920, 2604, 3834행의 미사용 로컬, 모호한 이름, 불필요 f-string을 관측했다.
  - 해결 방안: 별도 정리 태스크에서 의도를 확인한 뒤 제거·개명한다.
  - 자동 수정: 부분 Y
  - 참조: https://docs.astral.sh/ruff/rules/

- [ ] GC-005~GC-017 [`opal/tools/state-tool/tests/test_state_tool.py`] Ruff 기본 진단 13건
  - 카테고리: 미사용 import / 죽은 코드 / import 순서 / 네이밍
  - 위반 기준: T2 Ruff 참조 진단 (`F401` 2, `E402` 1, `F841` 8, `E401` 1, `E741` 1); 프로젝트 강제 규칙 아님
  - 설명: 대상 파일의 기존 미사용 심볼·import 형식을 관측했다. 현재 변경 행에서 새 진단은 없다.
  - 해결 방안: 광범위 레거시 테스트 정리 태스크로 분리하고, lint 설정 채택 여부를 먼저 확정한다.
  - 자동 수정: 부분 Y
  - 참조: https://docs.astral.sh/ruff/rules/

### Info (0건)

## 4. 문서 업데이트 제안

- 발동한 트리거 없음. 동일 fingerprint가 3개 이상 파일에서 반복되지 않았고, 프로젝트 SSOT와 충돌하는 신규 카테고리도 없다.

## 5. 검증 근거

- `git diff --check -- <4 files>`: exit 0
- `python3 -m py_compile <4 files>`: exit 0
- `~/.opal/tools/code-scan/run.sh validate <4 files>`: exit 0, coverage 43.3% (251/580)
- `ruff check <4 files>`: 17 diagnostics; 프로젝트 lint 설정 부재로 T2 advisory 처리
- `target_files`: 4개 모두 프로젝트 루트 내에 존재, `checked_files` 일치
