# STATE: 근거 등급층 신설 + 확정/미확정 판정 + 트랙 자동 강등

> 최종 갱신: 2026-08-21 23:20
> 파이프라인 현황(rows/상태/다음 액션)의 SSOT는 `state.json`입니다.
> 조회: `~/.opal/tools/state-tool/run.sh show <task-path>`

## 의사결정 로그
| # | 시점 | 결정 | 근거 |
|---|------|------|------|
| 1 | 2026-08-21 22:23 | additional row inserted after row 7: stage=EXECUTE, item=추가작업 ADD-1 — §9 E1 실행 관측 스코프 병기 1줄, key=execute.add1_e1_scope, new_row_id=8 | 캡틴 승인 2026-08-21 22:2x — 통과 수 스코프 누락 3회 반복 대응. 태스크 미완료 상태이므로 CLOSE 재진입 아닌 EXECUTE 인플라이트 확장 |
| 2 | 2026-08-21 22:58 | additional row inserted after row 12: stage=CLOSE, item=추가작업 ADD-2 — 배포 경로 루트 파생 결함 수정 (RED-first), key=close.add2_root_derivation, new_row_id=13 | 캡틴 승인 — state_tool.py:2400 __file__ 기반 루트 파생을 태스크 경로 기준으로 교체. 배포본에서 정규 인용이 전건 오강등되는 P0 |

## 블로커
없음

## 재개 지점 (2026-08-21 18:27 — 캡틴 지시로 Step 6 완료 후 정지)

### 완료된 것

| Step | 내용 | 산출 |
|------|------|------|
| 1 ✅ | `citation-rules.md` §9 근거 등급·관할 신설 + §0·§2.2·§4·§5 개정 | 426 → 484줄 |
| 2 ✅ | `op-task/SKILL.md` 확정/미확정 스키마 | 280 → 286줄 |
| 3 ✅ | `op-dev-analysis`·`op-dev-plan` SKILL + `plan-guide.md` — 확정 입력 소비 규약 + 형식 경량화 | 178→198 / 450→470 / 463→476 |
| 4 ✅ | RED 테스트 13건 + `TestErrorCodesCompleteness` 45종 선갱신 | `test_state_tool.py` 8353 → 8817줄 |
| 5 ✅ | `state_tool.py` GREEN 구현 + README | 2618→2884 / 363→420줄 |
| 6 ✅ | 독립 재검증 (구현자≠검증자) | 실질 회귀 0건 |

### 남은 것 (재개 시 여기서 시작)

| Step | 내용 | 의존 | agent |
|------|------|------|-------|
| **7** ⬜ | `harness/track-routing.md` **신설** + `opal-harness.md` §2 모듈 표 1행 등재 | Step 6 | opal-task-agent |
| **8** ⬜ | 오케스트레이터 2종 배선 — `opal-pilot-dev/SKILL.md` 강등 판정 호출 지점 + `opal-pilot-dev-short/SKILL.md` 포인터 1줄 | Step 7 | opal-task-agent |
| **9** ⬜ | `docs/PROJECT.md` 레지스트리 등재 + `docs/CONVENTIONS.md` §Citation Rules 포인터 | Step 8 | PM 직접 |

설계 내용은 `PLAN.md` §3.4.2(F-004)·§4.2 Step 7~9가 SSOT. 완료 판정은 `TEST-SCENARIO.md` S-8·S-14·S-16·S-17·S-19·S-20·S-27.

### 재개 후 남은 파이프라인

`execute.implement`(🔄 유지) → TEST 단계(`test.run_tests` → `test.pm_gate`) → CLOSE 진입(**캡틴 승인 필수**) → `close.done_md` + install 재배포(S-29) + brain ingest.

### 이월 판단 대기 1건

`citation-rules.md` §9 E1 항목에 **"실행 관측 인용 시 관측 스코프·명령을 함께 기재"** 1줄 추가 여부 — 캡틴 확인 대기. 근거: 본 태스크에서 통과 수 스코프 누락 오류가 **3회** 반복됐다(358 도구 2종 합계 / PLAN 오귀속 / 디렉토리 341 vs 단일파일 324 오진). Step 9(PM 직접) 때 함께 넣을 수 있다.

### 선재 결함 (미접촉, 후속 태스크 후보)

`TestR11Invariants::test_r11_invariants_S40` 서브테스트 `error_codes_key_set_untouched` — `git show HEAD` 상대 비교라 에러 코드 추가 태스크가 커밋 전까지 구조적으로 FAIL한다(`test_state_tool.py:8795-8809`). 상세: `TEST-SCENARIO.md` §7.

### 워킹트리 상태

브랜치 `feat/098-opds-evidence-tier-track-demote` (base `17a95c4`). 커밋 0건 — 전 변경이 워킹트리에 있다. `~/.opal/` 배포본은 미갱신(S-29 CLOSE 절차).
