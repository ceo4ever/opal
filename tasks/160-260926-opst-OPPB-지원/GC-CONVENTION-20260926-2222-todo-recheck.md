# GC CONVENTION REPORT — 20260926-2222-todo-recheck

## 1. 헤더

- 실행 일시: 시작 2026-09-26 22:22 / 완료 2026-09-26 22:23 / 소요 1분
- 범위: `all` / Task 160 TODO 기존 대상 15개 재검사
- 에이전트: `opal-convention-checker` fallback
- 기준 문서: `docs/CONVENTIONS.md`, `.opal/code-scan.json`
- baseline: `GC-CONVENTION-20260926-2214-todo.md`, `gc-findings-convention-20260926-2214-todo.json`
- APPLY 수행 여부: N (read-only 재검사)
- 검사 실행 상태: `pass` — 기존 대상 15개 모두 검사, missing capability 없음
- 최종 판정: `PASS_WITH_ADVISORIES` — 신규 blocking 0건, 정보성 pre-existing 1건

---

## 2. 요약 지표

| 지표 | 값 |
|------|-----|
| 현재 이슈 수 | 1 |
| 심각도 분포 | Critical 0 / High 0 / Medium 0 / Low 1 / Info 0 |
| 집행 수준 | Blocking 0 / Advisory 0 / Informational 1 |
| 자동 수정 가능 | 0 |
| 수동 조치 필요 | 1 (비차단 기존 이슈) |
| baseline delta | New 0 / Persisting 1 / Resolved 3 / Suppressed 0 |
| `code-scan` 분류 | newly-uncovered 0 / pre-existing 1 |
| 새 blocking finding | 0 |
| 문서 업데이트 제안 수 | 0 |

`code-scan validate --scope framework --changed <15개 대상> --json`은 `ok: true`, exit 0을 반환했다. 지원 확장자 9개 중 8개가 covered(88.9%)이고, 남은 `README.md` 1건은 `pre_existing`으로 분류되어 게이트를 차단하지 않았다. `newly_uncovered`는 0건이다.

### 보완 확인

- baseline GC-002: `_opal/AGENT.md` 인라인 `@header` 누락 → 해소. `code-scan` covered 증가 7→8, newly-uncovered 1→0.
- baseline GC-003: `_opal/AGENT.md` 영어 전용 본문 → 해소. 설명·검토 항목·제약이 한국어로 작성됨.
- baseline GC-004: `docs/PROJECT.md` 영어 본문·표 → 해소. 서술·섹션·표 설명이 한국어로 작성됨.

---

## 3. 수정 대상 (체크리스트)

### Critical (0건)

없음.

### High (0건)

없음.

### Medium (0건)

없음.

### Low (1건)

- [~] GC-001 [`opal/skills/opal-skill-tester/README.md:1`] 인라인 `@header` 누락 — pre-existing, 비차단
  - 카테고리: 문서화
  - 위반 기준: T0 — `.opal/code-scan.json` `headerSource=inline`, `docs/CONVENTIONS.md` §구현 규칙/§@header 구칙
  - 설명: `code-scan validate`가 `uncovered/pre_existing`로 계속 보고했지만, 도구 자체 판정은 `ok: true`, exit 0이다. 이번 TODO 추가에서 새로 생긴 결함이 아니며 재검사 게이트를 차단하지 않는 정보성 finding으로 유지한다.
  - 영향: 전체 code-map coverage가 100%는 아니지만, 신규 coverage 회귀는 없고 결정론 검증은 통과한다.
  - 해결 방안: 별도 기존 부채 정리 범위에서 `code-scan target` 판정에 따라 파일 상단에 현재 사실만 담은 `@header` 블록을 추가한다.
  - 자동 수정: N
  - 검증: `code-scan validate --changed ... --json`에서 해당 `pre_existing` 항목이 사라지는지 확인한다.
  - 참조: `docs/CONVENTIONS.md` §구현 규칙/§@header 구칙

### Info (0건)

없음.

---

## 4. 문서 업데이트 제안

- 빈도 트리거 없음 — 현재 finding이 1개 파일에만 남음.
- 새 카테고리 트리거 없음.

---

## 5. 문서 작성 유도

- `docs/CONVENTIONS.md` 존재 — 초안 작성 유도 생략.

## 6. 활성·비활성 검사 영역

- 활성: 파일/폴더 네이밍, 들여쓰기·EOF·줄 끝 공백, 파일 구조, 문서화/`@header`, Python import 사용·순서, 문서 언어.
- 비활성: DB query·복잡도·메모리 할당(해당 구현 없음), frontend framework 특화 규칙(기준 없음), 외부 community 참조(사용 안 함).
- 통과 관측: 기존 명시 대상 15/15 존재·루트 내부, `git diff --check`, Python 5개 `ast.parse`, JSON 4개 parse, 비어 있지 않은 파일의 EOF newline.
