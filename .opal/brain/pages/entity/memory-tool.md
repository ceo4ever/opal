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
related:
  - state-tool
  - three-layer-memory-architecture
created: "2026-06-26"
updated: "2026-06-26"
status: active
---

## 개요

`memory-tool`은 OPAL 프로젝트의 `MEMORY.md` 인덱스·히스토리를 결정론적으로 집행하는 CLI 도구다. "반드시"를 산문이 아니라 도구가 강제한다(PRINCIPLES.md Core Stance: "Enforce, don't just advise")는 원칙에 따라, 길이캡·마커 가드·히스토리 FIFO·졸업 워크플로우를 자동화한다. `state-tool`의 구조(run.sh + Python, ok/err/ERROR_CODES, 마커 가드 패턴)를 재사용하여 표준 라이브러리만으로 구현했다. (근거: task:045 PLAN §3.2.2)

## 책임 (WHAT)

9개 서브명령으로 메모리 전 생애주기를 집행한다.

| 서브명령 | 역할 |
|---------|------|
| `init` | MEMORY.md에 신포맷 마커·헤더 삽입 (없으면 신규 생성) |
| `append` | 메모리(`--kind memory`) 또는 히스토리(`--kind history`) 행 추가. 요약 ≤80자 검증, 히스토리는 FIFO=5 자동 적용 |
| `update` | 메모리 상태(`active/promoted/superseded/dead`)·요약 갱신 |
| `promote` | 메모리를 영구 거처(`--to docs\|brain`)로 졸업 — `--ref`(위치) 필수, 이전 확인 후 행+파일 삭제 + provenance 기록 |
| `prune` | 히스토리 FIFO=5 결정론 정리 (멱등) |
| `migrate` | 구포맷 MEMORY.md → 신포맷 변환 (제목 추출 + `[REVIEW]` 플래그, 무손실) |
| `show` | 인덱스·히스토리 현황 출력 (read-only) |
| `review` | 자가검토 단독 health 명령 — violations[] + 라이프사이클 후보 반환 |
| `delete` | `dead`/`superseded` 상태 메모리만 삭제 허용 (`delete_requires_dead_or_superseded` 가드) |

모든 변경 명령(`init/append/update/promote/prune/migrate`) 응답 JSON에 `review` 블록이 자동 첨부된다 — 호출할 때마다 메모리 정리·졸업을 ambient하게 강제한다. (`opal/tools/memory-tool/memory_tool.py`)

## 설계 배경 (WHY)

메모리 관리의 핵심 긴장은 **무손실(지식 보존) vs 비대화(컨텍스트 비팽창)**다. 기존 체계는 FIFO 10, 갯수 상한, 수동 정리에 의존했다 — 도구 미집행으로 운영 산문이 형식을 따르지 않고, 인덱스 셀이 수천 자에 달하는 비대화가 반복됐다. (근거: task:045 PLAN §2.1.2 baseline 실증)

메모리 갯수 상한은 캡틴 지시(2026-06-26)로 전면 제외했다. (근거: task:045 DONE 핵심 설계 결정 #1) 비대화 방지는 세 기제가 분담한다: 졸업(promoted 메모리는 행·파일 삭제), 자가검토(ambient 강제), 길이캡(요약 ≤80자). (추론: 코드패턴 — 갯수 게이트 없이 나머지 세 기제로 충분함을 task:045 S-26 실증 — 17,248→7,535 bytes 56% 감소가 확인)

`delete` 서브명령은 캡틴 지시에 의해 태스크 중반에 추가됐다. 무손실 가드(`delete_requires_dead_or_superseded`)로 살아있는(active) 메모리를 blind 삭제하지 못하도록 차단한다. (근거: task:045 DONE 추가작업 #1)

## 관계 (HOW)

- [[state-tool]] — 구조·패턴의 원형. `ok/err/ERROR_CODES/마커가드/run.sh` 를 직접 재사용
- [[three-layer-memory-architecture]] — memory-tool이 집행하는 단기 기억(MEMORY.md) 계층을 담당
- `brain-tool` — promote `--to brain` 경로는 brain-tool add-page / `//opbr ingest`를 재사용. memory-tool이 brain 쓰기를 재발명하지 않는다 (Simplicity)

## 소스 커버리지

| 식별자 | 경로:줄번호 | 설명 |
|--------|-----------|------|
| `memory_tool.py` | `opal/tools/memory-tool/memory_tool.py` | 서브명령 디스패처 + ok/err/ERROR_CODES |
| `run.sh` | `opal/tools/memory-tool/run.sh` | venv Python 래퍼 |
| `memory.schema.json` | `opal/tools/memory-tool/schema/memory.schema.json` | 행 스키마 문서용 SSOT |
| `test_memory_tool.py` | `opal/tools/memory-tool/tests/test_memory_tool.py` | pytest 단위 테스트 88건 |
| `ERROR_CODES` | `opal/tools/memory-tool/memory_tool.py` | 에러 코드 SSOT dict |
| `HISTORY_FIFO_LIMIT` | `opal/tools/memory-tool/memory_tool.py` | 히스토리 FIFO 상수 = 5 |
