# op-gc-report

> 이 스킬은 사용자가 직접 호출하지 않습니다. `opal-pilot-gc`가 각 검사(security/convention 등) 완료 후 디스패치합니다.

각 검사가 낸 결과 JSON을 정규화해 단일 릴리스 판정과 baseline delta, 문서 업데이트 트리거를 산출하는 단계입니다.

## 역할

이 스킬은 검사자가 아니라 **결과 정규화와 릴리스 판정**만 소유합니다. 새 finding을 만들지 않고, 소스 파일을 다시 읽어 검사하지 않습니다. `fingerprint`+`location`+`rule_id` 세 값이 모두 같은 finding만 병합하고, baseline과 비교해 `new`/`persisting`/`resolved`/`suppressed`를 분류합니다. `disposition: blocking` finding만 차단 대상으로 계산하며, community 참조(T2) advisory를 severity가 높다고 blocking으로 승격하지 않습니다.

## 입력

- `project_root`(경로 정규화 기준), `output_dir`, `timestamp`
- `findings_inputs`: 각 check가 낸 결과 JSON 경로 배열
- `baseline`: 직전 실행의 `gc-report.json` 경로 또는 `none`

## 출력

- `GC-REPORT-{ts}.md`, `gc-report.json` (같은 데이터에서 동시 생성)
- 판정: `PASS` / `PASS_WITH_ADVISORIES` / `FAIL` / `INCOMPLETE`
- 문서 업데이트 트리거 3종(빈도/심각도/새 카테고리)을 독립 판정해 보고서에 각각 표기
- 반환 JSON: `status`, `verdict`, `report_path`, `json_path`, `delta`, `missing_capabilities`, `blockers`

## 호출 시점

`opal-pilot-gc`가 개별 GC 검사(security·convention 등)의 findings JSON을 모두 확보한 뒤, 최종 릴리스 판정을 위해 디스패치합니다.

## [MUST] 경계

`output_dir` 밖에 쓰지 않습니다. 결측(`status: partial`/`error`, `missing_capabilities` 존재) 상태를 pass와 같은 판정으로 묶지 않습니다. 입력 JSON을 하나도 읽을 수 없으면 판정을 만들지 않고 `status: blocked`로 반환합니다.

## 관련 문서

- `opal/core/references/harness/gc-finding-schema.md` (envelope·fingerprint·source_tier·판정표·baseline delta SSOT)
- `opal/skills/op-gc-report/references/report-template.md`
