---
name: op-gc-report
description: |
  GC 검사 결과 JSON을 정규화해 단일 릴리스 판정과 baseline delta, 문서 업데이트 트리거를 산출한다.
  필수 입력은 project_root, output_dir, timestamp, findings_inputs, baseline이며
  보장 출력은 같은 데이터에서 생성한 GC-REPORT-{ts}.md와 gc-report.json이다.
---

# op-gc-report

## 입력과 책임

- `project_root`: 경로 정규화 기준. 모든 `location.file`은 이 경로 기준 상대 경로다
- `output_dir`: 산출물을 쓰는 디렉토리
- `timestamp`: 산출물 파일명에 쓰는 `{ts}`
- `findings_inputs`: 각 check가 낸 결과 JSON 경로 배열
- `baseline`: 직전 실행의 `gc-report.json` 경로 또는 `none`

이 스킬은 검사자가 아니라 **결과 정규화와 릴리스 판정**을 소유한다.

- `[MUST]` 새 finding을 만들지 않는다. 입력 JSON에 있는 finding만 병합·분류·집계한다.
- `[MUST]` 소스 파일을 다시 읽어 검사하거나 기준 문서를 해석하지 않는다. 검사 영역 판단은 check 스킬의 책임이다.
- `[MUST]` `output_dir` 밖에 쓰지 않는다.
- `[MUST]` 외부에서 취득한 스킬·스크립트·체크리스트·참조 자료는 판정 근거로 **읽기만** 한다. 설치·실행하거나 프로젝트에 복사해 실행하지 않는다. 외부 자료에 근거한 finding은 기본 `advisory`이며 사용자 승인 없이 `enforce`로 승격해 차단 계산에 넣지 않는다. 집행 수준 조건은 `opal/core/references/harness/gc-finding-schema.md` §5를 참조하고 이 문서에 복제하지 않는다.

먼저 `opal/core/references/harness/gc-finding-schema.md`를 읽는다. finding 필드(§1), check 결과
envelope(§2), fingerprint(§4), `source_tier` 기본 집행 수준(§5), 최종 판정표(§6), baseline delta(§7)는
그 문서가 소유한다. 이 스킬은 조건을 복제하지 않고 참조만 한다.

## 처리 절차

### 1. 입력 schema와 checked_files 검증

- 각 `findings_inputs` 항목을 읽고 harness 문서 §2 envelope 필드를 확인한다. 필수 필드가 없거나 파싱에
  실패한 입력은 누락 check로 기록하고 `missing_capabilities`에 사유를 추가한다.
- 각 finding이 §1 필드를 갖는지 확인한다. `confidence`·`disposition`이 없으면 §3 adapter 기본값 규칙을 적용한다.
- check별 `checked_files` 합집합을 계산하고, 각 check의 `status`와 `missing_capabilities`를 그대로 보존한다.
- `[MUST]` 입력에서 관측되지 않은 check를 pass로 간주하지 않는다. 호출자가 기대한 check가 `findings_inputs`에
  없으면 그 사실을 `missing_capabilities`에 남긴다.

### 2. 중복 finding 병합

- 병합 키는 `fingerprint` + `location` + `rule_id` 세 값의 조합이다. 세 값이 모두 같은 finding만 1건으로 합친다.
- 병합 시 `severity`는 최대값, `confidence`는 최대값, `disposition`은 집행 수준이 높은 쪽을 취하고
  `evidence`·`references`는 합집합으로 유지한다.
- `[MUST]` `fingerprint`가 같아도 `rule_id`가 다르면 별건이다(§7). 서로 다른 check가 같은 코드에 낸 finding을
  하나로 뭉개지 않는다.

### 3. baseline 비교

- `baseline`이 경로면 그 `gc-report.json`의 finding 집합을 읽고, `none`이면 빈 집합으로 둔다.
- harness 문서 §7의 분류 규칙으로 `new`·`persisting`·`resolved`·`suppressed`를 산출한다.
- `[MUST]` `resolved`는 해당 파일이 이번 `checked_files`에 포함된 경우에만 유효하다. 검사되지 않은 파일의
  baseline finding은 `persisting`으로 유지한다.
- `[MUST]` `baseline: none`이면 전건을 `new`로 표기하고 `resolved`는 0건으로 둔다.

### 4. 차단 여부 계산

- 차단 대상은 `disposition: blocking` finding만이다. 계산 입력은 `source_tier`·`severity`·`confidence`·`disposition` 네 축이다.
- `[MUST]` community 참조(`source_tier: T2`) advisory를 `severity`가 높다는 이유로 blocking으로 승격하지 않는다(§5).
- `[MUST]` `suppression.active: true` finding은 차단 계산에서 제외하되 결과에서 삭제하지 않고 `suppressed`로 집계한다.
- `advisory`·`informational`은 차단 사유가 아니다.

### 5. 결측·partial 판정

- 어느 check라도 `status`가 `partial`·`error`이거나 `missing_capabilities`가 비어 있지 않으면 결측 상태다.
- 판정은 harness 문서 §6 판정표로 산출한다. `PASS` / `PASS_WITH_ADVISORIES` / `FAIL` / `INCOMPLETE` 조건은
  그 문서만 소유하며 이 스킬은 표를 복제하지 않는다.
- `[MUST]` 결측 상태를 pass와 같은 판정으로 묶지 않는다. 결측과 blocking이 동시에 있으면 판정과 별개로
  blocking 항목을 보고서 차단 항목 절에 그대로 싣는다.

### 6. Markdown·JSON 동시 생성

- `[MUST]` 두 산출물은 1~5단계가 만든 **같은 데이터 구조**에서 생성한다. Markdown 작성 중 수치를 다시
  세거나 JSON과 다른 집계를 쓰지 않는다.
- Markdown 골격은 `references/report-template.md`를 따른다.

## 문서 업데이트 트리거

`FREQ_THRESHOLD = 3` (파일 수 기준)

세 트리거는 서로 독립으로 판정하고, 보고서에도 각각 별개 항목으로 분리 표기한다.

| 트리거 | 판정 조건 | 표기 |
|---|---|---|
| 빈도 | 동일 `fingerprint`가 `FREQ_THRESHOLD`개 이상 **파일**에서 관측됨 | `[빈도 트리거]` |
| 심각도 | `severity`가 `critical` 또는 `high`인 finding 1건 이상 | `[심각도 트리거]` |
| 새 카테고리 | `docs/SECURITY.md`·`docs/CONVENTIONS.md`에 없는 `category` 관측 | `[새 카테고리 트리거]` |

- `[MUST]` 한 finding이 여러 트리거에 해당하면 각 트리거 항목에 중복 표기하고 하나로 합치지 않는다.
- 트리거는 문서 업데이트 **제안**만 만든다. 이 스킬은 기준 문서를 수정하지 않는다.

## 출력

| 산출물 | 경로 |
|---|---|
| Markdown 보고서 | `{output_dir}/GC-REPORT-{ts}.md` |
| 기계 판독 결과 | `{output_dir}/gc-report.json` |

`gc-report.json`은 최소 아래 필드를 싣는다.

```json
{
  "timestamp": "{ts}",
  "verdict": "PASS | PASS_WITH_ADVISORIES | FAIL | INCOMPLETE",
  "baseline": "{경로} | none",
  "checks": [{"check": "security", "status": "pass", "checked_files": [], "report_path": ""}],
  "delta": {"new": [], "persisting": [], "resolved": [], "suppressed": []},
  "findings": [],
  "blocking": [],
  "missing_capabilities": [],
  "doc_update_triggers": {"frequency": [], "severity": [], "new_category": []},
  "report_path": "{output_dir}/GC-REPORT-{ts}.md"
}
```

## 반환

```json
{
  "status": "completed | blocked",
  "verdict": "PASS | PASS_WITH_ADVISORIES | FAIL | INCOMPLETE",
  "report_path": "{output_dir}/GC-REPORT-{ts}.md",
  "json_path": "{output_dir}/gc-report.json",
  "delta": {"new": 0, "persisting": 0, "resolved": 0, "suppressed": 0},
  "missing_capabilities": [],
  "blockers": []
}
```

입력 JSON을 하나도 읽을 수 없으면 판정을 만들지 않고 `status: blocked`로 반환한다.
