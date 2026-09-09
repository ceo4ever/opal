---
name: op-dev-plan
description: |
  **구현 계획 수립 단계 스킬**. TASK와 ANALYSIS를 실행 가능한 계약·Work items·위험·릴리즈/복구 계획으로 변환한다.
  반드시 이 스킬을 사용해야 하는 상황: 개발 오케스트레이터가 PLAN 단계를 워커에게 디스패치할 때.
  필수 입력: task_folder, TASK.md. 선택 입력: ANALYSIS.md, PM 주입 프로젝트 문서와 실행 capability. 보장 출력: PLAN.md.
version: 3.2
---

# op-dev-plan — 구현 계획 수립

## 입력 분기

1. TASK 첫 frontmatter가 `template: sdlc-v2`이면 `references/plan-guide.md`를 Read하고 신규 PLAN을 작성한다.
2. legacy TASK에 기존 PLAN이 있으면 재작성하지 않고 기존 산출물을 반환한다.
3. legacy TASK에 PLAN이 없으면 `references/plan-guide.md`의 legacy 절만 적용한다.

## 실행 계약

- TASK의 문제·결과·영향 범위·AC/C와 ANALYSIS의 확인 사실·변경 경계·가정·handoff를 재조사하거나 다른 이름으로 복제하지 않는다.
- PM이 `docs/PROJECT.md` 레지스트리에서 선별해 주입한 프로젝트·기획·설계 문서를 적용한다. 구현으로 내용이 달라질 문서만 Work item의 변경 대상에 포함한다.
- PM이 `## 실행 capability`에 주입한 항목만 실행 방법에 반영한다. 고정 도구·스킬 카탈로그나 추천표를 만들지 않는다.
- PLAN은 `TEST-SCENARIO.md`, `execution-plan.json`, QA 문서, 단계·승인 상태를 생성하지 않는다.

## 완료

가이드의 sdlc-v2 형식으로 PLAN.md를 저장하고 다음 검사를 통과시킨다.

```bash
~/.opal/tools/state-tool/run.sh verify <task-folder> --plan-contract-check
~/.opal/tools/state-tool/run.sh verify <task-folder> --code-scan-citation-check
```

반환:

```text
PLAN 완료: {task_folder}/PLAN.md
실행 그룹: {P1 ... Pn}
착수 차단: {없음 | 항목}
```

## 변경이력

| 버전 | 일시 | 변경내용 |
|---|---|---|
| v1.0 | - | 초기 작성 |
| v2.0 | 2026-04-13 13:48 | 탑다운 기능 중심 구조 전면 개편 (114) |
| v2.7 | 2026-08-24 22:39 | ANALYSIS 승계 원천 2원 규정 추가 (101) |
| v3.0 | 2026-09-09 14:18 KST | 신규 PLAN 작성 계약을 `template: sdlc-v2`와 `Approach/Decisions and contracts/Work items/Risks/Release and recovery`로 단순화. Work items에 실제 agent, 배타적 파일 소유권, 선행 작업, 실행 그룹을 포함해 병렬/순차 실행 순서를 명시하고 legacy 형식은 재개 호환으로 축소 (task 111/W-4) |
| v3.1 | 2026-09-09 14:18 KST | ANALYSIS Change boundary와 docs/PROJECT.md 레지스트리 기준으로 구현 결과 내용이 달라질 문서를 Work items 변경 대상에 포함하되, 참조 전용 문서와 문서 전문 복제는 제외하도록 명시 (task 111/W-4) |
| v3.2 | 2026-09-09 KST | SKILL을 입력 분기·실행 계약·gate 호출로 축소하고 PLAN 형식·작성 규칙은 plan-guide 단일 SSOT로 정리 (111) |
