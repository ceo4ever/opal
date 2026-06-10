# TASK: TDD RED-first 트랙 도입 — 독립 RED 작성 + 테스트코드 산출물 + state-tool red 게이트

> 작성일: 2026-06-09 | 작업 유형: 개선 | 적용 스킬: opds | 모드: agentic
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

OPAL 하네스에 "실행 가능한 RED 테스트 코드 → GREEN 구현" 규율을 도입한다. 현재 자연어 시나리오 + 즉석 Bash 명령에 머무는 테스트를, **프로젝트 소스 트리에 영속하는 테스트 코드 산출물**과 **실패 증거(RED) 선확보 후 구현(GREEN)**이라는 TDD 사이클로 강화한다.

## 배경

현재 OPAL 테스트 흐름(`opal-pilot-dev-short` STEP 2~4, `op-dev-test-scenario`, `op-dev-execute`, `opal-test-agent`)은 다음 한계가 있다:

- TEST-SCENARIO.md는 자연어 Given/When/Then + 즉석 "실행 명령"뿐 → **영속하는 테스트 파일(pytest/vitest 등)이 남지 않아** 회귀 안전망이 누적되지 않는다.
- EXECUTE 자가점검은 "코드 작성 → 실행 → PASS"로 **GREEN만 확인**한다. TDD 핵심인 "먼저 실패하는 테스트(RED)를 증거로 확보 → 그다음 구현" 순서가 없다.
- 같은 워커가 구현과 검증을 겸하면 self-confirming(약한 테스트로 통과) 위험이 있다. 헌법 §4(동작 증거)는 목업을 차단하지만, "테스트 코드 자체가 부실/자기충족적"인 경우는 아직 deterministic하게 막지 못한다.

## 배경 분석 (대화에서 도출)

설계 대화에서 현재 구조와 베스트 프랙티스를 대조했다.

**현재 구조 (코드 확인 완료)**:
- 시나리오 작성 주체 = PM(`op-dev-test-scenario`, STEP 3.5 직접 수행). "실행 명령/결과/상세" 칸은 빈칸으로 워커에 위임 (`opal/skills/op-dev-test-scenario/SKILL.md`).
- 실제 실행 = EXECUTE 워커(L1/L2 자가점검, `opal/skills/op-dev-execute/SKILL.md:57-66`) + TEST 워커(`opal/agents/opal-test-agent/AGENT.md`, M1/M2/M3 실행방식).
- 증거 강제 = 헌법 §4 + `state-tool verify`(태스크 013 — 목업 패턴·증거 누락 검출).
- 계층 L1/L2/L3 + 실행방식 M1/M2/M3 체계 존재 (`op-dev-test-scenario/references/test-scenario-guide.md:48-96`).

**갭**: (1) 테스트 코드 산출물 부재, (2) RED-first 부재, (3) 작성자≠구현자 분리 부재, (4) 테스트 불변성(reward hacking 방어) 부재.

**외부 베스트 프랙티스 근거**:
- RED/GREEN 분리 필요 — 에이전트는 둘을 한 프롬프트에 합치는 경향 ([aihero TDD skill](https://www.aihero.dev/skills-tdd), [Codex TDD](https://codex.danielvaughan.com/2026/04/10/codex-cli-test-driven-development-workflow/)).
- 테스트 보호 = reward hacking 방어. 프런티어 모델이 통과 목적으로 테스트를 약화·삭제하는 사례 ([METR](https://metr.org/blog/2025-06-05-recent-reward-hacking/), [ImpossibleBench](https://www.lesswrong.com/posts/qJYMbrabcQqCZ7iqm/impossiblebench-measuring-reward-hacking-in-llm-coding-1)).
- 공개 인터페이스로 검증, 내부 구현 결합 금지 ([aihero TDD skill](https://www.aihero.dev/skills-tdd)).
- 외부 진실원(exit code)으로만 GREEN 판정 — Codex의 Stop 훅. OPAL은 플랫폼 훅이 아닌 `state-tool`로 집행해야 헌법(플랫폼 독립성)에 부합.

## 확정된 설계 방향 (대화에서 합의)

| # | 합의 사항 | 비고 |
|---|----------|------|
| C-1 | **독립 RED 작성** — TEST-SCENARIO 단계에서 PM/QA가 M1 시나리오를 "실패하는 실제 테스트 코드"로 변환·실행·실패증거 확보. EXECUTE 워커는 테스트 파일 수정 금지. 작성자≠구현자. | self-confirming/reward-hacking 최강 방어. OPAL 기존 "작성자(PM)↔검증자(test-agent) 분리" 철학과 일치. |
| C-2 | **테스트 스택·위치는 프로젝트 구성 탐지** — pytest/vitest 등 하드코딩 금지. `CONVENTIONS.md` → 스택 문서 → 설정파일(`package.json`/`pyproject.toml`/`go.mod`) → 기존 테스트 관례 순으로 도출. 테스트 인프라 부재 시 자동 우회 금지·사용자 에스컬레이션. | 헌법: 플랫폼·프로젝트 독립성. 탐지 로직 자체가 어댑터. |
| C-3 | **모듈 미러링 배치** — 테스트 코드는 "대상 모듈"에 붙는다(태스크 폴더가 아님). 대상 모듈명 기반 파일, 프로젝트 관례 위치. 추적은 ① 케이스명 프리픽스(`[T016/L1-AC1]`) ② 테스트 파일 @header(`task`, `scenarios`) ③ TEST-SCENARIO §4 매핑표 "테스트 파일:케이스" 열. 모듈 1개=테스트 파일 1개, 후속 태스크는 기존 파일에 케이스 추가. | 러너 발견성·관례 준수·회귀 누적 동시 충족. |
| C-4 | **집행은 state-tool(deterministic)** — RED 체크포인트(실패 증거 없으면 GREEN 진입 차단) + 테스트 불변성(fix 루핑 중 테스트 파일 수정 거부). Claude 훅이 아닌 state-tool로 플랫폼 중립 집행. | 헌법: enforce don't advise. 태스크 013 `verify` 확장. |

> **산출물 위치 구분**: 테스트 코드 = 대상 프로젝트 소스 트리(영속 코드, 커밋됨) / 시나리오·RED 증거 = 태스크 폴더 문서.

## 요구사항

- [ ] **R-1 (RED-first 파이프라인)**: TEST-SCENARIO/EXECUTE 흐름에 "RED(실패 테스트코드 작성·실행·실패증거 확보) → GREEN(구현)" 순서가 명문화된다.
  - **무엇을**: opds(및 공유 시 opd) 파이프라인 단계 정의에 RED→GREEN 순서 추가
  - **어디에**: `opal/skills/opal-pilot-dev-short/SKILL.md` STEP 2~3, `op-dev-test-scenario/SKILL.md`, `op-dev-execute/SKILL.md`
  - **왜**: 확정 방향 C-1
  - **AC**: 해당 SKILL.md들에 "RED 단계에서 실패 테스트 코드를 작성하고 실행하여 실패(exit code≠0)를 증거로 기록한 뒤 GREEN(구현) 진입"이 명시되고, GREEN 진입 전제로 RED 증거 존재가 기술된다.

- [ ] **R-2 (독립 RED 작성 — 작성자≠구현자)**: RED 테스트 코드 작성 주체가 EXECUTE 구현 워커와 분리된다.
  - **무엇을**: RED 테스트 코드 작성 주체/시점 정의 + EXECUTE 워커의 "테스트 파일 수정 금지" Scope 제약 추가
  - **어디에**: `op-dev-test-scenario/SKILL.md`(또는 RED 작성 담당 정의), `op-dev-execute/SKILL.md` Scope 제한
  - **왜**: 확정 방향 C-1
  - **AC**: RED 테스트 코드 작성 담당이 문서에 명시되고, `op-dev-execute`에 "RED 테스트 파일은 수정 금지(위반 시 블로커)" 규칙이 존재한다.

- [ ] **R-3 (테스트 스택·위치 탐지)**: 테스트 프레임워크/언어/배치 위치를 프로젝트 구성에서 탐지하는 절차가 정의된다.
  - **무엇을**: 탐지 우선순위(CONVENTIONS→스택문서→설정파일→기존 관례) + 인프라 부재 시 에스컬레이션 규칙
  - **어디에**: `op-dev-test-scenario/references/test-scenario-guide.md`(탐지 절차 추가)
  - **왜**: 확정 방향 C-2
  - **AC**: 가이드에 탐지 우선순위 4단계가 순서대로 기재되고, "테스트 러너 부재 시 자동 우회 금지·사용자 에스컬레이션" 규칙이 명시된다. 특정 프레임워크(pytest 등) 하드코딩이 없다.

- [ ] **R-4 (모듈 미러링 배치·명명·추적 규칙)**: 테스트 코드 배치/파일명/추적 규칙이 정의된다.
  - **무엇을**: 모듈 미러링 배치 + 케이스명 프리픽스 + 테스트 파일 @header 필드 + TEST-SCENARIO §4 매핑표 "테스트 파일:케이스" 열
  - **어디에**: `op-dev-test-scenario/references/test-scenario-guide.md`, `op-dev-test-scenario/SKILL.md`(§4 매핑표 스키마), `opal/core/references/harness/header-rules.md`(테스트 파일 @header)
  - **왜**: 확정 방향 C-3
  - **AC**: 가이드에 "모듈 1개=테스트 파일 1개, 후속 태스크는 기존 파일에 케이스 추가" 규칙과 케이스명 프리픽스 포맷이 기재되고, §4 매핑표 스키마에 "테스트 파일:케이스" 열이 추가되며, header-rules에 테스트 파일 @header 필드(task/scenarios)가 정의된다.

- [ ] **R-5 (state-tool RED 게이트 + 테스트 불변성 — 코드)**: state-tool에 RED 증거 검증과 테스트 파일 수정 차단을 deterministic하게 집행하는 기능이 추가된다.
  - **무엇을**: (a) RED 증거(실패 출력) 누락 시 GREEN/EXECUTE mark 차단, (b) fix 루핑 중 테스트 파일 변경 검출 시 거부. ERROR_CODES 추가.
  - **어디에**: `opal/tools/state-tool/` (소스 + 테스트)
  - **왜**: 확정 방향 C-4, 헌법 §4(enforce don't advise)
  - **AC**: state-tool에 RED 게이트/테스트 불변성 검증 로직이 추가되고, 신규 ERROR_CODES(예: `red_evidence_missing`, `test_modified_in_fix`)가 정의되며, 이를 검증하는 단위 테스트가 추가되어 전체 테스트 스위트가 PASS한다. (RED-first 자기적용: 이 기능의 테스트를 먼저 작성해 실패 확인 후 구현)

- [ ] **R-6 (공개 인터페이스 검증 규율)**: 테스트가 내부 구현이 아닌 공개 인터페이스/관찰 가능 행위를 검증하도록 하는 원칙이 추가된다.
  - **무엇을**: "내부 구현/private 결합 금지, 공개 인터페이스·관찰 행위로 검증" 1~2줄 규칙
  - **어디에**: `op-dev-test-scenario/references/test-scenario-guide.md`, `opal/core/references/harness/coding-principles.md`
  - **왜**: 확정 방향(검색 근거 — 구현 결합 안티패턴 회피)
  - **AC**: 두 문서에 해당 원칙이 명시된다.

- [ ] **R-7 (변경이력·배포 정합)**: 수정된 모든 스킬·에이전트·참조 문서에 변경이력 행이 추가되고, install 배포 영향이 식별된다.
  - **무엇을**: 변경이력 행 추가(일시 KST + 태스크 016) + 배포 대상 식별
  - **어디에**: 변경된 각 SKILL.md/AGENT.md/참조 문서 변경이력 표, 후속 install 배포 메모
  - **왜**: 프로젝트 금지사항(변경이력 누락 금지) + 배포 경계
  - **AC**: 변경된 모든 문서에 016 변경이력 행이 존재하고, DONE.md에 install 재배포 필요 여부가 기재된다.

## 제약 조건

- **배포 경계 준수**: `~/.opal/` 직접 수정 금지. 프로젝트 소스(`opal/`, `skills/`, `agents/`)만 수정 후 install로 재배포.
- **플랫폼 독립성**: 테스트 러너/언어 하드코딩 금지. Claude 전용 훅에 의존 금지 — 집행은 state-tool(플랫폼 중립).
- **하위 호환**: 테스트 인프라가 없는 프로젝트/문서 전용 태스크에서 RED 트랙이 강제 실패를 유발하지 않아야 한다(에스컬레이션 또는 graceful skip).
- **자기적용(dogfooding)**: R-5(state-tool 코드)는 RED-first로 구현한다 — 테스트 먼저 작성·실패 확인 후 구현.
- **SSOT 준수**: 하네스 규칙은 SSOT 문서에 정의하고 발췌·복제하지 않는다.
- **opds 범위 확인**: PLAN 결과 변경 파일 ≥10 또는 다단계 의사결정이 확인되면 Full Task(opd) 에스컬레이션을 사용자에게 제안한다(자동 전환 금지).

## 기술 스택

- Markdown (스킬·에이전트·참조 문서), YAML (frontmatter), Bash/Node.js (state-tool, date 도구)
- state-tool 구현 언어/테스트 러너: `opal/tools/state-tool/` 기존 구성을 따른다 (PLAN에서 확인)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | OPAL 헌법 | `~/.opal/PRINCIPLES.md` §4 | 동작 증거·목업 금지 — RED/GREEN 집행 근거 |
| D-2 | 소스 | opal-pilot-dev-short SKILL | `opal/skills/opal-pilot-dev-short/SKILL.md` | 파이프라인 STEP 2~4 (RED-first 삽입 지점) |
| D-3 | 소스 | op-dev-test-scenario SKILL | `opal/skills/op-dev-test-scenario/SKILL.md` | 시나리오 작성·§4 매핑표 (RED 작성 주체) |
| D-4 | 소스 | op-dev-test-scenario 가이드 | `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md` | 계층·실행방식·탐지 절차 추가 지점 |
| D-5 | 소스 | op-dev-execute SKILL | `opal/skills/op-dev-execute/SKILL.md` | 자가점검·Scope 제한 (테스트 파일 수정 금지) |
| D-6 | 소스 | opal-test-agent | `opal/agents/opal-test-agent/AGENT.md` | TEST 단계 실행·증거 기록 |
| D-7 | 소스 | state-tool | `opal/tools/state-tool/` | RED 게이트·테스트 불변성 구현 대상 |
| D-8 | 설계 | header-rules | `opal/core/references/harness/header-rules.md` | 테스트 파일 @header 필드 정의 |
| D-9 | 설계 | coding-principles | `opal/core/references/harness/coding-principles.md` | 공개 인터페이스 검증 규율 |
| D-10 | 설계 | CONVENTIONS | `docs/CONVENTIONS.md` | 변경이력·@header·테스트 위치 컨벤션 |
| D-11 | 외부 | aihero TDD skill | [aihero TDD skill](https://www.aihero.dev/skills-tdd) | RED/GREEN 분리·공개 인터페이스 검증 근거 |
| D-12 | 외부 | Codex CLI TDD | [Codex CLI TDD](https://codex.danielvaughan.com/2026/04/10/codex-cli-test-driven-development-workflow/) | 테스트 보호·exit code 게이트 근거 |
| D-13 | 외부 | METR reward hacking | [METR](https://metr.org/blog/2025-06-05-recent-reward-hacking/) | 테스트 약화·삭제 reward hacking 근거 |
