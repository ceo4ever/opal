# PLAN: opwt 산출물 체계 v4 — interview 통합 + PRD 8섹션 + 시나리오·화면 흐름도 + WBS 제거

> 작성일: 2026-05-24
> 입력: TASK.md (R-1~R-8 + 확정 방향 §1~§8)
> 출력: PLAN.md
> 작성자: opal-plan-agent (op-task-plan 스킬)

---

## 1. 현황 조사

### 1.1 참조 문서 (PLAN 작성 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 기획 | app-planning-presentation 캡처 | `/Volumes/Data/AiStudio/workspace/ai-plan-dev/app-planning-presentation/` | 흡수 대상 자료 — 11 슬라이드 + templates/ 3종 (TASK.md `관련 문서` D-1) |
| D-2 | 설계 | opwt SKILL.md (v3.4) | `opal/skills/opal-pilot-write-tech/SKILL.md` | 수정 대상 1 — TASK 절(L56-82) + 커버 범위(L33-39) + 변경이력(L363-388) |
| D-3 | 설계 | network-guide.md | `opal/skills/opal-pilot-write-tech/references/network-guide.md` | 수정 대상 2 — §1 산출물 유형(L7-54), §2 연결 맵(L57-135), §5 diagnosis.json(L197-253), §7-3 워커 프롬프트(L382-440) |
| D-4 | 설계 | consistency-rules.md | `opal/skills/opal-pilot-write-tech/references/consistency-rules.md` | 수정 대상 3 — §1 검증 규칙(L7-75), §7 Tier(L246-277), §8 외부 참조(L289-339) |
| D-5 | 설계 | interview 스킬 | `opal/skills/interview/SKILL.md` | 통합 대상 — Step 1~4 흐름(L23-61) + 질문 유형 템플릿(L65-89) + 한 번 최대 4문 원칙(L36-38) |
| D-6 | 설계 | opwt 프로젝트 정책 | `.opal/AGENT.md` | 금지사항 — 배포 경계(L60) / 변경이력 의무(L42 + L61) / state-tool 의무(L43 + L65) / 사용자 승인 없는 코드 변경 금지(L64) |
| D-7 | 설계 | citation-rules.md | `opal/core/references/harness/citation-rules.md` | 인용 규칙 — 비개발 트랙 매트릭스(§1.5), 인라인 인용 `(→ D-N §N)` 포맷(§3.2), [MUST] 토큰 포맷(§2.4) |
| D-8 | 설계 | opal-harness-agentic.md | `~/.opal/references/opal-harness-agentic.md` | agentic 모드 운영 — AGENTIC-LOG, Gate 루핑, 강화 검토 (TASK.md `관련 문서` D-8) |
| D-9 | 설계 | docs/CONVENTIONS.md | `docs/CONVENTIONS.md` | 프로젝트 컨벤션 — Guards / 변경이력 / 배포 경계 / kebab-case / YAML frontmatter |

> 인용 형식: `opal/core/references/harness/citation-rules.md` §3.1 참조. 본 태스크는 **비개발 트랙**(스킬 .md 문서 수정)이므로 §1.5에 따라 "문서 + 설계 산출물" 근거가 필수.

#### [MUST] 인용 (재해석 금지 제약)

- `[MUST]` `opal/core/references/opal-harness.md` §1 Guards: "사용자가 명시적으로 '승인', '진행해', '구현해' 등의 실행 허가를 내릴 때까지 코드를 작성하거나 파일을 생성/수정하지 않는다." → PLAN 단계는 산출물 문서(.md) 작성만 허용. 대상 3개 파일 본체 수정은 EXECUTE 단계에서 워커 디스패치를 통해 수행.
- `[MUST]` `opal/core/references/opal-harness.md` §1 Guards: "커밋은 사용자가 명시적으로 요청할 때만 수행한다." → PLAN/EXECUTE 모두 git commit 금지.
- `[MUST]` `.opal/AGENT.md` §금지사항: "`~/.opal/` 직접 편집 금지 — 항상 프로젝트 소스를 수정한 후 install로 배포한다." → EXECUTE Step에서 수정 대상 경로는 `opal/skills/opal-pilot-write-tech/` 만 허용.
- `[MUST]` `.opal/AGENT.md` §금지사항: "STATE.md 마크다운 직접 편집 금지 — `state-tool`만 사용." → PLAN/EXECUTE 단계 모두 STATE.md 직접 편집 금지, state-tool 호출만 허용.
- `[MUST]` `docs/CONVENTIONS.md` §변경이력 작성 의무: "스킬·에이전트·참조 문서를 변경하면 '## 변경이력' 표에 행을 추가한다. 일시는 `YYYY-MM-DD HH:mm` (KST), 버전은 semver, 변경내용은 태스크 번호를 괄호로 포함." → SKILL.md 변경이력 v4.0 행에 `2026-05-24 HH:mm` + `(008)` 형식 적용.
- `[MUST]` `docs/CONVENTIONS.md` §언어 규칙: "문서 본문 한국어 (기술 용어는 영어 병기) / 코드/변수/필드명 English / 파일·폴더 kebab-case." → 신규 추가 섹션·다이어그램 파일명·테이블 컬럼명 일관 적용.

### 1.2 관련 파일

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| `opal/skills/opal-pilot-write-tech/SKILL.md` | opwt 본체 — 커버 범위/TASK 절/변경이력 | 수정 | `opal/skills/opal-pilot-write-tech/SKILL.md:33-39` (커버 범위), `:56-82` (TASK 절), `:363-388` (변경이력) |
| `opal/skills/opal-pilot-write-tech/references/network-guide.md` | 산출물 유형·연결 맵·diagnosis 스키마·워커 프롬프트 | 수정 | `opal/skills/opal-pilot-write-tech/references/network-guide.md:7-54` (§1), `:57-135` (§2), `:197-253` (§5), `:382-440` (§7-3) |
| `opal/skills/opal-pilot-write-tech/references/consistency-rules.md` | 정합성 검증 규칙 | 수정 | `opal/skills/opal-pilot-write-tech/references/consistency-rules.md:7-75` (§1), `:246-277` (§7), `:289-339` (§8) |
| `skills/interview/SKILL.md` | interview 스킬 — opwt TASK에서 호출만 (수정 대상 아님) | 변경 없음 | `skills/interview/SKILL.md:23-61` (Step 1~4) |
| `.opal/MEMORY.md` | 프로젝트 작업 히스토리 | 수정 (CLOSE 단계에서) | - |

### 1.3 현재 상태 요약 (Before)

opwt **v3.4** (2026-05-09 18:30 기준, `D-2 §변경이력`):

- **산출물 9종**: 필수 4종(PRD/TRD/정책서/IA) + 선택 4종(기능도/순서도/운영정책서/매뉴얼) + 프로젝트 특화(외부 API 명세서) + **PMO(개발 WBS)** (→ D-2 §커버 범위)
- **PRD 워커 프롬프트** (§7-3): 6섹션 — 제품 목표 / Non-goals / 타깃 유저 / 핵심 요구사항(Must/Should/Nice-to-have) / Acceptance Criteria / Open Questions (→ D-3 §7-3 L408-417)
- **TASK 절**: 4개 확인 항목 — 모드 결정 / 대상 문서 유형 / 외부 참조 / 산출물 저장 경로 (→ D-2 §TASK 단계 L60-65)
- **시각화**: IA만 Mermaid 사이트맵 필수 출력. 시나리오·정책서·TRD는 텍스트 위주 (→ D-3 §9 IA 형식)
- **정합성 검증 §1**: PRD↔TRD / PRD↔정책서 / PRD↔IA / TRD↔IA / 정책서↔IA + 외부 API명세서 3쌍 = 8쌍 (→ D-4 §1)
- **Tier 분류 §7**: Tier 1~5 (외부 참조 포함) — 5단계 (→ D-4 §7 L262-266)
- **§8 외부 참조 검증**: 와이어프레임↔IA / 와이어프레임↔정책서 / ERD↔정책서·TRD / API명세서↔TRD·정책서 = 7쌍 (→ D-4 §8)

### 1.4 변경 후 상태 (After) — Before/After 매핑

| # | 영역 | v3.4 (Before) | v4.0 (After) | 영향 R-N |
|---|------|--------------|-------------|---------|
| 1 | 산출물 종수 | 9종 (PMO 포함) | **10종** (PMO 제거, 화면 흐름도·시나리오 다이어그램 신설) | R-2, R-3, R-5 |
| 2 | PRD 섹션 수 | 6섹션 | **8섹션** (배경 및 목표 / 주요 기능 / 요구사항 명세 신규) | R-1 |
| 3 | "순서도" 산출물 | 정의 모호한 선택 산출물 | **"기능 시나리오 다이어그램"** 재정의 (flowchart+sequence+state 3종) | R-2 |
| 4 | 화면 흐름도 | 없음 | **신규** 선택 산출물 (화면 단위 Mermaid flowchart) | R-3 |
| 5 | Mermaid 표준 | IA만 필수 (§9) | **시각화 표준 절 신설** — 산출물별 필수/권장 매트릭스 | R-4 |
| 6 | PMO·WBS | 커버 범위 포함, §1·§2·§5·§7 분산 기재 | **전체 제거** (커버 범위·연결맵·diagnosis enum·Tier에서 삭제) | R-5 |
| 7 | TASK 절 | 4개 항목 PM 직접 수동 입력 | **interview 스킬 호출** (Round 1/2/3) + 신규 TASK.md 섹션 3종 | R-6 |
| 8 | 정합성 검증 쌍 | 8쌍 (§1) + 7쌍 (§8) = 15쌍 | **+4쌍 추가** (시나리오↔정책서·TRD·IA + 화면 흐름도↔IA) + 외부 참조에 화면 흐름도↔와이어프레임 1쌍 추가 | R-7 |
| 9 | 변경이력 | v3.4 (2026-05-09 18:30) | **v4.0 (2026-05-24 HH:mm) 행 추가** (008) | R-8 |

### 1.5 영향 범위

- **직접 변경**: 3개 파일 (SKILL.md + network-guide.md + consistency-rules.md) — opal/skills/opal-pilot-write-tech/ 하위 전부
- **간접 영향**: `~/.opal/skills/opal-pilot-write-tech/` 배포본 (EXECUTE 후 install로 재배포 필요 — 본 태스크 EXECUTE 범위 외, 사용자 검토 후 별도 install 수행)
- **외부 의존**: `skills/interview/SKILL.md` (변경 없음, 호출 인터페이스만 사용)
- **마이그레이션 대상**: 기존 프로젝트의 "순서도" 산출물 — "수동 재분류 안내" 정책 (TASK.md §제약 조건, M-4 참조)
- **하네스 SSOT**: `opal/core/references/opal-harness.md` 미수정 (TASK.md §제약 조건)

---

## 2. 구현 계획

### 2.1 파일 변경 계획

#### 신규 생성

| # | 파일 경로 | 역할 | 근거 |
|---|----------|------|------|
| - | (없음 — 모든 변경은 기존 3개 파일 내부 수정) | - | - |

#### 수정

| # | 파일 경로 | 변경 내용 | 근거 |
|---|----------|----------|------|
| F-1 | `opal/skills/opal-pilot-write-tech/SKILL.md` | (1) 커버 범위에서 PMO·개발 WBS 제거 + 선택 5종으로 갱신 (2) TASK 절을 interview 호출 + 3라운드 + 4-Step 구조로 재구성 (3) 변경이력 v4.0 행 추가 | (→ D-2 §커버 범위 L33-39 / §TASK 단계 L56-82 / §변경이력 L363-388) |
| F-2 | `opal/skills/opal-pilot-write-tech/references/network-guide.md` | (1) §1 산출물 유형 — "순서도"→"기능 시나리오 다이어그램" 재정의, "화면 흐름도" 행 추가, PMO 섹션 + Level 분해 표 제거 (2) §2 연결 맵 — 시나리오 3쌍·화면 흐름도 2쌍 추가, WBS 관련 행 제거, §2 참조 항목 테이블 갱신 (3) §5 diagnosis.json `type` enum — "개발 WBS" 제거 + "기능 시나리오 다이어그램"·"화면 흐름도" 추가 (4) §7-3 워커 프롬프트 — PRD 8섹션 표 교체, 기능 시나리오 다이어그램·화면 흐름도 작성 가이드 신설 (5) 신규 §11 "Mermaid 시각화 표준" 절 추가 (산출물별 필수/권장 매트릭스) | (→ D-3 §1 L7-54 / §2 L57-135 / §5 L197-253 / §7-3 L382-440 / TASK.md §1·§2·§3·§4·§5) |
| F-3 | `opal/skills/opal-pilot-write-tech/references/consistency-rules.md` | (1) §1 — "기능 시나리오 다이어그램 ↔ 정책서/TRD/IA" 3쌍 추가 + "화면 흐름도 ↔ IA" 1쌍 추가 (각 쌍 양방향 체크 ≥2개) (2) §7 Tier — WBS 행 제거 + 시나리오·화면 흐름도를 적절한 Tier에 배치 (3) §8 외부 참조 — "화면 흐름도 ↔ 와이어프레임" 쌍 추가 | (→ D-4 §1 L7-75 / §7 L246-277 / §8 L289-339 / TASK.md R-7 AC) |
| F-4 | `.opal/MEMORY.md` | 작업 히스토리 008 행에 CLOSE 완료일시 갱신 (CLOSE 단계에서 자동) | (→ TASK.md R-8 AC) |

#### 삭제

| # | 파일 경로 | 사유 |
|---|----------|------|
| - | (없음 — 섹션 내부 제거는 수정에 해당) | - |

### 2.2 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | F-1 SKILL.md 3개 영역 수정 | `opal/skills/opal-pilot-write-tech/SKILL.md` | 중 |
| 2 | F-2-a network-guide.md §1·§2·§5 수정 (산출물 유형·연결맵·diagnosis enum) | `opal/skills/opal-pilot-write-tech/references/network-guide.md` | 중 |
| 3 | F-2-b network-guide.md §7-3 워커 프롬프트 갱신 + §11 Mermaid 표준 신설 | `opal/skills/opal-pilot-write-tech/references/network-guide.md` | 상 |
| 4 | F-3 consistency-rules.md §1·§7·§8 수정 | `opal/skills/opal-pilot-write-tech/references/consistency-rules.md` | 중 |
| 5 | F-4 MEMORY.md 갱신 (CLOSE 단계에서 자동) | `.opal/MEMORY.md` | 하 |

**순서 원칙**:

- 의존 받는 쪽(하위 레이어) 우선 원칙 — 본 태스크는 3개 파일이 상호 독립이므로 의존 순서 제약 약함.
- **단, F-2-a와 F-2-b는 동일 파일이므로 순차** (Phase 그룹핑 §2.4 참조).
- F-1 / F-2 / F-3는 서로 다른 파일 → 병렬 가능.
- F-4(MEMORY 갱신)는 CLOSE 단계의 PM 자동 수행이므로 EXECUTE 체크리스트에서 제외.

### 2.3 핵심 설계 (Decision Log)

#### M-1: PRD 8섹션 순서 — TASK.md 확정 방향 §2 그대로 채택

확정 순서: 개요 → 배경 및 목표 → Non-goals → 타깃 사용자 → 주요 기능 → 요구사항 명세 → Acceptance Criteria → Open Questions (→ D-1 슬라이드, TASK.md §확정 방향 §2)

**근거**:
- TASK.md `§2 PRD 8섹션 표준` 표가 8섹션을 명시한 단일 진실 (→ D-1 § "기획서 4섹션 + 한 페이지 응집" 흡수)
- 기존 PRD 6섹션(제품 목표/Non-goals/타깃 유저/핵심 요구사항/AC/Open Q)을 확장 — "제품 목표"는 "개요"+"배경 및 목표"로 분리, "주요 기능"·"요구사항 명세" 신규 (→ D-3 §7-3 L408-417 비교)
- `[MUST]` 8섹션 명칭이 TASK.md §확정 방향 §2와 정확히 일치해야 R-1 AC 통과 (→ TASK.md R-1 AC 2번 항목)

**EXECUTE 시 적용**: F-2-b Step 3에서 network-guide.md §7-3 PRD 신규 작성 가이드의 6섹션 표를 8섹션 표로 교체. 컬럼은 기존과 동일(섹션명/필수·선택/작성 기준).

#### M-2: 시나리오 다이어그램 파일명 컨벤션

확정: `scenario-{기능명}.md` (→ TASK.md R-2 AC 3번)

**근거**:
- 기존 IA 사이트맵 분리 파일명 `ia-sitemap-{domain}.md` (→ D-3 §9 L637) 와 일관성 유지
- 시나리오는 **기능 단위**이므로 기능명을 식별자로 사용 (TASK.md §확정 방향 §3 "단위 = 기능 단위")
- `docs/CONVENTIONS.md` §파일/폴더: "kebab-case 사용" 적용 → `{기능명}` 자리는 kebab-case로 명시

**EXECUTE 시 적용**: F-2-b Step 3에서 §7-3에 추가될 "기능 시나리오 다이어그램 작성 가이드"의 첫 줄에 파일명 컨벤션 명시 (예: `scenario-checkout.md`, `scenario-member-signup.md`).

#### M-3: 화면 흐름도 vs 시나리오 다이어그램 경계

확정 (TASK.md §확정 방향 §4 마지막 줄 채택):

| 산출물 | 단위 | 표현 대상 |
|--------|------|----------|
| **화면 흐름도** | 화면 단위 | 화면-화면 전환 (네비게이션 중심) |
| **기능 시나리오 다이어그램** | 기능 단위 | 사용자-시스템 상호작용 + 상태 전이 |

**근거**:
- TASK.md §확정 방향 §4 "시나리오 다이어그램과 경계 = 화면 흐름도 = **화면 단위**(전환). 시나리오 = **기능 단위**(상호작용·상태)"
- 두 산출물이 모두 Mermaid flowchart를 사용하므로 경계 명문화가 필수 (R-3 AC 4번)

**EXECUTE 시 적용**: F-2-b Step 3에서 §7-3 화면 흐름도 가이드에 경계 박스(`> 시나리오 다이어그램과 경계: ...`) 삽입. F-2-a Step 2에서 §1 선택 산출물 표의 두 산출물 "설명" 컬럼에도 경계 단어 명시("화면 단위" / "기능 단위").

#### M-4: 기존 "순서도" 산출물 마이그레이션 정책

확정: **수동 재분류 안내** (TASK.md §제약 조건 채택)

**근거**:
- TASK.md §제약 조건: "기존 '순서도' 산출물이 있는 프로젝트는 PLAN 단계에서 '수동 재분류 안내' 정책 결정. v4 install 후 사용자가 결정."
- v4 자동 변환 도구 신설은 본 태스크 범위 외 (R-1~R-8 어디에도 명시 없음)
- opwt는 프로젝트 의존 하드코딩 없이 동작해야 함 — 프로젝트별 마이그레이션은 사용자 결정 영역 (→ D-6 §도메인 검토)

**EXECUTE 시 적용**: 본 태스크에서는 마이그레이션 가이드를 별도 문서로 작성하지 않는다. 대신 SKILL.md 변경이력 v4.0 행 변경내용에 "기존 '순서도' 산출물은 사용자가 수동 재분류 — 마이그레이션 도구 미제공" 한 줄 명시 (R-8 AC 변경내용 한 줄 요약 항목 활용).

#### M-5: Mermaid 시각화 표준의 "필수 vs 권장" 기준

확정 (TASK.md §확정 방향 §5 그대로 채택):

| 강제 수준 | 산출물 | 다이어그램 유형 |
|----------|--------|-------------|
| **필수** | IA (기존) | flowchart TD 사이트맵 |
| **필수** | 기능 시나리오 다이어그램 (신규) | flowchart + sequence + state 3종 |
| **필수** | 화면 흐름도 (신규) | flowchart |
| **권장** | PRD — 타깃 사용자 | flowchart (사용자 여정) |
| **권장** | TRD — 아키텍처 | graph (구성도) + sequence (호출) |
| **권장** | 정책서 — 상태 변화 | stateDiagram |
| **권장** | 기능도 | graph |

**근거**:
- "필수" = 산출물 자체가 시각화 출력을 핵심 가치로 가짐 (IA·시나리오·화면 흐름도는 시각화 없으면 산출물 의미 약함)
- "권장" = 시각화가 보조 수단인 산출물 (PRD/TRD/정책서/기능도는 텍스트가 본체, 시각화는 명확성 강화 수단)
- TASK.md R-4 AC 2·3번이 이 분류를 명시 ("필수: IA / 시나리오 / 화면 흐름도" + "권장: PRD/TRD/정책서/기능도")

**EXECUTE 시 적용**: F-2-b Step 3에서 network-guide.md 신규 §11(또는 §9 직후 §10) "Mermaid 시각화 표준" 절 추가, 위 표를 그대로 기재.

#### M-6: WBS 제거 시 PMO 그룹 자체 폐기

확정: **PMO 그룹 자체 폐기** (TASK.md §확정 방향 §6 채택 — "PMO 제거")

**근거**:
- TASK.md `§확정 방향 §6 WBS 제거` 절이 "SKILL.md 커버 범위에서 'PMO·개발 WBS' 섹션 제거"를 명시 — PMO 자체를 폐기 (개발 WBS만 빠지는 게 아님)
- network-guide.md §1 PMO 섹션 자체 제거 (Level 분해 표 포함) — TASK.md R-5 AC 2번 "§1 PMO 섹션 행 0건"
- "빈 자리"로 남기지 않음 — 향후 기획 WBS 등이 추가될 예정이라는 v3.4의 가능성 언급(→ D-3 §1 L40)도 제거. 향후 재도입 시 별도 태스크에서 신설

**EXECUTE 시 적용**: F-1 Step 1에서 SKILL.md 커버 범위 4번째 행("PMO: 개발 WBS ...") 삭제. F-2-a Step 2에서 network-guide.md §1 "### PMO" 헤더부터 "Level 분해 구조" 표 끝까지 통째로 삭제 (L37-54 범위).

#### M-7: interview 스킬 통합 시 Round 3 트리거 조건

확정 (TASK.md §확정 방향 §7 채택):

- Round 1: 모드(작성/수정/분석) + 표준 산출물 선택 + 조건부 외부 API
- Round 2: 부가 산출물 사전 필터 + 외부 참조(docs/) 자동 스캔 확인
- **Round 3 (PRD 5섹션, PRD 작성 모드 한정)**: PRD 입력 컨텍스트(개요/배경/타깃/기능/제약) 수집 — **PRD가 표준 산출물에 포함된 경우에만 활성**

**근거**:
- TASK.md §확정 방향 §7 "라운드 구성" 행: "Round 3 (PRD 5섹션, **PRD 작성 모드 한정**)"
- PRD 미작성 모드(예: TRD만 작성하는 경우)에서 Round 3을 호출하면 사용자에게 불필요한 질문 발생 — interview 원칙 "라운드 최소화 (2~3라운드 이내)" 위배 (→ D-5 §인터뷰 원칙 5)
- `[MUST]` Round 3 호출 조건: Round 1 답변에서 "표준 산출물 선택" 항목에 PRD가 체크된 경우에만 활성

**EXECUTE 시 적용**: F-1 Step 1에서 SKILL.md TASK 절 재구성 시 Round 3 호출 조건을 "PRD가 Round 1에서 선택된 경우" 명시한다. Round 3 라운드 설계 표(질문 수·옵션 형식·multiSelect 여부)를 SKILL.md에 포함.

#### M-8: docs/ 갱신 필요 여부 판단

확정: **docs/ 갱신 불필요** — 본 태스크는 opwt 스킬 내부 산출물 체계 변경. `docs/PROJECT.md`·`docs/ARCHITECTURE.md`·`docs/CONVENTIONS.md` 모두 영향 없음

**근거**:
- `docs/PROJECT.md`: 프로젝트 전체 개요 — opwt 스킬 내부 산출물 체계는 프로젝트 문서 테이블에 영향 없음
- `docs/ARCHITECTURE.md`: 시스템 아키텍처 — opwt 산출물 종수 변화는 시스템 컴포넌트가 아니므로 영향 없음
- `docs/CONVENTIONS.md`: 코드 컨벤션 — 본 태스크는 컨벤션 변경 없이 컨벤션 준수 산출물 작성

**EXECUTE 시 적용**: docs/ 갱신 Step 추가 없음 (워커 가이드 §"docs/ 갱신 Step"에 따른 판단 결과 — 영향 없음으로 Step 미추가).

---

## 3. 실행 체크리스트

> 총 4개 Step | Phase 3개
>
> | Phase | Step | 실행 | 비고 |
> |-------|------|------|------|
> | 1     | 1, 2, 4 | 병렬 | 서로 다른 파일 — F-1(SKILL.md) / F-2-a(network-guide.md §1·§2·§5) / F-3(consistency-rules.md) 독립 |
> | 2     | 3    | 순차 | Step 2와 동일 파일(network-guide.md) → 충돌 방지 위해 Step 2 완료 후 |
> | 3     | (없음 — CLOSE 자동) | - | MEMORY 갱신은 CLOSE 단계 PM 자동 수행 |

### Step 1: SKILL.md 3개 영역 수정 (커버 범위 + TASK 절 + 변경이력)

- [ ] 완료
- **파일**: `opal/skills/opal-pilot-write-tech/SKILL.md`
- **agent**: opal-task-agent (범용 — 스킬 문서 작업)
- **작업 내용**:
  1. **커버 범위 갱신** (L33-39):
     - 기존 "PMO: 개발 WBS ..." 행 **삭제**
     - 선택 4종 → 선택 5종으로 갱신 (기존 "기능도, 순서도, 운영 정책서, 서비스 매뉴얼" → "기능도, **기능 시나리오 다이어그램**, **화면 흐름도**, 운영 정책서, 서비스 매뉴얼")
     - "순서 체인" 행 유지 (변경 없음 — PRD→TRD→정책서→IA는 v4에서도 유효)
  2. **TASK 절 재구성** (L56-82, "TASK 단계" 헤더부터 "완료 처리" 직전까지):
     - 기존 4개 확인 항목(모드/대상 문서/외부 참조/저장 경로) **삭제**
     - 신규 구조: `### interview 스킬 호출` 헤더 + 스킬 탐색 경로 2개 명시 (`{프로젝트}/.opal/skills/interview/` → `~/.opal/skills/interview/`)
     - `### Round 1/2/3 라운드 설계` 표 신설 (질문 수·옵션 형식·multiSelect 여부 컬럼)
     - `### Step 1 — opwt 도메인 옵션 구성` 가이드: (a) 외부 API 신호 탐지(키워드/도메인) → Q3 조건부 노출 (b) 부가 산출물 신호 탐지 → Q4 옵션 필터 (c) docs/ 스캔 → Q5 외부 참조 자동 감지
     - `### Step 4 — 결과 기록` 가이드: TASK.md 신규 섹션 양식 — "산출물 결정" + "외부 참조" + "PRD 입력 컨텍스트(PRD 작성 모드 한정)"
     - **M-7 적용**: Round 3 호출 조건을 "PRD가 Round 1 답변에서 표준 산출물로 선택된 경우" 명시
     - 기존 "완료 처리" 절(TASK.md 작성·STATE.md 초기화·State Gate) **유지** — interview 결과 → TASK.md 작성 흐름
  3. **변경이력 v4.0 행 추가** (L388 다음 줄):
     - 형식: `| v4.0 | 2026-05-24 HH:mm | 산출물 체계 v4 — interview 통합(TASK 절 재구성) + PRD 8섹션 표준 + 기능 시나리오 다이어그램 재정의 + 화면 흐름도 신설 + Mermaid 시각화 표준 + PMO/WBS 제거. 기존 '순서도' 산출물은 사용자가 수동 재분류 (008) |`
     - **[MUST] D-9 §변경이력 작성 의무**: 일시 `YYYY-MM-DD HH:mm` (KST), 버전 semver, 태스크 번호 `(008)` 괄호 포함
     - **[MUST] HH:mm 치환**: 워커는 위 형식의 `HH:mm` 플레이스홀더를 작업 완료 시점 KST 시각으로 반드시 치환한다. 치환 방법: `node ~/.opal/tools/date/date.js hhmm` 호출 결과를 사용하거나, 환경에서 KST 시각을 직접 취득. **리터럴 'HH:mm'을 그대로 남기지 않는다.**
- **완료 기준**:
  - SKILL.md 커버 범위 섹션에 "PMO" / "개발 WBS" 문자열 0건 (R-5 AC 1번)
  - 선택 산출물에 "기능 시나리오 다이어그램" / "화면 흐름도" 명칭 등장
  - TASK 절에 "interview 스킬" 호출 문구 + 탐색 경로 2개 명시 (R-6 AC 1번)
  - Round 1/2/3 표 존재 (R-6 AC 2번)
  - 변경이력 마지막 행이 v4.0 + 2026-05-24 + (008) (R-8 AC 1번)
  - 변경 내용 한 줄 요약에 R-1~R-7 핵심 변경 명시 (R-8 AC 2번)
- **테스트**:
  - `grep -c "PMO\|개발 WBS" opal/skills/opal-pilot-write-tech/SKILL.md` 결과 0
  - `grep -c "기능 시나리오 다이어그램\|화면 흐름도" opal/skills/opal-pilot-write-tech/SKILL.md` ≥2
  - `grep "v4.0" opal/skills/opal-pilot-write-tech/SKILL.md` 결과 1행 (변경이력 행)
  - `grep -v "HH:mm" opal/skills/opal-pilot-write-tech/SKILL.md | grep "v4.0"` 결과 1행 (HH:mm 치환 확인)
  - `grep "interview" opal/skills/opal-pilot-write-tech/SKILL.md` ≥3 (탐색 경로 2개 + 호출 안내)
  - `grep -c "TASK 전용 확인 항목\|모드 결정$\|대상 문서 유형\|외부 참조 여부\|산출물 저장 경로" opal/skills/opal-pilot-write-tech/SKILL.md` 결과 0 (기존 4개 항목 텍스트 제거 검증 — R-6 AC 5번 매핑)
- **의존**: 없음

### Step 2: network-guide.md §1·§2·§5 수정 (산출물 유형 + 연결 맵 + diagnosis enum)

- [ ] 완료
- **파일**: `opal/skills/opal-pilot-write-tech/references/network-guide.md`
- **agent**: opal-task-agent
- **작업 내용**:
  1. **§1 산출물 유형 정의 갱신** (L7-54):
     - 선택 4종 표(L19-26)에서 "순서도" 행을 "**기능 시나리오 다이어그램**" 으로 명칭 변경 + 설명을 "기능 단위 사용자-시스템 상호작용·상태 전이. Mermaid flowchart + sequenceDiagram + stateDiagram-v2 3종 통합" 으로 갱신
     - 선택 4종 → 선택 5종 — "**화면 흐름도**" 행 신설 (설명: "화면 단위 네비게이션 전환. Mermaid flowchart 단일. IA·와이어프레임과 연결.")
     - **§1 "### PMO" 헤더부터 "개발 WBS Level 분해 구조" 표 끝까지(L37-54) 통째로 삭제** (M-6 적용)
  2. **§2 논리적 연결 맵 갱신** (L57-135):
     - "개발 WBS ↔ IA" / "개발 WBS ← PRD" / "개발 WBS ← TRD" 양방향 참조 블록(L102-110) **삭제**
     - 신규 양방향 참조 블록 추가:
       - "기능 시나리오 다이어그램 ↔ 정책서" — 예외/규칙 정합 + 정책 결정 → 시나리오 재검증
       - "기능 시나리오 다이어그램 ↔ TRD" — API 시퀀스 / 통신 흐름 정합
       - "기능 시나리오 다이어그램 ↔ IA" — 기능 동작 / 화면 진입 정합
       - "화면 흐름도 ↔ IA" — 메뉴 구조 vs 전환 흐름 정합
       - "화면 흐름도 ↔ 와이어프레임 (외부 참조)" — 화면 전환 노드 vs 와이어프레임 화면 ID 정합
     - "각 연결의 참조 항목" 테이블(L121-135)에서 WBS 관련 3행(L133-135) **삭제** + 시나리오·화면 흐름도 행 추가
  3. **§5 diagnosis.json 스키마 갱신** (L197-253):
     - `documents[].type` enum에서 "개발 WBS" 제거 (L217)
     - enum에 "기능 시나리오 다이어그램" / "화면 흐름도" 추가
     - 변경 후 enum: `"PRD | TRD | 서비스 정책서 | IA | 기능도 | 기능 시나리오 다이어그램 | 화면 흐름도 | 운영 정책서 | 서비스 매뉴얼 | 외부 API 명세서"`
- **완료 기준**:
  - §1 PMO 섹션 / Level 분해 표 0건 (R-5 AC 2번)
  - §2 "개발 WBS" 문자열 0건 (R-5 AC 3·4번)
  - §5 `type` enum에 "개발 WBS" 0건 + "기능 시나리오 다이어그램" + "화면 흐름도" 추가 (R-5 AC 5번)
  - §1 선택 산출물 표에 "기능 시나리오 다이어그램" 행 존재 + 설명에 flowchart+sequence+state 3종 명시 (R-2 AC 1번)
  - §1 선택 산출물 표에 "화면 흐름도" 행 존재 + 설명에 Mermaid flowchart + 화면 단위 명시 (R-3 AC 1번)
  - §2 연결 맵에 "화면 흐름도 ↔ IA" + "화면 흐름도 ↔ 와이어프레임" 추가 (R-3 AC 2번)
- **테스트**:
  - `grep -c "개발 WBS\|PMO" opal/skills/opal-pilot-write-tech/references/network-guide.md` 결과 0
  - `grep -c "기능 시나리오 다이어그램" opal/skills/opal-pilot-write-tech/references/network-guide.md` ≥3 (§1·§2·§5)
  - `grep -c "화면 흐름도" opal/skills/opal-pilot-write-tech/references/network-guide.md` ≥3 (§1·§2·§5)
- **의존**: 없음

### Step 3: network-guide.md §7-3 워커 프롬프트 + §11 Mermaid 시각화 표준 신설

- [ ] 완료
- **파일**: `opal/skills/opal-pilot-write-tech/references/network-guide.md`
- **agent**: opal-task-agent
- **작업 내용**:
  1. **§7-3 신규 작성 가이드 PRD 섹션 교체** (L408-417):
     - 기존 PRD 6섹션 표 **전체 삭제** → 신규 8섹션 표로 교체
     - **헤더 문구 유지**: 기존 "**PRD 유형의 경우, 아래 섹션을 반드시 포함한다:**" 문구는 그대로 유지 (Step 3 테스트 grep "PRD 유형의 경우" 안정성 확보). 변경하려면 테스트 grep 패턴도 동시 갱신.
     - 신규 8섹션 표 (M-1 확정, TASK.md §확정 방향 §2):

       | 섹션 | 필수/선택 | 작성 기준 |
       |------|----------|-----------|
       | 1. 개요 | 필수 | 작성일/작성자/버전 + 프로젝트 한 줄 정의 |
       | 2. 배경 및 목표 | 필수 | 시장 문제·경쟁 환경·기존 솔루션 한계 + SMART 목표 (비즈니스 vs 사용자, 단기·장기) |
       | 3. Non-goals | 필수 | 이번 버전 명시적 제외 범위 |
       | 4. 타깃 사용자 | 필수 | **인구통계학적**(연령/성별/직업/소득/지역) + **행동·심리적**(관심사/라이프스타일/기술 활용도/소비/니즈·페인) + User Stories(`As a {역할}, I want {목적}, so that {이유}`) + Mermaid 사용자 여정 권장 |
       | 5. 주요 기능 | 필수 | 핵심 가치 제안 / 차별점 / Must·Should·Nice-to-have 분류 + MVP 표시 + 향후 예정 |
       | 6. 요구사항 명세 | 필수 | **기능적 요구사항 테이블** (FR-XXX/제목/설명/우선순위/의존성) + 비기능적 요구사항 (성능/보안/확장성, TRD와 중복 시 PRD 요약·TRD SSOT) |
       | 7. Acceptance Criteria | 필수 | GIVEN/WHEN/THEN, 핵심 Must 기능당 최소 1개 |
       | 8. Open Questions | 필수 | 미결 사항. 없으면 "없음" 명시 |

     - PRD 섹션 표 아래에 **작성 원칙** 박스 추가 (한 페이지 응집 / 간결·명확 / 모호 표현 금지(예: "빠르게"→"응답 3초 이내") / 시각적 요소 권장)
     - TRD 섹션 표(L419-427)는 변경 없음 — v4 범위 외
  2. **§7-3 기능 시나리오 다이어그램 신규 가이드 추가** (TRD 가이드 직후):
     - 헤더: `**기능 시나리오 다이어그램 신규 작성 시 필수 섹션:**`
     - 파일명 컨벤션 명시: `scenario-{기능명}.md` (M-2 적용)
     - 필수 섹션 6개 (TASK.md §확정 방향 §3 채택):
       1. 시나리오 개요
       2. 정상 경로 (Mermaid `flowchart TD`)
       3. 시스템 통신 (Mermaid `sequenceDiagram` — Client–API 경계 명시, `sequenceNumbers` 활성화)
       4. 상태 전이 (Mermaid `stateDiagram-v2`)
       5. 예외·실패 케이스
       6. 연관 정책서·TRD·IA id (양방향 연결 명시)
     - Mermaid 규칙: `sequenceNumbers` / `box`·`rect` 도메인 경계 / `alt/else/end` 분기 / `loop/end` 반복
  3. **§7-3 화면 흐름도 신규 가이드 추가** (시나리오 가이드 직후):
     - 헤더: `**화면 흐름도 신규 작성 시 필수 섹션:**`
     - 단위: 화면 단위 (네비게이션 중심)
     - 표기법: Mermaid `flowchart` 단일
     - 필수 섹션 6개 (TASK.md §확정 방향 §4 채택):
       1. 시작점
       2. 화면 노드 + 전환 화살표
       3. 분기·조건
       4. 종료점
       5. 화면 그룹화
       6. 연관 IA 메뉴 id
     - **경계 박스** (M-3 적용): "> 시나리오 다이어그램과 경계: 화면 흐름도 = **화면 단위**(전환). 시나리오 = **기능 단위**(상호작용·상태)."
  4. **신규 §11 "Mermaid 시각화 표준" 절 추가** (§10 외부 참조 산출물 다음):
     - 표 헤더: `| 산출물 | 시각화 강제 수준 | 다이어그램 유형 |`
     - 표 본문 (M-5 확정, TASK.md §확정 방향 §5 그대로 채택 — 7행):
       - IA / 필수 / `flowchart TD` 사이트맵
       - 기능 시나리오 다이어그램 / 필수 / flowchart + sequence + state 3종
       - 화면 흐름도 / 필수 / flowchart
       - PRD — 타깃 사용자 / 권장 / flowchart (사용자 여정)
       - TRD — 아키텍처 / 권장 / graph (구성도) + sequence (호출)
       - 정책서 — 상태 변화 / 권장 / stateDiagram
       - 기능도 / 권장 / graph
     - 표 아래 안내문: "**필수**는 산출물 자체 구성요소(없으면 산출물 부적합). **권장**은 명확성·이해도 강화를 위한 시각화."
- **완료 기준**:
  - §7-3 PRD 섹션 표가 8행 + 8섹션 명칭이 TASK.md §확정 방향 §2와 일치 (R-1 AC 1·2번)
  - 타깃 사용자 행에 "인구통계학적 + 행동·심리적" 가이드 명시 (R-1 AC 3번)
  - 요구사항 명세 행에 "기능적 요구사항 테이블 (FR-XXX 형식)" 가이드 명시 (R-1 AC 4번)
  - 작성 원칙 박스에 "한 페이지 응집 / 간결 / 모호 금지" 명시 (R-1 AC 5번)
  - 기능 시나리오 다이어그램 가이드 — 필수 섹션 6개 + Mermaid 작성 규칙 명시 (R-2 AC 2번)
  - 파일명 컨벤션 `scenario-{기능명}.md` 명시 (R-2 AC 3번)
  - 화면 흐름도 가이드 — 필수 섹션 6개 명시 (R-3 AC 3번)
  - 시나리오 다이어그램과 경계 박스 명시 (R-3 AC 4번)
  - §11 Mermaid 시각화 표준 표 7행 — 필수 3종(IA/시나리오/화면 흐름도) + 권장 4종(PRD/TRD/정책서/기능도) (R-4 AC 1·2·3·4번)
- **테스트**:
  - `grep -A 12 "PRD 유형의 경우" opal/skills/opal-pilot-write-tech/references/network-guide.md | grep -c "필수"` ≥8 (8섹션 모두 필수). **헤더 "PRD 유형의 경우, 아래 섹션을 반드시 포함한다:" 문구가 유지되어 있어야 매핑됨 — Step 3 작업 내용 1번 헤더 유지 가이드 참조**
  - `grep -c "1\. 개요\|2\. 배경 및 목표\|3\. Non-goals\|4\. 타깃 사용자\|5\. 주요 기능\|6\. 요구사항 명세\|7\. Acceptance Criteria\|8\. Open Questions" opal/skills/opal-pilot-write-tech/references/network-guide.md` ≥8 (8섹션 명칭 직접 검증 — 헤더 문구 의존 없음)
  - `grep "scenario-{기능명}" opal/skills/opal-pilot-write-tech/references/network-guide.md` 결과 1행
  - `grep "Mermaid 시각화 표준\|시각화 강제 수준" opal/skills/opal-pilot-write-tech/references/network-guide.md` ≥1
- **의존**: Step 2 (동일 파일이므로 충돌 방지를 위해 Step 2 완료 후 진행)

### Step 4: consistency-rules.md §1·§7·§8 수정

- [ ] 완료
- **파일**: `opal/skills/opal-pilot-write-tech/references/consistency-rules.md`
- **agent**: opal-task-agent
- **작업 내용**:
  1. **§1 유형 간 검증 — 신규 4쌍 추가** (외부 API 명세서 ↔ IA 절(L68-75) 직후):
     - "### 기능 시나리오 다이어그램 ↔ 서비스 정책서" — 양방향 체크 ≥2개 (예: 시나리오의 예외 분기가 정책서 규칙과 일치 / 정책서 규칙이 시나리오 분기에 반영)
     - "### 기능 시나리오 다이어그램 ↔ TRD" — 양방향 체크 ≥2개 (예: 시나리오 sequenceDiagram 호출이 TRD API 명세와 일치 / TRD 보안 요구사항이 시나리오 인증 분기에 반영)
     - "### 기능 시나리오 다이어그램 ↔ IA" — 양방향 체크 ≥2개 (예: 시나리오 화면 진입점이 IA 메뉴 id와 일치 / IA 기능 정의가 시나리오 정상 경로에 반영)
     - "### 화면 흐름도 ↔ IA" — 양방향 체크 ≥2개 (예: 화면 흐름도 화면 노드가 IA 메뉴 id와 1:1 매핑 / IA depth 구조가 화면 흐름도 그룹화와 정합)
  2. **§7 Tier 분류 갱신** (L262-266):
     - **Tier 1 (필수)**: PRD ↔ TRD, PRD ↔ IA (변경 없음)
     - **Tier 2 (중요)**: PRD ↔ 서비스 정책서, TRD ↔ IA (변경 없음)
     - **Tier 3 (선택)**: 서비스 정책서 ↔ IA, 유형 내 검증, **+ 기능 시나리오 다이어그램 ↔ 정책서/TRD/IA** (시나리오 산출물 존재 시), **+ 화면 흐름도 ↔ IA** (화면 흐름도 산출물 존재 시)
     - **Tier 4 (외부 API)**: (변경 없음)
     - **Tier 5 (외부 참조)**: 와이어프레임↔IA, ERD↔정책서, api-spec↔TRD, **+ 화면 흐름도 ↔ 와이어프레임** (reference_artifacts 존재 시)
     - WBS 관련 행 0건 — 기존에도 WBS는 §7에 명시 없음(검색 결과 0건). 단, 본 태스크에서 신규 진입 차단을 위해 명시적 검증 포함 (R-5 AC 7번)
  3. **§8 외부 참조 산출물 검증 — 신규 쌍 추가** (L289-339):
     - "### 화면 흐름도 ↔ 와이어프레임" 신규 추가 (와이어프레임↔정책서 절 직후 또는 §8 끝)
     - 양방향 체크 ≥2개:
       - 화면 흐름도 화면 노드 → 와이어프레임: 각 화면 노드가 와이어프레임에 대응 화면 존재
       - 와이어프레임 → 화면 흐름도: 와이어프레임의 화면 간 링크가 화면 흐름도 전환 화살표에 반영
- **완료 기준**:
  - §1에 신규 4쌍(시나리오↔정책서/TRD/IA + 화면 흐름도↔IA) 존재, 각 쌍 양방향 체크 ≥2개 (R-7 AC 1번)
  - §7 Tier 분류에 WBS 행 0건 (R-5 AC 7번 / R-7 AC 2번)
  - §7 Tier 3 또는 적절한 Tier에 "시나리오 ↔ 정책서·TRD·IA" + "화면 흐름도 ↔ IA" 존재 (R-7 AC 2번)
  - §8에 "화면 흐름도 ↔ 와이어프레임" 절 존재 (R-7 AC 3번)
- **테스트**:
  - `grep -c "기능 시나리오 다이어그램\|시나리오 ↔" opal/skills/opal-pilot-write-tech/references/consistency-rules.md` ≥4 (§1에 3쌍 + §7에 ≥1행)
  - `grep -c "화면 흐름도" opal/skills/opal-pilot-write-tech/references/consistency-rules.md` ≥3 (§1·§7·§8)
  - `grep -c "WBS\|개발 WBS" opal/skills/opal-pilot-write-tech/references/consistency-rules.md` 결과 0
- **의존**: 없음

---

## 4. QA 체크리스트

### 4.1 기능 테스트 (R-1~R-8 AC 매핑)

#### R-1 PRD 8섹션 표준 도입
- [ ] §7-3 PRD 신규 작성 가이드에 8섹션 표(섹션명/필수·선택/작성 기준 컬럼) 존재
- [ ] 8섹션 명칭이 TASK.md §확정 방향 §2와 정확히 일치 (개요/배경 및 목표/Non-goals/타깃 사용자/주요 기능/요구사항 명세/Acceptance Criteria/Open Questions)
- [ ] 타깃 사용자 섹션에 "인구통계학적 + 행동·심리적" 가이드 명시
- [ ] 요구사항 명세 섹션에 "기능적 요구사항 테이블(FR-XXX 형식)" 가이드 명시
- [ ] 작성 원칙(한 페이지 응집·간결·모호 금지) 명시

#### R-2 기능 시나리오 다이어그램 신설 (순서도 재정의)
- [ ] §1 선택 산출물 표에서 "순서도"가 "기능 시나리오 다이어그램"으로 명칭 변경 + 설명에 flowchart+sequence+state 3종 명시
- [ ] §7-3에 기능 시나리오 다이어그램 작성 가이드 신설 (필수 섹션 6개 + Mermaid 작성 규칙)
- [ ] 파일명 컨벤션 `scenario-{기능명}.md` 명시

#### R-3 화면 흐름도 신설
- [ ] §1 선택 산출물 표에 "화면 흐름도" 행 추가 + 설명에 Mermaid flowchart + 화면 단위 명시
- [ ] §2 연결 맵에 "화면 흐름도 ↔ IA"·"화면 흐름도 ↔ 와이어프레임(외부 참조)" 추가
- [ ] §7-3에 화면 흐름도 작성 가이드 신설 (필수 섹션 6개)
- [ ] 시나리오 다이어그램과의 경계(화면 vs 기능 단위)가 명시

#### R-4 Mermaid 시각화 표준 확대
- [ ] 신규 절(network-guide.md §11)에 산출물별 시각화 강제 수준 표(필수/권장 분류) 존재
- [ ] 필수: IA / 기능 시나리오 다이어그램 / 화면 흐름도 (3종)
- [ ] 권장: PRD(사용자 여정) / TRD(아키텍처) / 정책서(상태 전이) / 기능도 (4종)
- [ ] 각 산출물별 권장 다이어그램 유형(flowchart/sequence/state/graph) 명시

#### R-5 WBS 제거 (PMO 그룹 폐기)
- [ ] SKILL.md "커버 범위" 섹션에서 PMO·개발 WBS 문구 0건
- [ ] network-guide.md §1 PMO 섹션 행 0건 / Level 분해 구조 표 0건
- [ ] §2 연결 맵에서 "개발 WBS ↔ *" 행 0건
- [ ] §2 참조 항목 테이블에서 "개발 WBS" 관련 행 0건
- [ ] §5 diagnosis.json `type` enum에서 "개발 WBS" 문자열 0건
- [ ] §7 Phase 3 워커 프롬프트에서 WBS 관련 가이드 0건
- [ ] consistency-rules.md §7 Tier 분류에서 WBS 관련 행 0건

#### R-6 interview 스킬 통합 (TASK 단계)
- [ ] SKILL.md TASK 절에 interview 스킬 의존성 명시 (탐색 경로 2개 포함: `{프로젝트}/.opal/skills/interview/` → `~/.opal/skills/interview/`)
- [ ] Round 1/2/3 라운드 설계 표 존재 (질문 수·옵션 형식·multiSelect 여부)
- [ ] Step 1 도메인 옵션 구성 가이드 명시 (외부 API 신호 / 부가 산출물 신호 / docs/ 자동 스캔)
- [ ] TASK.md 신규 섹션 양식 명시 ("산출물 결정" + "외부 참조" + "PRD 입력 컨텍스트")
- [ ] 기존 "TASK 전용 확인 항목" 4개가 인터뷰 라운드로 재구성됨
- [ ] Round 3 호출 조건이 "PRD가 Round 1에서 선택된 경우" 로 명시 (M-7 적용)

#### R-7 정합성 검증 규칙 확장
- [ ] §1에 "시나리오 ↔ 정책서/TRD/IA" 3쌍 + "화면 흐름도 ↔ IA" 1쌍 추가 (각 쌍 양방향 체크 ≥2개)
- [ ] §7 Tier 분류에서 WBS 행 제거, "시나리오 ↔ 정책서·TRD·IA"·"화면 흐름도 ↔ IA"가 적절한 Tier에 추가
- [ ] §8 외부 참조 검증에 "화면 흐름도 ↔ 와이어프레임" 추가

#### R-8 변경이력 + 메모리 갱신
- [ ] SKILL.md 변경이력 마지막 행이 v4.0 + 날짜(2026-05-24) + 태스크 008 번호 포함
- [ ] 변경 내용에 R-1~R-7 핵심 변경이 한 줄 요약으로 명시
- [ ] `.opal/MEMORY.md` 작업 히스토리 008 행이 CLOSE 단계에서 완료일시 갱신

### 4.2 일관성 테스트

- [ ] SKILL.md 커버 범위·TASK 절·변경이력 3영역의 v4 변경이 서로 모순되지 않음 (예: 커버 범위에서 "기능 시나리오 다이어그램" 명시 ↔ network-guide.md §1과 명칭 일치)
- [ ] network-guide.md §1·§2·§5·§7-3·§11 사이 신규 산출물 명칭 일관 — "기능 시나리오 다이어그램" / "화면 흐름도"가 모든 절에서 동일 표기
- [ ] consistency-rules.md §1·§7·§8 신규 쌍의 산출물명이 network-guide.md §1과 동일 표기
- [ ] PMO/WBS 잔여 흔적 0건 — 3개 파일 전체 `grep "WBS\|PMO" -c` 결과 합계 0
- [ ] Mermaid 다이어그램 유형(flowchart/sequence/state/graph)이 §7-3 가이드와 §11 표 사이에서 일관
- [ ] 8섹션 명칭이 SKILL.md TASK 절(Round 3 PRD 입력 컨텍스트)과 network-guide.md §7-3 PRD 가이드 양쪽에서 동일 표기

### 4.3 문서 품질

- [ ] 한국어 본문 + 영어 코드/필드명 규칙 준수 (`docs/CONVENTIONS.md` §언어 규칙) — FR-XXX, type enum 등 영어 식별자 유지
- [ ] kebab-case 파일/폴더 네이밍 준수 — `scenario-{기능명}.md` 컨벤션 (`docs/CONVENTIONS.md` §파일/폴더)
- [ ] YAML frontmatter 변경 없음 (SKILL.md frontmatter는 v4.0에서 미수정 — name/description 그대로)
- [ ] 변경이력 행 형식 — 일시 `YYYY-MM-DD HH:mm` (KST) / 버전 semver / 태스크 번호 `(008)` 괄호 (`docs/CONVENTIONS.md` §변경이력 작성 의무)
- [ ] 인용 포맷 — 신규 추가 섹션에 인라인 인용 부착 시 `(→ D-N)` 또는 `` `경로` §N `` 형식 (citation-rules.md §2)
- [ ] 표 정렬 — 모든 신규 마크다운 표가 헤더 구분선(`|---|`) 정렬 유지

---

## 5. 리스크 및 대응

| # | 리스크 | 영향 | 대응 방안 |
|---|--------|------|----------|
| RISK-1 | 시나리오 다이어그램과 화면 흐름도 경계 모호 — 사용자가 동일 내용을 양쪽에 작성할 가능성 | 산출물 중복·정합성 검증 비용 증가 | M-3 경계 박스를 §7-3 화면 흐름도 가이드 본문에 강조 삽입 + consistency-rules.md §1 신규 쌍에 "범위 중복 검증" 체크 항목 1개 포함 |
| RISK-2 | 기존 프로젝트의 "순서도" 산출물 — v4 install 후 명칭 불일치로 다이어그노시스 오작동 | 기존 프로젝트의 진단 실패 또는 산출물 분류 오류 | M-4 "수동 재분류 안내" 정책 — SKILL.md 변경이력 v4.0 행에 "기존 '순서도' 산출물은 사용자가 수동 재분류" 명시 + 향후 별도 마이그레이션 도구는 새 태스크에서 처리 |
| RISK-3 | interview 스킬의 라운드 수(2~3) 원칙 초과 가능성 — Round 3 추가로 라운드가 3개 이상 발생 가능 | interview 원칙 위배 / 사용자 피로도 증가 | M-7 Round 3 호출 조건을 "PRD가 Round 1에서 선택된 경우"로 제한 + interview SKILL.md §인터뷰 원칙 5 "라운드 최소화" 그대로 적용. PRD 미작성 모드는 Round 2까지로 종료 |
| RISK-4 | 한 페이지 응집 원칙과 8섹션 확장의 충돌 — 8섹션을 모두 채우면 한 페이지를 넘을 가능성 | 본 자료 §"한 페이지 응집" 원칙 손상 | §7-3 PRD 가이드의 "작성 원칙" 박스에 "각 섹션 핵심만 응집, 부수 설명은 [상세는 별도 절 참조] 패턴" 안내 추가 검토 — EXECUTE 시 워커 판단 |
| RISK-5 | EXECUTE Step 2·3 동일 파일 충돌 — network-guide.md 동시 편집 위험 | 워커 디스패치 시 파일 잠금·머지 충돌 | Phase 그룹핑(§3 상단) — Step 2와 Step 3을 다른 Phase로 분리, 순차 실행 강제 |
| RISK-6 | 인용 누락 — 비개발 트랙은 §1.5에 따라 문서·웹 근거 필수(설계·소스 선택) — EXECUTE 산출물에서 인용 누락 시 R-8 변경이력의 추적성 약화 | 산출물 부적합 처리 가능성 | EXECUTE 워커 프롬프트에 "citation-rules.md §1.5 비개발 트랙 매트릭스 + §3.2 인라인 인용" 의무 명시 (PM이 디스패치 시 주입) |
| RISK-7 | 변경이력 v4.0 행 누락 — Step 1 작업 중 변경이력 갱신을 잊어버릴 가능성 | `.opal/AGENT.md` §금지사항 "변경이력 누락 금지" 위배 + 추적성 손상 | Step 1 완료 기준에 "변경이력 마지막 행이 v4.0 + 2026-05-24 + (008)" 명시 + EXECUTE QA에서 검증 |

---

## 6. 의존 관계 (Phase 그룹핑 — §3 상단 요약 보강)

- **Phase 1 (병렬)**: Step 1 (SKILL.md) + Step 2 (network-guide.md §1·§2·§5) + Step 4 (consistency-rules.md) — 서로 다른 파일이므로 독립 실행 가능
- **Phase 2 (순차)**: Step 3 (network-guide.md §7-3·§11) — Step 2와 동일 파일이므로 Step 2 완료 후 진행
- **Phase 3 (CLOSE 자동)**: MEMORY.md 갱신은 EXECUTE 체크리스트 외부 (CLOSE 단계에서 PM 자동 수행)

**디스패치 권장 방식** (오케스트레이터가 EXECUTE 진입 시):
1. Phase 1: Step 1·2·4 워커 3개 병렬 디스패치 (1회 메시지에 Task 도구 3개 호출)
2. **Phase 1 완료 신호**: 병렬 디스패치한 Task 3개의 응답이 모두 수신되고 모두 `status: "completed"`인 경우. `status: "failed"` 또는 `blockers != []`인 워커가 1건이라도 있으면 즉시 에스컬레이션(Gate Fail 처리)하고 Phase 2 진입 보류.
3. Phase 2: Step 3 워커 1개 디스패치 (network-guide.md §2 수정 결과를 입력으로 §7-3·§11 작성)
4. 모든 Step 완료 후 QA Gate

---

## 변경이력 (PLAN 자체)

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-05-24 14:05 | 초기 작성 — R-1~R-8을 4개 Step + 8개 의사결정(M-1~M-8)으로 분해. Phase 그룹핑 적용 (Phase 1 병렬 / Phase 2 순차). 비개발 트랙 citation 매트릭스 적용. (008) |
| v1.1 | 2026-05-24 14:15 | QA-PLAN Normal 4건 + Minor 3건 반영 — HH:mm 치환 지침(N-1) / Step 3 grep 안정성 + 헤더 유지 가이드(N-2) / Step 1 TASK 전용 항목 제거 grep 검증(N-3) / §6 Phase 1 완료 신호 명시(N-4) / D-5 경로 통일(m-1) / F-5→F-4 정정(m-2) / 리스크 # 컬럼 RISK-N 변경(m-3). (008) |
