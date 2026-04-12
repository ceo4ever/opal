# TASK: SDD 명세 검증 전용 에이전트 분리

> 작성일: 2026-04-03 | 작업 유형: 개선 | 적용 스킬: opp | 모드: interactive
> 입력: oppd 1-1b SDD 명세 검증 (081), opsdd 설계 방안 (080)
> 출력: spec-validator 에이전트 스킬 + oppd/opsdd 연동

## 작업 목표

081 태스크에서 oppd 1-1b에 추가된 "PM 직접 수행" 방식의 SDD 명세 검증을 전용 에이전트로 분리하여, oppd와 opsdd 양쪽에서 재사용 가능한 검증 레이어를 구축한다.

## 배경

### 현재 oppd 1-1b 방식 (PM 직접 수행)

```
opwt 완료 → PM이 PRD/TRD 직접 Read → P1~P6 / T1~T5 체크리스트 직접 판정 → Pass/Fail 처리
```

**문제점**:
1. **PM 컨텍스트 소비**: 검증 판단 작업이 PM 컨텍스트를 차지 — 대형 PRD/TRD일수록 비효율
2. **재사용 불가**: oppd 전용 로직 → opsdd(080)도 동일한 검증이 필요하나 별도 구현 필요
3. **검증 집중도**: PM이 오케스트레이션과 검증을 동시 수행 → 누락 위험

### 에이전트 분리 후 기대 구조

```
opwt 완료 → spec-validator 에이전트 디스패치 (PRD+TRD 경로 전달)
           → {item, result, reason, suggestion} 구조화 반환
           → PM이 결과만 수신 → Pass/Fail 처리
```

### opsdd 연계 기대

opsdd(080) SPEC 단계에서도 동일 에이전트를 호출하여 spec.md 검증에 활용 가능.

## 요구사항

- [x] `op-spec-validator` 스킬 신규 생성 (OPAL 전용, `~/.opal/skills/` 계열)
- [x] 입력 인터페이스 정의: PRD 경로, TRD 경로, 체크리스트 타입(PRD/TRD/ALL)
- [x] 출력 인터페이스 정의: 항목별 Pass/Fail + 실패 사유 + 수정 제안 구조화 반환
- [x] PRD 체크리스트 P1~P6 검증 로직 이관 (oppd 1-1b → 에이전트)
- [x] TRD 체크리스트 T1~T5 검증 로직 이관 (oppd 1-1b → 에이전트)
- [x] oppd SKILL.md 1-1b를 "PM 직접 수행" → "에이전트 디스패치" 방식으로 변경
- [x] opal-skills-registry.json에 `op-spec-validator` 등록 (alias 없음 — 디스패치 전용 워커)
- [x] (선택) opsdd 연동 가이드를 스킬 SKILL.md에 명시

## 제약 조건

- oppd 1-1b의 체크리스트 항목(P1~P6, T1~T5)과 판정 기준은 유지한다 — 로직 이관이지 변경 아님
- OPAL 개발/배포 경계 원칙 준수 (소스: `opal/skills/`, 배포: `~/.opal/skills/`)
- 하네스 Guards 준수 (디스패치 의무 원칙, 커밋 규칙)
- oppd Phase 1의 전체 흐름(1-1 → 1-1b → 1-2)은 유지한다

## 관련 문서

- `opal/skills/opal-pilot-project-dev/SKILL.md` — oppd 1-1b 수정 대상
- `tasks/081-opp-oppd-spec-validation/DONE.md` — 현재 1-1b 로직 및 체크리스트 정의
- `tasks/080-opp-opsdd-design-proposal/TASK.md` — opsdd 설계 (연동 후보)
- `~/.opal/references/opal-harness.md` — 디스패치 의무 원칙
- `~/.opal/references/opal-skills-registry.json` — 스킬 등록 대상
