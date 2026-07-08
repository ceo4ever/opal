# TASK: README 최신화 — 신규 베이스라인(001~017 + brain) 반영

> 작성일: 2026-06-12 | 작업 유형: 개선 | 적용 스킬: opp | 모드: semi-agentic
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

README.md가 마지막 정비(141) 이후 진행된 v0.5.0 베이스라인의 신규 기능·플랫폼·트랙·정정 사항을 반영하지 못하고 있다. 누락 기능을 추가하고 부정확한 기술(技述)을 SSOT(레지스트리·하네스·PROJECT.md)와 일치하도록 최신화한다.

## 배경

README는 `4d30954 docs(141)`에서 오픈소스 공개 수준으로 정비된 이후 `b1b7618`로 tasks 베이스라인이 리셋되고 001~017 + brain 라인 작업이 누적되었다. 그 변경의 대부분이 README에 반영되지 않아, 신규 사용자가 보는 공개 문서와 실제 프레임워크 기능 사이에 갭과 오정보가 존재한다.

## 배경 분석 (대화에서 도출)

대화에서 README ↔ 현재 프로젝트(git log + 레지스트리 + PROJECT.md) 갭을 진단했다.

### (A) 통째로 누락된 신규 기능

| # | 항목 | 근거 | README 현재 |
|---|------|------|------------|
| A-1 | **opal-brain (`//opbr`)** — 프로젝트 지식 위키 (init/ingest/query/lint) | 015·016 커밋, 레지스트리, `docs/PROJECT.md` §주요 컴포넌트(Project Brain) | 전혀 없음 |
| A-2 | **opal-pilot-gc (`//opgc`)** — 보안·컨벤션 체크 경량 Pilot | 레지스트리, `docs/PROJECT.md` §주요 컴포넌트(GC) | Pilot 목록·사용법 없음 |
| A-3 | **Codex 플랫폼** (4번째 지원 환경) | 009 커밋, `docs/PROJECT.md` §프로젝트 원칙 3 | "Claude/Cursor/Gemini"만 표기 |
| A-4 | **OPAL 헌법 (PRINCIPLES.md)** | 012 커밋, `~/.opal/PRINCIPLES.md` | 핵심 철학에 미반영 |
| A-5 | **L2 경량 트랙** ("그냥 해" 직접 수정) | 014 Phase 5 | 비서/PM 모드만 설명 |
| A-6 | **TDD RED-first 트랙** | 016·017 커밋 | opds/opd 흐름에 미반영 |
| A-7 | 독립 스킬 누락: `html-mockup`, `html-sa`(system-architecture-html), `ppt-builder` | 레지스트리 standalone 그룹 | 사용법 누락 |

### (B) 내용은 있으나 부정확 (오정보)

| # | 항목 | README 현재 | 실제(SSOT) |
|---|------|------------|-----------|
| B-1 | 부트스트랩 체크리스트 예시 | `✅ identity ✅ harness …` | `✅ principles ✅ identity …` (principles 칼럼 추가, reporting 제거) — `~/.opal/AGENT.md` §부트스트랩 완료 보고 |
| B-2 | `opsdd` 파이프라인 표기 | `TASK→SPEC→VERIFY→REVIEW→DESIGN→EXECUTE-LOOP→DONE` | 레지스트리: `SPEC→VERIFY→PLAN→TASKS→VERIFY→LOOP→DONE` / PROJECT.md: `SPEC→VERIFY→PLAN→TASKS→EXECUTE` — SKILL.md SSOT로 확정 필요 |
| B-3 | 지원 AI 플랫폼 표 | Claude/Cursor/Gemini | + Codex |
| B-4 | 아키텍처 개요 에이전트 수 표기 | "전문 6 + 범용 5 + GC 2" | 실제 `opal/agents/` 구성과 대조 검증 필요 |

> SSOT 불일치(B-2 등)는 PLAN 단계에서 각 SKILL.md 원본을 Read하여 확정한다. README는 SSOT를 따른다.

## 확정된 설계 방향 (대화에서 합의)

- 트랙: 변경량이 크고 정확성 검증이 필요하므로 L2 경량이 아닌 `//opp` 풀 파이프라인으로 진행 (사용자 AskUserQuestion 선택).
- 순수 문서 작업이므로 코드 동작검증(TEST)은 불요. PM Gate 문서검증으로 품질을 보장한다.
- README는 SSOT(레지스트리·하네스·각 SKILL.md·PROJECT.md)를 따른다. 문서·코드 불일치 시 코드(SKILL.md)가 우선.

## 요구사항

- [ ] **R-1 신규 기능 반영**: 누락 기능 A-1~A-6을 README에 추가한다.
  - 무엇을: opal-brain(`//opbr`), opal-pilot-gc(`//opgc`), Codex 플랫폼, OPAL 헌법, L2 경량 트랙, TDD RED-first 트랙 설명을 추가
  - 어디에: `README.md` — 각 항목에 맞는 섹션(주요 특징/Pilot 목록/설치·플랫폼/핵심 철학/모드·트랙/파이프라인)
  - 왜: 배경 분석 (A) — 신규 사용자 공개 문서와 실제 기능의 갭 제거
  - AC: A-1~A-6 6개 항목이 README 본문에 각각 1개 이상의 설명 단락 또는 표 행으로 존재하고, 약어(`//opbr`,`//opgc`)와 파이프라인/모드 설명이 레지스트리·PROJECT.md와 일치한다.
- [ ] **R-2 오정보 정정**: 부정확 항목 B-1~B-4를 SSOT와 일치시킨다.
  - 무엇을: 부트스트랩 체크리스트 예시, opsdd 파이프라인 표기, 지원 플랫폼 표, 에이전트 수 표기를 정정
  - 어디에: `README.md` — 설치 Step 3, Pilot 비교표·opsdd 사용법, 설치 Step 1 플랫폼 표, 아키텍처 개요
  - 왜: 배경 분석 (B) — 오정보 제거
  - AC: B-1~B-4 4개 항목이 각 SSOT(AGENT.md / SKILL.md / PROJECT.md / `opal/agents/`)와 문자열·구조가 일치한다. 특히 opsdd 파이프라인 표기는 README 내 모든 등장 위치에서 동일하다.
- [ ] **R-3 독립 스킬 목록 동기화**: A-7 독립 스킬을 "독립 스킬 사용법" 섹션과 일치시킨다.
  - 무엇을: 레지스트리 standalone 그룹과 README "독립 스킬 사용법" 목록을 대조하여 누락분을 추가하고, 존재하지 않는 스킬은 제거
  - 어디에: `README.md` §독립 스킬 사용법
  - 왜: 배경 분석 A-7
  - AC: 레지스트리 standalone 그룹의 사용자 노출 스킬과 README 독립 스킬 목록이 1:1 대응한다(미확정 ppt-builder 제외 또는 결정 반영).
- [ ] **R-4 일관성·링크 무결성**: 목차·내부 앵커·문서 링크가 갱신 후에도 유효하다.
  - 무엇을: 섹션 추가/변경에 맞춰 목차와 내부 앵커 링크를 갱신, 깨진 링크 없음
  - 어디에: `README.md` §목차 및 본문 앵커
  - 왜: 섹션 추가 시 목차 누락·앵커 깨짐 방지
  - AC: 목차의 모든 항목이 실제 섹션 헤딩과 매칭되고, README 내부 `#앵커` 링크가 모두 존재하는 헤딩을 가리킨다.

## 미확정 사항 (PLAN에서 결정)

- **U-1 ppt-builder 노출 여부**: `skills/ppt-builder/`가 미추적(`??`)이고 레지스트리도 미커밋(`M`) 상태이며 PROJECT.md 주요 컴포넌트에 없음 → 정식 컴포넌트인지 작업 중 산출물인지 불확실. README 등재 여부는 PLAN에서 상태 확인 후 결정하거나 캡틴에 확인.
- **U-2 opsdd 파이프라인 정본**: 레지스트리(`SPEC→VERIFY→PLAN→TASKS→VERIFY→LOOP→DONE`)와 PROJECT.md(`…→EXECUTE`) 표기가 다름 → `opal-pilot-sdd/SKILL.md` 원본을 Read하여 정본 확정.
- **U-3 README 개편 범위**: 부분 보강(섹션 추가·정정)으로 충분한지, 구조 재편이 필요한지 PLAN에서 판단.

## 제약 조건

- 배포 경계 준수: README는 프로젝트 루트 소스 파일이므로 직접 수정 가능. 단, `~/.opal/` 배포 파일은 직접 편집 금지.
- SSOT 우선: README 내용은 레지스트리·하네스·각 SKILL.md·PROJECT.md를 근거로만 작성한다(상상·추정 금지 — citation-rules §0).
- 변경이력: README는 변경이력 표 대상 문서가 아님(공개 소개 문서). 단, 관련 SSOT 문서를 수정하게 되면 해당 문서 변경이력 규칙 적용.
- 미커밋 변경(`opal-skills-registry.json` 수정, `skills/ppt-builder/` 등)은 본 태스크와 독립적이며 건드리지 않는다.

## 기술 스택

- Markdown (문서). 코드 빌드/테스트 없음.

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | 스킬 레지스트리 | `opal/core/references/opal-skills-registry.json` | Pilot·독립 스킬·약어 SSOT |
| D-2 | 설계 | PROJECT.md | `docs/PROJECT.md` | 주요 컴포넌트(브레인/GC), 지원 플랫폼, 프로젝트 정의 |
| D-3 | 설계 | AGENT.md | `~/.opal/AGENT.md` | 부트스트랩 완료 보고 형식(B-1), L2 경량 트랙 |
| D-4 | 설계 | OPAL 헌법 | `~/.opal/PRINCIPLES.md` | 핵심 철학(A-4) |
| D-5 | 설계 | opal-pilot-sdd SKILL | `~/.opal/skills/opal-pilot-sdd/SKILL.md` | opsdd 파이프라인 정본(B-2/U-2) |
| D-6 | 설계 | opal-pilot-gc SKILL | `~/.opal/skills/opal-pilot-gc/SKILL.md` | GC Pilot 사용법(A-2) |
| D-7 | 설계 | opal-brain SKILL | `~/.opal/skills/opal-brain/SKILL.md` | 브레인 4모드 사용법(A-1) |
| D-8 | 소스 | 현재 README | `README.md` | 갱신 대상 (현행 구조·목차) |
| D-9 | 설계 | red-first 하네스 | `~/.opal/references/harness/red-first.md` | TDD RED-first 설명(A-6) |
