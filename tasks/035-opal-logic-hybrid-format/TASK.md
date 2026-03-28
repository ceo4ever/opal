# TASK: opal-logic 하이브리드 포맷 PoC

> 작성일: 2026-03-28 | 작업 유형: 신규
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

복잡한 OPAL 스킬의 분기 로직을 구조화된 YAML 블록(`opal-logic`)으로 보강하여, LLM이 추론 대신 구조화된 데이터를 직접 참조할 수 있게 한다.

## 배경

현재 OPAL 스킬의 분기 로직(조건부 파일 로드, 다중 기준 판정, 입력 우선순위, 상태 전이, 디스패치 규칙)이 순수 마크다운 테이블/문장으로만 서술되어 있다. LLM이 매번 자연어를 추론으로 해석해야 하므로 정확도와 일관성이 떨어질 수 있다.

이미 `execution-plan.json`, `test-tools.yaml` 등 구조화 포맷이 부분적으로 사용되고 있으나, 스킬 프로세스 내 분기 로직은 아직 마크다운에 의존한다.

## 요구사항

- [ ] opal-logic 스키마 정의 문서 생성 (6가지 type: conditional-load, decision-matrix, input-priority, state-machine, dispatch-map, dag)
- [ ] dtp-todo SKILL.md에 decision-matrix 블록 추가 (복잡도 판별 5기준 OR)
- [ ] otp-dev SKILL.md에 state-machine + dispatch-map 블록 추가 (파이프라인 전이 + 단계별 디스패치)
- [ ] dtp-qa SKILL.md에 conditional-load + decision-matrix 블록 추가 (가이드 선택 + QA 판정)
- [ ] otp-dev-short SKILL.md에 decision-matrix 블록 추가 (에스컬레이션 판정)
- [ ] AGENT.md에 opal-logic 해석 메타 지시 추가
- [ ] 기존 서술형 마크다운은 제거하지 않음 (하위 호환)

## 제약 조건

- 기존 SKILL.md의 마크다운 서술을 제거하지 않는다 (YAML 블록은 보충)
- opal-logic 블록이 없는 스킬은 영향받지 않아야 한다
- MCP 파서 도구는 이번 범위에 포함하지 않는다 (별도 태스크)
- YAML 블록은 마크다운 코드 블록 내에 배치한다

## 기술 스택

- Markdown (SKILL.md)
- YAML (opal-logic 블록)
- 프레임워크 자체 스킬 수정 (코드 없음, 문서 기반)

## 관련 문서

- 계획 파일: `~/.claude/plans/splendid-inventing-quokka.md`
- dtp-todo: `skills/dtp-todo/SKILL.md`
- otp-dev: `skills/otp-dev/SKILL.md`
- dtp-qa: `skills/dtp-qa/SKILL.md`
- otp-dev-short: `skills/otp-dev-short/SKILL.md`
- AGENT.md: `opal/core/AGENT.md`
