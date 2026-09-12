---
type: concept
title: opal-pilot-gc — GC 진단 오케스트레이터
tags:
- skill
- pilot
- gc
- security
- convention
sources:
- skill:opal-pilot-gc
- task:120
related:
- gc-finding-schema
- opal-skill-classification-system
- close-retrospective-hardstep
- opal-security-model
- opal-conventions
- opal-project-definition
created: '2026-06-11'
updated: '2026-09-12'
status: active
---
## 개념 요약

커밋 전 보안·컨벤션 진단 오케스트레이터. SCAN → CHECK → REPORT → CLOSE 4단계를 소유하지만 검사 절차 자체는 보유하지 않는 thin wrapper다. 소유하는 것은 검사 범위 확정, 상태 추적, 사용자 Gate, CLOSE 계약이며 소스 파일을 직접 수정하지 않는다 (`opal/skills/opal-pilot-gc/SKILL.md`).

## 배경·문제 (WHY)

원래는 보안 검사와 컨벤션 검사의 절차·기준이 이 Pilot의 수명주기 안에 결합돼 있었다. 그래서 보안 검사만 필요한 다른 파이프라인도 태스크 채번·상태·CLOSE까지 소유하는 Pilot 전체를 시작해야 했다. 검사 기준이 Pilot 참조 문서와 checker 역할 문서 양쪽에 나뉘어 있어 어느 쪽이 원본인지 불명확했고, 한쪽만 갱신되는 표류가 발생했다.

태스크 120에서 검사 역량을 독립 호출 가능한 단계 스킬로 분리했다. 분리의 판단 기준은 "재사용 수요가 있는 것은 절차 소유자를 스킬로 올리고, 수명주기·Gate는 Pilot에 남긴다"이다. Pilot을 없애지 않은 이유는 독립 실행 수명주기·상태 추적·CLOSE 계약 자체가 이 Pilot의 고유 가치이고 기존 사용자의 실행 결과가 달라지면 안 되기 때문이다(TASK C-6).

## 결정 내용 (HOW)

### 소유 경계

- Pilot이 소유: 검사 범위 해석(staged·전체·untracked·특정 커밋·호출자 명시 목록), 이전 실행 비교 대상 탐색, 상태 행과 사용자 Gate, CLOSE(DONE.md·관련 문서 갱신·brain ingest 훅·회고 하드스텝·후속 체인 안내).
- 스킬이 소유: 검사 항목·기준 선택 순서·보고서 구성·fingerprint 산출·판정 트리거. 보안 검사·컨벤션 검사·보고 통합 세 단계 스킬로 이관됐다.
- 에이전트가 소유: 아무 기준도 소유하지 않는다. 두 checker는 지정된 스킬 경로를 읽어 수행하는 role이 됐다(각각 212→69행, 250→87행).

### 회귀 판정을 결정론으로 고정

전환 전후 동작 동일성(AC-2)의 판정 기준을 `references/pipeline.json`의 행 구성 불변 하나로 못박았다 — 한 글자도 바꾸지 않는 것이 계약이고, 상태 도구 테스트가 이 파일을 실제로 읽기 때문에 회귀가 자동 검출된다. 사용자 Gate 문안과 채번 지시 문구도 문자열 존재 여부로 보존을 확인한다. 경량화가 지워서는 안 되는 문구를 유지 목록으로 명시한 이유다.

### 하위 스킬의 대상 재선별 금지

SCAN이 확정한 파일 목록이 검사 대상의 유일 기준이며, 하위 검사 스킬이 git 상태로 대상을 다시 고르는 것을 금지한다. 검사된 파일 집합과 전달된 대상 집합의 일치 여부가 "범위가 몰래 축소되지 않았다"를 관찰하는 유일한 결정론 지표이기 때문이다. 불일치는 부분 실행으로 보고된다.

## 영향·관계

- 검사 규칙 원본은 이제 `opal/core/references/harness/gc-finding-schema.md`와 세 단계 스킬이 소유한다.
- 기존 보고서 파일명을 유지해 PM 리뷰 게이트·프로젝트 루프 등 기존 소비자가 깨지지 않는다.
- 미적용 범위: 자체 PM 연결은 해당 컴포넌트가 실재하지 않아 제외했다.

## 관련 페이지

- [[gc-finding-schema]]
- [[opal-skill-classification-system]]
- [[close-retrospective-hardstep]]
- [[opal-security-model]]
- [[opal-conventions]]
- [[opal-project-definition]]

## 근거 출처

태스크 120 (`task:120`), `opal/skills/opal-pilot-gc/SKILL.md`
