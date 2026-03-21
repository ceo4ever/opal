---
date: 2026-03-21
task: opal-project-init 일반 프로젝트(scope=opal-only) 모드 추가
result: 완료
commit: dfb2a18
---

# opal-project-init 일반 프로젝트 모드 추가

## 작업 내용

- SKILL.md: 일반/개발 프로젝트 카테고리 선택 + PM 공통 인터뷰(Q1~Q5) 프로세스 추가
- apply.js: scope=opal-only 지원 (.opal/AGENT.md + MEMORY.md만 생성)
- AGENT.md 템플릿: PM 프로필 구조 개선
- install-mac.sh: python3 → /usr/bin/python3 절대 경로 통일

## opal 프로젝트 자체에도 적용

- .opal/AGENT.md (PM 프로필) + .opal/MEMORY.md (메모리 인덱스) 생성 완료
- .opal/ 디렉토리는 git 커밋에서 제외 (로컬 전용)
