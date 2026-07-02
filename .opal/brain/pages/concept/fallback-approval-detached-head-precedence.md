---
type: concept
title: detached HEAD 판정은 no-upstream보다 먼저 검사해야 한다
tags:
- git
- judgment-order
- fallback-approval
- lesson
sources:
- task:052
related:
- git-sync-tool
created: '2026-07-02'
updated: '2026-07-02'
status: active
---
## 개념 요약

[[git-sync-tool]]이 저장소 상태를 dirty/diverged/detached/no-upstream/fetch-failed 5종으로 분류할 때, detached HEAD 여부는 upstream 존재 여부보다 먼저 판정해야 정확하게 분류된다.

## 배경·문제 (WHY)

원래 설계는 no-upstream을 detached보다 먼저 검사하는 순서였다 (근거: task:052 PLAN§3.1.2(d)). 그런데 실제 git 동작을 검증하는 과정에서, detached HEAD 상태의 저장소에 대해 upstream 조회 명령을 실행하면 exit code 128의 fatal 오류로 실패한다는 사실이 드러났다 (근거: task:052 AGENTIC-LOG #6). 이 오류는 "upstream이 설정되지 않은 경우"의 실패와 동일한 형태로 나타나기 때문에, 원래 순서대로 검사하면 detached 저장소가 no-upstream으로 오분류된다.

## 결정 내용 (HOW)

detached 판정을 no-upstream보다 선행하도록 순서를 교정했다 — 먼저 브랜치명이 detached 상태를 가리키는지 확인하고, detached가 아닐 때만 upstream 존재 여부를 검사한다. 이 교정은 EXECUTE 단계에서 담당 에이전트가 발견해 헌법상 폴백 승인 절차(agentic 모드에서 더 나은 방식 발견 시 PM 사후 승인)를 거쳐 반영되었다 (근거: task:052 AGENTIC-LOG #7). 기존 RED 테스트 계약(detached 케이스가 detached로 분류되어야 한다는 기대)은 그대로 유지되었고, 판정 정확도만 개선되었다.

## 영향·관계

- [[git-sync-tool]]의 저장소 판정 순서: branch 조회 → detached 판정 → no-upstream 판정 → dirty → fetch → diverged/ff.
- 이후 유사하게 "특정 git 상태를 exit code나 에러 메시지로 판별하는 로직"을 설계할 때는, 서로 다른 상태가 동일한 실패 시그널(예: exit 128)을 낼 수 있다는 점을 먼저 확인하고 판정 순서를 정해야 한다.

## 근거 출처

task:052 (PLAN§3.1.2(d), AGENTIC-LOG #6·#7), [[git-sync-tool]]
