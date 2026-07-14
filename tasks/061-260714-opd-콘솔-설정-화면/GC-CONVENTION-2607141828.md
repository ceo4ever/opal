# GC CONVENTION REPORT — 2607141828

## 1. 헤더

- 실행 일시: 시작 2026-07-14 18:28:00 / 완료 2026-07-14 18:33:40 / 소요 5분 40초
- 범위: `all` (BE Python + FE TypeScript) / 대상 파일 12개
- 에이전트: opal-convention-checker
- 기준 문서: `docs/CONVENTIONS.md` 존재 — 단일 허브 문서(OPAL 자체 프로젝트, 허브+링크 미적용) 전체를 기준으로 적용. 상세 링크(FE/BE-CONVENTIONS.md 등) 없음 — 문서 자체가 "OPAL 프레임워크 자체는 단일 docs/CONVENTIONS.md를 사용한다"고 명시.
- APPLY 수행 여부: N (수동 대기) — 본 에이전트는 진단 전담, 소스 미수정

---

## 2. 요약 지표

| 지표 | 값 |
|------|-----|
| 총 이슈 수 | 3 |
| 심각도 분포 | Critical 0 / High 0 / Medium 0 / Low 2 / Info 1 |
| 자동 수정 가능 | 0 |
| 수동 조치 필요 | 3 (문서 보완/정책 판단 성격 — 코드 수정 불요 항목 다수) |
| 파일별 상위 Top 5 | dashboard/frontend/src/pages/settings/SettingsPage.tsx (1) / dashboard/frontend/src/components/app-shell/AppShell.tsx (1) / dashboard/frontend/src/lib/api.ts (1) / dashboard/backend/models.py (1) |
| 카테고리별 빈도 | 네이밍 (2 파일) / 문서화 (2 파일) |
| Critical/High 수 | 0 |
| 문서 업데이트 제안 수 | 1 (참고성 관찰 1건 — 엄격한 빈도 임계값 N=3 미충족이나 코드베이스 전반의 기존 패턴이므로 참고 표기) |

**총평**: 대상 12개 파일 모두 CONVENTIONS.md §@header 규칙(module/layer/domain/description/exports 필수 필드)을 준수한다. shadcn 자동 생성 파일 2건(`switch.tsx`, `label.tsx`)은 헤더가 없으나 지시된 관례("생성기 원형 유지")에 따라 위반으로 판정하지 않았다. 범위 축소(save_project_local, ConsoleConfigUpdate, SettingLocalUpdate, POST /api/config/console, GET|POST /api/config/project-local 등 제거) 이후 잔재를 전수 grep했으나 실제 코드에서 죽은 참조·미사용 import는 발견되지 않았다 — changelog/description 텍스트에만 남아 있으며 이는 변경 이력 서술이므로 정상이다.

---

## 3. 수정 대상 (체크리스트)

### Critical (0건)

### High (0건)

### Medium (0건)

### Low (2건)

- [ ] GC-C001 [dashboard/frontend/src/pages/settings/SettingsPage.tsx, dashboard/frontend/src/components/app-shell/AppShell.tsx] FE 컴포넌트 파일명이 PascalCase — CONVENTIONS.md §네이밍 규칙(언어 규칙 표)의 "파일/폴더 이름: English, kebab-case(Python 파일은 snake_case)"과 문자 그대로는 불일치
  - 카테고리: 네이밍
  - 위반 기준: 프로젝트(CONVENTIONS.md §언어 규칙 / §네이밍 규칙 — 파일/폴더 kebab-case)
  - 설명: `SettingsPage.tsx`(신규)와 수정된 `AppShell.tsx`는 PascalCase 파일명을 사용한다. CONVENTIONS.md의 일반 파일 네이밍 규칙은 kebab-case를 명시하고 Python만 snake_case 예외를 두는데, React 컴포넌트 파일에 대한 별도 예외 조항은 없다. 다만 이는 이번 태스크에서 새로 만든 패턴이 아니라 `DashboardPage.tsx`/`ProjectsPage.tsx`/`TasksPage.tsx`/`MemoryPage.tsx`/`DoctorPage.tsx`/`BrainPage.tsx` 등 프론트엔드 전체에 이미 일관되게 적용된 기존 관례다.
  - 해결 방안: (a) 코드를 문서에 맞춰 kebab-case로 일괄 리네이밍 — import 체인 전체 영향으로 비용 큼, 권장하지 않음. (b) CONVENTIONS.md §네이밍 규칙에 "React 컴포넌트 파일(.tsx, 컴포넌트를 export하는 파일)은 PascalCase 허용" 예외 조항 추가 — 기존 코드베이스 실태와 일치시키는 문서 보정을 권장.
  - 자동 수정: N
  - 참조: TBD — 프로젝트 CONVENTIONS.md 개정 논의 필요 (React 커뮤니티 관례는 PascalCase가 일반적: https://react.dev/learn/your-first-component)

- [ ] GC-C002 [dashboard/frontend/src/lib/api.ts:1] @header에 `depends` 필드 누락 — 외부 패키지(`@tanstack/react-query`) 의존이 실제로 존재
  - 카테고리: 문서화
  - 위반 기준: 프레임워크 header-rules.md(CONVENTIONS.md §@header 규칙의 근거 문서) — "선택 필드: depends(외부 의존 있을 때)"
  - 설명: `api.ts`는 `import { QueryClient } from "@tanstack/react-query"`로 외부 패키지에 의존하지만 헤더에 `depends` 필드 자체가 없다. 동일 태스크의 다른 파일들(`SettingsPage.tsx`, `main.py` 등)은 depends 필드를 명시하는 것과 대비된다.
  - 해결 방안: 헤더에 `"depends": ["@tanstack/react-query"]` 추가.
  - 자동 수정: Y (필드 추가 — 단순 삽입)
  - 참조: `opal/core/references/harness/header-rules.md` §파일 생성 시 (내부 문서, 절대경로: /Volumes/Data/AIStudio/workspace/ai-framework/opal/core/references/harness/header-rules.md)

### Info (1건)

- [ ] GC-C003 [dashboard/backend/models.py:30] @header `depends: []`이나 실제로는 `pydantic`(외부 패키지) 의존
  - 카테고리: 문서화
  - 위반 기준: 프레임워크 header-rules.md — depends 선택 필드 (CONVENTIONS.md §@header 규칙 근거)
  - 설명: `from pydantic import BaseModel`을 사용하지만 depends가 빈 배열이다. 다만 pydantic·dataclasses 등 프레임워크 기반 라이브러리는 이 코드베이스 전반에서 관례적으로 depends에서 생략되는 경향이 있어(예: `config.py`도 stdlib만 사용해 depends: [] — 다만 config.py는 실제로 외부 의존이 없음) 엄격한 위반이라기보다 참고용 관찰이다.
  - 해결 방안: 필요 시 `"depends": ["pydantic"]`로 보완 (선택 사항, 강제 아님).
  - 자동 수정: N (정책 판단 필요 — 프레임워크 기반 의존을 depends에 포함할지는 팀 컨벤션 결정 사항)
  - 참조: TBD — 팀 내 depends 필드 범위(프레임워크 기반 라이브러리 포함 여부) 정책 확정 필요

---

## 4. 문서 업데이트 제안 (§9·§10, 참고성 관찰)

<!-- 엄격한 빈도 트리거(N=3, 대상 파일 수 기준)는 미충족 — 대상 12개 파일 내에서는 2개 파일만 해당. 다만 프로젝트 전체 프론트엔드 코드베이스 관점에서는 8개 이상 파일에 동일 패턴이 존재하여 참고용으로 제안한다. -->

- [ ] GC-DP-C001 [참고 관찰] "FE 컴포넌트 파일명 PascalCase" (대상 파일 내 2개: SettingsPage.tsx, AppShell.tsx / 프론트엔드 전체 기준 8개 이상) → CONVENTIONS.md §네이밍 규칙에 예외 조항 추가 제안
  - 근거: 대상 파일 기준으로는 빈도 임계값 N=3에 못 미치나(2개), `dashboard/frontend/src/pages/*/**.tsx` 전반에 이미 확립된 패턴 — 문서 미비로 인한 잠재적 반복 위반 소지
  - 제안 내용: "React 컴포넌트를 default/named export하는 `.tsx` 파일은 PascalCase를 허용한다 (예: `SettingsPage.tsx`, `AppShell.tsx`). 그 외 유틸/설정 파일은 기존 kebab-case 규칙을 유지한다."

---

## 5. 문서 작성 유도 (해당 시)

- `docs/CONVENTIONS.md` 존재 — 작성 유도 생략.
