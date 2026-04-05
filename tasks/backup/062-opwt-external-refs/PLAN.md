# PLAN: opwt 외부 참조 산출물 지원 + wtm wireframe 모드

> 작성일: 2026-04-01
> 입력: TASK.md
> 출력: PLAN.md

## 1. 현황 조사

### 관련 파일

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| `skills/web-to-markdown/SKILL.md` | wtm 스킬 소스 (full/clean 2모드) | Yes — wireframe 모드 추가 |
| `opal/skills/opal-pilot-write-tech/SKILL.md` | opwt 오케스트레이터 | Yes — 외부 참조 산출물 언급 추가 |
| `opal/skills/opal-pilot-write-tech/references/network-guide.md` | 산출물 정의, diagnosis.json 스키마, 워커 프롬프트 | Yes — 참조 산출물 가이드, 스키마 확장, 워커 프롬프트 확장 |
| `opal/skills/opal-pilot-write-tech/references/consistency-rules.md` | 유형 간/내 정합성 검증 규칙 | Yes — 외부 참조 검증 섹션 추가 |
| `skills/erd-modeler/SKILL.md` | ERD 모델링 스킬 | No — 참조만 (산출물 형식 파악용) |

### 현재 상태

**wtm SKILL.md (v1.2)**:
- 추출 모드: `full`(기본) / `clean` 2개만 존재
- 3단계 폴백: WebFetch -> Crawl4AI -> Node Playwright
- 복수 URL 병렬 처리: wtm-agent 서브에이전트 활용
- 저장 경로: 사용자 지정 > 태스크 폴더/references > /tmp
- wireframe 모드 없음 — 기획 관점의 구조화된 분석 기능 부재

**network-guide.md**:
- 산출물 유형 정의: 필수 4종(PRD, TRD, 서비스 정책서, IA) + 선택 4종
- diagnosis.json 스키마: `documents[]` 배열에 `id`, `type`, `name`, `path`, `status`, `version`, `issues`, `depends_on`, `connected_to` 필드
- `reference_artifacts` 필드 없음 — 외부 참조 산출물(와이어프레임, ERD, API 명세서)을 인지/활용하는 구조가 없음
- Phase 1 워커 프롬프트: 문서 분석만 수행, 외부 참조 분석 지시 없음
- Phase 3 워커 프롬프트: 보강/재작성/신규 3종 — `{reference_artifacts}` 플레이스홀더 없음

**consistency-rules.md**:
- 유형 간 검증: PRD↔TRD, PRD↔서비스 정책서, PRD↔IA, TRD↔IA, 서비스 정책서↔IA (모두 내부 산출물 간)
- 유형 내 검증: 복수 정책서 간 검증
- 외부 참조 산출물(wireframe, ERD, API 명세서)과의 크로스 체크 규칙 없음
- QA 워커 프롬프트: diagnosis.json 기반 내부 산출물 검증만 수행

**opwt SKILL.md (v1.2)**:
- 설계 원칙: "문서가 인터페이스" — 다른 스킬 존재를 모름 (유지)
- 커버 범위: 필수 4종 + 선택 4종
- 참조 가이드: network-guide.md, consistency-rules.md만 언급
- 외부 참조 산출물에 대한 언급 없음

**소스 vs 배포 확인**:
- `skills/web-to-markdown/SKILL.md` (프로젝트 내 소스) = `~/.opal/skills/web-to-markdown/SKILL.md` (배포본) — 동일 내용 (v1.2)
- 소스를 수정하는 것이 원칙

### 영향 범위

1. **wtm 스킬**: wireframe 모드 추가 — 기존 full/clean 모드에 영향 없음 (독립 추가)
2. **opwt 스킬**: 외부 참조 인지 추가 — 기존 8종 관리 구조 변경 없음
3. **network-guide.md**: diagnosis.json 스키마 확장 + 워커 프롬프트 확장 — 기존 필드 호환성 유지 (새 필드 추가만)
4. **consistency-rules.md**: 외부 참조 검증 섹션 추가 — 기존 검증 규칙 변경 없음 (섹션 추가만)
5. **배포 동기화**: 소스 수정 후 `~/.opal/skills/web-to-markdown/SKILL.md`에 배포 필요

## 2. 구현 계획

### 파일 변경 계획

#### 신규 생성

| # | 파일 경로 | 역할 |
|---|----------|------|
| (없음) | | |

#### 수정

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| 1 | `skills/web-to-markdown/SKILL.md` | wireframe 모드 추가 (추출 모드 테이블, 산출물 형식, 저장 경로 규칙, 인덱스 생성) |
| 2 | `opal/skills/opal-pilot-write-tech/references/network-guide.md` | diagnosis.json 스키마에 `reference_artifacts[]` 추가, 참조 산출물 가이드 섹션 추가, Phase 1/3 워커 프롬프트 확장 |
| 3 | `opal/skills/opal-pilot-write-tech/references/consistency-rules.md` | 외부 참조 검증 섹션 추가, QA 워커 프롬프트 확장 |
| 4 | `opal/skills/opal-pilot-write-tech/SKILL.md` | 외부 참조 산출물 관련 설명 추가 (커버 범위, 참조 가이드 섹션) |

#### 삭제

| # | 파일 경로 | 사유 |
|---|----------|------|
| (없음) | | |

### 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | wtm wireframe 모드 추가 | `skills/web-to-markdown/SKILL.md` | 중 |
| 2 | diagnosis.json 스키마 확장 + 참조 산출물 가이드 + 워커 프롬프트 확장 | `network-guide.md` | 높 |
| 3 | 외부 참조 크로스 체크 규칙 + QA 워커 프롬프트 확장 | `consistency-rules.md` | 중 |
| 4 | opwt SKILL.md 업데이트 | `opal-pilot-write-tech/SKILL.md` | 낮 |

### 핵심 설계

#### Step 1: wtm SKILL.md — wireframe 모드 추가

**추출 모드 테이블 확장** — 기존 full/clean 아래에 wireframe 행 추가:

```
| **wireframe** | 와이어프레임 분석. 화면 구조, 구성요소, 기능 동작, 네비게이션, 데이터 I/O를 구조화된 기획 관점으로 추출한다. | 와이어프레임 HTML을 기획 문서로 변환할 때, opwt 정책서/IA 작성 시 참조 |
```

키워드 매칭: "와이어프레임", "wireframe", "화면 분석", "기획 분석"

**wireframe 모드 실행 로직** — 기존 3단계 폴백 위에 분석 레이어 추가:

```
URL 입력 (wireframe 모드)
  │
  ├─ 기존 3단계 폴백으로 HTML/마크다운 취득 (full 모드 기반)
  │
  └─ 분석 레이어 적용
        ├─ 화면 개요 추출 (타이틀, 목적, URL 경로)
        ├─ 구성요소 분석 (헤더, 메인, 사이드바, 푸터 등 영역별)
        ├─ 기능 동작 분석 (버튼, 폼, 인터랙션 요소)
        ├─ 네비게이션 구조 (링크, 메뉴, 브레드크럼)
        └─ 데이터 I/O 정의 (입력 필드, 출력 데이터, API 호출 추정)
```

**wireframe 모드 산출물 형식**:

```markdown
# 와이어프레임 분석: {페이지 타이틀}

> 소스: {URL}
> 캡처일: {YYYY-MM-DD HH:mm}
> 추출 방식: {WebFetch | Crawl4AI | Playwright}
> 추출 모드: wireframe

---

## 1. 화면 개요

| 항목 | 내용 |
|------|------|
| 화면명 | {페이지 타이틀} |
| URL 경로 | {URL path} |
| 화면 목적 | {1줄 요약} |
| 접근 권한 | {public / member / admin — 추정} |

## 2. 화면 구성요소

### 2.1 헤더 영역
- {구성요소 목록}

### 2.2 메인 콘텐츠 영역
- {구성요소 목록}

### 2.3 사이드바 (있는 경우)
- {구성요소 목록}

### 2.4 푸터 영역
- {구성요소 목록}

## 3. 기능 동작

| # | 기능명 | 유형 | 동작 설명 | 조건/제약 |
|---|--------|------|----------|----------|
| 1 | {기능} | 버튼/폼/링크/토글 등 | {동작 설명} | {조건} |

## 4. 네비게이션

| 출발 | 도착 | 트리거 | 비고 |
|------|------|--------|------|
| {현재 화면} | {대상 화면} | {클릭/제출 등} | {조건부 등} |

## 5. 데이터 I/O

### 입력 (Input)
| # | 필드명 | 타입 | 필수 | 검증 규칙 |
|---|--------|------|------|----------|

### 출력 (Output)
| # | 데이터 | 소스 | 표시 형식 |
|---|--------|------|----------|
```

**wireframe 모드 Phase 1 WebFetch 프롬프트**:

```
WebFetch(url="{URL}", prompt="이 와이어프레임 페이지를 기획 관점에서 분석해줘. 전체 HTML 구조를 보존하면서, 화면 구성요소(헤더, 메인, 사이드바, 푸터), 버튼/폼/링크 등 인터랙션 요소, 네비게이션 링크, 입출력 필드를 식별해줘. script, style 태그만 제거해줘.")
```

**저장 경로 규칙**:
- 사용자 지정 > PROJECT.md 문서 테이블에서 와이어프레임 경로 매칭 > 기본값(`docs/wireframes/`)
- 네이밍: URL 경로 기반 kebab-case — `{path-segment}.md` (예: `/login` -> `login.md`, `/mypage/order` -> `mypage-order.md`)
- 인덱스: 복수 URL 처리 시 `_index.md` 자동 생성/갱신

**인덱스 파일 형식** (`_index.md`):

```markdown
# 와이어프레임 인덱스

> 생성일: {YYYY-MM-DD HH:mm}
> 총 {N}개 화면

| # | 화면명 | URL 경로 | 파일 | 접근 권한 |
|---|--------|---------|------|----------|
| 1 | {화면명} | {path} | {filename}.md | {권한} |
```

**복수 URL 병렬 처리**: 기존 wtm-agent 구조 그대로 활용. wireframe 모드도 서브에이전트 디스패치 프롬프트에 모드를 전달하면 됨.

---

#### Step 2: network-guide.md — diagnosis.json 스키마 확장 + 참조 산출물 가이드 + 워커 프롬프트 확장

**A. 참조 산출물 가이드 섹션 추가** (새로운 섹션 "10. 외부 참조 산출물"):

opwt가 관리하는 8종 산출물 외에, 다른 도구/스킬이 생성한 문서를 "참조 산출물"로 활용할 수 있음을 정의한다.

```markdown
## 10. 외부 참조 산출물

opwt 관리 산출물(필수 4종 + 선택 4종) 외에, 프로젝트에 존재하는 외부 문서를 참조하여 작성 품질을 높일 수 있다.
참조 산출물은 opwt가 직접 생성/관리하지 않으며, "읽기 전용"으로 활용한다.

### 참조 산출물 유형

| 유형 | 설명 | 활용 대상 문서 | 활용 방법 |
|------|------|--------------|----------|
| `wireframe` | 화면 와이어프레임 분석 문서 (.md) | 서비스 정책서, IA | 화면 구성요소/기능 동작으로 정책 상세화, IA 기능 정의 보완 |
| `erd` | ERD 모델링 산출물 (Mermaid, DBML) | 서비스 정책서, TRD | 엔티티/속성으로 정책 데이터 규칙 검증, TRD 데이터 모델 정합성 |
| `api-spec` | API 명세서 (OpenAPI, 마크다운 등) | TRD, 서비스 정책서 | API 엔드포인트/파라미터로 TRD 기술 구현 보완, 정책 규칙 반영 확인 |

### 참조 산출물 획득

PM이 Phase 2 진단 시 프로젝트에서 참조 산출물을 스캔한다:
1. `docs/PROJECT.md` 문서 테이블에서 참조 산출물 경로 탐색
2. 사용자가 직접 경로를 제공
3. 프로젝트 내 일반적 경로 스캔 (docs/wireframes/, docs/erd/, docs/api-spec/)

### 주의 사항
- opwt는 참조 산출물의 존재를 "문서 경로"로만 인지한다 (스킬 의존 없음)
- 참조 산출물이 없어도 opwt는 정상 동작한다 (선택적 보강)
- 참조 산출물의 생성/수정은 각 전담 스킬 또는 PM 오케스트레이션으로 해결
```

**B. diagnosis.json 스키마 확장** — 기존 스키마의 최상위에 `reference_artifacts[]` 필드 추가:

```json
{
  "project": "프로젝트명",
  "scan_path": "기존 문서 경로",
  "reference_artifacts": [
    {
      "id": "고유 식별자 (kebab-case)",
      "type": "wireframe | erd | api-spec",
      "name": "산출물명",
      "path": "파일 경로",
      "scope": "커버하는 범위 설명 (예: 로그인 화면, 회원 도메인 ERD)"
    }
  ],
  "documents": [ ... ]
}
```

새 필드 설명 테이블에 추가:

```
| `reference_artifacts` | 외부 참조 산출물 목록. opwt가 관리하지 않지만 작성 시 참조하는 문서 |
| `reference_artifacts[].type` | 참조 유형: wireframe, erd, api-spec |
| `reference_artifacts[].scope` | 커버 범위 (어떤 도메인/화면을 다루는지) |
```

**C. Phase 1 워커 프롬프트 확장** — 기존 "수행 작업" 뒤에 외부 참조 분석 지시 추가:

```
6. 프로젝트에 외부 참조 산출물(와이어프레임, ERD, API 명세서 등)이 있는지 확인한다.
   - docs/wireframes/, docs/erd/, docs/api-spec/ 경로 스캔
   - PROJECT.md 문서 테이블에서 관련 문서 탐색
   - 발견된 참조 산출물은 reference_artifacts에 기록한다.
```

**D. Phase 3 워커 프롬프트 확장** — 보강/재작성/신규 3종 모두에 참조 산출물 섹션 추가:

기존 `### 참조 문서` 블록 아래에 추가:

```
### 외부 참조 산출물
{reference_artifacts 목록과 경로 — 해당하는 것만}
- 와이어프레임: {경로} — 화면 구성요소/기능 동작 참조
- ERD: {경로} — 엔티티/속성/관계 참조
- API 명세서: {경로} — 엔드포인트/파라미터 참조
```

수행 작업에 추가:

```
N. 외부 참조 산출물이 제공된 경우, 해당 내용을 참조하여 작성한다.
   - 와이어프레임: 화면 구성요소와 기능 동작을 정책서/IA에 반영
   - ERD: 엔티티/속성 정의를 정책서 데이터 규칙에 반영
   - API 명세서: API 엔드포인트/파라미터를 TRD/정책서에 반영
```

---

#### Step 3: consistency-rules.md — 외부 참조 검증 섹션 + QA 워커 프롬프트 확장

**A. 외부 참조 검증 섹션** (새로운 "8. 외부 참조 산출물 검증 (External Reference Validation)" 섹션):

```markdown
## 8. 외부 참조 산출물 검증 (External Reference Validation)

diagnosis.json에 reference_artifacts가 존재하는 경우, 해당 참조 산출물과 opwt 산출물 간 정합성을 검증한다.

### 와이어프레임 ↔ IA

| 체크 항목 | 방향 | 기준 |
|-----------|------|------|
| 와이어프레임 화면이 IA 메뉴 구조에 매핑되는가 | WF → IA | 각 화면에 대응하는 IA 메뉴 존재 |
| 와이어프레임 기능 동작이 IA 기능 정의에 반영되었는가 | WF → IA | 주요 기능 누락 0건 |
| IA 기능의 화면 경로가 와이어프레임 URL과 일치하는가 | IA → WF | path 불일치 0건 |

### 와이어프레임 ↔ 서비스 정책서

| 체크 항목 | 방향 | 기준 |
|-----------|------|------|
| 와이어프레임 입력 필드의 검증 규칙이 정책서에 정의되었는가 | WF → 정책서 | 주요 입력 필드의 검증 규칙 커버 |
| 와이어프레임 기능 조건이 정책서 비즈니스 규칙과 일치하는가 | WF → 정책서 | 조건 불일치 0건 |

### ERD ↔ 서비스 정책서

| 체크 항목 | 방향 | 기준 |
|-----------|------|------|
| 정책서 데이터 규칙이 ERD 엔티티/속성과 정합하는가 | 정책서 → ERD | 정책에서 언급하는 데이터 항목이 ERD에 존재 |
| ERD 제약조건(NOT NULL, FK 등)이 정책 규칙을 반영하는가 | ERD → 정책서 | 필수 필드, 참조 무결성 일치 |
| 코드성 컬럼의 값 범위가 정책서 정의와 일치하는가 | ERD → 정책서 | 코드값 매핑 일치 |

### ERD ↔ TRD

| 체크 항목 | 방향 | 기준 |
|-----------|------|------|
| TRD 데이터 모델 기술이 ERD 구조와 일치하는가 | TRD → ERD | 테이블/컬럼 구조 정합 |
| ERD 인덱스/제약조건이 TRD 성능 요구사항을 충족하는가 | ERD → TRD | 주요 쿼리 대상 인덱스 존재 |

### API 명세서 ↔ TRD

| 체크 항목 | 방향 | 기준 |
|-----------|------|------|
| TRD API 설계가 API 명세서와 일치하는가 | TRD → API | 엔드포인트/메서드/파라미터 일치 |
| API 인증/권한 규칙이 TRD 보안 요구사항과 일치하는가 | API → TRD | 인증 방식 정합 |

### API 명세서 ↔ 서비스 정책서

| 체크 항목 | 방향 | 기준 |
|-----------|------|------|
| API 응답의 에러 코드/메시지가 정책서 예외 처리와 일치하는가 | API → 정책서 | 주요 에러 시나리오 커버 |
| 정책서 비즈니스 규칙이 API 파라미터 검증에 반영되었는가 | 정책서 → API | 검증 규칙 정합 |
```

**B. QA 워커 프롬프트 확장** — 기존 수행 절차에 추가:

```
8. diagnosis.json에 reference_artifacts가 있는 경우:
   a. 각 참조 산출물 파일을 Read한다
   b. 외부 참조 산출물 검증(8절) 체크 항목을 순회한다
   c. 검증 결과를 external_reference 배열에 기록한다
```

QA 출력 JSON에 `external_reference` 배열 추가:

```json
"external_reference": [
  {
    "pair": "와이어프레임 ↔ IA",
    "item": "체크 항목 내용",
    "result": "pass | fail | skip",
    "reason": "판단 근거"
  }
]
```

**C. 우선순위 기반 검증 확장** — 기존 Tier에 외부 참조 Tier 추가:

```
4. **Tier 4 (외부 참조)** — 와이어프레임↔IA, ERD↔서비스 정책서, API 명세서↔TRD (reference_artifacts 존재 시만)
```

---

#### Step 4: opwt SKILL.md 업데이트

**커버 범위 섹션 확장**:

기존 "**필수 4종**" / "**선택 4종**" 아래에 추가:

```
**외부 참조**: 와이어프레임, ERD, API 명세서 등 프로젝트 내 기존 문서를 참조하여 작성 품질 향상 (읽기 전용, 선택적)
```

**참조 가이드 섹션 확장**:

기존 `references/network-guide.md`, `references/consistency-rules.md` 설명에 외부 참조 관련 내용 추가:

```
- `references/network-guide.md` — 산출물 정의, 연결 맵, diagnosis.json 스키마, 워커 프롬프트, 배치 규칙, IA 형식, **외부 참조 산출물 가이드**
- `references/consistency-rules.md` — 유형 간/내 검증, QA 워커 프롬프트, **외부 참조 검증**
```

**Phase 2 PM 진단 설명 확장**:

기존 설명에 참조 산출물 스캔 단계 추가:

```
PM 직접 수행: 워커 결과 종합 → 교차 논리 검토 → 누락/불일치 진단 → **외부 참조 산출물 스캔** → 문서별 조치(보강/재작성/신규) → `diagnosis.json` 생성 → 배치 편성 → 사용자 진단 보고
```

**변경이력 추가**:

```
| v1.3 | 2026-04-01 | 외부 참조 산출물 지원 — diagnosis.json reference_artifacts[], 워커 프롬프트 확장, 외부 참조 검증 규칙 |
```

## 3. 실행 체크리스트

> 총 5개 Step

### Step 1: wtm wireframe 모드 추가
- [x] 완료
- **파일**: `skills/web-to-markdown/SKILL.md`
- **작업 내용**:
  - 추출 모드 테이블에 wireframe 행 추가
  - wireframe 모드 전용 섹션 추가 (실행 로직, WebFetch 프롬프트, 산출물 형식, 저장 경로 규칙, 인덱스 생성)
  - 복수 URL 병렬 처리에 wireframe 모드 전달 방법 명시
  - 변경이력 v1.3 추가
- **완료 기준**: wireframe 모드가 full/clean과 동등하게 문서화되고, 산출물 형식이 기획 관점(화면 개요, 구성요소, 기능 동작, 네비게이션, 데이터 I/O)으로 정의됨
- **테스트**: SKILL.md의 추출 모드 테이블에 3개 모드 존재, wireframe 산출물 형식이 5개 섹션 포함, 저장 경로 규칙에 docs/wireframes/ 기본값 명시
- **의존**: 없음

### Step 2: network-guide.md 참조 산출물 가이드 + diagnosis.json 확장
- [x] 완료
- **파일**: `opal/skills/opal-pilot-write-tech/references/network-guide.md`
- **작업 내용**:
  - "10. 외부 참조 산출물" 섹션 추가 (유형 정의, 활용 대상, 획득 방법, 주의 사항)
  - diagnosis.json 스키마에 `reference_artifacts[]` 필드 추가 (id, type, name, path, scope)
  - 필드 설명 테이블에 reference_artifacts 관련 행 추가
- **완료 기준**: 참조 산출물 3유형(wireframe, erd, api-spec)이 정의되고, diagnosis.json 스키마에 reference_artifacts 필드가 포함됨
- **테스트**: diagnosis.json 예시가 reference_artifacts를 포함, 유형별 활용 대상 문서가 명시됨
- **의존**: 없음

### Step 3: network-guide.md Phase 1/3 워커 프롬프트 확장
- [x] 완료
- **파일**: `opal/skills/opal-pilot-write-tech/references/network-guide.md`
- **작업 내용**:
  - Phase 1 워커 프롬프트에 외부 참조 산출물 스캔 지시 추가 (6번 항목)
  - Phase 3 보강/재작성/신규 3종 프롬프트 모두에 `### 외부 참조 산출물` 블록과 수행 작업 항목 추가
- **완료 기준**: Phase 1에서 reference_artifacts를 스캔하고, Phase 3에서 참조 산출물을 활용하여 작성하는 지시가 포함됨
- **테스트**: Phase 1 프롬프트에 "외부 참조 산출물" 키워드 존재, Phase 3 3종 프롬프트 모두에 `{reference_artifacts}` 관련 블록 존재
- **의존**: Step 2

### Step 4: consistency-rules.md 외부 참조 검증 + QA 확장
- [x] 완료
- **파일**: `opal/skills/opal-pilot-write-tech/references/consistency-rules.md`
- **작업 내용**:
  - "8. 외부 참조 산출물 검증" 섹션 추가 (WF↔IA, WF↔정책서, ERD↔정책서, ERD↔TRD, API↔TRD, API↔정책서)
  - QA 워커 프롬프트에 외부 참조 검증 절차(8번) 추가
  - QA 출력 JSON에 `external_reference` 배열 추가
  - 우선순위 기반 검증에 Tier 4 추가
- **완료 기준**: 6개 외부 참조 검증 쌍이 체크 항목과 함께 정의되고, QA 워커가 이를 수행할 수 있는 프롬프트가 완성됨
- **테스트**: 검증 쌍 6개 존재, QA 출력에 external_reference 배열 스키마 존재, Tier 4 명시됨
- **의존**: Step 2

### Step 5: opwt SKILL.md 업데이트
- [x] 완료
- **파일**: `opal/skills/opal-pilot-write-tech/SKILL.md`
- **작업 내용**:
  - 커버 범위에 "외부 참조" 항목 추가
  - Phase 2 PM 진단에 외부 참조 산출물 스캔 단계 추가
  - 참조 가이드 설명에 외부 참조 관련 키워드 추가
  - 변경이력 v1.3 추가
- **완료 기준**: SKILL.md가 외부 참조 산출물 지원을 인지하고, network-guide.md와 consistency-rules.md의 확장된 내용과 정합
- **테스트**: "외부 참조" 키워드가 커버 범위, Phase 2, 참조 가이드에 존재, 변경이력에 v1.3 기록
- **의존**: Step 2, Step 4

## 4. QA 체크리스트

### 기능 테스트
- [ ] wtm wireframe 모드가 추출 모드 테이블에 정의되었는가 (A1)
- [ ] wireframe 산출물 형식이 5개 섹션(화면 개요, 구성요소, 기능 동작, 네비게이션, 데이터 I/O)을 포함하는가 (A2)
- [ ] 저장 경로 규칙이 PROJECT.md 테이블 > docs/wireframes/ 기본값 순서로 정의되었는가 (A3)
- [ ] URL 경로 기반 kebab-case 네이밍이 정의되었는가 (A4)
- [ ] 복수 URL 처리 시 _index.md 자동 생성이 정의되었는가 (A5)
- [ ] diagnosis.json에 reference_artifacts[] 필드가 추가되었는가 (B1)
- [ ] network-guide.md에 참조 산출물 가이드 섹션이 존재하는가 (B2)
- [ ] Phase 3 보강/재작성/신규 프롬프트에 reference_artifacts 블록이 있는가 (B3)
- [ ] Phase 1 프롬프트에 외부 참조 분석 지시가 있는가 (B4)
- [ ] consistency-rules.md에 외부 참조 검증 6쌍이 정의되었는가 (C1)
- [ ] QA 워커 프롬프트에 외부 참조 검증 절차가 있는가 (C2)

### 일관성 테스트
- [ ] diagnosis.json 기존 필드(documents, batches)와 새 필드(reference_artifacts)가 충돌 없이 공존하는가
- [ ] opwt "문서가 인터페이스" 원칙이 유지되는가 (스킬 의존 없음, 문서 경로만 참조)
- [ ] 기존 8종 산출물 관리 구조에 변경이 없는가
- [ ] wtm 기존 full/clean 모드 정의가 영향받지 않는가
- [ ] consistency-rules 기존 7개 섹션이 변경 없이 유지되는가
- [ ] 참조 산출물 유형명(wireframe, erd, api-spec)이 모든 파일에서 동일하게 사용되는가

### 문서 품질
- [ ] 한국어 본문 + 영어 코드/필드명 규칙을 따르는가
- [ ] kebab-case 파일/폴더 네이밍을 따르는가
- [ ] 각 파일의 변경이력이 갱신되었는가

## 5. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| diagnosis.json 기존 파서가 reference_artifacts 필드를 무시하지 못할 수 있음 | PM 진단 시 오류 | reference_artifacts는 선택 필드(optional)로 정의, 없으면 빈 배열 또는 생략 가능하도록 명시 |
| wireframe 모드 산출물 형식이 실제 와이어프레임과 맞지 않을 수 있음 | 정보 누락/과잉 | 산출물 형식을 권장 구조로 정의, 실제 페이지에 맞게 섹션 생략/추가 허용 |
| 외부 참조 산출물이 없는 프로젝트에서 QA 오류 발생 | 불필요한 검증 실패 | Tier 4 검증은 reference_artifacts 존재 시만 수행, skip 처리 명확히 정의 |
| 소스(skills/web-to-markdown/) 수정 후 배포본(~/.opal/skills/web-to-markdown/) 동기화 누락 | 실행 시 구버전 사용 | 실행 체크리스트 완료 후 배포 동기화 단계 포함 (구현 단계에서 cp 수행) |
