# DONE: opal-harness.md 모듈화 — harness/ 폴더 분리

> 완료일: 2026-04-12 | 태스크: 111 | 스킬: opp

## 작업 요약

`opal-harness.md`에서 Lazy 로딩 가능한 6개 섹션을 `references/harness/` 개별 모듈로 분리. 메인 하네스는 핵심 규칙 + §번호 stub + 모듈 매핑 테이블의 허브로 전환.

## 변경 파일

| # | 파일 | 변경 내용 |
|---|------|----------|
| 1 | `opal/core/references/harness/state-template.md` | 신규 — §3 STATE.md 공통 템플릿 + 행 구성 규칙 (58줄) |
| 2 | `opal/core/references/harness/additional-work.md` | 신규 — §3 추가작업 프로세스 + ADD_DONE 템플릿 (60줄) |
| 3 | `opal/core/references/harness/qa-standards.md` | 신규 — §2 QA 체크리스트 + 산출물 표준 (56줄) |
| 4 | `opal/core/references/harness/observability.md` | 신규 — §5 Observability 전체 (59줄) |
| 5 | `opal/core/references/harness/parallel-execution.md` | 신규 — §7 병렬 처리 원칙 전체 (89줄) |
| 6 | `opal/core/references/harness/header-rules.md` | 신규 — §8 @header 규칙 + code-scan 가이드 (74줄) |
| 7 | `opal/core/references/opal-harness.md` | 수정 — 분리 내용 → stub 교체 + §2 모듈 매핑 테이블 + v4.0 변경이력 (651→364줄) |
| 8 | `opal/core/references/opal-harness-interactive.md` | 수정 — §3 PM Gate에 하네스 모듈 체크포인트 테이블 추가 |
| 9 | `opal/core/references/opal-harness-agentic.md` | 수정 — §2.5 깨진 참조 수정 + §7.6 참조 모듈화 정합 |

## 효과

- 메인 하네스 **651줄 → 364줄** (44% 감축)
- Lazy 모듈 6개로 분리 → 필요 시점에만 로드
- 각 stub에 `[필수 로드]` + 적용 주체/시점/PM Gate 검증 명시 → 트리거 명확화
- PM Gate에 모듈 체크포인트 테이블 → 누락 시 Fail + 재작업 안전망
- §번호(§0~§9) 유지 → 62개+ 외부 참조 영향 없음
- SSOT: 스킬 → 하네스 §N → harness/ 파일 1방향 참조

## QA 결과

- QA-PLAN.md: Pass (Warning 1건)
- QA-EXECUTE.md: Pass (Warning 1건 — 364줄로 300줄 목표 소폭 초과, 44% 감축 달성)
