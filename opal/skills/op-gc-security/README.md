# op-gc-security

> 이 스킬은 사용자가 직접 호출하지 않습니다. `opal-pilot-gc`가 CHECK 단계에서 디스패치합니다.

호출자가 지정한 대상 파일을 read-only로 검사해 보안 finding을 산출하는 단계입니다.

## 역할

`opal-security-checker` role 에이전트가 자체 검사 기준 없이 이 스킬을 읽어 수행하는 read-only 보안 진단입니다. 기준은 `docs/SECURITY.md`(T0) → 실행 설정·CI 보안 설정(T0) → `references/security-baseline.md`의 공식 표준(T1) → 검토된 community 참조(T2, 항상 advisory) 순으로 선택하며, 상위 기준과 충돌하면 상위가 이기고 충돌은 임의 병합하지 않고 별도 finding으로 남깁니다. 대상 파일 확장자·매니페스트로 감지된 검사 영역만 켭니다.

## 입력

- 필수: `project_root`, `target_files`(호출자가 확정한 유일 기준), `output_dir`, `timestamp`
- 선택: `scope`, `element`, `baseline`, `project_documents`

## 출력

- `GC-SECURITY-{timestamp}[-{element}].md` 보고서
- `gc-findings-security-{timestamp}[-{element}].json` (`check: security` envelope)
- 반환 JSON: `artifact_path`, `findings_path`, `check_status`(pass/partial/error), `missing_capabilities`, `blockers`, `changed_files`

## 호출 시점

`opal-pilot-gc` CHECK 단계 또는 다른 파이프라인이 보안 검사를 워커에게 디스패치할 때 호출됩니다.

## [MUST] 경계

read-only이며 소스 파일을 수정하지 않습니다. `target_files`를 그대로 사용하고 git 상태로 재선별하지 않습니다. 외부 자료 기반 finding은 기본 `advisory`이며 사용자 승인 없이 `enforce`로 승격하지 않습니다. 시크릿·자격증명 의심값의 원문은 보고서·JSON에 복제하지 않습니다.

## 관련 문서

- `opal/core/references/harness/gc-finding-schema.md` (finding 필드·envelope·fingerprint·판정 SSOT)
- `opal/skills/op-gc-security/references/security-baseline.md`
- `opal/skills/op-gc-security/references/report-template.md`, `sample-report.md`
