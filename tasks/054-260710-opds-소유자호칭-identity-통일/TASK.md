# TASK: 산출물 소유자 호칭을 identity.md owner_name 기준으로 하네스 통일

> 작성일: 2026-07-10 | 작업 유형: 개선 | 적용 스킬: opds | 모드: agentic
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

산출물(state.json note·DONE.md 등)의 소유자 호칭이 **항상 로컬 `~/.opal/identity.md`의 `owner_name`을 기준**으로 작성되도록 하네스를 통일한다. 로드된 레포 컨텍스트(MEMORY 브리핑·brain·직전 태스크 산출물)의 지배 호칭을 계승하는 **오염(contamination)을 차단**한다.

## 배경

OPAL 에이전트가 생성하는 산출물의 소유자 호칭이 로컬 identity에 신뢰성 있게 묶이지 않고, 세션에 로드된 프로젝트 컨텍스트에서 우세한 호칭에 오염된다. 그 결과 다른 개발자의 세션 산출물도 레포에 지배적인 호칭으로 찍혀, `state.json` note만으로는 "누가 승인/확인했는가"를 신뢰할 수 없다.

## 배경 분석 (대화에서 도출)

pointail 레포(`/Volumes/Data/StoreLinkStudio/pointail`)에서 실증 확인된 사실:

- **증상**: git author가 `Yoonhwan Jung <unani92@naver.com>`인 태스크 030·029·027의 산출물이 전부 "캡틴 승인/직접확인"으로 기록됨. 승인/확인 note 호칭 집계 = **캡틴 29건, 그 외 0건**(완전 균일).
- **원인 규명 (ai-framework 소스 대조)**:
  - `state-tool`은 `--note` 텍스트를 **그대로 저장**만 한다 — `~/.opal/identity.md`를 읽지 않는다. `--owner`는 역할 enum(PM/worker/user/auto)이지 사람 이름이 아니다 (`opal/tools/state-tool/state_tool.py`).
  - 하네스 note 예시는 이미 `{owner_name} 확인: …` 플레이스홀더로 올바르다(task 139, 2026-05-09에 하드코딩 "캡틴"→`{owner_name}` 치환 완료 — `opal/core/references/opal-harness-agentic.md:105` 등).
  - **진짜 갭**: `{owner_name}`을 **어디서 채우라는 결정론적 규칙이 없다**. LLM이 note를 지을 때 로컬 identity 대신 로드된 레포 컨텍스트의 지배 호칭을 채운다. `AGENT.md §정체성 적용`은 "소유자를 `{owner_name}`으로 부른다"고만 하며 이는 **대화 호칭** 지침이지 **영속 산출물 호칭을 identity로 못박는** 규칙이 아니다.
  - 정리: **"매번 읽는다 ≠ 매번 그 값을 쓴다"** — 읽기(부트스트랩 Phase A)와 사용(note 작성) 사이에 강제 링크가 없어 컨텍스트 우세항에 밀린다.

## 확정된 설계 방향 (대화에서 합의)

캡틴 지시: **"identity.md > owner_name 로 작성되게 하네스를 통일"**, 그리고 **"2개 방식이 모두 공조"** — 아래 A(도구 집행)·B(문서 규칙)를 함께 적용한다. (헌법 Core Stance: *"규칙이 항상 성립해야 하면 프로즈가 아니라 도구가 집행한다"* — 문서 규칙만으로는 컨텍스트 압력에 재오염되므로 도구 집행이 필수.)

- **A — 도구 집행 (도구가 닿는 경로 봉인)**: `state-tool`이 note 작성 시 `~/.opal/identity.md`의 `owner_name`을 직접 읽어 결정론적으로 반영한다(유력안: note 내 `{owner_name}` 플레이스홀더를 write 시점에 치환 → LLM은 호칭을 못 씀 → 오염 원천 차단). 정확한 메커니즘은 PLAN에서 확정.
- **B — 문서 규칙 (도구가 안 닿는 자유서술 산출물)**: 하네스 SSOT에 "소유자 호칭은 **매 작성 시점에 identity.md `owner_name`에서 재확인하여** 해석하고, 로드된 레포 컨텍스트(MEMORY·brain·직전 태스크)의 호칭을 계승하지 않는다(오염 금지)"를 명문화한다. DONE.md 등 LLM 자유서술 산출물이 대상.
- **공조 관계**: 도구가 닿는 곳(state.json note)은 A가 봉인, 안 닿는 곳(DONE.md 등)은 B가 규칙+재확인으로 커버한다.

## 명확화 결과

> TASK 4요소를 잠근다.

| 요소 | 확정값 | 미확정(있으면) | 의존 사실 |
|------|--------|--------------|----------|
| 목표 | 산출물 소유자 호칭을 로컬 `~/.opal/identity.md` `owner_name` 기준으로 통일하고 레포 컨텍스트 오염을 차단 (A 도구 집행 + B 문서 규칙 공조) | A의 정확한 치환 메커니즘(플레이스홀더 치환 vs 구조 필드) | PLAN에서 결정 |
| 범위 | 포함: state_tool.py(note에 identity 반영) + README + 테스트, 하네스 SSOT 문서 규칙 명문화 + note 예시 통일, identity 부재 폴백. 제외: 과거 산출물 소급 정정, git author 감사 시스템 신설, identity.md 스키마 변경 | - | citation-rules §5 레거시 호환 |
| 제약 | 배포 경계(~/.opal 직접 편집 금지, opal/ 소스 수정 후 install) / 플랫폼 독립(OPAL_HOME 기준, 하드코딩 분기 금지) / state-tool 하위호환(기존 note 회귀 0) / 변경이력 행 추가 | - | `.opal/AGENT.md` 금지사항 |
| 완료기준 | 아래 "요구사항" AC 전체 충족 + RED→GREEN 테스트 통과 + 하드코딩 호칭 잔존 grep 0건 | - | - |

## 요구사항

- [ ] **R-1 (A) state-tool identity 반영**: `state-tool`이 note 작성 시 `~/.opal/identity.md`의 `owner_name`을 읽어 소유자 호칭을 결정론적으로 반영한다.
  - 어디에: `opal/tools/state-tool/state_tool.py` (mark/advance의 note 처리 경로)
  - 왜: 확정 방향 A — 도구가 닿는 경로의 오염 원천 차단
  - AC: `--note "{owner_name} 확인: 검토 완료"` 호출 시, state.json에 identity.md의 `owner_name` 값으로 치환되어 저장된다(예: owner_name=루카스 → `"루카스 확인: 검토 완료"`). RED 테스트가 먼저 실패하고, 구현 후 통과한다.
- [ ] **R-2 (A) 하위호환·폴백**: 플레이스홀더가 없는 기존 note는 변경 없이 저장된다. `~/.opal/identity.md` 부재 또는 `owner_name` 공란 시 정의된 폴백대로 동작한다(치환 스킵 + 원문 유지, 또는 PLAN이 정한 폴백).
  - 어디에: `state_tool.py` + `opal/tools/state-tool/README.md`
  - 왜: 제약 — 회귀 0 + fail-safe
  - AC: 플레이스홀더 없는 note 저장 회귀 테스트 PASS. identity 부재 케이스 테스트 PASS(에러 없이 폴백).
- [ ] **R-3 (B) 하네스 오염 차단 규칙 명문화**: 소유자 호칭을 매 작성 시점 identity.md `owner_name`에서 해석하고 레포 컨텍스트 계승을 금지하는 규칙을 하네스 SSOT에 추가한다.
  - 어디에: `opal/core/references/opal-harness.md`(또는 sub-harness 적정 위치) + `opal/core/AGENT.md §정체성 적용` 보강
  - 왜: 확정 방향 B — 자유서술 산출물 커버
  - AC: 지정 문서에 "identity.md owner_name 기준 + 레포 컨텍스트 호칭 계승 금지" 규칙 문장이 존재한다.
- [ ] **R-4 (B) note 예시·DONE.md 규칙 통일**: 모든 note 예시가 `{owner_name}` 플레이스홀더로 통일되고, DONE.md 등 자유서술 산출물의 소유자 호칭 작성 규칙이 명시된다.
  - 어디에: `opal-harness-agentic.md`, `opal-harness-semi-agentic.md`, `tools.md`, `opal/skills/opal-pilot-*` 및 `op-task`/CLOSE 관련 SKILL.md의 note·DONE.md 예시
  - 왜: 확정 방향 B — 예시 일관성
  - AC: 대상 문서의 소유자 호칭 하드코딩("캡틴" 등 특정 이름)이 예시/규칙 본문에서 0건이다(변경이력·도메인 지식 테이블 제외). grep으로 검증.
- [ ] **R-5 변경이력**: 수정한 모든 참조 문서·도구 README에 변경이력 행을 추가한다(일시 KST + 태스크 054).
  - AC: `git diff`상 변경된 각 문서에 054 변경이력 행이 존재한다.

## 제약 조건

- **배포 경계**: `~/.opal/` 배포본을 직접 편집하지 않는다. `opal/` 프로젝트 소스를 수정한 뒤 install로 재배포한다. 테스트·검증은 소스 기준.
- **플랫폼 독립성**: identity.md 경로 해석은 `OPAL_HOME`(기본 `~/.opal`) 기준. Claude/Cursor/Gemini 하드코딩 분기 금지.
- **하위호환**: 기존 note(플레이스홀더 미포함) 저장 동작 불변 — 회귀 0.
- **RED-first**: state-tool 로직 변경은 self-confirming 위험 영역 → RED 증거 확보 후 GREEN.

## 기술 스택

- Python (state_tool.py, pytest/자체 테스트 하네스) · Markdown/YAML(하네스 문서) · Bash(run.sh 래퍼)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | state_tool.py | `opal/tools/state-tool/state_tool.py` | note 저장 로직 — A 도구 집행 대상 |
| D-2 | 설계 | opal-harness-agentic.md | `opal/core/references/opal-harness-agentic.md` | note 예시(`{owner_name} 확인`) — B 규칙 대상 |
| D-3 | 설계 | opal-harness-semi-agentic.md | `opal/core/references/opal-harness-semi-agentic.md` | note 예시 — B 규칙 대상 |
| D-4 | 설계 | AGENT.md §정체성 적용 | `opal/core/AGENT.md` | "소유자를 {owner_name}으로 부른다" — 호칭 해석 규칙 보강 |
| D-5 | 설계 | citation-rules.md §5 | `opal/core/references/harness/citation-rules.md` | 레거시 호환 — 과거 산출물 소급 정정 제외 근거 |
| D-6 | 소스 | identity-template.md | `opal/core/identity-template.md` | owner_name 필드 스키마 확인 |
