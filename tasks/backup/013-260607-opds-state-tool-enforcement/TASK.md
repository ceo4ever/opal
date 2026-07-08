# TASK 013 — state-tool 동작 증거 강제 게이트

> 채번: 013 | 일자: 2026-06-07 | 스킬: opds | 모드: agentic

## 목적
헌법 §4("목업 금지·동작 증거")를 **코드로 강제**한다. 태스크 012가 헌법+문서(advisory)를 강화했고,
이번은 state-tool 종료코드로 deterministic 강제 — 캡틴 사례(API를 목업으로 때우고 완료 선언)를 기계적으로 차단.

## 배경
진단(태스크 012)에서 "강제 부재가 근본"으로 수렴. 검증 게이트가 전부 자연어 권고였다.
state-tool은 행 상태만 관리하고 테스트 내용을 검사하지 않아 "글자 존재=Pass", 목업 통과가 가능했다.

## 범위
- 신규 서브커맨드 `verify` — TEST-SCENARIO.md의 mock 코드 패턴 + 증거 누락 검사
- ERROR_CODES 2종 추가: `mock_in_scenario`, `evidence_missing`
- `cmd_mark` 자동 훅 — TEST stage 행 ✅ 시 verify 자동 실행 (문서 태스크 예외)
- `test_state_tool.py` 테스트 케이스 추가 (헌법 §4 — 동작 증거로 검증)

## AC
- [ ] `verify` 서브커맨드: mock 코드 패턴 검출 시 `mock_in_scenario` (exit≠0)
- [ ] `verify`: Pass 시나리오에 실행 증거 없으면 `evidence_missing` (exit≠0)
- [ ] `verify`: 정상(증거 있고 mock 없음)이면 ok (exit 0)
- [ ] `mark`가 TEST stage 행 done 시 verify 자동 실행, 위반 시 거부
- [ ] TEST-SCENARIO.md 부재(문서 태스크) 시 자동 skip
- [ ] test_state_tool.py에 신규 케이스 추가 + 전체 테스트 통과 (실제 실행 출력 증거)
