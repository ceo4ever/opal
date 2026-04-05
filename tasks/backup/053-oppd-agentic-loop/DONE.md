# DONE: oppd Phase 3 agentic 자율 루핑 + 병렬 실행 설계

> 완료일: 2026-03-30 | 스킬: //opp

## 변경 파일

| # | 파일 | 변경 유형 | 설명 |
|---|------|----------|------|
| 1 | `opal/core/references/opal-harness.md` | 수정 | Guards에 자동 루핑 제약 + State에 병렬 실행 State 추가 |
| 2 | `opal/skills/opal-pilot-project-dev/references/verification-loop-guide.md` | 신규 | 자동 검증 루핑 가이드 (Layered Verification, 실패 유형별 전략, 회귀 방지, 에스컬레이션) |
| 3 | `opal/skills/opal-pilot-project-dev/references/parallel-execution-guide.md` | 신규 | 병렬 실행 가이드 (의존성 그래프, worktree 격리, 병렬 디스패치, 머지 전략, Fallback) |
| 4 | `opal/skills/opal-pilot-project-dev/references/roadmap-guide.md` | 수정 | 자동 테스트 가능성 원칙 + 액션 구조 + 검증 명령 컬럼 + 의존성 그래프 |
| 5 | `opal/skills/opal-pilot-project-dev/SKILL.md` | 수정 | v3.0 — actions/ 구조, Phase 2 세분화, Phase 3 자동 루핑+병렬 실행 |
| 6 | `opal/tools/skill-registry/skill-registry.js` | 수정 | get 명령에서 alias 조회 지원 |

> 배포본(`~/.opal/`)도 모두 동기화 완료.

## 핵심 설계 요약

### A. actions 폴더 구조
oppd 태스크 하위에 `actions/A{NN}-{name}/` 폴더로 액션을 관리. top-level tasks/ 오염 방지.

### B. 자동 검증 루핑 (Layered Verification)
L1(lint) → L2(build) → L3(test) → L4(QA) 계층적 검증. 실패 시 자동 수정 루프(lint 무제한, build 2회, test 3회, QA 즉시 에스컬레이션). 회귀 방지 가드.

### C. 병렬 액션 실행
의존성 그래프(topological sort) → 병렬 그룹 판별 → worktree 격리 → Agent 병렬 디스패치 → 순차 머지 + 통합 테스트. Fallback으로 순차 실행 지원.

### D. 로드맵 세분화
태스크 분할 원칙에 "자동 테스트 가능성" 추가. 액션마다 검증 명령 필수화. 의존성 그래프 시각화.
