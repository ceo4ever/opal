# TASK: opwt 산출물 체계 v4 — interview 통합 + PRD 8섹션 + 시나리오·화면 흐름도 + WBS 제거

> 작성일: 2026-05-24 | 작업 유형: 개선 | 적용 스킬: opp | 모드: agentic
> 입력: 사용자 요청 + app-planning-presentation 자료 흡수 검토
> 출력: TASK.md

## 작업 목표

opwt(opal-pilot-write-tech) 스킬의 산출물 체계를 v4로 개편한다. `app-planning-presentation` 교육 자료의 내용·산출물·구성을 적극 흡수하여, PRD를 "서비스 기획서 + 요구사항 명세서" 통합 문서로 확장하고, 시각화 산출물(기능 시나리오 다이어그램·화면 흐름도)을 신설하며, 산출물 결정 인터뷰를 TASK 단계에 통합한다. 동시에 PMO 그룹(개발 WBS)을 제거하여 산출물 체계를 단순화한다.

## 배경

opwt 현재 버전(v3.4)은 PRD/TRD/정책서/IA 4종 기획 산출물 + 외부 API 명세서 + 개발 WBS를 양방향 네트워크로 관리한다. 정합성 검증·버전 관리·QA Gate 등 운영 기반은 견고하지만, 다음 영역에서 공백이 있다:

1. **시각화 빈약** — IA만 Mermaid 사이트맵 강제. PRD/TRD/정책서/시나리오는 텍스트 위주
2. **PRD 구조 약함** — 서비스 기획서 핵심 요소(개요/배경·목표/타깃 페르소나/주요 기능) 가이드 부족
3. **요구사항 명세 단편화** — PRD 내부 "핵심 요구사항"이 ID·우선순위·의존성 추적 미흡
4. **순서도 정의 모호** — 선택 산출물 "순서도"는 정의·표준 구조가 없어 활용도 낮음
5. **화면 동적 전환 표현 부재** — IA는 정적 구조, 와이어프레임은 외부 참조. 화면-화면 흐름이 빈 공간
6. **TASK 단계 산출물 결정 비효율** — 사용자가 모든 산출물 옵션을 일일이 선택해야 함
7. **WBS 잉여** — 개발 WBS는 기획 산출물 범위 밖. opwt에서 다루는 가치 < 복잡도

`app-planning-presentation` (2026-05-23 캡처, `/Volumes/Data/AiStudio/workspace/ai-plan-dev/app-planning-presentation/`) 자료를 분석한 결과, 위 7개 공백 중 1·2·3·4·5를 직접 해결할 수 있는 패턴이 다수 존재한다. 6은 OPAL의 `interview` 스킬로 흡수 가능하며, 7은 같은 개편 시점에 함께 정리한다.

## 배경 분석 (대화에서 도출)

### 본 자료 분석 결과 — 흡수 가능 요소 5종

| # | 본 자료 요소 | opwt 흡수 방향 |
|---|------------|--------------|
| A-1 | 기획서 4섹션(개요/배경·목표/타겟/기능) + 한 페이지 응집 원칙 | PRD 8섹션으로 확장 흡수 |
| A-2 | 요구사항 명세서 (FR-ID/제목/우선순위/의존성) | PRD 내부 "요구사항 명세" 섹션으로 통합 (별도 산출물 미생성) |
| A-3 | 화면 흐름도 (Mermaid flowchart, 화면 단위) | 선택 산출물로 신설 |
| A-4 | 기능별 시나리오 다이어그램 (flowchart + sequence + state) | 기존 "순서도" 재정의 |
| A-5 | Mermaid 단일 표기법 통일 | 시각화 표준 산출물 확대 |

### 본 자료 약점 — 흡수 미적용

| # | 약점 | opwt 유지 강점 |
|---|------|------------|
| N-1 | 단방향 누적 체인 | 양방향 네트워크(connected_to + depends_on) 유지 |
| N-2 | 검증 단계 부재 | QA Gate + consistency-rules 유지 |
| N-3 | 비기능 요구사항 일률 수치 | TRD "[미결: 수치 확정 필요]" 패턴 유지 |
| N-4 | 갱신·버전 관리 부재 | status / version / 변경이력 유지 |
| N-5 | 코딩 프롬프트 변환 (templates/ 3종) | 별도 태스크로 분리. 본 태스크 범위 외 |

### 현재 opwt 산출물 구조 (v3.4)

| 그룹 | 종류 |
|------|------|
| 필수 4종 | PRD / TRD / 정책서 / IA |
| 선택 4종 | 기능도 / 순서도 / 운영정책서 / 매뉴얼 |
| 프로젝트 특화 | 외부 API 명세서 |
| PMO | 개발 WBS |

→ 총 9종. v4에서 PMO 제거 + 선택 5종(흐름도 추가)으로 재편.

## 확정된 설계 방향 (대화에서 합의)

### §1. 산출물 구조 v4

| 그룹 | 종류 (10종) | v3.4 대비 변경 |
|------|----------|-------------|
| 필수 4종 | **PRD(8섹션 확장)** / TRD / 정책서 / IA | PRD 대폭 확장 |
| 선택 5종 | 기능도 / **기능 시나리오 다이어그램** / 운영정책서 / 매뉴얼 / **화면 흐름도** | 순서도 재정의 + 화면 흐름도 신설 |
| 프로젝트 특화 | 외부 API 명세서 | 유지 |
| ~~PMO~~ | (제거) | 폐기 |

### §2. PRD 8섹션 표준

| # | 섹션 | 필수/선택 | 핵심 내용 |
|---|------|---------|---------|
| 1 | 개요 | 필수 | 작성일·작성자·버전 / 프로젝트 한 줄 정의 |
| 2 | 배경 및 목표 | 필수 | 프로젝트 배경(시장 문제·경쟁 환경·기존 솔루션 한계) + 목표(SMART, 비즈니스 vs 사용자, 단기·장기) |
| 3 | Non-goals | 필수 | 이번 버전 제외 범위 |
| 4 | 타깃 사용자 | 필수(강화) | 인구통계학적(연령/성별/직업/소득/지역) + 행동·심리적(관심사/라이프스타일/기술 활용도/소비/니즈·페인 포인트) + User Stories + Mermaid 사용자 여정 권장 |
| 5 | 주요 기능 | 필수(신규) | 핵심 가치 제안 / 차별점 / 주요 기능 요약(Must/Should/Nice-to-have) / MVP 표시 / 향후 예정 |
| 6 | 요구사항 명세 | 필수(신규, 명세서 흡수) | 기능적 요구사항 테이블(FR-XXX/제목/설명/우선순위/의존성) + 비기능적 요구사항(성능/보안/확장성, TRD와 중복 시 PRD 요약·TRD SSOT) |
| 7 | Acceptance Criteria | 필수(강화) | GIVEN/WHEN/THEN, 핵심 Must 기능당 최소 1개 |
| 8 | Open Questions | 필수 | 미결 사항. 없으면 "없음" 명시 |

**작성 원칙** (본 자료 흡수):
- 한 페이지 응집 — 모든 이해관계자가 같은 그림을 보게
- 간결·명확 / 모호한 표현 금지 ("빠르게" → "응답 3초 이내")
- 시각적 요소(다이어그램·차트) 활용 권장

### §3. 기능 시나리오 다이어그램 (순서도 재정의)

| 항목 | 내용 |
|------|------|
| 단위 | 기능 단위 (시나리오별 파일 분리, `scenario-*.md`) |
| 표기법 | Mermaid (flowchart TD + sequenceDiagram + stateDiagram-v2) |
| 필수 섹션 | ① 시나리오 개요 ② 정상 경로(flowchart) ③ 시스템 통신(sequence) ④ 상태 전이(state) ⑤ 예외·실패 케이스 ⑥ 연관 정책서·TRD·IA id |
| Mermaid 규칙 | `sequenceNumbers` 활성화 / `box`·`rect` 도메인 경계 / Client–API 경계 명시 / `alt/else/end` 분기 / `loop/end` 반복 |
| 연결 | ↔ 정책서(예외/규칙) / ↔ TRD(API 시퀀스) / ↔ IA(기능 동작) |

### §4. 화면 흐름도 (신규)

| 항목 | 내용 |
|------|------|
| 단위 | 화면 단위 (네비게이션 중심) |
| 표기법 | Mermaid flowchart |
| 필수 섹션 | ① 시작점 ② 화면 노드 + 전환 화살표 ③ 분기·조건 ④ 종료점 ⑤ 화면 그룹화 ⑥ 연관 IA 메뉴 id |
| 연결 | ↔ IA(메뉴 구조) / ↔ 와이어프레임(외부 참조) |
| 시나리오 다이어그램과 경계 | 화면 흐름도 = **화면 단위**(전환). 시나리오 = **기능 단위**(상호작용·상태) |

### §5. Mermaid 시각화 표준

| 산출물 | 시각화 강제 수준 | 다이어그램 유형 |
|--------|----------------|-------------|
| IA (기존) | 필수 | `flowchart TD` 사이트맵 |
| 기능 시나리오 다이어그램 (신규) | 필수 | flowchart + sequence + state 3종 |
| 화면 흐름도 (신규) | 필수 | flowchart |
| PRD — 타깃 사용자 | 권장 | flowchart (사용자 여정) |
| TRD — 아키텍처 | 권장 | graph (시스템 구성도) + sequence (핵심 호출) |
| 정책서 — 상태 변화 | 권장 | stateDiagram |
| 기능도 | 권장 | graph |

### §6. WBS 제거

- SKILL.md 커버 범위에서 "PMO·개발 WBS" 섹션 제거
- network-guide.md §1 PMO 섹션 제거 / §2 연결 맵에서 WBS 관련 행 제거 / §5 diagnosis.json `type` enum에서 "개발 WBS" 제거
- consistency-rules.md §7 Tier 분류에서 WBS 행 제거

### §7. interview 스킬 통합 (TASK 단계)

| 항목 | 내용 |
|------|------|
| 호출 시점 | opwt TASK 단계 (PM 직접 수행) |
| 호출 대상 | `interview` 스킬 (탐색: `{프로젝트}/.opal/skills/interview/` → `~/.opal/skills/interview/`) |
| 라운드 구성 | Round 1 (모드 + 표준 산출물 + 조건부 외부 API) / Round 2 (부가 산출물 사전 필터 + 외부 참조 자동 스캔) / Round 3 (PRD 5섹션, PRD 작성 모드 한정) |
| Step 1 — opwt 도메인 옵션 구성 | (a) 외부 API 신호 탐지(키워드/도메인) → Q3 조건부 노출 (b) 부가 산출물 신호 탐지 → Q4 옵션 필터 (c) docs/ 스캔 → Q5 외부 참조 자동 감지 |
| Step 4 — 결과 기록 | TASK.md 신규 섹션 "산출물 결정" + "외부 참조" + "PRD 입력 컨텍스트" |

### §8. 변경이력 버전

- v4.0 (메이저 변경) — 산출물 체계 재편 + PRD 대폭 확장 + interview 통합. 태스크 008 참조.

## 요구사항

- [ ] **R-1 PRD 8섹션 표준 도입**
  - **무엇을**: PRD 워커 프롬프트(network-guide.md §7-3)에 8섹션 표준 추가
  - **어디에**: `opal/skills/opal-pilot-write-tech/references/network-guide.md` §7-3
  - **왜**: 본 자료의 서비스 기획서 + 요구사항 명세서 통합 흡수 (확정 방향 §2)
  - **AC**:
    - §7-3 PRD 신규 작성 가이드에 8섹션 표(섹션명/필수·선택/작성 기준 컬럼 포함)가 존재
    - 8섹션 명칭이 확정 방향 §2와 정확히 일치 (개요/배경 및 목표/Non-goals/타깃 사용자/주요 기능/요구사항 명세/Acceptance Criteria/Open Questions)
    - 타깃 사용자 섹션에 "인구통계학적 + 행동·심리적" 가이드 명시
    - 요구사항 명세 섹션에 "기능적 요구사항 테이블(FR-XXX 형식)" 가이드 명시
    - 작성 원칙(한 페이지 응집·간결·모호 금지) 명시

- [ ] **R-2 기능 시나리오 다이어그램 신설 (순서도 재정의)**
  - **무엇을**: network-guide.md §1 산출물 유형에서 "순서도"를 "기능 시나리오 다이어그램"으로 재정의 + §7-3에 작성 가이드 신설
  - **어디에**: `network-guide.md` §1, §7-3
  - **왜**: 본 자료의 sequence/state/flowchart 통합 흡수 (확정 방향 §3)
  - **AC**:
    - §1 선택 산출물 표에서 "순서도" 행이 "기능 시나리오 다이어그램"으로 명칭 변경되고 설명에 flowchart+sequence+state 3종 명시
    - §7-3에 기능 시나리오 다이어그램 작성 가이드 신설 (필수 섹션 6개 + Mermaid 작성 규칙)
    - 파일명 컨벤션 `scenario-{기능명}.md` 명시

- [ ] **R-3 화면 흐름도 신설**
  - **무엇을**: 선택 산출물에 "화면 흐름도" 추가 + 워커 프롬프트 작성 가이드 추가
  - **어디에**: `network-guide.md` §1, §2, §7-3
  - **왜**: 본 자료의 화면-화면 전환 흐름 표현 흡수 (확정 방향 §4)
  - **AC**:
    - §1 선택 산출물 표에 "화면 흐름도" 행 추가 + 설명에 Mermaid flowchart + 화면 단위 명시
    - §2 연결 맵에 "화면 흐름도 ↔ IA"·"화면 흐름도 ↔ 와이어프레임(외부 참조)" 추가
    - §7-3에 화면 흐름도 작성 가이드 신설 (필수 섹션 6개)
    - 시나리오 다이어그램과의 경계(화면 vs 기능 단위)가 명시

- [ ] **R-4 Mermaid 시각화 표준 확대**
  - **무엇을**: network-guide.md에 "Mermaid 시각화 표준" 절 신설
  - **어디에**: `network-guide.md` (현 §9 또는 §11 신규 절)
  - **왜**: 본 자료의 Mermaid 단일 표기법 흡수 (확정 방향 §5)
  - **AC**:
    - 신규 절에 산출물별 시각화 강제 수준 표(필수/권장 분류) 존재
    - 필수: IA / 시나리오 다이어그램 / 화면 흐름도
    - 권장: PRD(사용자 여정) / TRD(아키텍처) / 정책서(상태 전이) / 기능도
    - 각 산출물별 권장 다이어그램 유형(flowchart/sequence/state/graph) 명시

- [ ] **R-5 WBS 제거 (PMO 그룹 폐기)**
  - **무엇을**: SKILL.md / network-guide.md / consistency-rules.md에서 PMO 그룹·개발 WBS 관련 모든 내용 제거
  - **어디에**: 3개 파일 전체
  - **왜**: 산출물 체계 단순화 (확정 방향 §6)
  - **AC**:
    - SKILL.md "커버 범위" 섹션에서 PMO·개발 WBS 문구 0건
    - network-guide.md §1 PMO 섹션 행 0건 / Level 분해 구조 표 0건
    - §2 연결 맵에서 "개발 WBS ↔ *" 행 0건
    - §1 참조 항목 테이블에서 "개발 WBS" 관련 행 0건
    - §5 diagnosis.json `type` enum에서 "개발 WBS" 문자열 0건
    - §7 Phase 3 워커 프롬프트에서 WBS 관련 가이드 0건
    - consistency-rules.md §7 Tier 분류에서 WBS 관련 행 0건

- [ ] **R-6 interview 스킬 통합 (TASK 단계)**
  - **무엇을**: SKILL.md TASK 단계 절을 "interview 스킬 호출 + 3라운드"로 재구성
  - **어디에**: `opal/skills/opal-pilot-write-tech/SKILL.md` TASK 절
  - **왜**: 산출물 결정 + PRD 입력 컨텍스트를 인터뷰로 수집 (확정 방향 §7)
  - **AC**:
    - SKILL.md TASK 절에 interview 스킬 의존성 명시 (탐색 경로 2개 포함)
    - Round 1/2/3 라운드 설계 표 존재 (질문 수·옵션 형식·multiSelect 여부)
    - Step 1 도메인 옵션 구성 가이드 명시 (외부 API 신호 / 부가 산출물 신호 / docs/ 자동 스캔)
    - TASK.md 신규 섹션 양식 명시 ("산출물 결정" + "외부 참조" + "PRD 입력 컨텍스트")
    - 기존 "TASK 전용 확인 항목" 4개가 인터뷰 라운드로 재구성됨

- [ ] **R-7 정합성 검증 규칙 확장**
  - **무엇을**: consistency-rules.md §1에 신규 쌍 추가 + §7 Tier 갱신
  - **어디에**: `consistency-rules.md` §1, §3, §5, §7
  - **왜**: 신규 산출물(시나리오·화면 흐름도)의 정합성 검증
  - **AC**:
    - §1에 "시나리오 ↔ 정책서/TRD/IA" 3쌍 + "화면 흐름도 ↔ IA" 1쌍 추가 (각 쌍 양방향 체크 항목 ≥2개)
    - §7 Tier 분류에서 WBS 행 제거, "시나리오 ↔ 정책서·TRD·IA"·"화면 흐름도 ↔ IA"가 적절한 Tier에 추가
    - §8 외부 참조 검증에 "화면 흐름도 ↔ 와이어프레임" 추가

- [ ] **R-8 변경이력 + 메모리 갱신**
  - **무엇을**: SKILL.md 변경이력 표에 v4.0 행 추가 + 메모리 갱신
  - **어디에**: `SKILL.md` §변경이력, `.opal/MEMORY.md` 작업 히스토리
  - **왜**: 추적성·세션 복원
  - **AC**:
    - SKILL.md 변경이력 마지막 행이 v4.0 + 날짜(2026-05-24) + 태스크 008 번호 포함
    - 변경 내용에 R-1~R-7 핵심 변경이 한 줄 요약으로 명시
    - `.opal/MEMORY.md` 작업 히스토리 008 행이 CLOSE 단계에서 완료일시 갱신

## 제약 조건

- **배포 경계 준수**: `~/.opal/` 직접 편집 금지. 항상 프로젝트 소스(`opal/skills/opal-pilot-write-tech/`)를 수정한 뒤 install로 재배포한다. (`opal/.opal/AGENT.md` §금지사항)
- **하네스 SSOT**: 본 태스크는 opwt 스킬 자체만 수정한다. `opal/core/references/opal-harness.md`는 건드리지 않는다.
- **state-tool 사용 의무**: STATE.md 마크다운 직접 편집 금지. 모든 행 상태 변경은 `~/.opal/tools/state-tool/run.sh`로 수행.
- **마이그레이션 정책**: 기존 "순서도" 산출물이 있는 프로젝트는 PLAN 단계에서 "수동 재분류 안내" 정책 결정. v4 install 후 사용자가 결정.
- **변경이력 의무**: opwt SKILL.md 수정 시 변경이력 표에 일시·태스크 번호 포함 행 추가.
- **에이전트 의존성**: 본 태스크는 `interview` 스킬(`skills/interview/SKILL.md`)을 신규 통합한다. 해당 스킬의 인터페이스가 변경되지 않는 한 호환된다.

## 기술 스택

- Markdown 문서 (`SKILL.md`, `network-guide.md`, `consistency-rules.md`)
- OPAL 스킬 구조 (`opal/skills/opal-pilot-write-tech/`)
- 외부 의존: `skills/interview/SKILL.md` (TASK 단계 통합 대상)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 기획 | app-planning-presentation 캡처 | `/Volumes/Data/AiStudio/workspace/ai-plan-dev/app-planning-presentation/` | 흡수 대상 자료 — 11 슬라이드 + templates/ 3종 |
| D-2 | 설계 | opwt SKILL.md (v3.4) | `opal/skills/opal-pilot-write-tech/SKILL.md` | 수정 대상 — TASK 절 + 커버 범위 + 변경이력 |
| D-3 | 설계 | network-guide.md | `opal/skills/opal-pilot-write-tech/references/network-guide.md` | 수정 대상 — §1 산출물 유형, §2 연결 맵, §5 diagnosis.json, §7-3 워커 프롬프트 |
| D-4 | 설계 | consistency-rules.md | `opal/skills/opal-pilot-write-tech/references/consistency-rules.md` | 수정 대상 — §1 검증 규칙, §7 Tier, §8 외부 참조 |
| D-5 | 설계 | interview 스킬 | `skills/interview/SKILL.md` | 통합 대상 — Step 1/2/3/4 흐름 활용 |
| D-6 | 설계 | opwt 프로젝트 정책 | `opal/.opal/AGENT.md` | 금지사항·검토 기준 — 배포 경계 / 변경이력 의무 / state-tool 의무 |
| D-7 | 설계 | citation-rules.md | `opal/core/references/harness/citation-rules.md` | 산출물 인용 규칙 — TASK/PLAN 단계 모두 적용 |
| D-8 | 설계 | opal-harness-agentic.md | `~/.opal/references/opal-harness-agentic.md` | agentic 모드 운영 — AGENTIC-LOG, Gate 루핑, 강화 검토 |
