---
name: otp-write
description: |
  **범용 문서 작성 오케스트레이터**. 코드 변경 없이 단일 문서를 체계적으로 작성하는 3단계 파이프라인.
  반드시 이 스킬을 사용해야 하는 상황: "otp-write", "otpw", "문서 작성해줘", "보고서 작성", "가이드 만들어줘", "기획서 써줘", "명세서 작성", "설계서 작성", "정책서 작성", "PRD 작성".
  코드 구현이 수반되면 otp-dev/otp-dev-short, 프로젝트 파일럿은 opdp, 와이어프레임은 otp-wf, API 분석은 api-analyzer.
---

# 범용 문서 작성 오케스트레이터

## Harness
모드: 문서 작성 (TASK → PLAN → WRITE)
> 부트스트랩에서 로드되지 않은 경우: `~/.opal/references/opal-harness.md`를 Read한다.

---

## 커버 범위

**가능**: PRD, TRD, IA, ERD, 정책서, API 명세서, 설계서, 보고서, 가이드/매뉴얼, 기획/제안, 내부 커뮤니케이션(회의록, FAQ)
**아닌 것**: 코드 구현(otp-dev), 프로젝트 파일럿(opdp), 와이어프레임(otp-wf), API 분석(api-analyzer)

---

## STEP 1: TASK (직접 수행)

Harness "TASK 공통 프로세스"를 따르되, 추가 확인:
- 작업 유형: "문서 작성"
- 문서 유형, 대상 독자, 범위, 출력 형식(.md/.docx/.pdf)

---

## STEP 2: PLAN (직접 수행)

### 소스 조사 (문서 유형별 분기)

| 문서 유형 | 소스 조사 방식 |
|-----------|-------------|
| 기술 산출물 (설계서, 명세서, ERD 등) | Glob/Grep/Read로 코드베이스 분석 |
| 보고서 | 코드 분석 + WebSearch |
| 가이드/매뉴얼 | 코드 분석 + 기존 문서 참조 |
| 기획/제안 | WebSearch + interview 스킬 |
| 내부 커뮤니케이션 | 기존 문서/데이터 참조 |

### 목차 + 구조 설계

1. `~/.opal/references/opal-doc-standard.md` Read → 문서 표준 적용
2. 필수 섹션 구성 + 섹션별 핵심 개요
3. PLAN.md 작성 (목차 + 개요 + 참조 소스)

QA: 복잡한 문서는 dtp-qa 호출, 단순 문서는 스킵.
사용자에게 목차/구조 제시. **승인 = WRITE 시작 허가**.

---

## STEP 3: WRITE (직접 수행)

1. PLAN.md 목차 따라 섹션별 순차 작성
2. opal-doc-standard 적용
3. 출력 형식: `.md`(기본), `.docx`(`anthropics/docx`), `.pdf`(`anthropics/pdf`)
4. 완성본 제시 → DONE.md 생성

---

## STATE.md 도메인 치환값

Harness STATE.md 템플릿에 적용:
- `{모드}`: 문서 작성
- `{단계 목록}`: TASK / PLAN / WRITE
- `{산출물 목록}`: TASK.md, PLAN.md, {문서명}, DONE.md

---

## 변경이력

| 버전 | 날짜 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-03-29 | 초기 작성 |
| v1.1 | 2026-03-28 | Harness 참조 전환으로 슬림화 |
