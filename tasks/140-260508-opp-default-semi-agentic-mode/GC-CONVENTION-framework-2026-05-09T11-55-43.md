# GC CONVENTION REPORT — 2026-05-09T11-55-43

<!--
  체크박스 5단계 상태 기호 (APPLY 단계가 기입):
  [ ]  open    — 미처리 (신규)
  [x]  done    — 적용 완료  ← 주석: 적용 시각 YYYY-MM-DD HH:mm + 수정 요약
  [~]  pending — 보류       ← 주석: 보류 사유
  [?]  review  — 확인 필요  ← 주석: 판단 근거 / 해결 방안
  [!]  failed  — 실패       ← 주석: 실패 사유 / 권장 대안
-->

## 1. 헤더

- 실행 일시: 시작 2026-05-09 11:55:43 / 완료 2026-05-09 11:58:00 / 소요 약 2분
- 범위: `framework` (scope=all 폴백 — OPAL 단일 문서 모델) / 대상 파일 21개
- 에이전트: opal-convention-checker
- 기준 문서: `docs/CONVENTIONS.md` (존재 — 단일 진입점 모델, 허브+링크 미적용)
- APPLY 수행 여부: N (수동 대기)

---

## 2. 요약 지표

| 지표 | 값 |
|------|-----|
| 총 이슈 수 | 4 |
| 심각도 분포 | Critical 0 / High 0 / Medium 2 / Low 2 / Info 0 |
| 자동 수정 가능 | 2 |
| 수동 조치 필요 | 2 |
| 파일별 상위 Top 5 | opal/core/AGENT.md (2건) / harness/state-template.md (1건) / opal/core/references/harness/task-process.md (1건) |
| 카테고리별 빈도 | 문서화(변경이력 형식) (2 파일) / 파일 구조(frontmatter/변경이력 헤더 형식) (2 파일) |
| Critical/High 수 | 0 → **PM Gate PASS** |
| 문서 업데이트 제안 수 | 0 (빈도 트리거 미발동 / 새 카테고리 트리거 미발동) |

---

## 3. 수정 대상 (체크리스트)

<!--
  [MUST] 모든 이슈에 아래 필드를 기입한다. Low/Info 항목도 참조 URL 필드를 포함한다.
-->

### Critical (0건)

### High (0건)

### Medium (2건)

- [ ] GC-C001 [`opal/core/AGENT.md`:309] 변경이력 표 헤더 필드명 불일치
  - 카테고리: 파일 구조
  - 위반 기준: 프로젝트(CONVENTIONS.md §파일 구조 §변경이력) — `| 버전 | 일시 | 변경내용 |` 표준 헤더 형식
  - 설명: 변경이력 표 헤더가 `| 버전 | 날짜 | 내용 |`로 작성되어 있음. 규칙 기준 필드명은 `일시`(YYYY-MM-DD HH:mm KST 형식 포함), `변경내용`이어야 함. 내용 필드가 `내용`으로 단축되어 있으며 `날짜`는 시:분 시각을 포함하지 않아 형식 불일치 가능성 있음.
  - 해결 방안: 헤더를 `| 버전 | 일시 | 변경내용 |`로 교체. 기존 날짜 값(`2026-04-01` 형식)에 시:분이 없는 레거시 행은 그대로 유지하되 신규 행부터 `YYYY-MM-DD HH:mm` 형식 준수.
  - 자동 수정: Y (헤더 셀 단순 치환)
  - 참조: `docs/CONVENTIONS.md §파일 구조 §변경이력` L93-103

- [ ] GC-C002 [`opal/core/references/harness/state-template.md`:L(말미)] 변경이력 표 헤더 필드명 불일치
  - 카테고리: 파일 구조
  - 위반 기준: 프로젝트(CONVENTIONS.md §파일 구조 §변경이력) — `| 버전 | 일시 | 변경내용 |` 표준 헤더 형식
  - 설명: `harness/state-template.md` 변경이력 표 헤더가 `| 버전 | 날짜 | 내용 |`로 작성되어 있음 (`harness/task-process.md`도 동일). 날짜 필드명이 `일시`가 아닌 `날짜`, 변경내용 필드가 `내용`으로 축약됨.
  - 해결 방안: 헤더를 `| 버전 | 일시 | 변경내용 |`로 교체.
  - 자동 수정: Y (헤더 셀 단순 치환)
  - 참조: `docs/CONVENTIONS.md §파일 구조 §변경이력` L93-103

### Low (2건)

- [ ] GC-C003 [`.opal/memory/preferences_default_semi_agentic.md`:전체] 메모리 파일이 changed_files에 포함 — 배포 경계 점검
  - 카테고리: 파일 구조
  - 위반 기준: 프로젝트(CONVENTIONS.md §구현 규칙 §배포 경계) — `~/.opal/` 배포 파일을 직접 편집하지 않는다. 변경은 항상 프로젝트 소스에서 수행한다.
  - 설명: `.opal/memory/preferences_default_semi_agentic.md`는 `~/.opal/memory/`에 배포되는 경로임. 이 파일이 프로젝트 소스(`.opal/memory/` — 프로젝트 루트의 `.opal/`)에 존재하고 install 후 `~/.opal/`로 배포되는 구조라면 컨벤션 준수임. 단, 이 경로가 직접 배포 대상 파일을 의미한다면 배포 경계 위반 가능성 있음. 태스크 context상 install 스크립트를 통한 정상 배포 흐름으로 보이나 확인 필요.
  - 해결 방안: `install-mac.sh`에서 `.opal/memory/` → `~/.opal/memory/` 복사가 포함되어 있는지 확인. 포함되어 있으면 컨벤션 준수(Low 해소). 미포함 시 소스 경로 재검토.
  - 자동 수정: N (외부 스크립트 확인 필요)
  - 참조: `docs/CONVENTIONS.md §구현 규칙 §배포 경계` L200-203 / 참조: TBD — `scripts/install-mac.sh` 배포 경로 확인

- [ ] GC-C004 [`opal/tools/state-tool/state_tool.py`:전체] 변경이력 섹션 파일 내 미존재
  - 카테고리: 문서화
  - 위반 기준: 프로젝트(CONVENTIONS.md §구현 규칙 §@header 규칙) — 코드 파일은 파일 상단 @header 블록을 작성한다. 변경이력은 별도 표(스킬·에이전트·참조 문서) 또는 헤더 내 변경이력 라인으로 갱신한다.
  - 설명: `state_tool.py`는 @header 블록은 존재하나, @header 내에 변경이력 라인이 포함되지 않음. Python 코드 파일의 변경이력 추적이 README.md에만 있음. header-rules.md 기준상 `.py` 파일의 변경이력을 @header 내에 추가해야 하는지 또는 README 방식도 허용하는지 확인 필요.
  - 해결 방안: `opal/core/references/harness/header-rules.md`를 확인하여 Python 파일 변경이력 위치 기준 확인. README.md 방식이 허용되면 이슈 해소(Low 해소). 미허용 시 @header에 `"changelog"` 필드 추가.
  - 자동 수정: N (header-rules.md 확인 후 판단)
  - 참조: `docs/CONVENTIONS.md §구현 규칙 §@header 규칙` L172-174 / 참조: TBD — `opal/core/references/harness/header-rules.md` Python 파일 변경이력 규칙

### Info (0건)

---

## 4. 문서 업데이트 제안 (트리거 발동 시만)

<!-- 빈도 트리거: 동일 fingerprint 이슈가 3개 파일 이상 — 분석 결과 미발동 -->
<!-- 새 카테고리 트리거: 기존 CONVENTIONS.md에 없는 신규 카테고리 — 미발동 -->

해당 없음 — 빈도 트리거(N=3 미만) 및 새 카테고리 트리거 모두 미발동.

---

## 5. 문서 작성 유도

존재 — 작성 유도 생략 (`docs/CONVENTIONS.md` 확인됨).

---

## 핵심 점검 사항별 결과

| 점검 항목 | 결과 | 비고 |
|----------|------|------|
| 네이밍 — kebab-case 파일/폴더 | PASS | 모든 신규 파일(`opal-harness-semi-agentic.md`, `preferences_default_semi_agentic.md`) 규칙 준수 (md는 kebab-case, 메모리 파일은 snake_case 허용 범위) |
| 네이밍 — snake_case 메모리 | PASS | `preferences_default_semi_agentic.md` — 메모리 파일 snake_case 준수 |
| 네이밍 — 약어 alias 충돌 | PASS | 신규 alias 없음 (semi-agentic은 플래그이지 alias가 아님) |
| 파일 구조 — 스킬 frontmatter | PASS (Info) | 7개 pilot SKILL.md 모두 frontmatter 보유. triggers/version은 CONVENTIONS.md에서 "스킬만" 선택 필드이므로 미포함 스킬도 허용 범위 |
| 파일 구조 — 에이전트 frontmatter | PASS | `opal/core/AGENT.md`는 에이전트 파일이 아닌 OPAL 공통 에이전트 정의 파일 — frontmatter 미요구 |
| 변경이력 작성 의무 — 21개 파일 | PASS (2 Medium) | 모든 스킬·에이전트·참조 문서에 (140) 포함 변경이력 행 추가 확인. 일부 파일 헤더 필드명 불일치(GC-C001, GC-C002) |
| 변경이력 일시 형식 (KST HH:mm 포함) | PASS | 모든 신규 변경이력 행이 `2026-05-09 11:22` 형식 준수 |
| 구현 규칙 — Guards | PASS | 관련 파일 모두 명시 |
| 구현 규칙 — 디스패치 의무 | PASS | 7개 pilot SKILL.md 모두 [MUST] 마커 + 워커 디스패치 의무 포함 |
| 구현 규칙 — @header (.py) | PASS (Low) | `state_tool.py` @header 블록 존재. 변경이력 위치 기준 확인 필요(GC-C004) |
| 구현 규칙 — Citation Rules | PASS | 모든 pilot SKILL.md에 citation-rules 트리거 1줄 주입 확인 |
| 구현 규칙 — State 관리 (state-tool) | PASS | state-tool 3-way 모드 지원 추가(v1.1), README 변경이력 준수 |
| 구현 규칙 — 도구 우선 | PASS | 해당 파일 내 언급 충족 |
| 구현 규칙 — 배포 경계 | Low (GC-C003) | `.opal/memory/` 파일 changed_files 포함 — install 흐름 확인 필요 |
| 구현 규칙 — 플랫폼 분기 격리 | PASS | 신규 파일에 플랫폼 조건문 미포함 확인 |
| 커밋 규칙 | 해당 없음 | 커밋 메시지 미제공 |
