# 통합 조율 (전문 에이전트 체계)

> 출처: opal-pm.md §10
> Lazy 트리거: 다중 에이전트 배치 구성 시
> 탐색 경로: `opal/core/references/pm/orchestration.md`

전문 에이전트 체계에서 PM이 추가로 담당하는 역할.

## 인터페이스 계약 관리

- BE 에이전트가 만든 API 스펙(엔드포인트, request/response DTO) → FE 에이전트에 전달
- 공통 타입 정의 → 양쪽 에이전트에 동기화
- DB 에이전트가 확정한 스키마 → BE 에이전트에 전달

## Batch 간 핸드오프

- Batch N 완료 → changed_files 수집 → Batch N+1 에이전트에 주입
- 선행 Batch 실패 → 후속 Batch 중단 여부 판단
- 선행 에이전트의 산출물(API 스펙, 스키마 등)을 후속 에이전트 프롬프트에 포함

## 충돌 해소

- 동일 파일을 FE/BE 양쪽에서 수정해야 할 때 → 순차 실행으로 전환
- 공통 영역(타입 정의, 공유 모듈) 변경 시 → 먼저 실행한 에이전트 결과를 후속에 반영
- worktree 격리가 필요한 경우 → Agent 도구의 isolation: "worktree" 사용
