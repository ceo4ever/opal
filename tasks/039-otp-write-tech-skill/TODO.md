# TODO: otp-write-tech 서비스 기획 산출물 오케스트레이터 개발

> 작성일: 2026-03-29 | 참조: TASK.md, ANALYSIS.md, PLAN.md

## Part A: 실행 체크리스트

> 총 10개 Step | 실행 모드: **복잡**

### Step 1: network-guide.md 산출물 정의 및 연결 맵 작성
- [ ] 완료
- **파일**: `skills/otp-write-tech/references/network-guide.md`
- **작업 내용**: 필수 4종(PRD, TRD, 서비스 정책서, IA) + 선택 4종(기능도, 순서도, 운영 정책서, 서비스 매뉴얼)의 목적/구성/문서 수 정의. 유형 간 양방향 참조 맵핑(PRD↔TRD, PRD↔정책서, 정책서↔IA 등). 유형 내 연결(정책서들 간) 명시. 순서 체인 + 역방향 처리 프로세스 기술. 수정 시 영향 분석 가이드 포함.
- **완료 기준**: 산출물 8종 모두 정의 완료, 양방향 참조 관계 맵 작성, 순서 체인 명확화, 역방향 처리 프로세스 기술, 영향 분석 메서드 정의
- **테스트**: 문서 읽기 > 산출물 정의 섹션 확인 > 연결 맵 다이어그램/테이블 확인 > Phase 1/3 워커 프롬프트 템플릿 존재 확인
- **실행 방법**: `direct`
- **의존**: 없음

### Step 2: network-guide.md 배치 편성 규칙 및 IA 형식 가이드 작성
- [ ] 완료
- **파일**: `skills/otp-write-tech/references/network-guide.md` (Step 1 파일 확장)
- **작업 내용**: depends_on 기반 배치 자동 편성 로직 정의. Phase 1 워커 프롬프트 템플릿 작성(문서 분석 역할). Phase 3 워커 프롬프트 템플릿 작성(문서 작성/수정 역할). IA JSON 스키마 정의. JSON 작성 후 xlsx 변환 프로세스 설명. JSON → xlsx 실패 시 .md 폴백 전략 명시.
- **완료 기준**: 배치 편성 로직 완성, Phase 1/3 워커 프롬프트 템플릿 완성(실행 가능 형태), IA JSON 스키마 정의 완료, .xlsx/.md 폴백 프로세스 명시
- **테스트**: 배치 편성 규칙 검증(의존성 순환 없음), 워커 프롬프트 가독성 확인, IA JSON 스키마 유효성(예제 포함), 폴백 조건 명확성 확인
- **실행 방법**: `direct`
- **의존**: Step 1

### Step 3: consistency-rules.md 유형 간 + 유형 내 검증 규칙 작성
- [ ] 완료
- **파일**: `skills/otp-write-tech/references/consistency-rules.md`
- **작업 내용**: 유형 간 검증 5쌍(PRD↔TRD, PRD↔정책서, PRD↔IA, TRD↔IA, 정책서↔IA)의 체크 항목 정의. 유형 내 검증(복수 정책서 간 용어 통일, 범위 중복/누락, 상호 참조 정합성) 규칙 정의. 용어 일관성 매핑 테이블 형식 제시. 범위 일관성 검증(PRD ⊇ TRD, PRD 기능 목록 = IA 기능 목록) 명확화.
- **완료 기준**: 5쌍 유형 간 검증 항목 모두 정의, 유형 내 검증 규칙 완성, 용어/범위/기능 매핑 테이블 형식 제시, QA 워커 판단 기준 명확화
- **테스트**: 검증 항목별 가독성 확인, 검증 체크리스트 실행 가능성 확인, 매핑 테이블 예제 포함 여부, QA 워커 호출 판단 기준 명확성 확인
- **실행 방법**: `direct`
- **의존**: Step 1

### Step 4: consistency-rules.md 대규모 네트워크 처리 전략 및 QA 워커 프롬프트 작성
- [ ] 완료
- **파일**: `skills/otp-write-tech/references/consistency-rules.md` (Step 3 파일 확장)
- **작업 내용**: 10개 이상 산출물 시 배치 분할 전략 정의(대규모 네트워크 특수 처리). QA 워커 프롬프트 템플릿 작성(정합성 검증 워커에게 전달할 표준 프롬프트). diagnosis.json 기반 검증 범위 자동 결정 로직 명시.
- **완료 기준**: 대규모 네트워크(10개+) 처리 전략 명시, QA 워커 프롬프트 템플릿 완성(실행 가능), diagnosis.json 파싱 → 검증 범위 결정 로직 명확화
- **테스트**: 대규모 시나리오 예제 확인, QA 프롬프트 실행 가능성 확인, diagnosis.json 기반 검증 범위 결정 로직 검증
- **실행 방법**: `direct`
- **의존**: Step 3

### Step 5: SKILL.md YAML frontmatter + 설계 원칙 + 커버 범위 작성
- [ ] 완료
- **파일**: `skills/otp-write-tech/SKILL.md`
- **작업 내용**: YAML frontmatter(name, description, 트리거 키워드). "문서가 인터페이스" 설계 원칙 기술. "필수 4종 + 선택 4종 산출물" 커버 범위 명시. "산출물 저장 구조"(docs/ vs 별도 폴더, PROJECT.md SSOT, default 제안) 명시.
- **완료 기준**: frontmatter 완성, 3가지 설계 원칙 명확히 기술, 8개 산출물 모두 명시, 저장 구조 선택 로직(PROJECT.md 읽기 → 있으면 따름, 없으면 제안) 명확화
- **실행 방법**: `direct`
- **의존**: Step 1, 2, 3, 4

### Step 6: SKILL.md 3가지 모드 + 4 Phase 파이프라인 기술
- [ ] 완료
- **파일**: `skills/otp-write-tech/SKILL.md` (Step 5 파일 확장)
- **작업 내용**: 3가지 모드(작성/수정/분석) 정의 및 각 모드별 Phase 진입 분기 명시. 4 Phase 파이프라인 명확히 기술(Phase 1: 병렬 분석 → Phase 2: PM 진단 → Phase 3: 병렬 작성 → Phase 4: 정합성 검증). 각 Phase 입출력, 담당자(PM/워커), 도구 명시.
- **완료 기준**: 3가지 모드 정의 및 Phase 분기 명확화, 4 Phase 파이프라인 입출력 명확화, PM vs 워커 역할 분리 명시, 의사결정 지점(게이트 체크포인트) 명확화
- **테스트**: 3가지 모드별 실행 흐름 확인, Phase 간 의존성 검증(Phase 1→2→3→4 순차/분기 가능성), 게이트 체크포인트 명시 여부 확인
- **실행 방법**: `direct`
- **의존**: Step 5

### Step 7: SKILL.md Phase 2 PM 조치 판단 + diagnosis.json 스키마 기술
- [ ] 완료
- **파일**: `skills/otp-write-tech/SKILL.md` (Step 6 파일 확장)
- **작업 내용**: Phase 2 PM 조치 판단(보강/재작성/신규) 정의 및 사용자 선택 명시. diagnosis.json 생성 프로세스 기술(Phase 2 산출물). diagnosis.json 스키마(documents[], batches[] 구조) network-guide.md 참조 명시. diagnosis.json 배열을 순회하며 Phase 3 워커 디스패치 로직 기술.
- **완료 기준**: 3가지 조치 정의(보강/재작성/신규), PM이 사용자에게 제안하는 형식 명확화, diagnosis.json 스키마 명시, Phase 3 워커 디스패치 로직 명확화
- **테스트**: diagnosis.json 스키마 유효성 확인(예제 포함), 디스패치 로직 의존성 검증(배치 순서 정확), PM 조치 판단 기준 명확성 확인
- **실행 방법**: `direct`
- **의존**: Step 6

### Step 8: SKILL.md STATE.md 네트워크 확장 + 게이트 체크포인트 기술
- [ ] 완료
- **파일**: `skills/otp-write-tech/SKILL.md` (Step 7 파일 확장)
- **작업 내용**: STATE.md 문서 네트워크 상태 테이블(산출물 | 유형 | 상태 | 버전 | 경로) 정의. STATE.md 배치 계획 테이블(Batch | 문서 | 의존 | 상태) 정의. Phase/배치 완료 시 게이트 체크포인트(사용자 확정) 명시. STATE.md 상태 추이(미작성→작성중→대기→승인) 명시.
- **완료 기준**: STATE.md 네트워크 상태 테이블 포맷 정의, 배치 계획 테이블 포맷 정의, 게이트 체크포인트 3개(Phase 1→2, Phase 2→3, Phase 3→4) 명시, 상태 추이 명확화
- **테스트**: STATE.md 테이블 예제 포함 여부 확인, 게이트 체크포인트별 사용자 확정 지점 명확성 확인, 상태 추이 프로세스 명확성 확인
- **실행 방법**: `direct`
- **의존**: Step 7

### Step 9: SKILL.md opal-doc-standard 적용 + references 참조 + 변경이력 기술
- [ ] 완료
- **파일**: `skills/otp-write-tech/SKILL.md` (Step 8 파일 확장)
- **작업 내용**: opal-doc-standard 적용(문서 표준, 버전 관리 규칙) 명시. references/network-guide.md, consistency-rules.md 참조 경로 명시. 변경이력 테이블(버전 | 날짜 | 작성자 | 변경내용) 추가. 전체 줄 수 200줄 이내 확인. SKILL.md 본문에 다른 스킬명(version-mgr, doc-writer 등) 미포함 확인.
- **완료 기준**: opal-doc-standard 참조 명시, references/ 2개 파일 참조 경로 정확, 변경이력 테이블 완성, 줄 수 검증(200줄 이내), 스킬명 미포함 확인
- **테스트**: SKILL.md 줄 수 카운트, Grep으로 다른 스킬명 미포함 자동 검증, references/ 경로 존재 여부 확인, opal-doc-standard 참조 링크 유효성 확인
- **실행 방법**: `direct`
- **의존**: Step 8

### Step 10: skills.md + skill-guide.md 레지스트리 등록
- [ ] 완료
- **파일**: `opal/core/references/skills.md`, `opal/core/references/skill-guide.md`
- **작업 내용**: skills.md의 프레임워크 스킬 테이블에 otp-write-tech 행 추가(트리거: "otp-write-tech", "otpwt", "기획 문서 세트", "기술 산출물 작성", "기획 문서 검토/최신화"). skill-guide.md 스킬 목록 테이블에 행 추가(대분류: 기획, 스킬명: otp-write-tech, 호출: //otp-write-tech, //otpwt, 설명: "기획 산출물 네트워크 관리 오케스트레이터").
- **완료 기준**: skills.md 추가 행이 포맷에 맞고 트리거가 모두 포함, skill-guide.md 추가 행이 기존 형식과 일치, 기존 행 훼손 없음, 파일 저장 완료
- **테스트**: skills.md 기존 항목 훼손 여부 확인, skill-guide.md 기존 항목 훼손 여부 확인, 추가된 행의 링크 유효성 확인(SKILL.md 존재 여부), frontmatter 트리거와 skills.md 트리거 일치 확인
- **실행 방법**: `direct`
- **의존**: Step 9

---

## Part B: QA 체크리스트

### B-1. 기능 테스트

- [ ] TASK.md 요구사항 1(4 Phase 파이프라인): SKILL.md에 병렬 분석 → PM 진단 → 병렬 작성 → 정합성 검증 4단계 명확히 정의되어 있는가
- [ ] TASK.md 요구사항 2(3가지 모드): SKILL.md에 작성/수정/분석 3가지 모드와 각 모드별 Phase 분기 명확히 정의되어 있는가
- [ ] TASK.md 요구사항 3(PM 중심 관리): SKILL.md에서 PM이 교차 검토/진단/배치 편성/최종 판정 역할을 명시했는가
- [ ] TASK.md 요구사항 4(워커 병렬 디스패치): SKILL.md에서 독립 문서는 병렬, 의존 문서는 배치 순차 디스패치 로직이 기술되어 있는가
- [ ] TASK.md 요구사항 5(복수 문서 지원): network-guide.md에 유형당 복수 문서(정책서 N개 등) 처리 방법이 명시되어 있는가
- [ ] TASK.md 요구사항 6(논리적 연결 관리): network-guide.md에 유형 간 + 유형 내 양방향 연결 맵핑이 정의되어 있는가
- [ ] TASK.md 요구사항 7(diagnosis.json): SKILL.md에서 Phase 2 산출물로 diagnosis.json 생성 및 문서별 조치/이슈/의존성/배치 구조화가 명시되어 있는가
- [ ] TASK.md 요구사항 8(IA도 JSON): network-guide.md에 IA를 JSON으로 작성 → 검토 후 필요 시 xlsx 변환 프로세스가 명시되어 있는가
- [ ] TASK.md 요구사항 9(정합성 검증): consistency-rules.md에 유형 간 + 유형 내 검증 항목이 모두 정의되어 있는가
- [ ] TASK.md 요구사항 10(순서 자유): SKILL.md에서 어떤 산출물이든 먼저 작성 가능한 메커니즘이 명시되어 있는가
- [ ] TASK.md 요구사항 11(프로젝트 환경 인지): SKILL.md에서 docs/PROJECT.md 읽기 + PROJECT.md 폴더 구조 기반 산출물 저장 경로 결정 로직이 명시되어 있는가
- [ ] TASK.md 요구사항 12(기존 문서 활용): SKILL.md에서 기존 문서가 있으면 참고/보강, 없으면 생성하는 분기가 명시되어 있는가
- [ ] TASK.md 요구사항 13(산출물 저장): SKILL.md에서 PROJECT.md 폴더 구조 따름, 없으면 default 구조 제안 → PROJECT.md 기록 로직이 명시되어 있는가
- [ ] TASK.md 요구사항 14(opal-doc-standard): SKILL.md에서 문서 표준 + 버전 관리 규칙 적용이 명시되어 있는가

### B-2. 회귀 테스트

- [ ] 기존 스킬(dtp-task, dtp-analysis, dtp-plan 등)에 변경 없음 확인
- [ ] 기존 에이전트(dtp-worker, dtp-qa-worker 등)에 변경 없음 확인
- [ ] skills.md 기존 항목이 훼손되지 않았는가
- [ ] skill-guide.md 기존 항목이 훼손되지 않았는가
- [ ] opal-doc-standard.md(문서 표준) 참조 무결성 확인

### B-3. 코드 품질

- [ ] SKILL.md 줄 수가 200줄 이내인가 (PLAN.md 예상 120줄 기준)
- [ ] SKILL.md 본문에 다른 스킬명(version-mgr, doc-writer, dtp-analysis 등)이 포함되지 않았는가 (참조 가이드만 가능)
- [ ] network-guide.md와 consistency-rules.md 파일이 SKILL.md에서 정확히 참조되는가
- [ ] YAML frontmatter 트리거(otp-write-tech, otpwt 등)가 skills.md 트리거와 일치하는가
- [ ] PM 중심 관리 원칙이 명확히 반영되어 있는가 (교차 검토 = PM 직접, 개별 문서 = 워커 병렬)
- [ ] 프로젝트 언어 규칙 준수 (본문 한국어, 코드/필드명 영어)
- [ ] SKILL.md에 변경이력 테이블(버전 | 날짜 | 작성자 | 변경내용) 포함되어 있는가

---

## Part C: 실행 아키텍처 (복잡 모드)

### 복잡도 판별 근거

| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 10개 | 복잡 (6개 이상) |
| 변경 파일 수 | 5개 (network-guide.md, consistency-rules.md, SKILL.md, skills.md, skill-guide.md) | 복잡 (4개 이상) |
| 모듈 범위 | 5개 파일 + 3개 섹션 (network, consistency, SKILL 본체) | 다중 모듈 |
| 작업 유형 | 신규 오케스트레이터 + 참조 가이드 2개 + 레지스트리 업데이트 | 신규 개발 |
| 외부 의존성 | opal-doc-standard.md 참조, anthropics/xlsx 선택 | 새 문서 표준 참조 |

**판정: 복잡 모드** ✓

### C-1. 에이전트 토폴로지

```
Step 1-4: 참조 가이드 작성 (network-guide.md, consistency-rules.md)
  ├─ Step 1: network-guide 산출물 정의 + 연결 맵 [직렬]
  ├─ Step 2: network-guide 배치 규칙 + 워커 프롬프트 [직렬, Step 1 의존]
  ├─ Step 3: consistency-rules 유형 간/내 검증 [병렬 with Step 1-2]
  └─ Step 4: consistency-rules 대규모 처리 + QA 프롬프트 [직렬, Step 3 의존]

Step 5-9: SKILL.md 본체 작성 (오케스트레이터)
  ├─ Step 5: frontmatter + 설계 원칙 + 커버 범위 [직렬, Step 1-4 의존]
  ├─ Step 6: 3가지 모드 + 4 Phase 파이프라인 [직렬, Step 5 의존]
  ├─ Step 7: Phase 2 조치 판단 + diagnosis.json [직렬, Step 6 의존]
  ├─ Step 8: STATE.md 확장 + 게이트 체크포인트 [직렬, Step 7 의존]
  └─ Step 9: opal-doc-standard 적용 + 변경이력 [직렬, Step 8 의존]

Step 10: 레지스트리 등록
  └─ Step 10: skills.md + skill-guide.md 등록 [직렬, Step 9 의존]

병렬 실행 가능 그룹:
  - Batch A: Step 1-4 (참조 가이드) — 병렬 가능 (Step 1 먼저, 그 후 Step 2와 Step 3 병렬 가능)
  - Batch B: Step 5-9 (SKILL.md) — 직렬 필수 (누적 작성)
  - Batch C: Step 10 (레지스트리) — Step 9 완료 후 실행
```

**배치 편성 다이어그램:**

```
Time →
[Batch A: 참조 가이드]    [Batch B: SKILL.md 본체]    [Batch C: 레지스트리]
  Step 1─────────
  Step 2┐
  Step 3├─(병렬)─────→ Step 5─Step 6─Step 7─Step 8─Step 9─→ Step 10
  Step 4┘
```

### C-2. 스킬 요구사항

| 항목 | 현황 | 비고 |
|------|------|------|
| dtp-worker (문서 분석/작성) | 기존 | otp-write-tech에서 Phase 1/3 워커 프롬프트로 활용 |
| dtp-qa-worker (정합성 검증) | 기존 | otp-write-tech에서 Phase 4 검증 워커 프롬프트로 활용 |
| opal-doc-standard.md | 기존 참조 | SKILL.md에서 opal-doc-standard 명시하여 버전 관리 규칙 적용 |
| anthropics/xlsx | 선택 의존 | IA JSON → xlsx 변환 시 필수, 미설치 시 .md 폴백 (network-guide.md에 명시) |

### C-3. 도구 요구사항

| 도구 | 설치 | 설정 | 목적 |
|------|------|------|------|
| 마크다운 에디터 | 기존 | 불필요 | SKILL.md, references/ 작성 |
| Grep/텍스트 검색 | 기존 | 불필요 | Step 9에서 스킬명 미포함 검증 |
| anthropics/xlsx | 선택 | 필요 | IA JSON → xlsx 변환(선택) |

### C-4. 테스트 전략

**Phase 1: Step 1-4 완료 후 참조 가이드 유효성 검증**

```
테스트 항목:
1. network-guide.md 산출물 정의 완성도
   - 필수 4종(PRD, TRD, 서비스 정책서, IA) 정의 확인
   - 선택 4종(기능도, 순서도, 운영 정책서, 매뉴얼) 정의 확인
   - 양방향 참조 맵 가독성 확인

2. network-guide.md 배치 편성 규칙 실행 가능성
   - 의존성 관계 순환 없음 확인
   - Phase 1/3 워커 프롬프트 실행 가능 형태 확인

3. consistency-rules.md 검증 체크리스트 완성도
   - 5쌍 유형 간 검증 항목 모두 정의 확인
   - 유형 내 검증 규칙 명확성 확인
   - QA 워커 프롬프트 실행 가능 형태 확인
```

**Phase 2: Step 5-9 완료 후 SKILL.md 품질 검증**

```
테스트 항목:
1. SKILL.md 형식 검증
   - YAML frontmatter 완성 (name, description, 트리거)
   - 줄 수 200줄 이내 확인
   - 변경이력 테이블 포함 확인

2. SKILL.md 내용 검증
   - 3가지 모드(작성/수정/분석) Phase 분기 명확성
   - 4 Phase 파이프라인 입출력 명확성
   - PM vs 워커 역할 분리 명확성
   - 게이트 체크포인트 3개 이상 명시 확인

3. SKILL.md 스킬명 미포함 검증 (Grep)
   - version-mgr, doc-writer, dtp-task 등 스킬명 0건 확인
   - references/ 경로만 참조 확인
```

**Phase 3: Step 10 완료 후 레지스트리 정합성 검증**

```
테스트 항목:
1. skills.md 정합성
   - otp-write-tech 행 추가 확인
   - 트리거(otpwt 등) skills.md와 SKILL.md frontmatter 일치 확인
   - 기존 행 훼손 없음 확인

2. skill-guide.md 정합성
   - otp-write-tech 행 추가 확인
   - 호출 형식(//otp-write-tech, //otpwt) 일치 확인
   - 기존 행 훼손 없음 확인

3. 링크 유효성
   - skills.md 스킬 경로 → SKILL.md 존재 확인
   - SKILL.md references/ 경로 → network-guide.md, consistency-rules.md 존재 확인
```

**Phase 4: 통합 검증 (모든 Step 완료 후)**

```
테스트 항목:
1. TASK.md 요구사항 14개 모두 커버 확인
2. 기존 스킬/에이전트 비파괴 확인
3. opal-doc-standard 적용 확인
4. 파일 구조 및 경로 무결성 확인
```

---

## 승인 요청

> 위 TODO가 사용자의 승인을 받으면 EXECUTE 단계를 시작합니다.
> 복잡 모드: 워커가 Part C 토폴로지에 따라 배치별 실행을 진행합니다.

---

**작성자**: dtp-todo | **상태**: 대기 중 (사용자 승인 필요)
