<!--
  module: report-convention-template
  layer: reference
  domain: opal-pilot-gc
  description: GC 컨벤션 보고서 템플릿 — opal-convention-checker가 생성하는 자기완결 보고서 (체크리스트 내장)
-->

# GC CONVENTION REPORT — {타임스탬프}

<!--
  체크박스 5단계 상태 기호 (APPLY 단계가 기입):
  [ ]  open    — 미처리 (신규)
  [x]  done    — 적용 완료  ← 주석: 적용 시각 YYYY-MM-DD HH:mm + 수정 요약
  [~]  pending — 보류       ← 주석: 보류 사유
  [?]  review  — 확인 필요  ← 주석: 판단 근거 / 해결 방안
  [!]  failed  — 실패       ← 주석: 실패 사유 / 권장 대안
-->

## 1. 헤더

- 실행 일시: 시작 {YYYY-MM-DD HH:mm:ss} / 완료 {YYYY-MM-DD HH:mm:ss} / 소요 {N분 N초}
- 범위: `{staged|all}` / 대상 파일 {N}개
- 에이전트: opal-convention-checker
- 기준 문서: {docs/CONVENTIONS.md 존재 → 해당 문서 | 부재 → 초안 생성 유도}
- APPLY 수행 여부: {Y (--apply 플래그) | N (수동 대기)}

---

## 2. 요약 지표

| 지표 | 값 |
|------|-----|
| 총 이슈 수 | {N} |
| 심각도 분포 | Critical {N} / High {N} / Medium {N} / Low {N} / Info {N} |
| 자동 수정 가능 | {N} |
| 수동 조치 필요 | {N} |
| 파일별 상위 Top 5 | {파일1} ({N건}) / {파일2} ({N건}) / ... |
| 카테고리별 빈도 | {카테고리1} ({N} 파일) / {카테고리2} ({N} 파일) |
| Critical/High 수 | {N} |
| 문서 업데이트 제안 수 | {N} (빈도 {N}건 + 새 카테고리 {N}건) |

---

## 3. 수정 대상 (체크리스트)

<!--
  [MUST] 모든 이슈에 아래 필드를 기입한다. Low/Info 항목도 참조 URL 필드를 생략하지 않는다.
  Low/Info 항목의 참조 URL을 모를 경우: "참조: TBD — {관련 도구/규칙 링크}" 형태로 placeholder 기입.

  형식 (각 이슈 필드):
  - [ ] GC-CNNN [{파일}:{라인}] {이슈 요약}
    - 카테고리: {네이밍 | 들여쓰기 | 파일 구조 | 죽은 코드 | 미사용 import | 문서화 | import 순서 | 코드 품질}
    - 위반 기준: 프로젝트(CONVENTIONS.md §N) | 프레임워크 base-convention-checklist (참조용)
    - 설명: {무엇이 문제인지}
    - 해결 방안: {구체적 수정 안내}
    - 자동 수정: Y | N
    - 참조: {공식 문서/린트 규칙 URL | TBD — {도구} 링크}
-->

### Critical ({N}건)

### High ({N}건)

### Medium ({N}건)

### Low ({N}건)

### Info ({N}건)

---

## 4. 문서 업데이트 제안 (§9·§10, 트리거 발동 시만)

<!--
  트리거 독립 판정:
  - 빈도 트리거:        동일 fingerprint가 N=3 이상 파일에서 발견 (파일 수 기준)
  - 새 카테고리 트리거: 기존 CONVENTIONS.md에 없는 카테고리 등장
  (컨벤션 보고서는 심각도 트리거가 Critical/High 0건인 경우가 대부분이므로 빈도 중심)

  각 트리거는 별개 항목으로 표기한다.
-->

<!-- 빈도 트리거 발동 시 -->
- [ ] GC-DP-C{NNN} [빈도 트리거] 이슈 "{카테고리}" ({N}개 파일) → CONVENTIONS.md §{N} 규칙 추가 제안
  - 근거: 단일 실행 내 {N}개 파일 — 빈도 임계값 N=3 초과
  - 제안 내용: "{규칙 내용}"

<!-- 새 카테고리 트리거 발동 시 -->
- [ ] GC-DP-C{NNN} [새 카테고리 트리거] "{카테고리}" → CONVENTIONS.md §{다음 번호} 신설 제안

---

## 5. 문서 작성 유도 (해당 시)

<!-- docs/CONVENTIONS.md 존재 시: 이 섹션 생략 또는 "존재 — 작성 유도 생략" 표기 -->
<!-- docs/CONVENTIONS.md 부재 시: 아래 안내 표시 -->
- `docs/CONVENTIONS.md` 부재 감지 → 코드베이스 분석 기반 컨벤션 초안 생성 제안
  - 분석 항목: 네이밍 / 들여쓰기 / 파일 구조 / import 순서
  - 생성 방식: `opal-project-init` 스킬 재사용
  - 소유자 승인 후 실행
