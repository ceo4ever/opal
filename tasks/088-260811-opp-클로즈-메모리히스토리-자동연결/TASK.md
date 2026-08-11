# TASK: CLOSE 완료 시 메모리 히스토리 자동 연결

> 작성일: 2026-08-11 | 작업 유형: 개선 | 적용 스킬: opp | 모드: agentic
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

CLOSE 마지막 행 mark 시점에 작업 히스토리 행이 **도구에 의해 결정론적으로 생성**되도록 하여, 커밋 이후 별도 커밋으로 히스토리를 갱신하던 흐름을 제거한다.

## 배경

현재 작업 히스토리 갱신은 어느 pilot의 CLOSE 스펙에도 하드스텝으로 존재하지 않고, `harness/memory-learning.md` §갱신 트리거의 "태스크 완료" ambient 규칙으로만 걸려 있다. 실행 시점이 PM 재량이라 커밋 뒤로 밀리고, 결과적으로 `chore: 메모리 히스토리 단계 갱신` 형태의 후속 커밋이 매 태스크마다 1건씩 추가로 발생한다.

## 배경 분석 (대화에서 도출)

| # | 확인 사실 | 근거 |
|---|----------|------|
| A-1 | CLOSE 스펙은 DONE.md → 관련 문서 → brain-ingest → 완료 보고 4스텝이며 히스토리 갱신 스텝이 없다 | `opal/skills/opal-pilot-project/SKILL.md:118-147` |
| A-2 | 히스토리 갱신은 ambient 트리거로만 정의되어 강제력이 없다 | `opal/core/references/harness/memory-learning.md:16` |
| A-3 | CLOSE 스펙은 pilot 10종(opp/opd/opd-short/opds/opdw/opsdd/oppd/oppl/opwt/gc)에 각각 복제되어 있다 | 각 SKILL.md `## STEP N: CLOSE` 절 |
| A-4 | state-tool은 매 `advance`/`mark`마다 파이프라인 프론티어(첫 미완료 행)를 파생한다 | `opal/tools/state-tool/state_tool.py:490` `_derive_next_action` |
| A-5 | state-tool은 `build_todo_mirror()` 페이로드를 init/advance/mark/block stdout에 항상 싣는다 (stdout 전용·비영속) | `opal/tools/state-tool/state_tool.py:6` @header 076 항목 |
| A-6 | PostToolUse 릴레이 훅이 그 페이로드를 `hookSpecificOutput.additionalContext`로 세션에 주입한다 | `opal/tools/state-tool/todo_mirror_hook.py:1-20` |
| A-7 | 훅 등록은 install이 소유권 마커 기반으로 멱등 upsert한다 | `scripts/merge-hooks.py:16` `MARKER = "_opal_managed"` |
| A-8 | 히스토리 행 필수 필드는 title·date·stage·path·result이며 date는 KST 자동 채움이다 | `opal/tools/memory-tool/schema/memory.schema.json` §$defs.historyRow / `memory_tool.py:931` |
| A-9 | `append --kind history`는 `--summary`를 `result`에 매핑하며 memory 분기의 80자 캡이 적용되지 않는다 | `opal/tools/memory-tool/memory_tool.py:969-987` |
| A-10 | 히스토리 FIFO=5 집행과 오기재 정정(`update --kind history`)은 memory-tool이 이미 보유한다 | `memory_tool.py:983` `_enforce_history_fifo` / `:999` `_UPDATE_HISTORY_ONLY_ARGS` |

## 확정된 설계 방향 (대화에서 합의)

**3안 — state-tool 직접 호출 + 훅은 보조** (캡틴 확정, 2026-08-11)

| # | 결정 | 근거 |
|---|------|------|
| D-1 | CLOSE 마지막 행 mark 시 state-tool이 `memory-tool append --kind history`를 **직접 호출**한다 | 훅 유무·플랫폼 종류와 무관하게 히스토리 행 생성이 100% 집행된다 |
| D-2 | title·date·stage·path는 도구가 state.json에서 확정적으로 채운다 | 판단이 개입하지 않는 필드이므로 LLM에 위임할 이유가 없다 |
| D-3 | `result`(핵심결과)는 PM이 이어서 `update --kind history`로 보강한다 | 핵심결과는 LLM 판단 산출물이라 도구 단독 생성이 불가능하다 |
| D-4 | 훅·페이로드는 "result를 지금 보강하라"는 리마인더로 역할을 축소한다 | 생성은 도구가 보장하므로 훅은 강제 수단이 아니라 보조 레이어다 |
| D-5 | pilot 10종의 CLOSE 스펙은 수정하지 않는다 | 도구 계층 1지점 변경으로 전 pilot에 동시 적용되며 복제 세금을 피한다 |
| D-6 | 히스토리 기록 시점이 커밋 이전으로 당겨지므로 단계값은 `완료`로 기재한다 | 커밋은 하네스 커밋 규칙상 CLOSE 밖(캡틴 지시)이라 `완료·커밋` 표기를 쓸 수 없다 |

## 명확화 결과

| 요소 | 확정값 | 미확정(있으면) | 의존 사실 |
|------|--------|--------------|----------|
| 목표 | CLOSE 마지막 행 mark 시 state-tool이 memory-tool을 직접 호출해 작업 히스토리 행을 결정론적으로 생성하고, 커밋 후 별도 히스토리 커밋을 제거한다 | - | A-1, A-2 |
| 범위 | **포함**: state-tool 히스토리 연동 로직 + 훅/페이로드 리마인더 + `memory-learning.md` SSOT 절 + 변경이력·@header + install 정합 확인. **제외**: pilot 10종 SKILL.md 수정, memory-tool CLI 신규 서브명령, 커밋 자동화 | - | D-1, D-5, A-3 |
| 제약 | 배포 경계(프로젝트 소스만 수정 후 install) / 훅 없이도 D-1 동작(플랫폼 독립) / state.json 스키마 `additionalProperties:false` 보존 / FIFO·정정은 memory-tool 재사용, state-tool 재구현 금지 / 히스토리 생성 실패가 mark를 실패시키지 않음 | - | A-5, A-8, A-10 |
| 완료기준 | 실 태스크 폴더 mark로 히스토리 행 1건 자동 생성 실증 + 재mark 중복 0건 실증 + memory-tool 실패 주입 시 mark `ok:true` 유지 실증 + 기존 state-tool 테스트 전건 통과 | - | R-1~R-4 |

## 요구사항

- [ ] **R-1 히스토리 자동 생성** — CLOSE 마지막 행 `mark --done` 성공 시 state-tool이 `memory-tool append --kind history`를 호출한다
  - 어디에: `opal/tools/state-tool/state_tool.py` mark 경로
  - 왜: 확정 방향 D-1
  - AC: 미완 태스크 폴더에서 CLOSE 마지막 행을 mark하면 `.opal/MEMORY.json` `history[0]`에 해당 태스크 행이 새로 생기고, `title`·`path`·`stage`가 state.json 값과 일치한다

- [ ] **R-2 필드 자동 충전** — title·stage·path를 state.json에서 파생해 채운다
  - 어디에: R-1과 동일 경로
  - 왜: 확정 방향 D-2, D-6
  - AC: 생성된 행의 `title`은 state.json 태스크 제목, `path`는 `tasks/{폴더}/` 형태, `stage`는 `완료`이며, `date`는 memory-tool이 채운 KST 당일이다

- [ ] **R-3 중복 방지(멱등)** — 동일 태스크에 대해 히스토리 행이 2건 이상 생기지 않는다
  - 어디에: R-1과 동일 경로
  - 왜: mark는 재실행 가능한 명령이므로 반복 호출이 정상 시나리오다
  - AC: 같은 태스크 폴더로 CLOSE 마지막 행 mark를 2회 연속 실행해도 `history` 내 해당 `path` 행이 정확히 1건이다

- [ ] **R-4 실패 비차단** — memory-tool 호출이 실패해도 mark 자체는 성공한다
  - 어디에: R-1과 동일 경로
  - 왜: brain-ingest 훅의 no-op 비차단 패턴 답습 (`opal-pilot-project/SKILL.md:135`)
  - AC: MEMORY.json 부재·memory-tool 비정상 종료를 주입한 상태에서 mark를 실행해도 응답이 `"ok": true`이고, 경고가 응답 필드로 표면화된다

- [ ] **R-5 result 보강 리마인더** — 생성 직후 PM이 `result`를 보강하도록 지시가 전달된다
  - 어디에: state-tool stdout 페이로드 + `todo_mirror_hook.py` 주입 경로
  - 왜: 확정 방향 D-3, D-4
  - AC: CLOSE 마지막 행 mark 응답 stdout에 `update --kind history`로 `result`를 보강하라는 지시 문자열이 포함되고, 훅 미설정 환경에서도 동일 문자열이 stdout에 남는다

- [ ] **R-6 SSOT 문서 반영** — 자동 연결 규약을 하네스 SSOT에 명문화한다
  - 어디에: `opal/core/references/harness/memory-learning.md`
  - 왜: 확정 방향 D-1·D-6을 prose SSOT에 고정해야 PM이 이중 기록하지 않는다
  - AC: 해당 문서에 CLOSE 자동 연결 절이 존재하고, "생성=도구 / result 보강=PM" 역할 분담과 단계값 `완료` 규약이 기재되며, 변경이력 표에 088 행이 추가된다

- [ ] **R-7 배포 정합** — 변경 파일이 install 경유로 `~/.opal/`에 반영된다
  - 어디에: `scripts/install-mac.sh` 배포 대상 확인 + 변경 파일 @header 갱신
  - 왜: 배포 경계 준수 (`.opal/AGENT.md` §금지사항)
  - AC: install 재실행 후 `~/.opal/tools/state-tool/state_tool.py`가 프로젝트 소스와 동일 내용이고, 변경한 코드 파일의 @header `description`에 088 변경 내용이 반영된다

## 제약 조건

- [MUST] `.opal/AGENT.md` §금지사항: "`~/.opal/` 직접 편집 금지 — 항상 프로젝트 소스를 수정한 후 install로 배포한다."
- [MUST] `opal/core/references/opal-harness.md` §1 Guards: "커밋은 사용자가 명시적으로 요청할 때만 수행한다."
- [MUST] `~/.opal/PRINCIPLES.md` §2 Simplicity First: "Solve only the current requirement. No speculative abstraction or unrequested flexibility."
- state.json 스키마는 `additionalProperties: false`이므로 신규 영속 필드 추가 시 스키마 동반 갱신이 필요하다 — 가능하면 076 todo_mirror 선례대로 stdout 전용·비영속으로 처리한다
- 히스토리 FIFO=5 집행·정정 경로는 memory-tool이 이미 소유하므로 state-tool에서 재구현하지 않는다
- pilot SKILL.md 10종은 이번 범위에서 수정하지 않는다 (도구 계층 단일 지점 변경 원칙)

## 기술 스택

- Python 3 (state-tool / memory-tool CLI, 표준 라이브러리 중심)
- Bash (`run.sh` 래퍼, `scripts/install-mac.sh`)
- Markdown (하네스 참조 문서 SSOT)
- JSON Schema (state.schema.json / memory.schema.json)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | state_tool.py | `opal/tools/state-tool/state_tool.py` | mark 경로·프론티어 파생·todo_mirror 페이로드 접합점 |
| D-2 | 소스 | todo_mirror_hook.py | `opal/tools/state-tool/todo_mirror_hook.py` | PostToolUse 릴레이 주입 구조 |
| D-3 | 소스 | memory_tool.py | `opal/tools/memory-tool/memory_tool.py` | history append·update 계약 |
| D-4 | 설계 | memory.schema.json | `opal/tools/memory-tool/schema/memory.schema.json` | historyRow 필수 필드·FIFO 상수 |
| D-5 | 설계 | memory-learning.md | `opal/core/references/harness/memory-learning.md` | 히스토리 규약 SSOT 반영 대상 |
| D-6 | 설계 | opal-harness.md | `opal/core/references/opal-harness.md` | Guards(커밋 규칙)·도구 목록 정합 |
| D-7 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | @header·변경이력·도구 경계 컨벤션 |
| D-8 | 소스 | opal-pilot-project SKILL.md | `opal/skills/opal-pilot-project/SKILL.md` | CLOSE 스펙 현행(비수정 범위 확인용) |
| D-9 | 소스 | merge-hooks.py | `scripts/merge-hooks.py` | 훅 멱등 등록 경로 |
