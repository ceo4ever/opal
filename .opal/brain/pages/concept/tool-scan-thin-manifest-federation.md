---
type: concept
title: tool-scan 매니페스트 thin 설계 + federation 불파괴
tags: [design-principle, tool-scan, manifest, federation, ssot]
sources: [task:044]
related: []
created: 2026-06-26
updated: 2026-06-26
status: active
---

## 개요

tool-scan의 capability 인벤토리는 두 축으로 나뉜다: ① OPAL atomic 도구 7종은 `manifest.json` SSOT(thin, 포인터만) ② MCP·스킬은 기존 `mcps.md`·`opal-skills-registry.json`을 읽기 전용 federation. 두 파일을 복사하거나 수정하지 않으므로 기존 소비자(install·harness)에 영향을 주지 않는다.

## 결정 배경 (WHY)

MCP/스킬 인벤토리는 이미 `mcps.md`(4개 MCP)와 `opal-skills-registry.json`(스킬 레지스트리)에 정의되어 있고, `skill-registry.js`(install 중 사용)가 직접 파싱한다. 중복 저장 시 두 위치가 drift할 위험이 있으며, 원본 파일을 수정하면 install·harness가 파괴될 수 있다. (근거: `opal/tools/skill-registry/skill-registry.js:64-87`, task:044 PLAN.md §H-1)

## 결정 내용

- **manifest.json 저장 대상**: OPAL atomic 도구 7종(xlsx/state/code-scan/cmux/test/brain/tool-scan)만 SSOT. MCP·스킬은 저장하지 않는다.
- **manifest 엔트리 필드**: `name`, `kind`, `purpose`, `when[]`, `exec`, `usage_source`(포인터), `fallback`. usage 본문 텍스트는 저장하지 않는다.
- **federation 읽기 전용**: `mcps.md`는 `## {server}` 섹션 정규식 파싱, `opal-skills-registry.json`은 json 읽기만. 바이트 수준 무변경 보장(MD5 단언).
- **list/resolve 통합**: manifest 도구 + federation MCP/스킬을 통합하여 결과를 반환한다.
- **cmux fallback 계약 명시**: cmux-tool 엔트리는 에러 종류별 폴백 허용 여부를 `fallback` 필드에 명시한다(`cmux_not_installed`=허용, `usage`=금지).

## 영향 범위

- `opal/tools/tool-scan/manifest.json` — thin SSOT 7 엔트리
- `opal/tools/tool-scan/lib/federation.py` — mcps.md·skills-registry.json 읽기 파서
- `opal/core/references/mcps.md`, `opal/core/references/opal-skills-registry.json` — 읽기 전용 입력
