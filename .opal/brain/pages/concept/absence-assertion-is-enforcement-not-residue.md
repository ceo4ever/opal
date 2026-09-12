---
type: concept
title: 부재 단언은 잔재가 아니라 집행 장치다 — 제거 전수 검사의 명시 예외
tags:
- removal
- verification
- test-design
- lesson
sources:
- task:118
related:
- removal-task-boundary-unification
- marker-literal-check-meta-circular-false-positive
- context-tag-suppresses-false-positive-without-removing-hit
- worktree-task-root-allocator-root-split
created: '2026-09-12'
updated: '2026-09-12'
status: draft
---
## 개요

제거형 태스크에서 "제거 대상 심볼의 전역 잔존 0건"을 판정할 때, 검색에 걸린 잔존 매칭 중 **"그 심볼이 제거됐음"을 단언하는 테스트 가드**는 잔재가 아니라 제거를 지키는 집행 장치다. 전수 검사 규칙을 설계할 때 부재 단언을 명시적 예외로 두지 않으면, 판정을 통과시키려고 회귀 방지 자산을 지우게 된다.

## 결정 배경 (WHY)

- 태스크 118은 네 런타임에 중복된 허브 보정 심볼을 제거하고 "활성 코드·주석·헤더·테스트 범위에서 대상 토큰 매칭 0건"을 완료 조건으로 걸었다. 전수 검색 결과 잔존 매칭이 남았고, 유형은 넷이었다 — 삭제된 골든표 파일을 가리키는 stale 문서 참조, 붉은 단계 시점 서술만 남은 주석, 제거된 심볼과 무관한 지역 변수명 오탐, 그리고 **부재를 단언하는 테스트 가드**다(근거: task:118 AGENTIC-LOG 엔트리 70).
- 앞의 세 유형은 전부 정리 대상이지만 마지막 하나는 성격이 다르다. 그 테스트는 제거 계약 자체를 지키는 회귀 방지 자산이라 지우면 다음 개정이 심볼을 조용히 되살려도 아무도 모른다. 판정을 통과시키기 위해 지우는 순간 완료 조건이 자기 목적을 파괴한다(근거: task:118 AGENTIC-LOG 엔트리 71 — "부재 단언 가드는 보존하고, 전수 판정 시 명시적 예외로 기록한다").
- 최종 실측에서도 제거 대상 4종 중 세 토큰은 잔존 0건이었고, 남은 매칭 5건은 전부 테스트 제목·단언문·단언 실패 메시지, 즉 "제거됐음"을 말하는 자리였다(`opal/tools/brain-tool/tests/test_brain_tool.py:2528-2529`, `opal/tools/code-scan/tests/test-hub-root.js:153,156,157`). 이 기준을 확정해 검증 단계 워커와 컨벤션 진단에 주입했다(근거: task:118 AGENTIC-LOG 엔트리 89·101, DONE §검증 "제거 심볼 전수").
- 골든표를 폐기하는 작업에서도 같은 경계가 지켜졌다 — 붉은 단계 시점 서술 문구는 현재 계약 서술로 교체하되 부재 단언 가드는 보존하고 단언문은 한 줄도 바꾸지 않았다(근거: task:118 AGENTIC-LOG 엔트리 69).

## 결정 내용

- 제거 전수 검사의 완료 조건을 쓸 때, 매칭 0건을 요구하는 **같은 자리에** "부재를 단언하는 테스트는 예외"를 함께 명시한다. 예외를 사후 판단에 맡기면 워커마다 판정이 갈리고, 보수적인 워커일수록 가드를 지워 통과를 만든다.
- 잔존 매칭을 발견하면 유형을 먼저 분류한다 — 실제 잔재(stale 참조·미갱신 주석), 토큰 오탐(같은 이름의 무관한 지역 변수), 부재 단언 가드. 앞 둘만 정리하고 마지막은 보존 근거와 좌표를 판정문에 남긴다.
- 보존한 가드의 좌표를 완료 문서의 검증 절에 명시한다. 다음 태스크가 같은 검색을 돌렸을 때 "왜 0건이 아닌가"를 다시 조사하지 않게 하는 것이 목적이다.

## 영향 범위

심볼·섹션·규범을 완전 삭제하고 "잔존 0건"을 완료 조건으로 삼는 모든 제거형 태스크의 검증 설계에 적용된다. 특히 삭제 대상의 이름이 그대로 테스트 제목·단언 메시지에 들어가는 경우 — 즉 제거를 집행하는 테스트일수록 검색에 더 잘 걸리는 구조 — 에서 예외 선언이 필수다.

## 관련 페이지

- [[removal-task-boundary-unification]]
- [[marker-literal-check-meta-circular-false-positive]]
- [[context-tag-suppresses-false-positive-without-removing-hit]]
- [[worktree-task-root-allocator-root-split]]
