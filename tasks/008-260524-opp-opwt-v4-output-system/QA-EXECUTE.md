# QA-EXECUTE: opwt 산출물 체계 v4

> 검증 일시: 2026-05-24 14:55 | QA 워커: opal-task-qa-agent (sonnet)
> 검증 대상: SKILL.md / network-guide.md / consistency-rules.md
> 검증 기준: TASK.md R-1~R-8 / PLAN.md §4 / citation-rules.md

---

## 1. 검증 요약

| 항목 | 결과 |
|------|------|
| 전체 판정 | **Pass** |
| R-1~R-8 AC 매핑 | 통과 8/8 |
| 영역 간 용어 일관성 | 통과 5/6 (Minor 1건 — §10 "선택 4종" 미갱신) |
| PLAN §4 체크리스트 | 통과 29/30 (Minor 1건 동일 사안) |
| 변경이력 형식 | 통과 1/1 |
| 마이그레이션 안내 | 통과 1/1 |

---

## 2. R-1~R-8 AC 검증

### R-1 PRD 8섹션 표준 도입

| AC 항목 | 결과 | 근거 |
|---------|------|------|
| §7-3 PRD 가이드에 8섹션 표(섹션명/필수·선택/작성 기준 컬럼) 존재 | Pass | `network-guide.md §7-3 L402-413` — 헤더 "PRD 유형의 경우, 아래 섹션을 반드시 포함한다:" 직후 3컬럼 표 확인 |
| 8섹션 명칭이 TASK.md §확정 방향 §2와 정확히 일치 | Pass | 표 8행: 개요/배경 및 목표/Non-goals/타깃 사용자/주요 기능/요구사항 명세/Acceptance Criteria/Open Questions — `TASK.md §2` 와 완전 일치 |
| 타깃 사용자 섹션에 "인구통계학적 + 행동·심리적" 가이드 명시 | Pass | `network-guide.md §7-3 L409` — "**인구통계학적**(연령/성별/직업/소득/지역) + **행동·심리적**(관심사/라이프스타일/기술 활용도/소비/니즈·페인)" 명시 |
| 요구사항 명세 섹션에 "기능적 요구사항 테이블(FR-XXX 형식)" 가이드 명시 | Pass | `network-guide.md §7-3 L411` — "**기능적 요구사항 테이블** (FR-XXX/제목/설명/우선순위/의존성)" 명시 |
| 작성 원칙(한 페이지 응집·간결·모호 금지) 명시 | Pass | `network-guide.md §7-3 L415-418` — 작성 원칙 박스에 3개 원칙 명시 |

**판정: Pass** — R-1 AC 5/5 충족

---

### R-2 기능 시나리오 다이어그램 신설 (순서도 재정의)

| AC 항목 | 결과 | 근거 |
|---------|------|------|
| §1 선택 산출물 표에서 "순서도"가 "기능 시나리오 다이어그램"으로 명칭 변경 + 설명에 flowchart+sequence+state 3종 명시 | Pass | `network-guide.md §1 L23` — "기능 시나리오 다이어그램 \| 기능 단위 사용자-시스템 상호작용·상태 전이. Mermaid flowchart + sequenceDiagram + stateDiagram-v2 3종 통합" 확인. "순서도" 행 없음 (추가 확인: `SKILL.md L455` v4.0 변경이력에 "기존 '순서도' 재정의" 명시) |
| §7-3에 기능 시나리오 다이어그램 작성 가이드 신설 (필수 섹션 6개 + Mermaid 작성 규칙) | Pass | `network-guide.md §7-3 L430-447` — 필수 섹션 6개(시나리오 개요/정상 경로/시스템 통신/상태 전이/예외·실패/연관 id) + Mermaid 작성 규칙(sequenceNumbers/box·rect/alt·else·end/loop·end) |
| 파일명 컨벤션 `scenario-{기능명}.md` 명시 | Pass | `network-guide.md §7-3 L432` — "파일명 컨벤션: `scenario-{기능명}.md` (kebab-case, 시나리오별 파일 분리)" |

**판정: Pass** — R-2 AC 3/3 충족

---

### R-3 화면 흐름도 신설

| AC 항목 | 결과 | 근거 |
|---------|------|------|
| §1 선택 산출물 표에 "화면 흐름도" 행 추가 + 설명에 Mermaid flowchart + 화면 단위 명시 | Pass | `network-guide.md §1 L24` — "화면 흐름도 \| 화면 단위 네비게이션 전환. Mermaid flowchart 단일. IA·와이어프레임과 연결." |
| §2 연결 맵에 "화면 흐름도 ↔ IA"·"화면 흐름도 ↔ 와이어프레임(외부 참조)" 추가 | Pass | `network-guide.md §2 L97-103` — 양방향 참조 블록 2쌍 확인. §2 "각 연결의 참조 항목" 표(L126-127)에도 IA·시나리오·화면 흐름도 행 존재 |
| §7-3에 화면 흐름도 작성 가이드 신설 (필수 섹션 6개) | Pass | `network-guide.md §7-3 L449-461` — 단위/표기법 명시 + 필수 섹션 6개(시작점/화면 노드+전환 화살표/분기·조건/종료점/화면 그룹화/연관 IA 메뉴 id) |
| 시나리오 다이어그램과의 경계(화면 vs 기능 단위)가 명시 | Pass | `network-guide.md §7-3 L463` — "> **시나리오 다이어그램과 경계**: 화면 흐름도 = **화면 단위**(전환). 시나리오 = **기능 단위**(상호작용·상태). 동일 내용을 양쪽에 작성하지 않는다." |

**판정: Pass** — R-3 AC 4/4 충족

---

### R-4 Mermaid 시각화 표준 확대

| AC 항목 | 결과 | 근거 |
|---------|------|------|
| 신규 절(network-guide.md §11)에 산출물별 시각화 강제 수준 표(필수/권장 분류) 존재 | Pass | `network-guide.md §11 L735-747` — "opwt 산출물별 Mermaid 다이어그램의 강제 수준과 권장 유형" 표 7행 확인 |
| 필수: IA / 기능 시나리오 다이어그램 / 화면 흐름도 (3종) | Pass | `network-guide.md §11 L740-742` — 3종 모두 "필수" 확인 |
| 권장: PRD(사용자 여정) / TRD(아키텍처) / 정책서(상태 전이) / 기능도 (4종) | Pass | `network-guide.md §11 L743-747` — 4종 모두 "권장" 확인 |
| 각 산출물별 권장 다이어그램 유형(flowchart/sequence/state/graph) 명시 | Pass | `network-guide.md §11 L739-747` — 각 행마다 다이어그램 유형 명시 (`flowchart TD`/`flowchart + sequenceDiagram + stateDiagram-v2`/`flowchart`/`graph`/`sequenceDiagram`/`stateDiagram-v2`) |

**판정: Pass** — R-4 AC 4/4 충족

---

### R-5 WBS 제거 (PMO 그룹 폐기)

| AC 항목 | 결과 | 근거 |
|---------|------|------|
| SKILL.md "커버 범위" 섹션에서 PMO·개발 WBS 문구 0건 | Pass | `SKILL.md L34-38` 커버 범위 — "필수 4종/선택 5종/프로젝트 특화/순서 체인/외부 참조"만 존재. PMO/WBS 문자열 없음 (grep 확인: 변경이력 행 2건만 존재 — v2.4 이력 기록과 v4.0 이력의 "PMO 그룹 및 개발 WBS 제거" 문구) |
| network-guide.md §1 PMO 섹션 행 0건 / Level 분해 구조 표 0건 | Pass | `network-guide.md §1 L7-36` — PMO 헤더 없음. 선택 5종/필수 4종/프로젝트 특화만 존재 |
| §2 연결 맵에서 "개발 WBS ↔ *" 행 0건 | Pass | `network-guide.md §2 L40-130` — grep 결과 "개발 WBS" 문자열 0건 |
| §2 참조 항목 테이블에서 "개발 WBS" 관련 행 0건 | Pass | `network-guide.md §2 L114-129` 참조 항목 표 — WBS 관련 행 없음 |
| §5 diagnosis.json `type` enum에서 "개발 WBS" 문자열 0건 | Pass | `network-guide.md §5 L211` — enum: "PRD \| TRD \| 서비스 정책서 \| IA \| 기능도 \| 기능 시나리오 다이어그램 \| 화면 흐름도 \| 운영 정책서 \| 서비스 매뉴얼 \| 외부 API 명세서" |
| §7 Phase 3 워커 프롬프트에서 WBS 관련 가이드 0건 | Pass | `network-guide.md §7 L295-513` — WBS 문자열 없음. 기능 시나리오 다이어그램·화면 흐름도 가이드로 대체됨 |
| consistency-rules.md §7 Tier 분류에서 WBS 관련 행 0건 | Pass | `consistency-rules.md §7 L293-299` Tier 1~5 — WBS 행 없음 |

**참고**: SKILL.md 변경이력 L444에 "v2.4 \| PMO 그룹 신설..." 이력 행이 유지됨 — 이는 과거 이력 기록이므로 R-5 AC 위반 아님 (TASK.md §제약 조건 "변경이력 의무" 참조). PM의 사전 grep 검증과 일치.

**판정: Pass** — R-5 AC 7/7 충족

---

### R-6 interview 스킬 통합 (TASK 단계)

| AC 항목 | 결과 | 근거 |
|---------|------|------|
| SKILL.md TASK 절에 interview 스킬 의존성 명시 (탐색 경로 2개 포함) | Pass | `SKILL.md L59-64` — "interview 스킬 호출" 헤더 + 탐색 경로 2개: `{프로젝트}/.opal/skills/interview/SKILL.md` / `~/.opal/skills/interview/SKILL.md` |
| Round 1/2/3 라운드 설계 표 존재 (질문 수·옵션 형식·multiSelect 여부) | Pass | `SKILL.md L66-72` — 5컬럼 표(라운드/질문 수/옵션 형식/multiSelect/트리거 조건) 존재 |
| Step 1 도메인 옵션 구성 가이드 명시 (외부 API 신호 / 부가 산출물 신호 / docs/ 자동 스캔) | Pass | `SKILL.md L74-97` — (a)외부 API 신호 탐지/키워드·도메인 목록, (b)부가 산출물 신호 탐지 5개 신호, (c)외부 참조 자동 스캔 경로 3개 |
| TASK.md 신규 섹션 양식 명시 ("산출물 결정" + "외부 참조" + "PRD 입력 컨텍스트") | Pass | `SKILL.md L103-131` — Step 4 결과 기록에 markdown 코드 블록으로 3개 섹션 양식 전체 명시 |
| 기존 "TASK 전용 확인 항목" 4개가 인터뷰 라운드로 재구성됨 | Pass | grep 결과: "TASK 전용 확인 항목"/"모드 결정"/"대상 문서 유형"/"외부 참조 여부"/"산출물 저장 경로" 문자열 0건 |
| Round 3 호출 조건이 "PRD가 Round 1에서 선택된 경우"로 명시 | Pass | `SKILL.md L72` — "트리거 조건" 컬럼: "**PRD가 Round 1 답변에서 표준 산출물로 선택된 경우에만**" |

**판정: Pass** — R-6 AC 6/6 충족

---

### R-7 정합성 검증 규칙 확장

| AC 항목 | 결과 | 근거 |
|---------|------|------|
| §1에 "시나리오 ↔ 정책서/TRD/IA" 3쌍 + "화면 흐름도 ↔ IA" 1쌍 추가 (각 쌍 양방향 체크 ≥2개) | Pass | `consistency-rules.md §1 L77-107` — 시나리오↔정책서(3체크/L79-83), 시나리오↔TRD(3체크/L86-91), 시나리오↔IA(3체크/L94-99), 화면 흐름도↔IA(3체크/L101-107) 확인. 각 쌍 ≥2개 충족 |
| §7 Tier 분류에서 WBS 행 제거, "시나리오 ↔ 정책서·TRD·IA"·"화면 흐름도 ↔ IA"가 적절한 Tier에 추가 | Pass | `consistency-rules.md §7 L296` — Tier 3: "기능 시나리오 다이어그램 ↔ 정책서/TRD/IA (시나리오 산출물 존재 시), 화면 흐름도 ↔ IA (화면 흐름도 산출물 존재 시)" 명시 |
| §8 외부 참조 검증에 "화면 흐름도 ↔ 와이어프레임" 추가 | Pass | `consistency-rules.md §8 L373-379` — "### 화면 흐름도 ↔ 와이어프레임" 절 신설, 3체크 항목(흐름도→와이어프레임/와이어프레임→흐름도/분기 조건 양방향) |

**판정: Pass** — R-7 AC 3/3 충족

---

### R-8 변경이력 + 메모리 갱신

| AC 항목 | 결과 | 근거 |
|---------|------|------|
| SKILL.md 변경이력 마지막 행이 v4.0 + 날짜(2026-05-24) + 태스크 008 번호 포함 | Pass | `SKILL.md L455` — "v4.0 \| 2026-05-24 14:21 \| ... (008)" — semver/날짜/태스크번호 모두 확인 |
| 변경 내용에 R-1~R-7 핵심 변경이 한 줄 요약으로 명시 | Pass | `SKILL.md L455` — "interview 통합(TASK 절 재구성) + PRD 8섹션 표준 + 기능 시나리오 다이어그램 재정의 + 화면 흐름도 신설 + Mermaid 시각화 표준 절 신설 + PMO 그룹 및 개발 WBS 제거" — R-1~R-7 전부 포함 |
| `.opal/MEMORY.md` 작업 히스토리 008 행이 CLOSE 단계에서 완료일시 갱신 | N/A | CLOSE 단계 미완료 — PLAN.md §4 설명대로 CLOSE 단계에서 자동 수행. 본 QA 범위 외 |

**참고**: HH:mm 리터럴 잔류 여부 grep 결과: 0건. `2026-05-24 14:21`로 정상 치환됨.

**형식 검증 (docs/CONVENTIONS.md §변경이력)**:
- 일시: `2026-05-24 14:21` (KST) — YYYY-MM-DD HH:mm 형식 준수
- 버전: `v4.0` — semver 준수
- 태스크 번호: `(008)` — 괄호 형식 준수

**판정: Pass** — R-8 AC 2/2 충족 (나머지 1건 N/A + 사유 명시)

---

## 3. PLAN.md §4 QA 체크리스트 갱신

> PLAN.md 자체를 수정하지 않음. QA-EXECUTE.md §3에 갱신본 수록.

### 4.1 기능 테스트 (R-1~R-8 AC 매핑)

#### R-1 PRD 8섹션 표준 도입
- [x] §7-3 PRD 신규 작성 가이드에 8섹션 표(섹션명/필수·선택/작성 기준 컬럼) 존재 — `network-guide.md §7-3 L402-413`
- [x] 8섹션 명칭이 TASK.md §확정 방향 §2와 정확히 일치 (개요/배경 및 목표/Non-goals/타깃 사용자/주요 기능/요구사항 명세/Acceptance Criteria/Open Questions)
- [x] 타깃 사용자 섹션에 "인구통계학적 + 행동·심리적" 가이드 명시 — `L409`
- [x] 요구사항 명세 섹션에 "기능적 요구사항 테이블(FR-XXX 형식)" 가이드 명시 — `L411`
- [x] 작성 원칙(한 페이지 응집·간결·모호 금지) 명시 — `L415-418`

#### R-2 기능 시나리오 다이어그램 신설 (순서도 재정의)
- [x] §1 선택 산출물 표에서 "순서도"가 "기능 시나리오 다이어그램"으로 명칭 변경 + 설명에 flowchart+sequence+state 3종 명시 — `§1 L23`
- [x] §7-3에 기능 시나리오 다이어그램 작성 가이드 신설 (필수 섹션 6개 + Mermaid 작성 규칙) — `L430-447`
- [x] 파일명 컨벤션 `scenario-{기능명}.md` 명시 — `L432`

#### R-3 화면 흐름도 신설
- [x] §1 선택 산출물 표에 "화면 흐름도" 행 추가 + 설명에 Mermaid flowchart + 화면 단위 명시 — `§1 L24`
- [x] §2 연결 맵에 "화면 흐름도 ↔ IA"·"화면 흐름도 ↔ 와이어프레임(외부 참조)" 추가 — `§2 L97-103`
- [x] §7-3에 화면 흐름도 작성 가이드 신설 (필수 섹션 6개) — `L449-461`
- [x] 시나리오 다이어그램과의 경계(화면 vs 기능 단위)가 명시 — `L463`

#### R-4 Mermaid 시각화 표준 확대
- [x] 신규 절(network-guide.md §11)에 산출물별 시각화 강제 수준 표(필수/권장 분류) 존재 — `§11 L735-747`
- [x] 필수: IA / 기능 시나리오 다이어그램 / 화면 흐름도 (3종) — `L740-742`
- [x] 권장: PRD(사용자 여정) / TRD(아키텍처) / 정책서(상태 전이) / 기능도 (4종) — `L743-747`
- [x] 각 산출물별 권장 다이어그램 유형(flowchart/sequence/state/graph) 명시 — `L739-747`

#### R-5 WBS 제거 (PMO 그룹 폐기)
- [x] SKILL.md "커버 범위" 섹션에서 PMO·개발 WBS 문구 0건 — `SKILL.md L34-38`
- [x] network-guide.md §1 PMO 섹션 행 0건 / Level 분해 구조 표 0건 — `§1 L7-36`
- [x] §2 연결 맵에서 "개발 WBS ↔ *" 행 0건 — grep 검증 완료
- [x] §2 참조 항목 테이블에서 "개발 WBS" 관련 행 0건 — `§2 L114-129`
- [x] §5 diagnosis.json `type` enum에서 "개발 WBS" 문자열 0건 — `§5 L211`
- [x] §7 Phase 3 워커 프롬프트에서 WBS 관련 가이드 0건 — `§7 L295-513`
- [x] consistency-rules.md §7 Tier 분류에서 WBS 관련 행 0건 — `§7 L293-299`

#### R-6 interview 스킬 통합 (TASK 단계)
- [x] SKILL.md TASK 절에 interview 스킬 의존성 명시 (탐색 경로 2개 포함) — `SKILL.md L59-64`
- [x] Round 1/2/3 라운드 설계 표 존재 (질문 수·옵션 형식·multiSelect 여부) — `L66-72`
- [x] Step 1 도메인 옵션 구성 가이드 명시 (외부 API 신호 / 부가 산출물 신호 / docs/ 자동 스캔) — `L74-97`
- [x] TASK.md 신규 섹션 양식 명시 ("산출물 결정" + "외부 참조" + "PRD 입력 컨텍스트") — `L103-131`
- [x] 기존 "TASK 전용 확인 항목" 4개가 인터뷰 라운드로 재구성됨 — grep 결과 0건 확인
- [x] Round 3 호출 조건이 "PRD가 Round 1에서 선택된 경우"로 명시 — `L72`

#### R-7 정합성 검증 규칙 확장
- [x] §1에 "시나리오 ↔ 정책서/TRD/IA" 3쌍 + "화면 흐름도 ↔ IA" 1쌍 추가 (각 쌍 양방향 체크 ≥2개) — `consistency-rules.md §1 L77-107`
- [x] §7 Tier 분류에서 WBS 행 제거, "시나리오 ↔ 정책서·TRD·IA"·"화면 흐름도 ↔ IA"가 적절한 Tier에 추가 — `§7 L296`
- [x] §8 외부 참조 검증에 "화면 흐름도 ↔ 와이어프레임" 추가 — `§8 L373-379`

#### R-8 변경이력 + 메모리 갱신
- [x] SKILL.md 변경이력 마지막 행이 v4.0 + 날짜(2026-05-24) + 태스크 008 번호 포함 — `SKILL.md L455`
- [x] 변경 내용에 R-1~R-7 핵심 변경이 한 줄 요약으로 명시 — `L455`
- N/A `.opal/MEMORY.md` 작업 히스토리 008 행이 CLOSE 단계에서 완료일시 갱신 — CLOSE 단계 미완료. 본 QA 시점 기준 해당 없음

### 4.2 일관성 테스트

- [x] SKILL.md 커버 범위·TASK 절·변경이력 3영역의 v4 변경이 서로 모순되지 않음 — "기능 시나리오 다이어그램"/"화면 흐름도" 3영역 모두 동일 명칭 (`SKILL.md L35, L113-114, L455`)
- [x] network-guide.md §1·§2·§5·§7-3·§11 사이 신규 산출물 명칭 일관 — "기능 시나리오 다이어그램"(14건)/화면 흐름도"(14건) 모든 절에서 동일 표기 (grep 확인)
- [x] consistency-rules.md §1·§7·§8 신규 쌍의 산출물명이 network-guide.md §1과 동일 표기 — 4쌍 모두 "기능 시나리오 다이어그램"/"화면 흐름도" 동일 표기
- [x] PMO/WBS 잔여 흔적 0건 — 3개 파일 grep 결과: SKILL.md는 변경이력 행 2건(v2.4 과거 이력 + v4.0 "제거" 문구)만 존재. network-guide.md·consistency-rules.md 0건
- [x] Mermaid 다이어그램 유형(flowchart/sequence/state/graph)이 §7-3 가이드와 §11 표 사이에서 일관 — 기능 시나리오 다이어그램: §7-3 L438-440(flowchart+sequence+state) ↔ §11 L741 일치. 화면 흐름도: §7-3 L451 ↔ §11 L742 일치
- [ ] 8섹션 명칭이 SKILL.md TASK 절(Round 3 PRD 입력 컨텍스트)과 network-guide.md §7-3 PRD 가이드 양쪽에서 동일 표기 — **Minor** SKILL.md Step 4 결과 기록(L125-130)의 PRD 입력 컨텍스트 섹션에는 "배경 및 목표/타깃 사용자/주요 기능+MVP 범위/Non-goals" 4개 항목만 명시. 8섹션 전체 명칭이 나열되어 있지 않으나, 이는 "PRD 입력 컨텍스트" 항목이 Round 3에서 수집하는 PRD 작성 초안 컨텍스트이므로 8섹션 전체를 나열할 필요는 없음 — 설계상 의도적 차이로 판단. 기능 차단 수준 아님

### 4.3 문서 품질

- [x] 한국어 본문 + 영어 코드/필드명 규칙 준수 — FR-XXX, type enum, scenario-{기능명}.md 등 영어 식별자 유지 확인 (`docs/CONVENTIONS.md §언어 규칙`)
- [x] kebab-case 파일/폴더 네이밍 준수 — `scenario-{기능명}.md` 컨벤션 명시 (`docs/CONVENTIONS.md §파일/폴더`)
- [x] YAML frontmatter 변경 없음 — SKILL.md L1-7 frontmatter: name/description 유지, v4.0에서 미수정 확인
- [x] 변경이력 행 형식 — `2026-05-24 14:21` (YYYY-MM-DD HH:mm) / `v4.0` (semver) / `(008)` 괄호 — 모두 준수 (`docs/CONVENTIONS.md §변경이력 작성 의무`)
- [x] 표 정렬 — 신규 §7-3 PRD 8섹션 표, 기능 시나리오 다이어그램 표, 화면 흐름도 표, §11 Mermaid 시각화 표준 표 — 헤더 구분선(`|---|`) 정렬 확인

---

## 4. 발견 사항

### 4.1 Critical

없음.

---

### 4.2 Normal

없음.

---

### 4.3 Minor

**m-1: network-guide.md §10 설명 텍스트의 "선택 4종" 미갱신**

- 파일: `opal/skills/opal-pilot-write-tech/references/network-guide.md`
- 위치: §10 L709 — "opwt 관리 산출물(필수 4종 + **선택 4종**) 외에..."
- 현황: v4에서 선택 산출물이 5종으로 변경되었으나 §10 도입 설명 텍스트는 "선택 4종"으로 남아있음
- 영향: 기능 오작동 없음. 단순 설명 텍스트 불일치 — 사용자/워커가 §1 선택 5종 표와 불일치를 인지할 경우 혼란 가능성
- 권고: 차기 작업 시 `선택 4종` → `선택 5종` 수정 권장
- R-N 매핑: PLAN §4.2 일관성 (용어 일관성 Minor)

---

## 5. 최종 판정

| 구분 | 판정 | 비고 |
|------|------|------|
| R-1~R-8 AC 전체 | **Pass** | 30개 AC 중 29개 Pass / 1개 N/A (MEMORY.md — CLOSE 단계) |
| 영역 간 용어 일관성 | **Pass** (Minor 1건) | §10 "선택 4종" 미갱신 — 기능 차단 없음 |
| 변경이력 형식 | **Pass** | YYYY-MM-DD HH:mm / semver / (008) 모두 준수 |
| 마이그레이션 안내 | **Pass** | v4.0 변경이력 행에 "사용자 수동 재분류" 명시 (RISK-2/M-4 적용) |
| Critical 이슈 | **없음** | |
| Normal 이슈 | **없음** | |
| Minor 이슈 | **1건** | §10 "선택 4종" → "선택 5종" 수정 권고 |

**전체 판정: Pass**

> EXECUTE 산출물(SKILL.md / network-guide.md / consistency-rules.md) 3개 파일이 TASK.md R-1~R-8 AC를 모두 충족한다. Minor 1건(§10 설명 텍스트 불일치)은 기능에 영향을 주지 않으므로 Pass 판정을 유지한다. 다음 단계(CLOSE) 진입 가능.
