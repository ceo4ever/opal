# PLAN: op-dev-plan 탑다운 기능 중심 구조 개편 + 후속 파이프라인 정합화

> 작성일: 2026-04-13 | 입력: TASK.md | 출력: PLAN.md
> 모드: Multi-Feature (본 태스크는 기능 6개로 시범 적용)

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

`op-dev-plan` 스킬의 PLAN.md 출력 구조를 파일/레이어 중심에서 **탑다운 기능 중심 구조(F-NNN 기반)**로 전면 개편하고, 중복 산출물인 `execution-plan.json`을 폐기하여 PLAN.md를 단일 SSOT로 통합한다. 개편된 PLAN 구조를 소비하는 후속 스킬(`op-dev-execute`, `op-dev-qa`, `ui-designer`)을 동일 태스크 내에서 정합화한다.

### 1.2 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-000 | 수정 전 원본 파일 백업 | R0 (횡단, 캡틴 지시로 PLAN에서 추가) | P0 | 없음 |
| F-001 | PLAN.md 기능 중심 구조 재설계 | R1 | P0 | F-000 |
| F-002 | plan-guide.md 기능 중심 단계 재설계 | R2, R4, R5 | P0 | F-001 |
| F-003 | execution-plan.json 폐기 처리 | R3 | P0 | F-001 |
| F-004 | op-dev-execute 소비자 정합화 | R6 | P0 | F-001, F-003 |
| F-005 | ui-designer plan-driven 입력 전환 | R7 | P0 | F-001, F-003 |
| F-006 | op-dev-qa 기능-QA 매핑 검증 규칙 추가 | R8 | P0 | F-001 |

> **R 매핑 검증**: R0→F-000(PLAN 추가), R1→F-001, R2→F-002, R3→F-003, R4→F-002, R5→F-002, R6→F-004, R7→F-005, R8→F-006. 모든 요구사항이 정확히 1개 F에 매핑됨.
>
> **R0 정의** (PLAN에서 추가된 횡단 요구사항): 본 태스크에서 수정하는 모든 원본 파일(8개)을 수정 전에 태스크 폴더 `backup/` 하위로 원본 경로 구조를 유지하여 복사한다. 목적은 롤백 안전성 확보.

### 1.3 기능 의존 그래프

```
F-000 ─ F-001 ─┬─ F-002 (R2+R4+R5: 가이드+파싱규칙+Flat/Multi)
               ├─ F-003 ─┬─ F-004 (R6: execute 정합화)
               │         └─ F-005 (R7: ui-designer 정합화)
               └─ F-006 (R8: qa 정합화)
```

---

## 2. 기능별 분석

### F-000: 수정 전 원본 파일 백업

#### 2.0.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 백업 | `tasks/114-260413-opp-op-dev-plan-feature-driven-redesign/backup/` | 수정 전 원본 보관 디렉토리 | 신규 생성 |
| 백업 | `backup/opal/skills/op-dev-plan/SKILL.md` | 원본 복사본 | 신규 생성 |
| 백업 | `backup/opal/skills/op-dev-plan/references/plan-guide.md` | 원본 복사본 | 신규 생성 |
| 백업 | `backup/opal/skills/op-dev-execute/SKILL.md` | 원본 복사본 | 신규 생성 |
| 백업 | `backup/opal/skills/op-dev-execute/references/execute-guide.md` | 원본 복사본 | 신규 생성 |
| 백업 | `backup/opal/skills/op-dev-qa/SKILL.md` | 원본 복사본 | 신규 생성 |
| 백업 | `backup/opal/skills/op-dev-qa/references/qa-dev-guide.md` | 원본 복사본 | 신규 생성 |
| 백업 | `backup/skills/ui-designer/SKILL.md` | 원본 복사본 | 신규 생성 |
| 백업 | `backup/skills/ui-designer/modes/plan-driven.md` | 원본 복사본 | 신규 생성 |
| 문서 | `backup/MANIFEST.md` | 백업 파일 매니페스트(원본 경로↔백업 경로 매핑 + 백업 시점) | 신규 생성 |

#### 2.0.2 현재 구현

백업 메커니즘 없음. 모든 수정은 소스 파일 직접 Edit으로 이뤄진다. 롤백은 git revert로만 가능.

#### 2.0.3 영향 범위

- F-001~F-006의 모든 수정 Step에 선행해야 한다 (의존).
- 기존 디렉토리 구조에 영향 없음 (태스크 폴더 내부에 backup/만 추가).
- git에는 backup/도 포함된다 (확정 기준 #3: docs/backup과 같은 정책 — 백업 파일은 중요 자산).

---

### F-001: PLAN.md 기능 중심 구조 재설계

#### 2.1.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 스킬 | `opal/skills/op-dev-plan/SKILL.md` | PLAN 단계 스킬 정의 + PLAN.md 출력 형식 + execution-plan.json 스키마 | 수정 |

> 영역 라벨: 본 태스크는 프레임워크 문서 개편이므로 **스킬 / 가이드 / 오케스트레이터 / 에이전트 / 문서 / 환경 / 배치** 축을 사용한다. 일반 개발 태스크에서는 **FE / BE / DB / 환경 / 배치 / 공통**을 사용한다.

#### 2.1.2 현재 구현

`op-dev-plan/SKILL.md` (현재 구조):
- **PLAN.md 출력 형식**: §1 코드 분석 → §2 구현 계획 → §3 실행 체크리스트 → §4 QA 체크리스트 → §5 복잡도 판별 → §6 실행 아키텍처 → §7 기술 컨텍스트 → §8 리스크. **기능 단위 그룹핑이 전혀 없음.**
- **프로세스**: Step 1 가이드 로딩 → Step 2 기술 컨텍스트 → Step 3 코드 분석(ANALYSIS 분기) → Step 4 구현 계획(1~5단계) → Step 5 복잡도 판별 → Step 6 실행 아키텍처 → Step 7 execution-plan.json → Step 8 PLAN.md 작성 → Step 9 결과 반환.
- **입력 분기**: ANALYSIS.md 유무에 따라 코드 분석 깊이만 조절. 기능 식별 단계 없음.
- **영역 태그**: `[FE]`/`[BE]`/`[공통]` 3개만 존재. 환경/배치/DB가 1급 시민이 아님.
- **execution-plan.json 스키마**: SKILL.md 하단에 JSON 스키마 전문이 포함됨 (L241~L303). frontend.screens(기능 단위) vs backend.layers(레이어 단위) 비대칭.
- **품질 체크리스트**: 기능-QA 매핑 없음. 파일 중심 검증만.

#### 2.1.3 영향 범위

- F-001 변경은 F-002~F-006 모두의 전제 조건이다.
- `opal-pilot-dev`/`opal-pilot-dev-short` 오케스트레이터가 이 스킬을 디스패치하므로, 출력 형식 변경이 후속 소비자 전부에 영향.
- **하위호환**: 기존 태스크 산출물(과거 PLAN.md)은 이미 완료된 것이므로 직접 영향 없음. 단, op-dev-execute의 입력 우선순위가 바뀌므로 F-004에서 처리.

---

### F-002: plan-guide.md 기능 중심 단계 재설계

#### 2.2.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 가이드 | `opal/skills/op-dev-plan/references/plan-guide.md` | PLAN 단계 상세 가이드 (0~6단계 + 실행 체크리스트 + 복잡도 + QA) | 수정 |

#### 2.2.2 현재 구현

`plan-guide.md` (현재 구조):
- **0단계**: 기술 컨텍스트 로딩 (스킬/MCP 매칭) — 유지 대상.
- **입력 기반 분기**: ANALYSIS.md 유무에 따른 코드 분석 — 기능 식별 없음.
- **1단계**: 구현 범위 확정 (파일 변경 계획 — 신규/수정/영향 확인). **파일 단위.**
- **2단계**: 구현 순서 결정 — 하위 레이어부터. 영역 태그 `[FE]`/`[BE]`/`[공통]` 3개.
- **3단계**: 핵심 설계 명세 — 클래스/함수 시그니처, 데이터 모델, FE 화면 설계. **기능 루프 아님.**
- **4단계**: 의존성 및 환경 변경.
- **5단계**: 테스트 전략.
- **6단계**: execution-plan.json 생성 (FE/BE 시) — **폐기 대상 (R3).**
- **실행 체크리스트 작성**: 분해 규칙(1파일=1작업), Step 형식, Phase 그룹핑.
- **복잡도 판별**: 5기준 테이블.
- **실행 아키텍처**: C-1~C-4.
- **QA 체크리스트 작성**: 기능/회귀/코드품질/보안 — 기능-QA 매핑 없음.

**R4 관련** (파싱 규칙): 현재 후속 소비자가 PLAN.md를 파싱하는 규칙이 명시적으로 정의된 곳이 없다. execute-guide.md는 "PLAN.md 섹션 3 실행 체크리스트"라고만 언급하고, 섹션 앵커/테이블 컬럼/F-ID 포맷 같은 형식 계약은 없다.

**R5 관련** (Flat/Multi): 현재 기능 개수에 따른 모드 구분이 없다. 항상 동일 구조.

#### 2.2.3 영향 범위

- plan-guide.md는 op-dev-plan 워커가 Step 1에서 Read하는 유일한 가이드 파일. 변경 시 모든 향후 PLAN 작성에 즉시 영향.
- R4의 파싱 규칙 신설은 F-004(execute), F-005(ui-designer)의 구현 전제.
- R5의 Flat/Multi 판정은 SKILL.md에도 반영 필요 (F-001과 동시 변경이지만 같은 Phase에 넣지 않음 — 같은 파일을 수정하지 않으므로 병렬 가능).

---

### F-003: execution-plan.json 폐기 처리

#### 2.3.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 스킬 | `opal/skills/op-dev-plan/SKILL.md` | Step 7 (json 생성), 스키마 섹션, 입출력 테이블 | 수정 |
| 가이드 | `opal/skills/op-dev-plan/references/plan-guide.md` | 6단계 (json 생성) | 수정 |

#### 2.3.2 현재 구현

- **SKILL.md**:
  - frontmatter `description`: "보장 출력: PLAN.md (실행 체크리스트+복잡도 판별 포함), execution-plan.json (FE/BE 시)" — json 산출물 명시.
  - 입출력 테이블: "조건부 출력 | execution-plan.json (FE/BE 작업 포함 시)".
  - Step 7: "execution-plan.json 생성 (FE/BE 작업 시)".
  - "execution-plan.json 스키마" 섹션 (L241~L303): 전체 JSON 스키마 포함.
  - "참조: execution-plan.json" 경로 표기 (PLAN.md 출력 형식 마지막).
  - 품질 체크리스트: "FE/BE 작업 시 execution-plan.json을 생성했는가?".
- **plan-guide.md**:
  - 6단계: "execution-plan.json 생성 (FE/BE 작업 시)" 전체 섹션 (L158~L176).
  - 품질 체크리스트: "FE/BE 작업 시 execution-plan.json을 생성했는가?".

#### 2.3.3 영향 범위

- **op-dev-execute**: 현재 입력 우선순위가 "1. execution-plan.json (있으면) → 2. PLAN.md 섹션 3" (SKILL.md L52, execute-guide.md L56~L57). json 폐기 시 이 우선순위를 전면 변경해야 함 → F-004.
- **ui-designer plan-driven**: 현재 입력이 "execution-plan.json screen 객체" (SKILL.md L6, modes/plan-driven.md 전체). json 폐기 시 입력 소스를 PLAN.md로 전환해야 함 → F-005.
- **기존 json 파일**: 과거 태스크에 생성된 `execution-plan.json` 파일은 수정/삭제하지 않음 (하위호환). 단, execute가 향후 이를 참조하지 않도록 폴백 서술 필요.

---

### F-004: op-dev-execute 소비자 정합화

#### 2.4.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 스킬 | `opal/skills/op-dev-execute/SKILL.md` | EXECUTE 단계 스킬 정의 — 입력 우선순위, json 기반 실행, FE 역할 분담 | 수정 |
| 가이드 | `opal/skills/op-dev-execute/references/execute-guide.md` | EXECUTE 상세 가이드 — json 기반 실행 섹션, 입력 우선순위 | 수정 |

#### 2.4.2 현재 구현

**SKILL.md** (op-dev-execute):
- frontmatter `description`: "선택 입력: execution-plan.json".
- 입력: `checklist_source` — "PLAN.md 섹션 3 실행 체크리스트 (또는 execution-plan.json)".
- Step 2 체크리스트 확인: 입력 우선순위 "1. execution-plan.json → 2. PLAN.md 섹션 3".
- "execution-plan.json 기반 실행" 섹션 (L183~L194): phase별 실행, FE screen → ui-designer 전달 규칙.
- FE 역할 분담: "호출 방법: execution-plan.json의 FE screen 항목을 ui-designer plan-driven 모드로 전달".
- 가드레일: "PLAN/execution-plan.json에 없는 파일 생성/수정" 금지.
- 품질 체크리스트: "PLAN/execution-plan.json에 없는 파일을 생성/수정하지 않았는가".

**execute-guide.md**:
- 금지 행동: "PLAN/execution-plan.json에 없는 파일 생성/수정".
- "execution-plan.json 기반 실행" 섹션 (L51~L66): 입력 우선순위 1위 json, FE screen → ui-designer plan-driven, BE layer 순서.
- 품질 체크리스트: 동일한 json 참조.

#### 2.4.3 영향 범위

- execute 스킬은 `opal-pilot-dev`, `opal-pilot-dev-short`, `opal-pilot-dev-wireframe` 3개 오케스트레이터에서 사용.
- json 의존성 제거 시 execute의 **FE 실행 순서**(비UI → ui-designer → 통합) 패턴 자체는 유지해야 하며, 입력 소스만 PLAN.md §3(기능 루프 기반 실행 체크리스트)로 전환.
- **폴백**: PLAN.md에 §2·§3 기능 섹션이 없는 과거 태스크 대응. 기존 PLAN.md 형식(§1~§8)도 읽을 수 있도록 폴백 규칙 서술 필요.
- `checkpoint-guide.md`(execute references)는 json을 직접 참조하지 않으므로 변경 불필요.

---

### F-005: ui-designer plan-driven 입력 전환

#### 2.5.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 스킬 | `skills/ui-designer/SKILL.md` | UI 구현 스킬 — 모드 판별, 입력 스키마 | 수정 |
| 가이드 | `skills/ui-designer/modes/plan-driven.md` | plan-driven 모드 프로세스 — json screen 입력 | 수정 |

#### 2.5.2 현재 구현

**SKILL.md** (ui-designer):
- frontmatter `description`: "2. plan-driven 모드: execution-plan.json의 screen 객체를 입력으로 받아 기존 프로젝트에 화면을 추가/수정".
- 모드 판별 테이블: plan-driven 입력 = "execution-plan.json screen 객체".
- 판별 규칙: "opal-pilot EXECUTE에서 호출 → plan-driven 모드".

**modes/plan-driven.md**:
- 입력: "execution-plan.json의 screen 객체 1개" + 필드 테이블 (id, name, type, action, route, files, shadcn_components, ui_work, api_work).
- 실행 프로세스: screen 객체 기반 Step 1~4.
- 전체가 json screen 입력 전제로 작성됨.

#### 2.5.3 영향 범위

- ui-designer는 `opal/skills/`가 아닌 `skills/` (독립 스킬 소스)에 위치. 프로젝트 간 재사용 가능한 스킬.
- plan-driven 모드의 입력을 PLAN.md §3.N.2(FE 화면 설계) 섹션으로 전환해야 함.
- scaffold 모드는 wireframe.md 기반이므로 영향 없음.
- **입력 필드 매핑**: json screen 객체의 필드(id, name, type, action, route, files, shadcn_components, ui_work, api_work)가 PLAN.md의 FE 화면 설계 섹션에서 어떻게 표현되는지 명세해야 함 — F-002의 파싱 규칙과 연동.

---

### F-006: op-dev-qa 기능-QA 매핑 검증 규칙 추가

#### 2.6.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 스킬 | `opal/skills/op-dev-qa/SKILL.md` | QA 검증 스킬 정의 — 검증 기준 | 수정 |
| 가이드 | `opal/skills/op-dev-qa/references/qa-dev-guide.md` | Dev QA 가이드 — PLAN 검증 기준 P-1~P-6, SP-1~SP-5 | 수정 |

#### 2.6.2 현재 구현

**SKILL.md** (op-dev-qa):
- PLAN (Full) 검증 ID: P-1~P-6 (구현 가능성, 의존성 순서, ANALYSIS 반영, 파일 일치, 설계 구체성, 테스트 전략). **기능-QA 매핑 검증 없음.**
- PLAN (Short) 검증 ID: SP-1~SP-5. 마찬가지로 기능-QA 매핑 없음.

**qa-dev-guide.md**:
- PLAN (Full) 검증 기준 테이블: P-1~P-6. 기능 커버리지 항목 없음.
- PLAN (Short) 검증 기준 테이블: SP-1~SP-5. 동일하게 없음.

#### 2.6.3 영향 범위

- QA 스킬에 검증 규칙 추가는 다른 스킬과 직접 충돌 없음.
- 단, 새 규칙("모든 F-NNN이 §5 QA 체크리스트에서 최소 1개 항목 커버")은 PLAN.md가 기능 중심 구조(F-001)여야 의미가 있으므로 F-001 의존.
- Flat 모드(기능 1개)에서는 F-NNN이 없으므로, "Multi-Feature 모드에서만 적용" 조건 필요.

---

## 3. 기능별 설계

### F-000: 수정 전 원본 파일 백업

#### 3.0.1 파일 변경 계획

**신규 생성**

| # | 경로 | 영역 | 역할 |
|---|------|------|------|
| 1 | `tasks/114-260413-opp-op-dev-plan-feature-driven-redesign/backup/` | 백업 | 백업 루트 디렉토리 |
| 2 | `backup/opal/skills/op-dev-plan/SKILL.md` | 백업 | 원본 복사본 |
| 3 | `backup/opal/skills/op-dev-plan/references/plan-guide.md` | 백업 | 원본 복사본 |
| 4 | `backup/opal/skills/op-dev-execute/SKILL.md` | 백업 | 원본 복사본 |
| 5 | `backup/opal/skills/op-dev-execute/references/execute-guide.md` | 백업 | 원본 복사본 |
| 6 | `backup/opal/skills/op-dev-qa/SKILL.md` | 백업 | 원본 복사본 |
| 7 | `backup/opal/skills/op-dev-qa/references/qa-dev-guide.md` | 백업 | 원본 복사본 |
| 8 | `backup/skills/ui-designer/SKILL.md` | 백업 | 원본 복사본 |
| 9 | `backup/skills/ui-designer/modes/plan-driven.md` | 백업 | 원본 복사본 |
| 10 | `backup/MANIFEST.md` | 문서 | 백업 매니페스트 |

**수정**

| # | 경로 | 영역 | 변경 내용 요약 |
|---|------|------|--------------|
| (없음) | | | |

#### 3.0.2 구조/인터페이스 설계

**백업 경로 규칙**:
- 원본 경로 구조를 그대로 유지하여 `backup/` 하위에 복사
  - 예: `opal/skills/op-dev-plan/SKILL.md` → `backup/opal/skills/op-dev-plan/SKILL.md`
  - 예: `skills/ui-designer/SKILL.md` → `backup/skills/ui-designer/SKILL.md`
- 이유: 복원 시 `cp -R backup/* ./` 한 줄로 원복 가능

**MANIFEST.md 포맷**:

```markdown
# backup MANIFEST

> 백업 시점: {YYYY-MM-DD HH:mm KST}
> 태스크: 114-op-dev-plan 탑다운 기능 중심 구조 개편
> 목적: 수정 전 원본 보관 (롤백 안전성)

## 백업 파일 목록

| # | 원본 경로 | 백업 경로 | 크기(bytes) |
|---|----------|----------|-----------|

## 복원 방법

```bash
# 태스크 루트에서 실행
cp -R backup/opal /Volumes/Data/AiStudio/workspace/opal/
cp -R backup/skills /Volumes/Data/AiStudio/workspace/opal/
```

## 변경이력

| 일시 | 변경내용 |
|------|---------|
```

#### 3.0.3 환경 변경

해당 없음.

#### 3.0.4 배치/마이그레이션

해당 없음. 단순 파일 복사.

#### 3.0.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-016 | R0 | 파일 존재 검사 | `backup/` 하위에 8개 원본 파일이 원본 경로 구조 그대로 존재 |
| TS-017 | R0 | 내용 일치 검사 | 각 백업 파일의 바이트 크기/해시가 원본과 일치 (Step 1 실행 시점 기준) |
| TS-018 | R0 | 매니페스트 검사 | `backup/MANIFEST.md`가 존재하고 8개 파일 매핑 테이블을 포함 |

---

### F-001: PLAN.md 기능 중심 구조 재설계

#### 3.1.1 파일 변경 계획

**신규 생성**

| # | 경로 | 영역 | 역할 |
|---|------|------|------|
| (없음) | | | |

**수정**

| # | 경로 | 영역 | 변경 내용 요약 |
|---|------|------|--------------|
| 1 | `opal/skills/op-dev-plan/SKILL.md` | 스킬 | PLAN.md 출력 형식을 기능 중심 §1~§8(또는 동등) 구조로 교체; 프로세스를 기능 식별→기능별 분석→기능별 설계→통합 실행 계획 순으로 재정렬; frontmatter description 갱신; 영역 태그 6개로 확장; 품질 체크리스트 갱신 |

#### 3.1.2 구조/인터페이스 설계

**새 PLAN.md 출력 형식 (SKILL.md에 명시할 골격)**:

```
§1. 태스크 개요 + 기능 리스트업
  1.1 요약
  1.2 기능 목록 (F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존)
  1.3 기능 의존 그래프 (ASCII)
§2. 기능별 분석 (F-NNN 하위 섹션 반복)
  2.N.1 관련 파일 맵 (영역 | 경로 | 역할 | 변경유형) — 6영역: FE/BE/DB/환경/배치/공통
  2.N.2 현재 구현
  2.N.3 영향 범위
§3. 기능별 설계 (F-NNN 하위 섹션 반복)
  3.N.1 파일 변경 계획 (신규/수정)
  3.N.2 API·데이터 모델·화면 설계
  3.N.3 환경 변경
  3.N.4 배치/마이그레이션
  3.N.5 테스트 시나리오 (TS-ID | AC 매핑 | 유형 | 기대결과)
§4. 통합 실행 계획
  4.1 Phase 그룹핑 (기능 의존 기반)
  4.2 실행 체크리스트 (기능-Step 매핑, 소속 F-ID 필수)
  4.3 병렬/순차 판별 근거
§5. QA 체크리스트 (기능-QA 매트릭스)
  5.1 기능별 QA (F-ID | QA 항목 | TS-ID | Pass 조건)
  5.2 회귀 테스트
  5.3 코드/문서 품질
  5.4 보안
§6. 복잡도 판별
§7. 실행 아키텍처 (복잡 모드 시)
§8. 기술 컨텍스트
§9. 리스크 및 대응 (기능-리스크 연결)
```

**새 프로세스 순서 (SKILL.md의 Step 재정렬)**:

| Step | 작업 | 기존 대응 |
|------|------|----------|
| 1 | 가이드 로딩 | 기존 Step 1 유지 |
| 2 | 기술 컨텍스트 로딩 | 기존 Step 2 유지 |
| 3 | 기능 식별 | **신설** — TASK.md 요구사항을 F-NNN으로 그룹핑 |
| 4 | 기능별 분석 (코드 분석 통합) | 기존 Step 3 재배치 — 기능 루프 안으로 |
| 5 | 기능별 설계 (구현 계획 통합) | 기존 Step 4 재배치 — 기능 루프 안으로 |
| 6 | 통합 실행 계획 | 기존 Step 4 일부 + Phase 그룹핑 |
| 7 | 복잡도 판별 | 기존 Step 5 유지 |
| 8 | 실행 아키텍처 (복잡 모드) | 기존 Step 6 유지 |
| 9 | PLAN.md 작성 | 기존 Step 8 유지 |
| 10 | 결과 반환 | 기존 Step 9 유지 |

**영역 태그 확장**: `[FE]`/`[BE]`/`[공통]` → `FE`/`BE`/`DB`/`환경`/`배치`/`공통` (6영역). 태그를 관련 파일 맵의 "영역" 컬럼에 사용. 기존 `[FE]`/`[BE]`/`[공통]` 표기의 대괄호는 제거하여 테이블 컬럼 값으로 통일.

**ANALYSIS.md 입력 분기 유지**: 기능 식별(Step 3) 후 기능별 분석(Step 4)에서 ANALYSIS.md 유무에 따라 분석 깊이 조절. 기존 동작과 호환.

#### 3.1.3 환경 변경

해당 없음.

#### 3.1.4 배치/마이그레이션

해당 없음. SKILL.md 변경은 소스에만 적용. 배포는 캡틴이 install-mac.sh로 별도 수행.

#### 3.1.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 (TASK.md의 R) | 유형 | 기대 결과 |
|-------|---------------------|------|----------|
| TS-001 | R1 AC | 산출물 검사 | SKILL.md의 PLAN.md 출력 형식이 §1~§9 구조이며, §2·§3가 "### F-NNN: {이름}" 하위 섹션 반복 구조임이 명시됨 |
| TS-002 | R1 AC | 용어 검사 | "기능 리스트업", "기능별 분석", "기능별 설계", "기능-QA 매트릭스" 용어가 SKILL.md에 등장 |
| TS-003 | R1 AC | 프로세스 검사 | SKILL.md 프로세스에 "기능 식별" Step이 존재하고, 기능 루프 기반으로 분석→설계가 진행됨이 명시됨 |

---

### F-002: plan-guide.md 기능 중심 단계 재설계

#### 3.2.1 파일 변경 계획

**신규 생성**

| # | 경로 | 영역 | 역할 |
|---|------|------|------|
| (없음) | | | |

**수정**

| # | 경로 | 영역 | 변경 내용 요약 |
|---|------|------|--------------|
| 1 | `opal/skills/op-dev-plan/references/plan-guide.md` | 가이드 | 0단계 유지; "1단계: 기능 식별" 신설; 기존 1~5단계를 기능 루프 안으로 재배치; 6단계(json 생성) 제거(F-003); "PLAN.md 파싱 규칙" 섹션 신설(R4); Flat/Multi 모드 판정 규칙 추가(R5); 실행 체크리스트·복잡도·실행 아키텍처·QA 섹션을 기능 중심 용어로 갱신 |

#### 3.2.2 구조/인터페이스 설계

**plan-guide.md 새 단계 구조**:

```
0단계: 기술 컨텍스트 로딩 (유지)
1단계: 기능 식별 (신설)
  - TASK.md 요구사항을 F-NNN으로 그룹핑
  - F-ID 포맷: F-{NNN} (3자리 zero-padded)
  - 기능 목록 테이블 작성 (F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존)
  - 기능 의존 그래프 작성
  - Flat/Multi 모드 판정 (D3 규칙)
2단계: 기능별 분석 (기능 루프)
  - F-NNN별 관련 파일 맵 (6영역 분류)
  - F-NNN별 현재 구현 (ANALYSIS.md 유무에 따른 분석 깊이 조절)
  - F-NNN별 영향 범위
3단계: 기능별 설계 (기능 루프)
  - F-NNN별 파일 변경 계획 (신규/수정, 6영역)
  - F-NNN별 API·데이터 모델·화면 설계
  - F-NNN별 환경 변경
  - F-NNN별 배치/마이그레이션
  - F-NNN별 테스트 시나리오 (TS-ID | AC 매핑 | 유형 | 기대결과)
4단계: 통합 실행 계획 (기능 의존 기반)
  - Phase 그룹핑
  - 실행 체크리스트 (Step별 소속 F-ID 명시)
  - 병렬/순차 판별
5단계: 복잡도 판별 (기존 유지)
6단계: 실행 아키텍처 (복잡 모드, 기존 유지)
```

**Flat/Multi 모드 판정 테이블 (R5)**:

| 조건 | 모드 | 동작 |
|------|------|------|
| 기능 >= 2개 | **Multi-Feature** | F-NNN 하위 섹션 전개 (§2·§3 반복) |
| 기능 = 1개 | **Flat** | §2·§3의 F 하위 섹션 생략, 평면 구조. §1.2 기능 목록에 단일 행만 표기. §4 실행 체크리스트에서 소속 F-ID 생략 가능 |
| ANALYSIS.md에 `features[]` 명시 | Multi 강제 | 상류 결과 존중 |

**Flat 모드 PLAN.md 구조 (예시)**:
- §1.2 기능 목록: 단일 행 (F-001)
- §1.3 의존 그래프: 생략
- §2: 관련 파일 맵 / 현재 구현 / 영향 범위 (F 하위 구조 없이 평면)
- §3: 파일 변경 계획 / 설계 / 환경 / 배치 / 테스트 시나리오 (평면)
- §4 이후: 동일

**PLAN.md 파싱 규칙 (R4)** — plan-guide.md에 신설할 섹션:

| 요소 | 포맷 | 파싱 방법 |
|------|------|----------|
| F-ID | `F-{NNN}` (3자리 zero-padded) | 정규식 `F-\d{3}` |
| 기능 섹션 앵커 | `### F-NNN: {이름}` (H3 레벨) | H3 헤딩에서 `F-\d{3}:` 매칭 |
| 기능 목록 테이블 | §1.2의 `\| F-ID \| 기능명 \| ...` | §1.2 하위 첫 번째 테이블 파싱 |
| 관련 파일 맵 컬럼 | `영역 \| 경로 \| 역할 \| 변경유형` | §2.N.1 하위 테이블 |
| 테스트 시나리오 컬럼 | `TS-ID \| AC 매핑 \| 유형 \| 기대결과` | §3.N.5 하위 테이블 |
| 실행 체크리스트 Step | `#### Step N: {제목}` + `**소속 기능**: F-NNN` | §4.2 하위 H4 파싱 |
| QA 매트릭스 | `F-ID \| QA 항목 \| TS-ID \| Pass 조건` | §5.1 하위 테이블 |
| FE 화면 설계 (ui-designer 입력) | §3.N.2 내 "화면 유형", "경로", "shadcn 컴포넌트", "action" 등 | 구조화된 서브섹션으로 파싱 |

**FE 화면 설계 서브섹션 포맷** (§3.N.2 내 FE 화면 기재 시):

```markdown
##### 화면: {화면명}
- **ID**: FE-{N}
- **유형**: {dashboard | crud | form | auth | detail | settings | report | monitor}
- **action**: {new | modify}
- **경로**: {route}
- **파일**: {파일 경로 목록}
- **shadcn 컴포넌트**: {컴포넌트 목록}
- **UI 작업**: {설명 + 생성/수정 컴포넌트}
- **API 연동**: {엔드포인트 + 설명}
```

이 포맷은 기존 `execution-plan.json`의 screen 객체 필드와 1:1 대응하여 ui-designer가 직접 파싱할 수 있다.

#### 3.2.3 환경 변경

해당 없음.

#### 3.2.4 배치/마이그레이션

해당 없음.

#### 3.2.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-004 | R2 AC | 산출물 검사 | 가이드에 "기능 식별" 단계가 신설됨. 파일 변경 계획·구현 순서·핵심 설계·테스트 전략이 기능 루프 안에서 정의됨. 6영역 분류 축이 명시됨 |
| TS-005 | R4 AC | 산출물 검사 | "PLAN.md 파싱 규칙" 섹션이 존재하며 F-ID 포맷, 기능 섹션 앵커, 파일 맵 테이블 컬럼, 테스트 시나리오 테이블 컬럼이 규칙으로 정의됨 |
| TS-006 | R5 AC | 산출물 검사 | Flat/Multi 판정 조건 테이블이 존재하며, Flat 모드에서 F-NNN 섹션 생략한 평면 구조가 예시로 제시됨 |

---

### F-003: execution-plan.json 폐기 처리

#### 3.3.1 파일 변경 계획

**신규 생성**

| # | 경로 | 영역 | 역할 |
|---|------|------|------|
| (없음) | | | |

**수정**

| # | 경로 | 영역 | 변경 내용 요약 |
|---|------|------|--------------|
| 1 | `opal/skills/op-dev-plan/SKILL.md` | 스킬 | Step 7(json 생성) 제거; json 스키마 섹션 제거; frontmatter description에서 json 산출물 제거; 입출력 테이블에서 조건부 출력 제거; PLAN.md 출력 형식 마지막의 json 참조 제거; "Deprecated" 고지 추가; 품질 체크리스트에서 json 관련 항목 교체 |
| 2 | `opal/skills/op-dev-plan/references/plan-guide.md` | 가이드 | 6단계(json 생성) 전체 섹션 제거; 품질 체크리스트에서 json 관련 항목 교체; "Deprecated" 고지 추가 |

> 주의: SKILL.md와 plan-guide.md는 F-001, F-002에서도 수정 대상. F-003의 json 폐기 변경은 F-001/F-002의 구조 개편과 동시에 적용된다(같은 파일이므로 같은 Step에서 처리).

#### 3.3.2 구조/인터페이스 설계

**SKILL.md 변경 상세**:
- frontmatter `description`: "보장 출력: PLAN.md" (json 제거).
- 입출력 테이블: 조건부 출력 행 삭제.
- Step 7 제거 (번호 재조정은 F-001 프로세스 재정렬에서 통합 처리).
- json 스키마 섹션 (L241~L303) → "Deprecated — execution-plan.json" 고지로 교체:
  ```
  ## Deprecated: execution-plan.json

  > v2.0부터 execution-plan.json을 더 이상 생성하지 않는다.
  > PLAN.md §2·§3의 구조화된 기능별 설계가 단일 SSOT로 대체한다.
  > 기존에 생성된 execution-plan.json 파일은 삭제하지 않으며 하위호환을 보존한다.
  ```
- 품질 체크리스트: "FE/BE 작업 시 execution-plan.json을 생성했는가?" → 제거.

**plan-guide.md 변경 상세**:
- 6단계 전체 섹션 (L158~L176) 제거.
- 품질 체크리스트: 동일 항목 제거.
- Deprecated 고지를 "참고" 섹션으로 간략 추가.

#### 3.3.3 환경 변경

해당 없음.

#### 3.3.4 배치/마이그레이션

- **기존 execution-plan.json 파일**: 과거 태스크 폴더에 존재하는 json 파일은 수정/삭제하지 않는다.
- **op-dev-execute 폴백** (F-004에서 처리): execute가 과거 태스크의 json을 만나더라도 여전히 참조할 수 있도록 폴백 규칙 서술. 단, 새 PLAN.md가 있으면 PLAN.md를 우선.

#### 3.3.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-007 | R3 AC | 산출물 검사 | SKILL.md와 plan-guide.md에 "execution-plan.json을 생성하라"는 지시가 없음 |
| TS-008 | R3 AC | 산출물 검사 | 두 파일에 기존 json의 하위호환 보존 고지가 존재 |
| TS-009 | R3 AC (회귀) | 파일 존재 확인 | 과거 태스크 폴더의 execution-plan.json 파일이 삭제/수정되지 않음 |

---

### F-004: op-dev-execute 소비자 정합화

#### 3.4.1 파일 변경 계획

**신규 생성**

| # | 경로 | 영역 | 역할 |
|---|------|------|------|
| (없음) | | | |

**수정**

| # | 경로 | 영역 | 변경 내용 요약 |
|---|------|------|--------------|
| 1 | `opal/skills/op-dev-execute/SKILL.md` | 스킬 | 입력 우선순위를 "PLAN.md §4 실행 체크리스트 (1순위)" + "기존 execution-plan.json (폴백)"로 전환; json 기반 실행 섹션을 PLAN.md 기능 루프 기반으로 재작성; FE 역할 분담의 ui-designer 호출 방법을 PLAN.md §3.N.2 참조로 변경; 가드레일·품질 체크리스트에서 json 참조를 PLAN.md로 통일 |
| 2 | `opal/skills/op-dev-execute/references/execute-guide.md` | 가이드 | 입력 우선순위 변경; json 기반 실행 섹션을 PLAN.md 기반으로 재작성; 금지 행동·품질 체크리스트에서 json 참조를 PLAN.md로 통일 |

#### 3.4.2 구조/인터페이스 설계

**입력 우선순위 전환**:

```
현재:
  1. execution-plan.json (있으면) → FE/BE 구조화된 실행 순서
  2. PLAN.md 섹션 3 실행 체크리스트

변경 후:
  1. PLAN.md §4 실행 체크리스트 (기능-Step 매핑 포함) → 기능 루프 기반 실행
  2. 폴백: 기존 형식 PLAN.md §3 실행 체크리스트 (과거 태스크 호환)
  3. 폴백: execution-plan.json (과거 태스크에 json만 있는 경우)
```

**PLAN.md 기반 FE 실행 순서**:

```
op-dev-execute:
  1. PLAN.md §4 실행 체크리스트에서 Step을 Phase 순서대로 실행
  2. FE Step 중 ui-designer가 필요한 화면 → PLAN.md §3.N.2 FE 화면 설계 섹션을 Read하여 ui-designer plan-driven 모드 입력으로 전달
  3. BE Step: PLAN.md §4 체크리스트의 의존 순서대로 실행
  4. 통합: Step 완료 후 QA 체크리스트 검증
```

**가드레일 변경**: "PLAN/execution-plan.json에 없는 파일 생성/수정" → "PLAN.md에 없는 파일 생성/수정".

**폴백 규칙 서술** (SKILL.md와 execute-guide.md 모두):
```
PLAN.md에 §2·§3 기능별 섹션이 없는 경우 (과거 태스크):
  - §3(기존 형식) 실행 체크리스트가 있으면 그대로 실행
  - execution-plan.json이 있으면 기존 json 기반 실행 로직 적용
  - 둘 다 없으면 블로커 보고
```

#### 3.4.3 환경 변경

해당 없음.

#### 3.4.4 배치/마이그레이션

해당 없음. 코드 변경이 아닌 문서 변경.

#### 3.4.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-010 | R6 AC | 산출물 검사 | SKILL.md에 "PLAN.md §2·§3 입력", "기능 루프 실행", "execution-plan.json 사용 안 함" 지시가 명시됨 |
| TS-011 | R6 AC | 폴백 검사 | execute 스킬에 과거 태스크(기존 형식 PLAN.md 또는 json)에 대한 폴백 규칙이 명시됨 |

---

### F-005: ui-designer plan-driven 입력 전환

#### 3.5.1 파일 변경 계획

**신규 생성**

| # | 경로 | 영역 | 역할 |
|---|------|------|------|
| (없음) | | | |

**수정**

| # | 경로 | 영역 | 변경 내용 요약 |
|---|------|------|--------------|
| 1 | `skills/ui-designer/SKILL.md` | 스킬 | frontmatter description에서 json 참조를 PLAN.md로 변경; 모드 판별 테이블의 plan-driven 입력을 "PLAN.md §3.N.2 FE 화면 설계"로 변경 |
| 2 | `skills/ui-designer/modes/plan-driven.md` | 가이드 | 입력 소스를 json screen 객체에서 PLAN.md §3.N.2 FE 화면 설계 섹션으로 전환; 입력 필드 테이블을 md 기반 파싱 규칙으로 교체; 실행 프로세스를 PLAN.md Read 기반으로 재작성; 폴백으로 기존 json screen 지원 |

#### 3.5.2 구조/인터페이스 설계

**SKILL.md 변경**:
- frontmatter `description`: "2. plan-driven 모드: PLAN.md의 FE 화면 설계 섹션을 입력으로 받아 기존 프로젝트에 화면을 추가/수정" (json 참조 제거).
- 모드 판별 테이블: plan-driven 입력 = "PLAN.md §3.N.2 FE 화면 설계".

**plan-driven.md 입력 전환**:

```
현재: execution-plan.json의 screen 객체 1개 (JSON 필드)
변경 후: PLAN.md §3.N.2 내 "##### 화면: {화면명}" 서브섹션 (md 구조)
폴백: execution-plan.json screen 객체 (과거 태스크 호환)
```

**md 기반 입력 필드 매핑**:

| json 필드 | PLAN.md §3.N.2 대응 | 파싱 방법 |
|-----------|---------------------|----------|
| `id` | `**ID**: FE-{N}` | 라인 파싱 |
| `name` | `##### 화면: {화면명}` 헤딩 | H5 파싱 |
| `type` | `**유형**: {type}` | 라인 파싱 |
| `action` | `**action**: {new\|modify}` | 라인 파싱 |
| `route` | `**경로**: {route}` | 라인 파싱 |
| `files` | `**파일**: {경로 목록}` | 쉼표 구분 파싱 |
| `shadcn_components` | `**shadcn 컴포넌트**: {목록}` | 쉼표 구분 파싱 |
| `ui_work` | `**UI 작업**: {설명}` | 라인 파싱 |
| `api_work` | `**API 연동**: {설명}` | 라인 파싱 |

**폴백 규칙**: PLAN.md에 §3.N.2 FE 화면 설계가 없으면 execution-plan.json screen 객체를 시도.

#### 3.5.3 환경 변경

해당 없음.

#### 3.5.4 배치/마이그레이션

해당 없음.

#### 3.5.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-012 | R7 AC | 산출물 검사 | ui-designer가 PLAN.md의 FE 화면 섹션을 직접 Read하는 플로우가 명시됨 |
| TS-013 | R7 AC | 산출물 검사 | execution-plan.json 의존 서술이 1차 입력에서 제거됨 (폴백으로만 잔존) |

---

### F-006: op-dev-qa 기능-QA 매핑 검증 규칙 추가

#### 3.6.1 파일 변경 계획

**신규 생성**

| # | 경로 | 영역 | 역할 |
|---|------|------|------|
| (없음) | | | |

**수정**

| # | 경로 | 영역 | 변경 내용 요약 |
|---|------|------|--------------|
| 1 | `opal/skills/op-dev-qa/SKILL.md` | 스킬 | PLAN 검증 기준에 기능-QA 커버리지 항목 추가 (P-7 또는 기존 ID 확장); 검증 기준 요약에 Multi-Feature 조건 명시 |
| 2 | `opal/skills/op-dev-qa/references/qa-dev-guide.md` | 가이드 | PLAN (Full) 검증 기준 테이블에 기능-QA 매핑 검증 행 추가; PLAN (Short) 검증 기준에도 해당 항목 조건부 추가 (Multi-Feature 모드일 때만) |

#### 3.6.2 구조/인터페이스 설계

**SKILL.md 추가 검증 ID**:

| # | 검증 항목 | 확인 내용 |
|---|----------|----------|
| P-7 | 기능-QA 커버리지 | (Multi-Feature 모드) 모든 F-NNN이 §5 QA 체크리스트에서 최소 1개 항목으로 커버되는가? 빈틈 발견 시 Fail |

**qa-dev-guide.md 추가 규칙**:

PLAN (Full) 검증 기준 테이블에 추가:

| # | 검증 항목 | 확인 내용 |
|---|----------|----------|
| P-7 | 기능-QA 커버리지 | PLAN.md §1.2 기능 목록의 모든 F-NNN이 §5.1 기능별 QA 테이블에서 최소 1개 QA 항목으로 커버되는가? 빈틈이 있으면 Fail. Flat 모드(기능 1개)에서는 §5가 기능 매핑 없이 존재해도 Pass |

**적용 조건**: Multi-Feature 모드(§1 상단에 "모드: Multi-Feature" 표기)에서만 필수 적용. Flat 모드에서는 자동 Pass.

#### 3.6.3 환경 변경

해당 없음.

#### 3.6.4 배치/마이그레이션

해당 없음.

#### 3.6.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-014 | R8 AC | 산출물 검사 | QA 스킬에 "모든 F-NNN이 §5 QA 체크리스트에서 최소 1개 항목 커버" 규칙이 명시됨 |
| TS-015 | R8 AC | 산출물 검사 | "빈틈 발견 시 Fail" 판정 규칙이 명시됨 |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)

| Phase | 기능 | Step | 실행 | 비고 |
|-------|------|------|------|------|
| 1 | F-000 (백업) | 1 | 단일 | 모든 수정 Step의 선행 |
| 2 | F-001 + F-003 (SKILL.md 부분) | 2, 3 | 순차 | 같은 파일(SKILL.md) 순차 수정 |
| 3 | F-002 + F-003 (plan-guide.md 부분), F-006 | 4, 5 | 병렬 가능 | Phase 2 완료 후. Step 4는 plan-guide.md, Step 5는 qa 스킬 (독립 파일) |
| 4 | F-004, F-005 | 6, 7 | 병렬 가능 | Phase 3 완료 후. execute와 ui-designer는 독립 파일 |
| 5 | 변경이력 + 최종 정합 검증 | 8 | 순차 | 모든 변경 완료 후 |

### 4.2 실행 체크리스트 (기능-Step 매핑)

> 총 8개 Step | Phase 5개 | 실행 모드: 복잡

#### Step 1: 수정 대상 원본 파일 backup/에 복사
- [x] 완료
- **소속 기능**: F-000
- **파일**: 8개 원본 → `tasks/114-260413-opp-op-dev-plan-feature-driven-redesign/backup/` 하위 (원본 경로 구조 유지)
- **작업 내용**:
  1. `tasks/114-260413-opp-op-dev-plan-feature-driven-redesign/backup/` 디렉토리 생성
  2. 8개 원본 파일을 원본 경로 구조 유지하며 복사:
     - `opal/skills/op-dev-plan/SKILL.md` → `backup/opal/skills/op-dev-plan/SKILL.md`
     - `opal/skills/op-dev-plan/references/plan-guide.md` → `backup/opal/skills/op-dev-plan/references/plan-guide.md`
     - `opal/skills/op-dev-execute/SKILL.md` → `backup/opal/skills/op-dev-execute/SKILL.md`
     - `opal/skills/op-dev-execute/references/execute-guide.md` → `backup/opal/skills/op-dev-execute/references/execute-guide.md`
     - `opal/skills/op-dev-qa/SKILL.md` → `backup/opal/skills/op-dev-qa/SKILL.md`
     - `opal/skills/op-dev-qa/references/qa-dev-guide.md` → `backup/opal/skills/op-dev-qa/references/qa-dev-guide.md`
     - `skills/ui-designer/SKILL.md` → `backup/skills/ui-designer/SKILL.md`
     - `skills/ui-designer/modes/plan-driven.md` → `backup/skills/ui-designer/modes/plan-driven.md`
  3. `backup/MANIFEST.md` 작성 (백업 시점, 원본↔백업 경로 매핑 테이블, 복원 명령)
- **완료 기준**: 8개 파일이 backup/ 하위에 존재하고 원본과 바이트 크기 일치. MANIFEST.md에 8개 파일 매핑 테이블이 기재됨
- **테스트**: TS-016, TS-017, TS-018
- **실행 방법**: direct
- **의존**: 없음

#### Step 2: op-dev-plan SKILL.md 기능 중심 구조 전면 재작성
- [x] 완료
- **소속 기능**: F-001, F-003
- **파일**: `opal/skills/op-dev-plan/SKILL.md`
- **작업 내용**:
  1. frontmatter description 갱신 — json 산출물 제거, 기능 중심 구조 설명
  2. 입출력 테이블에서 execution-plan.json 조건부 출력 제거
  3. 프로세스 Step 재정렬: Step 1~10 (기능 식별 Step 신설, json 생성 Step 제거)
  4. PLAN.md 출력 형식을 §1~§9 기능 중심 구조로 교체 (F-NNN 하위 섹션 반복)
  5. 영역 태그 규칙을 6영역(FE/BE/DB/환경/배치/공통)으로 확장
  6. execution-plan.json 스키마 섹션을 Deprecated 고지로 교체
  7. 품질 체크리스트를 기능 중심 항목으로 갱신 (json 관련 제거, 기능-QA 매핑 추가)
  8. 변경이력에 v2.0 추가
- **완료 기준**: SKILL.md의 PLAN.md 출력 형식이 §1~§9 구조이며 §2·§3가 F-NNN 하위 섹션 반복 구조. "기능 리스트업", "기능별 분석", "기능별 설계", "기능-QA 매트릭스" 용어 등장. json 생성 지시 없음. Deprecated 고지 존재
- **테스트**: TS-001, TS-002, TS-003, TS-007, TS-008
- **실행 방법**: direct
- **의존**: Step 1

#### Step 3: op-dev-plan SKILL.md 입력 분기 + ANALYSIS.md 호환 확인
- [x] 완료
- **소속 기능**: F-001
- **파일**: `opal/skills/op-dev-plan/SKILL.md`
- **작업 내용**:
  1. 입력 분기 섹션에서 ANALYSIS.md 유무에 따른 분석 깊이 조절이 기능 루프 안에서도 유효함을 명시
  2. ANALYSIS.md에 `features[]` 필드가 있으면 Multi-Feature 강제 규칙 명시
  3. Step 2에서 작성한 내용과의 정합성 최종 점검
- **완료 기준**: SKILL.md에서 ANALYSIS.md 입력 분기가 기능별 분석 Step과 연결되어 명시됨
- **테스트**: TS-003 (프로세스 검사)
- **실행 방법**: direct
- **의존**: Step 2

#### Step 4: plan-guide.md 기능 중심 단계 + 파싱 규칙 + Flat/Multi 재작성
- [x] 완료
- **소속 기능**: F-002, F-003
- **파일**: `opal/skills/op-dev-plan/references/plan-guide.md`
- **작업 내용**:
  1. 0단계 유지
  2. "1단계: 기능 식별" 신설 (F-ID 부여, 기능 목록 테이블, 의존 그래프, Flat/Multi 판정)
  3. 기존 1~5단계를 "2단계: 기능별 분석" + "3단계: 기능별 설계"로 재배치 (기능 루프)
  4. 6단계(json 생성) 제거 + Deprecated 참고 섹션 추가
  5. "4단계: 통합 실행 계획" 작성 (Phase 그룹핑, 기능-Step 매핑)
  6. "PLAN.md 파싱 규칙" 섹션 신설 (F-ID 포맷, 섹션 앵커, 테이블 컬럼, FE 화면 서브섹션 포맷)
  7. Flat/Multi 모드 판정 테이블 추가 + Flat 모드 PLAN.md 예시
  8. 실행 체크리스트 작성 섹션에 소속 F-ID 필드 추가
  9. QA 체크리스트 섹션에 기능-QA 매트릭스 포맷 추가
  10. 복잡도 판별 + 실행 아키텍처 섹션 유지 (기존 그대로)
  11. 품질 체크리스트를 기능 중심으로 갱신
  12. 변경이력에 v2.0 추가
- **완료 기준**: 가이드에 "기능 식별" 단계가 존재. 파일 변경 계획·구현 순서·핵심 설계·테스트 전략이 기능 루프 안에서 정의됨. 6영역 분류 축 명시. "PLAN.md 파싱 규칙" 섹션 존재. Flat/Multi 판정 테이블과 Flat 예시 존재. json 생성 지시 없음
- **테스트**: TS-004, TS-005, TS-006, TS-007
- **실행 방법**: direct
- **의존**: Step 2

#### Step 5: op-dev-qa 기능-QA 매핑 검증 규칙 추가
- [x] 완료
- **소속 기능**: F-006
- **파일**: `opal/skills/op-dev-qa/SKILL.md`, `opal/skills/op-dev-qa/references/qa-dev-guide.md`
- **작업 내용**:
  1. SKILL.md의 PLAN 검증 기준에 P-7 (기능-QA 커버리지) 추가
  2. qa-dev-guide.md의 PLAN (Full) 검증 기준 테이블에 P-7 행 추가
  3. Multi-Feature 모드 조건 명시 (Flat에서는 자동 Pass)
  4. 변경이력에 버전 추가
- **완료 기준**: QA 스킬에 "모든 F-NNN이 §5 QA 체크리스트에서 최소 1개 항목 커버", "빈틈 발견 시 Fail" 규칙이 명시됨
- **테스트**: TS-014, TS-015
- **실행 방법**: direct
- **의존**: Step 2

#### Step 6: op-dev-execute PLAN.md 기반 실행으로 전환
- [x] 완료
- **소속 기능**: F-004
- **파일**: `opal/skills/op-dev-execute/SKILL.md`, `opal/skills/op-dev-execute/references/execute-guide.md`
- **작업 내용**:
  1. SKILL.md: frontmatter description에서 json 선택 입력 제거
  2. SKILL.md: 입력 우선순위를 "PLAN.md §4 > 기존 PLAN.md §3 > json 폴백"으로 전환
  3. SKILL.md: "execution-plan.json 기반 실행" 섹션을 "PLAN.md 기반 실행" 섹션으로 재작성 (기능 루프 기반)
  4. SKILL.md: FE 역할 분담의 ui-designer 호출 방법을 "PLAN.md §3.N.2 FE 화면 설계 참조"로 변경
  5. SKILL.md: 가드레일·품질 체크리스트에서 json 참조를 PLAN.md로 통일
  6. SKILL.md: 과거 태스크 폴백 규칙 서술
  7. execute-guide.md: 입력 우선순위 변경
  8. execute-guide.md: json 기반 실행 섹션을 PLAN.md 기반으로 재작성
  9. execute-guide.md: 금지 행동·품질 체크리스트에서 json 참조를 PLAN.md로 통일
  10. 변경이력에 버전 추가
- **완료 기준**: SKILL.md에 "PLAN.md §2·§3 입력", "기능 루프 실행", "execution-plan.json 사용 안 함" 지시가 명시됨. 폴백 규칙 존재
- **테스트**: TS-010, TS-011
- **실행 방법**: direct
- **의존**: Step 2, Step 4

#### Step 7: ui-designer plan-driven PLAN.md 입력 전환
- [x] 완료
- **소속 기능**: F-005
- **파일**: `skills/ui-designer/SKILL.md`, `skills/ui-designer/modes/plan-driven.md`
- **작업 내용**:
  1. SKILL.md: frontmatter description에서 json 참조를 PLAN.md로 변경
  2. SKILL.md: 모드 판별 테이블의 plan-driven 입력을 "PLAN.md §3.N.2 FE 화면 설계"로 변경
  3. plan-driven.md: 입력 소스를 PLAN.md §3.N.2 FE 화면 설계 섹션으로 전환
  4. plan-driven.md: 입력 필드 테이블을 md 서브섹션 파싱 규칙으로 교체
  5. plan-driven.md: 실행 프로세스를 PLAN.md Read 기반으로 재작성
  6. plan-driven.md: 폴백으로 기존 json screen 객체 지원 규칙 추가
  7. 변경이력에 버전 추가
- **완료 기준**: ui-designer가 PLAN.md의 FE 화면 섹션을 직접 Read하는 플로우가 명시됨. json 의존 서술이 1차 입력에서 제거됨 (폴백으로만 잔존)
- **테스트**: TS-012, TS-013
- **실행 방법**: direct
- **의존**: Step 2, Step 4

#### Step 8: 변경이력 통일 + 최종 정합 검증
- [x] 완료
- **소속 기능**: F-001~F-006 (공통)
- **파일**: 모든 수정 대상 파일
- **작업 내용**:
  1. 모든 수정 파일의 변경이력에 일시(KST), 버전, 변경내용 기록
  2. 파일 간 교차 참조 검증: SKILL.md가 참조하는 가이드 경로, 가이드가 참조하는 파싱 규칙, 파싱 규칙이 참조하는 섹션 번호가 실제 구조와 일치하는지 확인
  3. 한국어 본문 + 영어 필드명 규칙 최종 검증
  4. kebab-case 파일명 규칙 최종 검증 (본 태스크에서 파일명 변경은 없으므로 기존 확인만)
- **완료 기준**: 모든 파일에 변경이력이 기록됨. 교차 참조가 정합함. 규칙 위반 없음
- **테스트**: 전체 TS에 대한 최종 정합 확인
- **실행 방법**: direct
- **의존**: Step 3, Step 4, Step 5, Step 6, Step 7

### 4.3 병렬/순차 판별 근거

| 관계 | 근거 |
|------|------|
| Step 1 → Step 2~7 | 백업 완료가 모든 수정의 선행 조건 (롤백 안전성) |
| Step 2 → Step 3 | 동일 파일(SKILL.md) 순차 수정 |
| Step 2 → Step 4 | F-002는 F-001 의존. 다른 파일(plan-guide.md)이므로 Step 2 완료 후 병렬 가능 |
| Step 2 → Step 5 | F-006은 F-001 의존. 다른 파일(qa 스킬)이므로 Step 2 완료 후 병렬 가능 |
| Step 4 ∥ Step 5 | 독립 파일, 독립 기능. Phase 3에서 병렬 실행 가능 |
| Step 4 → Step 6 | F-004는 F-003(plan-guide.md 포함) 의존. 파싱 규칙 확정 후 execute 정합화 |
| Step 4 → Step 7 | F-005는 F-003(plan-guide.md 포함) 의존. 파싱 규칙 확정 후 ui-designer 정합화 |
| Step 6 ∥ Step 7 | 독립 파일(execute vs ui-designer). Phase 4에서 병렬 실행 가능 |
| Step 8 ← Step 3~7 | 모든 변경 완료 후 최종 검증 |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA

| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-000 | backup/ 디렉토리 + 8개 파일 존재 | TS-016 | 원본 경로 구조 유지 |
| F-000 | 백업 파일 바이트 크기 원본 일치 | TS-017 | cksum/크기 비교 Pass |
| F-000 | backup/MANIFEST.md 존재 + 매핑 테이블 | TS-018 | 8개 행 매핑 테이블 기재 |
| F-001 | SKILL.md PLAN.md 출력 형식이 §1~§9 기능 중심 구조 | TS-001 | §2·§3가 "### F-NNN:" 하위 섹션 반복 |
| F-001 | SKILL.md에 기능 중심 용어 등장 | TS-002 | "기능 리스트업", "기능별 분석", "기능별 설계", "기능-QA 매트릭스" 4개 용어 모두 존재 |
| F-001 | 프로세스에 기능 식별 Step 존재 | TS-003 | 기능 루프 기반 분석→설계 명시 |
| F-002 | plan-guide.md에 기능 식별 단계 신설 | TS-004 | 기능 루프 + 6영역 분류 |
| F-002 | PLAN.md 파싱 규칙 섹션 존재 | TS-005 | F-ID, 섹션 앵커, 테이블 컬럼 규칙 정의 |
| F-002 | Flat/Multi 판정 테이블 + Flat 예시 존재 | TS-006 | 판정 조건 3행 + 평면 구조 예시 |
| F-003 | json 생성 지시 제거 | TS-007 | 두 파일에 json 생성 지시 없음 |
| F-003 | 하위호환 보존 고지 | TS-008 | Deprecated 고지 + 기존 json 미삭제 선언 |
| F-003 | 과거 json 파일 미변경 | TS-009 | 과거 태스크 폴더의 json 파일 그대로 |
| F-004 | execute PLAN.md 기반 실행 명시 | TS-010 | "PLAN.md §2·§3 입력", "기능 루프 실행" 문구 |
| F-004 | 과거 태스크 폴백 규칙 존재 | TS-011 | 기존 형식 PLAN.md + json 폴백 명시 |
| F-005 | ui-designer PLAN.md 직접 Read 플로우 | TS-012 | PLAN.md §3.N.2 FE 화면 설계 참조 명시 |
| F-005 | json 1차 의존 제거 | TS-013 | 폴백으로만 잔존 |
| F-006 | 기능-QA 커버리지 규칙 | TS-014 | "모든 F-NNN이 §5에서 최소 1개 항목 커버" |
| F-006 | 빈틈 Fail 규칙 | TS-015 | "빈틈 발견 시 Fail" 판정 |

> 모든 F-000~F-006이 최소 1개 QA 항목으로 커버됨. 모든 TS-001~TS-018이 매핑됨.

### 5.2 회귀 테스트

- [x] backup/ 하위 백업 파일이 수정 후에도 초기 백업 상태와 바이트 일치 (백업 자체 무결성)
- [x] 기존 생성된 execution-plan.json 파일이 삭제·수정되지 않았는가
- [x] opsdd 파이프라인 파일(`opal/skills/op-sdd-*`)이 수정되지 않았는가
- [x] op-task-plan 파일(`opal/skills/op-task-plan/`)이 수정되지 않았는가
- [x] 하네스 파일(`~/.opal/references/opal-harness*.md`)이 수정되지 않았는가
- [x] PM 프로세스 파일(`.opal/AGENT.md`)이 수정되지 않았는가
- [x] `opal-pilot-dev`/`opal-pilot-dev-short` 오케스트레이터 본체가 수정되지 않았는가 (R6/R7/R8은 단계 스킬만 수정)
- [x] op-dev-execute `checkpoint-guide.md`가 수정되지 않았는가
- [x] ui-designer scaffold 모드(`modes/scaffold.md`)가 수정되지 않았는가
- [x] op-dev-qa `qa-wireframe-guide.md`가 수정되지 않았는가

### 5.3 코드/문서 품질

- [x] 한국어 본문 + 영어 필드명 규칙 준수
- [x] kebab-case 파일명 준수
- [x] 변경이력 기록(버전, KST 일시, 변경내용) — 모든 수정 파일
- [x] YAML frontmatter 형식 유지 (name, description, triggers, version)
- [x] 섹션 번호 연속성 (건너뛰기 없음)
- [x] 교차 참조 정합 (SKILL.md ↔ plan-guide.md ↔ execute-guide.md ↔ plan-driven.md)

### 5.4 보안

- [x] 커밋되지 않은 민감 정보 없음 (본 태스크에서는 해당 항목 거의 없음)
- [x] 코드에 하드코딩된 토큰/시크릿 없음 (문서 전용 태스크이므로 N/A)

---

## 6. 복잡도 판별

| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 8개 (백업 Step 포함) | 복잡 |
| 변경 파일 수 | 8개 수정 + 10개 신규(백업) = 18개 | 복잡 |
| 모듈 범위 | 다중 스킬 (op-dev-plan, op-dev-execute, op-dev-qa, ui-designer) | 복잡 |
| 작업 유형 | 아키텍처 개편 (문서 구조 전면 재설계) + 백업 | 복잡 |
| 외부 의존성 | 없음 | 단순 |
| **실행 모드** | **복잡** | |

---

## 7. 실행 아키텍처 (복잡 모드)

### C-1. 에이전트 토폴로지

본 태스크는 프레임워크 문서 개편이며, opp(opal-pilot-project) 파이프라인으로 실행된다. opp는 `op-task-execute` 스킬을 사용하며, op-dev-test-agent 대신 정적 산출물 검증을 수행한다.

**에이전트 구성**:

```
Phase 1: Agent-Main (direct)
  Step 1: 수정 대상 원본 파일 백업 (F-000)

Phase 2: Agent-Main (direct)
  Step 2: op-dev-plan SKILL.md 전면 재작성 (F-001 + F-003)
  Step 3: op-dev-plan SKILL.md 입력 분기 확인 (F-001 연속)

Phase 3: Agent-Main (direct, 순차)
  Step 4: plan-guide.md 재작성 (F-002 + F-003)
  Step 5: op-dev-qa 규칙 추가 (F-006)

Phase 4: Agent-Main (direct, 순차)
  Step 6: op-dev-execute 정합화 (F-004)
  Step 7: ui-designer 정합화 (F-005)

Phase 5: Agent-Main (direct)
  Step 8: 변경이력 + 최종 정합 검증
```

**병렬 실행 판단**: Phase 2의 Step 3/4와 Phase 3의 Step 5/6는 독립 파일이지만, 본 태스크는 문서 간 교차 참조가 밀접하여 같은 에이전트가 순차적으로 처리하는 것이 정합성 보장에 유리하다. opp 파이프라인에서는 단일 워커가 direct로 실행하므로 서브 에이전트 분리 불필요.

### C-2. 스킬 요구사항

| 스킬 | 용도 | 매칭 |
|------|------|------|
| op-task-execute | opp 파이프라인 실행 스킬 | 기존 스킬 |
| op-task-qa | opp 파이프라인 QA 스킬 | 기존 스킬 |

갭: 없음. 기존 스킬로 충분.

### C-3. 도구 요구사항

| 도구 | 용도 |
|------|------|
| Read | 기존 파일 확인 |
| Edit/Write | 문서 수정/작성 |
| Grep | 교차 참조 검증 (json 참조 잔존 여부 확인 등) |

추가 패키지/MCP 불필요.

### C-4. 테스트 전략

op-dev-test-agent는 opp 파이프라인에서 사용하지 않는다. 정적 산출물 검증으로 충분:

| 검증 방법 | 대상 | 기대 결과 |
|----------|------|----------|
| 산출물 Read | 각 수정 파일 | TS-001~TS-015 조건 충족 |
| Grep 검증 | 전체 수정 파일 | "execution-plan.json을 생성" 지시 미존재 확인 |
| Grep 검증 | opsdd 파이프라인 파일 | 변경 없음 확인 |
| Grep 검증 | op-task-plan 파일 | 변경 없음 확인 |

---

## 8. 기술 컨텍스트

### 기술 스택

| 영역 | 기술 | 적용 참조 |
|------|------|----------|
| 문서 | Markdown | CONVENTIONS.md |
| 스킬 정의 | YAML frontmatter | CONVENTIONS.md |
| 파일 네이밍 | kebab-case | CONVENTIONS.md |
| 언어 규칙 | 한국어 본문 + 영어 코드/필드명 | CONVENTIONS.md |

### 사용 MCP/스킬

| 항목 | 용도 |
|------|------|
| context7 | 해당 없음 (프레임워크 문서 작업) |
| 기타 MCP | 해당 없음 |

---

## 9. 리스크 및 대응

| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| 1 | op-dev-execute가 새 PLAN.md 구조(§2·§3)를 기대하지만, 과거 태스크의 기존 PLAN.md에는 해당 섹션이 없어 회귀 발생 | F-004 | 중 | 3단계 폴백 규칙 서술: 새 PLAN.md §4 → 기존 PLAN.md §3 → json. 과거 태스크 실행 시 기존 로직 유지 |
| 2 | ui-designer plan-driven 입력 전환 시 md 파싱 복잡도 증가. JSON 대비 구조 파악이 어려울 수 있음 | F-005 | 중 | F-002에서 파싱 규칙을 명확히 정의. H5 헤딩 + 볼드 필드명으로 일관된 파싱 가능. json 폴백 유지 |
| 3 | Flat/Multi 모드 경계 사례. 기능 개수 판정이 모호한 태스크(1개인지 2개인지 애매한 경우) | F-002 | 저 | Flat/Multi 판정을 워커가 §1에서 수행하고 PM Gate에서 검증. 모호하면 Multi로 처리 (overhead는 있지만 정보 누락 없음) |
| 4 | SKILL.md와 plan-guide.md 동시 대규모 변경으로 교차 참조 불일치 위험 | F-001, F-002 | 중 | Step 7에서 최종 정합 검증 수행. 섹션 번호, 파싱 규칙, Step 번호 일치 확인 |
| 5 | 6영역(FE/BE/DB/환경/배치/공통) 확장이 기존 `[FE]`/`[BE]`/`[공통]` 태그와 혼재될 위험 | F-001, F-002 | 저 | 새 PLAN에서는 대괄호 없이 테이블 컬럼 값으로 표기. 기존 형식과 명확히 구분. plan-guide.md에 영역 목록 정의 |

---

## 10. 자기정합 검증 체크리스트 (본 태스크 특이사항)

본 PLAN.md의 구조와 EXECUTE 결과(새 op-dev-plan SKILL.md + plan-guide.md)의 구조가 일치해야 한다:

- [x] PLAN.md §1~§9의 섹션 구조가 EXECUTE 결과 SKILL.md의 PLAN.md 출력 형식과 개념적으로 매칭
  - 본 PLAN: §1 태스크 개요+기능 리스트업, §2 기능별 분석, §3 기능별 설계, §4 통합 실행 계획, §5 QA, §6 복잡도, §7 실행 아키텍처, §8 기술 컨텍스트, §9 리스크
  - EXECUTE 결과 SKILL.md: 동일 §1~§9 출력 형식
- [x] F-ID 포맷(`F-{NNN}`)이 EXECUTE 결과의 파싱 규칙과 동일
  - 본 PLAN: `F-001`~`F-006` 사용
  - EXECUTE 결과 plan-guide.md: `F-{NNN}` 3자리 zero-padded 규칙 정의
- [x] 6영역 축(FE/BE/DB/환경/배치/공통)이 EXECUTE 결과의 관련 파일 맵 컬럼과 동일
  - 본 PLAN: 스킬/가이드/오케스트레이터/에이전트/문서/환경/배치 축 사용 (프레임워크 태스크 특성)
  - EXECUTE 결과 plan-guide.md: FE/BE/DB/환경/배치/공통 축 정의 (일반 개발 태스크용)
  - QA 확인: plan-guide.md에 6영역(FE/BE/DB/환경/배치/공통)과 "프레임워크 문서·스킬 태스크에서는 스킬/가이드/... 축 사용" 모두 명시됨. 본 PLAN은 프레임워크 태스크 특화 축을 사용하였으며 plan-guide.md 규칙과 정합함
- [x] TS-ID 매핑 테이블이 EXECUTE 결과의 테스트 시나리오 포맷과 동일
  - 본 PLAN: `TS-ID | AC 매핑 | 유형 | 기대결과` 컬럼
  - EXECUTE 결과 plan-guide.md: 동일 컬럼 규칙 정의

---

## 문서/코드 불일치 사항

| 항목 | 문서(TASK.md) | 코드(실제 파일) | PLAN 기준 |
|------|-------------|---------------|----------|
| ui-designer 위치 | TASK.md에 `opal/skills/ui-designer/SKILL.md` 기재 | 실제 경로는 `skills/ui-designer/SKILL.md` (독립 스킬 소스) | **코드 기준** — `skills/ui-designer/` |
| op-dev-plan Step 번호 | TASK.md에 "Step 7(execution-plan.json 생성)" | SKILL.md에서 실제로 Step 7이 json 생성 | 일치 |
| plan-guide.md 6단계 | TASK.md에 "plan-guide.md 6단계" | 실제로 6단계가 json 생성 | 일치 |

---

## 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-04-13 12:51 | 초기 작성 — 탑다운 기능 중심 PLAN.md 구조 시범 적용, F-001~F-006 기능 6개, Step 7개, Phase 4개 |
| v1.1 | 2026-04-13 13:41 | F-000(수정 전 원본 파일 백업) 횡단 기능 신설 — 캡틴 지시 반영. Step 1 백업 신설(기존 Step 1~7을 Step 2~8로 shift), Phase 1→5 재정렬, TS-016~TS-018 추가, §5.1 F-000 QA 3행 추가, §5.2 백업 무결성 회귀 항목 추가 |
