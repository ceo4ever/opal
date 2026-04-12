# DONE: post-commit 문서 동기화 — A안 설계 검토

> 완료일: 2026-04-06 | 태스크: 091-opp-post-commit-sync | 스킬: opp

## 완료 요약

A안(경량 agentic 스킬 + PostToolUse 훅) 설계 검토 완료.
opi 확장보다 신규 스킬(`opal-post-commit-sync`) 생성이 적합하다는 결론 도출.

## 핵심 결론

- **방향**: 신규 스킬 `opal-post-commit-sync` 생성
- **이유**: opi는 Phase 2.5/3에서 사용자 인터뷰/승인 필수 → 자동화 불가. 단일책임 위반
- **훅 연결**: `PostToolUse(Bash)` → `post-commit-check.sh`(stdin JSON 파싱) → Claude에게 스킬 실행 지시
- **구현 범위**: 생성 2개(SKILL.md, post-commit-check.sh) + 수정 3개(claude-hooks.json, install-mac.sh, skills.md)

## 캡틴 확인 필요 사항 (다음 구현 태스크 전)

1. **훅 type 선택**: `command` stdout 방식 vs `prompt` 주입 방식 — 실전 테스트 먼저 할지 여부
2. **자동화 범위**: 분석+제안만 자동 vs Write까지 자동
3. **워커 세션 처리**: 워커가 커밋 시 훅 스킵 여부

## 산출물

- `tasks/091-opp-post-commit-sync/PLAN.md` — 설계 분석 + 구현 범위 정의
