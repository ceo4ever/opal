---
type: concept
title: 회전 로그는 삭제 대신 정정 — FIFO 히스토리 무손실 가드 설계
tags:
- memory
- fifo
- data-integrity
- design-pattern
sources:
- task:079
related:
- memory-tool
- silent-loss-prevention-row-accounting-invariant
created: '2026-07-30'
updated: '2026-07-30'
status: draft
---
## 개요

FIFO 상한이 걸린 회전 로그(작업 히스토리 등)는 자동 회전이 정리를 대신하므로, 지목 삭제 명령을 신설하는 대신 오기재를 되돌리는 **정정** 경로를 제공해야 한다. 무손실 삭제 가드를 걸 상태 필드가 없는 자료구조에 삭제 명령을 노출하는 것은 정리 기능이 아니라 위험 표면이다. (근거: task:079 DONE §1, §6)

## 결정 배경 (WHY)

078의 메모리 SSOT를 `MEMORY.json`으로 전환하며 히스토리 관리가 전량 tool-gated가 됐고, 그 결과 오기재를 되돌릴 경로가 사라졌다 — 남은 선택지는 ① 5건을 더 추가해 FIFO로 밀어내기 ② 도구를 우회한 손편집(078이 없애려던 바로 그 행위)뿐이었다. (근거: task:079 DONE §1)

`delete`류 명령의 무손실 가드는 통상 `status`(`dead`/`superseded`) 같은 필드에 건다. 그런데 히스토리 행(`historyRow`)에는 그런 상태 필드가 없다(`opal/tools/memory-tool/schema/memory.schema.json:71-72`) — 가드를 걸 자리가 없는 자료구조에 삭제 명령을 얹으면, 살아있는 행을 막을 방법 없이 지울 수 있는 위험한 표면이 새로 생긴다. 히스토리는 FIFO=5 회전 로그이므로 애초에 필요한 것은 삭제가 아니라 정정이다. (근거: task:079 DONE §1, §6 — 소유자 결정)

## 결정 내용

- **`delete --kind history`는 신설하지 않는다.** 무손실 가드 근거(`status` 필드)가 히스토리 행에 없고, FIFO 5 회전 로그는 지목 삭제가 애초에 불필요하다(task:079 DONE §6 비범위).
- **대신 `update --kind history`로 4필드(`stage`/`result`/`path`/`title`)를 in-place 정정**한다 — 행 추가·삭제 없이 대상 행의 필드만 치환한다.
- **[MUST] 정정 경로는 회전(FIFO) 집행 함수를 호출하지 않는다.** `rows[:N]` 형태의 순수 절단 함수(예: `_enforce_history_fifo`, `opal/tools/memory-tool/memory_tool.py:774-778`)는 상한을 넘긴 문서에서 초과 행을 말없이 버린다. 스키마에 `maxItems`가 없어 초과 문서가 유효한 경우가 실재하므로(`schema:25-29`), "추가" 경로(append, FIFO 적용)와 "정정" 경로(update, FIFO 미적용)가 같은 절단 헬퍼를 공유하면 정정 명령이 조용한 삭제 명령으로 둔갑한다. 초과 상태는 응답의 `review.history_status.fifo_trimmed`로만 표면화하고, 실제 정리는 별도 `prune` 명령이 전담한다. (근거: task:079 PLAN H-6, P-5)

## 영향 범위

FIFO/회전 상한이 있고 항목에 무손실 가드용 상태 필드가 없는 모든 로그형 데이터 구조(작업 히스토리, 감사 로그, 최근 항목 목록 등)에 재사용 가능한 설계 원칙이다 — 삭제 요구가 들어오면 먼저 "회전으로 이미 자연 정리되는가"와 "가드를 걸 필드가 있는가"를 확인하고, 없다면 삭제 대신 정정 경로를 설계한다.

## 관련 페이지

- [[memory-tool]] — 이 결정이 적용된 `update --kind history` 신설 대상 도구
- [[silent-loss-prevention-row-accounting-invariant]] — 무성 유실 차단이라는 상위 원칙의 다른 적용 사례(마이그레이션 행 회계 vs 이번 회전 로그 절단 함수 오용)
