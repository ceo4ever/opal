# DONE: opal-pm 레퍼런스 신규 구축 — PM 행동 프로세스 SSOT

> 완료일: 2026-04-05

## 변경 파일

| # | 파일 | 변경 내용 |
|---|------|----------|
| 1 | `opal/core/references/opal-pm.md` | **신규 생성** — PM 행동 프로세스 레퍼런스 (§1~§8) |
| 2 | `~/.opal/AGENT.md` | PM 행동 상세 → 위임 참조로 교체 + Eager 4단계에 opal-pm.md Read 추가 |
| 3 | `opal/skills/opal-orchestrator/SKILL.md` | 폐기 마킹 (`deprecated: true`) |
| 4 | `opal/core/references/opal-harness-interactive.md` | §3 PM Gate 참조 경로를 opal-pm.md로 갱신 |

## 핵심 변경 사항

- **opal-pm.md**: PM 행동 프로세스의 SSOT. 8개 섹션(역할 개요, 컨텍스트 로드, 디스패치 전 프로세스, 검토 게이트, 학습 루프, 참조 문서 전달, 문서/코드 불일치 판단, 워커 행동 규칙)
- **부트스트랩**: Eager 4단계로 삽입 (harness → opal-pm → .opal/AGENT 순서)
- **AGENT.md 슬림화**: PM 행동 상세 ~66행 제거 → 위임 참조 6행으로 교체
- **역할 분리**: opal-pm.md = HOW, .opal/AGENT.md = WHAT
- **신규 기능**: 디스패치 전 5단계 프로세스(문서 Read → 핵심 제약 추출 → 워커 주입) + 문서/코드 불일치 시 코드 우선 원칙
