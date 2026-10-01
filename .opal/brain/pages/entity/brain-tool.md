---
type: entity
title: brain-tool
module: brain_tool
layer: util
domain: opal-brain
exports:
- cmd_init
- cmd_add_page
- cmd_index
- cmd_log
- cmd_search
- cmd_sync_header
- cmd_lint
- cmd_validate
- cmd_analyze
- cmd_ingest_scan
source_ref: opal/tools/brain-tool/brain_tool.py
header_synced: 2026-06-11
tags:
- tool
- knowledge
sources:
- code:opal/tools/brain-tool/
- task:015
- task:016
- task:035
- task:169
related: [state-tool, opal-brain-system, brain-validate-flatness-enforcement, worktree-close-brain-write-contract]
created: 2026-06-10
updated: '2026-10-01'
status: active
---
# brain-tool

## 개요

OPAL Project Brain 지식 위키를 결정론적으로 집행하는 CLI 도구. 016에서 10개 서브 명령(init/add-page/index/log/search/sync-header/lint/validate/analyze/ingest-scan)으로 확장됐다. index·log·링크 무결성을 도구가 집행하여 LLM의 직접 편집을 차단한다.

## 설계 배경 (WHY)

- **state-tool 패턴 복제**: brain-tool의 본질은 state-tool과 동일하다(마크다운 자산을 결정론적으로 집행). run.sh+venv python 래퍼, ERROR_CODES 카탈로그, KST 타임스탬프(date.js subprocess)를 그대로 차용했다 — 언어 Python 채택 근거.
- **PyYAML 재사용**: frontmatter 파싱에 venv에 이미 있는 PyYAML을 써 추가 의존성이 0이다.
- **집행 경계**: 페이지 본문은 LLM이 작성하지만 index 등록·log append·frontmatter 검증은 brain-tool이 전담한다(SCHEMA §7).
- **단방향 동기화**: sync-header는 code-scan @header → brain entity frontmatter 단방향만 수행한다. brain→코드 역방향 갱신은 금지 — 코드가 SSOT.

## 인터페이스

`~/.opal/tools/brain-tool/run.sh <command> [options]`. 출력 JSON `{ok, command, ...}`, 에러는 ERROR_CODES 카탈로그(14종) 키. lint kind 6종(orphan/stale/broken_link/missing_link/unsourced/contradiction).

016 신규 서브명령:
- `analyze` — code-scan @header 정량 집계(domain별 모듈수·layer 분포·exports·피의존도) → JSON 반환. init 타입 제안의 결정론적 입력.
- `ingest-scan --source docs|skills|tasks|all` — .md 문서·tasks/ 목록을 멱등 skip 판정과 함께 반환. 본문 요약은 LLM, 목록 산출은 도구(결정론적 역할 분리).

035 기능 추가:
- `validate_frontmatter` 선택 필드 평탄성 검사 — `tags`/`sources`/`related`가 flat `string[]`인지 검증. 중첩 리스트·비문자열 요소를 `frontmatter_invalid` violation으로 집행. None·빈 리스트 통과, 기존 검증(필수 5필드·type·status) 불변. (`brain_tool.py:291-299`, 참조: [[brain-validate-flatness-enforcement]])

053 기능 추가:
- `validate_frontmatter` 링크필드(`related`) 검사 — 요소가 위키링크 문법(`[[`/`]]`)이나 `.md` 접미사를 포함하면 `frontmatter_invalid`로 거부한다. 035 평탄성 검사가 놓친 quoted `"[[slug]]"` 사각지대를 닫는다. None·빈 리스트·정상 슬러그는 통과(기존 동작 불변). (`brain_tool.py`, 참조: [[brain-validate-flatness-enforcement]])
- `add-page --related a,b` 플래그 신설 — `tags`/`sources`와 동일한 CSV→평탄 리스트 패턴으로 `related`를 생성한다. 손편집 유인을 줄인다.

169 기능 변경(쓰기 루트 기본값 반전):
- 회고적 학습 쓰기(`add-page`·`update-page`)의 루트 판정 함수 `require_write_root`가 `--allocator-root` 미지정 시 더 이상 워크트리 여부를 검사해 거부하지 않는다. 조회(`require_brain`)와 동일하게 호출 시점의 작업본(task_root, cwd) 자신에 기본 쓰기가 성공한다. `--allocator-root`를 명시하는 경로(다른 루트를 지정할 때 쓰는 기존 기능, `finalize_brain_root` 경유)는 그대로 유지된다(`brain_tool.py:310-334`).
- 이전 가드(`_inside_worktree`로 워크트리 cwd의 기본 쓰기를 전면 거부)는 `worktree.md`의 task root/allocator root 계약(`.opal`을 task_root 쓰기 대상으로 규정)과 모순되는 과잉 일반화로 판단되어 제거됐다 — 유일한 호출처를 잃은 `_inside_worktree` 함수와 `WORKTREE_SEGMENT` 상수도 함께 삭제됐다(죽은 코드 금지). `.opal/MEMORY.json` 쓰기(별도 코드 경로인 `memory-tool`)는 계속 허브 명시 인자로만 수행되며 이 반전의 영향을 받지 않는다(근거: task:169 PLAN D-1·D-2, 회귀 확인). 설계 배경·CLOSE 절차와의 관계는 [[worktree-close-brain-write-contract]] 참조.

## 관련 페이지

- [[state-tool]] — brain-tool이 복제한 원본 패턴
- [[opal-brain-system]] — brain-tool이 집행하는 위키 시스템
- [[brain-validate-flatness-enforcement]] — 035 선택 필드 평탄성 집행 설계 결정
- [[worktree-close-brain-write-contract]] — 169 쓰기 루트 반전이 속한 CLOSE 계약
