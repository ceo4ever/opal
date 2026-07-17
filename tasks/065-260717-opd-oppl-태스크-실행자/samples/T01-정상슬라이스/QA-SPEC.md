# QA-SPEC — T01 명세 리뷰 게이트(G, 구현 전)

> oppl Loop 2 태스크 T01 — Evaluator(opal-evaluator-agent, 생성자와 분리) 구현-전 명세 리뷰.
> 실행자(opal-loop-action-agent)가 Evaluator verdict·근거를 산출한 리포트.
> 기준 원천: CONTRACT.md §3 루브릭절 (RB-1, RB-2).

- **phase**: spec-review (G 게이트, 구현 전)
- **verdict**: PASS
- **drift 필요성**: NO
- **판정 시점(KST)**: 2026-07-17T12:42:35+09:00
- **검토 대상**: PLAN.md, test-scenario.json (기준: CONTRACT.md)

## 루브릭별 결과 계약

| 대상(item) | 결과(result) | 사유(reason) | 제안(suggestion) | 시점 |
|------------|--------------|--------------|------------------|------|
| PLAN.md::RB-1 (산출물 경로·형식·경계 3필드 명시) | PASS (Likert 5) | PLAN §1이 3필드를 CONTRACT §1과 문자열 단위로 일치 명시 — 경로 `.../out/hello.md`, 형식 `마크다운 H1 1개 + 본문 2줄 이상`, 경계 `samples/T01-정상슬라이스/ 밖 생성/수정 금지` | 없음 | 2026-07-17T12:42:35+09:00 |
| test-scenario.json::RB-2 (MV-1·MV-2 전부 커버) | PASS (Likert 5) | TS-1(file-exists→`test -f out/hello.md`)=MV-1, TS-2(content-grep→`grep -c '^# ' out/hello.md ≥1`)=MV-2 전부 매핑, 검증명령·기대값이 CONTRACT §2 기계검증절과 동일 | 없음 | 2026-07-17T12:42:35+09:00 |

## 순서 evidence

- test-scenario.json 상태: `locked=true`, TS-1·TS-2 모두 `red_confirmed=true` (RED 실관찰 증거 기록) — RED-first 규율 충족 후 G 진입.
- 본 QA-SPEC.md 산출 시점(구현 전)은 이후 test-scenario.json result존 기록 시점(T4a, 구현 후)보다 앞선다 — 검증 2원화 순서 불변 준수.

## 종합

두 루브릭(RB-1, RB-2) 모두 통과선(≥4) 충족, 계약 불일치 없음 → **G 게이트 PASS, T3 구현 착수 가능.**
