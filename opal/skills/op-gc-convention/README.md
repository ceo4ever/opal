# op-gc-convention

> 이 스킬은 사용자가 직접 호출하지 않습니다. `opal-pilot-gc`가 CHECK 단계에서 디스패치합니다.

호출자가 지정한 파일 목록을 프로젝트 컨벤션 기준으로 read-only 검사하는 단계입니다.

## 역할

`opal-convention-checker` role 에이전트가 자체 규칙 없이 이 스킬을 읽어 수행합니다. 기준은 `docs/CONVENTIONS.md`(허브+링크 모델) → 실행 설정(formatter/linter/compiler/test) → 인접 코드 관측 패턴 → 언어·프레임워크 공식 style guide → community 참조(항상 advisory) 순으로 찾고, 각 finding의 `rule_id`·`source_tier`에 실제 출처를 남깁니다. 대상 파일의 언어·확장자에 해당하는 카테고리만 켭니다.

## 입력

- 필수: `project_root`, `target_files`(호출자가 확정한 명시 목록이 유일 기준), `output_dir`, `timestamp`
- 선택: `scope`, `element`, `baseline`, `project_documents`

## 출력

- `GC-CONVENTION-{timestamp}[-{element}].md` 보고서
- `gc-findings-convention-{timestamp}[-{element}].json` (`check: convention` envelope)
- 반환 JSON: `artifact_path`, `findings_path`, `check_status`(pass/partial/error), `missing_capabilities`, `blockers`, `changed_files`

## 호출 시점

`opal-pilot-gc` CHECK 단계 또는 PM Gate가 컨벤션 검사를 디스패치할 때 호출됩니다.

## [MUST] 경계

read-only이며 대상 소스 파일을 수정하지 않습니다. `target_files`를 그대로 쓰고 git 상태로 재선별하지 않습니다. `docs/CONVENTIONS.md` 부재는 중단 사유가 아니며(대체 기준으로 진행, finding은 advisory, status는 partial), 기준 문서와 실행 설정이 충돌하면 임의로 우선순위를 정하지 않고 별도 finding으로 보고합니다. formatter·linter 결과를 자연어 판단으로 뒤집지 않습니다.

## 관련 문서

- `opal/core/references/harness/gc-finding-schema.md`
- `opal/skills/op-gc-convention/references/convention-categories.md`
- `opal/skills/op-gc-convention/references/report-template.md`, `sample-report.md`
