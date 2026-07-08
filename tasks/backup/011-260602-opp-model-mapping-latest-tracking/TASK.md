# TASK: OPAL 모델 매핑 최신화 + 최신 추종 전략 도입

> 작성일: 2026-06-02 | 작업 유형: 개선 | 적용 스킬: opp | 모드: agentic
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

OPAL의 플랫폼별 모델 매핑(`light`/`standard`/`advanced` → 실제 모델)을 2026-06 최신 라인업으로 갱신하고, Claude 컬럼처럼 **"최신 추종(부동 별칭)" 전략**을 가능한 플랫폼에 적용하여 stale 재발을 구조적으로 줄인다.

## 배경

최근 LLM 모델이 대거 업그레이드되면서(Gemini 3.x, GPT-5.5 계열, Codex 5.3 계열) OPAL의 비-Claude 모델 매핑이 1세대 이상 뒤처졌다. 특히 OpenAI 컬럼(`gpt-4.1`/`o3`)은 폐기 수준으로 stale하다. Claude 컬럼만 부동 별칭(`haiku`/`sonnet`/`opus`)이라 자동 최신화되는 비대칭이 stale의 근본 원인이다.

## 배경 분석 (대화에서 도출)

PM(대화) 모드에서 현황을 분석하고 웹 검색으로 최신 라인업을 검증했다.

### 현황 — 모델 매핑이 3곳에 분산 (드리프트 리스크)

| # | 위치 | 라인 | 내용 |
|---|------|------|------|
| L-1 | `opal/core/references/opal-model-mapping.md` | §2 표 (L19-25) | SSOT — Claude/Gemini/OpenAI/Codex 4컬럼 |
| L-2 | `scripts/install-mac.sh` | L551-556 (claude/cursor/gemini/codex dict) + L697-700 (codex TOML) | 어댑터 — 실제 플랫폼 config에 모델 ID 주입 |
| L-3 | `opal/core/references/agents.md` | L174-176 | 레벨→모델 변환 규칙 표 (Claude/Cursor/Gemini) |

### 현행 vs 최신 라인업 (2026-06 기준, 웹 검증)

| 레벨 | 플랫폼 | 현행 매핑 | 최신 상태 | 판정 |
|------|--------|----------|----------|------|
| 전체 | Claude | `haiku`/`sonnet`/`opus` (부동 별칭) | 자동 해소 (Haiku 4.5/Sonnet 4.6/Opus 4.8) | ✅ OK — 변경 불요 |
| light/standard/advanced | Gemini | `gemini-2.5-flash-lite`/`flash`/`pro` | Gemini 3.5 Flash GA, 3 Flash, 3.x Pro 출시 | ❌ 1세대+ stale |
| light/standard/advanced | OpenAI | `gpt-4.1-mini`/`gpt-4.1`/`o3` | GPT-5.5 프론티어, o3 사실상 폐기 | ❌ 심각 stale |
| light/standard/advanced | Codex | `gpt-5-mini`/`gpt-5-codex`/`gpt-5.1-codex-max` | GPT-5.5 기본, 5.3-codex 최신 | ⚠️ standard/advanced stale |

### 구조적 발견

1. **버전 핀 전략 비대칭** — Claude만 부동 별칭, 나머지는 구체 버전 핀 → 비-Claude만 매 분기 수동 갱신 필요 (stale 근본 원인)
2. **OpenAI 컬럼 미배선 의혹** — `install-mac.sh`의 platform dict 키는 `claude`/`cursor`/`gemini`/`codex`뿐. `openai` 키 부재 → OpenAI 컬럼은 어디에도 적용되지 않는 "문서상 컬럼"일 가능성 (PLAN에서 확정)

### 웹 검증 출처 (2026-06)

- [Anthropic Models Overview](https://platform.claude.com/docs/en/about-claude/models/overview) — Opus 4.8 / Sonnet 4.6 / Haiku 4.5
- [Gemini API Models](https://ai.google.dev/gemini-api/docs/models) / [Gemini 3.5 Flash](https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash) — `gemini-3.5-flash` GA, `gemini-3-flash`
- [OpenAI All Models](https://developers.openai.com/api/docs/models/all) / [Introducing GPT-5.5](https://openai.com/index/introducing-gpt-5-5/) — GPT-5.5 / 5.4 / 5.3
- [Codex Models](https://developers.openai.com/codex/models) — GPT-5.5 기본, GPT-5.3-Codex

## 확정된 설계 방향 (대화에서 합의)

- **Q1=b**: 중단된 태스크 010 잔재는 그대로 두고 011 진행 (커밋 위생은 별도 처리)
- **Q2=a**: **최신 추종(부동 별칭) 전략 우선** — Claude처럼 비-Claude도 가능한 한 "최신 GA 추종" 방식으로 전환하여 stale 재발을 구조적으로 줄인다. 별칭 미지원 플랫폼은 갱신 운영 규칙 보강으로 보완한다.
- **모드**: agentic — 모든 게이트 PM 자율 통과, CLOSE 진입만 캡틴 승인.

## 요구사항

- [ ] **R-1: Gemini 컬럼 최신화** — `opal-model-mapping.md` §2, `install-mac.sh` gemini dict, `agents.md` 변환 표의 Gemini 값을 2026-06 최신 GA 모델로 갱신한다.
  - 어디에: L-1 §2 표 / L-2 L554 / L-3 L174-176
  - 왜: 2.5 계열은 1세대+ stale (배경 분석)
  - AC: 3곳 모두 Gemini light/standard/advanced 값이 공식 docs([Gemini API Models](https://ai.google.dev/gemini-api/docs/models))에 실재하는 GA 모델 ID로 기재되고, 3곳 값이 서로 일치한다.

- [x] **R-2: OpenAI 컬럼 처리 결정 및 반영** — OpenAI 컬럼이 실제 배선되는지 PLAN에서 확정한 뒤: (a) 배선되면 gpt-5 계열로 갱신, (b) 미배선 "죽은 컬럼"이면 제거하거나 "참조 전용" 명시.
  - 어디에: L-1 §2 표 / (배선 시) L-2 platform dict
  - 왜: `gpt-4.1`/`o3` 심각 stale + 미배선 의혹 (배경 분석)
  - AC: PLAN에서 배선 여부가 코드 근거(`install-mac.sh` 라인 인용)로 판정되고, 그 판정에 따라 OpenAI 컬럼이 갱신되거나 정리(제거/참조전용 표기)된다. 모호한 "죽은 컬럼"이 남지 않는다.

- [x] **R-3: Codex 컬럼 최신화** — standard/advanced를 최신 Codex 모델로 갱신한다.
  - 어디에: L-1 §2 표 / L-2 L555 + L697-700
  - 왜: gpt-5-codex/5.1-codex-max가 GPT-5.5/5.3-codex로 대체됨 (배경 분석)
  - AC: `install-mac.sh` 두 위치(dict + codex TOML map)와 `opal-model-mapping.md` §2의 Codex 값이 공식 docs([Codex Models](https://developers.openai.com/codex/models))에 실재하는 모델 ID로 일치 기재된다.

- [x] **R-4: 최신 추종 전략 도입** — 부동 별칭/최신 alias를 지원하는 플랫폼은 구체 버전 핀 대신 alias를 사용하도록 전환한다. 미지원 플랫폼은 `opal-model-mapping.md` §5 갱신 가이드에 "분기별 점검" 운영 규칙을 보강한다.
  - 어디에: L-1 §2 표 + §5 갱신 가이드라인
  - 왜: Q2=a 합의 — 비대칭 핀 전략이 stale 근본 원인
  - AC: 각 플랫폼별로 "별칭 추종 가능 여부"가 PLAN에서 공식 docs 근거로 판정되고, 가능한 플랫폼은 alias 적용, 불가능한 플랫폼은 §5에 분기 점검 규칙이 명시된다.

- [x] **R-5: 3개 동기화 지점 일치 검증** — L-1/L-2/L-3 세 곳의 매핑 값이 완전히 일치하는지 EXECUTE 후 교차 검증한다.
  - 어디에: L-1, L-2, L-3
  - 왜: 분산된 SSOT 드리프트 방지 (배경 분석 구조적 발견)
  - AC: 세 위치의 동일 레벨·동일 플랫폼 값이 1:1 일치한다 (불일치 0건). 검증 결과를 QA-EXECUTE.md에 기재한다.

- [x] **R-6: 변경이력 기록** — 수정한 참조 문서에 변경이력 행을 추가한다 (일시 KST + 태스크 번호 011).
  - 어디에: `opal-model-mapping.md` 변경이력 표 (+ `agents.md` 변경이력이 있으면)
  - 왜: 프로젝트 금지사항 — 변경이력 누락 금지 (`.opal/AGENT.md` §금지사항)
  - AC: 수정된 각 참조 문서에 v 버전 + `2026-06-02` + "(011)" 표기가 포함된 변경이력 행이 존재한다.

## 제약 조건

- **배포 경계 준수**: `~/.opal/` 배포본을 직접 수정하지 않는다. 항상 프로젝트 소스(`opal/`, `scripts/`)를 수정한 뒤 install로 재배포한다. (`.opal/AGENT.md` §금지사항)
- **플랫폼 분기 격리**: 모델 매핑은 어댑터 계층(`install-mac.sh` `emit_*` / 매핑 dict)에서만 분기한다. 하드코딩 분기를 다른 곳에 추가하지 않는다. (`docs/PROJECT.md` 원칙 3)
- **승인 없는 코드/설정 변경 금지**: EXECUTE 진입은 agentic PM 대행 승인하되, 실제 파일 수정은 워커만 수행한다. (하네스 §1 Guards)
- **정확 ID는 공식 docs 대조 필수**: 모델 ID는 상상/기억 금지 — PLAN/EXECUTE에서 공식 docs를 WebFetch/검색으로 대조해 확정한다. (citation-rules §0)
- **레벨 정의 불변**: `light`/`standard`/`advanced` 3레벨 정의 자체는 변경하지 않는다. (`opal-model-mapping.md` §5)

## 기술 스택

- Markdown (참조 문서), Bash + 임베디드 Python (`install-mac.sh` 어댑터)
- 플랫폼: Claude / Cursor / Gemini / Codex (+ OpenAI 컬럼 처리 결정 대상)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | opal-model-mapping.md | `opal/core/references/opal-model-mapping.md` | 매핑 SSOT (L-1) |
| D-2 | 소스 | install-mac.sh | `scripts/install-mac.sh` | 어댑터 매핑 dict + codex TOML (L-2) |
| D-3 | 설계 | agents.md | `opal/core/references/agents.md` | 레벨→모델 변환 규칙 표 (L-3) |
| D-4 | 설계 | AGENT.md (PM 프로필) | `.opal/AGENT.md` | 배포 경계·변경이력 금지사항 |
| D-5 | 외부 | Gemini API Models | [Gemini API Models](https://ai.google.dev/gemini-api/docs/models) | Gemini 최신 GA ID 대조 |
| D-6 | 외부 | OpenAI All Models | [OpenAI All Models](https://developers.openai.com/api/docs/models/all) | OpenAI 최신 ID 대조 |
| D-7 | 외부 | Codex Models | [Codex Models](https://developers.openai.com/codex/models) | Codex 최신 ID 대조 |
| D-8 | 외부 | Anthropic Models | [Anthropic Models Overview](https://platform.claude.com/docs/en/about-claude/models/overview) | Claude 별칭 추종 확인 |
