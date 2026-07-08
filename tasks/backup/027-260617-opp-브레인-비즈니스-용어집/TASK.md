# TASK: OPAL Brain 프로젝트별 비즈니스 용어집 관리 체계

> 작성일: 2026-06-17 | 작업 유형: 개선 | 적용 스킬: opp | 모드: agentic
> 입력: 사용자 요청
> 출력: TASK.md, PLAN.md, 변경 파일, DONE.md

## 작업 목표

OPAL Brain이 기획 산출물, 설계 문서, 소스 코드에서 등록한 지식을 답변 시 프로젝트별 비즈니스 용어로 종합 설명하도록, 프로젝트별 비즈니스 용어집(glossary) 관리 체계를 설계하고 반영한다.

## 배경

현재 OPAL Brain은 code-scan, source_ref, task/doc ingest를 통해 프로젝트 지식을 축적하지만, 답변의 주어가 코드 식별자·API·enum에 치우치면 PM·운영자·기획자가 이해하기 어렵다. 캡틴은 Brain 답변이 저장 원천과 무관하게 업무 언어로 재구성되기를 원하며, 이를 위해 프로젝트마다 고유한 비즈니스 용어가 지식 자산으로 관리되어야 한다고 판단했다.

## 배경 분석 (대화에서 도출)

- 5W1H는 페이지 양식이 아니라 사고의 틀이다. 페이지에 별도 "5W1H 블록"을 템플릿으로 삽입하지 않는다.
- Brain 본문과 질의 답변의 주어는 업무 개념이어야 한다. 코드 식별자, API, enum, 레포명은 본문 주어가 아니라 근거 인용 또는 개발자용 부록에 위치한다.
- 근거는 코드 단층 인용이 아니라 코드(SSOT), 정책서(POL-xxx), IA(`ia:{system}:{screen}`), 설계 문서 등 다층 인용으로 병기해야 한다.
- 프로젝트별 표준 용어가 없으면 Brain이 같은 개념을 서로 다른 표현으로 설명할 수 있으므로, 비즈니스 용어집을 Brain의 장기 지식 자산으로 관리해야 한다.

## 확정된 설계 방향 (대화에서 합의)

- Brain은 "소스/설계/정책을 검색하는 위키"를 넘어, 여러 원천을 종합해 업무 맥락으로 답변하는 지식 번역 계층이어야 한다.
- 프로젝트별 비즈니스 용어는 단순 번역 사전이 아니라 표준명, 별칭, 업무 의미, 행위자, 업무 표면, 정책/IA/코드 근거, 관련 용어를 담는 지식 자산이어야 한다.
- `term` 타입 도입은 설계 후보로 검토하되, 과설계를 피하기 위해 기존 SCHEMA 동적 타입 구조와 호환되는 방식으로 반영한다.

## 명확화 결과

> TASK 4요소를 잠근다. 각 요소는 확정값 또는 명시적 "N/A: <사유>"로 채운다 (공란·TBD 금지).

| 요소 | 확정값 | 미확정(있으면) | 의존 사실 |
|------|--------|--------------|----------|
| 목표 | OPAL Brain에 프로젝트별 비즈니스 용어집 관리 체계를 설계·반영하여, ingest/query가 표준 업무 용어와 다층 근거를 우선 사용하도록 한다. | - | 기존 brain은 SCHEMA 동적 페이지 타입과 source_ref 기반 ingest/query 구조를 가진다. |
| 범위 | 포함: citation-rules, brain SCHEMA/template, opal-brain skill, op-brain-ingest skill, 관련 brain 지식 페이지. 제외: 대규모 검색 알고리즘/DB/임베딩 구현, 기존 프로젝트별 용어 대량 백필. | - | 소스 수정은 프로젝트 소스(`opal/`, `.opal/brain/`)에 한정하고 `~/.opal/` 배포본은 직접 수정하지 않는다. |
| 제약 | 본문은 업무 언어 우선, 코드는 근거로 강등, 5W1H는 사고 프레임으로만 사용, `소스 커버리지` 등 개발자 부록은 유지. 변경이력 필수 문서에는 KST 일시와 태스크 번호를 기록한다. | - | `.opal/AGENT.md` 금지사항과 `citation-rules.md` §8 기존 원칙을 확장한다. |
| 완료기준 | 관련 문서에 glossary/term 관리, business-first query, 다층 근거, 업무 표면 규칙이 반영되어 있고, `brain-tool` 검증 또는 관련 정적 검증이 통과한다. | - | CLOSE 진입 전 캡틴 승인 필요. |

## 요구사항

- [ ] `citation-rules.md` §8을 확장하여 Brain 페이지/답변의 business-first 원칙, 5W1H 사고 프레임, 업무 표면 명명, 다층 근거, 개발자 부록 분리 기준을 명시한다.
- [ ] Brain SCHEMA 및 template에 프로젝트별 용어집 관리 체계를 추가한다. 표준 용어, 별칭, 행위자, 업무 표면, 정책/IA/코드 근거, 관련 용어를 관리할 수 있어야 한다.
- [ ] `opal-brain/SKILL.md` ingest/query 규칙에 용어 정규화 우선 흐름을 반영한다. query는 관련 glossary/term 검색 후 업무 언어 답변을 생성해야 한다.
- [ ] `op-brain-ingest/SKILL.md` CLOSE ingest 규칙에 새 업무 용어·상태·업무 표면 후보 추출과 사용자/PM 확정 전 draft 처리 기준을 추가한다.
- [ ] 기존 Brain에 이번 결정을 설명하는 concept 또는 glossary 관련 페이지를 등록하여 이후 질의에서 재사용할 수 있게 한다.
- [ ] 변경된 문서의 변경이력에 태스크 027 행을 추가한다.
- [ ] 검증 명령을 실행해 문서/스키마/brain 무결성에 치명 오류가 없는지 확인한다.

## 제약 조건

- `~/.opal/` 배포 파일은 직접 수정하지 않는다. 프로젝트 소스(`opal/`, `skills/`, `scripts/`, `.opal/brain/`)만 수정한다.
- 코드 식별자, enum, API path, 레포명은 Brain 본문 주어로 쓰지 않고 근거/부록에 둔다.
- 5W1H는 체크 기준이며 페이지 섹션 템플릿으로 강제하지 않는다.
- 기존 source_ref, code-scan, ingest-scan 멱등 규칙을 깨지 않는다.
- 커밋은 수행하지 않는다.

## 기술 스택

- Markdown, YAML frontmatter
- Python `brain-tool`
- Bash/Node 기반 OPAL 도구 체계

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | OPAL PM 프로필 | `.opal/AGENT.md` | 프로젝트 금지사항, 변경이력, 비즈니스 용어 우선 확정 기준 |
| D-2 | 설계 | PROJECT.md | `docs/PROJECT.md` | 프로젝트 구조, Brain 컴포넌트 위치, 문서 레지스트리 |
| D-3 | 설계 | citation-rules.md | `opal/core/references/harness/citation-rules.md` | 비즈니스 용어 우선 원칙 SSOT |
| D-4 | 설계 | OPAL Brain SKILL | `opal/skills/opal-brain/SKILL.md` | Brain init/ingest/query/lint 동작 규칙 |
| D-5 | 설계 | op-brain-ingest SKILL | `opal/skills/op-brain-ingest/SKILL.md` | CLOSE ingest 규칙 |
| D-6 | 설계 | Brain schema template | `opal/tools/brain-tool/templates/schema-template.md` | Brain SCHEMA 생성 원본 |
| D-7 | 지식 | Business terminology principle | `.opal/brain/pages/concept/business-terminology-first-principle.md` | 기존 brain 내 비즈니스 용어 우선 결정 |
