# DONE: 하네스 모듈화 — 공통 + 모드별 분리

> 완료일: 2026-03-31 | 스킬: //opp

## 요약

opal-harness.md를 **공통 + 모드별 서브 하네스** 구조로 모듈화했다. 추가로 EXECUTE 후 QA 체크리스트 갱신 프로세스를 보강했다.

## 변경 파일

| # | 파일 | 변경 내용 |
|---|------|----------|
| 1 | `opal/core/references/opal-harness-interactive.md` | **신규** — §2 Gates 이동 |
| 2 | `opal/core/references/opal-harness-agentic.md` | **신규** — §7 Agentic Mode 이동 |
| 3 | `opal/core/references/opal-harness.md` | §2,§7 제거 + §2 모듈 구조 + QA 체크리스트 검증 추가 |
| 4 | `opal/skills/opal-pilot-dev/SKILL.md` | §7→agentic 참조 + EXECUTE 후 PM Gate 추가 (v1.7) |
| 5 | `opal/skills/opal-pilot-dev-short/SKILL.md` | 동일 (v1.7) |
| 6 | `opal/skills/opal-pilot-project/SKILL.md` | §7→agentic 참조 + EXECUTE 후 QA Gate 추가 (v1.5) |
| 7 | `opal/skills/opal-pilot-project-dev/SKILL.md` | §7→agentic 참조 (v3.3) |
| 8 | `~/.opal/AGENT.md` | 부트스트랩 설명 텍스트 갱신 |

## 모듈 구조

```
opal/core/references/
├── opal-harness.md              ← 공통 (Guards, State, TASK, Observability, Model Mapping, 모듈 구조)
├── opal-harness-interactive.md  ← interactive 모드 (Gates)
└── opal-harness-agentic.md      ← agentic 모드 (PM 대행, 자율 검토, Gate 루핑, AGENTIC-LOG)
```

로딩: 오케스트레이터 → 공통 Read → §2 모듈 구조에 따라 서브 하네스 1개 추가 Read.

## 추가 보강

- 공통 하네스에 "QA 체크리스트 검증" 섹션 추가 — DONE.md 전 갱신 의무
- opd/opds: EXECUTE 후 PM Gate (TEST-SCENARIO 결과 + QA 체크리스트 갱신)
- opp: EXECUTE 후 QA Gate + PM Gate + QA 체크리스트 갱신
