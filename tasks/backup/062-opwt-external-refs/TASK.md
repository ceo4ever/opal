# TASK: opwt 외부 참조 산출물 지원 + wtm wireframe 모드

> 작성일: 2026-04-01 | 작업 유형: 개선
> 입력: 사용자 요청 + 논의 내용
> 출력: TASK.md

## 작업 목표

opwt(opal-pilot-write-tech)가 와이어프레임, ERD, API 명세서 등 외부 참조 산출물을 활용하여 기획 문서를 작성/검증할 수 있도록 하고, wtm(web-to-markdown)에 wireframe 분석 모드를 추가한다.

## 배경

현재 opwt는 자체 관리 8종(PRD, TRD, 서비스 정책서, IA + 선택 4종) 간의 정합성만 다룬다. 실제 기획+개발 프로젝트에서는 다음과 같은 크로스 참조가 필수적이다:

- 와이어프레임(opdw 산출물)을 참조하여 정책서/IA 작성
- ERD(erd-modeler 산출물)와 정책서 크로스 체크
- 외부 API 명세서를 참조하여 TRD/정책서 작성

또한 와이어프레임은 브라우저 실행 가능한 코드이므로, 기획 관점에서 활용하려면 구조화된 .md 문서로 변환하는 수단이 필요하다.

### 대상 유스케이스

| UC | 시나리오 | 현재 상태 |
|----|---------|----------|
| UC2 | opwt 와이어프레임+ERD 참조 → 정책서 작성 | 갭 (외부 참조 없음) |
| UC3 | opwt 정책서를 ERD 기준 크로스 체크 | 갭 (크로스 체크 규칙 없음) |
| UC4 | opwt 정책서 분석 후 IA 작성 | 기존 커버 |
| UC5 | opwt 와이어프레임 참조 → IA 작성 | 갭 (외부 참조 없음) |
| UC6 | opwt 정책서+API 명세서 → erd-modeler로 ERD | PM 오케스트레이션으로 해결 |

## 요구사항

### A. wtm wireframe 모드

- [ ] A1. wtm SKILL.md에 `wireframe` 모드 추가 — 기존 full/clean에 추가되는 3번째 모드
- [ ] A2. wireframe 모드 산출물 형식 정의 — 화면 개요, 구성요소, 기능 동작, 네비게이션, 데이터 I/O 구조
- [ ] A3. 저장 경로 규칙 — PROJECT.md 문서 테이블에서 와이어프레임 관련 경로 매칭 → 없으면 기본값(`docs/wireframes/`)
- [ ] A4. 네이밍 규칙 — URL 경로 기반 kebab-case 파일명
- [ ] A5. 인덱스 자동 생성 — 복수 URL 처리 시 `_index.md` 생성/갱신
- [ ] A6. 복수 URL 병렬 처리 — 기존 wtm-agent 구조 그대로 활용

### B. opwt 외부 참조 산출물 지원

- [ ] B1. `diagnosis.json`에 `reference_artifacts[]` 필드 추가 — 스키마 정의
- [ ] B2. network-guide.md에 참조 산출물 가이드 섹션 추가 — 유형(wireframe, erd, api-spec 등), 활용 방법
- [ ] B3. Phase 3 워커 프롬프트에 `{reference_artifacts}` 플레이스홀더 추가 — 보강/재작성/신규 모든 템플릿
- [ ] B4. Phase 1 워커 프롬프트에도 외부 참조 분석 지시 추가

### C. 크로스 체크 규칙 확장

- [ ] C1. consistency-rules.md에 외부 참조 검증 섹션 추가 — ERD↔정책서, 와이어프레임↔IA, API 명세서↔TRD
- [ ] C2. QA 워커 프롬프트에 외부 참조 검증 절차 추가

## 제약 조건

- opwt는 외부 스킬(erd-modeler, opdw)의 존재를 직접 참조하지 않는다 — "문서가 인터페이스" 원칙 유지
- 스킬 간 파이프라인(UC6 등)은 PM 오케스트레이션으로 해결, opwt 자체에 스킬 위임 메커니즘을 넣지 않는다
- wtm wireframe 모드는 기존 3단계 폴백(WebFetch→Crawl4AI→Playwright) 위에 분석 레이어를 추가하는 형태
- 기존 opwt 8종 문서 관리 구조는 변경하지 않는다

## 기술 스택

- Markdown 문서 (SKILL.md, network-guide.md, consistency-rules.md)
- JSON 스키마 (diagnosis.json 확장)

## 관련 문서

- `opal/skills/opal-pilot-write-tech/SKILL.md` — opwt 오케스트레이터
- `opal/skills/opal-pilot-write-tech/references/network-guide.md` — 산출물 네트워크 가이드
- `opal/skills/opal-pilot-write-tech/references/consistency-rules.md` — 정합성 검증 규칙
- `skills/web-to-markdown/SKILL.md` → `~/.opal/skills/web-to-markdown/SKILL.md` — wtm 스킬 (소스 vs 배포)
- `skills/erd-modeler/SKILL.md` — erd-modeler 스킬 (참조용)
