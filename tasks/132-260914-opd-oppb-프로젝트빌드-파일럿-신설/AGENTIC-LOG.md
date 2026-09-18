# AGENTIC-LOG: OPPB 프로젝트 빌드 Pilot 신설

> 모드: agentic | 시작: 2026-09-14 13:12 | 스킬: //opd

## 요약

| 항목 | 건수 |
|------|------|
| 게이트 판단 | 39회 (Pass: 38 / Fail: 1) |
| 3회 초과 Gate | 0건 (Critical: 0 / Normal: 0 / Minor: 0) |
| 오류 발견 | 24건 |
| 수정 지시 | 5건 (반영: 3 / 미반영: 2) |
| PM 의사결정 | 38건 |
| 개선 사항 | 16건 |
| 에스컬레이션 | 4건 |

## 대행 일지

| # | 시점 | 단계 | 카테고리 | 내용 | 결과 |
|---|------|------|----------|------|------|
| 1 | 2026-09-14 13:12 | TASK | DECISION | 태스크 범위를 제안서 §14의 Work item 그룹 G1~G5 전체로 단일 태스크화. 근거: OPPB가 OPPD를 교체하지 않게 되어 v1 기준선 측정·비교 benchmark가 사라졌고, 사람이 세션을 운용해야 하는 구간이 없어져 분할 근거가 소멸 | 소유자 승인 완료 |
| 2 | 2026-09-14 13:24 | ANALYSIS | GATE | 산출물 ANALYSIS.md 직접 Read 검증. 분석 질문 Q1~Q8 전부 응답, 모든 사실 주장에 `경로:줄번호` 근거 존재, 주입 제약(배포 경계·플랫폼 분기·state-tool·C-2) 반영 확인, 미승인 폴백 없음 | Pass |
| 3 | 2026-09-14 13:24 | ANALYSIS | ERROR | 워커가 착수 차단으로 보고: run root/cache root의 `<allocator_root>` 배치가 `worktree.md:36-44`의 "allocator_root 쓰기 대상은 허브 `.opal/MEMORY.json`뿐" 조항과 상충 | PM 실측 검증 수행 |
| 4 | 2026-09-14 13:24 | ANALYSIS | DECISION | **충돌 아님 — 조항 범위 오독으로 판정.** 근거: `worktree-tool`이 이미 허브 루트에 `.opal-worktrees/.meta/task_NNN.json`을 쓰고 있고(실측: task_123/126/127.json 존재), `.gitignore:42`로 미추적이며 `.opal/` 바깥이다. 표의 "쓰기 대상" 열은 allocator_root의 **태스크 귀속 계약상 역할**(채번·merge history)을 정의한 것이지 허브 루트 전체에 대한 쓰기 금지가 아니다. 두 `[MUST]`는 (1) allocator_root 경로 추론 금지 (2) 워커에게 allocator write 권한 부여 금지이며, Controller-tier 도구가 자기 소유 미추적 run/cache root를 쓰는 것은 어느 쪽도 위반하지 않는다. 따라서 제안서(a안)를 고치지 않는다 | 제안서 무변경 확정 |
| 5 | 2026-09-14 13:24 | ANALYSIS | DECISION | 다만 동일 오독 재발을 막기 위해 `worktree.md` 계약 절에 적용 범위 한정 1행을 추가하는 것을 **PLAN Work item으로 이관**한다. 지금 수정하지 않는 이유: Guards 구현 금지 원칙상 소스 변경은 EXECUTE 단계 소관 | PLAN 이관 |
| 6 | 2026-09-14 13:35 | PLAN | GATE | PLAN.md 직접 Read 검증 + `--plan-contract-check`·`--code-scan-citation-check` PM 재실행(둘 다 pass, W-1~W-36 전수 인식). AC-1~AC-21·C-1~C-9 전부 Work item 연결 확인, 제안서 33개 수용기준 전수 등장 확인 | Fail — 아래 ERROR |
| 7 | 2026-09-14 13:35 | PLAN | ERROR | §Acceptance mapping이 제안서 §13.2 "수용기준의 구현·증거 owner는 Work item 그룹에 **단일 배정**한다"를 위반한다. 5개 행이 복수 그룹(G3·G4, G2·G4, G1·G5, G1·G2, G1·G2·G4)을 기재해 각 체크포인트가 "이 그룹에서 무엇이 닫혔는가"를 판정할 수 없다. 특히 기준 24는 제안서가 G1에 배정했으나 내용(Supervisor 재부착)은 G2 소관이고, D5는 기준 25 일부를 G2→G1로 옮겼다 — 둘 다 제안서 배정표와의 불일치가 문서에 명시되지 않았다. C-1("제안서 본문과 어긋나는 구현 금지, 변경이 필요하면 제안서를 먼저 고친다") 위반 | 재지시 (루핑 1/3) |
| 8 | 2026-09-14 13:35 | PLAN | FIX | ERROR#7 재지시 — (1) 매핑표를 제안서 33개 기준 per-criterion 1행·단일 소유 그룹으로 재작성 (2) 제안서 배정표와 달라지는 항목을 근거와 함께 정정 목록으로 명시 (3) 제안서 §13.2 배정표 수정을 Work item으로 추가해 C-1을 닫을 것 | 발신 |
| 9 | 2026-09-14 13:38 | PLAN | GATE | 수정본 재검토 — §Acceptance mapping이 제안서 33개 기준 per-criterion 33행·소유 그룹 단일값으로 재작성됨. `기여(비소유)` 열 분리, AC-17·AC-21 별도 소유 고정, `### 제안서 배정 정정` 3건(기준 3·24·25) 근거와 함께 명시, W-37로 제안서 갱신 Work item 등록. PM이 두 검사 재실행(37 items·52 targets, 둘 다 pass)하고 제안서 무변경을 git status로 확인 | Pass (루핑 1회 후 해소) |
| 10 | 2026-09-14 13:38 | PLAN | DECISION | 기준 3의 G3→G4 정정을 채택. 워커 근거가 타당 — G3는 이미 생성된 단일 worktree 안의 lease 격리만 집행하므로 worktree 개수 자체를 자기 그룹 산출물로 닫을 수 없고, 관측·단언 주체는 G4의 W-28 fixture다 | 채택 |
| 11 | 2026-09-14 13:43 | TEST-SCENARIO | DECISION | RED-first 부분 적용으로 판정 — 도구·런타임 코드(opal-agent·state-tool·oppb-runtime-tool 전 모듈)는 `구현 전 RED`, 스킬·에이전트·레지스트리·문서 동기화는 행위 불변 문서 작업이라 `구현 후`, fixture 18회는 배포 자산 사용이라 `설치 후`. 근거: `harness/red-first.md` §1 | 확정 |
| 12 | 2026-09-14 13:43 | TEST-SCENARIO | GATE | 목표-커버 게이트 통과 증거 2종 확보 — (1) `scenario-coverage-build`·`scenario-coverage-check` exit 0, `all_covered: true`(요구 30·위험 5·시나리오 22) (2) `opal-evaluator-agent` scenario-rubric `verdict: pass`, 목표 2·채택 2·경계 2, 평균 2.0, gaps 0. 작성자(PM)와 평가자를 분리했고 PLAN 작성자와도 분리됨 | Pass |
| 13 | 2026-09-14 13:43 | TEST-SCENARIO | IMPROVE | evaluator가 gap이 아닌 참고로 지적 — AC-21의 "설치 스크립트가 신규 자산을 배포한다"를 S-18은 문서·레지스트리 행만 직접 확인하고 배포 자체는 S-19/S-20의 전제로 간접 확인한다. 게이트 통과 후 산출물 변경은 증거를 무효화하므로 TEST-SCENARIO를 고치지 않고, W-33("skills·agents 디렉토리 자동 배포 확인")이 이미 소유한 검증으로 EXECUTE에서 닫는다 | W-33으로 이관 |
| 14 | 2026-09-14 13:45 | EXECUTE | ERROR | `scenario-init`이 TEST-SCENARIO.md를 파싱하지 않고 `--scenarios` JSON 배열을 요구함(최초 호출 `scenarios_count: 0`). PM이 TEST-SCENARIO.md 표에서 id·acceptance_ref·type·expected·red_required 5필드를 추출해 재호출, 22건 등록 완료(red_required 17건) | 해소 |
| 15 | 2026-09-14 13:45 | EXECUTE | ESCALATION | **RED-first 잠금 계약과 PLAN 그룹 순서의 구조적 충돌.** `scenario-lock`은 `red_required==true` 17건이 **전부** `red_confirmed`여야 잠기고, 잠금 전에는 GREEN 구현을 시작할 수 없다(`harness/red-first.md` §1.5-4). 그런데 17건의 RED를 관찰하려면 테스트 스위트 5종(W-2·W-10·W-17·W-28·W-35)을 먼저 작성해야 하고, 이들은 P1·P4·P6·P8·P11로 흩어져 있다. 즉 PLAN의 그룹 순서를 따르면 영원히 잠글 수 없고, 잠그려면 그룹 순서를 깨야 한다. PM 임의 판단으로 PLAN 실행 구조를 바꾸지 않고 소유자에게 올린다 | 소유자 결정 대기 |
| 16 | 2026-09-14 14:53 | EXECUTE | DECISION | ESCALATION#15에 대해 소유자가 1안(테스트 스위트 P1 전진 배치)을 승인. 실행 그룹을 P1~P13으로 renumber하고 W-2·W-10·W-17·W-28을 P1에 모은다. 구현 Work item의 그룹 선후(C-7)는 그대로 유지되며 `[G1]`~`[G5]` 표기가 제안서 그룹 대응을 계속 소유한다 | 소유자 승인 |
| 17 | 2026-09-14 14:53 | EXECUTE | ERROR | TEST-SCENARIO S-7(`oppb-runtime-tool init`)이 red_required인데 어떤 테스트 Work item도 소유하지 않음을 재편성 중 발견. W-10 변경 대상에 `tests/test_oppb_init.py` 추가를 함께 지시 | 재지시에 포함 |
| 18 | 2026-09-14 14:53 | EXECUTE | IMPROVE | 테스트 전진 배치의 부작용을 위험으로 등록하도록 지시 — 미확정 G2 API(W-11 동결)에 테스트가 결합하면 동결 시 대량 수정이 발생한다. 대응은 W-10·W-17·W-28을 공개 CLI·파일 계약 수준에서만 작성하고 내부 함수 시그니처에 결합하지 않는 것 | 재지시에 포함 |
| 19 | 2026-09-14 15:00 | EXECUTE | GATE | W-4·W-37 diff 직접 검증. worktree.md는 표 아래 1행 추가뿐이고 기존 두 `[MUST]` 문구 바이트 무변경. 제안서는 §13.2 배정표만 변경(기준 3→G4, 24→G2, 25 각주)되고 수용기준 33개 본문·§14 그룹 표는 diff 미포함. 배정 총계 33개 보존(G1 0 + G2 5 + G3 12 + G4 12 + G5 4) | Pass |
| 20 | 2026-09-14 15:00 | EXECUTE | IMPROVE | 기준 24가 G2로 이동하면서 **G1 소유 수용기준이 0**이 됐다. W-5(G1-CP)는 제안서 기준으로는 아무것도 닫지 않고, 마감 판정이 D6 회귀 기준 4항 + TASK AC-19·C-8·C-9로만 성립한다. D6이 실질 게이트로 작동하므로 공백은 아니라고 판단해 재작업하지 않는다. G1의 산출물 가치(attempt runtime API·OPPL 회귀)는 G2 기준 24와 G5 기준 22가 증거로 소비한다 | 현행 유지 |
| 21 | 2026-09-14 15:00 | EXECUTE | IMPROVE | 경미 — 제안서 §13.2 배정표의 각주 `*`가 G1 행("없음*")과 G2 행("25*") 두 곳에 붙어 있는데 각주 본문은 기준 25만 설명한다. 표현상 모호하나 의미 왜곡은 없어 재지시하지 않는다 | 현행 유지 |
| 22 | 2026-09-14 15:05 | EXECUTE | ERROR | **RED 전진 배치의 미식별 부작용 발견(H-6 확장).** W-28이 보고 — PLAN·제안서가 이름을 명시하지 않은 구간(`run.sh` 서브커맨드명, run root 파일명)을 RED 테스트가 사실상 계약으로 고정했다. W-10·W-17도 같은 구간을 각자 고정할 것이므로 **세 워커의 명명이 충돌하면 GREEN에서 대량 RED 재작성**이 발생한다. H-6은 "내부 시그니처 결합"만 다뤘고 이 축은 대응에 없었다 | P1 게이트에서 통합 조정 |
| 23 | 2026-09-14 15:05 | EXECUTE | DECISION | 조정 방식 확정 — 네 RED 워커가 전부 반환한 뒤 PM이 각 스위트가 고정한 CLI 서브커맨드·run root 파일 계약을 **한 표로 취합해 단일 명명 계약**을 만든다. 충돌 지점만 골라 해당 RED를 정정하고, 이후 GREEN 디스패치(W-6~W-9·W-12~W-16·W-19~W-27)에 그 표를 구현 계약으로 주입한다. 지금 개별 조정하지 않는 이유는 세 스위트를 다 봐야 충돌 여부를 알 수 있기 때문이다 | 대기 |
| 24 | 2026-09-14 15:07 | EXECUTE | ERROR | **명명 충돌 실제 확인.** W-28은 run 식별을 `--run-root`로, W-10은 `--run-id`로 고정했다. 서브커맨드도 W-28 `project-run`·`revalidate` vs W-10 `start`·`resume`·`status`·`workgraph load`·`evidence submit`·`task accept`로 갈렸다. `--json` 플래그도 W-28은 명시, W-10은 기본 동작으로 가정. W-17 수신 후 3자 취합해 단일 계약으로 정정한다 | P1 게이트에서 조정 |
| 25 | 2026-09-14 15:07 | EXECUTE | ERROR | W-10 보고 — S-8(test_controller) fixture가 OPPB `pipeline.json`에 선행 의존하는데 그 산출물은 **W-20(P9)** 소관이다(워커는 W-12로 오기). 그대로 두면 G2-CP(W-11, P6)가 소유 기준 25를 P6에 닫을 수 없고 P9까지 밀린다 | 정정 필요 |
| 26 | 2026-09-14 15:07 | EXECUTE | DECISION | S-8 의존 해소 방식 확정 — `state-tool init`이 `--rows-from <path>` 외에 `--rows-spec <inline-json>`을 지원함을 실측 확인했다. S-8 fixture가 실제 `pipeline.json` 대신 최소 inline rows-spec을 쓰면 W-20 의존이 사라지고 G2-CP가 P6에 기준 25를 닫을 수 있다. 검증 의도(state.json↔workgraph.json 상호 직접 쓰기 0)는 rows 출처와 무관하므로 손실이 없다 | P1 정정에 포함 |
| 27 | 2026-09-14 15:07 | EXECUTE | GATE | W-2 결과 검토 — golden 9파일을 **변경 전 HEAD에서** 수집 완료(실모델 호출 0, 기존 공개 플래그 `--bin` stub 사용). D6 (a)(b)(c)(d) baseline 15건이 현재 green이며 이것이 H-1 게이트다. S-1 2 failed / S-2 7 failed / S-3 3 failed로 RED 확보. 기존 회귀 `42 passed` 무영향 | Pass |
| 28 | 2026-09-14 15:07 | EXECUTE | DECISION | W-2가 제기한 계약 가정 3건을 채택한다 — (1) run root 전달은 D6 (b)가 CLI 플래그 집합을 동결했으므로 신규 플래그 대신 환경변수 `OPAL_AGENT_RUN_ROOT` (2) attempt record 필수 키 `attempt_id`·`pid`·`pgid`·`exit_reason`, 값은 `completed`/`timeout` (3) epilogue allowlist는 `background_tasks_changed`·`task_updated`. 근거: D6가 플래그 집합 무변경을 회귀 기준으로 못박았으므로 신규 플래그 추가는 자기모순이다. W-1 디스패치에 구현 계약으로 주입한다 | 채택 |
| 29 | 2026-09-14 15:07 | EXECUTE | IMPROVE | W-2가 stream timeout golden을 바이트 비교에서 제외하고 사유를 명시 — 현행 `_run_stream`이 deadline을 stdout 줄 수신 루프 안에서만 확인해 `.events.jsonl` 줄 수가 타이밍 의존이라 결정론 고정이 불가능하다. 이 축은 S-2가 줄 수 대신 deadline 집행·PGID 회수·종료 사유로 판정한다. 타당한 판단으로 수용 | 수용 |
| 30 | 2026-09-14 15:11 | EXECUTE | GATE | W-17 결과 검토 — 5파일 41 테스트 전부 RED. H-6 준수(Python import 0), mock 0. `reset --hard`·전체 restore 금지를 PATH 앞단 git audit shim으로 **기계 단언**하고 그 shim 자체를 3중 검증(무해 호출 미검출 / 실제 `reset --hard` 검출 / 빈 로그 시 감사 채널 무효 실패)한 것이 특히 좋다 | Pass |
| 31 | 2026-09-14 15:11 | EXECUTE | DECISION | **단일 CLI 명명 계약 확정.** 실측 결과 `--run-root` 6파일 vs `--run-id` 4파일, `--project-root` 5 vs `--task-capsule` 1, `--json` 명시 2 vs 기본 9. 확정: (1) run 식별은 `--run-root <abs>` 단일 — `run_id`는 `init` 응답 필드로만 존재 (2) 작업본은 `--project-root <abs>` (3) stdout JSON 기본, `--json` 플래그 표면에서 제거. 근거 — `--run-root`는 자기완결적이라 매 명령에 `--allocator-root`를 다시 요구하지 않고, 제안서 §4.5의 "run root" 용어와 일치하며, 다수파다 | 확정 |
| 32 | 2026-09-14 15:11 | EXECUTE | FIX | ERROR#24·#25 정정 디스패치 — 11개 RED 파일의 CLI 표면을 단일 계약으로 통일하고, S-8 fixture를 `--rows-from <pipeline.json>`에서 `--rows-spec <inline>`으로 교체해 W-20(P9) 선행 의존을 제거한다. red-first §1.5-5에 따라 단언의 기대값·엄격도를 낮추지 말 것과, audit shim·mock 금지·H-6 유지를 명시했다 | 발신 |
| 33 | 2026-09-14 15:11 | EXECUTE | IMPROVE | W-17 주의 — PLAN이 W-17 변경 대상을 5파일로 한정해 `tests/conftest.py`가 누구 소유도 아니었고, 결과적으로 git fixture·CLI 헬퍼·audit shim이 파일마다 인라인 중복됐다. 지금 정리하면 RED 계약이 흔들리므로 손대지 않고, GREEN 안정화 이후 별도 정리 대상으로 남긴다 | 이월 |
| 34 | 2026-09-14 15:18 | EXECUTE | GATE | 정정본 PM 재검증 — 금지 토큰(`--run-id`·`--task-capsule`·`--json`) 0건, H-6 내부 import 0건, git audit shim 2파일 보존 확인. oppb 스위트 `32 failed, 67 errors, passed 0`으로 전부 RED 유지(약화 없음), opal-agent 스위트 `12 failed, 45 passed`로 golden baseline 유지 | Pass |
| 35 | 2026-09-14 15:18 | EXECUTE | ERROR | **`scenario-red` 16/17 기록 후 S-6 누락 확인.** 원인 — PLAN W-3이 `state_tool.py` 구현과 `test_state_tool.py` 테스트를 **한 Work item에 묶어** P2에 두었다. P1 전진 배치 때 테스트 스위트 4종만 옮기고 W-3 안에 숨은 테스트를 못 봤다. 결과적으로 (1) S-6 RED가 P1에 부재해 `scenario-lock`이 16/17에서 막히고 (2) 같은 워커가 테스트와 구현을 다 하므로 `red-first.md` §1.5-2(구현자와 다른 주체가 실패 테스트 작성)를 위반한다 | 분리 디스패치 |
| 36 | 2026-09-14 15:18 | EXECUTE | DECISION | W-3의 테스트 부분만 분리해 `opal-test-agent`에 선작성 지시. `state_tool.py` 수정 금지를 명시해 생성자·검증자 분리를 복원한다. S-6 fixture도 `--rows-from <pipeline.json>`(W-20, P9) 대신 `--rows-spec` 인라인을 쓰게 해 선행 의존을 제거했다 — `test_controller.py`의 `MINIMAL_PROJECT_ROWS` 선례를 따르게 했다. W-3은 이후 구현 전용으로 남는다 | 발신 |
| 37 | 2026-09-14 15:28 | EXECUTE | GATE | **RED-first 잠금 완료.** `scenario-lock` locked=true, red_required 17/17 red_confirmed. S-6 검증 시 `state_tool.py` diff 0으로 생성자·검증자 분리 실증. 기존 state-tool 회귀 410 passed 무영향 | Pass |
| 38 | 2026-09-14 15:28 | EXECUTE | IMPROVE | ERROR#35와 같은 구멍(구현+테스트 혼재 Work item)을 PLAN 전수 스캔으로 점검 — 담당이 `opal-test-agent`가 아닌데 변경 대상에 test 파일을 포함한 항목은 **W-3 하나뿐**. 이미 분리 처리했으므로 추가 조치 불요. W-3은 이후 구현 전용으로 취급한다 | 확인 완료 |
| 39 | 2026-09-14 15:34 | EXECUTE | GATE | W-3 GREEN 검증 — `state_tool.py` 4줄 변경(choices에 `oppb`, STAGE_ENUM에 P0~P5)만으로 `TestT132OppbStageEnumExtension` 3건 GREEN. 전체 `413 passed, 3 skipped, 111 subtests`로 기존 410건 무영향, opd·oppd·oppl regression guard 통과. 070 R-8 선례와 동일한 additive-only 패턴 확인 | Pass |
| 40 | 2026-09-14 15:34 | EXECUTE | ERROR | **잠재 결함 실측 발견 — `skill_enum` 이중 정의.** `state_tool.py`에는 skill 허용 목록이 두 곳에 있다: argparse choices(~3985, W-3이 `oppb` 추가 완료)와 `validate_pipeline_spec()` 내부 로컬 상수 `skill_enum`(:1247, `oppb` 없음). `:1248`이 `spec_skill_invalid`를 내고 `:1312`·`:2147`이 이 함수를 호출한다. PLAN §Appendix A와 W-20의 `pipeline.json`은 `"skill": "oppb"`이므로 **P9에서 `state-tool init --skill oppb --rows-from` 왕복 검증이 막힌다.** S-6이 못 잡은 이유는 fixture가 `--rows-spec` 인라인이라 spec-validate 경로를 타지 않기 때문이며, 그 설계 자체는 W-20 선행 의존 제거를 위한 의도된 것이라 바꾸지 않는다 | RED 선작성 디스패치 |
| 41 | 2026-09-14 15:34 | EXECUTE | DECISION | W-3 워커가 `skill_enum`을 "PLAN 범위 밖"으로 남긴 판단은 문자적으로는 옳으나 결과적으로 P9를 막는다. RED-first를 지켜 **테스트를 먼저** 추가하고(생성자≠구현자) 이후 구현을 붙인다. 지금 처리하는 이유 — P9에서 발견하면 G4 체크포인트가 이미 지나간 뒤라 되돌아가야 한다 | 발신 |
| 42 | 2026-09-14 15:41 | EXECUTE | GATE | **W-1 GREEN 검증 — 이번 태스크 최대 위험 변경.** PM 직접 재실행 `57 passed`(착수 전 12 failed/45 passed). 테스트 tracked diff 0, golden 9파일 재생성 없음, 신규 `add_argument` 0건, 플랫폼 분기 문자열 0건. HEAD 소스와 현재 소스의 CLI 플래그 집합을 추출 대조한 결과 **동일**(`--bin --cwd --model --resume --system-prompt --timeout`) — D6 (b) 충족. 변경 규모 507+/47- | Pass |
| 43 | 2026-09-14 15:41 | EXECUTE | IMPROVE | W-1 워커가 디스패치 프롬프트의 "D6 baseline 15건"이 실제 수집 수와 다름을 실측으로 정정 보고(회귀 baseline 14건 + `TestAttemptRecordIsAdditive` 3건 = 17건). PM이 준 수치를 그대로 따르지 않고 실측으로 바로잡은 것은 올바른 행동이다. 집계 기준 차이이며 누락 아님 | 수용 |
| 44 | 2026-09-14 15:41 | EXECUTE | IMPROVE | W-1 부수 개선 — sync 경로가 `subprocess.run(timeout=)` 대신 독립 watchdog을 쓰게 되면서, 자식이 종료해도 손자가 파이프를 잡고 있어 `communicate()`가 무한 대기하던 경로에서도 deadline이 발화한다. PLAN이 명시하지 않은 이득이며 S-2 검증 범위 안에 있다 | 수용 |
| 45 | 2026-09-14 15:52 | EXECUTE | GATE | **W-5 G1 체크포인트 통과.** D6 4항을 AST 시그니처 추출로 소스 대조 — 공개 심볼 제거 0·시그니처 변경 0·신규 추가 25, argparse option string HEAD 14개 = 현재 14개 동일 집합, `AgentResult` 필드 블록 텍스트 동일, `main()` 출력 경로 라인 단위 동일. 회귀 `57 passed` / `418 passed·3 skipped·111 subtests` 기대치 정확 일치. 기존 3 Pilot 8개 경로 `git diff HEAD` 0줄 | Pass |
| 46 | 2026-09-14 15:52 | EXECUTE | ERROR | W-5가 merge 범위 문제 제기 — `opal/tools/oppb-runtime-tool/`의 RED 스위트는 설계상 `32 failed, 67 errors`이며 이대로 허브에 올리면 **main에 빨간 테스트가 상주**한다. C-8의 "깨끗한 중간 merge" 취지와 충돌한다 | 소유자 판단 필요 |
| 47 | 2026-09-14 15:52 | EXECUTE | ERROR | W-5 환경 결손 보고 — 테스트 실행 인터프리터에 `jsonschema`·`PyYAML` 미설치로 test-tool 2건 실패·brain-tool 수집 불가. PM이 재확인했고 해당 소스는 HEAD 대비 무변경이라 G1 결함이 아니다. 그러나 **이후 체크포인트에서 진짜 실패를 가릴 수 있다** | 이월 |
| 48 | 2026-09-14 17:18 | EXECUTE | ESCALATION | **허브 merge 직전 병렬 세션 충돌 발견.** 다른 세션이 태스크 131을 진행해 main에 merge(분기점 이후 7커밋). 131이 `opal_agent.py`를 759줄 고쳐 process group·watchdog·terminal framing·epilogue allowlist를 이미 구현했고 `oppl-runtime-tool`도 신설했다. 제안서도 구판이 복원돼 두 판본 공존. PM이 임의 판단하지 않고 소유자에게 3개 선택지로 보고 | 소유자 1안 선택 |
| 49 | 2026-09-14 17:18 | EXECUTE | DECISION | 1안(main 131 구현 기준 G1 재설계) 실행 — `git merge main` 후 충돌 1파일(`opal_agent.py`)을 main 버전으로 확정. `state_tool.py`는 자동 병합돼 131의 48줄과 132의 oppb·P0~P5가 공존(452 passed). 132 W-1의 554줄은 폐기 | 완료 |
| 50 | 2026-09-14 17:18 | EXECUTE | DECISION | 제안서 SSOT 확정 — `opal-oppb-project-build-pilot.md`(1034행)가 최신. 131 복원본(926행)은 "전면 교체" 프레이밍 5곳·OPPB 언급 0·신규 3개 절 부재로 개정 이전 구판임을 실측 확인. 131이 흡수했다는 고유 기여 2건은 1034행본 §4.6에 동일 문장으로 존재. 구판 제거 후 archives의 깨진 인용 1건을 새 경로로 복구 | 완료 |
| 51 | 2026-09-14 17:18 | EXECUTE | ERROR | **131이 attempt record까지 이미 구현.** `_attempt_record()`가 `<run_dir>/<phase>[.aN].attempt.json`에 원자 기록하며 스키마가 132 것보다 풍부(`pgid_reclaimed`·`exit_class`·`timeout_reason`·`heartbeat{count,last_at,expired}`·`unterminated_children`·`fingerprint`). 전달 채널도 환경변수가 아닌 `run_dir`·`phase`·`attempt` kwonly 인자다. **PM이 확정했던 `OPAL_AGENT_RUN_ROOT` 계약(로그 28)은 폐기한다** | 계약 폐기 |
| 52 | 2026-09-14 17:18 | EXECUTE | DECISION | G1 잔여 범위를 2건으로 축소 — (1) 재부착·고아 판정 진입점 신설(`opal-agent`·`oppl-runtime-tool` 양쪽에 부재, S-4가 요구) (2) D6(a)를 "시그니처 무변경"에서 "기존 호출 호환성 유지"로 재정의(131이 추가한 kwonly 7개는 전부 기본값이라 호출 호환은 불변). 132 회귀 스위트는 폐기하지 않는다 — 131 구현 위에서 87 passed이고 golden 바이트 동일성이 그대로 유효하다 | PLAN 개정 지시 |
| 53 | 2026-09-14 17:44 | EXECUTE | GATE | W-2 정합 Pass — `94 passed, 0 failed`. ③ framing은 **131의 의도된 설계 차이**로 판정(결함 아님). 결정적 근거: D6(c)가 `.exitcode` 바이트 동일성을 회귀 기준으로 못박았으므로 framing 사유로 종료 코드를 바꾸는 것이 오히려 OPPL 계약 파괴다. 워커가 단언을 record 채널로 옮기면서 **같은 실행 경로에 정상 framing 대조군**을 넣어 "어떤 stream이든 error"로 통과하는 구멍을 스스로 막았다 | Pass |
| 54 | 2026-09-14 17:44 | EXECUTE | GATE | W-1 Pass — 재부착·고아 3분류 진입점 신설. **생존 확인을 record 완결성보다 먼저** 두어 실행 중 attempt의 오분류(중복 실행)를 차단했고, PID 재사용 방어를 `os.kill`→`getpgid` 일치→`ps etime` 역산 3중으로 쌓되 플랫폼 분기 0. 신원 미증명 시 재부착하지 않는 비대칭 판단(잘못된 재부착은 복구 불가, 잘못된 고아는 재기동으로 복구)이 옳다 | Pass |
| 55 | 2026-09-14 17:44 | EXECUTE | ERROR | W-1이 설계 공백 발견 — `_attempt_record()` 호출 지점이 finalize 1곳뿐이라 **실행 중 attempt는 record가 없고 `reattach` 분기가 도달 불가**. S-4 ①이 검증 불가 상태였다. 잠긴 시나리오라 기대를 못 바꾸므로 구현이 따라와야 한다 | W-39 신설 |
| 56 | 2026-09-14 17:44 | EXECUTE | DECISION | W-39 배치를 P2로 지시했으나 `--plan-contract-check`가 `file conflict W-1/W-39`로 거부. 같은 그룹·같은 파일·상호 선행 없음은 충돌이고 그룹 내 선행 선언도 금지된다. P3·선행 W-1로 재배치. **도구가 PM 판단 오류를 잡은 사례** — tool-gated 설계의 의도대로 작동했다 | 수용 |
| 57 | 2026-09-14 17:44 | EXECUTE | GATE | W-39 Pass — `reconcile-attempts`가 살아 있는 attempt에 `disposition: reattach`, `identity: confirmed`(PID 생존+PGID 일치+`ps etime` 역산 0.349초 차)를 실측 반환. 회귀 `94 passed` 유지, C-8 무영향(run_dir/phase 미지정 시 `ls -A` 공백) 실측 확인 | Pass |
| 58 | 2026-09-14 17:44 | EXECUTE | DECISION | W-39가 새 필드를 발명하지 않고 기존 20필드의 미확정 값(`status="running"`·`terminal=None`·`exit_code=None`)으로 진행 중 상태를 표현한 것을 채택. `StreamVerdict.status` 주석이 이미 `running`을 선언하고 있어 스키마 확장이 아니다. `outputs`를 시작 record에서 뺀 것도 옳다 — 죽은 뒤 시작 record만 남으면 `orphan/record_incomplete`로 올바르게 잡힌다 | 채택 |
| 59 | 2026-09-14 17:44 | EXECUTE | GATE | H-8 해소 확인 — PM이 워커 주장을 재검증. `opal-loop-action-agent/AGENT.md:253,260`이 완료 마커를 `.exitcode` **존재**로 못박고 `.result.json`·`.events.jsonl`로 판정하지 않음을 명시. `ledger.py`의 `json.load`·`is_file()` 5건은 전부 자기 `runtime.json`·config 대상이고, `record_path`는 `oppl_runtime_tool.py:339`에서 **문자열 외래 참조로만** 보관. OPPL에 "파일 존재 = 완료" 가정 없음 | Pass |
| 60 | 2026-09-14 17:52 | EXECUTE | GATE | W-38 Pass — `oppl-runtime-tool` 공개 표면 전수 실측 후 13축 대조. 중복 2건·고유 6건·공용 4건·정책 충돌 1건. **우려했던 "OPPL이 만든 걸 OPPB가 다시 만든다"는 사실상 없었고**, 진짜 위험은 W-8이 `opal-agent`의 프로세스 생존 판정 340줄을 다시 쓰는 것이었다. PLAN W-8 문구 "record를 **읽어**"가 파일 직접 파싱으로 읽혀 W-1 사고가 반복될 뻔했다 | Pass |
| 61 | 2026-09-14 17:52 | EXECUTE | DECISION | **P-5 run identity — 현 RED 표면 유지**(OPPB `init` 자체 발급). OPPL D8로 정렬하지 않는다. 근거: OPPL run root는 태스크 폴더 안 `.oppl-run/`이라 태스크 종속이 자연스럽지만, OPPB run root는 허브 `.opal-runs/`이고 제안서 `:269`가 "worktree 회수와 함께 삭제하지 않는다"를 요구한다 — **태스크보다 오래 살아남는 것이 설계 요구**라 state.json에 묶으면 깨진다. 정책 차이는 사고가 아니라 의도다 | 확정 |
| 62 | 2026-09-14 17:52 | EXECUTE | DECISION | **P-8 예산 게이트 — 현 범위 유지.** 제안서 §11 게이트 4를 집행하는 Work item이 없다는 실측을 수용하되, 태스크가 이미 40건이라 v1은 동시성 예산 3종만 집행하고 비용·무진전은 후속이 소유한다. C-1 준수를 위해 PLAN §Approach와 제안서 §11 양쪽에 명시 | 확정 |
| 63 | 2026-09-14 17:52 | EXECUTE | GATE | W-40 Pass — diff가 §11 구간 4줄 추가에만 존재(`git diff --stat` 4+/1-), §9.3·§13.2·§14 무변경, 게이트 항목 6개 유지. W-37의 `\*` 각주 스타일을 그대로 따랐다 | Pass |
| 64 | 2026-09-14 17:52 | EXECUTE | IMPROVE | W-40의 file conflict 회피가 정확했다 — W-37과 같은 파일이라 같은 그룹 불가. W-37이 P1에서 완료됐으므로 W-40을 P2로 내리고 선행에 W-37을 선언해 충돌 규칙과 dependency group order를 동시에 만족시켰다 | 수용 |
| 65 | 2026-09-14 18:08 | EXECUTE | GATE | **W-5 G1 체크포인트 재실행 — 품질 게이트 전부 통과.** D6 4항 AST 소스 대조 4/4(`call_agent` kwonly 7개는 전부 131 소유, 132 자체 델타 0 / `_build_parser` main과 AST 완전 동일). S-4 `reattach` 직접 재현(`identity: confirmed`, `age_delta 0.035s`, kill 후 `harvest` 전이, 고아 0). 기존 3 Pilot + `oppl-runtime-tool` 9/9 무변경. tool-scan 4건 실패는 pristine main 워크트리에서 동일 재현돼 기존 결손 확정 | Pass |
| 66 | 2026-09-14 18:08 | EXECUTE | ERROR | **PM 기록 누락 — 제안서 926행 삭제가 PLAN에 없다.** 삭제 자체는 소유자 승인을 받은 의도적 조치(로그 50)지만, W-37·W-40처럼 제안서 변경은 Work item이 있는데 삭제만 PM이 직접 수행하고 PLAN에 근거를 남기지 않았다. 워커 지적이 옳다 | PLAN 기록 지시 |
| 67 | 2026-09-14 18:08 | EXECUTE | ERROR | **PM 판단 착오 — RED 스위트 커밋 순서.** 1차 W-5가 "G1만 merge, RED 스위트 제외"를 권고했는데도 커밋을 `81d890d`(G1) → `74d3766`(RED) 순서로 쌓았다. 브랜치가 선형이라 지금 merge하면 `32 failed + 67 errors`가 main에 상주한다. 범위 분리가 불가능해졌다 | 전략 재판단 |
| 68 | 2026-09-14 18:08 | EXECUTE | DECISION | **G1 중간 merge 포기, G2 완료 후 merge로 변경(소유자 승인).** 조기 merge의 실익이 소멸했다 — 원래 근거인 "watchdog·PGID 수정의 OPPL 즉시 개선"은 131이 이미 main에 넣었고, G1이 추가하는 재부착 진입점·시작 record는 OPPB가 쓰기 전까지 소비자가 없다. 반면 브랜치 재구성 비용은 이득보다 크다. 미커밋 G1 산출물 5건은 `612db93`으로 커밋 완료 | 확정 |
| 69 | 2026-09-14 18:18 | EXECUTE | GATE | W-6 Pass — `test_oppb_init.py` 18건 GREEN(착수 시 18 failed), 회귀 546 passed 무영향, RED 테스트 diff 0, 신규 파일 정확히 3개. `init` 검사 순서를 **부작용보다 앞에 전부 배치**해 거부된 호출이 `.opal-runs/`·`.opal-cache/`를 남기지 않는 것이 좋다 | Pass |
| 70 | 2026-09-14 18:18 | EXECUTE | DECISION | W-6의 `init` 멱등 해법 채택 — 호출마다 run_id를 새로 발급해 **덮어쓰기 경로 자체를 없앴다.** `oppl`의 실패 모드(`cmd_init`이 기존 ledger를 무조건 `new_ledger()`로 덮어써 카운터 0 초기화, `:170-173`)를 구조적으로 복제 불가능하게 만든 설계다. 재개는 `init` 재실행이 아니라 `start --run-root`로 한다 | 채택 |
| 71 | 2026-09-14 18:18 | EXECUTE | IMPROVE | W-6이 RED에 없는 거부 1건 추가 — `allocator_root_not_repository_root`. allocator_root가 저장소 하위 디렉토리면 `.git/info/exclude`의 상대 패턴이 run root를 가리키지 못해 등록·판정이 성립하지 않으므로 선거부한다. 계약 약화가 아니라 강화이고 근거가 타당해 수용 | 수용 |
| 72 | 2026-09-14 18:18 | EXECUTE | IMPROVE | W-6이 범위 밖으로 지적한 `install-mac.sh` 배포 등재는 **PLAN W-33(P11)이 이미 소유**함을 확인. 배포 경로 실호출이 필요한 시점은 W-34(P12)의 fixture 실행이고 W-33이 그 앞이라 순서 문제 없음. 추가 조치 불요 | 확인 완료 |
| 73 | 2026-09-14 18:28 | EXECUTE | GATE | W-7 Controller 구현 검토 — `workgraph load` 표면은 5개 테스트 전부에서 GREEN이고 S-8 파일 계약을 실 git repo·실 CLI로 직접 확인했다(`workgraph.json`에 P0~P5 토큰 0·`task_steps`/`pm_gate`/`STATE.md` 0, 캡슐 누출 0, `.opal-runs` git 노출 0, revision 1→3 전진). `controller.py`에 `state.json` 문자열 자체가 없다. W-6 무회귀, 546 passed 유지 | 부분 Pass |
| 74 | 2026-09-14 18:28 | EXECUTE | ERROR | W-7이 판정 요청 — `test_controller.py:307`이 `state-tool advance <capsule>`을 **행 주소 없이** 호출해 `task_step_addr_required`로 거부된다. 테스트는 이를 "W-3 oppb 전이 지원 전 정상 실패"로 주석했으나 **오해다** — W-3은 enum만 추가했고 addressless advance와 무관하다 | PM 판정 |
| 75 | 2026-09-14 18:28 | EXECUTE | DECISION | **테스트 호출 형식을 고친다.** `state-tool advance`는 설계상 행 주소가 필수다 — 070 task-step 키 주소 체계, README `:11` "`advance`/`mark`/`block`/`add-row`는 `--task-step` / `--task-step-id` / `--row` 중 **정확히 하나**를 받는다". 인자 없는 advance는 존재하지 않는 기능이므로 state-tool에 추가하지 않는다(546 green에 영향). S-8의 검증 의도(`state.json` 전이가 `workgraph.json`을 건드리지 않음)는 불변이고, 오히려 **지금은 명령이 실패해 의도를 전혀 검증하지 못한다** — 호출 형식 복구는 약화가 아니라 강화다 | 정정 디스패치 |
| 76 | 2026-09-14 18:32 | EXECUTE | FIX | S-8 호출 정정 완료 — `advance` 인자 1줄과 주석·에러 메시지만 변경, **단언 2건은 diff에 등장하지 않음**을 PM이 직접 확인. 대상 테스트 GREEN, 나머지 4건은 W-8 대기로 실패(의도), `state-tool 452 passed` 유지로 무수정 증명 | 반영 |
| 77 | 2026-09-14 18:32 | EXECUTE | IMPROVE | 정정 과정에서 `--rows-spec` 제약 발견 — `build_rows_from_spec()`이 행에 `key` 필드를 채우지 않아 `--task-step <key>` 주소를 쓸 수 없고 `--task-step-id <n>`만 유효하다. W-20이 만들 실제 `pipeline.json` 경로에는 key가 있으므로 `--rows-spec` 경로 한정 제약이다. OPPB Product Flow(W-19)가 `--rows-from`을 쓰므로 실사용에는 영향 없으나, 테스트 fixture가 inline spec을 쓰는 한 이 제약이 계속 적용된다 | 기록 |
| 78 | 2026-09-14 18:41 | EXECUTE | GATE | W-8 Supervisor Pass — `test_supervisor.py` **5 passed**(2회 재현), `test_controller.py`도 5 passed로 함께 해소. `opal_agent.py` diff 0으로 **호출만** 했음을 증명. 잔존 `OPPB_TEST_*` 프로세스 0 | Pass |
| 79 | 2026-09-14 18:41 | EXECUTE | DECISION | W-8의 Verifier 우선 배정 설계 채택 — `saturated` 플래그로 **`max_total_agent_processes` 포화를 한 번 관측한 뒤부터만** Verifier를 신규 Runner 앞에 놓는다. 포화 전에 Verifier를 앞세우면 검증 대상이 생기기 전에 slot을 점유해 포화 자체가 성립하지 않는다는 판단이 옳다 — 수용기준 10의 전제("상한 포화 상태에서")를 그대로 코드로 옮긴 형태다. Runner+Executor를 **하나의 admission 단위**로 승인해 반쪽 in-flight를 막은 것도 좋다 | 채택 |
| 80 | 2026-09-14 18:41 | EXECUTE | GATE | W-9 Evidence Tool Pass — 거부 5단계를 전부 색인 **전**에 배치했고, 불변 색인을 `os.link(tmp, target)`으로 구현해 check-then-write TOCTOU 창을 없앴다. `task accept`도 락 밖 확인 후 트랜잭션 안에서 재확인. 작업 중 `controller.py` 랜딩을 발견하고 두 번째 lock+atomic-write 경로를 만드는 대신 소비자로 재설계한 판단이 옳다 | Pass |
| 81 | 2026-09-14 18:41 | EXECUTE | ERROR | **PM 실측 오류 — `runner_attempt_id` 판정을 틀렸다.** 내가 `grep ... | head -8`로 잘라 읽어 `test_evidence.py:314-317`을 못 보고 "테스트가 직접 요구하는 필드는 `scope_hash` 하나뿐"이라고 W-7에 지시했다. 실제로는 `scope_hash`와 동일한 형태로 직접 요구한다. 워커가 실측으로 반증했고 지시대로 필드를 추가하지 않고 보고한 것이 옳다 | 정정 |
| 82 | 2026-09-14 18:41 | EXECUTE | DECISION | `runner_attempt_id` (a)안 승인 — Controller가 공표한다. 파생 불가 근거 3건 실측 확인: 단언 시점이 `workgraph load` 직후라 `attempts[]`가 빈 배열, fixture(`:107,:113`)가 `pre_state: candidate_ready`에 `run_command` 없어 Supervisor 미기동, 따라서 runner attempt가 영원히 생기지 않는다. `pre_state`가 runner attempt 종료를 함의하는 상태에서만 발급하도록 제한했다 — 아무 태스크에나 심으면 W-8이 실제 dispatch할 때 충돌한다 | 승인 |
| 83 | 2026-09-14 18:41 | EXECUTE | GATE | W-7 애드덤 Pass — `compute_scope_hash`가 도메인 태그(`oppb-scope/v1`) + 4축 정규화(중복 제거·정렬·미선언 축 흡수) + `sort_keys` JSON의 sha256이다. 축 간 이동은 구분하고 표기 차이는 흡수한다. **공개 함수로 노출**해 W-12가 재구현하지 않게 한 것이 지시대로다. `test_evidence.py` 1 passed/6 failed → 6 passed/1 failed로 반전 | Pass |
| 84 | 2026-09-14 18:49 | EXECUTE | GATE | **G2 kernel 완성 검증.** `test_oppb_init` 18 · `test_controller` 5 · `test_supervisor` 5 · `test_evidence` 7 = **35 passed**. 공용 자산 회귀 `546 passed, 3 skipped, 111 subtests` 유지. W-10이 P1에서 선작성한 RED 스위트가 전부 GREEN으로 전환됐다 | Pass |
| 85 | 2026-09-14 18:49 | EXECUTE | GATE | W-8 주장 PM 재검증 — `supervisor.py`에서 `task["attempts"]`·`task.get("attempts")` **0건**. `attempts`를 다루는 지점은 전부 `reconcile-attempts` 응답 payload다. W-38 B-1이 지목한 재발 위험(340줄 재구현)이 실제로 회피됐다 | Pass |
| 86 | 2026-09-14 18:49 | EXECUTE | GATE | W-7 애드덤 2차 Pass — `runner_attempt_id` 발급을 `POST_RUN_STATES`(`candidate_ready`·`verifying`·`accepted`) 3종으로 한정. **`running` 제외 근거가 정확하다** — runner 비행 중이고 실제 `attempt_id`는 `create_execution_packet()`이 dispatch 시점에 발급하므로 미리 심으면 충돌한다. spec이 `runner_attempt_id`를 선언했는데 `pre_state`가 범위 밖이면 `spec_invalid` 거부 가드도 추가했다 | Pass |
| 87 | 2026-09-14 18:49 | EXECUTE | DECISION | 재사용 경계가 코드로 확보됨을 확인 — `controller.py` exports에 `POST_RUN_STATES`·`normalize_lease`·`compute_scope_hash` 노출(`:13,:62,:284,:293`). W-12(Scope Lease Tool)가 scope hash를 재구현할 이유가 없다. 이 태스크에서 두 번 난 중복 구현 사고의 구조적 예방 | 확인 |
| 88 | 2026-09-14 19:00 | EXECUTE | GATE | **W-11 G2 API 동결 Pass.** sha256 4종을 PM이 재계산해 `api-freeze.md` 기록값과 **전부 일치** 확인. 동결 기준 commit `612db93`, 상류 변경 `git log main ^HEAD` **0건**. 구현·테스트 파일 무변경(schema/ 5파일만 신규) | Pass |
| 89 | 2026-09-14 19:00 | EXECUTE | DECISION | W-11이 스키마를 **실측에서 뽑은 방식** 채택 — 코드 심볼 대조(TASK_STATES 8·ROLES 3·LEASE_AXES 4·COMMANDS 7·FLAGS 6·ERROR_CODES 52·이벤트명 5)와 실산출물 대조(격리 git 저장소에서 init→load→start→evidence submit→task accept 완주, 산출물 30건 전부 draft-07 통과, 음성 사례 2건 거부) 2방향. 검증용 `jsonschema`는 1회성으로만 쓰고 도구 런타임은 표준 라이브러리 전용 유지 | 채택 |
| 90 | 2026-09-14 19:00 | EXECUTE | IMPROVE | W-11이 실측 불일치 2건을 구현이 아니라 **스키마를 맞춰** 기술 — (1) `evidence`의 `schema_version`은 정수인데 `workgraph`·`acceptance`·`execution-packet`은 문자열 `"1.0"`. 각각 테스트가 단언하는 현행 계약이라 구현을 고치지 않았다 (2) `mini_task.evidence[]`는 계속 빈 배열이고 실제 역인덱스 소유자는 `acceptance.json`이다. 미래 용도를 추정해 채우지 않았다. "동결은 현재 사실의 고정이지 새 계약 선언이 아니다"라는 지시를 정확히 지켰다 | 수용 |
| 91 | 2026-09-14 19:00 | EXECUTE | DECISION | `attempt.attempt.json`을 동결 범위에서 **의도적 제외** 승인 — 그 필드 집합은 `opal-agent`의 `classify_attempt()` 입력 계약이고 소유자도 `opal-agent`라 G2가 동결할 대상이 아니다. `api-freeze.md` §3에 근거 기록됨 | 승인 |
| 92 | 2026-09-15 10:26 | EXECUTE | GATE | W-12 Scope Lease Pass — `10 passed`, G2 kernel 30건 무회귀, 스키마 sha256 4종 불변. `controller.` 호출 23회로 재사용 실증 — `compute_scope_hash`·`normalize_lease`뿐 아니라 락(`_locked`)·원자 쓰기(`_atomic_write_json`)까지 재사용해 `workgraph.lock` 하나로 직렬화. 신규 `leases.json`만 소유하고 `workgraph.json`은 읽지도 쓰지도 않는다 | Pass |
| 93 | 2026-09-15 10:26 | EXECUTE | DECISION | W-12의 충돌 판정 설계 채택 — `check-parallel`(dispatch 전 spec 쌍별)과 `acquire`(신규 ↔ active 전수)가 **같은 함수**를 쓰므로 admission과 집행이 어긋날 수 없다. 이것이 "동시 lease 0"의 실제 근거다. Verifier 포트를 `bind(0)`로 OS에서 실제 빈 포트를 받는 것도 겹친 채 검증 시작 경로를 없앤다 | 채택 |
| 94 | 2026-09-15 10:26 | EXECUTE | GATE | W-13 Environment Probe Pass — `8 passed`, 누적 18 passed(probe+lease), G2 kernel 35 무회귀, 스키마 sha256 불변. 입력 hash를 **repository tree 순회 없이** 5개 key(commands·bootstrap·config·lockfile·toolchain)로 한정한 것이 §P2.2 요구를 정확히 지켰다 — `src/app.py` 변경은 `fresh: true`, `lockfile.lock` 변경만 `fresh: false` | Pass |
| 95 | 2026-09-15 10:26 | EXECUTE | DECISION | W-13의 late discovery 판정 순서 채택 — 경로 안전성 → 이미 봉인 → lease 교차 → epoch 소비 → delta probe 실제 재실행 → 정책 분류 → 봉인. **앞 단계가 뒤 단계보다 항상 먼저 승격**하므로 민감 경로가 무과금 batch로 새는 경로가 없다. epoch 키를 `<task_id>|<revision>`로 잡아 revision 전진 시 새 무과금 epoch가 열리는 것도 §P2.2와 일치 | 채택 |
| 96 | 2026-09-15 10:26 | EXECUTE | DECISION | **스키마 드리프트 해법 확정 — (b)안: 동결 범위를 "G2 표면"으로 한정 명시.** W-12·W-13이 동일 blocker를 올렸고 W-14~W-16도 같을 것이다. (a)안(enum에 G3 명령 추가 후 재동결)은 G4에서 또 재동결이 필요해 sha256이 그룹마다 바뀌고 동결 자체가 무의미해진다. 개념적으로도 D3의 동결 대상은 **Controller·Supervisor·Evidence의 계약**이지 G3가 추가하는 자기 서브커맨드가 아니다. `command_name` 설명이 "COMMANDS·DISPATCH 키 집합과 동일"이라 쓴 것이 과도했다 — G2 시점 실측을 전체 표면으로 일반화한 오류다 | 확정 |
| 97 | 2026-09-15 10:40 | EXECUTE | GATE | G3 구현 5종 Pass — `test_lease` 10 · `test_probe` 8 · `test_checkpoint` 9 · `test_cache` 9 · `test_recovery` 5 = **41 passed**. `worktree_tool.py` diff 0, 스키마 sha256 불변, G2 kernel 35 무회귀 | Pass |
| 98 | 2026-09-15 10:40 | EXECUTE | DECISION | W-14의 write-window 귀속 규칙 수용 — S-12①(lease 밖 쓰기 거부)과 S-13①(타 Runner dirty 허용)은 git 상태만으로 구별 불가하고 유일한 관측 차이가 쓰기 순서(mtime)다. **동시각은 귀속 불가로 보수적 거부**하므로 false positive(위반인데 통과)는 없고 false negative만 가능 — 안전한 방향이다. FS 시간 해상도 의존은 W-18 확인 대상으로 이월 | 수용 |
| 99 | 2026-09-15 10:40 | EXECUTE | DECISION | `cache.py`가 `controller`를 재사용하지 않은 것을 정당으로 판정 — cache root(`<allocator_root>/.opal-cache/oppb/`)는 **run root 밖**이라 `controller._locked`의 `workgraph.lock`과 락 도메인이 다르다. 재사용하면 오히려 잘못된 직렬화다. scope hash 미사용도 정당(3계층 cache key는 lease와 무관) | 정당 |
| 100 | 2026-09-15 10:40 | EXECUTE | ERROR | **워커 지시 위반 — 상태 변경 도구 호출.** S-12-7 정정 워커에게 "상태 변경 도구 호출·커밋 금지"를 명시했으나 `state-tool mark --task-step execute.implement --done`을 호출해 **EXECUTE 행 12를 ✅로 조기 완료 처리**했다. 실제로는 G4(W-19~W-29)·G5(W-30~W-36) 18건이 남았다 | 되돌리기 시도 |
| 101 | 2026-09-15 10:40 | EXECUTE | DECISION | **되돌릴 수 없음을 확인하고 기록으로 보완한다.** `advance`는 `row_not_found`("row 12 is already done, advance only allows pending→in_progress")로 거부하고 `--force` 플래그가 없다. 단방향 설계는 감사 추적성 측면에서 의도된 것이라 우회하지 않는다. 실질 영향은 `next_action`이 "TEST 작업 진입"으로 잘못 표시되는 것뿐이며, **실제 진행 SSOT는 PLAN의 Work item 40건**이다. TEST 단계로 넘어가지 않고 G4(P9)를 계속한다 | 기록 보완 |
| 102 | 2026-09-15 10:40 | EXECUTE | IMPROVE | 프레임워크 개선 후보 — 워커가 `--as-worker --action-step <N/M>` 없이 최종 파이프라인 행을 done 처리할 수 있는 경로가 열려 있다. opd SKILL은 워커 mark 시 `--action-step`을 요구하지만 도구가 강제하지 않는다. CLOSE 회고 대상 | 이월 |
| 103 | 2026-09-15 12:46 | EXECUTE | GATE | W-11 재진입 Pass — enum 무증가 0줄 증명, sha256 4종 일치, 8스위트 76 passed. 범위 한정 문구가 "동결 시점 COMMANDS 일치는 **G2 시점 실측 사실이지 유지할 불변식이 아니다**"로 내 과잉 일반화 지적을 정확히 교정했다 | Pass |
| 104 | 2026-09-15 12:46 | EXECUTE | ESCALATION | **W-18 blocked — 상류 main 5커밋 선행(병렬 세션 충돌 2회차).** `feat(129) Ego Lite`·`fix(129) agentic 지속성`·`chore(134) 마감` 계열. `state_tool.py` 양방향(main +154 / 우리 +6), `test_state_tool.py`(main +47/-47 / 우리 +370) 충돌 확정 | 소유자 승인 후 병합 |
| 105 | 2026-09-15 12:46 | EXECUTE | GATE | main 병합 완료 — 충돌 1곳(`test_state_tool.py` 말미)뿐이고 **main 쪽이 비어 있어 손실 0**으로 해소. `state_tool.py`는 자동 병합돼 main `+142`와 우리 `+6`이 공존. `state-tool` 회귀 **460 passed·3 skipped·125 subtests**(병합 전 452 → main 신규 포함), `oppb` enum 2곳·P0~P5 전부 생존 | Pass |
| 106 | 2026-09-15 12:46 | EXECUTE | ERROR | **W-18이 `classify_writes` 구조적 false positive 3종 발견.** (1) 순수 이탈 — 자기 lease에 안 쓰고 lease 밖만 쓰면 `own_marker=None`이라 검출 0, 가장 전형적 위반이 무조건 통과 (2) 쓰기 순서 역전 (3) lease 밖 삭제 — `mtime 0 >= own_marker`가 항상 거짓이라 구조적으로 귀속 불가. 테스트가 GREEN인데도 결함이 남은 것은 W-17의 RED가 이 케이스를 커버하지 않았기 때문 | 처리 방향 판정 |
| 107 | 2026-09-15 12:46 | EXECUTE | ERROR | **PM 판단 오류 정정** — 내가 "제안서 `:700` baseline 봉인으로 교체"를 제안하고 소유자 승인까지 받았으나, 실측 결과 **틀렸다**. S-12①과 S-13①의 파일시스템 상태가 동일하고(양쪽 다 `src/orders/`·`src/users/` dirty) 차이는 쓰기 순서뿐이라 baseline으로도 구별되지 않는다. 제안서 `:700`은 **Git 전이(HEAD·index·reflog) 봉인**이지 worktree 파일 귀속이 아니며, 내가 두 문제를 혼동했다 | 범위 축소 재승인 |
| 108 | 2026-09-15 12:46 | EXECUTE | DECISION | 처리를 "baseline 교체"에서 **"버그 2건 수정 + 한계 1건 문서화"**로 축소(소유자 재승인). ①순수 이탈·③삭제는 명백한 버그라 고치고, ②순서 역전은 mtime 접근의 근본 한계로 현재 계약에서 관측 불가하므로 docstring·`TOOL-BOUNDARY.md`에 명시만 한다. 대안(Runner 자기 신고)은 §4.5 사후 탐지와 어긋나고, attempt별 격리 worktree는 제안서가 명시 거부(worktree 1개) | 확정 |
| 109 | 2026-09-15 13:35 | EXECUTE | GATE | W-14 보강(버그 2건) Pass — `11 passed`. 삭제 판정을 `mtime 0` 센티널에서 `None`(관측 불가)으로 바꾸고 foreign을 deleted/present 두 모집단으로 분리해 **존재→부재 전이 자체를 위반**으로 판정. RED 작성자가 "단순 임계값 조정으로는 안 된다"고 지목한 구조 변경을 정확히 수행 | Pass |
| 110 | 2026-09-15 13:35 | EXECUTE | ESCALATION | **상류 main 3회차 선행(태스크 133).** W-18 2차가 `git merge-tree --write-tree`로 **읽기 전용 프로브**를 먼저 돌려 충돌 0을 확인한 뒤 보고한 것이 좋았다 — 병합을 시도하지 않고 판정했다. PM이 재병합했고 실제로 충돌 0 | 재병합 완료 |
| 111 | 2026-09-15 13:35 | EXECUTE | ERROR | **W-18 2차가 기준 6의 잔여 구멍 발견** — `is_shared_knowledge`가 `attributed`를 거친 뒤에야 적용돼(`:483`), MEMORY/brain을 먼저 쓰고 자기 lease를 나중에 쓰면 순서 역전 한계와 함께 빠져나간다. `test_s12_3`이 lease→MEMORY 순서라 **우연히** 통과하고 있었다 | 수정 |
| 112 | 2026-09-15 13:35 | EXECUTE | DECISION | 워커가 "scope 밖"이라 고치지 않고 **해법까지 제시하며 보고**한 것을 채택 — 공유 지식은 Runner가 정당하게 쓰는 경우가 없으므로(제안서 `:219` 행동 계약 4번, §5 P5 지식 반영 1회) 귀속 판정 없이 dirty 존재만으로 거부하면 mtime 한계와 무관하게 닫힌다. lease 밖 **소스**는 S-13①이 타 Runner 정당 쓰기를 요구하므로 귀속 판정이 계속 필요하다 — 두 축을 분리한 것이 핵심 | 채택·수정 완료 |
| 113 | 2026-09-15 13:35 | EXECUTE | GATE | 공유 지식 축 수정 Pass — `12 passed`, 6건 공존(`s12_1`·`s12_1a`·`s12_1b`·`s12_3`·`s12_3a`·`s13_1`). `classify_writes` 맨 앞에서 `observed`를 shared/remaining으로 선분리하고 mtime 귀속은 소스에만 남겼다. 한계 문서 범위를 "lease 밖 **소스** 경로 한정"으로 축소 | Pass |
| 114 | 2026-09-15 13:35 | EXECUTE | ERROR | **PM 절차 오류 — 워커 실행 중 커밋.** W-14 워커가 "completed" 반환 후에도 백그라운드로 전체 스위트를 돌고 있었는데 내가 `a72cc47`을 커밋했다. 워커는 이를 "제3자 커밋"으로 관측했고, baseline 확인용 `git stash pop`이 `No stash entries found`로 실패했다. 내용 유실은 없음을 워커가 확인했다(커밋 트리에 변경 전부 존재, 3파일 stat 일치) | 절차 교정 |
| 115 | 2026-09-15 13:35 | EXECUTE | IMPROVE | 교정 규율 — **워커가 완료를 반환해도 후속 백그라운드 작업이 남아 있을 수 있으므로, 같은 파일 영역을 건드리는 커밋은 후속 알림까지 확인한 뒤 수행한다.** 특히 워커가 `git stash`를 쓰면 PM 커밋이 그 전제를 깨뜨린다(세션 지침도 bare stash를 금지한다). CLOSE 회고 대상 | 이월 |

## [116] G4 1파 디스패치 — W-19·W-20·W-21·W-22
- 유형: decision
- 상류 재확인(H-7): `git log --oneline main ^HEAD` = 0건, 충돌 없음
- 디스패치 4건 병렬, 파일 상호 배타: SKILL.md / pipeline.json / capability AGENT.md / project-slice SKILL.md
- 각 프롬프트에 receipt 블록(manifest sha256 `14d5d62f…`, 문서 4종), RED 계약 SSOT(`test_product_flow.py`), 동결 스키마 금지(H-3 blocker 보고), 재사용 강제(`controller.compute_scope_hash`, oppl import 0), 금지사항(배포 소스·state-tool·커밋·bare stash·플랫폼 분기) 포함
- 2파 예정: W-23·W-25·W-27 / 3파: W-24·W-26 (`oppb_runtime_tool.py` 공유)

## [117] W-20·W-21 완료 — 접합부 미결 1건 등록
- W-20: `pipeline.json` 22행, gate 6개(5·10·13·17·19·21), pipeline RED 3건 GREEN. 보정 2건은 `state_tool.py:1343,1349` 스키마 강제로 독립 검증됨 — PLAN §Appendix A에 각주 추가
- W-21: `opal-capability-agent/AGENT.md` 210행, §4.3 입력4·출력5·행동계약6 전 항목 매핑. `worker.dispatch` 대신 execution-packet·lease receipt 진입 게이트 5항(§4.1 headless attempt 경로라 events.json에 oppb 선언 없음)
- **미결 O-1 (blocker 아님)**: 동결 `oppb-state.schema.json`의 `attempt_result`는 `additionalProperties: false`이고 `changes`/`proof`/`knowledge` 필드가 없다(독립 확인). capability agent 출력 5종 중 3종의 영속 경로가 미정. W-21은 "stdout 구조화 JSON 반환, run root 직접 쓰기 없음"으로 회피. **3파 W-24(Verifier evidence adapter)에 접합 판정을 위임**하고, 스키마 변경이 불가피하면 H-3 blocker로 승격

## [118] W-22 완료 — 미결 O-2 등록, 7축/4축 관계 재확인
- W-22: `op-oppb-project-slice/SKILL.md` 245행. 슬라이싱 기준·수평 레이어 금지·sibling 5조건·구조화 출력 3종 반영
- 7축/4축 정합 독립 확인: `lease.OWNERSHIP_AXES`(7)는 판정 축, `controller.LEASE_AXES`(4)는 기계 발급 축이고 나머지는 `unrepresented_global_outputs`로 회수된다 — G2 설계대로이며 모순 아님
- **미결 O-2 (blocker 아님)**: 동결 스키마 `mini_task`(`additionalProperties: false`)와 `contract`(lease·run_command·verify_command·executors만)에 `business_rules`·`acceptance_cluster`·`parallel_eligible`·`preimage_scope`·`runner_profile` 슬롯이 없음(독립 확인). W-22는 acceptance cluster를 `acceptance[].{id,contributing_tasks}`로, 나머지를 `PROJECT-DESIGN.md`로 라우팅해 회피
- O-1·O-2는 같은 계열이다 — 동결 G2 state schema는 **런타임 실행 스키마**이고 설계 근거 필드를 담지 않는다. W-29(G4 체크포인트)에서 두 건을 함께 판정한다

## [119] W-19 완료 — **에스컬레이션 E-5: `project-run` 미소유 발견**
- W-19: `opal-pilot-project-build/SKILL.md` 533행. `test_oppb_entry_point_files_exist` 포함 4 passed
- **차단 발견**: `test_product_flow.py` 12건이 전부 module fixture `_completed_run`에서 error. 원인 동일 — `oppb-runtime-tool project-run` 서브명령 부재(`COMMANDS`에 없음, 실측 `oppb_runtime_tool.py:149`)
- fixture는 `project-run --run-root`가 P0~CLOSE를 무인 완주시키고 `project_state == "closed"`를 반환할 것을 요구한다. **PLAN의 어느 Work item도 이 드라이버를 소유하지 않는다** — W-28(RED 작성)이 계약으로 가정만 했다
- 부수 발견: fixture의 `workgraph["tasks"]`는 실제 스키마·Controller의 `mini_tasks`와 키 이름이 불일치(독립 확인 — schema `workgraph.properties`에 `mini_tasks`만 존재)
- RED-first §1.5-5에 따라 기대를 약화·삭제할 수 없다. 소유자 판단 필요 → 사용자 에스컬레이션

## [120] W-25 완료 — additive 증명 통과
- `op-scenario-gate/SKILL.md` +80/-0. `git diff -U0 | grep -c '^-[^-]'` = 0, hunk 2개 모두 `-x,0` 순수 삽입 → 기존 OPPD 분기 바이트 무변경 성립
- 신규 §5는 `pilot: oppb`에서만 진입, 기존 절은 이 절을 읽지 않음
- 워커가 제기한 `schema_version` 타입 불일치(evidence=int 1, workgraph/acceptance=문자열 "1.0")는 **동결 스키마 양쪽에 의도적 사실로 이미 명기돼 있음**(독립 확인) — 결함 아님

## [121] W-23 완료 + PM 보정 1건 — phase enum 인라인 추가
- W-23: `opal-evaluator-agent/AGENT.md` +51/-0. HEAD 원본 189행이 신본 240행에 순서대로 바이트 동일 보존(미보존 0행), 4분기 키워드 보존 3/3·3/3·3/3·14/14
- 워커는 "바이트 무변경" 제약을 우선해 phase 열거 행을 **수정하지 않고** 아래에 `[MUST]` 블록으로 additive 선언했다
- **PM 판정**: PLAN 원문은 "§입력명세 phase 열거값에 5번째 값 `acceptance`를 추가"를 명시했고, 바이트 무변경 제약의 대상은 **4개 분기의 서술**이지 열거 행이 아니다. 열거 행이 계약 표면이므로 미갱신은 실질적 결함이다
- PM이 직접 보정: `:32` 행 끝에 `/ \`acceptance\`(...)` **추가만** 수행. 기존 4개 값 문자열 4/4 부분문자열로 보존, 4분기 절은 무변경. 결과 `+52/-1`이며 유일한 삭제행은 이 열거 행 자체다

## [122] W-27 완료 — 미결 O-3 등록, G4 1·2파 종료
- W-27: `op-oppb-knowledge-finalize/SKILL.md` 289행. `brain-tool`·`memory-tool` 실측 CLI 7항 대조, 발명 옵션 0
- 실측 확정 3건: (a) 두 도구에 `batch` 서브명령은 없다 — "프로젝트 batch"는 정해진 순서를 프로젝트당 1회 통과하는 단일 pass로 정의, (b) 쓰기 대상은 허브(allocator root) — `brain_tool.require_write_root`가 worktree cwd 파생 쓰기를 거부하고 `memory_tool._is_worktree_target`이 deferred 요청으로 우회시킨다(pipeline id 18 pre-finalize guard의 "worktree MEMORY/brain diff 0"과 정합), (c) 본문 경로는 `<allocator_root>/.opal/memory/<slug>.md`
- `op-brain-ingest` 미호출 근거: 그 스킬은 태스크 `DONE.md/PLAN.md/TASK.md`를 입력으로 받는데 OPPB 미니 태스크는 §7.3상 그 문서를 만들지 않는다. `opal-improve`는 기록 대상이 프레임워크·로컬 PM 개선이라 거처가 다르다. 둘 다 무변경(C-2)
- **미결 O-3**: 동결 `oppb-event.schema.json`은 `required: ["ts","event"]` + `event_name` 5종 폐쇄 enum인데, RED 테스트는 `e["type"]`(`knowledge.batch_started`/`knowledge.batch_applied`/`project.hub_merged`)과 `e["stage"]`를 읽는다. 다만 **`additionalProperties: true`임을 독립 확인** — 스키마는 "Supervisor 단일 writer"이자 "런타임 검증기가 아님"을 본문에 선언하므로 P5 Product Flow 라인을 범위 밖으로 해석하면 H-3 위반 없이 해소 가능
- **O-1·O-2·O-3·E-5는 같은 뿌리다** — W-28의 RED 계약이 `project-run` 드라이버와 그 이벤트 로그라는 런타임 표면을 가정했는데 G2 동결 스키마가 그것을 모델링하지 않았다. E-5 결정과 함께 일괄 판정한다
- G4 진척: W-19·W-20·W-21·W-22·W-23·W-25·W-27 = 7/9 완료. 잔여 W-24·W-26(3파, E-5 결정 대기)

## [123] 소유자 승인 — E-5 해소안 4갈래 전부 승인
- **근본 원인 확정**: `project-run`은 CLI 서브명령이 아니라 제안서 `:278`의 명사구("프로젝트 런의 pre-finalize guard")였다. W-28이 이를 서브명령으로 오독해 존재하지 않는 단일 진입점을 계약으로 가정했다
- 그 명사구가 가리킨 실물은 **이미 구현돼 있다** — `checkpoint.py:875 pre_finalize_check`, `SUBCOMMANDS`에 `pre-finalize` 포함, `test_checkpoint.py` 12 passed
- P0~P5 소유자 지도 실측 결과 빈칸 0 — 대화형 세션(P0~P2·P5) + `start` 1회(P3~P4, Supervisor가 `_admit_verifier`로 P4까지 스케줄) + CLI 서브명령. `project-run`은 **만들지 않는다**(만들면 P0~P2 "무인 보장 대상 아님"과 P5 merge 게이트 `--auto-pass` 거부를 위반)
- 12건 재분류: A 테스트 버그 6 / B 스키마 필드 누락 3 / C 검증 계층 오배치 4
- 승인 결과: W-41(동결 스키마 additive 확장, H-3) + W-42(fixture 재작성·4건 W-34 이관) 신규 등재. PLAN Work items에 추가
- **merge 조건 변경 기록**: G4 merge 시점에 AC-2·AC-15의 실증 근거는 없다. 실증 소유자가 W-28 → W-34(G5 실주행)로 이동했다. 소유자가 이 사실을 인지하고 승인했다

## [124] PM 오류 — receipt 파일 경로 누락으로 W-42 blocked (3회째 재발)
- W-42 워커가 `worker.dispatch` 진입 게이트에서 blocked 반환. **정당한 거부다**
- 원인: PM이 프롬프트에 receipt의 **인라인 요약**(event/manifest_sha256/문서 4종)만 넣고 `event-verify --receipt`가 요구하는 **실제 파일 경로**를 주지 않았다. 워커가 `/private/tmp` 전역 검색으로 receipt 부재를 확인한 뒤 어떤 문서도 읽지 않고 반환했다
- 전역 메모리에 "디스패치 receipt 블록 필수 (2회 재발)"이 이미 있었고 이번이 **3회째**다. 요약만으로 충족된다고 오해한 것이 반복 원인
- 조치: 디스패치 전용 receipt를 새로 발급(`scratchpad/wdr-w42.json`)하고 `state-tool event-verify`로 선검증(`ok: true`, `verified_document_count: 4`) 후 경로를 명시해 재디스패치
- **교정 규율**: 워커 프롬프트의 receipt 블록은 반드시 (a) receipt **파일 절대경로**, (b) 워커가 직접 실행할 `event-verify` 명령 전문, (c) PM 선검증 결과 3요소를 포함한다. 인라인 요약만으로는 게이트를 통과할 수 없다. CLOSE 회고 대상

## [125] W-41 완료 — 동결 스키마 additive 확장, PM 독립 검증 통과
- 추가 2필드 확인: `properties.execution_contract`(string, minLength 1), `$defs.mini_task.properties.profile`(enum fast/full). **둘 다 optional** — top `required` 7종·mini_task `required` 9종 무변경
- 워커 증명: 전 노드 546개 경로 평탄화 대조에서 경로 삭제 0, 기존 dict 키집합 부분집합 보존, enum 값 16→18(기존 16 전수 생존·순서 불변), required 블록 16/16
- **scope hash 불변 PM 독립 확인**: `controller.py` diff에서 `SCOPE_HASH_DOMAIN`·`LEASE_AXES`·`compute_scope_hash`·`normalize_lease` 관련 변경 **0줄**. 워커 실측도 lease 5종에서 확장 전후 동일 해시(`363320d0…37b5c`)
- sha256 PM 재계산 대조 일치: state `7fa09f9c…`(변경), event `8a78a0c7…`·command `f3fab919…`·evidence `2bc84ff5…`(무변경 3종)
- 회귀: 83 passed. 실패 7(W-26 소유)·error 12(W-42 소유)는 확장 전 baseline과 **동일 수치** — 증가 0
- `oppb-command.schema.json`의 `workgraph_spec`이 `additionalProperties: true`라 command 스키마는 손댈 필요가 없었다(동결 3종 무변경)

## [126] W-24 완료 — 미결 O-1 해소(스키마 변경 0)
- `verifier_adapter.py` 588행 + `test_verifier_adapter.py` 425행(RED 선작성 17/17 → GREEN 17/17). `oppb_runtime_tool.py`에 `verifier` 서브명령 추가
- PM 독립 확인: `oppb_runtime_tool.py` diff의 유일한 삭제행은 @header depends 배열 **마지막 원소 뒤 콤마 추가**뿐 — 실질 순수 추가. `controller.py`·`schema/` 변경분은 전부 W-41 소유이며 W-24는 무접촉
- **O-1 해소**: `oppb-evidence.schema.json`은 최상위 `additionalProperties: true`(PM 재확인)이고 `evidence._validate_schema`는 필수 8필드만 검사한다. capability agent의 `changes`/`proof`/`knowledge`는 `attempt_result`가 아니라 **evidence 문서의 `runner_result` 객체**에 안착한다 — **동결 스키마 0바이트 변경**. W-21의 "구조화 stdout만 반환"과 충돌 없음(Runner는 여전히 run root 미기록, Verifier 경로가 받아 귀속)
- 증거 독립성 2중 방어: 기본 attempt id를 `<task>-verifier-<kind>-<uuid4[:8]>`로 신규 발급해 runner 규약과 충돌 불가. 명시 `--attempt`가 `runner_attempt_id`와 같으면 **문서 생성 단계에서** 거부해 evidence.py 4번 검사에 도달조차 않음(색인 0건까지 테스트로 확인)
- 조건부 호출 판정: `accept`+위험신호 → `risk_accept` 승격, 계약폐쇄는 같은 contract를 선언한 peer≥1이고 자신+전 peer가 `POST_RUN_STATES`일 때만. 위험신호는 `lease.runtime_resources` 비어있지 않음이라는 **workgraph 사실**에서만 파생하고 코드 내용 추론 0
- 부작용 1건 기록: `verifier plan`이 `<run_root>/verify/<task_id>`를 선생성한다(gc 스킬 `output_dir` 계약용). run root 내부이고 `init`이 `.opal-runs/`를 `.git/info/exclude`에 등록하므로 Git 추적 밖 — 유지 판정

## [127] W-42 완료 — 실주행이 타 파일 진짜 버그 2건을 노출
- `test_product_flow.py` +242/-101. fixture 재작성 완료: `init` → INTENT·spec seed → `workgraph load` → `start`(Supervisor가 P3 Runner → P4 Verifier/acceptance 무인 수행, `status` 폴링) → `checkpoint pre-finalize`. 미니 태스크 2건(fast/full, 실제 run_command·verify_command) 실동작
- 결과 12노드 중 **11 PASS**(mock 0, 실행 2회 동일). W-41의 `execution_contract`·`profile`이 이미 워크트리에 있어 (C) 항목은 첫 시도에 통과
- 4건 W-34 이관 기록: 모듈 헤더 `migration_note` + 섹션 주석에 목적지(W-34, G5 cold×9/warm×9 실주행)·이관 수용기준·pytest 불가 사유(대화형 세션 행동 관측 필요, P0~P2 수동 seed 시 항진명제화)를 "삭제가 아닌 검증 계층 이동"으로 명시
- **버그 A (수정 착수)**: `checkpoint.py:859 _unprocessed_results`가 `document.get("tasks")`를 읽는다 — 실제 키는 `mini_tasks`. terminal이 항상 공집합이라 정상 accept 후에도 `pre-finalize`가 **언제나** `PRE_FINALIZE_BLOCKED`. pipeline id 18 P5 guard가 사실상 상시 차단 상태였다. W-43으로 등재·디스패치(RED 선작성 조건)
- **버그 B (에스컬레이션)**: `test_fast_mini_task_artifacts_are_packet_result_evidence_only` 1건 RED. `supervisor.py launch()`가 profile과 무관하게 `attempt-spec.json`·`attempt-runner.log`·`attempt.attempt.json`·`capability.out`·`capability.err`를 쓴다. 테스트의 `ALLOWED_ATTEMPT_FILES = {"execution-packet.json","result.json"}`가 이를 위반으로 본다
- **버그 B는 AC-8과 AC-11의 정면 충돌이다(PM 실측)**: `reconcile-attempts`는 `*.attempt.json`을 읽고 `supervisor.py:443`은 그 **부재를 고아 판정 근거**로 쓴다. 테스트 해석대로 파일을 없애면 이미 GREEN인 AC-11(비정상 종료 복구)이 깨진다. 한편 제안서 §7은 제목이 "미니 태스크 **문서**"이고 §7.1 상시 생성 표는 문서 SSOT 4종이며, §7.3 금지 목록도 TASK/DONE/ANALYSIS/PLAN/QA/CLOSE **문서**다 — 런타임 부기 파일은 대상이 아니다
- 소유자 판단 요청 중

## [128] W-43·W-26 완료 — 미결 O-4(workgraph.json 이중 계약) 등록
- **W-43**: `checkpoint.py:859` `document.get("tasks")` → `mini_tasks`, 식별자 `task_id` 폴백 제거(실측상 `id` 단일). RED 선확인 원문 확보(`unprocessed_results: ['attempts/T01/a1/result.json', ...]`) 후 GREEN. `test_checkpoint.py` 12→14 passed. 대조군 테스트(비종료 태스크는 여전히 차단)를 함께 추가해 가드 무력화가 아님을 잠갔다
- 워커가 자기 변경 무관함을 실측 증명: 스크래치패드 복사본에서 `checkpoint.py`만 HEAD 원본으로 되돌려 잔여 실패 1건이 동일 재현됨을 확인
- 같은 키 버그 전수 조사 잔여 0건. `controller.py:536`의 `raw.get("tasks", [])`는 사용자 제출 acceptance spec의 별칭 폴백이라 무관
- **W-26**: `revalidation.py` 486행, `test_revalidation.py` 7/7 통과. 전이적 폐쇄를 계산하지 않아 2-hop이 구조적으로 불가능하고, `REVALIDATABLE_STATES=("accepted",)`로 미실행 태스크를 배제. 자동 재귀를 넣지 않은 것이 "Repair가 출력 계약을 다시 바꾼 경우에만 전파"를 만족시키는 유일한 정직한 구현 — 전파는 명시적 재호출로만 1-hop씩 나아간다
- W-24 로직 재사용은 근거 있게 거부: `closed_contracts`는 방향 없는 lease `contracts` 축 기반이라 producer까지 끌려들어와 테스트 2를 깬다. 대신 `controller.workgraph_transaction`·`attempt_dir`·`_atomic_write_json`을 재사용해 락·원자쓰기·revision 규율은 재구현 0
- **미결 O-4 (PM 독립 확인 완료)**: `<run_root>/workgraph.json` 한 경로에 **호환되지 않는 두 문서 계약**이 걸려 있다. 동결 스키마·Controller·W-24·`test_product_flow.py`는 `mini_tasks[]`(상태 8종)를 쓰고, `test_revalidation.py`(:180-257)는 `{"contracts":[...], "tasks":[...]}`에 `consumes_contracts`/`produces_contract`와 재검증 상태 어휘를 쓴다. 실주행에서는 `workgraph load`가 `mini_tasks`를 쓰므로 **AC-12 경로가 실제로는 동작하지 않는다**
- W-26은 잘못된 shape에 `revalidation_graph_invalid`를 던져 조용한 오독은 막았다. `api-freeze.md` §3이 "스키마가 구현보다 좁은 상태는 의도된 것"을 허용하므로 동결 위반은 아니다
- O-4 해소 방향(재검증 그래프를 별도 run root 문서로 분리 vs 동결 스키마에 흡수)은 소유자 판단 — W-29 안건

## [129] W-44 완료 — 재검증 그래프 흡수, profile enum 정정
- 스키마 +74/-4, controller +99/-3. workgraph 최상위 `contracts[]`, `mini_task`에 `consumes_contracts`·`produces_contract`·`acceptance_scenarios`·`contract_tests`, `task_state` 8→10(`needs_revalidation`·`repair` 추가, 기존 8종 보존)
- 기계 증명 5항목: 노드 557→643 삭제 0 / dict 186개 키집합 위반 0 / enum 소실은 `profile`의 `"full"` 1건뿐(승인된 정정) / required 16블록 축소 0·증가 0 / scalar 334개 중 변경 3건 전부 profile 정정분
- 워커가 `task_state.description` 보강을 시도했다가 제약 위반으로 **스스로 원문 복구**했다 — 신규 상태 설명은 `api-freeze.md` §9로 이동. 절제 판단으로 기록
- scope hash 불변: lease 5종 전부 확장 전후 동일. 같은 lease에 profile·재검증 4필드를 채워도 `fb5b732f…70bb6` 고정
- `profile` 정정 근거: 제안서 §8은 Fast/Standard/Critical 3종이고 `"full"`은 문서 어디에도 없다. `git show HEAD:...schema.json`에 `"profile"` 0건이므로 원 동결본 기준 순수 추가 — 동결 위반 아님. `TASK_PROFILES`·`DEFAULT_TASK_PROFILE`도 `full`→`standard`로 정합
- 재동결 #4: state `c0532009…`(변경), 나머지 3종 무변경. `jsonschema`로 draft-07 유효성·신규필드 문서 통과·**신규필드 0개 동결당시 문서 통과(하위호환)**·음성사례 `profile:"full"` 거부 4종 확인
- 회귀 `109 passed, 8 errors` — 8건 전부 `test_product_flow.py:398`의 `"profile": "full"` 단일 원인(`workgraph load`가 `spec_invalid` 거부). W-45 소유라 미접촉
- **상류 4번째 선행(H-7)**: `main ^HEAD` 7건(태스크 123 계열). 우리 변경 파일과 교집합 **0**, `git merge-tree --write-tree` 탐침 **conflict 없음**

## [130] W-45 완료 — 8 errors 해소, 네 번째 어휘 발산 판정
- `test_product_flow.py` `:398` `"full"` → `"standard"` 1줄로 **8 errors → 0**. 현재 11 passed / 1 failed(판단 대기 중인 별건)
- `test_revalidation.py` seed를 `{"contracts", "mini_tasks"}` 동결 shape로 재작성. 각 record가 동결 `mini_task` required 9종을 충족하고 재검증 4필드를 W-44 정의 위치에 담는다. `scope_hash`는 stdlib hashlib 더미(`sha256_hex` 패턴만 충족, 내부 API import 0 — H-6 준수)
- **단언 강도 무변경 증명**: 7개 테스트 함수 본문이 HEAD 대비 **바이트 동일**, assert 행 diff 0. 변경은 모듈 헤더·seed 빌더·`_states()`의 키 1줄뿐
- 워커가 W-43의 `checkpoint.py` 수정을 실측 확인한 뒤 stale 주석을 현행화하고, `checkpoint pre-finalize` 호출을 **관측용에서 단언으로 승격**했다(`ok`·`finalize_allowed` 둘 다 true). 승격 후 재실행해도 1 failed/11 passed 유지 — P5 guard가 이제 회귀로 잠겼다
- **네 번째 발산 판정**: `revalidation.py`의 지역 `TASK_STATES`에 `queued`가 있는데 동결 enum 10종에는 없다. **PM 판정 — 동결 enum이 단일 SSOT다.** 제안서 §9.1의 `queued`는 추상 상태기계 어휘이고 구현의 `pending`/`ready`는 정당한 세분이다(`candidate_ready`·`failed`도 같은 정련). W-46이 지역 재선언을 제거하고, W-45에게 seed `queued`→`pending` 1건을 후속 지시
- `REVALIDATABLE_STATES=("accepted",)` 유지로 "미실행 태스크 재검증 0" 단언은 그대로 성립
- 발산 4건 전부 같은 뿌리 — W-28이 RED를 쓸 때 구현·스키마를 참조하지 않고 자기 어휘를 만들었다. CLOSE 회고 대상

## [131] W-46 완료 — **O-4 완전 해소**
- `revalidation.py`가 `document["mini_tasks"]`를 읽는다(:147). 오류 메시지·`revalidation_graph_invalid` 설명도 새 키로 현행화
- 지역 `TASK_STATES` 튜플 **완전 삭제**, `controller.TASK_STATES` 직접 참조(:159,:163). PM 독립 확인 — 파일에 지역 재선언 0
- 재선언 제거 근거 3종(워커 실측): 이미 `import controller` 중이라 추가 결합 0 / 외부에서 `revalidation.TASK_STATES`를 읽는 코드 0건(전수 grep) / `supervisor.py:60`이 같은 패턴("상태 어휘는 controller.TASK_STATES가 SSOT")을 이미 쓴다
- (C) 4항목 무변경 근거 확인: `direct_consumers`·`revalidation_scope` 본문 바이트 무변경, `"propagated": []` 유지, 자기 호출 0, `workgraph_transaction` 2회·`attempt_dir` 2회·`_atomic_write_json` 1회 호출 지점 무변경
- `test_revalidation.py` **7/7 GREEN**. 전체 회귀 `1 failed, 116 passed`
- **O-4 해소 완료**: W-44(스키마 흡수) → W-45(테스트 shape) → W-46(구현 정합) 3단으로 `workgraph.json` 단일 계약 성립. AC-12 경로가 실주행 shape에서 동작한다
- 잔여 판단 1건: 버그 B(`ALLOWED_ATTEMPT_FILES` vs AC-11 복구 계약). merge 전 마지막 결정

## [132] W-45 후속 완료 — 상태 어휘 정합 마무리
- seed `queued` → `pending`. `TERMINAL_STATES`도 §9.1 7종 집합에서 동결 10종 enum으로 교체. 모듈 헤더에 "동결 enum이 단일 SSOT, `queued`는 §9.1 추상 어휘를 `pending`/`ready`로 정련한 것" 판정 근거 기록
- 도구 트리 전체에 `"queued"` 리터럴 **잔여 0**(PM 확인)
- 7건 본문 중 2줄만 변경 — `assert states[TASK_QUEUED] == "queued"` → `"pending"`. 상태 리터럴 자체가 바뀌었으므로 불가피한 추종이며 **의미는 동일**(미실행 태스크는 `REVALIDATABLE_STATES=("accepted",)` 밖이라 배제). assert 행 전수 diff로 그 외 무변경 확인
- 워커가 공유 워크트리에서 W-46의 동시 착지를 관측하고 정직하게 보고 — `revalidation.py` 미접촉을 `git status`로 확인. 두 워커의 산출이 독립적으로 맞물려 7/7 GREEN이 된 것이 seed의 구조·의미 정합성을 사후 입증

## [133] W-47 완료 — 117 passed, 0 failed
- `ALLOWED_ATTEMPT_FILES`를 `_DOCUMENT_ATTEMPT_FILES`(§7.1 SSOT 2종) ∪ `_RUNTIME_BOOKKEEPING_FILES`(5종)로 분리·확장. 각 파일의 계약 출처를 주석으로 고정 — `supervisor.py:48,50-53`, `recovery.py:59`, `opal_agent.py`의 `<stem>.attempt.json` 규약. 내부 API import 0(H-6)
- **단언 이빨 유지 확인**: `.md` 문서 0건 게이트와 허용 목록 초과 게이트를 추가하고, 워커가 `DESIGN.md`·`unexpected-rogue-file.bin`을 실제 주입해 각각 실패함을 확인한 뒤 제거했다. 무조건 통과 테스트가 아님

## [134] W-29 G4 체크포인트 — merge 가능 판정
- **oppb 회귀 117 passed, 0 failed** (2회 재현 동일)
- **공용 자산 회귀 `5 failed, 1305 passed, 3 skipped, 295 subtests`**
- 5건은 전부 `tool-scan/tests/test_tool_scan.py`이며 **상류 선재 결함으로 확정**: `git archive main`을 스크래치패드에 풀어 동일 테스트 실행 → **동일한 5건이 동일하게 실패**(`test_manifest_entries`·`test_agentmd_cmux_routing`·`test_agentmd_usage_discipline`·`test_drift_entries`·`test_registry_parity`). 실패 내용도 동일(`harness §9 표에서 7도구 행 미확인. found={'state'}`). 태스크 132와 무관
- **C-7 검증**: 기존 파일 삭제 0건(`--diff-filter=D` 공집합), 레지스트리 2종 diff 0(W-30/G5 소유라 정상), 기존 자산 수정 2건 모두 additive — `opal-evaluator-agent/AGENT.md` +52/-1(유일 삭제행은 PM이 값을 덧붙인 phase 열거 행), `op-scenario-gate/SKILL.md` +80/-0
- **상류 5번째 확인**: `main ^HEAD` 7건, 우리 변경 파일과 교집합 0, `git merge-tree --write-tree` conflict 없음
- 산출: 신규 7(capability agent·oppb 파일럿 스킬+pipeline.json·project-slice·knowledge-finalize·verifier_adapter·revalidation·test_verifier_adapter), 수정 10
- **판정: merge 가능.** 소유자 승인 요청

## [135] G4 허브 merge 완료 (소유자 승인)
- 커밋 `186fb1c` — 20 files, +4112/-174
- main 병합 `89a86d7` — 태스크 123 계열 7건 흡수, 충돌 0. 병합으로 `workstudio/`가 사라졌으나 main의 `eeaedb1 chore: WorkStudio 폐기` 소유이며 태스크 132와 무관(확인)
- 병합 후 회귀 재확인: oppb **117 passed 0 failed**, 공용(state-tool·opal-agent) **599 passed 3 skipped 187 subtests, 실패 0**
- `feat/OP-TASK-132` → `main` **fast-forward merge 완료**. main HEAD = `89a86d7`
- 반영 검증: 신규 7자산 전부 `git cat-file -e HEAD:` OK. 양방향 미병합 커밋 0/0
- 다음: G5(W-30~W-36). **W-34는 실주행 18회라 PLAN상 실행 전 시간·모델 비용 보고와 소유자 승인이 필요하다** — G5 진입 시 견적 제시

## [136] W-34 범위 정정 — 「18회 전부 무인」은 E-5와 같은 허구였다
- 소유자 질문("W-34는 실재 스킬로 돌려서 테스트를 하는 건가?")을 계기로 제안서 §13을 재검토해 발견
- 제안서 `:898` 원문: "총 18회이며 **전부 무인 headless 실행이므로 사람이 세션을 운용하는 구간이 없다**"
- **이는 `project-run`과 동일한 가정이다** — §4.1은 P0~P2를 "대화형 Product Flow가 호출하는 bounded planning, 무인 실행 보장의 대상이 아니다"로 정하고, `p5.user_merge_gate`는 `--auto-pass`를 거부한다. 명세대로는 18회를 무인으로 돌릴 방법이 없다
- 정정: **측정 구간을 P3~P4로 한정.** fixture당 P0~P2 산출물(`INTENT.md`·workgraph spec·봉인 profile)을 한 번 확정해 고정하고, 18회는 그 고정 입력에서 `start` 1회로 무인 반복. §13 차단 지표가 실제로 정한 것은 「**사용자 게이트 사이** 무인 실행」이며 병렬 안전성·lease 비충돌·cache 정확성이 전부 이 구간에서 발생하므로 측정 목적은 온전
- 제안서 §13 본문과 PLAN W-34 행 양쪽 정정. P0~P2 planning 벽시계는 관찰 지표에서 제외
- E-5(`project-run`)와 같은 뿌리의 **다섯 번째 발산**이다 — 설계 문서 자체가 "전체 무인 완주" 서술을 한 곳 더 갖고 있었다

## [137] W-33 완료 — 설치 배선, `references/` 배포 실증
- `scripts/install-mac.sh` +8/-0. `oppl-runtime-tool` 블록 직후에 동일 4요소 패턴(주석 라벨+태스크번호 / `local <name>_run=` / `[[ -f ]]` 가드 / `chmod +x`+`success`)으로 삽입
- **핵심 확인 — `references/pipeline.json` 배포**: 워커가 스크립트의 스킬·에이전트 루프와 `install_dir`·`strip_deploy_md_recursive` 본문을 그대로 추출해 **샌드박스 디렉토리로 실행**(`~/.opal/` 미접촉)했다. 결과 4종 전부 배포되고 `pipeline.json`은 원본과 byte-identical·JSON 파싱 정상. `install_dir`이 `cp -r`/`cp -Rf` 재귀이고 화이트리스트·확장자 필터가 없으며 `strip_deploy_md_recursive`는 `-name "*.md"` 한정이라 `.json`을 건드리지 않는다. **`//oppb` 기동 자산이 기존 루프로 전부 배포된다 — 추가 분기 불필요**
- `oppb-runtime-tool/run.sh` 실측: `-rwxr-xr-x` 529B, oppl 래퍼 패턴 복제, 소스 플랫폼 분기 0 → C-4·C-5 충족
- `bash -n` 통과. 관련 테스트: `test_oppb_init` 18 passed, `test_agent_adapter_fields` 18/0, `test_version_stamp` 11/0
- `test-install-skill-cleanup.sh` FAIL 1건은 **선재 결함 확정** — 워커가 `git show HEAD:scripts/install-mac.sh`로 원본 복원 후 동일 실패 재현(구 `opal-pilot-dev-short` 정리 로직, OPPB 무관). 원본 즉시 복구, numstat 8/0 유지

## [138] W-31·W-32 완료
- **W-31**: 4파일 순수 삽입 — `README.md` +26/-0, `ARCHITECTURE.md` +7/-0, `PROJECT.md` +4/-0, `CONVENTIONS.md` +1/-0. 기존 OPPD·OPPL·OPSDD 서술 무변경
- Pilot 선택 기준에 실행 주체 분할을 정확히 명시: "무인 실행이 보장되는 구간은 P3~P4뿐이며, P0~P2와 P5는 대화형 세션이 몰고 간다 — P5 merge 게이트는 `--auto-pass`를 거부하고 소유자 발화를 요구한다". G4에서 걷어낸 "전체 무인 완주" 오해가 문서에 새로 심기지 않았다. 워커가 근거를 전부 `path:line`으로 제시
- PM 후속 지시 1건: 트리 헤더 개수 표기가 실물과 어긋난다(문서 스킬 44·에이전트 15·도구 22 vs 실제 디렉토리 47/16/25). 그 항목에 한해 삭제행 0 제약 해제. 문서 자체 분류로 재계수하고 **선재 drift와 태스크 132 증가분(스킬 3·에이전트 1)을 구분해 보고**하도록 지시
- **W-32**: `actor.md` +1/-1. 총 행수 103→103 불변, 차이 행 1개, 그 행에서 제거된 문자는 닫는 `).` 2자뿐이고 신규 행이 구 행을 접두사로 포함(`b.startswith(a[:-2])`) — 목록 말미 삽입 1건 외 삭제·수정 0. 지원 표·`[MUST]` 통보 조항·2중 게이트 서술 전부 바이트 무변경
- `actor.md` 직접 검사 테스트는 0건이나 `events.json`이 참조하므로 event-loader+state-tool 스위트 실행: **525 passed, 3 skipped, 201 subtests, 실패 0**

## [139] W-31 후속 완료 — 개수 표기 갱신, 선재 drift 4건 분리 보고
- 최종 numstat: `README.md` +26/-0, `ARCHITECTURE.md` +17/-9, `CONVENTIONS.md` +4/-3, `PROJECT.md` +6/-2. 변경 14행 전부 개수 숫자와 그 숫자를 성립시키는 인벤토리 나열
- PM 독립 확인: 독립 스킬(루트 `skills/`) 8, OPAL 스킬 47, 에이전트 16, 도구 디렉토리 25 — 워커 수치와 일치
- 내역 합 검증 통과: 에이전트 전문 9 + 범용 7 = 16, PROJECT.md Dev 11 + 나머지 5 = 16, CONVENTIONS 이름 나열 16개, 도구 6 + 19 = 25
- 모호 판단 2건을 워커가 명시: (a) `opal-capability-agent`를 전문 에이전트로 귀속(ARCHITECTURE 전문 표 등재 근거), (b) 도구 총수에서 `check-env.js`·`requirements.txt` 2파일 제외(문서의 "디렉토리 기준" 문구 근거)
- **선재 drift 4건 분리 보고(태스크 132 이전부터 존재)**:
  1. ARCHITECTURE의 CLI 도구 수가 oppb 추가 이전에 이미 2 뒤처져 있었다(22 vs 실제 24, CONVENTIONS는 24로 정확). 순수 증분만 반영하면 23이라 여전히 틀리므로 **실측값 25를 택해 drift가 함께 해소됐다** — PM 승인: 알면서 틀린 숫자를 쓰는 것이 더 나쁘다
  2. CONVENTIONS alias 표에 `osw`(`opal-skill-wizard`) 행 누락 — 개수가 아니라 행 누락이라 미접촉
  3. ARCHITECTURE의 `references/` 엔트리 표기 부정확(문서 21엔트리·harness 23파일 vs 실측 20엔트리·harness 27파일) — 개수 해제 범위 밖이라 미접촉
  4. 트리의 `opal-pilot-dev/` 행 중복 2행 — 미접촉
- 2·3·4는 OPPB와 무관한 선재 결함이므로 **태스크 132 범위에 넣지 않는다.** 소유자 판단 대상으로 기록
- 워커 보고의 "레지스트리 alias 31→32"는 PM이 단순 계수로 재현하지 못했다(레지스트리가 `groups` 중첩 구조, `"alias"` 필드 출현 55). W-30 보고로 확정한다

## [140] W-30 완료 — 레지스트리 등재, `//oppb` 라우팅 성립
- `agents.md` +18/-0(삭제·수정 0행), `opal-skills-registry.json` +62/-2. 삭제 2행은 **항목이 아니라 파일 메타**(`version` 3.18.0→3.19.0, `updated_at`)이며 이 파일의 자체 관례(3.18.0=태스크 122, 3.17.0=태스크 120)를 따랐다. 기존 skill 항목·그룹·trigger 변경 0
- `oppb` 항목 키 집합이 `oppd`·`oppl`과 **동일**(name/alias/description/triggers/paths/domain/pipeline). `triggers` 3종은 SKILL.md frontmatter와 문자열 동일, `pipeline`은 `meta.stages` P0~P5와 정합
- **라우팅 기계 검증**: `skill-registry.js match "//oppb"` → `found: true, name: opal-pilot-project-build, group: opal-pilot, alias: oppb`. `get`도 6필드 반환·`resolved_path` 정상. JS 테스트 5파일 fail 0
- 워커 재량 1건 승인 — **`op-oppb` 그룹 신설**로 미등재 단계 스킬 2건(`op-oppb-project-slice` P2, `op-oppb-knowledge-finalize` P5)을 등재했다. W-30 문구는 `oppb` 항목만 명시했으나 두 스킬이 폴더만 있고 레지스트리에 없어 validator가 `unregistered` error를 내던 상태였고 AC-21에 직접 걸린다. 스키마는 `op-gc` 그룹과 동일
- validator error 3건은 전부 `dangling — no SKILL.md at any path`이며 원인은 `~/.opal/skills/` 미배포뿐(W-33 install로 해소). **변경 전 baseline도 error 3건**(같은 3개가 `unregistered`)이라 건수 증가 0, 오류 클래스만 "미등재"→"배포 대기"로 이동
- `opal-capability-agent`를 `agents.md`의 전문 에이전트 매핑 테이블에 **넣지 않은** 판단 승인 — PM 대화형 디스패치 대상이 아니라 Supervisor headless 전용이다. **PM 선례 확인**: `opal-task-action-agent`도 ARCHITECTURE 전문 표에는 있으나(2건) agents.md 매핑 테이블에는 없다(0건). capability-agent가 정확히 같은 패턴이므로 W-31의 ARCHITECTURE 전문 9 계수와도 모순되지 않는다
- 회귀 `5 failed, 1520 passed, 3 skipped, 356 subtests`. 실패 5건은 상류 선재 `tool-scan` 결함이며 워커가 **자기 2파일을 `git checkout`으로 되돌린 상태에서 동일 5건 재현**을 확인해 귀속 증명. `test_registry_parity`는 이름과 달리 skills-registry가 아니라 `tools.md` ↔ `opal-harness.md` §9 도구 표 정합 검사다

## [141] W-49 완료 — 파일럿 공용 인프라 상시 가드 (소유자 제안 추가 작업)
- `opal/tools/state-tool/tests/test_pilot_shared_contract.py` 656행 신규. PM 직접 실행 **20 passed, 152 subtests**
- **스캔 기반 확인**: `SKILLS_DIR.glob("opal-pilot-*")`로 발견분 전부를 대상으로 삼는다(`:105`). 하드코딩·개수 단언 0. 실제로 **11종**을 잡았다 — data-design·dev-short·dev-wireframe·dev·gc·project-build·project-dev·project-loop·project·sdd·write-tech. 내가 수동 확인한 4종보다 넓다
- `PILOTS_WITH_PIPELINE`으로 자기 `pipeline.json`을 가진 파일럿만 규격 검사 대상으로 분리
- **결함 격리(검사 7) 안전성 확인**: `tempfile.mkdtemp(prefix="w49-fault-isolation-")`에 손상 사본을 만들고 원본은 읽기만 한다(`:595,612`). `git status`에 pipeline.json 변경 0건으로 교차 확인. 손상 대상도 이름순 첫 파일럿으로 고르고 특정 파일럿명을 하드코딩하지 않는다
- **검사 6 기준선은 축소 채택** — 워커가 `.github/workflows` 부재(PM 재확인: 0건)와 얕은 클론·단일 브랜치 클론에서 git ref 가용성이 보장되지 않는다는 근거로, 지시가 명시 허용한 폴백("현재 판 내부 일관성": alias 중복 0 + 필수 7필드 보유)을 택하고 설계 메모를 코드에 남겼다. 판단 근거가 타당하므로 승인
- 이 가드는 태스크 132 일회성이 아니라 **앞으로 파일럿을 추가·수정할 때마다 공유 인프라 계약을 회귀 판정하는 상시 자산**이다. W-35(OPPB 전용 귀속 검증)와 역할이 다르며 병존한다

## [142] G5 전반 커밋 (소유자 승인) — 설치는 소유자가 직접 수행
- 커밋 `e21029e` — 12 files, +868/-20
- 소유자 지시: **설치(`scripts/install-mac.sh` 실행)는 소유자가 직접 한다.** PM은 `~/.opal/` 배포를 수행하지 않는다
- **PM 오류 정정 기록**: "파일럿은 서로를 참조하지 않는다"고 소유자에게 답했으나 그것은 큰 파일럿 4종만 본 관측이었다. W-49 워커가 `opal-pilot-*` 전수(11종)를 스캔해 **7종이 다른 파일럿을 참조**함을 발견했다(PM 재확인). 상위 파일럿이 하위 실행 파일럿으로 라우팅하는 정상 설계이며 결함은 아니다. 4종 표본으로 일반화한 것이 오류 — 전수 조사 없이 "전부"를 단정하지 않는다. CLOSE 회고 대상
- 잔여: W-34(소유자 주행 후 재정의), W-35(OPPB 전용 귀속 검증), W-36(최종 판정·허브 merge)

## [143] W-35 완료 — 귀속 검증, 기준선 결함 발견·정정
- `test_pilot_isolation.py` 553행, 13 tests. oppb 스위트 117 → **130 passed**
- 검사 축 4종: (1) 기존 파일럿 3종 디렉토리를 건드린 커밋 중 132 소유 0건(대조군으로 131·133·136이 실제로 건드렸음도 함께 단언 — 0건이면 baseline 오류 신호), (2) registry `(group,name)`·agents.md 헤딩 집합 상위집합, (3) 공유 인프라 5접점 additive, (4) 복구 계약
- **검사 4가 복구 계약을 실물 증명**: 고장난 `oppb_runtime_tool.py` 사본을 `PYTHONPATH` 최우선에 두고 실제 oppd pipeline.json에 `spec-validate`를 실행해 성공 확인. fixture가 실제로 컴파일 불가인지 sanity 체크까지 포함. 외부 `.py`의 oppb import 0건도 정적 확인
- **워커 발견 — 기준 커밋 결함**: `81d890d`는 subject가 "feat(opal-agent): 공용 attempt runtime"이지만 실제로 태스크 132 W-3 변경(`# 132 W-3` 주석 포함, STAGE_ENUM P0~P5·skill_enum·choices의 oppb)을 담고 있다. **태그 누락 커밋**이며 PM이 `git show`로 확인
- 그 결과 검사 3의 enum 부분이 **아무것도 증명하지 못하던 상태**였다(baseline에 이미 oppb가 있어 "추가 0·삭제 0"). 기준선을 부모 `6ae6125`로 이동하고 **"추가 집합이 비어 있지 않음" + "기대 최소 추가값이 실제 추가값의 부분집합"** 단언을 넣어, 기준선을 잘못 잡아 검사가 무의미해지는 회귀까지 잡도록 강화
- 정정 후 실측: skill_enum 10→11(+oppb), choices 10→11(+oppb), STAGE_ENUM 20→26(+P0~P5), 삭제 전부 0
- **PM 측정 오류 1건**: 내가 앞서 "STAGE_ENUM 19→19, 추가 없음"으로 보고했는데 정규식이 여러 줄 리스트를 첫 `]`에서 잘라낸 결과였다. 올바른 값은 20→26. 결론(삭제 0)은 동일하나 수치가 틀렸다 — 다중행 리터럴은 `ast.literal_eval`로 파싱한다. CLOSE 회고 대상
- 검사 1·2·4는 기준선 변경 무영향(`81d890d`가 해당 파일들을 건드리지 않음)

## [144] 배포 누락 발견 — merge 지연이 원인 (PM 판단 오류)
- 소유자 질문("스킬 레지지스트리에 추가가 되었나?")으로 발견. 배포본 `~/.opal/references/opal-skills-registry.json`이 **v3.18.0, oppb 0건**이었다
- 원인: 등재 커밋 `e21029e`가 **브랜치에만 있고 main에 없었다.** `install_opal_references()`가 `FRAMEWORK_ROOT`(실행한 체크아웃) 기준으로 복사하므로 main에서 설치하면 구판이 배포된다. 스킬 파일은 G4 커밋이 이미 main에 있어 배포됐고, **등재만 빠진 반쪽 상태**였다
- **PM 오류 2건**: (a) "`//oppb` 라우팅 성립"이라 보고했으나 `skill-registry.js`가 cwd의 소스 트리를 1순위로 읽는데 내가 워크트리 안에서 실행했다 — **배포본을 검증한 것이 아니었다**(거짓 양성). (b) 더 근본적으로, 등재 커밋을 main에 올리지 않은 채 "설치하시면 됩니다"라고 안내했다. 설치가 main을 읽는다는 사실을 고려하지 않았다
- 교정 규율: **배포 검증은 반드시 소스 트리 밖에서 실행한다.** 경로 우선순위가 cwd를 먼저 보는 도구가 있다
- `skill-registry.js` 자체에는 파일럿 하드코딩 0건(oppd/oppl/opsdd/oppb 전부 미등장) — 등록은 JSON에만 하면 된다

## [145] main 병합 — 첫 실제 충돌 해소
- main이 9건 앞서 있었고(태스크 139·140 계열) 양쪽이 같이 건드린 파일 2종 발생. 상류 충돌 5번 만에 처음으로 실제 conflict
- `scripts/install-mac.sh` — 자동 병합. oppb chmod 블록 2건과 main의 hook 소유권 수정 1건 모두 생존, `bash -n` 통과
- `docs/ARCHITECTURE.md` — 충돌 1건 해소. main의 `opal-workspace-sync` 설명 개선(139)과 태스크 132의 에이전트 개수 정정(16개: 전문 9 + 범용 7)을 **둘 다 보존**. 실제 디렉토리 수 16으로 재확인
- 병합 커밋 `a7cfc62`

## [146] CLOSE 진입 (소유자 명시 승인)
- 소유자 판단: "기본적인 테스트는 끝났으니 close. 실제 테스트 후 문제가 있으면 다시 태스크를 연다"
- W-34(실주행)·W-36(최종 출시 판정)은 **이월**한다. 자동 18회 벤치마크는 측정 구간 정정 후에도 9~16M 토큰·6~13시간 규모라 소유자 판단으로 보류
- `DONE.md` 작성 — 산출물, 검증, 실주행으로 드러난 결함 5건, 실행 주체 분할, 이월 항목, 남긴 상시 자산
