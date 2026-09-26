# GC CONVENTION REPORT — 260918-1610-console-fe

## 1. 헤더

- 실행 일시: 시작 2026-09-18 16:10:00 / 완료 2026-09-18 16:13:30 (소요 약 3분 30초)
- 범위: `Console FE` (`dashboard/frontend/`) / 대상 파일 10개
- 에이전트: opal-convention-checker
- 기준 문서: `docs/CONVENTIONS.md` 존재 — 해당 문서 적용. `dashboard/frontend/`용 별도 `FE-CONVENTIONS.md`(허브+링크)는 부재해 단일 허브 문서만 적용했다.
- APPLY 수행 여부: N (수동 대기 — read-only 진단 전담)

---

## 2. 요약 지표

| 지표 | 값 |
|------|-----|
| 총 이슈 수 | 4 |
| 심각도 분포 | Critical 0 / High 0 / Medium 0 / Low 4 / Info 0 |
| 자동 수정 가능 | 4 |
| 수동 조치 필요 | 0 |
| 파일별 상위 Top 5 | `AppShell.tsx` (2) / `router.tsx` (2) |
| 카테고리별 빈도 | documentation (2 파일) — 빈도 트리거 미달 (N=2 < 3) |
| Critical/High 수 | 0 |
| 문서 업데이트 제안 수 | 0 |

**대상 영역 판정**: `docs/PROJECT.md` §프로젝트 구성 — `Console FE | dashboard/frontend/ | React, TypeScript, Vite, Tailwind, shadcn/ui | opal-fe-agent`.

**적용 기준 계층**:
- T0: `docs/CONVENTIONS.md` (네이밍·헤더·파일 구조), `dashboard/frontend/eslint.config.js` (실행 설정 — `@eslint/js` recommended, `typescript-eslint` recommended, `react-hooks`/`react-refresh` 규칙. import 그룹/순서 강제 규칙은 미설정)
- T2: 인접 코드 관측 패턴 (컴포넌트 파일 PascalCase, `@header task` 필드 표기 방식, import 블록 무공백 나열 등 — 기존 파일 전반에서 일관되게 관측되어 위반으로 판정하지 않음)

**비활성 영역과 이유**: 카테고리 8(코드 품질 — N+1 쿼리, O(n²), 불필요한 메모리 할당)은 대상 파일이 클라이언트 렌더링 코드로 DB 쿼리·대규모 루프 연산이 없어 해당 사항 없음. 카테고리 7(import 순서)은 T0 실행 설정(eslint.config.js)에 순서 강제 규칙이 없고, 기존 코드베이스 전반이 외부/내부 그룹을 공백 없이 나열하는 동일 패턴이므로 위반으로 판정하지 않음(T2 관측 패턴과 일치).

---

## 3. 수정 대상 (체크리스트)

### Critical (0건)

### High (0건)

### Medium (0건)

### Low (4건)

- [ ] GC-C001 [dashboard/frontend/src/components/app-shell/AppShell.tsx:6] `@header` description이 "좌측 7개 네비"로 기재됐으나 실제 `NAV_ITEMS`(line 90-99)는 8개 항목(대시보드/프로젝트/태스크/메모리/환경/프로젝트 브레인/OPAL Docs/설정)이다.
  - 카테고리: 문서화
  - 위반 기준: 프로젝트(header-standard.md §2.1 — "@header에는 현재 사실만 기재") / T0
  - 설명: 태스크 140에서 OPAL Docs 항목이 추가되며 개수가 7→8로 늘었지만 헤더 설명은 갱신되지 않았다.
  - 해결 방안: description의 "7개 네비"를 "8개 네비"로 수정
  - 자동 수정: Y
  - 참조: opal/core/references/header-standard.md §2.1

- [ ] GC-C002 [dashboard/frontend/src/components/app-shell/AppShell.tsx:82] 인라인 주석 "6개 네비 항목"이 실제 `NAV_ITEMS` 8개 항목과 불일치한다.
  - 카테고리: 문서화
  - 위반 기준: 프로젝트(header-standard.md §2.1) / T0
  - 설명: GC-C001과 동일 원인 — 항목 추가 시 인접 주석 미갱신
  - 해결 방안: 주석을 "8개 네비 항목"으로 수정하거나 개수 표기를 제거
  - 자동 수정: Y
  - 참조: opal/core/references/header-standard.md §2.1

- [ ] GC-C003 [dashboard/frontend/src/router.tsx:6] `@header` description이 "7개 라우트(/ /projects /tasks /memory /doctor /brain /settings)"로 기재됐으나 실제 `children`(line 29-41)은 9개 라우트이며 신설된 `/docs/skills`, `/docs/skills/:skillId`가 목록에서 빠졌다.
  - 카테고리: 문서화
  - 위반 기준: 프로젝트(header-standard.md §2.1) / T0
  - 설명: 태스크 140에서 OPAL Docs 라우트 2개가 추가됐지만 헤더 설명이 갱신되지 않았다.
  - 해결 방안: description의 라우트 개수·목록을 9개로 갱신하고 `/docs/skills`, `/docs/skills/:skillId`를 포함
  - 자동 수정: Y
  - 참조: opal/core/references/header-standard.md §2.1

- [ ] GC-C004 [dashboard/frontend/src/router.tsx:8] `@header` depends 배열이 `DocsCatalogPage`·`DocsDetailPage` import(line 22-23)를 반영하지 않는다.
  - 카테고리: 문서화
  - 위반 기준: 프로젝트(header-standard.md §2.1) / T0
  - 설명: depends 목록이 실제 import 구성보다 오래된 상태로 남아 있다.
  - 해결 방안: depends 배열에 `"docs-catalog-page"`, `"docs-detail-page"` 추가
  - 자동 수정: Y
  - 참조: opal/core/references/header-standard.md §2.1

### Info (0건)

---

## 4. 문서 업데이트 제안 (§9·§10)

트리거 미발동. 동일 카테고리(documentation)가 2개 파일에서만 발견돼 빈도 트리거 임계값(N=3)에 미달하며, 새 카테고리 등장도 없다.

---

## 5. 문서 작성 유도

`docs/CONVENTIONS.md` 존재 — 작성 유도 생략. Console FE 영역 전용 `FE-CONVENTIONS.md`는 없으나 현재 단일 문서로 커버 가능한 범위이므로 허브+링크 분리를 제안하지 않는다.

---

## 6. 참고 — 검토했으나 위반 아님

- **`AppShell.tsx`/`router.tsx`/`DocsCatalogPage.tsx`/`DocsDetailPage.tsx` import 블록 무공백 나열**: 외부→내부 그룹 사이 빈 줄이 없으나, 코드베이스 전역에서 관측되는 기존 패턴(T2)과 동일해 위반으로 판정하지 않음.
- **미사용 import/변수**: 대상 파일 전체에서 미사용 export·import 없음 (AppShell의 lucide 아이콘 전량 사용 확인, docs 페이지의 shadcn 컴포넌트 전량 사용 확인).
- **`DocsDetailPage.test.tsx`의 `Object.assign(navigator, { clipboard: ... })` 패턴**: `test/setup.ts` 헤더가 명시하듯 이 패턴은 happy-dom 기본 상태에서 실패하나, `setup.ts`가 `navigator.clipboard`를 `configurable: true, writable: true`로 선(先)폴리필하므로 테스트 시점에는 정상 동작한다(T140 W-8 대응 확인, setup.ts:14-20). 위반 아님.
- **`@header task` 필드 표기 방식**: 신규 파일(`DocsCatalogPage.tsx` 등)은 전체 태스크 폴더명(`140-260917-opdw-...`)을, 기존 일부 파일(`router.tsx` 등)은 짧은 번호(`061`)를 쓴다. 코드베이스 전역에 두 표기 모두 이미 혼재하는 T2 패턴이라(`vite-env.d.ts`, `api-timeout.test.ts` 등) 신규 위반으로 판정하지 않음.
- **`api.ts`의 `ApiError` additive 확장**: 기존 `Error` 상속 유지, 기존 호출자 시그니처 불변 — 컨벤션 위반 없음.

---

## 반환 요약

- status: completed
- check_status: pass (전 대상 검사 완료, `docs/CONVENTIONS.md` 기준 적용, 결측 없음)
- Critical 0 / High 0 / Medium 0 / Low 4 / Info 0
- Critical·High 없음
