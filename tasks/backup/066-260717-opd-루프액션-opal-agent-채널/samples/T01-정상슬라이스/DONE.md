# DONE: T01 — greeting 문서 슬라이스

> 산출: opal-loop-action-agent (oppl Loop 2, opal-agent 채널 완주 실증)
> 완료 시점(KST): 2026-07-17T14:36:01+0900

## 1. 결과 요약

`out/greeting.md` 생성 완료 — H1 제목 1개(`# Greeting`) + 본문 2줄. 수용기준 2개 모두 충족. verdict: **All Pass**.

## 2. 파이프라인 완주 기록 (T1~T5+G, opal-agent 채널)

| 단계 | 축 | 대상 | 호출 모드 | model | exit | 결과 |
|------|-----|------|----------|-------|------|------|
| T1 명세·설계 | 생성자(공통→task-agent) | op-dev-plan | 비동기(bg) | opus | 0 | PLAN.md 산출 |
| T2 RED 시나리오 | test-agent | opal-test-agent(red) | 비동기(bg) | sonnet | 0 | S1/S2 RED 실관찰 |
| G 명세 리뷰 ★① | Evaluator | opal-evaluator-agent | 동기(fg) | opus | 0 | VERDICT pass → QA-SPEC.md |
| T3 구현 | 생성자(warm resume) | op-dev-execute | 비동기(bg) | sonnet | 0 | out/greeting.md 생성 |
| T4a GREEN ★② | test-agent | opal-test-agent | 동기(fg) | sonnet | 0 | S1/S2 pass |
| T4b 규칙검사 | checker | (인라인, 저위험) | — | — | — | 위반 없음 |

- 생성자 세션: cold prime(`--session-id`) T1 → warm resume(`--resume`) T3, session.json 보존.
- 3-분리 캡처: `.oppl-run/<phase>.{result.json,err.log,exitcode}` (완료 마커 = exitcode 파일 존재).
- `--dangerously-skip-permissions` 미사용. 축별 `--allowed-tools` allowlist 준수. `--cwd` 프로젝트 루트 고정.

## 3. 검증 2원화 순서 evidence (H-9)

- 생성자 ≠ 평가자: 구현=생성자 세션(opus/sonnet), 심사=opal-evaluator-agent(별도 세션).
- G(구현 전) QA-SPEC.md: 2026-07-17T14:33:20 (KST)
- T4a(구현 후) result marked_at: 2026-07-17T14:35:31 (KST)
- 14:33:20 < 14:35:31 → 검증 2원화 순서 실증(구현 전 리뷰 → 구현 후 테스트).
- RED-first: scenario locked_at 14:32:05 (전 시나리오 red_confirmed 후 lock, self-confirming RED 차단).

## 4. 기계검증 결과 (CONTRACT.md §2)

| # | 명령 | 기대 | 결과 |
|---|------|------|------|
| MV-1 | `test -f out/greeting.md` | exit 0 | pass (exit 0) |
| MV-2 | `grep -c '^# ' out/greeting.md` | ≥1 | pass (출력 1) |

## 5. 변경 파일 (task_scope 내부 한정)

- `out/greeting.md` (신규)
- `PLAN.md`, `QA-SPEC.md`, `test-scenario.json`, `DONE.md` (태스크 산출물)
- `.oppl-run/` (전송 산출물, .gitignore 권고)

경계 준수: `samples/T01-정상슬라이스/` 밖 파일 생성/수정 없음.

## 6. blockers

없음.
