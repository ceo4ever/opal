# TASK: oppd 개선 — 프로세스(문서 승격) + WBS 세분화(BE/FE) + 액션 완성도 루프(B7)

> 작성일: 2026-06-21 | 작업 유형: 개선 | 적용 스킬: opd | 모드: agentic
> 입력: 사용자 요청 (설계 대화 선행)
> 출력: TASK.md

## 작업 목표

oppd(`opal-pilot-project-dev`) 파이프라인을 3개 축으로 개선한다: ① PRD/TRD를 태스크 폴더에서 작성 후 확정분만 docs/로 승격하는 프로세스, ② WBS 액션 세분화를 "단일 책임 + 단일 수용 시나리오" 기준으로 재정의(BE/FE 분할 기준 포함), ③ 액션 실행을 선형 파이프라인에서 **실패 분류 기반 경계 재설계 루프(B7)**로 전환하여 "작게 → 명확 → 구현+테스트 → 완성도" 원칙을 구조와 루프 양쪽으로 집행한다.

## 배경

캡틴의 핵심 관심: **수행 단위가 작을수록 명확해지고, 구현+테스트로 완성도가 올라간다.** 현 oppd는 이 관심을 구조적으로 보장하지 못한다 — sizing 규칙이 큰 묶음을 허용하고, 액션 실패가 코드 수정 루프로만 처리되며 설계 재검토 루프가 없다. 병렬성은 세분화의 *결과*인데 일부 문서가 병렬을 1차 목표처럼 서술한다.

## 배경 분석 (대화에서 도출)

현 oppd 구조 진단 (대상은 프로젝트 소스 `opal/...`):

| 영역 | 현재 상태 | 갭 |
|------|----------|-----|
| Phase 1 (기획) | opwt가 `docs/PRD.md`·`docs/TRD.md`에 **직접** 작성 (`opal/skills/opal-pilot-project-dev/SKILL.md` §Phase 1) | 미확정 초안이 프로젝트 SSOT(docs/) 선오염 |
| Phase 2 (WBS) | sizing "하나의 태스크는 1~3일 분량이 적정" (`references/wbs-guide.md` §태스크 분할 원칙) | 단일 책임 규칙 부재 → 다개념 액션 허용(화면 3개·BE 4책임 묶음이 규칙 위반 아님) |
| 검증 명령 | generic (`npm run lint && npm test`) (`references/wbs-guide.md` §WBS 구조) | "이 단위가 됐다"를 증명하는 수용 시나리오 아님 |
| 통합 | 통합 액션 개념 없음 | 조각은 완벽한데 합치면 깨지는 함정 미방어 |
| 액션 루프 | `opal/agents/opal-task-action-agent/AGENT.md` §실행 프로세스 = **선형 6단계** (PLAN→QA→TEST-SCENARIO→EXECUTE→VERIFY→TEST). VERIFY 실패 시 EXECUTE 코드 수정만 루프, 한도 초과 시 `status: failed` 에스컬레이션. PLAN 회귀는 QA 게이트 1회뿐 | 실패 시 재설계(PLAN) 루프 부재 → 설계 결함을 코드로만 두드림 |
| QA 설계 이슈 | `references/verification-loop-guide.md` §3-5 = "QA 설계/아키텍처 이슈 0회 재시도 즉시 에스컬레이션" | B7 재설계 루프와 의미 충돌 (조정 필요) |
| 루프 상한 SSOT | `opal/core/references/opal-harness.md` §자동 루핑 제약 (lint∞/build2/L3a3/L3b1/QA0) | B7 PLAN 재진입 상한 미등록 |

## 확정된 설계 방향 (대화에서 합의)

캡틴이 AskUserQuestion으로 직접 선택한 결정 (권고안 채택):

**#1 프로세스**
- PRD/TRD는 태스크 폴더(작업본)에 작성 → 사용자 확정 후 docs/로 승격
- 승격 방식 = **PM 자동 판단**: 기존 docs 없으면 전체 복사(greenfield), 있으면 변경 델타 병합(반복 개발)
- WBS는 태스크 폴더 전용 (실행 산출물 — docs/ 승격 불요)

**#2 세분화**
- sizing "1~3일" → **"단일 책임 + 단일 수용 시나리오로 독립 검증 가능한 단위"**
- 집행 = **문서 규칙화(이번 태스크) + WBS 검증기 도구 게이트(후속 태스크)**
- BE 분할: 모델·엔드포인트·서비스·외부연동·인증 단위
- FE 분할: **3계층** — T0 컴포넌트 설계 → T1 공통 컴포넌트(병렬) → T2 화면 모듈(병렬). 공통 컴포넌트 추출 = **기존 UI킷(shadcn) 우선 + 프로젝트 고유는 2+ 화면 실사용 기준**. 소규모 예외(화면 ≤3) = T0/T1 생략
- 계약: API 계약(BE) / 컴포넌트 API 계약(FE) = 액션 간 인터페이스. 통합 액션 필수

**B7 액션 완성도 루프**
- 선형 → **경계 재설계 루프**(성공까지 순환, Guards 상한 내)
- VERIFY 실패 **triage**: 구현 / 설계 / 회귀
- 분류 주체 = **액션 에이전트 1차분류 + fix 한도초과 자동승격**(구현→설계)
- 설계 실패 **3계층 라우팅**: 액션-로컬(에이전트 자율 재PLAN) / WBS(PM) / TRD·PRD(사용자)
- WBS 변경 권한 = **2단 기준**(scope·인터페이스 불변 조정=PM 자율+로그 / scope·기능 변경=사용자). TRD/PRD 변경 = 항상 사용자 게이트
- 회귀(regression) = 즉시 중단 (재PLAN/재fix 안 함)
- 신규 신호: 액션 반환값 `failure_context.scope: action|wbs|trd`

## 요구사항

### #1 프로세스 변경

- [ ] **F-001** PRD/TRD 작성 위치를 태스크 폴더로 변경
  - 무엇을: Phase 1 산출물 경로를 `docs/PRD.md`·`docs/TRD.md` 직접 작성 → `tasks/{NNN}-oppd-…/PRD.md`·`TRD.md`(작업본)
  - 어디에: `opal/skills/opal-pilot-project-dev/SKILL.md` §Phase 1 (1-1 opwt 호출, 1-2 사용자 확정)
  - 왜: 확정 방향 #1 — docs/ SSOT 선오염 방지
  - AC: SKILL.md Phase 1이 PRD/TRD를 태스크 폴더 경로로 작성하도록 기술되어 있고, docs/ 직접 작성 지시가 제거되어 있다

- [ ] **F-002** 사용자 확정 후 docs/ 승격 단계 신설
  - 무엇을: Phase 1 "사용자 확정 후 후속 조치"에 **승격(promote)** 단계 추가 — PM 자동 판단(greenfield 전체 복사 / 반복 델타 병합) + PROJECT.md 등록 + ARCHITECTURE delta
  - 어디에: `opal/skills/opal-pilot-project-dev/SKILL.md` §1-3 후속 조치
  - 왜: 확정 방향 #1
  - AC: §1-3에 승격 단계가 있고, greenfield/반복 분기 판단 기준이 명시되어 있으며, 승격 대상(PRD/TRD 본문 + PROJECT.md 등록 + ARCHITECTURE)이 열거되어 있다

- [ ] **F-003** WBS를 태스크 폴더 전용으로 전환
  - 무엇을: `docs/WBS.md` 등록/승격 제거, WBS는 태스크 폴더 산출물로만 유지 (docs/PROJECT.md 등록 프로토콜에서 WBS 행 제거)
  - 어디에: `opal/skills/opal-pilot-project-dev/SKILL.md` §2-5 후속 조치, §문서 등록 프로토콜
  - 왜: 확정 방향 #1 (WBS는 실행 산출물)
  - AC: 문서 등록 프로토콜 표에서 WBS.md 행이 제거되고, §2-5에 docs/ 승격 지시가 없다

### #2 WBS 세분화

- [ ] **F-010** sizing 규칙 교체
  - 무엇을: "하나의 태스크는 1~3일 분량" → "단일 책임 + 단일 수용 시나리오로 독립 검증 가능한 단위"
  - 어디에: `references/wbs-guide.md` §태스크 분할 원칙, `SKILL.md` §2-2 태스크 분할
  - 왜: 확정 방향 #2 / 배경 분석 (sizing이 묶음 허용)
  - AC: wbs-guide·SKILL 양쪽에서 "1~3일" 표현이 단일 책임+수용 시나리오 기준으로 교체되어 있다

- [ ] **F-011** "너무 큼/작음" 판정 기준 명문화
  - 무엇을: 너무 큼(독립 책임 2+ / 독립 수용기준 2+ / 단일 수용 시나리오 작성 불가 → 재분할) + 너무 작음(관찰 동작 없는 헬퍼·타입 단독 → 흡수) 기준 추가
  - 어디에: `references/wbs-guide.md` §태스크 분할 원칙
  - 왜: 확정 방향 #2 (A17·A13 재발 차단)
  - AC: wbs-guide에 너무 큼/작음 신호와 재분할·흡수 조치가 각각 명시되어 있다

- [ ] **F-012** 액션별 구체 수용 시나리오 필수화
  - 무엇을: 각 액션에 자연어 완료 기준 + 검증 명령(구체) 필수, generic 명령 금지. 이 수용 시나리오가 액션 TEST-SCENARIO.md(RED-first) 씨앗임을 명시
  - 어디에: `references/wbs-guide.md` §WBS 구조(액션 목록 컬럼), §PM 검수 체크리스트
  - 왜: 확정 방향 #2 (완성도 = 단위별 증명)
  - AC: WBS 액션 컬럼에 "수용 시나리오"가 추가되고, generic 검증 명령 금지 규칙이 기재되며, TEST-SCENARIO 연결이 서술되어 있다

- [ ] **F-013** 통합 검증 액션 1급 타입 도입
  - 무엇을: 병렬군마다 "합쳐서 E2E 통과"를 별도 테스트된 액션으로 명시 (액션 타입에 `통합` 추가)
  - 어디에: `references/wbs-guide.md` §액션 구조, §WBS 구조
  - 왜: 확정 방향 #2 (합성 함정 방어)
  - AC: wbs-guide에 통합 액션 타입과 작성 규칙(언제 두는가 + 통합 수용 시나리오)이 명시되어 있다

- [ ] **F-014** 병렬 = 세분화의 파생으로 재서술
  - 무엇을: 병렬을 1차 목표가 아닌 세분화 DAG의 산출로 재서술
  - 어디에: `references/wbs-guide.md` §병렬 실행 전략, `references/parallel-execution-guide.md` 도입부
  - 왜: 확정 방향 #2 (B5)
  - AC: 두 문서에서 병렬이 세분화의 결과로 서술되고, 세분화↑→충돌↓→병렬↑ 인과가 기재되어 있다

- [ ] **F-015** PM 검수 체크리스트 갱신
  - 무엇을: 단일 책임 / 구체 수용 시나리오(generic 금지) / 통합 액션 존재 / 너무 큼 판정 대조 항목 추가
  - 어디에: `references/wbs-guide.md` §PM 검수 체크리스트, `SKILL.md` §2-3 PM 검수
  - 왜: 확정 방향 #2 (B6 게이트화)
  - AC: 체크리스트에 F-010~F-013 대조 항목 4종이 추가되어 있다

- [ ] **F-016** BE 액션 분할 기준 추가
  - 무엇을: 원자 단위(모델·마이그레이션 / 엔드포인트 / 도메인 서비스 / 외부연동 / 인증) + 각 수용 시나리오 예 + 너무 큼/작음 신호
  - 어디에: `references/wbs-guide.md` (신규 §BE 액션 분할 기준)
  - 왜: 확정 방향 #2 BE
  - AC: BE 원자 단위 5종이 표로 정리되고 각 수용 시나리오 예가 있다

- [ ] **F-017** FE 3계층 분할 기준 + opal-fe-agent 역할 추가
  - 무엇을: T0 컴포넌트 설계 → T1 공통 컴포넌트(병렬) → T2 화면 모듈(병렬) 3계층 + 추출 기준(UI킷 우선 + 2+ 화면) + 소규모 예외 + opal-fe-agent에 T0/T1/T2 역할·컴포넌트 API 계약 반영
  - 어디에: `references/wbs-guide.md` (신규 §FE 액션 분할 기준), `opal/agents/opal-fe-agent/AGENT.md`
  - 왜: 확정 방향 #2 FE
  - AC: wbs-guide에 FE 3계층 표 + 추출 기준 + 소규모 예외가 있고, opal-fe-agent에 T0/T1/T2 + 컴포넌트 API 계약 역할이 기재되어 있다

- [ ] **F-018** BE/FE 분할 매트릭스 + 계약 규칙
  - 무엇을: 레이어 경계=액션 경계(BE≠FE), API 계약(BE)/컴포넌트 API 계약(FE)=액션 간 인터페이스, 병렬/순차 판단(계약 합의 시 병렬)
  - 어디에: `references/wbs-guide.md` (신규 §BE/FE 분할 매트릭스)
  - 왜: 확정 방향 #2 계약
  - AC: BE/FE 분할 매트릭스 표 + 계약 합의 기반 병렬/순차 규칙이 명시되어 있다

### B7 액션 완성도 루프

- [ ] **F-020** 경계 재설계 루프 도입
  - 무엇을: 선형 6단계를 성공까지 순환하는 재설계 루프로 전환 (VERIFY/TEST 실패가 EXECUTE 또는 PLAN으로 분기)
  - 어디에: `opal/agents/opal-task-action-agent/AGENT.md` §실행 프로세스 / §5 VERIFY
  - 왜: 확정 방향 B7
  - AC: AGENT.md에 실패 시 PLAN 재진입 경로가 명시되고, 선형 종료(즉시 status:failed)가 루프 + 상한으로 대체되어 있다

- [ ] **F-021** VERIFY 실패 triage (구현/설계/회귀)
  - 무엇을: VERIFY 실패를 구현 수준 / 설계 수준 / 회귀로 분류하고 각 신호와 라우팅 정의
  - 어디에: `opal/agents/opal-task-action-agent/AGENT.md` §5, `references/verification-loop-guide.md` §3
  - 왜: 확정 방향 B7
  - AC: 3분류 표(성격·신호·라우팅)가 두 문서에 일관되게 기재되어 있다

- [ ] **F-022** 분류 주체 = 액션 에이전트 1차분류 + 자동승격
  - 무엇을: 액션 에이전트가 1차 분류, 구현으로 분류 후 fix 한도 초과 시 설계 수준 자동 승격 → PLAN 재진입. 분류 근거는 verification_log에 기록
  - 어디에: `opal/agents/opal-task-action-agent/AGENT.md` §5
  - 왜: 확정 방향 B7 (옵션1)
  - AC: AGENT.md에 1차분류 + fix 한도초과 자동승격 흐름과 verification_log 근거 기록이 명시되어 있다

- [ ] **F-023** 설계 실패 3계층 라우팅
  - 무엇을: 액션-로컬(에이전트 자율 재PLAN) / WBS(PM) / TRD·PRD(사용자) 3계층 + 범위 애매 시 로컬 재설계 시도(bounded) 후 상위 승격
  - 어디에: `opal/agents/opal-task-action-agent/AGENT.md`, `opal/skills/opal-pilot-project-dev/SKILL.md` §Phase 3
  - 왜: 확정 방향 B7 (소유권: PLAN.md=에이전트 / WBS.md=PM / TRD·PRD=사용자)
  - AC: 3계층 라우팅 표(범위·신호·누가·게이트)가 명시되고, 액션 에이전트가 WBS/TRD를 직접 수정 못 한다는 가드가 있다

- [ ] **F-024** WBS 변경 2단 기준 + TRD/PRD 사용자 게이트
  - 무엇을: WBS 변경은 scope·인터페이스 불변 조정=PM 자율+AGENTIC-LOG / scope·기능 변경=사용자 에스컬레이션. TRD/PRD 변경=항상 사용자 게이트
  - 어디에: `opal/skills/opal-pilot-project-dev/SKILL.md` §Phase 3 / §에스컬레이션
  - 왜: 확정 방향 B7 (Phase 3 PM 자율 ↔ Phase 2 확정 산출물 보호)
  - AC: SKILL.md에 WBS 2단 기준과 TRD/PRD 사용자 게이트 필수가 명시되어 있다

- [ ] **F-025** failure_context.scope 반환 신호 추가
  - 무엇을: 액션 에이전트 반환 JSON `failure_context`에 `scope: action|wbs|trd` 필드 추가
  - 어디에: `opal/agents/opal-task-action-agent/AGENT.md` §결과 반환 형식
  - 왜: 확정 방향 B7 (PM이 코드 실패 vs 설계-범위 에스컬레이션 구분)
  - AC: 반환 형식 JSON 예시에 scope 필드가 있고, PM의 scope별 처리 분기가 SKILL.md Phase 3에 기재되어 있다

- [ ] **F-026** 하네스 자동 루핑 제약 표에 PLAN 재진입 상한 행 신설
  - 무엇을: `opal-harness.md` §자동 루핑 제약 표에 "PLAN 재진입(재설계 루프) — 최대 N회 → 에스컬레이션" 행 추가
  - 어디에: `opal/core/references/opal-harness.md` §1 Guards 자동 루핑 제약
  - 왜: 확정 방향 B7 (Guards SSOT — 무한루프 방지) / PM 검토기준 "하네스 변경 시 SSOT 수정"
  - AC: 자동 루핑 제약 표에 PLAN 재진입 상한 행이 추가되고, verification-loop-guide §7 정합성 표와 일치한다

- [ ] **F-027** verification-loop-guide §3-5 QA 0회 규칙 재조정
  - 무엇을: "QA 설계 이슈 0회 즉시 에스컬레이션"을 B7 재설계 루프와 정합되게 조정 (액션-로컬 설계 결함 = 재PLAN / WBS·TRD 수준 = 에스컬레이션)
  - 어디에: `references/verification-loop-guide.md` §3-5
  - 왜: 배경 분석 (의미 충돌 해소)
  - AC: §3-5가 B7 3계층 라우팅과 모순 없이 서술되어 있다

## 명확화 결과 (4요소 잠금)

| 요소 | 내용 |
|------|------|
| **목표** | oppd를 프로세스(문서 승격) + WBS 세분화(BE/FE) + 액션 완성도 루프(B7) 3축으로 개선 |
| **범위** | `opal/skills/opal-pilot-project-dev/` (SKILL + wbs-guide + verification-loop-guide + parallel-execution-guide), `opal/agents/opal-task-action-agent/AGENT.md`, `opal/agents/opal-fe-agent/AGENT.md`, `opal/core/references/opal-harness.md`. **문서/스킬 정의 변경만** — 런타임 코드(state-tool 등) 변경 없음. WBS 검증기 도구는 후속 태스크 |
| **수용 기준** | F-001~F-027 각 AC 충족 + 영역 간 용어 일관성(triage·scope·계층 명칭 통일) + 하네스 SSOT(F-026)와 가이드(F-021/F-027) 정합 |
| **제약** | 아래 §제약 조건 |

## 제약 조건

- **배포 경계**: 대상은 프로젝트 소스 `opal/...`만 수정한다. 배포본 `~/.opal/` 직접 편집 금지 (install 재배포는 후속). 근거: `.opal/AGENT.md` §금지사항
- **하네스 SSOT**: 루프 상한은 `opal/core/references/opal-harness.md`에만 등록하고 가이드는 참조/정합만 (F-026). 발췌·복제 금지
- **변경이력 의무**: 수정한 SKILL·AGENT·참조 문서의 변경이력 표에 행 추가 (일시 KST + 태스크 031)
- **플랫폼 독립성**: Claude/Cursor/Gemini/Codex 분기 추가 금지 (어댑터 계층 외)
- **WBS 검증기 도구 게이트는 이번 범위 제외** (확정 방향 #2 집행 = 문서 규칙화 우선, 도구는 후속)
- **문서 작업 성격**: 코드 .py/.ts 변경 없음 → 동작 TEST는 문서 정합성·구조 검증(grep/존재/섹션 대조) 중심. RED-first 트랙 적용 여부는 PLAN/TEST-SCENARIO에서 판정

## 기술 스택

- Markdown (스킬/에이전트/참조 문서), YAML frontmatter
- 검증: grep/Bash 기반 문서 구조·정합성 검증 (코드 런타임 없음)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | oppd SKILL | `opal/skills/opal-pilot-project-dev/SKILL.md` | Phase 1~3 프로세스 변경 대상 (#1, F-024) |
| D-2 | 소스 | wbs-guide | `opal/skills/opal-pilot-project-dev/references/wbs-guide.md` | 세분화 기준 변경 대상 (#2, F-010~F-018) |
| D-3 | 소스 | 액션 에이전트 | `opal/agents/opal-task-action-agent/AGENT.md` | B7 루프 변경 대상 (F-020~F-025) |
| D-4 | 소스 | verification-loop-guide | `opal/skills/opal-pilot-project-dev/references/verification-loop-guide.md` | triage·QA 0회 재조정 (F-021, F-027) |
| D-5 | 소스 | parallel-execution-guide | `opal/skills/opal-pilot-project-dev/references/parallel-execution-guide.md` | 병렬=파생 재서술 (F-014) |
| D-6 | 소스 | 하네스 SSOT | `opal/core/references/opal-harness.md` | 자동 루핑 제약 상한 행 (F-026) |
| D-7 | 소스 | FE 에이전트 | `opal/agents/opal-fe-agent/AGENT.md` | FE 3계층 역할 (F-017) |
| D-8 | 설계 | PM 검토기준/금지사항 | `.opal/AGENT.md` | 배포 경계·변경이력·하네스 SSOT 제약 |
| D-9 | 설계 | 프로젝트 정의 | `docs/PROJECT.md` | 프로젝트 구성(FE/BE 영역)·문서 레지스트리 |

> [MUST] `.opal/AGENT.md` §금지사항: "`~/.opal/` 직접 편집 금지 — 항상 프로젝트 소스를 수정한 후 install로 배포한다."
> [MUST] `.opal/AGENT.md` §업무 수행 지침: "하네스 변경 시 `opal/core/references/opal-harness.md`(SSOT)를 수정한다. 다른 곳에서 발췌·복제하지 않는다."
