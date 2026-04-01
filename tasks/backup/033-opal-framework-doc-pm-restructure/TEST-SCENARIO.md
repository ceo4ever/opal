# TEST SCENARIO: OPAL 프레임워크 문서 구조 + PM 역할 재설계

> 작성일: 2026-03-27 | 상태: 작성 완료

## 시나리오 목록

### S-1: 플랫폼 템플릿 경량화 — CLAUDE.md 구조

| 항목 | 내용 |
|------|------|
| 대상 | `skills/opal-project-init/templates/common/platform/CLAUDE.md` 파일이 부트스트래퍼만 포함하는가 (R1) |
| 조건 | PLAN.md M1 변경사항 적용 후 파일 내용 |
| 기대 결과 | 파일 내용이 OPAL START/END 마커만 포함하고, 프로젝트 정보/기술 스택/docs 참조/코드 컨벤션은 제거됨. 약 10줄 |
| 도구 | manual document inspection |
| 실행 명령 | _{dtp-test가 채움}_ |
| 결과 | _{dtp-test가 채움: Pass / Fail / Skip}_ |
| 상세 | _{dtp-test가 채움}_ |

### S-2: 플랫폼 템플릿 경량화 — GEMINI.md, .cursorrules

| 항목 | 내용 |
|------|------|
| 대상 | `templates/common/platform/GEMINI.md`, `.cursorrules` 파일이 부트스트래퍼만 포함하는가 (R1) |
| 조건 | PLAN.md M2, M3 변경사항 적용 후 파일 내용 |
| 기대 결과 | GEMINI.md: OPAL 부트스트래퍼만 (약 10줄). .cursorrules: Cursor frontmatter 유지 + OPAL 부트스트래퍼 (약 12줄). 프로젝트 정보 모두 제거됨 |
| 도구 | manual document inspection |
| 실행 명령 | _{dtp-test가 채움}_ |
| 결과 | _{dtp-test가 채움: Pass / Fail / Skip}_ |
| 상세 | _{dtp-test가 채움}_ |

### S-3: apply.js 역할 축소 — 플랫폼 파일만 처리

| 항목 | 내용 |
|------|------|
| 대상 | `skills/opal-project-init/scripts/apply.js`가 PLATFORM_FILES (CLAUDE.md, GEMINI.md, .cursorrules)만 처리하는가 (R7, M9) |
| 조건 | apply.js 실행 후 생성된 파일 목록 확인. 테스트: 임시 디렉토리에서 스크립트 실행 |
| 기대 결과 | PLATFORM_FILES 3개만 생성됨. 기존 COMMON_DOCS (docs/server, docs/client), OPAL_FILES (AGENT.md, MEMORY.md) 로직 제거됨 |
| 도구 | node (단위 테스트) |
| 실행 명령 | _{dtp-test가 채움}_ |
| 결과 | _{dtp-test가 채움: Pass / Fail / Skip}_ |
| 상세 | _{dtp-test가 채움}_ |

### S-4: docs 작성 가이드 — PROJECT.md, CONVENTIONS.md 포함

| 항목 | 내용 |
|------|------|
| 대상 | `skills/opal-project-init/references/docs-guide.md`가 모든 문서 타입의 구조를 정의하는가 (R2, R3, R7, N1) |
| 조건 | N1 가이드 생성 후 docs-guide.md 내용 |
| 기대 결과 | 파일이 포함: PROJECT.md (프로젝트 정의 SSOT, 문서 레지스트리), CONVENTIONS.md (코드 컨벤션), ARCHITECTURE.md, BACKEND.md, FRONTEND.md. 각 문서의 필수 섹션이 명시됨 |
| 도구 | manual document inspection |
| 실행 명령 | _{dtp-test가 채움}_ |
| 결과 | _{dtp-test가 채움: Pass / Fail / Skip}_ |
| 상세 | _{dtp-test가 채움}_ |

### S-5: AGENT.md 작성 가이드 — PM 역할 + 검토 기준

| 항목 | 내용 |
|------|------|
| 대상 | `skills/opal-project-init/references/agent-guide.md`가 PM 역할 정의 템플릿을 포함하는가 (R4, R8, N2) |
| 조건 | N2 가이드 생성 후 agent-guide.md 내용 |
| 기대 결과 | 파일이 포함: PM 전문 역할 (도메인 전문가 예시), PM 검토 기준 (필수/도메인 체크리스트), 업무 수행 지침 (참조 문서 전달 의무), 도메인 지식 (용어 테이블), 금지사항, 확정 기준 (반복 원칙 누적 공간) |
| 도구 | manual document inspection |
| 실행 명령 | _{dtp-test가 채움}_ |
| 결과 | _{dtp-test가 채움: Pass / Fail / Skip}_ |
| 상세 | _{dtp-test가 채움}_ |

### S-6: opi SKILL.md 전면 재설계 — 초기화 모드

| 항목 | 내용 |
|------|------|
| 대상 | `skills/opal-project-init/SKILL.md`의 초기화 모드 프로세스가 4 Phase (이해 → 공통 문서 → 개발 문서 → 플랫폼 파일)로 정의되는가 (R7, M8) |
| 조건 | SKILL.md 초기화 모드 섹션 내용 |
| 기대 결과 | Phase 1: 분석 + 대화 (프로젝트명, 도메인, Phase, PM 전문 역할, 추가 문서). Phase 2: PROJECT.md, AGENT.md, MEMORY.md 작성 + 검토. Phase 3: 개발 프로젝트 추가 문서 (ARCHITECTURE, CONVENTIONS, BACKEND, FRONTEND). Phase 4: 플랫폼 파일 생성. 각 Phase가 명확함 |
| 도구 | manual document inspection |
| 실행 명령 | _{dtp-test가 채움}_ |
| 결과 | _{dtp-test가 채움: Pass / Fail / Skip}_ |
| 상세 | _{dtp-test가 채움}_ |

### S-7: opi SKILL.md 전면 재설계 — 최신화 모드

| 항목 | 내용 |
|------|------|
| 대상 | `skills/opal-project-init/SKILL.md`의 최신화 모드 프로세스가 4 Phase (현재 상태 분석 → 유형별 분석 → 변경 사항 정리 → 플랫폼 파일 갱신)로 정의되는가 (R7, M8) |
| 조건 | SKILL.md 최신화 모드 섹션 내용 |
| 기대 결과 | Phase 1: 기존 AGENT.md, docs/ 전체 Read. Phase 2: 개발 프로젝트(코드 분석, 변경 감지) vs 일반 프로젝트(문서 정리 점검) 분기. Phase 3: 캡틴에게 변경 사항 보고 + 미등록 문서 인터뷰. Phase 4: 승인 후 해당 문서만 업데이트. 프로세스가 명확함 |
| 도구 | manual document inspection |
| 실행 명령 | _{dtp-test가 채움}_ |
| 결과 | _{dtp-test가 채움: Pass / Fail / Skip}_ |
| 상세 | _{dtp-test가 채움}_ |

### S-8: 글로벌 AGENT.md — PM 컨텍스트 로드 절차

| 항목 | 내용 |
|------|------|
| 대상 | `opal/core/AGENT.md`의 부트스트랩 절차에 "PM 컨텍스트 로드" 단계가 4단계 후에 추가되는가 (R5, M5) |
| 조건 | AGENT.md 부트스트랩 섹션 |
| 기대 결과 | 5단계: {프로젝트}/.opal/AGENT.md가 존재하면 Read하여 PM 역할 활성화. docs/PROJECT.md, docs/CONVENTIONS.md도 Read (존재 시). PM 전문 역할, 검토 기준, 업무 지침, 확정 기준이 세션 컨텍스트에 로드됨. 기존 5~7단계가 6~8로 시프트 |
| 도구 | manual document inspection |
| 실행 명령 | _{dtp-test가 채움}_ |
| 결과 | _{dtp-test가 채움: Pass / Fail / Skip}_ |
| 상세 | _{dtp-test가 채움}_ |

### S-9: 글로벌 AGENT.md — PM 학습 루프

| 항목 | 내용 |
|------|------|
| 대상 | `opal/core/AGENT.md`에 "PM 학습 루프" 행동 규칙이 추가되는가 (R8, M5) |
| 조건 | AGENT.md 행동 규칙 섹션 |
| 기대 결과 | "PM 학습 루프" 섹션 추가. 내용: 질문 프로토콜 (선택지와 영향 정리), 답변 분류 (반복 원칙 vs 일회성), 자동 적용 (다음 세션에서 확정 기준 자동 로드). .opal/AGENT.md의 "확정 기준" 섹션 참조 |
| 도구 | manual document inspection |
| 실행 명령 | _{dtp-test가 채움}_ |
| 결과 | _{dtp-test가 채움: Pass / Fail / Skip}_ |
| 상세 | _{dtp-test가 채움}_ |

### S-10: otp-dev 변경 — TASK 단계 + 디스패치 + PM 게이트

| 항목 | 내용 |
|------|------|
| 대상 | `skills/otp-dev/SKILL.md`에 4가지 변경사항이 포함되는가 (R6, M6) |
| 조건 | SKILL.md 내용 |
| 기대 결과 | 변경 1: TASK 단계에서 docs/PROJECT.md 및 .opal/AGENT.md 읽어 프로젝트 컨텍스트 반영. 변경 2: 디스패치 프롬프트가 `docs/PROJECT.md` + 관련 문서 (CONVENTIONS.md 등) 참조로 전환. 변경 3: 워커 완료 후 PM 검토 게이트 (관련 문서 전달 확인 → 검토 기준 체크 → TASK 정합성 → Pass/Fail 판정). 변경 4: EXECUTE 완료 후 새 문서 생성 시 캡틴에게 확인 → PROJECT.md 테이블 등록. 모두 포함됨 |
| 도구 | manual document inspection |
| 실행 명령 | _{dtp-test가 채움}_ |
| 결과 | _{dtp-test가 채움: Pass / Fail / Skip}_ |
| 상세 | _{dtp-test가 채움}_ |

### S-11: otp-dev-short 변경 — otp-dev와 동일

| 항목 | 내용 |
|------|------|
| 대상 | `skills/otp-dev-short/SKILL.md`가 otp-dev와 동일한 4가지 변경사항을 포함하는가 (R6, M7) |
| 조건 | SKILL.md 내용 |
| 기대 결과 | S-10과 동일한 4가지 변경사항: TASK 컨텍스트 반영, 디스패치 변경, PM 검토 게이트, 문서 등록 확인. Short Task에 맞게 조정됨 |
| 도구 | manual document inspection |
| 실행 명령 | _{dtp-test가 채움}_ |
| 결과 | _{dtp-test가 채움: Pass / Fail / Skip}_ |
| 상세 | _{dtp-test가 채움}_ |

### S-12: 기존 템플릿 삭제 — docs/, opal/, web/, ai-agent/, optional/

| 항목 | 내용 |
|------|------|
| 대상 | `templates/common/docs/*`, `templates/common/opal/AGENT.md`, `MEMORY.md`, `templates/web/`, `templates/ai-agent/`, `templates/optional/` 디렉토리/파일이 삭제되는가 (R7, D1~D6) |
| 조건 | PLAN.md 삭제 목록 (D1~D6) 적용 후 파일 시스템 |
| 기대 결과 | 지정된 모든 파일/디렉토리 미존재. apply.js 실행 시 에러 없음 |
| 도구 | manual file system inspection |
| 실행 명령 | _{dtp-test가 채움}_ |
| 결과 | _{dtp-test가 채움: Pass / Fail / Skip}_ |
| 상세 | _{dtp-test가 채움}_ |

### S-13: 문서 일관성 — PLAN vs 실제 문서

| 항목 | 내용 |
|------|------|
| 대상 | PLAN.md의 설계 설명과 실제 생성된 docs-guide.md, agent-guide.md 내용이 일치하는가 |
| 조건 | PLAN.md "N1/N2" 섹션과 docs-guide.md, agent-guide.md 내용 비교 |
| 기대 결과 | 문서 구조, 섹션, 예시가 PLAN의 설명과 일치. 오타/누락 없음 |
| 도구 | manual document inspection |
| 실행 명령 | _{dtp-test가 채움}_ |
| 결과 | _{dtp-test가 채움: Pass / Fail / Skip}_ |
| 상세 | _{dtp-test가 채움}_ |

### S-14: 회귀 테스트 — 기존 프로젝트 호환성 (OPAL 마커 병합)

| 항목 | 내용 |
|------|------|
| 대상 | 기존 CLAUDE.md에 OPAL 마커가 있을 때 apply.js 병합이 깨지지 않는가 (회귀) |
| 조건 | 테스트 시나리오: 기존 CLAUDE.md에 `# === OPAL START ===` 마커 있음 → apply.js 실행 |
| 기대 결과 | 기존 내용 유지, 새 부트스트래퍼로 교체됨. 파일 손상 없음. OPAL 마커 정합성 유지 |
| 도구 | node (단위 테스트) |
| 실행 명령 | _{dtp-test가 채움}_ |
| 결과 | _{dtp-test가 채움: Pass / Fail / Skip}_ |
| 상세 | _{dtp-test가 채움}_ |

### S-15: 에지 케이스 — docs/PROJECT.md 없을 때 otp 폴백

| 항목 | 내용 |
|------|------|
| 대상 | otp-dev, otp-dev-short가 docs/PROJECT.md 미존재 시 폴백 동작하는가 (하위 호환) |
| 조건 | 프로젝트에 .opal/AGENT.md는 있지만 docs/PROJECT.md 없음 |
| 기대 결과 | CLAUDE.md 폴백 참조 (R6 설명: "docs/ 미존재 시 CLAUDE.md 폴백"). 에러 없음 |
| 도구 | manual document inspection + 시뮬레이션 |
| 실행 명령 | _{dtp-test가 채움}_ |
| 결과 | _{dtp-test가 채움: Pass / Fail / Skip}_ |
| 상세 | _{dtp-test가 채움}_ |

## 코드 품질

| # | 검사 | 도구 | 결과 | 상세 |
|---|------|------|------|------|
| 1 | 마크다운 린트 | markdownlint | _{채움}_ | _{채움}_ |
| 2 | 문서 구조 일관성 | manual inspection | _{채움}_ | _{채움}_ |
| 3 | apply.js 문법 | node (단위) | _{채움}_ | _{채움}_ |

## 보안

| # | 항목 | 결과 | 상세 |
|---|------|------|------|
| 1 | 하드코딩 시크릿 스캔 | _{채움}_ | _{채움}_ |
| 2 | .gitignore 확인 | _{채움}_ | _{채움}_ |

## 회귀 테스트

| # | 테스트 스위트 | 결과 | 상세 |
|---|-------------|------|------|
| 1 | 기존 OPAL 파일 손상 여부 (S-14) | _{채움}_ | _{채움}_ |
| 2 | 폴백 호환성 (S-15) | _{채움}_ | _{채움}_ |

## 판정

**_{dtp-test가 채움: All Pass / Partial Fail / Critical Fail}_ -- _{판정 근거}_**

## 설계 피드백

### 발견 사항 1: opi SKILL.md 최신화 모드의 문서 테이블 동기화

**빈틈**: PLAN의 M8에서 최신화 모드 Phase 2 "개발 프로젝트 vs 일반 프로젝트 분기"는 명확하지만, 이미 등록된 문서가 삭제/이동되었을 때 PROJECT.md 문서 테이블을 어떻게 정리하는지 명시되지 않았다.

**제안**: SKILL.md의 최신화 모드 Phase 3에 "문서 테이블 동기화" 단계를 추가하거나, 캡틴에게 "삭제된 문서를 PROJECT.md에서도 제거할까요?" 질문하는 프로토콜 추가.

### 발견 사항 2: .opal/AGENT.md "확정 기준" 섹션의 크기 관리

**빈틈**: R8의 PM 학습 루프에서 "다음 세션에서 확정 기준을 자동 적용"한다고 했지만, 시간이 지나면서 확정 기준 테이블이 커지면 어떻게 할지 명시되지 않았다 (프로젝트별 메모리 정리 규칙은 있지만, AGENT.md 정리 규칙은 없음).

**제안**: AGENT.md 작성 가이드(N2)에 "확정 기준 테이블 관리 원칙" 섹션 추가 (예: 프로젝트 Phase 전환 시 정리, 1년 이상 미사용 항목 아카이브 등).

### 발견 사항 3: docs/PROJECT.md 문서 테이블의 "참조 시점" 규칙

**빈틈**: PLAN의 N1에서 PROJECT.md는 "문서 레지스트리" 역할을 하며, 각 문서에 "용도"와 "참조 시점"을 기입한다고 했다. 하지만 "참조 시점" 값의 표준화가 명시되지 않았다 (예: "부트스트랩 시"? "PLAN 단계"? "모든 단계"?).

**제안**: docs-guide.md(N1)에 "참조 시점" 표준값 리스트 추가 (예: 부트스트랩 시 / TASK 단계 / PLAN 단계 / EXECUTE 단계 / 모든 단계).

---

### 해결 불필요한 관찰

- **OPAL 부트스트래퍼 포맷 변경 금지**: 제약 조건으로 이미 명시되어 있음 (TASK 제약 조건 참고)
- **기존 메모리 구조 유지**: 기존 프로젝트의 .opal/MEMORY.md는 변경 없음 (제약 조건)
- **스킬 페르소나 미변경**: dtp-*/personas/ 파일은 이번 태스크 범위 밖 (제약 조건)
