---
type: entity
title: memory-tool — 프로젝트 메모리 인덱스·히스토리 결정론적 집행 CLI
tags:
  - tool
  - memory
  - cli
  - lifecycle
sources:
  - task:045
  - task:078
  - task:079
  - task:088
  - task:096
related:
  - state-tool
  - three-layer-memory-architecture
  - close-history-auto-link-enforce-conversion
  - guard-precision-none-passthrough-early-return
  - unresolvable-not-absent-two-vocabulary-split
  - tool-created-state-flagged-by-consumer-as-reminder
created: "2026-06-26"
updated: "2026-08-20"
status: active
---

## 개요

`memory-tool`은 OPAL 프로젝트의 메모리 인덱스·히스토리를 결정론적으로 집행하는 CLI 도구다. "반드시"를 산문이 아니라 도구가 강제한다(PRINCIPLES.md Core Stance: "Enforce, don't just advise")는 원칙에 따라, 길이캡·히스토리 FIFO·졸업 워크플로우를 자동화한다. `state-tool`의 구조(run.sh + Python, ok/err/ERROR_CODES)를 재사용하여 표준 라이브러리만으로 구현했다. (근거: task:045 PLAN §3.2.2)

SSOT는 2026-07-29(task:078)부터 `.opal/MEMORY.md`(HTML 주석 마커 + 마크다운 표)에서 `.opal/MEMORY.json`(문서 스키마 런타임 검증)으로 전환됐다 — 마커·표 파싱이라는 변형에 취약한 계층을 소멸시키는 것이 1순위 정당화이며, 토큰 절약은 부수 효과다(상세: [[json-not-token-saving-format]]). (근거: task:078 DONE §1)

## 책임 (WHAT)

8개 서브명령으로 메모리 전 생애주기를 집행한다. 구 `migrate` 서브명령은 삭제되고, md만 있는 프로젝트를 만나면 **모든 서브명령이 최초 진입 시 자동으로(lazy) JSON으로 변환**한다.

| 서브명령 | 역할 |
|---------|------|
| `init` | `MEMORY.json` 골격 생성 (없으면 신규 생성) |
| `append` | 메모리(`--kind memory`) 또는 히스토리(`--kind history`) 행 추가. 요약 ≤80자 검증, 히스토리는 FIFO=5 자동 적용 |
| `update` | `--kind memory`(기본): 메모리 상태(`active/promoted/superseded/dead`)·요약 갱신. `--kind history`(task:079 신설): 작업 히스토리 행을 **삭제 없이 정정**(`stage`/`result`/`path`/`title`, 행 수 불변, FIFO 미적용) |
| `promote` | 메모리를 영구 거처(`--to docs\|brain`)로 졸업 — `--ref`(위치) 필수, 이전 확인 후 행+파일 삭제 + provenance 기록 |
| `prune` | 히스토리 FIFO=5 결정론 정리 (멱등) |
| `show` | 인덱스·히스토리 현황 출력 (read-only). `--brief`(dead/superseded/promoted/candidate 제외 필터, PM 브리핑 전용, task:078) / `--history` 옵션 |
| `review` | 자가검토 단독 health 명령 — violations[] + 라이프사이클 후보 반환. task:096부터 인덱스 행의 `file` 포인터 참조 무결성도 검사한다 (아래 참조) |
| `delete` | `dead`/`superseded` 상태 메모리만 삭제 허용 (`delete_requires_dead_or_superseded` 가드). task:096부터 `--orphan --ref <위치>`로 본문 부재 행(상태 무관)을 정식 정리하는 경로가 추가됐다 (아래 참조) |
| `task-number` | (task:078 신설) 태스크 채번을 락으로 직렬화해 원자적으로 발급 — 종전에는 LLM이 헤더를 직접 Read+Edit하던 유일한 비게이트 쓰기 경로였다(상세: [[non-gated-write-path-audit-before-ssot-conversion]]) |

md만 있는 프로젝트에서 임의 서브명령을 호출하면 `_migrate_md_to_json`이 락 하에서 자동 변환하고 `.bak`을 보존한다(상세: [[silent-loss-prevention-row-accounting-invariant]]). 모든 변경 명령(`init/append/update/promote/prune`) 응답 JSON에 `review` 블록이 자동 첨부된다 — 호출할 때마다 메모리 정리·졸업을 ambient하게 강제한다. (`opal/tools/memory-tool/memory_tool.py`)

## 설계 배경 (WHY)

메모리 관리의 핵심 긴장은 **무손실(지식 보존) vs 비대화(컨텍스트 비팽창)**다. 기존 체계는 FIFO 10, 갯수 상한, 수동 정리에 의존했다 — 도구 미집행으로 운영 산문이 형식을 따르지 않고, 인덱스 셀이 수천 자에 달하는 비대화가 반복됐다. (근거: task:045 PLAN §2.1.2 baseline 실증)

메모리 갯수 상한은 캡틴 지시(2026-06-26)로 전면 제외했다. (근거: task:045 DONE 핵심 설계 결정 #1) 비대화 방지는 세 기제가 분담한다: 졸업(promoted 메모리는 행·파일 삭제), 자가검토(ambient 강제), 길이캡(요약 ≤80자). (추론: 코드패턴 — 갯수 게이트 없이 나머지 세 기제로 충분함을 task:045 S-26 실증 — 17,248→7,535 bytes 56% 감소가 확인)

`delete` 서브명령은 캡틴 지시에 의해 태스크 중반에 추가됐다. 무손실 가드(`delete_requires_dead_or_superseded`)로 살아있는(active) 메모리를 blind 삭제하지 못하도록 차단한다. (근거: task:045 DONE 추가작업 #1)

md→JSON 전환(task:078)은 마커·표 파싱의 변형 취약성(헤더 컬럼 순서 변화, 자유텍스트 상태값 등)을 근본 해소하기 위한 결정이었다 — 문서 스키마가 코드 enum 상수의 단일 출처가 되어 두 계층이 구조적으로 어긋날 수 없게 됐다. 원자적 쓰기(`tmp→fsync→os.replace`)와 O_EXCL+stale 60s 크로스프로세스 락(`memory_lock`)이 신설되어, 검증 실패나 동시 진입 상황에서도 SSOT 파손 없이 실패한다. (근거: task:078 PLAN §3.1.2, §3.2.2)

task:096 이전에는 `review`가 인덱스 행의 `file` 포인터가 가리키는 본문이 실제로 존재하는지 검사하지 않았고, 그 결과 인덱스와 본문이 불일치한 행은 `promote`(본문 실재를 전제)로도 무플래그 `delete`(상태 가드만 봄)로도 다시 도달할 수 없는 고착 상태에 빠질 수 있었다(근거: task:096 DONE.md §1). `build_review_block(doc, json_path)`이 참조 무결성 검사를 신설해 이 상태를 두 검출 어휘(`memory_file_missing`=포인터는 정상 해석되나 파일이 없음 / `memory_file_unresolvable`=포인터 자체를 해석할 수 없음)로 분리하고, `delete --orphan --ref`가 전자에 한해 정식 정리를 허용한다. 가드는 삭제 허용 조건이 아니라 "본문 부재 확인"을 술어로 삼도록 정밀화됐으며, 이 정밀화 과정에서 술어가 의존하는 경로 해석 함수의 `None` 반환을 조기 반환으로 처리하지 않으면 오히려 새 blind 삭제 벡터가 생긴다는 점이 목표-커버 게이트 1차 반복에서 드러나 재설계됐다(상세: [[guard-precision-none-passthrough-early-return]], [[unresolvable-not-absent-two-vocabulary-split]]). `append --kind memory`는 인덱스 행만 만들고 본문 파일을 생성하지 않으므로, 이 검사는 본문을 쓰지 않고 방치된 행을 append 직후부터 표면화한다 — 이는 오탐이 아니라 검사의 존재 이유로 재해석됐다(상세: [[tool-created-state-flagged-by-consumer-as-reminder]]). 부수적으로 스키마 `status` enum과 `memory-learning.md`의 라이프사이클 표 사이에 있던 `candidate` 행 누락(4행 vs 5종)도 함께 정합됐다(근거: task:096 DONE.md §1 F-003). (근거: task:096 PLAN §미확정 사항 판정, DONE.md §1-§4)

078의 전환으로 히스토리 관리가 전량 tool-gated되며 오기재를 되돌릴 경로가 사라진 부작용이 발생했다(task:079). `delete --kind history`는 신설하지 않았다 — 무손실 삭제 가드를 걸 `status` 필드가 히스토리 행에 없고, 히스토리는 FIFO=5 회전 로그라 지목 삭제가 애초에 불필요하기 때문이다. 대신 `update --kind history`로 행 추가·삭제 없이 4필드(`stage`/`result`/`path`/`title`)만 in-place 정정한다. 이 정정 경로는 FIFO 절단 함수(`_enforce_history_fifo`)를 호출하지 않는다 — 상한 초과 문서에서 행을 조용히 버리게 되어 "삭제 없는 정정" 전제를 깨기 때문이다(상세: [[rotating-log-correction-over-deletion]]). `--kind` 인자는 기본값을 `memory`로 두어 기존 132건 테스트가 무변경 통과했고(상세: [[backward-compat-default-value-discipline]]), 값 검증은 `choices=`가 아니라 코드에서 수행해 단일라인 JSON 응답 계약을 지켰다(상세: [[argparse-choices-breaks-json-contract]]). (근거: task:079 DONE §1, §5, §6)

## 관계 (HOW)

- [[state-tool]] — 구조·패턴의 원형. `ok/err/ERROR_CODES/run.sh` 를 직접 재사용. task:088부터는 완료 단계의 히스토리 자동 연결에서 state-tool이 memory-tool을 별도 프로세스로 호출하는 소비자 관계도 추가됐다(상세: [[close-history-auto-link-enforce-conversion]]) — memory-tool 자체에는 신규 서브명령이나 옵션이 추가되지 않았다
- [[three-layer-memory-architecture]] — memory-tool이 집행하는 단기 기억(MEMORY.json) 계층을 담당
- `brain-tool` — promote `--to brain` 경로는 brain-tool add-page / `//opbr ingest`를 재사용. memory-tool이 brain 쓰기를 재발명하지 않는다 (Simplicity)
- [[json-not-token-saving-format]] / [[silent-loss-prevention-row-accounting-invariant]] / [[non-gated-write-path-audit-before-ssot-conversion]] / [[parser-drift-silent-longevity-lesson]] — task:078 전환에서 도출된 설계 판단·교훈
- [[rotating-log-correction-over-deletion]] / [[backward-compat-default-value-discipline]] / [[argparse-choices-breaks-json-contract]] — task:079 `update --kind history` 신설에서 도출된 설계 판단
- [[guard-precision-none-passthrough-early-return]] / [[unresolvable-not-absent-two-vocabulary-split]] / [[tool-created-state-flagged-by-consumer-as-reminder]] — task:096 참조 무결성 검사·`delete --orphan` 신설에서 도출된 설계 판단
- [[expected-total-as-reference-not-gate-criterion]] — task:096이 선재 `ERROR_CODES` 총계 하드코딩 회귀 가드를 부분집합+추가분 단언으로 재구성한 사례가 이 페이지에 추가됨

## 소스 커버리지

| 식별자 | 경로:줄번호 | 설명 |
|--------|-----------|------|
| `memory_tool.py` | `opal/tools/memory-tool/memory_tool.py` | 서브명령 디스패처 + ok/err/ERROR_CODES + `_migrate_md_to_json` |
| `run.sh` | `opal/tools/memory-tool/run.sh` | venv Python 래퍼 |
| `memory.schema.json` | `opal/tools/memory-tool/schema/memory.schema.json` | 문서 스키마 SSOT (task:078 — 행 스키마에서 재설계) |
| `test_memory_tool.py` | `opal/tools/memory-tool/tests/test_memory_tool.py` | pytest 단위 테스트 132건 (task:078 — RED 61건 신규 + 이관/재작성) |
| `ERROR_CODES` | `opal/tools/memory-tool/memory_tool.py` | 에러 코드 SSOT dict (`migration_failed`/`invalid_json`/`schema_load_failed`/`lock_timeout`/`task_number_regression` 등 task:078 신설) |
| `HISTORY_FIFO_LIMIT` | `opal/tools/memory-tool/memory_tool.py` | 히스토리 FIFO 상수 = 5 |
| `memory_lock` | `opal/tools/memory-tool/memory_tool.py` | O_EXCL + stale 60s 크로스프로세스 락 (task:078) |
| `atomic_write_json` | `opal/tools/memory-tool/memory_tool.py` | tmp→fsync→os.replace 원자적 쓰기 (task:078) |
| `_apply_history_correction` | `opal/tools/memory-tool/memory_tool.py` | `update --kind history` 대상 행 식별 + in-place 필드 치환 (task:079 신설) |
| `_check_update_kind_args` | `opal/tools/memory-tool/memory_tool.py` | `--kind` ↔ 필드 인자 조합 사전 검증, 락 밖 게이트 (task:079 신설) |
| `build_review_block` | `opal/tools/memory-tool/memory_tool.py:837-` | 자가검토 블록 생성 + `file` 포인터 참조 무결성 검사 (task:096 확장) |
| `_resolve_memory_file` | `opal/tools/memory-tool/memory_tool.py:806-820` | 경로 포인터 해석, 실패 시 `None` 반환 3경로(예외/탈출/빈 값) |
| `cmd_delete` `--orphan/--ref` | `opal/tools/memory-tool/memory_tool.py:1380-1391` | 본문 부재 행 정식 정리 — 조기 반환 가드로 `None` 통과 차단 (task:096 신설) |
| `ERROR_CODES` 3종 신설 | `opal/tools/memory-tool/memory_tool.py:105-160` | `memory_file_exists`/`memory_file_unresolvable`/`orphan_ref_missing` — 총 23→26종 (task:096) |
