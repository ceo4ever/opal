# TASK: otp-write 범용 문서 작성 오케스트레이터 개발

> 작성일: 2026-03-28 | 작업 유형: 신규
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

코드 구현을 수반하지 않는 모든 단일 문서 작성을 위한 오케스트레이터 스킬 `otp-write`를 개발한다. 기술/비기술 문서 모두 커버하며, 기존 doc-writer + version-mgr를 `opal-doc-standard.md` 참조 문서로 통합한다.

## 배경

현재 OPAL 프레임워크에는 "문서 하나를 체계적으로 작성"하는 전용 파이프라인이 없다:
- opdp는 프로젝트 전체 파일럿 (PRD/TRD → 로드맵 → 태스크)이지 단일 문서 작성이 아님
- doc-writer는 공통 규칙만 있고 프로세스가 없음
- 커뮤니티 스킬(doc-coauthoring 등)은 아이디어는 좋지만 OPAL 파이프라인에 통합 안 됨

## otp-write 커버 범위

### 가능한 문서 유형
- **기술 프로젝트 산출물**: PRD, TRD, IA, ERD, 정책서, API 명세서, 설계서
- **보고서**: 기술 분석 보고서, 비즈니스 분석 보고서, 상태 보고서
- **가이드/매뉴얼**: 사용자 매뉴얼, 온보딩 가이드, 운영 가이드
- **기획/제안**: 제안서, 기획서, RFP 응답
- **내부 커뮤니케이션**: 회의록, FAQ, 내부 공지

### otp-write가 아닌 것
- 코드 구현이 수반되는 작업 → otp-dev / otp-dev-short
- 프로젝트 전체 파일럿 (PRD+TRD+로드맵+태스크) → opdp
- 와이어프레임/UI 설계 → otp-wf
- 외부 API 분석 → api-analyzer

## 요구사항

### otp-write 스킬

- [ ] 3단계 파이프라인: TASK → PLAN → WRITE
- [ ] 오케스트레이터가 직접 수행 (워커 디스패치 없음 — 문서 작성은 사용자와 대화형 협업이 핵심)
- [ ] STEP 1 (TASK): dtp-task 활용하여 문서 유형/대상/범위/출력 형식 정의
- [ ] STEP 2 (PLAN): 소스 조사 + 목차/구조 설계 → [QA] → 사용자 검토
- [ ] STEP 3 (WRITE): 섹션별 작성 → doc-writer 베이스 적용 → 사용자 검토 → DONE.md
- [ ] 문서 유형별 소스 조사 방식 분기 (코드 분석 / 웹 조사 / 인터뷰 / 기존 문서 참조)
- [ ] 출력 형식 지원: .md 기본, .docx / .pdf는 커뮤니티 스킬 연동
- [ ] 게이트 체크포인트 (각 단계 완료 시 사용자 검토)
- [ ] 커밋 규칙: 사용자 명시 요청 시에만
- [ ] STATE.md 관리
- [ ] 200줄 이내 유지

### opal-doc-standard.md 참조 문서 생성

- [ ] `~/.opal/references/opal-doc-standard.md` 신규 생성
- [ ] doc-writer 핵심 내용 통합 (언어 규칙, 문서 헤더 템플릿, 테이블 규칙, 문서 유형별 필수 섹션)
- [ ] version-mgr 핵심 내용 통합 (버전 넘버링, 파일 관리, 변경이력)
- [ ] 120줄 이내 유지
- [ ] 참조 전용 (사용자 트리거 없음, 레지스트리 미등록)

### doc-writer + version-mgr 삭제 + 참조 대체

- [ ] skills/doc-writer/SKILL.md 삭제
- [ ] skills/version-mgr/SKILL.md 삭제
- [ ] "version-mgr" 참조 6곳 → "opal-doc-standard" 대체:
  - opal-skill-creator/SKILL.md (의존 테이블 + 본문)
  - opal-agent-creator/SKILL.md (의존 테이블 + 본문)
  - dtp-test-scenario/SKILL.md
  - dtp-analysis/SKILL.md
  - wireframe-builder/SKILL.md
  - dtp-analysis/references/tech-context-guide.md
- [ ] "doc-writer" 참조 3곳 → "opal-doc-standard" 대체:
  - opal-skill-creator/SKILL.md (의존 테이블)
  - opal-agent-creator/SKILL.md (의존 테이블)
  - dtp-analysis/references/tech-context-guide.md
- [ ] execute-plan-guide.md (2곳) 스킬 카탈로그에서 version-mgr/doc-writer → opal-doc-standard
- [ ] CLAUDE.md 소스 구조 + 의존 관계 업데이트

### 레지스트리 업데이트

- [ ] skills.md에서 doc-writer/version-mgr 삭제, otp-write 등록
- [ ] skill-guide.md에 otp-write 추가

## 제약 조건

- otp-write는 워커 디스패치 없이 오케스트레이터가 직접 수행
- doc-coauthoring 등 커뮤니티 스킬을 직접 Read하지 않음 — 핵심 패턴만 otp-write에 녹임
- 기존 dtp-task는 재활용 (수정 없음)
- dtp-qa는 PLAN 검토 시 재활용

## 기술 스택

- 마크다운 문서 (SKILL.md)

## 관련 문서

- [skills/doc-writer/SKILL.md](skills/doc-writer/SKILL.md) — 현재 doc-writer (삭제 → opal-doc-standard로 통합)
- [skills/version-mgr/SKILL.md](skills/version-mgr/SKILL.md) — 현재 version-mgr (삭제 → opal-doc-standard로 통합)
- [skills/otp-dev/SKILL.md](skills/otp-dev/SKILL.md) — 오케스트레이터 구조 참조
- [skills/otp-dev-short/SKILL.md](skills/otp-dev-short/SKILL.md) — 3단계 파이프라인 참조
- [community-skills/anthropics/doc-coauthoring/SKILL.md](community-skills/anthropics/doc-coauthoring/SKILL.md) — 패턴 참조
- [community-skills/anthropics/internal-comms/SKILL.md](community-skills/anthropics/internal-comms/SKILL.md) — 문서 유형 참조
