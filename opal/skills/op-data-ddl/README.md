# op-data-ddl

> 이 스킬은 사용자가 직접 호출하지 않습니다. `opal-pilot-data-design`(opdd)이 DDL/MIGRATION 단계에서 디스패치합니다.

MODEL 물리(DBML) 산출물을 입력으로 받아 DBMS별 DDL 스크립트와 ORM 마이그레이션 코드를 생성하는 DDL/마이그레이션 생성 단계 스킬입니다.

## 역할

`opal-db-agent`가 실행 주체이며, `db-architect.md` 페르소나를 사용합니다. `op-data-model`의 물리(DBML) 산출 이후에만 실행 가능하며, `{설계}/물리모델링/{프로젝트}.dbml`이 존재하지 않으면 state-tool stage-transition guard가 자동 차단하고 이 스킬도 즉시 블로커를 보고합니다.

변환은 `dbml2sql` CLI 사용을 우선하고, CLI가 없으면 `references/dbml-guide.md`와 `op-data-dictionary/references/db-type-mapping.md`를 SSOT로 삼아 수동 변환 규칙표(예: `bigint [pk, increment]` → `BIGINT AUTO_INCREMENT PRIMARY KEY`)를 적용해 폴백합니다. 기존 DB에서 DBML을 역추출해야 할 때는 `sql2dbml`로 역공학하며, 그 결과는 `op-data-model`의 물리 모드 산출물 경로에 저장합니다. ORM을 쓰는 프로젝트에서 마이그레이션 스크립트가 요청되면 Alembic·Django ORM·Prisma·TypeORM·Sequelize 등 ORM별 관례에 맞춰 생성하고 DDL과의 정합성(테이블명·컬럼명·타입·제약·FK·인덱스)을 검증합니다.

## 입력

| 항목 | 설명 |
|------|------|
| 필수 입력 | `{설계}/물리모델링/{프로젝트}.dbml`(MODEL 물리 산출물) |
| 선택 입력 | 대상 DBMS(미지정 시 확인), 기존 DDL·마이그레이션(증분 모드) |

## 출력

- `{설계}/DDL/{프로젝트}_{DBMS}.sql`(보장 출력) — DBMS별 CREATE TABLE + INDEX + FK DDL
- ORM 마이그레이션 스크립트(선택 출력, ORM 사용 프로젝트에서 요청 시)

## 호출 시점

opdd 파이프라인의 DDL/MIGRATION 단계에서, MODEL의 물리(DBML) 산출이 완료된 이후에만 디스패치됩니다. 물리 DBML 입력 전제가 충족되지 않으면 이 단계를 시작하지 않고 MODEL physical 단계 완료를 요구합니다.

## 관련 문서

- `opal/skills/op-data-ddl/references/dbml-guide.md`
- `opal/skills/op-data-dictionary/references/db-type-mapping.md`
