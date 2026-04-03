---
type: task
status: 진행중 (PLAN 대기)
created_at: 2026-04-03 17:00
---

# opal-pilot-sdd (opsdd) 스킬 설계 방안 검토 (080)

태스크 경로: `tasks/080-opp-opsdd-design-proposal/`

## 확정된 방향

| 항목 | 결정 |
|------|------|
| 스킬명 | `opal-pilot-sdd` |
| 약어 | `opsdd` |
| 유형 | OPAL 전용 스킬 (`~/.opal/skills/`) |
| 역할 | SDD+TDD 하이브리드 오케스트레이터 |
| 파이프라인 | `SPEC → TASKS → EXECUTE → QA` |

**핵심 원칙**: SPEC이 TASK보다 상위 개념. spec.md를 먼저 확정한 후 tasks.md로 분해.

## 미결 사항 (캡틴 추가 고민 필요)

1. **SPEC 단계 수행 방식**: PM 직접 vs 워커 디스패치
2. **TDD 포함 범위**: 테스트 스켈레톤 필수 포함 vs 선택
3. **oppd 연계**: Phase 3 액션 스킬로 등록 여부
4. **언어 제한**: 범용 vs Python 특화 (ruff/pytest)
5. **validate-spec**: 별도 단계 vs SPEC 단계 내 포함

## 참조

- `temp/sdd.txt` — SDD 기본 개념, spec.md 구조
- `temp/sdd1.txt` — SDD+TDD 하이브리드 8단계 워크플로우
- TASK.md "SDD 방법론 분석" 섹션에 두 파일 내용 정리 완료

## oppd와의 포지셔닝

```
oppd: 아이디어 → PRD/TRD → WBS → 액션 실행 (프로젝트 전체)
opsdd: SPEC(기능 명세) → tasks.md → 구현(TDD) → QA (기능 단위)
       ↑ oppd Phase 3 액션 스킬로 포지셔닝 가능
```
