# QA-SPEC: T01 정상슬라이스 — G 명세 리뷰 게이트 (spec-review)

> 산출 시점: 2026-07-17T20:08:17+0900 (검증 2원화 ① — 구현 전, 순서 evidence 원천)
> Evaluator: opal-evaluator-agent (opal-agent 채널 동기 디스패치, model=opus) — 생성자(opal-task-agent)≠평가자 (H-9)
> 기준 원천: CONTRACT.md §3 루브릭절

## verdict: **PASS**

| 루브릭 | 판정 | 근거 |
|--------|------|------|
| RB-1 (PLAN 산출물 경로·형식·경계 3필드) | PASS | PLAN.md §3.2가 3필드 전부 CONTRACT.md §1과 일치 명시 (경로 out/status.md·형식 H1 1개+본문 2줄 이상·경계 samples/T01-정상슬라이스/ 밖 금지) |
| RB-2 (시나리오 MV-1·MV-2 커버) | PASS | PLAN §3.6 TS-1→MV-1·TS-2→MV-2, test-scenario.json S-1(AC-1/MV-1)·S-2(AC-2/MV-2) 양쪽 매핑, 둘 다 red_confirmed=true |
| drift 필요성 | no | CONTRACT.md 변경 신호 없음 |

## 결론
명세·설계·시나리오가 계약과 완전 정합. 미충족 항목 없음 → T3 구현 진입 허용.
