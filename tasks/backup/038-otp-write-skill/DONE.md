# DONE: otp-write 범용 문서 작성 오케스트레이터 개발

> 완료일: 2026-03-29

## 변경 요약

### 신규 생성
- **skills/otp-write/SKILL.md** (162줄) — 3단계 오케스트레이터 (TASK → PLAN → WRITE)
- **opal/core/references/opal-doc-standard.md** (115줄) — doc-writer + version-mgr 통합 참조 문서

### 삭제
- skills/doc-writer/ — opal-doc-standard로 통합
- skills/version-mgr/ — opal-doc-standard로 통합

### 참조 대체 (14개 파일)
- opal-skill-creator, opal-agent-creator: 의존 테이블 + 본문
- dtp-test-scenario, dtp-analysis, wireframe-builder: 버전 관리 참조
- tech-context-guide.md: 범용 스킬 나열
- execute-plan-guide.md x2: 스킬 카탈로그
- otp-dev-short, otp-dev, dev-task-pilot: description
- dtp-action-plan-agent: 스킬 매칭 테이블
- CLAUDE.md: 소스 구조 + 의존 관계
- skills.md, skill-guide.md: 레지스트리

## 검증

- [x] otp-write 162줄 (200줄 이내)
- [x] opal-doc-standard 115줄 (120줄 이내)
- [x] version-mgr 잔존 참조 0건 (태스크/README/메모리 제외)
- [x] doc-writer 잔존 참조 0건 (태스크/README/메모리 제외)
- [x] skills.md에 otp-write 등록, doc-writer/version-mgr 삭제
- [x] skill-guide.md에 otp-write 추가
