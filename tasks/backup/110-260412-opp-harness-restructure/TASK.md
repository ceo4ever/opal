# TASK: opal-harness.md 구조화 리팩토링

> 작성일: 2026-04-12 | 작업 유형: 개선 | 적용 스킬: opp | 모드: interactive
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

`opal/core/references/opal-harness.md`의 비대한 구조를 정리하여, 중복 제거 · 도메인 특화 내용 분리 · 레거시 정리를 수행한다.

## 배경

opal-harness.md는 오케스트레이터 공통 인프라를 정의하는 핵심 레퍼런스다. 109개 태스크를 거치며 지속적으로 내용이 추가되어 현재 ~751줄 / 16,487 토큰으로, Read 도구 한계(10,000 토큰)를 초과한다. 세션 시작 시 Eager 로드되는 파일이므로 크기가 곧 컨텍스트 비용이다.

## 배경 분석 (대화에서 도출)

### 현재 구조 (§ 번호 — 줄 수 추정)

| § | 섹션 | 줄 수 | 비고 |
|---|------|------|------|
| 0 | 용어 정의 | ~20 | 적정 |
| 1 | Guards | ~45 | 적정 |
| 2 | 모듈 구조 | ~70 | QA 체크리스트 검증 + 산출물 표준 파일명 포함 |
| 3 | State | ~250 | **비대** — 7개 이상 서브 관심사 혼재 |
| 4 | TASK 공통 프로세스 | ~45 | 적정 |
| 5 | Observability | ~55 | 적정 |
| 6 | Model Mapping | ~10 | 적정 |
| 7 | 병렬 처리 원칙 | ~80 | 적정 |
| 8 | EXECUTE @header 규칙 | ~66 | 최근 추가, code-scan 가이드 포함 |
| 9 | OPAL Tools | ~30 | 적정 |

### 식별된 문제

1. **§3 State 비대화** — STATE.md 구조/템플릿, 파이프라인 현황판 행 규칙, opsdd 예시(40줄), ADD_DONE 템플릿, 추가작업 프로세스, 병렬 실행 State(55줄, oppd 전용), 세션 복원, State Gate가 전부 한 섹션에 혼재
2. **도메인 특화 내용이 공통 하네스에 침투** — opsdd 파이프라인 현황판 예시, 병렬 실행 State(oppd 전용)
3. **State Gate 자가 점검 프롬프트가 레거시 값 참조** — `QA Gate 대기` / `PM Gate 대기` / `사용자 확인 대기` 등 deprecated 상태값이 line 403에 존재
4. **수행 순서 강제 원칙 중복** — §3 (line 168)과 opal-harness-interactive.md §4 (line 121-127)에 동일 내용
5. **변경이력 23개 항목** — 길지만 삭제보다는 유지 (히스토리 가치)

## 요구사항

- [x] R-1: §3 State에서 opsdd 파이프라인 현황판 예시(lines 233-273)를 제거하고, 해당 내용이 opsdd SKILL.md에 이미 존재하는지 확인 후, 없으면 이관한다
  - **무엇을**: opsdd 전용 43행 파이프라인 현황판 예시 제거
  - **어디에**: `opal/core/references/opal-harness.md` §3
  - **왜**: 도메인 특화 내용은 해당 스킬 SKILL.md에 위치해야 한다
  - **AC**: opal-harness.md에 opsdd 파이프라인 예시가 없고, opsdd SKILL.md에 동일 정보가 존재한다

- [x] R-2: §3 State에서 병렬 실행 State(lines 330-386)를 제거하고, oppd SKILL.md에 이관한다
  - **무엇을**: oppd 전용 병렬 실행 State (그룹 요약/태스크 상세/머지 이력/검증 루프 로그 테이블)
  - **어디에**: `opal/core/references/opal-harness.md` §3 → `opal/skills/opal-pilot-project-dev/SKILL.md`
  - **왜**: oppd 전용 상태 확장은 공통 하네스가 아닌 해당 오케스트레이터에 위치해야 한다
  - **AC**: opal-harness.md에 병렬 실행 State가 없고, oppd SKILL.md에 동일 정보가 존재한다

- [x] R-3: State Gate 자가 점검 프롬프트(line 403)에서 deprecated 상태값(`QA Gate 대기`, `PM Gate 대기`, `사용자 확인 대기`)을 파이프라인 현황판 기반으로 갱신한다
  - **무엇을**: 레거시 상태값을 현행 파이프라인 현황판 행 기반 확인으로 교체
  - **어디에**: `opal/core/references/opal-harness.md` §3 State Gate
  - **왜**: §3 line 178에서 deprecated 선언한 값이 같은 §3 내에서 아직 사용 중
  - **AC**: State Gate 자가 점검 프롬프트에 deprecated 상태값이 없고, 파이프라인 현황판 행 상태 확인 방식으로 서술되어 있다

- [x] R-4: 수행 순서 강제 원칙 중복 제거 — opal-harness.md §3에 정의를 유지하고, opal-harness-interactive.md §4에서는 §3 참조로 교체한다
  - **무엇을**: interactive 서브 하네스의 중복 서술을 참조로 교체
  - **어디에**: `opal/core/references/opal-harness-interactive.md` §4
  - **왜**: 동일 원칙이 두 곳에 있으면 하나만 수정 시 불일치 발생
  - **AC**: opal-harness-interactive.md §4에서 수행 순서 강제 원칙을 직접 서술하지 않고, 공통 하네스 §3을 참조한다

- [x] R-5: 변경이력에 이번 리팩토링을 기록한다
  - **무엇을**: 변경이력 행 추가
  - **어디에**: `opal/core/references/opal-harness.md` 변경이력, `opal/core/references/opal-harness-interactive.md` 변경이력
  - **왜**: 변경 추적
  - **AC**: 변경이력에 110번 태스크 내용이 기록되어 있다

## 제약 조건

- 배포본(`~/.opal/`) 직접 수정 금지 — 소스(`opal/core/references/`)에서만 수정
- 기존 오케스트레이터(opp/opds/opd/opwt/opsdd/oppd)의 동작에 영향을 주지 않아야 한다
- 이관 시 의미 손실 없이 동일 내용을 유지한다
- 하네스 §번호가 변경되면, 다른 문서에서 해당 §번호를 참조하는 곳도 확인한다

## 기술 스택

- Markdown 문서

## 관련 문서

- `opal/core/references/opal-harness.md` — 변경 대상 (공통 하네스)
- `opal/core/references/opal-harness-interactive.md` — 변경 대상 (서브 하네스)
- `opal/skills/opal-pilot-sdd/SKILL.md` — R-1 이관 대상 확인
- `opal/skills/opal-pilot-project-dev/SKILL.md` — R-2 이관 대상
- `.opal/AGENT.md` — PM 검토 기준
- `docs/PROJECT.md` — 프로젝트 원칙
