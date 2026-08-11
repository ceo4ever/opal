---
type: concept
title: CLOSE 완료 히스토리 자동 연결 — 산문 트리거에서 도구 집행으로 전환
tags:
- opal-pipeline
- close
- memory
- state-tool
- memory-tool
- enforce-not-advise
sources:
- task:088
related:
- state-tool
- memory-tool
- pipeline-todo-mirror-hook-enforcement
- memory-lifecycle-graduation-workflow
- opal-principles-constitution
created: '2026-08-11'
updated: '2026-08-11'
status: draft
---
## 개요

태스크를 마칠 때마다 커밋이 두 번 발생하던 문제를 해결한 결정이다. 진행 SSOT 도구가 완료 처리를 확정하는 순간 작업 히스토리 행을 직접 생성하도록 바꿔, 산출물 확정과 히스토리 갱신이 한 커밋으로 묶이게 했다. (근거: task:088 DONE §1)

## 결정 배경 (WHY)

- 작업 히스토리 갱신 규칙이 어느 완료 단계 절차에도 강제 스텝으로 없었고, 참조 문서의 "완료 시" 산문 안내로만 존재했다 — 실행 시점이 재량이라 완료 확정 이후로 밀리곤 했다. (근거: task:088 DONE §1)
- 헌법 Core Stance "Enforce, don't just advise: if a rule must always hold, a tool gates it, not prose"를 적용한 사례다 — 관련 개념: [[opal-principles-constitution]]. (근거: task:088 DONE §2)
- 완료 단계 절차 10종에 히스토리 스텝을 개별 삽입하는 방안은 절차 정의 10건 + 변경이력 10행이 중복되는 복제 비용이 있어 기각됐다. 완료 처리 직후 리마인더를 훅으로 주입하는 방안도 훅 미설정 환경·실행 플랫폼 차이에서 강제력이 사라져 함께 기각됐다. 대신 진행 SSOT 도구가 히스토리 도구를 직접 호출하는 방식을 채택했다 — 훅 유무·실행 플랫폼과 무관하게 항상 집행된다. (근거: task:088 DONE §2 안 비교표)

## 결정 내용

- 완료 단계의 마지막 행이 완료로 확정되는 순간, 진행 SSOT 도구가 히스토리 도구를 별도 프로세스로 호출해 히스토리 행을 생성한다. 완료 단계 절차 정의 10종은 한 줄도 바뀌지 않는다 — 도구 계층 단일 지점의 변경이 전 절차에 동시 적용되는 것이 이 설계의 핵심 이점이다. (근거: task:088 DONE §3)
- **역할 분담은 판단 개입 여부로 가른다.** 제목·날짜·단계값·경로처럼 진행 상태에서 결정론적으로 파생되는 필드는 도구가 채우고, 핵심결과(무엇을 바꿨고 어떤 결과였는지)처럼 판단이 개입하는 필드는 소유자가 나중에 보강하는 자리로 남긴다. 도구는 그 자리를 식별 가능한 플레이스홀더로 채우고, 그대로 실행할 수 있는 보강 명령을 안내에 담아 돌려준다. (근거: task:088 DONE §2, §4 신설 심볼표)
- **도구 간 호출은 별도 프로세스로 격리한다.** 진행 SSOT 도구가 히스토리 도구를 같은 프로세스 안으로 끌어들여 쓰면, 히스토리 도구 쪽 오류 처리 방식이 진행 SSOT 프로세스 전체를 함께 죽일 위험이 있다. 별도 프로세스로 호출하면 그 위험이 차단된다. 두 도구가 각자 자기 파일의 잠금만 다루므로 중첩 잠금도 발생하지 않는다는 것을 설계 단계에서 확인했다. (근거: task:088 PLAN §2.2, DONE §4 락 상호작용 검증)
- **연동 실패가 완료 처리 자체를 막지 않는다.** 히스토리 연동이 실패하거나(예: 히스토리 저장소 파일 손상) 대상 프로젝트를 찾지 못해도, 완료 처리 응답은 항상 정상 성공으로 유지되고 연동 결과·경고는 별도 필드로만 보고된다. 이 필드는 진행 상태 파일에 영속하지 않는다 — 기존 진행 미러 기능(관련: [[pipeline-todo-mirror-hook-enforcement]])이 같은 이유로 택한 비영속·응답 전용 방식을 그대로 답습했다. (근거: task:088 PLAN §2.5)
- 멱등성은 태스크 경로를 판정 키로 쓴다 — 같은 완료 행을 다시 확정해도 히스토리 행이 중복 생성되지 않는다. (근거: task:088 PLAN §2.4)

## 영향 범위

- 진행 SSOT 도구(`opal/tools/state-tool/state_tool.py`) — 완료 확정 처리에 히스토리 연동 오케스트레이션 신설
- 진행 미러 릴레이 훅(`opal/tools/state-tool/todo_mirror_hook.py`) — 기존 진행 미러 안내에 히스토리 보강 안내를 병존 추가
- `opal/core/references/harness/memory-learning.md` — "CLOSE 자동 연결" 절 신설
- 완료 단계 절차 정의 10종은 무변경 — 도구 계층 단일 지점 변경으로 전체에 동시 적용

## 관련 페이지

- [[state-tool]]
- [[memory-tool]]
- [[pipeline-todo-mirror-hook-enforcement]] — 동일 enforce 전환 패턴의 선행 사례(진행 미러)
- [[memory-lifecycle-graduation-workflow]]
- [[opal-principles-constitution]]
