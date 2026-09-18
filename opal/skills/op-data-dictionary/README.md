# op-data-dictionary

> 이 스킬은 사용자가 직접 호출하지 않습니다. `opal-pilot-data-design`(opdd)이 DICT 단계에서 디스패치합니다.

표준단어사전·도메인사전·코드사전 3종 md SSOT를 작성·검증·보강하고, xlsx 뷰를 단방향 export하는 표준사전·표준코드 관리(DICT) 단계 스킬입니다.

## 역할

`opal-db-agent` 워커 에이전트의 컨텍스트에서 실행됩니다. DICT 단계는 오케스트레이터가 디스패치할 때마다 항상 실행되며, 기존 사전 주입 여부에 따라 신규 작성 모드(사전 없음, 또는 있어도 커버리지 불충분)와 검증·보강 모드(기존 사전 있음 + 커버리지 충분)로 자동 분기합니다.

수정은 md에서만 하며, xlsx는 `xlsx-tool`이 md를 export한 파생물일 뿐 원본이 아닙니다. 역방향(xlsx→md) 수정은 금지되어 SSOT가 혼선되지 않습니다. 사전 저장 경로는 하드코딩하지 않고 `docs/PROJECT.md`에 등록된 `{설계}` 변수를 읽어 `{설계}/사전/`으로 해소하며, 미등록 시 `200.설계/` 탐색 → default `200.설계/210.사전/` 제안 순서로 확정합니다.

작성 시 `opal-db-agent`의 `db-architect.md` 페르소나와 `references/naming-convention.md`(수식어·분류어 약어), `references/db-type-mapping.md`(D001~D022 DBMS별 타입 매핑)를 근거로 사용합니다.

## 입력

| 항목 | 설명 |
|------|------|
| 필수 입력 | 프로젝트 컨텍스트(서비스 기획서 / 기존 사전 md / ERD·스키마 중 1종 이상) |
| 선택 입력 | 기존 `표준단어사전.md`, `도메인사전.md`, `코드사전.md`(주입 시 검증·보강 모드) |

## 출력

- `{설계}/사전/표준단어사전.md`, `도메인사전.md`, `코드사전.md` (보장 출력, md SSOT)
- `{설계}/사전/*.xlsx` (선택 출력, xlsx-tool export 파생물)

표준단어사전은 수식어·분류어 표, 도메인사전은 D001~D022 도메인별 DBMS 타입 매핑 표, 코드사전은 코드성 컬럼(`_cd`, `_yn`, `_clsf`, `_tp` 등)의 CHECK 허용값 열거 표로 구성됩니다.

## 호출 시점

opdd 파이프라인의 DICT 단계에서, MODEL 단계(논리/물리 모델링)의 속성명·타입 SSOT로 쓰일 사전이 필요할 때 디스패치됩니다. `op-data-model`의 논리 모드가 표준단어사전을, 물리 모드가 도메인사전·`db-type-mapping.md`를 참조합니다.

## 관련 문서

- `opal/skills/op-data-dictionary/references/naming-convention.md`
- `opal/skills/op-data-dictionary/references/db-type-mapping.md`
