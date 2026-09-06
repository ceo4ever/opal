# PLAN: 헤더 소스 단일화 — headerSource 기준 통일 + 스코프 include/exclude

> 작성일: 2026-08-01 | 입력: TASK.md (초판은 ANALYSIS.md 없이 코드 직접 분석) · ANALYSIS.md (v1.1 보정 시 교차 검증 결과 반영)
> 모드: Multi-Feature (기능 7개) | 실행 모드: **복잡** | RED-first: **적용**
> 대상 도구: `opal/tools/code-scan/code-scan.js` v1.3.3 (1,774줄, Node 무의존) → v1.4.0
>
> **v1.1 보정 이력 (2026-08-01)** — 독립 분석가(op-dev-analysis) 교차 검증 결과 반영. 반증된 설계 주장은 없었고 아래 5건을 보정했다:
> ① `target`이 5지점 중 유일한 **무필터 공백 지점**임을 반영하고 out-of-scope 반환 계약을 신설(§3.2.2 (C-bis), Step 5 ⑤, H-13, R-15)
> ② `codemap-repo` 그룹 A/B/C 조치 결정 — **그룹 C(077 TS-005) 폐기 + 077 TS-044·TS-045로 불변식 분할 승계**, 픽스처 자산 무변경(§3.7.2, R-10)
> ③ `.gitignore` `!.opal/code-scan.json` **예외 채택 결정**(§3.5.3, Step 9, R-8, H-14)
> ④ 인용 정밀도 — `buildCtx` 호출 5곳(N-5) · CONVENTIONS.md 갱신 Step 12(§1.4)
> ⑤ `brain_tool.py` **무수정 성립을 줄번호로 확정**(§3.5.4)
>
> **v2.0 설계 축소 (2026-08-02)** — 소유자 결정으로 D-2가 변경됐다: **`headerSource`는 전역 단일 키이며 스코프별 오버라이드를 두지 않는다**(→ D-7 §확정된 설계 방향 D-2 갱신본). 문구 보정이 아니라 설계 범위 축소다:
> ① 우선순위 **3층 → 2층**(CLI > 전역). `effectiveHeaderSource(relPath, ctx)` **함수 자체 삭제**, 모드는 실행당 1값으로 확정(§3.1.2 (C)(D))
> ② `index.json` `scopes.{name}`에서 모드 선언 키 제거 — `include`/`exclude`(파일 집합 필터)만 유지(§3.2.2 (A)(E))
> ③ `readonly` 처리 **흡수 → 무시 + 안내 1회**. `manifest`로 해석하지 않는다(§3.4.2, TS-030 반전)
> ④ `out_of_scope` 배선·`reason`/`write_to` 3값 도메인은 **불변**(모드가 아니라 필터 축이므로 별개)
> ⑤ 축소 정량은 §12 참조
>
> **v2.1 보정 (2026-08-02)** — 시나리오 게이트 iteration 2(pass, 평균 1.67) gap 4건 흡수:
> ① 스코프 오버라이드 재도입 문이 `code-scan.json` 쪽에 열려 있던 것을 막음 — `normalizeConfigScope`에 감지+안내, (E)를 **두 파일 공통 표**로 확장(§3.2.2 (A)(E), TS-069)
> ② §12가 선언한 "모드 판정 1곳 수렴"을 **산출물 검사로 집행**(TS-070) + `discover` 산출물 모드 키 0건(TS-071)
> ③ `mixed-scope` 픽스처를 **생존 스코프 2개** 구조로 확정해 "실행당 1값" 검증 무대 확보(§3.7.2, TS-072~074) + `scope_ambiguous` 트리 분리
> ④ `include`/`exclude` 타입 위반 거부 TS 추가(TS-075)
>
> **v2.2 최종 보정 (2026-08-02)** — 목표-커버 게이트 iteration 3 **통과(goal 2 / adoption 2 / boundary 2, 평균 2.0 만점)**. 게이트가 함께 지적한 PLAN 정합 결함 3건을 EXECUTE 진입 전에 닫았다:
> ① `deprecationOnce` 계약 불일치 — §3.4.2 스텁 2곳이 1인자였던 것을 **`(key, message)` 2인자**로 정정하고 §3.2.2 (E) 3키 표와 대조 완료 + 함수 시그니처·호출 지점 표 신설
> ② TS-070 봉인이 리터럴 blacklist라 **구조분해·별칭으로 우회**되던 것을 **화이트리스트 4단계 절차**로 교체(함수 범위를 중괄호 깊이로 특정 → 그 밖에서 허용 3형태 외 토큰 출현 시 FAIL) + 금지/허용 예시 각 4건
> ③ `mixed-scope` 매니페스트 `files` 미명세로 충돌하던 3역할을 **커밋 상태 1개 + 임시 복사본 오버레이**로 양립시키고, **TS별 사전 상태 고정표**로 못박음(§3.7.2)

---

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

`code-scan`의 헤더 소스 판정이 **조회 경로 1곳**(`resolveHeader`, `code-scan.js:690`)에서만 `headerSource`를 참조하고, 작성 판정(`decideTarget`, `code-scan.js:755-791`)·`scaffold`·`validate` 커버리지는 모드를 무시한다. 그 결과 한 프로젝트 안에서 인라인과 code-map 두 소스가 계속 혼재한다. 이 태스크는 `headerSource`를 **조회·작성 판정·검증 전 경로의 단일 기준**으로 승격하고(`auto` 제거 → 2택, 미설정 = 거부), `scopes`에 객체 형식(`include`/`exclude`)을 추가해 혼재 디렉토리를 화이트리스트로 표현한다.

**`headerSource`는 전역 단일 키다 — 스코프별 오버라이드를 두지 않는다**(2026-08-02 소유자 결정, → D-7 §확정된 설계 방향 D-2). 한 실행의 모드는 **실행당 1값**으로 확정되며 파일·스코프에 따라 달라지지 않는다. 근거: 전역이 `manifest`면 프로젝트 전체가 매니페스트 기록이므로 스코프별 재선언이 무의미하고, 오버라이드가 값을 갖는 유일한 경우인 혼재 케이스를 소유자가 "존재할 수 없다"고 판단했다. 이는 D-3이 `auto`(파일 단위 암묵 혼재)를 제거한 논리와 일관된다 — 스코프 단위 혼재만 남기면 결정이 반쪽이 된다. [MUST] `opal/core/PRINCIPLES.md` §2: "Solve only the current requirement. No speculative abstraction or unrequested flexibility."

동시에 077에서 드러난 **필터 적용 지점 분산 결함**(파일 집합 판정이 5곳에 흩어져 한 곳이 빠지면 조용한 오탐 — `code-scan.js` v1.3.1/v1.3.3 변경이력 `:1759-1774`)을 단일 함수 계약(`isInScope`)으로 구조적으로 봉인한다.

### 1.2 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | `headerSource` 스키마 재정의 + 전 명령 차단 게이트 + `--header-source` 플래그 | TASK F-1, F-2, F-12② | P0 | 없음 |
| F-002 | `scopes` 객체 형식 정규화 + 단일 필터 계약 `isInScope` + 스코프 중복 우선순위 | TASK F-7, F-8, F-10 | P0 | 없음 |
| F-003 | 작성·검증 경로의 모드 존중 (`decideTarget`/`scaffold`/`validate`/검출기) | TASK F-3, F-4, F-5, F-9 | P0 | F-001, F-002, F-004 |
| F-004 | `readonly` 제거(**무시 + 안내 1회**) + `discover` 산출물 정합 | TASK F-6 | P0 | F-001 |
| F-005 | 소비자 파급 대응 (저장소 설정 · hook fail-safe · `brain-tool` 실패 전달 · PM Gate 절차) | TASK F-12 ①③④⑤ | P0 | F-001, F-003 |
| F-006 | 규칙 문서 5종 + 프로젝트 `docs/` 3종 갱신 | TASK F-11 | P1 | F-001~F-005 |
| F-007 | 테스트 자산 전면 갱신 + 픽스처 계약 + 골든 재캡처 | TASK F-13 | P0 | (RED는 F-001~F-005보다 **선행**) |

### 1.3 기능 의존 그래프

```
F-007(RED 테스트/픽스처) ──선행──┐
                                 ▼
F-001(스키마·게이트) ──┬──► F-004(readonly 제거) ──┐
                        │                            ├──► F-003(작성·검증 모드 존중) ──► F-005(소비자 파급)
F-002(스코프 정규화·필터) ─────────────────────────┘                                          │
                                                                                                ▼
                                                                              F-006(규칙·docs 문서 갱신)
                                                                                                │
                                                                                                ▼
                                                                              F-007(GREEN 확인·골든 재캡처)
```

### 1.4 [MUST] 제약 (재해석 금지 — 원문 인용)

- [MUST] `.opal/AGENT.md` §금지사항: "**`~/.opal/` 직접 편집 금지** — 항상 프로젝트 소스를 수정한 후 install로 배포한다."
- [MUST] `.opal/AGENT.md` §금지사항: "**변경이력 누락 금지** — 스킬·에이전트·참조 문서 수정 시 변경이력 표 행 추가 의무."
- [MUST] `docs/CONVENTIONS.md` §구현 규칙 > @header 규칙: "**기록 위치는 `code-scan target <file>` 판정을 따른다** — 인라인 주석 또는 외부 소스 코드 지도(`.opal/code-map/`) 2소스 중 하나이며, 사람·워커가 임의 선택하지 않는다(읽기 전용 스코프는 code-map 강제)." → 괄호절의 "읽기 전용 스코프"는 F-004로 소멸하므로 **본 태스크가 이 문장을 갱신 대상으로 포함**한다 (Step 12 — `docs/` 3종 갱신 Step. Step 13은 골든 재캡처이며 이 문서와 무관하다).
- [MUST] `docs/CONVENTIONS.md` §구현 규칙 > 변경이력 작성 의무: "스킬·에이전트·참조 문서를 변경하면 '## 변경이력' 표에 행을 추가한다. 일시는 `YYYY-MM-DD HH:mm` (KST), 버전은 semver, 변경내용은 태스크 번호를 괄호로 포함"
- [MUST] `docs/CONVENTIONS.md` §구현 규칙 > 배포 경계: "`~/.opal/` 배포 파일을 직접 편집하지 않는다. 변경은 항상 프로젝트 소스(`opal/`, `skills/`, `agents/`, `community-skills/`, `scripts/`)에서 수행한다."
- [MUST] `docs/CONVENTIONS.md` §언어 규칙: "코드/변수/필드명 — English" · "파일/폴더 이름 — English, kebab-case (Python 파일은 snake_case)" → 신규 식별자 `isInScope` · `headerSource` · `--header-source` · `header_source_unset`은 이 규칙을 따른다.
- [MUST] `opal/core/PRINCIPLES.md` §2 Simplicity First: "Remove a duplicated existing pattern before introducing a new one." → 스코프 필터 판정은 **`isInScope` 단일 함수로만** 존재한다. 기존 `isExcluded`를 `matchesAnyPattern`으로 승격 재사용하고 신규 매칭 로직을 만들지 않는다.
- [MUST] `~/.opal/references/harness/red-first.md` §3: "GREEN/fix 루핑 중 RED 테스트 파일 수정 금지."
- [MUST] TASK.md §제약 조건: "신규 도구 코드는 Node.js 표준 모듈만 사용한다 (외부 npm 의존 금지)"
- [MUST] TASK.md §제약 조건: "규칙·문서에 개인 식별자(에이전트 이름·소유자 호칭)를 기재하지 않고 역할명(PM/소유자)을 사용한다"
- [MUST] TASK.md §제약 조건: "**제약②(기존 프로젝트 동작 변화 0)는 이번 태스크에서 파기된다** — D-3·D-4·D-5의 직접 결과이며, 완료기준을 '명시 설정 후 동작 변화 0'으로 대체한다"

### 1.5 제약② 파기 선언 (명시)

077의 최상위 제약이었던 **"기존 프로젝트 동작 변화 0"은 이 태스크에서 의도적으로 파기된다.**

| 항목 | 077 계약 | 080 계약 |
|------|---------|---------|
| 미설정 프로젝트 | `headerSource: 'auto'` 암묵 기본값으로 정상 동작 (`code-scan.js:198`) | **전 명령 exit 1** (`header_source_unset`) — D-4/D-5 |
| `auto` 값 | 유효값 (`code-scan.js:199`) | **명시 거부** (`header_source_invalid`) — D-3 |
| 골든 8커맨드 | 무설정 상태에서 바이트 동일 | **`headerSource: "inline"` 명시 상태**에서 바이트 동일 (F-013 재캡처) |
| `target` `reason` 도메인 | `readonly_repo`/`inline_exists`/`new_file`/`legacy_no_header` 4값 (`header-rules.md:25`) | `header_source_inline`/`header_source_manifest`/`out_of_scope` **3값** (§3.2.2 (C-bis)) |
| `target` `write_to` 도메인 | `inline`/`manifest` 2값 (`code-scan.js:762,773,776,782`) | `inline`/`manifest`/`none` **3값** — 스코프 필터 탈락 파일 표기 (§3.2.2 (C-bis)) |
| 모드 판정 단위 | 파일 단위 — `readonly` 스코프면 그 파일만 `manifest` (`code-scan.js:759-770`) | **실행 단위** — 실행당 1값으로 확정, 파일·스코프에 따라 달라지지 않는다 (2026-08-02 소유자 결정) |
| 스코프별 모드 선언 | `scopes[].readonly: true`로 스코프 단위 강제 가능 (`header-standard.md:206`) | **없음** — `index.json` `scopes.{name}` 허용 키에서 모드 선언 제거. `include`/`exclude`(파일 집합 필터)만 남는다 |
| `readonly: true` 처리 | 스코프 1순위 판정 → `manifest` 강제 | **무시 + deprecated 안내 1회**(전역 `headerSource` 설정 안내). `manifest`로 해석하지 **않는다** — 전역값이 그대로 적용된다 |
| `target`의 스코프 필터 | **없음** — `decideTarget`(`:755-791`)은 `isExcluded`/`hasExcludedSegment` 호출 0건 | `isInScope` 적용 (F-8 AC 5지점 중 마지막 공백 지점 충전) |
| `validate` 커버리지 | 인라인+매니페스트 **합산** (`header-rules.md:53`) | **모드별 단일 소스** |
| 077 TS-046 `headerSource:"bogus"` | `auto` 폴백 + stderr 경고 + exit 0 (`test-resolve-header.js:406-419`) | `header_source_invalid` + exit 1 (**반전** — 본 PLAN TS-003이 승계) |
| 077 TS-005 "혼재 파일 인라인 승리, 병합 없음" (`test-resolve-header.js:244-262`) | `auto` 단일 실행에서 양 소스 공존 관찰 | **폐기 — 불변식은 077 TS-044·TS-045로 분할 승계** (§3.7.2 그룹 C) |
| 077 TS-055 `.opal/code-scan.json` gitignore 여부 (`test-regression.js:126-127`) | 무시됨(exit 0)을 단언 | **비무시**(exit 1)로 반전 — `.gitignore` 예외 채택 (§3.5.3) |

이 파기는 계약 변경이므로 077이 남긴 테스트 자산 8파일도 새 계약으로 **재작성**된다. 재작성은 "테스트 약화"가 아니라 "계약 이전"이며, red-first.md §3의 금지 대상(GREEN 루핑 중 수정)과 구분하기 위해 **RED Step(Step 2)에서 일괄 수행하고 GREEN Step(Step 3~10) 동안에는 손대지 않는다.**

---

## 리스크 가설 표

> PLAN 단계에서 작성. TEST-SCENARIO.md §1의 입력이 됨.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | F-001 `main()` 전 명령 게이트 | code-scan을 subprocess로 호출하는 전 소비자(brain-tool `sync-header` `brain_tool.py:786-793`, PM Gate `pm-review-gate.md:53`, hook)가 동시 정지 | **P0** | L2(실 subprocess 호출) | S-후보 A |
| H-2 | F-001 `loadConfig` 반환 계약 (`headerSource: null` 허용) | `loadConfig`가 `process.exit`하면 hook의 fail-safe(무출력 exit 0)가 붕괴 — hook은 `main()`을 거치지 않고 `loadConfig`를 직접 호출한다 (`code-map-hook.js:120`) | **P0** | L1(단위) + L2(hook stdin 주입) | S-후보 B |
| H-3 | F-002 `getSearchPaths` 반환 타입 변경 (`string[]` → `{abs, scopeDef}[]`) | 호출자 `discoverFiles`(`code-scan.js:299`) 1곳 — 조회 8커맨드 전체가 이 경로를 탄다 | **P0** | L1(단위) + L2(골든 8커맨드) | S-후보 C |
| H-4 | F-002 `resolveScope` 우선순위 변경 | 기존 "최장 root → 이름 사전순"(`code-scan.js:564`)에 **include 매칭 축만** 삽입된다 — 모드 축은 전역 단일 키 결정으로 소멸했으므로 `resolveScope`는 "어느 스코프에 귀속되는가"만 판정하고 모드에는 관여하지 않는다. include 미사용 프로젝트의 귀속이 바뀌면 매니페스트 경로가 통째로 이동 | P1 | L1(tiebreak 픽스처 order-a/order-b) | S-후보 D |
| H-5 | F-002 `isInScope` 5개 지점 배선 누락 | 077 결함 D와 동형의 오탐 재발 — `scaffold`가 제외한 파일을 `validate`가 `files_key_removed`로 잡음 (`code-scan.js:1595-1599`) | **P0** | L2(혼재 디렉토리 픽스처 5지점 교차) | S-후보 E |
| H-6 | F-003 `decideTarget` reason 도메인 축소 | `header-rules.md:25` "이 4값 외를 반환하지 않는다" 명문 계약 위반 + hook `buildWarning`이 reason을 출력 (`code-map-hook.js:70`) | P1 | L1 + 문서 정합 | S-후보 F |
| H-7 | F-003 `validate` 모드별 커버리지 | `pm-review-gate.md:57` "합산 커버리지" 게이트 기준이 무효 → PM Gate가 오판정 | P1 | L2(양 모드 동일 픽스처 대조) | S-후보 G |
| H-8 | F-004 `readonly` **무시** 전환 | 기존 index.json 18종 중 17종이 `readonly` 키를 보유하고 그중 `true`는 1건(`fixtures/codemap-repo/.opal/code-map/index.json:23`). **초판의 `manifest` 흡수 로직이 잔존하면** 전역값을 무시하고 그 스코프만 `manifest`로 새어 나가 전역 단일 키 결정이 조용히 파괴된다 — 반대 방향(안내 누락)은 사용자가 동작 변화를 인지하지 못하게 만든다 | P1 | L1(양방향 TS-030·TS-033 + 안내 TS-031) | S-후보 H |
| H-9 | F-007 픽스처 20개 `code-scan.json` | 전량에 `headerSource` 부재 → 게이트 도입 즉시 **기존 100 케이스 전량 exit 1** | **P0** | L2(전 테스트 실행) | S-후보 I |
| H-10 | F-007 골든 재캡처 | `legacy-repo`는 code-map 부재이므로 `inline` 모드 결과가 기존 `auto` 결과와 동일해야 한다 — 바이트가 달라지면 조회 경로에 의도치 않은 회귀가 생긴 것 | P1 | L2(골든 대조 + diff 기록) | S-후보 J |
| H-11 | F-005 이 저장소 `.opal/code-scan.json` | 이 파일은 **gitignore 대상**(`.gitignore:2` `.opal/*`) → 설정 변경이 커밋되지 않아 타 환경·CI에서 게이트가 재발 | P1 | L3(신규 클론 시나리오) — 영속 해결은 `code-scan-management.md` 생성 규약 | S-후보 K |
| H-12 | F-003 `manifest` 모드 + index.json 부재 | 조회 결과가 전량 공백이 되어 "조용한 실패" 발생 | P2 | L1(경고 1줄 비차단) | S-후보 L |
| H-13 | F-002 **`target`은 애초에 필터 대상이 아니었다** — `decideTarget`(`:755-791`)의 `isExcluded`/`hasExcludedSegment` 호출 0건 | H-5(5지점 배선 누락)와 별개 사실. 나머지 4지점은 "기존 호출 대체"지만 `target`은 **신규 도입**이므로 반환 계약 자체가 미정의였다 — 계약 없이 배선하면 스코프 밖 파일에 매니페스트 경로 없는 `write_to: manifest`가 나가 워커가 쓸 자리를 못 찾는다 | **P0** | L1(반환 계약) + L2(hook 이탈 회귀) | S-후보 M |
| H-14 | F-005 `.gitignore` 예외 추가 | 077 TS-055(`test-regression.js:126-127`)가 "`.opal/code-scan.json`은 계속 무시되어야 함"을 단언 → 예외 채택 시 이 테스트가 반전된다. 반전 누락 시 GREEN에서 실패 | P1 | L2(`git check-ignore` 실측) | S-후보 N |

---

## 2. 기능별 분석

### F-001: `headerSource` 스키마 재정의 + 전 명령 차단 게이트

#### 2.1.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 도구 | `opal/tools/code-scan/code-scan.js:40-46` | `DEFAULT_CONFIG` — `headerSource: 'auto'` 기본값 보유 | 수정 |
| 도구 | `opal/tools/code-scan/code-scan.js:61-110` | `USAGE` 문자열 — 설정 예시에 `"headerSource": "auto"` 노출(`:108`) | 수정 |
| 도구 | `opal/tools/code-scan/code-scan.js:131-173` | `parseArgs` — `--header-source` 플래그 미지원 | 수정 |
| 도구 | `opal/tools/code-scan/code-scan.js:193-213` | `loadConfig` — 3택 검증 + `auto` 폴백 | 수정 |
| 도구 | `opal/tools/code-scan/code-scan.js:474-477` | `codeMapErrorExit` — stdout JSON only | 수정 |
| 도구 | `opal/tools/code-scan/code-scan.js:1696-1733` | `main()` 디스패치 진입부 — 게이트 삽입 지점 | 수정 |

#### 2.1.2 현재 구현

`loadConfig`는 `.opal/code-scan.json`을 읽어 `headerSource`를 3택(`auto`/`inline`/`manifest`)으로 검증하고, 유효하지 않으면 stderr 경고 후 `auto`로 폴백한다(`code-scan.js:198-202`). 파일이 없거나 JSON 파싱에 실패하면 `DEFAULT_CONFIG`(`headerSource: 'auto'`)를 그대로 반환한다(`code-scan.js:210`, `:212`) — **파싱 실패와 파일 부재가 구분되지 않는다.**

`main()`은 `help`/`version`을 조기 반환한 뒤(`:1699-1700`) `findProjectRoot()`·`loadConfig()`를 호출하고(`:1702-1703`) 13개 커맨드 디스패치 테이블(`:1705-1719`)로 분기한다. `headerSource` 관련 검증은 이 지점에 **전혀 없다**.

`codeMapErrorExit(code, extra)`는 `console.log`로 stdout에만 JSON을 쓰고 exit 1 한다(`:474-477`). stderr에는 아무것도 쓰지 않는다.

#### 2.1.3 영향 범위

- **상위 의존(호출자)**: `main()`을 통해 13커맨드 전부. 외부에서는 `brain_tool.py:786-789`가 `node code-scan.js scan --json`을 subprocess로 호출하고 `returncode != 0`이면 `header_parse_failed`로 err하며 **`stderr`만 detail에 담는다**(`brain_tool.py:790-792`) — 게이트 메시지가 stdout에만 있으면 사유가 소실된다(H-1).
- **하위 의존**: `loadConfig`는 `code-map-hook.js:120`에서도 직접 호출된다. `main()`을 거치지 않으므로 게이트를 `loadConfig` 안에 넣으면 hook의 fail-safe 계약(`code-map-hook.js:151-158`)이 붕괴한다(H-2).
- **관련 테스트**: `tests/test-resolve-header.js` 077 TS-044/045/046(headerSource 스위치), `tests/test-regression.js` 골든 8커맨드.

---

### F-002: `scopes` 객체 형식 정규화 + 단일 필터 계약

#### 2.2.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 도구 | `opal/tools/code-scan/code-scan.js:219-232` | `patternToRegex` — `*`/`**`/`?` 글롭 컴파일 (재사용) | 유지 |
| 도구 | `opal/tools/code-scan/code-scan.js:234-241` | `isExcluded(relPath, fileName, patterns)` — "패턴 중 하나라도 매치" 판정 (`/` 포함 시 전체 경로, 아니면 파일명) | 수정(개명) |
| 도구 | `opal/tools/code-scan/code-scan.js:250-252` | `hasExcludedSegment` — 디렉토리 세그먼트 축 (별개 축, 유지) | 유지 |
| 도구 | `opal/tools/code-scan/code-scan.js:279-296` | `getSearchPaths` — `config.scopes[name]`를 문자열로 가정 (`:281`, `:292`) | 수정 |
| 도구 | `opal/tools/code-scan/code-scan.js:298-314` | `discoverFiles` — **적용 지점 ①(열거)** | 수정 |
| 도구 | `opal/tools/code-scan/code-scan.js:506-533` | `loadCodeMap` — index 스키마 검증 (`scopes` 객체·`root` 필수 `:524-531`) | 수정 |
| 도구 | `opal/tools/code-scan/code-scan.js:557-569` | `resolveScope` — 최장 root 승리 + 이름 사전순 (`:564`) | 수정 |
| 도구 | `opal/tools/code-scan/code-scan.js:1093-1110` | `inferScopes` — config.scopes → index.scopes 파생 | 수정 |
| 도구 | `opal/tools/code-scan/code-scan.js:1222-1246` | `collectDirsWithCodeFiles` — **적용 지점 ②(scaffold 열거)**, `isExcluded` 호출 `:1236` | 수정 |
| 도구 | `opal/tools/code-scan/code-scan.js:1433-1446` | `listCodeFilesInDir` — **적용 지점 ③(validate 구조 패스)**, `isExcluded` 호출 `:1441` | 수정 |
| 도구 | `opal/tools/code-scan/code-scan.js:1455-1477` | `cmdValidate --changed` — **적용 지점 ④** | 수정 |
| 도구 | `opal/tools/code-scan/code-scan.js:755-791` | `decideTarget` — **적용 지점 ⑤(target)**. 현재 필터 유틸 호출 **0건**(무필터 공백 지점) — `resolveScope`(`:759`)로 스코프 귀속만 판정한다 | 수정(**신규 배선**) |
| 도구 | `opal/tools/code-scan/code-scan.js:1479` | `cmdValidate` 스코프 존재 확인 — `config.scopes[opts.scope]` | 수정 |
| 도구 | `opal/tools/code-scan/code-scan.js:1665-1666` | `cmdFeature` — `Object.keys(config.scopes)` | 확인(무변경 가능) |

#### 2.2.2 현재 구현

**두 개의 스코프 레지스트리가 공존한다.**

| 레지스트리 | 파일 | 스키마 | 소비 지점 |
|-----------|------|--------|----------|
| `config.scopes` | `.opal/code-scan.json` | `Record<name, string>` (경로 문자열) | `getSearchPaths:281,292` · `inferScopes:1095-1099` · `cmdValidate:1479` · `cmdFeature:1665` |
| `index.scopes` | `.opal/code-map/index.json` | `Record<name, {root, anchors, stripPrefix, readonly}>` | `resolveScope:559` · `cmdScaffold:1329-1331` · `cmdValidate` 구조 패스 `:1544` |

`isExcluded(relPath, fileName, patterns)`는 이름과 달리 **순수한 "패턴 중 하나라도 매치하는가" 판정**이다(`:234-241`) — 부정 의미는 호출자가 부여한다. 호출 지점은 4곳: `discoverFiles:312` · `collectDirsWithCodeFiles:1236` · `listCodeFilesInDir:1441` · `cmdValidate --changed:1475`.

파일 집합을 판정하는 지점은 5곳이지만, **실제로 필터를 적용하는 곳은 4곳뿐이다.** 다섯 번째인 `decideTarget`(`:755-791`)은 `isExcluded`·`hasExcludedSegment` 중 어느 것도 호출하지 않는다 — `resolveScope`(`:759`)로 스코프 귀속만 판정하고 include/exclude 멤버십은 보지 않는다. 즉 `target`은 "기존 필터를 교체할 자리"가 아니라 **필터가 처음 도입되는 공백 지점**이며, 이 때문에 반환 계약(§3.2.2 (C-bis))을 함께 정의해야 한다 (→ H-13, N-8).

077에서는 이미 v1.3.1(`--changed` 누락)과 v1.3.3(구조 패스 누락) 두 차례 필터 비대칭 오탐이 발생했다(`code-scan.js:1759-1774` 변경이력). `target`은 그 목록에 오르지 않았을 뿐 세 번째 비대칭 후보다.

#### 2.2.3 영향 범위

- `getSearchPaths`의 반환 타입을 바꾸면 유일한 호출자 `discoverFiles:299`만 영향받지만, `discoverFiles`는 `scanAll:798` → `scanHeaders:816` → 조회 8커맨드 전부가 타는 경로다(H-3).
- `resolveScope`는 `resolveManifestContext:620` · `decideTarget:759` 두 곳에서 호출되고, 전자는 `resolveHeader:710` · `cmdValidate:1493`이 다시 호출한다 — 우선순위 변경은 조회·검증·작성 3경로에 동시 파급한다(H-4).
- `module.exports`(`:1739-1750`)가 `resolveScope`를 외부에 노출하므로 시그니처 유지가 바람직하다.

---

### F-003: 작성·검증 경로의 모드 존중

#### 2.3.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 도구 | `opal/tools/code-scan/code-scan.js:688-751` | `resolveHeader` — 유일한 `headerSource` 소비 지점 (`:690`, `:693`, `:699`) | 수정 |
| 도구 | `opal/tools/code-scan/code-scan.js:755-791` | `decideTarget` — `readonly` → 인라인 존재 → 신규 → 레거시 4단 | 수정 |
| 도구 | `opal/tools/code-scan/code-scan.js:1313-1393` | `cmdScaffold` — 모드 무관 전 디렉토리 매니페스트 생성 | 수정 |
| 도구 | `opal/tools/code-scan/code-scan.js:1448-1657` | `cmdValidate` — 합산 커버리지 + 6종 검출기 | 수정 |
| 도구 | `opal/tools/code-scan/code-scan.js:1496-1504` | `uncovered` 검출기 (`managedByManifest` 분기 `:1501-1502`) | 수정 |
| 도구 | `opal/tools/code-scan/code-scan.js:1595-1599` | `files_key_removed` 검출기 | 수정(간접) |
| 도구 | `opal/tools/code-scan/code-scan.js:1626-1641` | `counts`/`coverage`/`blockingViolations` 산출 | 수정 |

#### 2.3.2 현재 구현

**`resolveHeader`(조회)** — `headerSource !== 'manifest'`면 인라인을 먼저 추출하고(`:693-695`), code-map 부재 또는 `inline` 모드면 `extractHeader` 결과를 그대로 반환한다(`:699-701`, `_source` 키를 붙이지 않는 제약② 보증 지점). 그 외에는 인라인 단독 승리(`:703-707`) 또는 매니페스트 5단 상속(`:709-750`)으로 간다.

**`decideTarget`(작성 판정)** — `headerSource`를 **참조하지 않는다**. 판정 순서는 ① `scoped.scope.readonly === true` → `manifest`/`readonly_repo`(`:761-770`) ② 인라인 존재 → `inline`/`inline_exists`(`:772-773`) ③ 디스크 부재 → `inline`/`new_file`(`:775-776`) ④ 그 외 → `manifest`/`legacy_no_header`(`:778-790`).

**`cmdScaffold`** — `index.scopes` 전 스코프를 순회해 코드 파일이 있는 모든 디렉토리에 매니페스트를 생성한다(`:1328-1374`). 모드 분기 없음.

**`cmdValidate`** — `covered = inlineHeader !== null || fe !== null`(`:1496`)로 **합산** 판정하고, `coverage.covered = inlineCount + manifestCount`(`:1636`)를 산출한다. `uncovered`의 `no_entry` 서브는 "매니페스트가 이 디렉토리를 관리 중인데 키가 없음"일 때 부여된다(`:1501-1502`).

#### 2.3.3 영향 범위

- `decideTarget`은 `cmdTarget:1401`과 `code-map-hook.js:130` 두 곳에서 호출되고 `module.exports:1741`로 노출된다.
- `reason` 값 도메인 축소는 `header-rules.md:25`("이 4값 외를 반환하지 않는다")·`tools.md:240`·`tests/test-target.js` 077 TS-020/TS-022와 정면 충돌한다(H-6).
- 합산 커버리지 폐기는 `header-rules.md:53`·`header-rules.md:131`(저커버리지 폴백 기준)·`pm-review-gate.md:57`에 직접 연결된다(H-7).

---

### F-004: `readonly` 제거(무시 + 안내)

#### 2.4.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 도구 | `opal/tools/code-scan/code-scan.js:761-762` | `decideTarget` 1순위 판정 + `readonly_repo` reason | 수정(제거) |
| 도구 | `opal/tools/code-scan/code-scan.js:1098` | `inferScopes` — config.scopes 파생 시 `readonly: false` 기입 | 수정(제거) |
| 도구 | `opal/tools/code-scan/code-scan.js:1107` | `inferScopes` — 디렉토리 스캔 파생 시 `readonly: false` 기입 | 수정(제거) |
| 도구 | `opal/tools/code-scan/code-scan.js:1199` | `cmdDiscover` — `note` 문자열에 "readonly/anchors/stripPrefix 확인" 안내 | 수정 |
| 도구 | `opal/tools/code-scan/code-scan.js:506-533` | `loadCodeMap` — `readonly` 정규화 삽입 지점 | 수정 |
| 설계 | `opal/core/references/header-standard.md:206` | `scopes[].readonly` 필드 정의 행 | 수정 |
| 설계 | `opal/core/references/harness/header-rules.md:20` | 4단 판정표 ① 행 | 수정 |

#### 2.4.2 현재 구현

`readonly`의 코드상 효력은 `decideTarget:761`의 1순위 분기 **단 하나**다. `resolveHeader`·`cmdValidate`·`cmdScaffold`·`code-map-hook.js`에는 참조가 0건이다. 즉 "소스 코드 편집을 막는 코드"는 존재하지 않으며, `header-standard.md:206`의 서술("`true`면 `target`이 무조건 `manifest` 반환")이 구현과 정확히 일치한다.

`inferScopes`는 두 파생 경로 모두에서 `readonly: false`를 명시 기입한다(`:1098`, `:1107`).

> **TASK.md 기재 교정**: TASK.md §배경분석 (2)는 `readonly` 전량 참조를 "`:761`·`:1098`·`:1107` — 그 외 없음"으로 기술했으나, 실제로는 `cmdDiscover`의 `note` 문자열(`:1199`)에 1건이 더 있다. 문자열 리터럴이므로 판정 로직은 아니지만 F-11 AC("`readonly`를 판정 근거로 서술하는 문장 잔존 0건")의 대상이므로 갱신한다.

#### 2.4.3 영향 범위

- 픽스처 `index.json` **18종 중 17종**이 `readonly` 키를 보유하지만 `readonly: true`는 **전 저장소에서 1건뿐**이다 — `codemap-repo`의 `legacy` 스코프(`fixtures/codemap-repo/.opal/code-map/index.json:23`). 나머지 16종은 전부 `readonly: false`다(실측: `find fixtures -name index.json` 18건 / `grep -rl '"readonly"'` 17건 / `grep -rn '"readonly": true'` 1건). 이 저장소 자신은 `.opal/code-map/` 부재로 **0건**이다. 이 1건이 `test-target.js` 077 TS-020/TS-022·`test-resolve-header.js` 077 S-8의 근거 자산이며, **하위호환(무시+안내) 동작을 검증할 유일한 실증 자산**이다(H-8, §3.7.2).
- `code-scan-management.md:80`("도구는 도메인 경계·`readonly` 정책을 판정하지 않는다")·`pm-review-gate.md:56`("`readonly` 스코프에 속한 파일은 인라인 기록이 금지되므로")도 서술 대상이다.

---

### F-005: 소비자 파급 대응

#### 2.5.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 도구 | `opal/tools/code-scan/code-map-hook.js:116-136` | hook 조기 이탈 ⑤~⑦ — `loadConfig` 호출 `:120` | 수정 |
| 환경 | `.opal/code-scan.json` | 이 저장소 설정 — `headerSource` 키 부재, `scopes` 문자열 3종 | 수정 |
| 환경 | `.gitignore:2-6` | `.opal/*` 무시 + `brain`/`code-map` 2예외 — `code-scan.json`은 추적 제외 | 수정 |
| 도구 | `opal/tools/brain-tool/brain_tool.py:766-798` | `sync-header` — code-scan subprocess 소비 | 확인(**무변경 확정** — §3.5.4) |
| 설계 | `opal/core/references/harness/pm-review-gate.md:52-62` | PM Gate 8번 절차 | 수정 |

#### 2.5.2 현재 구현

**hook** — `code-map-hook.js`는 9단 조기 이탈 구조다. ⑤ `loadCodeMap` 부재 이탈(`:116-117`) → ⑥ `loadConfig` 호출 후 확장자 확인(`:120-122`) → ⑦ `decideTarget` 결과가 `manifest`가 아니면 이탈(`:136`). 최상위에 전 경로 fail-safe try/catch + 무조건 `process.exit(0)`이 있다(`:151-158`).

**brain-tool** — `_load_code_scan_json`은 `.opal/code-scan.json` 존재만 확인한 뒤(`brain_tool.py:776-777`) `node code-scan.js scan --json`을 실행하고, `returncode != 0 or not stdout.strip()`이면 `header_parse_failed`를 내며 **detail에 `stderr`만 담는다**(`brain_tool.py:790-792`).

**PM Gate** — 8번 절차가 `code-scan scan <file> --json`(`pm-review-gate.md:53`), `validate --json`(`:57`), `validate --changed`(`:58`)를 사용한다.

#### 2.5.3 영향 범위

- 이 저장소의 `.opal/code-scan.json`은 `.gitignore:2`(`.opal/*`)에 걸려 **git 추적 대상이 아니다**(`git ls-files .opal/code-scan.json` 결과 없음, `git check-ignore -v` 확인). 반면 픽스처의 `code-scan.json` 20종은 `.gitignore:5-6`의 code-map 예외와 무관하게 `opal/tools/code-scan/tests/fixtures/**` 경로라 정상 추적된다. 따라서 F-12①의 설정 변경은 **작업 트리 한정**이며 영속 해결책이 별도로 필요하다(H-11).
- `test-regression.js:97-101`(077 TS-052)은 저장소 루트에서 `scan --json` exit 0을 단언하므로, 이 저장소 설정이 갱신되지 않으면 **테스트가 실패한다**.

---

### F-006: 규칙 문서 5종 + `docs/` 3종

#### 2.6.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 문서 | `opal/core/references/header-standard.md:184-259` | §7 2소스 표현 — 스키마 SSOT | 수정 |
| 문서 | `opal/core/references/harness/header-rules.md:14-55` | 4단 판정표·3단 갱신 시점·커버리지 합산 | 수정 |
| 문서 | `opal/core/references/pm/code-scan-management.md:10-93` | 생성 시점 규약·`headerSource` 관리·index 관리 의무 | 수정 |
| 문서 | `opal/core/references/harness/pm-review-gate.md:52-62` | 검토 절차 8번 | 수정 |
| 문서 | `opal/core/references/tools.md:202-306` | code-scan 커맨드·옵션·종료 코드·설정 예시 | 수정 |
| 문서 | `docs/CONVENTIONS.md:171-176` | §@header 규칙 — "읽기 전용 스코프는 code-map 강제" | 수정 |
| 문서 | `docs/ARCHITECTURE.md:82` | `tools/` 표 code-scan 행 | 수정 |
| 문서 | `docs/PROJECT.md:197` 이하 | 변경이력 표 | 수정 |

#### 2.6.2 현재 구현 (문서 ↔ 코드 불일치 포함)

| # | 문서 서술 | 실제 코드 | 판정 |
|---|----------|----------|------|
| M-1 | `code-scan-management.md:73` "…자동 폴백한다(`code-scan.js:187-190`)" | 실제 위치는 `code-scan.js:198-202` | **불일치 — 교정 대상** |
| M-2 | `tools.md:240` "파일의 @header 기록 위치 판정 (4단: inline_exists/readonly_repo/legacy_no_header/manifest)" | 실제 `reason` 4값은 `readonly_repo`/`inline_exists`/`new_file`/`legacy_no_header`이며 `manifest`는 `write_to` 값 | **불일치 — 교정 대상** |
| M-3 | `header-standard.md:219` "`files` 키는 `dir` 실제 파일 목록과 **집합 일치**" | v1.3.3부터 `exclude`/`excludePatterns`로 걸러진 파일은 이미 부분집합 (`code-scan.js:1583-1584`) | **선행 불일치 — 보강④로 정합** |
| M-4 | `header-standard.md:209` `exclude` "8커맨드 탐색에는 미적용" | 유지 (조회 8커맨드는 `config.exclude`만 사용) | 일치 |
| M-5 | `header-rules.md:26` "code-map이 없는 프로젝트는 ①이 성립하지 않으므로 결과는 항상 `inline`" | 현행 코드와 일치 | 신 계약으로 무효화 예정 |

#### 2.6.3 영향 범위

`header-standard.md` §7은 스키마 SSOT이므로 `code-map-hook.js:10`의 note("header-standard.md §7 5필드와 동기 유지")와도 연결된다. `header-rules.md:131`의 저커버리지 폴백 기준(합산 커버리지 30%)은 F-003의 모드별 커버리지로 재정의된다.

---

### F-007: 테스트 자산 + 골든 재캡처

#### 2.7.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 테스트 | `opal/tools/code-scan/tests/test-resolve-header.js` (35KB) | 5단 상속·headerSource 스위치·스키마 | 수정 |
| 테스트 | `opal/tools/code-scan/tests/test-target.js` (9KB) | 4단 판정·readonly 우선순위 | 수정 |
| 테스트 | `opal/tools/code-scan/tests/test-validate.js` (42KB) | 6종 위반·커버리지·`--changed` | 수정 |
| 테스트 | `opal/tools/code-scan/tests/test-scaffold.js` (14KB) | 매니페스트 생성·멱등 | 수정 |
| 테스트 | `opal/tools/code-scan/tests/test-discover.js` (10KB) | 초안 생성·`readonly` 필드 | 수정 |
| 테스트 | `opal/tools/code-scan/tests/test-regression.js` (14KB) | 골든 8커맨드·픽스처 격리·문서 검사 | 수정 |
| 테스트 | `opal/tools/code-scan/tests/test-hook.js` (11KB) | hook 조기 이탈 9단 | 수정 |
| 테스트 | `opal/tools/code-scan/tests/test-feature.js` (5KB) | cross-scope 조회 | 수정 |
| 테스트 | `opal/tools/code-scan/tests/test-header-source.js` | 게이트·2택·CLI 플래그 | **신규** |
| 테스트 | `opal/tools/code-scan/tests/test-scope-filter.js` | `isInScope` 5지점 일관성·우선순위 | **신규** |
| 환경 | `tests/fixtures/**/.opal/code-scan.json` (20개) | 픽스처 설정 | 수정 |
| 환경 | `tests/fixtures/mixed-scope/` | 혼재 디렉토리 픽스처 (생존 스코프 2개) | **신규** |
| 환경 | `tests/fixtures/mixed-scope-ambiguous/` | `scope_ambiguous` 전용 트리 | **신규** |
| 환경 | `tests/fixtures/golden/*.{json,txt}` (8개) | 골든 출력 | 재캡처 |
| 환경 | `tests/fixtures/golden/README.md` | 캡처 규약·080 재캡처 diff 근거 | **신규** |

#### 2.7.2 현재 구현

테스트는 `node --test "opal/tools/code-scan/tests/*.js"`로 실행한다(`tasks/077-.../AGENTIC-LOG.md:23,30` — Node v25.8.2에서 디렉토리 인자는 MODULE_NOT_FOUND, glob 형태만 동작). 077 최종 결과는 100/100 pass(`tasks/077-.../DONE.md:40`).

전 픽스처(20개)의 `.opal/code-scan.json`에 `headerSource` 키가 **없다**. 골든 8종은 `legacy-repo`(code-map 부재, `extensions: [".py",".ts"]`) 기준으로 캡처되었고 `test-regression.js:64-83`이 바이트 동일을 단언한다.

`test-resolve-header.js:74-83`의 `makeHeaderSourceFixture(value)`는 `codemap-repo`를 임시 디렉토리에 복제한 뒤 `.opal/code-scan.json`에 `headerSource` 값을 실제로 기재하는 오버레이 헬퍼다. 077 TS-044/045/046이 이미 이것을 사용하고 있어(`:358`, `:384`, `:407`) 신규·재배치 테스트가 그대로 재사용할 수 있다 — **픽스처 트리를 새로 만들 필요가 없는 근거**다(§3.7.2).

#### 2.7.3 영향 범위

게이트 도입 즉시 **픽스처 20개 전량이 exit 1**이 되어 100 케이스가 붕괴한다(H-9). 픽스처 갱신이 RED 테스트보다 **먼저** 완료되어야 한다.

---

## 3. 기능별 설계

> 인용 형식: `(→ D-N §N)` 단축 참조는 §8.3 참조 문서 테이블에 대응한다.

### F-001: `headerSource` 스키마 재정의 + 전 명령 차단 게이트

#### 3.1.1 파일 변경 계획

**신규 생성** — 없음 (전량 기존 파일 내 함수 추가)

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/code-scan/code-scan.js` | 도구 | `DEFAULT_CONFIG.headerSource` `'auto'` → `null`, `HEADER_SOURCE_VALUES` 상수 신설 | `code-scan.js:45` |
| 2 | `opal/tools/code-scan/code-scan.js` | 도구 | `parseArgs`에 `--header-source <inline\|manifest>` 추가 | `code-scan.js:131-173` (→ D-7 D-1) |
| 3 | `opal/tools/code-scan/code-scan.js` | 도구 | `loadConfig` — 값 판정 제거, 원문 그대로 반환 + `configError` 구분 | `code-scan.js:193-213` |
| 4 | `opal/tools/code-scan/code-scan.js` | 도구 | `resolveHeaderSource` 신설(유일 판정 지점) + `main()` 게이트 삽입 + `buildCtx` 확장 | `code-scan.js:1696-1733`, `:535-539` |
| 5 | `opal/tools/code-scan/code-scan.js` | 도구 | `errorExit` — stdout JSON + **stderr 사람용 메시지** 동시 출력 | `code-scan.js:474-477` (→ H-1) |
| 6 | `opal/tools/code-scan/code-scan.js` | 도구 | `USAGE` — 옵션·설정 예시·종료 코드 갱신 | `code-scan.js:61-110` |

#### 3.1.2 함수 시그니처 · 데이터 모델

**(A) 상수**

```js
// 값 도메인 2택 — 'auto'는 제거되었다 (D-3)
const HEADER_SOURCE_VALUES = ['inline', 'manifest'];
const HEADER_SOURCE_DOC = '~/.opal/references/header-standard.md §7';
```

[MUST] TASK.md §확정된 설계 방향 D-3: "`auto` **완전 제거** → `inline` / `manifest` **2택**" — 혼재를 허용하는 값이 남으면 이번 결정이 무력화된다.

**(B) `loadConfig` 반환 계약 변경 — 판정하지 않고 싣기만 한다**

```js
/**
 * @returns {{
 *   extensions: string[], exclude: string[], excludePatterns: string[],
 *   scopes: Record<string, NormalizedConfigScope>,
 *   headerSource: string|null,        // 원문 그대로. 미설정이면 null. 유효성 판정 안 함.
 *   configPresent: boolean,           // .opal/code-scan.json 존재 여부
 *   configError: 'config_parse_failed'|null
 * }}
 * loadConfig는 절대 process.exit / throw 하지 않는다.
 */
function loadConfig(projectRoot)
```

[MUST] 이 계약은 hook fail-safe의 전제다 — `code-map-hook.js:120`이 `main()`을 거치지 않고 `loadConfig`를 직접 호출하므로, 여기서 종료하면 PostToolUse fail-safe(`code-map-hook.js:151-158`)가 붕괴한다 (→ H-2).

기존 `catch { return DEFAULT_CONFIG; }`(`code-scan.js:210`)는 파싱 실패와 파일 부재를 구분하지 못했다. 신규 `configError: 'config_parse_failed'`로 분리하여 게이트가 "미설정"과 "깨진 설정"을 다른 메시지로 안내한다 (→ F-12② 에러 메시지 품질).

**(C) 모드 확정 — `main()` 전용, 유일한 판정 지점**

> 초판의 `resolveGlobalHeaderSource`에서 **`Global` 접두를 뗀다.** 스코프 층이 사라져 대비되는 다른 층이 없으므로 "전역"이 정보를 더하지 않고, 오히려 "전역 외의 층이 있다"는 오해를 남긴다.

```js
/**
 * 이 실행의 headerSource를 확정한다 — 도구 전체에서 **유일한** 모드 판정 지점이다.
 * CLI 플래그 > 전역 config 순으로 병합하고 유효성을 판정한다(2층).
 * @returns {{ok:true, value:'inline'|'manifest'} |
 *           {ok:false, error:'header_source_unset'|'header_source_invalid'|'code_scan_config_invalid', detail:string}}
 */
function resolveHeaderSource(config, opts)
```

판정 순서:

| # | 조건 | 결과 |
|---|------|------|
| ① | `config.configError === 'config_parse_failed'` | `code_scan_config_invalid` |
| ② | `opts.headerSource` 존재 + 유효 | `{ok:true, value: opts.headerSource}` |
| ③ | `opts.headerSource` 존재 + 무효 | `header_source_invalid` (detail = 입력값, `where: 'cli'`) |
| ④ | `config.headerSource == null` | `header_source_unset` |
| ⑤ | `config.headerSource === 'auto'` 또는 그 외 무효값 | `header_source_invalid` (detail = 값, `where: 'config'`) |
| ⑥ | 그 외 | `{ok:true, value: config.headerSource}` |

`auto`는 ⑤로 흡수되되 **전용 마이그레이션 힌트**를 붙인다 (F-1 AC "`auto` 지정 시 명시 거부(에러 코드 반환)").

**(D) 확정값 전파 — 파일 단위 판정 함수는 두지 않는다**

**우선순위 계약 (2층)**

| 순위 | 소스 | 근거 |
|------|------|------|
| ① | `--header-source <inline\|manifest>` CLI 플래그 | D-1 — 비대화형 1회 지정 수단 |
| ② | `.opal/code-scan.json` 전역 `headerSource` | D-4 |

[MUST] TASK.md §요구사항 F-1 AC: "**한 실행의 모드는 실행당 1값으로 확정되며 파일·스코프에 따라 달라지지 않는다**(우선순위 2층 — CLI 플래그 > 전역 config)"

따라서 **`effectiveHeaderSource(relPath, ctx)` 같은 파일 단위 판정 함수를 만들지 않는다.** `resolveHeaderSource`(아래 (C))가 `main()`에서 1회 판정한 값이 실행 전체의 모드이며, 소비자는 `ctx.headerSource`를 **상수처럼** 읽는다.

> **설계 판단 근거**: 스코프별 오버라이드를 기각한 이유는 그것이 값을 갖는 유일한 상황이 "한 저장소 안에서 스코프마다 기록 소스가 다른" 혼재 케이스인데, 소유자가 그 케이스는 존재할 수 없다고 판단했기 때문이다(2026-08-02). 전역이 `manifest`면 프로젝트 전체가 매니페스트 기록이고 `inline`이어도 마찬가지이므로 스코프별 재선언은 의미가 없다. [MUST] `opal/core/PRINCIPLES.md` §2: "Solve only the current requirement. No speculative abstraction or unrequested flexibility."
>
> 부수 효과로 **함수 1개·우선순위 1층·index 스키마 키 1개·테스트 2건이 통째로 사라진다**(§12 축소 요약). 판정 지점이 `main()` 1곳으로 수렴하므로 "어느 파일이 어느 모드인가"를 추적할 필요 자체가 없어진다.

**전파 경로** — `ctx`에 확정값을 싣는 것은 **유지한다**(hook 포함 전 소비자가 모드를 알아야 한다). `buildCtx(projectRoot, config)`(`code-scan.js:535-539`)의 시그니처를 `buildCtx(projectRoot, config, headerSource)`로 확장하고, `code-scan.js` 내 호출 5곳(`scanAll:799` · `cmdDiscover:1161` · `cmdScaffold:1314` · `cmdTarget:1400` · `cmdValidate:1449`)을 갱신한다. hook은 `buildCtx`를 쓰지 않고 `ctx`를 직접 조립하므로(`code-map-hook.js:127`) 별건으로 갱신한다.

**(E) 게이트 삽입 — `main()`**

```js
function main() {
  const opts = parseArgs(process.argv);
  if (opts.command === 'help')    { console.log(USAGE); return; }   // 게이트 이전 — 무변경
  if (opts.command === 'version') { console.log(`code-scan v${VERSION}`); return; }

  const projectRoot = findProjectRoot();
  const config = loadConfig(projectRoot);

  // ── 전 명령 차단 게이트 (D-5) ────────────────────────────────
  const hs = resolveHeaderSource(config, opts);
  if (!hs.ok) return errorExit(hs.error, { detail: hs.detail, fix: ..., doc: HEADER_SOURCE_DOC });
  const mode = hs.value;   // 이 실행의 모드 — 이후 변하지 않는다 (ctx.headerSource로 전파)
  //  ↑ [MUST] 변수명은 `mode`다. `headerSource`가 아니다 — TS-070 화이트리스트(§3.1.5)가
  //    허용 3구간 밖의 `headerSource` 토큰을 전부 위반으로 잡기 때문이며, 이는 의도된 규율이다.
  //    "결과를 담은 변수"와 "판정하는 코드"를 이름으로 구분해 봉인을 날카롭게 유지한다.
  // ─────────────────────────────────────────────────────────────

  const commands = { ... };   // 13커맨드 — 무변경
  ...
}
```

[MUST] TASK.md §확정된 설계 방향 D-5: "차단 범위 = **code-scan 전 명령**" (조회 8커맨드 포함). `help`/`version`은 커맨드가 아니라 메타 출력이므로 게이트 이전에 반환되며(`code-scan.js:1699-1700` 기존 구조가 그대로 이 요건을 만족한다), 이는 "설정 없는 사용자가 사용법을 볼 수 있어야 한다"는 F-12② 취지와도 부합한다.

**(F) 에러 출력 계약 — stdout + stderr 동시**

```js
function errorExit(code, extra) {
  const payload = Object.assign({ ok: false, error: code }, extra || {});
  console.log(JSON.stringify(payload));                    // 기계 소비자 (기존 codeMapErrorExit 계약 보존)
  process.stderr.write(renderHumanError(payload) + '\n');  // 사람 + brain-tool detail 전달 경로
  process.exit(1);
}
```

`header_source_unset` 렌더 예시:

```
stdout: {"ok":false,"error":"header_source_unset","detail":".opal/code-scan.json에 headerSource가 없습니다","fix":"\"headerSource\": \"inline\" 또는 \"manifest\"를 .opal/code-scan.json에 추가하거나 --header-source <inline|manifest>로 실행하세요","doc":"~/.opal/references/header-standard.md §7"}
stderr: code-scan: header_source_unset — .opal/code-scan.json에 headerSource가 없습니다
        해결: "headerSource": "inline" 또는 "manifest"를 .opal/code-scan.json에 추가하거나 --header-source <inline|manifest>로 실행하세요
        근거: ~/.opal/references/header-standard.md §7
```

> **stderr 병기가 필수인 이유**: `brain_tool.py:790-792`가 실패 시 `stderr`만 detail에 담는다. stdout에만 쓰면 `brain-tool sync-header`가 `header_parse_failed, detail="code-scan exit=1, stderr="`라는 **사유 없는 실패**를 노출한다. stderr 병기로 `brain_tool.py`를 수정하지 않고 F-12③ AC를 충족한다 (→ D-6:790-792, H-1).

기존 `codeMapErrorExit`(`code-scan.js:474-477`)은 `errorExit`로 통합하고, 기존 호출 지점 3곳(`:1167` `index_exists` · `:1315` `index_missing` · `:1347` `mirror_collision` · `:1730` `CodeMapFatalError`)은 stderr 1줄이 추가로 나가는 것 외 stdout 계약이 동일하다.

#### 3.1.3 환경 변경

해당 없음 (Node 표준 모듈만 사용 — [MUST] TASK.md §제약 조건).

#### 3.1.4 배치/마이그레이션

`auto`를 사용 중인 프로젝트는 `header_source_invalid` + 마이그레이션 힌트로 안내된다. 자동 변환은 하지 않는다 — 어느 쪽으로 통일할지는 도메인 결정이며 도구가 추측하면 자산이 오염된다 (보강⑤와 동일 원리, → D-7 개선 A 보강 ⑤).

#### 3.1.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | F-2 AC | 기능 | `headerSource` 없는 픽스처에서 13커맨드 전부 exit 1 + stdout `{"ok":false,"error":"header_source_unset",...}` |
| TS-002 | F-2 AC | 기능 | 동일 상황에서 stderr에 해결 방법 1줄 + 근거 문서 경로가 포함된다 |
| TS-003 | F-1 AC | 기능 | `"headerSource": "auto"` 설정 시 `header_source_invalid` + `detail: "auto"` + 마이그레이션 힌트, exit 1 |
| TS-004 | F-1 AC | 기능 | `--header-source inline`으로 미설정 프로젝트에서 `scan`이 exit 0 |
| TS-005 | F-1 AC | 기능 | **[재정의 — 부정 단언]** `index.json` `scopes.{name}`에 `headerSource: "manifest"`를 넣어도 **무시**되고 전역 `inline`이 적용된다(`write_to: inline`) + 안내 1줄. 삭제하지 않고 부정 단언으로 남긴 이유는 §3.7.2 결정과 동일 — "스코프 오버라이드가 없다"는 것 자체가 지켜야 할 계약이고, 검증이 없으면 나중에 조용히 되살아난다 |
| TS-006 | F-1 AC | 기능 | **[재정의 — 우선순위 2층]** 전역 `manifest` + `--header-source inline` → **CLI 승리**로 실행 전체가 `inline`. 같은 실행 안의 서로 다른 파일·스코프가 모두 동일 모드를 보고한다(실행당 1값 확정, F-1 AC) |
| TS-007 | F-2 AC | 회귀 | `--help` / `--version`은 미설정 상태에서도 exit 0 |
| TS-008 | F-12② | 기능 | 깨진 JSON `.opal/code-scan.json` → `code_scan_config_invalid` (미설정과 구분) |
| TS-009 | F-1 AC · §3.1.2 (C) ③ | 기능 | **CLI 무효값** — `--header-source bogus` → `header_source_invalid` + `where: 'cli'` + `detail: "bogus"` + exit 1. 마이그레이션 힌트는 **붙지 않는다**(`auto` 특례와 구분) |
| TS-065 | F-1 AC · §3.1.2 (C) ⑤ | 기능 | **config 임의 무효값** — `"headerSource": "bogus"` → `header_source_invalid` + `where: 'config'` + `detail: "bogus"` + exit 1, stdout JSON 무오염. 077 TS-046(`bogus` → `auto` 폴백 + exit 0, `test-resolve-header.js:406-419`)의 **반전 승계처** |
| TS-066 | D-3 | 산출물 검사 | **소스 자산 `auto` 잔존 0건** — `code-scan.js`의 `DEFAULT_CONFIG`(`:40-46`)·`USAGE`(`:61-110`, 설정 예시 `:108`)·`loadConfig`(`:193-213`)에 `auto` 리터럴 0건. **예외**: `header_source_invalid`의 마이그레이션 힌트 문자열(§3.1.4)은 `auto`를 언급해야 하므로 허용하며, 그 1개소만 매칭되어야 한다 |

| TS-069 | F-1 AC · §3.2.2 (E) | 기능 | **[보정1 — config 측 부정 단언]** 전역 `headerSource: inline` + `.opal/code-scan.json`의 `scopes.{name}` 객체에 `headerSource: "manifest"` → **`inline`이 적용**되고(`target` → `write_to: inline`) stderr에 안내 1줄(`config_scope_header_source`, 중복 0). TS-005(`index.json` 측)와 **대칭 쌍**을 이룬다 |
| TS-070 | D-2 · §12 | 산출물 검사 | **[모드 판정 지점 봉인]** 허용 영역 3개(`resolveHeaderSource`·`loadConfig`·`parseArgs`) **밖**에서 `headerSource` 토큰이 허용 3형태 (a)(b)(c) 외로 등장하면 **FAIL**. 구조분해·별칭 우회까지 검출한다 — 절차는 아래 4단계 |
| TS-075 | F-7 AC · §3.2.2 (E) | 기능 | **[보정4]** `include`/`exclude`가 `string[]`이 아닌 입력 거부 — `index.json` 측은 `invalid_index`, `code-scan.json` 측은 `code_scan_config_invalid`. 검사 케이스 3종: 문자열 스칼라(`"a/*.ts"`) · 원소에 비문자열 혼입(`["a", 1]`) · 객체(`{}`) |

**TS-070 검사 절차 — 블랙리스트가 아니라 화이트리스트**

> **초판(리터럴 blacklist) 기각 근거**: `config.headerSource`/`opts.headerSource` 리터럴만 막으면 구조분해(`const { headerSource } = config;`)·별칭(`const cfg = config; cfg.headerSource`)·간접 참조로 **우회된다**. 정규식으로 별칭을 추적하는 것은 신뢰할 수 없으므로 검사 방식을 뒤집는다 — **허용된 영역과 허용된 형태를 열거하고, 그 밖에서 `headerSource` 토큰이 나타나면 실패**로 판정한다. 우회 수단은 전부 "허용 형태가 아닌 토큰 출현"으로 귀결되므로 자동으로 잡힌다.

**절차 (재현 가능한 4단계 — 구현 워커가 그대로 실행한다)**

```bash
# ── ① 허용 영역 3개의 줄 범위를 확정한다 (중괄호 깊이 계산, 정규식 아님)
#     대상 함수: resolveHeaderSource / loadConfig / parseArgs
#     시작줄 S = `^function <name>(` 매치 줄
#     종료줄 E = S부터 문자열·주석을 제외하고 { } 깊이를 세어 0으로 복귀하는 줄
node -e '
const fs=require("fs"), src=fs.readFileSync("opal/tools/code-scan/code-scan.js","utf8").split("\n");
function range(name){
  const S=src.findIndex(l=>new RegExp("^function\\s+"+name+"\\s*\\(").test(l));
  let d=0,E=S;
  for(let i=S;i<src.length;i++){
    const l=src[i].replace(/\/\/.*$/,"").replace(/(["'`]).*?\1/g,"");
    for(const ch of l){ if(ch==="{")d++; else if(ch==="}")d--; }
    if(i>S && d===0){ E=i; break; }
  }
  return [S+1,E+1];   // 1-based
}
console.log(JSON.stringify({
  resolveHeaderSource: range("resolveHeaderSource"),
  loadConfig: range("loadConfig"),
  parseArgs: range("parseArgs")
}));'

# ── ② 검사 대상 = 파일 전체 − 위 3구간
# ── ③ 대상 영역에서 토큰 `headerSource`가 등장하는 모든 줄을 수집한다
#      (문자열 리터럴 내부·주석 내부는 제외 — 에러 메시지·USAGE·안내 문구는 검사 대상이 아니다)
# ── ④ 수집된 각 줄이 아래 허용 3형태 중 하나가 아니면 FAIL
```

**허용 영역 3개** (이 안에서는 어떤 형태든 허용)

| 영역 | 이유 |
|------|------|
| `resolveHeaderSource` 본문 | **유일한 판정 지점**(§3.1.2 (C)) |
| `loadConfig` 본문 | 원문을 싣기만 한다 — 판정하지 않는다(§3.1.2 (B) `headerSource: string\|null` "유효성 판정 안 함") |
| `parseArgs` 본문 | CLI 토큰을 `opts.headerSource`에 담기만 한다(`code-scan.js:131-173`) |

**허용 영역 밖의 허용 3형태** (이 외 = FAIL)

| # | 형태 | 예시 |
|---|------|------|
| (a) | `ctx.headerSource` **읽기**(대입 좌변 아님) | `const mode = ctx.headerSource;` · `if (ctx.headerSource === 'inline')` |
| (b) | `buildCtx` 시그니처·본문의 **파라미터 전달** | `function buildCtx(projectRoot, config, headerSource)` · `return { projectRoot, config, codeMap, headerSource };` |
| (c) | `DEFAULT_CONFIG`의 **프로퍼티 키 정의 1회** | `headerSource: null` (`code-scan.js:45`) |

**금지 예시 (전부 FAIL — 우회 수단 포함)**

| # | 코드 | 검출 방식 |
|---|------|----------|
| 1 | `const mode = config.headerSource \|\| 'inline';` | 허용 형태 아님 → FAIL |
| 2 | `const { headerSource } = config;` | **구조분해** — 허용 형태 아님 → FAIL (초판 blacklist는 놓쳤다) |
| 3 | `const cfg = config; ... cfg.headerSource` | **별칭** — 허용 형태 아님 → FAIL (초판 blacklist는 놓쳤다) |
| 4 | `ctx.headerSource = 'manifest';` | (a)는 **읽기만** 허용 — 대입 좌변이므로 FAIL |

**허용 예시 (전부 PASS)**

| # | 코드 | 근거 |
|---|------|------|
| 1 | `const mode = ctx.headerSource;` (`resolveHeader` 내부) | (a) 확정값 읽기 |
| 2 | `if (ctx.headerSource === 'inline') { /* scaffold no-op */ }` | (a) |
| 3 | `buildCtx(projectRoot, config, mode)` 호출 5곳 | (b) 파라미터 전달 — **인자 변수명은 `mode`**. 중간 전달 함수(`scanAll`·`cmdDiscover`·`cmdScaffold`·`cmdTarget`·`cmdValidate`)의 파라미터명도 `headerSource`를 쓰지 않는다 |
| 4 | `` `headerSource가 없습니다` `` (에러 메시지 문자열) | ③에서 문자열 리터럴 제외 |

> 이 검사는 F-8이 필터 판정을 `isInScope` 1곳으로 봉인한 것(TS-013)과 **동형의 집행 장치**다. 다만 TS-013은 함수 호출 여부만 보면 되는 반면 모드 축은 **값 접근**이라 우회 표면이 넓으므로, 화이트리스트가 필수다.

> 이 검사는 F-8이 필터 판정을 `isInScope` 1곳으로 봉인한 것(TS-013)과 **동형의 집행 장치**다. §12가 "모드 판정 지점이 `main()` 1곳으로 수렴"을 이번 축소의 구조적 이득으로 선언했으므로, 선언만 두고 집행을 두지 않으면 후속 워커가 파일 단위 재계산을 되살려도 아무도 모른다 — [MUST] `opal/core/PRINCIPLES.md`: "Enforce, don't just advise: if a rule must always hold, a tool gates it — not prose."

> **무효값 3경로 구분** — `auto`(TS-003)는 **특례 경로**로 전용 마이그레이션 힌트가 붙고, CLI 무효값(TS-009)과 config 임의 무효값(TS-065)은 **일반 경로**로 힌트가 붙지 않는다. 세 경로 모두 에러 detail에 `where`(`cli`/`config`/`index`)를 실어 값의 출처를 식별 가능하게 한다 (§3.1.2 (C) ③⑤ · §3.2.2 (E) index 검증).

---

### F-002: `scopes` 객체 형식 정규화 + 단일 필터 계약

#### 3.2.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/code-scan/code-scan.js` | 도구 | `isExcluded` → `matchesAnyPattern` 개명 + 호출 4곳 갱신 | `code-scan.js:234-241`, 호출 `:312,:1236,:1441,:1475` |
| 2 | `opal/tools/code-scan/code-scan.js` | 도구 | `normalizeConfigScope`/`normalizeIndexScope`/`isInScope`/`resolveScopeIn` 신설 | 개선 A 보강① (→ D-7) |
| 3 | `opal/tools/code-scan/code-scan.js` | 도구 | `getSearchPaths` 반환 타입 변경 + `discoverFiles` 필터 적용 (지점①) | `code-scan.js:279-314` |
| 4 | `opal/tools/code-scan/code-scan.js` | 도구 | `collectDirsWithCodeFiles` 필터 적용 (지점②) | `code-scan.js:1236` |
| 5 | `opal/tools/code-scan/code-scan.js` | 도구 | `listCodeFilesInDir` 필터 적용 (지점③) | `code-scan.js:1441` |
| 6 | `opal/tools/code-scan/code-scan.js` | 도구 | `cmdValidate --changed` 필터 적용 (지점④) | `code-scan.js:1466-1477` |
| 7 | `opal/tools/code-scan/code-scan.js` | 도구 | `resolveScope` → `resolveScopeIn` 위임 + 우선순위 (지점⑤ 경유) | `code-scan.js:557-569` |
| 8 | `opal/tools/code-scan/code-scan.js` | 도구 | `loadCodeMap` 스키마 검증 확장 (`include`/`exclude`/`headerSource`) | `code-scan.js:518-531` |
| 9 | `opal/tools/code-scan/code-scan.js` | 도구 | `inferScopes` 객체 형식 승계 + include 추론 금지 | `code-scan.js:1093-1110` |
| 10 | `opal/tools/code-scan/code-scan.js` | 도구 | `cmdValidate:1479` 스코프 존재 확인 — 정규화 객체 대응 | `code-scan.js:1479` |

#### 3.2.2 함수 시그니처 · 데이터 모델

**(A) 정규화 — 두 레지스트리, 하나의 내부 형태**

사용자 대면 키는 파일별로 다르지만(`code-scan.json` → `path`, `index.json` → `root`), 내부 정규화 형태는 **`root`로 통일**한다. 두 레지스트리 모두 **모드 선언 키를 갖지 않는다** — `include`/`exclude`는 *파일 집합 필터*이지 *모드 선언*이 아니며, 이 구분이 전역 단일 키 결정과 개선 A가 공존하는 근거다.

```js
/** .opal/code-scan.json  scopes[name]: string | {path, include?, exclude?} */
function normalizeConfigScope(raw, scopeName) {
  //   "opal/"                                   → { root: "opal/",  include: [], exclude: [] }
  //   { path: "opal/", include: ["a/*.ts"] }     → { root: "opal/",  include: ["a/*.ts"], exclude: [] }
  //
  //   모드 선언 키는 여기에도 없다 — 사용자가 실제로 손대는 파일이 code-scan.json이므로
  //   스코프 객체에 headerSource를 넣는 시도가 가장 잦을 지점이다. 조용히 버리지 않고 안내한다.
  if (hasOwn(raw, 'headerSource')) {
    deprecationOnce('config_scope_header_source',
      `scopes."${scopeName}".headerSource는 지원하지 않습니다 — 이 키는 무시됩니다. ` +
      'headerSource는 .opal/code-scan.json의 **최상위** 키 1개로만 설정합니다(전역 단일 키, Task 080).');
  }
}

/** .opal/code-map/index.json  scopes[name]: {root, anchors?, stripPrefix?, include?, exclude?} */
function normalizeIndexScope(raw) {
  //   → { root, anchors: [], stripPrefix: [], include: [], exclude: [] }
  //   모드 선언 키는 없다 — headerSource는 전역 1개뿐이다(§3.1.2 (D)).
  //   readonly 키가 존재하면 값과 무관하게 무시하고 deprecated 안내 1회 (F-004, §3.4.2)
}
```

[MUST] TASK.md §확정된 설계 방향 개선 A: "`scopes` 값에 객체 형식 추가 — `{path, include: [], exclude: []}`. 문자열은 동일 형태로 정규화(하위호환)" — 사용자 대면 키는 TASK 원문 그대로 `path`를 사용한다.

**(B) 단일 필터 계약 — `isInScope`**

```js
/**
 * 스코프 필터의 유일한 판정 함수. 5개 적용 지점이 전부 이것만 호출한다.
 * @param {string} relPath   프로젝트 루트 기준 POSIX 파일 경로 (예: "opal/tools/x.js")
 * @param {{include: string[], exclude: string[]}} scopeDef  정규화된 스코프 정의
 * @returns {boolean}
 */
function isInScope(relPath, scopeDef) {
  const fileName = relPath.slice(relPath.lastIndexOf('/') + 1);
  const inc = (scopeDef && scopeDef.include) || [];
  if (inc.length > 0 && !matchesAnyPattern(relPath, fileName, inc)) return false;  // ① 화이트리스트 우선
  const exc = (scopeDef && scopeDef.exclude) || [];
  if (exc.length > 0 &&  matchesAnyPattern(relPath, fileName, exc)) return false;  // ② 그 다음 블랙리스트
  return true;
}
```

- **패턴 문법**: 기존 `excludePatterns`와 동일 — `*`(경로 구분자 제외 임의) · `**`(임의) · `?`(1문자), `/` 포함 시 전체 상대 경로 대조, 아니면 파일명 대조 (`code-scan.js:219-238`).
- **순서 계약**: `include`가 비어 있지 않으면 화이트리스트가 먼저 적용되고, 통과분에 대해서만 `exclude`가 적용된다 ([MUST] TASK.md §개선 A: "`include`가 있으면 화이트리스트 우선, 그 다음 `exclude`").
- **`matchesAnyPattern`**: 기존 `isExcluded`의 개명. 부정 의미를 이름에서 제거해 include·exclude 양쪽에 동일 함수를 재사용한다 — [MUST] `opal/core/PRINCIPLES.md` §2: "Remove a duplicated existing pattern before introducing a new one."

**(C) 5개 적용 지점 배선 — 지점별 명세**

| # | 지점 | 함수 | 스코프 레지스트리 | 배선 방법 |
|---|------|------|-----------------|----------|
| ① | 열거 | `discoverFiles` (`:298-314`) | `config.scopes` | `getSearchPaths`가 `{abs, scopeDef}`를 반환 → 각 파일에 `isInScope(rel, scopeDef)` 적용 |
| ② | scaffold 열거 | `collectDirsWithCodeFiles` (`:1222-1246`) | `index.scopes` | `:1236` 직후 `if (!isInScope(rel, scopeDef)) continue;` |
| ③ | validate 구조 패스 | `listCodeFilesInDir` (`:1433-1446`) | `index.scopes` | 인자에 `scopeDef` 추가, `:1441` 직후 동일 판정 |
| ④ | `--changed` | `cmdValidate` (`:1466-1477`) | `config.scopes` | 기존 3필터 뒤에 `resolveScopeIn(rel, config.scopes)` → 스코프 있으나 `isInScope` 실패 시 `skipped.push({file, reason:'out_of_scope'})` |
| ⑤ | target | `decideTarget` (`:755-791`) | `index.scopes` (부재 시 `config.scopes`) | **신규 배선** — `decideTarget` 선두에서 `isFilteredOutOfScope` 호출(아래 (C-bis)). `resolveScope` 위임만으로는 불충분하다 |

> **⑤가 나머지 4지점과 다른 점**: ①~④는 이미 `isExcluded`를 호출하던 자리에 스코프 필터를 **추가**하는 작업이지만, `decideTarget`은 `isExcluded`·`hasExcludedSegment` 호출이 **0건**이다(`code-scan.js:755-791` 실측 — 필터 유틸 3종 중 어느 것도 호출하지 않는다). 즉 `target`은 F-8이 말하는 5지점 중 **유일하게 필터가 아예 없던 공백 지점**이며, 배선은 "대체"가 아니라 "신규 도입"이다. `resolveScope`가 `isInScope`로 후보를 거르더라도 그 결과는 "어느 스코프에 귀속되는가"일 뿐 "이 파일이 관리 대상인가"를 표현하지 못한다 — 스코프 밖 파일과 필터 탈락 파일이 모두 `scoped === null`로 뭉개지기 때문이다 (→ H-13).
>
> [MUST] TASK.md §요구사항 F-8 AC: "열거·scaffold 열거·`validate` 구조 패스·`--changed`·`target` **5개 지점이 모두 이 함수만 호출**하고, 중복 판정 로직이 존재하지 않는다"

**(C-bis) `target` 스코프 필터 탈락 반환 계약 (신설)**

```js
/**
 * root에는 속하지만 스코프 필터에서 탈락했는지 판정한다.
 * 필터 판정 자체는 isInScope에만 위임하고, root 매칭은 resolveScopeIn과 동일한 rootMatches를 공유한다
 * (중복 판정 로직 없음 — [MUST] PRINCIPLES.md §2).
 * @param {string} relPath
 * @param {Record<string, {root, include, exclude}>} scopes  정규화된 스코프 레지스트리
 * @returns {boolean}  root 매칭 스코프가 1개 이상 있고, 그 전부가 isInScope 실패일 때만 true
 */
function isFilteredOutOfScope(relPath, scopes)
```

```js
function decideTarget(fileRel, ctx) {
  const relPath = (fileRel || '').split(path.sep).join('/');
  const scopes = ctx.codeMap.present ? ctx.codeMap.index.scopes : ctx.config.scopes;
  if (isFilteredOutOfScope(relPath, scopes)) {
    return { write_to: 'none', reason: 'out_of_scope' };   // 모드 판정보다 먼저
  }
  ... // 이하 §3.3.2 (B) 모드 직결 판정
}
```

**반환 계약 결정표**

| 항목 | 결정 | 근거 |
|------|------|------|
| 발동 조건 | ① 스코프 레지스트리가 비어 있지 않고 ② 파일이 어떤 스코프의 `root`에는 속하며 ③ root 매칭 스코프 **전부**가 `isInScope` 실패 | root에 애초에 속하지 않는 파일과 스코프 미설정 프로젝트는 **기존 동작(모드 직결)을 유지** — include/exclude 미사용 프로젝트의 `target` 결과가 바뀌지 않아야 골든·회귀가 보존된다 (→ H-13, TS-037) |
| `write_to` | **`'none'`** (신규 3번째 값) | "여기에 쓰라"가 아니라 "쓸 자리가 없다"가 사실이다. `'inline'`으로 폴백하면 `manifest` 모드에서 소스 혼재가 재발하고, `'manifest'`로 두면 매니페스트 경로가 없는 지시가 나가 워커가 쓸 자리를 못 찾는다 |
| `reason` | **`'out_of_scope'`** | §1.5 `reason` 도메인이 2값 → **3값**으로 확장된다. 판정 근거가 실제로 3종(모드 2 + 필터 1)이므로 값 축소 원칙(§3.3.2 (B))과 모순되지 않는다 |
| 부가 필드 | `scope`/`manifest`/`key` **모두 생략** | 관리 대상이 아니므로 기록 위치가 존재하지 않는다 |
| exit code | **0** | 오류가 아니라 정상 판정이다. 에러 코드(exit 1)는 `header_source_unset` 계열 전용으로 유지한다 |
| hook 영향 | **로직 변경 0** | `code-map-hook.js:136`이 `decision.write_to !== 'manifest'`면 무출력 이탈하므로 `'none'`도 자동으로 조용히 처리된다. `buildWarning`(`:63-75`)은 `reason`을 문자열 출력만 하므로 값 확장에 영향받지 않는다 |
| `cmdTarget` 출력 | `write_to: none` / `reason: out_of_scope` 2줄 (`manifest` 줄 없음 — `code-scan.js:1405` 기존 조건부 출력이 그대로 커버) | - |
| 레지스트리 선택 | `index.scopes`가 있으면 그것, 없으면 `config.scopes` | 그 프로젝트에서 실제로 파일 집합을 지배하는 레지스트리를 따른다 (§3.2.2 (C) ①~④의 레지스트리 배정과 동형) |

**`getSearchPaths` 반환 타입 변경**:

```js
/** @returns {Array<{abs: string, scopeDef: {include,exclude}|null}>} */
function getSearchPaths(projectRoot, config, opts)
```

- `opts.scope` 지정 시 → `[{abs: resolve(root), scopeDef}]`
- `opts.targetPath` 지정 시 → `[{abs: resolve(targetPath), scopeDef: null}]` — **명시 경로에는 필터를 적용하지 않는다**
- 스코프 미설정 시 → `[{abs: projectRoot, scopeDef: null}]`

> **`targetPath` 필터 면제 근거**: `pm-review-gate.md:53`의 PM Gate 8번은 `code-scan scan <file> --json`으로 단일 파일을 조회한다. 명시 지정 파일에 스코프 필터를 적용하면 include 밖 파일이 "결과 없음 = @header 누락"으로 오판정된다. 명시 지정은 사용자 의도이므로 필터보다 우선한다 (→ D-4 §검토 절차 8).

**(D) 스코프 중복 우선순위 — `resolveScopeIn` (보강③)**

```js
/**
 * 정규화된 스코프 레지스트리에서 relPath의 소속 스코프를 판정한다.
 * @param {string} relPath
 * @param {Record<string, {root, include, exclude}>} scopes
 * @returns {{name: string, scope: object} | null}
 * @throws {CodeMapFatalError} 'scope_ambiguous' — 동률 root에서 두 스코프의 include가 모두 매칭될 때
 */
function resolveScopeIn(relPath, scopes)
```

판정 순서:

| # | 단계 | 규칙 |
|---|------|------|
| ① | root 매칭 | `root === ''` 이면 전체 매칭, 아니면 `relPath === root \|\| relPath.startsWith(root + '/')` (기존 `:561` 로직 보존) |
| ② | 스코프 필터 | `isInScope(relPath, scope)` 실패 후보는 **탈락** (include 밖 / exclude 대상) |
| ③ | 최장 root 승리 | 기존 `:563-566` 보존 |
| ④ | 동률 + include 매칭 1개 | 그 스코프 승리 |
| ⑤ | 동률 + include 매칭 2개 이상 | **`scope_ambiguous` 에러** (exit 1, `detail`에 스코프명 2개) |
| ⑥ | 동률 + include 매칭 0개 | 이름 사전순 (기존 `:564` 보존 — include 미사용 프로젝트 동작 불변) |

[MUST] TASK.md §개선 A 보강 ③: "동률에서는 **include 매칭 스코프 승리**, 둘 다 매칭되면 명시 에러" — 사전순 우연 판정을 남기지 않는다.

`resolveScope(relPath, index)`는 `module.exports:1745`로 노출된 공개 인터페이스이므로 **시그니처를 유지**하고 내부에서 `resolveScopeIn(relPath, index.scopes)`에 위임한다 (→ H-4 회귀 방어).

**(E) 스코프 스키마 검증 — 두 파일 공통** (`code-scan.js:518-531` index 분 / `:193-213` config 분)

| 파일 | 필드 | 규칙 | 위반 시 |
|------|------|------|--------|
| `index.json` | `scopes[].root` | 기존 — 비어 있지 않은 string 필수 | `invalid_index` (기존) |
| `index.json` | `scopes[].include` / `.exclude` | 존재하면 `string[]`. 배열이 아니거나 원소에 비문자열이 섞이면 거부 | `invalid_index` (TS-075) |
| `index.json` | `scopes[].readonly` | **허용 키 아님**. 존재하면 값과 무관하게 무시 + deprecated 안내 1회 (거부하지 않는다 — 즉시 파괴 금지) | (F-004) |
| `index.json` | `scopes[].headerSource` | **허용 키 아님**(전역 전용). 무시 + 안내 1회 | (TS-005) |
| **`code-scan.json`** | `scopes[].path` | 문자열 필수(문자열 축약형은 그대로 `path`로 승격) | `code_scan_config_invalid` |
| **`code-scan.json`** | `scopes[].include` / `.exclude` | 존재하면 `string[]` | `code_scan_config_invalid` (TS-075) |
| **`code-scan.json`** | `scopes[].headerSource` | **허용 키 아님**(전역 전용). 무시 + 안내 1회 — "최상위 키로 설정하세요" | (TS-069) |

> **`code-scan.json` 행이 필수인 이유**: 사용자가 실제로 편집하는 파일은 `.opal/code-scan.json`이고 `.opal/code-map/index.json`은 `discover`가 생성하는 자산이다. `index.json` 쪽만 막으면 **전역 단일 키 결정이 가장 되살아나기 쉬운 문을 열어둔 채**로 두게 된다 — `normalizeConfigScope`가 미지 키를 조용히 버리므로 사용자는 설정이 먹은 줄 안다.

**안내 중복 계약** — `deprecationOnce(key, message)`는 **키별로 실행당 1회**다.

| 안내 키 | 트리거 | 횟수 |
|---------|--------|------|
| `index_scope_readonly` | `index.json` 스코프에 `readonly` | 실행당 1회 (스코프가 여럿이어도 1회) |
| `index_scope_header_source` | `index.json` 스코프에 `headerSource` | 실행당 1회 |
| `config_scope_header_source` | `code-scan.json` 스코프에 `headerSource` | 실행당 1회 |

- 세 키는 **독립**이다 — 두 파일 모두에 문제가 있으면 최대 3줄이 나간다. "합쳐서 1회"로 묶지 않는 이유는 사용자가 고쳐야 할 **파일이 다르기** 때문이다(안내를 합치면 어느 파일을 고쳐야 할지 알 수 없다).
- 전량 **stderr** 출력이며 stdout JSON을 오염시키지 않는다 (`brain_tool.py:793` `json.loads(result.stdout)` 보호). 동일 키의 중복 출력은 0건이어야 한다 (TS-031, TS-069).

**(F) `inferScopes` 갱신** (`:1093-1110`) — 보강⑤

```js
// config.scopes 파생 경로 (:1096-1099)
scopes[name] = {
  root: normalized.root.endsWith('/') ? normalized.root : normalized.root + '/',
  anchors: [], stripPrefix: [],
  include: normalized.include,     // 사람이 code-scan.json에 명시한 값은 그대로 승계
  exclude: normalized.exclude,
};
// 디렉토리 스캔 파생 경로 (:1104-1108)
scopes[e.name] = { root: e.name + '/', anchors: [], stripPrefix: [], include: [], exclude: [] };
```

[MUST] TASK.md §개선 A 보강 ⑤: "**`discover`는 `include`를 추론하지 않는다** — 빈 배열로 두고 사람이 채우는 필드로 규정" — 어느 파일이 우리 것인지는 도메인 지식이며, 도구 추측은 오탐을 자산에 고정시킨다. 명시값 승계는 추론이 아니므로 허용한다(명시 근거의 보존).

`readonly: false` 기입(`:1098`, `:1107`)은 제거한다 (F-6 AC).

#### 3.2.3 환경 변경

`.opal/code-scan.json` 스키마 확장 (문자열·객체 양립). 기존 문자열 설정은 무수정 동작 (F-7 AC).

```jsonc
{
  "scopes": {
    "framework": "opal/",                                     // 문자열 — 하위호환
    "order-svc": { "path": "svc/shared/",                     // 객체 — 신규
                   "include": ["Order*.java", "order/**"],
                   "exclude": ["*.generated.java"] }
  },
  "headerSource": "inline"
}
```

#### 3.2.4 배치/마이그레이션

`exclude`/`include` 변경 후에는 `scaffold` 재실행이 필요하다 — 기존 등재 파일이 `orphan`으로 남는다 (`code-scan-management.md:54` 기존 안내를 `include`까지로 확장).

#### 3.2.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-010 | F-7 AC | 회귀 | 기존 문자열 `scopes` 픽스처 20종이 무수정으로 동작 |
| TS-011 | F-7 AC | 기능 | 객체 형식 `{path, include, exclude}`가 스키마 검증 통과 |
| TS-012 | F-8 AC | 통합 | 혼재 디렉토리 픽스처에서 **5개 지점이 동일 파일 집합**을 판정 (열거·scaffold·구조 패스·`--changed`·`target`) |
| TS-013 | F-8 AC | 산출물 검사 | `code-scan.js`에 스코프 필터 판정 로직이 `isInScope` 외 0곳 (grep 기반) |
| TS-014 | F-9 AC | 기능 | include로 걸러진 형제 파일이 매니페스트에 없어도 `files_key_removed` 미집계 |
| TS-015 | F-9 AC | 기능 | 필터에 걸리지 않는 미등재 파일은 여전히 `files_key_removed`로 검출 |
| TS-016 | F-10 AC | 기능 | root 동일 + include만 다른 두 스코프에서 파일이 올바른 스코프로 귀속 |
| TS-017 | F-10 AC | 기능 | 양쪽 include 매칭 설정은 `scope_ambiguous`로 exit 1 |
| TS-018 | F-10 AC | 회귀 | include 미사용 tiebreak 픽스처(order-a/order-b) 판정 결과 불변 |
| TS-019 | F-8 AC | 기능 | `scan <file>` 명시 경로는 include 밖이어도 결과를 반환 (PM Gate 보호) |
| TS-035 | F-8 AC | 기능 | 스코프 필터에 탈락한 파일의 `target`이 `{write_to:'none', reason:'out_of_scope'}` + exit 0을 반환하고 `scope`/`manifest`/`key` 필드가 없다 (→ (C-bis)) |
| TS-036 | F-8 AC | 회귀 | 위 파일에 hook 이벤트를 주입하면 stdout 0바이트 · exit 0 (`code-map-hook.js:136` 이탈 경로 보존) |
| TS-037 | F-8 AC | 회귀 | include/exclude 미사용 프로젝트(`legacy-repo`)·스코프 밖 파일의 `target` 결과가 필터 도입 전과 동일 (`out_of_scope` 오발동 0건) |

---

### F-003: 작성·검증 경로의 모드 존중

#### 3.3.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/code-scan/code-scan.js` | 도구 | `resolveHeader` — `ctx.headerSource` 직접 사용 + `auto` 분기 제거 | `code-scan.js:688-701` |
| 2 | `opal/tools/code-scan/code-scan.js` | 도구 | `decideTarget` — 4단 판정 → 필터 1단 + 모드 직결 2단 = **3값 도메인** | `code-scan.js:755-791` |
| 3 | `opal/tools/code-scan/code-scan.js` | 도구 | `cmdScaffold` — `inline` 모드 no-op + 사유 보고 | `code-scan.js:1313-1393` |
| 4 | `opal/tools/code-scan/code-scan.js` | 도구 | `cmdValidate` — 모드별 커버리지·검출기 분기 | `code-scan.js:1488-1641` |

#### 3.3.2 함수 시그니처 · 핵심 로직

**(A) `resolveHeader` (조회) — 2택 직결**

```js
function resolveHeader(filePath, ctx) {
  const mode = ctx.headerSource;      // 'inline' | 'manifest' — 실행당 확정값(§3.1.2 (D))

  if (mode === 'inline') {
    return extractHeader(filePath);   // _source 키를 붙이지 않는다 — 조회 8커맨드 골든 보존 지점
  }
  // mode === 'manifest' — 인라인은 읽지 않는다
  if (!ctx.codeMap.present) { warnOnce('manifest 모드이나 .opal/code-map/index.json이 없습니다'); return null; }
  ... // 기존 :709-750 매니페스트 4단(files → package → layerRules → domains) 그대로
}
```

**계약 변화 — 상속 단수 재정의**:

| 모드 | 참조 tier | `_source` 도메인 |
|------|----------|-----------------|
| `inline` | ① 인라인 **단독** | (`_source` 키 없음 — 기존 `:697-701` 계약 보존) |
| `manifest` | ② `files` → ③ `package` → ④ `layerRules` → ⑤ `domains` **4단** | `file` / `package` / `rule` / `domain` |

077의 "5단 상속 + 인라인 단독 승리"는 `auto` 모드의 서술이었다(`header-standard.md:189-191`). 2택 전환으로 tier①과 tier②~⑤는 **모드에 의해 상호 배타**가 되며, "인라인 단독 승리"라는 병합 규칙 자체가 소멸한다(모드가 소스를 고르므로 경합이 없다). 이 변화는 `header-standard.md` §7 전면 재작성 대상이다 (Step 11).

`manifest` 모드 + index.json 부재는 **비차단 stderr 경고 1줄**로 처리한다 — 차단 조건을 늘리면 D-5 범위를 넘어서므로 의도적으로 fail-soft를 택한다 (→ H-12).

**(B) `decideTarget` (작성 판정) — 모드 직결**

```js
function decideTarget(fileRel, ctx) {
  const relPath = (fileRel || '').split(path.sep).join('/');
  const mode = ctx.headerSource;      // 실행당 확정값

  if (mode === 'inline') return { write_to: 'inline', reason: 'header_source_inline' };

  const out = { write_to: 'manifest', reason: 'header_source_manifest' };
  const scoped = ctx.codeMap.present ? resolveScope(relPath, ctx.codeMap.index) : null;
  if (scoped) {
    const mp = mirrorPathForDir(posixDirname(relPath), scoped.name, scoped.scope);
    if (!mp.skipped) {
      out.scope = scoped.name;
      out.manifest = `${CODE_MAP_DIR}/${scoped.name}/${mp.mirrorRel}.json`;
      out.key = path.basename(relPath);
    }
  }
  return out;
}
```

**`reason` 도메인 변경 (계약 변경)**:

| 구 값 | 신 값 | 처리 |
|-------|-------|------|
| `readonly_repo` | **소멸** — 전역값에 따라 `header_source_inline` 또는 `header_source_manifest` | `readonly`는 흡수되지 않고 **무시**된다. 스코프 예외가 없으므로 `readonly` 전용 reason이 존재할 자리가 없다 (F-004, 2026-08-02 결정) |
| `inline_exists` / `new_file` | `header_source_inline` | 파일 상태는 더 이상 판정 근거가 아니다 — 모드가 단독으로 결정한다 |
| `legacy_no_header` | `header_source_manifest` | 동상 |
| (없음) | **`out_of_scope`** | 신설 — 스코프 필터 탈락. 모드 판정보다 **먼저** 반환된다 (§3.2.2 (C-bis)) |

따라서 최종 도메인은 `write_to` 3값(`inline`/`manifest`/`none`) × `reason` 3값(`header_source_inline`/`header_source_manifest`/`out_of_scope`)이며, 실제 조합은 3쌍으로 닫힌다.

> **설계 판단**: 구 4값 중 **모드에서 파생되는 3값을 2값으로 병합**한 이유는 F-3 AC("`manifest` 설정 하에서 신규 파일·인라인 보유 파일 **모두** `write_to: manifest`")가 파일 상태 분기를 무의미하게 만들기 때문이다. 판정 근거가 아닌 값을 `reason`에 남기면 "이 값이 판정에 관여한다"는 오해를 재생산한다 — [MUST] `opal/core/PRINCIPLES.md` §2 Simplicity First.
>
> 여기에 **판정 근거가 실재하는** `out_of_scope` 1값이 별도 축(스코프 필터, §3.2.2 (C-bis))에서 추가되어 **최종 도메인은 3값**이다. "축소"는 모드 축 내부의 이야기이고 `out_of_scope`는 다른 축이므로 두 결정은 상충하지 않는다 — 문서(§3.6.2)와 테스트(TS-053·TS-068)는 반드시 **최종 3값**을 기준으로 삼는다.
> `code-map-hook.js:70`은 `reason`을 문자열로 출력할 뿐 값에 의존하지 않으므로 hook 로직 변경은 불필요하다.

**(C) `cmdScaffold` — `inline` 모드 no-op**

```js
function cmdScaffold(projectRoot, config, opts) {
  const ctx = buildCtx(projectRoot, config, mode);   // 파라미터 전달 — 지역 변수명은 `mode`(§3.1.2 (C) 주석)
  if (ctx.headerSource === 'inline') {
    const result = { ok: true, created: 0, updated: 0, unchanged: 0, added: [], pruned: [], stale: [],
                     skipped: [{ reason: 'header_source_inline',
                                 detail: 'headerSource가 inline이므로 매니페스트를 생성하지 않습니다' }] };
    // .opal/code-map/ 하위에 어떤 파일도 쓰지 않는다
    output → exit 0
  }
  if (!ctx.codeMap.present) return errorExit('index_missing');   // 기존 :1315
  ... // 기존 로직
}
```

`skipped` 배열은 이미 결과 스키마에 존재하므로(`code-scan.js:1389` `skipped: []`) 신규 필드 추가 없이 사유를 실어 보낸다. exit 0을 유지하는 것은 "설정대로 동작했다"는 뜻이기 때문이다 (실패가 아니다).

**(D) `cmdValidate` — 모드별 판정**

| 항목 | `inline` 모드 | `manifest` 모드 |
|------|--------------|----------------|
| `covered` 판정 (`:1496`) | `inlineHeader !== null` | `fe !== null` |
| `coverage.inline` / `.manifest` | `inlineCount` / 0 | 0 / `manifestCount` |
| `coverage.covered` | 해당 모드 값 (합산 폐기) | 동상 |
| `uncovered.sub` 분류 (`:1497-1504`) | 항상 `classifyUncovered` (git 2분류) | 기존 그대로 — 관리 매니페스트 있으면 `no_entry`, 없으면 git 2분류 |
| `incomplete` 필수 필드 검사 (`:1509-1513`) | 유지 (`resolveHeader` 결과 기준) | 유지 |
| `conflict/inline_shadowed` (`:1515-1517`) | 유지 — **양 모드 공통** | 유지 |
| `draft` (`:1519-1524`) | **미적용** (매니페스트 전용 개념) | 유지 |
| `exports_not_found` (`:1526-1536`) | 유지 | 유지 |
| 구조 패스 (`:1540-1624`) | **스킵** + `.opal/code-map/` 매니페스트 존재 시 stderr 안내 1줄 | 유지 |
| 결과 스키마 | `result.headerSource: 'inline'` 추가 | `result.headerSource: 'manifest'` 추가 |

> **`conflict/inline_shadowed`를 양 모드에서 유지하는 근거**: 이 위반의 실질은 "한 파일에 두 소스가 동시에 기재됨"이며, 이는 이 태스크가 없애려는 상태 그 자체다. 모드가 무엇이든 검출 가치가 있다. 위반 코드·서브 값을 그대로 두어 소비자 스키마 churn을 피한다.
>
> **구조 패스를 `inline` 모드에서 스킵하는 근거**: `orphan`/`worker_scope_violation`은 전부 매니페스트 무결성 위반이다. `inline` 모드는 매니페스트를 만들지도 읽지도 않으므로(F-4·본 절 (A)) 검사 대상이 없다. 스킵 대신 안내 1줄로 "설정과 자산이 어긋나 있다"는 사실만 노출한다.

**차단 정책은 불변**: `uncovered:pre_existing`만 비차단(`code-scan.js:1638-1641`), 나머지는 차단, exit 2 (`:1656`).

#### 3.3.3 환경 변경

해당 없음.

#### 3.3.4 배치/마이그레이션

`manifest` 모드로 전환한 프로젝트는 `scaffold` 실행 후 워커가 `files[].description`을 채워야 커버리지가 회복된다. 인라인→매니페스트 자동 이관(주석 삽입·역주입)은 [MUST] TASK.md §명확화 결과 §범위 "**제외**: `inline ↔ manifest` 자동 이관"에 따라 범위 밖이다.

#### 3.3.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-020 | F-3 AC | 기능 | `manifest` 모드에서 신규 파일·인라인 보유 파일 모두 `write_to: manifest`, `reason: header_source_manifest` |
| TS-021 | F-3 AC | 기능 | `inline` 모드에서 항상 `write_to: inline`, `reason: header_source_inline` |
| TS-022 | F-3 AC | 기능 | `manifest` 모드 `target` 결과에 `scope`/`manifest`/`key`가 정확히 채워진다 |
| TS-023 | F-4 AC | 기능 | `inline` 설정 프로젝트에서 `scaffold` 실행 시 `.opal/code-map/` 하위 파일 생성 0건 + `skipped[0].reason === 'header_source_inline'` + exit 0 |
| TS-024 | F-5 AC | 통합 | 동일 픽스처를 두 모드로 `validate` → 커버리지 분모·분자가 각 모드 소스만 반영 |
| TS-025 | F-5 AC | 기능 | `manifest` 모드에서 인라인 부재가 위반으로 집계되지 않는다 |
| TS-026 | F-5 AC | 기능 | `inline` 모드에서 매니페스트 부재가 위반으로 집계되지 않는다 (구조 패스 스킵) |
| TS-027 | F-3/F-5 | 회귀 | `uncovered:pre_existing` 비차단·나머지 차단·exit 2 정책 불변 |
| TS-028 | H-12 | 기능 | `manifest` 모드 + index.json 부재 → stderr 경고 1줄, exit 0 (비차단) |
| TS-029 | F-5 AC | 기능 | `validate --json` 결과에 `headerSource` 필드가 포함된다 |
| TS-072 | F-1 AC · F-3 AC | 통합 | **[보정3(a) — 실행당 1값]** `mixed-scope`에서 전역 `inline` 1회 실행 시 **두 스코프(`order-svc`·`ship-svc`)의 4파일이 모두 동일 모드**를 보고한다 — `target`이 4건 모두 `write_to: inline`/`reason: header_source_inline`. 스코프가 다르다는 이유로 갈리는 파일 0건 |
| TS-073 | F-1 AC · F-3~F-5 | 통합 | **[보정3(b) — 4경로 일치]** 같은 실행에서 `target`·`scaffold`·`validate`·`scan` **4경로의 모드가 일치**한다. 전역 `inline`이면 ① `target` 4건 전부 `inline` ② `scaffold`가 no-op(`skipped[0].reason === 'header_source_inline'`, `.opal/code-map/` 생성 0건) ③ `validate`의 `result.headerSource === 'inline'` + 커버리지 분모·분자가 인라인만 반영 ④ `scan --json` 결과에 `_source` 키 0건 |
| TS-074 | F-1 AC · D-2 | 통합 | **[보정3(c) — 전역값만 뒤집기]** `mixed-scope`의 `.opal/code-scan.json`에서 **`headerSource` 한 값만** `inline` → `manifest`로 바꾸고 재실행하면 **5경로가 함께 뒤집힌다** — `target` 4건 전부 `manifest`, `scaffold`가 매니페스트 생성, `validate.headerSource === 'manifest'` + 커버리지가 매니페스트만 반영, `scan`이 매니페스트 유래 헤더 반환, hook이 `manifest` 경고 경로 진입. **두 스코프 중 어느 쪽도 예외가 되지 않는다** |

---

### F-004: `readonly` 제거(무시 + 안내)

#### 3.4.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/code-scan/code-scan.js` | 도구 | `normalizeIndexScope`에서 `readonly` 키 **무시** + deprecated 안내 1회 (흡수하지 않는다) | `code-scan.js:506-533` |
| 2 | `opal/tools/code-scan/code-scan.js` | 도구 | `decideTarget`에서 `readonly` 분기 제거 | `code-scan.js:761-770` |
| 3 | `opal/tools/code-scan/code-scan.js` | 도구 | `inferScopes` `readonly: false` 기입 제거 | `code-scan.js:1098`, `:1107` |
| 4 | `opal/tools/code-scan/code-scan.js` | 도구 | `cmdDiscover` `note` 문자열 갱신 | `code-scan.js:1199` |

#### 3.4.2 하위호환 계약 — **무시 + 안내** (흡수 아님)

```js
// normalizeIndexScope 내부 — 값과 무관하게 무시하고 안내만 한다
// [MUST] deprecationOnce(key, message) 2인자 — 키는 §3.2.2 (E) 안내 중복 계약 3키 표와 일치해야 한다
if (hasOwn(raw, 'readonly')) {
  deprecationOnce('index_scope_readonly',                       // ← 키 ①
    'scopes[].readonly는 제거되었습니다(Task 080) — 이 키는 무시됩니다. ' +
    '기록 소스는 .opal/code-scan.json의 전역 "headerSource"("inline" 또는 "manifest")로 설정하세요 ' +
    '(근거: ~/.opal/references/header-standard.md §7).');
}
// 스코프 전용 모드 키도 마찬가지 — 전역 1개뿐이므로 스코프에 실려 있으면 무시 + 안내
if (hasOwn(raw, 'headerSource')) {
  deprecationOnce('index_scope_header_source',                  // ← 키 ②
    'scopes[].headerSource는 지원하지 않습니다 — 이 키는 무시됩니다. ' +
    'headerSource는 .opal/code-scan.json의 최상위 키 1개로만 설정합니다(전역 단일 키, Task 080).');
}
```

> **키 인자가 필수인 이유**: `deprecationOnce`가 1인자면 "이미 한 번 안내했는가"를 메시지 문자열로 판별하게 되어, index 측 2키(`readonly`·`headerSource`)가 서로를 덮어쓰거나 중복 출력된다. 세 안내는 **사용자가 고쳐야 할 위치가 각각 다르므로**(index 스코프 / index 스코프 / config 스코프) 독립 키로 각 1회 출력되어야 한다 — §3.2.2 (E) 안내 중복 계약과 동일 계약이며, 그 표의 3키 이름을 그대로 쓴다.

**`deprecationOnce` 시그니처 (3호출 지점 공통)**

```js
const _deprecationSeen = new Set();
/**
 * @param {string} key      §3.2.2 (E) 3키 중 하나 — 중복 판별의 유일한 기준
 * @param {string} message  stderr로 나갈 사람용 문구 (stdout JSON 오염 금지)
 */
function deprecationOnce(key, message) {
  if (_deprecationSeen.has(key)) return;
  _deprecationSeen.add(key);
  process.stderr.write(`code-scan: [deprecated] ${message}\n`);
}
```

| 호출 지점 | 키 | 근거 |
|-----------|----|------|
| `normalizeIndexScope` — `readonly` | `index_scope_readonly` | 위 스텁 ① |
| `normalizeIndexScope` — `headerSource` | `index_scope_header_source` | 위 스텁 ② |
| `normalizeConfigScope` — `headerSource` | `config_scope_header_source` | §3.2.2 (A) |

| 입력 | 결과 | 안내 |
|------|------|------|
| `readonly: true` | **무시** — 전역 `headerSource`가 그대로 적용된다 (`manifest`로 해석하지 **않는다**) | deprecated 1줄 (stderr, 실행당 1회) |
| `readonly: false` | 무시 | deprecated 1줄 |
| `scopes[].headerSource` | 무시 — 전역값 적용 | 안내 1줄 |
| 위 키 없음 | 무동작 | 없음 |

[MUST] TASK.md §명확화 결과 §제약 ①: "`readonly: true`를 만나도 실행이 실패하지 않는다 — **무시 + 안내 1회**(즉시 파괴 금지). 단 **`manifest`로 해석하지 않는다**(전역 단일 키 결정, 2026-08-02)"

[MUST] TASK.md §요구사항 F-6 AC: "`readonly: true`만 있는 기존 index로 실행해도 **전역 `headerSource`가 그대로 적용되고**(스코프 예외 없음) 안내 1줄이 출력되며, 신규 `discover` 산출물에는 `readonly`가 포함되지 않는다. 안내는 실행당 1회이며 stdout JSON을 오염시키지 않는다"

> **초판 대비 방침 변경**: 초판은 `readonly: true`를 스코프 단위 `headerSource: 'manifest'`로 **흡수**했다. 전역 단일 키 결정으로 **흡수할 자리 자체가 사라졌으므로** 무시로 바뀐다. 이는 기존 `readonly: true` 프로젝트의 `target` 결과를 바꾸는 동작 변화이며(전역이 `inline`이면 `manifest` → `inline`), §1.5 제약② 파기 범위 안에서 수용된다 — 안내 1줄이 그 변화를 사용자에게 알리는 유일한 접점이므로 문구에 전역 설정 방법을 반드시 포함한다.

**안내 출력 채널**: stderr. stdout은 `--json` 소비자(brain-tool·PM Gate)의 파이프이므로 오염시키지 않는다 (`brain_tool.py:793` `json.loads(result.stdout)`).

`cmdDiscover` `note` 신규 문자열:

```
'OWNER REVIEW REQUIRED — headerSource/anchors/stripPrefix/include 확인 후 status를 reviewed로 변경'
```

#### 3.4.3 환경 변경 / 3.4.4 배치·마이그레이션

해당 없음 (기존 index.json 무수정 동작).

#### 3.4.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-030 | F-6 AC | 기능 | **[반전]** `readonly: true` 스코프 + 전역 `headerSource: inline` → `target`이 `write_to: inline`(`reason: header_source_inline`). **`manifest`가 아니다** — 전역값이 그대로 적용된다 |
| TS-031 | F-6 AC | 기능 | 위 실행 시 stderr에 deprecated 안내 **1줄**(실행당 1회, 중복 출력 0) + 안내 문구에 전역 `headerSource` 설정 방법 포함 + **stdout JSON 무오염** |
| TS-032 | F-6 AC | 기능 | 신규 `discover` 산출물의 `scopes[]`에 `readonly` 키 0건 |
| TS-071 | D-2 · §12 | 기능 | **[보정2]** 신규 `discover` 산출물의 `scopes[]`에 **`headerSource` 키 0건** — TS-032의 대응물. `discover`가 모드 키를 산출물에 심으면 그 순간부터 스코프 오버라이드가 자산에 고정된다(보강⑤ "도구 추측은 오탐을 자산에 고정시킨다"와 동일 논리, → D-7 §개선 A 보강 ⑤) |
| TS-033 | F-6 AC | 기능 | **[재정의]** `readonly: true` 스코프 + 전역 `headerSource: manifest` → `write_to: manifest`. TS-030과 짝을 이뤄 "**결과가 `readonly`가 아니라 전역값을 따른다**"를 두 방향으로 고정한다(한 방향만 보면 우연 일치와 구분되지 않는다) |
| TS-034 | F-6 AC | 산출물 검사 | `code-scan.js`에 `readonly`를 판정 근거로 쓰는 코드 0건 (`note` 문자열 포함 잔존 0. deprecated 안내 문자열의 키 이름 언급은 예외) |

---

### F-005: 소비자 파급 대응

#### 3.5.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/code-scan/code-map-hook.js` | 도구 | 조기 이탈 ⑤.5 신설 — headerSource 미설정/무효 시 무출력 exit 0 | `code-map-hook.js:116-122` |
| 2 | `opal/tools/code-scan/code-map-hook.js` | 도구 | `ctx` 조립에 `headerSource` 추가 | `code-map-hook.js:127` |
| 3 | `.opal/code-scan.json` | 환경 | `"headerSource": "inline"` 추가 | TASK F-12① |
| 4 | `.gitignore` | 환경 | `!.opal/code-scan.json` 예외 1줄 추가 (`.gitignore:6` 다음) | §3.5.3 결정 (→ H-14) |
| 5 | `opal/core/references/harness/pm-review-gate.md` | 문서 | 검토 절차 8번 — `readonly` 서술 제거·모드별 커버리지·미설정 대응 절차 | `pm-review-gate.md:52-62` |

#### 3.5.2 hook fail-safe 설계

```js
// ⑤ index.json 부재 → 무출력 exit 0 (기존 :116-117)
const codeMap = loadCodeMap(projectRoot);
if (!codeMap.present || codeMap.error) return;

// ⑤.5 headerSource 미설정·무효 → 무출력 exit 0 (신설, F-12⑤)
const config = loadConfig(projectRoot);
const mode = config.headerSource;
if (mode !== 'inline' && mode !== 'manifest') return;
if (mode === 'inline') return;          // 인라인 모드는 경고할 대상 자체가 없다

// ⑥ 확장자 (기존 :122)
```

[MUST] TASK.md §D-4·D-5 동반 필수 작업 ⑤: "**hook은 예외 — 미설정에서도 무출력 exit 0**" — PostToolUse hook의 fail-safe 계약(077 PM-7). 매 편집마다 에러가 뜨면 세션이 망가진다.

이 설계는 두 겹으로 계약을 지킨다: ① `loadConfig`가 절대 종료하지 않는다(§3.1.2 (B)) ② hook이 명시적으로 조기 이탈한다. `code-map-hook.js:151-158`의 전 경로 try/catch + 무조건 `process.exit(0)`은 3차 방어로 그대로 유지한다.

> `inline` 모드에서 즉시 이탈하는 것은 최적화가 아니라 계약이다 — `inline` 모드의 `decideTarget`은 항상 `write_to: 'inline'`을 반환하므로(§3.3.2 (B)) 기존 ⑦단(`:136`)에서 어차피 이탈한다. 상위에서 끊어 `resolveScope`·`mirrorPathForDir` 연산을 생략한다.

#### 3.5.3 이 저장소 설정

```jsonc
// .opal/code-scan.json  (변경 후)
{
  "headerSource": "inline",      // ← 신규. 이 저장소는 인라인 @header 자산을 보유한다
  "scopes": { "framework": "opal/", "console-fe": "dashboard/frontend/src/", "console-be": "dashboard/backend/" },
  "extensions": [...],           // 무변경
  "exclude": [...],              // 무변경
  "excludePatterns": []
}
```

**gitignore 파급 — 결정: `.gitignore` 예외를 추가한다 (채택)**

문제: `.gitignore:2`가 `.opal/*`를 무시하고 `.opal/brain/`·`.opal/code-map/`만 예외 처리하므로(`.gitignore:3-6`), `.opal/code-scan.json`은 git 추적 대상이 아니다(`git ls-files` 결과 없음 / `git check-ignore -v` → `.gitignore:2:.opal/*`). D-4 도입 후 이 파일은 **저장소가 동작하기 위한 필수 파일**이 되므로, 추적되지 않으면 **신규 clone·CI 환경에서 이 저장소 자신이 즉시 `header_source_unset`으로 전 명령 차단**된다 — brain-tool `sync-header`·PM Gate 8번·hook 소비자가 동시에 멎는다.

```diff
  .opal/*
  !.opal/brain/
  !.opal/brain/**
  !.opal/code-map/
  !.opal/code-map/**
+ !.opal/code-scan.json
```

| 판단 축 | 내용 |
|---------|------|
| 채택 근거 ① | D-4/D-5로 이 파일이 **선택 설정 → 필수 계약**으로 성격이 바뀐다. 필수 계약을 추적하지 않는 것은 저장소를 미완성 상태로 배포하는 것과 같다 |
| 채택 근거 ② | 선례가 있다 — `.gitignore:3-6`이 이미 `.opal/brain/`·`.opal/code-map/`을 "버전 관리해야 할 OPAL 프로젝트 자산"으로 예외 처리한다. 동일 성격의 3번째 항목이다 |
| 채택 근거 ③ | 내용에 비밀정보가 없다 — `scopes`/`extensions`/`exclude`/`excludePatterns`/`headerSource`뿐이며 전부 저장소 상대 경로다(현행 파일 실측) |
| 채택 비용 | **077 TS-055 반전** — `test-regression.js:126-127`이 "`.opal/code-scan.json`은 계속 무시되어야 함(exit 0 기대)"을 단언한다. 예외 채택 시 이 단언이 `exit 1`(비무시)로 뒤집힌다. 비용은 Step 2(RED 재작성)에 흡수되며 §1.5 계약 변경표에 명시했다 (→ H-14) |
| 기각안 검토 | "생성 규약만으로 대응"은 **새 프로젝트용 예방**이지 이 저장소의 즉시 대응이 아니다. clone 직후 PM이 code-scan을 첫 호출할 때까지 저장소는 계속 막혀 있다 |

**병행 조치(영속 예방)**: `code-scan-management.md` §생성 시점의 자동 생성 규약에도 `headerSource`를 포함시킨다(**Step 10**). 예외 추가는 *이 저장소*를 고치고, 생성 규약은 *다음 프로젝트*를 고친다 — 둘은 대체재가 아니라 보완재다.

#### 3.5.4 `brain-tool sync-header` 대응 — **무수정으로 성립함 (확정)**

`brain_tool.py`는 **수정하지 않는다.** 이는 목표가 아니라 코드로 확정된 결론이다. 후속 워커는 이 판단을 재검토하지 말고 그대로 따른다.

**성립 근거 (줄번호 확정)**:

| # | 코드 사실 | 근거 |
|---|----------|------|
| ① | subprocess 실행 시 `capture_output=True`이므로 **stdout과 stderr가 모두 캡처**된다 | `brain_tool.py:788` |
| ② | 실패 판정은 `result.returncode != 0 or not result.stdout.strip()` — 게이트가 exit 1을 내므로 첫 조건에서 확실히 걸린다 | `brain_tool.py:790` |
| ③ | 실패 detail이 `f"code-scan exit={result.returncode}, stderr={result.stderr.strip()}"`로 조립된다 — **stderr 내용이 그대로 실린다** | `brain_tool.py:791-792` |
| ④ | 따라서 §3.1.2 (F)가 게이트 메시지를 stderr에 병기하면, 별도 코드 변경 없이 사유가 최종 사용자에게 도달한다 | ①+②+③ |

기대 출력:

```
brain-tool sync-header  →  {"ok":false,"command":"sync-header","error":"header_parse_failed",
                            "detail":"code-scan exit=1, stderr=code-scan: header_source_unset — ...해결: ...근거: ..."}
```

> **역으로, stderr 병기를 생략하면 이 무수정 성립이 깨진다.** 기존 `codeMapErrorExit`(`code-scan.js:474-477`)처럼 stdout에만 쓰면 `result.stderr`가 빈 문자열이 되어 `detail: "code-scan exit=1, stderr="`라는 사유 없는 실패가 노출된다. 즉 §3.1.2 (F)의 stderr 병기는 편의가 아니라 **F-12③ AC를 충족하는 유일한 무수정 경로**다.

검증은 실제 subprocess 실행으로 수행한다(L2) — mock으로는 stderr 전달 경로를 확인할 수 없다(TS-045).

#### 3.5.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-040 | F-12⑤ | 기능 | 미설정 트리에 hook 이벤트 주입 → stdout 0바이트 · exit 0 |
| TS-041 | F-12⑤ | 기능 | `headerSource: "auto"`(무효) 트리에서도 hook stdout 0바이트 · exit 0 |
| TS-042 | F-12⑤ | 회귀 | `manifest` 모드 + 미갱신 매니페스트 → hook 경고 정상 출력 (077 TS-038 계약 보존) |
| TS-043 | F-12⑤ | 기능 | `inline` 모드에서 hook stdout 0바이트 · exit 0 |
| TS-044 | F-12① | 기능 | 이 저장소 루트에서 8커맨드 exit 0 (`test-regression.js:97-101` TS-052 계승) |
| TS-045 | F-12③ | 통합 | 미설정 임시 트리에서 `brain-tool sync-header` 실행 → detail에 `header_source_unset` 문자열 포함 (`brain_tool.py` 무수정 상태에서) |
| TS-046 | §3.5.3 | 기능 | `git check-ignore .opal/code-scan.json` **exit 1**(비무시) — 077 TS-055 반전 |
| TS-047 | §3.5.3 | 회귀 | `git check-ignore .opal/code-map/index.json` exit 1 유지 (`test-regression.js:122-124` 기존 단언 불변) |

---

### F-006: 규칙 문서 5종 + `docs/` 3종

#### 3.6.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/core/references/header-standard.md` | 문서 | §7 전면 개정 — 2택 모드·상속 단수 재정의·`readonly` deprecated·`include`/`exclude` 필드·`dir` 부분집합 | `:184-259` |
| 2 | `opal/core/references/harness/header-rules.md` | 문서 | 기록 위치 판정표 4단 → 모드 직결·커버리지 합산 → 모드별·저커버리지 폴백 기준 | `:14-55`, `:131` |
| 3 | `opal/core/references/pm/code-scan-management.md` | 문서 | `headerSource` 관리 재작성·생성 규약에 `headerSource` 포함·M-1 인용 교정 | `:10-31`, `:63-73`, `:80` |
| 4 | `opal/core/references/harness/pm-review-gate.md` | 문서 | 검토 절차 8번 갱신 (F-005와 동일 파일 — Step 12에서 일괄) | `:52-62` |
| 5 | `opal/core/references/tools.md` | 문서 | 커맨드·옵션·종료 코드·설정 예시·M-2 교정 | `:202-306` |
| 6 | `docs/CONVENTIONS.md` | 문서 | §@header 규칙 — "읽기 전용 스코프는 code-map 강제" → "전역 `headerSource: manifest`면 code-map 강제" | `:174` |
| 7 | `docs/ARCHITECTURE.md` | 문서 | `tools/` 표 code-scan 행 — headerSource 단일 기준 반영 | `:82` |
| 8 | `docs/PROJECT.md` | 문서 | 변경이력 행 추가 (Task 080) | `:197` 이하 |

#### 3.6.2 문서별 개정 명세

**(1) `header-standard.md` §7**

| 대상 | 현행 | 개정 |
|------|------|------|
| §7 도입부 (`:191`) | "`config.headerSource`(`auto`(기본) / `inline` / `manifest`)로 소스를 강제할 수 있으며" | "`config.headerSource`(`inline` / `manifest` **2택, 미설정 시 전 명령 거부**)가 소스를 결정한다" |
| §7 상속 서술 (`:189`) | "인라인이 없는 파일에 한해 5단 상속으로 해석" | 모드별 표 — `inline`: tier① 단독 / `manifest`: tier②~⑤ 4단 |
| §7.1 `readonly` (`:206`) | "`true`면 `target`이 무조건 `manifest` 반환" | **제거(deprecated)** 표기 — "이 키는 무시된다. 기록 소스는 `.opal/code-scan.json`의 **전역 `headerSource`**로 설정한다. `manifest`로 해석되지 **않는다**" |
| §7 `headerSource` 성격 | (스코프 오버라이드 여지가 있는 서술) | **"전역 단일 키"임을 명시** — `index.json` `scopes.{name}`에는 모드 선언 키를 두지 않으며, 한 실행의 모드는 실행당 1값이다. **스코프별 `headerSource` 절을 신설하지 않는다** |
| §7.1 신규 행 | - | `scopes[].include` / `scopes[].exclude` (선택, string[], 기본 `[]`) — 패턴 문법·순서 계약 |
| §7.2 `files` (`:219`) | "키는 `dir` 실제 파일 목록과 **집합 일치**" | "키는 `dir`의 파일 중 **스코프 필터(`include`/`exclude`)·`exclude`/`excludePatterns`를 통과한 부분집합**과 집합 일치. 매니페스트가 디렉토리 전체를 대표하지 않는 것이 정상이다" (보강④) |
| §7.3 `_source` (`:231-241`) | 5종 | `inline` 모드에서는 `_source` 키가 붙지 않음을 명시 + `manifest` 모드 4종 |
| §7.5 신규 | - | 스코프 중복 우선순위 (최장 root → include 매칭 → 사전순, 양쪽 매칭 = `scope_ambiguous`) |

**(2) `header-rules.md`**

| 대상 | 개정 |
|------|------|
| §기록 위치 판정 (`:14-27`) | 4단 표 → **3행 표**(아래 확정 도메인 표 그대로). 폐쇄 도메인 문장은 **3값 기준**으로 쓴다 — "`reason`은 이 **3값** 외를, `write_to`는 이 **3값** 외를 반환하지 않는다". `out_of_scope`가 나오는 조건(스코프 `include`/`exclude` 필터 탈락)과 그것이 **모드 판정보다 먼저 평가된다**는 순서를 표에 포함한다 |
| `:20` `readonly` 행 | 삭제 (F-11 AC "`readonly`를 판정 근거로 서술하는 문장 잔존 0건") |
| `:26` code-map 부재 서술 | "code-map 부재 프로젝트는 `headerSource: inline`으로 설정하며 결과는 항상 `inline`이다" |
| §커버리지 합산 (`:51-55`) | "합산" → "**모드별 단일 소스**. `inline` 모드는 인라인 작성분만, `manifest` 모드는 매니페스트 작성분만 계상한다" |
| §빈 결과 폴백 ② (`:131`) | "합산 커버리지(`covered = inline + manifest`) 30% 미만" → "`coverage.percent` 30% 미만" |
| §갱신 시점 (b) (`:36`) | 유지 (게이트 기준 불변) |

**`header-rules.md` 기록 위치 판정표 확정 내용 (문서에 그대로 반영)**

| # | 조건 | `write_to` | `reason` |
|---|------|-----------|----------|
| ① | 소속 스코프의 `include`/`exclude` 필터에서 탈락 (관리 대상 아님) | `none` | `out_of_scope` |
| ② | `headerSource`(CLI 플래그 > 전역 config, **2층**) = `inline` | `inline` | `header_source_inline` |
| ③ | `headerSource` = `manifest` | `manifest` | `header_source_manifest` |

- 판정은 ①→②→③ 순으로 첫 매칭이 승리한다. **①이 모드 판정보다 먼저**인 이유는 §3.2.2 (C-bis) 반환 계약과 같다 — 관리 대상이 아닌 파일에는 기록 위치 자체가 존재하지 않는다.
- `reason`은 이 **3값**(`out_of_scope`/`header_source_inline`/`header_source_manifest`) 외를, `write_to`는 이 **3값**(`none`/`inline`/`manifest`) 외를 반환하지 않는다.
- ① 미발동 조건(스코프 미설정 · `include`/`exclude` 미사용 · root 밖 파일)은 §3.2.2 (C-bis) 결정표를 그대로 인용한다.

> **[MUST] 이 표는 §1.5 계약 변경표(`target` `reason`/`write_to` 각 3값)·§3.2.2 (C-bis)·§3.3.2 (B)와 **동일 도메인**이어야 한다.** 문서가 구현보다 좁은 폐쇄 도메인을 선언하면 `tools.md:240`의 M-2(현행 4값 오기)·077 H-6(`header-rules.md:25` "이 4값 외를 반환하지 않는다")과 **동형 결함을 새로 고정**하게 된다 — 이 태스크가 교정하러 온 결함을 재생산하지 않는다.

**(3) `code-scan-management.md`**

| 대상 | 개정 |
|------|------|
| §추론 소스 3종 규약 (`:16-20`) | `headerSource` 행 추가 — **"추론 금지. PM이 소유자에게 확인한다"** (D-1 역할명 규약 준수) |
| §최소 구조 예시 (`:24-31`) | `"headerSource": "inline"` 포함 (→ H-11 영속 해결) |
| §생성 보고 (`:38-42`) | 보고 형식에 `headerSource={값}` 추가 |
| §headerSource 필드 관리 (`:63-73`) | 3택 표 → 2택 표 + 미설정 = `header_source_unset` 전 명령 거부 + **PM이 최초 설정을 소유자에게 묻는 절차**(D-1) + **"프로젝트당 전역 1회 설정이며 스코프별 재선언은 없다"** 명시 |
| `:73` 인용 | `code-scan.js:187-190` → 삭제 (행 번호 인용 대신 동작 서술) — **M-1 교정** |
| §index 관리 의무 (`:80`) | "`readonly` 정책" → "`include`/`exclude` **파일 집합 필터** 정책" (모드는 index.json 소관이 아니다) |

**PM 최초 설정 절차 (신설, 역할명만 사용)**:

```
1. PM이 code-scan을 첫 호출할 때 `.opal/code-scan.json`이 없거나 `headerSource`가 없으면,
   소유자에게 다음 2택을 제시하고 확인을 받는다.
   - inline   : 소스 파일에 직접 @header 주석을 기록한다 (기본 권장 — 소스 편집이 자유로운 저장소)
   - manifest : .opal/code-map/ 외부 매니페스트에만 기록한다 (소스 편집이 제한되는 저장소)
2. 확인된 값을 `.opal/code-scan.json`의 **최상위 `headerSource`**에 기재한 뒤 호출을 진행한다 — 프로젝트당 **전역 1회** 설정이며, 스코프별로 다시 묻거나 재선언하지 않는다.
3. 도구는 이 질문을 하지 않는다 — 비대화형을 유지한다 (D-1).
```

**(4) `pm-review-gate.md` 검토 절차 8번**

| 대상 | 개정 |
|------|------|
| `:56` 2소스 판정 | "`readonly` 스코프에 속한 파일은 인라인 기록이 금지되므로" → "**프로젝트 전역** `headerSource`가 `manifest`이면 전 파일의 `_source`가 code-map 유래로 나오는 것이 정상" (스코프 단위 서술을 남기지 않는다) |
| `:57` 합산 커버리지 | "`coverage.covered`(= `coverage.inline` + `coverage.manifest`)" → "`coverage.covered`(설정된 `headerSource` 소스 기준)" |
| 신규 소절 | **미설정 대응**: `code-scan` 호출이 `header_source_unset`(exit 1)으로 거부되면 PM은 `code-scan-management.md §headerSource 필드 관리`의 최초 설정 절차를 수행한 뒤 재실행한다. 이 실패를 워커 결함으로 판정하지 않는다 |

**(5) `tools.md`**

| 대상 | 개정 |
|------|------|
| `:240` target 주석 | "(4단: inline_exists/readonly_repo/legacy_no_header/manifest)" → "(`headerSource` 직결 — `write_to`: `inline`/`manifest`/`none`, `reason`: `header_source_inline`/`header_source_manifest`/`out_of_scope`)" — **M-2 교정. 교정 내용 자체가 신 도메인(각 3값)을 반영해야 하며, `write_to`와 `reason`을 섞어 나열하지 않는다**(현행 오기의 근본 원인) |
| §주요 옵션 (`:253-264`) | `--header-source <inline\|manifest>` 행 추가 — 설명은 "**이 실행의 전역 모드를 지정한다. 설정 파일의 전역값보다 우선한다**"로 쓰고, 스코프·파일 단위 예외를 시사하는 서술을 넣지 않는다 |
| §종료 코드 (`:266-272`) | `validate` 전용 표 → **전 명령 공통 표**로 확장: `1` = 사용법·스키마 오류 + `header_source_unset`/`header_source_invalid`/`code_scan_config_invalid`/`scope_ambiguous` |
| §프로젝트 설정 (`:289-296`) | 예시에 `"headerSource": "inline"` + `scopes` 객체 형식 예시 추가. **`auto`를 유효값으로 서술하는 문장 잔존 0건** |
| §커맨드 `scaffold`(`:238`) | "`inline` 모드에서는 no-op" 1줄 추가 |
| `auto` 잔존 | `headerSource` 값 도메인을 서술하는 전 지점에서 `auto`를 **유효값으로 나열하지 않는다**. 제거 사실을 안내할 필요가 있으면 "`auto`는 제거됨(Task 080)"처럼 **폐기 표기**로만 쓴다 (→ TS-067) |

**(6~8) `docs/` 3종**

| 파일 | 개정 |
|------|------|
| `docs/CONVENTIONS.md:174` | "(읽기 전용 스코프는 code-map 강제)" → "(전역 `headerSource`가 `manifest`이면 code-map 강제)" |
| `docs/ARCHITECTURE.md:82` | code-scan 행 — "인라인 및 `.opal/code-map/` 2소스" → "인라인·`.opal/code-map/` 2소스 중 `headerSource`로 택1(전 경로 단일 기준)" + 변경이력 행 |
| `docs/PROJECT.md` 변경이력 | "2026-08-01 | 헤더 소스 단일화 — `headerSource` 2택 전 경로 적용·미설정 거부·`scopes` include/exclude·`readonly` deprecated (Task 080)" |

#### 3.6.3 환경 변경 / 3.6.4 배치·마이그레이션

해당 없음.

#### 3.6.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-050 | F-11 AC | 산출물 검사 | 5문서 전부 변경이력 표에 신규 행 (버전·`YYYY-MM-DD HH:mm` KST·태스크 번호 `(080)`) |
| TS-051 | F-11 AC | 산출물 검사 | 5문서에 `readonly`를 판정 근거로 서술하는 문장 0건 (deprecated 표기는 허용) |
| TS-052 | F-11 AC | 산출물 검사 | 규칙 문서에 개인 식별자(에이전트 이름·소유자 호칭) 신규 기재 0건 |
| TS-053 | F-11 AC | 산출물 검사 | `header-rules.md` 기록 위치 판정표의 `reason` 값이 `header_source_inline`/`header_source_manifest`/`out_of_scope` **3값**이고, 폐쇄 도메인 문장도 3값 기준으로 서술된다 (2값 서술 잔존 0건) |
| TS-054 | F-11 AC | 산출물 검사 | `code-scan-management.md` 최소 구조 예시에 `headerSource` 포함 |
| TS-055 | docs 갱신 | 산출물 검사 | `docs/` 3종에 Task 080 변경이력 행 |
| TS-067 | F-11 AC · D-3 | 산출물 검사 | `tools.md` · `header-standard.md` §7 · `code-scan-management.md` 3문서에 **`auto`를 유효값으로 서술하는 문장 0건**. "제거됨/deprecated" 폐기 표기는 허용하며, 값 목록·설정 예시·필드 관리 표에 `auto`가 나열되면 실패 |
| TS-068 | F-11 AC | 산출물 검사 | `header-rules.md`·`tools.md` 2문서에 `write_to` **3값**(`inline`/`manifest`/`none`)이 반영되고, `write_to`와 `reason` 값이 한 목록에 섞여 나열되지 않는다 (M-2 재발 방지) |

---

### F-007: 테스트 자산 + 골든 재캡처

#### 3.7.1 파일 변경 계획

**신규 생성**

| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `opal/tools/code-scan/tests/test-header-source.js` | 테스트 | 게이트·2택·**우선순위 2층(CLI > 전역)**·스코프 오버라이드 부재 부정 단언·에러 메시지 품질 | TASK F-1/F-2/F-12② |
| 2 | `opal/tools/code-scan/tests/test-scope-filter.js` | 테스트 | `isInScope` 5지점 일관성·우선순위·검출기 필터 | TASK F-8/F-9/F-10 |
| 3 | `opal/tools/code-scan/tests/fixtures/mixed-scope/` | 환경 | 혼재 디렉토리 픽스처 — **생존 스코프 2개 + `out_of_scope` 1건**, 전역값 반전 대조 무대 | TASK §배경 분석 (3), §3.7.2 |
| 3b | `opal/tools/code-scan/tests/fixtures/mixed-scope-ambiguous/` | 환경 | `scope_ambiguous` 전용 트리 (정상 트리에서 분리 — §3.7.2) | 보강③, TS-017 |
| 4 | `opal/tools/code-scan/tests/fixtures/golden/README.md` | 환경 | 캡처 명령·설정 조건·080 재캡처 diff 근거 기록 | F-13 AC |

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 5 | `tests/fixtures/**/.opal/code-scan.json` (20개) | 환경 | `headerSource` 명시 추가 | H-9 |
| 6 | `tests/test-resolve-header.js` | 테스트 | 077 TS-005 **삭제**(그룹 C) · 077 TS-044/045에 승계 근거 주석 · 077 TS-046 **반전**(`auto` 폴백 → 거부) · 077 TS-004 그룹 A/B 오버레이 이전 | §3.7.2, 3.3.2 (A) |
| 7 | `tests/test-target.js` | 테스트 | 4단 판정 → 모드 직결, `readonly_repo` → 하위호환 케이스, **`out_of_scope` 신규 케이스**(TS-035, TS-037) | 3.3.2 (B), 3.2.2 (C-bis) |
| 8 | `tests/test-validate.js` | 테스트 | 합산 커버리지 → 모드별, 구조 패스 모드 분기 | 3.3.2 (D) |
| 9 | `tests/test-scaffold.js` | 테스트 | `inline` 모드 no-op 케이스 추가 | 3.3.2 (C) |
| 10 | `tests/test-discover.js` | 테스트 | `readonly` 부재 · `include: []` 검증 | 3.2.2 (F) |
| 11 | `tests/test-regression.js` | 테스트 | 골든 대조 조건에 `headerSource: inline` 명시 반영 + 문서 검사 항목 갱신 + **077 TS-055 gitignore 단언 반전**(TS-046/047) | F-13, §3.5.3 |
| 12 | `tests/test-hook.js` | 테스트 | 미설정·무효·`inline` 모드 무출력 케이스 추가 + **`out_of_scope` 파일 무출력 케이스**(TS-036) | 3.5.2, 3.2.2 (C-bis) |
| 13 | `tests/test-feature.js` | 테스트 | 픽스처 설정 변경 반영 | H-9 |
| 14 | `tests/fixtures/golden/*.{json,txt}` (8개) | 환경 | 재캡처 | F-13 |

#### 3.7.2 픽스처 `headerSource` 배정 (계약 결정)

`auto` 제거로 각 픽스처가 어느 모드를 검증하는지 **명시 선언**해야 한다.

| 픽스처 | 배정 | 근거 |
|--------|------|------|
| `legacy-repo` | `inline` | code-map 부재 · 골든 8커맨드 기준선 (`test-regression.js:51`) |
| `header-proximity` | `inline` | 인라인 근접 판정 전용 (`code-scan.js:430-451`) |
| `codemap-repo` | `manifest` | 매니페스트 4단 상속·미러 경로 사상 검증 자산. 인라인 계열은 임시 복사본 `inline` 오버레이로 분리 검증 (아래 그룹 A/B/C). **`legacy` 스코프의 `readonly: true`는 그대로 남긴다** (아래 결정) |
| `tiebreak/order-a`,`order-b` | `manifest` | `resolveScope` 사전순 tie-break 검증 (H-4 회귀) |
| `schema/*` (4) | `manifest` | index 스키마 오류 검증 — 게이트를 통과해야 스키마 에러에 도달한다 |
| `violations/*` (11) | `manifest` | 매니페스트 무결성 위반 검증 |
| `mixed-scope` (신규) | **전역값만 뒤집는 2회차 실행** (`inline` → `manifest`) | 5지점 교차 검증 + **실행당 1값 대조**. 구조는 아래 명세 |
| `mixed-scope-ambiguous` (신규) | `inline` | `scope_ambiguous` 전용 (분리 이유는 아래) |

**`codemap-repo` 재배치 — 그룹별 조치 (결정 완료)**

> **범위 정정**: 초판은 이 픽스처의 재작성 가능성을 우려했으나, 실측 결과 **픽스처 자산(`fixtures/codemap-repo/.opal/code-map/index.json`·5파일 tier 배치)은 전혀 손대지 않아도 된다.** 필요한 것은 `.opal/code-scan.json` 1줄 추가(Step 1)와 **테스트 코드 재배치**뿐이다. 임시 복사본에 `headerSource`를 실기재하는 오버레이 헬퍼 `makeHeaderSourceFixture`(`test-resolve-header.js:74-83`)가 이미 존재하며, 077 TS-044/045/046이 이 헬퍼를 이미 쓰고 있다(`:358`, `:384`, `:407`).

| 그룹 | 077 테스트 | 조치 | 근거 |
|------|-----------|------|------|
| **A** — tier②~⑤ 단독 | 077 TS-004의 `OrderService.java`(file)·`ShipRepo.java`(package)·`AdminGuard.tsx`(rule)·`OrderMisc.java`(domain) 4케이스(`test-resolve-header.js:187-238`), 077 TS-007(`:269-285`), S-20 depends(`:424-434`) | **그대로 이전** — `makeHeaderSourceFixture('manifest')` 오버레이 위에서 동일 기대값 유지 | 이 4개 파일은 애초에 인라인이 없으므로 `manifest` 모드에서 결과가 동일하다. 077 TS-045가 이미 `OrderService.java`를 manifest 모드에서 검증한다(`:403-404`) |
| **B** — tier① inline 단독 | 077 TS-004의 `AdminHome.tsx` `_source: inline` 케이스(`:176-185`) | **명제 교체 후 이전** — `makeHeaderSourceFixture('inline')` 하에서 "인라인 보유 파일만 반환"으로 재서술 | `inline` 모드에서는 `_source` 키가 붙지 않으므로(§3.3.2 (A)) `_source === 'inline'` 단언 자체가 성립하지 않는다. 077 TS-044(`:357-381`)가 이미 이 명제를 담당한다 |
| **C** — 혼재 파일 인라인 승리 | 077 TS-005 전체(`:244-262`) | **폐기 — 단, 불변식은 077 TS-044·TS-045로 분할 승계** (아래) | `auto`가 사라지면 "두 소스가 공존하는 상태에서 우선순위가 적용된다"는 상황 자체가 발생하지 않는다 |

**그룹 C 결정: 폐기(테스트 삭제)하되 불변식은 소실되지 않는다 — 재정의 신설이 불필요하다**

PM 권고는 "폐기가 아니라 재정의"였으나, 코드를 확인한 결과 **재정의 대상 테스트가 077에 이미 존재한다.** TS-005가 지키던 불변식("두 소스가 조용히 섞이지 않는다")은 077 TS-044·TS-045가 두 모드로 나누어 **이미 완전히** 담당한다:

| 모드 | 담당 테스트 | 실제 단언 (혼재 파일 `AdminHome.tsx` 대상) |
|------|-----------|-------------------------------------|
| `inline` | 077 TS-044 (`test-resolve-header.js:357-381`) | 결과 키가 정확히 1건이고 그것이 `AdminHome.tsx`이며 `module === 'AdminHome'`(인라인 값). 매니페스트 유래 5파일이 결과에 **0건**임을 개별 단언(`:373-380`) |
| `manifest` | 077 TS-045 (`test-resolve-header.js:383-405`) | 같은 혼재 파일의 `description`이 매니페스트 값이고 `exports`가 `['ManifestOnlyExport']`이며, **인라인 전용 `'AdminHome'`이 섞이면 안 됨**을 명시 단언(`:394-397`) |

즉 TS-005의 명제는 "한 실행에서 인라인이 이긴다"였고, 2택 후에는 "각 모드에서 반대 소스가 결과에 섞이지 않는다"로 **분해되어 두 테스트에 이미 흡수되어 있다.** 077 TS-044/045는 우연히 겹치는 것이 아니라 정확히 같은 혼재 파일(`AdminHome.tsx`)을 대상으로 반대 방향 오염을 각각 막는다 — **중복이 아니라 승계다.**

따라서:
- 077 TS-005는 **삭제**한다. 별도의 약화된 재정의 테스트를 새로 만들지 않는다 — 만들면 077 TS-044/045와 진짜 중복이 되어 [MUST] `opal/core/PRINCIPLES.md` §2(중복 제거)에 어긋난다.
- 대신 **077 TS-044·TS-045를 "혼재 파일 무병합 불변식의 정식 담당"으로 승격**하고, 두 테스트 상단 주석에 "TS-005(077)에서 승계 — 삭제된 테스트의 불변식을 이 두 케이스가 모드별로 분담한다"는 계승 근거를 남긴다. 근거가 코드에 남아야 후속 워커가 "방어가 사라졌다"고 오판하지 않는다.
- 077 TS-046(`bogus` → `auto` 폴백, `:406-419`)은 **반전**된다 — `auto` 폴백이 사라지므로 본 PLAN TS-003(`header_source_invalid` + exit 1)이 대체한다.

**`mixed-scope` 픽스처 구조 명세 (보정3 — 목표 검증 무대 확보)**

> **문제**: 초판 구조는 한 스코프만 살아남고 형제 파일이 모드 판정 **이전에** `out_of_scope`로 탈락하므로(§3.2.2 (C-bis) 판정 순서 ①), "서로 다른 스코프의 파일이 같은 실행에서 동일 모드를 본다"는 장면이 발생하지 않는다. 새 목표(**전역 단일 키 · 스코프 예외 없음 · 실행당 1값**)를 보여줄 무대가 픽스처에 없었다.

**확정 구조** — `include`에 걸려 **살아남는 스코프를 2개** 둔다.

```
opal/tools/code-scan/tests/fixtures/mixed-scope/
├── .opal/
│   ├── code-scan.json
│   │     {
│   │       "headerSource": "inline",            ← 전역 1키. TS-072~074가 이 값만 뒤집는다
│   │       "extensions": [".java"],
│   │       "scopes": {
│   │         "order-svc": { "path": "svc/shared/", "include": ["Order*.java"] },
│   │         "ship-svc":  { "path": "svc/shared/", "include": ["Ship*.java"]  }
│   │       }
│   │     }
│   └── code-map/index.json
│         scopes: order-svc / ship-svc — root·include 동일, anchors: [], stripPrefix: []
└── svc/shared/                                  ← 한 디렉토리에 3소속이 공존(TASK §배경 분석 (3) 실사례)
    ├── OrderService.java     → order-svc (include "Order*.java")
    ├── OrderRepo.java        → order-svc
    ├── ShipService.java      → ship-svc  (include "Ship*.java")
    ├── ShipRepo.java         → ship-svc
    └── VendorLegacy.java     → 어느 include에도 미매칭 → out_of_scope
```

**`.opal/code-map/` 매니페스트 확정 명세 (커밋 상태)**

`index.json`은 `layerRules`·`domains`를 반드시 포함한다 — 없으면 `manifest` 모드에서 `layer`/`domain`이 비어 `uncovered:incomplete` 위반이 떠서(`code-scan.js:1509-1513`) `validate ok:true`가 성립하지 않는다.

```jsonc
// .opal/code-map/index.json  (발췌)
{
  "version": 1, "status": "reviewed",
  "scopes": {
    "order-svc": { "root": "svc/shared/", "anchors": [], "stripPrefix": [], "include": ["Order*.java"] },
    "ship-svc":  { "root": "svc/shared/", "anchors": [], "stripPrefix": [], "include": ["Ship*.java"]  }
  },
  "layerRules": [{ "match": "**/shared/**", "layer": "service" }],
  "domains":    { "shared": { "paths": ["svc/shared/**"] } }
}
```

```jsonc
// .opal/code-map/order-svc/_root.json  ·  .opal/code-map/ship-svc/_root.json
// (root="svc/shared/", anchors=[], stripPrefix=[] → mirrorRel = ROOT_MIRROR_NAME "_root", code-scan.js:614)
{ "version": 1, "scope": "order-svc", "dir": "svc/shared",
  "files": {
    "OrderRepo.java":    { "description": "주문 저장소", "exports": ["OrderRepo"] },
    "OrderService.java": { "description": "주문 서비스", "exports": ["OrderService"] }
  } }
{ "version": 1, "scope": "ship-svc", "dir": "svc/shared",
  "files": {
    "ShipRepo.java":    { "description": "배송 저장소", "exports": ["ShipRepo"] },
    "ShipService.java": { "description": "배송 서비스", "exports": ["ShipService"] }
  } }
```

| 파일 | 등재 | 이유 |
|------|------|------|
| `OrderService.java` · `OrderRepo.java` | `order-svc`에 **등재 + description 실기입** | `validate ok:true` 기준선 (`draft` 위반 0 — 빈 description은 `draft`로 잡힌다, `code-scan.js:1519-1524`) |
| `ShipService.java` · `ShipRepo.java` | `ship-svc`에 **등재 + description 실기입** | 동상 |
| `VendorLegacy.java` | **미등재** | out-of-scope 미등재가 `files_key_removed`로 집계되지 **않음**을 보이는 자산 (TS-014) |

> **`mirror_collision`이 나지 않는 근거**: 두 스코프의 `root`가 같아 mirrorRel이 둘 다 `_root`지만, 매니페스트 경로는 `.opal/code-map/{scope}/{mirrorRel}.json`(`code-scan.js:627`)이라 **스코프명이 경로에 들어가** 서로 다른 파일이 된다. 충돌 검출(`cmdScaffold:1337-1341`)은 `manifestAbs` 동일성으로 판정하므로 발동하지 않는다.

**세 요구의 양립 — 트리 분리 없이 오버레이로 해결 (결정)**

| 요구 | 출처 | 해결 |
|------|------|------|
| `validate ok:true` (생존 4파일 전부 등재) | S-19 (d) | **커밋 상태 그대로** — 가공 없이 성립 |
| in-scope 미등재 파일 검출 | TS-015 | **임시 복사본에서 `ShipRepo.java` 엔트리 1개 삭제** 후 실행 |
| out-of-scope 미등재 미집계 | TS-014 | **커밋 상태 그대로** — `VendorLegacy.java`가 원래 미등재 |

> **분리하지 않은 근거**: 충돌하는 것은 S-19(d)와 TS-015 둘뿐이고 차이가 **엔트리 1개**다. `makeHeaderSourceFixture`(`test-resolve-header.js:74-83`)가 이미 임시 복사본을 만들므로 그 복사본에서 키 1개를 지우면 된다. `mixed-scope-ambiguous`를 분리한 이유(**exit 1이 트리 전체를 마비시킴**)와 달리 여기서는 커밋 상태가 다른 TS를 막지 않는다 — 트리를 늘리면 동일 구조가 2벌이 되어 향후 드리프트 원인이 된다.
>
> **커밋 기준을 "정상(전부 등재)"으로 둔 이유**: 픽스처의 기본 상태가 정상이어야 나머지 TS(TS-012·016·035~037·072~074)가 깨끗한 기준선에서 돈다. 위반 상태를 기본으로 두면 모든 TS가 그 위반을 예외 처리해야 한다.

**TS별 사전 상태 고정표** — "어떤 상태에서 무엇을 단언하는가"

| TS / S | 트리 | `headerSource` | 매니페스트 사전 조작 | `scaffold` 선행 | 단언 |
|--------|------|---------------|--------------------|----------------|------|
| **S-19 (d)** | `mixed-scope` 커밋 상태 | **`manifest` 오버레이** | 없음 | 불필요 | `validate ok:true` · `coverage.manifest = 4` · `total = 4`(VendorLegacy는 열거에서 탈락) |
| **TS-014** | `mixed-scope` 커밋 상태 | **`manifest` 오버레이** | 없음 | 불필요 | `files_key_removed` **0건** — `VendorLegacy.java`가 디스크에 있고 미등재여도 미집계 |
| **TS-015** | `mixed-scope` **임시 복사본** | **`manifest` 오버레이** | `ship-svc/_root.json`의 `files["ShipRepo.java"]` **삭제** | 불필요 | `files_key_removed` **1건**, `key === "ShipRepo.java"` — in-scope 미등재는 여전히 검출 |
| **TS-012** | `mixed-scope` 커밋 상태 | `manifest` 오버레이 | 없음 | 불필요 | 5지점이 동일 파일 집합(생존 4)을 판정 |
| **TS-016** | `mixed-scope` 커밋 상태 | 커밋값 `inline` | 없음 | 불필요 | `Order*` → `order-svc`, `Ship*` → `ship-svc` 귀속 |
| **TS-035~037** | `mixed-scope` 커밋 상태 | 커밋값 `inline` | 없음 | 불필요 | `VendorLegacy.java` → `{write_to:'none', reason:'out_of_scope'}` |
| **TS-072** | `mixed-scope` 커밋 상태 | 커밋값 `inline` | 없음 | 불필요 | `target` 4건 전부 `inline` |
| **TS-073** | `mixed-scope` 커밋 상태 | 커밋값 `inline` | 없음 | 불필요 | 4경로 일치. **`scaffold` no-op 판정은 "`.opal/code-map/` 하위 전 파일의 내용·mtime 무변화 + `skipped[0].reason === 'header_source_inline'`"로 측정**한다 — 커밋 픽스처에 매니페스트가 이미 있으므로 "생성 파일 수 0"으로는 측정할 수 없다 |
| **TS-074** | `mixed-scope` **임시 복사본** | `inline` → **`manifest`로 값 1개만 교체** | 없음 | 불필요 — `scaffold`가 **단언 대상**이다 | 5경로 반전. `scaffold`는 exit 0 + `skipped`에 `header_source_inline` **없음** + 매니페스트 갱신 수행 |

> **`scaffold` 선행이 필요한 TS는 0건이다.** 커밋 매니페스트가 이미 완비되어 셋업으로서의 `scaffold`가 불필요하고, TS-073·TS-074에서 `scaffold`는 **관찰 대상**이다. 따라서 §4.2 Step에 추가할 선행 순서가 없으며, Step 1(픽스처)에서 매니페스트를 **완성 상태로 커밋**하는 것이 그 역할을 대신한다.

| 이 구조가 동시에 만족하는 것 | 근거 |
|---------------------------|------|
| **두 스코프가 같은 실행에서 함께 생존** — 4파일이 모두 조회·판정 대상 | 전역값만 뒤집어 두 스코프가 **함께** 뒤집히는 대조가 성립한다 (TS-072~074) |
| **`root` 동률 + `include`만 다름** | 보강③(`resolveScopeIn` 동률 tie-break에서 include 매칭 스코프 승리) 검증 무대 그대로 유지 — TS-016이 이 트리를 쓴다 |
| **`out_of_scope` 1건 상주**(`VendorLegacy.java`) | H-13·TS-035~037 검증 무대. 모드 판정 **이전** 단계가 살아 있음을 같은 트리에서 보인다 |
| **혼재 디렉토리 실사례 재현** | TASK.md §배경 분석 (3) "한 디렉토리에 서비스 A 파일 1개와 서비스 B 파일 다수가 공존" |

**`mixed-scope-ambiguous` 분리 — 결정: 별도 트리로 뗀다**

| 판단 축 | 내용 |
|---------|------|
| 결정 | TS-017(양쪽 `include` 매칭 → `scope_ambiguous`) 전용으로 `fixtures/mixed-scope-ambiguous/`를 따로 만든다 |
| 분리 이유 | `scope_ambiguous`는 `CodeMapFatalError`로 **exit 1**이다(§3.2.2 (D) ⑤). 정상 트리 안에 이 조건을 심으면 **그 트리를 쓰는 다른 TS 전부(TS-012·016·035~037·072~074)가 같은 에러에 막혀** 검증 불능이 된다 — 하나의 픽스처가 "정상 동작"과 "즉시 실패"를 동시에 표현할 수 없다 |
| 구조 | `mixed-scope`와 동일하되 두 스코프의 `include`를 모두 `["*.java"]`로 두어 같은 파일이 양쪽에 매칭되게 한다 |

**`codemap-repo` `legacy` 스코프의 `readonly: true` — 결정: 제거하지 않고 유지**

| 판단 축 | 내용 |
|---------|------|
| 결정 | `fixtures/codemap-repo/.opal/code-map/index.json:23`의 `"readonly": true`를 **그대로 둔다** |
| 근거 ① | 이것이 **전 저장소에서 유일한 `readonly: true` 실증 자산**이다(실측 1건, §2.4.3). 제거하면 F-6 AC("`readonly: true`만 있는 기존 index로 실행해도 전역 `headerSource`가 그대로 적용되고 안내 1줄이 출력된다")를 검증할 픽스처가 **0건**이 되어 TS-030·TS-031·TS-033이 전부 검증 불능이 된다 |
| 근거 ② | 이 픽스처의 역할이 "제거 대상 키의 **무시 + 안내** 동작 검증"으로 **바뀐다** — `readonly` 기능 검증 자산에서 하위호환 검증 자산으로의 용도 전환이며, 파일은 그대로 두고 테스트 기대값만 반전시키면 된다(TS-030) |
| 근거 ③ | 나머지 16종의 `readonly: false`도 손대지 않는다 — 무시되므로 동작에 영향이 없고, 건드리면 §3.7.2 "픽스처 자산 무변경" 원칙(그룹 A/B/C 결정)이 깨진다 |
| Step 1 영향 | 픽스처 작업은 `.opal/code-scan.json`에 `headerSource` 추가 **1줄뿐**이며 `index.json`은 전 18종 무변경 |

> **TS-ID 네임스페이스 주의**: 본 PLAN의 TS-044/TS-045(§3.5.5, F-12①/③)와 077의 TS-044/TS-045(headerSource 스위치)는 **서로 다른 태스크의 번호**다. 본 문서에서 077 자산을 가리킬 때는 항상 `077 TS-NNN`으로 표기한다.

#### 3.7.3 골든 재캡처 설계

**캡처 조건**

```bash
# 캡처 대상: legacy-repo (code-map 부재) — .opal/code-scan.json에 "headerSource": "inline" 명시 후
cd opal/tools/code-scan/tests/fixtures/legacy-repo
for c in "scan --json:scan.json" "domain:domain.txt" "layer:layer.txt" \
         "search auth --json:search.json" "exports token --json:exports.json" \
         "summary:summary.txt" "depends auth_service:depends.txt" "missing:missing.txt"; do
  node ../../../code-scan.js ${c%%:*} > ../golden/${c##*:}
done
```

**예측 결과 — 바이트 차이 0**

| 근거 | 설명 |
|------|------|
| ① | `legacy-repo`에는 `.opal/code-map/index.json`이 없다 (`find` 결과 미검출) |
| ② | 구 코드는 `auto` + `!ctx.codeMap.present` → `extractHeader` 결과를 그대로 반환했다 (`code-scan.js:699-701`) |
| ③ | 신 코드는 `inline` 모드 → `extractHeader` 결과를 그대로 반환한다 (§3.3.2 (A)) |
| ④ | `include`/`exclude` 미설정이므로 `isInScope`는 항상 true (§3.2.2 (B)) |

**따라서 재캡처 후 `git diff --stat opal/tools/code-scan/tests/fixtures/golden/`가 비어 있어야 정상이다.** 바이트가 달라지면 조회 경로에 의도치 않은 회귀가 발생한 것이므로 **차이를 GREEN 완료 조건으로 삼지 말고 원인을 규명**한다 (H-10).

`fixtures/golden/README.md` 기록 항목: 캡처 명령 · 캡처 시 픽스처 설정 전문 · 077 골든과의 diff 결과(예상 0) · 차이가 있었다면 원인. 이 파일은 `fixtures/` 하위이며 이 저장소 `.opal/code-scan.json`의 `exclude`에 `fixtures`가 있으므로 @header 작성 대상이 아니다.

#### 3.7.4 RED-first 트랙 적용 판단

**적용한다.**

| 판단 축 (`red-first.md` §1.5) | 해당 여부 | 근거 |
|---------------------------|---------|------|
| API 계약 | **해당** | exit code(전 명령 1) · JSON 에러 스키마 · `target.reason` 도메인 · `validate.coverage` 의미가 전부 대외 계약이다 |
| 비즈니스 로직 | **해당** | 필터 판정·스코프 귀속·모드별 커버리지는 순수 판정 로직이다 |
| 버그 수정(회귀 방지) | **해당** | 보강②는 077 결함 D(필터 비대칭, `DONE.md:58`)의 재발 방지가 목적이다 |
| 행위 불변 리팩터 | 비해당 | 행위가 의도적으로 바뀐다 (§1.5 제약② 파기) |
| 설정·문서 | 부분 해당 | F-006은 산출물 검사로 검증 |

추가 근거: 077에서 **테스트가 실제로 5건의 결함을 잡았고**(`tasks/077-.../DONE.md:48-58`), 그중 2건(필터 비대칭·게이트 과차단)은 이번 태스크가 건드리는 바로 그 경로다. 구현-후-검증 트랙은 self-confirming 위험이 크다.

**집행 규칙**:
- RED 작성 주체는 `opal-test-agent(mode: red)`, 구현 주체는 `opal-task-agent` — [MUST] `red-first.md` §2 작성자≠구현자.
- [MUST] `red-first.md` §3: "GREEN/fix 루핑 중 RED 테스트 파일 수정 금지." → Step 3~10 동안 `tests/*.js` 편집 금지. 픽스처(Step 1)는 RED 이전에 확정한다.
- RED 증거: `node --test "opal/tools/code-scan/tests/*.js"` exit≠0 로그를 `RED-EVIDENCE.md`에 기록.

#### 3.7.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-060 | F-13 AC | 회귀 | `headerSource: inline` 명시 상태에서 8커맨드 출력이 재캡처 골든과 바이트 동일 |
| TS-061 | F-13 AC | 산출물 검사 | `fixtures/golden/README.md`에 캡처 조건 + 077 대비 diff 근거 기록 |
| TS-062 | 완료기준 | 회귀 | `node --test "opal/tools/code-scan/tests/*.js"` 전량 pass · exit 0 |
| TS-063 | H-9 | 회귀 | 픽스처 20종 전부 `headerSource` 보유 (grep 기반 산출물 검사) |
| TS-064 | F-13 AC | 회귀 | `scan --json` 결과에 `_source` 키 0건 (`inline` 모드 — `test-regression.js:85-91` 계승) |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑

| Phase | 기능 | Step | agent | 실행 | 비고 |
|-------|------|------|-------|------|------|
| **0** | F-007 | 1 | opal-task-agent | 순차 | 픽스처 계약 확정 — RED의 선결 자산 (H-9) |
| **0** | F-007 | 2 | opal-test-agent (mode: red) | 순차 | RED 테스트 일괄 작성 — Step 1 완료 후 |
| **1** | F-001, F-002, F-004, F-003 | 3, 4, 5, 6, 7 | opal-task-agent | **순차** | 전부 `code-scan.js` 단일 파일 — 파일 충돌로 병렬 불가 |
| **2** | F-005 | 8, 9 | opal-task-agent | **병렬 가능** | Step 8은 `code-map-hook.js`, Step 9는 `.opal/code-scan.json`+검증 — 독립 파일 |
| **3** | F-006 | 10, 11, 12 | opal-task-agent / PM 직접 | **병렬 가능** | 문서 3그룹 상호 독립 파일 |
| **4** | F-007 | 13, 14 | opal-task-agent / opal-test-agent | 순차 | 골든 재캡처 → 전량 GREEN 확인 |

> Phase 1을 하나의 에이전트가 순차 처리하는 것은 [MUST] `plan-guide.md` §C-1 그룹핑 우선순위 1 "동일 파일을 수정하는 Step은 반드시 같은 에이전트에 배치"에 따른다.

### 4.2 실행 체크리스트

> 총 **14개 Step** | Phase **5개** | 테스트 시나리오 **67종**(TS-001~TS-075 중 정의분) | 실행 모드: **복잡**

#### Step 1: 픽스처 계약 확정 — `headerSource` 명시 + 혼재 디렉토리 픽스처 신설
- [ ] 완료
- **소속 기능**: F-007
- **영역**: 환경
- **agent**: opal-task-agent
- **파일**: `opal/tools/code-scan/tests/fixtures/**/.opal/code-scan.json` (20개) · `opal/tools/code-scan/tests/fixtures/mixed-scope/**` (신규) · `opal/tools/code-scan/tests/fixtures/golden/README.md` (신규)
- **작업 내용**: §3.7.2 배정표대로 20개 픽스처 설정에 `headerSource`를 추가한다. 혼재 디렉토리 픽스처 `mixed-scope/`를 **§3.7.2 확정 구조·매니페스트 명세 그대로** 신설한다 — `svc/shared/`에 5파일(`Order*` 2 / `Ship*` 2 / `VendorLegacy` 1), `root` 동률 + `include`만 다른 **생존 스코프 2개**, 전역 `headerSource: inline`, `.opal/code-map/`에 `index.json`(+`layerRules`·`domains`)과 스코프별 `_root.json` 2개. `scope_ambiguous` 전용 트리 `mixed-scope-ambiguous/`를 **별도로** 신설한다(정상 트리에 심으면 그 트리를 쓰는 TS 전부가 exit 1에 막힌다 — §3.7.2 분리 근거). `golden/README.md`에 캡처 명령·설정 조건 골격을 작성한다(diff 결과는 Step 13에서 채운다).
- **완료 기준**: `find opal/tools/code-scan/tests/fixtures -name code-scan.json | xargs grep -L headerSource` 결과 0건 · `mixed-scope/`·`mixed-scope-ambiguous/` 두 트리에 `.opal/code-scan.json`+`.opal/code-map/index.json` 존재 · `mixed-scope/`에서 두 스코프가 각각 2파일씩 생존하고 `VendorLegacy.java`만 어느 include에도 미매칭 · **`mixed-scope/` 매니페스트가 §3.7.2 확정 명세대로 커밋된다** — `index.json`에 `layerRules`·`domains` 포함, 스코프별 `_root.json`에 생존 4파일 등재 + description 실기입, `VendorLegacy.java` 미등재. `manifest` 오버레이 상태에서 `validate ok:true`가 **무가공으로** 성립함을 실행으로 확인
- **테스트**: TS-063
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 2: RED 테스트 작성 — 신규 계약 전량
- [ ] 완료
- **소속 기능**: F-007
- **영역**: 테스트
- **agent**: opal-test-agent (mode: red)
- **파일**: `tests/test-header-source.js`(신규) · `tests/test-scope-filter.js`(신규) · `tests/test-resolve-header.js` · `tests/test-target.js` · `tests/test-validate.js` · `tests/test-scaffold.js` · `tests/test-discover.js` · `tests/test-regression.js` · `tests/test-hook.js` · `tests/test-feature.js`
- **작업 내용**: §3.N.5 테스트 시나리오 표에 정의된 TS 전량(TS-001 ~ TS-075 범위 중 실제 정의분 **67종**)을 RED로 구현한다. 기존 8파일은 §1.5 계약 변경표에 따라 재작성한다 — 기대값을 느슨하게 바꾸는 약화가 아니라 새 계약으로의 이전임을 각 파일 상단 주석에 명시한다(077 재작업 선례 `test-resolve-header.js:14-19` 포맷 준용). 신규 테스트 파일에는 `layer: test` + `task: "080"` + `scenarios` 필드를 포함한 @header를 작성한다(`header-rules.md:76-83`).
  **077 자산 처리 3건을 반드시 포함한다** — ① 077 TS-005(`test-resolve-header.js:244-262`) **삭제** + 077 TS-044·TS-045(`:357-405`)에 승계 근거 주석 추가(§3.7.2 그룹 C) ② 077 TS-046(`:406-419`) `auto` 폴백 단언을 `header_source_invalid`+exit 1로 **반전**(본 PLAN TS-003) ③ 077 TS-055(`test-regression.js:126-127`) `.opal/code-scan.json` 무시 단언을 **비무시(exit 1)로 반전**(TS-046/TS-047, §3.5.3 결정).
- **완료 기준**: `node --test "opal/tools/code-scan/tests/*.js"` exit≠0 + 실패 목록이 신규 계약 항목과 일치 + RED 증거 기록
- **테스트**: 자체 (RED 증거)
- **실행 방법**: sub-agent
- **의존**: Step 1

#### Step 3: F-001 — `headerSource` 스키마 재정의 + 전 명령 차단 게이트 + `--header-source`
- [x] 완료 (2026-08-02 13:52 · PM Gate Pass)
- **소속 기능**: F-001
- **영역**: 도구
- **agent**: opal-task-agent
- **파일**: `opal/tools/code-scan/code-scan.js`
- **작업 내용**: §3.1.2 (A)~(F) 구현 — `HEADER_SOURCE_VALUES` 상수, `DEFAULT_CONFIG.headerSource: null`(`:45`), `parseArgs`에 `--header-source`(`:131-173`), `loadConfig` 반환 계약 변경(`:193-213`, **process.exit·throw 금지**), `resolveHeaderSource` 신설(**유일 판정 지점 — 파일 단위 판정 함수를 만들지 않는다**, §3.1.2 (D)), `codeMapErrorExit` → `errorExit`(stdout JSON + stderr 사람용, `:474-477`), `main()` 게이트 삽입(`:1702-1704` 직후), `buildCtx` 시그니처 확장(`:535`) 및 호출 5곳 갱신, `USAGE` 갱신(`:61-110`).
  **`auto` 완전 제거를 자산에서 확인한다** — `DEFAULT_CONFIG`(`:45`)·`USAGE` 설정 예시(`:108`)·`loadConfig` 검증 배열(`:199`)에서 `auto` 리터럴을 제거하고, 남는 유일한 `auto` 언급은 `header_source_invalid`의 마이그레이션 힌트 문자열 1개소여야 한다(TS-066).
- **완료 기준**: TS-001~TS-004, TS-007~TS-009, TS-065, TS-066, **TS-070** GREEN · `help`/`version` 회귀 없음 · `loadConfig`에 `process.exit` 0건 · `code-scan.js` `auto` 리터럴이 마이그레이션 힌트 1개소로 한정 · **모드 판정 지점이 `resolveHeaderSource` 1곳**(TS-070 화이트리스트 4단계 절차, §3.1.5)
- **테스트**: TS-001~TS-004, TS-007~TS-009, TS-065, TS-066, TS-070
- **[PM 재배정 2026-08-02 13:52]** TS-005·TS-006·TS-069는 **Step 7로 이관**한다. 세 케이스가 요구하는 `write_to:'inline'` + `reason:'header_source_inline'`은 `decideTarget` 모드 직결(Step 7)이 있어야 성립하고, 스코프 키 무시 안내(Step 6)와 객체형 `scopes` 지원(Step 4)에도 걸린다 — Step 3 단독으로는 원리상 달성 불가한 배정 오류였다. 테스트 자체는 정확하며 수정하지 않는다.
- **실행 방법**: sub-agent
- **의존**: Step 2

#### Step 4: F-002 — 스코프 정규화 + `isInScope` + `resolveScopeIn` 우선순위
- [x] 완료 (2026-08-02 14:10 · PM Gate Pass)
- **소속 기능**: F-002
- **영역**: 도구
- **agent**: opal-task-agent
- **파일**: `opal/tools/code-scan/code-scan.js`
- **작업 내용**: §3.2.2 (A)(B)(D)(E)(F) 구현 — `isExcluded` → `matchesAnyPattern` 개명 + 호출 4곳(`:312`,`:1236`,`:1441`,`:1475`) 갱신, `normalizeConfigScope`/`normalizeIndexScope`/`isInScope`/`resolveScopeIn` 신설, `resolveScope`(`:557-569`)는 시그니처 유지 후 위임, `loadCodeMap` 스키마 검증 확장(`:518-531`), `inferScopes` 객체 승계 + include 추론 금지(`:1093-1110`), `cmdValidate:1479`·`cmdFeature:1665` 정규화 대응.
- **완료 기준**: TS-010, TS-011, TS-016~TS-018, **TS-075** GREEN · `module.exports`(`:1739-1750`) 시그니처 불변
- **테스트**: TS-010, TS-011, TS-016, TS-017, TS-018, TS-075
- **실행 방법**: sub-agent
- **의존**: Step 3

#### Step 5: F-002 — 5개 적용 지점 배선
- [x] 완료 (2026-08-02 14:25 · PM Gate Pass)
- **소속 기능**: F-002
- **영역**: 도구
- **agent**: opal-task-agent
- **파일**: `opal/tools/code-scan/code-scan.js`
- **작업 내용**: §3.2.2 (C) 표대로 5지점 배선 — ① `getSearchPaths`(`:279-296`) 반환 타입 변경 + `discoverFiles`(`:298-314`) 필터 적용(`targetPath`는 면제) ② `collectDirsWithCodeFiles:1236` ③ `listCodeFilesInDir:1441`(인자에 `scopeDef` 추가, 호출부 `:1583-1584` 갱신) ④ `cmdValidate --changed:1466-1477`에 `out_of_scope` skipped 사유 추가 ⑤ **`decideTarget`(`:755-791`)에 필터를 신규 배선한다** — `rootMatches` 헬퍼 추출 + `isFilteredOutOfScope` 신설 + `decideTarget` 선두에서 호출해 §3.2.2 (C-bis) 반환 계약(`{write_to:'none', reason:'out_of_scope'}`, exit 0)을 구현한다. 현행 `decideTarget`은 `isExcluded`/`hasExcludedSegment` 호출이 **0건**이므로 이 지점만 "대체"가 아니라 "신규 도입"이다(→ H-13).
- **완료 기준**: TS-012~TS-015, TS-019, TS-036 GREEN · **TS-035·TS-037의 `out_of_scope` 부정 단언(오발동 0건) 전량 통과** · `code-scan.js`에 스코프 필터 판정 로직이 `isInScope` 외 0곳 · `decideTarget`이 `isFilteredOutOfScope`를 경유해 `isInScope`를 호출함이 코드로 확인됨(F-8 AC 5지점 충족)
- **[PM 재배정 2026-08-02 14:25]** TS-035 대조군 케이스·TS-037 legacy-repo 케이스에 포함된 **모드 직결 단언**(`write_to:'inline'` + `reason:'header_source_inline'`)은 **Step 7로 이관**한다. 한 TS 안에 필터 축 단언과 모드 축 단언이 섞여 있어 Step 5 단독으로는 완주 불가였다 — Step 3→7 이관과 동형 사유다. Step 5 범위인 필터 축(오발동 부정 단언)은 전량 통과했다.
- **테스트**: TS-012, TS-013, TS-014, TS-015, TS-019, TS-035, TS-036, TS-037
- **실행 방법**: sub-agent
- **의존**: Step 4

#### Step 6: F-004 — `readonly` 제거(무시 + 안내 1회)
- [x] 완료 (2026-08-02 14:42 · PM Gate Pass)
- **소속 기능**: F-004
- **영역**: 도구
- **agent**: opal-task-agent
- **파일**: `opal/tools/code-scan/code-scan.js`
- **작업 내용**: §3.4.2 구현 — `normalizeIndexScope`에서 `readonly` 키를 **무시**하고 stderr deprecated 안내(실행당 1회, 전역 `headerSource` 설정 방법 포함). **`manifest`로 흡수하지 않는다** — 흡수 코드가 남으면 전역 단일 키 결정이 조용히 파괴된다(H-8). `scopes[].headerSource` 키도 동일하게 무시 + 안내. `decideTarget`의 `readonly` 분기 제거(`:761-770`), `inferScopes`의 `readonly: false` 기입 제거(`:1098`,`:1107`), `cmdDiscover` `note` 문자열 갱신(`:1199`).
- **완료 기준**: TS-031, TS-032, TS-034, **TS-071** GREEN · **TS-030·TS-033의 `readonly_repo` 소멸 부정 단언 통과** · `grep -n readonly code-scan.js` 결과 0건(하위호환 정규화 코드의 입력 키 참조 제외) · `discover` 산출물에 `readonly`·`headerSource` 각 0건
- **테스트**: TS-031, TS-032, TS-034, TS-071
- **[PM 재배정 2026-08-02 14:42]** TS-030·TS-033의 **모드 직결 단언**(`reason:'header_source_inline'` / `'header_source_manifest'`)은 **Step 7로 이관**한다. `readonly` 축(`readonly_repo` 소멸)은 Step 6에서 통과했고, 남은 단언은 `decideTarget` 모드 직결로만 성립한다. Step 3·5에 이은 **3번째 동형 사례**(다축 TS ↔ 단축 Step 경계 불일치).
- **실행 방법**: sub-agent
- **의존**: Step 4

#### Step 7: F-003 — `resolveHeader`/`decideTarget`/`scaffold`/`validate` 모드 존중 + 버전 갱신
- [x] 완료 (2026-08-02 15:00 · PM Gate Pass)
- **소속 기능**: F-003
- **영역**: 도구
- **agent**: opal-task-agent
- **파일**: `opal/tools/code-scan/code-scan.js`
- **작업 내용**: §3.3.2 (A)~(D) 구현 — `resolveHeader`(`:688-701`) 2택 직결 + `manifest` 모드 index 부재 경고, `decideTarget`(`:755-791`) 모드 직결(모드 축 2값 — `out_of_scope`는 Step 5에서 이미 배선되어 전체 도메인은 3값), `cmdScaffold`(`:1313-1393`) `inline` no-op, `cmdValidate`(`:1488-1641`) 모드별 커버리지·검출기 분기·`result.headerSource` 필드 추가. 마지막으로 `VERSION`(`:37`)을 `1.4.0`으로 올리고 변경이력(`:1752-1774`)에 v1.4.0 행을 추가한다.
- **완료 기준**: TS-020~TS-029, **TS-072~TS-074** GREEN · **TS-005·TS-006·TS-069 GREEN(Step 3에서 이관 — 아래 참조)** · `uncovered:pre_existing` 비차단 정책 불변 · `VERSION === '1.4.0'` · `mixed-scope`에서 전역값만 뒤집었을 때 5경로가 함께 반전
- **테스트**: TS-020~TS-029, TS-072, TS-073, TS-074, **TS-005, TS-006, TS-069, TS-035, TS-037, TS-030, TS-033**
- **[PM 재배정 2026-08-02 14:42]** TS-030(전역 inline → `header_source_inline`)·TS-033(전역 manifest → `header_source_manifest`)의 모드 직결 단언도 Step 6에서 이관받는다. 두 케이스는 **짝을 이뤄야** "결과가 `readonly`가 아니라 전역값을 따른다"가 증명된다(`test-target.js:180-212` 주석). `readonly_repo` 소멸 부정 단언은 Step 6에서 이미 통과 — 깨뜨리지 마라.
- **[PM 재배정 2026-08-02 14:25]** TS-035(대조군 4파일)·TS-037(legacy-repo 4케이스, codemap-repo)의 **모드 직결 단언**도 Step 5에서 이관받는다. `decideTarget` 4단 판정을 모드 직결로 교체하면 함께 GREEN이 된다. 필터 축(오발동 부정 단언)은 Step 5에서 이미 통과 — **깨뜨리지 마라.**
- **[PM 재배정 2026-08-02 13:52]** TS-005(index.json 스코프 키 무시)·TS-006(CLI > 전역 2층, 4파일 동일 모드)·TS-069(code-scan.json 스코프 키 무시)를 Step 3에서 이관받는다. 세 케이스는 `decideTarget` 모드 직결(본 Step) + 스코프 키 무시 안내(Step 6) + 객체형 `scopes`(Step 4)가 **모두** 갖춰져야 성립하므로, 셋의 합류 지점인 본 Step이 검증처다.
- **실행 방법**: sub-agent
- **의존**: Step 5, Step 6

#### Step 8: F-005 — hook fail-safe 보강
- [x] 완료 (2026-08-02 15:12 · PM Gate Pass)
- **소속 기능**: F-005
- **영역**: 도구
- **agent**: opal-task-agent
- **파일**: `opal/tools/code-scan/code-map-hook.js`
- **작업 내용**: §3.5.2 구현 — 조기 이탈 ⑤.5 신설(`:117` 직후), `ctx` 조립에 `headerSource` 추가(`:127`), 파일 상단 @header `description`의 조기 이탈 단수 표기 갱신(9단 → 10단), 변경이력 행 추가(`:162-163`).
- **완료 기준**: TS-040~TS-043 GREEN · 미설정·무효·`inline` 3케이스 모두 stdout 0바이트 exit 0
- **테스트**: TS-040, TS-041, TS-042, TS-043
- **실행 방법**: sub-agent
- **의존**: Step 7

#### Step 9: F-005 — 이 저장소 설정 + `brain-tool sync-header` 실패 전달 검증
- [x] 완료 (2026-08-02 15:12 · PM Gate Pass)
- **소속 기능**: F-005
- **영역**: 환경
- **agent**: opal-task-agent
- **파일**: `.opal/code-scan.json` · `.gitignore`
- **작업 내용**: §3.5.3대로 ① `.opal/code-scan.json`에 `"headerSource": "inline"`을 추가하고 ② `.gitignore`에 `!.opal/code-scan.json` 예외 1줄을 `.gitignore:6`(`!.opal/code-map/**`) 다음에 추가한다. 추가 후 `git check-ignore .opal/code-scan.json`이 exit 1(비무시)임을 실측하고, `git status`에 이 파일이 신규 추적 대상으로 나타나는지 확인한다. §3.5.4대로 미설정 임시 트리에서 `brain-tool sync-header`를 실제 실행해 detail에 `header_source_unset`이 전달되는지 확인한다 — **`brain_tool.py`는 수정하지 않는다(§3.5.4에서 무수정 성립이 코드로 확정됨).**
- **완료 기준**: TS-044~TS-047 GREEN · 저장소 루트에서 8커맨드 exit 0 · `brain_tool.py` 변경 0줄 · `git check-ignore .opal/code-scan.json` exit 1
- **테스트**: TS-044, TS-045, TS-046, TS-047
- **실행 방법**: sub-agent
- **의존**: Step 7

#### Step 10: F-006 — 규칙 문서 3종 (스키마·판정·PM 관리)
- [x] 완료 (2026-08-02 15:05 · PM Gate Pass)
- **소속 기능**: F-006
- **영역**: 문서
- **agent**: opal-task-agent
- **파일**: `opal/core/references/header-standard.md` · `opal/core/references/harness/header-rules.md` · `opal/core/references/pm/code-scan-management.md`
- **작업 내용**: §3.6.2 (1)(2)(3) 표대로 개정한다. `header-rules.md` 기록 위치 판정표는 §3.6.2 (2)의 **확정 3행 표**를 그대로 옮기고 폐쇄 도메인 문장을 **3값 기준**으로 쓴다(TS-053·TS-068). `header-standard.md` §7·`code-scan-management.md`에서 **`auto`를 유효값으로 서술하는 문장을 전량 제거**한다(TS-067). `code-scan-management.md` 최소 구조 예시에 `headerSource` 포함(H-11 영속 해결) · PM 최초 설정 절차 신설(역할명만) · M-1 stale 인용(`:73`) 교정. 3문서 모두 변경이력 표에 행 추가 — [MUST] `docs/CONVENTIONS.md` §변경이력 작성 의무: 일시 `YYYY-MM-DD HH:mm`(KST), semver, 태스크 번호 `(080)` 포함.
- **완료 기준**: TS-050~TS-054 · TS-067 · TS-068(`header-rules.md` 분) GREEN · `readonly` 판정 근거 서술 0건 · **`auto` 유효값 서술 0건** · `reason`/`write_to` 각 3값 반영 · 개인 식별자 신규 기재 0건
- **테스트**: TS-050, TS-051, TS-052, TS-053, TS-054, TS-067, TS-068
- **실행 방법**: sub-agent
- **의존**: Step 7

#### Step 11: F-006 — 규칙 문서 2종 (PM Gate·도구 레퍼런스)
- [x] 완료 (2026-08-02 15:05 · PM Gate Pass)
- **소속 기능**: F-006, F-005
- **영역**: 문서
- **agent**: opal-task-agent
- **파일**: `opal/core/references/harness/pm-review-gate.md` · `opal/core/references/tools.md`
- **작업 내용**: §3.6.2 (4)(5) 표대로 개정한다. `pm-review-gate.md` 8번 — `readonly` 서술 제거·모드별 커버리지·**미설정 대응 소절 신설**(F-12④). `tools.md` — `--header-source` 옵션 행·전 명령 공통 종료 코드 표·설정 예시(`headerSource` + `scopes` 객체)·**M-2 교정(`:240`)은 `reason` 3값과 `write_to` 3값을 축별로 분리 서술**(TS-068)·**`auto` 유효값 서술 제거**(TS-067). 2문서 변경이력 행 추가.
- **완료 기준**: TS-050~TS-052 해당 항목 · TS-067 · TS-068(`tools.md` 분) GREEN · `tools.md` 종료 코드 표에 신규 에러 코드 4종 등재 · `write_to`/`reason` 도메인이 한 목록에 섞이지 않음
- **테스트**: TS-050, TS-051, TS-052, TS-067, TS-068
- **실행 방법**: sub-agent
- **의존**: Step 7

#### Step 12: `docs/` 3종 갱신
- [x] 완료 (2026-08-02 15:08 · PM 직접 수행 · TS-055 GREEN)
- **소속 기능**: F-006
- **영역**: 문서
- **agent**: PM 직접
- **파일**: `docs/CONVENTIONS.md` · `docs/ARCHITECTURE.md` · `docs/PROJECT.md`
- **작업 내용**: §3.6.2 (6)(7)(8)대로 갱신한다. `CONVENTIONS.md:174`의 "(읽기 전용 스코프는 code-map 강제)"를 "(전역 `headerSource`가 `manifest`이면 code-map 강제)"로 교정한다 — 이는 §1.4 [MUST] 인용문 자체의 갱신이므로 PM이 직접 수행한다. `ARCHITECTURE.md:82`·`PROJECT.md` 변경이력에 Task 080 행 추가.
- **완료 기준**: TS-055 GREEN · 3문서 변경이력 행 존재
- **테스트**: TS-055
- **실행 방법**: direct
- **의존**: Step 10, Step 11

#### Step 13: 골든 재캡처 + diff 근거 기록
- [x] 완료 (2026-08-02 15:15 · PM Gate Pass · diff 0건)
- **소속 기능**: F-007
- **영역**: 환경
- **agent**: opal-task-agent
- **파일**: `opal/tools/code-scan/tests/fixtures/golden/*.{json,txt}` (8개) · `opal/tools/code-scan/tests/fixtures/golden/README.md`
- **작업 내용**: §3.7.3의 캡처 명령을 실행해 골든 8종을 재캡처한다. `git diff --stat`으로 077 골든과의 차이를 확인하고 결과를 `README.md`에 기록한다. **예측은 차이 0이다** — 차이가 발견되면 GREEN 완료로 처리하지 말고 원인을 규명하여 PM에 보고한다(H-10).
- **완료 기준**: TS-060, TS-061 GREEN · `README.md`에 diff 결과와 근거 기록
- **테스트**: TS-060, TS-061
- **실행 방법**: sub-agent
- **의존**: Step 7, Step 9

#### Step 14: 전량 GREEN 확인 + 자기 게이트
- [x] 완료 (2026-08-02 15:24 · PM Gate Pass · 191/191 exit 0 · 봉인 6/6)
- **소속 기능**: F-007
- **영역**: 테스트
- **agent**: opal-test-agent
- **파일**: (검증 전용 — 소스 수정 없음)
- **작업 내용**: `node --test "opal/tools/code-scan/tests/*.js"` 전량 pass·exit 0을 확인한다. 이 태스크의 `changed_files`에 대해 `code-scan validate --changed <목록> --json`을 실행해 `newly_uncovered` 0건·`worker_scope_violation` 0건을 확인한다(077 자기 게이트 선례 `tasks/077-.../DONE.md:44`). [MUST] `red-first.md` §3에 따라 이 Step에서도 테스트 파일을 수정하지 않는다 — 실패가 남으면 구현 Step으로 되돌린다.
- **완료 기준**: exit 0 + `validate --changed` `ok: true` + **봉인 검사 6종** 최종 재확인 — 잔존 4종(TS-066 소스 `auto` · TS-067 문서 `auto` · TS-034 소스 `readonly` · TS-051 문서 `readonly`) + 단일 지점 2종(TS-013 필터 판정 `isInScope` 1곳 · **TS-070 모드 판정 `resolveHeaderSource` 1곳**)
- **테스트**: TS-062, TS-064 + 봉인 검사 재확인(TS-013, TS-034, TS-051, TS-066, TS-067, TS-070) + 전체 회귀
- **실행 방법**: sub-agent
- **의존**: Step 8, Step 12, Step 13

### 4.3 병렬/순차 판별 근거

| 관계 | 근거 |
|------|------|
| Step 1 → Step 2 | RED 테스트가 픽스처 자산을 참조한다 (H-9 — 픽스처 미갱신 시 100 케이스 전량 exit 1) |
| Step 2 → Step 3 | [MUST] `red-first.md` §1: "RED 증거 없이 GREEN 진입 금지" |
| Step 3 → Step 4 → Step 5 | 동일 파일(`code-scan.js`) 순차 수정 + Step 4의 `isInScope`가 Step 5 배선의 전제 |
| Step 4 → Step 6 | `normalizeIndexScope`(Step 4)가 `readonly` 흡수 지점(Step 6)이다 |
| Step 5, Step 6 → Step 7 | `decideTarget`이 `resolveScope`(Step 5 배선)와 스코프 `headerSource`(Step 6)를 동시에 소비한다 |
| Step 8 ∥ Step 9 | 독립 파일 (`code-map-hook.js` ↔ `.opal/code-scan.json`), 상호 참조 없음 |
| Step 10 ∥ Step 11 | 독립 파일 5종, 상호 참조 없음 |
| Step 10, 11 → Step 12 | `docs/`는 규칙 문서의 상위 요약이므로 하류 정합 확보 후 갱신 |
| Step 7, Step 9 → Step 13 | 골든은 구현 완료 + 저장소 설정 반영 후에만 유효 |
| Step 8, 12, 13 → Step 14 | 최종 회귀는 전 변경 반영 후 |

---

## 5. QA 체크리스트

### 5.1 기능별 QA

| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | 미설정 시 전 명령이 동일 에러·동일 exit code로 거부되고 해결 방법·근거 문서가 포함된다 | TS-001, TS-002 | 13커맨드 exit 1 + stdout JSON + stderr 3줄 |
| F-001 | `auto` 명시 거부 + CLI 플래그 동작 + **우선순위 2층(CLI > 전역)** + 스코프 오버라이드 부재 | TS-003~TS-006 | 각 케이스 기대값 일치 · 실행당 1값 확정 |
| F-001 | **스코프 오버라이드 재도입 봉인 — 두 파일 대칭** | TS-005(`index.json`), TS-069(`code-scan.json`) | 양쪽 모두 무시 + 안내 1줄(중복 0, stdout 무오염) |
| F-001 | **모드 판정 지점이 `resolveHeaderSource` 1곳** | TS-070 | `config.headerSource`/`opts.headerSource` 출현이 해당 함수 밖 0건 |
| F-001 | **실행당 1값 — 두 스코프 동일 모드 + 4경로 일치 + 전역값만 뒤집기** | TS-072, TS-073, TS-074 | 스코프별 예외 0건 · 5경로 동시 반전 |
| F-004 | `discover` 산출물에 모드 키 0건 | TS-071 | `scopes[]`에 `headerSource` 0건 |
| F-002 | `include`/`exclude` 타입 위반 거부 | TS-075 | 3케이스 전부 전용 에러 코드로 exit 1 |
| F-002 | 문자열 하위호환 + 객체 형식 스키마 통과 | TS-010, TS-011 | 픽스처 20종 무수정 동작 |
| F-002 | 5개 지점이 동일 파일 집합을 판정하고 필터 판정 로직이 1곳 | TS-012, TS-013 | 교차 검증 일치 + grep 0건 |
| F-002 | 스코프 중복 우선순위 (include 승리 / 양쪽 매칭 = 명시 에러 / 사전순 회귀) | TS-016~TS-018 | 3케이스 전부 |
| F-002 | **`target` 스코프 필터 신규 배선** — 탈락 파일 반환 계약 + hook 무영향 + 미사용 프로젝트 회귀 | TS-035~TS-037 | `{write_to:'none', reason:'out_of_scope'}` exit 0 · hook stdout 0바이트 · `out_of_scope` 오발동 0건 |
| F-003 | 두 모드에서 `target`이 각각 단일 값을 반환 | TS-020, TS-021 | 모드 축 `reason` 2값 (전체 도메인은 `out_of_scope` 포함 3값) |
| F-001 | **무효값 3경로** — `auto` 특례 / CLI 일반 / config 일반, 각각 `where` 식별 | TS-003, TS-009, TS-065 | 3케이스 전부 exit 1 + `where` 필드 정확 · 힌트 유무 구분 |
| F-001 | **`auto` 소스 자산 잔존 0건** | TS-066 | 마이그레이션 힌트 1개소 외 `auto` 리터럴 0건 |
| F-006 | **`auto` 문서 잔존 0건 + 도메인 3값 정합** | TS-067, TS-068, TS-053 | 3문서 `auto` 유효값 서술 0건 · `reason`/`write_to` 각 3값 반영 |
| F-003 | `inline` 모드 `scaffold` no-op + 사유 보고 | TS-023 | `.opal/code-map/` 파일 생성 0건 |
| F-003 | 모드별 커버리지 + 반대 소스 부재 비집계 | TS-024~TS-026 | 동일 픽스처 2모드 대조 |
| F-004 | `readonly` **무시 + 안내**(전역값 적용) 양방향 + `discover` 산출물 정합 | TS-030~TS-034 | 5케이스 전부 · `manifest` 흡수 0건 |
| F-005 | hook 3케이스 무출력 exit 0 + 정상 경고 보존 | TS-040~TS-043 | stdout 0바이트 |
| F-005 | `brain-tool sync-header`가 사유를 그대로 노출 (`brain_tool.py` 무수정) | TS-045 | detail에 `header_source_unset` |
| F-005 | `.gitignore` 예외로 이 저장소 설정이 추적된다 | TS-046, TS-047 | `code-scan.json` 비무시(exit 1) · `code-map/index.json` 비무시 유지 |
| F-006 | 5문서 변경이력 + `readonly` 판정 서술 0건 + 개인 식별자 0건 | TS-050~TS-054 | 산출물 검사 |
| F-007 | 명시 설정 상태 골든 바이트 동일 + diff 근거 기록 | TS-060, TS-061 | `git diff --stat` 결과 기록 |
| F-007 | 전 테스트 GREEN | TS-062 | exit 0 |

### 5.2 회귀 테스트

- [ ] `node --test "opal/tools/code-scan/tests/*.js"` 전량 pass · exit 0
- [ ] 골든 8커맨드 바이트 동일 (명시 `headerSource: inline` 상태)
- [ ] `scan --json` 결과에 `_source` 키 0건 (`inline` 모드)
- [ ] `tiebreak` 픽스처 사전순 판정 결과 불변 (include 미사용 프로젝트 — H-4)
- [ ] `uncovered:pre_existing` 비차단 · 나머지 5종 차단 · exit 2 정책 불변
- [ ] `module.exports` 10개 심볼 시그니처 불변 (`code-scan.js:1739-1750`)
- [ ] **모드가 실행당 1값** — 같은 실행 안의 서로 다른 파일·스코프가 모두 동일 모드를 보고 (TS-006)
- [ ] **`readonly` 흡수 코드 0건** — `manifest`로 해석하는 경로가 남아 있지 않음 (TS-030 역방향 포함)
- [ ] `code-map-hook.js` 전 경로 fail-safe(`:151-158`) 불변
- [ ] `brain_tool.py` 변경 0줄
- [ ] `--help` / `--version`이 미설정 상태에서 exit 0

### 5.3 코드/문서 품질

- [ ] Node 표준 모듈만 사용 — `require` 대상이 `fs`/`path`/`child_process`뿐 ([MUST] TASK.md §제약 조건)
- [ ] 규칙 문서 5종 + `docs/` 3종 변경이력 행 추가 (버전·`YYYY-MM-DD HH:mm` KST·`(080)`)
- [ ] `~/.opal/` 배포 파일 직접 편집 0건 ([MUST] `docs/CONVENTIONS.md` §배포 경계)
- [ ] 규칙·문서에 개인 식별자 신규 기재 0건 (역할명 PM/소유자만)
- [ ] `code-scan.js` `VERSION` = `1.4.0` + 변경이력 행
- [ ] 신규 테스트 2파일에 `layer: test` @header + `task: "080"` + `scenarios`
- [ ] 스코프 필터 판정 로직이 `isInScope` 외 0곳 ([MUST] `opal/core/PRINCIPLES.md` §2)
- [ ] **`auto` 완전 제거 확인** — `code-scan.js` 리터럴은 마이그레이션 힌트 1개소로 한정(TS-066) · 규칙 문서 3종에 유효값 서술 0건(TS-067)
- [ ] **도메인 정합** — `reason` 3값·`write_to` 3값이 §1.5·§3.2.2 (C-bis)·§3.3.2 (B)·§3.6.2 (2)(5)·구현·테스트에서 모두 동일 (TS-053, TS-068)

### 5.4 보안

- [ ] 에러 메시지에 절대 경로·사용자명 등 환경 정보가 과도하게 노출되지 않는가 (프로젝트 상대 경로만 사용)
- [ ] `.opal/code-scan.json`·`.opal/code-map/` 에 토큰·시크릿이 기재되지 않는가
- [ ] `--header-source` 인자가 파일 경로·셸로 전달되지 않는가 (값 도메인 2택 화이트리스트 검증)
- [ ] stdout JSON 오염 0건 — 안내·경고는 전부 stderr (파이프 소비자 `brain_tool.py:793` 보호)
- [ ] 신규 파일 생성 경로가 `.opal/code-map/` 하위로 한정되는가 (경로 이스케이프 방지)

---

## 6. 복잡도 판별

| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 14개 (TS 67종) | 복잡 (6개 이상) |
| 변경 파일 수 | **약 47개** (도구 2 · 설정 2[`.opal/code-scan.json`+`.gitignore`] · 테스트 10 · 픽스처 20+**신규 트리 2**(`mixed-scope`·`mixed-scope-ambiguous`) · 골든 9 · 규칙 문서 5 · docs 3) | 복잡 (4개 이상) |
| 모듈 범위 | 다중 (code-scan 도구 · hook · brain-tool 소비 계약 · 규칙 문서 SSOT · 프로젝트 docs) | 복잡 |
| v2.0 축소분 | 함수 1개 · 우선순위 1층 · index 스키마 키 1개 · 문서 절 1개 제거 (§12) — Step·파일 수는 불변 | 복잡 유지 |
| 작업 유형 | 대규모 개선 + **계약 파기**(제약②) | 복잡 |
| 외부 의존성 | 없음 (Node 표준 모듈만) | 단순 |
| **실행 모드** | **복잡** | |

---

## 7. 실행 아키텍처 (복잡 모드)

### C-1. 에이전트 토폴로지

```
Batch 1  ── A1: opal-task-agent   [Step 1]           픽스처 계약
              ↓
Batch 2  ── A2: opal-test-agent   [Step 2]           RED 일괄 (작성자≠구현자)
              ↓
Batch 3  ── A3: opal-task-agent   [Step 3→4→5→6→7]  code-scan.js 단일 소유 (파일 충돌 방지)
              ↓
Batch 4  ── A4: opal-task-agent   [Step 8]  ∥  A5: opal-task-agent [Step 9]
              ↓
Batch 5  ── A6: opal-task-agent   [Step 10] ∥  A7: opal-task-agent [Step 11] ∥ (PM: Step 12는 A6·A7 후)
              ↓
Batch 6  ── A8: opal-task-agent   [Step 13]          골든 재캡처
              ↓
Batch 7  ── A9: opal-test-agent   [Step 14]          전량 GREEN + 자기 게이트
```

**그룹핑 근거**: A3가 Step 3~7을 단독 소유하는 것은 5개 Step이 전부 `code-scan.js` 한 파일을 수정하기 때문이다(`plan-guide.md` §C-1 우선순위 1). A2와 A3를 분리한 것은 [MUST] `red-first.md` §2 "RED 테스트 코드 작성 주체는 EXECUTE 구현 워커와 분리한다".

### C-2. 스킬 요구사항

| 에이전트 | 스킬 | 갭 |
|---------|------|---|
| A1, A3~A8 | `op-dev-execute` | 없음 |
| A2, A9 | `opal-test-agent` (mode: red / 검증) | 없음 |
| 전원 | `opal/core/references/harness/red-first.md` · `header-standard.md` · `header-rules.md` | 없음 — 기존 참조 문서로 충족 |

3개 이상 Step에서 반복되는 패턴은 "동일 파일 순차 수정"뿐이며 스킬화 대상이 아니다 → **신규 스킬 불필요**.

### C-3. 도구 요구사항

| 항목 | 값 |
|------|---|
| 런타임 | Node.js 18+ (기존 요구사항 — `run.sh:9` `Install Node 18+`) |
| 테스트 러너 | `node --test "opal/tools/code-scan/tests/*.js"` — **glob 형태 필수** (Node v25.8.2에서 디렉토리 인자는 MODULE_NOT_FOUND, `tasks/077-.../AGENTIC-LOG.md:30`) |
| 신규 패키지 | 없음 ([MUST] TASK.md §제약 조건 무의존) |
| 검증 도구 | `code-scan validate --changed`(자기 게이트) · `brain-tool sync-header`(L2 실 subprocess) · `git diff --stat`(골든) |
| MCP | 사용 없음 |

### C-4. 테스트 전략

| 계층 | 대상 | 실행 |
|------|------|------|
| L1 (단위/CLI 블랙박스) | `isInScope` · `resolveScopeIn` · `resolveHeaderSource` · `decideTarget` | `node --test` 개별 파일 |
| L2 (통합) | 5지점 교차 일관성 · 모드별 `validate` 대조 · hook stdin 주입 · `brain-tool` 실 subprocess | `node --test` 전량 + 수동 subprocess |
| L3 (회귀) | 골든 8커맨드 바이트 대조 · 저장소 루트 자기 게이트 | Step 13, 14 |

RED 증거는 Step 2 완료 시 `RED-EVIDENCE.md`에 기록하고, [MUST] `red-first.md` §3에 따라 Step 3~14 동안 테스트 파일을 수정하지 않는다.

---

## 8. 기술 컨텍스트

### 8.1 기술 스택

| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| 도구 | Node.js (무의존, CommonJS) — `code-scan.js` v1.3.3 → v1.4.0 | op-dev-execute |
| 테스트 | `node:test` + `node:assert/strict` (CLI 블랙박스 8파일 100 케이스) | opal-test-agent |
| 설정 | JSON — `.opal/code-scan.json` · `.opal/code-map/index.json` | - |
| 문서 | Markdown — 규칙 SSOT 5문서 + `docs/` 3문서 | op-dev-execute |
| 소비자 | Python — `brain_tool.py` (subprocess 소비, 무수정 목표) | - |

### 8.2 사용 MCP

| MCP | 조회 결과 요약 |
|-----|--------------|
| (없음) | Node 표준 모듈만 사용하며 외부 라이브러리 API 확인이 불필요하다 — [MUST] TASK.md §제약 조건 "외부 npm 의존 금지" |

### 8.3 참조 문서 (설계 결정 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | code-scan.js | `opal/tools/code-scan/code-scan.js` | 전 설계의 1차 근거 — `loadConfig:193-213` · `resolveScope:557-569` · `resolveHeader:688-751` · `decideTarget:755-791` · `cmdValidate:1448-1657` · `main:1696-1733` |
| D-2 | 설계 | header-standard.md | `opal/core/references/header-standard.md` | §7 2소스 스키마 SSOT · `readonly` 정의(`:206`) · `files` 집합 일치 서술(`:219`) |
| D-3 | 설계 | header-rules.md | `opal/core/references/harness/header-rules.md` | 기록 위치 4단 판정표(`:14-27`) · 커버리지 합산(`:51-55`) · 저커버리지 폴백(`:131`) |
| D-4 | 설계 | pm-review-gate.md | `opal/core/references/harness/pm-review-gate.md` | 검토 절차 8번의 code-scan 호출 3종(`:52-62`) |
| D-5 | 설계 | code-scan-management.md | `opal/core/references/pm/code-scan-management.md` | 생성 규약(`:10-31`) · `headerSource` 관리(`:63-73`) · stale 인용 M-1(`:73`) |
| D-6 | 소스 | brain_tool.py | `opal/tools/brain-tool/brain_tool.py:766-798` | `sync-header`의 subprocess 소비 + stderr-only detail 전달(`:790-792`) |
| D-7 | 기획 | 080 TASK.md | `tasks/080-260801-opd-헤더소스-단일화/TASK.md` | 확정 방향 D-1~D-5 · 개선 A 보강 5건 · 동반 필수 작업 5건 · F-1~F-13 AC |
| D-8 | 기획 | 077 DONE.md | `tasks/077-260727-opd-코드맵-헤더작성층/DONE.md` | 이관 결정 원문(`:71-80`) · 설계 결정 6건(`:27-34`) · dogfooding 결함 5건(`:48-58`) |
| D-9 | 소스 | code-map-hook.js | `opal/tools/code-scan/code-map-hook.js` | fail-safe 계약 — 조기 이탈 9단(`:88-148`) · 전 경로 try/catch(`:151-158`) |
| D-10 | 설계 | tools.md | `opal/core/references/tools.md:202-306` | code-scan 커맨드·옵션·종료 코드·설정 예시 |
| D-11 | 설계 | red-first.md | `opal/core/references/harness/red-first.md` | RED-first 적용 기준(§1.5) · 작성자≠구현자(§2) · 테스트 불변성(§3) |
| D-12 | 설계 | PRINCIPLES.md | `opal/core/PRINCIPLES.md` §2 | Simplicity First — 필터 판정 단일 함수 계약의 근거 |
| D-13 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | @header 규칙(`:171-176`) · 변경이력 작성 의무(`:197-201`) · 배포 경계(`:203-208`) · 언어 규칙(`:5-12`) |
| D-14 | 소스 | 테스트 자산 | `opal/tools/code-scan/tests/` | 픽스처 20종 설정 · 골든 8종 · 100 케이스 계약 |
| D-15 | 설계 | citation-rules.md | `opal/core/references/harness/citation-rules.md` | 인용 포맷 4종 · [MUST] 토큰 대상 6종(§2.5) |
| D-16 | 기획 | 080 ANALYSIS.md | `tasks/080-260801-opd-헤더소스-단일화/ANALYSIS.md` | 독립 교차 검증 — V-3(`target` 무필터)·V-9(`brain_tool.py` stderr 경로)·V-11(줄번호)·V-12(gitignore)·§9(`codemap-repo` 그룹 A/B/C 판정) |

---

## 9. 리스크 및 대응

| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| R-1 | 전 명령 차단이 소비자 3종(brain-tool·PM Gate·hook)을 동시에 멈춘다 | F-001, F-005 | P0 | stderr 병기(§3.1.2 (F))로 brain-tool 무수정 대응 · hook 조기 이탈(§3.5.2) · PM Gate 절차 신설(§3.6.2 (4)) · TS-040~TS-045로 3경로 전부 검증 |
| R-2 | `loadConfig`에 게이트를 넣으면 hook fail-safe가 붕괴한다 | F-001 | P0 | `loadConfig` 무종료 계약을 [MUST]로 못박고(§3.1.2 (B)) 게이트를 `main()`에만 배치 · TS-040/041로 회귀 방어 |
| R-3 | 픽스처 20종 미갱신 시 기존 100 케이스가 전량 붕괴 | F-007 | P0 | Step 1을 RED보다 선행 배치 · TS-063 산출물 검사로 누락 검출 |
| R-4 | 필터 배선 누락으로 077 결함 D와 동형 오탐 재발 | F-002 | P0 | `isInScope` 단일 계약 + TS-012(5지점 교차) + TS-013(grep 산출물 검사) 2중 방어 |
| R-5 | `resolveScope` 우선순위 변경이 include 미사용 프로젝트의 매니페스트 귀속을 바꾼다 | F-002 | P1 | include 매칭 0개일 때 기존 사전순 경로를 그대로 보존(§3.2.2 (D) ⑥) + TS-018 tiebreak 회귀 |
| R-6 | `target.reason` 도메인 축소가 문서·테스트 명문 계약을 깬다 | F-003 | P1 | 계약 변경을 §1.5에 명시 선언 · `header-rules.md`·`tools.md` 동시 갱신(Step 10, 11) · hook은 값에 의존하지 않음을 확인(`code-map-hook.js:70`) |
| R-7 | 합산 커버리지 폐기로 PM Gate가 오판정한다 | F-003, F-006 | P1 | `pm-review-gate.md:57`·`header-rules.md:53,131` 3지점 동시 갱신 · `validate --json`에 `headerSource` 필드 추가로 소비자가 모드를 식별 가능 |
| R-8 | 이 저장소 `.opal/code-scan.json`이 gitignore라 설정이 커밋되지 않는다 → 신규 clone·CI에서 저장소 자신이 즉시 전 명령 차단 | F-005 | P1 | **결정: `.gitignore`에 `!.opal/code-scan.json` 예외 추가**(§3.5.3, Step 9) + `code-scan-management.md` 생성 규약에 `headerSource` 포함(영속 예방, Step 10). 부수 비용인 077 TS-055 반전은 H-14·Step 2로 흡수 |
| R-9 | 골든 재캡처에서 예상치 못한 바이트 차이 발생 | F-007 | P1 | 차이 0을 **예측이자 검증 조건**으로 명문화(§3.7.3) · 차이 발생 시 GREEN 처리 금지, 원인 규명 후 PM 보고 |
| R-10 | `codemap-repo` 픽스처가 `auto` 전제로 만들어져 한 트리에서 2동작을 검증할 수 없다 | F-007 | P1 | **결정 완료(§3.7.2)** — 픽스처 자산은 무변경, 테스트만 재배치. 그룹 A 그대로 이전 / 그룹 B 명제 교체 / **그룹 C(077 TS-005) 폐기 + 불변식은 077 TS-044·TS-045로 분할 승계**. 신규 재정의 테스트를 만들지 않는 이유는 승계처가 이미 존재해 중복이 되기 때문 |
| R-11 | brain 지식 페이지 3건이 구 계약("5단 상속·인라인 단독 승리·`readonly` 1순위 4단 판정")을 서술한 채 남는다 — 전역 단일 키 결정으로 어긋남이 더 커졌다 — `.opal/brain/pages/concept/code-header-dual-source-inheritance.md`, `.../code-map-write-location-decision.md`, `.../entity/code-scan-tool.md` | F-006 | P2 | **본 태스크 범위 밖**(TASK.md §범위에 brain 미포함). CLOSE 후 `op-brain-ingest`로 3페이지 갱신을 후속 제안 — PM 판단 사항 |
| R-12 | `manifest` 모드 + index.json 부재의 조용한 실패 | F-003 | P2 | stderr 경고 1줄 비차단(§3.3.2 (A)) — 차단 조건 추가는 D-5 범위를 넘으므로 의도적 fail-soft · TS-028 |
| R-13 | 용어 불일치 — 문서의 "5단 상속"(`header-standard.md:189`) ↔ 신 계약의 "모드별 tier① 단독 / tier②~⑤ 4단" | F-006 | P1 | `header-standard.md` §7 전면 개정으로 용어 통일(Step 10) · TS-051/TS-053 산출물 검사로 잔존 검출 |
| R-14 | 규칙 문서에 개인 식별자가 신규 유입될 위험 (PM 절차 신설 시) | F-006 | P2 | [MUST] TASK.md §제약 "역할명(PM/소유자)만 사용" 준수 · TS-052 산출물 검사 |
| R-15 | **`target`이 F-8의 5지점 중 유일하게 필터가 없던 공백 지점** — `decideTarget`(`:755-791`)의 `isExcluded`/`hasExcludedSegment` 호출 0건. 반환 계약 없이 배선하면 스코프 밖 파일에 경로 없는 `write_to: manifest`가 나간다 | F-002 | **P0** | §3.2.2 (C-bis)에 반환 계약을 명문화(`write_to:'none'`/`reason:'out_of_scope'`/exit 0/hook 무영향) · Step 5 항목 ⑤를 "확인"→"신규 배선"으로 승격 · TS-035~TS-037 (→ H-13) |
| R-16 | `.gitignore` 예외 채택이 077 TS-055 단언을 반전시킨다 | F-005, F-007 | P1 | §1.5 계약 변경표에 반전을 명시 선언 + Step 2 작업 내용에 반전 지시 3건 중 ③으로 포함 (→ H-14) |
| R-17 | **`readonly: true` 프로젝트의 `target` 결과가 바뀐다** — 초판(흡수)에서는 `manifest`였으나 무시 전환으로 전역값을 따르므로, 전역이 `inline`인 프로젝트에서는 `manifest` → `inline`으로 뒤집힌다 | F-004 | P1 | §1.5 제약② 파기 범위 안에서 수용. **안내 1줄이 사용자에게 이 변화를 알리는 유일한 접점**이므로 문구에 전역 설정 방법을 필수 포함(TS-031) + 양방향 TS-030·TS-033으로 고정 |
| R-18 | 스코프 오버라이드 제거가 **되살아난다** — 후속 작업자가 "스코프마다 다른 소스" 요구를 받고 두 설정 파일 중 어느 쪽에든 모드 키를 재도입 | F-001, F-006 | **P1**(v2.1 상향) | **봉인 4중**: 부정 단언 TS-005(`index.json`)·**TS-069(`code-scan.json`)** 대칭 쌍 + **TS-070**(판정 지점 grep — 재도입 시 `resolveHeaderSource` 밖에서 판정이 생기므로 즉시 검출) + **TS-071**(`discover` 산출물 모드 키 0건) + `header-standard.md` §7 "전역 단일 키" 명시(§3.6.2 (1)) + 무시 시 안내 1줄로 시도를 즉시 노출 |

---

## 10. Full Task 에스컬레이션 검토

TASK.md는 이 작업을 `opds`(Short Task)로 시작했으나, 설계 결과 **세 가지 에스컬레이션 신호를 모두 충족**한다. 전환 여부는 PM·소유자가 결정한다.

| 신호 | 기준 | 실측 | 판정 |
|------|------|------|------|
| 예상 변경 파일 | 10개 이상 | **약 47개** — 도구 2 · 설정 2(`.opal/code-scan.json`·`.gitignore`) · 테스트 10(신규 2 포함) · 픽스처 20+**신규 트리 2** · 골든 9 · 규칙 문서 5 · `docs/` 3 | **해당** |
| 다단계 기술 의사결정 | 있음 | ① `auto` 제거에 따른 상속 단수 재정의(5단 → 모드별 1단/4단) ② 두 스코프 레지스트리의 단일 내부 형태 통일 ③ 우선순위 **2층**(CLI > 전역) 확정 — 스코프 오버라이드 기각(2026-08-02 소유자 결정) ④ `reason`/`write_to` 도메인 재정의(모드 축 2값 병합 + 필터 축 `out_of_scope` 신설 = 각 3값) ⑤ 모드별 검출기 분기 ⑥ 픽스처 모드 배정 ⑦ 무효값 3경로 분리(`auto` 특례 / CLI·config 일반) | **해당** |
| 3개 이상 독립 모듈 연쇄 영향 | 3개 이상 | ① `code-scan.js` ② `code-map-hook.js` ③ `brain_tool.py` 소비 계약 ④ 규칙 문서 SSOT 5종 ⑤ 프로젝트 `docs/` 3종 ⑥ 테스트·픽스처·골든 자산 | **해당** (6개) |

**추가 근거**: `plan-guide.md` §4.2 "Short Task: 5개 이하 Step 권장. 초과 시 Full Task 에스컬레이션 고려" 대비 **14 Step**으로 2.8배다. 또한 §1.5의 제약② 파기는 077이 명시적으로 지킨 최상위 계약을 뒤집는 것이므로, ANALYSIS 단계와 별도 QA Gate를 갖춘 Full Task 파이프라인(`opd`)의 검증 밀도가 적절하다.

**Short Task 유지 시 권고**: Phase를 2회 이상 나누어 PM Gate를 중간 삽입한다 — 최소한 Batch 3(구현 완료) 직후와 Batch 7(전량 GREEN) 직후 2회.

---

## 11. 문서/코드 불일치 보고

> [MUST] 지시사항: "문서와 실제 코드가 다르면 **코드(실질적 문서) 기준**으로 설계하고, 불일치 사항을 PLAN.md에 별도로 보고한다."

### 11.1 TASK.md 줄번호 스냅샷 교정

| TASK.md 기재 | 실제 위치 | 판정 |
|-------------|----------|------|
| `resolveHeader` `:690-699` | 함수 전체 `:688-751`, `headerSource` 소비 3줄은 `:690`·`:693`·`:699` | **범위 교정** — 인용은 `:688-751`(함수) / `:690-701`(모드 분기) |
| `decideTarget` `:755-792` | `:755-791` (`:792`는 공백줄) | **off-by-one 교정** |
| `resolveScope` `:557-569` | `:557-569` | 일치 |
| `files_key_removed` `:1582` | 실제 push는 `:1597`. `:1581-1582`는 `structExcludeDirs`/`structExcludePatterns` 변수 선언 | **교정** — 검출기 블록은 `:1595-1599` |
| `inferScopes` `:1093` | `:1093-1110` | 일치 |
| `readonly` 전량 `:761`·`:1098`·`:1107` "그 외 없음" | 위 3곳 + **`cmdDiscover` note 문자열 `:1199`** | **보완** — 문자열 1건 누락 |
| `loadConfig` `:193-213` | `:193-213` | 일치 |
| index 스키마 검증 `:524 부근` | `loadCodeMap` `:506-533`, `scopes` 객체 검증 `:524-531` | **범위 교정** |
| `brain_tool.py:766-798` / `:786-793` | 동일 | 일치 |
| `header-standard.md:206` readonly | 동일 | 일치 |
| `code-scan.js` v1.3.3 · 1,774줄 | 동일 (`VERSION` `:37`, `wc -l` 1774) | 일치 |

### 11.2 문서 ↔ 코드 불일치 (선행 결함 — 이번 태스크에서 교정)

| # | 위치 | 문서 서술 | 실제 코드 | 조치 |
|---|------|----------|----------|------|
| M-1 | `code-scan-management.md:73` | "…`auto`로 자동 폴백한다(`code-scan.js:187-190`)" | 해당 로직은 `code-scan.js:198-202` | Step 10에서 행 번호 인용 삭제 (동작 서술로 대체 — 행 번호 인용은 재drift 원인) |
| M-2 | `tools.md:240` | "기록 위치 판정 (4단: `inline_exists`/`readonly_repo`/`legacy_no_header`/`manifest`)" | 실제 `reason` 4값은 `readonly_repo`/`inline_exists`/`new_file`/`legacy_no_header`. `manifest`는 `write_to` 값이며 `new_file`이 누락 | Step 11에서 신 계약으로 교체 — **`reason` 3값·`write_to` 3값을 축별로 분리 서술**한다(두 도메인을 한 목록에 섞는 것이 이 오기의 근본 원인). TS-068이 재발을 검사 |
| M-3 | `header-standard.md:219` | "`files` 키는 `dir` 실제 파일 목록과 **집합 일치**" | v1.3.3부터 `exclude`/`excludePatterns` 제외분은 이미 부분집합 (`code-scan.js:1583-1584`) | Step 10에서 보강④ 서술로 교정 |
| M-4 | `header-rules.md:26` | "code-map이 없는 프로젝트는 ①이 성립하지 않으므로 결과는 항상 `inline`" | 현행 코드와 일치하나 신 계약에서는 `headerSource: inline` 설정이 근거가 된다 | Step 10에서 근거 교체 |

### 11.3 TASK.md 미기재 — PLAN에서 보강한 항목

| # | 항목 | 근거 | 반영 위치 |
|---|------|------|----------|
| N-1 | 이 저장소 `.opal/code-scan.json`이 **gitignore 대상**(`.gitignore:2`)이라 F-12① 설정이 커밋되지 않는다 | `git check-ignore -v .opal/code-scan.json` → `.gitignore:2:.opal/*` | §3.5.3, R-8, Step 9·10 |
| N-2 | `code-scan-management.md` **자동 생성 규약**에 `headerSource`가 없으면 PM이 생성한 설정이 생성 직후 게이트에 걸린다 | `code-scan-management.md:12`("사용자 인터럽트 없이 즉석 추론으로 생성"), `:24-31` 최소 구조 예시 | §3.6.2 (3), Step 10 |
| N-3 | 픽스처 `.opal/code-scan.json` **20종**이 전부 `headerSource` 부재 → 게이트 도입 즉시 100 케이스 붕괴 | `find fixtures -name code-scan.json` 20건, 전량 키 없음 | §3.7.2, Step 1, H-9 |
| N-4 | `codemap-repo` 픽스처가 `auto` 전제(한 트리 2동작)라 2택 전환 시 모드 배정 결정이 필요하다 | `fixtures/codemap-repo/.opal/code-map/index.json` + `test-resolve-header.js` 077 TS-004/005 | §3.7.2, R-10 |
| N-5 | `buildCtx`(`:535-539`) 시그니처 확장이 필요하며 **`code-scan.js` 내 호출 지점은 5곳**이다. hook은 `buildCtx`를 호출하지 않고 `ctx`를 직접 조립하므로 **별건**으로 갱신한다 | 호출 5곳 `code-scan.js:799,1161,1314,1400,1449` (`:535`는 정의부이며 호출이 아니다). `cmdFeature`는 `scanHeaders`→`scanAll`(`:799`) 경유이므로 직접 호출 아님 · hook `ctx` 조립 `code-map-hook.js:127` | §3.1.2 (D), Step 3, Step 8 |
| N-6 | brain 지식 페이지 3건이 구 계약을 서술한 채 남는다 | `.opal/brain/pages/concept/*.md` 2건 + `entity/code-scan-tool.md` | R-11 (후속 제안) |
| N-7 | `manifest` 모드 + index.json 부재 상황의 동작이 미정의였다 | `code-scan.js:699` 분기 구조 | §3.3.2 (A), R-12, TS-028 |
| N-8 | **F-8이 말하는 5지점 중 `target`은 현재 필터가 아예 없다** — TASK.md §배경 분석 (4)는 5지점을 대등하게 나열했으나, `decideTarget`은 `isExcluded`·`hasExcludedSegment` 어느 것도 호출하지 않는다. 따라서 배선은 "대체"가 아니라 "신규 도입"이며 반환 계약이 필요하다 | `code-scan.js:755-791` 구간에 필터 유틸 호출 0건 (`isExcluded` 호출은 `:312`·`:1236`·`:1441`·`:1475` 4곳뿐) | §3.2.2 (C)(C-bis), Step 5 ⑤, H-13, R-15, TS-035~037 |
| N-9 | `.opal/code-scan.json` 미추적의 **파급**(신규 clone·CI에서 저장소 자신이 즉시 차단)에 대한 즉시 대응이 필요하다 — 생성 규약 갱신은 새 프로젝트 예방책일 뿐이다 | `.gitignore:2` + `git check-ignore` 실측 · 소비자 3종(`brain_tool.py:786-793`·`pm-review-gate.md:53`·`code-map-hook.js:120`) | §3.5.3 결정(예외 채택), Step 9, R-8, H-14 |

---

## 12. v2.0 설계 축소 정량 요약

> 2026-08-02 소유자 결정(`headerSource` 전역 단일 키)으로 **없어진 복잡도**. Step 수(14)는 불변이고 검증 자산은 오히려 늘었지만(TS 67종 · 픽스처 트리 2개), 줄어든 것은 **런타임 설계 표면적**이다 — 축소한 만큼 그 축소가 유지되는지 감시하는 장치(TS-005·TS-069·TS-070·TS-071)를 함께 넣었다.

| 축 | 단위 | 초판(v1.1) | 축소 후(v2.0) | 삭제분 |
|----|------|-----------|--------------|--------|
| **함수** | 개 | `resolveGlobalHeaderSource` + `effectiveHeaderSource(relPath, ctx)` **2개** | `resolveHeaderSource` **1개** | **−1개** (파일 단위 판정 함수 소멸) |
| **판정 층** | 층 | 3층 (스코프 > CLI > 전역) | **2층** (CLI > 전역) | **−1층** |
| **판정 단위** | - | 파일 단위 (호출마다 재판정) | **실행 단위** (1회 확정 후 상수) | 파일별 재판정 경로 전량 |
| **index 스키마 키** | 개 | `scopes[].headerSource` 신설 + `scopes[].readonly` 정규화 | 둘 다 **허용 키 아님** (무시 + 안내) | **−1개 신설 취소** |
| **스키마 검증 행** | 행 | 3행 (`headerSource` 유효성 / `readonly` 정규화 / 동시 존재 우선순위) | **2행** (둘 다 무시 + 안내) | **−1행**, 나머지 2행도 "검증"에서 "무시"로 단순화 |
| **하위호환 분기** | 분기 | 4분기 (`true` 흡수 / `false` / `headerSource` 동시 / 없음) | **2분기** (키 있음 → 안내 후 무시 / 없음) | **−2분기** |
| **`reason` 값** | 값 | 3값 (불변) | 3값 | 0 — `readonly_repo`는 초판에서 이미 `header_source_manifest`로 흡수 예정이었고, 이제 **흡수 자체가 없어져** 전역값을 따른다 |
| **문서 절** | 절 | `header-standard.md` §7.1에 `scopes[].headerSource` 신규 행 추가 | **추가하지 않음** + `readonly` 행은 "제거됨" 표기 | **−1개 신규 절** |
| **테스트** | 건 | TS-005·TS-006이 스코프 승리 2건 | 동일 2건이 **부정 단언 + 2층 검증**으로 재정의 | 0건 (삭제 대신 방향 반전 — R-18 재발 방지) |
| **`ctx` 계약** | - | `ctx.headerSource`는 "전역 판정 결과"이고 파일별로 다시 계산 | `ctx.headerSource`가 **최종값** | 소비자의 재계산 의무 소멸 |
| **봉인 장치**(v2.1 추가) | 건 | 없음 (선언만) | 4건 — TS-005/TS-069(두 파일 재도입 차단) · TS-070(판정 지점 grep) · TS-071(`discover` 산출물) | **+4건** — 축소를 유지하는 비용. [MUST] `opal/core/PRINCIPLES.md`: "Enforce, don't just advise" |

**구조적 이득**: 모드 판정 지점이 `main()` 1곳으로 수렴하므로 "어느 파일이 어느 모드인가"를 추적할 필요가 사라진다. 이는 F-8이 필터 판정을 `isInScope` 1곳으로 모은 것과 같은 형태의 축소이며, 077이 겪은 "적용 지점 분산 → 조용한 오작동"(`code-scan.js:1759-1774` 변경이력) 리스크를 모드 축에서 **구조적으로 제거**한다.

**유지된 것**: `include`/`exclude`(개선 A)는 그대로다. 이는 *파일 집합 필터*이지 *모드 선언*이 아니며, `out_of_scope` 배선(§3.2.2 (C-bis))과 `reason`/`write_to` 3값 도메인도 모두 불변이다.
