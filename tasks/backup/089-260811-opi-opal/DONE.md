# DONE: opi 프로젝트 최신화 — 문서 3종 실측 정합 + 다이어그램 단계명 정정

> 완료일: 2026-08-11 14:18 KST | 적용 스킬: opi (최신화 모드)
> 태스크: `tasks/089-260811-opi-opal/`

## 1. 무엇을 해결했나

프로젝트 SSOT 문서 3종이 실물과 얼마나 벌어졌는지 전수 대조하고, 확인된 **64건을 전건 반영**했다. 태스크 086의 이관 목록(I-1~I-8)에서 출발했으나 실제로는 그보다 훨씬 컸다.

| 문서 | 검증 항목 | 어긋난 항목 | 처리 |
|------|----------|------------|------|
| `docs/ARCHITECTURE.md` | 116 | **32 (27.6%)** | 전건 반영 + 084·086 신규 반영 |
| `docs/PROJECT.md` | 19 | 12 | 전건 반영 + Dev 파이프라인 섹션 신설 |
| `docs/CONVENTIONS.md` | 22 | 16 | 전건 반영 + 변경이력 절 신설 |
| `docs/architecture-diagram/*.html` | — | 1 | opsdd 단계명 정정 (승인 후 범위 추가) |

## 2. 가장 중요한 3가지

### (1) 지원 플랫폼 하나가 문서에서 통째로 비가시였다

`install_codex_agents()`·`install_codex_config()`·`codex mcp add`·`codex-bootstrap.md`가 모두 실재하는데, `ARCHITECTURE.md` 배포 모델은 Claude·Cursor·Gemini 3종만 서술하고 있었다. 수치 오차가 아니라 **Codex 지원 사실 자체가 문서에 없던** 상태다. 배포 모델·MCP 등록·시스템 다이어그램 전 경로에 Codex를 신설했다.

### (2) 존재하지 않는 경로가 규범으로 기술되고 있었다 — 6개 지점

루트 `agents/` 디렉토리는 **없는데** `PROJECT.md:37,50,158`·`CONVENTIONS.md:21,71,206`이 이를 정상 경로로 적고 있었다. `프로젝트 구성` 표의 Framework 경로에까지 들어가 있어 opgc 동적 분할·PM 컨텍스트 주입 라우팅에 실제 영향을 주는 상태였다. 같은 유형으로 `community-skills/`(루트 부재)·`op-sdd-tasks`(실물 부재)·MCP `Notion` 행(배포·설치 경로 어디에도 없음)을 함께 제거했다.

### (3) 인벤토리가 실제의 절반 수준이었다

| 항목 | 문서 | 실측 |
|------|------|------|
| OPAL 스킬 | 24·25종 (문서 내부에서도 불일치) | **42** |
| 독립 스킬 | 5·6종 (내부 불일치) | **8** |
| 서브에이전트 | 12개 (4곳) | **15** |
| 도구 | 6종(표)·4종(트리) | **18** |
| alias | 9종 | **27** |

특히 `PROJECT.md`에는 **주력 dev 파이프라인 섹션 자체가 없었다** — opd/opds/opdw/opwt/opp/oppd 6종과 `op-dev-*` 7종, 워커 에이전트 10종이 "주요 컴포넌트" 8개 섹션 어디에도 등재되지 않은 상태였다. §주요 컴포넌트 (Dev 파이프라인)을 신설해 해소했다.

## 3. 변경 파일

| 파일 | 변경 |
|------|------|
| `docs/ARCHITECTURE.md` | 32건 반영 + Codex 경로 신설 + 디렉토리 트리 재작성 + 변경이력 3행 추가·날짜 역순 정렬 복구 + 미종료 코드펜스 복구 |
| `docs/PROJECT.md` | 12건 반영 + §주요 컴포넌트 (Dev 파이프라인) 신설 + 문서 레지스트리 6→10행 |
| `docs/CONVENTIONS.md` | 16건 반영 + §변경이력 절 신설 (v1.1.0) |
| `docs/architecture-diagram/opal_framework_architecture.html` | opsdd 단계명 2지점 정정 |
| `docs/backup/{PROJECT,ARCHITECTURE,CONVENTIONS}_202608111324.md` | 수정 전 백업 (opi 백업 프로토콜) |
| `.opal/MEMORY.json` | 태스크 채번 + 작업 히스토리 |

## 4. 검증 결과 (PM 직접 실측)

| 항목 | 결과 |
|------|------|
| 도구 수 3문서 교차 | **18종 통일** (`19종` 잔존 0) |
| 없는 경로 잔존 (살아있는 서술) | `op-sdd-tasks` 0 · `Notion` 0 · `WebFetch` 0 · 루트 `agents/` 0 |
| 에이전트 15 / 스킬 42 / 독립 8 | 3문서 일치 |
| alias | 27종 (오케스트레이터 10 + 운영 11 + 독립 6) |
| 다이어그램 무결성 | `data-id` 46 = `NODE_DATA` 46, 차집합 0, 구 단계명 잔존 0 |
| 코드펜스 균형 | `ARCHITECTURE.md` 8개 (짝수) |
| 워커 임의 생성 파일 | 0건 |

## 5. 워커가 범위를 넘어 발견한 것 (PM 검증 후 승인)

| # | 발견 | PM 검증 |
|---|------|---------|
| 1 | **opsdd 파이프라인 단계명이 실물과 다름** — 문서의 `SPEC-VERIFY`/`TASKS`/`TASKS-VERIFY`는 존재하지 않는 단계 | `opal-pilot-sdd/SKILL.md` Phase 헤딩 재실측 → 실제는 `TASK → SPEC → REVIEW → DESIGN → EXECUTE-LOOP → VERIFY → CLOSE`. **정정 정확** |
| 2 | `ARCHITECTURE.md` 디렉토리 트리의 **코드펜스가 닫히지 않아** §변경이력 전체가 코드블록 안에서 렌더링 | 펜스 8개 균형 확인. **복구 타당** |
| 3 | `state-tool` 서브명령 10종이 아니라 **11종**(`verify`) — 도구 자체 help도 "10종"으로 오기재 | 실측 확인. 세 문서에 해당 서술이 없어 이번 갱신 대상 아님 → 후속 이관 |
| 4 | `backlog-tool`은 **8종**이 맞고 `opal-harness.md` 7종 표기가 오기재 | 도구 help 실측 확인 → 후속 이관 |

## 6. PM Gate에서 잡은 것

**세 문서가 도구 수를 다르게 말하는 상태**를 출고 직전에 차단했다. `ARCHITECTURE.md`만 19종(디렉토리 18 + `check-env.js`)으로 세고 나머지 둘은 18종이었다. `check-env.js`는 `{도구}/run.sh` 래퍼 규약을 따르지 않고 하네스 §9 등록 도구 표에도 없으므로 **18종(도구 디렉토리 기준)** 으로 통일하고, `check-env.js`는 "도구 외 보조 스크립트"로 분리 표기했다. 이번 최신화가 없애려던 바로 그 drift라 넘기지 않았다.

## 7. 수용 판정한 관측 (고치지 않은 이유)

| 관측 | 판정 |
|------|------|
| 변경이력 행에 `op-sdd-tasks`·`Notion`·`WebFetch`·`12개` 리터럴이 남음 | **정상** — 이력은 무엇을 고쳤는지 남겨야 한다. 살아있는 서술에는 0건 |
| 루트 `CLAUDE.md`가 **0바이트 빈 파일** | 프레임워크 설계상 Claude Code는 전역 마커로 비서 tier가 상시 활성화되므로 프로젝트 마커가 불필요하다. 빈 파일 자체는 무해 — 삭제는 범위 밖으로 보류 |
| 루트 `AGENTS.md`(Codex 부트스트래퍼) 부재 | 위와 동일 — Codex도 전역 마커 경로다. 생성하지 않음 |
| 루트 `.cursorrules`(2026-03-30)가 레거시 | 현행은 `~/.cursor/rules/000-opal-agent.mdc` 전역 규칙 + 프로젝트 `cursor-rules/*.mdc`. 마커는 유효해 무해 |
| `PROJECT.md` 변경이력에 semver 미적용 | 표가 `| 날짜 | 변경 내용 |` 2컬럼이고 문서에 버전 개념이 없다. 컬럼 신설은 승인 범위 밖 |

> Phase 4-1(플랫폼 파일 갱신)은 **스킵**했다. 이 프레임워크의 부트스트랩 설계상 Claude·Cursor·Codex는 전역 마커로 동작하고 프로젝트 마커가 필요한 것은 Gemini뿐인데, `GEMINI.md`는 마커를 정상 보유하고 있다. 불필요한 부트스트래퍼 파일을 생성하지 않는 것이 설계 의도에 맞다.

## 8. 이번 태스크에서 배운 것

### (1) 문서 간 상호 인용은 검증이 아니다

`ARCHITECTURE.md`·`PROJECT.md`·`CONVENTIONS.md`가 서로를 참조하며 일관돼 보였지만, 셋 다 동시에 틀려 있었다. 스킬 수(24 vs 25), 독립 스킬 수(5 vs 6)는 **한 문서 안에서도** 어긋났다. 수치 SSOT를 디렉토리·frontmatter 실측으로 고정한 것이 32건 검출의 전제였다.

### (2) 같은 문서 안에서 표보다 트리가 더 빨리 낡는다

`ARCHITECTURE.md`의 에이전트 표는 15개를 정확히 나열하는데 디렉토리 트리는 12개였고, Console 본문은 7화면인데 트리는 6화면이었다. 트리는 사람이 손으로 유지하는 중복 표현이라 본문보다 먼저 썩는다. 트리를 본문 표에서 파생시키는 방향이 근본 해법이다.

### (3) 부재는 오류를 내지 않아 가장 오래 산다

없는 경로(`agents/`·`community-skills/`)·없는 스킬(`op-sdd-tasks`)·없는 MCP(`Notion`)는 아무 곳에서도 실패를 일으키지 않는다. 읽는 사람과 에이전트만 잘못된 곳을 찾아갈 뿐이다. 그래서 "문서에 있는데 실제에 없음" 분류를 별도 축으로 두고 전수 확인해야 한다.

## 9. 후속 이관 목록

| # | 대상 | 내용 |
|---|------|------|
| J-1 | `opal/core/references/opal-harness.md:251-252` | `state-tool` "9개" → **11종**(`spec-validate`·`verify`), `brain-tool` "8 서브명령" → **10종** |
| J-2 | `opal/core/references/opal-harness.md:257` | `backlog-tool` "7 서브명령" → **8종**(`coverage-check` 포함) |
| J-3 | `opal/tools/state-tool` help 문구 | 도구 자신이 "10종"으로 오기재 — 실제 11종 |
| J-4 | `opal/core/references/agents.md:254` | wtm 폴백 "Phase 1(WebFetch)" → 2단(cmux → playwright) |
| J-5 | `opal/core/references/harness/pm-review-gate.md` | **회전·세로쓰기 요소는 element 확대 캡처로 판독** 항목 추가 (태스크 086 §8 (1) 이관분 — I-9) |
| J-6 | 루트 `CLAUDE.md` 0바이트 | 삭제 여부 판단 |

J-1~J-3은 하네스·도구의 자기기술 오류라 성격이 같다. 한 태스크로 묶는 것이 효율적이다.
