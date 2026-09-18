---
type: entity
title: ownership-tool
module: ownership_core
layer: util
domain: opal-pipeline
exports:
- session_registry_path
- hub_lease_path
- stop_receipt_path
- registry_meta_path
- SessionRecord
- LeaseRecord
- StopReceipt
- write_json_atomic
- read_json
- read_registry_meta
- resolve_session_id
- task_ownership_copy_path
- resolve_roots
source_ref: opal/tools/ownership-tool/ownership_tool/ownership_core.py
header_synced: 2026-09-18
tags:
- tool
- ownership
- hook
- pipeline
sources:
- code:opal/tools/ownership-tool/
- task:138
related:
- worktree-locates-hub-by-issued-copy
- stop-force-requires-state-transition-claim
- red-corpus-precedes-contract-fabricates-layout
- worktree-tool
- state-tool
created: '2026-09-18'
updated: '2026-09-18'
status: active
---
## 개요

태스크 **소유권 판정의 런타임 저장소와 폐쇄 enum 계약**을 소유하는 신설 도구다(task:138). Stop 훅이 부모 디렉터리를 거슬러 올라가 허브 `tasks/`를 스캔하고 `updated_at` 최신 태스크를 "이 세션의 태스크"로 지목하던 추론을 대체한다 — 소유권은 이제 **발급된 값과 기록된 lease**로만 판정된다.

## 책임 경계

- **판정 로직은 이 도구가 소유한다.** 훅 어댑터는 봉투 파싱·출력 형식만 갖고 분류는 전부 `resolver`·`lease`에 위임한다.
- **추론하지 않는다.** cwd 문자열 자르기·부모 디렉터리 순회·`.opal-worktrees` 문자열 탐색·mtime/`updated_at` 최신순 선택을 어느 모듈에서도 하지 않으며, 테스트가 그 부재를 집행한다.
- **registry는 읽기 전용이다.** `<hub_root>/.opal-worktrees/.meta/task_<NNN>.json`을 읽기만 하고 발급 경로를 추측·보정하지 않는다 — 쓰기는 `worktree-tool`이 소유한다(dual-writer 금지).
- **실패는 예외가 아니라 구조화 반환이다.** 훅 진입점은 전 경로 fail-safe exit 0이라 어떤 실패도 세션을 막지 않는다.
- **플랫폼 고유 환경변수명은 `claude_adapter` 한 곳에만 둔다**(D-18·C-15).

## 모듈 구성 (`ownership_tool/`, 실측)

| 모듈 | 책임 |
|---|---|
| `ownership_core` | 런타임 저장소 3경로 계산·스키마 dataclass·파일 lock·원자 쓰기·registry 읽기 어댑터·세션 ID 해석(`resolve_session_id`)·실행 루트 해석(`resolve_roots`) |
| `lease` | hub task lease(`<canonical_task>/run/.runtime/owner.json`) claim·heartbeat·release·classify, TTL 해석, `claim_source` 폐쇄 enum |
| `session_registry` | 세션 registry(`<project_root>/.opal/run/.runtime/sessions/<id>.json`) 등록·멱등 갱신 |
| `fingerprint` | 파이프라인 의미 필드만 정규화한 SHA-256 지문 계산과 stop-guard receipt 저장·조회 |
| `resolver` | worktree/hub 후보 수집과 분류(`hub_canonical`·`worktree_owned_shadow`·`current_session_owned`·`foreign_session_owned`·`unowned`·`lease_expired`·`invalid_state`) |
| `stop_evaluator` | Stop 판정 조립 — 강제 후보 선별, 복수 후보 시 PM 이관, 차단 상한·무진전 지문 통과 |
| `decisions` | `decision_kind`·`diagnostic` 폐쇄 enum과 결과 스키마 검증(시스템 상태를 읽지 않는 순수 모듈) |
| `claude_adapter` | 플랫폼 고유 env 변수명 격리 |
| `session_start_hook` · `heartbeat_hook` · `session_end_hook` · `pretooluse_guard_hook` · `stop_hook` | 5종 훅 어댑터 — 각각 claim·연장·해제·쓰기 차단·Stop 판정 출력 |

훅 어댑터는 `opal/core/hooks/claude-hooks.json`에 파일 경로로 직접 등록되어 실행된다. `run.sh`는 `.venv` 래퍼이며 CLI 표면은 아직 없다 — 패키지 import 가능 여부만 확인하고 `not_implemented`를 반환한다.

## 저장소 3경로

세션 registry(`<project_root>/.opal/run/.runtime/sessions/`), hub task lease(`<canonical_task_path>/run/.runtime/owner.json`), stop receipt(`<project_root>/.opal/run/.runtime/stop-guard/`). 세 경로 모두 기존 `.gitignore` 커버 범위 안에 떨어져 `.gitignore` 자체를 바꾸지 않는다. 파일 0600·디렉터리 0700, 저장소마다 `<path>.lock` 1개이며 쓰기는 temp → 원자 교체다. lock 상한 초과는 예외가 아니라 `lock_timeout` 구조화 반환이다.

> 실측 SSOT는 코드와 `opal/tools/ownership-tool/README.md`다. enum 종수·모듈 수 같은 수치를 이 페이지에 복제하지 않는다.

## 형제 도구와의 관계

- **`worktree-tool`** — 발급 쪽. registry meta를 쓰고, 워크트리 생성 시 `<worktree_root>/.opal/task-ownership.json`에 발급값 사본을 배달한다. `ownership-tool`은 그 발급값을 읽기만 한다([[worktree-locates-hub-by-issued-copy]]).
- **`state-tool`** — 상태 전이 쪽. 첫 상태 전이에서 `claim_source=state_transition`으로 lease를 claim해, Stop 강제 차단 자격을 만든다([[stop-force-requires-state-transition-claim]]).

## 관련 페이지

- [[worktree-locates-hub-by-issued-copy]]
- [[stop-force-requires-state-transition-claim]]
- [[red-corpus-precedes-contract-fabricates-layout]]
- [[worktree-tool]]
- [[state-tool]]
