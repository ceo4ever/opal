---
template: sdlc-v2
---
# TEST-SCENARIO: 세션 브리핑 출력 집행

> 입력: [TASK.md](TASK.md), [PLAN.md](PLAN.md) | 작성자: PM

## Setup

- 환경: Python 3, 저장소 source checkout, 임시 프로젝트 fixture, 설치 후 `~/.opal/` 배포본
- 공통 데이터: 미완료 EXECUTE 태스크 1건과 candidate·feedback 검토 후보가 있는 MEMORY fixture
- 대역 사용과 한계: 외부 대역 없음. fixture는 저장소 도구의 실제 CLI를 호출하며 설치본은 실제 프로젝트 경로로 별도 확인
- 실행 조건: 자동 실행. 사용자 홈 임시 디렉터리를 쓰는 기존 테스트는 샌드박스 밖 실행 권한 필요

## Scenarios

| ID | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|
| S-1 | AC-1, AC-2, AC-3, C-1, C-2, H-1 | 미완료 태스크와 검토 후보가 있는 fixture | `event-loader project-brief` 실행 | stdout 한 덩어리에 부트 접두부·이어보기·우선 검토가 정확한 순서와 값으로 존재 | event-loader integration test | 구현 전 RED, 구현 후 |
| S-2 | AC-4, C-2 | 태스크·MEMORY가 없는 fixture | 같은 명령 실행 | 기존 짧은 접두부와 개행만 byte-identical 출력 | event-loader integration test | 구현 전 RED, 구현 후 |
| S-3 | AC-3, AC-4, C-2 | 매우 긴 UTF-8 상태값 또는 개별 조회 실패 | CLI와 조립 함수 실행 | 출력은 1,024바이트 이하이며 실패한 입력 블록만 생략 | unit/integration test | 구현 후 |
| S-4 | AC-5, AC-6, C-1, C-3 | 네 플랫폼 부트스트래퍼와 session resolver fixture | source 통합 감사 실행 | 네 본문은 동등하고 project-brief는 project 세션에만 연결되며 다른 세션 판정은 유지 | `task113_bootstrap_audit.py --mode source` | 구현 후 |
| S-5 | AC-6, C-4, H-2 | source 검증 통과 후 공식 install 실행 | installed parity 감사와 실제 프로젝트 명령 실행 | 배포본 해시가 source와 맞고 실제 stdout에 이어보기·우선 검토가 함께 존재 | installed integration | 설치 후 |
| S-6 | C-5 | 115 사용자 변경이 존재 | 최종 `git status`와 변경 파일 대조 | 115 파일의 기존 변경 내용은 본 태스크가 수정·복원하지 않음 | working-tree inspection | 구현 후 |
