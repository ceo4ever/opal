---
module: gc-finding-schema
role: GC 검사 finding schema·판정·legacy adapter SSOT
load: op-gc-security / op-gc-convention / op-gc-report 실행 시
상속: opal/core/PRINCIPLES.md
---

# GC finding schema

검사 스킬과 통합 보고 스킬은 이 문서의 필드·판정만 사용한다. 각 스킬 문서와 checker AGENT.md는
이 문서를 참조하고 필드·판정표를 복제하지 않는다.

## 1. finding 필드

| 필드 | 값 | 규칙 |
|---|---|---|
| `id` | `GC-{NNN}` | 단일 실행 내에서만 유효한 채번. 실행 간 동일성 근거로 쓰지 않는다 |
| `fingerprint` | hex 16자 | §4로 산출한다. 실행 간 동일 finding 판별의 유일한 키 |
| `category` | 문자열 | 검사 영역. 보안은 OWASP/CWE 카테고리, 컨벤션은 규칙 분류 |
| `severity` | `critical`·`high`·`medium`·`low`·`info` | 사실이라고 가정했을 때의 **영향 크기**만 표현한다 |
| `confidence` | `high`·`medium`·`low` | 그 판단이 **사실일 확률**. severity로 대체하지 않는다 |
| `disposition` | `blocking`·`advisory`·`informational` | 집행 수준. §5 `source_tier` 기본값에서 출발한다 |
| `rule_id` | 문자열 | 규칙 식별자(`OWASP-A01`, `CONVENTIONS.md §3` 등). 다르면 별건이다 |
| `source_tier` | `T0`~`T3` | 기준 출처 계층. §5 |
| `location` | `{file, line, symbol?}` | `file`은 `project_root` 기준 상대 경로 |
| `evidence` | 문자열 | 관측한 사실. secret 의심값·자격증명 원문은 복제하지 않고 위치만 남긴다 |
| `impact` | 문자열 | 이 상태가 유지될 때 발생하는 결과 |
| `remediation` | `{guidance, reference?, auto_fixable}` | 수정 안내. `auto_fixable`은 표시값이며 자동 수정 권한이 아니다 |
| `verification` | 문자열 | 수정이 됐음을 확인하는 관측 방법 |
| `suppression` | `{active, reason, scope}` 또는 `null` | 억제 상태. 억제된 finding도 결과에서 제거하지 않는다 |

`[MUST]` `severity`와 `confidence`를 한 축으로 합치지 않는다. 낮은 확신의 고영향 항목을 blocking으로
승격하려면 `confidence: high` 근거가 `evidence`에 있어야 한다.

## 2. check 결과 envelope

| 필드 | 값 | 규칙 |
|---|---|---|
| `check` | `security`·`convention` | 검사 종류 |
| `status` | `pass`·`partial`·`error` | 검사 **실행** 상태다. finding 유무가 아니다 |
| `checked_files` | 경로 배열 | 입력 `target_files`와 다르면 `status: partial`로 낮추고 사유를 `missing_capabilities`에 적는다 |
| `findings` | §1 객체 배열 | finding 0건도 빈 배열로 명시한다 |
| `evidence` | 문자열 배열 | 실행한 명령·읽은 설정 등 관측 근거 |
| `references` | 경로·URL 배열 | 적용한 기준 문서 |
| `missing_capabilities` | 문자열 배열 | 기준 문서 결측, 도구 부재, 접근 실패. 비어 있지 않으면 PASS 계열 판정이 금지된다 |
| `report_path` | 경로 | 같은 실행이 낸 Markdown 보고서 |

## 3. legacy adapter

현행 checker 이슈 레코드(`opal/agents/opal-security-checker/AGENT.md:100-111`)를 §1로 변환한다.

| legacy 필드 | §1 대상 | 변환 규칙 |
|---|---|---|
| `id` | `id` | 그대로 |
| `file` | `location.file` | `project_root` 상대 경로로 정규화 |
| `line` | `location.line` | 그대로 |
| `category` | `category` | 그대로 |
| `severity` | `severity` | 소문자 정규화. `Info` → `info` |
| `source` | `rule_id` + `source_tier` | `Base (OWASP-A01)` → `rule_id: OWASP-A01`, `source_tier: T1`. `프로젝트(SECURITY.md §N)` → `rule_id: SECURITY.md §N`, `source_tier: T0` |
| `description` | `impact` | 결과 서술만 남기고 관측 사실은 `evidence`로 분리한다 |
| `fix_hint` | `remediation.guidance` | 그대로 |
| `auto_fixable` | `remediation.auto_fixable` | 아래 규칙 |
| `reference_url` | `remediation.reference` | 그대로 |
| `fingerprint` | `fingerprint` | §4로 재산출한다 |

legacy에 없는 `confidence`·`disposition`·`verification`·`suppression`은 변환 시 채운다.
근거가 없으면 `confidence: medium`, `suppression: null`을 기본값으로 쓴다.

`auto_fixable` 처리 규칙:

- `[MUST]` `auto_fixable: true`는 표시값일 뿐이다. 검사 스킬은 read-only이며 이 값으로 수정을 실행하지 않는다.
- `[MUST]` `disposition`은 `auto_fixable`로 결정하지 않는다. §5 `source_tier` 기본 집행 수준으로 결정한다.

## 4. fingerprint 산출

```
fingerprint_input = "{category_id}|{normalized_tokens}"
fingerprint = sha1(fingerprint_input).hex()[:16]

정규화 순서:
1. 코드 스니펫 ±3줄 추출
2. 주석 제거
3. 문자열 리터럴 → STR
4. 숫자 리터럴 → NUM
5. 식별자 → ID (언어별 정규식)
6. 연속 공백 → 단일 스페이스
7. 파일 경로·라인 번호 제외
```

`[MUST]` 이 알고리즘을 스킬별로 변형하지 않는다. 파일 경로와 라인이 입력에서 빠지므로 코드 이동은
신규 finding을 만들지 않는다.

## 5. source_tier와 기본 집행 수준

| tier | 출처 | 기본 집행 수준 |
|---|---|---|
| `T0` | 프로젝트 SSOT 문서(`docs/SECURITY.md`·`docs/CONVENTIONS.md`)와 실행 설정(formatter·linter·CI) | `blocking` 가능 |
| `T1` | 승인된 공식 표준(OWASP Top 10, CWE Top 25, SANS Top 25, 언어 공식 style guide) | `blocking` 가능 |
| `T2` | 검토된 community 참조 | `advisory` 고정 |
| `T3` | 미검토 외부 출처 | `disabled` — finding을 생성하지 않는다 |

- `[MUST]` 사용자 승인 없이 T2·T3를 enforce로 승격하지 않는다. `severity`가 높다는 사실은 승격 근거가 아니다.
- T0과 T1이 충돌하면 T0이 우선한다. 임의 병합 없이 충돌 위치를 별도 finding으로 남긴다.

## 6. 최종 판정

| 판정 | 조건 |
|---|---|
| `PASS` | 모든 check `status: pass`, `missing_capabilities` 전건 비어 있음, `disposition: blocking` finding 0건, advisory 0건 |
| `PASS_WITH_ADVISORIES` | `PASS` 조건에서 advisory·informational finding만 존재 |
| `FAIL` | 모든 check가 실행됐고 `disposition: blocking` finding이 1건 이상 |
| `INCOMPLETE` | 어느 check라도 `status`가 `partial`·`error`이거나 `missing_capabilities`가 비어 있지 않음 |

- `[MUST]` `INCOMPLETE` 조건이 성립하면 blocking finding 유무와 무관하게 PASS 계열을 산출하지 않는다.
  결측과 통과를 같은 판정으로 묶지 않는다.
- `[MUST]` `advisory`·`informational`은 차단 사유로 계산하지 않는다. 기준 문서 결측으로 전건이
  advisory가 된 실행은 `INCOMPLETE`로 보고되며, 그 사실만으로 호출 파이프라인을 차단하지 않는다.
- `INCOMPLETE`와 동시에 blocking finding이 있으면 판정은 `INCOMPLETE`로 두고 blocking 항목을
  보고서의 차단 항목 절에 그대로 싣는다.

## 7. baseline delta

비교 키는 `fingerprint`다. `fingerprint`가 같아도 `rule_id`가 다르면 별건으로 본다.

| 분류 | 조건 |
|---|---|
| `new` | 현재 실행에만 있음 |
| `persisting` | 양쪽에 있음 |
| `resolved` | baseline에만 있음 |
| `suppressed` | 현재 실행에 있고 `suppression.active: true` |

- `suppressed`는 `new`·`persisting`과 겹칠 수 있으므로 별도 집계로 싣고 차단 계산에서 제외한다.
- `[MUST]` baseline이 `none`이면 현재 finding 전건을 `new`로 표기한다. baseline 부재를 `resolved` 0건
  이상의 다른 의미로 해석하지 않는다.
- `resolved` 판정은 해당 파일이 이번 `checked_files`에 포함된 경우에만 유효하다. 검사되지 않은 파일의
  baseline finding은 `persisting`으로 유지한다.
