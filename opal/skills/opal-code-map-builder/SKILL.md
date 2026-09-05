---
name: opal-code-map-builder
description: |
  **@header 자산 구축·환경설정 스킬**. 프로젝트의 `@header` 기록 소스(`.opal/code-scan.json` `headerSource`)를 소유자 확정으로 세우고, `manifest` 프로젝트에서는 `.opal/code-map/` 매니페스트 자산을 구축·정비한다.
  반드시 이 스킬을 사용해야 하는 상황: "opal-code-map-builder", "opcmb", "코드 맵", "code-map", "헤더 자산".
  모드: init | update. 모드는 자산 존재 감지로 자동 판별한다.
alias: opcmb
triggers:
  - "^opcmb$"
  - "^opal-code-map-builder$"
  - "(?i)(코드\\s*맵|code-?map|헤더\\s*자산)"
version: "1.0"
domain: metadata
---

<!--
@header {
  "module": "opal-code-map-builder",
  "layer": "skill",
  "domain": "metadata",
  "description": "@header 자산 구축·환경설정 스킬 — headerSource 2택 확정 + code-map 매니페스트 구축·정비 (code-scan 호출층)",
  "exports": ["모드 판별(init|update|종료 분기)", "STEP 0~6 시퀀스", "update 모드(scaffold→validate)"],
  "depends": ["header-standard", "code-scan-management", "header-rules"]
}
-->

# opal-code-map-builder (코드맵 빌더)

## Harness

이 스킬은 단일 pilot 구조다. 하네스 부트스트랩에서 로드되지 않은 경우:
- `~/.opal/references/opal-harness.md` Read.

이 스킬은 `code-scan` 도구의 **호출층**이다 — 판정·기록은 도구가 하고, 스킬은 소유자 확정값 중개와 순서 집행만 한다. 도구는 `~/.opal/tools/code-scan/run.sh <command>`로 호출한다. 출력이 `"ok": false`이면 `"error"`·`"fix"` 필드를 확인하여 사용자에게 에스컬레이션한다.

절차의 원천 문서:
- `~/.opal/references/header-standard.md` §7 (2소스 표현) · §7.1 (`index.json` 필드)
- `~/.opal/references/pm/code-scan-management.md` §headerSource 필드 관리 · §`.opal/code-map/index.json` PM·소유자 관리 의무
- `~/.opal/references/harness/header-rules.md` §갱신 시점

---

## 모드 판별 — 자산 존재 감지

STEP 0에서 아래 표를 위에서 아래로 평가해 **최초 일치 행**의 모드를 확정한다.

| 조건 | 모드 |
|------|------|
| `.opal/code-scan.json` 부재 (또는 `headerSource` 미설정·무효) | **init** — 설정 확정부터 |
| `.opal/code-scan.json` 유효 + `headerSource: manifest` + `.opal/code-map/index.json` 부재 | **init** — 매니페스트 구축부터 |
| `.opal/code-scan.json` 유효 + `headerSource: manifest` + `index.json` 존재 | **update** |
| `.opal/code-scan.json` 유효 + `headerSource: inline` | **종료 분기** — `code-scan missing` 안내 반환 |

> `index.json`의 `status: draft|reviewed`는 **판별에 사용하지 않는다** — 소유자 리뷰 완료 표시 전용이다 (`header-standard.md` §7.1 `status` 행).

---

## STEP 시퀀스

| STEP | 행위 | 도구 호출 | 산출물 |
|------|------|----------|--------|
| 0 | 모드 판별 (위 표) | 파일 존재 확인 | 모드 확정 1줄 보고 |
| 1 | `headerSource` 2택을 소유자에게 제시 → 확정값 수령 | `code-scan init --header-source <값> --write` | `.opal/code-scan.json` |
| 1-x | `inline` 확정 시 **종료 분기** | `code-scan missing` | 미작성 파일 목록 + "이후 갱신은 하네스 §갱신 시점이 처리한다" 안내 |
| 2 | `manifest` — 초안 생성 | `code-scan discover [--out\|--dry-run]` | `.opal/code-map/index.json` (`status: draft`, `origin: discover`) |
| 3 | **소유자 리뷰 게이트** — `scopes`(root/anchors/stripPrefix/include/exclude)·`layerRules`·`domains` 요약 제시 후 승인 대기 | 없음 | 리뷰 요약 + 승인 |
| 4 | `status: draft` → `reviewed` 전환 | 없음(PM 또는 소유자 직접) | `index.json` 갱신 |
| 5 | 매니페스트 골격 생성 | `code-scan scaffold [--dry-run]` | `.opal/code-map/{scope}/*.json` |
| 6 | 무결성 확인 + 완료 보고 | `code-scan validate` | 커버리지·위반 요약 |

---

## STEP 0 — 모드 판별

1. `{프로젝트}/.opal/code-scan.json` 존재를 확인하고, 존재하면 최상위 `headerSource` 값을 읽는다.
2. `headerSource`가 `manifest`면 `{프로젝트}/.opal/code-map/index.json` 존재를 확인한다.
3. 위 표의 최초 일치 행으로 모드를 확정하고, 확정 결과를 **1줄로 보고**한 뒤 해당 STEP으로 진입한다.

| 확정 모드 | 진입 STEP |
|----------|----------|
| init (설정 부재·무효) | STEP 1 |
| init (매니페스트 부재) | STEP 2 |
| update | [update 모드](#update-모드) |
| 종료 분기 | STEP 1-x |

---

## STEP 1 — `headerSource` 2택 확정

`headerSource`는 **추론 대상이 아니다**. 도구는 이 2택을 추론하지 않으므로(`code-scan init`의 `init_header_source_required` `fix` 안내), 스킬이 소유자에게 2택을 제시하고 확정값을 인자로 중개한다.

**2택 제시 문구** (`code-scan-management.md` §최초 설정 절차 1번과 동일):

| 값 | 의미 |
|----|------|
| `inline` | 소스 파일에 직접 `@header` 주석을 기록한다 (기본 권장 — 소스 편집이 자유로운 저장소) |
| `manifest` | `.opal/code-map/` 외부 매니페스트에만 기록한다 (소스 편집이 제한되는 저장소) |

**사용자 확인**을 받아 값을 확정한 뒤 호출한다:

```bash
# 초안만 확인 (파일을 쓰지 않는다)
~/.opal/tools/code-scan/run.sh init --header-source <inline|manifest>
# 실제 생성
~/.opal/tools/code-scan/run.sh init --header-source <inline|manifest> --write
```

- 설정이 이미 있는데 `headerSource`가 무효로 남아 전 명령이 거부되는 경우, 도구 에러 출력의 `fix` 필드가 지시하는 복구 명령(`init --header-source <값> --write --force` — 원본은 `.bak` 백업)을 그대로 사용한다.
- 확정 후 분기: `inline` → STEP 1-x (종료) · `manifest` → STEP 2.

---

## STEP 1-x — `inline` 종료 분기

`headerSource: inline`은 code-map 자산을 만들지 않는 정상 상태다. 이 스킬은 매니페스트를 구축하지 않고 **여기서 종료한다**.

```bash
~/.opal/tools/code-scan/run.sh missing
```

반환 내용:
1. `@header` 미작성 파일 목록 (`code-scan missing` 출력)
2. 안내 1줄 — **"이후 갱신은 하네스 §갱신 시점이 처리한다"** (`harness/header-rules.md` §갱신 시점)

---

## STEP 2 — `discover` 초안 생성

```bash
~/.opal/tools/code-scan/run.sh discover [--out <path>] [--dry-run]
```

- 산출물은 `.opal/code-map/index.json` **초안**이며 `status: "draft"`, `origin: "discover"`가 실린다.
- 이미 `index.json`이 존재하면 도구가 `index_exists`로 거부한다 — `--dry-run`으로 먼저 미리보기하거나 `--out`으로 별도 경로에 생성한다.
- 초안은 자동 추론 결과다. **그대로 확정 채택하지 않고** STEP 3으로 넘긴다.

---

## STEP 3 — 소유자 리뷰 게이트

초안 값을 요약해 제시하고 **사용자 확인**을 받는다. 승인 전에는 STEP 4·5로 진행하지 않는다.

**요약 제시 항목**:

| 항목 | 확인 대상 |
|------|----------|
| `scopes` | `root` · `anchors` · `stripPrefix` · `include` · `exclude` |
| `layerRules` | `match` → `layer` 규칙 목록 |
| `domains` | 도메인별 `paths` 글롭 |
| `exclude` | code-map 연산 전용 추가 제외 디렉토리 |

> 도구는 도메인 경계·`include`/`exclude` 파일 집합 필터 정책을 판정하지 않는다 (`code-scan-management.md` §index.json PM·소유자 관리 의무 2번). 이 값들은 소유자가 확정하며, 스킬은 판정을 대신하지 않고 리뷰를 중개한다.

**빈 값 처리 — 소유자가 이 자리에서 채운다**

`discover` 초안은 추론 근거가 없는 항목을 비운 채 낸다 — `layerRules: []`·`domains: {}`(또는 일부 디렉토리만 덮은 `layerRules`)가 그 경우다. 빈 값은 **도구가 이후에 채우지 않으므로**, STEP 3의 리뷰가 곧 값 확정 자리다.

**[MUST]** `code-scan-management.md` §`.opal/code-map/index.json` PM·소유자 관리 의무 2번: "**도구는 도메인 경계·`include`/`exclude` 파일 집합 필터 정책을 판정하지 않는다** — 이 값들은 소유자가 확정한다."

| 빈 값 | 이 자리에서 확정할 내용 |
|-------|----------------------|
| `layerRules: []` (또는 일부 디렉토리 미포함) | `match` 글롭 → `layer` 규칙 목록을 소유자가 열거한다 (형태: `**/core/**` → `core`) |
| `domains: {}` | 도메인명 → `paths` 글롭 집합을 소유자가 확정한다 |

- 빈 값을 그대로 두고 진행하면 STEP 6 `validate`에 `uncovered:incomplete` 위반이 남고 `detail`에 미해소 필드(`layer`·`domain`)가 실린다 — 매니페스트 엔트리의 `layer`는 `layerRules`, `domain`은 `domains`에서 해소되기 때문이다.
- 스킬은 값을 **추측해 채우지 않는다** — 소유자 확정값을 수령해 `index.json`에 반영하는 중개만 한다.

---

## STEP 4 — `status: reviewed` 전환

소유자 승인이 끝나면 `index.json`의 `status`를 `"draft"` → `"reviewed"`로 갱신한다.

**전환 전 반영 확인** (선행 절차 — 순서가 계약이다):

1. `index.json`을 다시 읽어 STEP 3에서 소유자가 확정한 `scopes`·`layerRules`·`domains` 값이 **파일에 반영되어 있는지** 확인한다.
2. `layerRules`가 비어 있거나 `domains`가 `{}`로 남아 있으면 **전환하지 않고 STEP 3으로 되돌린다** — 리뷰 승인은 빈 값 확정을 포함한다.
3. 반영이 확인된 뒤에만 `status`를 `"reviewed"`로 갱신한다.

- 도구는 이 전환을 자동화하지 않는다 — **PM 또는 소유자가 직접** 갱신한다.
- `index.json` 파일 전체는 소유자·PM 관할이며 **워커 직접 편집 금지**다 (`harness/header-rules.md` §워커 권한 경계).
- 승인이 나오지 않은 상태에서 `status`를 임의로 `reviewed`로 바꾸지 않는다.

---

## STEP 5 — `scaffold` 매니페스트 골격 생성

```bash
~/.opal/tools/code-scan/run.sh scaffold [--dry-run]
```

- 산출물: `.opal/code-map/{scope}/{mirrorRel}.json` 패키지 매니페스트.
- 도구가 소유하는 관리 필드(`version`·`scope`·`dir`·`files` 키 목록)만 채워진 골격이다. `description`·`exports`·`depends`·`note`·`feature` 값 기입은 워커의 파일 변경 시점 몫이다 (`harness/header-rules.md` §갱신 시점 (a)).
- 예약 폴더명과 겹치는 소스 디렉토리가 있으면 `reserved_name_collision`으로 거부된다 — 사용자에게 에스컬레이션한다.

---

## STEP 6 — `validate` 무결성 확인 + 완료 보고

```bash
~/.opal/tools/code-scan/run.sh validate
```

- exit 0 = 위반 없음 / exit 1 = usage·schema 오류 / exit 2 = 위반 존재.

**정상 종료 경로 2종** — exit 코드만으로 스킬 성패를 판정하지 않는다.

| 종료 상태 | 잔여 위반 | exit | 판정 |
|----------|----------|------|------|
| **골격 완료** — STEP 5 골격에 내용이 아직 기입되지 않은 상태 | `draft`(`draft: true` 또는 빈 `description`) · `uncovered:incomplete` | **2** | **정상** — 스킬 실패가 아니라 **"기입 대기" 상태 표시**다 |
| **기입 완료** — 매니페스트 `files{}`에 `description`·`exports` 등이 채워진 상태 | 없음 | 0 | 정상 |

- 골격 완료가 정상인 근거: **[MUST]** `harness/header-rules.md` 도입부 "도구는 구조를 만들고 워커는 내용을 채운다". 내용 기입은 §갱신 시점 (a)(**파일 변경과 같은 자리에서** 워커가 기록)의 몫이며, 이 스킬은 대신 채우지 않는다 (STEP 5 동일 근거).
- 따라서 이 스킬은 **exit 0을 완료 조건으로 삼지 않는다** — 골격 완료 상태로 종료해도 스킬은 성공이다.

**완료 보고 필수 항목**:

| # | 항목 |
|---|------|
| 1 | **종료 상태** — `골격 완료`(기입 대기) / `기입 완료` 중 어느 것으로 종료했는지 |
| 2 | **잔여 `draft` 건수** (`counts.draft`) — 0이면 기입 완료 |
| 3 | 커버리지 요약 + 위반 요약(위반 종류별 건수) |

- `draft`·`uncovered:incomplete` **외의 위반**(`orphan`·`conflict`·`exports_not_found`·`uncovered:no_entry` 등)이 있으면 목록을 그대로 제시하고 사용자 지시를 받는다 — 스킬이 위반을 임의 봉합하지 않는다.

---

## update 모드

`index.json`이 이미 존재하는 `manifest` 프로젝트의 자산 정비 경로다. **STEP 5 → STEP 6**을 수행한다 (STEP 1~4는 이미 확정·리뷰된 자산이므로 반복하지 않는다).

**진입 트리거** (`code-scan-management.md` §갱신 트리거):

| # | 상황 |
|---|------|
| 1 | 신규 도메인/폴더 추가 — EXECUTE 결과로 새 도메인 또는 주요 폴더가 추가된 경우 |
| 2 | 대규모 리팩토링 — 폴더 구조가 변경된 경우 |
| 3 | 신규 기술 스택 추가 — 기존 `extensions`에 없는 확장자를 가진 언어가 도입된 경우 |

- `exclude`/`excludePatterns` 설정을 변경한 뒤에는 `scaffold`를 재실행해 매니페스트를 정리한다 — 변경 전 등재 파일이 `orphan`으로 남는다.
- `index.json`의 `scopes`·`layerRules`·`domains` 자체를 고쳐야 하는 경우는 소유자 관할이다. 스킬은 STEP 3의 리뷰 요약 형식으로 변경 필요 사실을 보고하고 **사용자 확인**을 받는다.
- `status`가 `draft`인 채로 방치된 자산을 발견하면 임의 확정 없이 소유자에게 리뷰 필요 사실을 보고한다.

---

## 경계 — 신설하지 않는 것

**[MUST]** `header-standard.md` §7: "`headerSource`는 프로젝트당 전역 1개다. … 두 소스는 모드에 의해 상호 배타이므로 경합·병합 규칙이 존재하지 않는다."

따라서 STEP 1의 2택은 **1회 확정**이며, 이 스킬은 다음을 만들지 않는다:

| 금지 | 이유 |
|------|------|
| 두 소스의 병합 경로 | 모드에 의한 상호 배타 — 경합·병합 규칙이 존재하지 않는다 |
| 자동 폴백 (미설정·무효 시 조용히 다른 모드로 동작) | 도구가 전 명령을 exit 1로 거부한다. 폴백은 없다 |
| 스코프별 `headerSource` 재선언 | 전역 단일 키 — 스코프에 넣으면 무시되고 stderr 안내 1줄만 나온다 |

- 이미 기록된 `headerSource`를 바꾸는 것은 저장소 전체의 헤더 자산 위치를 바꾸는 결정이므로, 임의로 전환하지 않고 **사용자 확인**을 다시 받는다.
- 헤더 값의 상시 갱신은 이 스킬의 관할이 아니다 — `harness/header-rules.md` §갱신 시점 (a)(b)(c)가 처리한다.

---

## 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.1 | 2026-09-04 23:45 | STEP 3에 빈 값(`layerRules: []`·`domains: {}`) 소유자 확정 절차 신설(`code-scan-management.md` §index.json 관리 의무 2번 인용 — 도구는 도메인 경계를 판정하지 않음) + STEP 4에 `reviewed` 전환 전 반영 확인 3단 선행 절차 + STEP 6에 `validate` 정상 종료 2종 구분(골격 완료=`draft`/`uncovered:incomplete` 잔존 exit 2 정상 = 기입 대기 표시 / 기입 완료 exit 0)과 완료 보고 필수 3항(종료 상태·잔여 `draft` 건수·커버리지·위반 요약) 명문화 — exit 0을 완료 조건으로 읽히던 문면 결손 해소. 모드 판별 4분기·§경계 원문 무변경 (106) |
| v1.0 | 2026-09-04 22:38 | 초기 작성 — frontmatter 계약 5필드(+`domain`), 모드 판별 4분기(자산 존재 감지), STEP 0~6 시퀀스(`init`→`discover`→소유자 리뷰→`status: reviewed`→`scaffold`→`validate`), `inline` 종료 분기(`code-scan missing`), update 모드(scaffold→validate), §경계(병합·자동 폴백·스코프별 재선언 미신설) (106) |
