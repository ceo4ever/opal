# GC CONVENTION REPORT — 2026-09-13T00-36-30

## 1. 헤더

- 실행 일시: 시작 2026-09-13 00:36 / 완료 2026-09-13 00:38 / 소요 약 2분
- 범위: `WorkStudio` / 대상 파일 11개
- 에이전트: `opal-convention-checker`
- 기준 문서: `docs/CONVENTIONS.md` (단일 문서 모델)
- 실행 설정: `workstudio/eslint.config.js`, `workstudio/tsconfig.json`, `workstudio/vitest.config.ts`
- 검사 상태: `pass` (`check_enabled: true`)
- 통합 판정: `PASS_WITH_ADVISORIES`
- APPLY 수행 여부: N (read-only 진단)

## 2. 요약 지표

| 지표 | 값 |
|---|---|
| 총 이슈 수 | 4 |
| 심각도 분포 | Critical 0 / High 0 / Medium 0 / Low 4 / Info 0 |
| 집행 수준 | Blocking 0 / Advisory 4 / Informational 0 |
| 자동 수정 가능 | 0 |
| 수동 조치 필요 | 4 |
| 파일별 상위 | `workstudio/BACKLOG.md` (1), `WorkStudioApp.tsx` (1), `FirstRunWelcome.test.tsx` (1), `WorkStudioApp.test.tsx` (1) |
| Critical/High 수 | 0 |

`@header`는 대상 코드 9개 모두 존재했고 `code-scan validate`가 성공했다. Electron 경계는 `contextIsolation: true`, `nodeIntegration: false`, `sandbox: true`와 preload 기반 IPC를 유지한다. ESLint, TypeScript typecheck, Vitest 52개 테스트도 모두 통과했다.

## 3. 수정 대상 (체크리스트)

### Critical (0건)

없음.

### High (0건)

없음.

### Medium (0건)

없음.

### Low (4건)

- [ ] GC-001 [`workstudio/BACKLOG.md:1`] 문서 파일명이 kebab-case가 아니다
  - 카테고리: 네이밍
  - 위반 기준: 프로젝트(`docs/CONVENTIONS.md` §언어 규칙, §네이밍 규칙/파일·폴더)
  - 설명: 대문자 파일명 `BACKLOG.md`가 전체 파일명 kebab-case 규칙과 일치하지 않는다.
  - 영향: 운영체제·도구별 경로 대소문자 처리 차이와 프로젝트 내 파일명 규칙 불일치가 남는다.
  - 해결 방안: 문서 SSOT와 모든 참조를 함께 검토하는 별도 문서 정비 태스크에서 `backlog.md` 등 합의된 kebab-case 이름으로 전환하거나, 표준 산출물 예외를 `docs/CONVENTIONS.md`에 명시한다.
  - 자동 수정: N
  - 참조: `docs/CONVENTIONS.md` §네이밍 규칙/파일·폴더
  - 집행 수준: Advisory — 기존 SSOT 경로 변경은 현재 WS-F101 기능 범위를 넘으며 참조 체인 검토가 필요하다.

- [ ] GC-002 [`workstudio/src/workstudio/WorkStudioApp.tsx:1`] React 컴포넌트 파일명이 kebab-case가 아니다
  - 카테고리: 네이밍
  - 위반 기준: 프로젝트(`docs/CONVENTIONS.md` §언어 규칙, §네이밍 규칙/파일·폴더)
  - 설명: PascalCase 파일명 `WorkStudioApp.tsx`가 전체 파일명 kebab-case 규칙과 일치하지 않는다.
  - 영향: 프로젝트 문서에 선언된 파일 탐색·생성 규칙과 실제 컴포넌트 경로가 달라진다.
  - 해결 방안: import 체인을 포함한 별도 정비에서 `workstudio-app.tsx`로 전환하거나 React 컴포넌트 파일 예외를 기준 문서에 명시한다.
  - 자동 수정: N
  - 참조: `docs/CONVENTIONS.md` §네이밍 규칙/파일·폴더
  - 집행 수준: Advisory — 기존 공개 컴포넌트 경로이며 이번 변경은 Project Registry 기능에 한정된다.

- [ ] GC-003 [`workstudio/src/workstudio/FirstRunWelcome.test.tsx:1`] 테스트 파일명이 kebab-case가 아니다
  - 카테고리: 네이밍
  - 위반 기준: 프로젝트(`docs/CONVENTIONS.md` §언어 규칙, §네이밍 규칙/파일·폴더)
  - 설명: PascalCase 기반 파일명 `FirstRunWelcome.test.tsx`가 전체 파일명 kebab-case 규칙과 일치하지 않는다.
  - 영향: 테스트 파일 탐색과 명명 관례가 프로젝트 기준과 불일치한다.
  - 해결 방안: import·테스트 설정 영향을 확인한 뒤 `first-run-welcome.test.tsx`로 전환하거나 테스트 파일 예외를 기준 문서에 명시한다.
  - 자동 수정: N
  - 참조: `docs/CONVENTIONS.md` §네이밍 규칙/파일·폴더
  - 집행 수준: Advisory — 기존 테스트 파일의 범위 외 리네임이다.

- [ ] GC-004 [`workstudio/src/workstudio/WorkStudioApp.test.tsx:1`] 테스트 파일명이 kebab-case가 아니다
  - 카테고리: 네이밍
  - 위반 기준: 프로젝트(`docs/CONVENTIONS.md` §언어 규칙, §네이밍 규칙/파일·폴더)
  - 설명: PascalCase 기반 파일명 `WorkStudioApp.test.tsx`가 전체 파일명 kebab-case 규칙과 일치하지 않는다.
  - 영향: 테스트 파일 탐색과 명명 관례가 프로젝트 기준과 불일치한다.
  - 해결 방안: import·테스트 설정 영향을 확인한 뒤 `workstudio-app.test.tsx`로 전환하거나 테스트 파일 예외를 기준 문서에 명시한다.
  - 자동 수정: N
  - 참조: `docs/CONVENTIONS.md` §네이밍 규칙/파일·폴더
  - 집행 수준: Advisory — 기존 테스트 파일의 범위 외 리네임이다.

### Info (0건)

없음.

## 4. 검사 카테고리

| 카테고리 | 상태 | 근거 |
|---|---|---|
| 네이밍 | 활성 | 파일명과 신규 식별자를 `docs/CONVENTIONS.md` 기준으로 검사 |
| 들여쓰기 | 활성 | `git diff --check`, 탭·trailing whitespace 검색, ESLint 통과 |
| 파일 구조 | 활성 | 대상 경로가 `workstudio/` 및 task capsule 경계와 일치 |
| 죽은 코드 | 활성 | ESLint 정적 검사 통과 |
| 미사용 import | 활성 | ESLint 정적 검사 통과 |
| 문서화/@header | 활성 | 대상 코드 파일의 인라인 `@header`와 `code-scan validate` 확인 |
| import 순서 | 비활성 | `docs/CONVENTIONS.md`와 실행 설정에 구체적 정렬 규칙이 없음 |
| 코드 품질 | 비활성 | 프로젝트 기준에 정량 규칙이 없음 |
| Electron 보안 경계 | 활성 | BrowserWindow 보안 옵션과 preload IPC 경계 확인 |
| 테스트 규칙 | 활성 | Vitest 4 files / 52 tests, TypeScript typecheck 통과 |

## 5. 문서 업데이트 제안

- [ ] GC-DP-C001 [빈도 트리거] React 컴포넌트·테스트의 PascalCase 파일명이 3개 파일에서 관측됨 → `docs/CONVENTIONS.md`에 React 컴포넌트 파일명 예외를 둘지, 기존 파일을 kebab-case로 정비할지 결정 권장.

## 6. 증거

- `state-tool event-verify --event worker.dispatch --receipt /tmp/opal-worker-dispatch-convention.pJE8mO` → `ok: true`
- 입력 11개 파일의 존재·`project_root` 내부 경로 확인 완료
- `~/.opal/tools/code-scan/run.sh target <file>` → 전 대상 `write_to: inline`
- `~/.opal/tools/code-scan/run.sh validate ...` → `validate: OK`
- `git diff --check` → 출력 없음
- `npm run lint -- --max-warnings=0` → exit 0
- `npm run typecheck` → exit 0
- `npm run test -- --run` → 4 files, 52 tests passed

## 7. 차단 항목

없음. Critical/High 및 blocking finding은 0건이다.
