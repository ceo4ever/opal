---
type: entity
title: skill-registry 프로젝트 스코프 4소스 병합
module: <code-scan @header module>
layer: <code-scan @header layer>
domain: <code-scan @header domain>
exports: []
source_ref: '<코드 파일 경로 — 예: opal/tools/state-tool/state_tool.py>'
header_synced: <YYYY-MM-DD>
tags:
- tool
- skill-registry
- project-scope
- task-114
sources:
- task:114
related:
- opal-skill-wizard
- additive-field-extension-over-schema-replacement
- exploration-marker-as-output-artifact-creates-circularity
- community-skill-installation-architecture
created: '2026-09-09'
updated: '2026-09-09'
status: draft
---
## 개요

`skill-registry.js`의 스킬 병합 로직은 기존 전역 3소스(main/community/user)에 프로젝트 스코프를 4번째 소스로 additive 병합하도록 확장됐다. 이로써 `opal-skill-wizard`가 프로젝트 스코프에 설치한 스킬이 `//` 커맨드 발동 경로에 자연스럽게 편입된다.

## 책임 (WHAT)

- **4소스 병합 순서**: `main → community → user → project` (`opal/tools/skill-registry/skill-registry.js:129-147` 인접 확장). 나중에 병합되는 소스가 동일 `name`에서 우선하는 기존 override 규칙의 자연 연장으로, 프로젝트 스코프가 자동으로 최우선이 된다.
- **`_source` 마커**: 병합된 각 스킬 항목에 출처 소스(`main`/`community`/`user`/`project`)를 부착해 이후 분기(설치 판정, `match`/`get`/`list` 응답 분화)의 유일한 판별축으로 쓴다.
- **프로젝트 루트 판별**: `process.cwd()`부터 부모 방향으로 `.opal/` 디렉토리를 찾는 walk-up 탐색. 홈 디렉토리 경계·파일시스템 루트·상한 32단에서 정지한다.
- **경로 필드 확장**: `get` 서브커맨드에 additive 필드 `resolved_path`를 추가해 기존 raw passthrough 필드는 그대로 보존한다.

## 설계 배경 (WHY)

- **project 스킬은 `paths`를 갖지 않는다** (근거: task:114 DONE.md §7) — main 스킬과 달리 프로젝트 스킬 항목에는 정적 `paths` 배열이 없고 경로는 `resolveProjectSkillPath()`로 동적 계산된다. 이 때문에 `matchCommand()`·`validate()`에 project 전용 분기가 필수이며, 분기를 지우면 스키마 준수 registry도 오류를 낸다.
- **walk-up 채택 근거** (근거: task:114 PLAN.md DEC-1) — 명시적 인자 주입·환경변수 대비, 호출부(`match`/`get`/`list`/`validate` 4개 CLI 진입점, `skill-commands.md` 라우팅, `dashboard/backend/adapters/skill_adapter.py:47`)를 한 곳도 고치지 않는 배선 비용 0의 이점이 선택 근거였다. 이 탐색 마커의 순환 위험은 [[exploration-marker-as-output-artifact-creates-circularity]]에서 별도로 다룬다.
- **override 순서 채택 근거** (근거: task:114 PLAN.md DEC-3) — 별도 우선순위 테이블을 신설하지 않고 현행 override 방향("나중에 병합되는 소스가 우선")을 그대로 연장했다. 프로젝트 스코프는 사용자가 그 프로젝트에 한정해 의도적으로 설치한 것이므로, 전역보다 좁고 명시적인 의도를 우선하는 것이 기존 규칙과 의미상 일치한다.
- **`resolved_path` additive 채택 근거** (근거: task:114 PLAN.md DEC-5) — 기존 `getCommand()`의 raw passthrough 반환(`paths` 배열 등)을 한 필드도 제거·변경하지 않고 새 필드만 추가해, 하위호환을 깨지 않으면서 상위집합으로 확장했다. 이 패턴은 [[additive-field-extension-over-schema-replacement]]가 이미 다룬 일반 원칙의 재적용 사례다.

## 관계 (HOW)

- [[opal-skill-wizard]] — 이 병합 확장의 유일한 신규 소비자. wizard가 설치한 스킬이 이 확장을 통해 `//` 커맨드로 발동한다.
- [[additive-field-extension-over-schema-replacement]] — `resolved_path` 필드 추가가 따른 일반 원칙.
- [[exploration-marker-as-output-artifact-creates-circularity]] — walk-up 마커 선택이 회피한 순환 위험.
- [[community-skill-installation-architecture]] — 전역 스코프 설치 레이아웃(vendor 중첩)과는 별개의 프로젝트 스코프 레이아웃(`.opal/community-skills/{vendor}/{skill}/`)이 이를 동형으로 이식했다.

## 소스 커버리지

| 식별자 | 경로:줄번호 | 설명 |
|--------|-----------|------|
| `loadAllSkills()` | `opal/tools/skill-registry/skill-registry.js:129-147` | 4소스 병합 지점 |
| `matchCommand()` | `opal/tools/skill-registry/skill-registry.js:255-323` | `_source==='project'` 분기 추가 |
| `getCommand()` | `opal/tools/skill-registry/skill-registry.js:327-340` | `resolved_path` additive 필드 |
| `resolveProjectSkillPath()` | `opal/tools/skill-registry/skill-registry.js`(신규) | 프로젝트 스킬 경로 동적 계산 |
| `findProjectRoot()` | `opal/tools/skill-registry/skill-registry.js`(신규) | walk-up 루트 판별, 홈 경계 정지 |
