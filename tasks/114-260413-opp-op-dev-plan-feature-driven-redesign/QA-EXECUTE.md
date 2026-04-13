# QA-EXECUTE: op-dev-plan 탑다운 기능 중심 구조 개편

> 검토일: 2026-04-13 | 판정: Pass
> 검증 대상: EXECUTE changed_files 17개 (수정 8개 + 백업 9개) | 검증자: opal-task-qa-agent (op-task-qa)

## 1. 종합 판정

| 항목 | 결과 |
|------|------|
| 전체 판정 | **Pass** |
| Pass | 18개 |
| Fail | 0개 |
| Info | 1개 |

## 2. TS 검증 (A~G)

| TS-ID | F-ID | 결과 | 근거 (파일·라인·grep 결과 등) |
|-------|------|------|------|
| TS-001 | F-001 | Pass | `op-dev-plan/SKILL.md` L150: "§1~§9 골격을 사용", L32: "보장 출력: PLAN.md (기능 중심 구조 §1~§9)". PLAN.md 출력 형식 섹션에 §1~§9 전체 구조 및 `### F-NNN: {기능명}` H3 하위 섹션 반복 명시됨 |
| TS-002 | F-001 | Pass | `op-dev-plan/SKILL.md`: "기능 리스트업"(L159), "기능별 분석"(L174, Step4 제목), "기능별 설계"(L194, Step5 제목), "기능-QA 매트릭스"(L261, §5 제목) — 4개 용어 모두 등장 |
| TS-003 | F-001 | Pass | `op-dev-plan/SKILL.md` L88: `### Step 3: 기능 식별`, L98: `### Step 4: 기능별 분석 (기능 루프)`, L108: `### Step 5: 기능별 설계 (기능 루프)` — 기능 식별 Step 존재 + 기능 루프 기반 분석→설계 명시 |
| TS-004 | F-002 | Pass | `plan-guide.md` L27: `## 1단계: 기능 식별 (신설)`, L70: `## 2단계: 기능별 분석 (기능 루프)`, L76: 6영역 분류 축 `FE / BE / DB / 환경 / 배치 / 공통` 명시됨 |
| TS-005 | F-002 | Pass | `plan-guide.md` L284: `## PLAN.md 파싱 규칙 (후속 소비자용)` 섹션 존재. F-ID 포맷(`F-{NNN}` 3자리), 기능 섹션 앵커(`### F-NNN: {이름}`), 관련 파일 맵 컬럼(`영역\|경로\|역할\|변경유형`), 테스트 시나리오 컬럼(`TS-ID\|AC 매핑\|유형\|기대결과`) 모두 정의됨 |
| TS-006 | F-002 | Pass | `plan-guide.md` L54: Flat/Multi-Feature 모드 판정 테이블(3행: 기능>=2, 기능=1, ANALYSIS features[]), L61: Flat 모드 PLAN.md 구조 예시 제시됨 |
| TS-007 | F-003 | Pass | Grep 결과: `plan-guide.md`에 "execution-plan.json을 생성" 지시 없음. L350 `## 참고: execution-plan.json 하위호환` 섹션에 "더 이상 생성하지 않는다" 명시. `SKILL.md` L339 `## Deprecated: execution-plan.json` 섹션에 "더 이상 생성하지 않는다" 명시. 두 파일 모두 생성 지시 없음 확인 |
| TS-008 | F-003 | Pass | `SKILL.md` L344: "기존에 생성된 execution-plan.json 파일은 삭제하지 않으며 하위호환을 보존한다." `plan-guide.md` L354: 동일 문구. Deprecated 고지 + 기존 json 미삭제 선언 양 파일에 존재 |
| TS-009 | F-003 | Pass | `find tasks -name "execution-plan.json" -not -path "*/backup/*"` 결과 없음. 과거 태스크의 json 파일이 존재하더라도 삭제/수정 없음 확인. (현재 tasks/ 하위에 json 파일 자체가 없어 회귀 위험도 없음) |
| TS-010 | F-004 | Pass | `op-dev-execute/SKILL.md` L17-18: 입력 우선순위 1위 "PLAN.md §4 실행 체크리스트 (기능 중심 구조, F-NNN 소속 기능 포함)". L58-61: "PLAN.md에 §2·§3 기능별 섹션이 없는 경우 (과거 태스크)" 언급. L209: "**execution-plan.json 사용 안 함**" 명시. 기능 루프 기반 실행은 L172 FE 실행 순서, L196-209 PLAN.md 기반 실행 섹션에 명시됨 |
| TS-011 | F-004 | Pass | `op-dev-execute/SKILL.md` L54-61: 폴백 계층 "PLAN.md §3 (과거 형식) → execution-plan.json (json만 있는 경우) → 블로커 보고". `execute-guide.md` L56-77: 과거 태스크 폴백 규칙 상세 서술. 양 파일에 폴백 규칙 명시됨 |
| TS-012 | F-005 | Pass | `skills/ui-designer/SKILL.md` L6: frontmatter에 "PLAN.md의 FE 화면 설계 섹션(§3.N.2)을 입력으로 받아" 명시. 모드 판별 테이블 L22: plan-driven 입력 "PLAN.md §3.N.2 FE 화면 설계". `modes/plan-driven.md` L13: "기본 입력: PLAN.md §3.N.2 FE 화면 설계 섹션". 직접 Read 플로우 명시됨 |
| TS-013 | F-005 | Pass | `skills/ui-designer/SKILL.md`: frontmatter에서 "execution-plan.json" 참조 제거됨. 모드 판별 테이블에서 json 언급 없음. `modes/plan-driven.md` L44: "폴백 입력: execution-plan.json screen 객체" — 1차 입력에서 제거되고 폴백으로만 잔존 확인 |
| TS-014 | F-006 | Pass | `op-dev-qa/SKILL.md` L118: "P-7 (Multi-Feature 모드에서만 필수): 모든 F-NNN이 §5 QA 체크리스트에서 최소 1개 항목으로 커버되는가?" 규칙 명시. `qa-dev-guide.md` L89: P-7 행 추가 확인 |
| TS-015 | F-006 | Pass | `op-dev-qa/SKILL.md` L118: "빈틈 발견 시 Fail" 명시. `qa-dev-guide.md` L89: "빈틈이 있으면 Fail" 명시. 양 파일에 판정 규칙 존재 |
| TS-016 | F-000 | Pass | `backup/` 하위 파일 목록 확인: 8개 파일이 원본 경로 구조 유지하여 존재 (`backup/opal/skills/op-dev-plan/SKILL.md`, `backup/opal/skills/op-dev-plan/references/plan-guide.md`, `backup/opal/skills/op-dev-execute/SKILL.md`, `backup/opal/skills/op-dev-execute/references/execute-guide.md`, `backup/opal/skills/op-dev-qa/SKILL.md`, `backup/opal/skills/op-dev-qa/references/qa-dev-guide.md`, `backup/skills/ui-designer/SKILL.md`, `backup/skills/ui-designer/modes/plan-driven.md`) |
| TS-017 | F-000 | Pass | `wc -c` 비교 결과 — 백업 파일 8개 모두 MANIFEST.md 기재 크기와 일치: op-dev-plan/SKILL.md 11108B, plan-guide.md 14208B, op-dev-execute/SKILL.md 9845B, execute-guide.md 7777B, op-dev-qa/SKILL.md 6354B, qa-dev-guide.md 5336B, ui-designer/SKILL.md 12377B, plan-driven.md 4348B. 전체 일치 |
| TS-018 | F-000 | Pass | `backup/MANIFEST.md` 존재 확인. 백업 파일 목록 테이블에 8개 행 기재됨 (원본 경로, 백업 경로, 크기 컬럼 포함). 복원 방법 및 변경이력도 포함됨 |

## 3. 제약 조건 회귀 검증 (H)

| # | 항목 | 결과 | 근거 |
|---|------|------|------|
| H-1 | 기존 생성된 execution-plan.json 파일 삭제·수정 없음 | Pass | `find tasks -name "execution-plan.json" -not -path "*/backup/*"` 결과 없음. tasks/ 하위에 json 파일 자체 없어 삭제 위험 없음 |
| H-2 | opsdd 파이프라인(`opal/skills/op-sdd-*`) 미수정 | Pass | `git log --since="2026-04-12" -- "opal/skills/op-sdd-*"` 결과 없음 (해당 기간 수정 커밋 없음) |
| H-3 | op-task-plan(`opal/skills/op-task-plan/`) 미수정 | Pass | `git log --since="2026-04-12" -- "opal/skills/op-task-plan/*"` 결과 없음 |
| H-4 | 하네스 파일 미수정 | Pass | `git log --since="2026-04-12" -- "*opal-harness*"` 결과 없음 |
| H-5 | `.opal/AGENT.md` 미수정 | Pass | `git log --since="2026-04-12" -- ".opal/AGENT.md"` 결과 없음 |
| H-6 | `opal-pilot-dev`/`opal-pilot-dev-short` 오케스트레이터 본체 미수정 | Pass | `git log --since="2026-04-12" -- "*opal-pilot-dev*"` 결과 없음 |
| H-7 | op-dev-execute `checkpoint-guide.md` 미수정 | Pass | `git log --since="2026-04-12" -- "*/op-dev-execute/references/checkpoint-guide.md"` 결과 없음 |
| H-8 | ui-designer `modes/scaffold.md` 미수정 | Pass | `git log --since="2026-04-12" -- "*/ui-designer/modes/scaffold.md"` 결과 없음 |
| H-9 | op-dev-qa `qa-wireframe-guide.md` 미수정 | Pass | `git log --since="2026-04-12" -- "*/op-dev-qa/references/qa-wireframe-guide.md"` 결과 없음 |
| H-10 | `backup/` 무결성 (Step 1 이후 백업 파일 변경 없음) | Pass | `wc -c` 백업 파일 실측치가 MANIFEST.md 기재 크기와 완전 일치. 8개 파일 모두 수정 후 원래 크기 유지 |

## 4. 코드/문서 품질 (I)

| # | 항목 | 결과 | 근거 |
|---|------|------|------|
| I-1 | 한국어 본문 + 영어 필드명 규칙 | Pass | 수정된 8개 파일 모두 한국어 설명 본문 + 영어 필드명(PLAN.md, F-ID, TS-ID, FE/BE/DB 등) 패턴 준수 |
| I-2 | kebab-case 파일명 | Pass | 본 태스크에서 파일명 신규 생성 없음. 기존 kebab-case 파일명(plan-guide.md, execute-guide.md, qa-dev-guide.md, plan-driven.md) 유지 |
| I-3 | 변경이력(버전, KST 일시, 변경내용) — 모든 수정 파일 | Pass | `op-dev-plan/SKILL.md`: v2.0 / 2026-04-13 13:48 기록. `plan-guide.md`: v2.0 / 2026-04-13 13:48. `op-dev-execute/SKILL.md`: v1.2 / 2026-04-13 13:48. `execute-guide.md`: v1.1 / 2026-04-13 13:48. `op-dev-qa/SKILL.md`: v1.1 / 2026-04-13 13:48. `qa-dev-guide.md`: v1.1 / 2026-04-13 13:48. `ui-designer/SKILL.md`: v1.1 / 2026-04-13 13:48. `plan-driven.md`: v1.1 / 2026-04-13 13:48. 모든 수정 파일에 변경이력 존재 |
| I-4 | YAML frontmatter 형식 유지 | Pass | `op-dev-plan/SKILL.md`: `name`, `description`, `version: 2.0` 포함. `op-dev-execute/SKILL.md`: `name`, `description`, `version: 1.2` 포함. `ui-designer/SKILL.md`: `name`, `description`, `version: 1.1` 포함. `op-dev-qa/SKILL.md`에는 `version` 필드 없음 (원래 없던 것으로 기존 형식 유지이나 Info 기재) |
| I-5 | 교차 참조 정합 (SKILL.md ↔ plan-guide.md ↔ execute-guide.md ↔ plan-driven.md) | Pass | op-dev-plan SKILL.md Step 1이 `references/plan-guide.md` Read 참조. plan-guide.md §3.N.2 "FE 화면 설계 (ui-designer plan-driven 모드 입력 포맷)" — plan-driven.md와 포맷 일치. execute SKILL.md L147, L172: "PLAN.md §3.N.2 FE 화면 설계 섹션" 참조. plan-driven.md L13: "PLAN.md §3.N.2 FE 화면 설계 서브섹션(`##### 화면: {화면명}`)". 교차 참조 정합 확인 |

## 5. 자기정합 검증 (J)

| # | 항목 | 결과 | 근거 |
|---|------|------|------|
| J-1 | PLAN.md §1~§9 구조가 EXECUTE 결과 SKILL.md의 PLAN.md 출력 형식과 개념적 매칭 | Pass | 본 태스크 PLAN.md는 §1(기능 리스트업)~§9(리스크)를 실제로 사용. op-dev-plan SKILL.md의 PLAN.md 출력 형식(§1~§9 골격)과 완전히 대응. PLAN.md가 새 구조의 시범 적용 사례로 자기정합 |
| J-2 | F-ID 포맷 `F-{NNN}` 3자리 zero-padded 규칙 정의 | Pass | `plan-guide.md` L29: "F-ID 포맷: `F-{NNN}` (3자리 zero-padded, 예: F-001, F-002, F-010)". `plan-guide.md` L285 파싱 규칙 테이블: "F-ID: `F-{NNN}` (3자리 zero-padded)". 양쪽에 명시 |
| J-3 | 6영역 축(FE/BE/DB/환경/배치/공통) plan-guide.md에서 정의 | Pass | `plan-guide.md` L82: "6영역 라벨: `FE` (프론트엔드) / `BE` (백엔드) / `DB` (데이터베이스) / `환경` (설정·패키지) / `배치` (배치·크론·마이그레이션) / `공통` (FE/BE 공유)". op-dev-plan SKILL.md 영역 태그 규칙 테이블과 일치 |
| J-4 | TS-ID 매핑 테이블 컬럼 `TS-ID \| AC 매핑 \| 유형 \| 기대결과` 규칙 정의 | Pass | `plan-guide.md` L164-165: 테스트 시나리오 포맷 `\| TS-ID \| AC 매핑 \| 유형 \| 기대 결과 \|`. L168: "TS-ID: `TS-{NNN}` 형식, 태스크 내 전역 고유". `plan-guide.md` L294: 파싱 규칙 테이블에 "테스트 시나리오 컬럼: `TS-ID \| AC 매핑 \| 유형 \| 기대결과`" 명시 |

## 6. 발견 사항

### Non-blocking (Info/권고)

- **[Info] op-dev-qa/SKILL.md frontmatter에 `version` 필드 없음**: 수정된 다른 7개 파일 모두 YAML frontmatter에 `version` 필드가 있으나, `op-dev-qa/SKILL.md`는 원래부터 version 필드가 없는 상태. 본 개편에서 v1.1 변경이력이 추가되었으나 frontmatter에 version은 추가되지 않음. 기능 동작에는 영향 없고, 다른 op-dev-qa 관련 파일들이 기존 형식을 유지한 것이므로 Info로 분류.

- **[Info] TS-010 AC 표현 vs 실제 구현 미묘한 차이**: TASK.md R6 AC는 "PLAN.md §2·§3 입력"을 명시하나, 실제 SKILL.md는 "PLAN.md §4 실행 체크리스트"를 기본 입력으로 하고 §3.N.2를 FE 화면 설계 참조로 사용. §2·§3는 폴백 컨텍스트에서 언급됨. 개념적으로는 §4(실행 체크리스트)가 §2·§3(기능별 분석·설계)에서 도출되므로 정합하며 "execution-plan.json 사용 안 함" 문구는 명시됨. 기능 충족으로 판정.

### Blocking (Fail 원인)

없음.

## 7. 체크리스트 갱신 결과

### PLAN.md §4.2 Step 체크박스 확인

Step 1~8 모두 `[x] 완료` 상태 확인됨 (PLAN.md L793, L813, L831, L843, L865, L879, L899, L916). 추가 갱신 불필요.

### PLAN.md §5.1 기능별 QA 상태

§5.1은 체크박스 형식이 아닌 테이블 형식(`F-ID | QA 항목 | TS-ID | Pass 조건`)으로 구성되어 있음. 모든 항목(F-000~F-006, TS-001~TS-018)이 Pass 판정이므로 테이블에 상태 컬럼 추가 필요 없음. (PLAN.md 출력 규격 상 체크박스 없는 테이블이 정상 형식)

### PLAN.md §5.2 회귀 테스트

H-1~H-10 모두 Pass. PLAN.md §5.2의 10개 체크박스 모두 `[x]` 상태 확인됨 (PLAN.md L975-984). 갱신 완료 상태.

### PLAN.md §5.3 코드/문서 품질

I-1~I-5 모두 Pass. PLAN.md §5.3의 6개 체크박스 모두 `[x]` 상태 확인됨 (PLAN.md L988-993). 갱신 완료 상태.

### PLAN.md §5.4 보안

모두 Pass (문서 전용 태스크, N/A 항목). PLAN.md §5.4의 2개 체크박스 모두 `[x]` 상태 확인됨 (PLAN.md L997-998). 갱신 완료 상태.

> 참고: PLAN.md §4.2와 §5 체크박스는 EXECUTE 단계에서 이미 실행자가 `[x]`로 갱신한 상태로 확인됨. QA 검증 결과 모두 Pass이므로 현재 상태가 정확함.

## 8. 결론

**Pass** — TS-001~TS-018 18개 항목 전체 Pass, 제약 조건 회귀 10개 전체 통과, 코드/문서 품질 5개 전체 통과, 자기정합 4개 전체 통과. Blocking 이슈 없음. op-dev-plan 탑다운 기능 중심 구조 개편이 PLAN.md 설계 요구사항을 완전히 충족하며 후속 소비자(op-dev-execute, ui-designer, op-dev-qa) 정합화도 완료됨.
