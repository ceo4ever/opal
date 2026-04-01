# PLAN: 테스트 도구 레지스트리 설계 및 TEST-SCENARIO 통합

> 작성일: 2026-03-19 | 모드: Short Task | 참조: TASK.md

---

## 1. 코드 분석

### 관련 파일

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| `skills/task-flow/references/test-scenario-guide.md` | TEST-SCENARIO.md 작성 가이드 (task-flow-agent 담당 필드 정의) | Y — 도구 결정 흐름 추가 |
| `agents/claude/task-flow-test/AGENT.md` | EXECUTE 완료 후 테스트 실행 에이전트 정의 | Y — Step 1 환경 확인에 레지스트리 참조 추가 |
| `.opal/test-tools.yaml` (신규) | 프로젝트 루트 기준 테스트 도구 레지스트리 | Y — 신규 생성 (스키마 설계) |

### 현재 구현

**test-scenario-guide.md 현재 흐름:**

```
Step 1: 컨텍스트 확인 (PLAN/TODO에서 변경 파일, 설계, QA 체크리스트 파악)
Step 2: 시나리오 도출 (기능/에지케이스/통합)
Step 3: 시나리오 작성 (대상/조건/기대 결과만 — 도구는 task-flow-test가 채움)
Step 4: 문서 전용 태스크 확인
Step 5: 설계 검증
```

TEST-SCENARIO.md 템플릿의 "도구" 필드는 `_{task-flow-test가 채움}_` 으로 비워두는 구조다. task-flow-agent는 도구를 결정하지 않고, task-flow-test가 EXECUTE 완료 후 런타임에 즉석 결정한다.

**task-flow-test AGENT.md Step 1 현재 흐름:**

```
Step 1: TEST-SCENARIO.md 읽기 + 테스트 환경 확인
  1. 시나리오 목록 파악
  2. 테스트 도구 설치 여부 확인 (프로젝트 설정 파일 기반) ← 기준 모호
  3. 실행 가능 상태 검증
  4. 환경 문제 시 TEST-SCENARIO.md에 기록
```

Step 2에서 "도구 결정"을 시나리오 대상/조건 분석 기반으로 임의 수행한다. 레지스트리 참조 없이 즉석 결정하므로 프로젝트 미설치 도구를 선택하거나 카테고리별 기본 도구가 불일치할 수 있다.

**현재 문제점 요약:**

1. 도구 결정 시점이 EXECUTE 완료 후(task-flow-test)여서 TEST-SCENARIO 작성 시점에 도구 불명확
2. "프로젝트 설정 파일 기반"이라는 표현이 추상적 — 무엇을 보는지 정의 없음
3. 프로젝트마다 가용 도구가 달라도 통합 관리 수단 없음
4. 도구 미설치 발견이 테스트 실행 직전 → 지연 발생

### 영향 범위

**test-scenario-guide.md 변경 영향:**
- 호출자: task-flow SKILL.md (TEST-SCENARIO 작성 시점 안내), task-flow-agent AGENT.md
- 피호출자: TEST-SCENARIO.md 템플릿 (구조 변경 여부 결정 필요)
- 하위 호환: 기존 TEST-SCENARIO.md 구조는 유지해야 함 (TASK.md 제약)

**task-flow-test AGENT.md 변경 영향:**
- Step 1만 변경 — 나머지 Step(2~6) 로직은 그대로 유지
- 도구 결정 흐름이 레지스트리 → 시나리오 매핑으로 명확해짐

**.opal/test-tools.yaml 신규 영향:**
- 프로젝트 루트 기준 파일이므로, 프레임워크 내 example/template만 제공
- 실제 파일은 각 프로젝트가 생성 (task-flow-test가 없을 경우 fallback 처리 필요)

---

## 2. 구현 계획

### 변경 파일

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| 1 | `opal/core/references/` 하위 `test-tools-schema.yaml` (신규) | `.opal/test-tools.yaml` 스키마 레퍼런스 (전체 필드 설명 포함) |
| 2 | `opal/templates/test-tools.yaml` (신규) | 프로젝트 초기화 시 복사할 예시 파일 (글로벌 기본값 + 오버라이드 구조) |
| 3 | `skills/task-flow/references/test-scenario-guide.md` | Step 1에 레지스트리 참조 단계 추가, Step 3 템플릿 "도구" 필드 힌트 개선 |
| 4 | `agents/claude/task-flow-test/AGENT.md` | Step 1 환경 확인에 `.opal/test-tools.yaml` 참조 로직 추가 + 자동 설치 흐름 명시 |

### 핵심 설계

#### `.opal/test-tools.yaml` 스키마

```yaml
# .opal/test-tools.yaml
# 프로젝트 루트 기준. 없으면 task-flow-test가 프로젝트 설정 기반으로 추론 (fallback).

version: "1.0"

# 스택 선언 — 도구 카테고리 자동 추론에 사용
stack:
  language: typescript       # typescript | python | go | java | ...
  framework: nextjs          # nextjs | express | fastapi | ...
  runtime: node              # node | bun | deno | ...

# 전역 도구 (스택 무관 필수 — 항상 실행)
global:
  - name: gitleaks
    purpose: 하드코딩 시크릿 스캔 (보안)
    category: security
    check: "gitleaks version"
    install:
      mac: "brew install gitleaks"
      windows: "choco install gitleaks"
      linux: "curl -sSfL https://github.com/gitleaks/gitleaks/releases/latest/download/gitleaks_linux_amd64.tar.gz | tar -xz"
    install_fallback: "https://github.com/gitleaks/gitleaks/releases"
    required: true

# 카테고리별 도구 (스택별 선택 — stack 선언에 따라 활성화)
tools:
  unit:
    - name: vitest
      purpose: 단위 테스트
      check: "npx vitest --version"
      install: "npm install -D vitest"
      required: true

  e2e:
    - name: playwright
      purpose: E2E 브라우저 테스트
      check: "npx playwright --version"
      install: "npm install -D @playwright/test && npx playwright install"
      required: false

  lint:
    - name: eslint
      purpose: JavaScript/TypeScript 린트
      check: "npx eslint --version"
      install: "npm install -D eslint"
      required: true

  typecheck:
    - name: tsc
      purpose: TypeScript 타입 체크
      check: "npx tsc --version"
      install: "npm install -D typescript"
      required: true

  format:
    - name: prettier
      purpose: 코드 포맷터
      check: "npx prettier --version"
      install: "npm install -D prettier"
      required: false
```

**글로벌 기본값 + 프로젝트 오버라이드 구조:**
- 글로벌 기본 템플릿: `~/.opal/templates/test-tools.yaml` (설치 시 배포)
- 프로젝트별 오버라이드: `{project}/.opal/test-tools.yaml`
- task-flow-test는 프로젝트 파일 우선, 없으면 글로벌 기본값 사용, 둘 다 없으면 추론 fallback

#### `test-scenario-guide.md` 변경 포인트

**Step 1 뒤에 "Step 1-b: 도구 사전 확인" 추가:**

```
Step 1-b: 도구 사전 확인 (NEW)
  1. {project}/.opal/test-tools.yaml 존재 여부 확인
  2. 있으면: stack 및 tools 섹션을 읽어 사용 가능한 도구 목록 파악
  3. 없으면: 프로젝트 설정 파일(package.json, pyproject.toml 등)에서 추론
  4. 시나리오 유형 → 도구 매핑 테이블에 따라 각 시나리오에 사용할 도구 결정
  5. TEST-SCENARIO.md의 "도구" 필드에 결정된 도구를 사전 기입 (task-flow-agent가 채움)
```

**시나리오 유형 → 도구 매핑 테이블 (가이드에 추가):**

| 시나리오 유형 | 대응 카테고리 | 예시 도구 (TypeScript) |
|-------------|------------|----------------------|
| 함수/클래스 단위 검증 | unit | vitest, jest |
| API 엔드포인트 검증 | e2e 또는 unit | playwright, supertest |
| 브라우저 UI 검증 | e2e | playwright |
| 린트/포맷 | lint, format | eslint, prettier |
| 타입 안전성 | typecheck | tsc |
| 시크릿/보안 | security | gitleaks |

**TEST-SCENARIO.md 템플릿 "도구" 필드 변경:**
- 기존: `| 도구 | _{task-flow-test가 채움}_ |`
- 변경: `| 도구 | {task-flow-agent가 결정 / task-flow-test가 검증} |`
- 의미: 사전 결정이 있으면 기입, task-flow-test는 재검증하거나 설치 확인

#### `task-flow-test` AGENT.md Step 1 변경 포인트

```
Step 1: TEST-SCENARIO.md 읽기 + 테스트 환경 확인

  [추가] 1-a. .opal/test-tools.yaml 로드
    - {project}/.opal/test-tools.yaml 존재 확인
    - 있으면 레지스트리 로드; 없으면 package.json/pyproject.toml 기반 추론 fallback

  [추가] 1-b. 도구 설치 여부 확인 (레지스트리 기반)
    - 레지스트리의 각 도구에 대해 check 명령 실행
    - required: true 도구 미설치 시:
      - install 필드가 플랫폼 맵(mac/windows/linux)이면 현재 OS 감지 후 해당 플랫폼 명령 선택
        (OS 감지: `uname -s` → Darwin→mac, Linux→linux; Windows는 $env:OS 확인→windows)
      - install 필드가 단일 문자열이면 그대로 사용 (npm/pip 등 크로스플랫폼 도구)
      - 플랫폼 키 미존재 시 install_fallback URL 제시
      - 선택된 install 명령을 사용자에게 제안 후 확인 요청
    - required: false 도구 미설치 시 → 해당 시나리오 Skip 처리

  [기존 유지] 1-c. 실행 가능 상태 검증 (의존성 설치, 빌드 성공 등)
  [기존 유지] 1-d. 환경 문제 발견 시 TEST-SCENARIO.md에 기록
```

**자동 설치 흐름 명시:**
- required 도구 미설치: 사용자에게 `install` 명령 제시 → 승인 후 실행 → 재확인
- 사용자 미승인: 해당 시나리오를 "환경 미준비 — Skip"으로 기록 후 계속 진행

---

## 3. 실행 체크리스트

- [x] Step 1: 스키마 설계 — `opal/templates/test-tools.yaml` 신규 생성 — 글로벌 기본값 + 프로젝트 오버라이드 구조로 전체 스키마 작성 (stack, global, tools 섹션)
- [x] Step 2: 가이드 개선 — `skills/task-flow/references/test-scenario-guide.md` 수정 — Step 1-b 추가, 시나리오 유형→도구 매핑 테이블 추가, 템플릿 "도구" 필드를 task-flow-agent가 작성하도록 변경 (기존 `_{task-flow-test가 채움}_` → `{task-flow-agent가 결정 / task-flow-test가 검증}`)
- [x] Step 3: 에이전트 개선 — `agents/claude/task-flow-test/AGENT.md` 수정 — Step 1에 레지스트리 로드·설치 확인·자동 설치 흐름 추가
- [x] Step 4: 스키마 레퍼런스 — `opal/core/references/` 하위 또는 적절한 위치에 스키마 필드 설명 문서 작성 (각 필드의 의미, 유효값, 필수 여부)

> Step 수: 4개 (5개 이하 기준 충족)

---

## 4. QA 체크리스트

### 기능 테스트

- [x] `test-tools.yaml`에 `stack: typescript`를 선언했을 때, 가이드의 도구 매핑 테이블이 올바른 도구를 안내하는가
- [x] `required: true` 도구 미설치 시나리오에서 task-flow-test AGENT.md가 사용자 확인 후 설치 흐름을 따르는가
- [x] `required: false` 도구 미설치 시 해당 시나리오를 Skip 처리하도록 가이드되어 있는가
- [x] `test-tools.yaml` 없을 때 fallback 로직(package.json/pyproject.toml 추론)이 명시되어 있는가
- [x] TEST-SCENARIO.md 템플릿의 "도구" 필드가 task-flow-agent 작성 영역으로 변경되어 있는가

### 회귀 테스트

- [x] 기존 TEST-SCENARIO.md 템플릿 구조(S-N 형식, 코드 품질/보안/회귀/판정 섹션)가 유지되는가
- [x] task-flow-test AGENT.md의 Step 2~6 로직에 변경이 없는가
- [x] test-scenario-guide.md의 기존 Step 2~5 프로세스(시나리오 도출, 작성, 문서 확인, 설계 검증)가 유지되는가
- [x] 문서 전용 태스크(`.md` 파일만 변경) 처리 규칙이 그대로인가

### 코드 품질

- [x] `test-tools.yaml` 스키마의 필드명이 kebab-case 규칙을 따르는가 (예: `required`, `check`, `install`)
- [x] 가이드 내 도구 매핑 테이블이 문서 표준(마크다운 테이블)을 준수하는가
- [x] AGENT.md의 Step 번호 체계가 기존 1~6 패턴과 일관성을 유지하는가 (1-a, 1-b 서브스텝 사용)

---

## 변경이력

| 버전 | 날짜 | 작성자 | 변경내용 |
|------|------|--------|---------|
| v1.0 | 2026-03-19 | task-flow-agent | 최초 작성 |
| v1.1 | 2026-03-19 | task-flow-agent | QA Warning 반영: gitleaks tools.security 중복 제거(global에만 유지), install 필드 플랫폼별 맵 구조로 변경, Step 2 체크리스트에 도구 필드 변경 내용 명시, task-flow-test Step 1-b에 OS 감지 로직 추가 |
