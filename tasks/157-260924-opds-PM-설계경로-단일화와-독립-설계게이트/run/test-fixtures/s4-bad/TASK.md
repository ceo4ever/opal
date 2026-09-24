---
template: sdlc-v2
---
# TASK: 주문 내보내기 CSV 다운로드

## Problem
관리자가 주문 목록을 외부 정산 도구로 옮길 방법이 없어 화면을 수작업으로 복사한다(`admin/orders/list.py:40`).

## Proposed outcome
관리자가 필터된 주문 목록을 CSV 파일로 내려받는다.

## Affected users and systems
- 포함: 관리자 주문 목록 화면, 주문 조회 API
- 제외: 정산 도구 연동

## Constraints
- C-1: 한 번에 최대 10,000건까지만 내보낸다.

## Acceptance criteria
- AC-1: 필터가 적용된 주문 목록의 CSV를 내려받을 수 있다.
- AC-2: 10,000건을 넘으면 내보내기를 거부하고 사유를 보여 준다.
