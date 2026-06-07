# DONE 013 — state-tool 동작 증거 강제 게이트

> 완료: 2026-06-07 | 모드: agentic | 캡틴 CLOSE 승인 완료

## 완료 요약
헌법 §4("목업 금지·동작 증거")를 state-tool 종료코드로 **deterministic 강제**. 캡틴 사례(API를 목업으로 때우고 완료 선언)가 이제 기계적으로 차단된다.

## 변경 파일
| 파일 | 변경 |
|------|------|
| `opal/tools/state-tool/state_tool.py` | ERROR_CODES 2종(`mock_in_scenario`/`evidence_missing`) + `cmd_verify` 신설 + `cmd_mark` TEST stage 자동 훅 + verify 서브파서 |
| `opal/tools/state-tool/tests/test_state_tool.py` | TestVerify 13 케이스 |
| `tasks/013-.../` | TASK · PLAN · AGENTIC-LOG · DONE |

## QA 결과 (PM 직접 검증, 워커 신뢰 안 함 — 헌법 §4 self-application)
- 테스트 직접 재실행: **136 passed in 0.12s** (기존 121 회귀 없음)
- verify 실호출 mock 검출: `@patch` → `mock_in_scenario` exit 1 ✅
- verify 실호출 정상: 실 pytest+실응답 증거 → ok exit 0 ✅

## 잔여 / 후속
- `state-tool/README.md` · `opal-harness.md §3` 명령 목록(9→10)에 `verify` 문서화
- `qa-standards` · `test-scenario-guide`가 verify 자동 강제를 가리키게 연결 (advisory→tool 완성)
- 013 커밋 (캡틴 지시 대기)

## 한계 (정직)
verify는 TEST-SCENARIO.md의 mock 코드 패턴·증거 누락을 잡는다. 교묘하게 가짜 증거를 위조하면 못 막지만, "검증 건너뛰기·목업 통과"는 기계적으로 차단된다 — 현재(강제 0) 대비 근본적 개선.
