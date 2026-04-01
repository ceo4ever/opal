# TASK: 워커 에이전트 프로젝트 컨텍스트 자율 로딩

> 작성일: 2026-03-30 | 작업 유형: 개선
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

opal-task-agent가 스킬 실행 전에 `docs/` 문서를 자율적으로 읽어 프로젝트 컨텍스트를 확보하도록 개선한다. PM 주입에 의존하지 않고 워커가 자기완결적으로 동작하게 만든다.

## 배경

현재 워커(opal-task-agent)는 오케스트레이터가 전달한 스킬/산출물만 읽고 작업한다. 프로젝트의 구조, 아키텍처, 컨벤션 등은 PM이 디스패치 시 명시적으로 전달해야만 워커가 인지할 수 있다. PM이 빠뜨리면 워커가 프로젝트 구조를 모른 채 작업하여 잘못된 경로에 파일을 생성하거나 컨벤션을 위반하는 문제가 발생한다.

`docs/`는 프로젝트의 설계도 역할을 한다. 어떤 프로젝트든 `docs/PROJECT.md`, `docs/ARCHITECTURE.md` 등이 프로젝트의 구조와 규칙을 담고 있으므로, 워커가 이를 자율적으로 읽으면 PM 디스패치 품질에 의존하지 않고도 정확한 작업이 가능하다.

## 요구사항

- [ ] opal-task-agent의 실행 프로세스에 "프로젝트 컨텍스트 로드" 단계를 추가한다
- [ ] opal-task-qa-agent의 실행 프로세스에 "프로젝트 컨텍스트 로드" 단계를 추가한다
- [ ] op-dev-test-agent의 실행 프로세스에 "프로젝트 컨텍스트 로드" 단계를 추가한다
- [ ] 워커가 수행하는 스킬 유형에 따라 읽어야 할 docs/ 문서를 자동 판단한다
- [ ] `docs/PROJECT.md`는 모든 스킬에서 필수로 읽는다 (존재 시)
- [ ] `docs/ARCHITECTURE.md`, `docs/CONVENTIONS.md`는 코드 관련 스킬(op-dev-*) 실행 시 읽는다
- [ ] `docs/BACKEND.md`, `docs/FRONTEND.md`는 해당 도메인 작업 시 읽는다
- [ ] docs/ 문서가 없는 프로젝트에서도 기존대로 정상 동작한다 (하위 호환)

## 제약 조건

- 에이전트 AGENT.md 3개 파일만 수정한다 (개별 스킬 SKILL.md는 변경하지 않음)
- 기존 실행 프로세스의 순서를 깨뜨리지 않는다
- 컨텍스트 로딩은 docs/ 문서가 존재할 때만 수행하며, 없으면 스킵한다

## 기술 스택

- Markdown (AGENT.md 문서 수정)

## 관련 문서

- `agents/opal-task-agent/AGENT.md` — 수정 대상 (범용 워커)
- `agents/opal-task-qa-agent/AGENT.md` — 수정 대상 (QA 워커)
- `agents/op-dev-test-agent/AGENT.md` — 수정 대상 (테스트 워커)
- `docs/PROJECT.md` — 프로젝트 문서 허브 (프로젝트 문서 테이블 포함)
- `~/.opal/references/opal-harness.md` — 오케스트레이터 공통 인프라
