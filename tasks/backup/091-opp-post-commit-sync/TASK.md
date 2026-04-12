# TASK: post-commit 문서 동기화 — A안 설계 검토

> 작성일: 2026-04-06 | 작업 유형: 분석 | 적용 스킬: opp | 모드: interactive
> 입력: 사용자 요청
> 출력: PLAN.md (A안 설계 분석 + 구현 방향 정의)

## 작업 목표

커밋 후 docs/ 문서를 자동으로 업데이트하는 A안(새 경량 agentic 스킬)의 구체적 설계를 검토한다.
opi 확장 vs 신규 스킬 중 최적 방향을 결정하고, 구현 범위와 아키텍처를 정의한다.

## 배경

현재 커밋 후 docs/ 업데이트는 수동이다. 캡틴이 `//opi`를 직접 호출해야 한다.
A안: Claude Code `PostToolUse(Bash(git commit*))` 훅 → 경량 agentic 스킬 자동 호출.
opi는 interactive 5-Phase 구조라 훅 자동화에 부적합. 새 스킬 또는 opi 확장이 필요하다.

## 확정된 설계 방향 (대화에서 합의)

- 방향: A안 — 경량 agentic 스킬 + PostToolUse 훅 연결
- 구현 선택지:
  1. opi에 `--agentic` + `--post-commit` 플래그 추가 (확장)
  2. 신규 경량 스킬 `opal-post-commit` 별도 작성
- 최종 선택은 이번 검토(PLAN)에서 결정

## 요구사항

- [ ] **opi 현재 구조 분석** — 최신화 모드와 post-commit 스코프 비교
  - 무엇을: opi 최신화 모드 Phase별 분석, 훅 자동화에 적합한지 판단
  - 어디에: PLAN.md "현황 조사" 섹션
  - AC: opi 확장 가능 여부와 그 근거가 명시되어 있다

- [ ] **Claude Code 훅 연결 방식 분석** — PostToolUse + claude CLI 호출 가능성
  - 무엇을: `PostToolUse(Bash(git commit*))` 훅에서 claude CLI로 스킬 호출하는 방법 조사
  - 어디에: PLAN.md "현황 조사" 섹션
  - AC: 훅 → 스킬 호출 연결 방식이 구체적으로 명시되어 있다

- [ ] **설계 방향 결정** — opi 확장 vs 신규 스킬
  - 무엇을: 두 선택지의 장단점 비교 후 권장 방향 결정
  - 어디에: PLAN.md "핵심 설계" 섹션
  - AC: 권장 방향과 근거가 명확히 제시되어 있다

- [ ] **구현 범위 정의** — 스킬 구조 + 훅 설정 + 배포 경로
  - 무엇을: 스킬 파일 구조, 훅 설정 위치(claude-hooks.json), install-mac.sh 배포 경로 정의
  - 어디에: PLAN.md "구현 계획" 섹션
  - AC: 구현 시 생성/수정할 파일 목록과 각 역할이 명시되어 있다

## 제약 조건

- 이번 태스크는 검토/분석 단계. 실제 파일 생성/수정은 하지 않는다
- ~/.opal/ 경로 직접 수정 금지

## 기술 스택

- Markdown, Bash (훅 셸 스크립트), Claude Code hooks API

## 관련 문서

- `~/.opal/skills/opal-project-init/SKILL.md` — opi 현재 구조
- `opal/core/hooks/claude-hooks.json` — 현재 훅 설정
- `scripts/install-mac.sh` — 배포 스크립트
