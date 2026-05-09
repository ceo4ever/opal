# PLAN: .md @header 필드 재정의 — 기획/설계 layer 5개 + depends 설명 보강

> 작성일: 2026-04-12
> 입력: TASK.md
> 출력: PLAN.md

## 1. 현황 조사

### 관련 파일

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| `opal/core/references/header-standard.md` | @header 표준 정의 소스 | **예** (유일한 수정 대상) |
| `~/.opal/references/header-standard.md` | 배포본 | 아니오 (수정 금지) |

### 현재 상태

`opal/core/references/header-standard.md` v1.0 (2026-04-12 초기 작성) 실제 확인 결과:

1. **§2 layer 표준값**:
   - 코드 layer 16개: `router` / `controller` / `service` / `repository` / `model` / `schema` / `middleware` / `util` / `config` / `page` / `component` / `composable` / `store` / `hook` / `api-client` / `test`
   - 문서 layer 7개: `spec` / `analysis` / `report` / `skill` / `task` / `plan` / `reference`
   - 기획/설계 layer 없음

2. **§2 `depends` 필드 설명** (필드 정의 테이블 행):
   - 현재: `"이 파일이 의존하는 모듈/외부 API 목록"` — layer별 값 기준 미기재

3. **§3 Markdown 예시**:
   - `layer: "spec"`, `depends` 필드 없음 — 기획/설계 문서 패턴 미반영

4. **§4 exports 가이드 테이블**:
   - 14개 layer 가이드 존재 (코드 11 + 문서 4: `spec`, `analysis`, `report`, `skill`)
   - `task`, `plan`, `reference` 가이드 없음 (기존 상태)
   - 기획/설계 5개 layer 가이드 없음

5. **변경이력**: v1.0 단일 행

### 영향 범위

- 단일 파일 수정 (`opal/core/references/header-standard.md`)
- 배포본(`~/.opal/references/header-standard.md`)은 수정하지 않으므로, 실제 에이전트 동작에는 배포 전까지 영향 없음
- code-scan.js 파서는 layer 값을 자유 문자열로 처리하므로, layer 추가에 따른 코드 변경 불필요

---

## 2. 구현 계획

### 파일 변경 계획

#### 신규 생성

| # | 파일 경로 | 역할 |
|---|----------|------|
| - | 없음 | - |

#### 수정

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| 1 | `opal/core/references/header-standard.md` | R1~R5 전체 반영 (§2 layer + depends, §3 예시, §4 exports, 변경이력) |

#### 삭제

| # | 파일 경로 | 사유 |
|---|----------|------|
| - | 없음 | - |

### 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | §2 layer 표준값에 기획/설계 5개 추가 (R1) | `header-standard.md` | 낮음 |
| 2 | §2 depends 필드 설명 보강 (R2) | `header-standard.md` | 낮음 |
| 3 | §3 Markdown 예시 갱신 (R4) | `header-standard.md` | 낮음 |
| 4 | §4 exports 가이드에 5개 행 추가 (R3) | `header-standard.md` | 낮음 |
| 5 | 변경이력 v1.1 추가 (R5) | `header-standard.md` | 낮음 |

> 모두 동일 파일이므로 순차 실행 필수. 순서는 문서 위→아래 흐름(§2→§3→§4→변경이력)을 따라 자연스러운 편집 순서로 배치.

### 핵심 설계

#### R1: §2 layer 표준값 — 기획/설계 layer 5개 추가

현재 문서 layer 줄(29행):

```
`spec` / `analysis` / `report` / `skill` / `task` / `plan` / `reference`
```

변경 후 — 기존 7개 뒤에 5개 추가하되, 가독성을 위해 기획/설계 그룹을 별도 줄로 분리:

```
**문서 layer**:
`spec` / `analysis` / `report` / `skill` / `task` / `plan` / `reference`

**기획/설계 layer**:
`policy` / `ia` / `wireframe` / `erd` / `api-spec`
```

> 기존 문서 layer 7개 값은 변경하지 않음. 기획/설계 layer를 별도 라벨로 구분하여 용도를 명확히 함.

#### R2: §2 depends 필드 설명 보강

현재 필드 정의 테이블의 `depends` 행 설명(20행):

```
이 파일이 의존하는 모듈/외부 API 목록
```

변경 후:

```
이 파일이 의존하는 모듈/외부 API 목록. 코드 파일: module ID(kebab-case), 기획/설계 문서: 참조 문서명 — 예: `["auth-service"]`, `["결제_정책서", "회원_ERD"]`
```

> 두 가지 값 기준(module ID / 문서명)을 한 줄에 예시와 함께 명시. 혼재 허용도 암묵적으로 보여줌.

#### R4: §3 Markdown 예시 갱신

현재 Markdown 예시(112~124행):

```html
<!--
@header {
  "module": "auth-spec",
  "layer": "spec",
  "domain": "auth",
  "description": "인증 모듈 기능 명세",
  "exports": ["로그인 플로우", "토큰 갱신 정책", "세션 만료 처리"]
}
-->
```

변경 후:

```html
<!--
@header {
  "module": "payment-policy",
  "layer": "policy",
  "domain": "payment",
  "description": "결제 정책 체계 정의",
  "exports": ["환불 정책", "부분결제 기준", "PG 수수료 산정"],
  "depends": ["결제_ERD", "PG연동_API명세"]
}
-->
```

> `layer: "policy"` 사용 + `depends`에 문서명 형식 값 포함 — 기획/설계 문서 패턴 예시.

#### R3: §4 exports 가이드에 5개 행 추가

현재 §4 테이블의 마지막 행은 `skill`. 그 아래에 5개 행 추가:

| layer | exports에 담는 내용 | 예시 |
|-------|-----------------|------|
| `policy` | 정책/규칙 항목 | `["환불 정책", "부분결제 기준", "PG 수수료 산정"]` |
| `ia` | 주요 화면/메뉴 구조 | `["GNB 구조", "마이페이지 IA", "결제 플로우"]` |
| `wireframe` | 화면/컴포넌트명 | `["로그인 화면", "상품 목록", "결제 확인 팝업"]` |
| `erd` | 엔티티/테이블명 | `["User", "Order", "Payment"]` |
| `api-spec` | API 엔드포인트 또는 서비스명 | `["POST /payments", "PG 결제 승인 API"]` |

#### R5: 변경이력 v1.1 추가

현재 변경이력 테이블(178행)에 v1.1 행 추가:

```
| v1.1 | 2026-04-12 | 기획/설계 layer 5개 추가 + depends 필드 설명 보강 + exports 가이드 확장 (113) |
```

---

## 3. 실행 체크리스트

> 총 5개 Step | Phase 1개
>
> | Phase | Step | 실행 | 비고 |
> |-------|------|------|------|
> | 1 | 1, 2, 3, 4, 5 | 순차 | 동일 파일, 위→아래 순서 |

### Step 1: §2 layer 표준값에 기획/설계 layer 5개 추가 (R1)
- [x] 완료
- **파일**: `opal/core/references/header-standard.md`
- **작업 내용**: §2 "layer 표준값" 섹션의 문서 layer 아래에 **기획/설계 layer** 라벨과 `policy` / `ia` / `wireframe` / `erd` / `api-spec` 5개 값 추가. 기존 문서 layer 7개는 그대로 유지.
- **완료 기준**: 문서 layer 7개 + 기획/설계 layer 5개가 모두 나열되어 있다. 기존 코드 layer 16개, 문서 layer 7개는 변경 없다.
- **테스트**: 해당 섹션을 Read하여 12개 문서/기획 layer 값 존재 확인
- **의존**: 없음

### Step 2: §2 depends 필드 설명 보강 (R2)
- [x] 완료
- **파일**: `opal/core/references/header-standard.md`
- **작업 내용**: §2 필드 정의 테이블 `depends` 행의 "설명" 셀에 layer별 값 기준 예시 추가. "코드 파일: module ID(kebab-case), 기획/설계 문서: 참조 문서명" + 구체 예시 기재.
- **완료 기준**: `depends` 행 설명에 두 가지 값 기준(module ID, 문서명)과 각각의 예시가 기재되어 있다.
- **테스트**: 해당 테이블 행을 Read하여 두 가지 예시 존재 확인
- **의존**: 없음

### Step 3: §3 Markdown 예시 갱신 (R4)
- [x] 완료
- **파일**: `opal/core/references/header-standard.md`
- **작업 내용**: §3 "Markdown (HTML comment)" 예시를 `layer: "policy"`, `domain: "payment"` 패턴으로 교체. `depends` 필드에 문서명 형식 값 2개 포함.
- **완료 기준**: Markdown 예시에 `"layer": "policy"`가 사용되고, `"depends"` 배열에 문서명 형식 값이 포함되어 있다.
- **테스트**: 해당 예시를 Read하여 policy layer + depends 문서명 형식 확인
- **의존**: 없음

### Step 4: §4 exports 가이드에 5개 행 추가 (R3)
- [x] 완료
- **파일**: `opal/core/references/header-standard.md`
- **작업 내용**: §4 exports 가이드 테이블에 `policy` / `ia` / `wireframe` / `erd` / `api-spec` 5개 행 추가. 각 행에 "exports에 담는 내용"과 "예시" 기재.
- **완료 기준**: §4 테이블에 5개 신규 layer 행이 모두 존재하고, 각 행에 내용/예시 기재됨.
- **테스트**: 해당 테이블을 Read하여 5개 행 존재 및 예시 채워짐 확인
- **의존**: 없음

### Step 5: 변경이력 v1.1 추가 (R5)
- [x] 완료
- **파일**: `opal/core/references/header-standard.md`
- **작업 내용**: 변경이력 테이블에 `v1.1 | 2026-04-12 | 기획/설계 layer 5개 추가 + depends 필드 설명 보강 + exports 가이드 확장 (113)` 행 추가.
- **완료 기준**: 변경이력에 v1.1 행이 존재하고, 태스크 번호(113)가 포함되어 있다.
- **테스트**: 해당 테이블을 Read하여 v1.1 행 존재 확인
- **의존**: 없음

---

## 4. QA 체크리스트

### 기능 테스트
- [x] R1: 문서 layer 기존 7개 + 기획/설계 5개 = 12개가 §2에 모두 나열되어 있는가
- [x] R2: `depends` 필드 설명에 module ID 예시와 문서명 예시가 모두 기재되어 있는가
- [x] R3: §4 exports 가이드 테이블에 `policy` / `ia` / `wireframe` / `erd` / `api-spec` 5개 행이 존재하는가
- [x] R4: §3 Markdown 예시에 기획/설계 layer(`policy`)와 `depends` 문서명 형식이 포함되어 있는가
- [x] R5: 변경이력에 v1.1 행이 추가되어 있는가

### 일관성 테스트
- [x] 코드 layer 16개가 변경 없이 유지되는가
- [x] 기존 문서 layer 7개(`spec` ~ `reference`)가 변경 없이 유지되는가
- [x] 신규 layer 값이 kebab-case를 따르는가 (`policy`, `ia`, `wireframe`, `erd`, `api-spec`)
- [x] §4 exports 가이드의 기존 행(router ~ skill)이 변경 없이 유지되는가
- [x] Markdown 예시가 JSON 문법에 맞는가 (따옴표, 콤마, 괄호)

### 문서 품질
- [x] 한국어 본문 + 영어 코드/필드명 규칙을 따르는가
- [x] Markdown 테이블 정렬이 깨지지 않았는가
- [x] 배포본(`~/.opal/references/header-standard.md`)이 수정되지 않았는가

---

## 5. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| §2 layer 표준값 줄에서 기존 값 실수로 삭제 | 기존 layer 참조 깨짐 | 기존 문서 layer 줄은 그대로 유지하고, 기획/설계 layer를 별도 줄로 추가 |
| depends 설명이 테이블 셀에서 너무 길어짐 | 가독성 저하 | 핵심 정보만 한 줄로 압축 + 예시는 인라인 코드 형식 사용 |
| Markdown 예시 JSON 문법 오류 | 파서 에러 | 작성 후 JSON 유효성 확인 |
