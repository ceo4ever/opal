# TASK: .md @header 필드 재정의 — 기획/설계 layer 5개 + depends 설명 보강

> 작성일: 2026-04-12 | 작업 유형: 개선 | 적용 스킬: opp | 모드: agentic
> 입력: 사용자 요청 + PM 대화 검토
> 출력: TASK.md

## 작업 목표

`opal/core/references/header-standard.md`에 기획/설계 산출물용 layer 5개를 추가하고, `depends` 필드 설명에 layer별 값 기준 예시를 보강한다.

## 배경

현재 `header-standard.md`의 문서 layer 표준값(`spec` / `analysis` / `report` / `skill` / `task` / `plan` / `reference`)은 기획 산출물 유형을 커버하지 못한다. 정책서, IA, 와이어프레임, ERD, API 명세 등 기획/설계 문서에 @header를 적용하려면 적합한 layer 값이 없다.

## 배경 분석 (대화에서 도출)

**현재 상태 (`opal/core/references/header-standard.md`)**:
- §2 문서 layer: `spec` / `analysis` / `report` / `skill` / `task` / `plan` / `reference` — 기획/설계 유형 없음
- §2 `depends` 필드: "이 파일이 의존하는 모듈/외부 API 목록"으로만 정의됨, 문서명 참조 사례 미기재
- §4 exports 가이드: 위 7개 layer에 대한 안내만 존재, 기획/설계 layer 안내 없음

**검토 과정에서 확인한 사항**:
- `depends` 혼재 문제: 코드 파일(module ID, kebab-case)과 기획/설계 문서(문서명, 한국어+언더스코어)의 값 형식이 달라 code-scan 쿼리에서 자연 분리됨 → 혼재 허용
- `module-type` 필드: layer 값으로 코드/문서 구분이 이미 가능하므로 불필요
- `design` 통합 vs `ia`+`wireframe` 분리: 프레임워크 범용성 및 code-scan 정밀도를 위해 분리 결정

## 확정된 설계 방향 (대화에서 합의)

1. **신규 layer 5개 추가** (기존 `spec`/`analysis` 등과 동급, 문서 layer 섹션에 편입):
   - `policy` — 정책서 (운영 규칙, 산정 기준, 정책 체계)
   - `ia` — IA, 사이트맵, 네비게이션 구조
   - `wireframe` — 와이어프레임, 화면 설계
   - `erd` — ERD, 데이터 모델
   - `api-spec` — 외부 API 명세 (서드파티/연동)

2. **`depends` 필드 설명 보강**: 필드 정의표에 layer별 값 기준 예시 추가
   - 코드 파일: module ID (kebab-case) 기준
   - 기획/설계 문서: 참조 문서명 기준 (한국어+언더스코어 형식도 허용)
   - 두 형식이 혼재되어도 code-scan 쿼리에서 자연 분리되므로 허용

3. **`module-type` 필드**: 추가하지 않음

## 요구사항

- [x] **R1** §2 layer 표준값에 기획/설계 layer 5개 추가
  - 무엇을: 문서 layer 표준값에 `policy` / `ia` / `wireframe` / `erd` / `api-spec` 추가
  - 어디에: `opal/core/references/header-standard.md` §2 "layer 표준값" 섹션
  - 왜: 기획 산출물에 @header 적용 시 적합한 layer 값 부재
  - AC: 문서 layer 목록에 5개 값이 모두 존재하고, 기존 7개와 함께 나열되어 있다

- [x] **R2** §2 `depends` 필드 설명 보강
  - 무엇을: depends 필드 설명에 "(코드 파일: module ID, 기획/설계 문서: 참조 문서명)" 예시 추가
  - 어디에: `opal/core/references/header-standard.md` §2 필드 정의 테이블 `depends` 행
  - 왜: layer에 따라 depends 값 기준이 달라지므로 혼동 방지를 위해 명시 필요
  - AC: `depends` 행 설명에 두 가지 값 기준(module ID / 문서명)이 예시와 함께 기재되어 있다

- [x] **R3** §4 exports 가이드에 신규 layer 5개 행 추가
  - 무엇을: `policy` / `ia` / `wireframe` / `erd` / `api-spec` layer의 exports 작성 가이드 행 추가
  - 어디에: `opal/core/references/header-standard.md` §4 exports 작성 가이드 테이블
  - 왜: 신규 layer 사용 시 exports에 무엇을 쓸지 가이드 없으면 일관성 결여
  - AC: §4 테이블에 5개 신규 layer 행이 모두 존재하고, 각 행에 "exports에 담는 내용"과 "예시"가 채워져 있다

- [x] **R4** §3 Markdown 예시 갱신 (선택)
  - 무엇을: Markdown @header 예시를 `layer: "policy"`로 교체하고 `depends`에 문서명 형식 추가
  - 어디에: `opal/core/references/header-standard.md` §3 "Markdown (HTML comment)" 예시
  - 왜: 기존 예시(`spec` layer, depends 없음)가 신규 기획 문서 사용 패턴을 보여주지 못함
  - AC: Markdown 예시에 `layer: "policy"` 또는 기획/설계 layer 중 하나가 사용되고, `depends`에 문서명 형식 값이 포함되어 있다

- [x] **R5** 변경이력 추가
  - 무엇을: v1.1 변경이력 행 추가
  - 어디에: `opal/core/references/header-standard.md` 변경이력 섹션
  - AC: 변경이력 테이블에 v1.1 행이 추가되어 있고, 변경 내용이 기재되어 있다

## 제약 조건

- **배포 금지**: `~/.opal/` 경로 직접 수정 불가. 소스 파일(`opal/core/references/header-standard.md`) 수정 후 배포는 캡틴이 결정
- 기존 코드 layer 표준값 및 7개 문서 layer 값은 변경하지 않는다
- §1, §3(Markdown 제외), §5, §6은 수정 대상 아님

## 기술 스택

- Markdown 문서 편집

## 관련 문서

- `opal/core/references/header-standard.md` — 수정 대상 (소스)
- `~/.opal/references/header-standard.md` — 배포본 (수정 금지)
