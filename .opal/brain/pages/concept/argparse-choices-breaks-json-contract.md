---
type: concept
title: argparse choices=가 단일라인 JSON 응답 계약을 깬다
tags:
- cli
- argparse
- json-contract
- pitfall
sources:
- task:079
related:
- memory-tool
created: '2026-07-30'
updated: '2026-07-30'
status: draft
---
## 개요

단일라인 JSON 응답 계약(`{"ok": true|false, ...}`, traceback 금지)을 가진 CLI에서 `argparse`의 `choices=` 옵션을 값 검증에 쓰면 그 계약이 깨진다 — `choices=` 위반 시 argparse는 코드가 만든 에러 응답이 아니라 **exit 2 + stderr usage(비 JSON) 텍스트**를 낸다. 허용값 검증은 `choices=`가 아니라 코드에서 직접 수행해야 한다. (근거: task:079 DONE §5 부가 결정, PLAN H-8)

## 결정 배경 (WHY)

`memory-tool update`에 `--kind {memory,history}`를 신설하며, 잘못된 `--kind` 값에 대해 "단일라인 JSON, exit 1, `error:"invalid_kind"`"로 응답해야 하는 계약(R-1 AC(c))이 있었다. `argparse.add_argument(..., choices=[...])`를 그대로 붙이면 값 위반 시 argparse가 자체적으로 `exit(2)`하며 stderr에 사용법 텍스트를 출력한다 — 이는 JSON도 아니고 exit code도 다르다(1이 아니라 2). 같은 파일의 `append` 서브명령이 이미 `--kind`에 `choices=`를 쓰고 있어(`memory_tool.py:1395`), 신규 코드 작성 시 "옆 코드를 그대로 베끼는" 무비판 복사 위험이 실재했다. (근거: task:079 PLAN H-8, DONE §5 부가 결정)

## 결정 내용

- **허용값은 `metavar`로 `--help`에 노출**하고(`metavar="{memory,history}"`), 실제 값 검증은 `choices=`가 아니라 함수 본문 코드에서 수행해 도구 자체의 `err()` 헬퍼로 JSON 에러를 낸다.
- 이 규율은 "이미 같은 파일에 `choices=`를 쓰는 선례가 있다"는 사실이 안전하다는 근거가 되지 않는다는 것을 보여준다 — 선례가 있어도 그 선례가 이번과 같은 응답 계약 하에 있는지(이번 경우 `append`도 사실 동일 계약 하에 있어 잠재적으로 같은 결함을 안고 있을 수 있음)를 먼저 확인해야 한다.
- **검증 신호**: exit code와 stdout이 JSON임을 **동시에** 단정하는 테스트로 회귀를 잡는다(079 TS-004) — exit code만 보거나 stdout만 보면 이 결함을 놓친다.

## 영향 범위

단일라인 JSON 응답 계약(`ok/err` 패턴)을 쓰는 모든 OPAL 내부 도구(`memory-tool`, `state-tool`, `brain-tool` 등)의 `argparse` 서브명령 설계에 재사용 가능한 체크포인트다 — 새 옵션 인자에 값 제약을 걸 때 `choices=`를 습관적으로 붙이기 전에, 이 CLI의 에러 응답 계약이 argparse 기본 동작(exit 2 + stderr 텍스트)과 호환되는지 먼저 확인한다.

## 관련 페이지

- [[memory-tool]] — 이 판단이 적용된 `update --kind` 인자 설계
