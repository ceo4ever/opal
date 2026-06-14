# TASK: opi 아키텍처 문서 생성 깊이 강화 (WHERE → HOW)

> 작성일: 2026-06-14 | 작업 유형: 개선 | 적용 스킬: opp | 모드: semi-agentic
> 입력: 사용자 요청 + 사전 진단 대화
> 출력: TASK.md

## 작업 목표

opi(`opal-project-init`)가 생성하는 프로젝트 문서가 "지도(WHERE)" 수준에 머물러 구조를 알 수 없는 문제를 해소한다. **BE·FE·도메인 전 영역**의 구성과 구조를 **WHERE(어디에 무엇이 있는가) + HOW(어떻게 짜는가) 양면으로 철저히 분석**하여, 구현자(사람·AI 워커)가 소스에서 헤매지 않고 작업할 수 있는 **"맵과 나침반" 수준**의 문서를 산출하도록 스킬을 완벽히 개선한다. (수준 정의: 이 문서만 읽고 해당 프로젝트의 규약대로 새 도메인/API/화면을 구현할 수 있어야 한다)

## 배경

캡틴이 대형 백엔드 프로젝트에서 opi를 실행했으나, 결과물이 파일 위치·기술 스택·디렉토리 트리 수준에 그쳐 백엔드가 **어떤 구조로 짜였는지** 알 수 없었다. 스킬이 오작동한 것이 아니라, 설계 자체가 WHERE에서 멈추도록 되어 있다.

## 배경 분석 (대화에서 도출)

소스(`opal/skills/opal-project-init/`)를 분석하여 3대 근본 원인을 확인했다.

**원인 1 — ARCHITECTURE.md 템플릿이 WHERE만 묻고 HOW가 없음 (최대 원인)**
- `docs-guide.md:111-137`의 ARCHITECTURE.md 구조 = 시스템 구성 + 기술 스택 상세 + 개발 환경 + 디렉토리 구조. 전부 WHERE.
- 빠진 것: 레이어 규칙·의존 방향, 도메인 패턴(Controller-Service-Repository / port-adapter 등), 데이터 흐름, 트랜잭션, 상태 전이, "새 기능 추가 절차".
- 이 내용은 BACKEND.md 템플릿(`docs-guide.md:206-217` 도메인 패턴·새 기능 추가 가이드)에 일부 있으나, BACKEND.md는 "BE 있을 때"만 생성(`docs-guide.md:273`)되며 ARCHITECTURE보다 후순위라 대형 BE에서 핵심 HOW가 유실된다.

**원인 2 — 초기화 모드의 코드 분석이 나열뿐, 심층 탐색 방법론 부재 (비대칭)**
- 초기화 Phase 3-1(`SKILL.md:402-412`)은 "아키텍처/코드 구조 분석"을 **나열만** 한다.
- 반면 최신화 모드 Step C(`SKILL.md:602-617`)에는 구체적 탐색 패턴 표(엔트리포인트·베이스클래스·미들웨어·설정로더·라우터·유틸)가, Step D(`SKILL.md:619-639`)에는 작성 후 코드 1:1 재대조가 있다.
- 즉 **처음 만들 때(초기화)가 갱신할 때(최신화)보다 얕다** — 거꾸로 된 비대칭.

**원인 3 — PM 단독 표면 훑기 + 멀티레포/우산 구조 미인지**
- opi는 PM이 직접 분석·작성한다(`SKILL.md:341-432`). 대형 모놀리스를 단일 컨텍스트로 훑으면 표면만 보고 끝난다. 영역별 전문 워커(opal-be-agent/opal-fe-agent) 디스패치 단계가 없다.
- SKILL.md는 단일 레포 전제(`docs/ARCHITECTURE.md` 1벌). 독립 git 저장소 N개로 구성된 우산(workspace) 구조에 대한 레포별 문서 세트 분기와, 각 레포 자체 docs를 슬라이스로 정제·검증하는 단계가 없다.

## 확정된 설계 방향 (대화에서 합의)

**목표 수준 확정 (캡틴 발화)**: "BE·FE든 도메인 구성·구조를 WHERE·HOW 수준으로 철저히 분석해서, 구현할 때 맵과 나침반이 되어 헤매지 않고 소스를 분석해 구현할 수 있게끔 완벽한 개선." → 수용 기준 = "이 문서만 읽고 해당 프로젝트 규약대로 새 기능을 구현 가능".

**범위 확정**: A+B+C+D 전체 + 아래 분석으로 발견한 E를 한 태스크로 묶어 풀 파이프라인 진행. 상호의존이므로 분리하지 않는다 (C가 B 방법론으로 깊이 파서 A 그릇에 담고, D/E가 레포 구조·성숙도에 따라 경로를 분기).

**기준 레퍼런스 (실증)**: `/Volumes/Data/StoreLinkStudio/pointail/workspace/backend` 분석 결과가 목표 수준의 living reference다. 이 repo의 `docs/architecture/layer-rules.md`(헥사고날 포트&어댑터, domain=`I*Port`/infra=adaptor, "domain 순수 Kotlin·Spring 금지")·`transaction-patterns.md`(DB별 트랜잭션 매니저 5종, `@Transactional(transactionManager=...)` 필수, R2DBC/JPA 혼용 금지)가 정확히 "맵과 나침반" 수준이다. **그런데 opi는 이 5,261줄 자체 docs를 흡수하지 못하고 WHERE 수준만 산출** → 원인 3(자체 docs 미흡수)과 원인 1(템플릿에 layer-rules/transaction-patterns 슬롯 부재)이 동시 실증됨.

**발견된 추가 결 2가지 (pointail/backend 분석)**:
1. **단일 git + 다중 빌드 모듈/서비스**: `settings.gradle.kts`가 application(storelink6/pugshop6/pointail-jp/revup 등) × domain × infrastructure × external 50+ 모듈을 포함. D의 "독립 git N개"만으로는 부족 — **단일 레포 내 다중 서비스/모듈** 분기도 필요(이 repo의 `docs/claude/services/{storelink6,pugshop6-jp,revup}/` 구조가 그 증거).
2. **레포 자체 docs 보유**: 성숙한 레포는 자체 아키텍처 문서를 이미 갖는다 → 처방 E(발견·정제·흡수)가 빈약 레포의 직접 생성(B/C)보다 우선 레버.

## 요구사항

- [ ] **A. 템플릿 심화 (docs-guide.md)**
  - 무엇을: ARCHITECTURE.md 구조에 HOW 섹션(레이어 규칙·의존 방향, 데이터 흐름, 트랜잭션·상태 전이, 명명 규칙, "새 기능 추가 절차") 추가. BACKEND.md/FRONTEND.md 도메인 패턴·새 기능 가이드 강화. "구현 시 주입 가능 수준"을 작성 기준으로 명문화.
  - 어디에: `opal/skills/opal-project-init/references/docs-guide.md` — ARCHITECTURE.md 섹션(`:105-145`), BACKEND.md 섹션(`:187-224`), FRONTEND.md 섹션(`:226-262`)
  - 왜: 원인 1 — 담을 그릇(템플릿)이 WHERE만이면 B/C/D로 깊이 파도 유실됨
  - AC: docs-guide.md ARCHITECTURE.md "구조"에 레이어·의존방향, 데이터 흐름, "새 기능 추가 절차"가 필수 섹션으로 존재하고, 각 문서 "작성 규칙"에 "구현 시 주입 가능 수준" 기준 문장이 명시되어 있다.

- [ ] **B. 초기화 모드 심층 분석·재대조 이식 (SKILL.md)**
  - 무엇을: 초기화 모드 Phase 3-1에 최신화 Step C 동등 수준의 탐색 패턴 표 + 작성 후 코드 1:1 재대조(Step D 동등) 이식. BE/FE 스택별 탐색 체크리스트 포함.
  - 어디에: `opal/skills/opal-project-init/SKILL.md` — 초기화 Phase 3-1(`:402-412`), 초기화(기존) 케이스(`:311-337`)
  - 왜: 원인 2 — 초기화/최신화 분석 깊이 비대칭 해소
  - AC: 초기화 모드 Phase 3에 최신화 Step C와 동등한 탐색 패턴 표(엔트리포인트·베이스클래스·미들웨어·설정로더·라우터·유틸)가 존재하고, 작성 후 코드 1:1 재대조 단계가 추가되어 있다.

- [ ] **C. 대형 코드베이스 전문 워커 디스패치 (SKILL.md)**
  - 무엇을: Phase 3 분석·작성을 코드 디렉토리/영역별 전문 워커(opal-be-agent/opal-fe-agent)에게 디스패치하는 분기 추가. PM은 종합·검토 담당. 디스패치 임계 기준 명시.
  - 어디에: `opal/skills/opal-project-init/SKILL.md` — Phase 3(`:398-432`)
  - 왜: 원인 3 — PM 단독 표면 훑기 한계. (단, opi는 "직접 수행" 스킬이므로 디스패치 도입은 설계 변경 — PLAN에서 적정 임계·폴백 구체화)
  - AC: Phase 3에 "코드 규모/디렉토리 수가 임계 이상이면 영역별 전문 워커 디스패치" 분기가 명시되고, 디스패치 기준·전문 에이전트 매핑·PM 종합 절차가 기술되어 있다.

- [ ] **D. 멀티레포·멀티서비스 구조 분기 (SKILL.md)**
  - 무엇을: 코드가 ① 독립 git 저장소 N개(우산 구조) 또는 ② 단일 레포 내 다중 빌드 모듈/서비스(Gradle/Nx 멀티모듈 등)면, 영역/서비스별 문서 세트로 분기 생성하는 규칙 추가.
  - 어디에: `opal/skills/opal-project-init/SKILL.md` — Phase 1-1 Step A(`:97-132`), Phase 2/3 작성 대상(`:349-356`, `:414-421`)
  - 왜: 원인 3 — 단일 레포·단일 문서 세트 전제. pointail/backend는 단일 git이지만 `settings.gradle.kts` 50+ 모듈 × 다중 서비스 → 단일 ARCHITECTURE.md로는 표현 불가. 서비스별 분기 필요(이 repo `docs/claude/services/*` 구조가 증거).
  - AC: SKILL.md에 멀티레포(독립 git N개)와 멀티서비스(단일 레포 다중 모듈) 양쪽 판별 + 영역/서비스별 문서 세트 분기 규칙이 존재한다.

- [ ] **E. 레포 성숙도 분기 + 기존 docs 흡수 (SKILL.md) — 신규, 본 분석으로 도출**
  - 무엇을: 코드 디렉토리에 자체 아키텍처/도메인 문서(`docs/`, `ARCHITECTURE`, `ADR/` 등)가 존재하면 **발견 → 정제(슬라이스) → 흡수/링크**하는 단계를 분석 흐름에 추가. 자체 문서가 빈약하면 B/C(심층 분석·워커)로 직접 생성. 두 경로를 명시 분기.
  - 어디에: `opal/skills/opal-project-init/SKILL.md` — Phase 1-1 분석(`:93-153`), Phase 3 작성 흐름(`:398-432`)
  - 왜: 원인 3 핵심 — pointail/backend는 L3+ 자체 docs 5,261줄을 보유했으나 opi가 흡수하지 못하고 WHERE만 산출. 성숙 레포에선 D보다 E가 1순위 레버.
  - AC: SKILL.md 분석 단계에 "코드 디렉토리 내 자체 문서 탐색 → 있으면 정제·흡수, 없으면 직접 생성" 분기가 명시되고, 흡수 시 출처 추적(어느 원본 docs에서 왔는지)이 보존된다.

## 제약 조건

- **배포 경계 (MUST)**: `opal/skills/opal-project-init/` 프로젝트 소스만 수정한다. `~/.opal/skills/opal-project-init/` 직접 편집 금지. 수정 후 install로 재배포(후속).
- **변경이력 (MUST)**: `SKILL.md` 변경이력 표(`:871-884`)에 행 추가(차기 버전 v4.2 등). docs-guide.md 변경분도 추적 가능하게 기록.
- **플랫폼 독립 (MUST)**: 코드 탐색은 도구명이 아닌 행위(파일 탐색·패턴 검색)로 기술한다 (`SKILL.md:615` 기존 원칙 유지). Claude/Cursor/Gemini 분기를 로직에 넣지 않는다.
- **단순성**: 최신화 모드에 이미 존재하는 Step C/D 자산을 재사용(중복 패턴 제거 우선). 초기화/최신화가 공통 분석 블록을 참조하도록 설계 검토.
- **동작검증 필수**: opi 재실행으로 깊이 개선을 실증한다 — 본 프로젝트 또는 대형 BE 샘플에서 ARCHITECTURE/BACKEND에 HOW 섹션이 실제로 채워지는지 확인. (헌법 §4 — 문서 생성만으로 완료 선언 금지)

## 기술 스택

- Markdown (스킬 문서), Node.js (apply.js 스크립트 — 이번 범위 외), Bash (install 재배포 — 후속)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | opi SKILL.md | `opal/skills/opal-project-init/SKILL.md` | 수정 대상 — 초기화/최신화 Phase, 디스패치 구조 |
| D-2 | 소스 | docs-guide.md | `opal/skills/opal-project-init/references/docs-guide.md` | 수정 대상 — ARCHITECTURE/BACKEND/FRONTEND 템플릿 |
| D-3 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | 변경이력·@header·배포 경계·플랫폼 분기 구현 규칙 |
| D-4 | 설계 | PROJECT.md | `docs/PROJECT.md` | 프로젝트 원칙(플랫폼 독립·재사용성), 컴포넌트 표준 |
| D-5 | 설계 | 헌법 PRINCIPLES.md | `~/.opal/PRINCIPLES.md` | §2 단순성·§3 외과적 변경·§4 동작 증거 |
