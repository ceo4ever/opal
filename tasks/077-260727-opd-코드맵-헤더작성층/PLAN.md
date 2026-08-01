# PLAN: 코드 헤더 작성층 신설 — 인라인 + 외부 code-map 2소스

> 작성일: 2026-07-28 | 입력: TASK.md, ANALYSIS.md
> 모드: Multi-Feature (13기능) | 실행 모드: 복잡 | 영역: 전량 `Framework` (`docs/PROJECT.md` §프로젝트 구성 → D-19)
> 산출물 계약: PLAN.md 단일 (execution-plan.json 미생성 — op-dev-plan SKILL.md §Deprecated)

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

`code-scan`의 헤더 해석을 **인라인 주석 + 외부 `.opal/code-map/` 2소스**로 확장하고, 현재 비어 있는 **헤더 작성층**(`discover`/`scaffold`/`target`/`validate` + PostToolUse hook)을 신설한다. 해석 확장은 `scanAll`의 단일 호출점(`opal/tools/code-scan/code-scan.js:324`) 교체로 기존 8커맨드에 자동 전파되며, code-map 부재 프로젝트는 동작 변화 0이다(→ D-1 §1.2 / ANALYSIS §4 발견 1).

부수 목표 2종: ① `code-scan`에만 없는 `run.sh` 래퍼를 신설해 `opal-harness.md` §9 규약 위반과 `tool-scan usage code-scan` 실패(`help_exec_failed`)를 동시 해소(F-013) ② 이 저장소 `.opal/code-scan.json`을 생성해 픽스처가 실제 스캔에 오염되는 실측 경로를 차단(F-012 선결, → ANALYSIS §5 R-1).

### 1.2 기능 목록

TASK.md 요구사항 F-1~F-13과 **1:1 대응**한다 (PLAN F-00N ↔ TASK F-N).

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | code-map 스키마 정의 (index.json + 패키지 매니페스트) | TASK F-1 | P0 | 없음 |
| F-002 | 5단 상속 해석 + 경로 사상 + 단일 파일 역매핑 | TASK F-2 | P0 | F-001 |
| F-003 | `discover` 서브명령 (index.json 초안) | TASK F-3 | P0 | F-001 |
| F-004 | `scaffold` 서브명령 + 멱등 보존 merge | TASK F-4 | P0 | F-001, F-002 |
| F-005 | `target` 서브명령 (4단 기록 위치 판정) | TASK F-5 | P0 | F-001, F-002 |
| F-006 | `validate` 서브명령 (5종 위반 + 합산 커버리지 + `--changed`) | TASK F-6 | P0 | F-001, F-002, F-004 |
| F-007 | 워커 권한 경계 집행 | TASK F-7 | P0 | F-006 |
| F-008 | `feature` 옵셔널 필드 + cross-scope 조회 | TASK F-8 | P1 | F-001, F-002 |
| F-009 | PostToolUse hook (기록 위치 미갱신 감지) | TASK F-9 | P1 | F-005, F-013 |
| F-010 | `headerSource` 스위치 (auto/inline/manifest) | TASK F-10 | P0 | F-002 |
| F-011 | 규칙 SSOT 갱신 (7문서) | TASK F-11 | P0 | F-002~F-008 |
| F-012 | 합성 픽스처 6조건 + RED 테스트 + 자체 dogfooding | TASK F-12 | P0 | 선결분은 없음 / 검증분은 F-002~F-010 |
| F-013 | `run.sh` 래퍼 신설 + 배포·매니페스트 배선 | TASK F-13 | P0 | 없음 |

### 1.3 기능 의존 그래프 (ASCII)

```
F-012(선결: .opal/code-scan.json + .gitignore + 픽스처 + RED)
  │
F-001(스키마) ─┬─ F-002(해석기·경로사상·역매핑) ─┬─ F-004(scaffold) ─ F-006(validate) ─ F-007(권한경계)
               │                                 ├─ F-005(target) ─ F-009(hook)
               │                                 ├─ F-008(feature)
               │                                 └─ F-010(headerSource)
               └─ F-003(discover)
F-013(run.sh) ──────────────────────────────────────────────────────┘ (F-009 hook 커맨드 경로 선결)
  │
  └─ F-011(규칙 SSOT 7문서) ─ F-012(검증분: 4-pass + 8커맨드 회귀 + dogfooding)
```

### 1.4 PM 확정 설계 결정 승계 (재논의 금지 — 디스패치 프롬프트 7항목)

| # | 결정 | 반영 위치 |
|---|------|----------|
| PM-1 | `feature <id>`는 기본 전체 스코프 순회 + 스코프별 그룹핑, `--scope X` 동반 시 X로 제한 (R-3 해소) | §3.8.2 |
| PM-2 | 단일 파일 역매핑 **필수 구현** — `scan <file>`에서도 스코프·매니페스트 역매핑 (R-5 해소) | §3.2.2 (E) |
| PM-3 | F-011 갱신 대상에 `opal/tools/brain-tool/README.md` 추가 + `opal-harness.md` §9 도구 표 정합 확인 (R-4 해소) | §3.11.1 |
| PM-4 | `exports`·`depends` **생성=워커(LLM) / 검증=도구**. 문법 파서 미도입(무의존 유지). `validate`는 텍스트 존재 대조만(`exports_not_found`) | §3.6.2 (D) |
| PM-5 | `scaffold --inline`(소스 주석 삽입) **미채택** — 설계·Step에서 제외 | §3.4.2 (F) |
| PM-6 | R-1 해소: 픽스처를 자기완결 `.opal/` 보유 트리로 만들고 테스트를 `cwd: <fixture-root>` subprocess 실행 + F-012 선결(`.opal/code-scan.json`) 결합 = 이중 격리 | §3.12.2 (A)(B) |
| PM-7 | R-6 해소: hook은 code-map 미사용 프로젝트에서 즉시 무관 판정·무출력·exit 0 (`opal/tools/state-tool/todo_mirror_hook.py:124-130` fail-safe 준용) | §3.9.2 (C) |

### 1.5 핵심 제약 ([MUST] 원문 인용 — 재해석 금지)

- [MUST] `opal/core/PRINCIPLES.md` §2 Simplicity First: "Solve only the current requirement. No speculative abstraction or unrequested flexibility."
- [MUST] `opal/core/PRINCIPLES.md` §3 Surgical Changes: "Touch only what the plan names. Don't improve adjacent code."
- [MUST] `opal/core/references/opal-harness.md` §9: "OPAL 도구는 모두 `~/.opal/tools/{tool-name}/run.sh` 래퍼를 통해 호출한다."
- [MUST] `.opal/AGENT.md` §금지사항: "**`~/.opal/` 직접 편집 금지** — 항상 프로젝트 소스를 수정한 후 install로 배포한다."
- [MUST] `.opal/AGENT.md` §금지사항: "**변경이력 누락 금지** — 스킬·에이전트·참조 문서 수정 시 변경이력 표 행 추가 의무."
- [MUST] `opal/tools/brain-tool/README.md`: "**단방향 동기화**: `sync-header`는 code-scan @header → brain entity frontmatter 방향만 (역방향 금지)"
- [MUST] `docs/CONVENTIONS.md` §언어 규칙: "코드/변수/필드명 | English" — code-map 스키마 필드명은 전량 영문(§3.1.2).
- [MUST] `docs/CONVENTIONS.md` §네이밍 규칙 파일/폴더: "**kebab-case** 사용: `user-auth-implementation`, `op-dev-plan` (Python 파일은 **snake_case**: `creative_response.py`, `user_auth.py`)" — 신규 Node 파일은 kebab-case(`code-map-hook.js`), 테스트는 `test-<verb>.js`(→ D-15).
- [MUST] `docs/CONVENTIONS.md` §구현 규칙 §배포 경계: "`~/.opal/` 배포 파일을 직접 편집하지 않는다. 변경은 항상 프로젝트 소스(`opal/`, `skills/`, `agents/`, `community-skills/`, `scripts/`)에서 수행한다."
- [MUST] `docs/CONVENTIONS.md` §구현 규칙 §변경이력 작성 의무: "스킬·에이전트·참조 문서를 변경하면 "## 변경이력" 표에 행을 추가한다."
- [MUST] `docs/CONVENTIONS.md` §구현 규칙 §도구 우선 원칙: "파일 처리·데이터 변환 작업이 필요할 때, 직접 코드를 작성하기 전에 OPAL 도구(`~/.opal/tools/`)를 우선 검토한다."
- [MUST] `docs/CONVENTIONS.md` §구현 규칙 §Guards: "커밋은 사용자가 명시적으로 요청할 때만 수행한다 — EXECUTE 완료·DONE.md 생성·테스트 통과 후에도 자동 커밋 금지."
- TASK.md 제약 ②: 기존 `code-scan.js` 8커맨드 하위호환 유지 — code-map 부재 프로젝트 동작 변화 0
- TASK.md 제약 ④: 신규 도구 코드는 Node.js — 도구 내 언어 이원화 금지
- TASK.md 제약 ⑦: 검증은 저장소 내 합성 픽스처와 자체 소스로만 수행 (외부 저장소 인용·참조 금지)

---

## 리스크 가설 표

> PLAN 단계 작성. TEST-SCENARIO.md §1의 입력이 된다. ANALYSIS §5 R-1~R-7을 H-1~H-7로 승계하고 H-8~H-18로 확장한다.
> 검증 계층: L1=단위(순수 함수 직접 호출) / L2=통합(CLI 블랙박스 subprocess, 실 파일시스템 픽스처) / L3=실환경(install 배포본·실제 세션 hook·자체 저장소 dogfooding)

| ID | 승계 | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 검증 방법 | 시나리오 후보 |
|----|------|----------|----------------|---------|------------|----------|------------|
| H-1 | R-1 | F-012 픽스처 배치 | 저장소 전체 스캔이 픽스처 코드 파일을 흡수(`code-scan.js:236-239`) → `missing`·brain `sync-header` 오염 | P1 | L2+L3 | 저장소 루트에서 `scan --json` 실행 후 결과 경로에 `fixtures/` 0건 확인 + 픽스처 루트 `cwd`에서 실행 시 저장소 파일 0건 확인 (이중 격리) | S-1 |
| H-2 | R-2 | F-002 tier③ package 상속 | `depends` 역의존 탐색(`code-scan.js:538-543`)이 "파일 선언 의존" → "패키지 선언 의존"까지 매칭 → 정밀도 의미 변화 | P2 | L2 | 픽스처에서 package tier `depends` 부여 후 `depends <module>` 결과에 패키지 상속 파일이 포함되는지 확인(의도된 동작임을 스냅샷으로 고정) | S-2 |
| H-3 | R-3 | F-008 `feature` × `--scope` | 기존 `--scope`의 "탐색 범위 축소" 의미(`code-scan.js:223-231`)와 cross-scope 조회 요구가 충돌 | P2 | L2 | `feature X`(전체 순회·그룹핑) / `feature X --scope web`(단일 그룹) 2케이스 대조 (PM-1) | S-3 |
| H-4 | R-4 | F-011 문서 범위 | "code-scan @header"가 2소스를 뜻하게 된 의미 변화가 `brain-tool/README.md`·`opal-harness.md` §9에 미반영 | P2 | L1 | 7문서 grep — 변경이력 행 7건 + `header-rules.md` "별도 도구 없음" 잔존 0건 + harness §9 code-scan 행에 신규 서브명령 표기 | S-4 |
| H-5 | R-5 | F-002 단일 파일 역매핑 | PM Gate 8번 `code-scan scan <file> --json`(`pm-review-gate.md:53`)이 readonly 파일에서 결과 0건 → 기존 검증 절차 파손 | P0 | L2 | 인라인 없고 매니페스트만 있는 픽스처 파일 1개를 `scan <file> --json`으로 조회 → `_source: file` 헤더 반환 | S-5 |
| H-6 | R-6 | F-009 hook 전역 병합 | `~/.claude/settings.json` 전역 병합(`install-mac.sh:1212-1219`)으로 code-map 미사용 프로젝트의 매 `Edit`/`Write`에서 실행 → 성능·부작용 | P0 | L2+L3 | code-map 부재 트리에서 hook에 이벤트 JSON 주입 → stdout 0바이트·exit 0 확인 + 실 세션 1회 관측 | S-6 |
| H-7 | R-7 | F-012 테스트 자산 0 | 회귀 기준선이 없어 8커맨드 파손을 검출 못함 | P1 | L2 | 변경 전 8커맨드 `--json` 출력을 골든 파일로 캡처 → 변경 후 바이트 동일 대조 | S-7 |
| H-8 | 신규(제약②) | F-002 `scanAll:324` 교체 | code-map 부재 시 `resolveHeader`가 `extractHeader`와 다른 값 반환 → 기존 프로젝트 출력 변화 | P0 | L1+L2 | `.opal/code-map/` 없는 픽스처에서 8커맨드 출력이 골든과 바이트 동일 + `_source` 키 미출현 확인 | S-7, S-8 |
| H-9 | 신규 | F-009 hook matcher | `claude-hooks.json` matcher의 정규식 alternation(`Edit\|Write\|MultiEdit`) 미지원 시 hook 무발동 | P1 | L3 | 실 세션에서 `Write` 1회·`Edit` 1회 발생시켜 발동 관측. 미발동 시 폴백=3개 엔트리 분리 등록 | S-9 |
| H-10 | 신규 | F-004 scaffold 멱등 | 키 순서·개행·들여쓰기 비결정성으로 재실행 시 diff 발생 → 확정 방향 10 위반 | P1 | L2 | scaffold 2회 연속 실행 후 두 산출물 바이트 동일 + description 채운 뒤 3회차에서 값 보존 확인 | S-10 |
| H-11 | 신규 | F-001 `stripPrefix` | 두 소스 디렉토리가 동일 미러 경로로 접히면 매니페스트가 덮어써져 데이터 손실 | P0 | L2 | 충돌 픽스처에서 scaffold가 `mirror_collision`으로 거부(exit 1)하고 어떤 파일도 쓰지 않음 확인 | S-11 |
| H-12 | 신규 | F-001 `layerRules` | 동률 구체성에서 배열 순서에 의존하면 `discover` 출력 순서 변화가 조회 결과를 바꿈 | P1 | L1 | 동일 점수 규칙 2개를 순서만 바꿔 2회 조회 → 동일 layer 반환 확인 | S-12 |
| H-13 | 신규 | F-006 `draft` 차단 정책 | `draft`를 위반으로 취급하면 pass2(scaffold) 직후 `validate`가 항상 실패 → 파이프라인 오해·우회 유발 | P1 | L2 | scaffold 직후 `validate` = exit 2(draft N건), pass3 채움 후 = exit 0. `--changed`로 영향 범위 한정됨을 확인 | S-13 |
| H-14 | 신규 | F-006 `exports` 텍스트 대조 | 문법 파싱 없는 부분 문자열 대조는 주석·문자열 리터럴 우연 일치(false negative)와 부분 일치 통과를 허용 | P2 | L1 | 존재/미존재/주석 내 존재 3케이스 픽스처로 판정 결과를 명시 계약으로 고정(주석 내 존재는 통과로 계약) | S-14 |
| H-15 | 신규 | F-005 판정 순서 | `readonly` 스코프의 신규 파일에서 tier 순서가 뒤바뀌면 `write_to: inline`이 반환되어 규약 위반 유발 | P0 | L2 | readonly 스코프 × (신규/인라인보유/레거시) 3케이스에서 전부 `manifest`+`readonly_repo` 반환 확인 | S-15 |
| H-16 | 신규(발견4) | F-002 `_source` 의미론 | brain `sync-header`가 매니페스트 유래 헤더를 "코드에 실재하는 주석"으로 오인해 frontmatter에 동기화 | P2 | L1 | `brain-tool/README.md`에 2소스 의미 변화 1문장 명시 확인(코드 변경 없음 — `brain_tool.py:839` 4필드 비교는 무관 키 무시) | S-4 |
| H-17 | 신규 | F-013 배포 배선 | install 후 `run.sh` 실행 권한 누락 → `tool-scan usage code-scan`이 `help_exec_failed` 잔존 | P0 | L3 | install 실행 후 `~/.opal/tools/code-scan/run.sh --help` exit 0 + `tool-scan usage code-scan`이 `ok: true` | S-16 |
| H-18 | 신규 | F-012 `.gitignore` | `.opal/*` 무시(`.gitignore:2`)로 수작업 자산인 code-map이 추적되지 않음 | P1 | L2 | `.opal/code-map/` 예외 추가 후 `git check-ignore -v` 결과로 비무시 확인, `.opal/code-scan.json`은 무시 유지 | S-17 |

---

## 2. 기능별 분석

### F-001: code-map 스키마 정의

#### 2.1.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 공통 | `opal/tools/code-scan/code-scan.js` | 스키마 상수·기본값·버전 정의 추가 | 수정 |
| 문서 | `opal/core/references/header-standard.md` | 2소스 표현 절 신설 | 수정 |

#### 2.1.2 현재 구현
- `DEFAULT_CONFIG`(`code-scan.js:29-34`)가 `scopes`/`extensions`/`exclude`/`excludePatterns` 4키만 정의하며 code-map 관련 상수는 전무하다.
- `header-standard.md` §2(`:13-21`)는 인라인 7필드만 규정하고 외부 파일 표현이 없다 (→ D-2).

#### 2.1.3 영향 범위
- 스키마는 F-002~F-008 전부의 입력 계약이므로 선행 확정이 필수다. 소비자 코드는 없어(신규) 회귀 위험 0.

### F-002: 5단 상속 해석 + 경로 사상 + 단일 파일 역매핑

#### 2.2.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 공통 | `opal/tools/code-scan/code-scan.js` | `resolveHeader` 신설 + `scanAll:324` 단일 교체 + code-map 로더·경로 사상 함수 | 수정 |

#### 2.2.2 현재 구현
- `extractHeader(filePath)`(`code-scan.js:274-312`)가 유일한 해석 지점이며 8커맨드 전부가 `scanAll`(`:318-333`)을 경유해 `:324`에서 이 함수를 1회 호출한다 (→ ANALYSIS §1.2).
- 출력 계층(`fmtBrief:348` / `fmtFull:363` / `fmtJson:372`)은 `header` 키 목록을 검증하지 않으므로 `_source` 추가 키가 자동 통과한다 (→ ANALYSIS §4 발견 1).
- `discoverFiles`(`:242-258`)는 `opts.targetPath`가 파일이면 단일 파일 배열을 반환해(`:246`) 스코프 컨텍스트가 소실된다 → 역매핑 필요(R-5).

#### 2.2.3 영향 범위
- 직접: 8커맨드 전부(자동 전파). 간접: brain `sync-header`(`brain_tool.py:786-793`)가 `--json`을 소비 — `module/layer/domain/exports` 4필드만 비교(`:839`)하므로 코드 변경 불필요.
- `getSearchPaths`/`walkDir`/`discoverFiles`/`fmt*`는 **무변경**이 하위호환 논거의 핵심이다.

### F-003: `discover` 서브명령

#### 2.3.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 공통 | `opal/tools/code-scan/code-scan.js` | `cmdDiscover` + 추론 헬퍼 | 수정 |

#### 2.3.2 현재 구현
- 유사 추론 규약이 산문으로만 존재한다 — `code-scan-management.md` §추론 소스 3종(`:14-31`)이 `scopes`는 `docs/PROJECT.md §프로젝트 구성`에서, `exclude`는 기본값+보강으로 추론하라고 규정(→ D-4). 도구 구현은 0건.
- `cmdSummary`(`:496`)·`cmdDepends`(`:524`)가 공용 `output()`을 우회해 자체 포맷을 출력하는 선례가 있어, 신규 서브명령의 전용 포맷은 기존 관례에 부합한다 (→ ANALYSIS §1.2 바이패스 패턴).

#### 2.3.3 영향 범위
- 쓰기 대상은 `.opal/code-map/index.json` 단일. 소스 파일 무접촉.

### F-004: `scaffold` + 멱등 보존 merge

#### 2.4.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 공통 | `opal/tools/code-scan/code-scan.js` | `cmdScaffold` + merge 알고리즘 | 수정 |

#### 2.4.2 현재 구현
- 멱등 upsert 선례: 076 태스크의 state-tool todo 미러 merge (→ D-9). 소유권 마커 기반 보존 merge를 `install-mac.sh` `merge_hooks_config()`(`:1212-1219`)가 이미 사용한다.
- 소스 파일에 헤더를 기록하는 자동화는 저장소 전체에 0건이다 (→ TASK.md §배경분석(1)).

#### 2.4.3 영향 범위
- 쓰기 대상은 `.opal/code-map/{scope}/**.json`. PM-5에 따라 소스 파일 주석 삽입은 범위 외.

### F-005: `target` 4단 기록 위치 판정

#### 2.5.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 공통 | `opal/tools/code-scan/code-scan.js` | `cmdTarget` + `decideTarget` 순수 함수 | 수정 |

#### 2.5.2 현재 구현
- 기록 위치 판정 개념 자체가 부재하다. 현행 규칙은 [MUST] `opal/core/references/harness/header-rules.md` §8: "**작성 주체**: 워커(LLM)가 직접 작성. 별도 도구 없음." 이며 위치는 항상 소스 인라인이다(`header-rules.md:26-53`).

#### 2.5.3 영향 범위
- F-009 hook이 이 판정을 재사용한다(순수 함수 export 필요). 기존 커맨드와 공유 상태 없음.

### F-006: `validate` (5종 위반 + 합산 커버리지 + `--changed`)

#### 2.6.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 공통 | `opal/tools/code-scan/code-scan.js` | `cmdValidate` + 위반 검출기 + 커버리지 산출 | 수정 |
| 문서 | `opal/core/references/harness/pm-review-gate.md` | 8·14번 항목에 합산 커버리지·권한 경계 절차 반영 | 수정 |

#### 2.6.2 현재 구현
- `cmdMissing`(`:577-587`)이 유일한 "커버리지 계열" 커맨드이며 나열만 하고 판정·exit code가 없다(항상 exit 0).
- exit code 관례: 사용법·설정 오류는 `process.exit(1)`(`:229`, `:449`, `:455`, `:526`, `:616`). 위반 전용 코드는 미정의.

#### 2.6.3 영향 범위
- CLOSE 진입 게이트에서 호출될 예정(확정 방향 7(b)) → exit code 계약이 파이프라인 차단 신호가 된다.

### F-007: 워커 권한 경계 집행

#### 2.7.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 공통 | `opal/tools/code-scan/code-scan.js` | `validate` 경로 내 도구 관할 필드 재계산·대조 | 수정 |

#### 2.7.2 현재 구현
- 권한 경계 개념 부재. 유사 선례는 state-tool의 `worker_scope_violation` 거부 — 워커는 `--as-worker --worker-stage <자기단계>` 한정이며 다른 단계 행 갱신을 도구가 거부한다 (오케스트레이터 규약, opal-plan-agent AGENT.md §행동 규칙).

#### 2.7.3 영향 범위
- 검출은 **파일시스템·index.json 재계산 대조**로만 수행한다(git·베이스라인·해시 저장 없음 — TASK 제외 항목 "해시·mtime stale 감지" 준수).

### F-008: `feature` 옵셔널 필드 + cross-scope 조회

#### 2.8.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 공통 | `opal/tools/code-scan/code-scan.js` | `cmdFeature` + 스키마 `feature` 필드 | 수정 |
| 문서 | `opal/core/references/header-standard.md` | `feature` 필드 정의 추가 | 수정 |

#### 2.8.2 현재 구현
- 현행 자산은 구조축(module·layer·domain)만 보유한다 — `opal/tools/brain-tool/templates/page-entity.md` frontmatter에도 기능·화면 축 키가 없다(→ D-7).
- 화면·정책 축 토큰 체계는 별도 정의되어 있다 — `citation-rules.md` §8.6: "`POL-{번호}`(정책참조), `ia:{system}:{screen}`(IA참조)" (→ D-8).
- `getSearchPaths`(`:223-240`)는 `opts.scope` 1개만 처리하므로 cross-scope 순회는 호출자 루프로 구현해야 한다.

#### 2.8.3 영향 범위
- 태그 미부여 프로젝트에서 8커맨드 무변화(옵셔널 필드). 태그 실채우기는 범위 외(확정 방향 12).

### F-009: PostToolUse hook

#### 2.9.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 공통 | `opal/tools/code-scan/code-map-hook.js` | PostToolUse hook 본체(Node.js) | 신규 |
| 환경 | `opal/core/hooks/claude-hooks.json` | `PostToolUse` 배열 additive 엔트리 | 수정 |

#### 2.9.2 현재 구현
- `claude-hooks.json`의 유일한 `PostToolUse` 엔트리는 `"matcher": "Bash"`이고(`:2-11`), `todo_mirror_hook.py`는 `tool_input.command`만 파싱한다(`:25-31`). 코드 파일 수정 감지에는 `Edit`/`Write`/`MultiEdit`의 `tool_input.file_path`가 필요하다(→ ANALYSIS §4 발견 5).
- fail-safe 선례: `todo_mirror_hook.py:124-130`이 전 경로 예외를 삼키고 `sys.exit(0)`으로 종료한다.
- 언어는 TASK 제약 ④에 따라 Python(`~/.opal/.venv/bin/python`)이 아니라 Node.js를 사용한다.

#### 2.9.3 영향 범위
- 전역 병합(`install-mac.sh:1212-1219`)이므로 모든 프로젝트에 영향 → H-6 fail-safe가 필수 요건.

### F-010: `headerSource` 스위치

#### 2.10.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 공통 | `opal/tools/code-scan/code-scan.js` | `loadConfig`에 `headerSource` 추가 + 분기 | 수정 |
| 문서 | `opal/core/references/pm/code-scan-management.md` | `headerSource` 추론·관리 규칙 추가 | 수정 |

#### 2.10.2 현재 구현
- `loadConfig`(`:150-164`)는 정확히 4키 객체를 반환하고, 소비자는 `config` 객체 전체를 그대로 전달받아 구조분해하지 않으므로 5번째 키 추가는 하위호환이다 (→ ANALYSIS §1.2 설정 로더 단일화).

#### 2.10.3 영향 범위
- 분기 지점이 `resolveHeader` 진입부 1곳으로 국한되어야 한다(그 외 함수는 스위치를 모른다).

### F-011: 규칙 SSOT 갱신 (7문서)

#### 2.11.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 문서 | `opal/core/references/harness/header-rules.md` | "별도 도구 없음" 교체 + 4단 판정·3단 시점·권한 경계 표 | 수정 |
| 문서 | `opal/core/references/pm/code-scan-management.md` | `headerSource`·code-map 관리 의무 | 수정 |
| 문서 | `opal/core/references/harness/pm-review-gate.md` | 8·14번 항목 갱신 | 수정 |
| 문서 | `opal/core/references/tools.md` | code-scan 커맨드 표에 5서브명령 | 수정 |
| 문서 | `opal/tools/tool-scan/manifest.json` | code-scan `when` 키워드 확장(`:55`) | 수정 |
| 문서 | `opal/tools/brain-tool/README.md` | 2소스 의미 변화 1문장 (PM-3) | 수정 |
| 문서 | `opal/core/references/opal-harness.md` | §9 도구 표 code-scan 행 정합 (PM-3) | 수정 |

#### 2.11.2 현재 구현
- `header-rules.md:12`에 "작성 주체: 워커(LLM)가 직접 작성. 별도 도구 없음."이 그대로 남아 있다.
- `opal-harness.md` §9 도구 표의 code-scan 행은 서브명령을 열거하지 않는 유일한 도구 행이다(다른 행은 "9서브명령…" 형태로 명시) → 정합 대상.
- `tools.md` 변경이력에 "harness §9 drift 정합" 관례가 존재한다 (→ ANALYSIS §3.2).

#### 2.11.3 영향 범위
- 7문서 전부 `## 변경이력` 표 행 추가 의무 (§1.5 [MUST]). `manifest.json`은 변경이력 표가 없는 JSON이므로 예외.

### F-012: 합성 픽스처 + RED 테스트 + dogfooding

#### 2.12.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 환경 | `.opal/code-scan.json` | 선결 — 저장소 스코프 정의(픽스처 격리) | 신규 |
| 환경 | `.gitignore` | `.opal/code-map/` 추적 예외 | 수정 |
| 공통 | `opal/tools/code-scan/tests/fixtures/**` | 6조건 픽스처 + 위반 픽스처 | 신규 |
| 공통 | `opal/tools/code-scan/tests/test-*.js` | RED-first 테스트 7파일 | 신규 |

#### 2.12.2 현재 구현
- `opal/tools/code-scan/`에 `tests/` 디렉토리 자체가 없다 — code-scan 테스트 0건 (→ ANALYSIS §1.4).
- 이 저장소에 `.opal/code-scan.json`이 부재하여 스코프 미지정 스캔이 `[projectRoot]` 전체를 순회한다(`code-scan.js:236-239`) → 픽스처 오염 경로 실재(R-1).
- Node 테스트 컨벤션(유일 선례 `skill-registry`): `node:test` + `node:assert/strict` + `child_process` CLI 블랙박스, 중앙 러너·`package.json` 없음, 파일명 `test-<verb>.js`, RED 기대 인라인 주석 + TC↔S-ID 매핑 표 (→ D-15, `opal/tools/skill-registry/tests/test-validate.js:1-33`).
- `findProjectRoot()`(`:136-148`)의 `.opal` 마커 조건 덕분에 자체 `.opal/`을 가진 픽스처 트리는 자기 자신을 프로젝트 루트로 인식한다 (→ ANALYSIS §4 발견 3).
- 정적 픽스처 커밋 선례: `opal/tools/tool-scan/tests/fixtures/` (→ D-18).

#### 2.12.3 영향 범위
- `.opal/code-scan.json` 신설은 이 저장소의 brain `sync-header`·`missing` 결과를 즉시 바꾼다(전체 순회 → 3스코프 한정) — 의도된 개선이며 dogfooding 로그로 증명한다.

### F-013: `run.sh` 래퍼 신설

#### 2.13.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 환경 | `opal/tools/code-scan/run.sh` | 도구 래퍼(Node 호출) | 신규 |
| 배치 | `scripts/install-mac.sh` | `run.sh` 실행 권한 chmod 블록 | 수정 |

#### 2.13.2 현재 구현
- 등록 도구 12종 중 code-scan에만 `run.sh`가 없다. `tool-scan` 매니페스트는 `"exec": "run.sh --help"`로 등록되어 있어(`manifest.json:56`) 현재 `help_exec_failed`(`tool_scan.py:51` "self --help 셸 실행 실패 (run.sh 부재·실행권한 없음)")로 실패한다.
- 기존 래퍼 12종은 전부 Python venv 호출형이다(`state-tool/run.sh:4-12`, `tool-scan/run.sh:4-12`) — Node 호출형 래퍼는 첫 사례.
- install은 도구별 chmod 블록을 명시 열거한다(`install-mac.sh:1096-1174`) — code-scan 블록은 없다.
- `code-scan.js --help`는 `USAGE`(`:36-74`)를 출력하고 정상 종료한다(`:596`).

#### 2.13.3 영향 범위
- 기존 `node code-scan.js <cmd>` 직접 호출 경로는 `tools.md`(`:205,213-232`)·brain-tool(`brain_tool.py:786-793`)이 사용 중 → 반드시 병존해야 한다(F-013 AC③).

---

## 3. 기능별 설계

> 각 설계 결정 뒤에 `(→ D-N §N)` 단축 인용 또는 `경로:줄번호` 풀 인용을 기재한다 (→ D-8 §3.2).
> FE 화면 설계: **해당 없음** (전량 CLI 도구·문서 — `docs/PROJECT.md` §프로젝트 구성 `Framework` 영역).

### F-001: code-map 스키마 정의

#### 3.1.1 파일 변경 계획

**신규 생성**
| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | (없음 — 상수는 기존 파일에 추가) | - | - | - |

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/code-scan/code-scan.js` | 공통 | `CODE_MAP_DIR`·`CODE_MAP_VERSION`·`MANAGED_FIELDS`·`WORKER_FIELDS`·`ROOT_MIRROR_NAME` 상수 + `USAGE` 갱신 | `code-scan.js:26-34,36-74` |
| 2 | `opal/core/references/header-standard.md` | 문서 | §7 "2소스 표현 — 인라인과 code-map" 절 신설(두 파일 형식 필드 표) + `feature` 필드 행 추가 | (→ D-2 §2) |

#### 3.1.2 데이터 모델 설계

**(A) 상수 (`code-scan.js` Constants 블록 — `:22-34` 직후 추가)**

| 상수 | 값 | 역할 |
|------|-----|------|
| `CODE_MAP_DIR` | `'.opal/code-map'` | 지도 루트 (프로젝트 상대) |
| `CODE_MAP_VERSION` | `1` | `index.json`·매니페스트 `version` 기대값 (정수) |
| `ROOT_MIRROR_NAME` | `'_root'` | 스코프 루트 직속 파일용 미러 파일명 |
| `MANAGED_FIELDS` | `['dir','scope','version','module','layer','domain']` | 도구 관할 (워커 변경 거부 — F-007) |
| `WORKER_FIELDS` | `['description','exports','depends','note','feature']` | 워커 작성 허용 (확정 방향 9 + `feature`는 거부 목록 외) |
| `BUILD_MANIFESTS` | `['package.json','pom.xml','build.gradle','build.gradle.kts','pyproject.toml','setup.py','go.mod','Cargo.toml']` | `discover` 앵커 탐지용 (디스크 실재 확인 기반) |
| `STRIP_CANDIDATES` | `['src/main/java/','src/main/kotlin/','src/test/java/','app/src/main/java/','src/']` | `discover` `stripPrefix` 후보 (디스크 실재 확인 기반) |

**(B) `.opal/code-map/index.json` 필드 스키마**

| 필드 | 필수 | 타입 | 기본값 | 설명 |
|------|------|------|--------|------|
| `version` | 필수 | integer | - | `1` 고정. 불일치 시 `unsupported_version` (exit 1) |
| `origin` | 선택 | `"discover"` \| `"manual"` | `"manual"` | 생성 주체 표기 |
| `status` | 선택 | `"draft"` \| `"reviewed"` | `"draft"` | 초안 상태 표시 (F-003 AC — 소유자 리뷰 후 `reviewed`) |
| `generatedAt` | 선택 | string(ISO8601) | - | `discover` 생성 시각 |
| `note` | 선택 | string | `""` | 소유자 메모 |
| `scopes` | 필수 | object\<string, Scope\> | - | 스코프 정의. 최소 1개. 키 = 스코프명 |
| `scopes[].root` | 필수 | string | - | 프로젝트 루트 상대 디렉토리 경로 (후행 `/` 허용, 정규화하여 저장) |
| `scopes[].anchors` | 선택 | string[] | `[]` | 스코프 루트 상대 모듈 디렉토리 목록. 비었으면 스코프 루트 전체가 단일 앵커 공간 |
| `scopes[].stripPrefix` | 선택 | string[] | `[]` | 앵커 내부에서 제거할 경로 접두 목록(소스 루트·패키지 상용구) |
| `scopes[].readonly` | 선택 | boolean | `false` | `true`면 `target`이 무조건 `manifest` 반환 (F-005 tier①) |
| `domains` | 선택 | object\<string, {paths: string[]}\> | `{}` | tier⑤ 도메인 규칙. `paths` = 글롭 배열 |
| `layerRules` | 선택 | Array\<{match: string, layer: string}\> | `[]` | tier④ 레이어 규칙. `layer`는 `header-standard.md:26` 표준값 권장 |
| `exclude` | 선택 | string[] | `[]` | code-map 연산 전용 추가 제외 디렉토리명. `config.exclude`와 **합집합**으로 사용하되 8커맨드 탐색에는 미적용(제약② 보존) |

**(C) 패키지 매니페스트 `.opal/code-map/{scope}/{mirrorRel}.json` 필드 스키마**

| 필드 | 필수 | 타입 | 기본값 | 관할 | 설명 |
|------|------|------|--------|------|------|
| `version` | 필수 | integer | - | 도구 | `1` 고정 |
| `scope` | 필수 | string | - | 도구 | 소속 스코프명. 매니페스트 경로 첫 세그먼트와 일치해야 함 |
| `dir` | 필수 | string | - | 도구 | 미러 대상 소스 디렉토리 (프로젝트 루트 상대). **역매핑의 권위 소스** |
| `package` | 선택 | object | 없으면 키 생략 | 워커 | 이 디렉토리 공통값 (tier③). 허용 키 = `WORKER_FIELDS` |
| `files` | 필수 | object\<basename, FileEntry\> | `{}` | 키=도구 / 값=워커 | 파일별 고유값 (tier②). 키는 `dir` 실제 파일 목록과 집합 일치 |
| `files[].description` | 선택 | string | `""` | 워커 | 파일 역할 한 줄 |
| `files[].exports` | 선택 | string[] | `[]` | 워커 | 노출 항목. `validate`가 텍스트 존재 대조 (F-006) |
| `files[].depends` | 선택 | string[] | `[]` | 워커 | 의존 모듈 ID |
| `files[].note` | 선택 | string | - | 워커 | 메모 |
| `files[].feature` | 선택 | string | - | 워커 | 기능축 조인 키 (F-008) |
| `files[].module` | 선택 | string | basename stem 파생 | 도구 | 생략 권장. 존재 시 파생값과 일치해야 함(불일치 = `module_override` 위반) |
| `files[].draft` | 선택 | boolean | `description` 공란이면 `true` | 도구 | 골격 미기입 마커 |

- **`layer`·`domain`은 매니페스트에 기재하지 않는다** — tier④(`layerRules`)·tier⑤(`domains.paths`) 전용 필드다. 매니페스트에 키가 존재하는 것 자체가 F-007 위반(`layer_in_manifest`/`domain_in_manifest`)이다. 근거: 확정 방향 5가 tier④를 `index.layerRules`, tier⑤를 `index.domains.paths`로 명명했고(TASK.md §확정된 설계 방향 5), 확정 방향 9가 `layer`·`domain`을 도구 관할로 지정했다. 이 설계는 "재계산 대조로 검출 가능"이라는 F-007 요구를 베이스라인·해시 저장 없이 충족시키는 유일한 결정론적 방법이다 (→ §3.7.2).
- **`module` 파생 규칙**: `stem = basename.slice(0, -path.extname(basename).length)` — 케이스 변환을 하지 않는다. 근거: [MUST] `opal/core/references/header-standard.md` §2: "`module` … 파일 네이밍 컨벤션을 따른다 — Python은 snake_case, TypeScript/JS는 kebab-case, Kotlin/Swift는 PascalCase." 즉 파일명 자체가 이미 언어 컨벤션을 만족하므로 stem 그대로가 정답이다. 다중 확장자(`auth.service.ts`)는 마지막 확장자만 제거해 `auth.service`가 된다.
- **트레이드오프 T-1**: basename과 다른 `module` 명을 원하는 파일은 code-map으로 표현할 수 없다. 탈출구는 인라인 헤더(파일 단독 승리)다. 근거: [MUST] `opal/core/PRINCIPLES.md` §2 Simplicity First: "Solve only the current requirement. No speculative abstraction or unrequested flexibility."

**(D) `_source` 계약 (5종)**

| 값 | tier | 의미 |
|----|------|------|
| `inline` | ① | 소스 파일 인라인 `@header` (파일 단독 승리, 병합 없음) |
| `file` | ② | 매니페스트 `files[basename]` |
| `package` | ③ | 매니페스트 `package` |
| `rule` | ④ | `index.layerRules` 매칭 + `module` basename 파생 (도구·index 규칙 파생) |
| `domain` | ⑤ | `index.domains.paths` 매칭 |

- 결과 객체는 `_source`(문자열, **최근접 기여 tier 1개**)와 `_sources`(객체, 필드별 tier)를 함께 갖는다. `_source` 값 도메인은 위 5종으로 닫힌다(F-002 AC). `_sources`의 값 도메인도 동일 5종이다 — `module` 파생은 `rule`로 표기한다.
- 추가 키는 출력 계층이 필드 목록을 검증하지 않으므로 무해 통과한다 (`code-scan.js:348-376`, → ANALYSIS §4 발견 1).

#### 3.1.3 환경 변경
해당 없음 (외부 패키지 0 — `code-scan.js:19-20`이 `fs`/`path`만 require).

#### 3.1.4 배치/마이그레이션
해당 없음 (기존 데이터 없음 — 신규 포맷).

#### 3.1.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | F-1 AC | 산출물 검사 | `header-standard.md`에 2소스 표현 절이 존재하고 index.json·매니페스트 필수/선택 필드가 각각 표로 열거된다 |
| TS-002 | F-1 AC | 기능 테스트 | `version: 2` index를 준 픽스처에서 모든 code-map 서브명령이 `unsupported_version`으로 exit 1 |
| TS-003 | F-1 AC | 기능 테스트 | `scopes` 누락·`root` 누락 index에서 `invalid_index` exit 1 |

---

### F-002: 5단 상속 해석 + 경로 사상 + 단일 파일 역매핑

#### 3.2.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/code-scan/code-scan.js` | 공통 | `loadCodeMap`·`resolveScope`·`mirrorPathForDir`·`loadManifest`·`matchLayerRule`·`matchDomain`·`resolveHeader` 신설 + `scanAll:324` 1줄 교체 | `code-scan.js:318-333` |

#### 3.2.2 함수 시그니처 및 알고리즘

**(A) 컨텍스트 로더 — 프로세스당 1회 (lazy)**

```
loadCodeMap(projectRoot) -> { index, manifests: Map<string, object|null>, present: boolean }
```
- `path.join(projectRoot, CODE_MAP_DIR, 'index.json')` 부재 → `{ present: false }` 즉시 반환. 이후 모든 code-map 로직이 no-op이 되어 **code-map 부재 프로젝트 동작 변화 0**을 코드 구조로 보장한다 (제약②, F-010 AC).
- `manifests`는 경로→파싱결과 메모 캐시(동일 매니페스트를 파일 수만큼 재파싱하지 않기 위함). 파싱 실패는 `null`로 캐시하고 `validate`에서 `manifest_parse_failed`로 보고한다.

**(B) 스코프 판정**

```
resolveScope(relPath, index) -> { name, scope } | null
```
- `relPath`(프로젝트 루트 상대)가 `scopes[*].root`의 접두인 스코프들 중 **root 문자열이 가장 긴 것**이 승리한다. 동률이면 **스코프명 사전순 오름차순 최소값**이 승리한다(결정론적 tie-break).
- 매칭 없으면 `null` → 지도 커버리지 없음.

**(C) 미러 경로 사상 — 적용 순서와 충돌 우선순위**

```
mirrorPathForDir(dirRel, scopeName, scope) -> { mirrorRel, anchor } | { skipped: reason }
```
적용 순서는 **`root` → `anchors` → `stripPrefix`** 로 고정한다 (PM 지시 명세).

1. **`root` 절단**: `rel = path.relative(scope.root, dirRel)`. `rel`이 `..`로 시작하면 스코프 외 → `skipped: 'out_of_scope'`.
2. **`anchors` 매칭**: `scope.anchors`가 비어 있지 않으면, `rel === a` 또는 `rel`이 `a + '/'`로 시작하는 앵커 `a` 중 **가장 긴 것**이 승리(중첩 앵커 대응). 동률 불가(문자열 집합이므로 최장 유일). 매칭 없으면 `skipped: 'no_anchor'` — 앵커 선언 스코프에서 앵커 밖 디렉토리는 지도 대상이 아니다. 앵커가 비어 있으면 `anchor = ''`, `sub = rel`.
3. **`stripPrefix` 절단**: `sub`(앵커 이후 잔여 경로)에 대해 `scope.stripPrefix`를 **길이 내림차순**으로 순회하여 `sub`가 접두와 일치하는 **첫 하나만** 제거하고 중단한다(중복 제거 금지 → 결정론). 동률 길이면 사전순 최소가 승리.
4. **조립**: `mirrorRel = path.join(anchor, stripped)`. 결과가 빈 문자열이면 `ROOT_MIRROR_NAME`(`_root`).
5. **매니페스트 경로** = `{CODE_MAP_DIR}/{scopeName}/{mirrorRel}.json`.

*예시* (F-012 픽스처 기준): scope `svc` (`root: "svc/"`, `anchors: ["order-api","ship-api"]`, `stripPrefix: ["src/main/java/com/acme/","src/main/java/"]`)
```
소스 디렉토리 : svc/order-api/src/main/java/com/acme/order/service
① root 절단   : order-api/src/main/java/com/acme/order/service
② anchor      : anchor="order-api", sub="src/main/java/com/acme/order/service"
③ stripPrefix : "src/main/java/com/acme/" (최장) 제거 → "order/service"
④ 조립        : mirrorRel = "order-api/order/service"
⑤ 매니페스트  : .opal/code-map/svc/order-api/order/service.json
```
- **충돌 시 우선순위 규칙**: 서로 다른 두 소스 디렉토리가 동일 `mirrorRel`로 접히면 **어느 쪽도 우선하지 않고 오류**다(`mirror_collision`). `scaffold`는 exit 1로 거부하며 어떤 파일도 쓰지 않고, `validate`는 `conflict`(sub-reason `mirror_collision`)로 보고한다. 근거: 덮어쓰기 승자 규칙을 두면 소유자가 작성한 매니페스트가 조용히 소실되어 확정 방향 10(보존 merge)과 모순된다.
- `mirrorRel`이 `_root`인 실제 디렉토리(`{scope.root}/_root/`)가 존재하면 예약명 충돌 → 동일하게 `mirror_collision`.

**(D) 양방향 계산 보장**
- **정방향**(소스 디렉토리 → 매니페스트 경로): (C)의 결정론적 알고리즘.
- **역방향**(매니페스트 → 소스 디렉토리): 매니페스트의 `dir` 필드가 **권위 소스**다. `stripPrefix` 절단은 정보 손실적이라 문자열 역산이 불가능하므로 역매핑을 알고리즘으로 풀지 않고 `dir`로 명시 보존한다.
- **정합 검사**: `validate`가 모든 매니페스트에 대해 `mirrorPathForDir(m.dir, ...)`를 재계산하여 실제 파일 경로와 대조한다. 불일치 = `dir_mismatch`(F-007). 이 대조가 "양방향 계산 가능"을 런타임에 강제한다.

**(E) 단일 파일 역매핑 (PM-2 / R-5 해소 — 필수 구현)**
- 읽기 경로에서는 역방향 계산이 **필요 없다**: 파일 → `path.dirname` → (B) 스코프 판정 → (C) 정방향 사상 → 매니페스트 경로 → `files[basename]`. 즉 `discoverFiles`가 단일 파일을 반환해 스코프 컨텍스트를 잃어도(`code-scan.js:242-248`), `resolveHeader`가 파일 경로만으로 스코프를 재판정하므로 정보 손실이 없다.
- 이 설계로 `code-scan scan <file> --json`(PM Gate 8번, `pm-review-gate.md:53`)이 readonly 스코프 파일에서도 매니페스트 헤더를 반환한다.
- 비용: 스코프 수 N에 대해 O(N) 문자열 비교 + 매니페스트 1회 로드(캐시).

**(F) `layerRules` 구체성 순서 (배열 순서 무관 — 결정론)**

```
matchLayerRule(relPath, layerRules) -> { layer, rule } | null
matchDomain(relPath, domains)       -> { domain, pattern } | null
```
- 글롭 매칭은 기존 `patternToRegex`(`code-scan.js:170-183`)를 재사용한다(`**`=임의, `*`=슬래시 제외, `?`=1문자) — 새 매칭 엔진을 만들지 않는다. 대상 문자열은 파일의 프로젝트 루트 상대 경로.
- **구체성 점수** = 패턴 내 **리터럴 문자 수** (와일드카드 메타문자 `*`·`?`를 제외한 문자 수). 높을수록 구체적 → 승리.
- **tie-break 순서** (전부 결정론):
  1. 리터럴 문자 수 큰 것
  2. 와일드카드 토큰 수(`**`/`*`/`?` 출현 횟수) 적은 것
  3. 패턴 원문 길이 긴 것
  4. 패턴 원문 사전순 오름차순 최소
- **배열 순서는 우선순위에 관여하지 않는다.** 근거: `discover`가 생성하는 배열 순서가 바뀌면 조회 결과가 달라지는 비결정성을 제거하기 위함 (H-12).
- `domains`는 동일 점수 체계를 쓰고, 최종 동률 시 **도메인명 사전순 최소**가 승리한다.

**(G) 5단 상속 해석기**

```
resolveHeader(filePath, ctx) -> object | null
  ctx = { projectRoot, config, codeMap }
```
1. **`headerSource` 게이트** (F-010 분기 지점 — 유일): `config.headerSource`가 `'manifest'`면 인라인을 읽지 않고 5로, `'inline'`이면 2~3만 수행, `'auto'`(기본)면 전량.
2. `inline = extractHeader(filePath)` — 기존 함수(`code-scan.js:274-312`) **무변경 재사용**.
3. `inline !== null` → `return { ...inline, _source: 'inline', _sources: <모든 인라인 키를 'inline'으로> }`. **병합 없음, 파일 단독 승리** (확정 방향 5).
4. `ctx.codeMap.present === false` 또는 `headerSource === 'inline'` → `return inline`(= `null`). ← **제약② 하위호환 보증 지점**: 반환값이 `extractHeader`와 완전히 동일하며 `_source` 키도 붙지 않는다.
5. 지도 해석: 스코프 판정(B) → 정방향 사상(C) → 매니페스트 로드 → `fe = m.files[basename]`, `pkg = m.package`.
   필드별 최근접 승리로 조립:
   | 필드 | tier 순서 | `_sources` 값 |
   |------|----------|--------------|
   | `description`/`exports`/`depends`/`note`/`feature` | `fe.X` → `pkg.X` | `file` / `package` |
   | `module` | `fe.module` → stem 파생 | `file` / `rule` |
   | `layer` | `matchLayerRule(rel)` | `rule` |
   | `domain` | `matchDomain(rel)` | `domain` |
   `draft`는 진단 필드로 그대로 전달한다.
6. 기여 필드가 0개면 `return null` → `missing`·`uncovered` 판정이 정상 동작한다.
7. `_source` = 기여한 tier 중 최근접(`file` > `package` > `rule` > `domain`).
8. **매니페스트에 `layer`/`domain` 키가 있어도 해석에 반영하지 않는다** — `validate`(F-007)의 판정과 해석 결과가 일치해야 위반 매니페스트가 조회 결과를 오염시키지 않는다.

**(H) 단일 교체 지점 및 8커맨드 무변경 논거**

```diff
  function scanAll(projectRoot, config, opts) {
    const files = discoverFiles(projectRoot, config, opts);
+   const ctx = { projectRoot, config, codeMap: loadCodeMap(projectRoot) };
    ...
-     const header = extractHeader(f);
+     const header = resolveHeader(f, ctx);
```
- 교체는 `code-scan.js:324` 1줄 + `ctx` 준비 1줄이다. 무변경 보장 논거 3단:
  1. **호출 그래프 수렴**: 8커맨드 전부가 `scanAll`을 통과한다 — `cmdScan:390`/`cmdDomain:394`/`cmdLayer:421`/`cmdSearch:447`/`cmdExports:470`/`cmdSummary:496`/`cmdDepends:524`는 `scanHeaders:335`를 경유하고 `cmdMissing:577`은 `scanAll`을 직접 호출한다 (→ ANALYSIS §1.2). 따라서 상위 커맨드 함수 8개는 **코드 변경 0**이다.
  2. **탐색·출력 계층 불변**: `discoverFiles:242`/`walkDir:202`/`getSearchPaths:223`/`fmtBrief:348`/`fmtFull:363`/`fmtJson:372`는 손대지 않는다. `_source`는 출력 계층이 키 목록을 검증하지 않아 자동 통과한다.
  3. **부재 시 동일값**: (G)4단계에서 code-map 부재 시 `extractHeader`의 반환값을 **그대로** 돌려주므로 출력이 바이트 동일하다. 이는 골든 파일 대조로 검증한다(TS-006).

#### 3.2.3 환경 변경 / 3.2.4 배치·마이그레이션
해당 없음.

#### 3.2.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-004 | F-2 AC | 기능 테스트 | 5단 각각 단독 적용 5케이스에서 필드값이 기대치와 일치하고 `_source`가 `inline`/`file`/`package`/`rule`/`domain`으로 표기된다 |
| TS-005 | F-2 AC | 기능 테스트 | 혼재 케이스(인라인 + 매니페스트 동시)에서 인라인이 병합 없이 단독 승리하고 `_source: inline` |
| TS-006 | 제약② | 회귀 테스트 | code-map 없는 픽스처에서 8커맨드 `--json` 출력이 골든 파일과 바이트 동일 + `_source` 키 0건 |
| TS-007 | F-2 AC / R-5 | 통합 테스트 | 인라인 없고 매니페스트만 있는 파일에 `scan <file> --json` → 헤더 반환, `_source: file` |
| TS-008 | F-2 AC | 단위 테스트 | `mirrorPathForDir` 정방향 사상이 예시 5케이스(깊은 경로·stripPrefix 최장 승리·앵커 없음·루트 직속 `_root`·스코프 외) 기대치 일치 |
| TS-009 | H-12 | 단위 테스트 | 동일 구체성 점수 규칙 2개를 배열 순서만 바꿔 2회 조회 → 동일 `layer` 반환 |
| TS-010 | H-11 | 기능 테스트 | 충돌 픽스처에서 `mirror_collision` 검출 |

---

### F-003: `discover` 서브명령

#### 3.3.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/code-scan/code-scan.js` | 공통 | `cmdDiscover` + `inferScopes`/`inferAnchors`/`inferStripPrefix`/`inferLayerRules`/`inferExclude` | (→ D-4 §추론 소스 3종) |

#### 3.3.2 API 설계

```
code-scan discover [--out <path>] [--dry-run] [--json]
```
| 옵션 | 기본값 | 역할 |
|------|--------|------|
| `--out <path>` | `.opal/code-map/index.json` | 초안 출력 경로 |
| `--dry-run` | off | 파일을 쓰지 않고 stdout에 초안 JSON 출력 (pass1 소유자 리뷰용 — 확정 방향 8) |

- 기존 파일이 있으면 **덮어쓰지 않고** `index_exists` 에러(exit 1) + `--out`/`--dry-run` 안내. 근거: 소유자 리뷰를 통과한 index를 재실행이 되돌리면 확정 방향 10(보존)과 모순.

**추론 규칙 (전부 디스크 실재 확인 기반 — 추측 금지)**

| 필드 | 추론 소스 | 규칙 |
|------|----------|------|
| `scopes` | ① `.opal/code-scan.json`의 `scopes`(존재 시 1:1 승계, `root`=그 경로) ② 부재 시 프로젝트 루트 1-depth 디렉토리(`config.exclude` 제외) | (→ D-4 §추론 소스 3종: `scopes`는 `docs/PROJECT.md §프로젝트 구성` → 이 저장소는 `.opal/code-scan.json`이 그 표에서 파생되므로 ①이 동일 근거를 승계) |
| `anchors` | **2종 탐지** — (a) 빌드 매니페스트 기반: 스코프 루트 하위 깊이 ≤3에서 `BUILD_MANIFESTS` 중 하나를 포함한 디렉토리 (b) (a) 결과 0건이고 루트 직속 하위 디렉토리가 ≥2개면 그 1-depth 디렉토리명 목록 | F-012 조건③ (앵커 2종) |
| `stripPrefix` | 각 앵커 내부에서 `STRIP_CANDIDATES` 중 **실제 존재하는** 경로만. 추가로 소스 루트 직하가 단일 체인(`com/{org}/`)이면 그 체인을 후보에 append | F-012 조건② |
| `layerRules` | `header-standard.md:26` 코드 layer 표준값 16종 중, 스코프 하위에 **동명 디렉토리가 실재하는** 값에 대해 `{ match: "**/{L}/**", layer: L }` 생성 | (→ D-2 §2 layer 표준값) |
| `exclude` | `DEFAULT_CONFIG.exclude`(`code-scan.js:32`) + 컴파일 산출물 후보(`target`,`out`,`bin`,`obj`,`.gradle`,`generated`,`coverage`) 중 실재하는 것 | F-012 조건⑤ |
| `domains` | 추론하지 않는다(`{}`) — 도메인은 비즈니스 판단이므로 소유자 기입 | [MUST] `opal/core/PRINCIPLES.md` §2 Simplicity First: "Solve only the current requirement. …" |
| `readonly` | 항상 `false` — 규약은 추론 불가, 소유자 지정 | 동상 |

- 초안 표시: `origin: "discover"`, `status: "draft"`, `generatedAt`, `note: "OWNER REVIEW REQUIRED — readonly/anchors/stripPrefix 확인 후 status를 reviewed로 변경"` (F-003 AC "초안 상태 표시가 파일에 포함된다").
- 출력: 사람 가독 요약(스코프 수·앵커 수·규칙 수·exclude) + `--json` 시 `{ ok, out, scopes, counts }`.

#### 3.3.3 환경 변경 / 3.3.4 배치·마이그레이션
해당 없음.

#### 3.3.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-011 | F-3 AC | 기능 테스트 | 픽스처 실행 시 scopes ≥2종·layerRules(디렉토리 규약 기반) ≥1·exclude에 컴파일 산출물 디렉토리 포함된 초안 생성 |
| TS-012 | F-3 AC | 산출물 검사 | 초안 파일에 `origin`/`status: "draft"`/`generatedAt`/`note` 초안 표시가 존재 |
| TS-013 | F-3 AC | 기능 테스트 | 앵커 2종 픽스처에서 (a)빌드 매니페스트 기반·(b)단순 디렉토리 앵커가 각각 검출 |
| TS-014 | H-10 | 기능 테스트 | 기존 index 존재 시 `index_exists` exit 1, `--dry-run`은 파일 미생성 |

---

### F-004: `scaffold` + 멱등 보존 merge

#### 3.4.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/code-scan/code-scan.js` | 공통 | `cmdScaffold` + `mergeManifest` + `writeIfChanged` | 확정 방향 8 pass2 + 10 |

#### 3.4.2 알고리즘 설계

```
code-scan scaffold [--scope <name>] [--dry-run] [--json]
mergeManifest(existing|null, recomputed) -> { manifest, pruned[], added[] }
```

**(A) 대상 디렉토리 열거**
- 스코프별로 `scope.root`를 재귀 순회한다. 제외 = `config.exclude ∪ index.exclude`(디렉토리명 매칭, `walkDir:211` 규약 동일) + `config.excludePatterns`(파일 단위, `isExcluded:185` 재사용).
- 확장자 필터 = `config.extensions`(`code-scan.js:214` 규약 동일).
- **코드 파일이 1개 이상 있는 디렉토리만** 매니페스트 대상이다(빈 중간 디렉토리는 파일 생성 안 함) → 확정 방향 2의 "디렉토리(패키지) 단위 미러 1파일". 재귀 하위 파일은 각자의 디렉토리 매니페스트에 속한다(비재귀 `files` 집합).
- `anchors` 선언 스코프에서 앵커 밖 디렉토리는 `skipped: no_anchor`로 집계만 한다.

**(B) 멱등 보존 merge — 필드별 규칙**

| 대상 | 규칙 |
|------|------|
| `version`·`scope`·`dir` | 재계산 값으로 **덮어쓰기** (도구 관할) |
| `files` 키 집합 | 디스크 실제 파일 목록으로 **재계산**. 정렬은 `Array.prototype.sort()` 기본(코드포인트) — `discoverFiles:252,257`의 `.sort()` 관례 동일 |
| 기존 파일 엔트리 | 기존 객체의 **모든 키를 그대로 보존**(미지 키 포함). `draft`만 재계산: `description`이 비문자열/공백이면 `true`, 아니면 키 제거 |
| **신규 파일** | `{ "description": "", "exports": [], "draft": true }` 골격 추가 → `added[]`에 기록 |
| **삭제 파일**(기존 키 중 디스크 부재) | 해당 엔트리 **제거** + `pruned[]`에 기록해 보고. 근거: 존재하지 않는 파일을 서술하는 데이터는 보존 가치가 없고 `validate`의 `orphan`을 영구 유발한다 |
| `package` | 기존 객체 **그대로 보존**. 부재 시 키를 만들지 않는다(불필요 diff 방지) |
| `dir` 소멸 매니페스트 | **자동 삭제하지 않고** `stale[]`로 보고만 한다(사람 작성 내용 소실 방지). 소유자가 삭제한다 |

**(C) 결정론적 직렬화 (H-10)**
- 키 순서 고정: `version` → `scope` → `dir` → `package` → `files`. `files` 내부는 basename 정렬. 엔트리 내부는 `WORKER_FIELDS` 순서 → `module` → `draft` → 미지 키(원 순서 유지).
- `JSON.stringify(obj, null, 2) + '\n'`.
- `writeIfChanged`: 기존 파일 내용과 동일하면 쓰지 않는다(mtime churn 방지). 2회 연속 실행 시 바이트 동일 = 멱등 증거(TS-016).

**(D) 충돌·오류 처리**
- `mirror_collision` 검출 시 **아무 파일도 쓰지 않고** exit 1 (H-11). 사전 검사 단계에서 전체 사상을 계산해 충돌 여부를 먼저 판정한 뒤 쓰기 단계로 진입하는 2-pass 구조.
- 기존 매니페스트 JSON 파싱 실패 → 해당 매니페스트 스킵 + `manifest_parse_failed` 보고 + exit 1 (덮어쓰기로 원본 파괴 금지).

**(E) 출력**
- 요약: `created`/`updated`/`unchanged`/`added files`/`pruned`/`stale`/`skipped` 카운트. `--json`은 동일 구조 + 경로 목록.

**(F) `--inline` 미채택 (PM-5)**
- 소스 파일 주석 삽입 기능은 이번 범위에서 제외한다. `scaffold`는 `.opal/code-map/` 외부에 **어떤 파일도 쓰지 않는다**. 근거: [MUST] `opal/core/PRINCIPLES.md` §3 Surgical Changes: "Touch only what the plan names. Don't improve adjacent code."

#### 3.4.3 환경 변경 / 3.4.4 배치·마이그레이션
해당 없음 (기존 매니페스트 없음 — 최초 도입).

#### 3.4.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-015 | F-4 AC① | 기능 테스트 | 대상 스코프의 코드 보유 소스 디렉토리 수 = 생성된 매니페스트 수 |
| TS-016 | F-4 AC② / H-10 | 기능 테스트 | `dir`·`files` 키가 실제 파일 목록과 일치하고, 2회 연속 실행 산출물이 바이트 동일 |
| TS-017 | F-4 AC③ | 기능 테스트 | description 채운 뒤 재실행 → 값 유지 + 신규 파일만 `draft: true` 빈 엔트리로 추가 |
| TS-018 | F-4 AC③ | 기능 테스트 | 소스 파일 삭제 후 재실행 → 해당 엔트리 제거 + `pruned`에 보고 |
| TS-019 | PM-5 | 회귀 테스트 | scaffold 실행 후 소스 파일 mtime·내용 변화 0건 |

---

### F-005: `target` 4단 기록 위치 판정

#### 3.5.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/code-scan/code-scan.js` | 공통 | `decideTarget` 순수 함수 + `cmdTarget` (hook 재사용 위해 `module.exports` 노출) | 확정 방향 6 |

#### 3.5.2 API 설계

```
code-scan target <file> [--json]
decideTarget(fileRel, ctx) -> { write_to, reason, scope?, manifest?, key? }
```

**판정 순서 (확정 방향 6 — 이 순서를 바꾸면 규약 위반, H-15)**

| # | 조건 | `write_to` | `reason` |
|---|------|-----------|---------|
| ① | 소속 스코프의 `readonly === true` | `manifest` | `readonly_repo` |
| ② | 인라인 `@header` 존재 (`extractHeader !== null`) | `inline` | `inline_exists` |
| ③ | 파일이 디스크에 없음 (= 신규 파일) | `inline` | `new_file` |
| ④ | 그 외 (존재 + 인라인 없음) | `manifest` | `legacy_no_header` |

- `reason` 4종 계약: `readonly_repo` \| `inline_exists` \| `new_file` \| `legacy_no_header`. 이 4값 외를 반환하지 않는다(F-005 AC).
- `write_to === 'manifest'`면 `scope`·`manifest`(프로젝트 루트 상대 경로)·`key`(basename)를 함께 반환한다(F-005 AC).
- 스코프 판정 실패(지도 관할 밖) 시 → `{ write_to: 'inline', reason: <②③④ 규칙 적용> }`. 지도가 관할하지 않는 파일은 인라인이 유일한 기록 위치이므로 ①만 스킵된다.
- code-map 부재 프로젝트: `ctx.codeMap.present === false` → 항상 `inline`(②/③/④ 중 인라인 반환 경로만 도달, ④는 `legacy_no_header`+`inline`로 축약). 즉 지도가 없으면 현행 규칙(`header-rules.md:26-53`)과 동일 결론.
- `headerSource` 스위치는 `target`에 영향을 주지 않는다 — 스위치는 **읽기 해석** 전용이고 기록 위치는 확정 방향 6이 SSOT다 (설계 결정, §3.10.2 (C)).
- "신규 파일" 판정 근거는 **디스크 부재**다. 워커가 파일을 만든 뒤 호출하면 ④가 나오지만, 그 경우에도 "헤더를 어딘가에 기록해야 한다"는 결론은 동일하며 hook(F-009)이 사후 감지를 담당한다. `--new` 류 플래그는 도입하지 않는다 ([MUST] `opal/core/PRINCIPLES.md` §2 Simplicity First).

#### 3.5.3 환경 변경 / 3.5.4 배치·마이그레이션
해당 없음.

#### 3.5.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-020 | F-5 AC | 기능 테스트 | `readonly_repo`·`inline_exists`·`new_file`·`legacy_no_header` 4조건에서 각각 해당 `reason`과 올바른 `write_to` 반환 |
| TS-021 | F-5 AC | 기능 테스트 | `write_to: manifest`일 때 `manifest` 경로·`key`·`scope`가 실제 미러 경로와 일치 |
| TS-022 | H-15 | 기능 테스트 | readonly 스코프 × (신규/인라인보유/레거시) 3케이스 전부 `manifest`+`readonly_repo` |
| TS-023 | 제약② | 회귀 테스트 | code-map 부재 트리에서 `target`이 항상 `inline` 반환 |

---

### F-006: `validate` (5종 위반 + 합산 커버리지 + `--changed`)

#### 3.6.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/code-scan/code-scan.js` | 공통 | `cmdValidate` + `checkOrphan`/`checkUncovered`/`checkConflict`/`checkDraft`/`checkExports` + `computeCoverage` | 확정 방향 7(b) |
| 2 | `opal/core/references/harness/pm-review-gate.md` | 문서 | 8·14번 항목에 합산 커버리지·권한 경계·`validate --changed` 절차 반영 | `pm-review-gate.md:52-56,89-94` |

#### 3.6.2 API 설계

```
code-scan validate [--scope <name>] [--changed <csv|->] [--json]
```

**(A) 위반 5종 계약**

| 코드 | sub-reason | 검출 방법 |
|------|-----------|----------|
| `orphan` | `file_missing` / `dir_missing` | 매니페스트 `files` 키에 대응 소스 파일 부재 / `dir` 디렉토리 부재 |
| `uncovered` | `no_entry` / `incomplete` | 소스 파일이 인라인·지도 어디에도 없음 / 해석 결과에 필수 5필드(`module`·`layer`·`domain`·`description`·`exports`) 중 결손 (필수 5종 근거 → D-2 §2) |
| `conflict` | `inline_shadowed` / `mirror_collision` | 인라인 헤더 보유 파일에 실질 필드를 가진 매니페스트 엔트리 존재(인라인 단독 승리로 도달 불가 = 모순) / 두 소스 디렉토리가 동일 미러 경로 |
| `draft` | - | `files[].draft === true` 또는 `description` 공백 |
| `exports_not_found` | - | (B) 참조 |

**(B) `exports` 존재 대조 (PM-4 — 문법 파싱 금지)**
- 대상: 해석 결과 `exports` 배열의 각 식별자. 대상 파일 텍스트를 읽어 **부분 문자열 포함 여부**만 확인한다.
- 읽기 범위: 파일 전체(`fs.readFileSync`). `readFileHead`(`:264-272`, 8192B)는 헤더용이므로 재사용하지 않는다 — exports는 파일 하단에 나타날 수 있다.
- 정규화: 식별자에서 앞뒤 공백 제거. 라우터 스타일 `"POST /auth/login"`(→ D-2 §4)은 공백 분리 후 **마지막 토큰**(`/auth/login`)으로 대조한다. 빈 문자열은 스킵.
- 보고 단위: 파일 · 매니페스트 키 · 식별자 (F-006 AC).
- **계약된 한계 (H-14)**: 주석·문자열 리터럴 내 우연 일치는 통과로 계약한다. 문법 파서를 도입하지 않는 것이 PM-4 확정 사항이며, [MUST] TASK.md F-6 AC: "**exports 존재 대조**는 언어 문법 파싱 없이 대상 파일 텍스트에 해당 식별자가 나타나는지만 확인하며(무의존 유지)".
- 인라인 헤더 파일도 동일하게 검사한다(확정 방향 11 "양쪽 공용").

**(C) 커버리지 합산 (확정 방향 11)**
```
coverage = { total, inline, manifest, covered, percent }
covered = inline + manifest   (동일 파일 이중 계상 금지 — 인라인 우선)
percent = total === 0 ? 100 : round(covered / total * 1000) / 10
```
- `total` 분모 = `discoverFiles`(스코프 전체) − (`index.exclude` 추가 제외).

**(D) `--changed` 입력 형식**
| 형식 | 동작 |
|------|------|
| `--changed "a.js,dir/b.ts"` | 쉼표 구분. 공백 트림 + 빈 항목 제거 — `--exclude` 파싱 관례 재사용(`code-scan.js:114-116`) |
| `--changed -` | stdin에서 개행 구분 목록을 읽는다 (긴 `changed_files` 목록 파이핑) |
- 경로는 프로젝트 루트 상대 또는 절대 둘 다 허용하고 내부에서 상대로 정규화한다.
- 대상 외 확장자·존재하지 않는 경로·스코프 밖 경로는 판정에서 제외하고 `skipped[]`에 기록한다(오탐 방지).
- `--changed` 모드에서는 `uncovered`·`conflict`·`draft`·`exports_not_found`를 **주어진 파일에 한해** 판정하고, `orphan`은 그 파일이 속한 매니페스트에 한해 판정한다. 커버리지는 변경 파일 집합 기준으로 별도 산출하며 `mode: "changed"`로 표기한다.

**(E) exit code 계약**
| exit | 조건 |
|------|------|
| 0 | 위반 0건 |
| 1 | 사용법·설정·스키마 오류(`unsupported_version`·`invalid_index`·`manifest_parse_failed`·알 수 없는 스코프) — 기존 관례 계승(`code-scan.js:229,449,455,526,616`) |
| 2 | 위반 ≥1건 (5종 + `worker_scope_violation` 포함) |

- **`draft`도 차단 대상이다** (exit 2). 근거: [MUST] TASK.md F-6 AC: "5종 위반(orphan·uncovered·conflict·draft·exports_not_found)을 각각 심어둔 픽스처에서 유형별로 검출되고, 위반 존재 시 non-zero exit". 4-pass 파이프라인에서 `validate`는 pass4에만 실행되므로(확정 방향 8) pass2 직후 실패는 정상 흐름이 아니다. 영향 범위는 `--changed`로 한정한다 (H-13).

**(F) 출력 스키마 (`--json`)**
```json
{ "ok": false, "command": "validate", "mode": "full|changed",
  "coverage": { "total": 0, "inline": 0, "manifest": 0, "covered": 0, "percent": 0 },
  "counts": { "orphan": 0, "uncovered": 0, "conflict": 0, "draft": 0,
              "exports_not_found": 0, "worker_scope_violation": 0 },
  "violations": [ { "code": "orphan", "sub": "file_missing", "scope": "svc",
                    "manifest": ".opal/code-map/svc/...json", "key": "X.java",
                    "file": "svc/...", "detail": "" } ],
  "skipped": [] }
```

#### 3.6.3 환경 변경 / 3.6.4 배치·마이그레이션
해당 없음.

#### 3.6.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-024 | F-6 AC | 기능 테스트 | 5종 위반을 각각 심은 픽스처에서 유형별 검출 + exit 2 |
| TS-025 | F-6 AC | 기능 테스트 | 커버리지 %가 인라인+지도 합산으로 산출(이중 계상 0) |
| TS-026 | F-6 AC | 기능 테스트 | `--changed "a,b"` / `--changed -`(stdin) 두 형식에서 지정 파일만 판정, `skipped[]` 기록 |
| TS-027 | F-6 AC / H-14 | 단위 테스트 | exports 존재/미존재/주석내존재 3케이스 판정이 계약과 일치 |
| TS-028 | F-6 AC | 기능 테스트 | 위반 0 픽스처에서 exit 0, `ok: true` |
| TS-029 | H-13 | 통합 테스트 | scaffold 직후 exit 2(draft N) → 채움 후 exit 0 |

---

### F-007: 워커 권한 경계 집행

#### 3.7.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/code-scan/code-scan.js` | 공통 | `checkWorkerScope(manifestPath, manifest, ctx)` → `validate` 경로에 편입 | 확정 방향 9 |

#### 3.7.2 검출 방법 — 도구 관할 필드 재계산·대조

**설계 전제**: 베이스라인·해시·mtime·git을 저장하지 않는다(TASK §범위 제외 "해시·mtime stale 감지"). 따라서 "누가 썼는가"를 추적하는 대신 **도구 관할 필드를 전부 재계산 가능하게 설계**하고, 재계산값과 불일치하면 침범으로 판정한다.

| 도구 관할 필드 | 재계산·대조 방법 | 위반 detail |
|---------------|-----------------|-----------|
| `dir` | `mirrorPathForDir(m.dir, m.scope, index.scopes[m.scope])`를 정방향 재계산 → 매니페스트의 **실제 파일 경로**와 문자열 대조 | `dir_mismatch` |
| `scope` | 매니페스트 실제 경로의 `.opal/code-map/` 다음 첫 세그먼트와 `m.scope` 대조 + `index.scopes[m.scope].root`가 `m.dir`의 접두인지 확인 | `scope_mismatch` |
| `files` 키 집합 | `m.dir` 디렉토리를 `config.extensions`·`config.exclude ∪ index.exclude`·`excludePatterns` 적용해 열거 → **집합 동등성** 비교 | `files_key_added` (디스크에 없는 키 추가) / `files_key_removed` (디스크에 있는데 키 없음) |
| `module` | 키 존재 시 `stem` 파생값과 대조 (생략은 정상) | `module_override` |
| `layer` | `package`/`files[*]`에 키 **존재 자체**가 위반 (tier④ 전용 필드) | `layer_in_manifest` |
| `domain` | `package`/`files[*]`에 키 **존재 자체**가 위반 (tier⑤ 전용 필드) | `domain_in_manifest` |
| `version` | 정수 `CODE_MAP_VERSION` 대조 | `unsupported_version` (exit 1 — 스키마 오류로 분류) |

- 위반 코드는 F-007 요구대로 **전용 코드** `worker_scope_violation`이며 `sub`에 위 detail을 담는다.
- `files_key_removed`는 `uncovered`(`no_entry`)와 동시 검출될 수 있다 — 중복 보고를 허용하되 `counts`는 코드별로 각각 센다(진단 정보 손실 방지).
- **워커 허용 필드만 수정된 매니페스트는 통과한다**: `WORKER_FIELDS` + 미지 키는 검사 대상이 아니다(F-007 AC 전반부).
- `index.json`은 워커 편집 대상이 아니다 — 워커 권한 경계 문서(F-011)에 "워커는 `index.json`을 수정하지 않는다"를 명문화한다.

#### 3.7.3 환경 변경 / 3.7.4 배치·마이그레이션
해당 없음.

#### 3.7.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-030 | F-7 AC | 기능 테스트 | 워커 허용 필드만 수정된 매니페스트 → 통과(exit 0) |
| TS-031 | F-7 AC | 기능 테스트 | `dir` 조작 매니페스트 → `worker_scope_violation`/`dir_mismatch`, exit 2 |
| TS-032 | F-7 AC | 기능 테스트 | `files` 키 임의 추가/삭제 → `files_key_added`/`files_key_removed` |
| TS-033 | F-7 AC | 기능 테스트 | `layer`·`domain`·`module` 기재 매니페스트 → 각 전용 detail로 거부 |
| TS-034 | F-7 AC / §3.2.2(G)8 | 기능 테스트 | `layer` 침범 매니페스트가 `scan` 결과의 layer 값을 바꾸지 않는다(해석 무시 확인) |

---

### F-008: `feature` 옵셔널 필드 + cross-scope 조회

#### 3.8.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/code-scan/code-scan.js` | 공통 | `cmdFeature` + `commands` 테이블 엔트리 + `USAGE` | 배경분석 (4) |
| 2 | `opal/core/references/header-standard.md` | 문서 | §2 필드 표에 `feature`(선택, string) 행 추가 | (→ D-2 §2) |

#### 3.8.2 API 설계 (PM-1 / R-3 해소)

```
code-scan feature <id> [--scope <name>] [--brief|--full|--json]
```
| 호출 | 동작 |
|------|------|
| `feature <id>` | **전체 스코프 순회** 후 스코프별 그룹핑 반환 (기본) |
| `feature <id> --scope X` | X로 **제한** — 기존 `--scope`의 "탐색 범위 축소" 의미 보존 (`code-scan.js:223-231`) |

- 구현: `config.scopes` 키 목록을 순회하며 스코프별로 `scanHeaders(projectRoot, config, { ...opts, scope: s, domain: null, layer: null })`를 호출하고 `header.feature === id`로 필터한다. `config.scopes`가 비어 있으면 단일 의사 스코프 `(root)`로 처리한다(현행 폴백 `getSearchPaths:236-239`와 정합).
- 매칭은 **문자열 완전 일치**다(배열·부분 일치 미지원 — [MUST] `opal/core/PRINCIPLES.md` §2 Simplicity First).
- 인자 누락 → `Usage: code-scan feature <id>` + exit 1 (`cmdSearch:449` 관례 동일).
- 출력: `cmdDomain`(`:409-418`)의 그룹 출력 관례를 따라 스코프별 헤딩 + 파일 목록. `--json`은 `{ "<scope>": { "<path>": header } }` 2단 구조.
- 동일 파일이 2개 스코프 경로에 동시 포함되면 양쪽에 나타난다(스코프 정의 중복은 소유자 책임 — 문서에 명시).
- 태그 미부여 프로젝트: `feature` 필드는 옵셔널이므로 8커맨드 동작 무변화(F-008 AC 후반부, TS-006으로 커버).

#### 3.8.3 환경 변경 / 3.8.4 배치·마이그레이션
해당 없음.

#### 3.8.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-035 | F-8 AC | 기능 테스트 | 동일 `feature` 태그가 2스코프에 존재할 때 `feature <id>` 1회 호출로 스코프별 그룹 반환 |
| TS-036 | F-8 AC / H-3 | 기능 테스트 | `feature <id> --scope web` → web 그룹만 반환 |
| TS-037 | F-8 AC | 회귀 테스트 | 태그 미부여 픽스처에서 8커맨드 정상 동작(TS-006 공유) |

---

### F-009: PostToolUse hook

#### 3.9.1 파일 변경 계획

**신규 생성**
| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `opal/tools/code-scan/code-map-hook.js` | 공통 | PostToolUse hook 본체 (Node.js, 표준 모듈만) | TASK 제약 ④ / (→ D-11) |

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/core/hooks/claude-hooks.json` | 환경 | `PostToolUse` 배열에 additive 엔트리 1건 | `claude-hooks.json:2-12` |
| 2 | `opal/tools/code-scan/code-scan.js` | 공통 | `decideTarget`·`loadCodeMap`·`loadConfig`·`findProjectRoot`를 `module.exports`로 노출(hook 재사용) | (→ ANALYSIS §4 발견 5) |

#### 3.9.2 설계

**(A) 파일명·언어**
- 파일명은 kebab-case `code-map-hook.js` ([MUST] `docs/CONVENTIONS.md` §네이밍 규칙 파일/폴더). 언어는 Node.js — [MUST] TASK.md §제약: "신규 도구 코드는 code-scan과 동일 언어(Node.js) — 도구 내 언어 이원화 금지".
- `code-scan.js`는 현재 `main()`을 파일 끝에서 무조건 호출한다(`code-scan.js:621`). hook이 `require`할 수 있게 하려면 `if (require.main === module) main();` 가드로 감싼다 — **동작 변화 0**(직접 실행 시 동일, `require` 시 자동 실행만 억제).

**(B) 입력 계약**
```
stdin: { "tool_name": "Edit|Write|MultiEdit", "tool_input": { "file_path": "<abs path>" }, ... }
stdout: {} (무출력) 또는 { "hookSpecificOutput": { "hookEventName": "PostToolUse", "additionalContext": "<경고문>" } }
exit: 항상 0
```
- `tool_input.file_path`를 읽는다 — `todo_mirror_hook.py:25-31`이 `tool_input.command`를 읽는 것과 대응하는 구조이며, 대상 도구가 Bash가 아니라는 점이 선례와의 차이다 (→ ANALYSIS §4 발견 5).
- `MultiEdit`도 단일 `file_path`를 가진다고 가정하고, 배열형 입력(`edits[]`)이 오면 `file_path`만 사용한다. 필드 부재 시 무출력 종료.

**(C) 조기 이탈 순서 (PM-7 / R-6 해소 — 성능·부작용 0)**
| # | 조건 | 처리 |
|---|------|------|
| 1 | stdin JSON 파싱 실패 / 객체 아님 | 무출력 exit 0 |
| 2 | `tool_name ∉ {Edit, Write, MultiEdit}` | 무출력 exit 0 (matcher 이중 방어) |
| 3 | `tool_input.file_path` 부재·비문자열 | 무출력 exit 0 |
| 4 | `file_path` 상위로 `findProjectRoot` 탐색 실패 | 무출력 exit 0 |
| 5 | **`{root}/.opal/code-map/index.json` 부재** | 무출력 exit 0 ← code-map 미사용 프로젝트의 이탈 지점 (fs.existsSync 1회) |
| 6 | 확장자 ∉ `config.extensions` | 무출력 exit 0 |
| 7 | `decideTarget` 결과가 `write_to: 'inline'` | 무출력 exit 0 |
| 8 | `write_to: 'manifest'` + 매니페스트 엔트리 존재 + `draft !== true` + `description` 비공백 | 무출력 exit 0 (**갱신한 시나리오에서 침묵** — F-009 AC) |
| 9 | 그 외 | `additionalContext` 경고 출력 |
- 전체를 `try { ... } catch { }` + `process.exit(0)`으로 감싼다 — `todo_mirror_hook.py:124-130` fail-safe 패턴 준용(PM-7). **hook은 어떤 경우에도 정상 도구 흐름을 차단하지 않는다.**
- 5번 이전 비용은 JSON 파싱 1회 + 문자열 검사 + `existsSync` 몇 회로, code-map 미사용 프로젝트에 실질 오버헤드가 없다.

**(D) 경고문 내용**
- 결정론 지시문 + 대상 정보: 파일 경로 · `reason` · 기록해야 할 매니페스트 경로 · `key` · 허용 필드 목록(`WORKER_FIELDS`) · 갱신 명령 예시(`~/.opal/tools/code-scan/run.sh target <file> --json`). `build_additional_context`(`todo_mirror_hook.py:84-94`)의 "지시문 + 페이로드" 형식을 답습한다.

**(E) `claude-hooks.json` additive 엔트리**
```json
{ "matcher": "Edit|Write|MultiEdit",
  "hooks": [ { "type": "command", "command": "node \"$HOME/.opal/tools/code-scan/code-map-hook.js\"" } ] }
```
- 기존 `"matcher": "Bash"` 엔트리와 **충돌 없는 배열 추가**다(→ ANALYSIS §4 발견 5). 배선은 `install-mac.sh`의 `merge_hooks_config()`(`:1212-1219`)가 `claude-hooks.json` 전체를 병합하므로 **install 스크립트의 hook 관련 수정은 불필요**하다(→ ANALYSIS §1.1).
- **H-9 대응**: matcher 정규식 alternation이 동작하지 않으면 `"Edit"`/`"Write"`/`"MultiEdit"` 3개 엔트리로 분리한다(폴백 확정). (C)2의 이중 방어 덕분에 어느 형태든 동작이 동일하다.

#### 3.9.3 환경 변경
`~/.claude/settings.json` PostToolUse 엔트리 1건 추가(install 시 자동 병합). 신규 패키지 0.

#### 3.9.4 배치/마이그레이션
해당 없음.

#### 3.9.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-038 | F-9 AC | 기능 테스트 | code-map 대상 파일 수정 + 매니페스트 미갱신 이벤트 → 경고 출력, exit 0 |
| TS-039 | F-9 AC | 기능 테스트 | 매니페스트 갱신 완료 상태 이벤트 → stdout 0바이트, exit 0 |
| TS-040 | F-9 AC / H-6 | 기능 테스트 | code-map 부재 트리 이벤트 → stdout 0바이트, exit 0 (5번 이탈) |
| TS-041 | F-9 AC | 기능 테스트 | 깨진 JSON·`tool_name: Bash`·`file_path` 부재 3케이스 전부 무출력 exit 0 |
| TS-042 | H-9 | 통합 테스트 | `claude-hooks.json` 파싱 후 `PostToolUse` 배열이 기존 Bash 엔트리 + 신규 엔트리 2건 |

---

### F-010: `headerSource` 스위치

#### 3.10.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/code-scan/code-scan.js` | 공통 | `DEFAULT_CONFIG.headerSource='auto'` + `loadConfig` 5번째 키 + `USAGE` Config 예시 | `code-scan.js:29-34,150-164,66-73` |
| 2 | `opal/core/references/pm/code-scan-management.md` | 문서 | `headerSource` 관리 규칙 + code-map 존재 시 권장값 | (→ D-4 §추론 소스 3종) |

#### 3.10.2 설계

**(A) 설정 확장**
```js
// loadConfig 반환 (기존 4키 → 5키)
{ extensions, exclude, excludePatterns, scopes, headerSource }
```
- `headerSource: user.headerSource || 'auto'`. 값이 `auto|inline|manifest` 외면 `'auto'`로 폴백하고 stderr에 1줄 경고를 쓴다(stdout 오염 금지 — `--json` 파이핑 보호, `brain_tool.py:786-793`이 stdout을 파싱함).
- 하위호환 근거: 소비자는 `config` 객체를 통째로 전달받고 4키 구조분해를 하지 않으므로 키 추가가 안전하다 (→ ANALYSIS §1.2 설정 로더 단일화).

**(B) 분기 지점 — 유일**
| 값 | `resolveHeader` 동작 |
|----|---------------------|
| `auto` (기본) | 인라인 → 지도 (5단 전량). code-map 부재 시 인라인 단독 = 현행과 동일 |
| `inline` | 인라인만 해석. code-map을 **로드조차 하지 않는다** |
| `manifest` | 인라인을 읽지 않고 지도만 해석 (tier②~⑤) |
- 분기는 `resolveHeader` 진입부 1곳에만 존재한다(§3.2.2 (G)1). `discover`/`scaffold`/`validate`/`target`은 스위치를 참조하지 않는다.

**(C) `target`·`validate` 와의 관계 (설계 결정)**
- `target`은 스위치를 무시한다 — 기록 위치 SSOT는 확정 방향 6이다(§3.5.2).
- `validate`는 스위치를 무시하고 항상 2소스 합산으로 판정한다 — 커버리지 정의가 확정 방향 11("인라인+지도 합산")이기 때문이다. 스위치는 **조회 결과 축소용**이며 검증 기준을 바꾸지 않는다.

#### 3.10.3 환경 변경
`.opal/code-scan.json` 스키마에 `headerSource` 선택 키 추가(기존 파일 미수정 시 `auto`).

#### 3.10.4 배치/마이그레이션
해당 없음(기본값이 현행 동작).

#### 3.10.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-043 | F-10 AC | 회귀 테스트 | code-map 없는 프로젝트에서 8커맨드 출력이 변경 전과 동일(TS-006 공유) |
| TS-044 | F-10 AC | 기능 테스트 | `headerSource: "inline"` → 혼재 픽스처에서 지도 유래 헤더 0건 |
| TS-045 | F-10 AC | 기능 테스트 | `headerSource: "manifest"` → 인라인 보유 파일도 `_source`가 `inline`이 아님 |
| TS-046 | F-10 AC | 기능 테스트 | 잘못된 값(`"bogus"`) → `auto` 폴백 + stderr 경고, stdout JSON 무오염 |

---

### F-011: 규칙 SSOT 갱신 (7문서)

#### 3.11.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/core/references/harness/header-rules.md` | 문서 | §8 "작성 주체: … 별도 도구 없음" **교체** + ① 4단 기록 위치 판정 표 ② 3단 갱신 시점 표 ③ 워커 권한 경계 표 ④ 커버리지 합산 정의 신설 | `header-rules.md:12` / 확정 방향 6·7·9·11 |
| 2 | `opal/core/references/pm/code-scan-management.md` | 문서 | `headerSource` 관리 + `.opal/code-map/` PM 관리 의무(index 소유자 리뷰) 추가 | `code-scan-management.md:14-31` |
| 3 | `opal/core/references/harness/pm-review-gate.md` | 문서 | 8번 항목에 "2소스 판정·합산 커버리지·`validate --changed` 게이트" / 14번 항목에 "신규 서브명령 결과도 인용 대상" 반영 | `pm-review-gate.md:52-56,89-94` |
| 4 | `opal/core/references/tools.md` | 문서 | code-scan 절 실행 경로를 `run.sh` 우선으로 갱신 + 5신규 서브명령·옵션·exit code 표 추가 | `tools.md:202-289` |
| 5 | `opal/tools/tool-scan/manifest.json` | 문서 | code-scan `when` 배열에 `discover`/`scaffold`/`target`/`validate`/`feature`/`header`/`code-map` 추가 | `manifest.json:55` |
| 6 | `opal/tools/brain-tool/README.md` | 문서 | (PM-3) "code-scan @header"가 인라인·code-map 2소스를 뜻하게 된 의미 변화 **1문장** 명시. 단방향 계약 문언 자체는 불변 | (→ D-6) / ANALYSIS §4 발견 4 |
| 7 | `opal/core/references/opal-harness.md` | 문서 | (PM-3) §9 도구 표 code-scan 행에 신규 서브명령 열거(타 도구 행 서식과 동일화) | `opal-harness.md:250` |

- [MUST] `.opal/AGENT.md` §금지사항: "**변경이력 누락 금지** — 스킬·에이전트·참조 문서 수정 시 변경이력 표 행 추가 의무." → 1~4·6·7의 6문서에 변경이력 행 추가(5번 `manifest.json`은 변경이력 표가 없는 JSON이므로 제외).
- [MUST] `docs/CONVENTIONS.md` §구현 규칙 §변경이력 작성 의무: "일시는 `YYYY-MM-DD HH:mm` (KST), 버전은 semver, 변경내용은 태스크 번호를 괄호로 포함 — 예: `(138)`." → 태스크 번호 `(077)` 표기.

#### 3.11.2 문서 내용 설계 (신설 표 4종 — `header-rules.md`)

**표1 — 4단 기록 위치 판정** (§3.5.2 판정 순서 표를 그대로 이식, `reason` 4종 계약 포함)
**표2 — 3단 갱신 시점**
| # | 시점 | 주체 | 수단 |
|---|------|------|------|
| (a) | 파일 변경과 **같은 자리** | 워커 | `target` 판정 후 인라인 또는 매니페스트 즉시 기록 |
| (b) | **CLOSE 진입 전** 게이트 | PM | `validate --changed <changed_files>` — exit≠0이면 차단 |
| (c) | **PostToolUse hook** | 도구 | 미갱신 감지 시 경고 주입 |
- [MUST] 확정 방향 7: "작업 완료 후 일괄 갱신"은 금지 — 문서에 금지 문언으로 명기한다.

**표3 — 워커 권한 경계**
| 구분 | 필드 | 집행 |
|------|------|------|
| 허용 | `description`·`exports`·`depends`·`note`·`feature` | - |
| 금지(도구 관할) | `dir`·`files` 키 목록·`layer`·`domain`·`scope`·`module`·`version` | `validate`가 `worker_scope_violation`으로 거부 |
| 금지(파일 단위) | `index.json` 전체 | 소유자·PM 관할 |

**표4 — 커버리지 합산**: `covered = inline + manifest`(이중 계상 금지), 폴백 3분기(`header-rules.md:83-89`)의 "커버리지 30% 미만" 판정 기준을 **합산 기준**으로 재정의.

#### 3.11.3 환경 변경 / 3.11.4 배치·마이그레이션
해당 없음.

#### 3.11.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-047 | F-11 AC① | 산출물 검사 | 6문서 변경이력 행 추가 확인(+`manifest.json` 제외 근거 기재) |
| TS-048 | F-11 AC② | 산출물 검사 | `header-rules.md`에서 "별도 도구 없음" 문구 잔존 0건 (grep) |
| TS-049 | F-11 AC③ | 산출물 검사 | 4단 선택·3단 시점·워커 권한 경계가 각각 표로 존재 |
| TS-050 | F-11 AC④ | 통합 테스트 | `~/.opal/tools/tool-scan/run.sh usage code-scan`이 신규 4서브명령을 포함해 반환 |
| TS-051 | PM-3 / H-4 | 산출물 검사 | `brain-tool/README.md`에 2소스 의미 변화 1문장 존재 + 단방향 계약 문언 불변 / `opal-harness.md` §9 code-scan 행 정합 |

---

### F-012: 합성 픽스처 + RED 테스트 + dogfooding

#### 3.12.1 파일 변경 계획

**신규 생성**
| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `.opal/code-scan.json` | 환경 | **선결** — 저장소 스코프 3종 정의(픽스처 격리 1차) | ANALYSIS §5 R-1 / (→ D-19) |
| 2 | `opal/tools/code-scan/tests/fixtures/codemap-repo/**` | 공통 | 6조건 자기완결 픽스처 트리 | F-012 AC / PM-6 |
| 3 | `opal/tools/code-scan/tests/fixtures/violations/**` | 공통 | 위반 6종 격리 픽스처 | F-006·F-007 AC |
| 4 | `opal/tools/code-scan/tests/fixtures/golden/**` | 공통 | 8커맨드 회귀 골든 출력 | 제약② / H-7·H-8 |
| 5 | `opal/tools/code-scan/tests/test-resolve-header.js` | 공통 | 5단 상속·경로 사상·역매핑 (F-002) | (→ D-15) |
| 6 | `opal/tools/code-scan/tests/test-discover.js` | 공통 | F-003 | 동상 |
| 7 | `opal/tools/code-scan/tests/test-scaffold.js` | 공통 | F-004 (멱등 포함) | 동상 |
| 8 | `opal/tools/code-scan/tests/test-target.js` | 공통 | F-005 | 동상 |
| 9 | `opal/tools/code-scan/tests/test-validate.js` | 공통 | F-006·F-007 | 동상 |
| 10 | `opal/tools/code-scan/tests/test-feature.js` | 공통 | F-008 | 동상 |
| 11 | `opal/tools/code-scan/tests/test-regression.js` | 공통 | 8커맨드 골든 대조 + `headerSource`(F-010) | 제약② |
| 12 | `opal/tools/code-scan/tests/test-hook.js` | 공통 | F-009 | 동상 |

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `.gitignore` | 환경 | `!.opal/code-map/` + `!.opal/code-map/**` 예외 추가 | `.gitignore:2-4` (brain 예외 선례) |

#### 3.12.2 설계

**(A) 선결 — 이 저장소 `.opal/code-scan.json` (격리 1차)**
```json
{
  "scopes": {
    "framework": "opal/",
    "console-fe": "dashboard/frontend/src/",
    "console-be": "dashboard/backend/"
  },
  "extensions": [".py", ".js", ".ts", ".jsx", ".tsx", ".vue", ".svelte", ".kt", ".kts", ".java", ".swift", ".md"],
  "exclude": ["node_modules", "__pycache__", ".git", "dist", "build", ".venv", "env", ".next", ".nuxt", ".output",
              "fixtures", "backup", ".pytest_cache", "tasks", "specs"],
  "excludePatterns": []
}
```
- `scopes`는 `docs/PROJECT.md` §프로젝트 구성 3요소(Framework `opal/`,`skills/`,`agents/` / Console FE `dashboard/frontend/` / Console BE `dashboard/backend/`)에서 추론한다 (→ D-19, D-4 §추론 소스 3종). `scopes` 값은 문자열 1개이므로(`getSearchPaths:225,231`) Framework는 대표 경로 `opal/`을 쓴다 — `skills/`·`agents/`는 현재 각각 비어 있거나 `opal/` 하위에 정본이 있다(`docs/CONVENTIONS.md` §네이밍 규칙: "범용 에이전트 폴더: `agents/{agent-name}/` — 현재 비어있음").
- `extensions`에 `.md` 포함 — [MUST] `opal/core/references/pm/code-scan-management.md` §추론 소스 3종: "`.md` **기본 포함** — brain·문서 @header 자산화 목적".
- `exclude`에 **`fixtures`** 포함 = R-1 오염 차단의 핵심(디렉토리명 매칭, `walkDir:211`). `tests`는 넣지 않는다 — 신규 테스트 파일 자체가 dogfooding 커버리지에 잡혀야 한다.
- 생성 후 보고 1줄: `code-scan-management.md` §생성 보고 형식 준수.

**(B) 격리 2차 — 자기완결 픽스처 + `cwd` subprocess (PM-6)**
- 각 픽스처 루트에 자체 `.opal/code-scan.json` + `.opal/code-map/`을 둔다. `findProjectRoot()`의 `.opal` 마커 조건(`code-scan.js:141`)에 의해 픽스처 루트가 자기 자신을 프로젝트 루트로 인식한다 (→ ANALYSIS §4 발견 3).
- 테스트는 `spawnSync(process.execPath, [CODE_SCAN_JS, ...args], { cwd: fixtureRoot })` 형태의 CLI 블랙박스로 실행한다 — `skill-registry` 선례(`opal/tools/skill-registry/tests/test-validate.js:1-33`, → D-15)와 동일 방식. 목·몽키패치 0건.
- **이중 격리 성립 논거**: (A)가 저장소→픽스처 방향 오염을, (B)가 픽스처→저장소 방향 설정 누출을 각각 차단한다.

**(C) 6조건 픽스처 트리 (`fixtures/codemap-repo/`)**
```
codemap-repo/
├── .opal/
│   ├── code-scan.json                 # scopes: svc, web, legacy / extensions .java .ts .py / exclude target
│   └── code-map/
│       ├── index.json                 # version 1, status reviewed, 3 scopes, layerRules, domains, exclude
│       ├── svc/order-api/order/service.json     # dir: svc/order-api/src/main/java/com/acme/order/service
│       ├── svc/ship-api/ship/repository.json    # dir: svc/ship-api/src/main/java/com/acme/ship/repository
│       ├── web/admin/pages.json                 # dir: web/admin/pages  (AdminList.tsx만 실질 엔트리)
│       └── legacy/lib.json                      # dir: legacy/lib
├── svc/                               # 앵커 종1 — 빌드 매니페스트 기반
│   ├── order-api/
│   │   ├── pom.xml                    # 앵커 마커
│   │   ├── src/main/java/com/acme/order/service/OrderService.java   # 인라인 없음 → 지도 커버
│   │   ├── src/main/java/com/acme/order/service/PriceCalc.java      # 인라인 없음 → package tier 상속
│   │   └── target/classes/com/acme/order/service/OrderService.java  # 조건⑤ 컴파일 산출물 중복 사본
│   └── ship-api/
│       ├── pom.xml
│       └── src/main/java/com/acme/ship/repository/ShipRepo.java
├── web/                               # 앵커 종2 — 단순 디렉토리(1-depth)
│   └── admin/
│       └── pages/
│           ├── AdminHome.tsx          # 조건⑥ 인라인 @header 보유
│           └── AdminList.tsx          # 조건⑥ 지도 커버 (혼재)
└── legacy/                            # 조건④ readonly 스코프
    └── lib/
        └── legacy_util.py             # 인라인 없음 → 지도 커버
```
| 조건 | 충족 지점 |
|------|----------|
| ① 5단 이상 깊은 패키지 경로 | `svc/order-api/src/main/java/com/acme/order/service/` (7단) |
| ② 언어별 소스 루트 상용구 | `stripPrefix: ["src/main/java/com/acme/", "src/main/java/"]` |
| ③ 앵커 2종 | `svc`(pom.xml 기반) / `web`(1-depth 디렉토리 `admin`) |
| ④ `readonly` 스코프 1종 | `legacy` (`readonly: true`) |
| ⑤ 컴파일 산출물 중복 사본 | `svc/order-api/target/classes/...` — 동일 basename `OrderService.java`, `exclude: ["target"]`로 배제 |
| ⑥ 인라인·지도 혼재 파일 | `web/admin/pages/` 동일 디렉토리에 인라인 파일 + 지도 파일 공존 |
- `index.json` `layerRules` 예: `[{ "match": "**/service/**", "layer": "service" }, { "match": "**/repository/**", "layer": "repository" }, { "match": "**/pages/**", "layer": "page" }, { "match": "**/lib/**", "layer": "util" }]`. `domains` 예: `{ "order": { "paths": ["svc/order-api/**"] }, "ship": { "paths": ["svc/ship-api/**"] }, "admin": { "paths": ["web/**"] }, "legacy": { "paths": ["legacy/**"] } }`.
- H-12 검증용으로 동일 구체성 점수 규칙 2개(`**/service/**`와 `**/xervice/**` 류가 아니라 실제 동률 케이스)를 별도 픽스처 `fixtures/tiebreak/`에 둔다.

**(D) 위반 픽스처 (`fixtures/violations/`)** — 각 케이스를 최소 트리로 격리
`orphan/` · `uncovered/` · `conflict-inline-shadowed/` · `conflict-mirror-collision/` · `draft/` · `exports-missing/` · `worker-scope-dir/` · `worker-scope-layer/` · `worker-scope-files/`

**(E) 골든 회귀 픽스처 (`fixtures/golden/`)** — H-7·H-8
- `fixtures/legacy-repo/`(code-map **없는** 트리, 인라인 헤더만) + 8커맨드 `--json` 출력 골든 파일 8개.
- 골든은 **변경 전 코드로 생성**해 커밋한다(RED 단계 산출물). 이후 변경된 코드로 재실행해 바이트 동일을 주장한다 = 제약② 증거.

**(F) 4-pass 검증 순서 (확정 방향 8)**
```
pass1 discover  → index.json 초안 (--dry-run 대조)
   ↓ (소유자 리뷰: readonly/anchors/stripPrefix 확정 — 픽스처는 리뷰 완료본을 커밋)
pass2 scaffold  → 골격 매니페스트 전량 (LLM 개입 0)
pass3 워커 배치 → description/exports/depends 채움 (픽스처는 채움 완료본을 커밋)
pass4 validate  → 위반 0 + 샘플 대조 (생성자≠평가자)
```

**(G) 자체 dogfooding 정의 (AC "자체 저장소 실행 1회 성공 / 위반 0건이 로그로 증명")**
| # | 실행 | 성공 기준 |
|---|------|----------|
| 1 | `run.sh scan --scope framework --json`, `summary`, `missing --scope framework` 등 8커맨드 | 정상 종료 + 골든 대조(회귀 0) |
| 2 | `run.sh discover --dry-run --json` | 3스코프·layerRules·exclude 포함 초안이 stdout에 생성(**저장소에 `.opal/code-map/`을 만들지 않는다**) |
| 3 | `run.sh validate --changed "<이 태스크 changed_files>" --json` | `violations: []`, exit 0 — CLOSE 게이트 실사용 형태 |
| 4 | `~/.opal/tools/tool-scan/run.sh usage code-scan` | `ok: true` + 신규 서브명령 포함 |
- 저장소 전체 `validate`(full 모드)는 `dashboard/frontend/` 등 미헤더 파일로 인해 `uncovered`가 다수 발생하므로 **완료 기준에 넣지 않는다**. 근거: [MUST] `opal/core/PRINCIPLES.md` §2 Simplicity First: "Solve only the current requirement." — 저장소 전량 자산화는 확정 방향 12에 따라 후속 태스크다. 이 판단을 TEST.md에 로그로 명시한다.

**(H) 테스트 실행 명령 (중앙 러너 없음 — 기존 컨벤션)**
```bash
node --test opal/tools/code-scan/tests/
```
- `header-standard.md` §3 JSON 블록 포맷의 `@header`를 신규 테스트 파일에 실제로 작성한다 — `skill-registry` 테스트는 `// @module` 평문 스타일이어서 code-scan에 discoverable하지 않다(→ ANALYSIS §1.4 관찰). 신규 파일은 `layer: test` + 선택 필드 `task: "077"`, `scenarios: [...]`를 기재한다 ([MUST] `opal/core/references/harness/header-rules.md` §테스트 파일 전용 선택 필드).

#### 3.12.3 환경 변경
- `.opal/code-scan.json` 신규(비추적 — `.gitignore:2` 유지). `.gitignore`에 `.opal/code-map/` 예외 추가.
- **트레이드오프 T-2**: `.opal/code-scan.json`이 비추적이므로 새 클론에서는 부재하다. 테스트는 픽스처 자기완결 방식이라 영향 없고(§(B)), 부재 시 PM이 즉석 자동 생성한다(`code-scan-management.md` §생성 시점). code-map만 추적하는 것은 [MUST] TASK.md §제약: "`.opal/*` gitignore 예외 등록 필요 — code-map은 파생 캐시(`code-scan.json`)와 달리 수작업 자산이므로 추적 대상" 을 따른 결과다.

#### 3.12.4 배치/마이그레이션
해당 없음.

#### 3.12.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-052 | F-12 AC / H-1 | 통합 테스트 | 저장소 루트 `scan --json` 결과에 `fixtures/` 경로 0건 (격리 1차) |
| TS-053 | F-12 AC / H-1 | 통합 테스트 | 픽스처 루트 `cwd` 실행 결과에 저장소 파일 0건 (격리 2차) |
| TS-054 | F-12 AC | 통합 테스트 | 6조건 픽스처에서 discover→scaffold→target→validate 4-pass 전량 기대 결과 |
| TS-055 | F-12 AC / H-18 | 산출물 검사 | `git check-ignore -v .opal/code-map/index.json` 비무시 / `.opal/code-scan.json` 무시 유지 |
| TS-056 | F-12 AC | 통합 테스트 | 자체 저장소 dogfooding 4항목 로그 증명 (§(G)) |
| TS-057 | F-12 AC | 산출물 검사 | 신규 테스트 파일 8종이 `header-standard.md` §3 JSON 블록 `@header`를 보유하고 `scan`에 잡힘 |

---

### F-013: `run.sh` 래퍼 신설

#### 3.13.1 파일 변경 계획

**신규 생성**
| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `opal/tools/code-scan/run.sh` | 환경 | 도구 래퍼 (Node 호출형 — 첫 사례) | [MUST] `opal-harness.md` §9 |

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `scripts/install-mac.sh` | 배치 | code-scan `run.sh` chmod +x 블록 추가 + 파일 헤더 변경이력 1줄 | `install-mac.sh:1103-1108` (state-tool 패턴) |

#### 3.13.2 설계

**(A) 래퍼 형식 — 기존 관례 준수**
```bash
#!/bin/bash
# code-scan 래퍼 — Node.js 호출
# @header: shell script — 적용 대상 아님 (header-rules.md §적용 대상 확장자 참조)
NODE_BIN="${OPAL_NODE_BIN:-node}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v "$NODE_BIN" >/dev/null 2>&1; then
  echo '{"ok":false,"error":"node_missing","detail":"Node.js not found. Install Node 18+."}'
  exit 1
fi

exec "$NODE_BIN" "$SCRIPT_DIR/code-scan.js" "$@"
```
관례 대조 근거:
| 관례 | 출처 | 준수 방식 |
|------|------|----------|
| shebang + 1줄 설명 주석 + `@header` 미적용 주석 | `opal/tools/state-tool/run.sh:1-3`, `opal/tools/tool-scan/run.sh:1-3` | 동일 3줄 |
| `SCRIPT_DIR` 산출식 | `state-tool/run.sh:5` | 동일 |
| 인터프리터 환경변수 오버라이드 | `tool-scan/run.sh:4` (`${OPAL_VENV_PYTHON:-...}`) | `${OPAL_NODE_BIN:-node}` |
| 인터프리터 부재 시 JSON 에러 + exit 1 | `tool-scan/run.sh:7-10` (`error` 키 + `detail`) | 동일 키 구조 |
| `exec` 로 위임 | 전 도구 공통 | 동일 |
- 인터프리터가 venv 경로가 아닌 `command -v node`인 점이 유일한 차이이며, 이는 TASK 제약 ④(도구 언어 = Node.js)의 필연적 결과다.
- **stdout 오염 금지**: 에러 JSON을 stdout에 쓰는 `tool-scan/run.sh:8` 방식을 따른다(`state-tool/run.sh:8`은 stderr) — `tool-scan usage`가 stdout을 읽으므로 tool-scan 관례를 우선한다.
- `code-scan.js`는 `--help`에서 `USAGE`를 출력하고 정상 종료하므로(`code-scan.js:120,596`) `run.sh --help` = exit 0 (F-013 AC①).

**(B) 배포 배선**
```bash
# ── code-scan 실행 권한 (077) ──
local code_scan_run="$opal_home/tools/code-scan/run.sh"
if [[ -f "$code_scan_run" ]]; then
    chmod +x "$code_scan_run"
    success "code-scan run.sh 실행 권한 설정"
fi
```
- 삽입 위치: `install-mac.sh`의 도구 chmod 블록 열거부(`:1096-1174`) 말미(improve-tool 블록 직후). 기존 12종 블록과 동일 서식 — [MUST] `opal/core/PRINCIPLES.md` §3 Surgical Changes: "Match existing style."
- 파일 상단 변경이력 주석(`install-mac.sh:19-40` 서식)에 1줄 추가.
- hook은 `node <path>` 호출이라 실행 권한이 불필요하므로 별도 블록을 만들지 않는다.

**(C) 하위호환**
- `node code-scan.js <cmd>` 직접 호출 경로를 유지한다 — `tools.md:205,213-232`와 brain-tool(`brain_tool.py:786-793`)이 사용 중이다(F-013 AC③). 래퍼는 얇은 `exec`이므로 두 경로의 동작이 동일하다.

#### 3.13.3 환경 변경
`~/.opal/tools/code-scan/run.sh` 배포 + 실행 권한. 신규 패키지 0.

#### 3.13.4 배치/마이그레이션
`./scripts/install-mac.sh` 재실행 1회 필요 — [MUST] `.opal/AGENT.md` §금지사항: "**`~/.opal/` 직접 편집 금지** — 항상 프로젝트 소스를 수정한 후 install로 배포한다."

#### 3.13.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-058 | F-13 AC① | 통합 테스트 | `~/.opal/tools/code-scan/run.sh --help` exit 0 + 사용법 출력 |
| TS-059 | F-13 AC② / H-17 | 통합 테스트 | `tool-scan usage code-scan` → `ok: true` + 신규 서브명령 포함 |
| TS-060 | F-13 AC③ | 회귀 테스트 | `node code-scan.js scan --json` 직접 호출이 계속 동작(골든 동일) |
| TS-061 | F-13 AC① | 기능 테스트 | `OPAL_NODE_BIN=/nonexistent run.sh --help` → `node_missing` JSON + exit 1 |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)

| Phase | 기능 | Step | agent | 실행 | 비고 |
|-------|------|------|-------|------|------|
| 0. 선결·격리 | F-012(선결), F-001 | 1 | opal-task-agent | 단독 | 픽스처 오염 경로 선차단(R-1) — 이후 전 Step의 전제 |
| 1. RED | F-012 | 2, 3, 4 | opal-test-agent | 2·3 병렬 → 4 순차 | 작성자≠구현자 (→ D-25 §2). 골든은 **변경 전 코드**로 캡처해야 하므로 Phase 2 이전 필수 |
| 2. GREEN 도구 | F-001, F-002, F-003, F-004, F-005, F-006, F-007, F-008, F-010 | 5→6→7→8→9→10→11→12 | opal-task-agent | **전량 순차** | 동일 파일 `code-scan.js` 단일 수정 — 파일 충돌 방지가 그룹핑 1순위(→ D-1 §C-1) |
| 3. 배선 | F-013, F-009, F-011(매니페스트) | 13 ∥ 14 | opal-task-agent | 2트랙 병렬 | 서로 다른 파일 집합 |
| 4. 문서 | F-011, F-001, F-008 | 15 ∥ 16 ∥ 17 ∥ 18 | opal-task-agent | 4트랙 병렬 | 문서 7종이 서로 겹치지 않음 |
| 5. 검증 | F-012 | 19 | opal-test-agent | 단독 | GREEN 전량 + 회귀 + 배포 + dogfooding |
| 6. docs/ 갱신 | - | 20 | PM 직접 | 단독 | `docs/` 무효화 체크 (op-dev-plan SKILL.md §docs/ 갱신 Step 자동 생성 규칙) |

### 4.2 실행 체크리스트

> 총 20개 Step | Phase 7개 | 실행 모드: **복잡** (§6)

#### Step 1: 선결 — 저장소 `.opal/code-scan.json` 생성 + `.gitignore` code-map 예외
- [ ] 완료
- **소속 기능**: F-012 (선결), F-001
- **영역**: 환경
- **agent**: opal-task-agent
- **파일**: `.opal/code-scan.json`(신규), `.gitignore`(수정)
- **작업 내용**: §3.12.2 (A)의 JSON을 그대로 생성 (`scopes` 3종은 `docs/PROJECT.md` §프로젝트 구성 추론 / `exclude`에 **`fixtures`** 필수 / `extensions`에 `.md` 포함). `.gitignore`의 `!.opal/brain/**` 다음 줄에 `!.opal/code-map/` + `!.opal/code-map/**` 2줄 추가. 생성 보고 1줄(`code-scan-management.md` §생성 보고 형식).
- **완료 기준**: `node opal/tools/code-scan/code-scan.js scan --json`이 3스코프만 순회하고 결과 경로에 `tasks/`·`fixtures/` 0건. `git check-ignore -v .opal/code-map/index.json`이 비무시, `.opal/code-scan.json`은 무시 유지.
- **테스트**: TS-052, TS-055
- **실행 방법**: direct
- **의존**: 없음

#### Step 2: 픽스처 트리 구축 (6조건 + 위반 + tiebreak + legacy-repo)
- [ ] 완료
- **소속 기능**: F-012
- **영역**: 공통
- **agent**: opal-test-agent
- **파일**: `opal/tools/code-scan/tests/fixtures/codemap-repo/**`, `.../violations/**`, `.../tiebreak/**`, `.../legacy-repo/**`
- **작업 내용**: §3.12.2 (C) 트리를 그대로 생성(6조건 전량) + (D) 위반 9케이스 격리 트리 + H-12 tiebreak 트리 + (E) code-map 없는 legacy-repo. 각 픽스처 루트에 자체 `.opal/code-scan.json`(+ 필요 시 `.opal/code-map/`)을 배치해 자기완결화(PM-6).
- **완료 기준**: 6조건 충족 표(§3.12.2 (C))의 모든 행이 실제 파일 경로로 확인됨. 픽스처 루트 `cwd` 실행 시 저장소 파일 0건.
- **테스트**: TS-053
- **실행 방법**: sub-agent
- **의존**: Step 1

#### Step 3: 8커맨드 골든 출력 캡처 (변경 전 코드)
- [ ] 완료
- **소속 기능**: F-012
- **영역**: 공통
- **agent**: opal-test-agent
- **파일**: `opal/tools/code-scan/tests/fixtures/golden/*.json`
- **작업 내용**: **`code-scan.js`를 아직 수정하지 않은 상태에서** `legacy-repo` 픽스처를 대상으로 8커맨드(`scan`/`domain`/`layer`/`search`/`exports`/`summary`/`depends`/`missing`)의 `--json`(또는 stdout 텍스트) 출력을 골든 파일로 캡처·커밋. TTY 색상 코드가 섞이지 않도록 비TTY 실행으로 캡처한다(`code-scan.js:80` `isTTY` 분기).
- **완료 기준**: 골든 파일 8개 생성 + 재실행 시 바이트 동일(캡처 재현성).
- **테스트**: TS-006 기준선
- **실행 방법**: sub-agent
- **의존**: Step 2 (병렬 가능: Step 2의 `legacy-repo` 생성 직후)

#### Step 4: RED 테스트 8파일 작성 + 실패 증거 기록
- [ ] 완료
- **소속 기능**: F-012
- **영역**: 공통
- **agent**: opal-test-agent
- **파일**: `opal/tools/code-scan/tests/test-resolve-header.js`, `test-discover.js`, `test-scaffold.js`, `test-target.js`, `test-validate.js`, `test-feature.js`, `test-regression.js`, `test-hook.js`
- **작업 내용**: TS-001~TS-061을 8파일로 분할 구현. `node:test` + `node:assert/strict` + `spawnSync` CLI 블랙박스, `cwd: fixtureRoot`(PM-6). 각 파일에 `header-standard.md` §3 JSON `@header`(`layer: test`, `task: "077"`, `scenarios: [...]`) + TC↔TS-ID 매핑 표 주석 + `// [RED 기대]` 인라인 주석 (→ D-15 컨벤션).
- **완료 기준**: `node --test opal/tools/code-scan/tests/` 실행 시 신규 기능 테스트가 **실패(exit≠0)**하고 그 출력이 RED 증거로 기록됨. `test-regression.js`의 골든 대조는 이 시점에 **통과**해야 한다(기준선 유효성 확인).
- **테스트**: 자기 자신 (RED 증거)
- **실행 방법**: sub-agent
- **의존**: Step 2, Step 3

#### Step 5: 스키마 상수 + `headerSource` + code-map 로더 + 경로 사상 + 규칙 매칭
- [ ] 완료
- **소속 기능**: F-001, F-010, F-002(기반부)
- **영역**: 공통
- **agent**: opal-task-agent
- **파일**: `opal/tools/code-scan/code-scan.js`
- **작업 내용**: §3.1.2 (A) 상수 7종 추가. `DEFAULT_CONFIG.headerSource='auto'` + `loadConfig`(`:150-164`) 5번째 키 + 잘못된 값 stderr 폴백(§3.10.2 (A)). `loadCodeMap`·`resolveScope`·`mirrorPathForDir`·`loadManifest`·`matchLayerRule`·`matchDomain` 신설(§3.2.2 (A)(B)(C)(F)). index 스키마 검증(`unsupported_version`/`invalid_index`).
- **완료 기준**: TS-002·TS-003·TS-008·TS-009 통과. 기존 8커맨드 골든 대조 통과(아직 해석기 미교체이므로 무영향).
- **테스트**: TS-002, TS-003, TS-008, TS-009, TS-046
- **실행 방법**: sub-agent
- **의존**: Step 4

#### Step 6: `resolveHeader` 5단 상속 + `scanAll:324` 단일 교체 + 모듈 노출
- [ ] 완료
- **소속 기능**: F-002, F-010
- **영역**: 공통
- **agent**: opal-task-agent
- **파일**: `opal/tools/code-scan/code-scan.js`
- **작업 내용**: §3.2.2 (G) 알고리즘으로 `resolveHeader` 구현(인라인 단독 승리·필드별 최근접·`_source`/`_sources`·code-map 부재 시 `extractHeader` 반환값 그대로). (H)에 따라 `scanAll`(`:318-333`)에 `ctx` 준비 1줄 + `:324` 1줄 교체. `main()` 호출을 `if (require.main === module)` 가드로 감싸고(`:621`) `module.exports`로 `decideTarget`(Step 7 이후)·`loadCodeMap`·`loadConfig`·`findProjectRoot`를 노출.
- **완료 기준**: TS-004·TS-005·TS-007·TS-044·TS-045 통과 + **TS-006 골든 바이트 동일**(제약②). `discoverFiles`/`walkDir`/`getSearchPaths`/`fmt*`/8커맨드 함수 diff 0줄.
- **테스트**: TS-004, TS-005, TS-006, TS-007, TS-043, TS-044, TS-045
- **실행 방법**: sub-agent
- **의존**: Step 5

#### Step 7: `target` 4단 판정
- [ ] 완료
- **소속 기능**: F-005
- **영역**: 공통
- **agent**: opal-task-agent
- **파일**: `opal/tools/code-scan/code-scan.js`
- **작업 내용**: §3.5.2 판정 순서대로 `decideTarget` 순수 함수 + `cmdTarget` 구현. `reason` 4종 계약 외 값 반환 금지. `write_to: manifest` 시 `scope`/`manifest`/`key` 동반. `commands` 테이블(`:602-611`)·`USAGE`(`:36-74`) 추가.
- **완료 기준**: TS-020~TS-023 통과. `decideTarget`이 `module.exports`로 노출됨(hook 재사용).
- **테스트**: TS-020, TS-021, TS-022, TS-023
- **실행 방법**: sub-agent
- **의존**: Step 6

#### Step 8: `discover` 서브명령
- [ ] 완료
- **소속 기능**: F-003
- **영역**: 공통
- **agent**: opal-task-agent
- **파일**: `opal/tools/code-scan/code-scan.js`
- **작업 내용**: §3.3.2 추론 규칙표대로 `cmdDiscover` + `inferScopes`/`inferAnchors`(2종 탐지)/`inferStripPrefix`/`inferLayerRules`/`inferExclude` 구현. `--out`·`--dry-run` 플래그를 `parseArgs`(`:95-130`)에 추가. 초안 표시 4필드(`origin`/`status`/`generatedAt`/`note`). 기존 index 존재 시 `index_exists` exit 1.
- **완료 기준**: TS-011~TS-014 통과. `domains`·`readonly`를 추론하지 않음(빈 객체/`false`).
- **테스트**: TS-011, TS-012, TS-013, TS-014
- **실행 방법**: sub-agent
- **의존**: Step 7

#### Step 9: `scaffold` + 멱등 보존 merge
- [ ] 완료
- **소속 기능**: F-004
- **영역**: 공통
- **agent**: opal-task-agent
- **파일**: `opal/tools/code-scan/code-scan.js`
- **작업 내용**: §3.4.2 (A)~(E)대로 `cmdScaffold`·`mergeManifest`·`writeIfChanged` 구현. 2-pass 구조(전체 사상 계산 → 충돌 검사 → 쓰기). 결정론적 키 순서·2-space·후행 개행. `pruned`/`stale`/`added`/`skipped` 보고. **`--inline` 미구현**(PM-5).
- **완료 기준**: TS-015~TS-019 통과 + 2회 연속 실행 산출물 바이트 동일 + 소스 파일 무접촉.
- **테스트**: TS-015, TS-016, TS-017, TS-018, TS-019, TS-010
- **실행 방법**: sub-agent
- **의존**: Step 8

#### Step 10: `validate` 5종 위반 + 합산 커버리지 + `--changed`
- [ ] 완료
- **소속 기능**: F-006
- **영역**: 공통
- **agent**: opal-task-agent
- **파일**: `opal/tools/code-scan/code-scan.js`
- **작업 내용**: §3.6.2 (A)~(F)대로 `cmdValidate` + 검출기 5종 + `computeCoverage`. `--changed <csv|->` 파싱(`--exclude` 관례 재사용, stdin 지원). exit code 0/1/2 계약. `exports` 대조는 문법 파싱 없이 텍스트 포함 여부만(PM-4).
- **완료 기준**: TS-024~TS-029 통과. `draft` 포함 시 exit 2.
- **테스트**: TS-024, TS-025, TS-026, TS-027, TS-028, TS-029
- **실행 방법**: sub-agent
- **의존**: Step 9

#### Step 11: 워커 권한 경계 집행
- [ ] 완료
- **소속 기능**: F-007
- **영역**: 공통
- **agent**: opal-task-agent
- **파일**: `opal/tools/code-scan/code-scan.js`
- **작업 내용**: §3.7.2 재계산·대조 표 7행대로 `checkWorkerScope` 구현 후 `validate` 위반 목록에 편입. 전용 코드 `worker_scope_violation` + `sub` detail 7종.
- **완료 기준**: TS-030~TS-034 통과. 허용 필드만 수정된 매니페스트는 exit 0.
- **테스트**: TS-030, TS-031, TS-032, TS-033, TS-034
- **실행 방법**: sub-agent
- **의존**: Step 10

#### Step 12: `feature` 조회 + `USAGE`·`commands` 최종 정리
- [ ] 완료
- **소속 기능**: F-008
- **영역**: 공통
- **agent**: opal-task-agent
- **파일**: `opal/tools/code-scan/code-scan.js`
- **작업 내용**: §3.8.2대로 `cmdFeature` 구현(기본 전체 스코프 순회·그룹핑 / `--scope` 시 제한 — PM-1). `USAGE` Commands·Options·Config 블록에 5신규 서브명령·신규 플래그·`headerSource`·exit code 반영. `commands` 디스패치 테이블 13엔트리 확정. `VERSION`을 `1.3.0`으로 올리고 파일 말미 변경이력 주석(`:623-626`)에 1줄 추가.
- **완료 기준**: TS-035~TS-037 통과. `--help` 출력에 신규 서브명령 5종 전량 노출(F-013 AC② 선결).
- **테스트**: TS-035, TS-036, TS-037
- **실행 방법**: sub-agent
- **의존**: Step 11

#### Step 13: `run.sh` 래퍼 + install chmod 블록 + tool-scan 매니페스트
- [x] 완료
- **소속 기능**: F-013, F-011(#5)
- **영역**: 환경
- **agent**: opal-task-agent
- **파일**: `opal/tools/code-scan/run.sh`(신규), `scripts/install-mac.sh`(수정), `opal/tools/tool-scan/manifest.json`(수정)
- **작업 내용**: §3.13.2 (A) 래퍼 그대로 생성(+로컬 `chmod +x`). (B) install chmod 블록을 improve-tool 블록 직후(`install-mac.sh:1174` 뒤)에 추가 + 파일 헤더 변경이력 1줄. `manifest.json:55` `when` 배열에 `discover`/`scaffold`/`target`/`validate`/`feature`/`header`/`code-map` 추가.
- **완료 기준**: TS-058·TS-059·TS-060·TS-061 통과(TS-059는 install 후 — Step 19에서 최종 확인).
- **테스트**: TS-058, TS-060, TS-061
- **실행 방법**: sub-agent
- **의존**: Step 12

#### Step 14: PostToolUse hook + `claude-hooks.json` 배선
- [x] 완료
- **소속 기능**: F-009
- **영역**: 공통
- **agent**: opal-task-agent
- **파일**: `opal/tools/code-scan/code-map-hook.js`(신규), `opal/core/hooks/claude-hooks.json`(수정)
- **작업 내용**: §3.9.2 (B)(C)(D)대로 hook 구현 — 조기 이탈 9단, 전 경로 `try/catch` + exit 0 fail-safe(PM-7). `code-scan.js`의 `decideTarget`을 `require`로 재사용. (E) additive 엔트리 1건 추가(기존 Bash 엔트리 불변). 파일 상단에 `header-standard.md` §3 JSON `@header` 작성.
- **완료 기준**: TS-038~TS-042 통과. code-map 부재 트리에서 stdout 0바이트.
- **테스트**: TS-038, TS-039, TS-040, TS-041, TS-042
- **실행 방법**: sub-agent
- **의존**: Step 12, Step 13 (경고문 내 `run.sh` 경로 확정)

#### Step 15: `header-standard.md` 2소스 표현 절 + `feature` 필드
- [ ] 완료
- **소속 기능**: F-001, F-008, F-011
- **영역**: 문서
- **agent**: opal-task-agent
- **파일**: `opal/core/references/header-standard.md`
- **작업 내용**: §7 "2소스 표현 — 인라인과 code-map" 절 신설 — §3.1.2 (B)(C)(D) 3표(index.json 필드 / 매니페스트 필드 / `_source` 5종)를 이식하고 미러 경로 사상 예시(§3.2.2 (C))를 포함. §2 필드 표에 `feature`(선택, string) 행 추가. 변경이력 v1.3 행 추가.
- **완료 기준**: TS-001 통과. 필수/선택/타입/기본값 4컬럼이 두 파일 형식 모두에 존재.
- **테스트**: TS-001
- **실행 방법**: sub-agent
- **의존**: Step 12

#### Step 16: `header-rules.md` — 작성층 신설 반영 (4표)
- [ ] 완료
- **소속 기능**: F-011
- **영역**: 문서
- **agent**: opal-task-agent
- **파일**: `opal/core/references/harness/header-rules.md`
- **작업 내용**: `:12` "작성 주체: 워커(LLM)가 직접 작성. 별도 도구 없음." **교체**(도구 보조 + 워커 기입). §3.11.2 표1~표4(4단 판정 / 3단 시점 + "일괄 갱신 금지" 문언 / 워커 권한 경계 / 커버리지 합산) 신설. 폴백 3분기(`:83-89`)의 커버리지 기준을 합산 기준으로 재정의. 변경이력 v1.3 행 추가.
- **완료 기준**: TS-048·TS-049 통과("별도 도구 없음" grep 0건).
- **테스트**: TS-048, TS-049
- **실행 방법**: sub-agent
- **의존**: Step 12

#### Step 17: `code-scan-management.md` + `pm-review-gate.md`
- [ ] 완료
- **소속 기능**: F-010, F-011
- **영역**: 문서
- **agent**: opal-task-agent
- **파일**: `opal/core/references/pm/code-scan-management.md`, `opal/core/references/harness/pm-review-gate.md`
- **작업 내용**: (1) `code-scan-management.md`에 `headerSource` 관리 규칙 + `.opal/code-map/index.json` PM·소유자 관리 의무(discover 초안 → 리뷰 → `status: reviewed`) 추가. (2) `pm-review-gate.md` 8번(`:52-56`)에 2소스 판정·합산 커버리지·`validate --changed` CLOSE 게이트 절차 / 14번(`:89-94`)에 신규 서브명령 결과도 인용 대상임을 반영. 양쪽 변경이력 행 추가.
- **완료 기준**: TS-047 통과(변경이력 2행). PM Gate 8번이 readonly 파일 검증 절차를 포함.
- **테스트**: TS-047
- **실행 방법**: sub-agent
- **의존**: Step 12

#### Step 18: `tools.md` + `opal-harness.md` §9 + `brain-tool/README.md`
- [ ] 완료
- **소속 기능**: F-011, F-013
- **영역**: 문서
- **agent**: opal-task-agent
- **파일**: `opal/core/references/tools.md`, `opal/core/references/opal-harness.md`, `opal/tools/brain-tool/README.md`
- **작업 내용**: (1) `tools.md:202-289` code-scan 절 — 실행 경로를 `~/.opal/tools/code-scan/run.sh`(권장) + `node code-scan.js`(하위호환) 병기로 갱신, 5신규 서브명령·신규 옵션·exit code 표 추가. (2) `opal-harness.md:250` §9 도구 표 code-scan 행에 서브명령 열거(타 행 서식 동일화 — PM-3). (3) `brain-tool/README.md`에 "code-scan @header가 인라인·code-map 2소스를 뜻한다" **1문장** 추가 — [MUST] `opal/tools/brain-tool/README.md`: "**단방향 동기화**: `sync-header`는 code-scan @header → brain entity frontmatter 방향만 (역방향 금지)" 문언 자체는 **불변 유지**. 3문서 변경이력 행 추가.
- **완료 기준**: TS-051 통과. 단방향 계약 문언 diff 0.
- **테스트**: TS-051
- **실행 방법**: sub-agent
- **의존**: Step 12

#### Step 19: GREEN 전량 검증 + 회귀 + 재배포 + dogfooding
- [ ] 완료
- **소속 기능**: F-012
- **영역**: 공통
- **agent**: opal-test-agent
- **파일**: (검증 전용 — 소스 무수정), `tasks/077-.../TEST.md`
- **작업 내용**: (1) `node --test opal/tools/code-scan/tests/` 전량 GREEN. (2) 8커맨드 골든 바이트 동일 대조(제약②). (3) `./scripts/install-mac.sh` 재실행 후 `~/.opal/tools/code-scan/run.sh --help` exit 0 + `tool-scan usage code-scan` `ok: true`. (4) §3.12.2 (G) dogfooding 4항목 실행·로그 기록. (5) RED 테스트 파일 무수정 확인 — [MUST] `opal/core/references/harness/red-first.md` §3: "GREEN/fix 루핑 중 RED 테스트 파일 수정 금지. 위반 시 블로커."
- **완료 기준**: 전 테스트 exit 0 + 골든 회귀 0 + dogfooding 4항목 로그 + RED 파일 diff 0.
- **테스트**: TS-001~TS-061 전량, TS-050, TS-056, TS-059
- **실행 방법**: sub-agent
- **의존**: Step 13, 14, 15, 16, 17, 18

#### Step 20: docs/ 갱신 판정 및 반영
- [ ] 완료
- **소속 기능**: (전 기능 파생)
- **영역**: 문서
- **agent**: PM 직접
- **파일**: `docs/CONVENTIONS.md`, `docs/ARCHITECTURE.md`(판정 후), `docs/PROJECT.md`(변경이력)
- **작업 내용**: `docs/CONVENTIONS.md` §구현 규칙 §@header 규칙에 "기록 위치는 `code-scan target` 판정을 따른다(인라인 또는 `.opal/code-map/`)" 1~2줄 추가 — 신규 패턴 도입에 해당(op-dev-plan SKILL.md §갱신 대상 판단 기준: "새 패턴/규칙 도입 → CONVENTIONS.md"). `docs/ARCHITECTURE.md`에 도구 계층 서술이 있으면 code-scan 작성층 신설을 반영, 없으면 "해당 없음"으로 판정 근거 기록. `docs/PROJECT.md` 변경이력 1행.
- **완료 기준**: CONVENTIONS.md @header 규칙 절이 2소스를 반영. ARCHITECTURE.md 판정 결과가 명시적으로 기록됨.
- **테스트**: 산출물 검사 (PM Gate 11번 docs/ 무효화 체크)
- **실행 방법**: direct
- **의존**: Step 19

### 4.3 병렬/순차 판별 근거

| 관계 | 근거 |
|------|------|
| Step 1 → Step 2 | 픽스처 배치 전에 `exclude: ["fixtures"]`가 먼저 있어야 저장소 스캔 오염이 발생하지 않는다 (R-1 / H-1) |
| Step 2 ∥ Step 3 | Step 3은 Step 2의 `legacy-repo` 서브트리만 필요 — 부분 병렬(동일 에이전트 내 순차 처리 권장) |
| Step 3 → Step 5 | 골든은 **변경 전 코드**로 캡처해야 회귀 기준선이 유효하다 (H-7·H-8) |
| Step 4 → Step 5 | RED 증거 없이 GREEN 진입 금지 — [MUST] `opal/core/references/harness/red-first.md` §1: "RED 단계에서 실패 테스트 코드를 작성·실행하여 실패(exit code≠0)를 증거로 기록한 뒤 GREEN(구현) 진입. RED 증거 없이 GREEN 진입 금지." |
| Step 5→6→7→8→9→10→11→12 (전량 순차) | 8 Step 전부가 **동일 파일** `opal/tools/code-scan/code-scan.js`를 수정한다. 파일 충돌 방지가 그룹핑 1순위이므로 동일 에이전트·순차 배치 (→ D-1 plan-guide §C-1 그룹핑 우선순위 1) |
| Step 6 ← Step 5 | `resolveHeader`가 Step 5의 로더·사상·매칭 함수를 호출한다 (하위 레이어 먼저) |
| Step 10 ← Step 9 | `validate`의 `orphan`/`draft` 판정이 scaffold가 만든 매니페스트 구조를 전제한다 |
| Step 11 ← Step 10 | 권한 경계 검출은 `validate` 위반 목록에 편입되는 확장이다 |
| Step 13 ∥ Step 14 | 파일 집합이 서로 배타적 (`run.sh`·`install-mac.sh`·`manifest.json` ↔ `code-map-hook.js`·`claude-hooks.json`) |
| Step 14 ← Step 7, 13 | hook이 `decideTarget`을 `require`하고 경고문에 `run.sh` 경로를 인용한다 |
| Step 15 ∥ 16 ∥ 17 ∥ 18 | 문서 7종이 겹치지 않고, 전부 Step 12(도구 인터페이스 확정) 이후이므로 4트랙 병렬 가능 |
| Step 19 ← Step 13~18 전량 | 배포·문서 완료 후에만 `tool-scan usage`(TS-059)·문서 산출물 검사(TS-047~TS-051)를 판정할 수 있다 |
| Step 20 ← Step 19 | docs/ 무효화 판정은 최종 changed_files 확정 후 수행한다 (PM Gate 11번) |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA

| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | 2소스 스키마 문서화 + 스키마 위반 거부 | TS-001, TS-002, TS-003 | `header-standard.md`에 두 파일 형식 필드표(필수/선택/타입/기본값) 존재 + 위반 입력 시 에러 코드 exit 1 |
| F-002 | 5단 상속·`_source` 5종·단일 파일 역매핑 | TS-004, TS-005, TS-007, TS-008, TS-009, TS-010 | 5단 단독 5케이스 + 혼재 케이스 기대치 일치, `_source` 값 도메인 5종 이탈 0, `scan <file>`에서 매니페스트 헤더 반환 |
| F-003 | `discover` 초안 생성 + 초안 표시 | TS-011, TS-012, TS-013, TS-014 | scopes ≥2 · layerRules ≥1 · exclude에 컴파일 산출물 포함 + `status: "draft"` 표기 |
| F-004 | `scaffold` 전량 생성 + 멱등 보존 | TS-015~TS-019 | 디렉토리 수 = 매니페스트 수, `dir`·`files` 일치, 재실행 시 사람 작성 값 보존 + 바이트 동일 |
| F-005 | `target` 4단 판정 + `reason` 4종 | TS-020, TS-021, TS-022, TS-023 | 4조건에서 각 `reason`·`write_to` 정확, manifest 시 `manifest`/`key` 동반 |
| F-006 | `validate` 5종 + 합산 커버리지 + `--changed` | TS-024~TS-029 | 5종 유형별 검출 + non-zero exit + 합산 % + `--changed` 한정 판정 |
| F-007 | 워커 권한 경계 거부 | TS-030~TS-034 | 허용 필드만 수정 → 통과 / 도구 관할 필드 침범 → `worker_scope_violation` |
| F-008 | `feature` cross-scope 조회 | TS-035, TS-036, TS-037 | 2스코프 태그를 1회 호출로 스코프별 그룹 반환 + `--scope` 제한 동작 + 미부여 프로젝트 무영향 |
| F-009 | hook 감지·침묵·비파괴 | TS-038~TS-042 | 미갱신 시 경고 / 갱신 시 침묵 / 부재·오류 전 경로 무출력 exit 0 |
| F-010 | `headerSource` 3값 분기 + 회귀 0 | TS-006, TS-043, TS-044, TS-045, TS-046 | code-map 부재 시 출력 바이트 동일 + `inline`/`manifest` 명시 시 해당 소스만 해석 |
| F-011 | 규칙 SSOT 7문서 갱신 | TS-047, TS-048, TS-049, TS-050, TS-051 | 6문서 변경이력 행 + "별도 도구 없음" 0건 + 3표 존재 + `tool-scan usage` 신규 서브명령 반환 + brain README·harness §9 정합 |
| F-012 | 픽스처 6조건 + 이중 격리 + dogfooding | TS-052~TS-057 | 6조건 전량 재현 + 4-pass 기대 결과 + 격리 양방향 + dogfooding 4항목 로그 |
| F-013 | `run.sh` 신설 + 배포 + 하위호환 | TS-058, TS-059, TS-060, TS-061 | `run.sh --help` exit 0 + `tool-scan usage code-scan` `ok: true` + 직접 호출 경로 유지 |

### 5.2 회귀 테스트

- [ ] code-map 부재 픽스처에서 8커맨드(`scan`/`domain`/`layer`/`search`/`exports`/`summary`/`depends`/`missing`) `--json` 출력이 골든과 **바이트 동일** (TS-006 — 제약②)
- [ ] `header` 객체에 `_source`/`_sources` 키가 code-map 부재 시 **출현하지 않음**
- [ ] `discoverFiles`/`walkDir`/`getSearchPaths`/`fmtBrief`/`fmtFull`/`fmtJson`/8 `cmdXxx` 함수 **diff 0줄** (§3.2.2 (H) 논거의 실증)
- [ ] `node opal/tools/code-scan/code-scan.js scan --json` 직접 호출 경로 정상 (brain-tool 소비 경로 — `brain_tool.py:786-793`)
- [ ] `~/.opal/tools/brain-tool/run.sh sync-header` 실행이 `_source` 추가 키로 실패하지 않음 (간접 영향 — `brain_tool.py:839` 4필드 비교)
- [ ] 기존 `claude-hooks.json` Bash 엔트리(`todo_mirror_hook.py`) 정상 동작 유지 — 076 todo 미러 회귀 0
- [ ] `scaffold` 실행 후 소스 파일 내용·mtime 변화 0건 (PM-5)
- [ ] `install-mac.sh` 재실행이 기존 12종 도구 chmod·hook 병합을 깨지 않음

### 5.3 코드/문서 품질

- [ ] 신규 Node 파일 2종(`code-map-hook.js`)·`run.sh`가 kebab-case ([MUST] `docs/CONVENTIONS.md` §네이밍 규칙 파일/폴더)
- [ ] 테스트 파일명이 `test-<verb>.js` 규칙 준수 (→ D-15)
- [ ] 신규 코드 파일 전량에 `header-standard.md` §3 JSON `@header` 작성 + 테스트 파일은 `layer: test`·`task`·`scenarios` 선택 필드 포함
- [ ] `code-scan.js` `VERSION` 상수 갱신 + 파일 말미 변경이력 주석 1줄 추가 (`:623-626` 서식)
- [ ] 문서 6종 `## 변경이력` 표 행 추가 — 일시 `YYYY-MM-DD HH:mm` KST · semver · `(077)` 표기 ([MUST] `docs/CONVENTIONS.md` §구현 규칙 §변경이력 작성 의무)
- [ ] 외부 패키지 추가 0건 — `require`가 `fs`/`path`/`node:test`/`node:assert`/`child_process` 등 표준 모듈만 (TASK 기술 스택 "무의존")
- [ ] 도구 내 언어 이원화 0건 — 신규 실행 코드는 전부 Node.js (TASK 제약 ④)
- [ ] `~/.opal/` 직접 편집 0건 — 프로젝트 소스 수정 후 install 배포 ([MUST] `.opal/AGENT.md` §금지사항)
- [ ] 사변적 추가 0건 — 미채택 기능(`scaffold --inline`·역주입 마이그레이션·해시/mtime stale 감지·파일별 사이드카·`feature` 태그 실채우기) 코드 0줄 ([MUST] `opal/core/PRINCIPLES.md` §2·§3)
- [ ] 인접 코드 개선 0건 — `cmdSummary`/`cmdDepends`의 기존 바이패스 포맷을 손대지 않음

### 5.4 보안

- [ ] `.env`·인증 파일·토큰이 신규 파일·픽스처에 0건 (픽스처는 합성 코드만)
- [ ] `.gitignore`가 `.opal/code-scan.json`(파생 캐시)을 계속 무시하고 `.opal/code-map/`만 예외 등록 — 의도치 않은 로컬 설정 커밋 방지
- [ ] hook이 stdin 임의 JSON을 신뢰하지 않음 — 타입 검사 후 사용, 셸 실행·`eval`·문자열 보간 명령 구성 0건 (`todo_mirror_hook.py` 패턴)
- [ ] hook·`validate`가 `file_path`를 파일시스템 읽기에만 사용하고 쓰기 대상으로 삼지 않음 (경로 traversal로 인한 임의 쓰기 불가)
- [ ] `run.sh`가 사용자 입력을 `eval` 없이 `"$@"`로 그대로 전달 (인자 주입 차단)
- [ ] `exports` 텍스트 대조가 정규식이 아닌 **부분 문자열** 비교 — 사용자 제공 문자열로 인한 ReDoS 불가
- [ ] `discover`/`scaffold`가 `.opal/code-map/` 외부에 쓰기 0건
- [ ] 커밋은 사용자 명시 요청 시에만 ([MUST] `docs/CONVENTIONS.md` §구현 규칙 §Guards)

---

## 6. 복잡도 판별

| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 20개 | 복잡 (6개 이상) |
| 변경 파일 수 | 신규 14+ / 수정 11 = 25+개 | 복잡 (4개 이상) |
| 모듈 범위 | 다중 — 도구(code-scan) · hook · 설치 스크립트 · 규칙 문서 7종 · 설정 2종 | 복잡 |
| 작업 유형 | 신규 개발 (작성층 신설 + 해석기 확장) | 복잡 |
| 외부 의존성 | 신규 패키지 0 / 신규 도구 래퍼·hook 배선 필요 | 복잡 (새 도구 배선) |
| **실행 모드** | **복잡** | §7 실행 아키텍처 포함 |

### 6.1 RED-first 트랙 적용 판정

> 규칙 SSOT: `opal/core/references/harness/red-first.md` (Read 완료 — → D-25)

**판정: RED-first 강제 적용**

| 근거 | 인용 |
|------|------|
| 변경 영역이 "API 계약"에 해당 — code-scan CLI 서브명령 5종 신설 + `_source`/exit code/`reason` 계약 신설 | [MUST] `opal/core/references/harness/red-first.md` §1.5: "**RED-first 강제** (self-confirming 위험 높음): … API 계약" |
| 변경 영역이 "버그 수정(회귀 방지)"에 해당 — 8커맨드 하위호환(제약②)을 테스트로 처음 고정 | 동상: "버그 수정(회귀 방지)" |
| 변경 영역이 "비즈니스 로직"에 해당 — 5단 상속 우선순위·4단 판정 순서·구체성 tie-break는 순수 판정 로직 | 동상: "비즈니스 로직" |
| 제외 조건 미해당 | 동상 "구현 후 시나리오 검증 허용": 탐색적 프로토타입·UI 화면·행위 불변 리팩터·설정·문서 — 이 태스크의 코드 변경은 어디에도 속하지 않는다(문서 Step 15~18만 산출물 검사 대상) |

**운용 규칙 적용**

| 규칙 | 적용 |
|------|------|
| §1 RED→GREEN 순서 | Step 4(RED, 실패 증거) → Step 5~12(GREEN). Step 4 완료 없이 Step 5 진입 금지 (§4.3) |
| §2 작성자≠구현자 | RED 작성 = `opal-test-agent`(Step 2·3·4·19), 구현 = `opal-task-agent`(Step 5~18) |
| §3 테스트 불변성 | Step 5~18 중 `opal/tools/code-scan/tests/**` 수정 금지. 위반 시 블로커 — Step 19에서 diff 0 확인 |
| §4 공개 인터페이스 검증 | CLI 블랙박스(`spawnSync` + exit code + stdout JSON) 우선. 순수 함수 직접 호출은 `mirrorPathForDir`·`matchLayerRule`·`decideTarget`·`mergeManifest`처럼 `module.exports`로 **공개된** 함수에 한정 |
| §5 graceful skip | 해당 없음 — Node 내장 `node:test` 인프라가 존재하고 선례(→ D-15)가 있다 |
| §6 STATE 행 정책 | RED는 EXECUTE 내부 서브스텝으로 흡수. 별도 STATE 행 추가 없음 (opd 15행 SSOT 보존) |

**문서 전용 Step 예외**: Step 15~18(문서 7종)·Step 20(docs/)은 코드 산출물이 없어 RED 대상이 아니며 산출물 검사(TS-001·TS-047~TS-051)로 검증한다 — red-first.md §1.5 "설정·문서" 분류.

---

## 7. 실행 아키텍처 (복잡 모드)

### C-1. 에이전트 토폴로지

```
Batch 1  ┌─ A1: opal-task-agent   (Step 1)                         선결·격리
         └─ (단독 — 후속 전부의 전제)
              │
Batch 2  ┌─ A2: opal-test-agent   (Step 2 → 3 → 4)                 RED 트랙
         └─ (단독 — 작성자≠구현자 경계)
              │
Batch 3  ┌─ A3: opal-task-agent   (Step 5→6→7→8→9→10→11→12)        GREEN 도구 (동일 파일 순차)
         └─ (단독 — code-scan.js 파일 충돌 방지)
              │
Batch 4  ┌─ A4: opal-task-agent   (Step 13)   run.sh·install·manifest
         ├─ A5: opal-task-agent   (Step 14)   hook·claude-hooks.json     [A4 완료 후 시작]
         └─ (A4 → A5 순서 의존, A5는 A4와 동일 배치 내 후행)
              │
Batch 5  ┌─ A6: opal-task-agent   (Step 15)   header-standard.md
         ├─ A7: opal-task-agent   (Step 16)   header-rules.md
         ├─ A8: opal-task-agent   (Step 17)   code-scan-management·pm-review-gate
         └─ A9: opal-task-agent   (Step 18)   tools·opal-harness·brain README    ← 4트랙 병렬
              │
Batch 6  ┌─ A10: opal-test-agent  (Step 19)   GREEN·회귀·재배포·dogfooding
              │
Batch 7  └─ PM 직접              (Step 20)   docs/ 갱신
```

**그룹핑 근거 (plan-guide §C-1 우선순위)**
1. **파일 충돌 방지**: Step 5~12는 `code-scan.js` 단일 파일이므로 반드시 동일 에이전트(A3)에 배치.
2. **모듈 응집도**: 배선(A4·A5)과 문서(A6~A9)를 각각 분리.
3. **병렬 극대화**: Batch 5의 문서 4트랙이 유일한 진짜 병렬 구간(파일 배타적).
4. **검증 격리**: RED 작성(A2)과 최종 검증(A10)을 구현 에이전트(A3~A9)와 분리 — 생성자≠평가자 (→ D-25 §2).

### C-2. 스킬 요구사항

| 필요 역량 | 기존 스킬 매칭 | 갭 판정 |
|----------|--------------|--------|
| 단계 스킬(PLAN/EXECUTE/TEST) | `op-dev-plan`(현 단계), `op-dev-execute`, `opal-test-agent` mode:red/be | 갭 없음 |
| Node.js CLI 도구 확장 | 없음(프레임워크 내부 작업) | 인라인 지침으로 충분 — 3개 이상 Step에서 반복되는 신규 패턴은 "동일 파일 순차 수정" 뿐이며 이는 plan-guide가 이미 규정 |
| 외부 프레임워크 스킬(React/Python/shadcn 등) | 해당 없음 | ANALYSIS §6.2 "추천 스킬: 해당 없음" 승계 |

### C-3. 도구 요구사항

| 항목 | 필요 여부 | 비고 |
|------|----------|------|
| Node.js 18+ | 필수 | `node:test`·`node --test` 사용 (→ D-15). `install-mac.sh:1181-1184`가 이미 Node 환경 체크를 수행 |
| 신규 npm 패키지 | 0 | `code-scan.js:19-20` 무의존 유지 (TASK 기술 스택) |
| `~/.opal/tools/state-tool/run.sh` | 필수 | STATE 행 갱신 — [MUST] `docs/CONVENTIONS.md` §구현 규칙 §State 관리: "파이프라인 STATE.md 행 상태(⬜/🔄/✅) 변경은 `~/.opal/tools/state-tool/run.sh`로만 수행한다. 마크다운 표 직접 편집 금지." |
| `~/.opal/tools/tool-scan/run.sh` | 필수 | TS-050·TS-059 검증 |
| `./scripts/install-mac.sh` | 필수 | Step 19 재배포 (L3 검증) |
| MCP | 불필요 | 외부 라이브러리 조사 없음 (ANALYSIS §6.3) |

### C-4. 테스트 전략

| 계층 | 대상 | 실행 명령 | 기대 결과 |
|------|------|----------|----------|
| L1 단위 | `mirrorPathForDir`·`matchLayerRule`·`matchDomain`·`decideTarget`·`mergeManifest`·exports 대조 | `node --test opal/tools/code-scan/tests/test-resolve-header.js` 등 | TS-008·TS-009·TS-027 등 통과 |
| L2 통합(CLI 블랙박스) | 5신규 서브명령 × 픽스처 4종, hook stdin 주입, 위반 9케이스 | `node --test opal/tools/code-scan/tests/` (`cwd: fixtureRoot` subprocess) | TS-004~TS-046 통과, exit code 계약 일치 |
| L2 회귀 | 8커맨드 골든 대조 | `test-regression.js` | 바이트 동일 (제약②) |
| L3 실환경 | install 재배포 · `run.sh` · `tool-scan usage` · 자체 저장소 dogfooding 4항목 · 실 세션 hook 관측(H-9) | Step 19 수동 실행 + 로그 | exit 0 · `ok: true` · 위반 0(`--changed`) |
| 품질 | 린트·타입 체크 | 해당 없음 — 저장소에 JS 린터·`package.json`이 없다(→ ANALYSIS §1.4 "리포지토리 어디에도 `package.json`이 없고") | 대신 `node --check` 문법 검사로 대체 |
| 보안 | 시크릿 스캔 · `.gitignore` 확인 | `git check-ignore` + 픽스처 grep | §5.4 전 항목 통과 |

---

## 8. 기술 컨텍스트

### 8.1 기술 스택

| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| 도구 본체 | Node.js (외부 패키지 0) — `code-scan.js` v1.2.0 → v1.3.0 | 해당 없음 (프레임워크 내부) |
| hook | Node.js (표준 모듈만) — Claude Code PostToolUse | 해당 없음 |
| 래퍼·설치 | Bash — `run.sh`, `install-mac.sh` | 해당 없음 |
| 테스트 | Node 내장 `node:test` + `node:assert/strict` + `child_process` | 해당 없음 (선례 → D-15) |
| 규칙 문서 | Markdown | 해당 없음 |

### 8.2 사용 MCP

| MCP | 조회 결과 요약 |
|-----|--------------|
| 해당 없음 | 외부 라이브러리·API 신규 도입 0건. 태스크 Guards가 외부 저장소 참조·인용을 금지하며 근거는 전량 저장소 내부다 (ANALYSIS §2 승계) |

### 8.3 참조 문서 (설계 결정 근거)

> ANALYSIS §0의 D-1~D-20 번호를 그대로 승계하고 D-21~D-28을 추가한다(단계 간 인용 번호 정합).

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | code-scan.js | `opal/tools/code-scan/code-scan.js` | 단일 해석 지점(`:274`)·`scanAll` 교체점(`:324`)·8커맨드·config 로더(`:150`)·`patternToRegex`(`:170`)·exit code 관례 |
| D-2 | 설계 | header-standard.md | `opal/core/references/header-standard.md` | 필수 5필드(`:13-21`)·layer 표준값(`:26`)·`module` 언어별 컨벤션(`:15`)·layer별 exports 가이드(`:132-157`) |
| D-3 | 설계 | header-rules.md | `opal/core/references/harness/header-rules.md` | "별도 도구 없음"(`:12`)·파일 생성/수정 규칙(`:26-53`)·빈 결과 폴백 3분기(`:83-89`)·테스트 파일 선택 필드(`:33-40`) |
| D-4 | 설계 | code-scan-management.md | `opal/core/references/pm/code-scan-management.md` | 추론 소스 3종(`:14-31`)·`.md` 기본 포함·생성 보고 형식 |
| D-5 | 설계 | pm-review-gate.md | `opal/core/references/harness/pm-review-gate.md` | Gate 8번 `scan <file> --json`(`:52-56`)·14번 인용 검증(`:89-94`) |
| D-6 | 소스 | brain-tool README | `opal/tools/brain-tool/README.md` | `sync-header` 단방향 계약 — F-011 갱신 대상(PM-3) |
| D-7 | 설계 | brain entity 템플릿 | `opal/tools/brain-tool/templates/page-entity.md` | 구조축 한정 근거(기능축 키 부재) — `feature` 조인 키 설계 배경 |
| D-8 | 설계 | citation-rules.md | `opal/core/references/harness/citation-rules.md` | §2 인용 포맷·§3 적용 방식·§4 PLAN 의무 수준·§8.6 정책·IA 토큰 |
| D-9 | 기획 | 076 태스크 | `tasks/076-260723-opds-todo미러-hook자동화/` | 산문→hook 강제 선례·멱등 upsert 패턴 |
| D-10 | 소스 | brain_tool.py | `opal/tools/brain-tool/brain_tool.py:766-854` | `--json` 소비 경로·4필드 비교(`:839`) — 간접 영향 무해 논거 |
| D-11 | 소스 | todo_mirror_hook.py | `opal/tools/state-tool/todo_mirror_hook.py` | PostToolUse 입력 계약(`:25-31`)·fail-safe(`:124-130`)·`additionalContext` 형식(`:84-94`) |
| D-12 | 소스 | claude-hooks.json | `opal/core/hooks/claude-hooks.json` | hook 등록 스키마(`:2-12`) — additive 엔트리 대상 |
| D-13 | 소스 | install-mac.sh | `scripts/install-mac.sh:1091-1219` | 도구 chmod 블록 열거(`:1096-1174`)·`merge_hooks_config` 호출(`:1212-1219`)·Node 환경 체크(`:1181-1184`) |
| D-14 | 소스 | test_todo_mirror_hook.py | `opal/tools/state-tool/tests/test_todo_mirror_hook.py` | hook 테스트 컨벤션(subprocess + stdin 주입) |
| D-15 | 소스 | skill-registry tests | `opal/tools/skill-registry/tests/test-validate.js` 외 2건 | 유일한 Node 테스트 컨벤션 — `node:test`·CLI 블랙박스·`test-<verb>.js`·TC↔S-ID 매핑 표(`:1-33`) |
| D-16 | 소스 | tool-scan manifest | `opal/tools/tool-scan/manifest.json:51-65` | code-scan capability 등록(`exec: "run.sh --help"` — F-013 근거) |
| D-17 | 소스 | .gitignore | `.gitignore:2-4` | `.opal/*` 무시 + `!.opal/brain/**` 예외 선례 |
| D-18 | 소스 | tool-scan tests/fixtures | `opal/tools/tool-scan/tests/fixtures/` | 정적 커밋 픽스처 선례 |
| D-19 | 문서 | PROJECT.md | `docs/PROJECT.md` §프로젝트 구성(`:152-160`) | 3요소 Framework/Console FE/Console BE — `.opal/code-scan.json` scopes 추론 소스 |
| D-20 | 설계 | CONVENTIONS.md 변경이력 의무 | `docs/CONVENTIONS.md` §구현 규칙 §변경이력 작성 의무(`:196-200`) | F-011 7문서 갱신 형식 |
| D-21 | 설계 | PRINCIPLES.md | `opal/core/PRINCIPLES.md` §2·§3 | Simplicity First·Surgical Changes — 미채택 기능 근거 |
| D-22 | 설계 | opal-harness.md | `opal/core/references/opal-harness.md` §9(`:218-260`) | `run.sh` 래퍼 규약(`:232`)·도구 표 code-scan 행(`:250`) |
| D-23 | 소스 | state-tool run.sh | `opal/tools/state-tool/run.sh:1-12` | 래퍼 형식 관례(shebang·`SCRIPT_DIR`·인터프리터 검사·`exec`) |
| D-24 | 소스 | tool-scan run.sh / tool_scan.py | `opal/tools/tool-scan/run.sh:1-12`, `opal/tools/tool-scan/tool_scan.py:51,322-330` | 환경변수 오버라이드·stdout JSON 에러 형식·`help_exec_failed` 정의 |
| D-25 | 설계 | red-first.md | `opal/core/references/harness/red-first.md` | RED-first 적용 기준 §1.5·작성자≠구현자 §2·테스트 불변성 §3 |
| D-26 | 설계 | CONVENTIONS.md 구현 규칙 | `docs/CONVENTIONS.md` §언어 규칙·§네이밍 규칙·§구현 규칙(`:1-52,153-213`) | 필드명 English·kebab-case·배포 경계·State 관리·Guards |
| D-27 | 소스 | tools.md code-scan 절 | `opal/core/references/tools.md:202-289` | 현행 커맨드·옵션 표 — F-011 갱신 대상 및 하위호환 호출 경로 근거 |
| D-28 | 설계 | op-dev-plan plan-guide | `~/.opal/skills/op-dev-plan/references/plan-guide.md` | Step 형식·복잡도 기준·C-1 그룹핑 우선순위·docs/ 갱신 규칙 |

---

## 9. 리스크 및 대응 (기능-리스크 연결)

| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| 1 | 8커맨드 회귀 (제약② 파손) | F-002, F-010 | P0 | 변경 전 코드로 골든 캡처(Step 3) → 바이트 동일 대조(TS-006). code-map 부재 시 `extractHeader` 반환값을 그대로 돌려주는 구조로 설계(§3.2.2 (G)4). 탐색·출력 계층 diff 0줄 규율 (H-8) |
| 2 | 픽스처가 실제 스캔·brain 동기화를 오염 | F-012 | P1 | 이중 격리 — `.opal/code-scan.json` `exclude: ["fixtures"]`(Step 1, **Step 2보다 먼저**) + 픽스처 자기완결 `.opal/` + `cwd` subprocess (H-1 / PM-6) |
| 3 | hook이 전 프로젝트 매 `Edit`/`Write`에서 실행 | F-009 | P0 | 조기 이탈 9단(5번째에서 `index.json` 부재 판정) + 전 경로 `try/catch` exit 0 (H-6 / PM-7) |
| 4 | hook matcher 정규식 미지원으로 무발동 | F-009 | P1 | 실 세션 관측(TS-042/H-9) + 폴백 확정(3개 엔트리 분리). hook 내부 `tool_name` 이중 방어로 어느 형태든 동작 동일 |
| 5 | `scaffold` 비멱등으로 재실행 diff 발생 | F-004 | P1 | 키 순서·직렬화·`writeIfChanged` 결정론 고정 + 2회 실행 바이트 동일 검증(TS-016 / H-10) |
| 6 | 미러 경로 충돌로 매니페스트 소실 | F-001, F-004 | P0 | 2-pass 구조 — 전체 사상 선계산 후 충돌 시 **무쓰기 exit 1**(`mirror_collision`). 승자 규칙 미도입(H-11) |
| 7 | `layerRules` 배열 순서 의존 비결정성 | F-001, F-002 | P1 | 구체성 점수 + 4단 tie-break로 배열 순서 무관 설계 + 순서 교차 테스트(TS-009 / H-12) |
| 8 | 단일 파일 스캔에서 지도 미해석 → PM Gate 8번 파손 | F-002 | P0 | 파일 → dirname → 스코프 재판정 → 정방향 사상 경로로 역매핑 불필요화(§3.2.2 (E)) + TS-007 (H-5 / PM-2) |
| 9 | `draft` 차단 정책이 pass2 직후 실패로 오해 유발 | F-006 | P1 | `header-rules.md` 표2(3단 갱신 시점)에 "`validate`는 pass4 게이트"임을 명문화 + `--changed`로 영향 한정 + TS-029로 흐름 고정 (H-13) |
| 10 | `exports` 텍스트 대조의 false negative | F-006 | P2 | 한계를 **계약으로 문서화**(주석 내 존재는 통과) + TS-027로 3케이스 고정. 문법 파서 미도입은 PM-4 확정 (H-14) |
| 11 | `target` 판정 순서 오구현 → readonly 규약 위반 | F-005 | P0 | 판정 순서를 표로 고정(§3.5.2) + readonly × 3케이스 전수 테스트(TS-022 / H-15) |
| 12 | brain `sync-header` 의미론 오염 | F-002, F-011 | P2 | 코드 변경 없음(`brain_tool.py:839` 4필드 비교는 무관 키 무시) + `brain-tool/README.md`에 의미 변화 1문장 명시. 단방향 계약 문언 불변 (H-16 / PM-3) |
| 13 | install 후 `run.sh` 실행 권한 누락 | F-013 | P0 | state-tool 패턴 chmod 블록 추가(Step 13) + install 재실행 후 L3 확인(TS-058·TS-059 / H-17) |
| 14 | code-map이 gitignore로 미추적 | F-012 | P1 | `!.opal/code-map/` + `!.opal/code-map/**` 예외(brain 선례) + `git check-ignore` 검증(TS-055 / H-18) |
| 15 | `depends` 결과 정밀도 의미 변화 | F-002 | P2 | 의도된 동작임을 `tools.md`·`header-rules.md`에 명시하고 스냅샷 테스트로 고정(H-2). 정밀도 개선은 후속 태스크 |
| 16 | 동일 파일 8 Step 순차로 인한 리드타임 증가 | 전 기능 | P2 | 파일 충돌 방지가 우선순위 1이므로 수용. 문서 4트랙 병렬(Batch 5)로 총 리드타임 상쇄 |
| 17 | 저장소 전량 `validate`가 위반 다수 → 완료 판정 혼선 | F-012 | P1 | dogfooding 완료 기준을 `--changed` 기반으로 명시 한정(§3.12.2 (G)) + 전량 자산화는 확정 방향 12에 따라 후속 태스크로 분리 |
| 18 | 용어 일관성 — `code-map` / `code map` / `소스 코드 지도` 혼용 | F-011 | P2 | 문서 표기 규칙 고정: 디렉토리·필드·CLI는 `code-map`, 한국어 본문 정식명은 "소스 코드 지도(code-map)". `source-map`·`codes` 표기 사용 금지(확정 방향 1) — Step 15~18에서 grep 확인 |

> §7.1 영역 간 용어 일관성 검토 결과(→ D-8 §7): FE↔BE·정책↔코드·ERD↔코드·IA↔라우트 4쌍 모두 **해당 없음**(단일 도구·문서 태스크). 검출된 용어 리스크는 #18 1건이며 도메인 결정이 필요한 사안이 아니라 표기 규칙 고정으로 해소되므로 `decision_required` 에스컬레이션 대상이 아니다.

---
## 변경이력

| 날짜 | 변경 내용 |
|------|----------|
| 2026-07-28 13:24 | 최초 작성 — 13기능 1:1 매핑, code-map 2파일 스키마 확정, 5단 상속 해석기·미러 경로 사상(root→anchors→stripPrefix)·양방향 계산·단일 파일 역매핑, layerRules 구체성 4단 tie-break, target 4단 판정·reason 4종 계약, validate 5종+worker_scope_violation·exit 0/1/2, 워커 권한 경계 재계산 대조 7행, scaffold 멱등 merge, hook 조기이탈 9단, run.sh 래퍼 형식, 픽스처 6조건 트리, 20 Step·7 Phase 실행계획, H-1~H-18 리스크 가설, RED-first 강제 판정 (077) |
