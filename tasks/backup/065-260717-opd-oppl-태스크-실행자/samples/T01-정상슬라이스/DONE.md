# DONE — T01 정상 슬라이스 (hello 문서 생성)

> oppl Loop 2 태스크 T01 — opal-loop-action-agent 파이프라인 완주 리포트.
> 완료 시점(KST): 2026-07-17T12:43+09:00

## 태스크 개요

- **task_id**: T01
- **목표**: `samples/T01-정상슬라이스/out/hello.md` 문서 생성 (H1 제목 1개 + 본문 2줄 이상)
- **경계**: `samples/T01-정상슬라이스/` 폴더 내부만 (밖 파일 생성/수정 금지) — 준수 확인

## 파이프라인 실행 (T1~T5+G, 검증 2원화)

| 단계 | 담당(별도 디스패치) | 산출/결과 |
|------|--------------------|-----------|
| T1 명세·설계 | 생성자 opal-task-agent | PLAN.md (RB-1 3필드·RB-2 시나리오 매핑) |
| T2 RED-first | 실행자 scenario-init/red/lock + opal-test-agent(red) | test-scenario.json (TS-1·TS-2 red_confirmed=true, locked=true) |
| G 명세 리뷰 (구현 전) | Evaluator opal-evaluator-agent (생성자와 분리) | QA-SPEC.md verdict=PASS, drift=NO |
| T3 구현 | 생성자(T1 동일 에이전트) 재개 | out/hello.md 생성 |
| T4a 테스트 (구현 후) | 실행자 검증명령 실행 + scenario-mark | 2/2 PASS |
| T4b 규칙검사 | 실행자 인라인(저위험) | PASS — 코드/보안 표면 없음, 경계 준수 |
| T5 마무리 | 실행자 | 본 DONE.md |

**검증 2원화 순서 evidence**: QA-SPEC.md 산출(2026-07-17T12:42:35, 구현 전) < test-scenario.json result 기록(T4a, 구현 후) — 순서 불변 준수.

## 수용기준 대조

| acceptance | 검증명령 | 결과 |
|------------|----------|------|
| out/hello.md 파일이 존재한다 | `test -f out/hello.md` | exit 0 → PASS |
| H1 제목 1개와 본문 2줄 이상을 포함한다 | `grep -c '^# ' out/hello.md` = 1, 본문 3줄 | PASS |

## 결과 계약

- **verdict**: All Pass
- **scenario_results**:
  - TS-1 (out/hello.md 존재): pass — `test -f out/hello.md` exit 0 (2026-07-17T12:43 KST)
  - TS-2 (H1 1개): pass — `grep -c '^# ' out/hello.md` = 1 (2026-07-17T12:43 KST)
- **changed_files**: `samples/T01-정상슬라이스/out/hello.md` (신규), 본 태스크 폴더 내 산출물(PLAN.md, test-scenario.json, QA-SPEC.md, DONE.md)
- **blockers**: 없음
