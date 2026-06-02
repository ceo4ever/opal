# PLAN: OPAL 모델 매핑 최신화 + 최신 추종 전략 도입

> 작성일: 2026-06-02 | 모드: agentic | 파이프라인: opp
> 입력: `tasks/011-260602-opp-model-mapping-latest-tracking/TASK.md`
> 출력: PLAN.md

---

## 1. 현황 조사

### 참조 문서 (PLAN 작성 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | opal-model-mapping.md | `opal/core/references/opal-model-mapping.md` | 매핑 SSOT (L-1) §2 표·§5 갱신 가이드·변경이력 |
| D-2 | 소스 | install-mac.sh | `scripts/install-mac.sh` | 어댑터 매핑 dict(L551-556) + codex TOML map(L697-700) + 기본값(L743) |
| D-3 | 설계 | agents.md | `opal/core/references/agents.md` | 레벨→모델 변환 규칙 표 (L-3, L170-182) |
| D-4 | 설계 | AGENT.md (PM 프로필) | `.opal/AGENT.md` | 배포 경계·변경이력·플랫폼 분기 격리 금지사항 |
| D-5 | 외부 | Gemini API Models | [Gemini API Models](https://ai.google.dev/gemini-api/docs/models) | Gemini 최신 GA ID + `-latest` 부동 별칭 대조 |
| D-6 | 외부 | OpenAI All Models | [OpenAI All Models](https://developers.openai.com/api/docs/models/all) | OpenAI 최신 ID + gpt-4.1/o3 상태 대조 |
| D-7 | 외부 | Codex Models | [Codex Models](https://developers.openai.com/codex/models) | Codex 최신 ID + 기본 모델 대조 |
| D-8 | 외부 | Anthropic Models | [Anthropic Models Overview](https://platform.claude.com/docs/en/about-claude/models/overview) | Claude 별칭 추종 + 핀 정책 확인 |
| D-9 | 외부 | Claude Code Model Config | [Claude Code Model configuration](https://code.claude.com/docs/en/model-config) | Claude Code CLI `haiku/sonnet/opus` 슬러그 추종 확인 |
| D-10 | 소스 | windows.ps1 | `scripts/install/windows.ps1` | **신규 발견** — Windows 설치기 내 4번째 매핑 동기화 지점(L1302-1335) |
| D-11 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | 변경이력·네이밍·[MUST] 규칙 |
| D-12 | 외부 | Gemini API Changelog | [Gemini API Changelog](https://ai.google.dev/gemini-api/docs/changelog) | **QA Critical 해소** — 2026-01-21 "`gemini-pro-latest`/`gemini-flash-latest` 별칭" 실재 확정 |
| D-13 | 외부 | Firebase AI Logic Models | [Firebase AI Logic Models](https://firebase.google.com/docs/ai-logic/models) | flash-lite stable GA `gemini-3.1-flash-lite`(2026-05-07) 확인 + `gemini-flash-lite-latest` 미존재 확인 |

### [MUST] 필수 제약 인용 (재해석 금지)

- [MUST] `.opal/AGENT.md` §금지사항: "`~/.opal/` 직접 편집 금지 — 항상 프로젝트 소스를 수정한 후 install로 배포한다." → 변경 대상은 `opal/core/...`, `scripts/...` 소스 한정. `~/.opal/...` 배포본은 건드리지 않는다.
- [MUST] `.opal/AGENT.md` §금지사항: "변경이력 누락 금지 — 스킬·에이전트·참조 문서 수정 시 변경이력 표 행 추가 의무." (→ R-6)
- [MUST] `.opal/AGENT.md` §금지사항: "하드코딩된 플랫폼 분기 추가 금지 — Claude/Cursor/Gemini 분기는 어댑터 계층(install·plugin)에서만 수행한다." → 신규 분기 추가 없이 기존 어댑터 매핑 dict 값만 치환한다.
- [MUST] `opal/core/references/harness/citation-rules.md` §0: "상상·추정·기억 기반 기재 금지 — 모든 분석·설계 결정은 문서 근거를 인용해야 한다." → 모든 모델 ID는 공식 docs(D-5~D-9) WebFetch 대조로 확정 (§2 M-1).
- [MUST] `docs/CONVENTIONS.md` §변경이력: "스킬, 에이전트, 참조 문서의 변경이력은 일시(KST)를 포함한다 | 버전 | 일시 | 변경내용 |" → 변경이력 행은 KST 일시 + 태스크 번호(011) 포함.
- [MUST] `docs/CONVENTIONS.md` §파일/폴더 이름: "English, kebab-case (Python 파일은 snake_case)" — 본 태스크는 신규 파일 없음(전부 기존 파일 수정)이므로 네이밍 영향 없음.

### 관련 파일

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| `opal/core/references/opal-model-mapping.md` | 매핑 SSOT (L-1) | O | `opal/core/references/opal-model-mapping.md:19-23`(§2 표), `:32-34`(공식 URL), `:68-74`(§5 갱신 가이드), `:80-84`(변경이력) |
| `scripts/install-mac.sh` | macOS 어댑터 (L-2) | O | `scripts/install-mac.sh:551-556`(platform dict), `:697-700`(codex TOML map), `:743`(기본값) |
| `opal/core/references/agents.md` | 레벨→모델 변환 규칙 표 (L-3) | O | `opal/core/references/agents.md:174-176`(변환 표), `:310-317`(변경이력) |
| `scripts/install/windows.ps1` | **Windows 어댑터 (L-4, 신규 발견)** | O | `scripts/install/windows.ps1:1302-1317`(ModelMap), `:1335`(toml 기본값) |
| `.opal/MEMORY.md` | 프로젝트 메모리 (009 행에 모델 ID 흔적) | X(참조 전용) | `.opal/MEMORY.md:42`(009 변경 요약, 과거 이력이므로 소급 변경 안 함) |

### 현재 상태 (직접 Read 결과)

**3곳 분산 SSOT — 실제로는 4곳 (드리프트 리스크 확대)**

| 지점 | 위치 | 현행 값 |
|------|------|--------|
| L-1 | `opal-model-mapping.md:19-23` | Claude `haiku/sonnet/opus`, Gemini `gemini-2.5-flash-lite/flash/pro`, OpenAI `gpt-4.1-mini/gpt-4.1/o3`, Codex `gpt-5-mini/gpt-5-codex/gpt-5.1-codex-max` |
| L-2a | `install-mac.sh:551-556` | `mapping` dict — 키 = `claude`/`cursor`/`gemini`/`codex` **(`openai` 키 부재)**. gemini=`2.5-flash-lite/flash/pro`, codex=`gpt-5-mini/gpt-5-codex/gpt-5.1-codex-max`, cursor=`inherit` (→ D-2:551-556) |
| L-2b | `install-mac.sh:697-700,743` | codex TOML map = `gpt-5-mini/gpt-5-codex/gpt-5.1-codex-max`, 기본값 `gpt-5-codex` (→ D-2:697-700) |
| L-3 | `agents.md:174-176` | Claude `haiku/sonnet/opus`, Cursor `inherit`, Gemini `gemini-2.5-flash-lite/flash/pro` (OpenAI/Codex 컬럼 없음 — 이 표는 Claude/Cursor/Gemini 3컬럼) |
| **L-4** | `windows.ps1:1302-1317,1335` | **install-mac.sh와 동일 값** ModelMap (claude/cursor/gemini/codex) + toml 기본값 `gpt-5-codex` (→ D-10) |

**R-2 OpenAI 컬럼 배선 여부 — 코드로 확정 (미배선 "죽은 컬럼")**

- `install-mac.sh:557` `model_value = mapping.get(platform, {}).get(opal_model, 'inherit')` — `platform`은 `emit_platform_agent_adapter`의 3번째 인자(`:456` `local platform="$3"`)로 주입된다 (→ D-2:456,557).
- 호출처는 4곳뿐: `:612`(`"claude"`), `:634`(`"cursor"`), `:656`(`"gemini"`), 그리고 codex는 별도 `install_codex_agents`(TOML 경로). `"openai"`를 인자로 넘기는 호출처가 코드 전체에 **존재하지 않음** (→ D-2:608-660).
- 결론: `mapping` dict에 `openai` 키가 없고(`:551-556`), 어떤 호출도 `platform="openai"`를 넘기지 않으므로 **OpenAI 컬럼은 어떤 플랫폼 config에도 주입되지 않는 문서상 죽은 컬럼**이다. windows.ps1도 동일(claude/cursor/gemini/codex만, openai 부재 — D-10).

**Claude 별칭 추종 — 현행 유지 근거 확인**

- Anthropic API에서 모델 ID는 핀 스냅샷이다: [Anthropic Models Overview](https://platform.claude.com/docs/en/about-claude/models/overview): "Starting with the Claude 4.6 generation, model IDs use a dateless format that is also a pinned snapshot, not an evergreen pointer."
- 그러나 OPAL이 쓰는 값은 **Claude Code CLI의 슬러그**(`haiku`/`sonnet`/`opus`)이며, CLI 슬러그는 부동이다: [Claude Code Model configuration](https://code.claude.com/docs/en/model-config) — "aliases (sonnet, opus, haiku) resolve to the latest version ... update over time." 현재 `opus`→Opus 4.8, `sonnet`→Sonnet 4.6, `haiku`→Haiku 4.5로 해소 (→ D-8, D-9). **변경 불요.**

### 영향 범위

- 모델 ID 문자열 치환은 **값 교체**만 발생하며 코드 로직/구조 변경 없음 → 회귀 위험 낮음.
- 단, **동기화 지점이 TASK 배경 분석의 3곳이 아니라 4곳**(windows.ps1 추가)이므로 R-5 교차검증 범위를 4곳으로 확대해야 함 (§5 리스크 R-T1).
- OpenAI 컬럼 처리(제거 vs 참조전용)는 SSOT 표 구조에 영향 → §2 M-2에서 결정.

---

## 2. 구현 계획 — 의사결정 (M-1 ~ M-5)

### M-1: 정확 모델 ID 확정 (공식 docs WebFetch 대조 완료)

각 플랫폼 light/standard/advanced에 들어갈 2026-06 모델 ID를 공식 docs로 대조 확정했다. 미검증 ID는 채택하지 않는다 ([MUST] citation-rules §0).

| 레벨 | Claude (D-8/D-9) | Gemini (D-5) | Codex (D-7) | 비고 |
|------|------|--------|-------|------|
| `light` | `haiku` (CLI 슬러그, 부동) | `gemini-3.1-flash-lite` (핀 — `-latest` 별칭 미존재) | `gpt-5.4-mini` | |
| `standard` | `sonnet` (CLI 슬러그, 부동) | `gemini-flash-latest` | `gpt-5.5` | Codex 기본 권장 모델 |
| `advanced` | `opus` (CLI 슬러그, 부동) | `gemini-pro-latest` | `gpt-5.3-codex` | |

근거:
- **Gemini** (PM이 공식 docs 3종 직접 대조 — QA Critical 해소): `-latest` 부동 별칭은 **flash·pro 2종만 실재**한다. [Gemini API Changelog](https://ai.google.dev/gemini-api/docs/changelog) 2026-01-21: "Changed the `latest` aliases: `gemini-pro-latest` switched to `gemini-3-pro-preview`, `gemini-flash-latest` switched to `gemini-3-flash-preview`" → `gemini-pro-latest`·`gemini-flash-latest` **실재 확정**. 반면 `gemini-flash-lite-latest`는 changelog·models 페이지·[Firebase AI Logic Models](https://firebase.google.com/docs/ai-logic/models) 어디에도 없어 **미존재**로 판정. flash-lite 현행 stable GA는 `gemini-3.1-flash-lite`(2026-05-07 출시 — Firebase docs 확인). 따라서:
  - light = `gemini-3.1-flash-lite` (**핀** — flash-lite는 `-latest` 별칭 미존재. §5 분기점검 대상에 포함)
  - standard = `gemini-flash-latest` (부동 별칭, 현재 `gemini-3-flash-preview` 지시)
  - advanced = `gemini-pro-latest` (부동 별칭, 현재 `gemini-3-pro-preview` 지시)
- **Codex**: "For most tasks in Codex, start with `gpt-5.5`" → standard=`gpt-5.5`. 최신 코딩 특화 = `gpt-5.3-codex`("industry-leading coding model") → advanced. light(mini) = `gpt-5.4-mini`("fast, efficient mini model"; codex 권장 목록에 실재). 현행 `gpt-5-mini`/`gpt-5-codex`/`gpt-5.1-codex-max`는 권장 목록에서 사라졌거나 구세대 (→ D-7).
- **OpenAI(참조용)**: `gpt-5.5`/`gpt-5.5-mini`(검색 결과상 `gpt-5.4-mini`/`gpt-5.4-nano` 등) 프론티어 라인업 확인, `gpt-4.1`/`o3`는 "succeeded by GPT-5"로 사실상 레거시 (→ D-6). → M-2 처리.
- **Claude**: 변경 불요 (현황 조사 근거).

> **부동 별칭 GA/preview 트레이드오프**: `gemini-pro-latest`는 현 시점 preview 빌드(`gemini-3.1-pro-preview`)를 가리킬 수 있다. 이는 "구체 preview ID 핀"보다 안전하다(자동 추종으로 GA 승격 시 즉시 반영). preview 채택 리스크는 §5 R-T2에 기재.

### M-2: R-2 OpenAI 컬럼 운명 — "참조 전용(install 미연동)" 명시로 결정

코드 근거(현황 조사 §R-2)상 OpenAI 컬럼은 **미배선 죽은 컬럼**이다. 처리 옵션 (a)제거 / (b)참조전용 명시 중 **(b) 참조 전용 표기 + 최신 GPT-5.x로 값 갱신**을 채택한다.

- 사유: ① 완전 제거 시 "OpenAI를 지원하지 않는다"는 잘못된 신호. 실제로는 Codex가 OpenAI 모델(gpt-5.x)을 ChatGPT-auth로 사용하며, 향후 순수 OpenAI API 어댑터 추가 가능성 존재. ② SSOT는 "참조 전용 문서"로 명시돼 있으므로(`opal-model-mapping.md:2`) 참조 가치가 있는 정보는 보존하되 **install 미연동임을 명확히 표기**하여 "모호한 죽은 컬럼"을 제거한다 ([MUST] R-2 AC: "모호한 죽은 컬럼이 남지 않는다").
- 반영: §2 표의 OpenAI 컬럼 값을 `gpt-5.4-mini`/`gpt-5.5`/`gpt-5.3` 등 최신으로 갱신하고, 표 하단 각주에 **"OpenAI 컬럼 = 참조 전용 — install 어댑터 미연동(`install-mac.sh` mapping dict에 `openai` 키 없음). Codex 경로가 OpenAI 모델을 ChatGPT-auth로 사용."** 명시. `install-mac.sh`/`windows.ps1`에는 OpenAI 키를 **추가하지 않는다** ([MUST] AGENT.md: 하드코딩 분기 신규 추가 금지).

> OpenAI 컬럼 값 확정: light=`gpt-5.4-mini`, standard=`gpt-5.5`, advanced=`gpt-5.3` — 모두 D-6 실재 ID. (참조 전용이므로 install 영향 없음.)

### M-3: R-4 별칭 추종 가능 여부 (플랫폼별 판정)

| 플랫폼 | 부동 별칭 지원? | 근거 | 채택 전략 |
|--------|--------------|------|----------|
| Claude | O (CLI 슬러그 부동) | [Claude Code Model config](https://code.claude.com/docs/en/model-config): "aliases resolve to the latest version" (→ D-9) | 현행 `haiku/sonnet/opus` 유지 (이미 부동) |
| Gemini | △ 부분 (flash/pro만 `-latest` 실재, flash-lite 미존재) | [Gemini API Changelog](https://ai.google.dev/gemini-api/docs/changelog) 2026-01-21: `gemini-pro-latest`/`gemini-flash-latest` 별칭 명시. flash-lite-latest는 changelog·Firebase docs 모두 부재 (→ D-12/D-13) | standard/advanced = `gemini-flash-latest`/`gemini-pro-latest` 별칭 / light = `gemini-3.1-flash-lite` 핀 (별칭 미존재 → §5 분기점검) |
| Codex | X (부동 별칭 없음) | [Codex Models](https://developers.openai.com/codex/models): "No latest alias is mentioned ... requires explicit specification" (→ D-7) | 구체 ID 핀 + §5 갱신 가이드에 "분기별 점검" 운영 규칙 보강 |
| OpenAI | X (latest alias 없음) | [OpenAI All Models](https://developers.openai.com/api/docs/models/all): "No floating `latest` alias exists for general chat models" (→ D-6) | (참조 전용이라 install 영향 없음) §5 점검 규칙 대상 |
| Cursor | N/A | 사용자 IDE 위임 `inherit` (→ D-1 §4) | 현행 `inherit` 유지 |

결론(Q2=a 합의 충족): Claude(`haiku/sonnet/opus`)·Gemini standard/advanced(`gemini-flash-latest`/`gemini-pro-latest`)는 **부동 별칭 채택**으로 stale 자동 해소. 별칭이 없는 **Gemini light(flash-lite)·Codex·OpenAI**는 구체 ID 핀 + **§5 갱신 가이드에 "분기마다 공식 docs 점검" 운영 규칙 보강**으로 대체 (R-4 AC 충족 — "가능한 플랫폼은 alias, 불가능하면 §5 분기 점검").

### M-4: 변경 범위 확정 (수정 파일 + 위치)

| 파일 | 변경 위치 | 변경 내용 |
|------|----------|----------|
| D-1 `opal-model-mapping.md` | §2 표(`:19-23`) | Gemini 3값 → `-latest` 별칭, OpenAI 3값 → gpt-5.x + 참조전용 각주, Codex 3값 → gpt-5.4-mini/gpt-5.5/gpt-5.3-codex |
| D-1 | §2 공식 URL 표(`:32-34`) | Codex URL을 config-reference → [Codex Models](https://developers.openai.com/codex/models)로 정합 (선택, 정확도 개선) |
| D-1 | §5 갱신 가이드(`:68-74`) | "부동 별칭 우선(Claude/Gemini) + Codex/OpenAI 분기별 점검" 운영 규칙 추가 |
| D-1 | 변경이력(`:80-84`) | v1.3 행 추가 (R-6) |
| D-2 `install-mac.sh` | dict(`:554-555`) | gemini 3값 → `-latest`, codex 3값 → 최신. **openai 키 추가 안 함** |
| D-2 | codex TOML map(`:698-700`) + 기본값(`:743`) | 최신 codex ID로 치환 (기본값 `gpt-5-codex`→`gpt-5.5`) |
| D-3 `agents.md` | 변환 표(`:174-176`) | Gemini 3값 → `-latest` 별칭 (Claude/Cursor 컬럼 불변) |
| D-3 | 변경이력(`:310-317`) | v1.5 행 추가 (R-6) |
| D-10 `windows.ps1` | ModelMap(`:1312`,`:1317`) + 기본값(`:1335`) | install-mac.sh와 동일 값으로 동기 (R-5 4번째 지점) |

### M-5: docs/ 갱신 필요 여부 — 불요

`docs/PROJECT.md`/`ARCHITECTURE.md`/`CONVENTIONS.md`는 모델 ID 자체를 담지 않는다(어댑터 격리 원칙만 서술). 모델 값 치환은 docs/ 내용에 영향 없음 → docs/ 갱신 Step 추가하지 않음.

### 파일 변경 계획

#### 신규 생성
| # | 파일 경로 | 역할 | 근거 |
|---|----------|------|------|
| - | (없음) | - | - |

#### 수정
| # | 파일 경로 | 변경 내용 | 근거 |
|---|----------|----------|------|
| 1 | `opal/core/references/opal-model-mapping.md` | §2 표 4컬럼 갱신 + OpenAI 참조전용 각주 + §5 운영 규칙 보강 + 변경이력 | M-1/M-2/M-3 (→ D-1:19-23,68-74,80-84) |
| 2 | `scripts/install-mac.sh` | gemini dict `-latest`, codex dict+TOML map+기본값 최신화 | M-1/M-4 (→ D-2:554-555,698-700,743) |
| 3 | `opal/core/references/agents.md` | Gemini 변환 표 `-latest` + 변경이력 | M-1/M-4 (→ D-3:174-176,310-317) |
| 4 | `scripts/install/windows.ps1` | ModelMap gemini/codex 동기 + 기본값 | M-4/R-5 (→ D-10:1312,1317,1335) |

#### 삭제
| # | 파일 경로 | 사유 |
|---|----------|------|
| - | (없음) | OpenAI 컬럼은 제거가 아닌 "참조 전용" 표기로 처리 (M-2) |

### 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | SSOT 표/가이드/이력 갱신 | `opal-model-mapping.md` | 중 (구조+각주+이력) |
| 2 | macOS 어댑터 값 치환 | `install-mac.sh` | 하 (3위치 문자열) |
| 3 | Windows 어댑터 값 치환 | `windows.ps1` | 하 (2위치 문자열) |
| 4 | agents.md 변환 표 + 이력 | `agents.md` | 하 |
| 5 | 4곳 동기화 교차 검증 (R-5) | 전체 | 중 (grep 대조) |

> SSOT(D-1)를 먼저 확정한 뒤 어댑터·표를 그에 맞춘다(SSOT가 상위 레이어). Step 1~4는 서로 다른 파일이라 병렬 가능하나, 값 정합성 보장을 위해 Step 1 확정 후 2~4를 동일 값으로 일괄 적용한다.

### 핵심 설계 (파일별 명세)

**파일 1 — `opal/core/references/opal-model-mapping.md`**
- §2 표(`:21-23`)를 아래로 치환 (→ D-5/D-6/D-7):
  - `light`: `haiku` | `gemini-3.1-flash-lite` | `gpt-5.4-mini` | `gpt-5.4-mini`
  - `standard`: `sonnet` | `gemini-flash-latest` | `gpt-5.5` | `gpt-5.5`
  - `advanced`: `opus` | `gemini-pro-latest` | `gpt-5.3` | `gpt-5.3-codex`
- §2 표 하단 각주 추가: "OpenAI 컬럼 = 참조 전용(install 어댑터 미연동) — `install-mac.sh` mapping dict에 `openai` 키 없음(→ D-2:551-556). Codex 경로가 OpenAI 모델을 ChatGPT-auth로 사용." (M-2)
- §5(`:68-74`)에 운영 규칙 추가: "Claude(`haiku/sonnet/opus`)·Gemini standard/advanced(`gemini-flash-latest`/`gemini-pro-latest`)는 부동 별칭으로 자동 추종 → 갱신 불요. **별칭이 없는 Gemini light(`gemini-3.1-flash-lite`)·Codex·OpenAI는 분기마다 [Gemini API Models](https://ai.google.dev/gemini-api/docs/models)/[Codex Models](https://developers.openai.com/codex/models)/[OpenAI All Models](https://developers.openai.com/api/docs/models/all) 점검 후 핀 갱신.**" (M-3)
- 변경이력 v1.3 행 추가: `| v1.3 | 2026-06-02 (KST 시각) | Gemini 부동 별칭 전환 + Codex 최신화 + OpenAI 참조전용 명시 + 최신 추종 운영 규칙 보강 (011) |` ([MUST] CONVENTIONS §변경이력)

**파일 2 — `scripts/install-mac.sh`** ([MUST] AGENT.md: openai 키 신규 추가 금지)
- `:554` gemini dict → `{'light': 'gemini-3.1-flash-lite', 'standard': 'gemini-flash-latest', 'advanced': 'gemini-pro-latest'}`
- `:555` codex dict → `{'light': 'gpt-5.4-mini', 'standard': 'gpt-5.5', 'advanced': 'gpt-5.3-codex'}`
- `:698-700` codex TOML map → 동일 3값
- `:743` 기본값 `'gpt-5-codex'` → `'gpt-5.5'`
- 파일 상단 변경이력 주석(`:9` 근방 형식)에 `v2.7 2026-06-02: 모델 매핑 최신화 (011)` 행 추가 (R-6)

**파일 3 — `opal/core/references/agents.md`**
- `:174-176` Gemini 컬럼만 `-latest` 별칭으로 치환 (Claude `haiku/sonnet/opus`, Cursor `inherit` 불변):
  - `model: light` → `model: gemini-3.1-flash-lite`
  - `model: standard` → `model: gemini-flash-latest`
  - `model: advanced` → `model: gemini-pro-latest`
- 변경이력(`:316` 다음) v1.5 행 추가: `| v1.5 | 2026-06-02 (KST 시각) | Gemini 변환 표 부동 별칭 전환 (011) |` ([MUST] CONVENTIONS §변경이력)

**파일 4 — `scripts/install/windows.ps1`**
- `:1312` ModelMap gemini → `@{ light = 'gemini-3.1-flash-lite'; standard = 'gemini-flash-latest'; advanced = 'gemini-pro-latest' }`
- `:1317` ModelMap codex → `@{ light = 'gpt-5.4-mini'; standard = 'gpt-5.5'; advanced = 'gpt-5.3-codex' }`
- `:1335` toml 기본값 `'gpt-5-codex'` → `'gpt-5.5'`
- (windows.ps1에 변경이력 표/주석 형식이 있으면 011 행 추가, 없으면 스킵 — EXECUTE 워커가 파일 헤더 확인 후 판단)

---

## 3. 설계 상세 — 최종 매핑 + 요구사항 충족 매핑

### 최종 확정 매핑 테이블 (4곳 동기화 대상 값)

| 레벨 | Claude | Gemini | OpenAI (참조전용) | Codex |
|------|--------|--------|--------|-------|
| `light` | `haiku` | `gemini-3.1-flash-lite` | `gpt-5.4-mini` | `gpt-5.4-mini` |
| `standard` | `sonnet` | `gemini-flash-latest` | `gpt-5.5` | `gpt-5.5` |
| `advanced` | `opus` | `gemini-pro-latest` | `gpt-5.3` | `gpt-5.3-codex` |

> install 연동 컬럼 = Claude/Cursor(`inherit`)/Gemini/Codex. OpenAI 컬럼은 SSOT 참조 전용(install 미연동).

### 요구사항 충족 매핑

| 요구사항 | 충족 방법 | Step |
|---------|----------|------|
| R-1 Gemini 최신화 | standard/advanced=`-latest` 부동 별칭(D-12 changelog 실재), light=`gemini-3.1-flash-lite` 핀(D-13 실재, 별칭 미존재) — 4곳 동기 | 1,2,3,4 |
| R-2 OpenAI 처리 | 코드 근거로 미배선 판정(M-2) → 참조전용 각주 + gpt-5.x 갱신 | 1 |
| R-3 Codex 최신화 | dict+TOML+기본값 3위치 + SSOT를 gpt-5.4-mini/gpt-5.5/gpt-5.3-codex로 (D-7 실재) | 1,2,4 |
| R-4 최신 추종 전략 | Claude + Gemini flash/pro 별칭 채택 + Gemini flash-lite/Codex/OpenAI §5 분기점검 규칙(M-3) | 1,2,3,4 |
| R-5 4곳 동기 검증 | grep 교차 대조 (3곳→4곳 확대) | 5 |
| R-6 변경이력 | D-1 v1.3 / D-3 v1.5 / install-mac.sh 헤더 / (windows.ps1 해당 시) | 1,2,3,4 |

---

## 4. 실행 체크리스트

> 총 5개 Step | Phase 3개
>
> | Phase | Step | 실행 | 비고 |
> |-------|------|------|------|
> | 1 | 1 | 순차 | SSOT 확정 (상위 레이어, 값 기준점) |
> | 2 | 2, 3, 4 | 병렬 | 서로 다른 파일, Step 1 값 기준으로 동기 |
> | 3 | 5 | 순차 | 1~4 완료 후 교차 검증 |
>
> 모든 EXECUTE Step의 **agent = `opal-task-agent`** (Framework 영역: 문서·스크립트. FE/BE/DB 해당 없음).

### Step 1: SSOT(opal-model-mapping.md) 갱신
- [ ] 완료
- **파일**: `opal/core/references/opal-model-mapping.md`
- **agent**: `opal-task-agent`
- **작업 내용**: §2 표(`:21-23`) 4컬럼을 §3 최종 매핑 값으로 치환 / OpenAI 참조전용 각주 추가(M-2) / §5(`:68-74`)에 "Claude·Gemini(flash/pro) 부동 별칭 자동 추종 + Gemini light(flash-lite)·Codex·OpenAI 분기점검" 운영 규칙 추가(M-3) / 변경이력 v1.3 행(2026-06-02 KST + 011) 추가
- **완료 기준**: §2 표 값이 §3 매핑과 1:1 일치 / OpenAI 각주 존재 / §5 운영 규칙 존재 / 변경이력 v1.3 행 존재
- **테스트**: `grep -nE "gemini-3\.1-flash-lite|gemini-flash-latest|gemini-pro-latest|gpt-5\.(4|5|3)" opal/core/references/opal-model-mapping.md`로 신값 확인, 구값(`gemini-2.5`/`gpt-4.1`/`o3`/`gpt-5-codex`/`gpt-5.1-codex`) 0건 확인
- **의존**: 없음

### Step 2: install-mac.sh 어댑터 값 치환
- [ ] 완료
- **파일**: `scripts/install-mac.sh`
- **agent**: `opal-task-agent`
- **작업 내용**: `:554` gemini dict → §3 3값(light=`gemini-3.1-flash-lite` 핀, standard/advanced=`-latest` 별칭) / `:555` codex dict → 최신 3값 / `:698-700` codex TOML map → 동일 / `:743` 기본값 `gpt-5-codex`→`gpt-5.5` / 파일 상단 변경이력 주석 v2.7(011) 추가. **`openai` 키 추가 금지**([MUST] AGENT.md 하드코딩 분기 금지)
- **완료 기준**: 두 매핑 위치 + 기본값이 §3 Codex/Gemini 값과 일치 / mapping dict 키가 여전히 claude/cursor/gemini/codex 4개(openai 미추가) / bash 문법 오류 없음
- **테스트**: `bash -n scripts/install-mac.sh` 통과 / `grep -nE "gemini-2.5|gpt-4.1|o3|gpt-5-codex|gpt-5.1-codex" scripts/install-mac.sh` 0건
- **의존**: Step 1 (값 기준)

### Step 3: agents.md 변환 표 갱신
- [ ] 완료
- **파일**: `opal/core/references/agents.md`
- **agent**: `opal-task-agent`
- **작업 내용**: `:174-176` Gemini 컬럼을 §3 3값(light=`gemini-3.1-flash-lite`, standard=`gemini-flash-latest`, advanced=`gemini-pro-latest`)으로 치환(Claude/Cursor 불변) / 변경이력 v1.5 행(2026-06-02 KST + 011) 추가
- **완료 기준**: Gemini 3값이 §3과 일치 / Claude(`haiku/sonnet/opus`)·Cursor(`inherit`) 불변 / 변경이력 v1.5 행 존재
- **테스트**: `grep -n "gemini-" opal/core/references/agents.md`로 §3 3값 확인, `gemini-2.5` 0건
- **의존**: Step 1 (값 기준)

### Step 4: windows.ps1 어댑터 동기
- [ ] 완료
- **파일**: `scripts/install/windows.ps1`
- **agent**: `opal-task-agent`
- **작업 내용**: `:1312` gemini ModelMap → §3 3값(light=`gemini-3.1-flash-lite`, standard/advanced=`-latest` 별칭) / `:1317` codex ModelMap → 최신 / `:1335` toml 기본값 `gpt-5-codex`→`gpt-5.5` / 파일에 변경이력 주석·표 있으면 011 행 추가
- **완료 기준**: gemini/codex ModelMap + 기본값이 install-mac.sh와 1:1 일치
- **테스트**: `grep -nE "gemini-2.5|gpt-4.1|o3|gpt-5-codex|gpt-5.1-codex" scripts/install/windows.ps1` 0건 / install-mac.sh 값과 수기 대조
- **의존**: Step 1 (값 기준), Step 2 (값 정합 기준선)

### Step 5: 4곳 동기화 교차 검증 (R-5)
- [ ] 완료
- **파일**: 전체 (검증 전용 — 수정 없음)
- **agent**: `opal-task-agent`
- **작업 내용**: L-1(SSOT §2 install연동 컬럼)/L-2a(install-mac dict)/L-2b(install-mac codex TOML)/L-3(agents.md Gemini)/L-4(windows.ps1)에서 동일 레벨·동일 플랫폼 값이 1:1 일치하는지 grep 대조. 불일치 발견 시 SSOT(L-1) 기준으로 정정. 검증 결과를 QA-EXECUTE.md에 기재
- **완료 기준**: install 연동 컬럼(Claude/Cursor/Gemini/Codex) 값이 4(+1)곳에서 불일치 0건. (OpenAI는 L-1에만 존재 — 검증 제외)
- **테스트**: `grep -rnE "gemini-3\.1-flash-lite|gemini-flash-latest|gemini-pro-latest|gpt-5\.(4-mini|5)|gpt-5\.3-codex" opal/core/references/opal-model-mapping.md opal/core/references/agents.md scripts/install-mac.sh scripts/install/windows.ps1` — 각 위치 값 수기 대조표 작성
- **의존**: Step 1,2,3,4

---

## 5. QA 체크리스트

### 기능 테스트
- [x] R-1: 4곳 Gemini 값이 §3 매핑(light=`gemini-3.1-flash-lite` 핀 / standard=`gemini-flash-latest` / advanced=`gemini-pro-latest`)과 일치하고, 각 ID가 공식 docs(D-12 changelog / D-13 Firebase)에 실재하는가
- [x] R-2: install-mac.sh/windows.ps1에 `openai` 키가 없음을 코드로 재확인했고, SSOT에 참조전용 각주가 있으며 모호한 죽은 컬럼이 없는가
- [x] R-3: Codex 값(dict+TOML+기본값+SSOT)이 [Codex Models](https://developers.openai.com/codex/models) 실재 ID로 일치하는가
- [x] R-4: §5에 Claude/Gemini 별칭 추종 + Codex/OpenAI 분기점검 운영 규칙이 명시됐는가
- [x] R-6: D-1 v1.3 / D-3 v1.5 / install-mac.sh 헤더 변경이력 행에 2026-06-02 KST + (011)이 있는가

### 일관성 테스트
- [x] R-5: install 연동 컬럼 값이 L-1/L-2a/L-2b/L-3/L-4 5위치에서 불일치 0건인가
- [x] 레벨 정의(light/standard/advanced)가 불변인가 ([MUST] 제약)
- [x] 하드코딩 플랫폼 분기 신규 추가(openai 키 등)가 없는가 ([MUST] AGENT.md)
- [x] `~/.opal/` 배포본을 직접 수정하지 않았는가 ([MUST] AGENT.md)  ※ .opal/MEMORY.md 변경은 태스크 번호 갱신(채번)이며 배포본 모델값 수정 없음 — Warning 수준
- [x] `bash -n scripts/install-mac.sh` 문법 통과 / PowerShell 구문 오류 없음

### 문서 품질
- [x] 한국어 본문 + 영어 코드/필드명 규칙 준수
- [x] 변경이력 행이 KST 일시를 포함하는가 ([MUST] CONVENTIONS §변경이력)  ※ windows.ps1 변경이력 011 미추가 — Warning(PLAN §6 R-T5 허용 범위)

---

## 6. 리스크 및 대응

| # | 리스크 | 영향 | 대응 |
|---|--------|------|------|
| R-T1 | **동기화 지점 누락 — windows.ps1(L-4)이 TASK 배경 분석 3곳에 미포함** | windows.ps1만 stale로 잔존 → 드리프트 재발 | Step 4로 windows.ps1 동기 포함, Step 5 검증 범위를 4(+1)곳으로 확대 (본 PLAN에서 반영 완료) |
| R-T2 | preview 모델 채택 — `gemini-pro-latest`가 현 시점 `gemini-3.1-pro-preview`(GA 부재)를 가리킴 | advanced 출력 안정성·비용 변동 | 부동 별칭이 구체 preview 핀보다 안전(GA 승격 시 자동 전환). §5에 "preview 거동 변동 시 임시 핀 가능" 단서 기재 권고 |
| R-T3 | 부동 별칭의 무통보 거동 변화 — `-latest`/CLI 슬러그는 hot-swap | 출력 비결정성 증가 | Gemini는 2주 사전 통보 존재(D-5). Codex/OpenAI는 별칭 미지원이라 핀 유지 + 분기점검으로 제어 |
| R-T4 | OpenAI 컬럼 값(참조전용)이 향후 install 연동 시 stale 가능 | 미래 stale | §5 분기점검 대상에 OpenAI 포함 (M-3 반영) |
| R-T5 | windows.ps1 변경이력 형식 부재 가능성 | R-6 부분 미충족 | EXECUTE 워커가 파일 헤더 확인 후, 형식 있으면 011 행 추가 / 없으면 스킵(코드 파일은 변경이력 의무 대상 아닐 수 있음 — install-mac.sh 헤더 주석 형식 우선) |

> §7 영역 간 용어 일관성: 본 태스크는 FE/BE/ERD/IA 영역 쌍 해당 없음. 단 **동일 모델 매핑 값이 5개 지점에 중복**되는 구조적 일관성 리스크(R-T1)를 검출하여 기재함. 이는 PM 자율 결정 가능 범위(값 동기화)이므로 decision_required 에스컬레이션 대상 아님.
