# DONE: state-tool mock 가드 false positive 수정 (#1 정규식 + #2 메타-순환)

> 완료일: 2026-06-21 23:36 KST | 스킬: opds | 모드: agentic
> 태스크: 034 | 입력: TASK.md / PLAN.md / TEST-SCENARIO.md

## 1. 작업 요약

`state_tool.py`의 mock 코드 검출 가드가 **정당한 텍스트**(산문 단어 / 문서화용 인라인 백틱 코드 예시)를 실제 mock 코드로 오탐하던 두 층위 버그를 근본 수정했다. 실제 mock 코드 검출 능력(헌법 §4 "Don't fake it")은 그대로 보존했다.

- **#1 (F-001)**: `_MOCK_CODE_PATTERNS` 정규식 첫 대안 `MagicMock`(맨 단어)을 제거. 산문(예: op-dev-test-scenario SKILL §7 PM Gate 표준 문구 `"...MagicMock 등 부재"`)을 오탐하던 원인. 실제 `MagicMock()` 호출은 `Mock\(` 대안이 이미 커버하는 잉여 대안임을 입증.
- **#2 (F-002)**: `_check_mock_patterns`에 **인라인 백틱 제거 + 코드펜스 상태추적** 전처리 추가. 문서화용 인라인 백틱 코드 예시(`` `m = Mock()` ``)는 통과시키되, 코드펜스 내부·백틱 밖 bare 라인의 실제 mock 코드는 계속 검출. mock 가드를 검증·문서화하는 태스크(034 자신 포함)의 TEST 단계가 구조적으로 막히던 **메타-순환** 해소.

## 2. 변경 파일

| 파일 | 변경 내용 |
|------|----------|
| `opal/tools/state-tool/state_tool.py` | 정규식 `MagicMock\|` 대안 1개 제거(#1) + `_check_mock_patterns` 인라인 백틱/코드펜스 전처리(#2) + 주석/docstring + @header `description`에 `034:` 변경이력 |
| `opal/tools/state-tool/tests/test_state_tool.py` | RED-first 신규 테스트 13개 (TS-001~014) |
| `tasks/034-.../TEST-SCENARIO.md` | RED 증거 표 + 시나리오 결과 칸 + 판정(All Pass) |

> Surgical: `git diff --stat` = state_tool.py 27줄(±) + test 175줄(신규). `_check_evidence`·`_check_red_evidence`·`cmd_mark`/`cmd_verify` 본문 불변. `--force` 우회 미도입(D-DEC-3).

## 3. 검증 결과

| 항목 | 결과 |
|------|------|
| pytest 전체 회귀 | **197 passed, 0 failed** (기존 184 + 신규 13) |
| TEST 동적검증 (TEST-SCENARIO.md) | **All Pass** (S-1~S-10·S-12~S-14, S-11=배포 검증) |
| 메타-순환 해소 (S-13) | 재배포 전 배포본 가드 37건 오탐 → mark 거부 / **재배포 후 통과** → TEST 행 mark 성공 (실증) |
| 헌법 §4 정탐 보존 | bare `MagicMock()`/`@patch`/코드펜스 내부 mock 계속 검출 (PM 직접 spot-check) |
| 오탐 제거 | 산문 PM Gate 문구 `[]` / 인라인 백틱 예시 `[]` (PM 직접 spot-check) |
| install 재배포 | `./scripts/install-mac.sh` 완료 — 배포본 `MagicMock\|` 0건 + `in_fence` 전처리 반영. 033 미발효분 동반 발효 |

## 4. 설계 결정 (요약)

- **D-DEC-1**: #1은 `MagicMock` 대안 **제거**(b안). `Mock\(`가 `MagicMock()` 끝부분을 이미 매칭하므로 잉여. 가장 surgical.
- **D-DEC-2**: #2는 **(ii) 인라인 백틱 제거 + 코드펜스 추적** 채택. (i) 코드펜스-only는 기존 테스트 3개(bare 라인 mock)를 회귀시키고, (iii) 메타 마커는 파일 전체 스킵으로 헌법 §4 무력화 위험. (ii)만이 문서 예시 통과 + bare/코드펜스 정탐 유지를 모두 충족.
- **D-DEC-3**: `--force` 우회 **거부** — 가드 본질 약화. 오탐 제거로 우회 불요.
- **백틱 미닫힘 fail-safe**: 인라인 백틱이 닫히지 않으면 해당 구간 미제거 → "의심 시 검사" 방향으로 가드 약화 없음.

## 5. 후속 / 미해결

- (없음) — 소스 수정·테스트·배포·검증 전부 완료. 커밋 진행.
- brain: 메타-순환 교훈을 `concept/state-tool-mock-guard-skill-false-positive.md`(D-4)에 갱신.

## 6. 산출물

- `TASK.md` / `PLAN.md` / `TEST-SCENARIO.md` / `STATE.md` / `AGENTIC-LOG.md` / `DONE.md`
