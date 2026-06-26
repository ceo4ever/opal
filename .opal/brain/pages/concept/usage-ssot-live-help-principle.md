---
type: concept
title: 사용법 SSOT는 도구 자신의 live --help
tags: [design-principle, tool-scan, usage, drift, ssot]
sources: [task:044]
related: []
created: 2026-06-26
updated: 2026-06-26
status: active
---

## 개요

도구 사용법 텍스트를 문서·매니페스트·인지 맵 등에 복사 저장하면 도구 업데이트 시 drift가 발생한다. 유일한 SSOT는 도구 자신의 `--help` 출력이며, 매 호출 live 셸 실행으로 가져오는 것이 drift 표면을 0에 가깝게 만드는 방법이다.

## 결정 배경 (WHY)

tool-scan 설계 시 사용법 저장 방식을 논의했다. 선택지는 ① manifest에 usage 텍스트 inline 저장 ② 정적 캐시 파일 ③ 매 호출 live 셸 실행이었다. ①·②는 도구 `--help` 변경 시 저장본이 stale 되는 drift 문제가 구조적으로 내재한다. ③은 호출 비용이 있지만 항상 최신 사용법을 보장하며 drift 표면이 도구 추가/제거 시에만 나타난다. (근거: task:044 PLAN.md §3.3.2, TASK.md R-2)

## 결정 내용

- `tool-scan usage <도구>` 서브명령은 `~/.opal/tools/<name>/run.sh --help`를 매 호출 셸 실행(subprocess)한다.
- manifest.json의 `usage_source.text`는 반드시 `null`이어야 한다(`inline` 타입 단순 도구 예외).
- 성공 판정은 exit code(returncode==0) 기준 — `ok` 필드 기준 금지(cmux `ok:false+exit0` 함정).
- stdout이 JSON이면 `usage_json`, 텍스트면 `usage_text` 원문으로 반환. `live:true` 명시.
- 외부 CLI는 stderr로만 help를 출력하는 경우가 있으므로 stdout+stderr 병합 캡처 필수.

## 영향 범위

- `opal/tools/tool-scan/tool_scan.py` — `cmd_usage`, `_resolve_usage` 핸들러
- `opal/tools/tool-scan/manifest.json` — `usage_source.text: null` 강제
- `opal/core/AGENT.md` 인지 맵 — "사용법 선확인" 규율 문단
