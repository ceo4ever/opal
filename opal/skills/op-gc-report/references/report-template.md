<!--
  module: report-template
  layer: reference
  domain: op-gc-report
  description: GC 통합 보고서 템플릿 — op-gc-report가 생성하는 GC-REPORT-{ts}.md 골격
-->

# GC REPORT — {타임스탬프}

## 1. 판정

| 항목 | 값 |
|---|---|
| 판정 | {PASS \| PASS_WITH_ADVISORIES \| FAIL \| INCOMPLETE} |
| 판정 근거 | {판정을 결정한 조건 1줄 — 차단 항목 / 결측 / advisory 전건 등} |
| 대상 파일 수 | {N} |
| 총 finding | {N} (blocking {N} / advisory {N} / informational {N}) |
| baseline | {경로 \| none} |

| check | status | checked_files | finding | 보고서 |
|---|---|---|---|---|
| security | {pass\|partial\|error} | {N} | {N} | [→](./GC-SECURITY-{ts}.md) |
| convention | {pass\|partial\|error} | {N} | {N} | [→](./GC-CONVENTION-{ts}.md) |

---

## 2. baseline delta

| 분류 | 건수 | 비고 |
|---|---|---|
| 신규(new) | {N} | baseline이 `none`이면 전건 신규 |
| 잔존(persisting) | {N} | 미검사 파일의 baseline finding 포함 |
| 해결(resolved) | {N} | 이번 `checked_files`에 포함된 파일만 유효 |
| 억제(suppressed) | {N} | 차단 계산에서 제외 |

### 신규 항목

{fingerprint · rule_id · location · severity · disposition 목록 — 없으면 "없음"}

### 해결 항목

{fingerprint · rule_id · location 목록 — 없으면 "없음"}

---

## 3. 검사 결측

| check | 결측 내용 | 영향 |
|---|---|---|
| {security\|convention} | {기준 문서 결측 / 도구 부재 / 접근 실패 / 미실행} | {판정에 미친 영향} |

`checked_files` ≠ 입력 `target_files`인 check와 그 사유를 여기에 남긴다. 결측이 없으면 "없음".

---

## 4. 차단 항목

`disposition: blocking` finding만 싣는다. 판정이 `INCOMPLETE`여도 차단 항목은 그대로 표기한다.

```
- {fingerprint} [{file}:{line}] {요약}
  - rule_id / source_tier: {rule_id} / {T0~T3}
  - severity / confidence: {값} / {값}
  - 영향: {impact}
  - 조치: {remediation.guidance}
  - 확인 방법: {verification}
  - delta: {new | persisting}
```

차단 항목이 없으면 "없음".

---

## 5. 문서 업데이트 제안

세 트리거를 각각 독립 항목으로 분리해 표기한다. 한 finding이 여러 트리거에 해당하면 중복 표기한다.

### [빈도 트리거] ({N}건)

{동일 fingerprint가 3개 이상 파일에서 관측된 항목 — 대상 문서와 제안 문안}

### [심각도 트리거] ({N}건)

{critical·high finding 기반 제안 — 대상 문서와 제안 문안}

### [새 카테고리 트리거] ({N}건)

{기준 문서에 없는 category 기반 제안 — 대상 문서와 제안 문안}

제안은 제안일 뿐이며 이 보고서 생성 과정에서 기준 문서를 수정하지 않는다.
