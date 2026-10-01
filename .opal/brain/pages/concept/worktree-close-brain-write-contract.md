---
type: concept
title: 워크트리 CLOSE brain 쓰기 계약 — 같은 브랜치 반영·merge 전파
tags:
- worktree
- brain
- architecture
- workspace
sources:
- task:169
related: [brain-tool, worktree-tool, worktree-task-root-allocator-root-split]
created: '2026-10-01'
updated: '2026-10-01'
status: draft
---
## 개요

워크트리 태스크는 CLOSE 단계에서 문서·brain 지식·산출물을 모두 같은 브랜치에 직접 반영하고, 이후 merge 한 번으로 허브에 들어간다. merge 뒤에 지식을 따로 반영하는 추가 단계는 없다.

## 결정 배경 (WHY)

- CLOSE 파이프라인(op-brain-ingest 디스패치 → 회고 → `worktree-tool finalize`(merge 전 귀속 커밋) → 사용자 merge 안내)은 애초에 "워크트리에서 쓰고 merge 전에 확정"하는 순서로 배선돼 있었다. 이 순서를 막던 유일한 지점은 brain-tool의 쓰기 루트 가드가 명시 인자 없는 워크트리 쓰기를 전면 거부하던 것이었다(근거: task:169 PLAN Approach, (추론: 코드패턴) `opal/tools/brain-tool/brain_tool.py:310` 부근).
- 이전까지는 "워크트리 태스크는 실행 중 brain 파일을 직접 바꾸지 않고, merge 후 허브 finalize가 page를 생성·갱신한다"는 계약이었다(근거: task:169 TASK Problem, done-template.md 구버전 서술). 그런데 그 "merge 후 허브 finalize" 절차 자체가 어디에도 구현돼 있지 않았고, CLOSE에서 디스패치한 op-brain-ingest는 쓰기 루트 가드에 막혀 매번 아무것도 쓰지 못한 채 `skipped`만 반환했다(근거: task:169 TASK Problem — task:163·164·167 모두 동일 현상).
- 이 거부는 `worktree.md`의 task root/allocator root 계약과도 모순됐다 — 그 계약은 이미 `.opal`(brain 포함)을 task_root의 쓰기 대상으로 규정하고 있었다(근거: task:169 PLAN Approach). 이 가드는 memory-tool의 "MEMORY.json은 허브 전용"이라는 패턴을 brain-tool에 과잉 일반화해 생긴 것으로 판단된다(추론: 코드패턴, task:118 설계 이력과의 대조).

## 결정 내용

- **쓰기 루트 반전**: `require_write_root`는 `--allocator-root`를 명시하지 않으면 더 이상 워크트리 여부를 검사하지 않고, 조회와 동일하게 호출 시점의 작업본(task_root, 즉 cwd) 자신에 기본 쓰기가 성공한다. `--allocator-root`를 명시한 경로(다른 루트를 지정할 때 쓰는 기능)는 그대로 유지된다(근거: task:169 PLAN D-1, `opal/tools/brain-tool/brain_tool.py:310-334`). 상세 인터페이스는 [[brain-tool]] 참조.
- **MEMORY.json은 예외 없이 허브 전용 유지**: `.opal/MEMORY.json` 쓰기는 계속 허브(`allocator_root`) 명시 인자로만 수행되고, `memory-tool`의 워크트리 쓰기 거부는 brain-tool과 별도 코드 경로라 이번 반전의 영향을 받지 않는다(근거: task:169 PLAN C-1, 회귀 확인 섹션).
- **finalize의 S⊆D 판정은 그대로 유지**: `worktree-tool finalize`는 DONE.md `## 회고적 학습 후보` 절의 선언 집합(D)과 실제 미커밋 brain·MEMORY 변경 집합(S)을 대조해 S⊆D일 때만 merge 전 단일 귀속 커밋으로 확정한다. 선언에 없는 brain 경로를 건드리면 여전히 차단된다. op-brain-ingest가 반환한 `ingested_pages`는 호출 전에 DONE.md 선언과 대조해 누락분을 보정한다(근거: task:169 PLAN D-8, `opal/core/references/harness/done-template.md` §회고적 학습 후보 계약). 상세는 [[worktree-tool]] 참조.
- **공유 파일(log.md·index.md)은 merge=union**: `.gitattributes`에 `.opal/brain/log.md`·`.opal/brain/index.md` 2줄을 `merge=union`으로 등록해, 두 브랜치가 각각 추가한 로그·색인 항목이 merge에서 서로 지워지지 않고 합쳐지게 한다(근거: task:169 PLAN D-4). `index.md`는 어차피 merge 후 `brain-tool index` 1회 재실행으로 전체 page 목록과 재일치시키므로 union 병합 결과의 정확성 자체에 의존하지 않는다(근거: task:169 PLAN D-9).
- **같은 page 동시 수정은 git 기본 merge로 폴백**: page 파일(`pages/**/*.md`)에는 `merge=union`을 적용하지 않는다. 구조적 frontmatter(YAML)를 가진 문서에 union을 적용하면 두 버전의 서로 다른 값이 한 파일에 섞여 YAML이 깨질 위험이 있기 때문이다 — log.md(순수 append)·index.md(전량 재생성)와 성격이 다르다(근거: task:169 PLAN D-13). 두 브랜치가 같은 page의 같은 구간을 다르게 고치면 git이 표준 conflict marker를 남기며, 이는 지식 손실이 아니라 정상적인 git 동작이다(근거: task:169 PLAN H-4·D-13 실측 — iteration 4에서 두 브랜치가 우연히 같은 값으로 수렴하면 충돌 없이 자동 병합됨도 확인).
- **같은 page 충돌 해결 절차**: merge가 `.opal/brain/**`에서 conflict marker를 남기면 (1) 충돌 파일을 열어 사람이 양쪽 내용을 판단해 하나로 합친다(frontmatter가 있으면 중복 키 없이 유효한 YAML이 되도록 정리) (2) `brain-tool validate --brain-path <허브 절대경로>`(또는 `lint --brain-path <허브 절대경로>`) — 두 서브커맨드 모두 위치 인자가 아니라 `--brain-path`만 받는다 — 로 brain 전체 정합성을 확인한다 (3) `index.md`가 영향받았으면 `brain-tool index`를 재실행한다 (4) 검증 통과 후 커밋해 merge를 완료한다(근거: task:169 PLAN D-15).

## 영향 범위

- [[brain-tool]] — `require_write_root`의 기본값 반전(이 페이지의 핵심 집행 지점).
- [[worktree-tool]] — `finalize`가 "merge 전 귀속 커밋 확정"이라는 원래 의미대로 문서가 정정됨(이전 문서에 "merge 후 귀속 후처리 확정"류 오기가 남아 있었다).
- [[worktree-task-root-allocator-root-split]] — 이 페이지의 WHY 섹션이 "브레인 도구도 명시 인자 없는 쓰기를 전용 오류로 막는다"고 서술했던 부분이 이번 반전으로 더 이상 사실이 아니게 되어 정정이 필요하다.
- `op-brain-ingest`·`opal-pilot-dev` CLOSE 절차는 로직 변경 없이 이 계약을 명문화하는 문구만 추가됐다 — 워크트리·허브 구분 없이 동일한 STEP1~STEP6이 적용되고, 기본 쓰기는 호출 시점의 작업본 자신에 성공한다(근거: task:169 PLAN D-7, D-10).

## 관련 페이지

- [[brain-tool]]
- [[worktree-tool]]
- [[worktree-task-root-allocator-root-split]]
