# 워커 code-scan 우선 강제 격상 검토

> 유형: improvement | 상태: candidate | 등록: 2026-09-09 18:09 KST (메모리 정리 시 010 후속 파일에서 승계)
> 원출처: `follow-up-code-scan-phase2.md` (2026-06-11, 태스크 010-260526-opp-code-scan-pm-mandate 후속 ①)

## 내용

010 Phase 2 후속 — 워커(EXECUTE 단계) 자체 탐색에서 code-scan 우선을 권고에서 강제로 격상할지 판단한다.

## 현황 (2026-09-09 실측)

- 워커 에이전트 7종(be/fe/db/plan/planning/test/loop-action)은 탐색 순서 1번에 「`.opal/code-scan.json`이 있으면 code-scan search」를 두고 있으나 [MUST]·게이트 없이 자율 선택이다.
- 태스크 106이 도구 판정으로 승격한 것은 PM 측 PLAN 인용 검사(`state-tool verify --code-scan-citation-check`)뿐이다. 워커 EXECUTE 탐색은 규율 대상이 아니다.
- @header 커버리지 32.7%(113/346) — 강제 시 미커버 파일에서 code-scan이 빈 결과를 내는 폴백 설계가 전제다.

## 판단 조건

Phase 1(PM 무조건화) 운영 데이터에서 워커 Glob/Grep 직행 탐색이 PM 규약과 어긋나는 사례가 축적되면 격상. 사례가 없으면 dead 전이.

## 승계 시 정리된 항목

- 후속 ② @header 커버리지 확충 — 106 `opcmb` 스킬 신설 + 107 자산 정리로 수단·상태 모두 변경되어 원문 폐기.
- 폐기 기록 ③ .md @header 표준화 — 폐기 결정으로 종결, 107이 방향 확정. 기록 불요.
