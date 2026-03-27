# TASK: OPAL 프레임워크 문서 구조 + PM 역할 재설계

> 작성일: 2026-03-27 | 작업 유형: 개선
> 입력: 사용자 요청 + 분석 논의
> 출력: TASK.md

## 작업 목표

OPAL 프레임워크의 프로젝트 문서 구조를 재설계하고, 프로젝트 PM(AGENT.md) 역할을 실질적으로 작동하게 개선한다.

## 배경

현재 OPAL 프레임워크의 문제:

1. **LLM 플랫폼 문서가 무겁다** — CLAUDE.md/GEMINI.md에 프로젝트 정보(기술 스택, 환경 등)가 직접 포함되어 중복 발생
2. **프로젝트 AGENT.md가 작동하지 않는다** — 부트스트랩에서 존재 여부만 체크하고 내용을 활용하지 않음. 페르소나/의사결정 원칙이 otp 파이프라인 워커에게 전달되지 않음
3. **프로젝트 정의 문서가 없다** — docs/에 서버/클라이언트 가이드는 있지만, 프로젝트 자체를 정의하는 SSOT(Single Source of Truth) 문서가 없음
4. **일반 프로젝트는 docs/ 미생성** — scope=opal-only 모드에서 .opal/ 만 생성하고 docs/를 만들지 않음
5. **기존 문서 업데이트 불가** — existing 모드에서 파일이 있으면 건너뛰기만 함

## 요구사항

### R1. LLM 플랫폼 문서 경량화
- [ ] CLAUDE.md → OPAL 부트스트래퍼만 유지 (~7줄)
- [ ] GEMINI.md → OPAL 부트스트래퍼만 유지 (~7줄)
- [ ] .cursorrules → OPAL 부트스트래퍼만 유지 (~7줄)
- [ ] 프로젝트 정보, 기술 스택, 코드 컨벤션 등은 docs/ 문서로 이관

### R2. docs/PROJECT.md 신설 (프로젝트 정의 SSOT)
- [ ] 모든 프로젝트(일반/개발) 공통 필수 산출물
- [ ] 내용: 프로젝트명, 목적, 도메인, 기술 스택, 아키텍처 개요, 개발 환경, 현재 Phase
- [ ] CLAUDE.md, AGENT.md 등이 이 문서를 참조 (정보 중복 제거)

### R3. docs/CONVENTIONS.md 신설 (코드 컨벤션 SSOT)
- [ ] 개발 프로젝트 전용
- [ ] 내용: 네이밍, 파일 구조, 브랜치 전략, 커밋 규칙
- [ ] 기존 CLAUDE.md의 코드 컨벤션 섹션 이관

### R4. .opal/AGENT.md 재설계
- [ ] 페르소나(PERSONA), 의사결정 원칙(DECISION_PRINCIPLES) 제거
- [ ] "PM 검토 기준" 섹션 신설 — 알투가 워커 결과를 검토할 구체적 체크포인트
- [ ] 프로젝트 정보는 docs/PROJECT.md 참조 (중복 보유 안 함)
- [ ] 도메인 지식, 프로젝트 규칙 유지

### R5. 부트스트랩 절차 변경
- [ ] `~/.opal/AGENT.md` (글로벌): .opal/AGENT.md 내용을 Read하여 PM 컨텍스트 로드하는 절차 추가
- [ ] PM 역할 로드 시 docs/PROJECT.md, docs/CONVENTIONS.md도 Read

### R6. otp 파이프라인에 PM 검토 게이트 추가
- [ ] otp-dev, otp-dev-short: 각 단계 워커 완료 후 알투가 PM 관점으로 검토
- [ ] 검토 기준: .opal/AGENT.md의 "PM 검토 기준" + TASK.md 요구사항 + QA 결과
- [ ] Fail 시 워커에게 재지시 (최대 1회), Pass 시 사용자에게 보고

### R7. opi 스킬 개선
- [ ] PM 인터뷰 축소 (5개 → 3개: 프로젝트명, 도메인, 현재 Phase) + 검토 기준 수집
- [ ] 일반 프로젝트도 docs/PROJECT.md 생성
- [ ] 기존 문서 업데이트 모드(update) 추가 검토
- [ ] 플랫폼 템플릿 경량화 (부트스트래퍼만)

### R8. PM 학습 루프
- [ ] 글로벌 AGENT.md에 "PM 학습 루프" 행동 규칙 추가
- [ ] .opal/AGENT.md에 "확정 기준" 섹션 — 캡틴 승인 원칙이 누적되는 공간
- [ ] 판단 불확실 시 캡틴에게 질문하는 프로토콜 정의
- [ ] 캡틴 답변 분류: 반복 원칙 → 확정 기준에 추가, 일회성 → memory/에 기록
- [ ] 다음 세션에서 확정 기준 자동 적용 (재질문 안 함)

## 제약 조건

- OPAL 부트스트래퍼 포맷(`# === OPAL START ===` ~ `# === OPAL END ===`)은 변경하지 않는다
- 기존 프로젝트의 .opal/MEMORY.md 구조는 유지한다
- otp 파이프라인의 기본 흐름(TASK→PLAN→TEST-SCENARIO→EXECUTE)은 변경하지 않는다
- 스킬 자체 페르소나(dtp-*/personas/)는 이번 태스크에서 변경하지 않는다

## 기술 스택

- Markdown (스킬/에이전트 정의)
- JavaScript (apply.js — opi 템플릿 적용 스크립트)
- Shell (install-mac.sh — 배포 스크립트)

## 관련 문서

- `skills/opal-project-init/SKILL.md` — 현재 opi 스킬
- `skills/opal-project-init/templates/` — 현재 템플릿 구조
- `opal/core/AGENT.md` → 배포 시 `~/.opal/AGENT.md` — 글로벌 부트스트랩
- `skills/otp-dev-short/SKILL.md` — Short Task 오케스트레이터
- `skills/otp-dev/SKILL.md` — Full Task 오케스트레이터
- `opal/skills/opal-orchestrator/SKILL.md` — 오케스트레이션 스킬
- `tasks/029-opal-project-init-general-mode/` — 이전 opi 개선 태스크
