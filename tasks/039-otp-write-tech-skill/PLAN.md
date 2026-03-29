# PLAN: otp-write-tech 서비스 기획 산출물 오케스트레이터 개발

> 작성일: 2026-03-28 | 입력: TASK.md (v4), ANALYSIS.md (v2) | 출력: PLAN.md

## 1. 코드 분석

ANALYSIS.md v2 기반 요약.

### 관련 파일

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| agents/dtp-worker/AGENT.md | 범용 워커 에이전트 (병렬 디스패치 대상) | 아니오 |
| agents/dtp-qa-worker/AGENT.md | QA 워커 (정합성 검증) | 아니오 |
| opal/core/references/opal-doc-standard.md | 문서 표준, 버전 관리 규칙 | 아니오 |
| opal/core/references/skills.md | 스킬 레지스트리 | 예 (등록 추가) |
| opal/core/references/skill-guide.md | 스킬 가이드 브리핑 | 예 (항목 추가) |

### 현재 구현

- **오케스트레이터 패턴**: 기존 오케스트레이터들이 3~7단계 파이프라인으로 동작. 직접 수행 + STATE.md 관리 + 게이트 체크포인트.
- **워커 디스패치 패턴**: Agent 도구로 워커 병렬 디스패치. 파라미터 표준(스킬 경로, 태스크 폴더, 이전 산출물, 프로젝트 컨텍스트). JSON 반환(artifact_path, summary, status, blockers).
- **QA 워커**: 산출물 검증 후 PM 최종 판정.

### 영향 범위

- 기존 스킬/에이전트 변경 없음 (신규 추가만)
- 레지스트리(skills.md, skill-guide.md) 2개 파일만 수정

---

## 2. 구현 계획

### 파일 변경 계획

#### 신규 생성

| # | 파일 경로 | 역할 |
|---|----------|------|
| 1 | skills/otp-write-tech/SKILL.md | 오케스트레이터 본체 (200줄 이내) |
| 2 | skills/otp-write-tech/references/network-guide.md | 논리적 연결 관계 + 산출물 정의 + 워커 프롬프트 + 배치 편성 규칙 |
| 3 | skills/otp-write-tech/references/consistency-rules.md | 정합성 검증 규칙 (유형 간 + 유형 내) + QA 워커 프롬프트 |

#### 수정

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| 4 | opal/core/references/skills.md | 프레임워크 스킬 테이블에 행 추가 |
| 5 | opal/core/references/skill-guide.md | 스킬 목록 테이블에 행 추가 |

### 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | network-guide.md 작성 | skills/otp-write-tech/references/network-guide.md | 보통 |
| 2 | consistency-rules.md 작성 | skills/otp-write-tech/references/consistency-rules.md | 보통 |
| 3 | SKILL.md 본체 작성 | skills/otp-write-tech/SKILL.md | 높음 |
| 4 | skills.md 레지스트리 등록 | opal/core/references/skills.md | 쉬움 |
| 5 | skill-guide.md 가이드 등록 | opal/core/references/skill-guide.md | 쉬움 |

**순서 근거**: references/를 먼저 작성해야 SKILL.md에서 참조 경로를 확정할 수 있다. 레지스트리는 스킬 완성 후 등록.

### 핵심 설계

#### SKILL.md 구조 (200줄 이내, ~120줄 예상)

핵심만 본체에, 상세는 references/로 분리.

```
YAML frontmatter (name, description, 트리거 키워드)
─────────────────────────────────────────────
설계 원칙
  - 문서가 인터페이스다 — 프로젝트 문서만 참조
  - PM 중심 관리 — 교차 검토/진단/배치/판정/등록
  - 복수 문서 + 병렬 처리

커버 범위
  필수: PRD, TRD, 서비스 정책서(복수), IA(xlsx 추천)
  선택: 기능도, 순서도, 운영 정책서, 서비스 매뉴얼

산출물 저장 구조
  docs/ = 메타 문서 (PROJECT.md가 SSOT)
  프로젝트 산출물 = 별도 폴더 (default: outputs/)
  PM이 PROJECT.md 읽어 기존 구조 따름, 없으면 default 제안

3가지 모드
  작성: Phase 2(간략) → 3 → 4
  수정: Phase 1 → 2(영향 진단) → 3 → 4
  분석: Phase 1 → 2(진단 보고) → 승인 → 3 → 4

4 Phase 파이프라인
  Phase 1: 병렬 분석 — 워커 N개 디스패치, 기존 문서 읽기/요약
  Phase 2: PM 진단 — 교차 논리 검토 → diagnosis.json 생성 (문서별 조치/이슈/의존성/배치)
  Phase 3: 병렬 작성 — diagnosis.json 파싱 → 배치 순회 → 항목별 워커 디스패치
  Phase 4: 정합성 검증 — diagnosis.json 기반 검증 범위 결정 → QA 워커 + PM 판정

Phase 2 PM 조치 판단
  보강: 품질 OK, 누락/수정만 (버전 업)
  재작성: 구조 불일치 (기존 내용 계승)
  신규: 해당 산출물 없음
  → 사용자가 최종 선택

STATE.md 관리 (네트워크 상태 + 배치 계획)
게이트 체크포인트 (Phase/배치 완료 시 사용자 확정)

참조 가이드
  references/network-guide.md
  references/consistency-rules.md
변경이력
```

#### network-guide.md 핵심 내용

| 섹션 | 내용 |
|------|------|
| 산출물 유형 정의 | 필수 4종 + 선택 4종의 목적, 구성, 문서 수(단일/복수) |
| 논리적 연결 맵 | 유형 간 양방향 참조(PRD↔TRD, PRD↔정책서, 정책서↔IA 등). 유형 내 연결(정책서들 간) |
| 순서 체인 | PRD → TRD → 서비스 정책서 → IA. 역방향도 가능 |
| 수정 시 영향 분석 | 연결 문서 영향 범위 판단 프로세스 |
| diagnosis.json 스키마 | Phase 2 산출물 JSON 구조 (documents[], batches[]) |
| Phase 1 워커 프롬프트 | 문서 분석 워커에게 전달할 표준 프롬프트 템플릿 |
| Phase 3 워커 프롬프트 | 문서 작성/수정 워커에게 전달할 표준 프롬프트 템플릿 |
| 배치 편성 규칙 | depends_on 기반 배치 자동 편성 로직 |
| IA 형식 가이드 | JSON 스키마 정의, 검토 후 xlsx 변환 프로세스, .md 폴백 |

#### consistency-rules.md 핵심 내용

| 섹션 | 내용 |
|------|------|
| 유형 간 검증 | PRD↔TRD, PRD↔정책서, PRD↔IA, TRD↔IA, 정책서↔IA 쌍별 체크 항목 |
| 유형 내 검증 | 복수 정책서 간 용어 통일, 범위 중복/누락, 상호 참조 정합성 |
| 용어 일관성 | 동일 개념에 동일 용어 사용 (매핑 테이블) |
| 범위 일관성 | PRD 범위 ⊇ TRD 범위, PRD 기능 목록 = IA 기능 목록 |
| 기능 매핑 | PRD 요구사항 → IA 기능 전수 매핑 (누락 0건 기준) |
| QA 워커 프롬프트 | 정합성 검증 워커에게 전달할 표준 프롬프트 템플릿 |
| 대규모 네트워크 | 10개 이상 산출물 시 배치 분할 전략 |

#### STATE.md 확장 형식

```markdown
## 네트워크 상태
| 산출물 | 유형 | 상태 | 버전 | 경로 |
|--------|------|------|------|------|
| PRD | PRD | 승인 | v1.0 | outputs/01_기획/PRD_v1.0.md |
| 회원정책서 | 서비스 정책서 | 보강 필요 | v1.0 | outputs/01_기획/정책서/회원정책서_v1.0.md |
| 결제정책서 | 서비스 정책서 | 신규 필요 | - | - |
| IA | IA | 미작성 | - | - |

## 배치 계획
| Batch | 문서 | 의존 | 상태 |
|-------|------|------|------|
| 1 | PRD 보강, 결제정책서 신규 | 없음 (독립) | 완료 |
| 2 | TRD 보강 | PRD (Batch 1) | 진행 중 |
| 3 | IA 작성 | 전체 (Batch 1,2) | 대기 |
```

### 의존성 및 환경 변경

- 추가 패키지: 없음
- 환경 설정 변경: 없음
- 참조: opal-doc-standard.md (문서 표준/버전 관리)
- 선택 참조: anthropics/xlsx (IA JSON → xlsx 변환 시)

### 테스트 전략

| 테스트 종류 | 성공 기준 |
|------------|----------|
| SKILL.md 줄 수 검증 | 200줄 이내 |
| 스킬명 미참조 검증 | SKILL.md 본문에 다른 스킬명 미포함 — 문서가 인터페이스 원칙 |
| 삭제 스킬 미참조 | version-mgr, doc-writer 참조 0건 |
| 레지스트리 정합성 | skills.md 트리거와 SKILL.md frontmatter 일치 |
| references/ 참조 유효성 | SKILL.md에서 참조하는 references/ 경로가 실제 파일로 존재 |
| TASK.md 요구사항 커버리지 | 14개 요구사항 모두 SKILL.md + references/에서 커버 |

---

## 3. 실행 체크리스트

- [ ] Step 1: network-guide.md 작성 -- `skills/otp-write-tech/references/network-guide.md` -- 필수 4종 + 선택 4종 산출물 정의, 논리적 연결 맵(양방향), 순서 체인 + 역방향 처리, 수정 시 영향 분석 프로세스, Phase 1/3 워커 프롬프트 템플릿, 배치 편성 규칙, IA 형식 가이드(.xlsx/.md 폴백)
- [ ] Step 2: consistency-rules.md 작성 -- `skills/otp-write-tech/references/consistency-rules.md` -- 유형 간 검증(5쌍), 유형 내 검증(복수 문서), 용어/범위/기능 매핑 일관성, QA 워커 프롬프트 템플릿, 대규모 네트워크(10개+) 처리 전략
- [ ] Step 3: SKILL.md 작성 -- `skills/otp-write-tech/SKILL.md` -- YAML frontmatter + 설계 원칙 + 커버 범위 + 산출물 저장 구조 + 3가지 모드 + 4 Phase 파이프라인 + PM 조치 판단(보강/재작성/신규) + STATE.md 네트워크 확장 + 게이트 체크포인트 + references/ 참조. 200줄 이내. 본문에 다른 스킬명 미참조. opal-doc-standard 적용
- [ ] Step 4: skills.md 등록 -- `opal/core/references/skills.md` -- 프레임워크 스킬 테이블에 행 추가 (트리거: "otp-write-tech", "otpwt", "기획 문서 세트", "기술 산출물 작성", "기획 문서 검토/최신화")
- [ ] Step 5: skill-guide.md 등록 -- `opal/core/references/skill-guide.md` -- 스킬 목록 테이블에 행 추가 (기획 | otp-write-tech | //otp-write-tech, //otpwt | 기획 산출물 네트워크 관리 오케스트레이터)

---

## 4. QA 체크리스트

### 기능 테스트

- [ ] SKILL.md가 4 Phase 파이프라인을 명확히 정의하는가 (병렬 분석 → PM 진단 → 병렬 작성 → 정합성 검증)
- [ ] 3가지 모드(작성/수정/분석)별 Phase 진입 분기가 기술되어 있는가
- [ ] PM vs 워커 역할 분리가 명확한가 (교차 검토=PM 직접, 개별 문서=워커 병렬)
- [ ] 필수 산출물 4종(PRD, TRD, 서비스 정책서, IA) + 선택 산출물 4종이 커버되는가
- [ ] 복수 문서 지원(정책서 N개 등)이 파이프라인에 반영되는가
- [ ] 논리적 연결 관리(양방향, 순서 체인, 역방향)가 network-guide.md에 정의되는가
- [ ] 정합성 검증(유형 간 + 유형 내)이 consistency-rules.md에 체크리스트로 정의되는가
- [ ] 산출물 저장 구조: PROJECT.md 기반 + default 구조(outputs/) 제안 로직이 있는가
- [ ] Phase 2 PM 조치 판단(보강/재작성/신규)이 기술되고 사용자 선택 명시가 있는가
- [ ] STATE.md에 문서 네트워크 상태 테이블 + 배치 계획이 정의되어 있는가
- [ ] 게이트 체크포인트(Phase/배치 완료 시 사용자 확정)가 있는가
- [ ] opal-doc-standard 적용(문서 표준, 버전 관리)이 명시되어 있는가
- [ ] 수정 시 연쇄 업데이트(연결 문서 영향 분석)가 프로세스에 포함되는가
- [ ] 순서 자유성(어떤 산출물이든 먼저 작성 가능)이 지원되는가

### 회귀 테스트

- [ ] 기존 스킬/에이전트에 변경 없음 확인
- [ ] skills.md 기존 항목이 훼손되지 않았는가
- [ ] skill-guide.md 기존 항목이 훼손되지 않았는가

### 코드 품질

- [ ] SKILL.md 200줄 이내
- [ ] SKILL.md 본문에 다른 스킬명 미포함 (문서가 인터페이스 원칙)
- [ ] 삭제된 스킬(version-mgr, doc-writer) 미참조 -- opal-doc-standard.md만 참조
- [ ] PM 중심 관리 원칙: 교차 논리 검토, 진단, 배치 편성, 최종 판정, 문서 등록 모두 PM 역할로 기술
- [ ] references/ 파일이 SKILL.md에서 참조하는 경로와 일치
- [ ] 프로젝트 언어 규칙 준수 (본문 한국어, 코드/필드명 영어)
- [ ] 변경이력 테이블 포함 (opal-doc-standard 형식)

---

## 5. 기술 컨텍스트

### 기술 스택

| 영역 | 기술 | 비고 |
|------|------|------|
| 문서 포맷 | Markdown (.md) | SKILL.md, references/ |
| 문서 표준 | opal-doc-standard | 버전 관리, 헤더, 변경이력 |
| IA 권장 | JSON → xlsx | JSON으로 작성/검토, 필요 시 xlsx 변환 (anthropics/xlsx 선택) |

### 사용 MCP

| MCP | 조회 결과 요약 |
|-----|--------------|
| - | 이 작업은 MCP 조회 불필요 (마크다운 문서 작성) |

---

## 6. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| 200줄 제한 초과 | SKILL.md 복잡도 증가 | ANALYSIS 기준 ~120줄 예상. 워커 프롬프트/배치 규칙/검증 체크리스트를 references/로 분리 |
| 스킬명 참조 위반 | "문서가 인터페이스" 원칙 위반 | 작성 완료 후 Grep으로 스킬명 미포함 자동 검증 |
| 문서 간 수정 추적 복잡성 | 연쇄 업데이트 누락 위험 | network-guide.md에 영향 분석 프로세스를 구체적으로 정의 |
| 순서 자유성과 완전성 트레이드오프 | 의존 문서 없이 시작 시 품질 저하 | PM 진단(Phase 2)에서 누락 감지 + 사용자 확인 후 배치 편성 |
| 병렬 워커 간 충돌 | 동일 파일 동시 수정 위험 | 배치 편성에서 의존성 분석으로 방지 -- 같은 파일은 같은 배치 또는 순차 |
| 대규모 네트워크 (10개+) | 정합성 관리 복잡도 폭발 | consistency-rules.md에 배치 분할 전략 정의 |

---

변경이력:

| 버전 | 날짜 | 작성자 | 변경내용 |
|------|------|--------|---------|
| v1.0 | 2026-03-29 | R2 | 초기 작성 |
| v2.0 | 2026-03-29 | R2 | 4 Phase + PM/워커 역할 분리 + 병렬 디스패치 + 복수 문서 + 3모드 재설계 |
| v3.0 | 2026-03-28 | dtp-plan | TASK.md v4 기반 전면 재작성 -- 스킬명 미참조 원칙 적용, 삭제 스킬 미참조, PM 중심 관리 강화, 실행/QA 체크리스트 보강 |
