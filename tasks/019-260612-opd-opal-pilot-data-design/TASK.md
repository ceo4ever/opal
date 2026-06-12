# TASK: opal-pilot-data-design — DB 설계 OPAL 내재화 구현

> 작성일: 2026-06-12 | 작업 유형: 신규 | 적용 스킬: opd (opds→opd 전환) | 모드: agentic
> 입력: 사용자 요청 + 설계 검토서
> 출력: TASK.md

## 작업 목표

DB 설계 업무를 OPAL 표준 3층 체계로 내재화한다. 오케스트레이터 `opal-pilot-data-design`(opdd)와 단계 스킬 3종(op-data-dictionary / op-data-model / op-data-ddl)을 신설하고, erd-modeler를 분해 이관하며 opal-db-agent를 확장한다.

## 배경

DB 설계 자산(erd-modeler·data-dictionary(유령)·opal-db-agent)이 OPAL 표준 컴포넌트 체계 밖에 흩어져 있다. 다단계 워크플로(개념→논리→물리→DDL)인데 오케스트레이션·State·Gate가 없고, 표준사전 CRUD 주체가 없다. 설계 검토서에서 표준 3층 승격안을 확정했다.

## 확정된 설계 방향 (대화에서 합의)

설계 검토서 `docs/proposals/opal-data-design.md`가 SSOT다. 핵심 확정 사항:

- **명명**: 오케스트레이터 `opal-pilot-data-design`(alias `opdd`) — pilot 접두사 체계 정합 (검토서 O-1 확정)
- **파이프라인**: `TASK → DICT → MODEL(개념·논리·물리) → DDL/MIGRATION(물리 이후만) → QA → CLOSE`
- **DICT 선행**: 표준사전이 논리/물리 모델링 속성명·타입 SSOT (검토서 §3.2)
- **MODEL 3모드 분리 발동**: concept/logical/physical 각 단독 발동 + 모드별 산출물 양식 (검토서 §3.2.1)
- **사전 포맷**: md SSOT + xlsx 뷰 단방향(md→export) (검토서 §3.2.2, O-2 확정)
- **실행 에이전트**: opal-db-agent 단일 (역할에 사전·코드 관리 추가)

## 요구사항

- [ ] **R-1 오케스트레이터 신설**: `opal-pilot-data-design/SKILL.md` 생성
  - 무엇을: opdd 오케스트레이터 SKILL.md (Harness/단계/STATE 행/3-way 모드/PM Gate)
  - 어디에: `opal/skills/opal-pilot-data-design/SKILL.md`
  - 왜: 검토서 §3.1·§3.2
  - AC: 파이프라인 `TASK→DICT→MODEL→DDL/MIGRATION→QA→CLOSE` 단계 정의 + STATE 행 예시(검토서 §3.5) + 단계별 op-data-* 워커 디스패치 명시 + DDL이 물리 이후 의존 명시 + opal-pilot-dev SKILL 구조 준수
- [ ] **R-2 단계 스킬 3종 신설**: op-data 그룹
  - 무엇을: `op-data-dictionary`, `op-data-model`, `op-data-ddl` SKILL.md
  - 어디에: `opal/skills/op-data-dictionary/`, `opal/skills/op-data-model/`, `opal/skills/op-data-ddl/`
  - 왜: 검토서 §3.1·§3.2.1·§3.2.2
  - AC: (DICT) 사전·코드 CRUD + md SSOT/xlsx export 명시 / (MODEL) concept·logical·physical 3모드 분리 발동 + 모드별 산출물 양식 / (DDL) DBML→DDL + 마이그레이션, 물리 입력 전제. 각 스킬이 op-* 단계스킬 표준 frontmatter·실행컨텍스트 준수
- [ ] **R-3 erd-modeler 분해 이관**: references + 모델링/DDL 로직
  - 무엇을: erd-modeler `references/`(mermaid-guide·dbml-guide·naming-convention) → op-data-* 스킬로 이관, erd-modeler deprecate 처리(`//erm`은 op-data-model alias 하위호환)
  - 어디에: `skills/erd-modeler/` → `opal/skills/op-data-*/references/`
  - 왜: 검토서 §4
  - AC: op-data-model/op-data-ddl가 이관된 references를 참조 + erd-modeler 깨진 참조(`../data-dictionary/`) 해소 + `//erm` 하위호환 경로 명시
- [ ] **R-4 opal-db-agent 확장**: 역할에 사전·코드 관리 추가
  - 무엇을: AGENT.md description·실행프로세스에 DICT(사전·코드 CRUD) + op-data-* 스킬 경로 인지 추가
  - 어디에: `opal/agents/opal-db-agent/AGENT.md`
  - 왜: 검토서 §3.1
  - AC: description에 사전·코드 관리 명시 + 단계 스킬 경로 인지 + 기존 모델링/마이그레이션 역할 보존
- [ ] **R-5 레지스트리·PROJECT.md 등록**: 컴포넌트 등재
  - 무엇을: opal-skills-registry.json에 opal-pilot-data-design(opdd) + op-data-* 3종 등록, PROJECT.md 주요 컴포넌트 표에 추가
  - 어디에: `opal/core/references/opal-skills-registry.json`, `docs/PROJECT.md`
  - 왜: 검토서 §4
  - AC: 레지스트리 JSON 유효(파싱 성공) + opdd alias 충돌 없음 + skill-registry match 동작 + PROJECT.md 컴포넌트 표 행 추가
- [ ] **R-6 install 배포 반영**: 신규 스킬 배포 경로
  - 무엇을: install 스크립트가 신규 스킬을 배포하는지 확인·반영 (배포 경계 — 소스 수정 후 install)
  - 어디에: `scripts/install/` 관련
  - 왜: AGENT.md 검토 기준 "배포 영향 항목 install 반영"
  - AC: 신규 스킬 디렉토리가 install 배포 대상에 포함 (와일드카드 배포면 자동, 명시 목록이면 추가)

## 미확정 사항 (PLAN에서 결정)

- **U-1 (검토서 O-3)** 사전·코드 SSOT 위치: `.opal/AGENT.md` 프로젝트 규칙 / `{설계}/사전/` / 별도
- **U-2 (검토서 O-4)** DICT 스킵 조건: 기존 사전 충분 시 "검증만" 축약 여부
- **U-3 (검토서 O-5)** `//erm` 하위호환 유지 기간·deprecation 안내 방식
- **U-4** xlsx→md 역방향 import 보조 모드 필요 여부 (검토서 §3.2.2 잔여)
- **U-5** STATE 행 모드 경계 위치 (DICT 후 vs MODEL 후 PM 자율 전환)

## 제약 조건

- 배포 경계 준수: 소스(`opal/skills/`, `opal/agents/`, `skills/`, `opal/core/`, `scripts/`)만 수정. `~/.opal/` 직접 편집 금지.
- 변경이력: 신규 SKILL.md·AGENT.md에 변경이력 표. 수정 문서(레지스트리 제외)에 행 추가.
- SSOT: 설계 검토서 `docs/proposals/opal-data-design.md`를 따른다. erd-modeler 기존 로직을 근거로 이관(상상 금지).
- 컴포넌트 표준: 신규 SKILL.md는 기존 pilot/단계스킬 구조(frontmatter·Harness·STATE 도메인 치환값·변경이력)를 준수.

## 기술 스택

- Markdown(스킬/에이전트 문서), JSON(레지스트리), Bash(install), DBML/Mermaid(모델링 산출물 양식)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | 설계 검토서 (SSOT) | `docs/proposals/opal-data-design.md` | 전체 설계 확정안 |
| D-2 | 소스 | erd-modeler SKILL | `skills/erd-modeler/SKILL.md` | 모델링/DDL 로직 이관 원천 |
| D-3 | 소스 | naming-convention | `skills/erd-modeler/references/naming-convention.md` | 사전 스키마·명명규칙 |
| D-4 | 소스 | opal-db-agent | `opal/agents/opal-db-agent/AGENT.md` | 에이전트 확장 대상 |
| D-5 | 설계 | opal-pilot-dev SKILL | `opal/skills/opal-pilot-dev/SKILL.md` | pilot 구조 템플릿 |
| D-6 | 설계 | 스킬 레지스트리 | `opal/core/references/opal-skills-registry.json` | 컴포넌트 등록 |
| D-7 | 설계 | PROJECT.md | `docs/PROJECT.md` | 주요 컴포넌트 등재 |
