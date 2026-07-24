# TASK: 도구·MCP·스킬 통합 검색·사용법·활용 체계

> 작성일: 2026-06-26 | 작업 유형: 신규(개선 포함) | 적용 스킬: opd | 모드: agentic
> 입력: 사용자 요청 + 설계 대화
> 출력: TASK.md

## 작업 목표

PM이 작업 중 필요한 capability(OPAL/외부 CLI 도구·MCP·스킬)를 ①상황 기반으로 **검색**하고 ②권위 출처(live)에서 **정확한 사용법을 확인**한 뒤 ③**정확히 사용**하도록 하는, 결정론적 discovery/usage 메커니즘(신규 도구)과 thin 매니페스트(SSOT)를 구축하고 기존 인지 맵·도구 레지스트리의 분산·drift·오라우팅을 정비한다.

## 배경

PM이 "필요 시점에 도구를 꺼내 정확한 사용법을 확인하고 쓰는" 동작이 현재 신뢰성 있게 작동하지 않는다. 실증 사건(MAMS 세션): 브라우저 확인이 필요한 상황에서 PM이 ⓐ정식 `cmux-tool` 래퍼를 거치지 않고 raw `cmux browser`를 호출, ⓑ존재하지 않는 `take-screenshot` 서브명령을 추측, ⓒexit 1 후 `--help` 진단 없이 Playwright로 무분별 폴백, ⓓ`CMUX-TOOLS.md`를 사전 로드하지 않음. 즉 도구는 갖춰져 있으나 "검색→사용법 확인→사용" 절차가 강제되지 않고 산문(advisory)에 머물러 추측·오폴백을 막지 못한다.

## 배경 분석 (대화에서 도출)

대화에서 소스를 직접 확인하여 도출한 현황:

- **정식 도구는 이미 존재**: `opal/tools/cmux-tool/`(래퍼, `~/.opal/tools/cmux-tool/run.sh`)가 에러코드→폴백 규율(`usage`=폴백금지·호출자수정 / `cmux_not_installed`=폴백허용)을 내장. 사건은 이 래퍼를 *우회*하여 발생.
- **인지 맵 결함** (`opal/core/AGENT.md` §도구·MCP 적극 활용 규칙 → 배포 `~/.opal/AGENT.md`): `localhost·SPA 페이지 접근` 행이 **`playwright MCP`를 가리킴 — `cmux-tool`은 맵에 부재**(오라우팅). 실제 도구 인벤토리(xlsx/state/code-scan/cmux/test)를 나열하지 않고 "OPAL Tools" 한 줄로 뭉뚱그림.
- **레지스트리 분산 + drift**: CLI=`tools.md` / MCP=`mcps.md` / 스킬=`opal-skills-registry.json` 3곳에 손-관리. `harness §9 도구 표`={xlsx,state,brain,test} vs `tools.md 섹션`={xlsx,state,code-scan,cmux,test} — **두 목록이 이미 불일치**(brain은 tools.md 부재, code-scan·cmux는 harness 표 부재).
- **사용법 출처가 drift나는 문서**: `CMUX-TOOLS.md`의 `screenshot` 누락이 증거. 사용법의 권위 출처는 산문이 아니라 도구 자신(`--help`)·MCP 스키마.
- **스킬 메타는 이미 충분**: `opal-skills-registry.json`이 pilot(진입, `dispatched_by` 없음 + `//alias`)과 op 스테이지(`dispatched_by` 보유)를 이미 구분. `//erm`=`op-data-model` 단독 호출 선례 존재 → 자기완결 op 스킬을 capability로 노출 가능.

## 확정된 설계 방향 (대화에서 합의)

1. **thin JSON 매니페스트 = SSOT** — 각 엔트리에 `kind`/`purpose`/`when`/`exec`/`usage_source`/`fallback`. **사용법 텍스트는 저장하지 않고** `usage_source` 포인터만 둔다 → 매니페스트는 도구 추가/제거 시에만 변경 = drift 표면 ≈ 0.
2. **사용법 출처 우선순위(신뢰도)**: ⓪ `self --help` / `mcp-schema`(live, 최상) → ② `context7`/`url` 슬라이스(live 외부) → ① `inline`(단순) → ③ `doc:<path>`(최후수단 + freshness 표기). 캡틴 3유형(자체 파일 / 외부 URL / 문서화 파일) 모두 이 틀에 포함되며, 더 강한 ⓪(도구 자신)을 1순위로 추가.
3. **단일 호출 결합** — 검색+사용법 주입을 1콜로: `resolve <상황>` → `{tool, exec, live usage, fallback, error_contract}` 한 번에 반환(캡틴의 "사용법 컨텍스트를 한번에 주입"을 1콜로 실현).
4. **2단 토큰 구조** — `list`(전체 1줄 용도, 쌈) / `usage <tool>`(확정 1개의 live 사용법). 절대 `N개 × 전체 사용법`을 한꺼번에 주입하지 않음.
5. **통합 capability(tool+mcp+skill)** — `kind`로 구분. tool/mcp=atomic 호출, **pilot 스킬=`//`진입(파이프라인), op 스킬=워커 디스패치(SKILL.md 주입, `dispatched_by`가 정상 파이프라인 홈)**. 기존 mcps.md·skills-registry.json은 갈아엎지 않고 **federation(읽기)**.
6. **강제 한계 정직 고지** — 도구 호출 주체가 LLM이라 "사용법 선확인"의 100% 하드게이트는 불가. 현실적 지렛대 = (a) raw 외부 CLI 대신 에러계약 가진 OPAL 래퍼로 채널링, (b) `resolve`를 쉬운 기본 경로로. protocol + observability + 래퍼 채널링으로 대체.

## 명확화 결과

> TASK 4요소를 잠근다. 미확정 2건(도구 이름·1차 범위)은 agentic 모드에서 PM이 권고안으로 자율 확정하고 AGENTIC-LOG에 기록 (PLAN에서 재검토 가능).

| 요소 | 확정값 | 미확정(있으면) | 의존 사실 |
|------|--------|--------------|----------|
| 목표 | PM이 capability(도구/MCP/스킬)를 상황 검색→권위 출처 live 사용법 확인→정확 사용하도록 결정론적 discovery/usage 도구 + thin 매니페스트(SSOT) 구축 + 인지맵/레지스트리 정비 | - | 배경 분석·확정 설계 방향 |
| 범위 | **포함**: (1) 신규 결정론적 도구 `tool-scan`(가칭) — `list`/`which`/`usage`/`resolve`/`check` (2) thin 도구 매니페스트 JSON(SSOT, usage 텍스트 미저장) (3) `resolve` federation: mcps.md·opal-skills-registry.json 읽기로 tool/mcp/skill 통합 조회 (4) `opal/core/AGENT.md` 인지맵 정비(cmux-tool 추가·localhost→cmux-tool 오라우팅 수정·사용법 확인/에러 진단후 폴백 규율) (5) tools.md·harness §9 도구 표 drift 정합. **제외**: recipe 자동 제시(2차, 설계 훅만), 스킬/MCP 매니페스트 재작성(federation으로 충분), usage 선확인 하드게이트(메커니즘상 불가) | 도구 이름·1차 구현 깊이(MVP=tool-kind 우선 vs 처음부터 3종 federation)는 PM 자율 확정 | 확정 설계 방향 1·5·6 |
| 제약 | 배포 경계(`opal/` 소스만 수정·`~/.opal` 직접편집 금지·install은 캡틴) / 플랫폼 독립(분기는 어댑터만) / 기존 skills-registry.json 소비자(install·harness) 불파괴 / 매니페스트 usage 텍스트 저장 금지(포인터만) / 변경이력·@header 의무 / 신규 도구=도구 자체 로직 → self-confirming 위험 → **RED-first 적용 대상** | - | .opal/AGENT.md 금지사항·PRINCIPLES |
| 완료기준 | 아래 "요구사항" 전부 충족 + 기존 테스트 회귀 0 + 시뮬1(브라우저 확인) 재현 시 추측 호출 0 | - | - |

## 요구사항

- [ ] **R-1** 신규 결정론적 도구(가칭 `tool-scan`)가 `opal/tools/{name}/run.sh` + python으로 동작하고 JSON을 출력한다 (기존 state/cmux/test-tool 패턴 답습). AC: 4+서브명령이 `{"ok":true,...}` JSON 반환.
- [ ] **R-2** `usage <tool>`이 OPAL/외부 CLI에 대해 **live `--help`를 셸 실행해 반환**한다(정적 문서 복제 아님). AC: cmux-tool의 `usage`가 실제 `run.sh --help` 출력과 일치하고, 도구의 `--help`가 바뀌면 자동 반영(정적 캐시 아님)임을 검증.
- [ ] **R-3** thin 매니페스트 JSON(SSOT)이 `kind`/`purpose`/`when`/`exec`/`usage_source`/`fallback`을 담고 **usage 텍스트는 미저장**한다. AC: 매니페스트 grep 시 도구별 `--help` 본문 텍스트 부재, `usage_source` 포인터만 존재.
- [ ] **R-4** `which`/`resolve <상황>`이 상황→capability를 반환하며 tool/mcp/skill을 `kind`로 구분한다. AC: `resolve "browser check localhost"` → cmux-tool / `resolve "library docs"` → context7 / `resolve "데이터 모델"` → op-data-model(kind=skill-stage, dispatched_by 포함).
- [ ] **R-5** `resolve`가 기존 `mcps.md`·`opal-skills-registry.json`을 federation(읽기)한다 — 신규 매니페스트로 재작성하지 않는다. AC: skills-registry.json 원본 무변경, resolve가 그 데이터를 읽어 skill 후보 반환.
- [ ] **R-6** `opal/core/AGENT.md` §도구 인지 맵에 **cmux-tool 행 추가 + localhost·SPA→cmux-tool 오라우팅 수정**(현 playwright 단독 → cmux-tool 우선/playwright 폴백). AC: 맵에 cmux-tool 존재, localhost 행이 cmux-tool을 1순위로 명시.
- [ ] **R-7** `opal/core/AGENT.md`에 도구 사용 규율 추가: **변경/실행 계열 첫 호출 前 사용법 확인** + **에러 시 종류 기반 진단 후 폴백**(맹목 폴백 금지). AC: 규율 문단 존재, 에러계약 소비(usage=수정/cmux_not_installed=폴백) 명시.
- [ ] **R-8** `tools.md`·`opal-harness.md §9` 도구 표 drift 정합 — 두 목록을 실제 도구 집합({xlsx,state,code-scan,cmux,test,brain,신규})으로 일치. AC: 두 표의 도구 집합이 동일.
- [ ] **R-9** 신규 도구를 `install-mac.sh` 배포 경로에 등록(소스만 — 실제 install은 캡틴). AC: install 스크립트에 신규 도구 배포 라인 존재.

## 제약 조건

- **배포 경계**: `opal/`·`scripts/` 등 프로젝트 소스만 수정. `~/.opal/` 직접 편집 금지. install 재배포는 캡틴이 직접 수행.
- **플랫폼 독립**: Claude/Cursor/Gemini/Codex 분기는 어댑터 계층(install)만. 도구 로직에 플랫폼 분기 금지.
- **기존 소비자 불파괴**: `opal-skills-registry.json`은 install·harness가 소비 중 → 스키마 변경 없이 federation(읽기)만.
- **매니페스트 규율**: usage 텍스트 저장 금지(포인터만) — drift 표면 최소.
- **추적성**: 수정 문서에 변경이력 행 추가, 신규 도구 코드에 @header.
- **RED-first**: 신규 도구는 도구 자체 로직(self-confirming 위험) → 작성자≠구현자로 RED-first 적용.

## 기술 스택

- 도구 런타임: Python 3.x (`~/.opal/.venv`) + Bash 래퍼(`run.sh`) — 기존 state/test-tool 패턴
- 데이터: JSON 매니페스트 + 기존 `mcps.md`(md)·`opal-skills-registry.json`(json) federation
- 배포: `scripts/install-mac.sh`
- 테스트: pytest (기존 도구 테스트 패턴), test-tool unit

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | 프로젝트 정의 SSOT | `docs/PROJECT.md` | 프로젝트 구성·문서 레지스트리 |
| D-2 | 설계 | 코드·문서 컨벤션 | `docs/CONVENTIONS.md` | 네이밍·@header·배포경계·플랫폼분기 규칙 |
| D-3 | 설계 | 아키텍처 | `docs/ARCHITECTURE.md` | 도구 배포 모델·2-Layer |
| D-4 | 소스 | 도구 레지스트리 | `opal/core/references/tools.md` | 정합 대상 + 도구 패턴 기준 |
| D-5 | 소스 | MCP 레지스트리 | `opal/core/references/mcps.md` | federation 입력 |
| D-6 | 소스 | 스킬 레지스트리 | `opal/core/references/opal-skills-registry.json` | federation 입력(불파괴) |
| D-7 | 소스 | 글로벌 에이전트 정의(인지맵 원천) | `opal/core/AGENT.md` | 인지맵 정비 대상(R-6/R-7) |
| D-8 | 소스 | cmux 래퍼 | `opal/tools/cmux-tool/` (run.sh·README·docs/CMUX-REFERENCE.md) | 에러계약·라우팅 기준, 사건 당사자 |
| D-9 | 소스 | 도구 패턴 참조 | `opal/tools/state-tool/`·`opal/tools/test-tool/` | run.sh+python+JSON 패턴 답습 |
| D-10 | 소스 | 공통 하네스 §9 | `opal/core/references/opal-harness.md` | 도구 표 drift 정합(R-8) |
| D-11 | 소스 | 설치 스크립트 | `scripts/install-mac.sh` | 신규 도구 배포 등록(R-9) |
