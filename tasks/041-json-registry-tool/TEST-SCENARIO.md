# TEST SCENARIO: OPAL JSON 레지스트리 + 파싱 도구 개발

> 작성일: 2026-03-29 | 상태: 작성 완료

## 시나리오 목록

### S-1: JSON 레지스트리 파싱 (유효성)

| 항목 | 내용 |
|------|------|
| 대상 | `opal-skills-registry.json`의 JSON 구조 파싱 및 유효성 검증 |
| 조건 | 프로젝트 루트에서 `node opal/tools/skill-registry.js validate` 실행 |
| 기대 결과 | `valid: true` + 23개 스킬 파싱 성공 + 모든 필수 필드(name, type, triggers, paths) 확인 |
| 도구 | node (직접 JSON 파싱) |
| 실행 명령 | _{dtp-test가 채움}_ |
| 결과 | _{dtp-test가 채움: Pass / Fail / Skip}_ |
| 상세 | _{dtp-test가 채움}_ |

### S-2: match — 약어 앞 (//otpds 위치: 입력 앞)

| 항목 | 내용 |
|------|------|
| 대상 | `match()` 함수의 약어 추출 (입력 맨 앞에 위치) |
| 조건 | 입력: `"//otpds 로그인 버그"` |
| 기대 결과 | `found: true, name: "otp-dev-short", type: "otp", alias: "otpds"` |
| 도구 | node (CLI 직접 호출) |
| 실행 명령 | _{dtp-test가 채움}_ |
| 결과 | _{dtp-test가 채움: Pass / Fail / Skip}_ |
| 상세 | _{dtp-test가 채움}_ |

### S-3: match — 약어 뒤 (//otpds 위치: 입력 뒤)

| 항목 | 내용 |
|------|------|
| 대상 | `match()` 함수의 약어 추출 (입력 맨 뒤에 위치) |
| 조건 | 입력: `"로그인 버그 //otpds"` |
| 기대 결과 | `found: true, name: "otp-dev-short", type: "otp", alias: "otpds"` |
| 도구 | node (CLI 직접 호출) |
| 실행 명령 | _{dtp-test가 채움}_ |
| 결과 | _{dtp-test가 채움: Pass / Fail / Skip}_ |
| 상세 | _{dtp-test가 채움}_ |

### S-4: match — 약어 중간 (//otpds 위치: 입력 중간)

| 항목 | 내용 |
|------|------|
| 대상 | `match()` 함수의 약어 추출 (입력 중간에 위치) |
| 조건 | 입력: `"로그인 //otpds 수정"` |
| 기대 결과 | `found: true, name: "otp-dev-short", type: "otp", alias: "otpds"` |
| 도구 | node (CLI 직접 호출) |
| 실행 명령 | _{dtp-test가 채움}_ |
| 결과 | _{dtp-test가 채움: Pass / Fail / Skip}_ |
| 상세 | _{dtp-test가 채움}_ |

### S-5: match — 자연어 (약어 없음, 정규식 트리거 매칭)

| 항목 | 내용 |
|------|------|
| 대상 | `matchByTriggers()` 함수의 자연어 정규식 매칭 |
| 조건 | 입력: `"API 분석해줘"` (약어 없음) |
| 기대 결과 | `found: true, name: "api-analyzer"` (trigger: `(?i)API\s*(분석|명세서|검토)` 매칭) |
| 도구 | node (CLI 직접 호출) |
| 실행 명령 | _{dtp-test가 채움}_ |
| 결과 | _{dtp-test가 채움: Pass / Fail / Skip}_ |
| 상세 | _{dtp-test가 채움}_ |

### S-6: match — 미매칭 (약어도 없고 트리거 매칭 안 됨)

| 항목 | 내용 |
|------|------|
| 대상 | `match()` 함수의 미매칭 처리 |
| 조건 | 입력: `"오늘 날씨 어때"` (어떤 트리거와도 매칭 안 됨) |
| 기대 결과 | `found: false, input: "오늘 날씨 어때"` |
| 도구 | node (CLI 직접 호출) |
| 실행 명령 | _{dtp-test가 채움}_ |
| 결과 | _{dtp-test가 채움: Pass / Fail / Skip}_ |
| 상세 | _{dtp-test가 채움}_ |

### S-7: get — 스킬 존재 (메타데이터 조회)

| 항목 | 내용 |
|------|------|
| 대상 | `get()` 함수의 스킬 메타데이터 조회 (존재하는 스킬) |
| 조건 | 명령: `node skill-registry.js get otp-dev` |
| 기대 결과 | 스킬 객체 전체 반환 (name, type, alias, triggers, paths, domain, pipeline 포함) |
| 도구 | node (CLI 직접 호출) |
| 실행 명령 | _{dtp-test가 채움}_ |
| 결과 | _{dtp-test가 채움: Pass / Fail / Skip}_ |
| 상세 | _{dtp-test가 채움}_ |

### S-8: get — 스킬 미존재 (에러 처리)

| 항목 | 내용 |
|------|------|
| 대상 | `get()` 함수의 에러 처리 (존재하지 않는 스킬) |
| 조건 | 명령: `node skill-registry.js get nonexistent` |
| 기대 결과 | 에러 메시지 + exit code 1 |
| 도구 | node (CLI 직접 호출) |
| 실행 명령 | _{dtp-test가 채움}_ |
| 결과 | _{dtp-test가 채움: Pass / Fail / Skip}_ |
| 상세 | _{dtp-test가 채움}_ |

### S-9: list — 전체 목록 (필터 없음)

| 항목 | 내용 |
|------|------|
| 대상 | `list()` 함수의 전체 스킬 목록 반환 |
| 조건 | 명령: `node skill-registry.js list` |
| 기대 결과 | 23개 스킬의 JSON 배열 반환 (name, type, alias 포함) |
| 도구 | node (CLI 직접 호출) |
| 실행 명령 | _{dtp-test가 채움}_ |
| 결과 | _{dtp-test가 채움: Pass / Fail / Skip}_ |
| 상세 | _{dtp-test가 채움}_ |

### S-10: list — 유형 필터 (--type=otp)

| 항목 | 내용 |
|------|------|
| 대상 | `list()` 함수의 type 필터링 |
| 조건 | 명령: `node skill-registry.js list --type=otp` |
| 기대 결과 | otp 유형의 스킬만 반환 (otp-dev, otp-dev-short, otp-wf, otp-write, otp-write-tech = 5개) |
| 도구 | node (CLI 직접 호출) |
| 실행 명령 | _{dtp-test가 채움}_ |
| 결과 | _{dtp-test가 채움: Pass / Fail / Skip}_ |
| 상세 | _{dtp-test가 채움}_ |

### S-11: list — 도메인 필터 (--domain=dev)

| 항목 | 내용 |
|------|------|
| 대상 | `list()` 함수의 domain 필터링 |
| 조건 | 명령: `node skill-registry.js list --domain=dev` |
| 기대 결과 | domain이 "dev"인 스킬들만 반환 (otp-dev, otp-dev-short, 그 외 dev 도메인 스킬) |
| 도구 | node (CLI 직접 호출) |
| 실행 명령 | _{dtp-test가 채움}_ |
| 결과 | _{dtp-test가 채움: Pass / Fail / Skip}_ |
| 상세 | _{dtp-test가 채움}_ |

### S-12: validate — 정상 레지스트리

| 항목 | 내용 |
|------|------|
| 대상 | `validate()` 함수의 전체 검증 (정상 시나리오) |
| 조건 | 명령: `node skill-registry.js validate` |
| 기대 결과 | `valid: true, errors: [], warnings: []` (모든 검증 통과) |
| 도구 | node (CLI 직접 호출) |
| 실행 명령 | _{dtp-test가 채움}_ |
| 결과 | _{dtp-test가 채움: Pass / Fail / Skip}_ |
| 상세 | _{dtp-test가 채움}_ |

### S-13: validate — 정규식 컴파일 검증

| 항목 | 내용 |
|------|------|
| 대상 | `validate()` 함수의 triggers 정규식 컴파일 검증 |
| 조건 | 명령: `node skill-registry.js validate` (모든 triggers가 유효한 정규식이어야 함) |
| 기대 결과 | 모든 triggers의 정규식이 정상 컴파일됨 (에러 없음) |
| 도구 | node (CLI 직접 호출) |
| 실행 명령 | _{dtp-test가 채움}_ |
| 결과 | _{dtp-test가 채움: Pass / Fail / Skip}_ |
| 상세 | _{dtp-test가 채움}_ |

### S-14: validate — 경로 존재 확인

| 항목 | 내용 |
|------|------|
| 대상 | `validate()` 함수의 paths 존재 여부 검증 (~ 확장 후 fs.existsSync) |
| 조건 | 명령: `node skill-registry.js validate` (모든 paths의 SKILL.md가 존재해야 함) |
| 기대 결과 | 존재하지 않는 경로가 있으면 warnings에 포함 (errors 아님, 선택사항) |
| 도구 | node (CLI 직접 호출) |
| 실행 명령 | _{dtp-test가 채움}_ |
| 결과 | _{dtp-test가 채움: Pass / Fail / Skip}_ |
| 상세 | _{dtp-test가 채움}_ |

### S-15: validate — alias 중복 검증

| 항목 | 내용 |
|------|------|
| 대상 | `validate()` 함수의 alias 중복 검증 |
| 조건 | 명령: `node skill-registry.js validate` |
| 기대 결과 | 중복된 alias가 있으면 errors에 포함 (exit code 1) |
| 도구 | node (CLI 직접 호출) |
| 실행 명령 | _{dtp-test가 채움}_ |
| 결과 | _{dtp-test가 채움: Pass / Fail / Skip}_ |
| 상세 | _{dtp-test가 채움}_ |

### S-16: validate — name 중복 검증

| 항목 | 내용 |
|------|------|
| 대상 | `validate()` 함수의 name 중복 검증 |
| 조건 | 명령: `node skill-registry.js validate` |
| 기대 결과 | 중복된 name이 있으면 errors에 포함 (exit code 1) |
| 도구 | node (CLI 직접 호출) |
| 실행 명령 | _{dtp-test가 채움}_ |
| 결과 | _{dtp-test가 채움: Pass / Fail / Skip}_ |
| 상세 | _{dtp-test가 채움}_ |

### S-17: check-env.js 실행 (정상 Node.js 환경)

| 항목 | 내용 |
|------|------|
| 대상 | `check-env.js` 모듈의 Node.js 버전 확인 |
| 조건 | 명령: `node opal/tools/check-env.js` (Node.js v18+가 설치되어 있음) |
| 기대 결과 | `{ "node": true, "version": "v2x.x.x" }` 형식으로 JSON 반환 + exit code 0 |
| 도구 | node (CLI 직접 호출) |
| 실행 명령 | _{dtp-test가 채움}_ |
| 결과 | _{dtp-test가 채움: Pass / Fail / Skip}_ |
| 상세 | _{dtp-test가 채움}_ |

### S-18: check-env.js 버전 확인 (최소 v18)

| 항목 | 내용 |
|------|------|
| 대상 | `check-env.js`의 Node.js 버전 확인 (최소 v18 검증) |
| 조건 | Node.js v18 이상이 설치되어 있음 |
| 기대 결과 | 버전이 v18 이상이면 `{ "node": true }` + exit code 0 |
| 도구 | node (CLI 직접 호출) |
| 실행 명령 | _{dtp-test가 채움}_ |
| 결과 | _{dtp-test가 채움: Pass / Fail / Skip}_ |
| 상세 | _{dtp-test가 채움}_ |

### S-19: install-mac.sh 배포 (tools 디렉토리)

| 항목 | 내용 |
|------|------|
| 대상 | `install-mac.sh`의 `opal/tools/` → `~/.opal/tools/` 배포 로직 |
| 조건 | 명령: `./scripts/install-mac.sh` 실행 |
| 기대 결과 | `~/.opal/tools/` 디렉토리에 3개 파일 생성 (opal-skills-registry.json, skill-registry.js, check-env.js) |
| 도구 | bash (install-mac.sh 직접 실행) |
| 실행 명령 | _{dtp-test가 채움}_ |
| 결과 | _{dtp-test가 채움: Pass / Fail / Skip}_ |
| 상세 | _{dtp-test가 채움}_ |

### S-20: install-mac.sh 기존 기능 회귀 (skills 배포)

| 항목 | 내용 |
|------|------|
| 대상 | `install-mac.sh`의 기존 `opal/skills/` 배포 로직이 정상 동작하는지 회귀 테스트 |
| 조건 | 명령: `./scripts/install-mac.sh` 실행 후 `~/.opal/skills/` 확인 |
| 기대 결과 | `~/.opal/skills/` 디렉토리에 기존 스킬들(dev-task-pilot, api-analyzer, opal-onboarding 등)이 정상 배포됨 |
| 도구 | bash (install-mac.sh 직접 실행) |
| 실행 명령 | _{dtp-test가 채움}_ |
| 결과 | _{dtp-test가 채움: Pass / Fail / Skip}_ |
| 상세 | _{dtp-test가 채움}_ |

### S-21: install-mac.sh 기존 기능 회귀 (agents 배포)

| 항목 | 내용 |
|------|------|
| 대상 | `install-mac.sh`의 기존 `opal/agents/` 배포 로직이 정상 동작하는지 회귀 테스트 |
| 조건 | 명령: `./scripts/install-mac.sh` 실행 후 `~/.opal/agents/` 확인 |
| 기대 결과 | `~/.opal/agents/` 디렉토리에 기존 에이전트들(dtp-worker, dtp-qa-worker 등)이 정상 배포됨 |
| 도구 | bash (install-mac.sh 직접 실행) |
| 실행 명령 | _{dtp-test가 채움}_ |
| 결과 | _{dtp-test가 채움: Pass / Fail / Skip}_ |
| 상세 | _{dtp-test가 채움}_ |

### S-22: install-mac.sh 기존 기능 회귀 (MCP 설정)

| 항목 | 내용 |
|------|------|
| 대상 | `install-mac.sh`의 기존 MCP 설정 배포 로직이 정상 동작하는지 회귀 테스트 |
| 조건 | 명령: `./scripts/install-mac.sh` 실행 후 `~/.claude/.claude.json` 확인 |
| 기대 결과 | MCP 서버 설정이 정상 배포됨 (gitleaks, context7, Notion 등) |
| 도구 | bash (install-mac.sh 직접 실행) |
| 실행 명령 | _{dtp-test가 채움}_ |
| 결과 | _{dtp-test가 채움: Pass / Fail / Skip}_ |
| 상세 | _{dtp-test가 채움}_ |

### S-23: UTF-8 한글 처리 (match 명령)

| 항목 | 내용 |
|------|------|
| 대상 | Node.js의 UTF-8 한글 문자 정규식 처리 |
| 조건 | 입력: `"API 분석해줘"` (한글 포함 자연어) |
| 기대 결과 | 한글 문자가 정상 매칭되어 `found: true` 반환 (정규식: `(?i)API\s*(분석|명세서|검토)`) |
| 도구 | node (CLI 직접 호출) |
| 실행 명령 | _{dtp-test가 채움}_ |
| 결과 | _{dtp-test가 채움: Pass / Fail / Skip}_ |
| 상세 | _{dtp-test가 채움}_ |

## 코드 품질

| # | 검사 | 도구 | 결과 | 상세 |
|---|------|------|------|------|
| 1 | 외부 패키지 미사용 (내장 모듈만) | grep | _{dtp-test가 채움}_ | _{dtp-test가 채움}_ |
| 2 | require 검사 (fs, path, process만) | grep | _{dtp-test가 채움}_ | _{dtp-test가 채움}_ |
| 3 | shebang 포함 (#!/usr/bin/env node) | grep | _{dtp-test가 채움}_ | _{dtp-test가 채움}_ |

## 보안

| # | 항목 | 결과 | 상세 |
|---|------|------|------|
| 1 | 하드코딩 시크릿 스캔 (gitleaks) | _{dtp-test가 채움}_ | _{dtp-test가 채움}_ |
| 2 | .gitignore 확인 (.env, *.key 포함) | _{dtp-test가 채움}_ | _{dtp-test가 채움}_ |

## 회귀 테스트

| # | 테스트 스위트 | 결과 | 상세 |
|---|-------------|------|------|
| 1 | skills.md 내용 변경 없음 (마크다운 유지 확인) | _{dtp-test가 채움}_ | _{dtp-test가 채움}_ |
| 2 | skill-guide.md 내용 변경 없음 (마크다운 유지 확인) | _{dtp-test가 채움}_ | _{dtp-test가 채움}_ |

## 판정

**_{dtp-test가 채움: All Pass / Partial Fail / Critical Fail}_ -- _{판정 근거}_**

## 설계 피드백

### 발견 사항

#### 1. JSON 스키마 필드 명확화 필요
PLAN에서 dtp 스킬의 `dispatched_by` 필드가 정의되었으나, 현재 스킬 레지스트리의 실제 구조에서 이 필드가 필요한지 재검토 필요. dtp-test-scenario 자체는 오케스트레이터 디스패치만 되므로, `dispatched_by: ["dtp-dev", "dtp-dev-short"]` 형태로 기재하는 것이 향후 도구 활용성을 높일 것 같음.

#### 2. 자동화 기회: JSON ↔ skills.md 검증
현재 PLAN에서 "이중 관리" 리스크가 명시됨. 향후 validate 명령에 skills.md와 JSON의 스킬 수 비교 경고 기능을 추가하면 누락 방지 가능.

#### 3. Windows 경로 호환성
PLAN의 리스크에서 Windows 경로 호환성 언급됨. 현재 설계에서 `~` 확장을 fs 모듈의 `homedir()` 사용 + `path.join()`으로 OS 무관 처리해야 함. 테스트 환경이 macOS이지만, 향후 Windows 개발자를 위해 경로 처리 로직이 중요.

### 추가 고려 사항

#### 설계 검증 양호
- TASK, PLAN의 요구사항이 명확하고, 테스트 시나리오 도출이 원활함
- JSON 스키마, CLI 인터페이스, 환경 체크 로직의 범위가 잘 정의됨
- TODO 단계 없이 PLAN에서 직접 EXECUTE 가능할 수 있을 정도로 설계 완성도 높음

#### 빈틈 없음
테스트 시나리오 도출 과정에서 PLAN/TASK의 빈틈은 발견되지 않음. 모든 요구사항에 대응하는 시나리오 존재.
