<!--
@module opal-pilot-gc
@layer reference
@domain convention
@description opal-convention-checker가 생성하는 GC-CONVENTION 보고서 샘플
@audience opal-pilot-gc 개발자 / 보고서 포맷 검수자
-->

# GC CONVENTION REPORT — 샘플

> 본 문서는 `opal-pilot-gc` CHECK 단계에서 `opal-convention-checker`가 생성하는 컨벤션 보고서의 **샘플**입니다.
> 실사용 시 `tasks/{NNN}-opgc-{요약}/GC-CONVENTION-{타임스탬프}.md`로 저장됩니다.

## 1. 헤더

- 실행 일시: 2026-04-17 14:30:18 ~ 14:31:05 (소요 47초)
- 범위: `staged` / 대상 파일 12개
- 에이전트: `opal-convention-checker`
- APPLY 수행: ✅ (승인 모드 A)

## 2. 요약 지표

| 지표 | 값 |
|------|-----|
| 총 이슈 수 | 14 |
| 심각도 분포 | Critical 0 / High 0 / Medium 1 / Low 10 / Info 3 |
| 자동 수정 가능 | 11 |
| 수동 조치 필요 | 3 |
| 파일별 상위 Top 3 | `src/utils/helper.ts` (4), `src/components/Button.tsx` (3), `src/api/userApi.ts` (2) |
| 카테고리별 빈도 | **naming-convention (4 파일) — 빈도 트리거 발동 (N≥3)** |
| Critical/High 수 | 0 |
| 문서 업데이트 제안 수 | 1 |

## 3. 수정 대상 (체크리스트)

### Medium (1건)

- [?] GC-101 [src/api/userApi.ts:45] 함수 복잡도 초과 (cyclomatic complexity 15)
  - 카테고리: 코드 복잡도
  - 위반 기준: 프로젝트(CONVENTIONS.md §3.2)
  - 해결 방안: 함수 분리 또는 전략 패턴 적용
  - 자동 수정: N
  - 참조: TBD — CONVENTIONS.md §3.2 (복잡도 규칙 링크)
  - **확인 요청**: 비즈니스 로직 구조상 분리 방향이 여러 가지 — 설계 결정 필요

### Low (10건)

- [x] GC-102 [src/utils/helper.ts:3] 미사용 import `lodash/isEmpty`
  - 카테고리: unused-import
  - 위반 기준: 프로젝트(CONVENTIONS.md §2.1)
  - 해결 방안: 해당 import 삭제
  - 자동 수정: Y
  - 참조: TBD — ESLint `no-unused-vars`
  - **적용 시각**: 2026-04-17 14:30

- [x] GC-103 [src/utils/helper.ts:5] 미사용 import `dayjs`
  - 카테고리: unused-import
  - 위반 기준: 프로젝트(CONVENTIONS.md §2.1)
  - 자동 수정: Y
  - 참조: TBD — ESLint `no-unused-vars`
  - **적용 시각**: 2026-04-17 14:30

- [x] GC-104 [src/utils/helper.ts:12] 미사용 변수 `tempVar`
  - 카테고리: unused-variable
  - 위반 기준: 프로젝트(CONVENTIONS.md §2.1)
  - 자동 수정: Y
  - 참조: TBD — ESLint `no-unused-vars`
  - **적용 시각**: 2026-04-17 14:30

- [x] GC-105 [src/utils/helper.ts:28] 죽은 코드 (`if(false) { ... }`)
  - 카테고리: dead-code
  - 위반 기준: 프로젝트(CONVENTIONS.md §2.3)
  - 자동 수정: Y
  - 참조: TBD — ESLint `no-constant-condition`
  - **적용 시각**: 2026-04-17 14:30

- [!] GC-106 [src/components/Button.tsx:15] 네이밍 규칙 위반 (snake_case `on_click` → camelCase `onClick`)
  - 카테고리: naming-convention
  - 위반 기준: 프로젝트(CONVENTIONS.md §1.1)
  - 자동 수정: Y (시도됨)
  - 참조: TBD — CONVENTIONS.md §1.1 (네이밍 규칙 링크)
  - **실패 사유**: prop 이름이 공개 API 인터페이스 — 자동 변환 시 외부 의존성 파손 위험
  - **권장**: 병행 API 제공 + Deprecation 후 제거

- [x] GC-107 [src/components/Button.tsx:22] 네이밍 규칙 위반 (snake_case `is_loading` → camelCase)
  - 카테고리: naming-convention
  - 위반 기준: 프로젝트(CONVENTIONS.md §1.1)
  - 자동 수정: Y
  - 참조: TBD — CONVENTIONS.md §1.1
  - **적용 시각**: 2026-04-17 14:30

- [x] GC-108 [src/components/Button.tsx:30] 네이밍 규칙 위반 (PascalCase 함수명 `HandleClick` → camelCase)
  - 카테고리: naming-convention
  - 위반 기준: 프로젝트(CONVENTIONS.md §1.1)
  - 자동 수정: Y
  - 참조: TBD — CONVENTIONS.md §1.1
  - **적용 시각**: 2026-04-17 14:30

- [x] GC-109 [src/api/userApi.ts:10] import 순서 (외부 → 내부 정렬 위반)
  - 카테고리: import-order
  - 위반 기준: 프로젝트(CONVENTIONS.md §2.2)
  - 자동 수정: Y
  - 참조: TBD — ESLint `import/order`
  - **적용 시각**: 2026-04-17 14:30

- [~] GC-110 [src/legacy/old-helper.js:50] 네이밍 규칙 위반 (레거시 다수)
  - 카테고리: naming-convention
  - 위반 기준: 프로젝트(CONVENTIONS.md §1.1)
  - 자동 수정: Y (가능하나)
  - 참조: TBD — CONVENTIONS.md §1.1
  - **보류 사유**: 레거시 파일 — 2026 Q2 전체 리팩토링 예정

- [x] GC-111 [src/hooks/useAuth.ts:8] 미사용 import `React`
  - 카테고리: unused-import
  - 위반 기준: 프로젝트(CONVENTIONS.md §2.1)
  - 자동 수정: Y
  - 참조: TBD — ESLint `no-unused-vars`
  - **적용 시각**: 2026-04-17 14:30

### Info (3건)

- [ ] GC-112 [src/index.ts:1] 파일 헤더 주석 권장
  - 카테고리: documentation
  - 위반 기준: 프로젝트(CONVENTIONS.md §4)
  - 해결 방안: `@module`, `@description` 블록 추가
  - 자동 수정: N
  - 참조: TBD — CONVENTIONS.md §4 (파일 헤더 규칙)

- [ ] GC-113 [src/components/Button.tsx:1] 컴포넌트 props 문서화 누락
  - 카테고리: documentation
  - 위반 기준: 프로젝트(CONVENTIONS.md §4)
  - 해결 방안: TSDoc으로 props 타입·설명 작성
  - 자동 수정: N
  - 참조: TBD — TSDoc 가이드

- [ ] GC-114 [src/api/userApi.ts:1] 파일 헤더 주석 권장
  - 카테고리: documentation
  - 위반 기준: 프로젝트(CONVENTIONS.md §4)
  - 자동 수정: N
  - 참조: TBD — CONVENTIONS.md §4

## 4. 문서 업데이트 제안 (§9·§10)

- [ ] **빈번 이슈 명문화**: `naming-convention` 위반이 4개 파일에서 발견 — **빈도 트리거 발동 (N=4 ≥ 임계값 3)**. CONVENTIONS.md §1.1에 "공개 API 인터페이스(props 등)는 자동 변환 시 병행 제공 후 Deprecation" 보조 규칙 추가 권장.

## 5. 문서 작성 유도

- `docs/CONVENTIONS.md` 존재 확인 ✅ — 작성 유도 안내 없음.
