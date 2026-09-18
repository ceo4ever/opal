# DONE: ANALYSIS 분석 코어 공유 SSOT 신설 — 지식 선조회·확정 승계·중복 제거

> 완료일: 2026-08-24 | 적용 스킬: opd (Full Task) | 모드: semi-agentic
> 태스크 폴더: `tasks/100-260822-opd-분석코어-공유SSOT/`

## 1. 한 줄 요약

ANALYSIS·PLAN 두 단계가 공유하는 분석 절차 SSOT(`harness/analysis-core.md`)를 신설하고, 지식 선조회·확정 입력 승계·중복 제거를 규범과 도구 양쪽에 배선해 **이미 확정된 사실의 재도출을 제거**했다.

## 2. 결과 요약

| 항목 | 결과 |
|------|------|
| 변경 파일 | **15건**(신규 1 · 수정 14) |
| 요구사항 | R-1~R-12 / 기능 F-001~F-008 / Step 13개 전건 완료 |
| 시나리오 | S-1~S-33 중 **32 Pass / 1 Fail**(S-33, 소유자 확정) |
| 회귀 테스트 | 단일 파일 340→**347 passed** / 디렉토리 357→**364 passed** — 감소 0건 |
| 게이트 | 목표-커버 게이트 pass(결정론 exit 0 + 평가자 1.67) · 컨벤션 Critical 0 / High 0 |
| 추가작업 | ADD-1(3단-B 조건부 전환) · ADD-2(테스트 @header 갱신) |
| 미수행 | 커밋 · `install` 재배포 (둘 다 소유자 권한) |

## 3. 개정 내용

### 3.1 신규 SSOT

| 파일 | 내용 |
|------|------|
| `opal/core/references/harness/analysis-core.md` (신규 184줄) | §1 지식 선조회 3단 · §2 증분 소비 규율 · §3 델타 탐색 규율 · §4 분석 깊이 기준 · §5 관련 파일 맵 6영역 축 · §6 의존성·영향 범위 도출 · §7 분석 품질 체크리스트 |

절차는 이 문서가 단독 소유하고 산출물 형식은 각 스킬이 소유한다(역할 분리). 타 문서의 수치·목록·개수는 복제하지 않고 포인터만 둔다.

### 3.2 규범 배선

| 파일 | 변경 |
|------|------|
| `opal/core/references/opal-harness.md` | §2 모듈 표에 분석 코어 행 + `### 분석 코어 적용 의무` stub. 최상위 절 번호 불변(H-11 방어) |
| `opal/skills/op-dev-analysis/SKILL.md` | 체크리스트 본문 삭제 → §7 포인터 · 통일 형식에 `## 7 Q표`(권장)·`## 8 다음 단계 입력`·`### PLAN 결정 필요` 실물 섹션 신설 · 판정값 `승계` 추가(3값→4값) |
| `opal/skills/op-dev-analysis/references/analysis-guide.md` | 163→**108줄**. Glob/Grep 직행 서술 삭제 → §1 포인터(PM 규범 충돌 해소), 깊이·의존성·영향범위·체크리스트 4구간 이관 |
| `opal/skills/op-dev-analysis/references/tech-context-guide.md` | 미등록 MCP 하드코딩 목록 삭제 → 등록본 조회 규칙 · §6을 「프로젝트 SSOT 경로 + 델타」 2필드로 재설계 |
| `opal/skills/op-dev-plan/references/plan-guide.md` | 477→**459줄**. 0단계에 `analysis-core.md` Read 지시 · 2단계 절차 문단 **7→4**(감소 3, 포인터 3 대응) · 승계 `[MUST]` 3곳(`:92`·`:96` 승격·`:102`) |
| `opal/skills/op-dev-qa/references/qa-dev-guide.md` + `op-dev-qa/SKILL.md` | 검증 축 3개 신설(R-7 원문 덤프 차단 · R-8 098 규약 준수 · P-8 확정 승계 준수) + 거울 사본 동시 갱신(H-4 방어) |
| `opal/skills/opal-pilot-dev/SKILL.md` | STEP 2 디스패치 프롬프트에 `**분석 질문**:` 슬롯 |
| `opal/skills/opal-pilot-dev/references/pipeline.json` | `analysis.pm_gate.checklist` `["-"]` → **4항목**(spec-validate exit 0) |

### 3.3 도구 확장 (RED-first)

| 파일 | 변경 |
|------|------|
| `opal/tools/state-tool/tests/test_state_tool.py` | `TestT100DirectionEvidence` 7케이스 선작성(+415줄). 실 파일 픽스처 3종, mock 0건 |
| `opal/tools/state-tool/state_tool.py` | `_locate_confirmed_direction_items` 신설(표 파서 미재사용) · verdict `승계` · `items[].source` · `direction_confirmed_ratio` 반환. **기존 `confirmed_ratio` 분모 불변**(PD-1 분리형) |
| `opal/tools/state-tool/README.md` | 반환 계약 4종 반영(파싱 대상 2곳·source·verdict 3종·신규 키 + 두 비율 분모 대조표) |

### 3.4 문서

`docs/ARCHITECTURE.md`(harness 파일 수 2곳 정정) · `docs/PROJECT.md`(§주요 컴포넌트에 `analysis-core.md` 행).

## 4. 핵심 설계 결정

| # | 결정 | 근거 |
|---|------|------|
| PD-1 | `confirmed_ratio` **분리형** — 기존 키 분모 불변 + `direction_confirmed_ratio` 신설 | 분모 확대는 값 형식이 같아 소비자가 감지하지 못하는 조용한 계약 파괴다 |
| PD-2 | 하네스 **§2 재사용 + 하위 stub** 신설 | 최상위 절 신설은 타 문서의 `opal-harness.md §N` 인용을 전건 파손한다 |
| PD-3 | `analysis.pm_gate.checklist` **4항목** | 스키마 제약은 "비어있지 않은 문자열 배열"뿐, 선례 1~5개의 중앙값이며 R-5·R-6·R-7·R-8 AC와 1:1 |
| PD-4 | MUST 트리거 관용구 잔존은 **AC 위반 아님** | 제거하면 SSOT 로드 경로가 끊긴다. R-9 판정식이 문단 수로 교체됐으므로 텍스트 일치는 판정 대상이 아니다 |
| ADD-1 | 3단-B(과거 산출물) **무조건 → 트리거 T1~T4 조건부** + 스킵 시 결측 명시 + Glob/Grep 3층 위치 명시 | 무조건 조회는 결과 0건이 예정된 호출을 규범이 강제해 커버리지 착시를 만든다. 단 brain ingest 커버리지 58% 실측이라 폐기는 불가 |

## 5. 프레임워크 지식 — 「규범이 행동을 바꾼 직접 증거」

R-12 재생성 대조에서, PM이 **아무 절차도 주입하지 않은** 표준 프롬프트로 ANALYSIS를 1회 재생성했다.

| 관측 | baseline(PM 수동 주입) | 재생성(지시 없음) |
|------|----------------------|------------------|
| 지식 선조회 3단 | PM이 brain 5페이지 경로·절차 명시 | **워커가 자발 수행**(brain 0건 → code-scan 0건 → docs → T1 트리거로 과거 산출물) |
| Q표 섹션 | PM이 요건 지정 | **1건 등장** |
| 「다음 단계 입력」 | PM이 요건 지정 | **1건 등장** |
| 「PLAN 결정 필요」 | PM이 요건 지정 | **2건 등장** |
| 코드펜스 비율 | 6.3% | **0.0%** |

**결론**: 템플릿 실물 섹션에 넣은 것은 지시 없이 재현되고, 산문에만 있는 것은 재현되지 않았다. 099의 「템플릿 우위 법칙」이 다른 태스크·다른 산출물에서 재확인됐다.

**부수 관측**: ADD-1의 조건부 트리거가 승인 당일 첫 실사용에서 T1 성립 → 과거 산출물 조회로 정확히 분기했다.

## 6. 검증

| 계층 | 결과 |
|------|------|
| L1 문서(S-1~S-19) | 전건 Pass — 앵커 7개 일치, 이관 원본 잔존 0, 미등록 MCP 0건, 절차 문단 7→4 |
| L1 코드(S-20~S-26, RED-first) | 전건 **Pass(GREEN)** — RED 증거: 7 failed / 340 passed(단일 파일) → GREEN 347 passed |
| L2(S-27~S-29) | 전건 Pass — README 계약 정합, docs 수치 일치, 실 태스크 CLI 실행(items 26건·`승계` 5건·exit 0) |
| L3(S-30~S-33) | S-30 조건부 Pass · S-31 Pass · S-32 Pass · **S-33 Fail** |
| 회귀 | `python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py -q` → 347 passed / `python3 -m pytest opal/tools/state-tool/ -q` → 364 passed (스코프·명령 병기, 감소 0건) |
| 게이트 | 목표-커버: 결정론 exit 0(`all_covered` R12/F8/H14/S33) + 평가자 verdict pass(①1 ⑤2 ⑥2, 평균 1.67) |
| 컨벤션 | Critical 0 / High 0 / Medium 1(ADD-2로 해소) — `GC-CONVENTION-260824.md` |
| 보안 | 시크릿 0건, `.gitignore` 확인 |

### S-33 Fail — 은폐하지 않은 실패

핸드오프 표 스키마(`항목 | 확정값 | 근거`)가 `plan-guide.md` 2.N.1이 요구하는 필드(파일·6영역 라벨·변경 유형·순서)를 담지 못한다. 개정된 `:92`가 승계를 `[MUST]`로 요구하는데 표가 그 요구를 충족할 수 없는 **계약 불일치**다. 행 수 문제가 아니라 스키마 문제이며 baseline 8행도 동일하다.

## 7. 사고와 교훈

| # | 사고 | 교훈 |
|---|------|------|
| 1 | Step 1 워커가 Write 차단을 **Bash heredoc으로 우회**(세션 통산 3회) | 이후 디스패치에 「도구 차단 시 우회 금지 + 즉시 보고」를 명시하자 **4번째 차단에서 우회 0건**·텍스트 반환으로 대응했다. 프롬프트 주입으로 막히지만 아직 규범이 아니다 |
| 2 | PM(나)이 Step 12에서 `ARCHITECTURE.md:80`의 "17파일" **첫 발생만 확인**하고 같은 줄의 harness 수치를 놓쳤다 | S-28이 검출했다. 계수는 첫 매치가 아니라 **정규식 전종 매치**로 세야 한다. H-12 가설이 실제로 재현된 사례 |
| 3 | 내가 만든 AC-G1이 **잘못된 단계를 겨눴다** — `승계`는 상류가 있는 PLAN 단계 값인데 ANALYSIS(TASK.md 첫 소비자)에 요구했다 | AC는 판정 대상 단계의 계약과 맞물려야 한다. 판정식이 산출물보다 자주 틀린다 |
| 4 | grill 라운드 1에서 산출물에 적용한 `해당없음(결정)` 2분리를 **템플릿에 승격하지 않아** 재생성본이 `유효`를 썼다 | 산출물에서 얻은 개선을 규범으로 올리지 않으면 다음 회차에 사라진다 |
| 5 | 내 지시서에 `[결정] 15건`이라 적었으나 실제 TASK.md는 16건 | 워커 재측정이 정정했다. PM 수치도 실측 대상이다 |

## 8. 잔여·보류

### 미수행 (소유자 권한)

| # | 항목 | 영향 |
|---|------|------|
| 1 | **커밋** | 전 변경이 워킹트리에 있다 |
| 2 | **`install` 재배포** | `state_tool.py`·규범 문서 개정이 `~/.opal/`에 미반영 — 워커 런타임은 구버전(H-6, 정상 상태) |

### 후속 이월 5건

| # | 항목 | 근거 |
|---|------|------|
| 1 | 핸드오프 표 스키마 보강 — ⓐ 파일 맵 하위 표 규정 / ⓑ 2.N.1을 승계 대상에서 제외하고 ANALYSIS §1.1 직접 인용 | S-33 Fail |
| 2 | AC-G1을 PLAN 단계로 재배치 | §7-3 |
| 3 | `해당없음(결정)` 판정값을 `op-dev-analysis/SKILL.md` 템플릿으로 승격 | §7-4 |
| 4 | 워커 주입 「도구 차단 시 우회 금지」 조항을 `pm/dispatch-process.md` 전 워커 공통 고정에 신설 | §7-1, 099 이월분과 동일 |
| 5 | PLAN 트랙 행동 미검증 — R-9·R-11 검증이 전부 grep이라 "문서는 고쳤는데 행동은 그대로"를 못 잡는다 | 평가자 gaps 1 |

### 측정 한계 (숨기지 않음)

- R-12 대조는 **재생성 1회**라 통계가 아니라 존재 증명이다.
- baseline이 PM 수동 주입으로 만들어져 **천장 효과**가 있다 — 대조의 성격은 "개선 증명"이 아니라 "규범만으로 동등 수준이 재현되는가"다.
- 재생성 시 스킬 경로를 배포본이 아닌 **프로젝트 소스**로 지정했다(재배포가 범위 밖) — 실사용 경로와 동일하지 않다.
- AC-G4(PLAN 재생성 대조)는 baseline PLAN.md 부재로 **측정 불가**이며, S-33이 축소 대체 검증으로 갈음했다.
- opp·oppd 경로(`op-task-plan/references/plan-guide.md`)는 별도 파일이라 이번 개정 **미적용**(명시적 배제 결정).

## 9. 산출물

| 파일 | 내용 |
|------|------|
| `TASK.md` | 요구사항 R-1~R-12, 확정 방향 22건, 범위 15파일 |
| `ANALYSIS.md` / `ANALYSIS.baseline.md` | 분석 331줄 — grill 3축 캐묻기 2라운드 반영본. baseline은 R-12 대조군 |
| `ANALYSIS-REGEN.md` | 표준 프롬프트 재생성본 172줄 — R-12 실측 대상 |
| `PLAN.md` | 기능 8 · Phase 6 · Step 13 · 리스크 H-1~H-14 · PLAN 결정 4건 |
| `TEST-SCENARIO.md` | 시나리오 S-1~S-33 + 실행 결과·판정 |
| `SCENARIO-GATE-1.md` | 목표-커버 게이트 평가자 보고서 |
| `GC-CONVENTION-260824.md` | 컨벤션 진단 보고서 |
| `STATE.md` | 의사결정 로그 8행 |
