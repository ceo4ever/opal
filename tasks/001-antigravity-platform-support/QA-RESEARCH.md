# QA: RESEARCH — Antigravity 플랫폼 지원 추가 및 QA 호출 구조 개선

> 검토일: 2026-03-07 | 판정: ⚠️ Needs Revision → ✅ Pass (지적 사항 반영 완료)

## 1. 요약

AI 개발 프레임워크에 Google Antigravity 플랫폼을 3번째 지원 플랫폼으로 추가하기 위한 분석 결과이다. 핵심 발견으로 SKILL.md 포맷이 3-플랫폼 공통(Agent Skills 오픈 표준)이라 스킬 6개는 디렉토리 복사만으로 적용 가능하며, Antigravity에 agents/ 디렉토리가 없어 기존 3개 에이전트를 Skills로 변환하는 방안을 권장하고 있다. 병행하여 Cursor 에이전트의 플랫 파일 전환, QA 호출 누락의 구조적 원인(레퍼런스 가이드에 QA 호출 단계 부재)을 파악하고 4개 가이드 수정 + AGENT.md 표현 수정 + SKILL.md QA 강조 블록 추가를 제안한다. Antigravity 프리뷰 단계 변경 가능성, 에이전트->Skills 변환 시 독립 컨텍스트 약화, `~/.gemini/GEMINI.md` 충돌 등 4가지 리스크를 식별했다.

## 2. 검증 결과

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| R-1 | TASK 커버리지 | ⚠️ | A-1~A-6, B-0, C-1~C-3 모든 요구사항에 대해 분석 수행됨. 단, A-2 에이전트 적용 방안에서 3개 에이전트의 Antigravity Skills 변환 파일이 신규 생성 목록에 누락됨 (상세: 지적 사항 1) |
| R-2 | 코드 실독 여부 | ✅ | SKILL.md의 에이전트 탐색 경로(67~70행), AGENT.md의 "자동 호출" 표현(5행), references/ 5개 파일 구조, cursor/agents/ 디렉토리 구조, .mdc 포맷 frontmatter 등을 실제 파일 기반으로 정확히 기술함. 검증 시 모두 일치 확인 |
| R-3 | 변경 파일 완전성 | ⚠️ | 기존 파일 수정 목록(7개)과 신규 생성 목록(11개)을 관련 파일 테이블에 망라함. 단, Antigravity용 에이전트 변환 Skills 3개(`antigravity/skills/task-flow-qa/SKILL.md` 등)가 신규 생성 목록에 누락됨. 또한 `templates/CLAUDE.md`가 간접 영향으로 언급되었으나 변경 필요 여부가 미결 상태 (상세: 지적 사항 1, 2) |
| R-4 | 영향 범위 분석 | ✅ | 직접 영향(6개 영역), 간접 영향(2개 영역), 영향 없는 영역을 구분하여 분석. 간접 영향으로 `templates/CLAUDE.md`와 `templates/cursor-rules/002-development-workflow.mdc`를 식별한 점이 적절함 |
| R-5 | 리스크 식별 | ✅ | 4가지 리스크(Antigravity 프리뷰 변경, 독립 컨텍스트 약화, Cursor 기존 사용자 영향, GEMINI.md 충돌)를 식별하고 각각 완화 방안을 제시함. 리스크 수준과 대응이 현실적 |
| R-6 | 분석 깊이 적정성 | ✅ | 신규 개발 + 기능 개선 유형에 맞게 심층 분석 수행. 기술 선택(에이전트 적용 3가지 방안 비교), 아키텍처(3-플랫폼 매핑 종합 테이블), 포맷 변환 규칙(Rules frontmatter 매핑)을 포함하여 적정한 깊이 |

## 3. 지적 사항

### 지적 사항 1: Antigravity 에이전트 변환 Skills 파일 누락

**심각도: 🟡 Warning**

RESEARCH 섹션 2에서 에이전트를 Skills로 변환하는 방안 A를 권장하고, 3-플랫폼 매핑 종합 테이블에서 Antigravity Agents를 `antigravity/skills/{name}/SKILL.md`로 명시했다. 그러나 **신규 생성 파일 테이블**에는 다음 3개 파일이 누락되어 있다:

- `antigravity/skills/task-flow-qa/SKILL.md`
- `antigravity/skills/task-flow-planner/SKILL.md`
- `antigravity/skills/task-flow-test/SKILL.md`

신규 생성 목록에는 `antigravity/skills/task-flow/SKILL.md`과 `antigravity/skills/{나머지 5개}/SKILL.md`만 있다. 에이전트 변환 Skills는 기존 스킬 복사와 성격이 다르므로(AGENT.md -> SKILL.md 포맷 변환 필요) 별도 항목으로 명시해야 PLAN 단계에서 작업 범위를 정확히 산정할 수 있다.

**수정 권장**: 신규 생성 파일 테이블에 3개 에이전트 변환 Skills를 개별 행으로 추가.

### 지적 사항 2: `templates/CLAUDE.md` 변경 필요 여부 미결

**심각도: 🔵 Info**

간접 영향 섹션에서 `templates/CLAUDE.md`를 "에이전트 탐색 경로 예시가 CLAUDE.md와 일치해야 함 — 확인 필요"로 기술했으나, 실제 확인 결과를 기록하지 않았다. `templates/CLAUDE.md`는 에이전트 탐색 경로를 직접 언급하지 않지만, 아키텍처 섹션과 개발 워크플로우 섹션이 프로젝트 `CLAUDE.md`와 동기화되어야 한다. Antigravity 섹션 추가 시 이 템플릿도 업데이트가 필요할 수 있다.

**권장**: 간접 영향의 확인 결과를 "변경 필요" 또는 "변경 불필요"로 확정하여 기술. PLAN 단계에서 누락되지 않도록 명확히 해둘 것.

## 4. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK.md | A-1(Skills 디렉토리 구성) 분석 존재 여부 | ✅ — 섹션 1 관련 파일 + 섹션 2 매핑 테이블에서 구체적으로 다룸 |
| TASK.md | A-2(Agents 적용 방안) 분석 존재 여부 | ✅ — 섹션 2에서 3가지 방안 비교 후 권장안 제시. 단, 파일 목록은 불완전(지적 사항 1) |
| TASK.md | A-3(Rules 템플릿) 분석 존재 여부 | ✅ — 포맷 변환 규칙과 신규 파일 4개 명시 |
| TASK.md | A-4(R2 설정) 분석 존재 여부 | ✅ — 신규 파일 2개 명시 + 리스크 4에서 GEMINI.md 충돌 다룸 |
| TASK.md | A-5(에이전트 탐색 경로) 분석 존재 여부 | ✅ — 현재 경로 확인 + 변경 필요 명시 |
| TASK.md | A-6(문서 업데이트) 분석 존재 여부 | ✅ — CLAUDE.md, README.md 수정 명시 |
| TASK.md | B-0(Cursor 플랫 파일 전환) 분석 존재 여부 | ✅ — 현재 구조/변경 후 구조 명시, 발견 3에서 상세 설명 |
| TASK.md | C-1(레퍼런스 QA 호출 추가) 분석 존재 여부 | ✅ — 4개 가이드 수정 대상 명시, 발견 5에서 구조적 원인 분석 |
| TASK.md | C-2(자동 호출 표현 수정) 분석 존재 여부 | ✅ — AGENT.md 수정 대상 명시 |
| TASK.md | C-3(QA 호출 강조) 분석 존재 여부 | ✅ — SKILL.md 수정 대상 명시 |
| TASK.md | 제약 조건(하위 호환, 포맷 호환, 소스 원본 유지 등) 반영 여부 | ✅ — 리스크 3에서 하위 호환 다룸, 소스 구조 패턴에서 원본 유지 확인 |

## 5. 판정

**⚠️ Needs Revision**

분석 깊이와 범위는 우수하나, Antigravity 에이전트 변환 Skills 3개 파일이 신규 생성 목록에서 누락된 점(🟡 Warning)이 PLAN 단계의 작업 범위 산정에 영향을 줄 수 있다. 해당 파일을 신규 생성 테이블에 추가하면 Pass 가능.
