# ANALYSIS: 하네스 병렬 처리 원칙 추가 + opwt 재설계

## T1. opal-harness.md 현황

### 현재 섹션 구조

| 섹션 | 내용 |
|------|------|
| §0 | 용어 정의 |
| §1 | Guards (구현금지, Git, 디스패치의무, 커밋, 루핑제약) |
| §2 | 모듈 구조 (서브하네스, QA체크리스트) |
| §3 | State (STATE.md 구조, 병렬실행state, 세션복원) |
| §4 | TASK 공통 프로세스 |
| §5 | Observability (스킬탐색, 메모리동기화) |
| §6 | Model Mapping |

### 갭

- 병렬 처리 원칙 섹션 없음
- 오케스트레이터가 읽기/실행 모두 순차 처리해도 하네스 위반이 아님
- §3 병렬실행 State는 oppd 전용 — 범용 병렬 원칙이 아님

### 삽입 위치 결정

§7 (변경이력 직전) 신규 추가. 섹션 번호 재정렬 없이 추가.

**이유**: §1 Guards는 금지/제약 성격, 병렬 원칙은 실행 방식 원칙으로 성격이 다름. 새 섹션으로 분리가 명확.

---

## T2. opwt SKILL.md 현황

### Phase → 표준 단계 매핑

| Phase (현재) | 표준 단계 | 모드별 포함 여부 |
|-------------|---------|----------------|
| ❌ 없음 | TASK | 전체 모드 공통 |
| Phase 1 (병렬 분석) | ANALYSIS | 수정/분석만 |
| Phase 2 (PM 진단) | PLAN | 전체 모드 공통 |
| Phase 3 (병렬 작성) | EXECUTE | 작성/수정만 |
| Phase 4 (정합성 검증) | QA | 전체 모드 공통 |

### 모드별 단계 선택 재정의

| 모드 | 단계 |
|------|------|
| 작성 | TASK → PLAN(간략) → EXECUTE → QA |
| 수정 | TASK → ANALYSIS → PLAN → EXECUTE → QA |
| 분석 | TASK → ANALYSIS → PLAN(진단보고) → QA |

### STATE.md 갱신 누락 현황

현재 Phase 설명에 STATE.md 갱신 지시 없음. 하네스 §3 규칙은 있으나 opwt에서 명시하지 않아 실제 동작 보장 불가.

| Phase | STATE 갱신 지시 | 실제 State 추적 가능 여부 |
|-------|---------------|------------------------|
| Phase 1 시작/완료 | ❌ 없음 | ❌ |
| Phase 2 시작/완료 | ❌ 없음 | ❌ |
| Phase 3 배치별 | ❌ 없음 | ❌ |
| Phase 4 시작/완료 | ❌ 없음 | ❌ |

### 보존할 핵심 로직

- `diagnosis.json` 생성 및 `depends_on` 기반 배치 편성
- `references/network-guide.md` (Phase 1/3 워커 프롬프트)
- `references/consistency-rules.md` (QA 워커 프롬프트)
- `[WORKER]` 마커 + PM 컨텍스트 주입
- 외부 참조 산출물 스캔 (Phase 2)
- 커버 범위 (필수 4종 + 선택 4종 + 프로젝트 특화)
- 문서 표준 (opal-doc-standard)

### TASK 단계 추가 시 opwt 전용 확인 항목

op-task 기술 스택 판별 대신:
- **모드 결정**: 작성 / 수정 / 분석
- **대상 문서 유형**: PRD, TRD, 정책서, IA, 외부 API 명세서 등
- **외부 참조 여부**: 와이어프레임, ERD 등 참조할 기존 산출물
- **산출물 저장 경로**: docs/ 하위 구조 확인

---

## 파급 범위 분석

### T1 하네스 변경 파급 범위

| 대상 | 영향 | 조치 필요 |
|------|------|---------|
| opd / opds / opdw | 병렬 원칙 자동 상속 | 없음 (하네스 로드 시 적용) |
| opwt | 병렬 원칙 자동 상속 | 없음 |
| opp / oppd | 병렬 원칙 자동 상속 | 없음 |
| 서브 하네스 (interactive/agentic) | 원칙 추가 없음, 충돌 없음 | 없음 |

→ **하위 호환성 완전 유지**. 추가 섹션이므로 기존 로직 변경 없음.

### 소스/배포 동기화 대상

| 소스 | 배포 |
|------|------|
| `opal/core/references/opal-harness.md` | `~/.opal/references/opal-harness.md` |
| `opal/skills/opal-pilot-write-tech/SKILL.md` | `~/.opal/skills/opal-pilot-write-tech/SKILL.md` |

install-mac.sh가 배포 경로를 자동 처리한다고 가정 (별도 스크립트 수정 불필요).
