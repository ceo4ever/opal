# AGENTIC-LOG: OPAL Principles 헌법 신설 + 하네스 다이어트 + 테스트 하네스 강화

> 모드: agentic (전환: EXECUTE 중) | 시작: 2026-06-07 | 스킬: //opp

## 요약

| 항목 | 건수 |
|------|------|
| 게이트 판단 | 경량 트랙 — PM 자체 검토 |
| 오류 발견 | 1건 (install 배포 누락) |
| 수정 지시 | - |
| PM 의사결정 | 6건 |
| 개선 사항 | 4건 (테스트 하네스 강화) |
| 에스컬레이션 | 0건 |

## 대행 일지

| # | 시점 | 단계 | 카테고리 | 내용 | 결과 |
|---|------|------|----------|------|------|
| 1 | 사전 | 진단 | DECISION | 진단 워커 3개 병렬 디스패치(검증/Context Rot/명확화) — "강제 부재가 근본"으로 수렴 | 완료 |
| 2 | EXECUTE | 헌법 | DECISION | 경량 PM 직접수행 트랙 채택 — 다이어트 작업을 무거운 풀파이프라인으로 하면 자기모순 | 캡틴 승인 |
| 3 | EXECUTE | 배포 | ERROR | install 스크립트에 PRINCIPLES.md 배포 누락 발견 — Eager Step 2.5가 ~/.opal/PRINCIPLES.md를 못 찾을 위험 | install-mac.sh+windows.ps1 배포 추가로 해소 |
| 4 | EXECUTE | 다이어트 | DECISION | personas(service-planner) 2개·wtm-agent 다이어트 **제외** — 맥락 고유 원칙이라 헌법 치환 시 의미 손실. 헌법 §3("망가지지 않은 것 건드리지 마라") 적용 | 제외 확정 |
| 5 | EXECUTE | 방향전환 | DECISION | 캡틴 지시로 부차 다이어트 보류 → 테스트 하네스 강화로 전환. 헌법 §4 집행 핵심 지점 | 진행 |
| 6 | EXECUTE | 테스트하네스 | IMPROVE | opal-test-agent "작성자 신뢰" 폐기 → adversarial 시나리오 타당성 사전 검증 + 실행출력 증거 의무 + 목업 대체 시 Fail | 완료 |
| 7 | EXECUTE | 테스트하네스 | IMPROVE | qa-standards EXECUTE QA "동작 증거 의무" 신설 — grep=Pass 금지, 목업 프로덕션 잔존 차단, 증거 없으면 미완 처리 | 완료 |
| 8 | EXECUTE | 테스트하네스 | IMPROVE | test-scenario-guide mock 금지 룰에 "구현을 목업으로 대체 금지(Don't fake it)" + 실연동 불가 시 BLOCKED 추가 | 완료 |
| 9 | EXECUTE | 테스트하네스 | IMPROVE | coding-principles §3·4·5에 헌법 §4 "목업금지·동작증거" 체크 추가 (헌법 다이어트 시 동반) | 완료 |
| 10 | 마무리 | DECISION | 코드 강제(state_tool `verify` 서브커맨드)는 헌법 §4상 동작검증이 필요한 큰 작업 → 별도 후속 태스크로 분리. 이번은 헌법+문서 하네스 강화까지 | 후속 제안 |
| 11 | 마무리 | IMPROVE | 변경이력 행 추가 — AGENT.md(v2.9)/install-mac.sh(v2.8)/windows.ps1(v1.10.0)/coding-principles(v1.3)/test-agent(v1.3)/test-scenario-guide(v2.2) | 완료 |

## 미해결 / 후속

- **README.md** 부트스트랩 체크 예시가 구버전(reporting·principles 누락) — 별도 정비 필요
- **state-tool 강제 게이트** (진단 P0): mock grep·동작증거를 종료코드로 강제하는 코드 작업 → 후속 태스크 권장
- install 실제 실행으로 `~/.opal/PRINCIPLES.md` 배포 검증 미수행 (캡틴 환경 `opal-cli update` 필요)
