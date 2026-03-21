# QA: EXECUTE -- opal-project-init 기존 프로젝트 지원 (모드 분기)

> 검토일: 2026-03-21 | 판정: Pass

## 1. 요약

opal-project-init 스킬에 "기존 프로젝트" 모드를 추가하는 작업이 완료되었다. SKILL.md에 Step 0 모드 분기, Step 0-A 자동 분석, Step 0-B 확인/보정 인터뷰가 추가되었고, apply.js에 `--mode existing` 옵션, backupFile(), mergeClaudeMd(), mergeAppend() 함수, excludeTemplates 필터링, docs 스킵 로직이 구현되었다. README.md에 기존 프로젝트 모드 섹션과 FAQ가 보강되었다. Node.js 문법 검증(node --check) 통과. 기존 신규 프로젝트 플로우는 mode 기본값 "new"로 보호된다.

## 2. 검증 결과

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| E-1 | 체크리스트 갱신 완료 | Pass | PLAN.md 실행 체크리스트 Step 1~3 모두 [x], QA 체크리스트 16개 항목 모두 [x] |
| E-2 | 완료 기준 충족 | Pass | SKILL.md에 Step 0/0-A/0-B 추가됨, apply.js에 --mode existing/백업/병합 구현됨, README.md 갱신됨 |
| E-3 | 파일 변경 정합성 | Pass | PLAN.md가 명시한 3개 파일(SKILL.md, apply.js, README.md)이 모두 변경됨. 추가로 opal/core/references/skills.md 경로 갱신 및 구 opal/skills/project-init/SKILL.md 삭제 발생 (스킬 이전에 수반되는 정리 작업) |
| E-4 | 코드 컨벤션 준수 | Pass | apply.js는 기존 코드와 동일한 스타일(CommonJS require, JSDoc 주석, 한국어 콘솔 메시지) 유지. SKILL.md는 기존 Step 구조와 마크다운 포맷 일관성 유지 |
| E-5 | 테스트 결과 확인 | Pass | `node --check apply.js` 문법 검증 통과 (에러 없음). Short Task이므로 TEST-REPORT.md 없음 |
| E-6 | 블로커 해결 여부 | Pass | 블로커 보고 없음 |
| E-7 | QA 체크리스트 충족 | Pass (아래 상세) | 기능 8항목, 회귀 4항목, 코드 품질 4항목 -- 실질적으로 모두 충족 |

### E-7 상세: QA 체크리스트 항목별 검증

**기능 테스트**:
- SKILL.md Step 0 모드 분기: 자동 판별 기준(package.json 등 7개 파일/디렉토리), 신규/기존 선택지, 기존 모드 진행 경로(0-A -> 0-B -> 4~8) 모두 명확
- 자동 분석 대상: package.json, pyproject.toml, go.mod, Cargo.toml, .env, docker-compose.yml + LLM 파일(README.md, CLAUDE.md, .cursorrules, GEMINI.md, docs/) 포함
- 확인/보정 인터뷰: 분석 결과를 미리 채운 프롬프트 템플릿 제공, "확인"으로 진행 가능
- 템플릿 필터링: 4가지 조건별 제외 규칙 표로 정리, config.json excludeTemplates 연동
- apply.js --mode existing: CLI 파싱(modeIdx), config.json 우선순위(CLI > config > "new"), mode 검증("new"/"existing" 외 에러)
- CLAUDE.md 병합: mergeClaudeMd() 함수가 OPAL 마커 기반 3파트 병합(새 OPAL + 새 프로젝트 + 기존 사용자) 구현
- 백업: backupFile() 함수가 .bak 생성, try-catch 에러 핸들링 포함
- excludeTemplates: isExcluded() 함수가 정확 일치 + 디렉토리 프리픽스 일치 지원

**회귀 테스트**:
- 기존 플로우: Step 1~8은 "신규 모드 전용" 라벨로 보존, 모드 선택이 Step 0에서 분기
- --mode 없이 실행: cliMode null -> config.mode fallback -> "new" 기본값
- config.json 하위호환: `excludeTemplates = []`, `config.mode || "new"` 기본값 디폴트
- 템플릿 파일 미수정: templates/ 디렉토리는 읽기 전용 참조만 사용

**코드 품질**:
- backupFile: try-catch, mergeClaudeMd: try-catch + 폴백(새 내용 반환), mergeAppend: try-catch + 폴백
- SKILL.md 가독성: 모드별 단계가 "기존 프로젝트 모드 전용" 레이블로 분리
- README.md: 양쪽 모드 플로우, FAQ 5개 항목으로 기존 프로젝트 시나리오 커버
- 변경 범위: skills/opal-project-init/ 내 3개 파일이 핵심. 부수적으로 opal/core/references/skills.md 경로 갱신 + 구 파일 삭제 발생

## 3. 지적 사항

### [Warning] opal/core/references/skills.md 트리거 미갱신

- 심각도: Warning
- SKILL.md의 triggers에 "기존 프로젝트 문서화", "프로젝트 문서 만들어줘", "docs 생성", "프로젝트에 문서 추가" 4개가 추가되었으나, `opal/core/references/skills.md`의 opal-project-init 행에는 여전히 "프로젝트 에이전트 만들어줘"만 표시되어 있다. 또한 description도 구 스킬의 "프로젝트 에이전트 초기화" 설명 그대로이다.
- OPAL 에이전트가 skills.md를 참조하여 스킬을 탐색하므로, 새 트리거가 등록되지 않으면 "기존 프로젝트 문서화" 등의 요청에서 이 스킬이 매칭되지 않을 수 있다.
- 권장: skills.md의 opal-project-init 행에 새 트리거와 갱신된 description을 반영할 것.

### [Info] 스킬 경로 마이그레이션

- 심각도: Info
- 스킬이 `opal/skills/project-init/` (OPAL 내부)에서 `skills/opal-project-init/` (프레임워크 스킬)로 이동되었다. 이는 TASK.md에서 명시하지 않은 추가 구조 변경이지만, CLAUDE.md의 아키텍처("skills/ -- 프레임워크 스킬")에 부합하며 합리적인 정리이다.

## 4. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK.md | SKILL.md Step 0 모드 분기 요구 | Pass -- Step 0에 자동 판별 + 선택지 구현 |
| TASK.md | 자동 분석 대상 (package.json, pyproject.toml 등) | Pass -- Step 0-A에 상세 매핑 테이블 포함 |
| TASK.md | 분석 결과로 플레이스홀더 자동 채움 + 확인/보정 인터뷰 | Pass -- Step 0-B에 프롬프트 템플릿 구현 |
| TASK.md | 기술 스택 불일치 템플릿 자동 제외 | Pass -- Step 6에 필터링 규칙 표 + excludeTemplates 연동 |
| TASK.md | 기존 파일 병합 로직 구체화 | Pass -- SKILL.md Step 7 표 + apply.js mergeClaudeMd/mergeAppend 구현 |
| TASK.md | apply.js --mode existing | Pass -- CLI 파싱, 백업, 병합, 스킵 로직 모두 구현 |
| TASK.md | 기존 파일 백업(.bak) | Pass -- backupFile() 함수 구현 |
| TASK.md | 기존 신규 플로우 유지 | Pass -- mode 기본값 "new", Step 1~8 미변경 |
| TASK.md | 트리거 확장 | Pass (SKILL.md) / Warning (skills.md 레지스트리 미반영) |
| TASK.md | 템플릿 파일 수정 최소화 | Pass -- templates/ 미수정 |
| TASK.md | skills/opal-project-init/ 범위 내 변경 | Pass -- 핵심 변경은 범위 내, 부수적 정리(구 경로 삭제, 레지스트리 갱신)는 합리적 |
| TASK.md | README.md 업데이트 | Pass -- 모드 설명, 트리거, FAQ 모두 갱신 |
| PLAN.md | SKILL.md 구현 계획 2.1 vs 실제 | Pass -- Step 0/0-A/0-B 구조, 자동 추론 테이블, 확인/보정 프롬프트, 필터링 규칙 모두 일치 |
| PLAN.md | apply.js 구현 계획 2.2 vs 실제 | Pass -- --mode CLI, backupFile, mergeClaudeMd, processFile 분기, isExcluded, config 확장 모두 일치 |
| PLAN.md | README.md 구현 계획 2.3 vs 실제 | Pass -- 기존 프로젝트 모드 섹션, 트리거, FAQ 보강 모두 반영 |

## 5. 판정

**Pass**

TASK.md의 모든 요구사항이 SKILL.md, apply.js, README.md에 빠짐없이 구현되었고, PLAN.md의 구현 설계와 실제 코드가 정확히 일치한다. apply.js는 문법 검증을 통과했으며, 기존 신규 모드의 하위호환성이 기본값 처리로 보장된다. `opal/core/references/skills.md`의 트리거 미갱신은 Warning이나, 1건이므로 Pass 판정에 영향 없다. 해당 경고는 별도 수정을 권장한다.
