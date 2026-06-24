# PLAN: CLOSE 단계 관련 문서 업데이트 스텝 추가

> 작성일: 2026-06-24 | 입력: TASK.md (ANALYSIS.md 없음)
> 모드: Multi-Feature (F-001 ~ F-003)

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

8개 pilot SKILL.md의 CLOSE 단계에서 `op-brain-ingest` 디스패치 직전에 "관련 문서 업데이트" 스텝을 삽입한다. PROJECT.md 레지스트리 + 태스크 changed_files를 종합하여 기획·설계 문서를 최신화한 뒤 brain ingest가 이루어지도록 보장함으로써 ingest 품질을 높인다. 스텝 삽입에 따른 번호 재정렬과 8개 파일 변경이력 행 추가가 동반된다.

### 1.2 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | 8개 CLOSE에 "관련 문서 업데이트" 스텝 삽입 | F-1 | P0 | 없음 |
| F-002 | 스텝 번호 재정렬 | F-2 | P0 | F-001 (동일 편집에서 동반 처리) |
| F-003 | 변경이력 행 추가 (8개 파일) | F-3 | P0 | F-001 |

### 1.3 기능 의존 그래프 (ASCII)

```
F-001 (스텝 삽입) ─┬─ F-002 (번호 재정렬, 동일 Edit에서 동반)
                   └─ F-003 (변경이력 행 추가)
```

> F-001과 F-002는 동일 CLOSE 섹션의 단일 Edit으로 함께 처리된다 (스텝 삽입 시 후속 항목 번호를 +1로 다시 적는다). F-003은 동일 파일의 변경이력 섹션 별도 Edit이다. 따라서 8개 파일 각각이 1개 Step(= 2회 Edit: CLOSE 본문 + 변경이력)으로 묶인다.

---

## 리스크 가설 표

> PLAN 단계에서 작성. TEST-SCENARIO.md §1의 입력이 됨.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | 7개 numbered-list 파일(opd/opp/opdd/opds/opdw/opsdd/opwt) CLOSE 번호 항목 | 스텝 삽입 후 후속 번호 미재정렬 → 번호 중복/누락 (예: `1.→2.→2.` 또는 `1.→3.`). "완료 보고" 항목 번호가 brain ingest 번호와 충돌 | P1 (문서 정합성, 파이프라인 실행 혼선) | L1(grep: 번호 연속성 검사) | S-2 (번호 연속성), S-1 (신규 스텝 존재) |
| H-2 | 신규 스텝 위치 계약 | 신규 스텝이 brain ingest **뒤**에 삽입되면 "최신화 후 ingest" 보장 깨짐 (태스크 목표 무효화) | P0 (태스크 핵심 AC 위반) | L1(grep: 신규 스텝 줄번호 < brain ingest 줄번호) | S-3 (위치: brain ingest 직전) |
| H-3 | 신규 스텝 내용 계약 | "PROJECT.md 레지스트리" / "changed_files" 키워드 누락 → AC 미충족, ingest 기준 모호 | P1 (AC 위반) | L1(grep: 키워드 존재) | S-4 (키워드 포함) |
| H-4 | opgc 구조 상이 (numbered-list 아님, ### 4.x 서브섹션 + brain ingest는 무번호 단락) | numbered-list 가정으로 잘못 편집 시 §4.2 흐름 파손 / brain ingest 단락 위치 오류 | P1 | L1(grep: opgc 신규 스텝이 brain ingest 단락 앞에 위치) | S-3 (opgc 개별 위치 검증) |
| H-5 | 변경이력 의무 (.opal/AGENT.md §문서 변경이력) | 8개 중 일부 누락 → 추적성 규칙 위반 | P2 (거버넌스) | L1(grep: `042` + `2026-06-24` 행 8회) | S-5 (변경이력 8파일) |
| H-6 | Surgical Changes (TASK §제약: CLOSE 외 섹션 수정 금지) | CLOSE 외 영역 의도치 않은 변경 → 회귀 | P1 | L1(git diff 범위 검사) | S-6 (회귀: CLOSE+변경이력 외 무변경) |

**가설 도출 메모**:
- H-예 대응: 본 태스크는 코드 계약이 아닌 **문서 절차 계약**이므로, "번호 연속성"(H-1)과 "삽입 위치 순서"(H-2)가 깨지기 쉬운 핵심 계약이다.

---

## 2. 기능별 분석

### F-001: 8개 CLOSE에 "관련 문서 업데이트" 스텝 삽입

#### 2.1.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 스킬 | `opal/skills/opal-pilot-dev/SKILL.md` | opd Full Task 오케스트레이터 (STEP 6 CLOSE, 번호 1~3, brain=항목2) | 수정 |
| 스킬 | `opal/skills/opal-pilot-project/SKILL.md` | opp Project Task (STEP 4 CLOSE, 번호 1~3, brain=항목2) | 수정 |
| 스킬 | `opal/skills/opal-pilot-data-design/SKILL.md` | opdd Data Design (STEP 6 CLOSE, 번호 1~3, brain=항목2) | 수정 |
| 스킬 | `opal/skills/opal-pilot-dev-short/SKILL.md` | opds Short Task (STEP 5 CLOSE, 번호 1~3, brain=항목2) | 수정 |
| 스킬 | `opal/skills/opal-pilot-dev-wireframe/SKILL.md` | opdw Wireframe (STEP 4 CLOSE, 번호 1~3, brain=항목2) | 수정 |
| 스킬 | `opal/skills/opal-pilot-gc/SKILL.md` | opgc GC (STEP 4 CLOSE, **무번호 서브섹션 ### 4.1~4.3**, brain=§4.2 내 무번호 단락) | 수정 |
| 스킬 | `opal/skills/opal-pilot-sdd/SKILL.md` | opsdd SDD (Phase 6 CLOSE, 번호 1~5, brain=항목4) | 수정 |
| 스킬 | `opal/skills/opal-pilot-write-tech/SKILL.md` | opwt Write-Tech (CLOSE 단계, 번호 1~3, brain=항목2) | 수정 |

#### 2.1.2 현재 구현 (CLOSE 구조 실측)

ANALYSIS.md 없음 — 8개 파일 CLOSE 섹션을 직접 Read하여 구조를 확정했다. 3가지 패턴으로 분류된다:

**패턴 A — numbered-list, brain=항목2** (6개: opd / opp / opdd / opds / opdw / opwt)
공통 골격:
```
1. DONE.md 생성 후 행 mark ...
2. **op-brain-ingest 디스패치** (DONE.md 생성 직후 실행): ...
3. 완료 보고
```
- opd: `opal/skills/opal-pilot-dev/SKILL.md:234-244` (STEP 6)
- opp: `opal/skills/opal-pilot-project/SKILL.md:122-131` (STEP 4, brain 항목에 "PM Gate 통과 후" 문구 포함)
- opdd: `opal/skills/opal-pilot-data-design/SKILL.md:205-217` (STEP 6, 산출물 명칭 "사전·ERD·DDL")
- opds: `opal/skills/opal-pilot-dev-short/SKILL.md:174-183` (STEP 5)
- opdw: `opal/skills/opal-pilot-dev-wireframe/SKILL.md:148-157` (STEP 4)
- opwt: `opal/skills/opal-pilot-write-tech/SKILL.md:381-395` (CLOSE 단계)

**패턴 B — numbered-list, brain=항목4** (1개: opsdd)
```
1. 전체 TS Green 확인
2. 전체 ACT DONE.md 존재 확인
3. DONE.md 생성 후 CLOSE 행 mark
4. **op-brain-ingest 디스패치** ...
5. 완료 보고
```
- opsdd: `opal/skills/opal-pilot-sdd/SKILL.md:283-302` (Phase 6). 산출물 명칭 "SPEC·SPEC-PLAN 결정·신규 엔티티". DONE.md 생성은 항목3.

**패턴 C — 무번호 서브섹션** (1개: opgc)
```
### 4.1 DONE.md 생성
### 4.2 CLOSE 행 갱신
   ~/.opal/...mark --row 7 --done
   > [MUST] 행 갱신 / CLOSE 진입 게이트 ...
   **op-brain-ingest 디스패치** (무번호 단락)   ← line 349
### 4.3 수정이 필요한 경우 — opds 체인
```
- opgc: `opal/skills/opal-pilot-gc/SKILL.md:324-358` (STEP 4). DONE.md 생성=§4.1, mark=§4.2, brain ingest=§4.2 내 무번호 굵은 단락. **번호 항목 없음 → F-002 재정렬 비해당**.

#### 2.1.3 영향 범위

- **상위 의존**: 각 SKILL.md를 Read하는 오케스트레이터 PM의 CLOSE 실행 절차. 신규 스텝은 PM이 직접 판단·수행 또는 워커 호출하며, 대상 문서가 없으면 스킵하는 비차단(non-blocking) 설계 — brain ingest 비중단 원칙과 동일 결을 유지한다.
- **하위 의존**: 없음 (스킬 외부 코드/도구 미참조). state-tool 호출·STATE 행 구조 불변.
- **공유 상태**: STATE.md 행 구조는 변경하지 않는다 (신규 스텝은 절차 텍스트일 뿐 STATE 행을 추가하지 않음). 따라서 각 파일의 "STATE 행 N 불변".
- **회귀 위험 지점**: 변경이력 표(각 파일 말미), CLOSE 외 게이트 안내(`> CLOSE 진입 게이트 ...` 인용블록)는 건드리지 않는다.

### F-002: 스텝 번호 재정렬

#### 2.2.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 스킬 | 패턴 A 6개 + 패턴 B opsdd | 신규 스텝 삽입에 따른 후속 항목 번호 +1 | 수정 |
| 스킬 | opgc (패턴 C) | 번호 항목 없음 → 재정렬 비해당 (서브섹션 헤딩 ### 4.1~4.3 유지) | 변경 없음 |

#### 2.2.2 현재 구현

- 패턴 A: brain ingest = 항목2 → 삽입 후 brain ingest=항목3, 완료 보고=항목4.
- 패턴 B (opsdd): brain ingest = 항목4 → 삽입 후 brain ingest=항목5, 완료 보고=항목6.
- 패턴 C (opgc): 번호 없음 → 재정렬 없음.

#### 2.2.3 영향 범위

CLOSE 섹션 내부 번호만 영향. CLOSE 외 번호 매김(다른 STEP의 1./2.)과 무관.

### F-003: 변경이력 행 추가 (8개 파일)

#### 2.3.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 스킬 | 8개 SKILL.md 각 변경이력 표 | 신규 버전 행 추가 (`2026-06-24` + `042`) | 수정 |

#### 2.3.2 현재 구현 (각 파일 최신 변경이력 행 / 버전)

| 파일 | 최신 행 위치 | 최신 버전 |
|------|------------|----------|
| opd | `:391` | v4.2 |
| opp | `:266` | v3.2 |
| opdd | `:317` | v1.0 |
| opds | `:364` | v3.9 |
| opdw | `:294` | v2.9 |
| opgc | `:523` | v1.6 |
| opsdd | `:523` | v3.1.0 |
| opwt | `:545` | v4.3 |

> 버전 증가 규칙: 각 파일의 최신 버전에서 PATCH 1 증가 (예: opd v4.2 → v4.3, opdd v1.0 → v1.1, opsdd v3.1.0 → v3.1.1). EXECUTE 시 워커가 각 파일 최신 행을 다시 Read하여 정확한 다음 버전을 부여한다.

#### 2.3.3 영향 범위

변경이력 표 말미 행 추가뿐. 기존 행 불변.

---

## 3. 기능별 설계

### F-001: 8개 CLOSE에 "관련 문서 업데이트" 스텝 삽입

#### 3.1.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/skills/opal-pilot-dev/SKILL.md` | 스킬 | STEP 6 CLOSE 항목1↔2 사이 신규 스텝 삽입 | `:234-235` |
| 2 | `opal/skills/opal-pilot-project/SKILL.md` | 스킬 | STEP 4 CLOSE 항목1↔2 사이 삽입 | `:122-123` |
| 3 | `opal/skills/opal-pilot-data-design/SKILL.md` | 스킬 | STEP 6 CLOSE 항목1↔2 사이 삽입 (산출물 명칭: 사전·ERD) | `:205-209` |
| 4 | `opal/skills/opal-pilot-dev-short/SKILL.md` | 스킬 | STEP 5 CLOSE 항목1↔2 사이 삽입 | `:174-175` |
| 5 | `opal/skills/opal-pilot-dev-wireframe/SKILL.md` | 스킬 | STEP 4 CLOSE 항목1↔2 사이 삽입 (산출물 명칭: 와이어프레임) | `:148-149` |
| 6 | `opal/skills/opal-pilot-gc/SKILL.md` | 스킬 | §4.2 mark 인용블록↔brain ingest 무번호 단락 사이 신규 굵은 단락 삽입 | `:347-349` |
| 7 | `opal/skills/opal-pilot-sdd/SKILL.md` | 스킬 | Phase 6 CLOSE 항목3↔4 사이 삽입 (산출물 명칭: SPEC·SPEC-PLAN) | `:288-293` |
| 8 | `opal/skills/opal-pilot-write-tech/SKILL.md` | 스킬 | CLOSE 단계 항목1↔2 사이 삽입 | `:381-386` |

> 근거: 각 파일 CLOSE 실측 줄번호 (§2.1.2).

#### 3.1.2 신규 스텝 텍스트 설계

[MUST] `.opal/AGENT.md §업무 수행 지침`: 본 태스크는 스킬 SSOT(`opal/skills/`)만 수정하며 `~/.opal/` 직접 편집 금지. (TASK §제약)
[MUST] TASK §제약 "CLOSE 외 다른 섹션 수정 금지 (Surgical Changes)": CLOSE 본문 + 해당 파일 변경이력 외 영역 무변경.

**(a) 패턴 A·B 공용 — numbered-list 삽입 텍스트** (브레인 ingest 직전 위치, 번호는 삽입 지점에 맞춤)

아래를 "DONE.md 생성" 항목 **다음**, "op-brain-ingest 디스패치" 항목 **앞**에 삽입한다. 삽입되는 항목 번호 = (직전 DONE.md 생성 항목 번호 + 1), 이후 brain ingest·완료 보고 번호를 각각 +1로 다시 적는다.

```markdown
N. **관련 문서 업데이트** (op-brain-ingest 디스패치 직전 실행):
   - `<프로젝트-루트>/docs/PROJECT.md`의 "프로젝트 문서" 레지스트리와 이번 태스크의 `changed_files`(EXECUTE 산출)를 양쪽 종합하여, 태스크 결과로 내용이 달라진 관련 문서(ARCHITECTURE.md·기획서·{도메인 산출물} 등)를 식별한다.
   - 갱신 대상이 있으면 PM이 판단하여 직접 수정하거나 적합한 워커를 디스패치해 최신화한다. 갱신 대상이 없으면 자연 스킵(no-op) — CLOSE를 중단시키지 않는다.
   - 목적: brain ingest 이전에 기획·설계 문서를 최신 상태로 만들어 ingest 품질을 보장한다.
```

- `{도메인 산출물}` 치환값 (각 파일 brain ingest 항목의 산출물 명칭과 일관):
  - opd / opp / opds / opdw / opwt → "PLAN 결정·신규 엔티티" → 본문은 `ARCHITECTURE.md·기획서 등`으로 일반화
  - opdd → "사전·ERD" → `ARCHITECTURE.md·표준사전·ERD 등`
  - opdw → 와이어프레임 맥락 → `ARCHITECTURE.md·기획서·와이어프레임 등`
  - opsdd → `ARCHITECTURE.md·SPEC·기획서 등`

> 산출물 명칭 일관성 근거: 각 파일 brain ingest 항목의 기존 산출물 표현을 계승 (opdd `:211` "사전·ERD·DDL", opsdd `:295` "SPEC·SPEC-PLAN 결정", opdw `:182` "wireframe.md"). citation-rules §용어 일관성.

**(b) 패턴 C 전용 — opgc 무번호 굵은 단락 삽입 텍스트**

opgc는 numbered-list가 아니므로 §4.2의 `**op-brain-ingest 디스패치** ...` 굵은 단락 **바로 앞**에 동일 형식의 굵은 단락을 삽입한다 (번호 없음):

```markdown
**관련 문서 업데이트** (op-brain-ingest 디스패치 직전 실행):

- `<프로젝트-루트>/docs/PROJECT.md`의 "프로젝트 문서" 레지스트리와 이번 GC 태스크의 `changed_files`를 양쪽 종합하여, 결과로 내용이 달라진 관련 문서(ARCHITECTURE.md·기획서 등)를 식별한다.
- 갱신 대상이 있으면 PM이 직접 수정하거나 적합한 워커를 디스패치해 최신화한다. 없으면 자연 스킵(no-op) — CLOSE를 중단시키지 않는다.
- 목적: brain ingest 이전에 기획·설계 문서를 최신 상태로 만들어 ingest 품질을 보장한다.
```

> opgc는 진단 전담(소스 미수정)이나, CLOSE의 brain ingest 자체가 산출물 누적 절차이므로 동일하게 "문서 최신화 → ingest" 순서 보장이 유효하다.

#### 3.1.3 환경 변경

해당 없음.

#### 3.1.4 배치/마이그레이션

해당 없음.

#### 3.1.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | F-1 AC (신규 스텝 존재) | 산출물 검사 (grep) | 8개 파일 CLOSE에 "관련 문서 업데이트" 문자열이 각 1회 이상 존재 |
| TS-002 | F-1 AC (위치) | 산출물 검사 (grep 줄번호 비교) | 8개 파일 모두 "관련 문서 업데이트" 줄번호 < "op-brain-ingest 디스패치" 줄번호 |
| TS-003 | F-1 AC (키워드) | 산출물 검사 (grep) | 신규 스텝 블록에 "PROJECT.md" + "changed_files" 키워드 모두 포함 (8파일) |

### F-002: 스텝 번호 재정렬

#### 3.2.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | 패턴 A 6개 | 스킬 | brain ingest 2→3, 완료 보고 3→4 | §2.2.2 |
| 2 | opsdd | 스킬 | brain ingest 4→5, 완료 보고 5→6 | `:293,302` |

#### 3.2.2 설계

- 삽입과 재정렬은 **단일 Edit**으로 처리한다 (old_string = "1. DONE.md 생성...\n2. **op-brain-ingest..." → new_string = "1. DONE.md 생성...\n2. **관련 문서 업데이트...\n3. **op-brain-ingest...\n4. 완료 보고"). 부분 교체로 번호 충돌을 원천 차단한다.
- opgc(패턴 C): 번호 항목 없음 → 재정렬 스킵.

#### 3.2.3 환경 변경 / 3.2.4 배치

해당 없음.

#### 3.2.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-004 | F-2 AC (번호 연속성) | 산출물 검사 (grep) | 패턴 A·B 7개 파일 CLOSE 번호 항목이 1부터 연속 (중복/건너뜀 없음). opgc는 번호 항목 부재로 비해당 |

### F-003: 변경이력 행 추가 (8개 파일)

#### 3.3.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1~8 | 8개 SKILL.md 변경이력 표 | 스킬 | 신규 버전 행 1줄 추가 | §2.3.2 |

#### 3.3.2 설계 — 변경이력 행 템플릿

각 파일 변경이력 표 말미에 추가 (버전은 §2.3.2 기준 PATCH+1):

```markdown
| v{다음버전} | 2026-06-24 | CLOSE 단계 op-brain-ingest 디스패치 직전에 "관련 문서 업데이트" 스텝 삽입 — PROJECT.md 레지스트리 + changed_files 종합으로 관련 문서 최신화 후 ingest (없으면 no-op). 후속 항목 번호 재정렬 (042) |
```

- 패턴 C(opgc)는 번호 재정렬이 없으므로 행 문구에서 "후속 항목 번호 재정렬"을 생략한다:
  `| v1.7 | 2026-06-24 | §4.2 CLOSE op-brain-ingest 디스패치 직전에 "관련 문서 업데이트" 단락 삽입 — PROJECT.md 레지스트리 + changed_files 종합으로 관련 문서 최신화 후 ingest (없으면 no-op) (042) |`

[MUST] `.opal/AGENT.md §문서 변경이력`: "스킬·에이전트·참조 문서 수정 시 변경이력 표에 행을 추가한다 (일시 KST + 태스크 번호 포함)."

#### 3.3.3 환경 변경 / 3.3.4 배치

해당 없음.

#### 3.3.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-005 | F-3 AC (변경이력) | 산출물 검사 (grep) | 8개 파일 변경이력에 `042` + `2026-06-24` 포함 행이 각 1개 존재 |
| TS-006 | 제약 (Surgical) | 회귀 (git diff) | 각 파일 변경 범위가 CLOSE 섹션 + 변경이력 행에 국한, 그 외 무변경 |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)

| Phase | 기능 | Step | agent | 실행 | 비고 |
|-------|------|------|-------|------|------|
| 1 | F-001+F-002+F-003 | 1~8 | opal-task-agent | 8 Step 병렬 가능 (독립 파일) | 각 Step = 1파일 (CLOSE 본문 Edit + 변경이력 Edit) |

> F-001(삽입)·F-002(재정렬)·F-003(변경이력)은 동일 파일 내에서 함께 처리되므로 파일 단위로 묶는다. 8개 파일은 서로 독립적이라 병렬 디스패치 가능.

### 4.2 실행 체크리스트

> 총 8개 Step | Phase 1개 | 실행 모드: 복잡 (8 Step ≥ 6, 8 파일 ≥ 4)

#### Step 1: opd CLOSE 스텝 삽입 + 번호 재정렬 + 변경이력
- [ ] 완료
- **소속 기능**: F-001, F-002, F-003
- **영역**: 스킬
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-pilot-dev/SKILL.md`
- **작업 내용**: STEP 6 CLOSE(`:234-244`) 항목1↔2 사이에 §3.1.2(a) 텍스트(번호 2, `{도메인 산출물}`="ARCHITECTURE.md·기획서 등") 삽입, 기존 brain ingest 2→3 / 완료 보고 3→4 재정렬. 변경이력 표(`:391` 다음)에 §3.3.2 행(v4.3) 추가.
- **완료 기준**: TS-001/002/003/004/005/006 충족 (opd 한정)
- **테스트**: TS-001~006
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 2: opp CLOSE 스텝 삽입 + 번호 재정렬 + 변경이력
- [ ] 완료
- **소속 기능**: F-001, F-002, F-003
- **영역**: 스킬
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-pilot-project/SKILL.md`
- **작업 내용**: STEP 4 CLOSE(`:122-131`) 항목1↔2 사이에 §3.1.2(a) 텍스트 삽입(기존 brain 항목의 "PM Gate 통과 후" 문구는 brain ingest 항목에 보존), brain 2→3 / 완료 보고 3→4 재정렬. 변경이력(`:266` 다음)에 v3.3 행 추가.
- **완료 기준**: TS-001~006 충족 (opp 한정)
- **테스트**: TS-001~006
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 3: opdd CLOSE 스텝 삽입 + 번호 재정렬 + 변경이력
- [ ] 완료
- **소속 기능**: F-001, F-002, F-003
- **영역**: 스킬
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-pilot-data-design/SKILL.md`
- **작업 내용**: STEP 6 CLOSE(`:205-217`) 항목1↔2 사이에 §3.1.2(a) 텍스트(`{도메인 산출물}`="ARCHITECTURE.md·표준사전·ERD 등") 삽입, brain 2→3 / 완료 보고 3→4 재정렬. 변경이력(`:317` 다음)에 v1.1 행 추가.
- **완료 기준**: TS-001~006 충족 (opdd 한정)
- **테스트**: TS-001~006
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 4: opds CLOSE 스텝 삽입 + 번호 재정렬 + 변경이력
- [ ] 완료
- **소속 기능**: F-001, F-002, F-003
- **영역**: 스킬
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-pilot-dev-short/SKILL.md`
- **작업 내용**: STEP 5 CLOSE(`:174-183`) 항목1↔2 사이에 §3.1.2(a) 텍스트 삽입, brain 2→3 / 완료 보고 3→4 재정렬. 변경이력(`:364` 다음)에 v4.0 행 추가.
- **완료 기준**: TS-001~006 충족 (opds 한정)
- **테스트**: TS-001~006
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 5: opdw CLOSE 스텝 삽입 + 번호 재정렬 + 변경이력
- [ ] 완료
- **소속 기능**: F-001, F-002, F-003
- **영역**: 스킬
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-pilot-dev-wireframe/SKILL.md`
- **작업 내용**: STEP 4 CLOSE(`:148-157`) 항목1↔2 사이에 §3.1.2(a) 텍스트(`{도메인 산출물}`="ARCHITECTURE.md·기획서·와이어프레임 등") 삽입(기존 brain 항목 "PM Gate 통과 후" 문구 보존), brain 2→3 / 완료 보고 3→4 재정렬. 변경이력(`:294` 다음)에 v3.0 행 추가.
- **완료 기준**: TS-001~006 충족 (opdw 한정)
- **테스트**: TS-001~006
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 6: opgc CLOSE 단락 삽입 + 변경이력 (번호 재정렬 비해당)
- [ ] 완료
- **소속 기능**: F-001, F-003
- **영역**: 스킬
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-pilot-gc/SKILL.md`
- **작업 내용**: §4.2(`:349`)의 `**op-brain-ingest 디스패치**` 무번호 단락 **바로 앞**에 §3.1.2(b) 무번호 굵은 단락 삽입. **번호 항목 없으므로 F-002 재정렬 스킵**, 서브섹션 헤딩(### 4.1~4.3) 불변. 변경이력(`:523` 다음)에 v1.7 행(번호 재정렬 문구 제외, §3.3.2 opgc 변형) 추가.
- **완료 기준**: TS-001/002/003/005/006 충족 (opgc 한정). TS-004는 비해당.
- **테스트**: TS-001/002/003/005/006
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 7: opsdd CLOSE 스텝 삽입 + 번호 재정렬 + 변경이력
- [ ] 완료
- **소속 기능**: F-001, F-002, F-003
- **영역**: 스킬
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-pilot-sdd/SKILL.md`
- **작업 내용**: Phase 6 CLOSE(`:283-302`) 항목3(DONE.md 생성+mark)↔항목4(brain) 사이에 §3.1.2(a) 텍스트(번호 4, `{도메인 산출물}`="ARCHITECTURE.md·SPEC·기획서 등") 삽입, 기존 brain 4→5 / 완료 보고 5→6 재정렬. 삽입 위치는 `:291` G-13 인용블록 **다음**(brain 항목 직전). 변경이력(`:523` 다음)에 v3.1.1 행 추가.
- **완료 기준**: TS-001~006 충족 (opsdd 한정)
- **테스트**: TS-001~006
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 8: opwt CLOSE 스텝 삽입 + 번호 재정렬 + 변경이력
- [ ] 완료
- **소속 기능**: F-001, F-002, F-003
- **영역**: 스킬
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-pilot-write-tech/SKILL.md`
- **작업 내용**: CLOSE 단계(`:381-395`) 항목1↔2 사이에 §3.1.2(a) 텍스트 삽입, brain 2→3 / 완료 보고 3→4 재정렬. 변경이력(`:545` 다음)에 v4.4 행 추가.
- **완료 기준**: TS-001~006 충족 (opwt 한정)
- **테스트**: TS-001~006
- **실행 방법**: sub-agent
- **의존**: 없음

> **docs/ 갱신 Step 판단**: 본 태스크는 프레임워크 스킬 SSOT 수정으로, `docs/` 코드 문서(BACKEND/FRONTEND/ARCHITECTURE/CONVENTIONS) 내용에는 영향이 없다. 따라서 docs/ 갱신 Step을 추가하지 않는다. (변경 추적은 각 SKILL.md 변경이력 행 — F-003 — 으로 충족)

### 4.3 병렬/순차 판별 근거

| 관계 | 근거 |
|------|------|
| Step 1 ∥ 2 ∥ 3 ∥ 4 ∥ 5 ∥ 6 ∥ 7 ∥ 8 | 8개 독립 파일, 파일 간 상호 참조 없음 → 완전 병렬 가능 |
| 각 Step 내부 (CLOSE Edit → 변경이력 Edit) | 동일 파일 순차 (Edit 충돌 방지) |

> 단일 워커가 8 Step을 순차 처리해도 무방하나, opal-task-agent에 파일별 병렬 디스패치 시 처리량 향상. 동일 파일 2회 Edit는 한 워커 내에서 순차.

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA

| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | 8파일 CLOSE에 "관련 문서 업데이트" 스텝 존재 | TS-001 | `grep -c "관련 문서 업데이트"` ≥ 1 (8파일) |
| F-001 | 신규 스텝이 brain ingest 직전 위치 | TS-002 | 신규 스텝 줄번호 < brain ingest 줄번호 (8파일) |
| F-001 | "PROJECT.md" + "changed_files" 키워드 포함 | TS-003 | 신규 스텝 블록에 두 키워드 모두 grep 매칭 (8파일) |
| F-002 | CLOSE 번호 연속성 | TS-004 | 패턴 A·B 7파일 번호 1부터 연속 (opgc 비해당) |
| F-003 | 변경이력 행 추가 | TS-005 | `042` + `2026-06-24` 포함 행 8파일 각 1개 |

### 5.2 회귀 테스트
- [ ] git diff가 CLOSE 섹션 + 변경이력 행에만 국한되는가 (TS-006)
- [ ] STATE 행 구조(행 수)·CLOSE 진입 게이트 인용블록 불변
- [ ] brain ingest 항목 텍스트(탐색 경로·status 비중단)가 보존되었는가

### 5.3 코드/문서 품질
- [ ] 8파일 변경이력 행에 KST 일시 + 태스크 번호(042) 포함 (.opal/AGENT.md §변경이력)
- [ ] `~/.opal/` 직접 편집 없음 — `opal/skills/` 소스만 수정
- [ ] 산출물 명칭이 각 파일 brain ingest 기존 표현과 일관 (citation-rules §용어 일관성)

### 5.4 보안
- [ ] 문서 수정 태스크로 시크릿/토큰 변경 없음 (해당 없음 확인)

---

## 6. 복잡도 판별

| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 8개 | 복잡 |
| 변경 파일 수 | 8개 | 복잡 |
| 모듈 범위 | 단일(스킬 문서) 다중 파일 | 복잡 |
| 작업 유형 | 절차 텍스트 일괄 삽입 (대규모 개선) | 복잡 |
| 외부 의존성 | 없음 | 단순 |
| **실행 모드** | **복잡** | |

---

## 7. 실행 아키텍처 (복잡 모드)

### C-1. 에이전트 토폴로지

- **Batch 1 (병렬)**: opal-task-agent × 8 (파일별 1 디스패치) — Step 1~8 동시 실행. 파일 충돌 없음(서로 다른 파일).
- 자원 제약 시 단일 opal-task-agent에 8 파일 순차 처리도 허용 (각 파일 = CLOSE Edit + 변경이력 Edit).
- **Batch 2 (검증)**: opal-test-agent — TEST-SCENARIO.md 기반 grep 검증 (M1) 일괄 수행.

```
[Batch 1: 병렬]
 Step1 Step2 Step3 Step4 Step5 Step6 Step7 Step8  (opal-task-agent ×8)
        └──────────── 전원 완료 ────────────┘
[Batch 2]
 opal-test-agent (grep 검증 TS-001~006)
```

### C-2. 스킬 요구사항

- 신규 스킬 불필요. opal-task-agent가 단계 스킬 없이 인라인 지침(본 PLAN §3.1.2/§3.3.2 텍스트)으로 Edit 수행.
- 동일 패턴이 8회 반복되나, "스킬 후보"가 아닌 1회성 마이그레이션 → 인라인 지침으로 충분.

### C-3. 도구 요구사항

- Read / Edit (파일 수정), grep (검증). CLI·MCP·패키지 추가 없음.

### C-4. 테스트 전략

- **검증 도구**: opal-test-agent (mode=unit/static, grep 기반 M1).
- **기능 검증**: TS-001~006 (§3.N.5). 8파일 × {신규스텝 존재 / brain ingest 직전 위치 / PROJECT.md+changed_files 키워드}.
- **회귀**: `git diff --stat` 및 CLOSE 외 라인 무변경 확인 (TS-006).
- **실행 명령 예시**:
  - `grep -rn "관련 문서 업데이트" opal/skills/opal-pilot-*/SKILL.md` → 8 매칭
  - 파일별 `grep -n "관련 문서 업데이트\|op-brain-ingest 디스패치"` 줄번호 순서 확인 (신규 < brain)
  - `grep -rn "042" opal/skills/opal-pilot-*/SKILL.md | grep "2026-06-24"` → 8 매칭

---

## 8. 기술 컨텍스트

### 8.1 기술 스택

| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| 문서 | Markdown (SKILL.md) | op-dev-plan |
| 검증 | grep / git diff | opal-test-agent (M1) |

### 8.2 사용 MCP

| MCP | 조회 결과 요약 |
|-----|--------------|
| (없음) | 외부 라이브러리 무관 — Markdown 문서 수정 태스크 |

### 8.3 참조 문서 (설계 결정 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | opal-pilot-dev SKILL.md | `opal/skills/opal-pilot-dev/SKILL.md:230-254` | 패턴 A CLOSE 구조 기준 |
| D-2 | 소스 | opal-pilot-project SKILL.md | `opal/skills/opal-pilot-project/SKILL.md:118-135` | 패턴 A, PM Gate 문구 보존 |
| D-3 | 소스 | opal-pilot-data-design SKILL.md | `opal/skills/opal-pilot-data-design/SKILL.md:201-224` | 패턴 A, 산출물 명칭 사전·ERD |
| D-4 | 소스 | opal-pilot-dev-short SKILL.md | `opal/skills/opal-pilot-dev-short/SKILL.md:170-187` | 패턴 A |
| D-5 | 소스 | opal-pilot-dev-wireframe SKILL.md | `opal/skills/opal-pilot-dev-wireframe/SKILL.md:144-161` | 패턴 A, 와이어프레임 맥락 |
| D-6 | 소스 | opal-pilot-gc SKILL.md | `opal/skills/opal-pilot-gc/SKILL.md:324-358` | 패턴 C (무번호 서브섹션) |
| D-7 | 소스 | opal-pilot-sdd SKILL.md | `opal/skills/opal-pilot-sdd/SKILL.md:279-302` | 패턴 B (brain=항목4) |
| D-8 | 소스 | opal-pilot-write-tech SKILL.md | `opal/skills/opal-pilot-write-tech/SKILL.md:377-405` | 패턴 A |
| D-9 | 설계 | 프로젝트 AGENT.md | `.opal/AGENT.md:42,60-61` | 변경이력 의무, ~/.opal 직접편집 금지 |
| D-10 | 기획 | TASK.md | `tasks/042-260624-opds-close-문서업데이트/TASK.md` | 요구사항 F-1~F-3, 확정 설계 방향 |

> 인용 형식: `opal/core/references/harness/citation-rules.md` §3.1 참조.

---

## 9. 리스크 및 대응 (기능-리스크 연결)

| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| R-1 | 번호 재정렬 누락 → 번호 중복/건너뜀 (H-1) | F-002 | P1 | 삽입+재정렬을 단일 Edit으로 처리 (§3.2.2). TS-004로 검증 |
| R-2 | 신규 스텝이 brain ingest 뒤에 삽입되어 목표 무효화 (H-2) | F-001 | P0 | "DONE.md 생성 직후·brain 직전" 위치를 줄번호로 명시 (§3.1.1). TS-002로 줄번호 순서 검증 |
| R-3 | opgc 구조 상이로 잘못 편집 (H-4) | F-001 | P1 | Step 6에서 패턴 C 전용 텍스트(§3.1.2(b)) + 무번호 단락 삽입 명시, 재정렬 스킵 |
| R-4 | 키워드(PROJECT.md/changed_files) 누락 (H-3) | F-001 | P1 | §3.1.2 텍스트에 두 키워드 고정 포함. TS-003 검증 |
| R-5 | 변경이력 일부 파일 누락 (H-5) | F-003 | P2 | 8 Step 각각에 변경이력 Edit 포함. TS-005로 8회 매칭 검증 |
| R-6 | CLOSE 외 섹션 변경 (Surgical 위반, H-6) | F-001~003 | P1 | Edit old_string을 CLOSE/변경이력 범위로 한정. TS-006 git diff 검증 |
