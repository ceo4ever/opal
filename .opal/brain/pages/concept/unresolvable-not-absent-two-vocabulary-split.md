---
type: concept
title: 확인 불가는 부재가 아니다 — 검출 어휘 2분으로 처분을 표현한다
tags:
- memory-tool
- guard-design
- vocabulary
- lesson
- task-096
sources:
- task:096
related:
- guard-precision-none-passthrough-early-return
- memory-lifecycle-graduation-workflow
created: '2026-08-20'
updated: '2026-08-20'
status: draft
---
## 개요

"확인할 수 없다"와 "없다"는 다른 상태이며, 검출 로직이 둘을 하나의 어휘로 묶으면 무손실 원칙이 깨진다. 리소스 포인터를 해석할 수 없는 경우와 해석은 됐지만 파일이 실재하지 않는 경우를 별도 어휘로 분리하면, 처분(정리 가능 / 포인터 수리 필요)을 검출 시점의 이름 자체로 표현할 수 있다.

## 결정 배경 (WHY)

- 참조 무결성 검사를 설계할 때 자연스러운 접근은 "포인터가 가리키는 파일이 있는가"를 단일 불리언으로 판정하는 것이다. 그러나 포인터 자체를 해석하지 못하는 경우(경로 정규화 예외, 허용 디렉토리 밖으로의 탈출)까지 "파일이 없다"에 합쳐버리면, 실제로는 본문이 디스크 어딘가에 멀쩡히 존재할 수 있는 행을 "정리 가능"으로 잘못 분류하게 된다(근거: task:096 PLAN.md:369).
- 운영 피해는 구체적이다 — 해석 불가로 분류된 행을 "본문 없음"으로 오인해 삭제 경로로 보내면, 실제로는 존재하는 지식이 사라진다. 반대로 사람이 이 행을 살리려고 `promote`를 먼저 시도하면 "본문을 찾을 수 없음"을 받게 되는데, 실제 원인은 포인터가 잘못된 것이지 본문이 사라진 것이 아니다. 잘못된 라벨이 잘못된 복구 행동을 유도한다(근거: task:096 PLAN.md:559).

## 결정 내용

- 검출 어휘를 2종으로 분리한다 — `memory_file_missing`(경로는 정상 해석되나 그 위치에 파일이 없음 → 정리 가능)과 `memory_file_unresolvable`(경로 자체를 해석할 수 없음 → 확인 불가, 포인터 수리 필요)(`opal/tools/memory-tool/memory_tool.py:868-877`).
- 처분도 어휘를 따라 갈라진다 — `delete --orphan --ref`는 `memory_file_missing` 조건에서만 정리를 허용하고, `memory_file_unresolvable` 조건에서는 무손실 원칙에 따라 삭제를 거부한다(`opal/tools/memory-tool/memory_tool.py:1385-1391`, 에러 메시지: "확인 불가는 부재가 아니므로 정리 거부").
- 일반화: 리소스 존재 검사를 설계할 때 "조회 실패"(포인터를 못 읽음)와 "조회 성공 + 부재 확인"(포인터는 읽었으나 대상이 없음)을 반드시 별도 상태로 표현한다. 두 상태를 하나의 불리언으로 합치면, 조회 실패를 "없음"으로 취급하는 쪽에서 반드시 무손실 원칙 위반이 발생한다.

## 영향 범위

- `opal/tools/memory-tool/memory_tool.py:868-877` — `build_review_block` 참조 무결성 검사 어휘 2종.
- `opal/tools/memory-tool/memory_tool.py:1385-1391` — `delete --orphan` 처분 분기.
- 검출·정리 기능을 설계하는 모든 향후 도구 — "확인 불가"를 표현할 어휘가 없는 상태에서 존재 검사를 이진화하면 이 실패 형태가 재발한다.

## 관련 페이지

- [[guard-precision-none-passthrough-early-return]] — 이 어휘 분리를 가능하게 한 가드 재설계
- [[memory-lifecycle-graduation-workflow]] — 이 검출 어휘가 속한 memory-tool 라이프사이클
