# TEST-SCENARIO: CLOSE 단계 관련 문서 업데이트 스텝 추가

> 작성일: 2026-06-24 | 입력: PLAN.md | 검증 모드: M1 (grep/static)

## 검증 범위

8개 pilot SKILL.md CLOSE 섹션에 "관련 문서 업데이트" 스텝이 올바르게 삽입되었는지 grep 기반으로 검증한다.

## RED-first 판단

문서 수정 트랙 — 동작 구현 없음. RED-first 비해당 (스킵).

---

## 시나리오 목록

### TS-001: 신규 스텝 존재 (8파일)

| 항목 | 값 |
|------|------|
| **검증 대상** | 8개 SKILL.md CLOSE 내 "관련 문서 업데이트" 텍스트 |
| **유형** | M1 (grep) |
| **명령** | `grep -rn "관련 문서 업데이트" opal/skills/opal-pilot-*/SKILL.md` |
| **기대 결과** | 8개 파일 각 1줄 이상 매칭 (총 ≥ 8 결과) |
| **PASS 조건** | 매칭 수 == 8 |

### TS-002: 신규 스텝이 brain ingest 직전 위치 (8파일)

| 항목 | 값 |
|------|------|
| **검증 대상** | "관련 문서 업데이트" 줄번호 < "op-brain-ingest 디스패치" 줄번호 |
| **유형** | M1 (grep 줄번호 비교) |
| **명령** | 각 파일에서 `grep -n "관련 문서 업데이트\|op-brain-ingest 디스패치"` 실행 후 첫 줄번호 비교 |
| **기대 결과** | 8개 파일 모두: "관련 문서 업데이트" 줄번호 < "op-brain-ingest 디스패치" 줄번호 |
| **PASS 조건** | 8파일 전부 순서 만족 |

### TS-003: PROJECT.md + changed_files 키워드 포함 (8파일)

| 항목 | 값 |
|------|------|
| **검증 대상** | 신규 스텝 블록에 "PROJECT.md" 및 "changed_files" 키워드 존재 |
| **유형** | M1 (grep) |
| **명령** | `grep -rn "PROJECT.md" opal/skills/opal-pilot-*/SKILL.md` (8 매칭) + `grep -rn "changed_files" opal/skills/opal-pilot-*/SKILL.md` (8 매칭) |
| **기대 결과** | 두 키워드 모두 8파일 각 1회 이상 존재 |
| **PASS 조건** | 각 키워드 매칭 수 ≥ 8 |

### TS-004: CLOSE 번호 연속성 (패턴 A·B 7파일)

| 항목 | 값 |
|------|------|
| **검증 대상** | opd/opp/opdd/opds/opdw/opsdd/opwt CLOSE 내 번호 항목이 1부터 연속 (1→2→3→4) |
| **유형** | M1 (grep) |
| **명령** | 각 파일 CLOSE 섹션에서 `grep -n "^[0-9]\+\." SKILL.md` 패턴으로 번호 항목 추출 후 연속성 확인 |
| **기대 결과** | 삽입 후 항목 번호: 패턴 A = 1,2,3,4 연속 / 패턴 B(opsdd) = 1,2,3,4,5,6 연속 |
| **PASS 조건** | 7파일 모두 연속 (opgc는 번호 없음 — 비해당) |

### TS-005: 변경이력 행 추가 (8파일)

| 항목 | 값 |
|------|------|
| **검증 대상** | 8개 파일 변경이력에 태스크 042 + 날짜 포함 행 존재 |
| **유형** | M1 (grep) |
| **명령** | `grep -rn "042" opal/skills/opal-pilot-*/SKILL.md \| grep "2026-06-24"` |
| **기대 결과** | 8줄 매칭 |
| **PASS 조건** | 매칭 수 == 8 |

### TS-006: 회귀 — CLOSE+변경이력 외 무변경

| 항목 | 값 |
|------|------|
| **검증 대상** | git diff 범위가 CLOSE 섹션 + 변경이력 표에 국한 |
| **유형** | M1 (git diff) |
| **명령** | `git diff --stat opal/skills/opal-pilot-*/SKILL.md` + 각 파일 diff 내용에 CLOSE 섹션 외 변경 없음 확인 |
| **기대 결과** | 변경 행: CLOSE 내 신규 스텝 블록 + 후속 번호 변경 + 변경이력 행 추가만 존재 |
| **PASS 조건** | CLOSE 진입 게이트 인용블록(`> **CLOSE 진입 게이트 자동 검증**`) 불변 / STATE 행 구조 불변 / brain ingest 탐색 경로 텍스트 불변 |

---

## 코드 품질

- [ ] lint/format: Markdown — 해당 없음 (linter 없음)
- [ ] typecheck: 해당 없음
- [ ] build: 해당 없음

## 보안 항목

- [ ] 시크릿 스캔: 문서 수정 태스크 — 추가된 내용에 시크릿/토큰 없음 (해당 없음)
- [ ] .gitignore: 신규 파일 없음 (해당 없음)

## 설계 피드백

| 항목 | 상태 |
|------|------|
| 미해결 빈틈 | 없음 |
