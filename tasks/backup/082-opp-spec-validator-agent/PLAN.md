# PLAN: SDD 명세 검증 전용 에이전트 분리

> 작성일: 2026-04-03
> 입력: TASK.md
> 출력: PLAN.md

## 1. 현황 조사

### 관련 파일

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| `opal/skills/opal-pilot-project-dev/SKILL.md` | oppd 오케스트레이터 — 1-1b 섹션에 PM 직접 검증 로직 포함 | 수정 (1-1b를 에이전트 디스패치로 교체) |
| `opal/core/references/opal-skills-registry.json` | 소스 레지스트리 (배포 시 `~/.opal/references/`로 복사) | 수정 (osv 등록) |
| `~/.opal/references/opal-skills-registry.json` | 배포 레지스트리 (런타임 참조) | 수정 (osv 등록 — 소스와 동기) |
| `tasks/081-opp-oppd-spec-validation/DONE.md` | 081 완료 기록 — P1~P6, T1~T5 체크리스트 정의 | 변경 없음 (참조) |
| `tasks/080-opp-opsdd-design-proposal/TASK.md` | opsdd 설계 방안 — spec.md 검증에 동일 에이전트 활용 예정 | 변경 없음 (참조) |

### 현재 상태

**oppd 1-1b (lines 159~214)**:
- PM이 PRD(`docs/PRD.md`)와 TRD(`docs/TRD.md`)를 직접 Read하여 P1~P6 / T1~T5 총 11개 항목을 1:1 판정
- Fail 시 opwt "수정" 모드 재호출 (최대 2회), 2회 Fail 시 사용자 에스컬레이션
- 문제: PM 컨텍스트 소비, opsdd 재사용 불가, 검증 집중도 저하

**레지스트리**:
- 소스: `opal/core/references/opal-skills-registry.json` (v3.0.0)
- 배포: `~/.opal/references/opal-skills-registry.json` (동일 내용)
- `skill-registry.js`가 배포 경로 우선, 소스 fallback으로 탐색
- 소스와 배포 **양쪽 모두 수정**해야 즉시 반영됨

**기존 스킬 구조 패턴** (op-task, opwt 등 참조):
- YAML frontmatter (`name`, `description`, `triggers` 등)
- Harness 섹션 (모드별 서브 하네스 Read)
- 실행 컨텍스트 (오케스트레이터 직접 수행 vs 워커 디스패치)
- 프로세스 (Step 기반)
- 출력 형식 (구조화된 마크다운)

**op-spec-validator 스킬 디렉토리**: 미존재 (신규 생성 필요)

### 영향 범위

| 영역 | 영향 |
|------|------|
| oppd Phase 1 흐름 | 1-1b 내부 로직 변경 (PM 직접 → 에이전트 디스패치). 1-1 → 1-1b → 1-2 흐름 자체는 유지 |
| opsdd (미래) | spec.md 검증에 동일 에이전트 재사용 가능 — SKILL.md에 가이드만 명시 |
| 레지스트리 | opal 그룹에 1개 항목 추가 |
| 기존 프로젝트 | 변경 없음 — oppd 호출 시 자동 적용 |

---

## 2. 구현 계획

### 파일 변경 계획

#### 신규 생성

| # | 파일 경로 | 역할 |
|---|----------|------|
| N1 | `opal/skills/op-spec-validator/SKILL.md` | SDD 명세 검증 전용 에이전트 스킬 정의 |

#### 수정

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| M1 | `opal/skills/opal-pilot-project-dev/SKILL.md` | 1-1b 섹션을 "PM 직접 수행" → "에이전트 디스패치" 방식으로 교체 |
| M2 | `opal/core/references/opal-skills-registry.json` | opal 그룹에 op-spec-validator 항목 추가 |
| M3 | `~/.opal/references/opal-skills-registry.json` | M2와 동일 내용 동기 (배포 레지스트리) |

#### 삭제

없음.

### 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | op-spec-validator SKILL.md 신규 작성 | N1 | 중 (체크리스트 이관 + 인터페이스 설계) |
| 2 | oppd SKILL.md 1-1b 섹션 교체 | M1 | 낮 (기존 로직 삭제 + 디스패치 호출로 교체) |
| 3 | 소스 레지스트리에 osv 등록 | M2 | 낮 |
| 4 | 배포 레지스트리에 osv 등록 | M3 | 낮 (M2 동기) |

### 핵심 설계

#### N1: `opal/skills/op-spec-validator/SKILL.md`

**YAML frontmatter**:
```yaml
name: op-spec-validator
description: |
  **SDD 명세 검증 워커 스킬**. PRD/TRD 문서를 읽고 체크리스트 기반으로 명세 완성도를 판정한다.
  오케스트레이터(oppd 1-1b 등)가 디스패치하여 사용한다. 사용자 직접 호출 불가.
  필수 입력: PRD 경로, TRD 경로, 검증 대상(PRD/TRD/ALL).
  보장 출력: 항목별 {item, result, reason, suggestion} 구조화 판정 결과.
```

> alias/triggers 없음 — 사용자 직접 호출 스킬이 아닌 오케스트레이터 디스패치 전용 워커

**실행 컨텍스트**:
- 워커 에이전트로 디스패치됨 (오케스트레이터가 직접 수행하지 않음)
- 서브 에이전트를 생성하지 않음

**입력 인터페이스** (오케스트레이터가 전달):
```
검증 요청:
- PRD 경로: {path} (검증 대상이 PRD 또는 ALL일 때)
- TRD 경로: {path} (검증 대상이 TRD 또는 ALL일 때)
- 검증 대상: PRD | TRD | ALL
- (선택) 참조 문서: {추가 참조 경로 목록}
```

**프로세스**:
1. 입력 파싱 — PRD/TRD 경로와 검증 대상 확인
2. 대상 문서 Read — PRD 및/또는 TRD를 Read
3. 체크리스트 판정 수행 — 검증 대상에 따라 해당 체크리스트 실행
4. 결과 구조화 — 항목별 판정 결과를 출력 형식으로 정리
5. 결과 반환 — 오케스트레이터에 반환

**PRD 검증 체크리스트 (P1~P6)** — 081에서 그대로 이관:

| # | 항목 | 검증 기준 |
|---|------|-----------|
| P1 | Non-goals 섹션 존재 | 섹션이 있고 내용이 비어 있지 않음 |
| P2 | 타깃 유저 시나리오 형식 | `As a ... I want ... so that ...` 형식, 최소 1개 |
| P3 | 핵심 요구사항 Must 분류 | Must/Should/Nice-to-have 구분이 명시됨 |
| P4 | Acceptance Criteria 존재 | Must 핵심 기능당 최소 1개, GIVEN/WHEN/THEN 형식 |
| P5 | 모호한 표현 없음 | "빠르게", "쉽게", "적절히" 등 수량화 불가 표현 없음 |
| P6 | Open Questions 섹션 존재 | 섹션이 있고 "없음" 또는 구체적 항목이 기재됨 |

**TRD 검증 체크리스트 (T1~T5)** — 081에서 그대로 이관:

| # | 항목 | 검증 기준 |
|---|------|-----------|
| T1 | 기술 스택 버전 명시 | 주요 라이브러리/프레임워크에 버전이 명시됨 |
| T2 | 성능 요구사항 수치화 | 응답시간, 처리량 등이 수치로 명시됨 (미결 허용: "[미결: 수치 확정 필요]"로 표시된 경우 Pass) |
| T3 | 보안 요구사항 명시 | 인증/인가 방식이 구체적으로 기술됨 |
| T4 | PRD Must 기능 커버리지 | PRD의 Must 기능이 모두 TRD에 반영됨 |
| T5 | Open Questions 섹션 존재 | 섹션이 있고 "없음" 또는 구체적 항목이 기재됨 |

**통과 기준**: 해당 체크리스트 전항 Pass. 1개라도 Fail이면 해당 문서 Fail.

**출력 인터페이스** (구조화 반환):
```markdown
## 검증 결과

### 종합 판정
- PRD: Pass | Fail
- TRD: Pass | Fail
- 종합: Pass | Fail

### 상세 결과

| # | 항목 | 결과 | 사유 | 수정 제안 |
|---|------|------|------|----------|
| P1 | Non-goals 섹션 존재 | Pass/Fail | {판정 근거} | {Fail 시 구체적 수정 방향} |
| P2 | ... | ... | ... | ... |
| ... | ... | ... | ... | ... |
| T1 | ... | ... | ... | ... |
| ... | ... | ... | ... | ... |

### Fail 항목 요약 (Fail 존재 시)
- [P{번호}] {항목명}: {Fail 사유} → 제안: {수정 제안}
- [T{번호}] {항목명}: {Fail 사유} → 제안: {수정 제안}
```

**Fail 시 수정 제안 포함 방식**:
- 각 Fail 항목의 `suggestion` 컬럼에 구체적 수정 방향 기재
- 예: P5 Fail → `"빠르게" → "200ms 이내"와 같이 수치화된 표현으로 대체`
- 예: T4 Fail → `PRD Must 기능 "사용자 인증"에 대한 TRD 구현 방안 섹션 추가 필요`

**opsdd 연동 가이드** (F4):
- opsdd SPEC 단계에서 spec.md 검증 시 동일 에이전트 활용 가능
- 입력의 PRD/TRD 경로 대신 spec.md 경로를 전달
- 검증 대상으로 `SPEC`을 추가 지원하거나, 커스텀 체크리스트를 입력으로 받는 확장 인터페이스 예약
- 현 단계에서는 PRD/TRD 체크리스트만 구현하고, opsdd용 체크리스트는 opsdd 스킬 구현 시 추가

#### M1: `opal/skills/opal-pilot-project-dev/SKILL.md` 1-1b 섹션 교체

**삭제 범위**: lines 159~214 (현재 "1-1b. SDD 명세 검증 (PM 직접 수행)" 전체 섹션)
- PRD 검증 체크리스트 표
- TRD 검증 체크리스트 표
- 판정 결과 처리 표
- Fail 시 opwt 재호출 형식
- 재수행/에스컬레이션 로직

**교체 내용**: 에이전트 디스패치 방식의 1-1b 섹션

```markdown
### 1-1b. SDD 명세 검증 (op-spec-validator 디스패치)

opwt 완료 후, PM이 `op-spec-validator` 에이전트를 디스패치하여 PRD/TRD 명세 완성도를 검증한다.
**이 단계를 통과하지 않으면 1-2 사용자 확정으로 진행하지 않는다.**

#### 디스패치 형식

op-spec-validator 에이전트에 아래 정보를 전달한다:

\```
검증 요청:
- PRD 경로: docs/PRD.md
- TRD 경로: docs/TRD.md
- 검증 대상: ALL
\```

#### 결과 수신 및 처리

에이전트가 반환하는 구조화 결과(종합 판정 + 상세 결과)를 수신한다.

| 판정 | 처리 |
|------|------|
| 종합 Pass | 1-2 사용자 확정으로 진행 |
| PRD Fail | opwt "수정" 모드 재호출 — Fail 항목의 수정 제안을 `이슈`로 전달 |
| TRD Fail | opwt "수정" 모드 재호출 — Fail 항목의 수정 제안을 `이슈`로 전달 |
| PRD+TRD 모두 Fail | opwt "수정" 모드 재호출 — 두 문서의 Fail 항목을 통합 전달 |

#### Fail 시 opwt 재호출 형식

\```
//opwt 수정
- 대상 문서: {PRD | TRD | PRD, TRD}
- 이슈:
  - [P{번호}] {항목명}: {Fail 사유} → 제안: {수정 제안}
  - [T{번호}] {항목명}: {Fail 사유} → 제안: {수정 제안}
- 참조 문서: docs/PROJECT.md, docs/ARCHITECTURE.md
\```

opwt 재작성 완료 후 op-spec-validator를 재디스패치한다. (무한루프 방지: 최대 2회)
2회 Fail 시 미통과 항목을 사용자에게 보고하고 판단을 요청한다.
```

**핵심 변경점**:
- 체크리스트 항목 자체 삭제 (에이전트 내부로 이관)
- PM이 직접 Read/판정 → 에이전트 디스패치 + 결과 수신으로 변경
- 결과 처리 흐름(Pass/Fail 분기, opwt 재호출, 최대 2회, 에스컬레이션)은 그대로 유지
- Fail 시 opwt 재호출 형식에 에이전트가 생성한 `수정 제안`을 포함

#### M2/M3: 레지스트리 등록

`opal` 그룹의 `opal-pilot-project-dev` 항목 뒤에 추가:

```json
{
  "name": "op-spec-validator",
  "description": "SDD 명세 검증 워커 (PRD/TRD 체크리스트 기반 판정, 오케스트레이터 디스패치 전용)",
  "paths": ["{project}/.opal/skills/op-spec-validator/SKILL.md", "~/.opal/skills/op-spec-validator/SKILL.md"],
  "dispatched_by": ["opal-pilot-project-dev"]
}
```

- alias/triggers 없음 — 사용자 직접 호출 불가, 오케스트레이터가 경로로 직접 로드
- `dispatched_by` 필드로 oppd에서 디스패치됨을 명시

---

## 3. 실행 체크리스트

> 총 4개 Step

### Step 1: op-spec-validator SKILL.md 신규 작성
- [x] 완료
- **파일**: `opal/skills/op-spec-validator/SKILL.md`
- **작업 내용**: 위 N1 핵심 설계에 따라 SKILL.md 작성. YAML frontmatter + 실행 컨텍스트 + 입력/출력 인터페이스 + PRD 체크리스트(P1~P6) + TRD 체크리스트(T1~T5) + 프로세스 + 출력 형식 + opsdd 연동 가이드 포함
- **완료 기준**: SKILL.md가 존재하고, P1~P6/T1~T5 11개 항목이 081 DONE.md와 동일한 판정 기준으로 포함됨
- **테스트**: 파일 Read 후 체크리스트 항목 수/내용 대조
- **의존**: 없음

### Step 2: oppd SKILL.md 1-1b 섹션 교체
- [x] 완료
- **파일**: `opal/skills/opal-pilot-project-dev/SKILL.md`
- **작업 내용**: 1-1b 섹션(lines 159~214)을 위 M1 핵심 설계 내용으로 교체. 체크리스트 삭제, 디스패치 형식/결과 처리 흐름으로 대체
- **완료 기준**: 1-1b 제목이 "op-spec-validator 디스패치"로 변경됨. P1~P6/T1~T5 체크리스트 테이블이 삭제됨. 디스패치 형식과 결과 처리 표가 존재. 1-1 → 1-1b → 1-2 흐름 유지
- **테스트**: 파일 Read 후 (1) 체크리스트 직접 판정 로직 부재 확인, (2) op-spec-validator 디스패치 호출 존재 확인, (3) 전후 섹션(1-1, 1-2) 무손상 확인
- **의존**: Step 1

### Step 3: 소스 레지스트리에 osv 등록
- [x] 완료
- **파일**: `opal/core/references/opal-skills-registry.json`
- **작업 내용**: `opal` 그룹에 위 M2 JSON 항목 추가. version 및 updated_at 갱신
- **완료 기준**: JSON 파싱 정상, op-spec-validator 항목 존재, alias "osv" 포함
- **테스트**: `node -e "JSON.parse(require('fs').readFileSync('...'))"` 또는 Read 후 항목 확인
- **의존**: 없음

### Step 4: 배포 레지스트리에 osv 등록
- [x] 완료
- **파일**: `~/.opal/references/opal-skills-registry.json`
- **작업 내용**: Step 3과 동일한 항목을 배포 레지스트리에도 추가
- **완료 기준**: 소스 레지스트리(Step 3)와 동일한 op-spec-validator 항목 포함
- **테스트**: 소스와 배포의 op-spec-validator 항목 diff 비교
- **의존**: Step 3

---

## 4. QA 체크리스트

### 기능 테스트
- [ ] op-spec-validator SKILL.md가 PRD 체크리스트 P1~P6을 081 DONE.md와 동일한 판정 기준으로 포함하는가
- [ ] op-spec-validator SKILL.md가 TRD 체크리스트 T1~T5를 081 DONE.md와 동일한 판정 기준으로 포함하는가
- [ ] 입력 인터페이스(PRD 경로, TRD 경로, 검증 대상)가 명확히 정의되었는가
- [ ] 출력 인터페이스(item, result, reason, suggestion 구조)가 명확히 정의되었는가
- [ ] oppd 1-1b가 "PM 직접 수행" 로직을 포함하지 않는가 (체크리스트 삭제 확인)
- [ ] oppd 1-1b가 op-spec-validator 디스패치 형식을 포함하는가
- [ ] oppd Phase 1 흐름(1-1 → 1-1b → 1-2)이 유지되는가
- [ ] Fail 시 opwt 재호출 + 최대 2회 + 에스컬레이션 로직이 유지되는가

### 일관성 테스트
- [ ] 소스 레지스트리와 배포 레지스트리의 op-spec-validator 항목이 동일한가
- [ ] 레지스트리의 paths가 SKILL.md 실제 경로와 일치하는가
- [ ] SKILL.md의 name/alias가 레지스트리 등록과 일치하는가 (op-spec-validator / osv)
- [ ] oppd에서 디스패치하는 스킬명이 레지스트리에 등록된 name과 일치하는가

### 문서 품질
- [ ] SKILL.md YAML frontmatter가 올바른 형식인가 (name, description, triggers)
- [ ] 한국어 본문 + 영어 코드/필드명 규칙을 따르는가
- [ ] opsdd 연동 가이드가 SKILL.md에 포함되어 있는가 (F4)
- [ ] 체크리스트 이관이지 변경이 아닌지 확인 — 항목/기준이 081과 동일한가

---

## 5. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| 체크리스트 이관 시 미세한 판정 기준 변경 | 검증 결과가 기존과 달라질 수 있음 | 081 DONE.md와 oppd 원본의 체크리스트를 1:1 대조하여 완전 동일성 확보 |
| 배포 레지스트리 직접 수정의 안전성 | 소스/배포 불일치 가능 | Step 3 → Step 4 순서로 수행하고, QA에서 diff 비교 수행 |
| opsdd 체크리스트 미정의 | opsdd 구현 시 추가 작업 필요 | 현 단계에서는 PRD/TRD만 구현, SKILL.md에 확장 인터페이스 예약만 명시 |
| 에이전트 디스패치 시 컨텍스트 전달 누락 | 검증에 필요한 참조 문서 경로 미전달 | 입력 인터페이스에 "선택: 참조 문서" 필드를 포함하여 필요 시 추가 문서 전달 가능 |
