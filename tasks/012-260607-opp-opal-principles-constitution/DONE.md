# DONE 012 — OPAL Principles 헌법 신설 + 테스트 하네스 강화

> 완료: 2026-06-07 | 모드: agentic (EXECUTE 중 전환) | 캡틴 CLOSE 승인 완료

## 완료 요약

카파시 스킬 철학을 담은 OPAL 헌법(`PRINCIPLES.md`)을 SSOT로 신설하여 always-on 로드시키고,
테스트 관련 하네스가 헌법 §4("목업 금지·동작 증거")를 집행하도록 강화했다.

## 변경 파일

| 구분 | 파일 |
|------|------|
| 신규 | `opal/core/PRINCIPLES.md` (영어 헌법) |
| 신규 | `tasks/012-.../PRINCIPLES.ko.md` · `TASK.md` · `AGENTIC-LOG.md` · `DONE.md` |
| 수정 | `opal/core/AGENT.md` — Eager Step 2.5 헌법 always-on 등록 (v2.9) |
| 수정 | `opal/core/references/harness/coding-principles.md` — 헌법 참조 슬림화 + 목업·증거 체크 (v1.3) |
| 수정 | `opal/core/references/harness/qa-standards.md` — EXECUTE QA 동작 증거 의무 |
| 수정 | `opal/agents/opal-test-agent/AGENT.md` — adversarial + 증거 + 목업 Fail (v1.3) |
| 수정 | `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md` — 구현 목업 금지 (v2.2) |
| 수정 | `scripts/install-mac.sh` (v2.8) · `scripts/install/windows.ps1` (v1.10.0) — 헌법 배포 |

## 성과

1. **헌법 인프라** — 흩어진 행동 원칙을 단일 SSOT로 통합, always-on 로드, 하위 문서는 참조 상속 (구조화·다이어트 기반 확보)
2. **테스트 하네스 §4 집행** — "작성자 신뢰"·"grep=Pass"·"구현 목업 대체" 3대 구멍을 헌법 §4 참조로 차단 (캡틴 사례 방어 강화)

## 검토 결과 (경량 트랙 자체 검토)

- 헌법 참조 일관성 ✅ / 변경이력 6개 문서 행 추가 ✅ / install 배포 반영 ✅

## 잔여 / 후속 태스크 후보

- **state-tool 강제 게이트** (진단 P0): mock grep·동작증거·명확화 차단을 종료코드로 강제 — 목업 100% 차단의 핵심, 별도 태스크 권장
- install 실행으로 `~/.opal/PRINCIPLES.md` 실제 배포 검증 (캡틴 환경 `opal-cli update`)
- README 부트스트랩 체크 예시 동기화 (구버전)
- 부차 다이어트 (opal-harness Guards 중복 등, 이번 보류분)

## 한계 (정직)

이번 태스크는 헌법(원칙) + 문서 하네스 강화다. 헌법 always-on으로 advisory 실효성은 크게 올랐으나,
목업을 기계적으로 100% 차단하는 deterministic 강제는 후속 state-tool 작업에서 완성된다.
