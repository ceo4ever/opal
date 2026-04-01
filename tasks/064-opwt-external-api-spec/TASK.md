# TASK: opwt 외부 API 명세서 관리 타입 추가

> 작성일: 2026-04-01 | 작업 유형: 개선
> 입력: 사용자 요청 + PM 설계
> 출력: TASK.md

## 작업 목표

opwt에 "외부 API 명세서"를 선택 관리 타입으로 추가하여, 외부 API(메타, 구글광고 등 서드파티)를 연동하는 프로젝트의 기획 단계에서 API 스펙 분석·검토·산출물을 정책서·IA·와이어프레임·ERD와 논리적으로 연결 관리할 수 있게 한다.

## 배경

MAMS와 같이 외부 광고 API(Meta, Google Ads 등)를 호출하여 대시보드를 구성하는 프로젝트에서는 기획 단계에서 외부 API 명세서를 작성·분석·검토하고, 이를 정책서·IA·와이어프레임·ERD와 논리적으로 연결해야 한다.

현재 opwt의 `reference_artifacts.api-spec`은 외부에서 가져온 문서를 읽기 전용으로 참조하는 구조로, opwt가 직접 외부 API 명세서를 기획 산출물로 작성·관리하는 것은 지원하지 않는다.

**구분 원칙**:
- **외부 API 명세서** (기획 단계) — 서드파티 API 스펙 분석, 활용 정책 도출, 기획 산출물 간 연결 → opwt 관리
- **내부 API 설계** (개발 단계) — 시스템 자체 API 설계 → 개발 단계에서 별도 처리

## 요구사항

### A. SKILL.md 커버 범위 업데이트

- [ ] A1. 선택 타입에 "외부 API 명세서" 추가 (프로젝트 특화 선택 타입으로 명시)
- [ ] A2. 변경이력 v1.4 기록

### B. network-guide.md 업데이트

- [ ] B1. §1 산출물 유형 정의 — 선택 타입에 "외부 API 명세서" 추가 (설명, 수량, 적용 조건)
- [ ] B2. §2 논리적 연결 맵 — 외부 API 명세서 연결 추가:
  - 외부 API 명세서 ↔ TRD: API 제공 스펙 → 기술 요구사항
  - 외부 API 명세서 ↔ 서비스 정책서: API 제약/한도 → 정책 규칙 반영
  - 외부 API 명세서 ↔ IA: 제공 데이터 필드 → 기능 정의
  - 외부 API 명세서 ↔ 와이어프레임: API 응답 데이터 → 화면 구성 검증
- [ ] B3. §5 diagnosis.json 스키마 — `documents[].type`에 `외부 API 명세서` 추가
- [ ] B4. §7 Phase 3 워커 프롬프트 — 외부 API 명세서 신규 작성 템플릿 추가
- [ ] B5. §10 외부 참조 산출물 — `reference_artifacts.api-spec` 설명을 "내부/개발 단계 참조용"으로 재정의하여 외부 API 명세서(관리 타입)와 명확히 구분

### C. consistency-rules.md 업데이트

- [ ] C1. 외부 API 명세서 크로스 체크 규칙 추가:
  - 외부 API 명세서 ↔ TRD: API 엔드포인트/파라미터 정합성
  - 외부 API 명세서 ↔ 서비스 정책서: API 한도·제약 조건이 정책에 반영되었는가
  - 외부 API 명세서 ↔ IA: API 응답 필드가 기능 정의에 반영되었는가

## 제약 조건

- 외부 API 명세서는 **선택 타입** — 모든 프로젝트가 아닌, 외부 API 연동 프로젝트에서만 활용
- 기존 8종 관리 구조(필수 4종 + 선택 4종) 변경 없음 — 선택 타입으로 추가
- 내부 API 설계(개발 단계)와 명확히 구분 — SKILL.md 및 network-guide.md에 주석 필수
- `reference_artifacts.api-spec` 제거 금지 — 역할을 "내부 개발 참조용"으로 재정의하여 공존

## 기술 스택

- Markdown 문서 (SKILL.md, network-guide.md, consistency-rules.md)

## 관련 문서

- `opal/skills/opal-pilot-write-tech/SKILL.md` — opwt 오케스트레이터 (v1.3)
- `opal/skills/opal-pilot-write-tech/references/network-guide.md` — 산출물 네트워크 가이드
- `opal/skills/opal-pilot-write-tech/references/consistency-rules.md` — 정합성 검증 규칙
- `tasks/062-opwt-external-refs/` — 외부 참조 산출물 지원 (062, 선행 작업)
