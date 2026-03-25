---
name: otp-doc 스킬 계획
description: otp-doc 문서 작업 전용 스킬 — TASK(검토/방향수립/RESEARCH/PLAN) + 사용자 검토 + EXECUTE + QA 파이프라인. 별도 에이전트 검토 가능. 기존 스킬 개선 후 상세 논의 예정.
type: project
---

## otp-doc 스킬 (예정)

캡틴이 요청한 문서 작업 전용 스킬. otp-dev/short/wf 개선 완료 후 상세 설계 예정.

**파이프라인**: TASK(검토/방향수립) → RESEARCH(조사) → PLAN(문서 설계) → [사용자 검토/승인] → EXECUTE(문서 작성) → QA(품질 검증)

**미결 사항** (다음 논의 시 확인):
- 대상 문서 유형 및 기존 doc-writer와의 관계
- RESEARCH 단계 범위 (웹/코드베이스/둘 다)
- QA 에이전트: otp-qa-dev-agent 재활용 vs otp-qa-doc-agent 신규
- 별도 에이전트 구성 상세

**Why:** 캡틴이 코드 작업(otp-dev 계열)과 문서 작업을 명시적으로 분리하길 원함
**How to apply:** otp-dev/short/wf 리팩토링 완료 후 이 스킬 설계 착수
