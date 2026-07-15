# GC CONVENTION REPORT — 2026-07-15T18-10

## 1. 헤더

- 실행 일시: 시작 2026-07-15 18:04:00 / 완료 2026-07-15 18:10:00 / 소요 6분
- 범위: `all` (BE Python + FE TypeScript, 단일 호출) / 대상 파일 12개(진단) + 1개(제외 판단)
- 에이전트: opal-convention-checker
- 기준 문서: `docs/CONVENTIONS.md` 존재 — 단일 허브 문서(OPAL 자체 프로젝트, 문서 자체가 "OPAL 프레임워크 자체는 단일 docs/CONVENTIONS.md를 사용한다"고 명시 — 허브+링크 미적용). scope 파라미터 미지정 → 허브 전체 적용.
- APPLY 수행 여부: N (수동 대기) — 본 에이전트는 진단 전담, 소스 미수정

**대상 파일** (12개): `dashboard/backend/adapters/brain_session.py`, `dashboard/backend/models.py`, `dashboard/backend/routers/brain.py`, `dashboard/backend/tests/test_brain.py`, `dashboard/frontend/src/pages/brain/BrainPage.tsx`, `dashboard/frontend/src/pages/brain/brain-storage.test.ts`, `dashboard/frontend/src/pages/brain/brain-new-conversation-prime.test.ts`, `dashboard/frontend/src/pages/brain/brain-job-polling.test.ts`, `dashboard/frontend/src/pages/brain/brain-navigation-guard.test.tsx`, `dashboard/frontend/src/components/app-shell/AppShell.tsx`, `dashboard/frontend/src/store/ui-store.ts`, `dashboard/frontend/src/test/setup.ts`, `docs/ARCHITECTURE.md`.

**제외 판단** (1개): `dashboard/frontend/src/components/ui/alert-dialog.tsx` — 아래 참조.
**진단 제외**: `package.json`, `package-lock.json` — 지시에 따라 컨벤션 진단 대상 아님.

### 제외 판단 — alert-dialog.tsx

`npx shadcn add`로 생성된 신규 벤더 컴포넌트(`git status` 확인 결과 untracked `??` — 이번 태스크에서 신규 추가)로, `@header` 블록이 없다. CONVENTIONS.md·`header-rules.md`에는 벤더/생성 코드에 대한 명시적 예외 조항이 없으나:

- 같은 디렉토리(`dashboard/frontend/src/components/ui/`)의 기존 shadcn 컴포넌트 26개(`badge.tsx`, `button.tsx`, `accordion.tsx` 등 전수) 전부 `@header` 없이 생성기 원형을 유지하고 있다(코드베이스 전반에 100% 일관된 기존 관례).
- 이 관례는 이전 GC 보고서(`tasks/061-260714-opd-콘솔-설정-화면/GC-CONVENTION-2607141828.md`)에서 `switch.tsx`/`label.tsx` 사례로 이미 "생성기 원형 유지" 관례에 따라 위반 미판정으로 확정된 바 있다.

따라서 본 파일도 동일 관례를 적용해 **위반으로 판정하지 않는다** (Critical/High/Medium/Low/Info 어디에도 포함하지 않음). CONVENTIONS.md에 이 관례를 명문화할 것을 §4에서 재차 제안한다.

---

## 2. 요약 지표

| 지표 | 값 |
|------|-----|
| 총 이슈 수 | 7 |
| 심각도 분포 | Critical 0 / High 0 / Medium 4 / Low 3 / Info 0 |
| 자동 수정 가능 | 0 |
| 수동 조치 필요 | 7 (배열 항목 판단·필드 보완 성격 — 단순 치환 아님) |
| 파일별 상위 Top 5 | dashboard/backend/tests/test_brain.py (1) / dashboard/frontend/src/pages/brain/BrainPage.tsx (1) / dashboard/backend/adapters/brain_session.py (1) / dashboard/frontend/src/pages/brain/brain-storage.test.ts (1) / dashboard/frontend/src/pages/brain/brain-new-conversation-prime.test.ts (1) |
| 카테고리별 빈도 | 문서화 — 헤더 정합성 (6 파일) / 네이밍 (2 파일) |
| Critical/High 수 | 0 |
| 문서 업데이트 제안 수 | 3 (빈도 트리거 2건 + 재상기 1건) |

**총평**: 대상 12개 파일 모두 CONVENTIONS.md §@header 규칙의 필수 필드(module/layer/domain/description) 자체는 준수한다. 발견된 이슈는 전부 `exports` 필드(필수 필드 또는 그 내용 정합성) 관련 문서화 이슈이며 기능 결함이 아니다. Critical/High 0건으로 **PM Gate 통과 기준 충족**.

---

## 3. 수정 대상 (체크리스트)

### Critical (0건)

### High (0건)

### Medium (4건)

- [ ] GC-C001 [dashboard/backend/tests/test_brain.py:7-30] @header `exports` 배열이 실제 클래스와 불일치 — 태스크 060에서 이미 지적된 드리프트가 태스크 063까지 미해결로 이월
  - 카테고리: 문서화 (헤더 정합성)
  - 위반 기준: 프로젝트(`docs/CONVENTIONS.md` §@header 규칙) + `opal/core/references/harness/header-rules.md` §파일 수정 시 "함수/엔드포인트 추가 → exports 갱신"
  - 설명: 실제 클래스 정의(`grep -n "^class " test_brain.py`)에는 `TestOpbrAdapterAllowedTools`(1243행)가 존재하지만 헤더 `exports` 목록에는 여전히 없다. 반대로 `TestConversationBrainSessionWarm`은 실존하지 않는데(실제로는 `TestConversationBrainSessionCold` 내부의 `test_warm_ask_uses_resume` 메서드로 흡수됨) 목록에 남아 있다. 이 두 드리프트는 `tasks/060-.../GC-CONVENTION-2607141612.md` GC-C001에서 이미 Medium으로 지적됐다. 이번 태스크(063)의 diff가 정확히 같은 `exports` 배열 줄에 `"TestBrainPoolT063NeedBasedFill"`을 추가했음(`git diff` 확인)에도 기존 드리프트 2건은 함께 정정되지 않았다 — 같은 필드를 수정하면서 정합화 기회를 다시 놓쳤다. `code-scan exports` 조회 시 계속 잘못된 결과를 유발한다.
  - 해결 방안: `exports` 배열에서 `TestConversationBrainSessionWarm` 제거, `TestOpbrAdapterAllowedTools` 추가.
  - 자동 수정: N (배열 항목 판단 필요)
  - 참조: `opal/core/references/harness/header-rules.md` §파일 수정 시

- [ ] GC-C002 [dashboard/frontend/src/pages/brain/BrainPage.tsx:7] @header `exports` 배열에 이번 태스크(R-8)에서 신규 추가된 export 4건 누락
  - 카테고리: 문서화 (헤더 정합성)
  - 위반 기준: 프로젝트(`docs/CONVENTIONS.md` §@header 규칙) + `header-rules.md` §파일 수정 시 "함수/엔드포인트 추가 → exports 갱신"
  - 설명: 헤더 `exports`는 `["BrainPage", "addPendingTurn", "resolvePendingTurn", "makeSessionId", "projectDisplayName", "jobResponseToResolution", "jobPollingInterval", "BrainJobResponse"]`이지만, 실제 파일에는 `export const BRAIN_LEAVE_GUARD_TITLE`(53행, 이번 R-8 작업에서 신규), `export const BRAIN_LEAVE_GUARD_DESCRIPTION`(54행, 신규), `export type BrainState`(66행), `export interface BrainTurn`(108행) 4건이 추가로 export되어 있으나 목록에 없다. 특히 `BRAIN_LEAVE_GUARD_TITLE`/`DESCRIPTION`은 이번 태스크에서 신설된 심벌인데도 반영되지 않았다.
  - 해결 방안: `exports` 배열에 `"BRAIN_LEAVE_GUARD_TITLE"`, `"BRAIN_LEAVE_GUARD_DESCRIPTION"`, `"BrainState"`, `"BrainTurn"` 추가.
  - 자동 수정: N (배열 항목 판단 필요)
  - 참조: `opal/core/references/harness/header-rules.md` §파일 수정 시

- [ ] GC-C003 [dashboard/backend/adapters/brain_session.py:7] @header `exports` 배열에 외부에서 직접 import되는 `ConversationBrainSession` 누락
  - 카테고리: 문서화 (헤더 정합성)
  - 위반 기준: 프로젝트(`docs/CONVENTIONS.md` §@header 규칙) + `header-rules.md` §파일 생성 시 "필수 필드: exports"
  - 설명: 헤더 `exports`는 `["BrainSessionRegistry", "brain_session_registry"]`뿐이지만, `test_brain.py`가 `from dashboard.backend.adapters.brain_session import ConversationBrainSession`을 다수 지점(예: 530, 553, 591행 등)에서 직접 import해 사용한다 — 사실상 공개 API다. 하위 호환 별칭 `brain_session`(728행)도 목록에 없다.
  - 해결 방안: `exports` 배열에 `"ConversationBrainSession"` 추가(적어도). `brain_session` 별칭은 정책 판단(하위호환 전용이면 note 필드로 대체 가능).
  - 자동 수정: N (배열 항목 판단 필요)
  - 참조: `opal/core/references/harness/header-rules.md` §파일 생성 시

- [ ] GC-C004 [dashboard/frontend/src/pages/brain/brain-storage.test.ts, brain-new-conversation-prime.test.ts, brain-job-polling.test.ts] @header 필수 필드 `exports` 자체가 누락(빈 배열조차 없음)
  - 카테고리: 문서화 (필수 필드 누락)
  - 위반 기준: 프로젝트(`docs/CONVENTIONS.md` §@header 규칙) + `header-rules.md` §파일 생성 시 "필수 필드: module, layer, domain, description, **exports**"
  - 설명: 3개 파일 모두 `module`/`layer`/`domain`/`description`/`task`/`scenarios`는 있으나 `exports` 키 자체가 헤더 JSON에 없다. `git diff`로 확인한 결과 세 파일 모두 이번 태스크에서 헤더의 `description`/`task`/`scenarios` 필드가 갱신됐으나(같은 `@header` 블록을 직접 수정) `exports` 필드는 추가되지 않았다 — 기존에도 없었고 이번에도 채워지지 않음. 같은 브레인 테스트 스위트의 신규 파일 `brain-navigation-guard.test.tsx`는 `"exports": []`를 정확히 포함하고 있어 대비된다(3파일 vs 1파일 — 빈도 트리거 대상, §4 참조).
  - 해결 방안: 세 파일 헤더에 `"exports": []` 추가(테스트 파일은 named export가 없으므로 빈 배열이 정확한 값).
  - 자동 수정: Y (필드 삽입 — 단순 추가, 값은 빈 배열)
  - 참조: `opal/core/references/harness/header-rules.md` §파일 생성 시

### Low (3건)

- [ ] GC-C005 [dashboard/frontend/src/pages/brain/BrainPage.tsx, dashboard/frontend/src/components/app-shell/AppShell.tsx] FE 컴포넌트 파일명이 PascalCase — CONVENTIONS.md 언어 규칙 표의 "파일/폴더 이름: English, kebab-case(Python 파일은 snake_case)"와 문자 그대로는 불일치
  - 카테고리: 네이밍
  - 위반 기준: 프로젝트(CONVENTIONS.md §언어 규칙 표 — 파일/폴더 이름 kebab-case)
  - 설명: 두 파일 모두 PascalCase를 사용하나, 이는 이번 태스크에서 새로 만든 패턴이 아니라 프론트엔드 전체(`DashboardPage.tsx`/`ProjectsPage.tsx`/`TasksPage.tsx`/`MemoryPage.tsx`/`DoctorPage.tsx`/`SettingsPage.tsx` 등 8개 이상)에 이미 일관되게 적용된 기존 관례다. 이 동일 항목은 `tasks/061-260714-opd-콘솔-설정-화면/GC-CONVENTION-2607141828.md` GC-C001에서 이미 Low로 지적되었고, CONVENTIONS.md는 아직 갱신되지 않았다(재확인 — §4).
  - 해결 방안: (a) 코드 리네이밍은 import 체인 영향으로 비권장. (b) CONVENTIONS.md §네이밍 규칙에 "React 컴포넌트를 export하는 `.tsx` 파일은 PascalCase 허용" 예외 조항 추가.
  - 자동 수정: N
  - 참조: TBD — 프로젝트 CONVENTIONS.md 개정 논의 필요 (React 커뮤니티 관례: https://react.dev/learn/your-first-component)

- [ ] GC-C006 [dashboard/frontend/src/store/ui-store.ts:1] @header에 `depends` 필드 누락 — 외부 패키지(`zustand`, `zustand/middleware`) 의존이 실제로 존재
  - 카테고리: 문서화
  - 위반 기준: 프레임워크 `header-rules.md`(CONVENTIONS.md §@header 규칙의 근거 문서) — "선택 필드: depends(외부 의존 있을 때)"
  - 설명: `import { create } from "zustand"`, `import { persist } from "zustand/middleware"`를 사용하지만 헤더에 `depends` 필드 자체가 없다. 동일 패턴이 `tasks/061-.../GC-CONVENTION-2607141828.md` GC-C002(`api.ts`의 `@tanstack/react-query` 누락)에서 이미 Low로 지적된 바 있다.
  - 해결 방안: 헤더에 `"depends": ["zustand"]` 추가.
  - 자동 수정: Y (필드 추가 — 단순 삽입)
  - 참조: `opal/core/references/harness/header-rules.md` §파일 생성 시

- [ ] GC-C007 [dashboard/frontend/src/test/setup.ts:1] @header에 `depends` 필드 누락 — 외부 패키지(`@testing-library/jest-dom`) 의존이 실제로 존재
  - 카테고리: 문서화
  - 위반 기준: 프레임워크 `header-rules.md` — "선택 필드: depends(외부 의존 있을 때)"
  - 설명: `import '@testing-library/jest-dom'`를 사용하지만 `depends` 필드가 없다(GC-C006과 동일 패턴).
  - 해결 방안: 헤더에 `"depends": ["@testing-library/jest-dom"]` 추가.
  - 자동 수정: Y (필드 추가 — 단순 삽입)
  - 참조: `opal/core/references/harness/header-rules.md` §파일 생성 시

### Info (0건)

---

## 4. 문서 업데이트 제안 (§9·§10, 트리거 발동 시만)

<!-- 빈도 트리거 (N=3, 대상 파일 수 기준) -->

- [ ] GC-DP-C001 [빈도 트리거] "@header exports 배열이 실제 export 목록과 불일치" (3개 파일: test_brain.py, BrainPage.tsx, brain_session.py) → CONVENTIONS.md §@header 규칙에 "파일 수정 시 exports 필드 정합성 재검증" 절차 명시 제안
  - 근거: 단일 실행 내 3개 파일 — 빈도 임계값 N=3 충족. 3건 모두 "필드는 존재하나 최신화 누락" 유형으로 동일 근본 원인(파일 수정 시 exports 갱신을 다른 변경보다 부수적으로 취급)을 공유한다.
  - 제안 내용: "@header 규칙(header-rules.md) §파일 수정 시 표에 '필드 존재 여부'뿐 아니라 '기존 exports 값의 정확성 재검증'을 명시 — 코드 리뷰/PM Gate 체크리스트에 exports-실제코드 대조 단계 추가."

- [ ] GC-DP-C002 [빈도 트리거] "@header 필수 필드 exports 자체 누락" (3개 파일: brain-storage.test.ts, brain-new-conversation-prime.test.ts, brain-job-polling.test.ts) → CONVENTIONS.md에 "테스트 파일 @header 최소 템플릿" 예시 추가 제안
  - 근거: 단일 실행 내 3개 파일 — 빈도 임계값 N=3 충족. 같은 스위트의 신규 파일(`brain-navigation-guard.test.tsx`)은 `"exports": []`를 정확히 포함해 대비된다 — 필수 필드 누락이 "몰라서"가 아니라 "기존 파일 복제 시 누락 검증 부재"임을 시사.
  - 제안 내용: "CONVENTIONS.md §@header 규칙에 layer:test 파일의 최소 템플릿 예시(module/layer/domain/description/exports/task/scenarios 7필드 전부 표기)를 코드 블록으로 추가 — exports 누락 재발 방지."

<!-- 재상기 (이전 보고서에서 이미 제안되었으나 미반영) -->

- [ ] GC-DP-C003 [재상기] "FE 컴포넌트 파일명 PascalCase 예외" 및 "shadcn 생성 파일 @header 예외" — CONVENTIONS.md 미반영 상태 지속 확인
  - 근거: `tasks/061-260714-opd-콘솔-설정-화면/GC-CONVENTION-2607141828.md` GC-DP-C001(PascalCase 예외)에서 이미 제안됐고, `switch.tsx`/`label.tsx` 사례(같은 보고서)에서 shadcn 생성 파일 예외 관례가 이미 적용됐으나, CONVENTIONS.md 본문에는 두 예외 모두 아직 명문화되지 않았다(이번 실행에서 `docs/CONVENTIONS.md` 전체 Read로 재확인).
  - 제안 내용: CONVENTIONS.md §네이밍 규칙에 "(a) React 컴포넌트 export `.tsx` 파일은 PascalCase 허용, (b) `npx shadcn add` 등 생성기 산출물은 원형 유지 시 @header 예외" 2개 조항을 함께 반영 — 두 실행(061, 063) 연속으로 동일 판단이 반복되고 있어 문서화 시급성이 높아짐.

---

## 5. 문서 작성 유도 (해당 시)

`docs/CONVENTIONS.md` 존재 — 작성 유도 생략.
