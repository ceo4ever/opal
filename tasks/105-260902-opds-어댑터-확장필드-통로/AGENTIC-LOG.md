# AGENTIC-LOG: 플랫폼 sub-agent 어댑터 확장 필드 통로 신설 + effort 첫 적용

> 모드: agentic | 시작: 2026-09-02 18:13 | 스킬: //opds

## 요약

| 항목 | 건수 |
|------|------|
| 게이트 판단 | 13회 (Pass: 13 / Fail: 0 — TEST PM Gate는 예외 1건 명시 통과) |
| 3회 초과 Gate | 0건 (Critical: 0 / Normal: 0 / Minor: 0) |
| 오류 발견 | 10건 (워커 산출물 7 / PM 자기 과실 1 / 절차 설계 2) |
| 수정 지시 | 4건 (반영: 4 / 미반영: 0) |
| PM 의사결정 | 8건 |
| 개선 사항 | 3건 |
| 에스컬레이션 | 2건 (R-6 AC 재정의 — 캡틴 승인으로 해소 / S-14 미검증 — 이월) |

## 대행 일지

| # | 시점 | 단계 | 카테고리 | 내용 | 결과 |
|---|------|------|----------|------|------|
| 1 | 2026-09-02 18:13 | TASK | DECISION | effort 실적용 대상을 Claude·Codex 2종으로 한정. 근거: Gemini는 공식 subagents 필드 표에 effort 부재(미지원), Cursor는 model 값 대괄호 합성 방식이라 현행 `model: inherit` 정책을 깨야 함 | 범위 확정 |
| 2 | 2026-09-02 18:13 | TASK | DECISION | 에이전트별 effort 값 배정을 본 태스크에서 제외하고 이월. 근거: 통로(구조)와 값(정책)은 실패 양상이 다르며, 통로 검증 전에 값을 얹으면 회귀 원인 분리가 불가 | 범위 확정 |
| 3 | 2026-09-02 18:13 | TASK | DECISION | Codex `[agents] max_threads` legacy alias 정리를 본 태스크에 포함. 근거: 동일 파일·동일 함수(`install_codex_config`)를 건드리므로 분리 시 중복 수정 비용 발생 | 범위 확정 |
| 4 | 2026-09-02 18:31 | PLAN | ERROR | PLAN.md 내부 모순 — §4.2 Step 8 ④는 프로브 에이전트를 `~/.opal/agents/`에 직접 배치하라고 지시하는데, §9 R-6은 "`~/.opal/` 직접 편집은 하지 않고 install 경유만 사용"이라 선언. 전자는 TASK.md 제약 [MUST] `.opal/AGENT.md` §금지사항("`~/.opal/` 직접 편집 금지")에도 정면 위반 | 검출 |
| 5 | 2026-09-02 18:31 | PLAN | FIX | (#4 참조) 워커에 재지시 — 프로브를 프로젝트 소스 `opal/agents/`에 생성하고 install 경유로 배포하도록 Step 8 재작성 지시. 추가로 프로브 추가·삭제가 "60건 diff 공집합" 판정과 순서 충돌하지 않는지 확인 요구 | 반영 완료 — Step 8이 3-Run 절차(①스냅샷 → ②Run A 15종 회귀확정 → ④Run B 16종 프로브검증 → ⑤Run C 15종 복귀)로 재작성됨 |
| 6 | 2026-09-02 18:31 | PLAN | IMPROVE | 워커가 재지시 처리 중 미식별 리스크를 추가 발견 — `~/.opal/agents/`는 install `clean_dirs`(`scripts/install-mac.sh:1037`)로 자동 복귀하나 **플랫폼 어댑터 디렉토리는 clean 대상이 아니어서** 프로브 삭제 후 고아 어댑터 4개(md 3 + toml 1)가 잔존한다 | 적용 — Run C에 고아 파일 확인·삭제 + 완료 기준 (다)에 5개 배포 경로 `grep -rl 'probe-effort-105'` 0건 조항 추가 |
| 7 | 2026-09-02 18:33 | PLAN | GATE | 목표-커버 게이트 결정론 파트(②요구커버·③기능커버·④리스크커버) — `test-tool scenario-coverage-check` exit 0, `all_covered: true`. 계수: 요구 6 / 기능 5 / 가설 9 / 시나리오 14, 누락 0 | Pass |
| 8 | 2026-09-02 18:36 | PLAN | GATE | 목표-커버 게이트 판단 파트(①목표달성·⑤채택잔존·⑥경계부정) — `opal-evaluator-agent` scenario-rubric 채점 2/2/2, 평균 2.0, gaps 0. Producer(PM)≠Evaluator 분리 유지. tool-gated 증거 2종 확보로 게이트 행 mark | Pass |
| 9 | 2026-09-02 18:36 | PLAN | GATE | PLAN PM Gate — 항목별 실측: R-1~R-6 전건 §1.2 매핑 / 9 Step·9 완료기준·9 agent 필드(누락 0) / 보안 4항목 / `mock`·`patch` 금지어 0건 / 게이트 verdict pass. Full Task 승격 조건 미달(변경 파일 5개 < 10개)로 Short Task 유지 | Pass |
| 10 | 2026-09-02 18:53 | EXECUTE | GATE | Phase 1 RED 증거 확인 — `test_agent_adapter_fields.sh` 코드 변경 전 실행 PASS=5 / FAIL=9. PLAN Step 1 완료 기준("TS-001·010은 PASS, effort 관련 케이스는 FAIL 리포트")과 일치. 안전망이 실제로 회귀를 잡는 상태임을 관측 | Pass |
| 11 | 2026-09-02 18:53 | EXECUTE | ERROR | R-6 AC(a)·TS-018 자기모순 — AC가 `grep -rn 'max_threads' scripts/` **0건**을 요구하나, legacy 키를 탐지·치환하는 마이그레이션 로직 자체가 그 리터럴을 정규식에 담아야 동작한다. PM 실측 확인: 잔존 10곳(mac 6 / windows 4)은 전부 변경이력 2·주석 2·탐지 정규식 4·성공메시지 1·(테스트 픽스처 별도)이며, **실제 쓰기 경로(`scripts/install-mac.sh:850` 인근 append 블록)는 정식 키만 사용**함을 확인 | 검출 — 워커가 난독화를 거부한 판단은 타당(reward-hacking 방어) |
| 12 | 2026-09-02 18:53 | EXECUTE | ESCALATION | (#11 참조) AC 문면 조정은 잠긴 수용기준의 변경이므로 PM 자율 판정을 보류하고 캡틴에게 에스컬레이션. 근거: `opal/PRINCIPLES.md` §1 "Lock acceptance criteria before execution. Criteria added later are rationalization." — PM이 스스로 못 지킨 AC를 스스로 고치는 것이 이 조항이 경계하는 형태다 | 캡틴 판정 대기 (Phase 2는 무관하므로 병행 진행) |
| 13 | 2026-09-02 19:13 | EXECUTE | GATE | Phase 2(Step 3·4) 검토 — **TS-001 60건 diff 공집합 PASS**로 최상위 제약(effort 미선언 산출물 바이트 동일)이 실측 확인됨. TS-002(플랫폼명 리터럴 0건)·TS-003·004(Claude·Codex effort 도달)·TS-007(max→xhigh 축약)·TS-008(오타 방어) 전건 PASS. 스위트 PASS=11 / FAIL=3 | Pass |
| 14 | 2026-09-02 19:13 | EXECUTE | ERROR | TS-005 테스트 구현 결함 — `scripts/tests/test_agent_adapter_fields.sh:296-302`가 `ts00*.*` 산출물에서 `[effort=`를 스캔하는데, 스펙상 Claude·Codex는 `mode:"key"`·Cursor·Gemini는 `omit`이라 그 파일에는 해당 문자열이 원천적으로 나타날 수 없다. **TS-003/004/006의 정상 통과와 TS-005의 통과가 동시 성립 불가**. PM이 테스트 코드를 직접 Read하여 확인 | 검출 |
| 15 | 2026-09-02 19:13 | EXECUTE | DECISION | (#14 참조) TS-005는 #11(TS-018)과 성격이 다르다고 판정하여 **PM 권한으로 교정 지시**(에스컬레이션 불요). 근거: TS-018은 TASK.md의 잠긴 AC 자체가 충족 불가인 반면, TS-005는 PLAN·TEST-SCENARIO가 이미 규정한 설계(「임시 스펙 주입으로 경로를 실행」 — TEST-SCENARIO §3 S-3)를 테스트 구현이 따르지 않은 것이다. 즉 기준 변경이 아니라 기준 미이행의 교정이다 | 교정 지시 — 「합성이 깨지면 반드시 FAIL할 것」·「교정 후 FAIL이면 구현 결함이니 테스트를 다시 고치지 말 것」을 명시해 느슨화 우회를 차단 |
| 16 | 2026-09-02 19:31 | EXECUTE | GATE | Phase 3(Step 5 + TS-005 교정) 검토 — 교정된 TS-005가 임시 스펙 주입으로 `model_param` 경로를 실제 실행하여 `model: "inherit[effort=high]"` 합성 확인, **PASS**(구현 결함 아님). windows 미러 반영으로 TS-011·TS-014 PASS. 스위트 PASS=13 / FAIL=1 | Pass |
| 17 | 2026-09-02 19:31 | EXECUTE | GATE | Step 6 전체 검증 — 스위트 PASS=13/FAIL=1(TS-018만), 기존 자산 회귀 `test_archive_contents.sh` 11/11 · `test_version_stamp.sh` 11/11 전건 exit 0, `bash -n` 통과, bash 3.2 호환 확인, 시크릿 0건, 커밋 0건(워킹트리만) | Pass |
| 18 | 2026-09-02 19:31 | EXECUTE | ERROR | 스펙 리터럴 자동 검증 맹점 — 리터럴이 실제 **4곳**(mac 전역 상수 1 + mac 함수 내 폴백 2 + windows 미러 1)인데 TS-011의 센티넬 추출은 **2곳만** 비교한다. 4곳 전부 바이트 동일(각 1506B)임은 수동 확인됐으나 자동 회귀 안전망이 아니며, 폴백만 수정되면 TS-011이 계속 PASS로 남는다. **PM이 직전 보고에서 "총 3곳"이라 한 것도 오류 — mac 폴백이 함수당 1개씩 2개다** | 검출 (PM 자기 정정 포함) |
| 19 | 2026-09-02 19:31 | EXECUTE | ERROR | S-13 판정 기준 부정확 — "각 디렉토리 15/15"를 요구하나 실측은 cursor 21(어댑터 16 + 사용자 파일 5) · gemini 16. 어댑터가 16인 원인은 고아 `wtm-agent.md` 1건(소스가 `opal-wtm-agent`로 개명된 뒤 잔존)으로, **어댑터 디렉토리가 install `clean_dirs` 대상이 아니라는 PLAN 지적이 이미 실현된 상태**. 현 기준으로는 정상 환경이 게이트를 막는다 | 검출 |
| 20 | 2026-09-02 19:31 | EXECUTE | FIX | (#18·#19 참조) PM 권한으로 F-005 보강 지시 — (A) TS-011을 4곳 전수 바이트 대조로 확장(행번호 비의존 앵커, 4곳 미만 추출 시에도 FAIL) (B) S-13을 "파일 수" → "소스 집합 포함 판정 + 고아 열거"로 정밀화. 기준 변경이 아니라 검증 강화이므로 에스컬레이션 불요로 판정 | 반영 완료 — TS-011 `count=4/4 all bytes identical`, **음성 대조 통과**(폴백 1곳 `"order":10`→`11` 변조 시 `mismatch=mac_fallback`으로 FAIL, 원복 검증까지 수행) |
| 21 | 2026-09-02 19:31 | EXECUTE | DECISION | 고아 `wtm-agent.md`(cursor·gemini) 삭제를 이번 범위에서 제외하고 캡틴 판정으로 이월. 근거: 사용자 홈 디렉토리 정리는 태스크 목표와 무관하고, `.opal/AGENT.md` §금지사항의 배포 경계 취지상 PM이 임의로 배포본을 지우지 않는다. 워커 프롬프트에 삭제 금지를 명시 | 이월 |
| 22 | 2026-09-02 19:31 | EXECUTE | DECISION | Step 8(실 재배포) 착수를 PM 자율로 판단. 근거: agentic 모드는 CLOSE를 제외한 전 구간 PM 자율이고(`opal-harness-agentic.md` §4), 재배포는 이 프로젝트의 표준 절차이며(`.opal/AGENT.md` §금지사항 "install로 배포"), PLAN이 선백업·3-Run·원복 절차를 갖추어 가역적이다. 미결 사안(TS-018 AC)은 Step 8 실행에 의존하지 않는다 | 착수 |
| 23 | 2026-09-02 22:05 | EXECUTE | ERROR | **Step 8 1회차 블로커 — install 실행 불가**. `scripts/install-mac.sh:498`·`:819`가 `:470`의 `readonly OPAL_ADAPTER_FIELD_SPEC`과 같은 이름에 커맨드 prefix-assignment를 시도해 `readonly variable` 오류로 즉시 중단. PM이 최소 재현으로 확인(`bash -c 'readonly X="a"; X="b" echo hi'`). **단위 테스트 14개 중 13개 PASS인데 실물이 한 줄도 실행되지 않는 상태** | 검출 — 워커가 scope 밖이라며 임의 수정 없이 중단·보고(규율 준수) |
| 24 | 2026-09-02 22:05 | EXECUTE | ERROR | (#23의 근본 원인) **테스트 seam이 프로덕션 실행 형태와 어긋남**. 하네스 `extract_fn`이 함수 본문만 추출해 독립 실행하므로 전역 `readonly` 선언이 없는 컨텍스트에서 prefix-assignment가 정상 동작했다. 함수 내 자기완결 폴백은 그 seam을 성립시키려 넣은 것인데 결과적으로 프로덕션과의 차이를 가렸다 | 검출 — 이번 태스크 최대 산출 |
| 25 | 2026-09-02 22:05 | EXECUTE | FIX | (#23·#24) 수정 지시 — (A) `env` 경유 전달로 readonly 충돌 해소(v4.8) (B) **하네스가 전역 센티넬을 먼저 로드**하도록 seam 교정 + `install-mac.sh` strict 기동 케이스 TS-024 신설, fix 전 FAIL 관측 후 GREEN 전이 요구(RED-first) | 반영 완료 — seam 교정 즉시 fix 전 상태에서 TS-001·003·004·005·007·008·024가 전부 FAIL로 전환(**교정된 seam이 버그를 소급 재현**), fix 후 전건 GREEN. PM 직접 실행으로 PASS=14/FAIL=1 확인. windows.ps1은 동일 결함 없음(`Set-Variable -Option Constant/ReadOnly` 0건) |
| 26 | 2026-09-02 22:45 | EXECUTE | ERROR | Step 8 워커 2회 연속 스톨(결과 없이 종료). 하네스 §1 "워커 프로세스 비정상 종료" 규율 적용 — 1회 동일 컨텍스트 재개 후 동일 지점 재실패 시 즉시 중단 | 검출 |
| 27 | 2026-09-02 22:45 | EXECUTE | DECISION | (#26) **스톨 원인 규명 — 절차 설계 결함**. `install-mac.sh`가 OPAL Console 프론트엔드 빌드를 포함해 Bash 도구 타임아웃(120초)을 초과한다. PM이 직접 실행해 동일 현상 재현. 워커 결함이 아니며, PLAN Step 8이 install 3회 실행을 요구하면서 이 소요를 반영하지 않은 것이 원인이다 | 규명 — 프레임워크 개정 대상으로 DONE.md 이월 |
| 28 | 2026-09-02 22:45 | EXECUTE | DECISION | Step 8 잔여를 **PM이 직접 인수**(디스패치 의무 예외). 근거: ①하네스가 재시도 중단을 지시 ②프로브가 사용자 환경에 실제 에이전트 타입으로 노출된 상태라 지체 시 오염 지속 ③잔여 작업(원복·doctor)은 태스크 범위 구현이 아니라 PM이 지시한 검증 스캐폴딩의 회수다. 워커에는 즉시 정지 지시 | 인수 |
| 29 | 2026-09-02 22:45 | EXECUTE | GATE | Step 8 ①~④·⑥ PM 실측 판정 — ①백업 `/tmp/opds105-backup.b1D0Tu` ②Run A 완주(어댑터 60건 19:52 재생성) ③diff 차이 `opal-test-agent` 1건×4플랫폼, **미배포 소스 드리프트(커밋 `9d2644e`)로 전량 설명**되고 본문 1행뿐·frontmatter 무변경이라 emit 회귀 아님 ④프로브 4플랫폼 키 검증 전건 PASS(Claude `effort: high` / Codex `model_reasoning_effort = "high"` / Gemini·Cursor 키 부재·Cursor `model: inherit` 유지) ⑥`~/.codex/config.toml`에 정식 키 존재·`max_threads` 0건·`[hooks.state]` 무손상 | Pass |
| 30 | 2026-09-02 22:45 | EXECUTE | ERROR | **PM 자기 과실** — 워커의 install이 백그라운드로 돌고 있을 가능성을 확인하지 않고 PM이 Run C install을 실행해 동시 실행 충돌 위험을 만들었다. 워커가 이를 감지해 "두 install 결과를 확인해야 한다"고 정확히 지적했다 | 검출(자기 지적 반영) — 최종 상태를 PM이 재실측하여 확정 |
| 31 | 2026-09-02 22:45 | EXECUTE | IMPROVE | S-10 판정 기준의 한계 확인 — 실환경에서 "diff 공집합"은 과도하게 엄격하다(미배포 소스 드리프트가 정상적으로 차이를 만든다). 올바른 기준은 "차이가 소스 변경으로 전부 설명되는가"다 | S-13과 동일 계열의 검증 정밀화로 TEST 단계에서 반영 |
| 32 | 2026-09-03 | EXECUTE | GATE | Step 8 ⑤ Run C 원복 완료 — 프로브 소스 삭제 후 `~/.opal/agents/` 자동 복귀(`clean_dirs`), 플랫폼 어댑터 고아 4개는 PM이 AUTO-GENERATED 헤더 확인 후 삭제. **5경로 `probe-effort-105` 잔존 0건**, 파일 수 15/21/16/15 착수 시점 복귀, 기존 고아 `wtm-agent.md` 2건 불변, 사용자 파일 5개 미접촉 | Pass |
| 33 | 2026-09-03 | EXECUTE | GATE | Step 8 ⑦ 완료기준 (d) — `codex doctor --summary` **17 ok · 1 idle · 1 notes · 0 warn · 0 fail**, 에이전트 TOML malformed 경고 0건, `~/.codex/config.toml` `[agents]`에 `max_concurrent_threads_per_session = 6` 확정. **Step 8 ①~⑦ 전건 완료** | Pass |
| 34 | 2026-09-03 | EXECUTE | ESCALATION | (#12 해소) R-6 AC(a) 재정의를 **캡틴이 승인**. 판정 대상을 "소스 텍스트 grep"에서 "install이 생성·수정한 결과 파일"로 이전한다. 문자열 난독화는 금지로 명시. 3회 보류 끝에 캡틴 결정으로 확정 | 승인 — 재정의 작업 디스패치 |
| 35 | 2026-09-03 | EXECUTE | DECISION | 기존 고아 `wtm-agent.md`(cursor·gemini) 2건은 캡틴 답변이 없어 **삭제하지 않고 이월 유지**. 승인 발화가 R-6 AC 사안에 대한 것이므로 미언급 사안까지 확대 해석하지 않는다 | 이월 유지 |
| 36 | 2026-09-03 11:08 | TEST | GATE | TEST PM Gate — 컨벤션 진단 **Critical 0 / High 0**(Info 3, 조치 불요), 스위트 15/15, 회귀 22/22, `bash -n` OK, 시크릿 0건. **예외 1건 명시**: S-14(Windows 런타임, R-4 AC 일부)가 `pwsh` 미설치로 미검증 — "모든 시나리오 PASS" 항목만 미충족이며 재시도로 해소 불가하므로 통과로 처리하되 현황판 비고에 기록 | Pass (예외 명시) |
| 37 | 2026-09-03 13:08 | CLOSE | GATE | CLOSE 진입 게이트 — 캡틴 발화 "확인" 수신. `test.user_confirm` 행을 `--owner user`로 mark. agentic 모드에서도 자동 승인이 거부되는 유일 구간이며 규율대로 캡틴 발화를 받아 통과 | Pass |
| 38 | 2026-09-03 13:11 | CLOSE | ERROR | PLAN Step 9의 문서 갱신 범위 누락 — Step 9는 `docs/ARCHITECTURE.md`만 지목했으나 PM이 `docs/` 전수 grep을 수행해 `docs/architecture-diagram/opal_framework_architecture.html:599`에 legacy `max_threads` 표기 1건이 더 있음을 발견 | 검출 — 함께 정정하여 `docs/` 내 legacy 0건 달성 |
| 39 | 2026-09-03 13:11 | CLOSE | IMPROVE | (#38) 교체형 태스크의 문서 갱신 완료 기준은 특정 파일 지목이 아니라 **경로 전수 grep**이어야 한다. Step 9가 파일 1개만 지목한 탓에 다이어그램 HTML이 빠질 뻔했다 | 이월 — 후속 프레임워크 개정 후보 |
| 40 | 2026-09-03 13:15 | CLOSE | GATE | brain ingest 완료 — concept 신규 2건(테스트 seam 자기완결 폴백 / 교체형 AC 산출물 기준) + 갱신 2건(어댑터 플랫폼 격리 실체화·active 승격 / 존재검사≠버전검사에 3번째 사례 추가). index 315페이지 재스캔·log 기록 완료 | Pass |
