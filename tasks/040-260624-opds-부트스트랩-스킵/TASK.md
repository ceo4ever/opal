# TASK: OPAL 부트스트랩 스킵 옵션 (`OPAL_BOOTSTRAP=off`)

> 작성일: 2026-06-24 | 작업 유형: 개선 | 적용 스킬: opds | 모드: agentic
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

`OPAL_BOOTSTRAP=off` 환경변수로 OPAL 부트스트랩 전체를 스킵하는 옵션을 추가한다. 설정 시 모든 플랫폼(Claude/Cursor/Gemini/Codex)에서 OPAL 에이전트 없이 순수 Claude Code로 동작한다.

## 배경

OPAL 부트스트랩 Eager 단계는 principles → identity → harness → pm → 프로젝트 AGENT.md → MEMORY → PROJECT 순으로 7개 문서를 로드한다. 이 부하가 비OPAL 단발 잡담이나 프레임워크 자체 디버깅 세션에서 불필요한 토큰·지연을 발생시킨다.

기존 `[WORKER]` 스킵 메커니즘은 워커 전용(디스패치 프롬프트 첫 줄)이며 캡틴 세션에는 적용되지 않는다.

## 배경 분석 (대화에서 도출)

- **현재 부트스트랩 진입점**: 4종 플랫폼 마커(CLAUDE.md/Cursor .mdc/GEMINI.md/Codex AGENTS.md)가 "첫 응답 전 `~/.opal/AGENT.md` Read" 지시 산문을 포함. 마커는 LLM이 읽는 산문이므로 셸 변수를 직접 판독 불가.
- **해법**: 마커 텍스트에 "Bash 1회로 `echo $OPAL_BOOTSTRAP` 실행 → `off`이면 이하 절차 전체 스킵" 조건을 삽입. Claude Code는 Bash 도구를 보유하므로 가능.
- **스킵 범위 확정**: 정체성 포함 **전부 스킵** — `off` 시 순수 Claude Code로 동작(OPAL 정체성·harness·PM 컨텍스트 모두 미로드).
- **배포 경계**: `~/.opal/` 직접 편집 금지. 소스(`opal/`, `scripts/`) 수정 후 install 재배포 시 발효.
- **플랫폼 어댑터 SSOT**: `scripts/install-mac.sh`가 4종 플랫폼 마커 emit 담당. `scripts/windows.ps1`은 미러.

## 확정된 설계 방향 (대화에서 합의)

1. **발동 방식**: 환경변수 `OPAL_BOOTSTRAP=off` (세션/셸 단위 토글)
2. **스킵 범위**: 정체성 포함 전부 스킵 (`off` → 순수 Claude Code, 부분 스킵 없음)
3. **메커니즘**: 각 플랫폼 마커 텍스트에 skip 게이트 문구 삽입 — "먼저 Bash로 `echo $OPAL_BOOTSTRAP` 실행; 출력 `off`이면 이하 절차 전체 생략"
4. **적용 범위**: 전 플랫폼 동시 (Claude/Cursor/Gemini/Codex — `install-mac.sh` + `windows.ps1` 4종 어댑터)
5. **플랫폼 분기**: 어댑터 계층(`install-mac.sh`/`windows.ps1`)에만 — `opal/core/AGENT.md`에는 명문화(문서), 마커 emit 로직에서 적용

## 명확화 결과

> TASK 4요소를 잠근다. 각 요소는 확정값 또는 명시적 "N/A: <사유>"로 채운다.

| 요소 | 확정값 | 미확정(있으면) | 의존 사실 |
|------|--------|--------------|----------|
| 목표 | `OPAL_BOOTSTRAP=off` env로 모든 플랫폼에서 부트스트랩 완전 스킵 | - | - |
| 범위 | 포함: `scripts/install-mac.sh`(4종 마커 emit) + `opal/core/AGENT.md`(문서화) + `scripts/windows.ps1`(미러). 제외: harness/identity/principles 파일 내용 변경 없음, 기존 `[WORKER]` 메커니즘 불변 | 각 플랫폼별 emit 함수명·행 번호 → PLAN 분석 | 배포 경계: `~/.opal/` 직접 편집 금지 |
| 제약 | [MUST] `opal/core/AGENT.md` §금지사항: "`~/.opal/` 직접 편집 금지 — 항상 소스 수정 후 install 재배포". [MUST] `opal/core/AGENT.md` §행동규칙: "플랫폼 분기는 어댑터 계층에서만" | - | install 재배포 후 발효 |
| 완료기준 | ① install 재배포 후 `OPAL_BOOTSTRAP=off` 설정 세션에서 Bash 1회 후 부트스트랩 Read 0건. ② 미설정/on 세션에서 기존 부트스트랩 정상 동작. ③ 4종 플랫폼 마커 emit 함수에 skip 게이트 문구 포함 확인(grep). ④ `opal/core/AGENT.md` Eager 절차에 스킵 게이트 섹션 존재 | - | - |

## 요구사항

- [ ] **F-1** `scripts/install-mac.sh` Claude(CLAUDE.md) 마커 emit 함수에 `OPAL_BOOTSTRAP=off` skip 게이트 문구 삽입
  - 무엇을: 마커 텍스트 서두에 "Bash로 `echo $OPAL_BOOTSTRAP` 실행; `off`이면 이하 절차 전체 스킵" 조건 추가
  - 어디에: `scripts/install-mac.sh` 내 CLAUDE.md 마커 생성 함수
  - 왜: 확정 방향 §3 — 마커 텍스트가 skip 분기의 진입점
  - AC: install 재배포 후 생성된 `~/.claude/CLAUDE.md`(또는 해당 경로) OPAL 마커 블록에 `OPAL_BOOTSTRAP` 체크 문구가 존재함

- [ ] **F-2** `scripts/install-mac.sh` Cursor `.mdc` 마커 emit 함수에 동일 skip 게이트 문구 삽입
  - 무엇을: F-1과 동일 문구
  - 어디에: `scripts/install-mac.sh` 내 Cursor 어댑터 emit 함수
  - 왜: 확정 방향 §4 — 전 플랫폼 동시 적용
  - AC: 생성된 Cursor 마커 파일에 skip 게이트 문구 존재

- [ ] **F-3** `scripts/install-mac.sh` Codex `AGENTS.md` 마커 emit 함수에 동일 skip 게이트 문구 삽입
  - 무엇을: F-1과 동일 문구
  - 어디에: `scripts/install-mac.sh` 내 Codex 어댑터 emit 함수
  - 왜: 확정 방향 §4
  - AC: 생성된 Codex 마커에 skip 게이트 문구 존재

- [ ] **F-4** `scripts/install-mac.sh` Gemini `GEMINI.md` 마커 emit 함수에 동일 skip 게이트 문구 삽입
  - 무엇을: F-1과 동일 문구
  - 어디에: `scripts/install-mac.sh` 내 Gemini 어댑터 emit 함수
  - 왜: 확정 방향 §4
  - AC: Gemini 마커 emit 로직에 skip 게이트 문구 존재

- [ ] **F-5** `opal/core/AGENT.md` Eager 절차 최상단에 `OPAL_BOOTSTRAP=off` 스킵 게이트 명문화
  - 무엇을: `### Eager 단계` 섹션 최상단(step 0 또는 사전 게이트)에 "OPAL_BOOTSTRAP=off이면 이하 전 절차 스킵" 규칙 추가
  - 어디에: `opal/core/AGENT.md` §Eager 단계
  - 왜: 문서 정합 — 마커 동작과 AGENT.md 정의가 일치해야 함
  - AC: `opal/core/AGENT.md` §Eager 단계에 `OPAL_BOOTSTRAP` 스킵 게이트 항목이 step 1보다 앞에 존재, `[WORKER]` 스킵과 구분되어 기술됨

- [ ] **F-6** `scripts/windows.ps1` F-1~F-4 동일 적용(미러)
  - 무엇을: install-mac.sh에서 변경된 4종 마커 emit 함수와 동일한 skip 게이트 문구를 windows.ps1 미러 함수에도 적용
  - 어디에: `scripts/windows.ps1` 각 플랫폼 어댑터 emit 함수
  - 왜: `opal/core/.opal/AGENT.md` §플랫폼 독립성 + windows 미러 유지 원칙
  - AC: `scripts/windows.ps1` 플랫폼 어댑터 함수에 skip 게이트 문구 존재

## 제약 조건

- [MUST] `~/.opal/` 직접 편집 금지 — 소스 수정 후 install 재배포 경로만 허용 (→ D-1)
- [MUST] 플랫폼 분기(Claude/Cursor/Gemini/Codex)는 어댑터 계층(`install-mac.sh`/`windows.ps1`)에서만 처리. `opal/core/AGENT.md`에는 행동 규칙으로 명문화만 (→ D-1)
- [MUST] `opal/core/AGENT.md`는 배포본(`~/.opal/AGENT.md`)이 아닌 소스 파일. install 재배포 후 발효 (→ D-1)
- 기존 `[WORKER]` 스킵 메커니즘(디스패치 프롬프트 첫 줄 `[WORKER]`)은 변경하지 않음
- `off` 외 다른 값(미설정/on/기타)은 기존 동작과 동일하게 처리 — 조건 단순성 유지

## 기술 스택

- Bash (shell script) — `scripts/install-mac.sh`, `scripts/windows.ps1`
- Markdown — `opal/core/AGENT.md` (프레임워크 문서)
- 환경변수: `OPAL_BOOTSTRAP` (셸/세션 단위)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | PM 프로필 (AGENT.md) | `.opal/AGENT.md` | 배포 경계·플랫폼 분기 금지사항 SSOT |
| D-2 | 설계 | OPAL AGENT.md (소스) | `opal/core/AGENT.md` | 부트스트랩 Eager 절차 수정 대상 |
| D-3 | 소스 | install-mac.sh | `scripts/install-mac.sh` | 4종 플랫폼 마커 emit SSOT |
| D-4 | 소스 | windows.ps1 | `scripts/windows.ps1` | install-mac.sh 미러 |
| D-5 | 설계 | 공통 하네스 | `opal/core/references/opal-harness.md` | Guards·플랫폼 독립성 원칙 |
