# ANALYSIS: opal-pilot-data-design 구현 — 이관 매핑 정밀화

> 작성: op-dev-analysis 워커 결과를 PM이 파일로 정착 (워커 파일 생성 누락 보정)
> 입력: TASK.md, 설계 검토서 `docs/proposals/opal-data-design.md`
> 성격: 검토서 확정 방향의 코드 수준 검증·정밀 매핑

## 0. 참조 문서

| # | 유형 | 경로 | 참조 이유 |
|---|------|------|----------|
| D-1 | 설계 | `docs/proposals/opal-data-design.md` | 확정 방향 SSOT |
| D-2 | 소스 | `skills/erd-modeler/SKILL.md` | 분해 원천 |
| D-3 | 소스 | `opal/agents/opal-db-agent/AGENT.md` | 확장 대상 |
| D-4 | 소스 | `opal/core/references/opal-skills-registry.json` | 등록 위치 |
| D-5 | 소스 | `scripts/install-mac.sh` | 배포 방식 |

## 1. erd-modeler 분해 매핑 (줄번호 기준)

| 원천 (erd-modeler) | 목적지 신규 스킬 |
|--------------------|-----------------|
| §3 사전 참조 `skills/erd-modeler/SKILL.md:55-79` | → op-data-dictionary |
| §4 ERD 모델링 `:82-165` (개념/논리/물리) | → op-data-model |
| §5 DDL 추출 `:194-253` (DBML→DDL·역공학) | → op-data-ddl |

**references 이관**:
- `skills/erd-modeler/references/naming-convention.md` → `op-data-dictionary/references/` (수식어/분류어·도메인 타입표)
- `skills/erd-modeler/references/mermaid-guide.md` → `op-data-model/references/`
- `skills/erd-modeler/references/dbml-guide.md` → `op-data-ddl/references/`

## 2. 깨진 참조 해소

- `skills/erd-modeler/SKILL.md:275-276`의 `../data-dictionary/references/naming-convention.md`·`db-type-mapping.md` → 신규 경로로 갱신
- `db-type-mapping.md`는 **신규 작성** 필요 (도메인 D001~ ↔ DBMS 타입 매핑 — 현재 naming-convention.md §1 분류어 표에 MySQL만 존재, PG/MSSQL 확장)

## 3. opal-db-agent 확장 지점 (6)

| 항목 | 추가 내용 |
|------|----------|
| description | + "표준사전·표준코드 관리(CRUD)" |
| 실행 프로세스 | DICT 스킬 인지 + 사전 경로(md SSOT/xlsx export) 관리 단계 |
| 자체 로드 문서 | 표준사전 입출력(md/xlsx) 항목 |
| MCP/도구 | xlsx-tool(사전 export) 명시 |
| 스킬 경로 인지 | op-data-dictionary/model/ddl 경로 |
| 신규 섹션 | "단계별 스킬 디스패치 인식" |

> db-agent는 이미 "데이터 모델링(개념/논리/물리) 작성·수정·관리 + 마이그레이션" + xlsx-tool 보유 → 확장이 자연스러움.

## 4. 레지스트리 등록

- **op-data 그룹 신설**: op-data-dictionary(DICT) / op-data-model(MODEL) / op-data-ddl(DDL), 각 `dispatched_by: [opal-pilot-data-design]`
- **opal-pilot 그룹에 추가**: `opal-pilot-data-design` / alias `opdd` / pipeline `TASK → DICT → MODEL → DDL/MIGRATION → QA → CLOSE`
- **alias 충돌**: `opdd` 미사용 — 충돌 없음(재확인)
- PROJECT.md §주요 컴포넌트에 "Data Design 파이프라인" 표 추가

## 5. install 배포 방식 — 자동 ✓

- `scripts/install-mac.sh`가 `$opal_dir/skills/*/` **와일드카드 순회**로 스킬 배포 (워커 확인: `:883-900` 근방)
- **결론**: 신규 스킬 디렉토리 생성 시 install 스크립트 수정 **불필요**. R-6은 "배포 자동 확인"으로 축소
- (단 PLAN에서 실제 배포 루프 줄번호 재확인 필요 — 워커 light 모델 추정치)

## 6. 단계 스킬 표준 패턴 (신규 작성 템플릿)

기존 op-dev-*/op-task-* frontmatter + 섹션 골격:
- frontmatter: `name` / `description`(반드시 이 스킬 사용 상황 + 필수 입력/보장 출력) / `version`
- 섹션: 실행 컨텍스트(citation-rules 의무) → 페르소나 → 입력/출력 → 프로세스(Step N) → 활용 MCP → 저장 경로 → 품질 체크리스트 → 변경이력
- 신규 페르소나: data-dictionary→data-steward, data-model→db-architect(기존 재사용 가능), data-ddl→db-engineer

## 7. 구현 순서 (의존)

1. op-data-dictionary + references (DICT 선행 — 사전이 모델 SSOT)
2. opal-pilot-data-design (오케스트레이터)
3. op-data-model + op-data-ddl (병렬 가능)
4. db-agent 확장 + 레지스트리 + PROJECT.md + erd-modeler deprecate

## 8. 리스크 / decision_required

| # | 리스크 | 대응 |
|---|--------|------|
| R-1 | erd-modeler 로직 이관 누락 | 줄번호 매핑(§1) 기준 검증 |
| R-2 | 깨진 참조 잔존 | §2 경로 갱신 + db-type-mapping 신설 |
| R-3 | 신규 스킬 구조 비일관 | §6 표준 템플릿 적용 |
| R-4 | install 줄번호 추정(light 모델) | PLAN에서 재확인 |

**decision_required (PLAN 확정)**: U-1 사전 SSOT 위치 / U-2 DICT 스킵 조건 / U-3 //erm deprecation / U-4 xlsx→md 역import / U-5 STATE 모드경계
