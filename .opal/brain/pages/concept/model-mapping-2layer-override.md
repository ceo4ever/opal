---
type: concept
title: 모델 매핑 2-레이어 오버라이드 (setting.json SSOT + 부트스트랩 step 0 머지)
tags:
  - model
  - mapping
  - setting
  - override
  - bootstrap
sources:
  - task:046
related:
  - model-mapping-latest-tracking
  - opal-bootstrap-skip-gate
created: "2026-06-28"
updated: "2026-06-28"
status: active
---

## 개요

OPAL의 레벨↔모델 매핑(light/standard/advanced ↔ 플랫폼 실모델)은 `setting.json`의 `models` 블록이 SSOT다. 전역(`~/.opal/setting.json`)과 프로젝트(`{프로젝트}/.opal/setting.local.json`) 두 레이어를 **부트스트랩 step 0**에서 셀 단위 deep merge하여 effective setting을 결정한다.

## 결정 배경 (WHY)

기존 레벨↔모델 매핑은 `opal-model-mapping.md` 표와 install 스크립트(`install-mac.sh:563-567`, `:738-741`)에 하드코딩·이중 관리되었다. 사용자가 특정 등급 모델을 바꾸려면 프레임워크 문서를 직접 수정해야 했고, 프로젝트마다 다른 모델을 쓸 수 없었다(근거: task:046 TASK.md §배경). install은 머신 전역으로 실행되어 프로젝트를 알 수 없으므로 프로젝트 단위 오버라이드는 **런타임 해석으로만** 가능하다는 핵심 제약이 도출됐다(근거: task:046 DONE.md §2).

## 결정 내용

| 항목 | 내용 |
|------|------|
| SSOT | `opal/core/setting.default.json` — 실모델명 JSON (Claude/Gemini/OpenAI/Codex/Cursor × light/standard/advanced). install이 `~/.opal/setting.json`에 시드. |
| 머지 방식 | 부트스트랩 step 0: 전역 setting.json `models` 읽기 → 프로젝트 setting.local.json 셀 단위 덮어쓰기(로컬 우선) → effective setting |
| 적용 대상 | effective setting의 `bootstrap`(스킵 게이트) + `models`(모델 매핑) |
| install 경계 | 전역(`~/.opal/`)에만 작용. 프로젝트 베이킹·`setting.local.json` 자동 생성 없음. |
| 설계 진화 | ①provider×등급 오버라이드 → ②inert "default" scaffold → ③"default" 폐기·실모델 SSOT·step0 머지·미설정 오류(최종 v3) |

머지 시점은 **부트스트랩 step 0** — 4개 bootstrapper(`claude-bootstrap.md`, `gemini-bootstrap.md`, `codex-bootstrap.md`, `cursor-bootstrap.mdc`)와 `AGENT.md` Eager step 0 게이트에 반영됨(`opal/core/AGENT.md`, `opal/bootstrapper/*`).

## 영향 범위

- 변경 파일(12): `opal/core/setting.default.json`, `opal/core/AGENT.md`, `opal/core/references/opal-model-mapping.md`, `opal/core/references/opal-harness.md`, `opal/core/references/agents.md`, 4개 bootstrapper, `scripts/install-mac.sh`, `scripts/install/windows.ps1`, `.opal/MEMORY.md`
- 수혜: 사용자가 `~/.opal/setting.json` 또는 `{프로젝트}/.opal/setting.local.json`의 `models` 블록만 편집하면 즉시 모델 오버라이드 적용.

## 관련 페이지

- [[model-mapping-latest-tracking]]
- [[opal-bootstrap-skip-gate]]
