# TASK: Harness Gate 상태 관리 개선

> 적용 스킬: opal-pilot-project (opp)
> 태스크 폴더: tasks/097-opp-harness-gate-state/

## 배경

Gate 통과 시 STATE.md 갱신이 즉시 이루어지지 않고 마지막에 한꺼번에 처리되는 문제가 관찰됨.
원인: State Gate가 PM Gate 진입 전 1개만 존재하여 QA Gate → PM Gate 사이 갱신이 강제되지 않음.
또한 Gate Fail 처리가 harness-interactive / harness / pm 세 문서에 산발적으로 정의되어 있어 일관성 부족.

## 요구사항

- [x] 완료 산출물 테이블과 Gate 상태를 통합한 `진행 현황` 테이블로 교체
- [x] 각 Gate 완료 시 `진행 현황` 테이블 즉시 갱신 의무 명시
- [x] 앞 Gate 미완료 상태에서 후속 Gate/단계 진입 차단 원칙 추가
- [x] Gate Fail 공통 처리 섹션 신설 (opal-harness-interactive.md)
- [x] 각 Gate 섹션에서 Gate Fail 공통 처리 참조로 연결

## 범위

| 파일 | 수정 내용 |
|------|----------|
| `opal/core/references/opal-harness.md` | §3 STATE.md 공통 템플릿 — `완료 산출물` → `진행 현황` 통합 테이블. 이벤트 테이블 Gate 갱신 행 정비. |
| `opal/core/references/opal-harness-interactive.md` | §2 QA Gate 즉시 갱신 의무 추가. §2.5 Artifact Gate 즉시 갱신 + Fail 이후 처리 추가. §3 PM Gate 즉시 갱신 + 순서 강제 원칙 추가. §5 Gate Fail 공통 처리 섹션 신설. |

## 제외 범위

- `opal-harness.md §1` 자동 루핑 제약 — 워커 검증 루프 실패 영역, 별도 유지
- 각 오케스트레이터 SKILL.md — 하네스 참조 구조이므로 하네스 수정만으로 반영됨
- agentic 하네스 — 별도 작업으로 분리
