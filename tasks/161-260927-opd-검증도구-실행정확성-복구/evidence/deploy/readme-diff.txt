--- /Volumes/Data/AIStudio/workspace/ai-framework/.opal-worktrees/task_161/opal/tools/test-tool/README.md
+++ /Users/iskang/.opal/tools/test-tool/README.md
@@ -671,15 +671,3 @@
 
 ---
 
-## 변경이력
-
-| 버전 | 일시 | 변경내용 |
-|------|------|---------|
-| v1.0 | 2026-06-23 | 초기 구현 — 4서브명령(resolve/check/unit/integration) + cmux-tool 에러코드 소비 어댑터 + stop-on-fail 러너 (T039 Step3 GREEN) |
-| v1.1 | 2026-07-10 16:36 | scenario-* 4서브명령(scenario-init/scenario-lock/scenario-mark/scenario-status) 추가 — `lib/scenario.py`로 격리(기존 4서브명령 미간섭), test-scenario.json SSOT(spec존/result존), RED-first 동결 게이트(exit 8~11) (056) |
-| v1.2 | 2026-07-10 | `scenario-red` 서브명령 신설 — red_confirmed를 RED 증거와 함께 tool-gated로 갱신(--evidence 필수, locked 후 거부 scenario_already_locked exit 12), enforce-don't-advise 보강. scenario-init의 red_confirmed 시드 입력은 항상 무시(false 강제)+응답 warning으로 변경 — RED 미관찰 우회 선언 경로 봉쇄 (056/ADD-1) |
-| v1.3 | 2026-07-18 22:42 | 증거 충실도 사다리(`FIDELITY_ORDER`: mock<real-http<real-usage) 도입 — `required_fidelity`/`fidelity`/`surface_ref` 필드(optional additive, 미지정 시 mock 기본값) + `scenario-fidelity-check`(시나리오별 부분 게이트, fidelity_unmet exit 13) + `scenario-conformance`(표면 전수 conformance, surfaces.json 분모·읽기 전용, surface_unverified exit 14, surfaces.json 부재 시 applicable:false 스킵) 신규 서브명령. backlog.json 미접촉(축 분리 불변) (069) |
-| v1.4 | 2026-09-09 14:18 KST | `scenario-coverage-build --task-folder ... --template sdlc-v2` 추가 — sdlc-v2 TASK AC/C, PLAN H, TEST S를 `.scenario-coverage-input.json`으로 결정론 변환하고 W를 features에서 제외. 기존 `scenario-coverage-check` 입력·exit 계약은 유지 (task 111/W-5) |
-| v1.5 | 2026-09-09 14:58 KST | sdlc-v2 builder가 중복 S-ID를 `coverage_input_invalid`로 거부하도록 계약을 보강하고, Setup의 test substitute 기록이 실제 integration/E2E/manual 증거를 대체하지 못함을 명시 (task 111/W-5 보완) |
-| v1.6 | 2026-09-09 15:07 KST | sdlc-v2 PLAN Risks H를 optional로 변경. H 0건은 정상 build/check 통과하고, H가 존재하는 경우의 미커버 실패 계약은 유지 (task 111/W-5 보완) |
-| v1.7 | 2026-09-14 | `tools.md` test-tool 절 흡수 — `integration` 절에 E2E contract v2 profile 5종(`browser`/`api`/`hybrid`/`collaborative`/`manual`, SSOT `lib/e2e_contract.py` `PROFILES`) 명시 + 상단 소스·배포 경로 1줄 추가. 나머지 절 내용(트리거 조건·루프 한도 비보유·status/exit 표·legacy 입력 변환)은 이미 README가 보유해 중복 흡수 없음 (131 W-14) |
