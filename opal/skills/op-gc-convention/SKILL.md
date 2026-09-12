---
name: op-gc-convention
description: |
  **컨벤션 검사 단계 스킬**. 호출자가 지정한 파일 목록을 프로젝트 컨벤션 기준으로 read-only 검사하고
  Markdown 보고서와 machine-readable finding JSON을 산출한다.
  반드시 이 스킬을 사용해야 하는 상황: opal-pilot-gc CHECK 단계 또는 PM Gate가 컨벤션 검사를 디스패치할 때.
  필수 입력: project_root, target_files, output_dir, timestamp. 보장 출력: GC-CONVENTION 보고서, gc-findings-convention JSON, 반환 JSON.
---

# op-gc-convention — 컨벤션 검사

finding 필드·판정·legacy adapter·fingerprint는 `opal/core/references/harness/gc-finding-schema.md`가 소유한다.
이 문서는 그 문서를 참조하고 필드·판정표를 복제하지 않는다.

## 입력

| 파라미터 | 필수 | 설명 |
|---|---|---|
| `project_root` | O | 프로젝트 루트 절대 경로 |
| `target_files` | O | 검사 대상 파일 목록. 호출자가 확정한 명시 목록이 유일 기준이다 |
| `output_dir` | O | 보고서·JSON 산출 위치. `task_folder` 이름으로 전달돼도 같은 값으로 받는다 |
| `timestamp` | O | 산출물 파일명용 타임스탬프 (예: `2026-09-12T14-32-18`) |
| `scope` | X | 검사 범위 이름. `docs/PROJECT.md` "## 프로젝트 구성" 요소명 또는 `all` |
| `element` | X | 산출물 파일명 suffix. 병렬 호출 시 파일명 충돌을 막는다 |
| `baseline` | X | 직전 실행의 `gc-report.json` 경로 또는 `none` |
| `project_documents` | X | 호출자가 선별해 주입한 기준 문서 경로 목록 |

## 기준 선택 순서

아래 순서로 기준을 찾고, 각 finding의 `rule_id`·`source_tier`에 실제 출처를 남긴다.

1. `docs/CONVENTIONS.md` (허브+링크 모델 — 규약은 `opal/core/references/conventions-hub-model.md`)
2. 실행 설정 — formatter·linter·compiler·test 설정 파일
3. 인접 코드에서 관측한 패턴
4. 언어·프레임워크 공식 style guide
5. 검토된 community 참조 — advisory 고정

## 실행 절차

1. **입력 검증** — `target_files` 각 경로의 존재와 `project_root` 내부 여부를 확인한다.
   부재하거나 `project_root`를 이탈한 경로가 있으면 검사를 시작하지 않고 오류로 반환한다.
2. **기준 로드** — 기준 선택 순서대로 읽는다. `scope`가 주어지면 허브 링크에서 해당 영역 상세 문서를 병합한다.
   적용한 문서·설정을 결과 envelope의 `references`에 남긴다.
3. **검사 영역 확정** — 대상 파일의 언어·확장자에 해당하는 카테고리만 켠다.
   카테고리 목록은 `references/convention-categories.md`를 참조한다. 비활성 영역과 이유를 결과에 남긴다.
4. **파일 순회** — 각 파일을 Read하고 로드한 기준을 적용해 finding을 생성한다.
5. **산출** — 같은 데이터에서 Markdown 보고서와 finding JSON을 함께 만든다.
   보고서 골격은 `references/report-template.md`, 작성 예시는 `references/sample-report.md`를 따른다.

## 출력

- `{output_dir}/GC-CONVENTION-{timestamp}[-{element}].md`
- `{output_dir}/gc-findings-convention-{timestamp}[-{element}].json` — schema 문서 §2 envelope, `check: convention`

```json
{
  "artifact_path": "{output_dir}/GC-CONVENTION-{timestamp}[-{element}].md",
  "summary": "컨벤션 검사 결과 요약",
  "status": "completed | blocked",
  "blockers": [],
  "changed_files": ["산출한 보고서와 JSON 경로"]
}
```

## [MUST]

1. **read-only** — 검사 대상 소스 파일을 수정하지 않는다. `changed_files`에는 이 실행이 만든 산출물만 넣는다.
2. **대상 고정** — 입력 `target_files`를 그대로 쓰고 git 상태로 재선별하지 않는다.
   `checked_files`가 `target_files`와 다르면 `status: partial`로 낮추고 사유를 `missing_capabilities`에 적는다.
3. **기준 문서 부재는 중단 사유가 아니다** — `docs/CONVENTIONS.md`가 없으면 검사를 생략하지 않고
   실행 설정·인접 코드에서 관측한 규칙으로 수행한다. 이때 모든 finding의 `disposition`은 `advisory`,
   실행 `status`는 `partial`이며, 기준 문서 결측을 `missing_capabilities`에 기록한다.
   보고서의 초안 생성 유도는 유지한다. advisory는 차단 사유로 계산하지 않는다.
4. **충돌은 판정하지 않고 보고한다** — 기준 문서와 실행 설정이 충돌하면 임의로 한쪽을 우선하지 않고
   충돌 위치를 별도 finding으로 반환한다.
5. **도구 결과 재판정 금지** — formatter·linter가 낸 결과를 자연어 판단으로 뒤집거나 재분류하지 않는다.
6. **schema 복제 금지** — finding 필드·판정은 `opal/core/references/harness/gc-finding-schema.md`를 참조하고
   이 문서나 보고서에 필드표·판정표를 복제하지 않는다.
