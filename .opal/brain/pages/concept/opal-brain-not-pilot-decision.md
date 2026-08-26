---
type: concept
title: opal-brain은 pilot이 아니다 — 리네임 철회 결정
tags:
- opal-brain
- skill-naming
- pilot
- operator
- architecture
sources:
- task:029
related:
- skill-opal-brain
- opal-architecture
- skill-registry-validate-extension
created: '2026-06-18'
updated: '2026-06-18'
status: active
---
## 개념 요약

`opal-brain`에 `opal-pilot-*` 접두사를 붙이려 했으나, 실제 SKILL.md 검증으로 opal-brain이 pilot이 아님이 확인되어 리네임이 철회됐다. 오분류는 `docs/PROJECT.md`의 "오케스트레이터/Pilot" 표기 교정으로만 해소했다.

## 배경·문제 (WHY)

초기 TASK 명세에서 `opal-brain`을 "4모드 오케스트레이터"로 보고 `opal-pilot-brain` 리네임 + alias `opbr→opb` + 전역 9파일 cascade를 계획했다. PLAN 게이트에서 캡틴이 "pilot은 단계 파이프라인 분해 + 워커 지휘 오케스트레이터에 붙는 접두사인데 opal-brain도 그런가?"를 제기했다.

`opal/skills/opal-brain/SKILL.md` 실증 검증 결과:

- **독립 4모드 라우터** — `init|ingest|query|lint`는 순차 단계 파이프라인이 아니라 모드 라우팅 분기 (`SKILL.md:28-43` 모드 라우팅 표)
- **워커 디스패치 0건** — `brain-tool`(결정론적 CLI) 직접 호출 + LLM 페이지 작성뿐 (`SKILL.md:24`)
- **STATE·Gate·단계 전환 없음** — `SKILL.md:21`의 "단일 pilot 구조"는 "오케스트레이터+단계스킬로 미분할한 단일 스킬"의 느슨한 표기이지 orchestrator를 뜻하지 않는다

## 결정 내용 (HOW)

**opal-brain은 operator 스킬**이다 — 직접 실행 multi-mode 라우터이며, onboarding/start/project-init/skill-creator와 동일 부류(`opal` 그룹 잔류).

- 폴더명 `opal-brain`, alias `opbr`, triggers, 레지스트리 entry, 전역 참조: **전부 불변**
- 변경 대상: `docs/PROJECT.md` opal-brain 행의 "유형: 오케스트레이터 / 설명: 브레인 4모드 Pilot" 오기재만 교정
- 리네임 cascade(9파일) 소멸 → 4파일 수정으로 태스크 축소

**`opal-pilot-*` 접두사 기준 (이 결정에서 확정)**:  
단계 파이프라인 분해 + 워커 지휘 오케스트레이터에만 붙는다.  
예: `opal-pilot-dev`, `opal-pilot-sdd`, `opal-pilot-gc` — 여러 단계 스킬을 순차·병렬 디스패치하고 STATE/Gate를 관리.

**operator 스킬** (`opal` 그룹, `opal-pilot-*` 아님):  
`opal-brain`, `opal-onboarding`, `opal-start`, `opal-project-init`, `opal-skill-creator`, `opal-agent-creator`, `opal-skill-manager` — 단일 스킬이 직접 실행, 워커 디스패치 없음.

## 영향·관계

- `docs/PROJECT.md` — opal-brain 유형 표기 교정 (`오케스트레이터/Pilot` → `operator (멀티모드)`)
- `opal/core/references/opal-skills-registry.json` — opal-brain은 `opal` 그룹 잔류 (변경 없음)
- 리네임 종속 리스크(H-1·H-2·H-7) 전부 소멸; 불변 회귀 가드(H-8)로 대체

## 근거 출처

태스크 029 (`task:029`), `opal/skills/opal-brain/SKILL.md:14,21,24,28-43`

## 관련 페이지

- [[skill-opal-brain]]
- [[opal-architecture]]
- [[skill-registry-validate-extension]]
