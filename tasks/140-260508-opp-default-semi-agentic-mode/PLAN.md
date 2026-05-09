# PLAN: `--semi-agentic` 모드 도입 + 전체 pilot 기본 모드 변경

> 작성일: 2026-05-09
> 입력: TASK.md
> 출력: PLAN.md

본 PLAN은 OPAL 하네스에 세 번째 모드 `semi-agentic`을 신설하고, 전체 pilot 7종(opp/opd/opds/opdw/oppd/opsdd/opwt)의 기본 모드로 채택하기 위한 구현 설계서이다. PLAN 단계까지는 사용자 검토(interactive 동작), EXECUTE 단계 진입 후부터 PM 자율 통과(agentic 동작)이며, CLOSE 진입은 사용자 승인 필수(공통 게이트)이다.

---

## 1. 현황 조사

### 참조 문서 (PLAN 작성 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계(SSOT) | opal-harness.md | `opal/core/references/opal-harness.md` | 모듈 구조 표(§2) + 공통 Guards(§1) — 모드 분기 SSOT (F-5) |
| D-2 | 설계 | opal-harness-interactive.md | `opal/core/references/opal-harness-interactive.md` | interactive 게이트 동작 — semi-agentic의 PLAN 이전 동작 참조 (F-1) |
| D-3 | 설계 | opal-harness-agentic.md | `opal/core/references/opal-harness-agentic.md` | agentic 자율 게이트 + AGENTIC-LOG 정의 — semi-agentic의 EXECUTE 이후 동작 + CLOSE 게이트 공통 참조 (F-1/F-4/U-3) |
| D-4 | 설계 | state-template.md | `opal/core/references/harness/state-template.md` | STATE.md 모드 필드 값 + state init 인자 SSOT (F-6) |
| D-5 | 설계 | task-process.md | `opal/core/references/harness/task-process.md` | `state init --mode` 인자 정의 + TASK 공통 프로세스 (F-5) |
| D-6 | 설계 | skill-commands.md | `opal/core/references/harness/skill-commands.md` | 쌍슬래시 커맨드 예시 갱신 (F-5) |
| D-7 | 소스 | opal-pilot-project/SKILL.md | `opal/skills/opal-pilot-project/SKILL.md` | opp pilot — Harness 모드 분기 + Agentic Mode 절 (F-2) |
| D-8 | 소스 | opal-pilot-dev/SKILL.md | `opal/skills/opal-pilot-dev/SKILL.md` | opd pilot — Harness 모드 분기 + Agentic Mode 절 (F-2) |
| D-9 | 소스 | opal-pilot-dev-short/SKILL.md | `opal/skills/opal-pilot-dev-short/SKILL.md` | opds pilot — Harness 모드 분기 (F-2) |
| D-10 | 소스 | opal-pilot-dev-wireframe/SKILL.md | `opal/skills/opal-pilot-dev-wireframe/SKILL.md` | opdw pilot — Harness 모드 분기 (F-2) |
| D-11 | 소스 | opal-pilot-project-dev/SKILL.md | `opal/skills/opal-pilot-project-dev/SKILL.md` | oppd pilot — Phase 1/2/3 구조 모드 경계 정의 (F-2 / U-1) |
| D-12 | 소스 | opal-pilot-sdd/SKILL.md | `opal/skills/opal-pilot-sdd/SKILL.md` | opsdd pilot — 6 Phase 구조 모드 경계 정의 (F-2 / U-2) |
| D-13 | 소스 | opal-pilot-write-tech/SKILL.md | `opal/skills/opal-pilot-write-tech/SKILL.md` | opwt pilot — Harness 모드 분기 + Agentic Mode 절 신설 (F-2) |
| D-14 | 도구 | state-tool/state_tool.py | `opal/tools/state-tool/state_tool.py` | `--mode` choices / `--auto-pass` 거부 로직 / `check_close_gate` (F-3 / U-5) |
| D-15 | 도구 | state-tool/run.sh | `opal/tools/state-tool/run.sh` | Bash 래퍼 — venv Python 호출, 인자 변경 없음 |
| D-16 | 부트스트랩 | opal/AGENT.md | `opal/AGENT.md` | 역할 전환 + 부트스트랩 모드 설명 (F-5) |
| D-17 | 소스 | op-task/SKILL.md | `opal/skills/op-task/SKILL.md` | TASK.md 헤더 모드 필드 값 + state init 인자 (F-5) |
| D-18 | 컨벤션 | docs/CONVENTIONS.md | `docs/CONVENTIONS.md` | 구현 규칙 — Guards/디스패치/State/Citation/배포 경계/플랫폼 분기 |
| D-19 | 컨벤션 | .opal/AGENT.md | `.opal/AGENT.md` | 금지사항·확정 기준 + 캡틴 작업 패턴 등록 (F-7) |
| D-20 | 메모리 | .opal/MEMORY.md | `.opal/MEMORY.md` | last_task_number(140) + 메모리 인덱스 (F-7) |
| D-21 | 인용 | citation-rules.md | `opal/core/references/harness/citation-rules.md` | PLAN/EXECUTE 산출물 인용 규칙 + [MUST] 토큰 규정 |
| D-22 | 배포 | install-mac.sh | `scripts/install-mac.sh` | `install_opal_references()` 전체 복사 — 신규 하네스 파일 자동 포함 검증 (F-1) |
| D-23 | 설계 | state-tool README | `opal/tools/state-tool/README.md` | state-tool 사용법 — 인자 추가 시 갱신 대상 (F-3) |

> 인용 형식: `opal/core/references/harness/citation-rules.md` §3.1 참조.

### 핵심 제약 ([MUST] 인용)

다음 제약은 본 PLAN의 모든 설계 결정 및 후속 EXECUTE 단계에서 재해석 없이 그대로 준수한다.

- [MUST] `docs/CONVENTIONS.md` §구현 규칙 — Guards: "사용자가 명시적으로 '승인', '진행해', '구현해' 등의 실행 허가를 내리기 전까지 코드를 작성하거나 파일을 생성·수정하지 않는다."
- [MUST] `docs/CONVENTIONS.md` §구현 규칙 — Guards: "CLOSE 단계 진입 직전에는 사용자의 명시적 확인(`승인`/`확인`/`확인완료`)이 반드시 있어야 한다 (agentic 모드에서도 유지)."
- [MUST] `docs/CONVENTIONS.md` §구현 규칙 — 디스패치 의무: "오케스트레이터 SKILL.md에서 '워커 디스패치'로 정의된 단계(ANALYSIS/PLAN/EXECUTE 등)는 반드시 서브에이전트를 디스패치한다. PM이 직접 실행으로 대체하지 않는다."
- [MUST] `docs/CONVENTIONS.md` §구현 규칙 — State 관리: "파이프라인 STATE.md 행 상태(⬜/🔄/✅) 변경은 `~/.opal/tools/state-tool/run.sh`로만 수행한다. 마크다운 표 직접 편집 금지."
- [MUST] `docs/CONVENTIONS.md` §구현 규칙 — 변경이력 작성 의무: "스킬·에이전트·참조 문서를 변경하면 '## 변경이력' 표에 행을 추가한다. 일시는 `YYYY-MM-DD HH:mm` (KST), 버전은 semver, 변경내용은 태스크 번호를 괄호로 포함 — 예: `(140)`."
- [MUST] `docs/CONVENTIONS.md` §구현 규칙 — 배포 경계: "`~/.opal/` 배포 파일을 직접 편집하지 않는다. 변경은 항상 프로젝트 소스(`opal/`, `skills/`, `agents/`, `community-skills/`, `scripts/`)에서 수행한다."
- [MUST] `docs/CONVENTIONS.md` §구현 규칙 — Citation Rules: "TASK.md / PLAN.md / ANALYSIS.md / QA 산출물 등을 작성할 때 모든 주장은 근거를 인용한다 (`{경로}:{라인}` 또는 `docs/문서명 §섹션`). `[MUST]` 토큰이 붙은 항목은 인용 누락 시 산출물 부적합 처리."
- [MUST] `docs/CONVENTIONS.md` §구현 규칙 — 플랫폼 분기 격리: "Claude / Cursor / Gemini / Antigravity 등 플랫폼별 차이는 어댑터 계층(부트스트래퍼·`emit_platform_agent_adapter`·MCP install 분기)에서만 흡수한다. 스킬·에이전트 본문에 플랫폼 조건문을 추가하지 않는다."
- [MUST] `.opal/AGENT.md` §금지사항: "**`~/.opal/` 직접 편집 금지** — 항상 프로젝트 소스를 수정한 후 install로 배포한다."
- [MUST] `.opal/AGENT.md` §금지사항: "**STATE.md 마크다운 직접 편집 금지** — `state-tool`만 사용."
- [MUST] `.opal/AGENT.md` §금지사항: "**하네스 우회 금지** — Guards/Gates를 PM 임의 판단으로 건너뛰지 않는다 (특히 CLOSE 진입 게이트)."

### 관련 파일

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| `opal/core/references/opal-harness.md` | 공통 하네스 SSOT — 모듈 구조 표 + Guards | 필요 | `opal/core/references/opal-harness.md:60-79` (모듈 구조 §2) |
| `opal/core/references/opal-harness-interactive.md` | interactive 모드 서브 하네스 | 필요 (분기 보강) | `opal/core/references/opal-harness-interactive.md:1-7` (도입 블록) |
| `opal/core/references/opal-harness-agentic.md` | agentic 모드 서브 하네스 | 필요 (분기 보강) | `opal/core/references/opal-harness-agentic.md:7-21` (§1 모드 정의 + §2 활성화) |
| `opal/core/references/opal-harness-semi-agentic.md` | semi-agentic 신규 서브 하네스 | 신규 생성 | (D-1 §2 모듈 테이블에 행 추가 필요) |
| `opal/core/references/harness/state-template.md` | STATE.md 템플릿 + state init 인자 | 필요 (mode choices 3-way 갱신) | `opal/core/references/harness/state-template.md:11-18` |
| `opal/core/references/harness/task-process.md` | TASK 공통 프로세스 + state init 인자 | 필요 | `opal/core/references/harness/task-process.md:30-39` |
| `opal/core/references/harness/skill-commands.md` | 쌍슬래시 커맨드 예시 | 필요 (예시에 `--semi-agentic`/`--interactive` 추가) | `opal/core/references/harness/skill-commands.md:26-31` |
| `opal/AGENT.md` | 부트스트랩 + 역할 전환 | 필요 (소유자 오버라이드 표 / 도메인 지식 표) | `opal/AGENT.md` (도메인 지식 "Agentic Mode" 행) |
| `opal/skills/op-task/SKILL.md` | TASK.md 헤더 모드 필드 + state init 인자 | 필요 | `opal/skills/op-task/SKILL.md:109` (헤더 라인) / `:197` (state init mode) / `:225` (체크리스트) |
| `opal/skills/opal-pilot-project/SKILL.md` (opp) | Harness 분기 + Agentic Mode 절 | 필요 (3-way) | `opal/skills/opal-pilot-project/SKILL.md:14-20` (Harness) / `:177-203` (Agentic Mode) |
| `opal/skills/opal-pilot-dev/SKILL.md` (opd) | Harness 분기 + Agentic Mode 절 | 필요 (3-way) | `opal/skills/opal-pilot-dev/SKILL.md:14-20` / `:276-...` |
| `opal/skills/opal-pilot-dev-short/SKILL.md` (opds) | Harness 분기 + Agentic Mode 절 | 필요 (3-way) | `opal/skills/opal-pilot-dev-short/SKILL.md:14-20` |
| `opal/skills/opal-pilot-dev-wireframe/SKILL.md` (opdw) | Harness 분기 + Agentic Mode 절 | 필요 (3-way) | `opal/skills/opal-pilot-dev-wireframe/SKILL.md:14-20` |
| `opal/skills/opal-pilot-write-tech/SKILL.md` (opwt) | Harness 분기 + Agentic Mode 절 신설 | 필요 (3-way + 신규 절) | `opal/skills/opal-pilot-write-tech/SKILL.md:14-22` |
| `opal/skills/opal-pilot-project-dev/SKILL.md` (oppd) | Harness 분기 + Phase 경계 정의 (U-1) | 필요 (3-way) | `opal/skills/opal-pilot-project-dev/SKILL.md:22-32` / `:655-688` |
| `opal/skills/opal-pilot-sdd/SKILL.md` (opsdd) | Harness 분기 + Phase 경계 정의 (U-2) | 필요 (3-way) | `opal/skills/opal-pilot-sdd/SKILL.md:21-30` / `:442-500` |
| `opal/tools/state-tool/state_tool.py` | --mode choices / `--auto-pass` 거부 로직 | 필요 | `opal/tools/state-tool/state_tool.py:64-67` (ERROR_CODES) / `:311-348` (check_close_gate) / `:1179-1180` (mode choices) |
| `opal/tools/state-tool/run.sh` | Bash 래퍼 (변경 없음) | 변경 불필요 | `opal/tools/state-tool/run.sh:12` |
| `opal/tools/state-tool/README.md` | state-tool 사용법 문서 | 필요 (mode choices 갱신) | (Read 미수행 — EXECUTE 진입 시 대상 파일 Read 후 갱신) |
| `.opal/AGENT.md` | PM 프로필 — 확정 기준 + 도메인 지식 | 필요 (확정 기준 행 추가, 도메인 지식 모드 행 갱신) | `.opal/AGENT.md:51` (도메인 지식 Agentic Mode) / `:71-73` (확정 기준 표) |
| `.opal/MEMORY.md` | 메모리 인덱스 | 필요 (preferences 메모리 또는 확정 기준 등록) | `.opal/MEMORY.md:23-26` |
| `scripts/install-mac.sh` | 배포 스크립트 | 변경 불필요 (검증만) | `scripts/install-mac.sh:934-948` (`install_opal_references` cp -Rf 전체 복사) |
| `tasks/140-260508-opp-default-semi-agentic-mode/STATE.md` | 본 태스크 STATE | 변경 없음 (본 PLAN 작성은 interactive로 진행 중) | 본 태스크 STATE.md |

### 현재 상태

조사 결과 OPAL 하네스는 현재 **2개 모드 체계**(interactive 기본 / agentic opt-in)로 운영된다. 핵심 사실:

1. **하네스 모듈 구조**: `opal-harness.md §2` (D-1)가 모드별 서브 하네스 매핑 테이블의 SSOT이며, 현재 2개 행(interactive/agentic)으로 구성됨. 새 모드 추가 시 "이 테이블에 행을 추가하고, 서브 하네스 파일을 생성한다"고 명시(`opal-harness.md:78`).
2. **agentic 활성화 트리거**: `--agentic` 플래그가 유일한 분기 키워드. 7개 pilot SKILL.md가 모두 동일 패턴(`--agentic` 있음 → agentic 서브 하네스, 없음 → interactive 서브 하네스)으로 분기.
3. **state-tool mode choices**: `state_tool.py:1180` `choices=["interactive","agentic"]`로 하드코딩. CLOSE 게이트 거부는 `mode == "agentic"` 조건으로 동작(`state_tool.py:326`). `auto_pass_in_interactive_mode` 검증은 `mode == "interactive"` 시 owner=auto 차단(`state_tool.py:950`).
4. **CLOSE 게이트 공통**: `agentic_close_gate_requires_user`(D-3 §7 + state_tool.py:67)는 agentic 모드에서 CLOSE 첫 행 `--auto-pass`를 거부. interactive에서는 사용자 발화 후 `--owner user`로 mark하는 절차가 별도 필요.
5. **AGENTIC-LOG.md 생성 시점**: 현재 agentic 모드 시작 시 즉시 생성(`opal-harness-agentic.md §8 / :159`). semi-agentic은 EXECUTE 진입 시점부터 생성으로 시점 분기 필요.
6. **pilot별 Phase 구조 차이**:
   - opp/opd/opds/opdw/opwt: TASK→PLAN→(EXECUTE/TEST)→CLOSE 단순 구조 — PLAN 단계 사용자 확인 행이 명확한 모드 경계점
   - oppd: Phase 1(opwt 위임 PRD/TRD) + Phase 2(WBS) + Phase 3(액션 실행) — Phase 2까지가 "PLAN-equivalent", Phase 3가 "EXECUTE-equivalent"
   - opsdd: TASK + SPEC(Phase 1) + REVIEW(Phase 2) + DESIGN(Phase 3) + EXECUTE-LOOP(Phase 4) + VERIFY(Phase 5) + CLOSE(Phase 6) — DESIGN까지가 "PLAN-equivalent", EXECUTE-LOOP부터 "EXECUTE-equivalent"
7. **install-mac.sh**: `install_opal_references()`(D-22 / `scripts/install-mac.sh:934-948`)가 `cp -Rf "$ref_src"/. "$ref_dst"/` 전체 복사 — 신규 `opal-harness-semi-agentic.md` 파일 추가 시 자동 배포되며, install 스크립트 자체 수정 불필요(검증만 필요).

### 영향 범위

| 영역 | 영향 | 비고 |
|------|------|------|
| 하네스 (5 파일) | 신규 1개 + 수정 4개 | semi-agentic SSOT 신설 + 공통 모듈 표 + interactive/agentic 분기 보강 + state-template/task-process/skill-commands 모드 갱신 |
| pilot 7종 SKILL.md | 모두 수정 | Harness 절 3-way 분기 + Agentic Mode 절을 "Agentic / Semi-Agentic 흐름" 섹션으로 확장 (opwt는 신규 절 추가). 기본 모드 명시. |
| state-tool | state_tool.py 1 파일 + README.md 1 파일 | choices에 `semi-agentic` 추가 + 신규 에러 코드 1종(`semi_agentic_pre_execute_auto_pass_denied`) + EXECUTE 행 식별 로직 + check_close_gate / build_rows_from_* / cmd_validate 분기 보강 |
| 부트스트랩 | opal/AGENT.md / op-task/SKILL.md | 모드 옵션 표시 갱신 + TASK.md 헤더 모드 필드 3-way |
| 프로젝트 메모리 | .opal/AGENT.md / .opal/MEMORY.md | 확정 기준 행 추가 + 메모리 등록 |
| install/배포 | install-mac.sh | 변경 없음 — 검증만 (cp -Rf 전체 복사이므로 신규 파일 자동 포함) |
| 기존 진행 중 태스크 | 없음 (하위 호환) | 기존 STATE.md mode=`interactive`/`agentic`은 그대로 유효, 신규 행은 `semi-agentic` 추가만 (U-4 결정) |

---

## §결정 사항 (TASK.md 미확정 5건)

본 절은 TASK.md §미확정 사항 U-1 ~ U-5에 대해 옵션 비교 후 채택안을 명시한다. 후속 EXECUTE는 본 결정을 SSOT로 삼는다.

### D-DEC-1: oppd Phase 경계 (U-1 결정)

**문제**: oppd는 Phase 1(opwt 위임 PRD/TRD) + Phase 2(WBS) + Phase 3(액션 실행, 내부는 opds 파이프라인)이다. semi-agentic 모드에서 "PLAN까지 사용자 검토" 경계가 어디인가?

| 옵션 | 모드 경계 | 장점 | 단점 |
|------|---------|------|------|
| A | Phase 1+2 종료 시점 (Phase 2 사용자 확정 행 통과 후) | 캡틴이 PRD/TRD/WBS를 모두 확정한 시점이 자연스러운 경계. 액션 실행은 반복적·기계적이라 자율 + 기록이 효율적이라는 TASK.md §배경의 패턴과 정합. | Phase 3 액션 내부 PLAN 결정도 자율 통과 — 큰 설계 결정 누락 위험 |
| B | 각 액션 내부 opds PLAN 단계까지 사용자 검토 | 액션별 PLAN 결정 보호 | 액션이 N개일 때 N번 사용자 확인 — agentic의 효율성 손실. semi-agentic 본래 취지("PLAN 검토는 가치 있지만 EXECUTE는 자율")와 충돌 |
| C | 옵션 A + 액션 내부에서 캡틴이 명시적으로 `--interactive` 부여한 액션만 PLAN 검토 | 유연성 | 복잡성 증가. 사용자 발화 의존 |

**채택**: **옵션 A** — Phase 2 사용자 확정 행 통과 시점을 모드 경계로 한다. Phase 3 액션은 자율 실행 + AGENTIC-LOG 기록.

**근거**: TASK.md §배경 "PLAN 단계는 설계 결정이 큰 구간으로 사용자 검토가 가장 가치 있고, EXECUTE/TEST는 반복적·기계적이라 자율 + 기록이 효율적이다." (→ TASK.md L13). oppd의 Phase 1+2(PRD/TRD/WBS)가 설계 결정의 합산점이고, Phase 3는 실행이므로 의미적으로 "PLAN-equivalent까지 검토 / EXECUTE-equivalent부터 자율"과 일치. 옵션 B는 사용자 보고가 N번 발생해 모드 도입 효과 무력화. 옵션 C는 별도 플래그 도입으로 3-way 모드 체계가 복잡해져 KISS 원칙 위반.

**부수 결정**: Phase 1 내부 opwt 위임 결과(PRD/TRD)는 Phase 1 사용자 확정 행에서 검토하므로 별도 모드 경계가 추가되지 않는다. opwt가 Phase 1 내부에서 호출되어도 oppd STATE.md의 Phase 1 사용자 확정 행 통과 시점이 단일 경계로 작동.

### D-DEC-2: opsdd Phase 경계 (U-2 결정)

**문제**: opsdd는 TASK + SPEC(Phase 1) + REVIEW(Phase 2) + DESIGN(Phase 3) + EXECUTE-LOOP(Phase 4) + VERIFY(Phase 5) + CLOSE(Phase 6) 6단계. PLAN-equivalent가 어디인가?

| 옵션 | 모드 경계 | 장점 | 단점 |
|------|---------|------|------|
| A | DESIGN(Phase 3) 사용자 Gate 통과 시점 | DESIGN이 SPEC-PLAN.md(아키텍처 + ACT 분해)를 산출하는 PLAN 등가 단계. WHAT 단계(SPEC/REVIEW)와 HOW 단계의 자연 분기 → EXECUTE-LOOP 진입 = "실행 허가" 시점이라는 opsdd 자체 정의(`opal-pilot-sdd/SKILL.md:467`)와 일치 | 각 ACT 내부 PLAN 결정도 자율 — 단, 본 PLAN은 SPEC-PLAN.md에 이미 ACT 분해가 확정되어 있으므로 ACT별 PLAN은 op-dev-plan 단계의 세부 사항 |
| B | 각 ACT 내부 PLAN까지 사용자 Gate | ACT별 결정 보호 | ACT 수만큼 사용자 확인 발생 — semi-agentic 효과 무력화 |
| C | SPEC(Phase 1) 사용자 Gate까지만 검토, REVIEW부터 자율 | 빠른 진입 | DESIGN(아키텍처 결정)을 자율 통과 — 큰 설계 결정 누락 위험 |

**채택**: **옵션 A** — DESIGN(Phase 3) 사용자 Gate 통과 시점을 모드 경계로 한다. EXECUTE-LOOP / VERIFY / CLOSE는 자율(단, CLOSE 진입은 공통 게이트로 사용자 승인 유지).

**근거**: opsdd의 EXECUTE-LOOP 진입 = "구현 금지 원칙의 '실행 허가'를 PM이 판단"이라는 자체 정의(`opal-pilot-sdd/SKILL.md:467`)는 곧 "EXECUTE 진입부터 자율"이라는 semi-agentic 모드 경계와 정확히 일치. 또한 DESIGN Phase는 SPEC-PLAN.md를 산출하는 PLAN-equivalent이므로 의미적 정합. ACT 내부 PLAN(op-dev-plan)은 SPEC-PLAN의 분해 결과를 따르는 세부 실행이므로 자율 영역으로 분류. 옵션 B는 ACT 수만큼 사용자 Gate가 늘어 모드 도입 효과 상실. 옵션 C는 DESIGN을 자율 통과시켜 큰 설계 결정 누락 위험.

**부수 결정**: WHAT 단계(SPEC/REVIEW)는 사용자 Gate 그대로 유지(interactive 동작). HOW 단계의 첫 행인 DESIGN 작업 행도 사용자 검토 영역에 포함. DESIGN PM Gate / DESIGN 사용자 확인 행 통과 = 모드 경계 = EXECUTE-LOOP 첫 행부터 `--auto-pass` 허용.

### D-DEC-3: 신규 하네스 파일 vs 기존 분기 보강 (U-3 결정)

**문제**: `opal-harness-semi-agentic.md` 별도 파일을 신설할지, 기존 두 파일(`opal-harness-interactive.md` / `opal-harness-agentic.md`)에 분기를 추가할지.

| 옵션 | 구조 | 장점 | 단점 |
|------|------|------|------|
| A | `opal-harness-semi-agentic.md` 신규 파일 + 모듈 표에 행 추가 | 모드별 SSOT 명확 / 로딩 규칙(`opal-harness.md:72-78`)이 "1 모드 = 1 서브 하네스 1개 추가 Read"로 단순. 신규 모드 추가 시 기존 패턴 일관 적용. semi-agentic 고유 동작(EXECUTE 진입 시 AGENTIC-LOG 생성, PLAN까지 interactive 흐름, EXECUTE 이후 agentic 흐름)을 단일 파일에서 표현 가능. | 새 파일 1개 추가 |
| B | 기존 두 파일 분기 보강(예: `interactive.md`에 "semi-agentic에서는 PLAN까지 동일" 섹션, `agentic.md`에 "semi-agentic에서는 EXECUTE 이후 동일" 섹션) | 새 파일 없음 | "semi-agentic이 무엇인가"를 알기 위해 두 파일을 읽어야 함. 로딩 규칙(`opal-harness.md:72-78`)이 "모드별 서브 하네스 1개 추가 Read"이므로 두 파일을 모두 읽게 하면 토큰 비용 증가. SSOT 분산. |

**채택**: **옵션 A** — `opal-harness-semi-agentic.md` 신규 파일을 생성한다. 모듈 구조 표에 3번째 행을 추가한다(D-1 §2).

**근거**: `opal-harness.md:78` 명시: "새 모드 추가 시: 이 테이블에 행을 추가하고, 서브 하네스 파일을 생성한다." — 현 구조가 이미 옵션 A를 전제로 설계됨. 또한 컨벤션 [MUST] 배포 경계 / 변경이력 의무를 적용할 때 단일 파일이 추적·검증·인용 모두 단순. semi-agentic은 PLAN 시점 분기점·EXECUTE 진입 시 AGENTIC-LOG 생성·CLOSE 공통 게이트 등 고유 명세가 충분해 단독 SSOT를 정당화.

### D-DEC-4: 기존 진행 중 태스크 호환성 (U-4 결정)

**문제**: 기 생성된 태스크의 STATE.md `mode=interactive` 또는 `mode=agentic`이 본 PLAN 변경 후 어떻게 동작해야 하는가? 마이그레이션 전략.

| 옵션 | 정책 | 장점 | 단점 |
|------|------|------|------|
| A | 신규 태스크부터만 `semi-agentic` 기본값 적용. 기존 태스크는 `mode` 그대로 유지 (소급 변경 없음) | 기존 진행 중 태스크 안전 / 변경이력 추적 가능 / 캡틴이 의도한 모드 그대로 진행 | 사용자가 신·구 태스크에서 다른 동작을 경험 (단, 기존 태스크는 곧 완료될 단기 산출물이므로 영향 미미) |
| B | install 시 기존 태스크 `mode=interactive` 행을 `mode=semi-agentic`으로 일괄 마이그레이션 | 일관성 | 진행 중인 태스크의 모드 동작이 갑자기 변경 — 캡틴 합의 없는 자동 변경은 [MUST] Guards 위반 가능성 |
| C | 새 태스크부터 적용 + 진행 중 태스크에 대해 다음 단계 진입 시점에 캡틴에게 모드 변경 의사 확인 | 안전 + 일관성 | 복잡성 증가 / 모든 pilot에 마이그레이션 핸들러 추가 |

**채택**: **옵션 A** — 신규 태스크부터만 `semi-agentic` 기본값 적용. 기존 태스크는 STATE.md `mode` 필드 그대로 유지하고 동작도 그대로 유지한다.

**근거**: `opal/core/references/harness/state-template.md:101` 레거시 호환 원칙("기존 STATE.md(...)는 소급 변경하지 않는다. 신규 태스크부터 (...) 반영한다.")의 일관 적용. citation-rules.md §5 "레거시 호환 — 기존 산출물 소급 변경 불필요" 원칙과 정합. 진행 중 태스크의 자동 모드 변경은 캡틴 합의 없이 동작을 바꾸는 행위로 Guards 위반 위험. 옵션 B는 캡틴이 사전에 합의한 모드(interactive)에서 갑자기 자율 통과 동작으로 바뀌는 문제. 옵션 C는 마이그레이션 핸들러 7개 pilot에 추가하는 비용 대비 효익 부족(기존 태스크는 곧 완료).

**부수 결정**: state-tool은 `mode=interactive` 또는 `mode=agentic` 행을 그대로 받아들이며, 새로 도입되는 `mode=semi-agentic` 행만 EXECUTE 진입 후 `--auto-pass` 허용 검증 로직을 적용한다. 기존 모드 행에 대한 검증 로직은 변경하지 않는다.

### D-DEC-5: state-tool `--auto-pass` 허용 행 식별 로직 (U-5 결정)

**문제**: semi-agentic 모드에서 EXECUTE 단계 진입 후부터 `--auto-pass` 허용. 어떻게 "EXECUTE 진입 후"를 판별하는가?

| 옵션 | 식별 로직 | 장점 | 단점 |
|------|---------|------|------|
| A | 행 ID 기반 — 각 pilot 별로 EXECUTE 시작 행 ID를 SKILL.md에 명시 | 단순 | pilot별로 행 구성이 다름 (특히 oppd Phase 1/2/3, opsdd 6 Phase). SKILL.md 변경 시마다 행 ID 동기화 필요 — 유지보수 비용 |
| B | stage 필드 기반 — `stage` 필드가 PLAN-equivalent 단계 종료 후(즉 EXECUTE/TEST/EXECUTE-LOOP/CLOSE 단계 행)면 허용 | pilot 무관, stage 필드는 STAGE_ENUM(state_tool.py:28)으로 표준화됨 | "PLAN-equivalent"의 정의가 pilot별로 다름 (oppd는 Phase 2까지, opsdd는 DESIGN까지) |
| C | 옵션 B 변형 — pilot별 "PLAN-equivalent stage 집합"을 state_tool.py에 매핑 테이블로 정의. 각 행의 stage가 매핑 테이블의 "EXECUTE-equivalent 이후" stage 집합에 속하면 허용 | 정확 + 변경 격리 | state_tool.py에 pilot 의존성 추가 |
| D | "EXECUTE 진입 트리거" 메타데이터 행 도입 — STATE.md에 "EXECUTE 진입" 마킹 행을 추가하고, state-tool이 그 시점부터 `--auto-pass` 허용 | 명시적 | STATE.md 행 구성 변경 — 모든 pilot의 SKILL.md 도메인 치환값 갱신 필요 + 7개 행 마이그레이션 |
| E | 정방향 스캔 기반 — state.json의 `rows[]`를 정방향 스캔하며 "PLAN/SPEC/REVIEW/DESIGN/WBS/ANALYSIS/WIREFRAME 단계의 사용자 확인 행이 모두 done이면 그 이후 행은 EXECUTE 등가로 간주" — `mode_boundary_passed` 플래그 도입 | pilot 의존성 없음 / stage 필드의 일반성 활용 | 구현 약간 복잡 |

**채택**: **옵션 E (변형)** — `state.json` 메타에 `mode_boundary_stages: ["TASK", "ANALYSIS", "PLAN", "SPEC", "REVIEW", "DESIGN", "WBS", "WIREFRAME"]` 상수(state_tool.py)를 정의하고, "이 stage 집합 외(즉 EXECUTE/TEST/EXECUTE-LOOP/VERIFY/CLOSE 등)" 행에 대해서만 `mode=semi-agentic`인 경우 `--auto-pass`를 허용한다.

추가로, EXECUTE 등가 stage 진입 검증은 "현재 행의 stage가 boundary 집합에 속하면 거부, 속하지 않으면 허용"으로 단순화한다(즉 stage 필드 기반 직접 판별).

**근거**:
- 옵션 A는 행 ID 변동 시마다 동기화 비용 — pilot SKILL.md "STATE.md 도메인 치환값" 변경 시 state-tool 코드 동기 필요(`opal/skills/opal-pilot-project/SKILL.md:142-164`).
- 옵션 B는 pilot 무관성과 단순성을 살려 의도와 정합.
- 옵션 C는 pilot 매핑이 state_tool.py에 들어가 SSOT 위반(모드 경계는 SKILL.md에 정의되어야 함). 옵션 E는 stage 집합을 한 번만 정의하여 SSOT 단일화.
- 옵션 D는 STATE.md 행 구성 변경으로 7개 pilot 마이그레이션 필요 — 비용 큼.
- 옵션 E의 boundary stage 집합은 STAGE_ENUM(`state_tool.py:28-32`)에서 "구현 전 단계" 의미로 골라낸 것이며, 이 집합은 pilot 무관하게 정의 가능.

**구현 명세 (state_tool.py)**:
- 신규 상수: `MODE_BOUNDARY_STAGES = {"TASK","ANALYSIS","PLAN","SPEC","REVIEW","DESIGN","WBS","WIREFRAME"}`
- 신규 에러 코드: `semi_agentic_pre_execute_auto_pass_denied` — "semi-agentic 모드에서 EXECUTE 등가 단계 이전 행(row {row_id}, stage={stage})에 --auto-pass 사용 불가"
- `cmd_mark`(`state_tool.py:791-`)에 다음 검증 추가 (CLOSE 게이트 검증 직후):
  ```python
  if args.auto_pass and state.get("mode") == "semi-agentic":
      if row["stage"] in MODE_BOUNDARY_STAGES:
          err(command, "semi_agentic_pre_execute_auto_pass_denied",
              row_id=row["row_id"], stage=row["stage"])
  ```
- `check_close_gate`(`state_tool.py:311-348`)는 기존 동일 — agentic + semi-agentic 모두 CLOSE 첫 행에 대해 `--auto-pass` 거부(`agentic_close_gate_requires_user`로 통합 거부) — 단, 에러 코드는 "agentic"이라는 이름 그대로 두지 않고 후속 D-DEC-5b에서 명명 정리.

### D-DEC-5b: CLOSE 게이트 에러 코드 명명 정리 (D-DEC-5 부수)

**문제**: CLOSE 첫 행 `--auto-pass` 거부 에러 코드 `agentic_close_gate_requires_user`(`state_tool.py:67`)는 agentic 전용 명명이지만 semi-agentic도 동일 거부 대상이다.

| 옵션 | 정책 | 장점 | 단점 |
|------|------|------|------|
| A | 기존 코드명 유지 + semi-agentic도 동일 코드 발화 + 메시지 텍스트 갱신 | 하위 호환 | 코드명이 의미적으로 부정확 |
| B | 신규 에러 코드 `non_interactive_close_gate_requires_user` 신설 + 기존 코드 deprecated alias로 유지 | 의미적 정확 | 외부 통합(에러 코드 파싱 도구) 영향 |
| C | 기존 코드명 유지 + 메시지 텍스트만 "agentic/semi-agentic" 두 모드 모두 거부로 갱신 | 하위 호환 + 명확한 메시지 | 코드명은 부정확하나 OPAL 외부 연동이 없으므로 영향 없음 |

**채택**: **옵션 C** — 에러 코드 `agentic_close_gate_requires_user`는 그대로 유지(외부 호환). 메시지 텍스트만 "agentic 또는 semi-agentic 모드 CLOSE 첫 행에 --auto-pass 사용 불가 (§2.16 G-13)"로 갱신. `check_close_gate` 조건도 `mode in ("agentic","semi-agentic")`로 확장.

**근거**: 기존 코드명이 외부 도구·로그·문서에 이미 인용됨(예: `opal-harness-agentic.md:90-93`, `opal-pilot-project/SKILL.md:188`). 메시지 갱신만으로 의미 명확성 확보 + 코드명 변경 비용 회피. 후속에 신규 에러 코드를 추가할 일이 있으면 그때 별도 SemVer로 처리.

**구현 명세**:
- `state_tool.py:67` ERROR_CODES 메시지: "agentic 모드 CLOSE 첫 행에 --auto-pass 사용 불가 (§2.16 G-13)" → "agentic/semi-agentic 모드 CLOSE 첫 행에 --auto-pass 사용 불가 (§2.16 G-13)"
- `state_tool.py:326` 조건: `if auto_pass and state.get("mode") == "agentic":` → `if auto_pass and state.get("mode") in ("agentic","semi-agentic"):`

### D-DEC-6: 모드 활성화 플래그 체계 (TASK.md C-3/C-4 구현)

**문제**: `--semi-agentic` 기본 / `--interactive` 명시 / `--agentic` 명시 3-way 플래그 체계 정의.

**채택**: 다음 3-way 매트릭스를 SSOT로 채택:

| 호출 형식 | 결과 모드 | 비고 |
|----------|---------|------|
| `//opp 작업` | `semi-agentic` | 기본 (TASK.md C-3) |
| `//opp --semi-agentic 작업` | `semi-agentic` | 명시 호출 (선택적, 기본과 동일) |
| `//opp --interactive 작업` | `interactive` | TASK.md C-4 |
| `//opp --agentic 작업` | `agentic` | 기존 동작 (TASK.md C-4) |
| `//opp --interactive --agentic 작업` | 에러 — `mode_flag_conflict` | 다중 모드 플래그는 거부 |

**근거**: TASK.md C-4 "3단계 모드 체계 — semi-agentic 기본 / interactive 명시 / agentic 명시" 명시. 다중 모드 플래그 충돌은 명시적 에러로 처리하여 캡틴 의도 보호.

### D-DEC-7: AGENTIC-LOG.md 생성 시점 (TASK.md F-4 구현)

**문제**: AGENTIC-LOG.md는 PM 자율 판단 추적 로그. semi-agentic은 PLAN까지 interactive이므로 PLAN 단계에는 PM 자율 판단이 없다. 언제 생성하는가?

**채택**: **EXECUTE 단계 진입 시점**(첫 EXECUTE 등가 행 advance 또는 mark 시점)에 자동 생성. agentic 모드는 기존대로 TASK 시작 시점.

**근거**: TASK.md C-5 "AGENTIC-LOG.md 그대로 재사용. EXECUTE 단계 진입 시점부터 자동 생성·기록" 명시. PLAN까지의 활동은 interactive 동작이라 별도 로그 불필요. 구현은 pilot SKILL.md의 EXECUTE 진입 절차에 명시(state-tool 외부) — state-tool은 STATE.md/state.json만 관리하므로 AGENTIC-LOG는 PM 책임 영역.

**부수 결정**: AGENTIC-LOG.md 헤더의 `모드:` 필드는 `semi-agentic` 또는 `agentic` 양쪽 값을 허용. 헤더 시작 시각은 EXECUTE 진입 시각으로 기록(semi-agentic) 또는 TASK 시각(agentic).

---

## 2. 구현 계획

### 파일 변경 계획

#### 신규 생성

| # | 파일 경로 | 역할 | 근거 |
|---|----------|------|------|
| N-1 | `opal/core/references/opal-harness-semi-agentic.md` | semi-agentic 모드 서브 하네스 SSOT — 모드 경계, 단계별 동작, AGENTIC-LOG 생성 시점, CLOSE 게이트 공통 정책, agentic/interactive와의 차이 표 | TASK F-1 / D-DEC-3 |

#### 수정

| # | 파일 경로 | 변경 내용 | 근거 |
|---|----------|----------|------|
| M-1 | `opal/core/references/opal-harness.md` | §2 모듈 구조 표에 `semi-agentic` 행 추가 + 로딩 규칙(§2.2) `semi-agentic` 분기 명시 + 변경이력 행 추가 | TASK F-5 / D-1 §2 / D-DEC-3 |
| M-2 | `opal/core/references/opal-harness-interactive.md` | 도입부에 "semi-agentic 모드의 PLAN까지의 동작은 본 문서를 준용한다"는 1줄 분기 안내 + 변경이력 행 추가 | TASK F-1 / D-DEC-3 |
| M-3 | `opal/core/references/opal-harness-agentic.md` | §1 모드 정의 표에 `semi-agentic` 행 추가 + §7 CLOSE 진입 게이트 행에 "semi-agentic도 동일" 명시 + §8 AGENTIC-LOG 생성 시점에 "semi-agentic은 EXECUTE 진입 시점" 분기 + 변경이력 행 추가 | TASK F-1/F-4/C-5/C-7 |
| M-4 | `opal/core/references/harness/state-template.md` | `state init --mode` choices에 `semi-agentic` 추가 + 기본값 명시("기본: `semi-agentic`") + STATE.md 템플릿 `모드:` 필드 값 안내 갱신 + 변경이력 행 추가 | TASK F-6 / D-4 |
| M-5 | `opal/core/references/harness/task-process.md` | §오케스트레이터 공통 영역 4번 "`--agentic` 플래그 여부를 TASK.md 헤더 `모드` 필드에 기록" → "`--interactive`/`--semi-agentic`(기본)/`--agentic` 플래그를 TASK.md 헤더 `모드` 필드에 기록" 갱신 + state init 인자 mode choices 갱신 + 변경이력 행 추가 | TASK F-5 / D-5 |
| M-6 | `opal/core/references/harness/skill-commands.md` | 쌍슬래시 커맨드 예시에 `//opd --interactive ...` / `//opp --agentic ...` 표기 추가 (semi-agentic은 기본이므로 명시 예시 제외) + 변경이력 행 추가 | TASK F-5 |
| M-7 | `opal/AGENT.md` | "도메인 지식" 표의 `Agentic Mode` 행을 3-way 모드 설명으로 갱신 (semi-agentic/interactive/agentic + 기본값) | TASK F-5 / D-16 |
| M-8 | `opal/skills/op-task/SKILL.md` | TASK.md 헤더 템플릿 `모드: {interactive/agentic}` → `모드: {semi-agentic|interactive|agentic}` + 작성 체크리스트 모드 항목 갱신 + state init mode choices 갱신 + 변경이력 행 추가 | TASK F-5 / D-17 |
| M-9 | `opal/skills/opal-pilot-project/SKILL.md` (opp) | Harness 절 모드 분기 3-way 갱신 + Agentic Mode 절을 "Agentic / Semi-Agentic 모드" 절로 확장 + 자율 게이트 흐름에 semi-agentic 흐름 추가 + state init mode 인자 안내 + 변경이력 행 추가 | TASK F-2 / D-7 |
| M-10 | `opal/skills/opal-pilot-dev/SKILL.md` (opd) | M-9와 동일 패턴 (단, Full Task 단계 — TASK→ANALYSIS→PLAN→EXECUTE→TEST→CLOSE) | TASK F-2 / D-8 |
| M-11 | `opal/skills/opal-pilot-dev-short/SKILL.md` (opds) | M-9와 동일 패턴 (Short Task — TASK→PLAN→EXECUTE→TEST→CLOSE) | TASK F-2 / D-9 |
| M-12 | `opal/skills/opal-pilot-dev-wireframe/SKILL.md` (opdw) | M-9와 동일 패턴 (Wireframe — TASK→WIREFRAME→EXECUTE→CLOSE). semi-agentic 경계: WIREFRAME 사용자 Gate 통과 시점(WIREFRAME이 PLAN-equivalent) | TASK F-2 / D-10 |
| M-13 | `opal/skills/opal-pilot-write-tech/SKILL.md` (opwt) | Harness 절 모드 분기 3-way + Agentic Mode 절 신규 추가(opwt는 현재 미존재) + semi-agentic 경계: PLAN(간략/진단보고) 사용자 확정 시점 + 변경이력 행 추가 | TASK F-2 / D-13 |
| M-14 | `opal/skills/opal-pilot-project-dev/SKILL.md` (oppd) | Harness 절 모드 분기 3-way + Agentic Mode 절을 3-way로 확장 + Phase 2 사용자 확정 행 통과 시점이 semi-agentic 모드 경계임을 명시(D-DEC-1) + 변경이력 행 추가 | TASK F-2 / U-1 / D-DEC-1 / D-11 |
| M-15 | `opal/skills/opal-pilot-sdd/SKILL.md` (opsdd) | Harness 절 모드 분기 3-way + Agentic Mode 절을 3-way로 확장 + DESIGN(Phase 3) 사용자 Gate 통과 시점이 semi-agentic 모드 경계임을 명시(D-DEC-2) + EXECUTE-LOOP 진입 시 AGENTIC-LOG 생성 시점 분기 + 변경이력 행 추가 | TASK F-2 / U-2 / D-DEC-2 / D-12 |
| M-16 | `opal/tools/state-tool/state_tool.py` | (a) `--mode` choices에 `semi-agentic` 추가(`:1180`) (b) `MODE_BOUNDARY_STAGES` 상수 신설 (c) `cmd_mark`에 `semi_agentic_pre_execute_auto_pass_denied` 검증 추가 (d) `check_close_gate` 조건을 `mode in ("agentic","semi-agentic")`로 확장 (e) ERROR_CODES에 신규 코드 1종 추가 + 기존 `agentic_close_gate_requires_user` 메시지 갱신 (f) `cmd_validate`에 semi-agentic 모드용 검증 추가(EXECUTE 등가 행 이전 owner=auto 검출) (g) `build_rows_from_spec` / `build_rows_from_skill_md` agentic 자동 마킹 분기에 `mode == "agentic"`(기존) 그대로 유지 — semi-agentic은 사용자 확인 행을 자동 마킹하지 않음 (PLAN까지 사용자 검토하므로) | TASK F-3 / U-5 / D-DEC-5 / D-DEC-5b / D-14 |
| M-17 | `opal/tools/state-tool/README.md` | mode choices에 `semi-agentic` 추가 + 신규 에러 코드 카탈로그 1종 추가 + 변경이력 행 추가 | TASK F-3 / D-23 |
| M-18 | `.opal/AGENT.md` | "도메인 지식" 표의 `Agentic Mode` 행 갱신(3-way 설명) + "확정 기준" 표에 새 행 추가 — "PLAN까지 캡틴 검토, EXECUTE 이후 자율 진행이 캡틴 기본 작업 패턴" | TASK F-7 / D-19 |
| M-19 | `.opal/MEMORY.md` | "메모리" 표에 preferences 카테고리 행 추가 — `memory/preferences_default_semi_agentic.md` 링크 + 신규 메모리 파일 생성(요지: 캡틴 기본 작업 패턴은 PLAN 검토 + EXECUTE 자율) | TASK F-7 / D-20 |

#### 신규 생성 (메모리)

| # | 파일 경로 | 역할 | 근거 |
|---|----------|------|------|
| N-2 | `.opal/memory/preferences_default_semi_agentic.md` | 캡틴 작업 패턴 메모리 — semi-agentic이 기본 모드인 이유 + PLAN까지 검토 / EXECUTE 이후 자율의 의도 + 본 태스크(140) 결정 근거 링크 | TASK F-7 / D-20 |

#### 삭제

없음. (semi-agentic은 신규 추가, 기존 모드 유지 — 하위 호환 D-DEC-4)

### 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | 신규 하네스 파일 생성 | N-1 (opal-harness-semi-agentic.md) | 중 (모드 SSOT 명세) |
| 2 | 공통 하네스 + 모드 분기 보강 | M-1 ~ M-3 (opal-harness.md / -interactive / -agentic) | 중 (모듈 표 + 분기 안내) |
| 3 | 부트스트랩/공통 참조 갱신 | M-4 ~ M-7 (state-template / task-process / skill-commands / opal/AGENT.md) | 하 (필드값/예시 갱신) |
| 4 | op-task SKILL.md 갱신 | M-8 (op-task/SKILL.md) | 하 (헤더 + state init 인자) |
| 5 | state-tool 코드 변경 | M-16 (state_tool.py) + M-17 (README.md) | 상 (Python 코드 + 새 에러 + 분기 검증 + cmd_validate 보강) |
| 6 | pilot 7종 SKILL.md 일괄 갱신 | M-9 ~ M-15 (opp/opd/opds/opdw/opwt/oppd/opsdd) | 중 (각 pilot Harness + Agentic Mode 절) |
| 7 | 메모리/확정 기준 등록 | N-2 (memory) + M-18 (.opal/AGENT.md) + M-19 (.opal/MEMORY.md) | 하 |
| 8 | install + 배포 검증 | (코드 변경 없음 — 검증만) scripts/install-mac.sh + 수동 동작 검증 | 중 (하네스 자동 배포 확인 + state-tool 동작 검증) |
| 9 | docs/ 갱신 검토 | (PM 직접 — 본 PLAN 변경이 docs/ARCHITECTURE.md / docs/CONVENTIONS.md에 영향 있는지 점검) | 하 |

**원칙**: SSOT 우선 — 신규 하네스(N-1)와 모듈 표(M-1) → 공통 참조(M-4~M-7) → state-tool 인프라(M-16) → 사용처(pilot 7종 M-9~M-15) → 메모리/확정 기준 → 검증.

### 핵심 설계

> 각 파일별 변경 내용 뒤에 인라인 인용을 기재한다. citation-rules.md §2 포맷.

#### N-1: `opal/core/references/opal-harness-semi-agentic.md` (신규)

**구조**:

```markdown
# opal-harness-semi-agentic

> semi-agentic 모드(기본) 전용 하네스. 공통 하네스(opal-harness.md)와 함께 로드한다. `--semi-agentic` 플래그(또는 모드 플래그 미지정 — 기본 모드) 활성화 시 이 문서를 로드한다.

## 1. 모드 정의
| 모드 | 설명 |
|------|------|
| `interactive`   | 모든 단계 게이트마다 사용자 승인 (`--interactive` 명시) |
| `semi-agentic`  | **기본** — PLAN-equivalent 단계까지 사용자 검토, EXECUTE-equivalent 진입 후 PM 자율 통과. CLOSE 진입은 사용자 승인 필수 |
| `agentic`       | 모든 게이트 PM 자율 통과 (CLOSE 진입 제외) — `--agentic` 명시 |

## 2. 활성화 방법
- 기본: 모드 플래그 미지정 시 semi-agentic
- 명시: `--semi-agentic` 플래그
- 충돌: `--interactive` 또는 `--agentic`과 동시 사용 시 `mode_flag_conflict` 에러
- 활성화 시 STATE.md 모드 필드를 `semi-agentic`으로 기록 (state init --mode semi-agentic)

## 3. 모드 경계 (PLAN-equivalent → EXECUTE-equivalent 전환점)
| pilot | PLAN-equivalent 종료 시점 | EXECUTE-equivalent 시작 시점 |
|-------|--------------------------|----------------------------|
| opp   | PLAN 사용자 확인 행 | EXECUTE 작업 행 |
| opd   | PLAN 사용자 확인 행 | EXECUTE 작업 행 |
| opds  | PLAN 사용자 확인 행 | EXECUTE 작업 행 |
| opdw  | WIREFRAME 사용자 확인 행 | EXECUTE 작업 행 |
| opwt  | PLAN(간략/진단보고) 사용자 확정 | EXECUTE 작업 행 |
| oppd  | Phase 2 WBS 사용자 확정 행 | Phase 3 액션 실행 첫 행 |
| opsdd | Phase 3 DESIGN 사용자 Gate | Phase 4 EXECUTE-LOOP 첫 행 |

## 4. PLAN-equivalent까지의 동작 (interactive 준용)
- 단계 게이트마다 사용자 승인 필수
- QA Gate / PM Gate는 interactive 동일
- AGENTIC-LOG.md 미생성 (이 시점까지)

## 5. EXECUTE-equivalent 이후의 동작 (agentic 준용)
- PM 자율 통과 (state-tool `--auto-pass` 호출)
- AGENTIC-LOG.md 자동 생성 (EXECUTE 등가 첫 행 advance/mark 시점에 PM이 생성)
- Gate 루핑 규칙: opal-harness-agentic.md §5 적용
- PM 대행 의무(판단 기록/직접 검증/완수/품질 책임/투명성/에스컬레이션/폴백 승인): opal-harness-agentic.md §3 적용

## 6. CLOSE 진입 게이트 (공통)
- agentic 모드와 동일하게 CLOSE 첫 행 `--auto-pass` 거부 (`agentic_close_gate_requires_user`)
- 캡틴 발화(`승인`/`확인`/`확인완료`) 후 직전 사용자 확인 행을 `--owner user`로 mark 후 CLOSE 진입

## 7. AGENTIC-LOG.md 생성 시점
- agentic 모드: TASK 시작 시점
- semi-agentic 모드: EXECUTE-equivalent 첫 행 advance/mark 시점

## 8. interactive / agentic / semi-agentic 차이 표
| 단계 | interactive | semi-agentic | agentic |
|------|-------------|-------------|---------|
| TASK 완료     | 사용자 승인 | 사용자 승인 | PM 자율 |
| ANALYSIS 완료 | 사용자 승인 | 사용자 승인 | PM 자율 |
| PLAN 완료     | 사용자 승인 | 사용자 승인 (모드 경계) | PM 자율 |
| EXECUTE 완료  | 사용자 승인 | PM 자율 | PM 자율 |
| TEST 완료     | 사용자 승인 | PM 자율 | PM 자율 |
| CLOSE 진입    | 사용자 승인 | 사용자 승인 | 사용자 승인 (공통) |

## 9. 유지되는 규칙 (opal-harness.md §1 Guards 그대로 적용)
- 구현 금지 원칙 / 커밋 규칙 / 디스패치 의무 / 자동 루핑 제약 / CLOSE 진입 게이트

## 변경이력
| 버전 | 날짜 | 내용 |
|------|------|------|
| v1.0 | 2026-05-09 | 초기 작성 — semi-agentic 신규 모드 SSOT (140) |
```

**근거**: TASK.md F-1 AC ("모드 경계(C-6) + CLOSE 게이트(C-7) + AGENTIC-LOG 시점(C-5)이 명시된다. interactive/agentic과의 차이가 표로 정리된다.") (→ TASK.md L72) / D-DEC-1~D-DEC-7

[MUST] `opal/core/references/opal-harness.md` §1 Guards: "사용자가 명시적으로 '승인', '진행해', '구현해' 등의 실행 허가를 내릴 때까지 코드를 작성하거나 파일을 생성/수정하지 않는다." — semi-agentic도 동일.

[MUST] `opal/core/references/opal-harness.md` §1 Guards: "CLOSE 단계 진입 게이트 ... agentic 모드에서도 유지된다." — semi-agentic에도 동일 적용 (D-3 §7 / N-1 §6).

#### M-1: `opal/core/references/opal-harness.md`

**변경 내용**:

§2 모듈 구조 표(현재 2행)에 신규 행 추가:

```markdown
| `opal-harness-semi-agentic.md` | semi-agentic 모드 (기본 — PLAN까지 interactive 흐름, EXECUTE 이후 agentic 흐름, CLOSE 게이트 공통) | 모드 플래그 없음 (기본) 또는 `--semi-agentic` | `~/.opal/references/opal-harness-semi-agentic.md` |
```

기존 `interactive` 행의 "로드 조건" 컬럼을 `--agentic` 플래그 **없음** (기본) → `--interactive` 플래그 **있음** 로 갱신 (3-way 체계 반영, → D-DEC-6).

기존 `agentic` 행은 변경 없음.

§2 로딩 규칙(2번 항목)을 3-way로 갱신:

```markdown
2. 공통 하네스 Read 후, 모드에 따라 **서브 하네스 1개를 추가 Read**한다:
   - 모드 플래그 없음 (기본) 또는 `--semi-agentic` → `opal-harness-semi-agentic.md`
   - `--interactive` → `opal-harness-interactive.md`
   - `--agentic` → `opal-harness-agentic.md`
   - 다중 모드 플래그 동시 사용 → `mode_flag_conflict` 에러 (state init도 동일 거부)
   - **단, 해당 서브 하네스가 현재 세션 컨텍스트에 이미 로딩되어 있으면 Read를 스킵한다.**
```

변경이력 행: `| v4.7 | 2026-05-09 | §2 모듈 구조 표에 semi-agentic 행 추가 + 로딩 규칙 3-way 갱신 (140) |`

**근거**: D-1 §2 / D-DEC-3 / D-DEC-6 / TASK F-5

[MUST] `docs/CONVENTIONS.md` §구현 규칙 — 변경이력 작성 의무: "변경 시 '## 변경이력' 표에 행을 추가한다. 일시는 `YYYY-MM-DD HH:mm` (KST), 버전은 semver, 변경내용은 태스크 번호를 괄호로 포함 — 예: `(140)`."

#### M-2: `opal/core/references/opal-harness-interactive.md`

**변경 내용**:

도입부(1행)에 1줄 추가:

> "semi-agentic 모드의 PLAN-equivalent 종료 시점까지의 동작은 본 문서를 준용한다 (semi-agentic 하네스 §4)."

변경이력 행 추가: `| v2.6 | 2026-05-09 | semi-agentic 모드의 PLAN까지 동작 준용 안내 추가 (140) |`

**근거**: D-DEC-3 / `opal/core/references/opal-harness-interactive.md:1-7`

#### M-3: `opal/core/references/opal-harness-agentic.md`

**변경 내용**:

§1 모드 정의 표(현재 2행)에 `semi-agentic` 행 추가:

```markdown
| `semi-agentic` | **기본**. PLAN-equivalent까지 사용자 승인, EXECUTE-equivalent 이후 PM 자율. CLOSE 진입은 사용자 승인 필수 (공통 게이트). 본 문서의 §3~§9는 semi-agentic의 EXECUTE 이후 동작에도 동일 적용된다. |
```

§7 "유지되는 규칙" 표 `CLOSE 진입 게이트` 행 텍스트 갱신: "agentic / semi-agentic 양쪽 모두 CLOSE 첫 행 `--auto-pass` 거부 (`agentic_close_gate_requires_user`로 동일 코드)" 명시.

§8 AGENTIC-LOG.md 도입부에 분기 명시:

```markdown
**생성 시점**:
- agentic 모드: TASK 시작 시점 (즉시 생성)
- semi-agentic 모드: EXECUTE-equivalent 첫 행 advance 또는 mark 시점 (PM이 EXECUTE 진입 시 생성)
```

변경이력 행: `| v1.6 | 2026-05-09 | §1 모드 정의에 semi-agentic 행 추가 / §7 CLOSE 게이트 행 semi-agentic 공통 / §8 AGENTIC-LOG 생성 시점 분기 (140) |`

**근거**: D-3 §1·§7·§8 / D-DEC-3 / D-DEC-5b / D-DEC-7 / TASK F-1/F-4/C-7

#### M-4: `opal/core/references/harness/state-template.md`

**변경 내용**:

`state init` 호출 예시(state-template.md:11-18)의 `--mode` 인자 choices를 갱신:

```bash
~/.opal/tools/state-tool/run.sh init <task-path> \
  --skill <opp|opd|opds|opdw|opwt|opgc|oppd|opsdd> \
  --mode <interactive|semi-agentic|agentic> \
  [--task-title <태스크 제목>] \
  [--next-action <첫 액션 텍스트>]
```

도입부에 "기본값: `semi-agentic`. 캡틴이 `--interactive` 또는 `--agentic`을 명시 호출하지 않으면 자동 적용된다." 안내 추가.

§ STATE.md 공통 템플릿의 `- 모드: {모드}` 자리 안내에 "값은 `interactive` / `semi-agentic` / `agentic` 중 하나" 추가.

변경이력 행: `| v1.3 | 2026-05-09 | --mode choices에 semi-agentic 추가 + 기본값 안내 (140) |`

**근거**: D-4 / TASK F-6

#### M-5: `opal/core/references/harness/task-process.md`

**변경 내용**:

§오케스트레이터 공통 영역 4번 항목(task-process.md:30):

```
4. **`--agentic` 플래그 여부를 TASK.md 헤더 `모드` 필드에 반드시 기록한다** (`interactive` 또는 `agentic`).
```

→

```
4. **모드 플래그(`--interactive` / `--semi-agentic` / `--agentic`)를 TASK.md 헤더 `모드` 필드에 반드시 기록한다** (`interactive` / `semi-agentic` (기본) / `agentic`). 모드 플래그가 없으면 기본값 `semi-agentic`.
```

§오케스트레이터 공통 영역 5번 항목의 state init mode choices 갱신: `<interactive|agentic>` → `<interactive|semi-agentic|agentic>`.

변경이력 행: `| v1.2 | 2026-05-09 | --mode choices 3-way 갱신 + 기본값 semi-agentic 명시 (140) |`

**근거**: D-5 / TASK F-5

#### M-6: `opal/core/references/harness/skill-commands.md`

**변경 내용**: 쌍슬래시 커맨드 예시 블록(`skill-commands.md:26-31`)에 모드 플래그 예시 추가:

```
형식: //{스킬명 또는 약식} [--interactive|--semi-agentic|--agentic] {작업 설명}
예시: //opds 로그인 버그 수정해줘                  (기본 — semi-agentic)
      //opd --interactive 회원가입 기능 전체 개발해줘
      //opp --agentic 자율 진행
```

변경이력 행: `| v1.1 | 2026-05-09 | 쌍슬래시 커맨드 예시에 모드 플래그 3-way 추가 (140) |`

**근거**: D-6 / TASK F-5 / D-DEC-6

#### M-7: `opal/AGENT.md`

**변경 내용**: "도메인 지식" 표의 `Agentic Mode` 행을 갱신:

```
| Agentic Mode | `--agentic` 플래그로 PM 검토를 자율 진행하는 모드 |
```

→

```
| 모드 체계 | `interactive`(`--interactive`) / `semi-agentic`(기본) / `agentic`(`--agentic`) 3-way. semi-agentic은 PLAN까지 사용자 검토, EXECUTE 이후 PM 자율, CLOSE 진입은 사용자 승인 공통 |
```

소유자 오버라이드 표(opal/AGENT.md:117-123)에는 `--interactive`/`--semi-agentic`/`--agentic` 플래그가 별도 행으로 명시되지 않으므로 해당 표에는 변경 없음(쌍슬래시 커맨드 행이 모드 플래그를 포함하는 일반 형식이므로 추가 행 불필요).

변경이력은 본 파일에 별도 표 없으므로 추가하지 않음. (opal/AGENT.md 자체에 변경이력 표가 있으면 추가 — Read 후 EXECUTE 단계에서 확인)

**근거**: D-16 / TASK F-5

> 주: `opal/AGENT.md` 본문 Read 결과 변경이력 표 미확인 시 EXECUTE 단계에서 신설 또는 생략 결정.

#### M-8: `opal/skills/op-task/SKILL.md`

**변경 내용**:

(a) TASK.md 템플릿 헤더 라인(:109):

```
> 작성일: YYYY-MM-DD | 작업 유형: {신규/개선/수정/오류/Wireframe UI} | 적용 스킬: {약어} | 모드: {interactive/agentic}
```

→

```
> 작성일: YYYY-MM-DD | 작업 유형: {신규/개선/수정/오류/Wireframe UI} | 적용 스킬: {약어} | 모드: {interactive|semi-agentic|agentic}
```

(b) state init 호출 예시(`op-task/SKILL.md:194-200`)의 `--mode <interactive|agentic>` → `--mode <interactive|semi-agentic|agentic>`. 안내문 "기본: `semi-agentic`" 추가.

(c) 작성 체크리스트(:225) 모드 항목 갱신:

```
- [ ] 모드(interactive|semi-agentic|agentic)가 헤더에 기록되었는가
```

(d) 변경이력 행 추가: `| v1.5 | 2026-05-09 | 모드 필드 3-way 갱신 + state init choices 갱신 (140) |`

**근거**: D-17 / TASK F-5 / `op-task/SKILL.md:107-200`

#### M-9 ~ M-15: pilot 7종 SKILL.md (공통 패턴)

각 pilot SKILL.md에 다음 4가지 변경을 일관 적용한다.

**(a) Harness 절 모드 분기 3-way 갱신**:

```markdown
**[MUST]** 스킬 시작 즉시 모드에 따라 서브 하네스를 Read한다. 이 단계를 건너뛰면 안 된다:
- `--interactive` 플래그 → `~/.opal/references/opal-harness-interactive.md`
- `--agentic` 플래그 → `~/.opal/references/opal-harness-agentic.md`
- 모드 플래그 없음 (기본) 또는 `--semi-agentic` → `~/.opal/references/opal-harness-semi-agentic.md`
- 다중 모드 플래그 동시 사용 시 즉시 캡틴에게 보고 + state init도 거부 (`mode_flag_conflict`)
```

**(b) state init 호출 예시 mode choices 갱신**: `--mode <interactive|agentic>` → `--mode <interactive|semi-agentic|agentic>`. 기본값 안내 추가.

**(c) Agentic Mode 절을 "Agentic / Semi-Agentic 모드" 절로 확장 (또는 신규 추가 — opwt만)**:

각 pilot의 모드 경계와 자율 게이트 흐름을 명시:

```markdown
## Agentic / Semi-Agentic 모드

opal-harness-agentic.md / opal-harness-semi-agentic.md 참조. 본 절은 이 스킬의 차이점만 기술한다.

### 기본 모드 (semi-agentic)

기본 호출(`//{약어} {작업}`)은 semi-agentic 모드. PLAN-equivalent까지 사용자 검토, EXECUTE-equivalent 이후 PM 자율, CLOSE 진입은 사용자 승인 필수.

**모드 경계** (이 시점부터 PM 자율):
- {pilot별 명시 — 표 참조 N-1 §3}

### 명시 모드

| 호출 | 모드 |
|------|------|
| `//{약어} 작업` | semi-agentic (기본) |
| `//{약어} --interactive 작업` | interactive — 모든 단계 사용자 승인 |
| `//{약어} --agentic 작업` | agentic — 모든 단계 PM 자율 (CLOSE 진입 제외) |

### 자율 게이트 흐름 (semi-agentic)
{pilot별 ASCII 흐름도}

### CLOSE 진입 게이트 (공통)

semi-agentic / agentic 모두 CLOSE 첫 행 `--auto-pass` 거부 (`agentic_close_gate_requires_user`). 캡틴 발화 후 직전 사용자 확인 행 `--owner user` mark 필수.

### AGENTIC-LOG.md 생성 시점

- agentic: TASK 시작 시점
- semi-agentic: EXECUTE-equivalent 첫 행 advance 시점에 PM이 생성
```

**(d) 변경이력 행 추가**: `| v?.? | 2026-05-09 | 3-way 모드 체계 도입 — semi-agentic 기본 채택 + Agentic/Semi-Agentic 모드 절 확장 (140) |`

**pilot별 모드 경계 (M-9~M-15 차별점)**:

| pilot | M-# | 모드 경계 (PLAN-equivalent 종료 시점) | EXECUTE-equivalent 시작 |
|-------|-----|--------------------------------------|------------------------|
| opp   | M-9 | PLAN 사용자 확인 행 (행 11) | EXECUTE 작업 행 (행 12) |
| opd   | M-10 | PLAN 사용자 확인 행 | EXECUTE 작업 행 |
| opds  | M-11 | PLAN 사용자 확인 행 | EXECUTE 작업 행 |
| opdw  | M-12 | WIREFRAME 사용자 확인 행 | EXECUTE 작업 행 |
| opwt  | M-13 | PLAN(간략/진단보고) 사용자 확정 행 | EXECUTE 작업 행 (작성/수정 모드만 — 분석 모드는 EXECUTE 없음, semi-agentic이라도 PLAN(진단보고)까지로 종료) |
| oppd  | M-14 | Phase 2 WBS 사용자 확정 행 (D-DEC-1) | Phase 3 액션 실행 첫 행 |
| opsdd | M-15 | Phase 3 DESIGN 사용자 Gate (D-DEC-2) | Phase 4 EXECUTE-LOOP 첫 행 |

**근거**: D-7 ~ D-13 / D-DEC-1 / D-DEC-2 / D-DEC-6 / TASK F-2

[MUST] `opal/core/references/opal-harness.md` §1 디스패치 의무: "오케스트레이터 SKILL.md에서 '워커 디스패치'로 정의된 단계는 반드시 서브에이전트를 디스패치한다." — semi-agentic도 동일.

#### M-16: `opal/tools/state-tool/state_tool.py`

**변경 내용**:

(a) **`--mode` choices 추가** (`state_tool.py:1180`):

```python
p_init.add_argument("--mode", required=True,
                    choices=["interactive","semi-agentic","agentic"])
```

(b) **`MODE_BOUNDARY_STAGES` 상수 신설** (STAGE_ENUM 직후):

```python
# semi-agentic 모드 경계 — 이 stage 집합에 속하는 행은 EXECUTE-equivalent 이전으로 간주
# (PLAN-equivalent 단계까지 사용자 검토 강제)
MODE_BOUNDARY_STAGES = {
    "TASK", "ANALYSIS", "PLAN",
    "SPEC", "REVIEW", "DESIGN",
    "WBS", "WIREFRAME",
}
```

(c) **ERROR_CODES 갱신** (`state_tool.py:51-75`):
- 기존 `agentic_close_gate_requires_user` 메시지 갱신: "agentic/semi-agentic 모드 CLOSE 첫 행에 --auto-pass 사용 불가 (§2.16 G-13)"
- 신규 코드 1종 추가:
  ```python
  "semi_agentic_pre_execute_auto_pass_denied":
      "semi-agentic 모드에서 EXECUTE-equivalent 단계 이전 행(row {row_id}, stage={stage})에 --auto-pass 사용 불가 — PLAN-equivalent까지 사용자 검토 필수",
  ```
- 신규 코드 1종 추가:
  ```python
  "mode_flag_conflict":
      "다중 모드 플래그 동시 사용 — --interactive/--semi-agentic/--agentic 중 하나만 사용 가능",
  ```

(d) **`check_close_gate` 조건 확장** (`state_tool.py:325-327`):

```python
if auto_pass and state.get("mode") in ("agentic", "semi-agentic"):
    err(command, "agentic_close_gate_requires_user", row_id=row["row_id"])
```

(e) **`cmd_mark`에 semi-agentic pre-EXECUTE 검증 추가** (`state_tool.py:825` `check_close_gate` 호출 직후):

```python
# semi-agentic 모드에서 EXECUTE-equivalent 이전 행은 --auto-pass 거부 (D-DEC-5)
if args.auto_pass and state.get("mode") == "semi-agentic":
    if row["stage"] in MODE_BOUNDARY_STAGES:
        err(command, "semi_agentic_pre_execute_auto_pass_denied",
            row_id=row["row_id"], stage=row["stage"])
```

(f) **`build_rows_from_spec` / `build_rows_from_skill_md` 사용자 확인 행 자동 마킹 분기 유지** (`state_tool.py:391` / `:483`):
- 기존 `if mode == "agentic"` 조건 그대로 유지 — semi-agentic은 PLAN-equivalent까지 사용자 검토하므로 사용자 확인 행을 자동 마킹하지 않는다.
- 즉 semi-agentic 모드 init 시 사용자 확인 행은 모두 ⬜ pending으로 생성됨.

(g) **`cmd_validate` 보강** (`state_tool.py:931-955`):
- `auto_pass_in_interactive_mode` 검증과 유사하게 semi-agentic 모드에서 EXECUTE-equivalent 이전 행에 owner=auto가 있으면 violation 추가:
  ```python
  if owner == "auto" and mode == "semi-agentic":
      # PLAN-equivalent 이전 행에 owner=auto는 위반
      if row["stage"] in MODE_BOUNDARY_STAGES:
          violations.append({
              "code":   "semi_agentic_pre_execute_auto_pass_denied",
              "row_id": row["row_id"],
              "detail": f"semi-agentic mode but owner=auto on stage={row['stage']}"
          })
  ```

(h) **@header 갱신** (`state_tool.py:1-12`): description 필드에 "3-way 모드(interactive/semi-agentic/agentic) 지원" 추가.

**근거**: D-14 / TASK F-3 / U-5 / D-DEC-5 / D-DEC-5b / D-DEC-6 / `state_tool.py:64-67` / `:311-348` / `:790-892` / `:1179-1180`

[MUST] `docs/CONVENTIONS.md` §구현 규칙 — State 관리: "파이프라인 STATE.md 행 상태(⬜/🔄/✅) 변경은 `~/.opal/tools/state-tool/run.sh`로만 수행한다." — state-tool은 본 변경의 게이트 키퍼.

#### M-17: `opal/tools/state-tool/README.md`

**변경 내용**: mode choices 문서화 갱신 + 신규 에러 코드 카탈로그 행 추가 (`semi_agentic_pre_execute_auto_pass_denied`, `mode_flag_conflict`) + `agentic_close_gate_requires_user` 설명 갱신. 변경이력 행 추가.

**근거**: D-23 / TASK F-3

#### M-18: `.opal/AGENT.md`

**변경 내용**:

(a) "도메인 지식" 표(`.opal/AGENT.md:51`) `Agentic Mode` 행 갱신:

```markdown
| 모드 체계 | 3-way: `interactive` / `semi-agentic`(기본) / `agentic`. semi-agentic은 PLAN까지 사용자 검토 + EXECUTE 이후 자율, CLOSE 진입 사용자 승인 공통 |
```

(b) "확정 기준" 표(`.opal/AGENT.md:67-73`)에 행 추가:

```markdown
| 1 | PLAN까지 캡틴 검토 / EXECUTE 이후 PM 자율 / CLOSE 진입 캡틴 승인 — 모든 pilot의 기본 작업 패턴 (semi-agentic 모드 기본 채택) | 본 패턴은 캡틴의 작업 효율 + 설계 검토 가치의 균형점이며, 본 태스크(140)에서 SSOT 등록 | 2026-05-09 |
```

**근거**: D-19 / TASK F-7 / 본 PLAN의 §결정 사항 (D-DEC-1~D-DEC-7)

#### M-19: `.opal/MEMORY.md`

**변경 내용**:

"메모리" 표에 행 추가:

```markdown
| 2026-05-09 | preferences | 유지 | [memory/preferences_default_semi_agentic.md](memory/preferences_default_semi_agentic.md) | 캡틴 기본 작업 패턴: PLAN 검토 + EXECUTE 자율 (semi-agentic 모드 기본 채택) |
```

`last_task_number` 갱신 불필요(이미 140으로 설정됨).

**근거**: D-20 / TASK F-7

#### N-2: `.opal/memory/preferences_default_semi_agentic.md`

**구조**:

```markdown
# 캡틴 기본 작업 패턴: PLAN 검토 + EXECUTE 자율 (semi-agentic 모드 기본 채택)

> 등록일: 2026-05-09 | 카테고리: preferences | 등록 태스크: 140

## 요지

캡틴(소유자)의 기본 작업 패턴은 다음과 같다:

- **PLAN 단계까지**: 사용자 검토 (interactive 동작)
- **EXECUTE 단계 진입 후**: PM 자율 통과 + AGENTIC-LOG 기록 (agentic 동작)
- **CLOSE 진입**: 사용자 명시 승인 필수 (공통 게이트)

이 패턴이 OPAL 모든 pilot(opp/opd/opds/opdw/oppd/opsdd/opwt)의 기본 모드인 `semi-agentic`이다.

## 근거

- PLAN 단계는 설계 결정이 큰 구간으로 사용자 검토가 가장 가치 있음
- EXECUTE/TEST는 반복적·기계적이라 자율 + 기록이 효율적
- 본 패턴은 태스크 140(opp 본 태스크)에서 SSOT로 확정

## 관련 결정

- D-DEC-1: oppd Phase 경계는 Phase 2 사용자 확정 행
- D-DEC-2: opsdd Phase 경계는 DESIGN(Phase 3) 사용자 Gate
- D-DEC-3: 신규 하네스 파일 `opal-harness-semi-agentic.md` 신설
- D-DEC-4: 기존 진행 중 태스크는 모드 변경 없음 (소급 변경 없음)
- D-DEC-5: state-tool에서 stage 기반 boundary 검증
- D-DEC-6: `--interactive` / `--semi-agentic`(기본) / `--agentic` 3-way 플래그
- D-DEC-7: AGENTIC-LOG.md는 semi-agentic 모드에서 EXECUTE 진입 시점에 생성

## 인용

- TASK.md L13 "PLAN 단계는 설계 결정이 큰 구간 ... EXECUTE/TEST는 반복적·기계적이라 자율 + 기록이 효율적"
- PLAN.md §결정 사항 (140 PLAN.md)
```

**근거**: TASK F-7 / D-20

---

## 3. 실행 체크리스트

> 총 9개 Step | Phase 4개

| Phase | Step | 실행 | 비고 |
|-------|------|------|------|
| 1 | 1 | 단독 | 신규 하네스 파일 (다른 Step의 의존 받음) |
| 2 | 2, 3, 4, 5 | 병렬 | 각각 독립 파일(공통 하네스 / 부트스트랩 / op-task / state-tool 코드). Step 1 산출물 참조하지만 파일 자체는 독립. state-tool은 Bash/Python 실행 필요 |
| 3 | 6 | 단독 (내부는 7파일 묶음 — 워커 1회 디스패치) | pilot 7종 일괄 — Step 1~5의 SSOT 인용 필요 |
| 4 | 7 | 단독 | 메모리/확정 기준 등록 — Step 1~6 결정 사항 SSOT 후 등록 |
| 5 | 8 | 단독 | install + 동작 검증 — 모든 코드/문서 변경 후 |
| 6 | 9 | 단독 | docs/ 갱신 검토 — PM 직접 |

> Phase 분류 원칙: 동일 파일 수정 Step은 같은 Phase 미배치. 의존 있는 Step은 선행 Phase 이후 배치. Step 1(신규 하네스)은 모든 후속 Step의 SSOT이므로 Phase 1 단독.

### Step 1: 신규 하네스 파일 작성 — `opal-harness-semi-agentic.md`

- [ ] 완료
- **파일**: `opal/core/references/opal-harness-semi-agentic.md` (신규 N-1)
- **작업 내용**: §2 핵심 설계 N-1에 명시된 9개 섹션 구조로 작성. 모드 정의 / 활성화 방법 / 모드 경계 / PLAN-equivalent까지 동작 / EXECUTE 이후 동작 / CLOSE 진입 게이트 / AGENTIC-LOG 생성 시점 / 3-way 차이 표 / 유지되는 규칙. 변경이력 표 v1.0 행 포함.
- **완료 기준**:
  1. 파일 존재
  2. 9개 섹션 모두 작성
  3. 7개 pilot 모두에 대한 모드 경계 표(N-1 §3)가 D-DEC-1 / D-DEC-2 결정과 일치
  4. CLOSE 진입 게이트 §6 / AGENTIC-LOG 시점 §7이 D-DEC-7 결정과 일치
  5. 변경이력 표 v1.0 행 존재 (일시 KST + 태스크 번호 140)
- **테스트**: `cat opal/core/references/opal-harness-semi-agentic.md | head -50` 으로 헤더 확인. 후속 Step에서 Read하여 인용 시 일관성 검증.
- **의존**: 없음
- **agent**: opal-task-agent

### Step 2: 공통 하네스 + 모드 분기 보강 — opal-harness 3종

- [ ] 완료
- **파일**: M-1 `opal/core/references/opal-harness.md` / M-2 `opal/core/references/opal-harness-interactive.md` / M-3 `opal/core/references/opal-harness-agentic.md` (각 1파일, 같은 Step 내 순차 처리 — 동일 도메인)
- **작업 내용**: §2 핵심 설계 M-1~M-3 명세대로 3-way 모드 분기 갱신. 각 파일에 변경이력 행 추가.
- **완료 기준**:
  1. M-1: §2 모듈 구조 표에 `semi-agentic` 행 추가 + 로딩 규칙 3-way 갱신 + 변경이력 v4.7 행
  2. M-2: 도입부 1줄 분기 안내 추가 + 변경이력 v2.6 행
  3. M-3: §1 모드 정의 표에 semi-agentic 행 + §7 CLOSE 게이트 행 갱신 + §8 AGENTIC-LOG 시점 분기 + 변경이력 v1.6 행
- **테스트**: `grep -n "semi-agentic" opal/core/references/opal-harness*.md` 실행 시 3개 파일에서 모두 매칭 확인. 변경이력 정합성 검증.
- **의존**: Step 1 완료 (M-1의 모듈 표가 N-1 파일을 참조하므로)
- **agent**: opal-task-agent

### Step 3: 부트스트랩/공통 참조 갱신 — state-template / task-process / skill-commands / opal/AGENT.md

- [ ] 완료
- **파일**: M-4 `opal/core/references/harness/state-template.md` / M-5 `opal/core/references/harness/task-process.md` / M-6 `opal/core/references/harness/skill-commands.md` / M-7 `opal/AGENT.md`
- **작업 내용**: §2 핵심 설계 M-4~M-7 명세대로 mode choices / 기본값 안내 / 쌍슬래시 예시 / 도메인 지식 표 갱신. 각 파일에 변경이력 행 추가(opal/AGENT.md는 변경이력 표 존재 여부 확인 후 결정).
- **완료 기준**:
  1. M-4: state-template.md `--mode` choices에 `semi-agentic` + 기본값 안내 + 변경이력 v1.3
  2. M-5: task-process.md 4번 항목 / state init choices 갱신 + 변경이력 v1.2
  3. M-6: skill-commands.md 예시에 `--interactive`/`--agentic` 호출 추가 + 변경이력 v1.1
  4. M-7: opal/AGENT.md 도메인 지식 표 모드 행 3-way 갱신
- **테스트**: 각 파일 `grep -n "semi-agentic\|3-way\|interactive|semi-agentic|agentic"` 매칭 확인.
- **의존**: Step 1 완료 (참조 일관성)
- **agent**: opal-task-agent

### Step 4: op-task SKILL.md 갱신

- [ ] 완료
- **파일**: M-8 `opal/skills/op-task/SKILL.md`
- **작업 내용**: §2 핵심 설계 M-8 명세대로 (a) TASK.md 헤더 모드 필드 3-way (b) state init mode choices (c) 작성 체크리스트 (d) 변경이력 v1.5 행 추가.
- **완료 기준**:
  1. 헤더 라인 `모드: {interactive|semi-agentic|agentic}` 갱신
  2. state init choices `<interactive|semi-agentic|agentic>` 갱신 + 기본값 안내
  3. 작성 체크리스트 모드 항목 갱신
  4. 변경이력 v1.5 행 추가
- **테스트**: `grep -n "semi-agentic" opal/skills/op-task/SKILL.md` 4건 이상 매칭.
- **의존**: Step 1 완료
- **agent**: opal-task-agent

### Step 5: state-tool 코드 변경 — state_tool.py / README.md

- [ ] 완료
- **파일**: M-16 `opal/tools/state-tool/state_tool.py` + M-17 `opal/tools/state-tool/README.md`
- **작업 내용**: §2 핵심 설계 M-16/M-17 명세대로 — (a) `--mode` choices에 `semi-agentic` 추가 (b) `MODE_BOUNDARY_STAGES` 상수 신설 (c) ERROR_CODES 신규 2종 + 기존 1종 메시지 갱신 (d) `check_close_gate` 조건 확장 (e) `cmd_mark`에 semi-agentic pre-EXECUTE 검증 추가 (f) `cmd_validate` 보강 (g) @header 갱신 (h) README mode choices 갱신 + 에러 카탈로그 갱신.
- **완료 기준**:
  1. `state_tool.py:1180` choices에 `"semi-agentic"` 추가
  2. `MODE_BOUNDARY_STAGES` 상수 정의
  3. ERROR_CODES에 `semi_agentic_pre_execute_auto_pass_denied` + `mode_flag_conflict` 신규 행 추가
  4. `check_close_gate` 조건이 `mode in ("agentic","semi-agentic")` 로 확장
  5. `cmd_mark` 검증 블록 추가
  6. `cmd_validate` 분기 추가
  7. `python state_tool.py --help` 정상 출력 (mode choices 표시)
  8. 단위 테스트(존재 시 `opal/tools/state-tool/tests`)에 semi-agentic 케이스 추가 + 통과
  9. README.md 변경이력 행 추가
  10. @header description 필드에 "3-way 모드 지원" 명시
- **테스트**:
  ```bash
  # mode choices 확인
  ~/.opal/tools/state-tool/run.sh init --help 2>&1 | grep -E "semi-agentic"
  # 임시 테스트 디렉토리에서 init 호출 (수동)
  mkdir -p /tmp/test-semi && ~/.opal/tools/state-tool/run.sh init /tmp/test-semi --skill opp --mode semi-agentic
  # cmd_mark에서 PLAN 단계 행에 --auto-pass 거부 확인
  # cmd_mark에서 EXECUTE 단계 행에 --auto-pass 허용 확인 (CLOSE 진입 게이트는 별도 적용)
  ```
- **의존**: Step 1 완료 (semi-agentic 모드 정의 확정 후)
- **agent**: opal-task-agent

### Step 6: pilot 7종 SKILL.md 일괄 갱신

- [ ] 완료
- **파일**: M-9 ~ M-15 (opp/opd/opds/opdw/opwt/oppd/opsdd 7개 파일)
- **작업 내용**: §2 핵심 설계 M-9~M-15 공통 패턴(a~d)을 각 pilot에 적용:
  - (a) Harness 절 모드 분기 3-way
  - (b) state init mode choices 갱신
  - (c) Agentic Mode 절 → "Agentic / Semi-Agentic 모드" 절로 확장 (opwt는 신규 추가). pilot별 모드 경계는 D-DEC-1(oppd) / D-DEC-2(opsdd) / N-1 §3 표 적용.
  - (d) 변경이력 행 추가 (각 SKILL.md의 SemVer 규칙 — 다음 minor 버전)
- **완료 기준**:
  1. 7개 파일 모두 Harness 절에 `semi-agentic` 분기 명시
  2. 7개 파일 모두 state init `<interactive|semi-agentic|agentic>` 갱신
  3. 7개 파일 모두 Agentic / Semi-Agentic 모드 절 존재 (opwt는 신규 절)
  4. oppd Phase 2 사용자 확정 행 = 모드 경계 명시 (D-DEC-1)
  5. opsdd Phase 3 DESIGN 사용자 Gate = 모드 경계 명시 (D-DEC-2)
  6. 7개 파일 변경이력 행 (일시 KST + 태스크 번호 140)
- **테스트**:
  ```bash
  for f in opal/skills/opal-pilot-{project,dev,dev-short,dev-wireframe,write-tech,project-dev,sdd}/SKILL.md; do
    echo "=== $f ===";
    grep -c "semi-agentic" "$f";
  done
  ```
  각 파일 매칭 카운트 ≥ 5 확인.
- **의존**: Step 1, Step 2, Step 3, Step 4, Step 5 완료 (각 SKILL.md가 신규 하네스 + 갱신된 공통 참조 + state-tool mode 인자를 인용해야 하므로)
- **agent**: opal-task-agent

### Step 7: 메모리/확정 기준 등록 — N-2 + M-18 + M-19

- [ ] 완료
- **파일**: N-2 `.opal/memory/preferences_default_semi_agentic.md` (신규) / M-18 `.opal/AGENT.md` / M-19 `.opal/MEMORY.md`
- **작업 내용**: §2 핵심 설계 N-2 / M-18 / M-19 명세대로 메모리 파일 생성 + 확정 기준 행 추가 + 메모리 인덱스 행 추가.
- **완료 기준**:
  1. `.opal/memory/preferences_default_semi_agentic.md` 파일 존재 + 7개 섹션 (요지/근거/관련 결정 D-DEC-1~D-DEC-7/인용)
  2. `.opal/AGENT.md` "도메인 지식" 표 모드 행 3-way 갱신
  3. `.opal/AGENT.md` "확정 기준" 표에 행 1 신규
  4. `.opal/MEMORY.md` "메모리" 표에 신규 행 (preferences / 2026-05-09 / 링크)
- **테스트**: `cat .opal/MEMORY.md | grep "preferences_default_semi_agentic"` 매칭. `cat .opal/AGENT.md | grep "PLAN까지 캡틴 검토"` 매칭.
- **의존**: Step 1~6 완료 (모든 결정사항 확정 후 메모리 등록)
- **agent**: opal-task-agent

### Step 8: install + 배포 검증

- [ ] 완료
- **파일**: `scripts/install-mac.sh` (변경 없음 — 검증만) + 배포 후 동작 검증
- **작업 내용**:
  1. `./scripts/install-mac.sh` 또는 메뉴 진입 후 `[1] OPAL Skills/Agents/References` 재배포 (사용자 발화로 트리거)
  2. `~/.opal/references/opal-harness-semi-agentic.md` 배포 확인
  3. `~/.opal/tools/state-tool/state_tool.py` 배포 후 `--help` 호출 시 mode choices에 `semi-agentic` 표시
  4. 임시 테스트 태스크 폴더 생성 후 `state init --mode semi-agentic` 정상 동작 확인
  5. 임시 PLAN 행에 `--auto-pass` 호출 시 `semi_agentic_pre_execute_auto_pass_denied` 에러 확인
  6. 임시 EXECUTE 행에 `--auto-pass` 호출 시 정상 처리 확인
  7. 임시 CLOSE 첫 행에 `--auto-pass` 호출 시 `agentic_close_gate_requires_user` 에러 확인
- **완료 기준**:
  1. install 완료 메시지 정상
  2. 배포된 파일 7~8개(N-1, M-1~M-8, M-16) 존재 확인
  3. state-tool semi-agentic 동작 검증 6단계 모두 통과
- **테스트**:
  ```bash
  ls -la ~/.opal/references/opal-harness-semi-agentic.md
  ~/.opal/tools/state-tool/run.sh init --help 2>&1 | grep semi-agentic
  # 임시 검증 시퀀스 (위 작업 내용 4~7번)
  ```
- **의존**: Step 1~7 완료
- **agent**: opal-task-agent (Bash 검증 명령 실행 위임)
- **롤백 트리거**: 검증 실패 시 §6 롤백 전략 발동

### Step 9: docs/ 갱신 검토

- [ ] 완료
- **파일**: PM이 직접 검토 — `docs/PROJECT.md` / `docs/ARCHITECTURE.md` / `docs/CONVENTIONS.md`
- **작업 내용**: 본 PLAN 변경이 docs/ 문서 내용에 영향을 미치는지 점검:
  - `docs/ARCHITECTURE.md` — 하네스 / 컴포넌트 표에 모드 체계 변경 반영 필요한지 확인 (현 §하네스 표에 `Agentic Mode` 행 없음, 단순 추가 권장)
  - `docs/CONVENTIONS.md` — §구현 규칙에 모드 체계 직접 언급 없음, 변경 없음
  - `docs/PROJECT.md` — 프로젝트 문서 테이블에 변경 없음
- **완료 기준**:
  1. docs/ 3개 파일 검토 완료
  2. 영향 있는 항목이 있으면 갱신 (변경이력 표 보유 파일은 행 추가)
  3. 영향 없는 항목은 명시적 "변경 불필요" 결론 기록 (PLAN §리스크 또는 별도 메모)
- **테스트**: PM이 직접 docs/ Read 후 결론 보고.
- **의존**: Step 1~7 완료 (모든 변경사항 SSOT 확정 후)
- **agent**: PM 직접 (영향 발견 시 후속 EXECUTE 단계로 docs/ 변경 Step 추가)

---

## 4. QA 체크리스트

### 기능 테스트

- [ ] **F1-1**: `opal-harness-semi-agentic.md`이 N-1 §구조의 9개 섹션을 모두 포함하는가
- [ ] **F1-2**: `opal-harness-semi-agentic.md` §3 모드 경계 표에 7개 pilot 모두 명시되었으며 D-DEC-1(oppd Phase 2) / D-DEC-2(opsdd DESIGN)와 일치하는가
- [ ] **F1-3**: `opal-harness-semi-agentic.md` §6 CLOSE 진입 게이트가 D-3 §7 / N-1 §6과 일치하는가
- [ ] **F1-4**: `opal-harness-semi-agentic.md` §7 AGENTIC-LOG 생성 시점이 D-DEC-7과 일치하는가 (semi-agentic = EXECUTE 진입 시점)
- [ ] **F2-1**: `opal-harness.md` §2 모듈 구조 표에 `semi-agentic` 행이 추가되었으며 로딩 규칙 3-way 갱신
- [ ] **F2-2**: `opal-harness-interactive.md` 도입부에 semi-agentic 준용 안내 1줄 추가
- [ ] **F2-3**: `opal-harness-agentic.md` §1 / §7 / §8에 semi-agentic 분기 명시
- [ ] **F3-1**: 7개 pilot SKILL.md 모두 Harness 절에 3-way 모드 분기 명시 (interactive/semi-agentic/agentic)
- [ ] **F3-2**: 7개 pilot SKILL.md 모두 state init `--mode <interactive|semi-agentic|agentic>` 갱신
- [ ] **F3-3**: opwt SKILL.md에 "Agentic / Semi-Agentic 모드" 절 신규 추가 (현재 미존재)
- [ ] **F3-4**: oppd SKILL.md의 모드 경계가 Phase 2 사용자 확정 행으로 명시 (D-DEC-1)
- [ ] **F3-5**: opsdd SKILL.md의 모드 경계가 Phase 3 DESIGN 사용자 Gate로 명시 (D-DEC-2)
- [ ] **F4-1**: state-tool `--mode` choices에 `semi-agentic` 추가 (`state_tool.py:1180`)
- [ ] **F4-2**: state-tool `MODE_BOUNDARY_STAGES` 상수가 정의되고 8개 stage 포함 (TASK/ANALYSIS/PLAN/SPEC/REVIEW/DESIGN/WBS/WIREFRAME)
- [ ] **F4-3**: state-tool ERROR_CODES에 `semi_agentic_pre_execute_auto_pass_denied` + `mode_flag_conflict` 신규 추가
- [ ] **F4-4**: state-tool `agentic_close_gate_requires_user` 메시지 갱신 + 조건이 `mode in ("agentic","semi-agentic")`로 확장
- [ ] **F4-5**: state-tool `cmd_mark`에서 semi-agentic 모드 + boundary stage 행에 `--auto-pass` 거부 동작
- [ ] **F4-6**: state-tool `cmd_mark`에서 semi-agentic 모드 + EXECUTE 등가 행에 `--auto-pass` 정상 처리
- [ ] **F4-7**: state-tool `cmd_validate`에서 semi-agentic 모드 + boundary stage 행 owner=auto 위반 검출
- [ ] **F4-8**: state-tool `build_rows_from_*`에서 semi-agentic 모드 시 사용자 확인 행 자동 마킹 안 함 (PLAN까지 사용자 검토)
- [ ] **F5-1**: op-task/SKILL.md TASK.md 헤더 템플릿 모드 필드 3-way 갱신
- [ ] **F6-1**: state-template.md / task-process.md / skill-commands.md / opal/AGENT.md mode 옵션 3-way 갱신
- [ ] **F7-1**: `.opal/AGENT.md` 확정 기준 표에 행 추가 (PLAN 검토/EXECUTE 자율 패턴)
- [ ] **F7-2**: `.opal/MEMORY.md` 메모리 표에 preferences 행 추가 + `memory/preferences_default_semi_agentic.md` 파일 생성
- [ ] **F8-1**: 변경 대상 모든 파일에 변경이력 행 추가 (일시 KST + 태스크 번호 140) — 9개 이상

### 일관성 테스트

- [ ] **C-1**: 7개 pilot SKILL.md의 모드 분기 텍스트가 동일 형식 (Harness 절 4-bullet 패턴: `--interactive` / `--agentic` / 모드 플래그 없음(기본) 또는 `--semi-agentic` / 다중 플래그 충돌)
- [ ] **C-2**: 7개 pilot의 모드 경계가 `opal-harness-semi-agentic.md` §3 표와 일치 (단일 SSOT 참조)
- [ ] **C-3**: state-tool ERROR_CODES와 모든 SKILL.md / 하네스 문서에서 인용된 에러 코드명이 일치 (`agentic_close_gate_requires_user` / `semi_agentic_pre_execute_auto_pass_denied` / `mode_flag_conflict`)
- [ ] **C-4**: AGENTIC-LOG 생성 시점이 모든 pilot에서 일관 (agentic = TASK 시작 / semi-agentic = EXECUTE 진입)
- [ ] **C-5**: state init `--mode` 호출 표기가 모든 pilot SKILL.md / state-template.md / task-process.md / op-task SKILL.md에서 동일 choices(`interactive|semi-agentic|agentic`)
- [ ] **C-6**: D-DEC-1 / D-DEC-2 결정이 oppd / opsdd SKILL.md와 N-1 §3 표와 일치
- [ ] **C-7**: 기존 진행 중 태스크의 STATE.md mode 필드(interactive/agentic)가 본 변경 후에도 그대로 유효 (D-DEC-4)

### 문서 품질

- [ ] **Q-1**: 한국어 본문 + 영어 코드/필드명 규칙 준수
- [ ] **Q-2**: kebab-case 파일/폴더 네이밍 (`opal-harness-semi-agentic.md` / `preferences_default_semi_agentic.md`는 메모리 snake_case 컨벤션 — `.opal/MEMORY.md`의 기존 메모리 파일 네이밍 패턴 `memory/{type}_{name}.md` 일관성 검증)
- [ ] **Q-3**: 변경이력 행이 모든 변경 파일에 추가되었는가 (일시 KST + semver + 태스크 번호 140)
- [ ] **Q-4**: 원문 인용 [MUST] 토큰이 PLAN.md / 변경 산출물에 누락 없이 명시되어 있는가
- [ ] **Q-5**: 배포 경계 준수 — `~/.opal/` 직접 편집 없음 (모든 변경은 프로젝트 소스에서 수행)
- [ ] **Q-6**: 인용 규칙(citation-rules.md) 준수 — 핵심 설계 문장 뒤에 `(→ D-N §N)` / `경로:줄번호` / `[MUST] '경로' §N: <원문>` 포맷 인용

---

## 5. 리스크 및 대응

| # | 리스크 | 영향 | 대응 방안 |
|---|--------|------|----------|
| R-1 | OPAL 시스템 코어(하네스 + state-tool) 광범위 변경 — 잘못된 변경 시 모든 pilot 동작 마비 | Critical | (a) Step 8 install + 검증 단계에서 6단계 동작 검증 강제 (b) §6 롤백 전략(git revert) 사전 정의 (c) 본 태스크 자체는 interactive 모드로 진행해 EXECUTE도 사용자 검토 |
| R-2 | state-tool Python 코드 회귀 — 기존 모드(interactive/agentic) 동작 변경 위험 | High | (a) `cmd_mark` / `check_close_gate` / `cmd_validate` 분기 확장만 수행, 기존 분기 그대로 유지 (b) `build_rows_from_*` 분기는 `mode == "agentic"` 그대로 — semi-agentic 추가하지 않음 (c) 기존 단위 테스트 통과 + 신규 semi-agentic 케이스 추가 |
| R-3 | 7개 pilot SKILL.md 갱신 누락 | High | (a) Step 6 완료 기준에 7개 파일 모두 매칭 카운트 검증 (b) QA 체크리스트 F3-1~F3-5에서 명시 검증 |
| R-4 | 변경이력 누락 — `.opal/AGENT.md` §금지사항 "변경이력 누락 금지" 위반 | Medium | (a) 본 PLAN §QA Q-3 항목 + Step 1~6 각 완료 기준에 변경이력 행 명시 (b) op-task-qa 검증 시 변경이력 행 존재 확인 강제 |
| R-5 | 모드 플래그 충돌 처리 미구현 — `--interactive --agentic` 동시 지정 시 동작 모호 | Medium | (a) state-tool에 `mode_flag_conflict` 에러 코드 추가 (b) state init 시 다중 플래그 거부 (c) pilot SKILL.md Harness 절에 명시 |
| R-6 | 기존 진행 중 태스크의 모드 호환성 — `last_task_number` 이전 태스크 STATE.md mode 변경 위험 | Medium | (a) D-DEC-4 채택 — 신규 태스크부터만 semi-agentic 기본 (b) state-tool은 mode=interactive/agentic 행 기존 동작 그대로 유지 (c) install 후 기존 태스크 STATE.md 변경 없음 검증 |
| R-7 | install-mac.sh `cp -Rf` 전체 복사 가정이 깨질 위험 — 신규 하네스 파일이 배포되지 않음 | Low | (a) Step 8 검증에서 배포 파일 존재 확인 (b) `install_opal_references()` 코드(`scripts/install-mac.sh:944`) 변경 없으나, 만약 향후 변경되면 신규 파일 자동 포함 보장 메커니즘 명시 필요 |
| R-8 | 영역 간 용어 일관성 — "PLAN-equivalent" / "EXECUTE-equivalent" 용어가 pilot마다 다른 단계명에 매핑 (oppd Phase 2 / opsdd DESIGN 등) | Medium | (a) `opal-harness-semi-agentic.md` §3 표를 단일 SSOT로 모든 pilot이 인용 (b) 각 pilot SKILL.md "Agentic / Semi-Agentic 모드" 절에서 §3 표 인용 (c) 본 리스크는 citation-rules.md §7 영역 간 용어 일관성 검토 대상이며, decision_required 발동하지 않음 — 채택안이 명확하므로 |
| R-9 | 본 태스크의 모드(interactive)와 도입 모드(semi-agentic)의 혼동 | Low | (a) TASK.md "참고 — 본 태스크의 모드와 도입 모드의 분리" 명시 (b) PLAN 본문 §1 영향 범위에 별도 행으로 구분 |

---

## 6. 롤백 전략 (R-1 대응)

본 태스크는 OPAL 시스템 코어를 변경하므로 install 후 검증 실패 시 즉시 롤백한다.

### 롤백 발동 조건

- Step 8 검증 6단계 중 어느 하나라도 실패
- 기존 모드(interactive/agentic)의 동작 회귀 발견
- 7개 pilot 중 하나라도 Harness 절 로딩 실패
- state-tool `--help` 호출 실패 또는 stack trace

### 롤백 절차

1. **즉시 PM(캡틴)에게 보고** — 검증 실패 항목 + stack trace 첨부
2. **변경 파일 git revert** — `git status`로 변경 파일 목록 확인, `git stash` 또는 `git checkout HEAD -- <파일>`로 되돌림
3. **재배포 — `./scripts/install-mac.sh`로 이전 상태 복구**
4. **state-tool 재검증** — 기존 `--mode <interactive|agentic>` 동작 정상 확인
5. **기존 진행 중 태스크 STATE.md 영향 확인** — `tasks/*/STATE.md` mode 필드 변경 없음 확인
6. **본 PLAN 재작성** — 실패 원인 분석 후 PLAN.md §결정 사항 또는 §실행 체크리스트 보강

### 롤백 후 재시도

- 본 태스크 자체는 interactive 모드이므로 캡틴 명시 승인 후 EXECUTE 재시작
- 반복 롤백 시(2회 이상) 캡틴 에스컬레이션 + 본 태스크 보류

---

## 부록: 참조 인용 일람 ([MUST] / 코드/줄번호 인용)

### [MUST] 인용 (재해석 금지 제약)

본 PLAN은 다음 [MUST] 토큰을 EXECUTE 워커에게 그대로 전달해야 한다 (citation-rules.md §2.4 / §4 단계별 의무).

- [MUST] `docs/CONVENTIONS.md` §구현 규칙 — Guards: "사용자가 명시적으로 '승인', '진행해', '구현해' 등의 실행 허가를 내리기 전까지 코드를 작성하거나 파일을 생성·수정하지 않는다."
- [MUST] `docs/CONVENTIONS.md` §구현 규칙 — Guards: "CLOSE 단계 진입 직전에는 사용자의 명시적 확인(`승인`/`확인`/`확인완료`)이 반드시 있어야 한다 (agentic 모드에서도 유지)."
- [MUST] `docs/CONVENTIONS.md` §구현 규칙 — 디스패치 의무: "오케스트레이터 SKILL.md에서 '워커 디스패치'로 정의된 단계(ANALYSIS/PLAN/EXECUTE 등)는 반드시 서브에이전트를 디스패치한다."
- [MUST] `docs/CONVENTIONS.md` §구현 규칙 — State 관리: "파이프라인 STATE.md 행 상태(⬜/🔄/✅) 변경은 `~/.opal/tools/state-tool/run.sh`로만 수행한다. 마크다운 표 직접 편집 금지."
- [MUST] `docs/CONVENTIONS.md` §구현 규칙 — 변경이력 작성 의무: "스킬·에이전트·참조 문서를 변경하면 '## 변경이력' 표에 행을 추가한다. 일시는 `YYYY-MM-DD HH:mm` (KST), 버전은 semver, 변경내용은 태스크 번호를 괄호로 포함 — 예: `(140)`."
- [MUST] `docs/CONVENTIONS.md` §구현 규칙 — 배포 경계: "`~/.opal/` 배포 파일을 직접 편집하지 않는다. 변경은 항상 프로젝트 소스(`opal/`, `skills/`, `agents/`, `community-skills/`, `scripts/`)에서 수행한다."
- [MUST] `docs/CONVENTIONS.md` §구현 규칙 — Citation Rules: "TASK.md / PLAN.md / ANALYSIS.md / QA 산출물 등을 작성할 때 모든 주장은 근거를 인용한다 (`{경로}:{라인}` 또는 `docs/문서명 §섹션`). `[MUST]` 토큰이 붙은 항목은 인용 누락 시 산출물 부적합 처리."
- [MUST] `docs/CONVENTIONS.md` §구현 규칙 — 플랫폼 분기 격리: "Claude / Cursor / Gemini / Antigravity 등 플랫폼별 차이는 어댑터 계층에서만 흡수한다. 스킬·에이전트 본문에 플랫폼 조건문을 추가하지 않는다."
- [MUST] `.opal/AGENT.md` §금지사항: "**`~/.opal/` 직접 편집 금지** — 항상 프로젝트 소스를 수정한 후 install로 배포한다."
- [MUST] `.opal/AGENT.md` §금지사항: "**STATE.md 마크다운 직접 편집 금지** — `state-tool`만 사용."
- [MUST] `.opal/AGENT.md` §금지사항: "**하네스 우회 금지** — Guards/Gates를 PM 임의 판단으로 건너뛰지 않는다 (특히 CLOSE 진입 게이트)."

### 코드/줄번호 인용

- `opal/core/references/opal-harness.md:60-79` — §2 모듈 구조 SSOT (M-1 변경 대상)
- `opal/core/references/opal-harness.md:78` — "새 모드 추가 시: 이 테이블에 행을 추가하고, 서브 하네스 파일을 생성한다" (D-DEC-3 근거)
- `opal/core/references/opal-harness-interactive.md:1-7` — interactive 도입부 (M-2 변경 대상)
- `opal/core/references/opal-harness-agentic.md:7-21` — §1 모드 정의 + §2 활성화 (M-3 변경 대상)
- `opal/core/references/opal-harness-agentic.md:90-93` — `agentic_close_gate_requires_user` 거부 명세
- `opal/core/references/opal-harness-agentic.md:159` — AGENTIC-LOG.md 생성 시점 (M-3 §8 변경 대상)
- `opal/core/references/harness/state-template.md:11-18` — state init 호출 명세 (M-4 변경 대상)
- `opal/core/references/harness/state-template.md:101` — 레거시 호환 원칙 (D-DEC-4 근거)
- `opal/core/references/harness/task-process.md:30-39` — 모드 플래그 기록 (M-5 변경 대상)
- `opal/core/references/harness/skill-commands.md:26-31` — 쌍슬래시 예시 (M-6 변경 대상)
- `opal/core/references/harness/citation-rules.md §0` — 근거 제시 원칙 [MUST]
- `opal/core/references/harness/citation-rules.md §2.4` — [MUST] 포맷
- `opal/core/references/harness/citation-rules.md §5` — 레거시 호환 (D-DEC-4 근거)
- `opal/skills/op-task/SKILL.md:107-200` — TASK.md 헤더 템플릿 (M-8 변경 대상)
- `opal/skills/opal-pilot-project/SKILL.md:14-20` / `:177-203` — opp Harness + Agentic Mode (M-9 변경 대상)
- `opal/skills/opal-pilot-project-dev/SKILL.md:22-32` / `:655-688` — oppd Harness + Agentic Mode + Phase 1/2/3 구조 (M-14 변경 대상)
- `opal/skills/opal-pilot-sdd/SKILL.md:21-30` / `:442-500` / `:467` — opsdd Harness + Agentic Mode + EXECUTE-LOOP 진입 (M-15 변경 대상 / D-DEC-2 근거)
- `opal/tools/state-tool/state_tool.py:28-32` — STAGE_ENUM (D-DEC-5 boundary stage 도출 근거)
- `opal/tools/state-tool/state_tool.py:64-67` — ERROR_CODES `agentic_close_gate_requires_user` (M-16 변경 대상)
- `opal/tools/state-tool/state_tool.py:311-348` — `check_close_gate` (M-16 변경 대상)
- `opal/tools/state-tool/state_tool.py:391` / `:483` — `build_rows_from_*` agentic 자동 마킹 (M-16 (f) 그대로 유지 근거)
- `opal/tools/state-tool/state_tool.py:790-892` — `cmd_mark` (M-16 (e) 변경 대상)
- `opal/tools/state-tool/state_tool.py:920-970` — `cmd_validate` (M-16 (f) 변경 대상)
- `opal/tools/state-tool/state_tool.py:1179-1180` — argparse `--mode` choices (M-16 (a) 변경 대상)
- `scripts/install-mac.sh:934-948` — `install_opal_references()` cp -Rf 전체 복사 (Step 8 검증 근거)
- `.opal/AGENT.md:51` — 도메인 지식 Agentic Mode 행 (M-18 변경 대상)
- `.opal/AGENT.md:67-73` — 확정 기준 표 (M-18 변경 대상)
- `.opal/MEMORY.md:23-27` — 메모리 표 (M-19 변경 대상)
- `tasks/140-260508-opp-default-semi-agentic-mode/TASK.md` — 본 태스크 입력 (전체)

---

> 본 PLAN은 EXECUTE 단계에서 워커에게 디스패치된다. PM은 §3 실행 체크리스트의 Step별 `agent` 필드(전부 `opal-task-agent` — `docs/PROJECT.md` "프로젝트 구성" 표 Framework 영역 단일 에이전트 매핑 / Step 9는 PM 직접)에 따라 디스패치한다.
