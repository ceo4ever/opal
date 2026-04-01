# QA: PLAN -- opal-project-init 기존 프로젝트 지원 (모드 분기)

> 검토일: 2026-03-21 | 판정: Pass

## 1. 요약

opal-project-init 스킬에 "기존 프로젝트" 모드를 추가하는 Short Task PLAN이다. SKILL.md에 Step 0 모드 분기와 자동 분석 단계를 추가하고, apply.js에 `--mode existing` 옵션/백업/CLAUDE.md 병합 로직을 구현하며, README.md를 갱신하는 3-Step 구성이다. 변경 범위는 `skills/opal-project-init/` 내 3개 파일로 한정되며, 기존 신규 프로젝트 플로우는 그대로 유지하는 안전한 설계이다. 핵심 설계로 자동 분석 소스별 플레이스홀더 매핑표, CLAUDE.md OPAL 마커 기반 병합, 기술 스택별 템플릿 필터링 규칙이 구체적으로 명세되어 있다.

## 2. 검증 결과

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| SP-1 | 코드 분석 충분성 | Pass | SKILL.md 8단계 플로우, apply.js 212줄 구조(CLI/config/processFile/replacePlaceholders), 템플릿 디렉토리 22개 파일, CLAUDE.md OPAL 마커 등 실제 코드 기반 분석 확인. 영향 범위(OPAL AGENT.md -> SKILL.md -> apply.js -> config.json)도 파악됨 |
| SP-2 | 구현 계획 구체성 | Pass | SKILL.md(Step 0 모드 분기, 자동 분석, 확인형 인터뷰, 템플릿 필터링), apply.js(CLI 옵션, backupFile, mergeClaudeMd, processFile 분기, excludeTemplates), README.md(섹션 추가) 모두 파일별 구체적 변경 내용이 코드 스니펫과 함께 명시됨 |
| SP-3 | 체크리스트 완전성 | Pass | TASK.md의 4개 요구사항 영역(SKILL.md 변경 5항목, apply.js 변경 3항목, triggers 확장, 제약조건 4항목)이 실행 체크리스트 3개 Step으로 빠짐없이 분해됨 |
| SP-4 | QA 항목 커버리지 | Pass | 기능 테스트 8항목(모드 분기, 자동 분석, 인터뷰, 필터링, existing 동작, CLAUDE.md 병합, 백업, excludeTemplates), 회귀 테스트 4항목(기존 플로우, 기본값, 하위호환, 템플릿 무수정), 코드 품질 4항목(에러 핸들링, 가독성, 문서, 변경 범위) 포함 |
| SP-5 | Short Task 적정성 | Pass | 변경 대상이 3개 파일이고, 신규 기능이 아닌 기존 스킬의 모드 확장이며, 핵심 로직(apply.js 병합)도 명확한 패턴(마커 기반 파싱)이므로 Short Task에 적합 |

## 3. 지적 사항

지적 사항 없음.

다만 참고 사항이 하나 있다:

- [Info] `opal/core/references/skills.md` 레지스트리 갱신이 영향 범위 분석에서 언급되었으나 실행 체크리스트에는 포함되지 않았다. 트리거 추가 시 레지스트리도 함께 갱신이 필요할 수 있으나, TASK.md의 제약조건에서 "skills/opal-project-init/ 범위 내에서만 변경"으로 명시하고 있으므로 현재 범위에서는 제외가 맞다. 필요하면 별도 태스크로 처리하면 된다.

## 4. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK.md | SKILL.md 변경 요구사항 5개 항목 모두 PLAN에 반영 | Pass |
| TASK.md | apply.js 변경 요구사항 3개 항목 모두 PLAN에 반영 | Pass |
| TASK.md | triggers 확장 요구사항이 PLAN에 반영 | Pass |
| TASK.md | 제약조건 4개(기존 플로우 유지, 템플릿 수정 최소화, 범위 한정, README 업데이트) 모두 PLAN에 반영 | Pass |
| TASK.md | 관련 문서 3개 파일이 PLAN의 변경 파일 목록과 일치 | Pass |

## 5. 판정

**Pass**

TASK.md의 모든 요구사항과 제약조건이 PLAN에 빠짐없이 반영되었다. 코드 분석이 실제 파일 구조와 로직에 기반하며, 구현 계획이 코드 스니펫 수준으로 구체적이다. 실행 체크리스트와 QA 체크리스트 모두 충분한 커버리지를 갖추고 있어 바로 EXECUTE 단계로 진행할 수 있다.
