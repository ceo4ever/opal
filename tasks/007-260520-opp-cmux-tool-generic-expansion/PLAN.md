# PLAN: cmux-tool 범용 확장 + wtm-agent fallback 체인 재배선

> 작성일: 2026-05-20
> 입력: tasks/007-260520-opp-cmux-tool-generic-expansion/TASK.md
> 출력: tasks/007-260520-opp-cmux-tool-generic-expansion/PLAN.md
> 모드: semi-agentic (TASK.md L1 헤더) — PLAN 산출물만 생성, 코드/파일 수정 금지

---

## 0. 결정 요약 (Executive Summary)

미확정 사항 M-1 ~ M-7 결정 결과를 한 곳에 모아둔다. 상세 근거는 §2 핵심 설계 및 §5 리스크 참조.

| # | 결정 | 한줄 요지 |
|---|------|----------|
| **M-1** | (a) WebFetch 완전 제거 — 2단(cmux → playwright) 체인으로 축소 | 캡틴 발화 "cmux-tool 1순위, fallback playwright-tool"과 정합. WebFetch는 보조 위치라도 cmux 미설치 환경 분기와 충돌하여 의사결정 표가 3분기로 늘어남 → 단순성 우선 (§2 코딩 원칙 §2) |
| **M-2** | 노출 7종(필수) + 5종(선택) = **총 12종 서브명령** + `extract`(레거시 호환) 1종. `eval`+`wait` 조합은 별도 명령으로 노출 (자동화 핵심). A/B/C 분기 흐름은 `eval`+`wait` 레시피 + `lib/`의 분기 헬퍼로만 다루고 별도 서브명령으로 노출하지 않는다 | 알투 자동 트리거 가능 단위(읽기/네비/상호작용) 최소 집합 노출. cmux/scripts/test-browser.sh는 `lib/branch.sh`로 일반화 |
| **M-3** | 공통 필드 5종(`ok` / `command` / `surface` / `user_owned` / `error`) + 명령별 특화 필드. 기존 `extract` 8필드(`ok`/`method`/`mode`/`surface`/`user_owned`/`title`/`final_url`/`content`/`bytes`/`wait_ms`)는 `command:"extract"`일 때 한정하여 그대로 유지 | R-2 호환성과 R-1 범용성 모두 충족. 신규 명령은 공통 5필드 + 특화 필드(예: `snapshot`은 `snapshot_text`/`length`) |
| **M-4** | tools.md "트리거 조건" 표 — **명령군 × 대표 사용자 문장 × 우선 명령** 3열 매트릭스로 작성 (5행: 웹 크롤링 / 정보 수집 / 웹 테스트(상호작용) / E2E 자동화 / 로컬 SPA·동적 페이지) | 알투가 사용자 입력을 매트릭스 행으로 매핑하여 `cmux-tool extract` 또는 `cmux-tool click/fill/...`를 직접 선택. fallback 분기는 §M-5와 연동 |
| **M-5** | playwright-tool 폴백 트리거 에러 코드 집합 = `not_in_cmux` / `cmux_not_installed` / `surface_parse_failed` / `open_failed` 4종 (모두 `fallback: "phase3"` 라벨 보존). 그 외(`usage` / `invalid_surface` / `goto_failed` / `wait_failed` / `eval_failed`) 는 입력 오류·일시 장애로 분류 → 폴백 금지·즉시 에스컬레이션 | wtm-agent가 자동 우회할 안전 폴백 집합과 입력 정정이 필요한 에러를 분리 |
| **M-6** | `opal/tools/cmux-tool/` 하위 3개 디렉토리: `lib/` (공통 헬퍼 4파일) / `examples/` (E2E 레시피 2파일 + hooks 샘플 1파일) / `docs/` (CLI/Socket API 참조 1파일). docs/ 파일명은 `CMUX-REFERENCE.md`로 통합 | 흡수 출처 추적 가능 + install_dir 재귀 복사 자동 호환 |
| **M-7** | 자산 11종 처분 — 흡수 7건(`_lib.sh`/`test-browser.sh`/`CMUX-TOOLS.md`/`CMUX.md` [일반]섹션/`claude-hooks.sample.json`/`README.md` 일부/`ghostty.config.sample` 일부) / 폐기 4건(`_config.sh`/`cmux.json`/`start-all.sh`/`stop-all.sh`/`open-dev.sh`/`analyze-log.sh`) | 일반화 가능한 자산만 흡수. MAMS 전용·서버 기동 워크플로우 자산은 본 태스크 범위 외 |

---

## 1. 현황 조사

### 참조 문서 (PLAN 작성 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | cmux-tool run.sh | `opal/tools/cmux-tool/run.sh` | 확장 대상 본체 — 현 6종 cmux browser 내부 사용 (`open`/`goto`/`eval`/`wait`/`get`/`tab close`). 3모드(A/B/C) 결정·user_owned 시그널 발화 위치 |
| D-2 | 소스 | cmux-tool README | `opal/tools/cmux-tool/README.md` | 기존 인터페이스(3모드) · 출력 8필드 · 안전 가드(B/C cleanup 금지) · 에러 코드 9종 SSOT |
| D-3 | 소스 | playwright-tool run.sh + main.py | `opal/tools/playwright-tool/run.sh`, `opal/tools/playwright-tool/main.py` | fallback 대상. .venv python 기반 / 출력 형식 `{ok, url, mode, path, content}` |
| D-4 | 설계 | OPAL Tools 레지스트리 | `opal/core/references/tools.md` | 기존 3개 도구 등록 골격(xlsx/state/code-scan) — 신규 cmux-tool 등록 시 동일 구조 적용 |
| D-5 | 설계 | wtm-agent AGENT.md | `opal/agents/opal-wtm-agent/AGENT.md` | Phase 1→2→3 폴백 체인 SSOT. 본 PLAN에서 2단 체인(cmux→playwright)으로 재배선 |
| D-6 | 소스 | web-to-markdown SKILL.md | `skills/web-to-markdown/SKILL.md` | SKILL의 Phase 흐름·CLI 호출 패턴 — AGENT.md와 함께 갱신 대상 |
| D-7 | 소스 | install-mac.sh (도구 배포) | `scripts/install-mac.sh:814-842` | `install_dir`가 `opal/tools/cmux-tool` 트리 통째로 복사. 신규 하위 디렉토리는 자동 배포되나 실행 권한은 명시 chmod 필요 |
| D-8 | 인풋 | cmux 자산 묶음 | `tasks/007-260520-opp-cmux-tool-generic-expansion/cmux/` | 흡수·재배치·정리 대상 SSOT (캡틴이 직접 배치) |
| D-9 | 인풋 | CMUX-TOOLS.md | `tasks/007-.../cmux/docs/CMUX-TOOLS.md` | §3 브라우저 18종 명령 인벤토리 + §5 Socket API + §4 hooks 레시피. docs/ 흡수 핵심 |
| D-10 | 인풋 | test-browser.sh | `tasks/007-.../cmux/scripts/test-browser.sh` | A/B/C 분기 흐름 원형 (L65-100 분기 결정 로직). lib/branch.sh로 일반화 흡수 |
| D-11 | 인풋 | _lib.sh | `tasks/007-.../cmux/scripts/_lib.sh` | start_surface / verify_surface / ready_pattern_for 3종 헬퍼. lib/cmux-helpers.sh로 흡수 |
| D-12 | 인풋 | cmux/README.md | `tasks/007-.../cmux/README.md` | "프레임워크 승격 대상" 섹션 (L85-113) — 일반/MAMS 전용 분류 출처 |
| D-13 | 인풋 | claude-hooks.sample.json | `tasks/007-.../cmux/config/claude-hooks.sample.json` | Claude Code hooks 3종(Stop/Notification/PreCompact) — examples/ 흡수 |
| D-14 | 인풋 | ghostty.config.sample | `tasks/007-.../cmux/config/ghostty.config.sample` | 일반 cmux 사용자 키바인딩 가이드 — docs/CMUX-REFERENCE.md §부록에 일부 흡수 |
| D-15 | 인풋 | CMUX.md | `tasks/007-.../cmux/docs/CMUX.md` | [일반] 태그 섹션(§1 설치/§3 단축키/§6 알림) 일부 흡수, [MAMS 전용] 섹션 전량 폐기 |
| D-16 | 설계 | OPAL Harness §9 OPAL Tools | `opal/core/references/opal-harness.md` §9 (L204-237) | 도구 등록 원칙: 래퍼 호출 / JSON 출력 / `"ok": false`이면 `"error"` 필드 / Lazy 트리거 |
| D-17 | 설계 | Citation Rules | `opal/core/references/harness/citation-rules.md` | 산출물 인용 규칙 — §1 참조 테이블 + §2 인라인 인용 + §2.4 [MUST] 포맷 |
| D-18 | 설계 | Coding Principles | `opal/core/references/harness/coding-principles.md` | §2 PLAN 단순성 우선 + §4 EXECUTE 외과적 변경 — 본 PLAN의 단순화 결정 근거 |
| D-19 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | 언어/네이밍/구현 규칙 SSOT |
| D-20 | 외부 | cmux Browser Automation 공식 문서 | [cmux Browser Automation](https://cmux.com/ko/docs/browser-automation) | 서브명령 18종 시그니처·플래그 SSOT (TASK §배경분석 §cmux browser 공식 명령 인벤토리에서 인용된 1차 출처) |
| D-21 | 외부 | cmux GitHub | [manaflow-ai/cmux](https://github.com/manaflow-ai/cmux) | 버전·릴리스 확인 (cmux ≥ 0.64.3 요구) |

> 인용 형식: `opal/core/references/harness/citation-rules.md` §3.1 참조.

#### [MUST] 제약 원문 인용 (재해석 금지)

> `[MUST]` `docs/CONVENTIONS.md` §언어 규칙: "문서 본문 한국어 (기술 용어는 영어 병기) / 코드·변수·필드명 English / YAML frontmatter 키 English / 파일·폴더 이름 English, kebab-case (Python 파일은 snake_case)"

> `[MUST]` `docs/CONVENTIONS.md` §구현 규칙 Guards: "사용자가 명시적으로 '승인', '진행해', '구현해' 등의 실행 허가를 내리기 전까지 코드를 작성하거나 파일을 생성·수정하지 않는다."

> `[MUST]` `docs/CONVENTIONS.md` §구현 규칙 도구 우선 원칙: "파일 처리·데이터 변환 작업이 필요할 때, 직접 코드를 작성하기 전에 OPAL 도구(~/.opal/tools/)를 우선 검토한다."

> `[MUST]` `docs/CONVENTIONS.md` §구현 규칙 변경이력 작성: "스킬·에이전트·참조 문서를 변경하면 ## 변경이력 표에 행을 추가한다. 일시는 YYYY-MM-DD HH:mm (KST), 버전은 semver, 변경내용은 태스크 번호를 괄호로 포함."

> `[MUST]` `docs/CONVENTIONS.md` §구현 규칙 배포 경계: "~/.opal/ 배포 파일을 직접 편집하지 않는다. 변경은 항상 프로젝트 소스(opal/, skills/, agents/, community-skills/, scripts/)에서 수행한다. 변경 후 ./scripts/install-mac.sh로 재배포하여 검증한다."

> `[MUST]` `docs/CONVENTIONS.md` §구현 규칙 플랫폼 분기 격리: "Claude/Cursor/Gemini/Antigravity 등 플랫폼별 차이는 어댑터 계층에서만 흡수한다. 스킬·에이전트 본문에 플랫폼 조건문을 추가하지 않는다."

> `[MUST]` `opal/tools/cmux-tool/README.md` §안전 가드 (L124-132): "B/C 모드(사용자 surface 재사용)에서는 cmux browser <surface> tab close를 절대 호출하지 않는다."

> `[MUST]` `opal/core/references/harness/coding-principles.md` §2 PLAN 단순성 우선: "현재 요구사항이 강제할 때만 복잡성을 추가한다. 사전 추상화·미래 대비·불필요한 레이어 금지."

> `[MUST]` `opal/core/references/harness/coding-principles.md` §4 EXECUTE 외과적 변경: "PLAN.md에 명시된 범위만 변경한다. 범위 밖 파일·구간은 수정하지 않는다."

### 관련 파일

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| `opal/tools/cmux-tool/run.sh` | cmux browser 자동화 래퍼 본체 — 현 3모드(A/B/C) extract 전용 | 수정 (디스패처 골격으로 재설계) | `opal/tools/cmux-tool/run.sh:1-210` |
| `opal/tools/cmux-tool/README.md` | 도구 사용자 진입점 — 3모드 사용법·출력 8필드·에러 9종 SSOT | 수정 (서브명령 표 + 흡수 자산 위치 추가) | `opal/tools/cmux-tool/README.md:1-153` |
| `opal/tools/cmux-tool/lib/` | 공통 헬퍼 디렉토리 | 신규 | - |
| `opal/tools/cmux-tool/lib/cmux-helpers.sh` | _lib.sh 흡수 — surface 기동/검증 헬퍼 (run.sh 본체와 분리) | 신규 | `tasks/007-.../cmux/scripts/_lib.sh:11-103` |
| `opal/tools/cmux-tool/lib/branch.sh` | test-browser.sh 분기 로직 일반화 — A/B/C 결정 helper | 신규 | `tasks/007-.../cmux/scripts/test-browser.sh:65-100` |
| `opal/tools/cmux-tool/lib/dispatch.sh` | 서브명령 라우팅 + 인자 정규화 + JSON 직렬화 공통 | 신규 | - (디스패처 신설) |
| `opal/tools/cmux-tool/lib/json.sh` | python3 JSON 직렬화 헬퍼 (run.sh L178-207 분리) | 신규 | `opal/tools/cmux-tool/run.sh:178-207` |
| `opal/tools/cmux-tool/examples/` | 흡수된 E2E·hooks 레시피 디렉토리 | 신규 | - |
| `opal/tools/cmux-tool/examples/e2e-form-fill.sh` | "click + fill + wait + snapshot" 조합 E2E 레시피 (test-browser.sh + CMUX.md §7-A 흡수) | 신규 | `tasks/007-.../cmux/scripts/test-browser.sh`, `tasks/007-.../cmux/docs/CMUX.md:299-356` |
| `opal/tools/cmux-tool/examples/e2e-branch-auto.sh` | A/B/C 분기 자동 결정 E2E 레시피 (test-browser.sh 원형 보존판) | 신규 | `tasks/007-.../cmux/scripts/test-browser.sh:1-133` |
| `opal/tools/cmux-tool/examples/claude-hooks.sample.json` | Claude Code hooks 3종 샘플 흡수 | 신규 | `tasks/007-.../cmux/config/claude-hooks.sample.json:1-37` |
| `opal/tools/cmux-tool/docs/CMUX-REFERENCE.md` | CLI/Socket API/단축키 통합 참조 (CMUX-TOOLS.md + CMUX.md [일반]섹션 흡수) | 신규 | `tasks/007-.../cmux/docs/CMUX-TOOLS.md:1-283`, `tasks/007-.../cmux/docs/CMUX.md:23-130` |
| `opal/core/references/tools.md` | OPAL 도구 레지스트리 — 현 3개 도구 등록 | 수정 (`## cmux-tool` 섹션 신규 추가) | `opal/core/references/tools.md:1-300` |
| `opal/agents/opal-wtm-agent/AGENT.md` | wtm-agent 정의 — Phase 1/2/3 체인 SSOT | 수정 (Phase 1 제거 → 2단 체인) | `opal/agents/opal-wtm-agent/AGENT.md:1-121` |
| `skills/web-to-markdown/SKILL.md` | web-to-markdown 스킬 SSOT — Phase 흐름·CLI 호출 | 수정 (Phase 1 제거 + 호칭 일관화) | `skills/web-to-markdown/SKILL.md:1-260` |
| `scripts/install-mac.sh` | 도구 배포 + chmod | 수정 (lib/examples/ 실행 권한 + cmux-tool 안내 갱신) | `scripts/install-mac.sh:814-842` |
| `tasks/007-.../cmux/` | 인풋 자산 묶음 | 정리 (흡수 후 폴더 자체 정리) | - |

### 현재 상태

1. **`opal/tools/cmux-tool/run.sh`는 단일 진입점 + URL→HTML extract 전용 흐름** — 인자 파싱에서 `--surface` 또는 `http(s)://` URL만 받고 (`opal/tools/cmux-tool/run.sh:29-66`), 내부적으로 `cmux browser open`/`goto`/`wait`/`get title`/`get url`/`eval`/`tab close` 6종을 사용한다 (`opal/tools/cmux-tool/run.sh:105-167`). 다른 cmux browser 명령(`click`/`fill`/`type`/`press`/`select`/`hover`/`focus`/`snapshot`/`navigate`/`back`/`forward`/`reload`/`url`)은 노출되지 않는다.

2. **`opal/core/references/tools.md`에 cmux-tool 미등록** — 현재 등록 도구는 `xlsx-tool`/`state-tool`/`code-scan` 3종이다 (`opal/core/references/tools.md:8-298`). 알투(PM)와 워커가 Lazy-load 시점에 tools.md를 읽어도 cmux-tool 존재를 인식할 수 없다. OPAL Harness §9는 "파일 처리·데이터 변환 시 직접 코드 작성 전에 OPAL 도구 우선 검토" 원칙을 강제하므로, 등록되지 않으면 자동 선택이 불가하다 (→ D-16 §9).

3. **wtm-agent의 Phase 1(WebFetch)이 1순위** — `opal/agents/opal-wtm-agent/AGENT.md:5`는 description에서 "Phase 1(WebFetch) → Phase 2(cmux, 조건부) → Phase 3(playwright-tool CLI) 폴백 전략"으로 명시. 캡틴 발화 "cmux-tool 1순위, fallback playwright-tool"과 호칭·순서가 어긋난다.

4. **cmux 자산 13개 파일 인풋** — `tasks/007-.../cmux/` 하위에 11개 파일 + .gitkeep 1개. 자체 분류(`cmux/README.md:85-113`)에 따르면 [일반] 11건 + [MAMS 전용] 7건이지만, MAMS 전용 자산은 본 태스크 범위 외다 (TASK §F-5).

5. **install-mac.sh의 배포 흐름은 신규 디렉토리에 친화적** — `install_dir`가 `opal/tools/`를 재귀 복사 (`scripts/install-mac.sh:814-816`)하므로 `cmux-tool/lib/`, `cmux-tool/examples/`, `cmux-tool/docs/` 신설 시 자동 배포된다. 단, `cmux-tool/lib/*.sh`, `cmux-tool/examples/*.sh`는 chmod +x가 명시적으로 필요할 수 있다 (run.sh만 833-842행에서 chmod 처리됨).

### 영향 범위

| 영역 | 영향 | 비고 |
|------|------|------|
| cmux-tool 디스패처 | 신규 서브명령 12종 + 레거시 `extract` 1종 | 외부 호출자(wtm-agent, 알투, 워커) 자동 선택 가능 |
| wtm-agent | Phase 1 WebFetch 제거 → 2단 체인 | description·실행 프로세스·결과 JSON `method` 유효값(`webfetch` 삭제) |
| web-to-markdown SKILL.md | Phase 1 관련 섹션·다이어그램·트리거 키워드 갱신 | `//wtm --browser`의 의미가 사실상 기본 동작으로 일원화 |
| tools.md | 신규 `## cmux-tool` 섹션 (네번째 도구) | xlsx/state/code-scan 동등 위치. install-mac.sh 변경이력 행 추가 |
| install-mac.sh | lib/examples 하위 .sh 실행 권한 처리 + 안내 메시지 갱신 | `scripts/install-mac.sh:833-842` 블록 확장 |
| tasks/007-.../cmux/ 인풋 폴더 | 흡수 완료 후 폴더 자체 정리 (휴지통 또는 README 변환) | EXECUTE 시점 최종 결정 |

---

## 2. 구현 계획

### 파일 변경 계획

#### 신규 생성

| # | 파일 경로 | 역할 | 근거 |
|---|----------|------|------|
| N-1 | `opal/tools/cmux-tool/lib/dispatch.sh` | 서브명령 디스패처 본체 (case 라우팅 + 공통 인자 파싱) | M-2 결정 — 디스패처 분리, M-6 lib/ 구조 |
| N-2 | `opal/tools/cmux-tool/lib/cmux-helpers.sh` | _lib.sh 흡수 — `start_surface` / `verify_surface` / `ready_pattern_for` 일반화 | 흡수 출처: `tasks/007-.../cmux/scripts/_lib.sh:11-103` |
| N-3 | `opal/tools/cmux-tool/lib/branch.sh` | A/B/C 분기 결정 헬퍼 (test-browser.sh L65-100 일반화) | 흡수 출처: `tasks/007-.../cmux/scripts/test-browser.sh:65-100` |
| N-4 | `opal/tools/cmux-tool/lib/json.sh` | python3 JSON 직렬화 공통 함수 | run.sh L178-207 패턴 재사용 |
| N-5 | `opal/tools/cmux-tool/examples/e2e-form-fill.sh` | click + fill + wait + snapshot 조합 E2E 레시피 | 흡수 출처: CMUX.md §7-A (L301-356) + test-browser.sh |
| N-6 | `opal/tools/cmux-tool/examples/e2e-branch-auto.sh` | A/B/C 분기 자동 결정 E2E 레시피 (test-browser.sh 원형 보존판) | 흡수 출처: `tasks/007-.../cmux/scripts/test-browser.sh:1-133` |
| N-7 | `opal/tools/cmux-tool/examples/claude-hooks.sample.json` | Claude Code hooks 3종 샘플 (Stop/Notification/PreCompact) | 흡수 출처: `tasks/007-.../cmux/config/claude-hooks.sample.json` |
| N-8 | `opal/tools/cmux-tool/docs/CMUX-REFERENCE.md` | CLI 18종 + Socket API + 단축키 + hooks 레시피 통합 참조 | 흡수 출처: `tasks/007-.../cmux/docs/CMUX-TOOLS.md` 전량 + CMUX.md §1/§3/§6 |

#### 수정

| # | 파일 경로 | 변경 내용 | 근거 |
|---|----------|----------|------|
| M-1 | `opal/tools/cmux-tool/run.sh` | 디스패처로 재설계 — `$1`이 URL이면 `extract`로 라우팅(레거시 호환), 그 외 서브명령은 `lib/dispatch.sh`로 위임 | TASK §R-1, R-2 |
| M-2 | `opal/tools/cmux-tool/README.md` | 디스패처 구조 + 12+1종 서브명령 사용법 + 흡수 자산 위치 표 + 변경이력 v1.1 (006) | TASK §R-5 |
| M-3 | `opal/core/references/tools.md` | `## cmux-tool` 섹션 신규 추가 (xlsx/state/code-scan 동일 골격) + "트리거 조건" 표 + 변경이력 v1.5 (006) | TASK §R-4 |
| M-4 | `opal/agents/opal-wtm-agent/AGENT.md` | Phase 1(WebFetch) 제거 → Phase 1(cmux) → Phase 2(playwright) 2단 체인으로 갱신. description / 실행 프로세스 / 결과 JSON `method` 유효값(`webfetch` 삭제) / 변경이력 v1.1 (006) | TASK §R-3, M-1 |
| M-5 | `skills/web-to-markdown/SKILL.md` | Phase 1 WebFetch 관련 섹션·다이어그램·`--browser` 모드 의미 일원화. 변경이력 행 추가 (006) | TASK §R-3와 정합 (AGENT.md ↔ SKILL.md SSOT 일관성) |
| M-6 | `scripts/install-mac.sh` | `cmux-tool/lib/*.sh`, `cmux-tool/examples/*.sh`에 chmod +x 처리 추가 + 안내 메시지 갱신 (위치: L833-842 블록 확장) | TASK §R-6 |

#### 삭제 / 정리

| # | 파일 경로 | 사유 |
|---|----------|------|
| D-1 | `tasks/007-260520-opp-cmux-tool-generic-expansion/cmux/scripts/_config.sh` | MAMS 전용 (포트·경로 하드코딩). 본 태스크 범위 외 |
| D-2 | `tasks/007-260520-opp-cmux-tool-generic-expansion/cmux/scripts/start-all.sh` | 서버 일괄 기동 워크플로우 (cmux-tool 디스패처 영역과 무관) — 별도 후속 태스크에서 다룰 가능 |
| D-3 | `tasks/007-260520-opp-cmux-tool-generic-expansion/cmux/scripts/stop-all.sh` | 동일 |
| D-4 | `tasks/007-260520-opp-cmux-tool-generic-expansion/cmux/scripts/open-dev.sh` | 동일 |
| D-5 | `tasks/007-260520-opp-cmux-tool-generic-expansion/cmux/scripts/analyze-log.sh` | 로그 분석 워크플로우 (cmux-tool 영역과 무관) |
| D-6 | `tasks/007-260520-opp-cmux-tool-generic-expansion/cmux/config/cmux.json` | MAMS 팔레트 (프로젝트 전용 cmux 팔레트는 도구 디스패처 범위 외) |
| D-7 | `tasks/007-260520-opp-cmux-tool-generic-expansion/cmux/config/ghostty.config.sample` | 사용자 환경 설정 — 일반 cmux 사용자 환경 가이드는 examples/ 보다 docs/CMUX-REFERENCE.md §부록의 짧은 안내 링크로 충분 |
| D-8 | `tasks/007-260520-opp-cmux-tool-generic-expansion/cmux/docs/CMUX.md` [MAMS 전용] 섹션 | §2/§4/§5-4/§5-5/§7/§8 모두 MAMS 포트·스크립트 의존 |
| D-9 | `tasks/007-260520-opp-cmux-tool-generic-expansion/cmux/docs/CMUX.md` 파일 자체 | [일반] 섹션은 CMUX-REFERENCE.md에 흡수, [MAMS 전용] 섹션은 폐기. 원본 파일 자체는 EXECUTE 종료 시 정리 |
| D-10 | `tasks/007-260520-opp-cmux-tool-generic-expansion/cmux/README.md` | 흡수 완료 시 자체 분류 정보는 더 이상 필요 없음 |
| D-11 | `tasks/007-260520-opp-cmux-tool-generic-expansion/cmux/logs/.gitkeep` | 로그 디렉토리 자체가 MAMS 워크플로우 산물 |
| D-12 | `tasks/007-260520-opp-cmux-tool-generic-expansion/cmux/` (폴더 전체) | EXECUTE Step 9에서 폴더 자체 제거. 흡수 자산 추적성은 신규 파일 헤더 주석 + README §흡수 자산 출처 표에서 보존 |

### 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | docs/ 참조 통합 문서 작성 | `opal/tools/cmux-tool/docs/CMUX-REFERENCE.md` (N-8) | 중 |
| 2 | lib/ 공통 헬퍼 4파일 작성 | N-1 ~ N-4 (`lib/dispatch.sh`, `cmux-helpers.sh`, `branch.sh`, `json.sh`) | 상 |
| 3 | run.sh 디스패처 재설계 (lib/dispatch.sh 호출) | `opal/tools/cmux-tool/run.sh` (M-1) | 상 |
| 4 | examples/ E2E + hooks 샘플 흡수 | N-5, N-6, N-7 | 중 |
| 5 | README.md 갱신 (디스패처 + 흡수 자산 표) | `opal/tools/cmux-tool/README.md` (M-2) | 중 |
| 6 | tools.md 신규 등록 | `opal/core/references/tools.md` (M-3) | 중 |
| 7 | wtm-agent AGENT.md 재배선 | `opal/agents/opal-wtm-agent/AGENT.md` (M-4) | 중 |
| 8 | web-to-markdown SKILL.md 일관성 갱신 | `skills/web-to-markdown/SKILL.md` (M-5) | 중 |
| 9 | install-mac.sh 배포 처리 갱신 | `scripts/install-mac.sh` (M-6) | 하 |
| 10 | tasks/007-.../cmux/ 인풋 폴더 정리 | `tasks/007-.../cmux/` (D-12) | 하 |

> 의존성 원칙: 하위 레이어(`lib/` → run.sh → README → tools.md 등록 → wtm 재배선)부터 위로. examples/는 lib/ 헬퍼를 참조할 수 있어 lib/ 이후 배치.

### 핵심 설계

#### §2.1 디스패처 명령 인벤토리 (M-2 결정)

**필수 7종** (cmux browser 18종 중 자동화 핵심) — Lazy-load 후 알투가 직접 매핑 가능한 단위:

| # | 서브명령 | cmux 원본 | 카테고리 | 폴백 트리거 (M-5) |
|---|---------|---------|---------|------------------|
| 1 | `extract` | `open` + `goto` + `wait` + `get` + `eval` + `tab close` | 읽기 (현 흐름 유지) | `not_in_cmux` / `cmux_not_installed` / `open_failed` |
| 2 | `snapshot` | `cmux browser snapshot` | 읽기 | 동일 |
| 3 | `eval` | `cmux browser eval` | 읽기 | 동일 |
| 4 | `wait` | `cmux browser wait` | 읽기 | 동일 |
| 5 | `navigate` | `cmux browser navigate` | 네비 | 동일 |
| 6 | `click` | `cmux browser click` | 상호작용 | 동일 |
| 7 | `fill` | `cmux browser fill` | 상호작용 | 동일 |

**선택 5종** (E2E 보조 — 흔히 함께 호출):

| # | 서브명령 | cmux 원본 | 카테고리 | 비고 |
|---|---------|---------|---------|------|
| 8 | `open` | `cmux browser open` | 네비 | A 모드 신규 surface 열기 단독 노출 |
| 9 | `open-split` | `cmux browser open-split` | 네비 | 분할 오픈 |
| 10 | `reload` | `cmux browser reload` | 네비 | 새로고침 |
| 11 | `press` | `cmux browser press` | 상호작용 | 키 입력 |
| 12 | `get` | `cmux browser get` | 읽기 | 요소 텍스트/속성 조회 |

> **노출 제외 6종 (사유)**: `back`/`forward`/`url`/`type`/`select`/`hover`/`focus` — E2E 자동화 빈도가 낮고 (`type`은 `fill`로 대부분 대체, `back`/`forward`은 SPA 라우팅이 더 흔함, `select`/`hover`/`focus`는 `eval` + `wait` 조합으로 처리 가능), 알투 자동 선택 매트릭스에서 트리거 빈도가 낮음. 단순성 우선 원칙 (→ D-18 §2). 필요 시 후속 태스크에서 추가.

> **A/B/C 분기는 `eval`+`wait` 조합 + `lib/branch.sh` 헬퍼로만 다룬다 (별도 서브명령 비노출)** — test-browser.sh의 분기 흐름은 `examples/e2e-branch-auto.sh`로 보존하고, 알투가 호출할 때는 `cmux-tool snapshot` + `cmux-tool eval` 결과를 기반으로 직접 분기 결정한다. 새 서브명령 신설은 PLAN 단계의 사전 추상화에 해당하여 `[MUST]` `coding-principles.md` §2 단순성 우선 위반 (→ D-18 §2)

#### §2.2 디스패처 라우팅 로직 (run.sh + lib/dispatch.sh)

```
run.sh "$@"
  │
  ├─ $1이 http://* 또는 https://* → extract 서브명령으로 자동 라우팅 (R-2 호환 보장)
  │     → lib/dispatch.sh extract "$@"
  │
  ├─ $1이 --help / -h / 없음 → 사용법 JSON 출력 (서브명령 12+1종 목록 포함)
  │
  └─ $1이 알려진 서브명령 → lib/dispatch.sh "$@"
        ├─ extract  → run.sh의 현 흐름 (open/goto/wait/get/eval/tab close)
        ├─ snapshot → cmux browser snapshot
        ├─ eval     → cmux browser eval --script "..."
        ├─ wait     → cmux browser wait <selector|--load-state>
        ├─ navigate → cmux browser navigate <url>
        ├─ click    → cmux browser click <selector>
        ├─ fill     → cmux browser fill <selector> <value>
        ├─ open     → cmux browser open <url>
        ├─ open-split → cmux browser open-split <url>
        ├─ reload   → cmux browser reload
        ├─ press    → cmux browser press <key>
        └─ get      → cmux browser get <selector|attr>
```

레거시 호환 라우팅: 첫 인자가 URL이면 `extract` 호출과 동일하게 처리. `--surface <handle>` 사용 시도 `extract`로 라우팅 (TASK §R-2 AC — 기존 호출 시그니처 보존). (→ D-1, → D-5)

> `[MUST]` `opal/tools/cmux-tool/README.md` §안전 가드 (L124-132): "B/C 모드(사용자 surface 재사용)에서는 cmux browser <surface> tab close를 절대 호출하지 않는다." — 디스패처 재설계 후에도 이 가드는 `extract` 서브명령 내부에서 유지하며, 신규 명령은 surface를 직접 열지 않으므로 cleanup 대상이 아니다 (cmux 사용자가 직접 사용 중인 surface를 재사용하지 않음).

#### §2.3 출력 JSON 스키마 통일 (M-3 결정)

**공통 필드 5종** (모든 서브명령 공통):

| 필드 | 타입 | 설명 |
|------|------|------|
| `ok` | bool | 성공 여부 |
| `command` | string | 실행된 서브명령명 (`extract`/`snapshot`/`click` 등) |
| `surface` | string\|null | 사용된 surface 핸들. surface 무관 명령(`navigate` 등 전역)에서 null 가능 |
| `user_owned` | bool | `--surface` 핸들 명시 시 `true` (민감 정보 경고 시그널) — B/C 모드 보존 |
| `error` | string\|null | 실패 시 에러 코드 (성공 시 null 또는 필드 생략) |

**명령별 특화 필드** (예시):

| 서브명령 | 특화 필드 |
|---------|----------|
| `extract` | `method`(="cmux") / `mode`("A"/"B"/"C") / `title` / `final_url` / `content` / `bytes` / `wait_ms` — **기존 8필드 그대로 유지** (R-2 호환 보장) |
| `snapshot` | `snapshot_text` / `length` |
| `eval` | `result` (eval 반환값 string) / `script_len` |
| `wait` | `selector` / `elapsed_ms` / `matched`(bool) |
| `navigate` | `from_url` / `to_url` |
| `click`/`fill`/`press`/`hover` 등 | `selector` (해당 시) / `value` (해당 시) |
| `get` | `selector` / `value` |
| `open`/`open-split` | `new_surface` |
| `reload` | `before_url` / `after_url` |

성공 예시 (snapshot):
```json
{"ok":true,"command":"snapshot","surface":"surface:3","user_owned":true,"snapshot_text":"...","length":4096}
```

실패 예시 (공통 5필드):
```json
{"ok":false,"command":"click","surface":"surface:3","user_owned":true,"error":"wait_failed","detail":"selector #foo not found","fallback":"phase3"}
```

> 기존 extract 8필드 100% 보존 — TASK §R-2 AC ("기존 출력 JSON 8필드가 동일 키로 반환된다") 충족. 신규 명령은 `command` + `error` 필드를 정식 추가하지만 기존 호출자(wtm-agent)는 `command` 필드 미사용이므로 영향 없음.

#### §2.4 tools.md "트리거 조건" 표 정밀도 (M-4 결정)

알투 자동 도구 선택을 위한 **5행 매트릭스** (명령군 × 사용자 입력 패턴 × 우선 명령):

| 사용 시점 | 대표 사용자 문장 | 우선 명령 (cmux-tool) | 폴백 |
|----------|----------------|----------------------|------|
| **웹 크롤링** (HTML 본문 추출) | "URL 읽어줘", "사이트 내용 정리", "이 페이지 마크다운" | `cmux-tool extract <url>` | playwright-tool |
| **정보 수집** (구조화된 데이터 조회) | "스냅샷 떠줘", "현재 페이지 구조 보여줘" | `cmux-tool snapshot --surface <h>` | (없음 — 정보 조회만) |
| **웹 테스트** (단일 상호작용) | "로그인 버튼 눌러", "이메일 칸에 입력해" | `cmux-tool click <selector>` / `cmux-tool fill <selector> <value>` | playwright-tool |
| **E2E 자동화** (다단계 시나리오) | "회원가입 폼 테스트", "결제 흐름 자동화" | `examples/e2e-form-fill.sh` 또는 `cmux-tool fill + click + wait + snapshot` 조합 | playwright-tool |
| **로컬 SPA·동적 페이지** | "localhost:3000 분석", "Next.js 화면 확인" | `cmux-tool extract <url>` (localhost URL 자동 감지) | playwright-tool |

> 매트릭스 형식은 기존 `tools.md` `## xlsx-tool` §커맨드 표 (`opal/core/references/tools.md:17-30`)와 동일 골격. 알투 lazy-load 시 행 매칭으로 자동 선택 (→ D-4, D-16 §9)

#### §2.5 fallback 트리거 에러 코드 집합 (M-5 결정)

wtm-agent가 cmux-tool 실패 수신 시 자동으로 playwright-tool로 우회하는 에러 코드:

**자동 폴백 4종** (`fallback: "phase3"` 라벨 포함):

| 코드 | 종료값 | 폴백 사유 |
|------|--------|----------|
| `not_in_cmux` | 2 | `CMUX_SURFACE_ID` 미설정 — cmux 세션 외부 환경 |
| `cmux_not_installed` | 3 | cmux 바이너리 미설치 |
| `surface_parse_failed` | 5 | `cmux browser open` 출력 형식 변경 (버전 호환 문제) |
| `open_failed` | 5 | cmux 내부 오류 |

**입력 정정 필요 5종** (폴백 금지 — 즉시 사용자/오케스트레이터 에스컬레이션):

| 코드 | 종료값 | 처리 |
|------|--------|------|
| `usage` | 1 | 인자 오류 — 호출자 인터페이스 수정 필요 |
| `invalid_surface` | 4 | surface 핸들 형식 오류 — 호출자 입력 정정 |
| `goto_failed` | 6 | URL 유효성 문제 — fetch 재시도 의미 없음 |
| `wait_failed` | 7 | 페이지 로드 타임아웃 — 네트워크 또는 셀렉터 문제 |
| `eval_failed` | 8 | JS 스크립트 자체 오류 |

wtm-agent의 폴백 트리거 로직:
```bash
result=$(bash ~/.opal/tools/cmux-tool/run.sh extract <url>)
case $(echo "$result" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('error',''))") in
  not_in_cmux|cmux_not_installed|surface_parse_failed|open_failed)
    # Phase 2(playwright-tool)로 폴백
    ;;
  usage|invalid_surface|goto_failed|wait_failed|eval_failed)
    # 즉시 에스컬레이션 (status: blocked)
    ;;
esac
```

> 분류 근거: `opal/tools/cmux-tool/run.sh:79-89` (`not_in_cmux` `cmux_not_installed` 모두 `fallback:"phase3"` 포함) + run.sh:107-114 (`open_failed`/`surface_parse_failed`도 `fallback:"phase3"` 포함). 입력 정정 5종은 호출자 인터페이스/입력 문제이므로 다른 백엔드로 폴백해도 같은 실패 (→ D-1 L79-160)

> **SSOT 명시 (sparring 공격 5)**: `opal/tools/cmux-tool/run.sh`가 에러 코드 SSOT. `tools.md`(Step 6)·`opal-wtm-agent/AGENT.md`(Step 7)는 SSOT 인용·동기화 위치이며 직접 신설 금지. 신규 에러 코드 추가 시 (1) run.sh → (2) README.md → (3) tools.md → (4) AGENT.md 순으로 갱신.

> **silent fallback 정책 (캡틴 정책 — 2026-05-22 확정)**: cmux 미설치 또는 non-macOS 환경에서 wtm-agent는 **사용자 안내·유도 단계 없이 즉시 playwright-tool로 직행**한다. `command -v cmux` 단일 분기로 OS 감지(`uname -s`)와 설치 여부 검사를 동시 흡수 — macOS+cmux설치만 cmux-tool 시도, 그 외는 모두 playwright-tool. 결과 JSON `method` 필드만으로 사용된 백엔드를 식별 가능하므로 `summary`에 별도 표기 없음 (캡틴 Q1=b 결정).

> **적용 범위 — wtm-agent 경유 한정 (캡틴 정책 2026-05-22)**: 이 silent fallback 정책은 wtm-agent를 통한 호출 경로에만 적용된다. 알투/워커가 cmux-tool을 **단독 호출**할 때(`tools.md` §트리거 매트릭스 4행 — 정보 수집/웹 테스트/E2E 자동화/로컬 SPA)는 cmux-tool이 단일 책임으로 동작 — 미설치 시 에러 JSON(`{"ok": false, "error": "cmux_not_installed", "fallback": "phase2"}`)만 반환하고 자체 playwright 폴백을 수행하지 않는다. 단독 호출자(알투/워커)는 에러 JSON을 수신하여 자율 판단(다른 방법 시도/사용자 안내/blocked 처리). cmux-tool의 단일 책임(cmux browser 래퍼)을 유지하기 위함 — fallback 로직을 도구에 내장하면 단순성 원칙 위반.

#### §2.6 cmux-tool/ 하위 재배치 구조 (M-6 결정)

```
opal/tools/cmux-tool/
├── run.sh                          # 디스패처 진입점 (M-1)
├── README.md                       # 도구 사용자 진입점 (M-2)
├── lib/                            # 공통 헬퍼 (M-6 신규)
│   ├── dispatch.sh                 # 서브명령 라우팅 + 인자 파싱 (N-1)
│   ├── cmux-helpers.sh             # _lib.sh 흡수 (N-2)
│   ├── branch.sh                   # A/B/C 분기 로직 일반화 (N-3)
│   └── json.sh                     # python3 JSON 직렬화 헬퍼 (N-4)
├── examples/                       # 흡수된 레시피 (M-6 신규)
│   ├── e2e-form-fill.sh            # click+fill+wait+snapshot 조합 (N-5)
│   ├── e2e-branch-auto.sh          # A/B/C 분기 자동 결정 (N-6, test-browser.sh 원형)
│   └── claude-hooks.sample.json    # Claude Code hooks 3종 (N-7)
└── docs/                           # 통합 참조 문서 (M-6 신규)
    └── CMUX-REFERENCE.md           # CLI 18종 + Socket API + 단축키 + hooks 레시피 (N-8)
```

> install_dir 재귀 복사로 자동 배포 (→ D-7 `scripts/install-mac.sh:814-816`). chmod +x는 `lib/*.sh`와 `examples/*.sh` 모두 필요 (M-6 변경).

#### §2.7 자산 처분표 (M-7 결정)

| 원본 자산 | 처분 | 신규 위치 / 사유 |
|----------|------|-----------------|
| `tasks/007-.../cmux/README.md` | 폐기 | 자체 분류 정보는 본 PLAN §2.7 표에 흡수됨 |
| `tasks/007-.../cmux/docs/CMUX.md` | 부분 흡수 | §1 설치/§3 단축키/§6 알림 [일반] 섹션만 → `opal/tools/cmux-tool/docs/CMUX-REFERENCE.md` §부록. MAMS 전용 섹션(§2/§4/§5-4/§5-5/§7/§8) 폐기 |
| `tasks/007-.../cmux/docs/CMUX-TOOLS.md` | 전량 흡수 | → `opal/tools/cmux-tool/docs/CMUX-REFERENCE.md` 본문 (CLI 18종 + Socket API + 단축키 + hooks 레시피) |
| `tasks/007-.../cmux/scripts/_config.sh` | 폐기 | MAMS 포트·경로 하드코딩 |
| `tasks/007-.../cmux/scripts/_lib.sh` | 전량 흡수 | → `opal/tools/cmux-tool/lib/cmux-helpers.sh` (start_surface/verify_surface/ready_pattern_for) |
| `tasks/007-.../cmux/scripts/start-all.sh` | 폐기 | 서버 일괄 기동 워크플로우는 cmux-tool 디스패처 범위 외 (별도 후속 가능) |
| `tasks/007-.../cmux/scripts/stop-all.sh` | 폐기 | 동일 |
| `tasks/007-.../cmux/scripts/open-dev.sh` | 폐기 | 동일 |
| `tasks/007-.../cmux/scripts/test-browser.sh` | 전량 흡수 | (1) 분기 로직 → `lib/branch.sh` 일반화 (2) 원형 보존 → `examples/e2e-branch-auto.sh` |
| `tasks/007-.../cmux/scripts/analyze-log.sh` | 폐기 | 로그 분석 워크플로우 — cmux-tool 디스패처 범위 외 |
| `tasks/007-.../cmux/config/cmux.json` | 폐기 | MAMS 팔레트 — 도구 디스패처 영역과 무관 |
| `tasks/007-.../cmux/config/ghostty.config.sample` | 부분 흡수 | 본문은 폐기, 사용자 환경 설정 안내는 docs/CMUX-REFERENCE.md §부록에 외부 링크 형태로 1줄 흡수 |
| `tasks/007-.../cmux/config/claude-hooks.sample.json` | 전량 흡수 | → `opal/tools/cmux-tool/examples/claude-hooks.sample.json` |
| `tasks/007-.../cmux/logs/.gitkeep` | 폐기 | MAMS 로그 디렉토리 — 본 태스크 범위 외 |

흡수 출처는 신규 파일 상단 헤더 주석 + `opal/tools/cmux-tool/README.md` §흡수 자산 출처 표에서 1:1 매핑 보존 (TASK §R-7 AC).

> EXECUTE Step 10에서 `tasks/007-.../cmux/` 폴더 자체 제거 — 흡수 자산 추적성은 (1) 신규 파일 헤더 주석 (2) README §흡수 자산 출처 표 두 채널에서 보존 (TASK §제약조건 §출처 추적).

#### §2.8 wtm-agent 2단 체인 재배선 (M-1 결정)

> `[MUST]` 캡틴 발화: "cmux-tool 1순위, fallback playwright-tool" → WebFetch 완전 제거 채택. 보조 위치 강등(M-1 b안)을 거부한 사유: (1) cmux 미설치 환경 + WebFetch 보조 시점 결정 매트릭스가 3분기로 늘어남 → 단순성 우선 위반 (→ D-18 §2). (2) `--browser`/`--surface` 모드 사용자가 다수이므로 WebFetch 적용 빈도가 낮음 (D-6 `skills/web-to-markdown/SKILL.md:79-82` localhost/SPA 자동 감지).

새 Phase 흐름:

```
URL/--surface 입력
  │
  ├─ Phase 1: cmux-tool (1순위)
  │     ├─ bash ~/.opal/tools/cmux-tool/run.sh extract <url|--surface <h> [url]> ...
  │     ├─ {"ok": true, "content": ...} → MD 정제 → 저장
  │     └─ {"ok": false, "error": "<폴백코드>", "fallback": "phase2"} → Phase 2
  │
  └─ Phase 2: playwright-tool CLI (fallback)
        ├─ bash ~/.opal/tools/playwright-tool/run.sh {url} --mode {mode}
        ├─ {"ok": true} → MD 정제 → 저장
        └─ {"ok": false} → 사용자 에스컬레이션
```

- `method` 유효값 갱신: `cmux` / `playwright-cli` (← 기존 `cmux` / `webfetch` / `playwright-cli`에서 `webfetch` 삭제).
- `fallback` 라벨 갱신: cmux-tool run.sh의 `fallback: "phase3"` → `fallback: "phase2"` (이름 변경). 단, 도구 내부 호환을 위해 run.sh는 `"phase2"` + `"phase3"` 둘 다 출력하지 않고 **`"phase_next"` 등 호칭 무관한 라벨로 통일**하는 옵션도 검토. EXECUTE 단계에서 최소 변경 선택: 라벨 자체는 `phase2`로 단순 치환 (단순성 우선 → D-18 §2)

> `cmux-tool/run.sh`의 fallback 라벨은 wtm-agent의 호칭 의존성이 있으므로 양쪽 동시 변경 (TASK §R-3 AC — 호칭 잔재 없이 갱신)

#### §2.9 install-mac.sh 영향 점검 (R-6 충족 설계)

현 `scripts/install-mac.sh:834-842` 블록은 `cmux-tool/run.sh` 단일 파일만 chmod +x 처리한다 (다른 PC 알투의 006 install-linux 작업으로 playwright-tool 블록이 변경되어 cmux-tool 블록이 1줄 시프트됨 — `install-mac.sh:820-824` playwright 블록 + `:834-842` cmux 블록). 신규 lib/, examples/ 하위 .sh 파일이 추가되면 다음 블록 확장 필요:

```bash
# ── cmux-tool 실행 권한 ──
local cmux_run="$opal_home/tools/cmux-tool/run.sh"
if [[ -f "$cmux_run" ]]; then
    chmod +x "$cmux_run"
    success "cmux-tool run.sh 실행 권한 설정"
fi

# 신규: lib/ 및 examples/ 실행 권한
local cmux_lib_dir="$opal_home/tools/cmux-tool/lib"
local cmux_examples_dir="$opal_home/tools/cmux-tool/examples"
for sh_file in "$cmux_lib_dir"/*.sh "$cmux_examples_dir"/*.sh; do
    [[ -f "$sh_file" ]] && chmod +x "$sh_file"
done
success "cmux-tool lib/, examples/ 실행 권한 설정"

if ! command -v cmux &>/dev/null; then
    info "cmux 미감지 — cmux-tool 사용 시 https://cmux.com/ 또는 https://github.com/manaflow-ai/cmux 에서 설치 필요"
fi
```

> `install_dir`가 디렉토리 재귀 복사를 처리하므로 신규 하위 디렉토리는 자동 배포된다 (`scripts/install-mac.sh:814-816`). chmod만 명시 추가하면 완료. (→ D-7)

---

## 3. 실행 체크리스트

> 총 10개 Step | Phase 4개

| Phase | Step | 실행 | 비고 |
|-------|------|------|------|
| 1 | 1 | 순차 | docs/CMUX-REFERENCE.md (다른 파일이 참조) |
| 2 | 2 | 순차 | lib/ 4파일 (run.sh가 의존) |
| 3 | 3 | 순차 | run.sh 디스패처 (lib/ 의존) |
| 4 | 4, 5 | 병렬 | examples/, README.md (독립 파일) |
| 5 | 6, 7, 8 | 병렬 | tools.md, AGENT.md, SKILL.md (각각 독립 파일) |
| 6 | 9 | 순차 | install-mac.sh (run.sh + lib/ + examples/ 의존) |
| 7 | 10 | 순차 | cmux/ 폴더 정리 (모든 흡수 완료 후) |

### Step 1: docs/CMUX-REFERENCE.md 작성 (CLI/Socket API 통합 참조)

- [x] 완료
- **파일**: `opal/tools/cmux-tool/docs/CMUX-REFERENCE.md`
- **작업 내용**: CMUX-TOOLS.md(`tasks/007-.../cmux/docs/CMUX-TOOLS.md:1-283`) 전량 흡수 + CMUX.md(`tasks/007-.../cmux/docs/CMUX.md`) §1 설치/§3 단축키/§6 알림 [일반] 섹션 흡수. 5섹션 구성: CLI 명령 / 단축키 / 브라우저 CLI 18종 / hooks 레시피 / Socket API. 헤더에 흡수 출처(원본 경로) 주석 + 변경이력 표 v1.0 (006) 추가.
- **완료 기준**: 파일이 존재하고 CMUX-TOOLS.md의 §1~§5 모든 표가 보존되며, 흡수 출처 주석이 첫 줄에 있다. `head -5 opal/tools/cmux-tool/docs/CMUX-REFERENCE.md`로 확인.
- **테스트**: `cat opal/tools/cmux-tool/docs/CMUX-REFERENCE.md | grep -c "cmux browser"` ≥ 18 (서브명령 18종 모두 언급)
- **의존**: 없음

### Step 2: lib/ 공통 헬퍼 4파일 작성

- [x] 완료
- **파일**:
  - `opal/tools/cmux-tool/lib/dispatch.sh` (N-1) — 서브명령 라우팅
  - `opal/tools/cmux-tool/lib/cmux-helpers.sh` (N-2) — _lib.sh 흡수
  - `opal/tools/cmux-tool/lib/branch.sh` (N-3) — A/B/C 분기 결정
  - `opal/tools/cmux-tool/lib/json.sh` (N-4) — JSON 직렬화
- **작업 내용**:
  - dispatch.sh: case 라우팅 12+1종 (extract/snapshot/eval/wait/navigate/click/fill/open/open-split/reload/press/get + 레거시 URL 자동 라우팅). 공통 인자 파싱(`--surface`/`--mode`/`--wait`).
  - cmux-helpers.sh: `tasks/007-.../cmux/scripts/_lib.sh:11-103`의 start_surface/verify_surface/ready_pattern_for 3함수 흡수. 헤더에 출처 주석.
  - branch.sh: `tasks/007-.../cmux/scripts/test-browser.sh:65-100`의 분기 결정 로직 흡수 — 함수명 `decide_branch <target_url>` → A/B/C/D 출력.
  - json.sh: run.sh L178-207 패턴 흡수 — `json_emit <command> <ok> <kv-pairs>` 함수.
- **완료 기준**: 4개 파일 모두 존재하고 각각 #!/usr/bin/env bash + 헤더 주석 + 흡수 출처(있는 경우) + 함수 정의를 갖는다.
- **테스트**: `bash -n opal/tools/cmux-tool/lib/*.sh` (syntax check 통과)
- **의존**: Step 1 (참조 문서 먼저)

### Step 3: run.sh 디스패처 재설계

- [x] 완료
- **파일**: `opal/tools/cmux-tool/run.sh`
- **작업 내용**: 현 흐름을 디스패처로 재구성. 1) 첫 인자가 http(s):// → extract로 자동 라우팅, 2) 첫 인자가 알려진 서브명령 → lib/dispatch.sh로 위임, 3) --help → 사용법 JSON(서브명령 12+1종 목록 + 공통 필드 5종). 기존 extract 흐름(open/goto/wait/get/eval/tab close + A/B/C 모드 결정 + user_owned 시그널 + B/C cleanup 금지 가드)은 `lib/dispatch.sh`의 `extract` 케이스에 보존. fallback 라벨 `"phase3"` → `"phase2"` 치환 (M-1과 연동).
- **완료 기준**:
  - `bash ~/.opal/tools/cmux-tool/run.sh --help` 출력 JSON에 12+1종 서브명령 모두 포함.
  - `bash ~/.opal/tools/cmux-tool/run.sh https://example.com` 호출이 기존 extract와 동일한 8필드 JSON 반환 (R-2 호환 — `ok`/`method`/`mode`/`surface`/`user_owned`/`title`/`final_url`/`content`/`bytes`/`wait_ms`).
  - `grep -cE 'tab close' opal/tools/cmux-tool/lib/dispatch.sh` 결과 호출 위치가 모두 `A)` 케이스 내부 (B/C cleanup 금지 가드 보존).
- **테스트**: cmux 미설치 환경에서 `bash opal/tools/cmux-tool/run.sh https://example.com` → `{"ok":false,"error":"cmux_not_installed","fallback":"phase2"}` 출력 확인 (정적 검증)
- **의존**: Step 2

### Step 4: examples/ E2E + hooks 샘플 작성

- [x] 완료
- **파일**:
  - `opal/tools/cmux-tool/examples/e2e-form-fill.sh` (N-5)
  - `opal/tools/cmux-tool/examples/e2e-branch-auto.sh` (N-6)
  - `opal/tools/cmux-tool/examples/claude-hooks.sample.json` (N-7)
- **작업 내용**:
  - e2e-form-fill.sh: CMUX.md §7-A(L301-356)와 test-browser.sh §click/fill/wait/snapshot 조합을 통합한 회원가입 폼 E2E 레시피 (cmux-tool 디스패처 호출 형태로 재작성).
  - e2e-branch-auto.sh: `tasks/007-.../cmux/scripts/test-browser.sh:1-133` 원형 보존 — cmux-tool/lib/branch.sh 함수를 source해서 호출하는 형태로 일반화 (변수 치환).
  - claude-hooks.sample.json: `tasks/007-.../cmux/config/claude-hooks.sample.json` 그대로 흡수하되 `subtitle: 'MAMS'`를 generic 값(`'OPAL'`)으로 치환.
- **완료 기준**: 3개 파일 모두 존재. bash 파일은 `bash -n`로 syntax check 통과. JSON은 `python3 -m json.tool` 검증 통과.
- **테스트**: `bash -n opal/tools/cmux-tool/examples/*.sh && python3 -m json.tool opal/tools/cmux-tool/examples/claude-hooks.sample.json > /dev/null`
- **의존**: Step 2 (lib/branch.sh 의존)

### Step 5: README.md 갱신

- [x] 완료
- **파일**: `opal/tools/cmux-tool/README.md`
- **작업 내용**: 디스패처 구조 + 12+1종 서브명령 사용법 + 공통 JSON 5필드 + 특화 필드 표 + 흡수 자산 위치·출처 표 + 변경이력 v1.1 (006). 기존 3모드(A/B/C) 섹션은 `extract` 서브명령 하위로 재배치. 안전 가드(B/C cleanup 금지) 섹션 유지.
- **완료 기준**: README에 12+1종 서브명령이 모두 사용법 예시로 등장하고, 흡수 자산 표(11행) + 변경이력 행 추가.
- **테스트**: `grep -cE 'cmux-tool/run.sh (extract|snapshot|eval|wait|navigate|click|fill|open|open-split|reload|press|get)' opal/tools/cmux-tool/README.md` ≥ 12
- **의존**: Step 2, 3 (구조 확정 후)

### Step 6: tools.md 신규 등록

- [x] 완료
- **파일**: `opal/core/references/tools.md`
- **작업 내용**: 기존 3개 도구(xlsx/state/code-scan) 사이 또는 끝에 `## cmux-tool` 섹션 신규 추가. 골격: 용도 / 실행 경로 / 소스 경로 / 의존성 / 커맨드(12+1종) / 출력 형식(공통 5필드 + 특화) / 트리거 조건 표(§2.4 5행 매트릭스) / 사용 예시 / 종료 코드 / 에러 코드(폴백 4종 + 입력 정정 5종). 변경이력 v1.5 (006) 행 추가.
- **완료 기준**: tools.md에 `## cmux-tool` 섹션 존재하고 §2.4 트리거 조건 5행 표 포함. 알투가 lazy-load 시 행 매칭으로 자동 선택 가능한 수준.
- **테스트**: `grep -A 5 '^## cmux-tool' opal/core/references/tools.md | grep -c '트리거 조건'` = 1
- **의존**: Step 3, 5 (디스패처 인터페이스 확정 후)

### Step 7: wtm-agent AGENT.md 재배선

- [x] 완료
- **파일**: `opal/agents/opal-wtm-agent/AGENT.md`
- **작업 내용**:
  - YAML frontmatter description: "Phase 1(WebFetch) → Phase 2(cmux, 조건부) → Phase 3(playwright-tool CLI) 폴백 전략" → "Phase 1(cmux-tool, 1순위) → Phase 2(playwright-tool, fallback) 2단 폴백 전략"
  - L13~52 실행 프로세스: Step 5 "Phase 폴백 실행"의 Phase 정의 갱신 — Phase 1(WebFetch) 섹션 삭제, Phase 2→1(cmux-tool), Phase 3→2(playwright-tool).
  - **silent fallback 분기 명시 (캡틴 정책 2026-05-22)** — Phase 1 진입 직전 `command -v cmux >/dev/null 2>&1` 검사 추가. 결과 false면 Phase 1 skip하고 Phase 2 직행 (사용자 안내·유도 없음). 결과 true면 Phase 1 시도 후 4종 폴백 코드 발생 시 Phase 2 (기존 로직).
  - 결과 반환 JSON `method` 유효값: `cmux|webfetch|playwright-cli` → `cmux|playwright-cli`. `summary` 필드에 cmux 미감지 표기 **추가하지 않음** (캡틴 Q1=b).
  - 폴백 트리거 에러 코드 명시 추가 (§2.5 4종) — Phase 1 결과의 error가 `not_in_cmux|cmux_not_installed|surface_parse_failed|open_failed` 4종 중 하나일 때만 Phase 2로 폴백, 나머지(`usage|invalid_surface|goto_failed|wait_failed|eval_failed`)는 status: blocked.
  - **극단 케이스**: cmux 미설치 + playwright-tool도 미설치(install-mac.sh 미실행 환경) → `status: blocked` + 명확 안내 (caption: "두 도구 모두 미설치 — install-mac.sh 실행 또는 cmux 설치 권장").
  - WebFetch 위치: 완전 제거 명시. 의사결정 표가 단순화됨을 §실행 프로세스 머리말에 1줄 추가.
  - 변경이력 v1.1 (007) 행 추가.
- **완료 기준**: AGENT.md에 "Phase 1: WebFetch" 호칭 잔재가 없고, `method` JSON 유효값에 `webfetch` 없음. 폴백 트리거 4종 코드 명시. silent fallback 분기 코드 예시 포함.
- **테스트**: `grep -c "WebFetch\|webfetch" opal/agents/opal-wtm-agent/AGENT.md` = 0 (호칭 완전 제거) / `grep -c "command -v cmux" opal/agents/opal-wtm-agent/AGENT.md` ≥ 1 (silent 분기 명시)
- **의존**: Step 3, 6 (cmux-tool 인터페이스·tools.md 확정 후)

### Step 8: web-to-markdown SKILL.md 일관성 갱신

- [x] 완료
- **파일**: `skills/web-to-markdown/SKILL.md`
- **작업 내용**: AGENT.md(M-4)와 동일한 호칭/순서 갱신. L6 description, L24~33 호출 인터페이스(`//wtm` 명령 설명), L66~82 추출 모드 표, L86~115 실행 흐름 다이어그램, L119~232 Phase 섹션(Phase 1 WebFetch 섹션 삭제, Phase 2→1, Phase 3→2). **`--browser` 모드 처리 (sparring 공격 4 검증 결과 반영)** — `--browser`는 SKILL.md L26-27·L73·L79-81에서 4곳 외부 인터페이스로 명시되어 있음(`grep -rn '\-\-browser' skills/` 결과). 단순 제거 시 외부 호출자(`//wtm --browser <url>` 사용자) breaking change 발생. **결정: 모드 자체는 보존하되 의미를 갱신** — "WebFetch 생략" → "기본 동작과 동일(2단 체인). 하위 호환 alias로 유지". 변경이력 행에 "v1.6: WebFetch 제거에 따라 `--browser` 의미가 기본 동작과 일치 — alias로 deprecated 표기" 명시.
- **완료 기준**: SKILL.md에 "Phase 1: WebFetch" 호칭 잔재 없음, `webfetch` `WebFetch` 문자열이 호출 예시 외에는 등장하지 않음. `--browser` 모드는 보존되며 "deprecated alias — 기본 동작과 동일" 명시.
- **테스트**: `grep -c "Phase 1: WebFetch\|webfetch" skills/web-to-markdown/SKILL.md` = 0 / `grep -c '\-\-browser' skills/web-to-markdown/SKILL.md` ≥ 4 (보존 검증)
- **의존**: Step 7 (AGENT.md 우선 — SSOT가 AGENT.md임)

### Step 9: install-mac.sh 배포 처리 갱신

- [x] 완료
- **파일**: `scripts/install-mac.sh`
- **작업 내용**: **L834-842 cmux-tool 블록 확장** (다른 PC 알투의 006 install-linux 변경 후 시프트된 줄번호 — playwright-tool 블록이 L820-824로 확장된 영향) — `cmux-tool/lib/*.sh` + `cmux-tool/examples/*.sh` 일괄 chmod +x. 안내 메시지 generic 표현으로 갱신 ("Phase 2(cmux) 사용 시" → "cmux-tool 사용 시"). 헤더 변경이력 v2.3 추가.
- **완료 기준**: install-mac.sh 실행 시 `~/.opal/tools/cmux-tool/lib/*.sh`와 `examples/*.sh` 모두 실행 권한이 부여된다. 안내 메시지에서 "Phase 2(cmux)" 잔재 제거.
- **테스트**: `ls -l ~/.opal/tools/cmux-tool/lib/*.sh ~/.opal/tools/cmux-tool/examples/*.sh | awk '{print $1}' | grep -c '^-rwxr'` = (실행 권한 파일 수)
- **의존**: Step 2, 4 (lib/ + examples/ 생성 후)

### Step 10: tasks/007-.../cmux/ 인풋 폴더 정리

- [x] 완료
- **파일**: `tasks/007-260520-opp-cmux-tool-generic-expansion/cmux/` (디렉토리 전체)
- **작업 내용**: **사전 의무 (R-T5 sparring 검증 반영)** — `rm -rf` 직전 `git add tasks/007-260520-opp-cmux-tool-generic-expansion/cmux/` + 사용자 확인 후 commit하여 git 히스토리 보존을 강제. commit 후에야 §2.7 처분표 D-1~D-11 흡수 완료를 검증하고 원본 폴더를 제거 (`rm -rf tasks/007-.../cmux/`). 흡수 출처 추적은 (1) 신규 파일 헤더 주석 (2) cmux-tool/README.md §흡수 자산 출처 표 (3) git 히스토리 세 채널 유지.
- **완료 기준**: `tasks/007-260520-opp-cmux-tool-generic-expansion/cmux/` 폴더가 존재하지 않거나 빈 상태. **`git log -- tasks/007-.../cmux/` 출력 ≥ 1 commit (사전 add 검증)**. EXECUTE Step 9 산출물 changed_files 목록에 모든 흡수 출처 파일이 추적됨.
- **테스트**: `ls tasks/007-260520-opp-cmux-tool-generic-expansion/cmux/ 2>/dev/null | wc -l` = 0 / `git log --oneline -- tasks/007-.../cmux/ | wc -l` ≥ 1
- **의존**: Step 1~9 모두 완료 후

---

## 4. QA 체크리스트

### 기능 테스트

- [x] **R-1 충족**: `bash ~/.opal/tools/cmux-tool/run.sh --help` 출력 JSON에 12+1종 서브명령 사용법이 모두 포함되어 있다 (네비/상호작용/읽기 각 카테고리 최소 1종 이상)
- [x] **R-1 흡수 출처**: cmux-tool/lib/, examples/, docs/ 신규 파일 모두 헤더 주석에 `tasks/007-.../cmux/...` 원본 경로가 명시되어 있다 (EXECUTE changed_files에서 흡수 출처 추적 가능)
- [x] **R-2 호환**: `bash ~/.opal/tools/cmux-tool/run.sh https://example.com` (URL 단독) 호출이 기존 extract와 동일한 8필드 JSON 반환 — `ok`/`method`/`mode`/`surface`/`user_owned`/`title`/`final_url`/`content`/`bytes`/`wait_ms` 키가 모두 존재
- [x] **R-2 호환**: `bash ~/.opal/tools/cmux-tool/run.sh --surface surface:3` (B 모드) 호출이 기존 동작과 동일
- [x] **R-3 wtm-agent 일관성**: AGENT.md / SKILL.md 양쪽에서 "Phase 1: WebFetch" 호칭 잔재가 없다. fallback 트리거 4종 에러 코드가 AGENT.md에 명시되어 있다
- [x] **R-3 WebFetch 처리**: AGENT.md에 "WebFetch 완전 제거" 결정이 명시되어 있다 (M-1 (a)안)
- [x] **R-4 tools.md 등록**: `opal/core/references/tools.md`에 `## cmux-tool` 섹션이 존재하고 기존 3개 도구(xlsx/state/code-scan)와 동일한 골격(용도/실행 경로/소스 경로/의존성/커맨드/출력 형식/사용 예시/종료 코드)을 갖는다
- [x] **R-4 트리거 조건**: tools.md `## cmux-tool` 섹션에 §2.4 5행 트리거 매트릭스가 명시되어 있다 (웹 크롤링/정보 수집/웹 테스트/E2E/로컬 SPA)
- [x] **R-5 README**: cmux-tool/README.md에 12+1종 서브명령 사용법·예시·출력 스키마·에러 코드가 기재되고, 흡수 자산 위치·출처 표가 포함되어 있다. 변경이력 v1.1 (006) 행 추가
- [x] **R-6 install**: install-mac.sh 재실행 시 `~/.opal/tools/cmux-tool/lib/`, `examples/`, `docs/` 디렉토리가 모두 배포되고 .sh 파일에 chmod +x가 적용된다
- [x] **R-6 fallback 안내**: cmux 미설치 환경에서 install-mac.sh 안내 메시지가 generic 표현("cmux-tool 사용 시")으로 일관 출력
- [x] **R-7 cmux/ 정리**: `tasks/007-.../cmux/` 폴더가 정리되거나 후속 보류 자산만 남음. 흡수 자산은 모두 cmux-tool/ 하위 정확한 경로에 존재
- [x] **안전 가드**: `extract` 서브명령(B/C 모드)에서 `cmux browser <surface> tab close` 호출이 절대 발생하지 않는다 (정적 검증 — A) 케이스 내부에서만 호출)

### 일관성 테스트

- [x] **호칭 일관성**: AGENT.md ↔ SKILL.md ↔ tools.md 3개 문서에서 Phase 호칭(`Phase 1: cmux-tool`, `Phase 2: playwright-tool`)이 동일하게 표기됨
- [x] **에러 코드 일관성**: cmux-tool/run.sh의 9종 에러 코드 ↔ README.md 에러 코드 표 ↔ tools.md 에러 코드 표 ↔ AGENT.md fallback 트리거 코드가 모두 동일 식별자 사용
- [x] **JSON 스키마 일관성**: 신규 서브명령 모두 공통 5필드(`ok`/`command`/`surface`/`user_owned`/`error`) + 특화 필드 패턴 준수. extract는 기존 8필드 보존
- [x] **흡수 출처 추적성**: 신규 파일 헤더 주석의 원본 경로 ↔ README §흡수 자산 출처 표 두 채널이 일치
- [x] **CONVENTIONS 일관성**: 파일/폴더 이름 kebab-case (lib/, examples/, docs/, e2e-form-fill.sh, claude-hooks.sample.json 등), Python 파일은 snake_case (해당 없음). 코드/변수/필드명 English (서브명령 `extract`/`snapshot` 등). 문서 본문 한국어 (→ `docs/CONVENTIONS.md` §언어 규칙)
- [x] **플랫폼 분기 격리**: 신규 lib/*.sh, examples/*.sh, README, AGENT.md, SKILL.md 본문에 Claude/Cursor/Gemini 등 플랫폼 분기 조건문이 없다 (→ `docs/CONVENTIONS.md` §플랫폼 분기 격리)
- [x] **변경이력 작성 의무**: 수정된 모든 스킬·에이전트·참조 문서(`opal/agents/opal-wtm-agent/AGENT.md`, `skills/web-to-markdown/SKILL.md`, `opal/tools/cmux-tool/README.md`, `opal/core/references/tools.md`, `scripts/install-mac.sh`)에 변경이력 행(`YYYY-MM-DD HH:mm` KST + semver + 태스크 번호 `(006)`) 추가됨

### 문서 품질

- [x] **한국어 본문 + 영어 코드/필드명** 규칙을 따르는가 (→ `docs/CONVENTIONS.md` §언어 규칙)
- [x] **kebab-case 파일/폴더 네이밍** 규칙을 따르는가 (lib/, examples/, docs/, e2e-form-fill.sh, cmux-helpers.sh, branch.sh, dispatch.sh, json.sh, claude-hooks.sample.json, CMUX-REFERENCE.md)
- [x] **YAML frontmatter** (해당 시 — AGENT.md): name/description/model 키가 올바르게 갱신됨
- [x] **인용 규칙**: PLAN §1 참조 문서 테이블 + §2 인라인 인용 + §1 끝의 [MUST] 원문 인용이 모두 작성되어 있다 (→ `opal/core/references/harness/citation-rules.md` §3.1, §3.2, §2.4)
- [x] **단순성 검증**: PLAN 설계에 사변적 추가·미래 대비·불필요한 레이어가 없다 (→ `opal/core/references/harness/coding-principles.md` §2)
- [x] **외과적 검증**: EXECUTE 시 PLAN.md 범위 밖 파일이 수정되지 않는다 (→ `opal/core/references/harness/coding-principles.md` §4)

---

## 5. 리스크 및 대응

| # | 리스크 | 영향 | 대응 방안 |
|---|--------|------|----------|
| R-T1 | cmux 공식 명령 시그니처가 버전 업그레이드로 변경 (현재 ≥ 0.64.3 가정) — `cmux browser snapshot`/`get`/`eval` 등의 플래그 변경 가능성. **sparring 공격 3 검증 결과: 현재 환경에 cmux 미설치(`command -v cmux` 결과 없음)로 PLAN 단계 spot-check 불가** | 신규 서브명령 12종이 일제히 동작 불능 | (1) **PLAN 단계 검증을 외부 SSOT(`[cmux Browser Automation](https://cmux.com/ko/docs/browser-automation)` — D-20)에 위임** — EXECUTE 워커가 lib/dispatch.sh 작성 직전 D-20 문서 WebFetch로 18종 시그니처를 최종 검증한다 (EXECUTE Step 2 작업 내용에 추가). (2) EXECUTE 시 lib/dispatch.sh에서 cmux 명령을 호출하기 전 `cmux browser <sub> --help`로 런타임 검증 옵션 추가 (CMUX-TOOLS.md L20~23 권장사항). (3) 에러 코드 추가 정의 (`cmux_subcommand_unsupported`) 검토 — 단, 본 태스크 범위는 cmux ≥ 0.64.3 기준. 후속 태스크에서 버전별 어댑터 분리 가능 |
| R-T2 | WebFetch 완전 제거(M-1 a안) 후 fallback 정책 — **캡틴 정책 2026-05-22 확정**: (1) playwright는 install-mac.sh 자동 설치 흐름 그대로 유지 (Python 패키지 + Chromium best-effort) — `requirements.txt:25`에 `playwright>=1.40.0` 강제 + `install-mac.sh:976-981`에 `playwright install chromium` 자동 시도. (2) cmux는 사용자 선택 옵션 — install-mac.sh가 강제 설치하지 않음. (3) wtm-agent는 호출 시점에 `command -v cmux`로 감지 — 설치 시 cmux-tool 1순위, **미설치 시 사용자 유도 없이 silent로 playwright-tool 직행** | wtm-agent 호출 실패 가능성은 install-mac.sh 미실행 사용자에 한정 | (1) AGENT.md에 silent fallback 분기 명시 — `command -v cmux` 검사 + 결과에 따른 즉시 라우팅. (2) playwright마저 미설치(install-mac.sh 미실행)인 극단 경우만 `status: blocked` + 명확한 설치 안내. (3) wtm-agent 결과 JSON `method` 필드(`cmux`/`playwright-cli`)로 사용된 백엔드 추적 가능 — `summary` 별도 표기 없음 (캡틴 Q1=b) |
| R-T3 | fallback 라벨 `phase3` → `phase2` 치환이 wtm-agent 외 다른 소비자에게 영향 | 잠재적 호환성 문제 | EXECUTE 시 grep으로 전체 코드베이스 검색 — `grep -rn 'phase3' opal/ skills/ agents/` 결과 wtm-agent만 단독 소비 확인 후 진행. 다른 소비자 발견 시 라벨 변경 거부 |
| R-T4 | A/B/C 분기 흐름을 서브명령으로 노출하지 않는 결정이 사용자 직관과 어긋날 수 있음 (TASK §M-2 명시 옵션) | 사용자가 "분기 자동 결정"을 한 서브명령으로 기대 | examples/e2e-branch-auto.sh를 제공하고 README/tools.md 트리거 매트릭스에서 "분기 자동 결정"은 `examples/e2e-branch-auto.sh` 호출로 안내. 후속 태스크에서 `cmux-tool branch <url>` 신규 서브명령으로 정식 노출 검토 |
| R-T5 | cmux/ 인풋 폴더 자체 제거(Step 10) 시 흡수 출처 정보의 git 추적성 손실. **sparring 공격 1 검증 결과: `git ls-files tasks/007-.../cmux/` = 0건(untracked 확정), `git status` = `?? tasks/007-...` — git에 commit되지 않은 상태로 `rm -rf` 시 영구 손실 가능** | EXECUTE 완료 후 원본 폴더가 git에서 사라져 사후 검증 어려움 | **EXECUTE Step 10 직전(또는 Step 1 직전) `git add tasks/007-260520-opp-cmux-tool-generic-expansion/` + commit 의무화 — git 히스토리 보존을 강제**. 이후 `git log -- tasks/007-.../cmux/`로 사후 추적 가능. 또한 신규 파일 헤더 주석의 원본 경로 + README §흡수 자산 출처 표 두 채널이 SSOT 역할 |
| R-T6 | 단순성 vs 노출 범위 — 12+1종 노출 결정이 과한지 또는 부족한지 | 자동 트리거 정밀도 또는 유지보수 부담 | TASK §R-1 AC "PLAN에서 확정된 N개 이상의 서브명령(네비/상호작용/읽기 각 카테고리에서 최소 1종 이상)" 충족. 12종은 cmux 18종 중 67%로 자동화 핵심만 노출 (`type`/`select`/`hover`/`focus`/`back`/`forward`/`url` 제외 — 단순성 우선 §D-18) |
| R-T7 | 영역 간 용어 일관성 — `tools.md`의 "트리거 조건" 표 용어 ↔ AGENT.md의 Phase 호칭 ↔ README.md의 서브명령 분류명 | 알투/워커가 다른 토큰으로 호출 시 매핑 실패 | citation-rules.md §7 영역 간 용어 일관성 검토 적용. EXECUTE 시 3개 문서에서 동일 개념의 토큰을 통일 (예: "웹 크롤링" / "extract" / "Phase 1" 매핑). decision_required 발생 시 캡틴 에스컬레이션 |
| R-T8 | cmux **macOS 전용** — Linux/Windows 사용자(다른 PC 알투의 006 install-linux 흐름)는 cmux 영역 진입 자체가 없어야 함 | wtm-agent가 non-macOS에서 cmux를 호출 시도 시 `cmux_not_installed` 폴백으로 흡수되지만 비효율 | **`command -v cmux` 단일 분기로 OS 감지(`uname -s == "Darwin"`)와 설치 여부 검사를 동시 흡수** — macOS+cmux설치만 Phase 1 진입, 그 외(non-macOS · macOS+미설치)는 모두 Phase 2 직행. OS 명시 분기 코드 불필요 (캡틴 정책 2026-05-22 확정). install-linux 흐름과 자연 정합 — Linux 사용자는 자동으로 playwright-tool 사용 |

---

## 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-05-20 15:00 | 초기 작성 — TASK.md R-1~R-7 + M-1~M-7 결정 + 10 Step 실행 체크리스트 + QA 체크리스트 + 7 리스크 (006) |
| v1.1 | 2026-05-21 14:15 | **006→007 재채번** (다른 PC 알투의 006 install-linux와 충돌 회피, MEMORY.md last_task_number 7로 갱신) + **sparring 검증 5건 반영**: §2.5 SSOT 명시 1줄(공격 5), §2.9·Step 9 줄번호 833-842→834-838 시프트 반영, R-T1 PLAN 단계 cmux 외부 SSOT 검증 위임 추가(공격 3), R-T2 Chromium 자동 설치 확인 결과(공격 2 해소), R-T5 untracked 검증 결과 + Step 10에 사전 `git add`/commit 의무 추가(공격 1), Step 8 `--browser` 모드 보존(deprecated alias) 재결정(공격 4) (007) |
| v1.2 | 2026-05-22 | **fallback 정책 단순화 (캡틴 정책)** — cmux는 사용자 선택 옵션, playwright는 install-mac.sh 자동 설치 유지. cmux 미설치 시 사용자 안내·유도 없이 **silent fallback** (사용자 게이트 제거). §2.5에 silent fallback 1단락 + R-T2 정책 재작성 + R-T8(cmux macOS 전용) 신설 — `command -v cmux` 단일 분기로 OS 감지와 설치 여부를 동시 흡수. Step 7(AGENT.md)에 silent 분기 코드 명시 + `summary` 표기 추가 안 함(캡틴 Q1=b) (007) |
| v1.3 | 2026-05-22 | **단독 호출/wtm-agent 경유 경계 명시 (캡틴 정책)** — §2.5에 적용 범위 1단락 추가. silent fallback은 wtm-agent 경유 한정이고, 알투/워커가 cmux-tool을 단독 호출할 때는 cmux-tool이 단일 책임(에러 JSON 반환)만 수행. 호출자가 fallback 자율 판단. cmux-tool에 fallback 로직 내장 금지 (단순성 원칙) (007) |
