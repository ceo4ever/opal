# TASK: oppl 계약 접합면 검증 강화 — 표면 인벤토리·커버리지·전수 conformance·목 금지·여정 스모크

> 작성일: 2026-07-18 | 작업 유형: 개선 | 적용 스킬: opd | 모드: agentic (캡틴 지시로 semi-agentic에서 전환, 2026-07-18)
> 입력: 사용자 요청 (oppl 실전 프로젝트 사후분석 보고 기반)
> 출력: TASK.md

## 작업 목표

oppl의 완료 판정이 "테스트가 어떤 환경·어떤 상대로 실행됐는지"를 반영하지 않아, 목·비브라우저·서버 미기동 GREEN이 전부 "verified"로 집계되는 근본 갭을 해소한다 — **증거 충실도(Evidence Fidelity) 원칙**("사용자가 실제 접촉하는 방식과 같은 충실도의 증거만 최종 완료 증거로 인정")을 1급 규범으로 명문화하고, 계약 표면(surface) 전수 커버리지와 함께 도구 게이트로 강제하여, CORS·auth 형태 불일치 같은 열거된 사례뿐 아니라 미열거 결함 클래스까지 구조적으로 재발 불가능하게 만든다.

## 배경

캡틴이 타 프로젝트에서 `//oppl`로 병렬 FE/BE 개발을 수행한 결과, 다음 사고가 발생했다 (사후분석 보고 원문 — 대화 인용):

1. **계약 구멍**: CONTRACT §3.3 엔드포인트 표에 auth 행 자체가 없어 BE와 FE가 로그인 응답 형태를 각자 발명. 계약이 있어도(agents envelope) 준수 검사 장치가 없어 위반 통과. budgets/decisions는 계약에 있는데 백로그 분해에서 대응 태스크 미배정 — "계약 표면 ↔ 백로그 커버리지" 대조를 아무도 안 함.
2. **목 self-confirming**: FE는 실 BE가 아닌 MSW 목 상대로 개발·검증됨. 목은 FE 자신의 가정을 부호화하므로 "테스트 GREEN = 완료" 판정이 규칙상 성립 — 판정 기준 자체가 실 BE를 포함하지 않았음.
3. **표본 검증**: 크로스스택 동형성 테스트가 3개 표면만 표본 검사 → "크로스스택 OK"라는 잘못된 확신. auth·agents·budgets는 사각지대.
4. **PM 가로 감사 부재**: done-check는 태스크 축(all_done)만 판정 — "계약 전 표면이 어느 태스크에서 검증되는가"는 아무도 안 봄. "브라우저에서 실제 로그인해본다"가 파이프라인 어디에도 없음.

## 배경 분석 (대화에서 도출)

PM이 프레임워크 소스를 진단한 결과, 3개 원인 모두 대응 장치가 "prose로만 있거나 아예 없음" — 헌법 enforce-don't-advise 미적용 갭:

| 원인 | 프레임워크 현재 상태 | 갭 근거 |
|------|-------------------|--------|
| ① 계약 구멍 | CONTRACT 구조는 3파트+기계검증절만 요구, 표면 전수 나열 의무 없음. 완전성은 Evaluator 루브릭(Likert ≥4, LLM 주관)에만 의존 | `opal/skills/opal-pilot-project-loop/references/contract.md` §2 / `references/verification.md` §2.2 "계약 완전성" 행 |
| ① 커버리지 | D5 백로그 분해에 계약 표면↔태스크 대조 규칙·도구 없음. backlog-tool add-task에 표면 매핑 필드 부재 | `opal/skills/opal-pilot-project-loop/SKILL.md` §Loop 1 D5 / `opal/tools/backlog-tool/README.md` §2 add-task (fields: id/title/slice/acceptance/area/priority/depends/parallel-group — covers 없음) |
| ② 목 self-confirming | RED-first tool-gate(`scenario-red`)는 "테스트가 진짜 실패했는가"만 봉쇄 — "테스트 상대가 진짜인가"는 미검사. PRINCIPLES §4 "Don't fake it"은 구현의 목 대체만 금지 | `SKILL.md` §T2 (scenario-red/lock) / `~/.opal/PRINCIPLES.md` §4 |
| ② 통합 태스크 | "병렬 그룹마다 통합 태스크 필수"가 prose 권고 — tool-gate 없어 미생성해도 done-check 통과 | `SKILL.md` §병렬 실행: "통합 태스크 필수" |
| ③ 표본 검증 | 결정론 표의 "계약 conformance: binary"에 분모(전 표면) 개념 없음 → 표본 통과=전체 통과로 오독 | `references/verification.md` §2.1 "계약 conformance" 행 |
| ③ 가로 감사 | L✓ done-check는 태스크 축만 판정, 표면 축 판정 도구 없음 | `opal/tools/backlog-tool/README.md` §6 done-check (all_done/remaining만 반환) |
| ④ 여정 스모크 | USER_JOURNEY.md는 Loop 1 설계 입력으로만 소비 — Loop 2/L✓에서 재실행 의무 없음 | `SKILL.md` §Loop 1 D1.5 / §Loop 2 L✓ (여정 언급 없음) |

## 확정된 설계 방향 (대화에서 합의)

**근본 원칙 (캡틴 확정 — "CORS 자체가 아니라, 그 수준의 결함이 테스트를 통과한 것이 문제")**: 개별 결함 클래스(auth·CORS·envelope)의 열거식 체크가 아니라, **증거 충실도 게이트** 하나로 통일한다 — 시나리오마다 실행 충실도(`mock` < `real-http` < `real-usage`)를 tool-gated로 기록하고, 사용자 접촉 표면·여정은 `real-usage`(실 브라우저·실 진입점·실 데이터 흐름) PASS 증거 없이는 도구가 완료 판정을 거부한다. auth 토큰 체인·CORS preflight·브라우저 스모크는 이 원칙의 표준 구현 예시이지 규칙의 전부가 아니다.

캡틴이 AskUserQuestion에서 "5건 전체 태스크 (권고)"를 선택 — 아래 5건을 위 원칙의 집행 수단으로 진행:

| # | 개선 | 메커니즘 | 변경 대상 | 성격 |
|---|------|---------|----------|------|
| ① 표면 인벤토리 의무화 | CONTRACT.md 기계검증절에 기계가독 표면 목록(id·리소스·요청/응답 형태 — auth 포함) 필수화, D6 Evaluator가 PRD/TRD/여정 대비 누락 판정 | `contract.md` §2.2 + SKILL.md D4 | 문서 |
| ② 커버리지 매트릭스 tool-gated | backlog-tool `add-task --covers <surface-id>` 신설 + coverage 검사 — 전 표면 ≥1 태스크 매핑 없으면 D7 진입 거부(`surface_uncovered`), 병렬 그룹의 통합 태스크 부재도 동일 게이트로 거부 | backlog-tool + schema + SKILL.md D5/D7 | 도구 |
| ③ conformance 전수화 | L✓ 종료조건에 "표면×결과 매트릭스 all green" 추가 — done-check가 표본이 아닌 분모 전수를 판정 | backlog-tool done-check + SKILL.md L✓ | 도구 |
| ④ 충실도 게이트 (목 단독 GREEN 금지의 일반화) | test-scenario 시나리오에 `fidelity: mock\|real-http\|real-usage` 필드 추가 — 요구 충실도 PASS ≥1 없이 scenario 완료 불가(tool-gated) | test-tool + `verification.md` §3 | 도구 |
| ⑤ 여정 스모크 게이트 | user-facing 프로젝트는 L✓ 회귀에 USER_JOURNEY 첫 접촉 경로(로그인→핵심 1기능) 실환경 E2E 1회 의무 | SKILL.md L✓ + `journey-flow.md` | 문서 |
| ⑥ 워킹 스켈레톤 최우선 태스크 (캡틴 추가 — 개발환경 시점부터 브라우저 테스트 가능) | D5 백로그의 의존 루트(P0) 태스크로 "실행 스켈레톤" 의무화 — BE 서버 기동+스웨거(OpenAPI) UI, FE dev 서버 기동, 실 브라우저에서 FE→BE 실 호출 1개 관통. 이후 전 태스크의 real-http/real-usage 검증이 이 환경에서 실행됨 | SKILL.md D5 + verification.md (+게이트 메커니즘 PLAN 결정) | 문서+도구 |

## 명확화 결과

> TASK 4요소를 잠근다.

| 요소 | 확정값 | 미확정(있으면) | 의존 사실 |
|------|--------|--------------|----------|
| 목표 | 증거 충실도(Evidence Fidelity) 원칙을 1급 규범으로 명문화 + 표면(surface) 전수 커버리지와 함께 도구 게이트로 강제 — "실사용 충실도 미달 증거만으로 done 판정"이 되는 근본 갭을 봉쇄(열거된 사례와 미열거 결함 클래스 공통) | - | 사후분석 보고 + 캡틴 확정(근본 원칙 — 대화) |
| 범위 | 포함: 개선 5건(①~⑤) — backlog-tool·test-tool 코드 확장 + oppl SKILL.md·references 3종(contract/verification/journey-flow) 문서 개정. 제외: oppd/opsdd 등 타 파이프라인 적용(후속), 이미 실행된 타 프로젝트의 T16 수습(해당 프로젝트 소관), install 배포(EXECUTE 완료 후 별도 승인) | 표면 인벤토리의 스키마 상세는 PLAN에서 결정 — API 프로젝트는 OpenAPI(스웨거) spec을 인벤토리 형식으로 채택하는 안을 1순위 검토(spec 기반 전수 conformance 도구 생태계 활용 가능) | `opal/tools/{backlog-tool,test-tool}/` 소스 존재 |
| 제약 | ~/.opal 직접 수정 금지(프로젝트 소스 수정 후 install 배포) / 3-SSOT 축 분리 유지(backlog·state·test-scenario 상호 참조 금지) / enforce-don't-advise(규칙은 도구가 거부로 집행) / 기존 oppl 프로젝트(covers 미사용 backlog.json) 하위 호환 / 변경이력 표 갱신 의무 | - | `.opal/AGENT.md` §금지사항 / oppl SKILL.md §3-SSOT |
| 완료기준 | 요구사항 R-0~R-8의 AC 전부 충족 + backlog-tool/test-tool 기존 테스트 회귀 0 + 신규 게이트 거부 경로 실증(에러 코드 실관찰) | - | - |

## 요구사항

- [ ] **R-0 증거 충실도 원칙 명문화 (근본 처방)** — 무엇을: "완료(done)의 최종 증거는 사용자가 실제 접촉하는 방식과 같은 충실도에서 관찰된 것만 인정한다"를 oppl 검증 규범으로 명문화 + 충실도 3단계 사다리와 표준 실행 방법을 정의: `mock`(목 상대 테스트 코드 — 단위 수준) < `real-http`(실 서버 기동 + 계약 spec 기반 실 HTTP 전수 conformance — 스웨거/OpenAPI 방식, auth 토큰 체인 포함) < `real-usage`(실 브라우저(cmux browser 우선/playwright 폴백) E2E — 실 진입점·실 데이터 흐름). BE는 단위=테스트 코드/통합=spec 기반 실 HTTP, FE는 단위=목 허용 컴포넌트 테스트/통합=실 브라우저×실 BE로 매핑. 어디에: `references/verification.md` §1~§3 (신규 절) + SKILL.md §검증 2원화. 왜: 캡틴 확정 근본 원칙 — 열거식 결함 체크가 아니라 판정 체계 자체를 교정. AC: verification.md에 충실도 3단계 정의·단계별 표준 실행 방법·"사용자 접촉 표면/여정은 real-usage PASS ≥1 없이 done 불인정" 규칙이 명시되고, R-5의 도구 게이트가 이 규범을 집행 근거로 인용한다.

- [ ] **R-1 표면 인벤토리 규칙 명문화** — 무엇을: CONTRACT.md 기계검증절에 기계가독 "표면 인벤토리" 블록(표면 id·리소스·요청/응답 형태 + **표면별 `auth: required|none` 선언 의무, 인증 표면(로그인) 자체도 표면으로 등재**) 필수 규칙 추가 + **경계(Boundary)절에 웹 클라이언트 존재 시 허용 origin(개발·운영) 선언 의무**. 어디에: `opal/skills/opal-pilot-project-loop/references/contract.md` §2.1·§2.2 + SKILL.md D4 절. 왜: 확정 방향 ① + 캡틴 지적(auth가 계약에 없는 상태를 형식적으로 불가능하게 + CORS 기준의 계약 명문화). AC: contract.md §2.2에 표면 인벤토리 필수 규칙·형식 정의(auth 필드 포함)가 존재하고, §2.1 경계 파트에 허용 origin 선언 규칙이 존재하며, SKILL.md D4 디스패치 프롬프트가 이를 요구하고, D6 Evaluator 판정 기준에 "표면 누락(PRD/TRD/여정 대비)" + "auth 필드 미선언" + "웹 클라이언트 프로젝트의 origin 미선언" 항목이 명시된다.
- [ ] **R-2 backlog-tool covers 필드** — 무엇을: `add-task`/`update-task`에 `--covers '["surface-id",...]'` 필드 신설(schema 반영, 하위 호환: 미지정 허용). 어디에: `opal/tools/backlog-tool/`. 왜: 확정 방향 ②. AC: `add-task --covers` 호출이 backlog.json tasks[].covers에 기록되고 BACKLOG.md 미러에 렌더되며, covers 미지정 기존 호출이 그대로 동작한다(회귀 0).
- [ ] **R-3 커버리지 게이트** — 무엇을: backlog-tool에 표면 커버리지 검사 신설 — 표면 인벤토리 대비 미커버 표면이 있으면 `surface_uncovered`, parallel-group 존재 시 통합 태스크(area=통합) 부재면 `integration_task_missing` 거부. 어디에: `opal/tools/backlog-tool/` (신규 서브명령 or done-check 확장 — PLAN에서 결정) + SKILL.md D5/D7. 왜: 확정 방향 ②. AC: 미커버 표면 존재 상태에서 게이트 호출 시 ok:false + `surface_uncovered`가 실관찰되고, 전 표면 커버 시 통과한다.
- [ ] **R-4 conformance 전수 판정 + 실 API 실행 방식 정의** — 무엇을: (a) L✓ 종료 판정에 "표면×결과 매트릭스 all green" 조건 추가 — done-check(또는 R-3 게이트)가 표면 축 전수를 함께 판정. (b) **conformance 실행 방식 명문화 — 실 서버 기동 + 실 HTTP 호출로 응답 형태를 계약과 대조하며, `auth: required` 표면은 실 로그인으로 취득한 토큰 체인(로그인 → 토큰 → Authorization 헤더)으로 호출해야 결과로 인정. 목·핸들러 단위 테스트 대체 불인정**. (c) **CORS 결정론 검사 — 계약 경계절에 허용 origin이 선언된 경우, conformance가 표면 전수에 대해 Origin 헤더 포함 요청 + preflight(OPTIONS) 요청을 보내 응답의 `Access-Control-Allow-*` 헤더를 계약 선언과 대조**. 어디에: `opal/tools/backlog-tool/` + SKILL.md L✓ + `references/verification.md` §2.1·§3. 왜: 확정 방향 ③ + 캡틴 지적(스웨거식 실 API 규약 테스트·auth 체인 + CORS가 브라우저 수동 테스트에서야 발견되는 문제의 조기 검출). AC: 표면 1개라도 검증 결과 미기록/FAIL이면 종료 판정이 all_done:false(또는 전용 에러)를 반환하는 것이 실관찰되고, verification.md §2.1 계약 conformance 행에 "분모=표면 인벤토리 전수" + "실행 방식=실 서버·실 HTTP·auth 토큰 체인" + "origin 선언 시 CORS 헤더 검사 포함" 정의가 명시된다.
- [ ] **R-5 충실도 게이트 (R-0의 도구 집행)** — 무엇을: test-scenario 시나리오에 `fidelity: mock|real-http|real-usage` 필드 신설 — 태스크의 요구 충실도(BE 표면=real-http 이상, 사용자 접촉 표면·여정=real-usage) PASS ≥1 없이 시나리오 완료 판정 불가(tool-gated, 전용 에러 코드). 어디에: `opal/tools/test-tool/` + `references/verification.md` §3. 왜: 확정 방향 ④(목 단독 GREEN 금지)를 R-0 원칙으로 일반화 — `target: real|mock` 2값이 아니라 충실도 3단계로 집행. AC: 요구 충실도 미달 시나리오만으로 완료 판정 시 도구가 거부(전용 에러 코드 실관찰)하고, 충족 시 통과하며, fidelity 미지정 기존 시나리오는 하위 호환된다(미지정=mock 간주 등 보수적 기본값 — PLAN에서 결정).
- [ ] **R-6 여정 스모크 게이트** — 무엇을: user-facing 프로젝트의 L✓ 회귀에 USER_JOURNEY 첫 접촉 경로(예: 로그인→핵심 1기능) 실환경 E2E 1회 의무 규칙 추가 — **반드시 실 브라우저(cmux-tool 우선/playwright 폴백)로 실행하여 CORS·쿠키·리다이렉트 등 브라우저 계층 결함을 검출하는 최종 안전망으로 명시**. 어디에: SKILL.md §Loop 2 L✓ + `references/journey-flow.md` + `references/verification.md` §2.1 E2E 행(L3b 전반의 실행 환경 = 실 브라우저 명시). 왜: 확정 방향 ⑤ + 캡틴 지적(CORS류는 브라우저에서만 발동 — E2E는 실 브라우저(cmux browser)에서 실행). AC: SKILL.md L✓ 절과 journey-flow.md에 여정 스모크 의무·실 브라우저 실행 요건·스킵 조건(비 user-facing)·기록 위치(VERIFICATION.md)가 명시되고, verification.md §2.1 E2E(L3b) 행에 "실행 환경 = 실 브라우저(cmux-tool 우선/playwright 폴백)"가 명시된다.
- [ ] **R-7 변경이력·정합** — 무엇을: 수정된 스킬·참조 문서·도구 README 전부에 변경이력 행 추가(KST+태스크번호), oppl SKILL.md 내 상호 참조 정합. 어디에: 변경 파일 전체. 왜: `.opal/AGENT.md` §금지사항 "변경이력 누락 금지". AC: changed_files 중 변경이력 표 보유 문서 전부에 069 행이 존재한다.

- [ ] **R-8 워킹 스켈레톤 최우선 태스크 의무** — 무엇을: D5 백로그 분해 시 의존 루트(P0) 태스크로 "실행 스켈레톤" 슬라이스 의무화 — 구성 요건: (a) BE 서버 기동 + 스웨거(OpenAPI) UI 노출(표면 인벤토리 spec 연동), (b) FE dev 서버 기동, (c) 실 브라우저(cmux browser)에서 FE→BE 실 호출 1개 관통 확인, (d) auth 표면 존재 시 로그인 관통 포함. 이후 모든 태스크의 real-http/real-usage 검증은 이 환경 위에서 실행됨을 명시(목 개발의 "실 BE 부재" 사유 원천 제거). 어디에: SKILL.md D5·병렬 실행 절 + `references/verification.md` (게이트 메커니즘 — D6 Evaluator 판정 항목 포함, backlog-tool 검사 여부는 PLAN에서 결정). 왜: 캡틴 지시 — 개발환경이 만들어지는 시점부터 브라우저를 띄워 테스트 가능해야 하며, 임시 테스트 환경을 처음부터 만들어 진행. AC: SKILL.md D5에 스켈레톤 태스크 의무·구성 요건 4항이 명시되고, D6 Evaluator 판정 항목에 "스켈레톤 태스크 부재/구성 미달"이 포함되며, 스켈레톤 없는 백로그가 D6 fail 또는 게이트 거부되는 것이 실증에서 관찰된다.

## 제약 조건

- `~/.opal/` 배포본 직접 수정 금지 — 프로젝트 소스(`opal/`) 수정 후 install 재배포 (배포는 본 태스크 범위 외, CLOSE 후 별도 승인)
- 3-SSOT 축 분리 유지 — backlog.json이 test-scenario.json을 직접 참조하지 않는 설계 유지 (표면 결과 기록 위치는 PLAN에서 축 분리 원칙 하에 결정)
- 하위 호환 — covers/target 미지정 기존 데이터·호출이 깨지지 않아야 함 (기존 backlog-tool/test-tool 테스트 회귀 0)
- 도구는 Python(backlog_tool.py 패턴) + run.sh 래퍼 + JSON 출력 + 에러 코드 계약 준수

## 기술 스택

- Python 3 (backlog-tool·test-tool — stdlib 기반, run.sh 래퍼)
- Markdown (SKILL.md·references 문서)
- JSON Schema (`opal/tools/backlog-tool/schema/`)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | oppl 오케스트레이터 본문 | `opal/skills/opal-pilot-project-loop/SKILL.md` | D4/D5/D7/L✓/병렬 실행 절 개정 대상 |
| D-2 | 설계 | CONTRACT 거버넌스 가이드 | `opal/skills/opal-pilot-project-loop/references/contract.md` | §2.2 기계검증절에 표면 인벤토리 의무 추가 |
| D-3 | 설계 | 검증 가이드 | `opal/skills/opal-pilot-project-loop/references/verification.md` | §2.1 conformance 분모 정의 + §3 목 금지 규칙 추가 |
| D-4 | 설계 | 여정·플로우 가이드 | `opal/skills/opal-pilot-project-loop/references/journey-flow.md` | 여정 스모크 게이트 규칙 추가 |
| D-5 | 소스 | backlog-tool | `opal/tools/backlog-tool/` | covers 필드·커버리지 게이트 구현 대상 |
| D-6 | 소스 | test-tool | `opal/tools/test-tool/` | target 필드·real 스모크 게이트 구현 대상 |
| D-7 | 설계 | OPAL 헌법 | `~/.opal/PRINCIPLES.md` | "Enforce, don't just advise" 원칙 — 본 태스크의 설계 근거 |
| D-8 | 설계 | 하네스 공통 | `opal/core/references/opal-harness.md` | §1 Guards·자동 루핑 제약과의 정합 확인 |
