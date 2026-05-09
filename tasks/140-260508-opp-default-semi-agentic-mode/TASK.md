# TASK: `--semi-agentic` 모드 도입 + 전체 pilot 기본 모드 변경

> 작성일: 2026-05-08 | 작업 유형: 개선 | 적용 스킬: opp | 모드: interactive
> 입력: 사용자 요청 + 사전 대화(2회)
> 출력: TASK.md

## 작업 목표

OPAL 하네스에 **세 번째 모드 `semi-agentic`을 신설**하고 **전체 pilot 7종(opp/opd/opds/opdw/oppd/opsdd/opwt)의 기본 모드로 채택**한다. PLAN 단계까지는 사용자 검토(interactive 동작), EXECUTE 단계 진입 후부터 PM 자율 통과(agentic 동작), CLOSE 진입은 사용자 승인 필수(공통 게이트). 기존 interactive 동작은 `--interactive` 플래그로 명시 호출 가능하게 유지한다.

## 배경

캡틴의 작업 패턴 분석 결과, **PLAN 단계는 설계 결정이 큰 구간으로 사용자 검토가 가장 가치 있고, EXECUTE/TEST는 반복적·기계적이라 자율 + 기록이 효율적**이다. 현재 하네스의 두 모드(interactive / agentic)는 이 패턴에 정확히 맞지 않는다:

- `interactive` (기본): 모든 단계 게이트마다 사용자 승인 — EXECUTE 이후도 매 단계 캡틴 개입 필요 → 효율 저하
- `agentic` (`--agentic` 옵션): TASK부터 CLOSE 직전까지 모두 PM 자율 — PLAN 결정도 자율로 통과 → 설계 검토 기회 상실

이 갭을 메우는 **하이브리드 모드(semi-agentic)** 가 필요하다.

## 배경 분석 (대화에서 도출)

### 두 모드의 자율 시작점 비교

| 단계 | interactive | agentic | 캡틴 원하는 동작 (semi-agentic) |
|------|-------------|---------|-------------------------------|
| TASK 완료 | 사용자 승인 | PM 자율 | 사용자 승인 |
| ANALYSIS 완료 (opd만) | 사용자 승인 | PM 자율 | 사용자 승인 |
| PLAN 완료 | 사용자 승인 | PM 자율 | **사용자 승인** (모드 경계) |
| EXECUTE 완료 | 사용자 승인 | PM 자율 | **PM 자율** |
| TEST 완료 (opd만) | 사용자 승인 | PM 자율 | PM 자율 |
| CLOSE 진입 | 사용자 승인 | 사용자 승인 (예외) | 사용자 승인 (공통) |

→ semi-agentic의 모드 경계: **PLAN 단계 사용자 확인 행 통과 시점**.
   이 시점부터 PM이 EXECUTE/TEST 게이트를 자율 통과하고 AGENTIC-LOG.md에 기록한다.

### 영향 범위 식별

| 영역 | 변경 대상 |
|------|----------|
| 하네스 | `opal-harness.md` 모듈 구조 표 / `opal-harness-semi-agentic.md` 신규 / `opal-harness-interactive.md` 분기 보강 / `opal-harness-agentic.md` 분기 보강 / `harness/state-template.md` 모드 필드 값 |
| pilot 7종 | `opal-pilot-project/SKILL.md` (opp) / `opal-pilot-dev/SKILL.md` (opd) / `opal-pilot-dev-short/SKILL.md` (opds) / `opal-pilot-dev-wireframe/SKILL.md` (opdw) / `opal-pilot-project-dev/SKILL.md` (oppd) / `opal-pilot-sdd/SKILL.md` (opsdd) / `opal-pilot-write-tech/SKILL.md` (opwt) — 모드 분기 + 기본값 + Agentic Mode 절 갱신 |
| state-tool | `~/.opal/tools/state-tool/run.sh` + 내부 로직 — `--mode semi-agentic` 값 추가, EXECUTE 단계 행 진입 후부터 `--auto-pass` 허용하는 검증 로직 |
| 부트스트랩 | `~/.opal/AGENT.md` 모드 설명 / `references/harness/skill-commands.md` 예시 / `references/harness/task-process.md` `state init` 인자 예시 / `op-task/SKILL.md` 헤더 모드 필드 값 |

## 확정된 설계 방향 (대화에서 합의)

| # | 합의 사항 | 합의 내용 |
|---|----------|----------|
| C-1 | 모드 이름 | `semi-agentic` (캡틴 지정) |
| C-2 | 적용 범위 | 전체 pilot 7종 일괄 (opp/opd/opds/opdw/oppd/opsdd/opwt) |
| C-3 | 기본 모드 변경 | 모든 pilot의 기본을 semi-agentic으로. 즉 `//opp 작업` = `//opp --semi-agentic 작업` |
| C-4 | interactive 처리 | `--interactive` 플래그로 명시 호출 가능 (3단계 모드 체계 — semi-agentic 기본 / interactive 명시 / agentic 명시) |
| C-5 | 추적 로그 | AGENTIC-LOG.md 그대로 재사용. EXECUTE 단계 진입 시점부터 자동 생성·기록 |
| C-6 | 모드 경계 | PLAN 단계 "사용자 확인" 행 통과 시점부터 자율. EXECUTE 첫 행부터 `--auto-pass` 허용 |
| C-7 | CLOSE 진입 | agentic과 동일하게 `agentic_close_gate_requires_user`로 캡틴 승인 강제 (공통 게이트 유지) |

## 미확정 사항 (PLAN에서 결정)

| # | 미확정 항목 | PLAN 단계 결정 사유 |
|---|------------|--------------------|
| U-1 | oppd Phase 1/2/3 구조에서 semi-agentic 모드 경계의 정확한 정의 | oppd는 Phase 1(PRD/TRD) + Phase 2(WBS) + Phase 3(액션 실행, 내부는 opds 파이프라인). "PLAN까지 검토"가 Phase 1+2 종료 = 검토 시점인지, 각 액션 내부 PLAN까지 검토인지 PLAN에서 정의 |
| U-2 | opsdd의 SPEC/REVIEW/DESIGN/EXECUTE-LOOP 4 Phase 구조에서 모드 경계 | opsdd 도메인 특수성 — DESIGN Phase가 PLAN에 해당하는지, 각 ACT 내부에 별도 모드 경계를 둘지 PLAN에서 결정 |
| U-3 | 신규 하네스 파일 vs 기존 파일 분기 | `opal-harness-semi-agentic.md` 별도 파일 vs interactive/agentic 두 파일에 분기 추가. PLAN에서 영향 분석 후 결정 |
| U-4 | 기존 진행 중 태스크(STATE.md mode=interactive)의 호환성 처리 | 기 생성된 태스크는 interactive로 그대로 진행시킬지, 마이그레이션 전략 필요한지 PLAN에서 결정 |
| U-5 | state-tool `--auto-pass` 허용 행의 정확한 식별 로직 | 행 ID 기반 vs stage 필드 기반("EXECUTE" 이후) — state.json 스키마 확인 후 PLAN에서 결정 |

## 요구사항

- [x] **F-1**: `~/.opal/references/opal-harness-semi-agentic.md` 신규 파일을 작성한다 (또는 U-3 결정에 따라 기존 파일 분기 보강).
  - 어디에: `~/.opal/references/opal-harness-semi-agentic.md`
  - 왜: C-1 신규 모드 정의 SSOT 필요
  - AC: 파일이 존재하고 모드 경계(C-6) + CLOSE 게이트(C-7) + AGENTIC-LOG 시점(C-5)이 명시된다. interactive/agentic과의 차이가 표로 정리된다.

- [x] **F-2**: pilot 7종 SKILL.md의 "Harness" 섹션 모드 분기 규칙을 3-way로 갱신한다.
  - 어디에: `~/.opal/skills/opal-pilot-{project,dev,dev-short,dev-wireframe,project-dev,sdd,write-tech}/SKILL.md` "Harness" 절
  - 왜: C-2 전체 pilot 일괄 도입 + C-3 기본 모드 변경
  - AC: 각 SKILL.md가 `--semi-agentic`(기본) / `--interactive` / `--agentic` 3-way 분기를 명시하고, 기본값이 semi-agentic임을 분명히 표기한다. 7개 파일 모두 변경 확인.

- [x] **F-3**: `state-tool`이 `--mode semi-agentic` 값을 받고 EXECUTE 단계 행부터 `--auto-pass`를 허용하도록 확장한다.
  - 어디에: `~/.opal/tools/state-tool/run.sh` + 내부 lib 코드
  - 왜: C-5/C-6 구현의 핵심 인프라 — STATE.md 모드 필드와 게이트 통과 동작이 일관되어야 한다
  - AC: `state init --mode semi-agentic` 호출이 성공한다. EXECUTE 단계 첫 행 이전에 `--auto-pass` 사용 시 거부된다(`semi_agentic_pre_execute_auto_pass_denied` 등 명시적 에러). EXECUTE 행 이후 `--auto-pass`는 정상 처리된다. CLOSE 첫 행 `--auto-pass`는 기존 `agentic_close_gate_requires_user`로 거부된다.

- [x] **F-4**: AGENTIC-LOG.md 자동 생성 시점을 EXECUTE 단계 진입(첫 EXECUTE 행 advance)으로 확장한다.
  - 어디에: `~/.opal/references/opal-harness-agentic.md` §8 또는 신규 semi-agentic 하네스 — 생성 시점 정의 / pilot SKILL.md EXECUTE 진입 절차
  - 왜: C-5 추적성 확보 + 인프라 재사용
  - AC: semi-agentic 모드 태스크에서 PLAN 사용자 확인 후 EXECUTE 진입 시 AGENTIC-LOG.md가 자동 생성된다. agentic 모드 태스크는 기존대로 TASK 시작 시점에 생성된다.

- [x] **F-5**: 부트스트랩 문서(AGENT.md, opal-harness.md, skill-commands.md, task-process.md, op-task/SKILL.md)의 모드 설명을 3-way 체계로 갱신한다.
  - 어디에: `~/.opal/AGENT.md` "역할 전환" / `~/.opal/references/opal-harness.md` "모듈 구조" / `harness/skill-commands.md` 예시 / `harness/task-process.md` `state init` 인자 / `~/.opal/skills/op-task/SKILL.md` 헤더 모드 필드
  - 왜: 부트스트랩 시점에 에이전트가 3-way 모드 체계를 인지해야 한다
  - AC: 각 문서에서 모드 옵션이 `interactive | semi-agentic | agentic` 3개로 갱신되며, 기본값이 semi-agentic으로 명시된다.

- [x] **F-6**: STATE.md 템플릿(`harness/state-template.md`) 모드 필드 값에 `semi-agentic`을 추가한다.
  - 어디에: `~/.opal/references/harness/state-template.md` `--mode` 인자 설명 + 모드 필드 예시
  - 왜: STATE.md SSOT 정합성
  - AC: 템플릿에 3개 값 모두 명시되며 semi-agentic이 기본값임이 표기된다.

- [x] **F-7**: 메모리 인덱스(`/Volumes/Data/AIStudio/workspace/ai-framework/.opal/MEMORY.md`)에 확정 기준 추가 또는 캡틴 작업 패턴 메모리 등록.
  - 어디에: `.opal/MEMORY.md` 또는 `.opal/AGENT.md` "확정 기준" 표
  - 왜: 다음 세션에서 이 패턴을 재질문 없이 자동 적용
  - AC: "PLAN까지 사용자 검토, EXECUTE 이후 자율 진행이 캡틴 기본 작업 패턴" 메모리 또는 확정 기준 행이 추가된다.

- [x] **F-8**: 변경 대상 모든 파일에 변경이력 행을 추가한다(`.opal/AGENT.md`의 "프로젝트별 추가 지침" 중 `**문서 변경이력**` 규칙 준수).
  - 어디에: 변경된 모든 SKILL.md / 참조 문서 / 도구 변경이력 표
  - 왜: 프로젝트 컨벤션 — 추적 가능성 규칙
  - AC: 각 변경 파일의 변경이력 표에 일시(KST) + 태스크 번호(140) + 변경 요약이 기재된다.

## 제약 조건

- **하네스 우회 금지** — 새 모드도 Guards(구현 금지 / 디스패치 의무 / CLOSE 진입 게이트) 전부 유지
- **CLOSE 진입 게이트 공통 유지** — semi-agentic도 CLOSE 첫 행 `--auto-pass` 거부, 캡틴 명시 승인 발화 필수 (C-7)
- **하위 호환성** — 기존 진행 중 태스크(STATE.md mode=interactive/agentic)의 동작은 영향받지 않아야 함 (U-4 PLAN에서 결정)
- **배포 경계 준수** — `~/.opal/` 직접 편집 금지, 프로젝트 소스(`opal/core/`, `skills/`, `agents/` 등) 수정 후 install로 배포 (`.opal/AGENT.md` 금지사항)
- **state-tool SSOT 유지** — STATE.md 마크다운 직접 편집 금지, `state-tool` 명령으로만 갱신 (`.opal/AGENT.md` 금지사항)
- **인용 규칙 준수** — `references/harness/citation-rules.md` 적용 (PLAN/TASK/ANALYSIS 산출물 작성 시)

## 기술 스택

- Markdown 문서 (하네스 / SKILL.md / 참조 문서) — 주 변경 대상
- Bash 래퍼 + Node.js (state-tool 내부) — F-3 변경 대상
- OPAL 자체 인프라 (slash command / agent dispatch / state-tool) — 변경 없이 재사용

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계(SSOT) | opal-harness.md | `~/.opal/references/opal-harness.md` | 모듈 구조 + 서브 하네스 분기 규칙 (F-5) |
| D-2 | 설계 | opal-harness-interactive.md | `~/.opal/references/opal-harness-interactive.md` | interactive 모드 게이트 처리 — semi-agentic의 PLAN 이전 동작 참조 |
| D-3 | 설계 | opal-harness-agentic.md | `~/.opal/references/opal-harness-agentic.md` | agentic 모드 자율 게이트 처리 + AGENTIC-LOG 정의 — semi-agentic의 EXECUTE 이후 동작 참조 (F-4) |
| D-4 | 설계 | state-template.md | `~/.opal/references/harness/state-template.md` | STATE.md 모드 필드 값 (F-6) |
| D-5 | 설계 | task-process.md | `~/.opal/references/harness/task-process.md` | `state init --mode` 인자 정의 (F-5) |
| D-6 | 소스 | pilot 7종 SKILL.md | `~/.opal/skills/opal-pilot-{project,dev,dev-short,dev-wireframe,project-dev,sdd,write-tech}/SKILL.md` | 모드 분기 변경 대상 (F-2) |
| D-7 | 도구 | state-tool | `~/.opal/tools/state-tool/run.sh` + 내부 lib | `--mode semi-agentic` 인자 + auto-pass 허용 로직 (F-3) |
| D-8 | 부트스트랩 | AGENT.md | `~/.opal/AGENT.md` | 역할 전환 + 부트스트랩 모드 설명 (F-5) |
| D-9 | 컨벤션 | docs/CONVENTIONS.md | `/Volumes/Data/AIStudio/workspace/ai-framework/docs/CONVENTIONS.md` | 프로젝트 컨벤션 — PM Gate에서 자동 진단 적용 |
| D-10 | 컨벤션 | .opal/AGENT.md (프로젝트) | `/Volumes/Data/AIStudio/workspace/ai-framework/.opal/AGENT.md` | 금지사항·확정 기준 (F-7) |
| D-11 | 메모리 | .opal/MEMORY.md | `/Volumes/Data/AIStudio/workspace/ai-framework/.opal/MEMORY.md` | 확정 기준/패턴 등록 (F-7) |
