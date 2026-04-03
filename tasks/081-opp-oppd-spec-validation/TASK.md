# TASK: oppd PRD+TRD SDD 기반 명세 검증 단계 추가

> 작성일: 2026-04-03 | 작업 유형: 개선 | 적용 스킬: opp | 모드: interactive
> 입력: oppd SKILL.md, SDD 방법론 분석 (080 태스크)
> 출력: oppd Phase 1에 SDD 검증 단계를 추가하는 설계 방안 (PLAN.md)

## 작업 목표

oppd Phase 1(PRD+TRD 작성) 완료 후, SDD 방법론에 입각한 명세 완성도 검증 단계를 설계하여 oppd SKILL.md 개선 방안을 제안한다.

## 배경

### 현재 oppd Phase 1 흐름

```
opwt 호출 → PRD+TRD 작성 → opwt Phase 4(정합성 검증) → 사용자 확정 → Phase 2(WBS)
```

### 검증 공백

| 검증 유형 | 현재 상태 | 문제 |
|-----------|-----------|------|
| PRD ↔ TRD 정합성 | opwt Phase 4에서 수행 | ✅ 커버됨 |
| PRD 명세 완성도 | ❌ 없음 | AC가 GIVEN/WHEN/THEN으로 작성되었는가? 범위가 명확한가? |
| TRD 명세 완성도 | ❌ 없음 | 비기능 요구사항이 수치화되었는가? Open Questions가 해소되었는가? |
| WBS 실행 가능성 | ❌ 없음 | PRD/TRD가 충분히 구체적이어야 WBS 분할 가능 |

SDD 철학: **명세가 불완전한 상태로 구현 단계(WBS→EXECUTE)에 진입하면 환각, 범위 확장, 재작업이 발생한다.**

### SDD 방법론의 시사점 (080 태스크 분석)

- spec.md의 Acceptance Criteria = TDD 테스트 케이스의 원천
- validate-spec: 섹션 존재 여부 + GIVEN/WHEN/THEN 형식 + 미결 항목 해소 여부
- 검증 실패 → 수정 → 재검증 (통과 후에만 다음 단계 진입)

## 요구사항

- [x] oppd Phase 1의 현재 검증 범위와 공백을 명확히 분석한다
- [x] PRD 대상 SDD 검증 기준 항목을 설계한다
- [x] TRD 대상 SDD 검증 기준 항목을 설계한다
- [x] 검증 수행 주체를 결정한다 (PM 직접 수행)
- [x] 검증 실패 시 처리 흐름을 설계한다 (opwt 수정 모드 재호출, 최대 2회)
- [x] oppd SKILL.md에 반영할 위치와 방법을 결정한다 (1-1b 삽입)

## 제약 조건

- oppd Phase 1의 기본 흐름(opwt 위임)을 유지한다
- 검증 단계가 사용자 경험을 과도하게 지연시키지 않아야 한다
- 하네스 Guards 준수 (디스패치 의무 원칙)
- OPAL 프로젝트 개발/배포 경계 원칙 준수 (소스 수정만, 배포는 캡틴 결정)

## 관련 문서

- `~/.opal/skills/opal-pilot-project-dev/SKILL.md` — 수정 대상 (oppd)
- `~/.opal/skills/opal-pilot-write-tech/SKILL.md` — opwt Phase 4 정합성 검증 현황 파악용
- `tasks/080-opp-opsdd-design-proposal/TASK.md` — SDD 방법론 분석 (섹션 "SDD 방법론 분석" 참조)

## SDD 검증 기준 참고 (설계 입력)

### PRD 검증 항목 후보

| 항목 | 검증 내용 |
|------|-----------|
| 사용자 스토리 | `As a ... I want ... so that ...` 형식, 최소 1개 |
| Acceptance Criteria | GIVEN/WHEN/THEN 형식, 핵심 기능당 최소 1개 |
| Non-goals | 명시적으로 제외 범위 정의 |
| Open Questions | 미결 사항 없음 (또는 허용 가능 수준) |
| Must 요구사항 | 검증 가능한 단위로 작성 (모호한 표현 없음) |

### TRD 검증 항목 후보

| 항목 | 검증 내용 |
|------|-----------|
| 기술 스택 | 버전 명시 |
| 성능 요구사항 | 수치화 (응답시간 N초 이내 등) |
| 보안 요구사항 | 인증/인가 방식 명시 |
| PRD 요구사항 커버리지 | PRD의 모든 Must 기능이 TRD에 반영되었는가 |
| API/인터페이스 계약 | 주요 인터페이스 명세 존재 여부 |
