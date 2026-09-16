# GC CONVENTION REPORT — 2026-09-16T13-45-00

## 1. 헤더

- 실행 일시: 시작 2026-09-16 13:45:00 / 완료 2026-09-16 13:47:15 / 소요 2분 15초
- 범위: `Framework` / 대상 파일 20개 / `check_enabled: true`
- 에이전트: `opal-convention-checker`
- 기준 문서: `docs/CONVENTIONS.md`, `docs/PROJECT.md`, `.opal/code-scan.json`
- baseline: `gc-findings-convention-2026-09-16T13-37-00-framework.json`
- APPLY 수행 여부: N — read-only 재검사
- 검사 실행 상태: `pass`
- 최종 판정: `PASS_WITH_ADVISORIES`

## 2. 요약 지표

| 지표 | 값 |
|------|-----|
| check_enabled | true |
| 검사 파일 | 20 / 20 |
| 총 이슈 수 | 1 |
| 심각도 분포 | Critical 0 / High 0 / Medium 0 / Low 1 / Info 0 |
| 집행 수준 | Blocking 0 / Advisory 1 / Informational 0 |
| 자동 수정 가능 | 1 |
| 수동 조치 필요 | 0 |
| Critical/High 수 | 0 |
| 문서 업데이트 제안 수 | 0 |

이전 blocking finding `f98763af0670aaa2`는 해소됐다. `state_tool.py` 헤더가 이제 신규 pipeline의 명시적 `close.final`과 legacy 마지막 CLOSE 행 하위호환을 구분해 구현·schema와 일치한다.

## 3. 수정 대상

### Critical (0건)

없음.

### High (0건)

없음.

### Medium (0건)

없음. 이전 GC-001은 resolved.

### Low (1건)

- [ ] GC-001 [`opal/tools/state-tool/state_tool.py:7`] code-scan이 누적 이력형 헤더를 `header_history`로 계속 관측
  - 카테고리: 문서화
  - 위반 기준: 프로젝트(`docs/CONVENTIONS.md` §구현 규칙 > @header 규칙)
  - 근거: `opal/tools/code-scan/run.sh validate --changed ... --json`이 `header_history` 1건(`detail: 118,128,136,512`, `tasks: 4`)을 비차단 경고로 반환했다.
  - 영향: 현재 사실 요약에 태스크·변경 이력이 누적되어 헤더가 비대해지고 구조 탐색 신호 대 잡음비가 낮아진다.
  - 해결 방안: 이력성 태스크 번호와 과거 변경 설명을 제거하고 현재 공개 계약·책임만 간결하게 남긴다.
  - 자동 수정: Y
  - 검증: `code-scan validate --changed opal/tools/state-tool/state_tool.py --json`에서 `header_history`가 0인지 확인한다.
  - 참조: `docs/CONVENTIONS.md` §구현 규칙 > @header 규칙

### Info (0건)

없음.

## 4. Baseline delta

| 분류 | fingerprint | 결과 |
|------|-------------|------|
| Resolved | `f98763af0670aaa2` | `close.final` current-fact mismatch 해소 |
| Persisting | `3eac6cd5f503a2b1` | code-scan `header_history` advisory 유지 |
| New | 없음 | 신규 finding 없음 |
| Suppressed | 없음 | 억제 없음 |

## 5. 검사 근거

- 대상 20개 경로의 존재와 프로젝트 루트 내부 위치를 전건 확인했다.
- `git diff --check -- <target_files>`: 오류 없음.
- Hook·pipeline 10종·state schema JSON 파싱: 전건 성공.
- Python 대상 5개 `py_compile`: 성공.
- Bash 대상 2개 `bash -n`: 성공.
- code-scan changed validation: coverage 5/5(100%), `header_history` 1건, 그 외 violation count 0건.
- `state_tool.py:7`, `_is_close_final_row()`, `state.schema.json`을 교차 대조해 이전 current-fact mismatch 해소를 확인했다.

## 6. 문서 업데이트 제안

빈도·새 카테고리 트리거 없음.

## 7. 문서 작성 유도

`docs/CONVENTIONS.md` 존재 — 작성 유도 생략.
