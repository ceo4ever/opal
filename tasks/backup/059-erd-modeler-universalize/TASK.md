# TASK: erd-modeler 스킬 범용화

> 작성일: 2026-03-31 | 작업 유형: 개선
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

erd-modeler 스킬에서 프로젝트 특화 요소를 분리하여, 어떤 프로젝트에서든 범용적으로 사용 가능하도록 재구성한다.

## 배경

현재 erd-modeler 스킬은 MAMS 프로젝트 기준으로 작성되어 있어 다른 프로젝트에 그대로 적용하기 어렵다. 구체적으로:

- naming-convention.md에 MAMS 전용 약어표/SA코드가 포함
- data-dictionary 스킬 + `00.표준사전/` 폴더가 필수 의존으로 묶여 있어 사전이 없으면 모델링 자체 불가
- 폴더 구조(`{프로젝트}/{Phase}/DB설계/`)가 특정 구조에 종속
- dbml-guide.md 예시가 MAMS 테이블(`stl_ad_campaign_bsc` 등)로 고정
- 템플릿에 "알투(Altu)" 작성자가 하드코딩

## 요구사항

- [ ] **SKILL.md 범용화**: 프로젝트 특화 로직을 제거하고, 프로젝트별 컨텍스트를 외부에서 주입받는 구조로 전환
- [ ] **데이터 사전 유연화**: 사전 참조를 3단계 폴백으로 변경 — (1) 사용자가 위치 제공 시 해당 경로 Read (2) 없으면 내부 표준 자동 생성 (3) 웹 검색으로 외부 자료 활용 가능
- [ ] **naming-convention.md 범용화**: MAMS 전용 약어표를 "예시"로 격하하고, 실제 약어는 프로젝트별로 가져오는 구조로 전환. 규칙 자체(패턴, 원칙)만 범용으로 유지
- [ ] **dbml-guide.md 범용화**: MAMS 특화 예시(`stl_*`)를 프로젝트 중립적인 예시로 교체
- [ ] **mermaid-guide.md 범용화**: MAMS 특화 예시가 있으면 중립적으로 교체
- [ ] **폴더 구조 유연화**: 고정 경로(`{프로젝트}/{Phase}/DB설계/`) 대신 프로젝트에 맞는 출력 경로를 사용자에게 확인받는 구조로 변경
- [ ] **하드코딩 제거**: 작성자명 등 템플릿 내 고정값을 변수화

## 제약 조건

- 3단계 모델링 흐름(개념→논리→물리)과 DBML→DDL 변환 로직은 유지한다
- 기존 references/ 하위 파일 구조(dbml-guide.md, mermaid-guide.md, naming-convention.md)는 유지한다
- data-dictionary 스킬과의 연동 인터페이스는 유지하되, 필수 의존을 선택적으로 완화한다

## 기술 스택

- Markdown (SKILL.md, references)
- Mermaid (ERD 다이어그램)
- DBML (물리 모델링)

## 관련 문서

- `skills/erd-modeler/SKILL.md` — 현재 스킬 정의
- `skills/erd-modeler/references/naming-convention.md` — 명명규칙 (MAMS 특화)
- `skills/erd-modeler/references/dbml-guide.md` — DBML 가이드 (MAMS 예시)
- `skills/erd-modeler/references/mermaid-guide.md` — Mermaid 가이드
