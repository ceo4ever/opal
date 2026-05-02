<!--
  module: done-template
  layer: reference
  domain: opal-pilot-gc
  description: opal-pilot-gc CLOSE 단계 DONE.md 템플릿
-->

# DONE: opal-pilot-gc 실행 — {타임스탬프}

## 실행 범위

- scope: {staged|all}
- 대상 파일 수: {N}개
- 실행 시간: {HH:mm:ss}
- APPLY 모드: {기본 (사용자 승인) | --apply (자동)}
- 체커 범위: {both | --only security | --only convention}

---

## 처리 요약

| 에이전트 | 총 | [x] done | [!] failed | [?] review | [~] pending | [ ] open | 문서 제안 |
|----------|----|----------|------------|------------|-------------|----------|----------|
| security | {N} | {N} | {N} | {N} | {N} | {N} | {N}건 |
| convention | {N} | {N} | {N} | {N} | {N} | {N} | {N}건 |
| **합계** | {N} | {N} | {N} | {N} | {N} | {N} | {N}건 |

---

## 산출물

- [GC-SECURITY-{ts}.md](./GC-SECURITY-{ts}.md)
- [GC-CONVENTION-{ts}.md](./GC-CONVENTION-{ts}.md)

---

## 후속 권장

### 수동 조치 필요

{[?] review 및 [!] failed 항목 목록 — 없으면 "없음"}

### 문서 업데이트 미처리

{승인되지 않은 문서 업데이트 제안 건수} (다음 실행 시 재검토)

### 보류 항목

{[~] pending 항목 목록 — 없으면 "없음"}

---

## CLOSE 게이트 확인

- [x] APPLY 단계 사용자 확인 완료 (CLOSE 진입 게이트 통과)
- [x] 보고서 생성 완료 (GC-SECURITY + GC-CONVENTION)
- [x] `state-tool` 호출로 실행 요약 테이블 갱신 완료
