# TASK: opal-pilot-project-loop(oppl) 루프 기반 오케스트레이터 신설

> 작성일: 2026-07-10 | 작업 유형: 신규 | 적용 스킬: opd | 모드: semi-agentic

## 목표

요청 분석 → 계획 수립 → **목표 충족까지 반복(loop)**하여 규모 있는 프로젝트를 완주시키는 **루프 기반 오케스트레이터** `opal-pilot-project-loop`(alias `oppl`)를 신설한다. oppd와 목적은 동일하나 선형 Phase가 아닌 **종료조건 있는 수렴 루프**로 구동하며, oppd의 후계 후보로서 병행 도입한다.

> 설계 확정본(스펙): 본 폴더 `SPEC.html` (워크플로우·에이전트·검증·SSOT 전체 상세) + `REQUEST-DRAFT.md`

## 명확화 결과 (4요소 — 잠금)

| 요소 | 내용 |
|------|------|
| **목표** | `oppl` 스킬 + 전담 Evaluator 에이전트 + backlog-tool(신규) + test-tool 확장 + 참조 가이드 신설. 2-루프(설계 수렴 / 실행 수렴) 구조, 검증 2원화, 3-SSOT tool-gated. |
| **범위** | (포함) `opal-pilot-project-loop/SKILL.md`, `opal-evaluator-agent/AGENT.md`, `backlog-tool`, `test-tool` 확장(scenario-*), references(loop-control·contract·journey-flow·verification 등), skills/agents 레지스트리 등록, install 반영. (선택) `op-contract-evaluator` 스킬은 평가 절차 복잡 시에만. (제외) oppd 삭제·즉시 deprecate. |
| **제약** | ① 기존 컴포넌트 재사용(주입+상속) — Evaluator 외 신규 에이전트 금지. ② 3-way 모드 승계(semi-agentic 기본). ③ 3-SSOT(backlog/state/test-scenario JSON) tool-gated·축 분리. ④ 헌법 준수(생성자≠평가자, enforce-don't-advise, done=verified). ⑤ oppd 병행 유지(검증 후 deprecate). ⑥ `~/.opal/` 직접 편집 금지 — 프로젝트 소스 수정 후 install 배포. |
| **완료기준** | ① oppl 스킬·evaluator 에이전트·backlog-tool·test-tool 확장 생성 + 레지스트리 등록 + install 반영. ② 신규 도구 단위/통합 테스트 GREEN. ③ oppl 최소 1회 드라이런(설계 루프 → 실행 루프 1태스크)으로 동작 검증(evidence). ④ 변경이력·@header 규칙 준수. |

## 확정 설계 결정 (SPEC 요약)

| # | 결정 |
|---|------|
| 1 | 2-루프 수렴 구조(설계 루프 D1~D7 / 실행 루프 태스크 반복) |
| 2 | 태스크=얇은 수직 슬라이스, `backlog.json`=살아있는 백로그, 2단 설계(거시/미시) |
| 3 | CONTRACT 1급 산출물 — 작성=Planner / 리뷰=Evaluator / 반영=PM |
| 4 | 검증 2원화 — **Evaluator=명세 심판(구현 전)** / **test-agent=동작 검증(구현 후)**. 통과 후 변경파일 convention/security-checker. drift 시만 Evaluator 재콜백 |
| 5 | 디스패치 하이브리드(C) — 생성자(도메인 resolve, T1~T3) + Evaluator 별도, 태스크당 ~3회, 저위험 경량화 |
| 6 | Evaluator = 전담 신규 에이전트 `opal-evaluator-agent`(패턴 B, checker 선례) |
| 7 | 3-SSOT tool-gated JSON — backlog.json(backlog-tool 신규)·state.json(state-tool 재사용)·test-scenario.json(test-tool 확장). 사람 뷰 자동 렌더 |
| 8 | UX 산출물 조건부 — USER_JOURNEY(Loop1)/USER_FLOW(Loop2), Mermaid, user-facing만 |
| 9 | 산출물 자동 생성·기록, 기존 리포트 준용(GC-*/QA-*/DONE) 없으면 VERIFICATION.md, 결과계약 {대상·PASS/FAIL·사유·시점} |
| 10 | alias `oppl` · 종료조건 있는 루프 제어(반복상한·예산·무진전·목표체크·사람게이트) |

## 참조 문서

| 문서 | 용도 | 읽는 시점 |
|------|------|----------|
| 본 폴더 `SPEC.html` | 설계 확정 스펙 SSOT | 전체 |
| docs/PROJECT.md | 프로젝트 정의·문서 레지스트리 | 전체 |
| docs/ARCHITECTURE.md | 컴포넌트 표준·아키텍처 | ANALYSIS~PLAN |
| docs/CONVENTIONS.md | 코드 컨벤션 | EXECUTE |
| .opal/AGENT.md | PM 검토 기준·금지사항 | 전체 |
| 기존 유사: opal-pilot-project-dev/SKILL.md, opal-pilot-sdd/SKILL.md | 참고(계열·차별) | ANALYSIS |
| 기존 도구: state-tool, test-tool, opal-security/convention-checker | 재사용·확장 기준 | ANALYSIS~EXECUTE |

## 절차 (opd Full Task)

TASK → ANALYSIS → PLAN → TEST-SCENARIO → EXECUTE → TEST → CLOSE (semi-agentic: TEST-SCENARIO까지 사용자 검토, EXECUTE 이후 PM 자율, CLOSE 진입 사용자 승인)
