# DONE: opal-pilot-data-design — DB 설계 OPAL 내재화 구현

> 완료일: 2026-06-12 17:10 | 적용 스킬: opd (opds→opd 전환) | 모드: agentic
> 입력: TASK.md, ANALYSIS.md, PLAN.md, TEST-SCENARIO.md | 설계 SSOT: docs/proposals/opal-data-design.md

## 완료 요약

DB 설계 업무를 OPAL 표준 3층 체계(pilot + 단계 스킬 + 에이전트)로 내재화했다. 오케스트레이터 `opal-pilot-data-design`(opdd)와 단계 스킬 3종을 신설하고, standalone `erd-modeler`를 분해 이관하며 `opal-db-agent`를 사전·코드 CRUD 주체로 확장했다.

## 산출물 (신규 4 + 수정 4)

### 신규 컴포넌트
| 컴포넌트 | 경로 | 핵심 |
|---------|------|------|
| opal-pilot-data-design (opdd) | `opal/skills/opal-pilot-data-design/SKILL.md` | 파이프라인 TASK→DICT→MODEL→DDL/MIGRATION→QA→CLOSE, STATE 15행, DDL 물리의존, 모드경계 행8 |
| op-data-dictionary (DICT) | `opal/skills/op-data-dictionary/` | 사전·코드 CRUD, md SSOT 3종 + xlsx 단방향 export, +naming-convention 이관, +db-type-mapping(MySQL/PG/MSSQL/Oracle) |
| op-data-model (MODEL) | `opal/skills/op-data-model/` | concept/logical/physical 3모드 분리발동, 논리 속성명=DICT 용어, +mermaid-guide 이관 |
| op-data-ddl (DDL) | `opal/skills/op-data-ddl/` | DBML→DDL + ORM 마이그레이션, 물리 입력 전제, +dbml-guide 이관 |

### 수정
| 파일 | 변경 |
|------|------|
| `opal/agents/opal-db-agent/AGENT.md` | 6종 확장(description 사전·코드 관리, DICT 단계 인지, md/xlsx 자체로드, xlsx-tool export, op-data-* 경로, 디스패치 인식 섹션). 기존 모델링/마이그레이션 역할 보존 |
| `opal/core/references/opal-skills-registry.json` | opal-pilot 그룹에 opdd + op-data 그룹 3종 신설 + erd-modeler [deprecated] 표기 |
| `skills/erd-modeler/SKILL.md` | [DEPRECATED] 배너 + 깨진 참조(`../data-dictionary/`) 해소 + //erm 하위호환 안내 |
| `docs/PROJECT.md` | 주요 컴포넌트에 Data Design 파이프라인 표 추가 |

## 미확정 결정 (PLAN 확정, U-1~U-5)
- U-1 사전 위치: `{설계}/사전/` — opwt 패턴 차용(PROJECT.md {설계} 루트 등록 + default 트리 200.설계/), R-T1(경로 토큰 불일치) 해소. **캡틴 확정**
- U-2 DICT 스킵: 항상 발동 + 모드 분기(검증·보강 vs 신규 작성)
- U-3 //erm: alias 2 마이너 버전 유지 + 3단 안내, 제거는 후속 공지
- U-4 xlsx→md 역import: 범위 외(단방향만)
- U-5 STATE 모드 경계: MODEL 사용자확인 행8 후 PM 자율

## QA 결과 (TEST-SCENARIO S-1~S-7 ALL PASS)
- S-1 JSON 파싱 PASS / S-2 opdd 충돌0 / S-3 STATE 15행(배포전 대체검증) / S-4 깨진참조0 / S-5 references+4 DBMS / S-6 db-agent 회귀방지 / S-7 경로토큰 통일. 시크릿 0.

## 게이트 이력 (agentic)
게이트 7 Pass / Fail 0. 오류 1(ANALYSIS 워커 파일 미생성→PM 정착) / 에스컬레이션 2(opds→opd 전환, R-T1 사전경로). 상세: `AGENTIC-LOG.md`.

## 후속 태스크 후보
- **install 재배포**(소스→`~/.opal/`)로 opdd 실사용 활성화. 배포 후 `skill-registry match "opdd"`·`state-tool init --skill opdd` 실연동 재검증(S-2·S-3).
- 커밋(캡틴 지시 시): 018 README + 019 data-design + brain 누적 변경.
- U-3 //erm 제거 공지(2 마이너 버전 후), U-4 xlsx→md 역import 수요 발생 시 보조 모드.
