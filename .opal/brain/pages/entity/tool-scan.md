---
type: entity
title: tool-scan
tags: [tool, opal-tools, discovery, usage, capability]
sources: [task:044]
related: []
created: 2026-06-26
updated: 2026-06-26
status: active
---

## 개요

PM이 작업 중 필요한 capability(OPAL 도구·MCP·스킬)를 ①상황 기반 검색 → ②권위 출처(live)에서 정확한 사용법 확인 → ③정확히 사용하도록 하는 결정론적 도구다. MAMS cmux 사건(존재하지 않는 서브명령을 추측 호출 → 무분별 Playwright 폴백)의 재발을 방지하기 위해 설계됐다. (근거: task:044 DONE.md §1)

## 책임 (WHAT)

5개 서브명령을 통해 capability discovery와 사용법 확인을 결정론적으로 집행한다.

| 서브명령 | 역할 |
|---------|------|
| `list` | 전체 capability(도구·MCP·스킬) 1줄 purpose만 반환 — usage 텍스트 미주입(thin) |
| `which <상황>` | 상황 키워드 → 후보 capability 목록 + score 반환 |
| `resolve <상황>` | which top-1 → kind별 invoke 형태(shell/ToolSearch/alias/dispatch) + live usage 결합 |
| `usage <도구>` | 대상 도구의 `run.sh --help` 셸을 매 호출 실행(live, 정적 캐시 금지) |
| `check <도구>` | 도구 설치·실행 가능 여부 검사 |

(`opal/tools/tool-scan/tool_scan.py:1`, `opal/tools/tool-scan/lib/federation.py:1`)

## 설계 배경 (WHY)

- **usage SSOT = 도구 자신의 live `--help`**: 사용법 텍스트를 매니페스트·문서에 복사 저장하면 drift가 생긴다. `usage_source` 포인터만 manifest에 두고 매 호출 셸 실행으로 최신 사용법을 가져온다. (근거: task:044 PLAN.md §3.3.2 R-2)
- **thin manifest — 포인터만**: manifest.json에는 7종 OPAL 도구의 메타와 `usage_source` 포인터만 저장한다. usage 본문은 저장하지 않는다(`usage_source.text: null`). (근거: task:044 PLAN.md §3.2.2 MUST)
- **federation 읽기(불파괴)**: MCP 목록은 `mcps.md` 정규식 파싱, 스킬 목록은 `opal-skills-registry.json` json 읽기만 한다. 원본 수정 금지 — 다른 소비자(install·harness)가 사용 중. (근거: `opal/tools/skill-registry/skill-registry.js:64-87`, task:044 PLAN.md §H-1)
- **결정론 라우팅**: 동일 상황 키워드 입력에 동일 후보가 반환되도록 `(-score, kind우선순위, name)` 안정 정렬. (추론: 코드패턴 `opal/tools/tool-scan/tool_scan.py`)
- **cmux `--help` exit0+ok:false 함정 회피**: cmux-tool은 `--help` 시 exit code 0이지만 stdout JSON에 `"ok": false`가 있다. `ok` 필드로 판정하면 오판정 발생 → exit code 기준으로 성공 판정 강제. (근거: `opal/tools/cmux-tool/run.sh:99`, task:044 PLAN.md §H-4)

## 관계 (HOW)

- `opal/tools/tool-scan/manifest.json` — 7종 OPAL 도구 thin SSOT
- `opal/tools/tool-scan/lib/federation.py` — mcps.md·skills-registry.json 읽기 파서
- `opal/core/AGENT.md` 도구 인지 맵 — `tool-scan` 행과 도구 사용 규율 문단이 등록됨
- 설계 원칙 상세: `concept/usage-ssot-live-help-principle.md`, `concept/tool-scan-thin-manifest-federation.md`

## 소스 커버리지

| 식별자 | 경로:줄번호 | 설명 |
|--------|-----------|------|
| `tool_scan.py` | `opal/tools/tool-scan/tool_scan.py:1` | 메인 진입점, 5 argparse 서브명령 |
| `federation.py` | `opal/tools/tool-scan/lib/federation.py:1` | mcps.md·skills-registry.json 읽기 federation |
| `manifest.json` | `opal/tools/tool-scan/manifest.json:1` | thin SSOT — 7 OPAL 도구 포인터 |
| `run.sh` | `opal/tools/tool-scan/run.sh:1` | Bash 래퍼 (venv python 호출) |
