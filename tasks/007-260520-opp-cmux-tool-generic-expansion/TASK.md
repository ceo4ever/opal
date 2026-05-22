# TASK: cmux-tool 범용 확장 + wtm-agent fallback 체인 재배선

> 작성일: 2026-05-20 | 작업 유형: 개선 | 적용 스킬: opp | 모드: semi-agentic
> 입력: 사용자 요청 (대화 누적)
> 출력: TASK.md

## 작업 목표

기존 `opal/tools/cmux-tool/`을 cmux browser 공식 명령을 다목적으로 노출하는 디스패처로 확장하고, `opal/references/tools.md`에 정식 등록하여 알투/워커가 웹 크롤링·E2E·정보 수집·웹 테스트에 자동으로 도구를 인식·활용하도록 한다. 동시에 `opal-wtm-agent`의 호출 체인을 cmux-tool 1순위·playwright-tool fallback 형태로 재배선한다.

## 배경

캡틴의 핵심 발화 — "cmux-browser를 사용해서 알투나 워커가 web 크롤링, web 테스트, e2e 테스트, 웹으로 정보 수집 등 다양하게 사용하기 위해서 등록을 하려고 함. 즉, 툴로 인식해서 필요시에 도구로 사용을 하게 했으면 함."

즉 cmux의 강력한 브라우저 자동화를 OPAL **도구 레지스트리** 차원에서 노출하여, 알투(PM)와 워커가 lazy-load 시점에 자동으로 인식하고 활용하게 만드는 것이 목적이다.

## 배경 분석 (대화에서 도출)

### 현재 상태

| 자산 | 현 상태 |
|------|--------|
| `opal/tools/cmux-tool/run.sh` | URL→HTML 추출에만 특화 (`cmux browser open`/`goto`/`eval`/`wait`/`get`/`tab close` 6종 내부 사용). 서브명령 디스패처 부재. wtm 흐름 전용으로 협소 |
| `opal/tools/cmux-tool/README.md` | 3모드(A/B/C — URL/surface 단독/surface+URL) 기준으로 작성됨. 범용 도구 형태 아님 |
| `opal/references/tools.md` | 등록 도구 3종: `xlsx-tool` / `state-tool` / `code-scan`. **`cmux-tool` 및 `playwright-tool` 미등록** → 알투가 lazy-load 후에도 도구 인식 불가 |
| `opal/tools/playwright-tool/` | `run.sh` + `main.py` 존재 (.venv python 기반). 별도로 동작 가능하지만 레지스트리 미등록 |
| `opal/agents/opal-wtm-agent/AGENT.md:5` | 현재 폴백 체인 — Phase 1(WebFetch) → Phase 2(cmux, 조건부) → Phase 3(playwright-tool CLI) |
| `scripts/install-mac.sh:833-840` | cmux-tool run.sh chmod +x 처리 완료. cmux 미설치 환경 안내 출력 |

### cmux browser 공식 명령 인벤토리

본 태스크 폴더 `cmux/docs/CMUX-TOOLS.md` §3 참조 — 네비 7종 / 상호작용 7종 / 읽기 4종 = **총 18종 후보**.

| 분류 | 명령 |
|------|------|
| 네비 | `open` / `open-split` / `navigate` / `back` / `forward` / `reload` / `url` |
| 상호작용 | `click` / `fill` / `type` / `press` / `select` / `hover` / `focus` |
| 읽기 | `snapshot` / `get` / `eval` / `wait` |

> 노출 범위 선별은 PLAN 단계에서 확정. 이번 작업은 "cmux browser 공식 명령을 디스패처로 노출"이 목표.

## 확정된 설계 방향 (대화에서 합의)

| # | 결정 사항 | 출처 |
|---|---------|------|
| F-1 | 기존 `cmux-tool/run.sh`를 서브명령 디스패처로 범용 확장 (별도 도구 신설 ✕) | Q1 |
| F-2 | wtm-agent 호출 체인 — cmux-tool **1순위**, fallback **playwright-tool** | Q1 |
| F-3 | wtm-agent 기존 호출 호환 보장 — 첫 인자가 URL이면 `extract`(또는 동등 명령)로 자동 라우팅 | Q1 |
| F-4 | `tools.md` 등록은 **이번 작업에선 `cmux-tool`만**. `playwright-tool` 등록은 후속 작업으로 분리 | Q2 |
| F-5 | `tasks/007-.../cmux/` 자산 중 **필요한 것은 전부 흡수**하여 cmux-tool 디스패처 진영으로 일반화. **MAMS 전용 자산**(`_config.sh`, `cmux.json`, `CMUX.md` [MAMS 전용] 섹션 등)은 흡수 불가 — 폐기 또는 후속 태스크 보류 | 본 메시지 |
| F-6 | 진행 모드: `//opp` semi-agentic (PLAN까지 캡틴 검토, EXECUTE 이후 PM 자율, CLOSE 진입 캡틴 승인) | Q4 |
| F-7 | 흡수된 자산은 `opal/tools/cmux-tool/` 하위로 **재배치**. 세부 디렉토리 구조(예: `lib/` / `examples/` / `docs/`)는 PLAN에서 확정 | 본 메시지 |

## 요구사항

- [ ] **R-1. cmux-tool 다목적 디스패처 확장**
  - 무엇을: `opal/tools/cmux-tool/run.sh`를 서브명령 디스패처 형태로 재설계 — cmux browser 공식 명령을 OPAL 도구 인터페이스로 노출. **`tasks/007-.../cmux/scripts/test-browser.sh`의 E2E 분기 패턴**, **`_lib.sh`의 공통 호출/에러 처리 패턴**을 디스패처 내부 구조에 일반화하여 흡수
  - 어디에: `opal/tools/cmux-tool/run.sh` (+ PLAN에서 확정될 하위 헬퍼/예제 디렉토리)
  - 왜: F-1, F-2, F-5, F-7. 캡틴 의도 — "툴로 인식해서 필요시에 도구로 사용" + cmux/ 일반화 자산 흡수
  - AC: `bash ~/.opal/tools/cmux-tool/run.sh --help` 호출 시 PLAN에서 확정된 N개 이상의 서브명령(네비/상호작용/읽기 각 카테고리에서 최소 1종 이상)이 사용법 JSON에 노출된다. 각 서브명령은 단독 실행 가능하며 성공 시 단일 라인 JSON(`{"ok": true, ...}`) 반환, 실패 시 `{"ok": false, "error": "<코드>", ...}` 반환. **흡수 출처가 PLAN 산출물에 명시되고 EXECUTE 산출물(changed_files)에서 추적 가능해야 한다**

- [ ] **R-2. wtm-agent 기존 호출 호환 보장**
  - 무엇을: 기존 호출 형식(`run.sh <url> [--mode ...] [--wait ...]`, `run.sh --surface <h> [<url>] ...`)을 디스패처가 그대로 수용
  - 어디에: `opal/tools/cmux-tool/run.sh` 디스패치 라우팅 로직
  - 왜: F-3. wtm-agent의 기존 호출 시그니처를 깨지 않기 위함
  - AC: 첫 위치 인자가 `http://`/`https://`로 시작하면 추출 서브명령으로 자동 라우팅되며, 기존 출력 JSON 8필드(`ok`/`method`/`mode`/`surface`/`user_owned`/`title`/`final_url`/`content`/`bytes`/`wait_ms`)가 동일 키로 반환된다

- [ ] **R-3. wtm-agent fallback 체인 재배선**
  - 무엇을: `opal/agents/opal-wtm-agent/AGENT.md` Phase 흐름을 "cmux-tool 1순위 → playwright-tool fallback" 형태로 갱신
  - 어디에: `opal/agents/opal-wtm-agent/AGENT.md` + 연관 SKILL.md (`skills/web-to-markdown/SKILL.md` 위치 확인 후)
  - 왜: F-2. cmux 환경 우선 활용
  - AC: AGENT.md의 Phase 정의·진입 조건·fallback 트리거 에러 코드가 새 체인 기준으로 일관 기술되어 있고, "Phase 1/Phase 2" 호칭이 잔재 없이 갱신된다. WebFetch의 위치(완전 제거 / 보조 유지) 확정 명시
  - 미확정 M-1과 연결 (PLAN에서 결정)

- [ ] **R-4. tools.md 신규 등록**
  - 무엇을: `cmux-tool` 항목을 tools.md에 추가 — 용도·실행 경로·소스 경로·의존성·서브명령·트리거 조건·출력 형식·종료 코드
  - 어디에: `opal/references/tools.md`
  - 왜: F-4. 알투 lazy-load 시 자동 인식
  - AC: tools.md에 `## cmux-tool` 섹션이 추가되고, 기존 3개 도구(xlsx/state/code-scan)와 동일한 골격(용도/실행 경로/소스 경로/의존성/커맨드/출력 형식/사용 예시/종료 코드)을 갖춘다. **"트리거 조건" 표**(웹 크롤링·웹 테스트·E2E·정보 수집 등 사용 시점)가 명시되어 알투가 도구 선택을 자동화할 수 있다

- [ ] **R-5. README.md 갱신**
  - 무엇을: `opal/tools/cmux-tool/README.md`를 디스패처 구조 + 서브명령 + JSON 스키마 + 호환 정책 + **흡수된 cmux/ 자산 위치·출처** 기준으로 재작성
  - 어디에: `opal/tools/cmux-tool/README.md`
  - 왜: 도구 사용자(알투/워커/사람)의 진입점 + 흡수 자산 추적성
  - AC: 모든 노출 서브명령에 사용법·예시·출력 스키마·에러 코드가 기재되고, 흡수된 자산의 위치(`lib/` / `examples/` / `docs/` 등)와 원본 출처가 표로 정리된다. 변경이력 표에 v1.1(또는 그 이상) 행이 태스크 006 참조와 함께 추가된다

- [ ] **R-6. install-mac.sh 영향 점검**
  - 무엇을: cmux-tool 구조 변경(디렉토리 추가 + 다중 파일 배포)이 `scripts/install-mac.sh` 배포 흐름과 충돌하는지 점검 + 필요 시 갱신
  - 어디에: `scripts/install-mac.sh`
  - 왜: 배포 무결성
  - AC: install 실행 시 `~/.opal/tools/cmux-tool/` 하위가 신규 디렉토리 구조 그대로 배포되고 실행 파일에 chmod +x 적용된다. cmux 미설치 환경에서 자동 fallback 안내가 일관되게 동작한다

- [ ] **R-7. cmux/ 자산 흡수·재배치·정리**
  - 무엇을: `tasks/007-.../cmux/` 내 자산을 자산별로 판정 — (1) 흡수 대상은 일반화하여 `opal/tools/cmux-tool/` 하위로 이동, (2) MAMS 전용은 폐기 또는 후속 태스크 보류, (3) 도구 영역과 무관한 워크플로우 자산은 분리 처리
  - 어디에: `tasks/007-.../cmux/` → `opal/tools/cmux-tool/` 하위 (PLAN에서 확정된 구조)
  - 왜: F-5, F-7. cmux/ 폴더가 이번 태스크의 인풋 SSOT임을 명확화
  - AC: PLAN에 자산별 처분표(흡수/폐기/후속 보류) 1:1 매핑이 첨부되고, EXECUTE 완료 시점에 `tasks/007-.../cmux/`에는 후속 태스크 보류 자산만 남거나 폴더 자체가 정리된다. 흡수 자산은 cmux-tool/ 하위 정확한 경로에 존재하고 출처 주석/문서가 있다

## 미확정 사항 (PLAN에서 결정)

| # | 미확정 항목 | 결정 시점 |
|---|----------|---------|
| M-1 | wtm-agent의 WebFetch Phase 처리 방식 — (a) 완전 제거, 2단(cmux→playwright)으로 축소 / (b) 유지하되 보조 위치로 강등 | PLAN |
| M-2 | 서브명령 노출 범위 — cmux browser 18종 후보 중 어디까지 노출할지 (필수/선택 분류). **cmux/scripts/test-browser.sh의 E2E 흐름(A/B/C 분기)이 별도 서브명령으로 노출될지, `eval`+`wait` 조합 레시피로만 다룰지** 포함 | PLAN |
| M-3 | 서브명령별 출력 JSON 스키마 일관 키 정의 (기존 `extract` 8필드와 신규 명령 결과 필드 통일 정책) | PLAN |
| M-4 | tools.md "트리거 조건" 표의 정밀도 — 알투 자동 선택 알고리즘 수준 | PLAN |
| M-5 | cmux 미설치 환경에서 wtm-agent가 cmux-tool을 호출했을 때 playwright-tool으로 자동 우회되는 폴백 트리거 에러 코드 집합 | PLAN |
| M-6 | `cmux-tool/` 하위 재배치 디렉토리 구조 — 후보: `lib/` (공통 헬퍼) / `examples/` (E2E 패턴·hooks 샘플) / `docs/` (CLI/Socket API/단축키 참조 문서) — 최종 구조 PLAN 확정 | PLAN |
| M-7 | cmux/ 내 자산 처분표 — 자산별 (흡수/폐기/후속 보류) 1:1 매핑. 특히 `start-all.sh`·`stop-all.sh`·`open-dev.sh`·`analyze-log.sh`·`ghostty.config.sample`·`claude-hooks.sample.json`·`CMUX.md` [일반] 섹션 처분 | PLAN |

## 제약 조건

- **호환성**: 기존 wtm-agent 호출 형식이 깨져선 안 된다 (R-2)
- **흡수·재배치**: `tasks/007-.../cmux/` 자산은 필요 시 흡수 + `cmux-tool/` 하위 재배치 (F-5, F-7). MAMS 전용 자산은 흡수 불가 — 폐기 또는 후속 보류
- **범위**: playwright-tool의 tools.md 등록은 이번 범위 외 (F-4)
- **의존성**: cmux 버전 ≥ 0.64.3 (기존 README 요구사항 유지). cmux 미설치 환경에서도 도구가 graceful하게 실패하여 wtm-agent가 fallback 가능해야 한다
- **안전 가드 유지**: B/C 모드(사용자 surface 재사용) cleanup 절대 금지 / `user_owned` 시그널 유지 (기존 cmux-tool README §안전 가드)
- **출처 추적**: 흡수된 자산은 출처(원본 cmux/ 경로) 정보를 주석 또는 README 표로 보존해야 한다 (R-7 AC)

## 기술 스택

- Bash 5.x (run.sh 디스패처)
- Python 3.x (JSON 직렬화 — macOS 내장)
- cmux CLI ≥ 0.64.3
- Playwright (fallback 경로 — 기존 `opal/tools/playwright-tool/.venv`)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | cmux-tool run.sh | `opal/tools/cmux-tool/run.sh` | 확장 대상 본체 (현 6종 명령 사용 — open/goto/eval/wait/get/tab close) |
| D-2 | 소스 | cmux-tool README | `opal/tools/cmux-tool/README.md` | 기존 인터페이스·안전 가드 정책 |
| D-3 | 소스 | playwright-tool | `opal/tools/playwright-tool/run.sh`, `opal/tools/playwright-tool/main.py` | fallback 대상 — .venv python 기반 |
| D-4 | 설계 | tools.md | `opal/references/tools.md` | 신규 등록 대상 + 기존 3개 도구 골격 참조 |
| D-5 | 설계 | wtm-agent | `opal/agents/opal-wtm-agent/AGENT.md` | Phase 체인 재배선 대상 |
| D-6 | 소스 | install-mac.sh | `scripts/install-mac.sh` (L833-840 cmux-tool 처리) | 배포 영향 점검 |
| D-7a | 인풋 | cmux/ 인풋 SSOT (전체) | `tasks/007-260520-opp-cmux-tool-generic-expansion/cmux/` | 이번 태스크 흡수·재배치 대상 자산 묶음 (캡틴이 직접 배치) |
| D-7b | 인풋 | CMUX-TOOLS.md (CLI/Socket API/hooks) | `tasks/007-.../cmux/docs/CMUX-TOOLS.md` | §3 명령 18종 + §5 Socket API + §1~§2 CLI/단축키 + §4 hooks 레시피 — 흡수 대상 핵심 문서 |
| D-7c | 인풋 | test-browser.sh (E2E 패턴 원형) | `tasks/007-.../cmux/scripts/test-browser.sh` | A/B/C 분기 E2E 러너 — R-1 흡수 대상 |
| D-7d | 인풋 | _lib.sh (공통 헬퍼) | `tasks/007-.../cmux/scripts/_lib.sh` | cmux 호출·에러 처리 공통 패턴 — R-1 흡수 대상 |
| D-7e | 인풋 | cmux/README.md (자체 분류) | `tasks/007-.../cmux/README.md` | "프레임워크 승격 대상" 섹션 — 일반/MAMS 전용 분류 출처 |
| D-8 | 외부 | cmux 공식 문서 (브라우저 자동화) | [cmux Browser Automation](https://cmux.com/ko/docs/browser-automation) | 서브명령 시그니처·플래그 최종 검증 |
| D-9 | 외부 | cmux GitHub | [manaflow-ai/cmux](https://github.com/manaflow-ai/cmux) | 버전/릴리스 확인 |
| D-10 | 설계 | OPAL Harness | `opal/core/references/opal-harness.md` §9 OPAL Tools | 도구 등록 원칙 / 호출 방식 (래퍼 + JSON 출력) |
| D-11 | 설계 | Citation Rules | `opal/core/references/harness/citation-rules.md` | 산출물 인용 규칙 (PLAN/EXECUTE 산출물 필수 적용) |
