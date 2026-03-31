# DONE: opal-pilot agentic mode 추가

> 완료일: 2026-03-31 | 스킬: //opp

## 요약

opd, opds, opp, oppd 4개 오케스트레이터에 **agentic mode**를 추가했다. `--agentic` 플래그로 활성화하면 PM이 사용자를 대행하여 단계 게이트를 자율 통과하고, 100% 완수까지 루핑·모니터링한다.

## 변경 파일

| # | 파일 | 변경 내용 |
|---|------|----------|
| 1 | `opal/core/references/opal-harness.md` | §7 Agentic Mode 섹션 추가 (9개 항목) |
| 2 | `opal/skills/opal-pilot-dev/SKILL.md` | Agentic Mode 섹션 + v1.6 |
| 3 | `opal/skills/opal-pilot-dev-short/SKILL.md` | Agentic Mode 섹션 + v1.6 |
| 4 | `opal/skills/opal-pilot-project/SKILL.md` | Agentic Mode 섹션 + v1.4 |
| 5 | `opal/skills/opal-pilot-project-dev/SKILL.md` | Agentic Mode 섹션 + v3.2 |

## 핵심 설계

### 하네스 §7 구조 (9개 항목)

| # | 항목 | 내용 |
|---|------|------|
| 7-1 | 모드 정의 | interactive (기본) / agentic (opt-in) |
| 7-2 | 활성화 방법 | `--agentic` 플래그 필수, 스킬명 바로 뒤 |
| 7-3 | PM 대행 의무 | 판단 기록, 직접 검증, 완수, 품질 책임, 투명성, 에스컬레이션 책임 |
| 7-4 | PM 자율 검토 | 강화 검토 5기준 + Pass/Fail 판정 |
| 7-5 | Gate 루핑 규칙 | 3회 이내: 재지시, 3회 초과: 심각도 판별 (Critical→STOP, Normal/Minor→LOG+진행) |
| 7-6 | 에스컬레이션 조건 | Critical, 아키텍처 변경, 요구사항 모호, Guards 위반, 판단 모호 |
| 7-7 | 유지 규칙 | 구현 금지, 커밋, 디스패치 의무, 자동 루핑 제약 — 변경 없음 |
| 7-8 | AGENTIC-LOG.md | 6개 카테고리 (GATE/ERROR/FIX/DECISION/IMPROVE/ESCALATION) + 기록 의무 + 템플릿 |
| 7-9 | 완료 보고 | 종합 보고 + AGENTIC-LOG.md 참조 |

### 배포

소스 → `~/.opal/` 배포 완료 (5개 파일)

## 후속 조치

없음
