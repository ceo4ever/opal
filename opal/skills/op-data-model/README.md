# op-data-model

> 이 스킬은 사용자가 직접 호출하지 않습니다. `opal-pilot-data-design`(opdd)이 MODEL 단계에서 디스패치합니다. (`//erm` alias를 통한 단독 호출도 이 스킬로 라우팅됩니다.)

개념(Mermaid)·논리(Mermaid)·물리(DBML) 3모드를 분리 발동하는 DB 모델링 단계 스킬입니다.

## 역할

`opal-db-agent`가 실행 주체이며, `db-architect.md` 페르소나를 사용합니다. concept → logical → physical 순으로 증분 설계하는 것이 기본 흐름이지만, 기존 개념/논리 ERD나 DDL·ORM 스키마가 주입되면 해당 모드부터 시작합니다. 기존 DB/DDL 스키마를 역공학하는 트랙에서는 physical(역추출·정규화) → logical(역산) 순으로만 진행하며 concept은 실행하지 않습니다.

- **개념 모드**: Mermaid `erDiagram`으로 엔티티·관계만 표현합니다. 관계명은 한글 동사형, 엔티티명은 영문 대문자에 한글명 끝 "정보" 필수, 속성은 작성하지 않고 M:N 관계도 해소하지 않은 채 허용합니다.
- **논리 모드**: 개념 ERD에 속성·PK·FK·UK를 추가합니다. 속성명은 반드시 DICT 표준사전(`op-data-dictionary` 산출물) 용어를 쓰며 미등록 용어는 사전에 먼저 등록합니다. M:N은 매핑 엔티티로 해소하고, 식별(`--`)/비식별(`..`) 관계를 구분합니다.
- **물리 모드**: 논리 ERD를 DBML로 변환합니다. `{스키마}_{주제영역}_{엔티티}_{유형}` 명명규칙을 적용하고, 도메인사전(`db-type-mapping.md`) 기준 DBMS 타입 매핑, FK 제약·인덱스, `created_dt`/`updated_dt` 오딧 컬럼을 포함합니다.

## 입력

- `mode`: `concept` / `logical` / `physical`(파이프라인은 순차 3모드, 단독 호출은 특정 모드)
- 기획서·TASK.md·사용자 대화(엔티티·관계 도출 근거)
- `{설계}` 변수(PROJECT.md 등록 경로 또는 인터뷰 확정 경로)
- 선택: 기존 ERD 파일(증분 설계 베이스라인), DICT 사전 경로(논리/물리 모드 필수)

## 출력

```
{설계}/개념모델링/ERD_{영역}.mermaid, .md
{설계}/논리모델링/ERD_{영역}_논리.mermaid, .md
{설계}/물리모델링/{프로젝트}.dbml
```

## 호출 시점

opdd 파이프라인 MODEL 단계, 또는 사용자가 "ERD 만들어줘"·"개념/논리/물리 모델링"·"엔티티 설계"를 요청할 때, `//erm` alias 호출 시 디스패치됩니다. 물리 모드 산출물(DBML)은 `op-data-ddl`이 입력으로 받습니다.

## 관련 문서

- `opal/skills/op-data-model/references/mermaid-guide.md`
- `opal/skills/op-data-ddl/references/dbml-guide.md`
- `opal/skills/op-data-dictionary/references/db-type-mapping.md`
