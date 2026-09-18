---
type: concept
title: fixture-vs-real 맹점 — 테스트 픽스처 통과·실데이터 버그 반복 교훈
tags:
- lesson
- testing
- bug
- fixture
sources:
- task:045
- task:039
- task:044
- task:140
related:
- memory-tool
- agentic-output-direct-verification-lesson
- canonical-identity-from-unique-key-not-shared-attribute
created: '2026-06-26'
updated: '2026-09-18'
status: active
---
## 개요

테스트 픽스처는 단순화된 형식을 사용하기 때문에, 실제 데이터가 가진 특수 문법(백틱·파이프·이스케이프 등)이나 실제 스키마 구조에서 발생하는 버그를 잡지 못한다. 픽스처 통과와 실데이터 동작은 독립 보장이 아니다 — 픽스처가 통과해도 실데이터에서 달리 동작할 수 있다. 이 교훈은 task:039 → task:044 → task:045로 반복 발현됐고, task:140에서 한 태스크 안에서만 5회 반복 발현되며 별도 대응 원칙이 추가됐다. (근거: task:045 DONE 추가작업 #2, task:140 DONE "달성하지 못한 것")

## 결정 배경 (WHY)

task:045에서 `delete`/`promote --with-file` 명령이 `migrate`로 변환된 MEMORY.md에서 실파일을 삭제하지 못하는 버그가 발생했다. 원인은 `migrate`가 파일 경로를 백틱으로 감싸는 형식(`` `memory/x.md` ``)을 생성하는데, `_resolve_memory_file` 함수가 이 백틱을 strip하지 않아 파일 경로를 찾지 못한 것이다. (근거: task:045 DONE 추가작업 #2)

테스트 픽스처는 백틱 없이 `memory/x.md` 형식을 사용했기 때문에 단위 테스트는 전원 통과했다. 실데이터(`migrate` 변환 후 MEMORY.md)에서만 발현하는 형태였다. PM이 직접 실데이터로 재현 검증해서 포착했다. (추론: 코드패턴 — `_resolve_memory_file` strip 1줄 수정으로 해결됐음이 단순 버그임을 시사)

동일한 유형의 맹점이 task:039와 task:044에서도 반복 발현된 바 있다(반복 교훈). (근거: task:045 DONE 추가작업 #2 "039/044 반복 교훈")

### task:140 — 한 태스크 안에서 5회 반복

OPAL Console 스킬 문서 화면(task:140)에서는 같은 유형의 맹점이 개발 과정에서 5회 발현됐다. 모두 "합성한 fixture가 실제 corpus의 형태·스키마를 대표하지 못했다"는 동일 원인의 변주였다. (근거: task:140 배경 신호)

1. 레지스트리 fixture를 평탄한 스킬 배열로 합성했으나, 실제 registry 스키마는 `groups` 구조였다.
2. adapter가 실재하지 않는 물리 레이아웃(`corpus_root/registry.json` 한 파일 아래 통합)을 전제로 설계됐다 — 실제로는 registry와 스킬 폴더가 분리된 다중 소스 레이아웃이다.
3. fixture registry의 `name` 자리에 frontmatter `name`을 넣어, canonical identity 파생 규칙을 잘못된 방향(frontmatter name 우선)으로 유도했다.
4. `paths` 필드 기반으로 canonical identity를 파생하는 실험적 설계는, 두 스킬이 같은 파일을 공유하는 실제 케이스(`opal-pilot-dev-short`)에서 한쪽 스킬이 카탈로그에서 소실되는 결과를 낳았다.
5. 커버리지 단언이 `records`(고유 레코드 수) 대신 `order`(중복 포함 순서 목록) 길이를 세어, 실제로는 레코드가 소실됐는데도 단언이 통과했다.

## 결정 내용

### 맹점 패턴 정의

픽스처-vs-실데이터 맹점은 아래 조건이 겹칠 때 발생한다:

1. 테스트 픽스처가 실데이터보다 단순한 형식·구조를 사용한다 (특수 문법 부재, 또는 실제 스키마·물리 레이아웃과 다른 단순 구조)
2. 실데이터가 도구 자체 출력물이거나, 다중 소스가 병합되는 복합 구조다 — 합성 fixture가 이 복합성을 반영하지 못하면 형식·구조 불일치가 발생할 수 있다
3. 파싱·경로 해석·식별자 파생 코드가 그 특수 문법·구조를 처리하지 못한다
4. (task:140에서 새로 확인) 커버리지·정합성 단언 자체가 "개수"만 세고 "정체성 유지"를 확인하지 않으면, 레코드 소실이 있어도 단언이 green으로 통과할 수 있다

### 대응 원칙

- **실데이터 회귀 픽스처**: 버그 발현 후 실데이터에서 추출한 형식을 픽스처로 추가한다. task:045는 백틱 포함 경로 형식을, task:140은 실제 registry `groups` 구조와 다중 소스 레이아웃을 반영한 fixture로 교정했다.
- **PM 직접 실행 검증**: 단위 테스트 통과만으로는 충분하지 않다. 도구가 실데이터에서 end-to-end로 동작하는지 직접 실행해서 확인한다. 특히 도구 A가 생성한 출력을 도구 B가 소비하는 파이프라인, 또는 다중 소스를 병합하는 파이프라인은 실데이터 검증이 필수다.
- **형식 생성 코드와 파싱 코드의 일관성**: 도구가 쓰는 형식과 읽는 코드를 동일 개발 사이클에서 검토한다 — 생성자와 소비자의 형식 계약이 명시적으로 일치해야 한다.
- **커버리지 단언은 고유 레코드 수를 세어야 한다 (task:140 신규)**: 순서·중복을 포함하는 목록(`order`)의 길이가 아니라, 정체성이 보존된 고유 레코드 집합(`records`)의 크기를 세야 소실을 감지할 수 있다. `len(order) == expected`는 중복이 소실을 상쇄해 거짓 통과를 만들 수 있다.
- **identity 파생 규칙은 공유 가능한 속성이 아니라 고유 식별자에서 파생해야 한다 (task:140 신규)**: 여러 레코드가 같은 물리 파일(`paths`)을 공유하는 것은 정상 설계일 수 있다. 파생 규칙이 공유 속성을 키로 쓰면 공유 그룹의 레코드가 병합·소실된다 — 고유해야 하는 식별자(레지스트리 `name` 등)에서 파생해야 한다.

### 해결 사례

- task:045: `_resolve_memory_file` 함수에 1줄 strip을 추가하여 백틱 감싸기를 제거했다. 버그 회귀 픽스처 3건을 테스트에 추가했다.
- task:140: canonical identity 파생을 `paths` 대신 레지스트리 `name`으로 교체했고, 커버리지 단언을 `order` 길이 대신 `records` 크기 기준으로 교정했다. fixture를 실제 `groups` 스키마·다중 소스 레이아웃으로 재작성했다.

## 영향 범위

- `opal/tools/memory-tool/memory_tool.py` — `_resolve_memory_file` strip 수정 (task:045)
- `opal/tools/memory-tool/tests/test_memory_tool.py` — 버그 회귀 픽스처 3건 추가 (task:045)
- `dashboard/backend/adapters/skill_docs_adapter.py`, `dashboard/backend/parsers/skill_parser.py`, `dashboard/backend/tests/fixtures/skill_docs_corpus/**` — canonical identity 파생·커버리지 단언·fixture 구조 교정 (task:140)

## 관련 페이지

- [[memory-tool]] — task:045 교훈이 발현된 도구
- [[agentic-output-direct-verification-lesson]] — PM 직접 검증의 필요성을 다루는 관련 교훈
- [[canonical-identity-from-unique-key-not-shared-attribute]] — task:140에서 분리한 identity 파생 원칙 상세
