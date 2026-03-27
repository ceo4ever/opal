# TASK: opal-dev-builder 스킬 개발

> 작성일: 2026-03-27 | 작업 유형: 신규
> 입력: 033 태스크 논의 내용
> 출력: TASK.md

## 작업 목표

개발 프로젝트의 전체 라이프사이클을 관리하는 `opal-dev-builder` 스킬을 만든다. opi가 프로젝트를 셋업한 후, 캡틴이 "만들어줘"라고 요청했을 때 PRD/TRD 작성 → 로드맵 수립 → 태스크 순차 실행까지 이어지는 흐름을 구현한다.

## 배경

### 현재 문제

캡틴이 `//opi 번역 웹앱 만들어줘`라고 하면:
1. opi가 프로젝트 셋업을 한다 (docs/, .opal/)
2. 셋업이 끝나면 **멈춘다**
3. 캡틴이 직접 `//otpd` 또는 `//otpds`로 개별 태스크를 지시해야 한다

일반 LLM은 "만들어줘"라고 하면 바로 설계하고 개발을 시작한다. OPAL이 프로젝트 셋업만 하고 멈추는 것은 부자연스럽다.

### 빠져있는 것

```
opi         = 프로젝트 WHAT/WHY 정의 + 셋업
???         = PRD/TRD 작성 + 로드맵 + 태스크 관리    ← 이것
otp-dev     = 개별 태스크 실행
```

### PRD/TRD와 현재 프로젝트 문서의 관계

opi가 만드는 문서(PROJECT.md, ARCHITECTURE.md 등)는 **프로젝트 환경 정의**이다. "뭘 만들지"(PRD)와 "어떻게 만들지"(TRD)는 성격이 달라 별도 문서가 필요하다.

| 문서 | 성격 | 내용 |
|------|------|------|
| docs/PROJECT.md | 프로젝트 환경 | 개요, 원칙, 기준 |
| docs/ARCHITECTURE.md | 프로젝트 환경 | 기술 스택, 시스템 구성 |
| docs/PRD.md | 제품 설계 | 사용자, 기능 요구사항, 화면 흐름, 우선순위 |
| docs/TRD.md | 기술 설계 | API 설계, 데이터 모델, 성능/보안 요구사항 |

## 요구사항

### R1. 스킬 정의
- [ ] `skills/opal-dev-builder/SKILL.md` 작성
- [ ] 약식 명령어: `//odb` (opal-dev-builder)
- [ ] skills.md, skill-guide.md 레지스트리 등록

### R2. PRD 작성 (Phase 1)
- [ ] 캡틴과 대화 + 프로젝트 분석으로 PRD 초안 작성
- [ ] 내용: 사용자 정의(페르소나), 기능 요구사항(유저 스토리), 화면 흐름, 우선순위
- [ ] 캡틴 검토 → 확정
- [ ] docs/PRD.md 생성 → PROJECT.md 문서 테이블 등록

### R3. TRD 작성 (Phase 2)
- [ ] PRD 기반으로 기술 요구사항 도출
- [ ] 내용: API 설계, 데이터 모델, 시스템 아키텍처 상세, 성능/보안 요구사항
- [ ] 캡틴 검토 → 확정
- [ ] docs/TRD.md 생성 → PROJECT.md 문서 테이블 등록

### R4. 로드맵 수립 (Phase 3)
- [ ] PRD/TRD 기반으로 프로젝트를 태스크로 분할
- [ ] 각 태스크에 적합한 스킬 판단 (otpd/otpds/otpwf)
- [ ] 우선순위, 의존성 정리
- [ ] 캡틴 검토 → 확정

### R5. 태스크 순차 실행 (Phase 4)
- [ ] 로드맵 순서대로 otp 스킬 실행
- [ ] 각 태스크 완료 시 PM 검토
- [ ] 진행 상황 추적 및 로드맵 갱신
- [ ] 캡틴에게 정기 보고 (태스크 완료 시)

### R6. PM 역할 수행
- [ ] .opal/AGENT.md의 PM 검토 기준으로 각 태스크 결과 검토
- [ ] 참조 문서(PRD, TRD 등) 워커에게 전달 보장
- [ ] PM 학습 루프 — 판단 불확실 시 캡틴에게 질문 → 확정 기준 기록
- [ ] 로드맵 변경이 필요하면 캡틴에게 제안

### R7. opi 연동
- [ ] opi 완료 후 원래 요청이 개발인 경우 opal-dev-builder 자동 호출
- [ ] opi가 만든 프로젝트 환경(docs/, .opal/) 활용

## 전체 흐름

```
캡틴: "//opi 번역 웹앱 만들어줘"
  │
  ▼
opi: 인터뷰 → 프로젝트 셋업
  │  (docs/PROJECT.md, ARCHITECTURE.md, CONVENTIONS.md, .opal/AGENT.md)
  │
  ▼
opal-dev-builder 자동 호출:
  │
  │  Phase 1: PRD 작성
  │    캡틴과 대화 → docs/PRD.md 초안 → 캡틴 검토 → 확정
  │
  │  Phase 2: TRD 작성
  │    PRD 기반 → docs/TRD.md 초안 → 캡틴 검토 → 확정
  │
  │  Phase 3: 로드맵 수립
  │    PRD/TRD 기반 태스크 분할 → 캡틴 검토 → 확정
  │    예:
  │    T1. 프로젝트 기본 구조 (//otpds)
  │    T2. 파일 업로드 기능 (//otpds)
  │    T3. OCR/텍스트 추출 (//otpds)
  │    T4. 번역 API 연동 (//otpds)
  │    T5. 결과물 생성 — PDF/HTML/이미지 (//otpd)
  │    T6. UI 구현 (//otpwf → //otpds)
  │
  │  Phase 4: 태스크 순차 실행
  │    T1 → otp-dev-short → PM 검토 → 완료
  │    T2 → otp-dev-short → PM 검토 → 완료
  │    ...
  │    T6 → otp-wf → otp-dev-short → PM 검토 → 완료
  │
  ▼
전체 완료 보고
```

## OPAL 스킬 체계에서의 위치

```
//opi                프로젝트 WHAT/WHY 정의 + 셋업
//odb                PRD/TRD + 로드맵 + 태스크 순차 실행 + PM   ← 이 스킬
//otpd / //otpds     개별 태스크 실행 (코드 개발)
//otpwf              개별 태스크 실행 (와이어프레임)
//otpdoc             개별 태스크 실행 (문서) ← 향후
```

## 제약 조건

- opi가 만든 프로젝트 환경(docs/, .opal/)을 활용한다 (다시 만들지 않음)
- otp 파이프라인의 기본 흐름은 변경하지 않는다 (개별 태스크 실행은 otp가 담당)
- PRD/TRD는 알투가 직접 작성한다 (플레이스홀더 치환 아님)
- 모든 문서는 캡틴 검토 후 확정
- 문서 등록 프로토콜 준수 (PROJECT.md 테이블 등록)

## 기술 스택

- Markdown (스킬 정의, PRD/TRD 문서)

## 관련 문서

- `tasks/033-opal-framework-doc-pm-restructure/` — opi/PM 재설계 (선행 태스크)
- `skills/opal-project-init/SKILL.md` — opi 스킬 (연동 대상)
- `skills/otp-dev/SKILL.md` — Full Task 오케스트레이터
- `skills/otp-dev-short/SKILL.md` — Short Task 오케스트레이터
- `opal/core/AGENT.md` — 글로벌 에이전트 (PM 역할)
