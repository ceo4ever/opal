# Dev QA 가이드 (ANALYSIS / PLAN / TEST-SCENARIO 검증 기준)

> **실행 컨텍스트**: 이 가이드는 PM Gate 문서검증 시 PM이 참조하는 기준 라이브러리다. 문서 QA는 별도 QA Gate나 QA 에이전트 디스패치 없이 PM Gate가 직접 흡수한다. 동작 검증(TEST / TEST-SCENARIO 실행 / verify)은 본 가이드와 독립이다.

> **[MUST]** 산출물 작성·검증 시 `opal/core/references/harness/citation-rules.md`를 Read하여 근거 제시 규칙을 준수한다.

## 목적

PM이 PM Gate에서 각 단계 산출물을 사용자보다 먼저 검토하여 다음을 판단한다.

1. 다음 단계가 바로 실행 가능한가
2. 이전 단계의 목표·제약·완료 기준이 누락 없이 이어졌는가
3. `docs/PROJECT.md` 레지스트리에서 선별한 프로젝트 문서·기획·설계 산출물의 제약이 반영되었는가
4. 상태·결과·증거가 `state.json` 또는 `test-scenario.json` 대신 마크다운에 중복 기록되지 않았는가

## 적용 시점

| 단계 | sdlc-v2 검증 | legacy 검증 |
|---|---|---|
| ANALYSIS | `Findings / Change boundary / Critical assumptions / Handoff` 검토 | 기존 R-1~R-8 검토 |
| PLAN | `Approach / Decisions and contracts / Work items / Risks / Release and recovery` 검토 | 기존 P-1~P-8 또는 SP-1~SP-5 검토 |
| TEST-SCENARIO | `Setup / Scenarios`와 coverage build/check 결과 검토 | 기존 리스크·데이터·L1/L2/L3·매핑표 검토 |

TASK는 사용자 직접 검토 대상이다. EXECUTE 이후 동작 검증은 opal-test-agent와 `test-scenario.json`이 담당한다.

## sdlc-v2 공통 검증

| # | 검증 항목 | 확인 내용 |
|---|---|---|
| V2-1 | 템플릿 식별 | 파일 첫 YAML frontmatter에 `template: sdlc-v2`가 있는가 |
| V2-2 | 책임 경계 | 단계 상태·승인 상태·실행 결과·증거를 본문에 복제하지 않았는가 |
| V2-3 | 근거 | 설계에 영향을 주는 사실·제약·문서 참조에 근거가 있는가 |
| V2-4 | docs 레지스트리 | `docs/PROJECT.md` 문서 레지스트리와 PM 주입 문서가 필요한 범위로 반영되었는가 |
| V2-5 | 중복 제거 | legacy 독립 표·체크리스트·전문 복제가 신규 경로에 재생성되지 않았는가 |

## ANALYSIS sdlc-v2 검증 기준

| # | 검증 항목 | 확인 내용 |
|---|---|---|
| RA-1 | Findings 유효성 | PLAN을 바꿀 수 있는 질문과 확인한 사실만 남겼는가 |
| RA-2 | Change boundary | 직접 변경 후보, 호출자, 회귀 확인 대상, 구현 후 갱신 후보 문서가 확인되었는가 |
| RA-3 | Critical assumptions | 틀리면 구현·검증·실연동이 실패하는 가정과 확인 한계가 분리되었는가 |
| RA-4 | Handoff | PLAN에서 결정할 선택과 착수 차단 사항만 남겼는가 |
| RA-5 | 문서 선별 | `docs/PROJECT.md` 레지스트리의 작업 도메인 문서·기획·설계 산출물을 필요한 구간만 확인했는가 |
| RA-6 | 원문 덤프 차단 | 소스코드·문서 전문을 길게 복제하지 않았는가 |

## PLAN sdlc-v2 검증 기준

| # | 검증 항목 | 확인 내용 |
|---|---|---|
| PP-1 | Approach | source/installed 경계, 제외 범위, legacy 호환 정책이 명확한가 |
| PP-2 | Decisions and contracts | 구현자가 따라야 할 결정과 변경 후 계약이 충분히 구체적인가 |
| PP-3 | Work items | 담당, 변경 대상, 구체적 변경, 선행 작업, 실행 그룹, 완료 기준 연결이 모두 채워졌는가 |
| PP-4 | 병렬 안전성 | 같은 실행 그룹 안에 파일 소유권 충돌이 없고 선행 작업이 뒤집히지 않았는가 |
| PP-5 | docs 갱신 | 구현으로 내용이 달라질 프로젝트 문서·기획·설계 산출물이 변경 대상에 포함되었는가 |
| PP-6 | Risks | TEST-SCENARIO가 검증할 H-N 위험이 실제 실패 계약과 연결되는가 |
| PP-7 | Release and recovery | 검증, 설치/배포, 실패 시 복구 기준이 실행 가능하게 적혔는가 |

## TEST-SCENARIO sdlc-v2 검증 기준

| # | 검증 항목 | 확인 내용 |
|---|---|---|
| TS-1 | Setup | 공통 환경·데이터·대역 한계·상태 기록 소유권이 한 번만 정리되었는가 |
| TS-2 | Scenarios | 모든 S 행이 검증 대상, 조건, 행동, 기대 결과, 방법·환경, 시점을 가진가 |
| TS-3 | AC/C/H 커버 | TASK의 AC/C와 PLAN의 H가 최소 1개 시나리오에 연결되었는가 |
| TS-4 | 실행 방법 | FE/API/외부 연동 변경에 L2 자동화 또는 정당한 BLOCKED/L3 사유가 있는가 |
| TS-5 | 결과 비기재 | PASS/FAIL/BLOCKED와 실행 증거가 TEST-SCENARIO.md에 쓰이지 않았는가 |
| TS-6 | 도구 검증 | `scenario-coverage-build`와 `scenario-coverage-check`가 통과했는가 |

## legacy 검증 기준

`template: sdlc-v2`가 없는 기존 태스크에서는 기존 절명과 표를 읽기·재개 호환으로 검토한다.

| 단계 | legacy 기준 |
|---|---|
| ANALYSIS | R-1~R-8: TASK 커버리지, 코드 실독, 파일 완전성, 영향 범위, 리스크, 깊이, 원문 덤프 차단, 확정 입력 판정 |
| PLAN Full | P-1~P-8: 구현 가능성, 의존성 순서, ANALYSIS 반영, 파일 일치, 설계 구체성, 테스트 전략, 기능-QA 커버리지, 확정 승계 |
| PLAN Short | SP-1~SP-5: 코드 분석, 구현 계획, 체크리스트 완전성, QA 항목, Short 적정성 |

legacy에서도 새 기준을 이유로 기존 태스크 문서를 sdlc-v2로 재작성하지 않는다.

## QA 리포트

sdlc-v2에서는 PM Gate 판정을 사용자 보고와 `state.json`에 반영한다. `QA-{단계}.md`는 pipeline artifact가 요구하거나 legacy 태스크일 때만 작성한다.

```markdown
# QA: {단계명} — {태스크 제목}

> 검토일: YYYY-MM-DD | 판정: {Pass / Needs Revision}

## 1. 요약
{산출물의 핵심 내용 3~5줄}

## 2. 검증 결과
| # | 검증 항목 | 결과 | 비고 |
|---|---|---|---|
| {ID} | {항목명} | Pass / Warning / Fail | {근거 또는 문제 설명} |

## 3. 지적 사항
{Warning 또는 Fail 항목. 없으면 "지적 사항 없음"}

## 4. 교차 참조 검증
| 참조 산출물 | 검증 내용 | 결과 |
|---|---|---|

## 5. 판정
**{Pass / Needs Revision}**
{판정 근거 1~2줄}
```

## 변경이력

| 버전 | 일시 | 변경내용 |
|---|---|---|
| v1.0 | - | 초기 작성 — ANALYSIS R-1~R-6, PLAN(Full) P-1~P-6, PLAN(Short) SP-1~SP-5 검증 기준 |
| v1.5 | 2026-08-24 22:39 | P-8을 ANALYSIS 핸드오프 2원천 승계 기준으로 개정 (101) |
| v2.0 | 2026-09-09 | sdlc-v2 검증 기준을 신규 절명과 `docs/PROJECT.md` 레지스트리 계약 중심으로 재작성하고, legacy R/P/SP 기준은 호환 절로 축소 (111) |
