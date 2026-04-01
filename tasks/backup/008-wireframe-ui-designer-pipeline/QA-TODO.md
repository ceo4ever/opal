# QA: TODO -- wireframe-builder 개선 및 ui-designer 스킬 신규 개발

> 검토일: 2026-03-13 | 판정: ✅ Pass

## 1. 요약

TODO.md는 5개 Step으로 PLAN.md의 전체 구현 범위를 분해했다. Step 1(wireframe-builder 재작성)과 Step 2(ui-designer 신규 작성)가 핵심이며, Step 3~5는 레지스트리/문서 메타데이터 업데이트다. 복잡 모드로 판별되었으며, Part C에서 3개 에이전트(핵심 스킬 작성 / 레지스트리 업데이트 / 테스트 검증)를 순차 배치로 실행하는 아키텍처를 정의했다. 모든 변경이 마크다운과 쉘 스크립트 메시지 수정이므로, 병렬 실행보다 순차 실행이 효율적이라는 판단은 적절하다.

## 2. 검증 결과

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| D-1 | Step 완전성 | ✅ | PLAN의 5개 구현 항목(wireframe-builder, ui-designer, skills.md, CLAUDE.md, install-mac.sh)이 Step 1~5에 1:1 대응 |
| D-2 | 완료 기준 명확성 | ✅ | 각 Step에 검증 가능한 완료 기준 명시 (YAML frontmatter 유효, 프로세스 정의 완료, HTML 로직 제거 등) |
| D-3 | 의존성 순서 | ✅ | Step 1 -> Step 2 -> Step 3/4, Step 5 독립. PLAN의 구현 순서(wireframe-builder 먼저 -> ui-designer -> 레지스트리)와 일치 |
| D-4 | QA 체크리스트 커버리지 | ✅ | B-1 기능 테스트 11개 항목이 TASK.md의 wireframe-builder 요구사항 5개, ui-designer 요구사항 7개, 레지스트리 요구사항 3개를 모두 포함 |
| D-5 | 회귀 테스트 포함 | ✅ | B-2에서 기존 자산 보존(화면 도출 규칙, ASCII 패턴, 서브 에이전트 위임), 비변경 영역 무결성(skills.md, CLAUDE.md, install-mac.sh) 확인 항목 포함 |
| D-6 | 보안 체크 포함 | ✅ | B-4에서 민감정보 미포함 및 install-mac.sh 보안 관련 변경 없음 확인 항목 포함 |
| D-7 | 실행 방법 지정 | ⚠️ | Step 1~5 모두 "direct"로 표기되어 있으나, Part C에서는 Agent-1(sub-agent)이 Step 1, 2를 담당하고 Agent-2(sub-agent)가 Step 3, 4, 5를 담당한다고 정의. Part A의 실행 방법 표기와 Part C의 에이전트 할당이 불일치 |
| D-8 | 복잡도 판별 정확성 | ✅ | 변경 파일 5개(>=4), 다중 모듈 범위, 신규+개선 복합 작업 유형으로 복잡 모드 판정은 기준에 부합 |
| D-9 | Part C 완전성 | ✅ | 에이전트 토폴로지(DAG + 3개 에이전트), 스킬 요구사항(C-2), 도구 요구사항(C-3), 테스트 전략(C-4 상세 검증 명령 포함) 모두 포함 |

## 3. 지적 사항

### D-7: Part A 실행 방법과 Part C 에이전트 할당 불일치

- **심각도**: 🔵 **Info**
- **내용**: Part A의 Step 1~5가 모두 `실행 방법: direct`로 표기되어 있으나, Part C에서는 Agent-1(sub-agent)이 Step 1, 2를 수행하고 Agent-2(sub-agent)가 Step 3, 4, 5를 수행하는 것으로 정의되어 있다. 복잡 모드에서 Part C의 에이전트 토폴로지가 실제 실행 방식을 결정하므로 기능상 문제는 없지만, Part A의 실행 방법 필드가 최종 실행 계획과 맞지 않아 혼동의 여지가 있다.
- **권장**: Part A의 Step 1, 2를 `실행 방법: sub-agent (Agent-1)`, Step 3, 4, 5를 `실행 방법: sub-agent (Agent-2)`로 업데이트하면 Part C와 정합성이 높아진다. 다만 Part C가 최종 결정권을 갖는 구조이므로 진행에는 영향 없다.

## 4. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| PLAN.md | 5개 구현 파일(신규 1 + 수정 4)이 TODO Step 1~5에 모두 포함되었는가 | ✅ |
| PLAN.md | 구현 순서(1:wireframe-builder -> 2:ui-designer -> 3:skills.md -> 4:CLAUDE.md -> 5:install-mac.sh)가 일치하는가 | ✅ |
| PLAN.md | 테스트 전략(T-1~T-8)이 TODO Part B QA 체크리스트에 반영되었는가 | ✅ |
| PLAN.md | 리스크 대응(마이그레이션 안내, shadcn 런타임 참조)이 Step 작업 내용에 반영되었는가 | ✅ |
| RESEARCH.md | wireframe.md 스키마 6개 섹션이 Step 1 완료 기준에 포함되었는가 | ✅ |
| RESEARCH.md | shadcn Critical Rules 참조가 Step 2에 반영되었는가 | ✅ |
| RESEARCH.md | web-artifacts-builder 연계가 Step 2에 반영되었는가 | ✅ |
| RESEARCH.md | 기존 자산 보존(화면 도출 규칙, ASCII 패턴) 요구가 Step 1에 반영되었는가 | ✅ |
| TASK.md | wireframe-builder 요구사항 5개가 Step 1 + Part B에서 커버되는가 | ✅ |
| TASK.md | ui-designer 요구사항 7개가 Step 2 + Part B에서 커버되는가 | ✅ |
| TASK.md | 레지스트리 요구사항 3개가 Step 3, 4 + Part B에서 커버되는가 | ✅ |
| TASK.md | 성공 기준 5개가 Part B 기능 테스트에 매핑되는가 | ✅ |
| TASK.md | 제약 조건(스킬 구조, wireframe.md 구조화, shadcn 규칙 준수, install-mac.sh 호환)이 반영되었는가 | ✅ |

## 5. 판정

**✅ Pass**

9개 검증 항목 중 8개 Pass, 1개 Info 수준 불일치(Part A 실행 방법 표기 vs Part C 에이전트 할당). PLAN.md, RESEARCH.md, TASK.md와의 교차 참조에서 누락이나 정합성 문제 없음. Part C 실행 아키텍처가 작업 특성(마크다운 + 쉘 스크립트 메시지 수정)에 맞게 최소 분할되어 있어 다음 단계 진행 가능.
