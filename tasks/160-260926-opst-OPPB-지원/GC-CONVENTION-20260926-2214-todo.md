# GC CONVENTION REPORT — 20260926-2214-todo

## 1. 헤더

- 실행 일시: 시작 2026-09-26 22:14 / 완료 2026-09-26 22:19 / 소요 5분
- 범위: `all` / Task 160 TODO 추가 대상 15개
- 에이전트: `opal-convention-checker` fallback
- 기준 문서: `docs/CONVENTIONS.md`, `.opal/code-scan.json`
- baseline: `none`
- APPLY 수행 여부: N (read-only 진단)
- 검사 실행 상태: `pass` — 대상 15개 모두 검사, missing capability 없음
- 최종 판정: `FAIL` — T0 blocking finding 4건

> baseline이 `none`이므로 baseline delta는 finding 4건 모두 `new`다. 단, `code-scan`의 Git 기반 분류는 `README.md` 헤더 누락을 `pre_existing`, `_opal/AGENT.md` 헤더 누락을 `newly_uncovered`로 구분했다.

---

## 2. 요약 지표

| 지표 | 값 |
|------|-----|
| 총 이슈 수 | 4 |
| 심각도 분포 | Critical 0 / High 0 / Medium 0 / Low 4 / Info 0 |
| 집행 수준 | Blocking 4 / Advisory 0 / Informational 0 |
| 자동 수정 가능 | 0 |
| 수동 조치 필요 | 4 |
| 파일별 상위 | `_opal/AGENT.md` 2건 / `README.md` 1건 / `docs/PROJECT.md` 1건 |
| 카테고리별 빈도 | 문서화 4건(3개 파일) |
| `code-scan` 분류 | pre-existing 1 / newly-uncovered 1 |
| Critical/High 수 | 0 |
| 문서 업데이트 제안 수 | 0 |

`code-scan validate --scope framework --changed <15개 대상> --json`은 지원 확장자 9개 중 7개 covered(77.8%), `uncovered` 2건으로 exit 2를 반환했다. JSON·`_gitignore`·`.gitkeep` 6개는 unsupported extension으로 제외되었다.

---

## 3. 수정 대상 (체크리스트)

### Critical (0건)

없음.

### High (0건)

없음.

### Medium (0건)

없음.

### Low (4건)

- [ ] GC-001 [`opal/skills/opal-skill-tester/README.md:1`] 인라인 `@header` 누락 — pre-existing
  - 카테고리: 문서화
  - 위반 기준: T0 — `.opal/code-scan.json` `headerSource=inline`, `docs/CONVENTIONS.md` §구현 규칙/§@header 규칙
  - 설명: `code-scan validate`가 `uncovered/pre_existing`로 반환했다. TODO 추가가 처음 만든 결함은 아니지만, 명시 대상이므로 결과에서 제외하지 않았다.
  - 영향: 소스 코드맵 coverage가 불완전하고 결정론적 integrity validation이 exit 2로 실패한다.
  - 해결 방안: `code-scan target` 판정에 따라 파일 상단에 현재 사실만 담은 `@header` 블록을 추가한다.
  - 자동 수정: N
  - 검증: 동일 `code-scan validate --changed ... --json`에서 해당 `uncovered` 항목이 없고 exit 0이다.
  - 참조: `docs/CONVENTIONS.md` §구현 규칙/§@header 규칙

- [ ] GC-002 [`opal/skills/opal-skill-tester/scenarios/_bases/todo-web/_opal/AGENT.md:1`] 인라인 `@header` 누락 — newly-uncovered
  - 카테고리: 문서화
  - 위반 기준: T0 — `.opal/code-scan.json` `headerSource=inline`, `docs/CONVENTIONS.md` §구현 규칙/§@header 규칙
  - 설명: `code-scan validate`가 신규 파일의 `uncovered/newly_uncovered`로 반환했다.
  - 영향: 신규 Markdown이 코드맵 coverage에 포함되지 않고 결정론적 integrity validation이 exit 2로 실패한다.
  - 해결 방안: `code-scan target` 판정에 따라 파일 상단에 현재 사실만 담은 `@header` 블록을 추가한다.
  - 자동 수정: N
  - 검증: 동일 `code-scan validate --changed ... --json`에서 해당 `uncovered` 항목이 없고 exit 0이다.
  - 참조: `docs/CONVENTIONS.md` §구현 규칙/§@header 규칙

- [ ] GC-003 [`opal/skills/opal-skill-tester/scenarios/_bases/todo-web/_opal/AGENT.md:1`] 문서 본문이 영어로만 작성됨
  - 카테고리: 문서화
  - 위반 기준: T0 — `docs/CONVENTIONS.md` §언어 규칙 (문서 본문은 한국어, 기술 용어는 영어 병기)
  - 설명: 제목·역할·검토 항목·제약이 모두 영어로 작성되어 있다. 기술 용어 병기 범위를 넘는다.
  - 영향: OPAL 프레임워크 문서의 표준 언어와 일관성이 깨진다.
  - 해결 방안: 기술 식별자·경로는 영어로 유지하고, 설명·검토 문장·제약을 한국어로 작성한다.
  - 자동 수정: N
  - 검증: 설명성 본문이 한국어이고 영어가 기술 용어·식별자에만 사용되는지 재검토한다.
  - 참조: `docs/CONVENTIONS.md` §언어 규칙

- [ ] GC-004 [`opal/skills/opal-skill-tester/scenarios/_bases/todo-web/docs/PROJECT.md:11`] 문서 본문 설명·표가 영어로 작성됨
  - 카테고리: 문서화
  - 위반 기준: T0 — `docs/CONVENTIONS.md` §언어 규칙 (문서 본문은 한국어, 기술 용어는 영어 병기)
  - 설명: 프로젝트 설명, 섹션 제목, 표 헤더와 Purpose 설명이 영어로 작성되어 있다.
  - 영향: OPAL 프레임워크 문서의 표준 언어와 일관성이 깨진다.
  - 해결 방안: 프로젝트·스택·에이전트 식별자는 유지하고, 서술형 본문·섹션·표 설명을 한국어로 작성한다.
  - 자동 수정: N
  - 검증: 설명성 본문이 한국어이고 영어가 기술 용어·식별자에만 사용되는지 재검토한다.
  - 참조: `docs/CONVENTIONS.md` §언어 규칙

### Info (0건)

없음.

---

## 4. 문서 업데이트 제안

- 빈도 트리거 없음 — 동일 fingerprint가 3개 이상의 파일에서 발견되지 않음.
- 새 카테고리 트리거 없음 — 모든 finding은 `docs/CONVENTIONS.md`의 문서화·언어·`@header` 규칙 범위다.

---

## 5. 문서 작성 유도

- `docs/CONVENTIONS.md` 존재 — 초안 작성 유도 생략.

## 6. 활성·비활성 검사 영역

- 활성: 파일/폴더 네이밍, 들여쓰기·EOF·줄 끝 공백, 파일 구조, 문서화/`@header`, Python import 사용·순서, 문서 언어.
- 비활성: DB query·복잡도·메모리 할당(해당 구현 없음), frontend framework 특화 규칙(기준 없음), 외부 community 참조(사용 안 함).
- 통과 관측: 경로 존재·프로젝트 루트 내부 15/15, `git diff --check`, Python 5개 `ast.parse`, JSON 4개 parse, 비어 있지 않은 파일의 EOF newline.
