# ANALYSIS: otp-write-tech 기술 산출물 네트워크 오케스트레이터

> 작성일: 2026-03-29 | 입력: TASK.md | 출력: ANALYSIS.md

## 1. 기존 코드 분석

### 1.1 관련 파일 목록

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| skills/otp-write/SKILL.md | 단일 문서 작성 오케스트레이터 (재활용 대상) | 아니오 |
| skills/otp-dev/SKILL.md | Full Task 오케스트레이터 구조 (파이프라인 패턴 참조) | 아니오 |
| skills/otp-dev-short/SKILL.md | Short Task 오케스트레이터 (단계 통합 패턴 참조) | 아니오 |
| opal/core/references/opal-doc-standard.md | 문서 표준 및 버전 관리 규칙 | 아니오 |
| skills/version-mgr/SKILL.md | 산출물 버전 관리 (예상: otp-write-tech에서 호출) | 아니오 |
| skills/doc-writer/SKILL.md | 기술 문서 표준 템플릿 (예상: 개별 산출물 작성 시 참조) | 아니오 |
| docs/web-captures/it-ist-tistory-com-277.md | 서비스 기획 산출물 프로세스 (네트워크 매핑 근거) | 아니오 |

### 1.2 아키텍처 패턴

**오케스트레이터 계층 구조:**
- `otp-write`: 단일 독립 문서 작성 (연결성 없음) — 진입점: otp-write 직접
- `otp-dev`: Full Task 파이프라인 (TASK → ANALYSIS → PLAN+TEST-SCENARIO → EXECUTE) — 복잡한 개발 작업
- `otp-dev-short`: Short Task 파이프라인 (TASK → PLAN+TEST-SCENARIO → EXECUTE, ANALYSIS 생략) — 규모 작은 개발
- `otp-write-tech`: 기술 산출물 네트워크 오케스트레이터 (신규) — 기획 문서 간 논리적 연결 관리

**기존 오케스트레이터의 공통 패턴:**
1. STEP 1에서 TASK.md를 직접 작성 (dtp-task/SKILL.md 호출)
2. 이후 단계별 워커를 디스패치 (dtp-* 워커)
3. STATE.md로 단계별 진행 추적
4. 사용자 승인 게이트를 통한 단계 전환
5. 프로젝트 메모리 동기화 (있으면)

**otp-write 패턴 (재활용 가능):**
1. STEP 1 (TASK): 직접 수행
2. STEP 2 (PLAN): 소스 조사 + 목차 설계 + QA 호출 (선택)
3. STEP 3 (WRITE): 섹션별 순차 작성 + opal-doc-standard 적용

### 1.3 의존성 맵

**의존 관계 (하향식):**
```
otp-write-tech (신규)
  ├─ dtp-task/SKILL.md (기존 호출)
  ├─ otp-write (기존, 재활용)
  │   ├─ dtp-task/SKILL.md
  │   ├─ dtp-qa/SKILL.md (선택)
  │   └─ opal-doc-standard (참조)
  ├─ version-mgr (기존, 버전 관리)
  ├─ doc-writer (기존, 개별 문서 템플릿)
  └─ anthropics/xlsx (커뮤니티 스킬, IA 작성 시)

의존 구조:
  오페레이터(otp-write-tech) → 단계 스킬(dtp-*) → 에이전트(dtp-*-agent)
```

**호출하는 외부 컴포넌트:**
- `dtp-task/SKILL.md`: 초기 TASK.md 작성
- `otp-write`: 개별 산출물 작성 모드 → PLAN+WRITE 패턴 재사용
- `dtp-qa`: 산출물 검증 (선택)
- `anthropics/xlsx`: IA(기능 포함) .xlsx 형식 생성 시 (선택)

### 1.4 테스트 현황

- 기존 오케스트레이터(otp-write, otp-dev, otp-dev-short)는 TEST-SCENARIO 워커로 동적 검증
- otp-write-tech는 **문서 네트워크 정합성 검증**이 핵심 → dtp-qa 또는 수동 QA 필요
- 논리적 연결 관계 검증: 참조 문서 존재 확인, 용어/범위/기능 목록 일관성 확인

---

## 2. 외부 조사 결과

### 2.1 서비스 기획 산출물 네트워크 분석

**참조 문서**: docs/web-captures/it-ist-tistory-com-277.md

기획자의 글쓰기(모준승, 2021) 기준 서비스 기획 프로세스:
```
1. 문제 정의 → 2. 요구사항 정의 → 3. 기획 정책 수립 → 4. 기능 정의
→ 5. IA/순서도 → 6. 와이어프레임 → 7. 화면설계서 → 8. 운영정책서/매뉴얼
```

**otp-write-tech에서 커버할 범위:**
- 필수: 문제 정의(PRD 형태) → 요구사항(TRD) → 기획 정책(서비스 정책서) → 기능 정의(IA 기능 포함)
- 선택: 기능도, 순서도, 운영 정책서, 매뉴얼
- 범위 밖: 와이어프레임 (otp-wf로 별도 수행)

**논리적 네트워크의 특성:**
1. **순서 체인** (기본 흐름): PRD → TRD → 서비스 정책서 → IA
2. **양방향 참조**: 역방향도 가능 (IA 먼저 쓰고 PRD를 나중에 써도 됨)
3. **연쇄 업데이트**: 한 문서 수정 시 논리적으로 연결된 다른 문서 영향 분석 필요

### 2.2 논리적 연결 관계 구조

**필수 산출물 간 연결:**
```
PRD ↔ TRD ↔ 서비스정책서 ↔ IA(기능포함)
  ↓        ↓          ↓       ↓
  └────────┴──────────┴───────┘
        모두 상호 참조 가능
```

**선택 산출물 매핑:**
- 기능도 → IA 의존 (기능 정의 시각화)
- 순서도 → IA 의존 (기능별 흐름)
- 운영 정책서 → 서비스 정책서, IA 의존 (정책 확장)
- 매뉴얼 → IA, 운영 정책서 의존 (최종 참조)

### 2.3 기술 스택 및 커뮤니티 스킬 연동

**IA 형식 권장:** .xlsx (엑셀)
- 이유: 기능 목록 + 정보구조를 스프레드시트로 관리 시 수정/추적 용이
- 연동: `anthropics/xlsx` 커뮤니티 스킬 (IA 작성/수정 시 호출)

**문서 표준:** 마크다운 기본 (.md)
- 필수 산출물: PRD, TRD, 서비스 정책서 (.md)
- 선택 산출물: 기능도, 순서도, 운영 정책서, 매뉴얼 (.md 또는 .pptx)
- IA만 예외: .xlsx 추천

---

## 3. 영향 범위

### 3.1 직접 영향

**신규 생성:**
- `skills/otp-write-tech/SKILL.md` — 오케스트레이터 본체
- `skills/otp-write-tech/references/network-guide.md` — 논리적 연결 관리 가이드
- `skills/otp-write-tech/references/consistency-rules.md` — 정합성 검증 규칙

**등록:**
- `~/.opal/references/skills.md` — otp-write-tech 추가
- `~/.opal/references/skill-guide.md` — otp-write-tech 요약 추가

**변경 없음:**
- 기존 단계 스킬 (dtp-task, dtp-qa, doc-writer, version-mgr 등)
- 기존 오케스트레이터 (otp-write, otp-dev, otp-dev-short 등)

### 3.2 간접 영향

**상위 오케스트레이터:**
- otp-dev, otp-dev-short는 **코드 구현** 수반 태스크용
- otp-write-tech는 **문서 전용** 태스크용 → 분리된 진입점

**사용자 워크플로우:**
- 기획 문서 작성 태스크 → `//otp-write-tech` 호출 (신규)
- 단일 문서만 필요 → `//otp-write` 호출 (기존)
- 코드 개발 포함 → `//otp-dev` 또는 `//otp-dev-short` (기존)

**참조 레지스트리:**
- skills.md에 otp-write-tech 추가 시, 스킬 검색 범위 확장
- skill-guide.md 업데이트 필요

### 3.3 영향 범위 요약

- [ ] DB 스키마 변경: 없음
- [ ] API 인터페이스 변경: 없음
- [ ] 설정/환경변수 변경: 없음
- [x] 문서 레지스트리 변경: skills.md, skill-guide.md 업데이트 필요
- [ ] 빌드/배포 파이프라인 변경: 없음

---

## 4. 핵심 발견 사항

### 4.1 논리적 네트워크 관리의 핵심 메커니즘

1. **문서 간 의존성 그래프 구축**: PRD ↔ TRD ↔ 서비스정책서 ↔ IA의 상호 참조 맵핑
2. **작성 시 자동 참고**: 새 문서 작성 시 연결된 기존 문서를 Read하여 컨텍스트 제공
3. **수정 시 영향 분석**: 한 문서 수정 → 연결 문서 스캔 → 영향 분석 및 업데이트 제안
4. **순서 자유성**: 어떤 문서든 먼저 작성 가능 (없는 문서는 없는 대로 진행)

### 4.2 otp-write와의 관계: 재활용 vs 독립

**otp-write-tech는 otp-write의 상위 오케스트레이터:**
- otp-write: 단일 문서 작성 (TASK → PLAN → WRITE)
- otp-write-tech: 문서 네트워크 관리 (TASK → 네트워크 상태 초기화 → 산출물별 otp-write 호출 → 정합성 검증)

**구체적 재활용:**
- 개별 산출물 작성: otp-write의 PLAN→WRITE 패턴 그대로 적용
- 연결 관계 관리: otp-write-tech 레벨에서만 처리
- 정합성 검증: otp-write-tech → dtp-qa 호출 (또는 수동 검증)

**수행 흐름:**
```
사용자: "기획 문서 작성해줘"
  ↓
otp-write-tech (신규)
  ├─ TASK: 필요 산출물 + 논리적 연결 확인
  ├─ 각 산출물별:
  │   └─ otp-write (기존)
  │       ├─ PLAN: 소스 조사 + 목차 설계
  │       └─ WRITE: 섹션별 작성
  ├─ 정합성 검증 (dtp-qa)
  └─ STATE.md로 네트워크 상태 추적
```

### 4.3 anthropics/xlsx 커뮤니티 스킬 연동

**IA 작성 시 .xlsx 형식 지원:**
- otp-write-tech에서 IA 작성 모드 진입 시 anthropics/xlsx Read
- 기능 목록 + 정보구조도를 스프레드시트로 자동 생성
- 참조: TASK.md의 "IA는 엑셀(.xlsx) 형식 추천"

### 4.4 STATE.md와 네트워크 추적

**STATE.md의 역할 확장:**
- 기존: 단계별 진행 상태 추적
- 신규: 문서 네트워크의 각 산출물 상태 추적 (작성됨/미작성/수정필요)

**예시:**
```
## 네트워크 상태
| 산출물 | 상태 | 버전 | 의존도 |
|--------|------|------|--------|
| PRD | 작성됨 | v1.0 | TRD 참고 |
| TRD | 작성됨 | v1.0 | PRD/정책서 참고 |
| 서비스정책서 | 미작성 | - | PRD/TRD 필요 |
| IA | 수정필요 | v1.0 | - |
```

### 4.5 선택 산출물 처리

**기능도, 순서도, 운영 정책서, 매뉴얼:**
- 사용자가 필요 여부 판단 → TASK에서 명시
- 생성 시에만 otp-write 호출 (조건부 실행)
- 필수 산출물과 정합성만 검증

---

## 5. 제약/리스크

| 항목 | 설명 | 심각도 |
|------|------|--------|
| 문서 간 수정 추적의 복잡성 | 한 문서 수정 시 모든 연결 문서를 자동 감지하고 영향 분석하는 로직이 복잡할 수 있음 | 중간 |
| 순서 자유성과 완전성의 트레이드오프 | 어떤 문서든 먼저 쓸 수 있지만, 의존 문서가 없으면 완전성 보장 어려움 | 중간 |
| otp-write와의 역할 경계 | otp-write는 단일 문서용이므로, 네트워크 모드에서 혼용 시 혼동 가능 | 낮음 |
| .xlsx 형식 지원 (IA) | anthropics/xlsx 스킬 미설치 시 IA 작성 불가 | 낮음 |
| 대규모 문서 네트워크 | 산출물 10개 이상인 대규모 프로젝트에서 정합성 관리 난도 ↑ | 낮음 |

---

## 6. 기술 컨텍스트

### 6.1 기술 스택

| 카테고리 | 기술 | 버전 |
|----------|------|------|
| 문서 포맷 | Markdown | - |
| 표준화 | opal-doc-standard v1.0 | - |
| 버전 관리 | version-mgr | - |
| 커뮤니티 스킬 | anthropics/xlsx (선택) | - |

### 6.2 추천 스킬

| 스킬 | 용도 |
|------|------|
| dtp-task | TASK.md 초기 작성 (문서 유형 정의) |
| otp-write | 개별 산출물 작성 (PLAN+WRITE 패턴) |
| doc-writer | 개별 문서 템플릿 및 표준 (이미 포함) |
| version-mgr | 산출물 버전 관리 (Major/Minor) |
| dtp-qa | 정합성 검증 (선택) |
| anthropics/xlsx | IA 작성 (.xlsx 형식, 선택) |

### 6.3 추천 MCP

| MCP | 용도 |
|-----|------|
| context7 | 외부 라이브러리/프레임워크 API 조사 (필요 시) |
| WebSearch | 업계 표준, 모범 사례 조사 (필요 시) |

---

## 7. 추가 분석: 참조 대체/레지스트리 변경의 영향

### 7.1 skills.md 업데이트 영향

현재 skills.md에 등록된 스킬들:
```
- otp-write: 단일 문서 작성
- otp-dev: Full Task (코드 포함)
- otp-dev-short: Short Task (코드 포함)
- (신규) otp-write-tech: 문서 네트워크 오케스트레이터
```

**영향 범위:**
- 스킬 검색 범위 확장 (otp-write-tech 추가)
- 기획 문서 태스크 사용자는 otp-write-tech를 먼저 고려
- 기존 사용자는 otp-write, otp-dev, otp-dev-short와 구분하여 선택

### 7.2 skill-guide.md 업데이트 영향

skill-guide.md의 "스킬 사용 선택도":
```
[코드 변경?]
├─ No (문서만)
│  ├─ 단일 문서? → otp-write
│  └─ 문서 네트워크? → otp-write-tech (신규)
└─ Yes (코드 포함)
   ├─ 규모 크다? → otp-dev
   └─ 규모 작다? → otp-dev-short
```

**영향:** 명확한 진입점 제시로 사용자 혼동 감소

---

## 8. 200줄 제약 분석

**otp-write-tech/SKILL.md 예상 길이:**
- 파이프라인 개요: 5줄
- 아키텍처 패턴 설명: 10줄
- 각 STEP 상세: 40줄
- 논리적 연결 가이드: 20줄
- STATE.md 관리: 15줄
- 스킬 탐색 경로: 5줄
- 변경이력: 5줄
- **예상 총합: ~100줄** ✓ (200줄 이내 충분)

**상세 가이드 분리:**
- `references/network-guide.md` — 논리적 연결 맵핑 (상세)
- `references/consistency-rules.md` — 정합성 검증 체크리스트 (상세)

---

## 결론

### 설계 방향 확정

1. **otp-write-tech는 오케스트레이터 역할** (문서 네트워크 관리 전담)
2. **개별 산출물 작성은 otp-write 재활용** (PLAN+WRITE 패턴)
3. **논리적 연결 관리는 otp-write-tech 고유 기능** (상위 오케스트레이터만 처리)
4. **IA는 .xlsx 지원** (anthropics/xlsx 선택적 연동)
5. **정합성 검증은 dtp-qa + 수동 검증** (게이트 체크포인트)

### 다음 단계

1. otp-write-tech/SKILL.md 작성
2. 논리적 연결 가이드 문서 작성
3. 정합성 검증 체크리스트 작성
4. skills.md, skill-guide.md 업데이트
5. 선택사항: otp-write-tech 페르소나 및 참조 문서 작성

---

변경이력:

| 버전 | 날짜 | 작성자 | 변경내용 |
|------|------|--------|---------|
| v1.0 | 2026-03-29 | R2 | 초기 작성 |
