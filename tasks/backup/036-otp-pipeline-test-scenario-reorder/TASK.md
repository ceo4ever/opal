# TASK: otp 파이프라인 TEST-SCENARIO 단계 재배치 + EXECUTE 후 커밋 규칙 명시

> 작성일: 2026-03-28 | 작업 유형: 개선
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

otp-dev-short / otp-dev 파이프라인에서 TEST-SCENARIO 단계를 PLAN 직후로 이동하여 설계 산출물을 한번에 검토받고, EXECUTE 완료 후 커밋 금지 규칙을 명시한다.

## 배경

실제 프로젝트 수행 시 두 가지 문제가 반복 발생:

1. **TEST-SCENARIO 스킵**: PLAN 승인 후 TEST-SCENARIO를 건너뛰고 바로 EXECUTE로 진행하는 현상. TEST-SCENARIO가 독립 게이트(별도 STEP)로 존재하여 컨텍스트가 길어지면 스킵되기 쉬움.
2. **무단 커밋**: EXECUTE 완료 후 DONE.md 생성 없이 바로 커밋을 수행. 커밋은 사용자 명시 요청 시에만 해야 하는데 이 규칙이 스킬에 명시되어 있지 않음.

## 요구사항

- [ ] otp-dev-short: TEST-SCENARIO를 PLAN과 같은 STEP에 통합 (PLAN 워커 완료 → TEST-SCENARIO 워커 연속 디스패치 → QA → 사용자 검토/승인)
- [ ] otp-dev: TEST-SCENARIO를 TODO 직후로 이동 (TODO 워커 완료 → TEST-SCENARIO 워커 연속 디스패치 → 사용자 검토/승인)
- [ ] 두 스킬 모두: EXECUTE 완료 후 절차를 강조 — "Test → DONE.md → 보고 (커밋하지 않음)" + "커밋은 사용자가 명시적으로 요청할 때만 수행한다" 문구 추가
- [ ] 파이프라인 다이어그램 업데이트 (변경된 흐름 반영)
- [ ] STATE.md 템플릿의 단계 목록도 변경된 흐름에 맞게 수정

## 제약 조건

- 에이전트 파일(dtp-worker, dtp-test-worker 등)은 변경하지 않음 — 스킬 파일만 수정
- dtp-test-scenario/SKILL.md 자체는 변경 불필요 (호출 위치만 이동)
- 기존 게이트 체크포인트 원칙(각 단계 완료 시 사용자 보고 + 승인 대기)은 유지

## 기술 스택

- 마크다운 문서 (SKILL.md)

## 관련 문서

- [skills/otp-dev-short/SKILL.md](skills/otp-dev-short/SKILL.md) — Short Task 오케스트레이터
- [skills/otp-dev/SKILL.md](skills/otp-dev/SKILL.md) — Full Task 오케스트레이터
