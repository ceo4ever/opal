# AGENTIC-LOG: OPAL 범용 E2E 하네스 구현 (제안서 태스크 2~9)

> 모드: agentic | 시작: 2026-09-12 21:00 | 스킬: //oppl --agentic --wt

## 요약

| 항목 | 건수 |
|------|------|
| 게이트 판단 | 9회 (Pass: 7 / Fail: 2) |
| 3회 초과 Gate | 0건 (Critical: 0 / Normal: 0 / Minor: 0) |
| 오류 발견 | 8건 |
| 수정 지시 | 8건 (반영: 8 / 미반영: 0) |
| PM 의사결정 | 14건 |
| 개선 사항 | 5건 |
| 에스컬레이션 | 0건 |

## 대행 일지

| # | 시점 | 단계 | 카테고리 | 내용 | 결과 |
|---|------|------|----------|------|------|
| 1 | 2026-09-12 21:00 | TASK | DECISION | Git 사전 점검에서 `docs/proposals` 미커밋 7파일 감지. 워크트리가 main HEAD에서 분기하므로 제안서 최신본이 작업본에 포함되지 않는 문제 → 캡틴에게 선택 요청, `지금 커밋 후 진행` 선택 | `35c62d0 docs(proposals): 제안서 재정리` 커밋 후 워크트리 생성 |
| 2 | 2026-09-12 21:00 | TASK | DECISION | 프로젝트 범위를 제안서 §14 태스크 2~9 전부로 확정(태스크 1은 125로 완료). 캡틴 승인 | TASK.md AC-1~AC-14로 고정 |
| 3 | 2026-09-12 21:02 | TASK | GATE | 행 1~2 Pass — TASK.md `verify --clarification-check` pass(template sdlc-v2, 필수 5절, C-1~C-8/AC-1~AC-14 고유 ID), `state init` rows_count 19 생성 확인 | Pass |
| 4 | 2026-09-12 21:11 | PLAN | GATE | D2 PRD Pass — PRD.md 직접 Read(258행). AC-1~14·C-1~8 전 22건이 §9 역추적표에 대응, 제안서 §14 태스크 2~9 전건이 §8 매핑표에 존재, 브레인 과거 결정 대체가 §2.1에 명문화됨. 금지사항(이력절·~/.opal 편집·플랫폼 분기) 위반 0 | Pass |
| 5 | 2026-09-12 21:11 | PLAN | ERROR | PRD §5 전제절 인용 줄번호 3건 오차 — `e2e_contract.py:38/:39/:42`로 적었으나 실제는 PROFILES 37 · FINAL/OPERATIONAL 38-39 · STATUS_EXIT_CODES 41. 증적 게이트는 `:434`(required_fidelity 스키마 검사)로 적었으나 실제 게이트는 `validate_pass_requirements`(292, 누락 판정 357-366) | Minor |
| 6 | 2026-09-12 21:12 | PLAN | FIX | #5 반영 — PM이 PRD §5 인용 4개를 실측값으로 직접 보정(재디스패치 대신 PM 직접 수정: 사실 오차 1행 단위, 설계 판단 불변) | 반영 완료 |
| 7 | 2026-09-12 21:27 | PLAN | GATE | D3 TRD Pass — TRD.md 직접 Read(672행). PRD R/NR 26건 전건이 TD-1~TD-19에 대응(§11), 제안서 태스크 2~9 전부에 §6 변경지점 목록 존재, Q-1·Q-4·Q-5 결정 완료. 워커 실측 3건을 PM이 독립 재검증: pkill 2곳(`console.sh:88`·`install-mac.sh:1844`) 확인 · `import.meta.env` 사용 0건 + `vite-env.d.ts`/`.env.development` 부재 확인 · `tool-scan/tests/test_tool_scan.py:843` 문구 강제 + `templates/test-tools.yaml:130` 기본 생성 확인 | Pass |
| 8 | 2026-09-12 21:27 | PLAN | DECISION | 제안서와 다른 결론 3건 수용 — (1) `installed` target이 install을 실행하지 않음(`install-mac.sh:1772`가 소스 트리에서 FE 빌드, `:1798`이 사용자 `console.config.json` 갱신 → 호출 시 R-6·C-2·C-5 동시 위반. PM 재검증 완료) (2) 저장소 내부 산출물 경로 미지원 (3) 신규 도구 미신설, `test-tool` 확장. 세 건 모두 제약에서 연역되며 범위를 넓히지 않음 | 채택 |
| 9 | 2026-09-12 21:27 | PLAN | DECISION | TD-5의 `$OPAL_HOME/run/console.pid` 쓰기가 「~/.opal 직접 편집 금지」 위반인지 판정 — `docs/CONVENTIONS.md:255` "런타임 사용자 데이터 쓰기는 이 금지의 대상이 아니다" 원문 확인. 위반 아님 | 승인 |
| 10 | 2026-09-12 21:40 | PLAN | ERROR | **PM 자신의 오류** — #6의 인용 "보정"이 틀렸다. `sed -n '36,44p'` 출력의 첫 행을 36행으로 오독(실제 36행은 공백)해 PROFILES를 :37로 고쳤으나 실측은 :38. 이 잘못된 값이 D3·D4 디스패치 프롬프트에도 주입됐고 TRD §2.1이 그대로 상속했다. D4 워커가 자기 실측으로 검출·보고 | Critical(사실 오염) |
| 11 | 2026-09-12 21:41 | PLAN | FIX | #10 반영 — `grep -n`(줄번호 직접 출력)으로 재확정: SCHEMA_VERSION 37 · PROFILES 38 · FINAL_STATUSES 39 · OPERATIONAL 40 · EXECUTOR_TYPES 41 · STATUS_EXIT_CODES 42-49 · resolve_profile 137. PRD §5 3건, TRD §2.1 6행 + §3.2 1건 보정 | 반영 완료 |
| 12 | 2026-09-12 21:41 | PLAN | IMPROVE | 줄번호 인용 검증은 `sed -n 'A,Bp'`(오프셋 암산) 대신 `grep -n`(줄번호 직접 출력)만 쓴다. sed 범위 출력은 공백 행에서 눈으로 세다 off-by-one을 만든다 | 이 세션 이후 적용 |
| 13 | 2026-09-12 21:42 | PLAN | GATE | D4 CONTRACT Pass — CONTRACT.md 939행(§A 스키마 14종·§B 시그니처·§C 경계 9절·§D MV-01~MV-40·§E 루브릭 6축 앵커·§F TD/R 역추적), surfaces.json 40표면. PM 독립 검증: json 파싱 OK·필수키 누락 0·중복 id 0·auth 전건 none, SUT HTTP 17건이 `dashboard/backend/routers/` 실제 라우트 16 + `main.py:102` /health와 **정확히 일치**, 루브릭 6축이 즉시 감점 사유까지 앵커링됨 | Pass |
| 14 | 2026-09-12 21:42 | PLAN | DECISION | `origins.dev`에 `http://127.0.0.1:${OPAL_E2E_FRONTEND_PORT}` 플레이스홀더 채택 승인 — 와일드카드는 NR-4 "전체 허용 금지" 위반, 생략은 「부재 vs 누락」 구분 원칙 위배. MV-27이 플레이스홀더 잔존을 검사하므로 기계 추적 가능. `origins.prod: []`는 동일 오리진이라 0건 확정 선언 | 승인 |
| 15 | 2026-09-12 21:50 | REVIEW | GATE | D6 Evaluator verdict **fail** — E.1 4 / E.2 4 / **E.3 3(미달)** / E.4 drift=no / E.5 4 / E.6 5. 미해결 이슈 10건 | Fail (1회전) |
| 16 | 2026-09-12 21:50 | REVIEW | ERROR | FAIL 원인 ④ — T01(P0 루트, depends 없음)의 완료 기준이 "FE가 임대 backend를 가리키고 실 호출이 200"인데 `api.ts:14` 하드코딩과 `main.py:76-79` CORS를 고치는 T03·T04가 **T01에 의존**하도록 방향이 반대였다. 선언된 순서로는 워킹 스켈레톤이 성립 불가 | Critical |
| 17 | 2026-09-12 21:55 | REVIEW | FIX | ④ 반영 — 의존 역전 대신 **흡수**를 택했다(oppl [MUST]가 실행 스켈레톤을 의존 루트 P0로 못박으므로 T03·T04를 루트로 올리는 대안은 규약 위반). T01이 FE 3파일 + CORS env를 흡수하고 T03·T04 제거. backlog-tool에 삭제 서브명령이 없어 backlog.json·BACKLOG.md를 지우고 `init`으로 재생성(실행 0건 상태라 손실 없음, 손편집 아님). 15태스크로 재구성 후 `coverage-check` all_covered 재통과 | 반영 완료 |
| 18 | 2026-09-12 21:56 | REVIEW | FIX | ⑤⑥⑦⑧ 반영(PM 자율 — `contract.md` §4 #2 내부 조정) — CONTRACT §A.15 driver manifest 스키마 신설, §A.8에 `probe.json` 저장 경로 확정(+TRD §7 구조 반영), §A.1.2 `candidates[]` 후보 탐색 기록 신설(+A.1 필드 행), MV-14 검사 대상 파일 명시, MV-19를 문자열 grep + exit 인자 AST 검사로 분리, MV-38을 `candidates[].order` 검사로 치환 | 반영 완료 |
| 19 | 2026-09-12 21:57 | REVIEW | FIX | ①②③⑩ 반영 — CONTRACT §A.1/§A.4 인용 5건, §C.8 "라우터 16 + main.py health 1 = 17" 정정, TRD §2.1 `EXECUTOR_MATRIX` 57-66·`HANDOFF_REQUIRED_FIELDS` 67-76·`server_policy` 74, TD-19 "5건"→"7건" | 반영 완료 |
| 20 | 2026-09-12 21:57 | REVIEW | DECISION | ⑨ 격리 `OPAL_HOME` 생성 주체 공백 — 백로그에 태스크를 추가하지 않고 **범위 경계 선언**으로 닫았다. PRD §4.2 비목표에 명시, TRD RK-4에 "미준비 시 `--target installed` 입력 오류로 거부" 추가, T03 완료 기준에 반영. 배포본 생성은 설치 파이프라인의 일이지 E2E 하네스의 일이 아니다 | 승인 |
| 21 | 2026-09-12 21:57 | REVIEW | IMPROVE | D6가 지적한 R-14 부정 케이스 검증 지연(통합 단계에만 존재)을 백로그 T06(판정 부정 검증)으로 신설해 P0·g2로 앞당겼다 | 반영 완료 |
| 22 | 2026-09-12 22:02 | REVIEW | GATE | D6 2회전 verdict **pass** — E.1 4 / E.2 4 / E.3 4(1회전 3→해소) / E.4 drift=no / E.5 5 / E.6 5. 1회전 10건 중 9건 해소·④ 부분 해소·T06 신설 확인. Evaluator가 `e2e_contract.py` 인용 20여 건을 원본 전건 대조해 오류 0 확인 | Pass (2회전) |
| 23 | 2026-09-12 22:03 | REVIEW | FIX | 2회전 잔여 6건 반영 — A: T01 `covers`를 `sut-health` 단독으로 축소하고 `console-*` 3건을 T02로 이동(④와 같은 방향의 귀속 역전) · B: `excluded_by` enum에서 `tested_range_probe_failed` 제거(4곳의 infra_error 승격 규정과 모순) · C: CONTRACT의 백로그 인용 3건 재생성 번호로 정정 · D: T01 슬라이스에 포트 경계 명시(bind까지 T01, lease record는 T03) · E: MV-41·MV-42 신설 · F: T04를 g2에 넣지 않고 `depends T03,T10`으로 순차화 | 반영 완료 |
| 24 | 2026-09-12 22:03 | REVIEW | DECISION | F의 g2 편입을 거부한 근거 — T04와 T10이 모두 `test_tool.py`의 e2e 서브파서를 수정한다. 같은 병렬 그룹에 두면 동일 파일을 두 워커가 나눠 갖게 되어 `dispatch-process` Step 1("같은 파일을 여러 워커에게 나누지 않는다")을 어긴다. 대칭성보다 파일 소유권이 우선 | 승인 |
| 25 | 2026-09-12 22:04 | REVIEW | GATE | PM Gate Pass — 4요소 잠김 확인. `coverage-check` all_covered(40표면) 재통과, 백로그 15태스크 의존 그래프 무순환, T01이 P0 의존 루트(depends 없음)로 oppl D5 [MUST] 충족, 미해결 이슈 0건. QA-SPEC-DESIGN-2026-09-12T21-56.md 기록 | Pass |
| 26 | 2026-09-12 22:18 | REVIEW | DECISION | D7 캡틴 승인 수신 — Loop 1 4요소 잠김 확정. `docs/` 승격은 별도 지시가 없어 **보류**하고 태스크 폴더 유지(이 저장소 `docs/`는 프레임워크 문서 레지스트리이므로 태스크 설계 문서 등재는 캡틴 판단 영역, 사후 승격 가능) | 승인 |
| 27 | 2026-09-12 22:19 | EXECUTE | DECISION | Loop 2 진입. L0 `select-next` → T01. `add-row`로 STATE 14행 삽입, backlog T01 `in_progress`. 요구 충실도를 `real-usage`로 주입 — T01 완료 기준 5가 "FE 화면에서 발생한 실제 HTTP 호출"을 요구하므로 real-http로는 미충족이며, 브라우저 실행 수단 부재 시 통과 대신 `blocked` 반환을 명시 지시 | 디스패치 |
| 28 | 2026-09-12 23:41 | EXECUTE | GATE | T01 Pass — PM 독립 재검증 완료: `git status`가 예상 12파일만(변경 0 계약 파일 `e2e_contract.py`·`scenario.py`·`worktree-tool`·`console.sh` diff 0 확인) · test-tool 88 passed(baseline 84+4, 회귀 0, SSOT 인터프리터로 재실행) · `scenario-status` locked·red_confirmed 8/8·passed 8/0 · `lib/e2e/`에 pkill/killall/pgrep 0건 · 사용자 7823 Console health 200 생존 · vite/uvicorn/chrome 고아 0건 | Pass |
| 29 | 2026-09-12 23:41 | EXECUTE | DECISION | T01 보고 drift #2(내부 조정) 반영 — MV-26이 "CORS 설정에 `*`·정규식 패턴이 없고"로 쓰여 어떤 구현으로도 충족 불가였다. `allow_headers=["*"]`(`main.py:122`)는 T01 이전부터 있던 헤더 축이고 `_ORIGIN_PATTERN`(`main.py:86`)은 입력 형식 검사다. 검사 대상을 **오리진 축**(`allow_origins`·`allow_origin_regex`)으로 한정하고 §F.1 TD-7에 적용 범위 주석 추가. PM 자율 범위(`contract.md` §4 #2) | 승인 |
| 30 | 2026-09-12 23:41 | EXECUTE | DECISION | T01 보고 2건 판정 — (a) `scenario-conformance` exit 14(`surface_unverified` 38건)는 T01 결함이 아니다. 분모가 프로젝트 전체 40표면이고 38건은 T02~T09 소유다. conformance는 **Loop 2 종료(L✓) 게이트**이지 태스크 게이트가 아니므로 재작업 루프를 소진하지 않고 통과시킨다. (b) T01 실제 커버가 2표면(FE 루트가 `/api/dashboard` 호출)이므로 `covers`에 `sut-dashboard` 추가, `coverage-check` 재통과 | 승인 |
| 31 | 2026-09-12 23:42 | EXECUTE | IMPROVE | T01의 G 1회차 fail이 실질 결함을 잡았다 — `start_frontend`에 포트 인자가 없어 CORS 주입 origin과 vite 실제 바인딩 포트가 어긋날 수 있었고, 그러면 CDP는 200인데 앱 fetch는 차단되는 **거짓 통과**가 성립했다. 생성자≠평가자 2원화가 실제로 작동한 사례 | 기록 |
| 32 | 2026-09-12 23:42 | EXECUTE | ERROR | 실행 중 프로세스 누출 1건 관측 — T3 중간 시도가 고아 pgid(`npm run dev`→vite, PPID=1)를 남겼고 루프 액션 에이전트가 최종 확인에서 자체 모듈로 회수했다. 현행 코드 재현 시험에서는 누출 0. PM 재검증에서도 고아 0건 | 해소 |
| 33 | 2026-09-12 23:50 | EXECUTE | ERROR | **PM 오진 2회** — T02 워커가 T1 대기 중 반환하자 무진전으로 판정해 재개를 지시했다. 근거로 쓴 "프로세스 소멸"은 `ps | grep -E "opal_agent|claude -p"` 패턴이 실제 커맨드라인(`~/.opal/tools/opal-agent/run.sh`)과 어긋나 생긴 오탐이었고, "파일이 23:50에 멈춤"은 모델 추론 중 mtime 정적 구간이었다. 워커가 PID 체인 생존·`.exitcode` 부재=실행 중 규약·T1 단계 코드 변경 0건 정상을 근거로 반박했고 반박이 옳았다 | 오진 인정 |
| 34 | 2026-09-12 23:52 | EXECUTE | IMPROVE | 프로세스 생존 판정을 커맨드 문자열 추측으로 하지 않는다 — `.oppl-run/session.json`의 PID + `kill -0`, 완료는 `.exitcode` 파일 존재라는 **도구가 정한 결정론 마커**만 쓴다. `ls -la` mtime을 진행 신호로 읽지 않는다(추론 구간에 갱신되지 않음) | 이 세션 이후 적용 |
| 35 | 2026-09-12 23:57 | EXECUTE | DECISION | T1 완료 실측 확인 — `t1.exitcode` 0, `PLAN.md` 25,933 bytes 산출. 하네스 재시도 1/1 **미사용 보존** 확정(오진이었으므로 소비하지 않는다). T02 워커에 T2부터 재개 지시, 중간 보고 없이 전 단계 완주 후 1회 반환하도록 지정 | 재개 |
| 36 | 2026-09-13 09:2x | EXECUTE | ERROR | T02 T3가 exit 2로 중단 — `t3.events.jsonl` 마지막 이벤트가 `rate_limit_event {status: rejected, five_hour, out_of_credits}`. **환경 차단이지 설계 실패가 아니므로 재시도 미소비**로 판정하고 warm resume 지시 | 해소 |
| 37 | 2026-09-13 09:10 | EXECUTE | ERROR | **PM 감시 누락** — T4b 진입 시 재개 지시만 하고 watcher를 걸지 않아, 보안 검사가 03:54에 exit 0으로 끝난 뒤 **5시간 16분** 아무도 워커를 깨우지 않았다. 이 워커는 비동기 자식을 띄우면 부모가 반환하는 구조라 PM 감시가 유일한 진행 동력이다 | 복구 |
| 38 | 2026-09-13 09:10 | EXECUTE | IMPROVE | **재개 지시와 watcher 설치를 항상 한 쌍으로 묶는다.** watcher 없이 재개시키면 그 단계에서 조용히 멈춘다. 감시 조건은 `.exitcode` 파일명 추측이 아니라 "현재 최신 exitcode보다 새로운 `*.exitcode`"로 건다(앞서 `t1b*` vs 실제 `t1.a2*` 오탐 재발 방지) | 이 세션 이후 적용 |
| 39 | 2026-09-13 09:3x | EXECUTE | GATE | T4b 보안 검사가 **blocker 1건(B-1)** 적발 — `"pid": 0` 레코드가 판정표 6분기를 모두 통과해 `kill 0`(호출자 프로세스 그룹 전멸)에 도달. `install-mac.sh`가 이 경로를 무인 호출하므로 침묵 종료가 성립. T02가 없앤 광역 `pkill` 자리에 "의도치 않게 광역인 kill"을 남긴 셈 | Fail → 재작업 |
| 40 | 2026-09-13 09:4x | EXECUTE | FIX | B-1·M-3 해소 확인(PM 코드 직접 검증) — `_console_pid_sane`(0·1·음수·비정수 거부, pid≥2), 판정표 #2 합류(`unreadable_record`, kill 0회, 새 분기 미생성), writer·stop·status 3경로 헬퍼 공유, `_console_pid_value_unsafe`가 `[[:cntrl:]]` 한 클래스로 통일. 부정 케이스 실관측(센티넬 전건 ALIVE)으로 증명됨 | 반영 완료 |
| 41 | 2026-09-13 10:0x | EXECUTE | GATE | **T02 Pass** — PM 독립 재검증: MV-21 `pkill`/`pgrep`/`killall` 양쪽 0건 · 비간섭 회귀 20/20 ALL PASS · pytest 88 passed(회귀 0) · `fidelity-check all_met: true` 14/14 · DONE.md 16,670B · 사용자 7823 health 200 · 변경 0 계약(test-tool·worktree-tool) diff 0 | Pass |
| 42 | 2026-09-13 10:0x | EXECUTE | DECISION | BLOCKED-1·2·4를 계약으로 확정(PM 자율 #2 내부 조정) — §B.4에 `console-*` 출력이 `key=value`이지 JSON이 아님 + `console-stop` 값 계약(`pid=-`로 미상 표현), `start`의 "레코드 없음 + 포트 응답"은 **아무것도 죽이지 않고 기동도 않고 안내만**(`lsof` 포트 소유자 폴백 불채택 — 소유권 없는 종료 금지의 우회), §A.13에 경로 허용 문자 집합, §A.13.1에 `pid≥2` 안전 조건 | 승인 |
| 43 | 2026-09-13 10:0x | EXECUTE | DECISION | BLOCKED-3(PID 재사용)은 문서화로 닫지 않고 **백로그 T16으로 신설**. 워커의 자기 위험등급 정정을 수용한다 — 레코드는 `stop` 실행 시에만 삭제되므로 크래시·리부팅 시 무기한 잔존하고, 리부팅 후 PID 재할당 시 `app_dir`(레코드 자기 필드)은 당연히 일치하며 `kill -0`도 성공해 판정표 #5로 직행한다. `install-mac.sh` 무인 호출 경로가 이를 실행 가능한 위험으로 만든다. 저비용 해법(`started_at` < 부팅 시각 → 무조건 stale)을 T16 완료 기준으로 고정 | 승인 |

