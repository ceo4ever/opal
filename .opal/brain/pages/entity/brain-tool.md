---
type: entity
title: brain-tool
module: brain_tool
layer: util
domain: opal-brain
exports: [cmd_init, cmd_add_page, cmd_index, cmd_log, cmd_search, cmd_sync_header, cmd_lint, cmd_validate, cmd_analyze, cmd_ingest_scan]
source_ref: opal/tools/brain-tool/brain_tool.py
header_synced: 2026-06-11
tags: [tool, knowledge]
sources: [code:opal/tools/brain-tool/, task:015, task:016, task:035]
related: [state-tool, opal-brain-system, brain-validate-flatness-enforcement]
created: 2026-06-10
updated: 2026-06-22
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

## 관련 페이지

- [[state-tool]] — brain-tool이 복제한 원본 패턴
- [[opal-brain-system]] — brain-tool이 집행하는 위키 시스템
- [[brain-validate-flatness-enforcement]] — 035 선택 필드 평탄성 집행 설계 결정
