# oppd agentic 자율 루핑 장치 설계

> 등록일: 2026-03-30 | 카테고리: task | 상태: 예정

## 배경

oppd(opal-pilot-project-dev)는 아이디어 → product까지 agentic AI를 지향한다.
현재 Phase 3(태스크 실행)에서 opd/opds가 각 태스크를 실행하지만,
QA/TEST 실패 시 자동으로 재시도하고 스스로 개선/보정하는 루핑 장치가 부족하다.

## 요구사항

- Phase 3 실행 루프에 QA/TEST 결과 기반 자동 재시도 메커니즘 추가
- 실패 → 원인 분석 → 자동 수정 → 재검증 루프 (최대 N회)
- PM이 루프 결과를 모니터링하고, 루프 한도 초과 시 사용자에게 에스컬레이션
- opd/opds 내부의 TEST-SCENARIO 결과도 활용

## 캡틴 의견

"이 스킬은 한번에 아이디어부터 개발 완료(product)까지 agentic ai를 지향하는 것. qa, test 등 루핑하면서 스스로 개선과 보정을 하는 장치가 더 필요함."
