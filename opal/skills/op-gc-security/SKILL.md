---
name: op-gc-security
description: |
  **보안 검사 단계 스킬**. 호출자가 지정한 대상 파일을 read-only로 검사하고 보안 finding을 Markdown 보고서와 JSON으로 반환한다.
  반드시 이 스킬을 사용해야 하는 상황: opal-pilot-gc CHECK 단계나 다른 파이프라인이 보안 검사를 워커에게 디스패치할 때.
  필수 입력: project_root, target_files, output_dir, timestamp. 보장 출력: GC-SECURITY 보고서, gc-findings-security JSON.
---

# op-gc-security — 보안 검사

finding 필드·envelope·fingerprint·source_tier·판정은 `opal/core/references/harness/gc-finding-schema.md`가 소유한다.
실행 전에 그 문서를 읽고, 이 문서에는 복제하지 않는다.

## 1. 입력

| 파라미터 | 필수 | 값 |
|---|---|---|
| `project_root` | O | 프로젝트 루트 절대 경로 |
| `target_files` | O | 검사 대상 파일 목록. 호출자가 확정한 유일 기준 |
| `output_dir` | O | 산출물 디렉토리. 전환 기간 동안 `task_folder`를 alias로 허용하고 둘 다 오면 `output_dir`이 우선한다 |
| `timestamp` | O | 파일명용 타임스탬프 (예: `2026-04-17T14-32-18`) |
| `scope` | X | `frontend`·`backend`·`batch`·`mobile`·`all`. 기준 문서 상세 선택에 쓴다 |
| `element` | X | 요소명. 지정 시 산출물 파일명에 접미사로 붙는다 |
| `baseline` | X | 직전 실행의 `gc-report.json` 경로 또는 `none` |
| `project_documents` | X | 호출자가 선별해 넘긴 프로젝트 문서 경로 목록 |

## 2. 기준 선택 순서

1. `docs/SECURITY.md` — 프로젝트 SSOT. 허브+링크 구조면 `opal/core/references/conventions-hub-model.md` 규약으로 `scope`에 맞는 상세 문서까지 읽는다. `source_tier: T0`
2. 실행 설정·CI 보안 설정 — 의존성 감사, 시크릿 스캐너, 보안 linter 설정 등 실제로 집행되는 설정. `source_tier: T0`
3. `references/security-baseline.md`의 승인된 공식 표준 — OWASP Top 10, CWE Top 25, SANS Top 25, 스택별 도메인 항목. `source_tier: T1`
4. 검토된 community 참조 — 모든 finding은 `disposition: advisory`. `source_tier: T2`

상위 기준과 하위 기준이 충돌하면 상위가 이긴다. 임의로 병합하지 않고 충돌 위치를 별도 finding으로 남긴다.

## 3. 검사 영역 활성화

- 대상 stack과 `target_files`에 해당하는 영역만 켠다. 감지 근거는 대상 파일 확장자와 `package.json`·`requirements.txt`·`pyproject.toml`·`go.mod`·`pom.xml`·`build.gradle`·`Cargo.toml` 등 실재하는 매니페스트다.
- 근거 없이 켠 영역의 finding은 생성하지 않는다.
- 비활성 영역은 영역명과 비활성 이유를 결과 JSON의 `evidence`에 남긴다. 기준 문서·설정 결측으로 켤 수 없었던 영역은 `missing_capabilities`에도 기록한다.

## 4. 실행 절차

1. **대상 검증** — `target_files` 각 경로의 존재와 `project_root` 하위 여부를 확인한다. 부재 또는 이탈 경로가 있으면 검사를 시작하지 않고 `status: error`와 해당 경로를 반환한다.
2. **기준 로드** — §2 순서로 기준을 로드하고 적용한 문서 경로를 `references`에, 결측을 `missing_capabilities`에 기록한다.
3. **영역 활성화** — §3으로 검사 영역을 확정한다.
4. **Read 순회** — `target_files`를 순서대로 Read한다. 읽지 못한 파일은 건너뛰지 말고 사유와 함께 기록한다.
5. **finding 생성** — 관측된 위반마다 harness 문서 §1 필드로 finding을 만든다. `fingerprint`는 §4 알고리즘, `disposition` 기본값은 §5 `source_tier` 집행 수준에서 출발한다.
6. **envelope 구성** — harness 문서 §2로 `checked_files`·`status`·`evidence`·`references`·`missing_capabilities`를 채운다.
7. **산출** — §5 두 파일을 같은 데이터에서 생성한다.

## 5. 출력

- `{output_dir}/GC-SECURITY-{timestamp}[-{element}].md` — `references/report-template.md` 골격을 따른다. 작성 예시는 `references/sample-report.md`.
- `{output_dir}/gc-findings-security-{timestamp}[-{element}].json` — harness 문서 §2 envelope. `check: security`, `report_path`는 위 Markdown 경로.

`element`가 없으면 접미사 없이 저장한다.

## 6. 반환

```json
{
  "artifact_path": "{output_dir}/GC-SECURITY-{timestamp}[-{element}].md",
  "findings_path": "{output_dir}/gc-findings-security-{timestamp}[-{element}].json",
  "summary": "보안 검사 결과 요약",
  "status": "completed | blocked",
  "check_status": "pass | partial | error",
  "missing_capabilities": [],
  "blockers": [],
  "changed_files": ["생성한 보고서·JSON 경로만"]
}
```

## 7. [MUST]

1. `[MUST]` 이 스킬은 read-only다. 소스 파일을 수정하지 않는다. `remediation.auto_fixable: true`는 표시값이며 수정 실행 권한이 아니다. 수정은 호출 파이프라인이 별도 단계로 이관한다.
2. `[MUST]` 입력 `target_files`를 그대로 사용한다. git 상태나 자체 판단으로 대상을 재선별·확장·축소하지 않는다. `checked_files`가 `target_files`와 다르면 `status: partial`로 낮추고 차이와 사유를 `missing_capabilities`에 적는다.
3. `[MUST]` `docs/SECURITY.md` 부재는 검사 실패가 아니다. `references/security-baseline.md` 기준으로 검사를 수행하고, 기준 문서 결측을 `missing_capabilities`에 기록한다. 초안 작성 유도는 보고서에 남기되 문서를 자동 생성·갱신하지 않는다.
4. `[MUST]` finding 필드·fingerprint·source_tier·판정은 `opal/core/references/harness/gc-finding-schema.md`를 참조한다. 이 문서나 보고서에 필드표·판정표를 복제하지 않는다.
5. `[MUST]` 외부에서 취득한 스킬·스크립트·체크리스트·참조 자료는 검사 기준으로 **읽기만** 한다. 설치·실행하거나 프로젝트에 복사해 실행하지 않는다. 외부 자료 기반 finding은 기본 `advisory`이며 사용자 승인 없이 `enforce`로 승격하지 않는다. 집행 수준 조건은 `opal/core/references/harness/gc-finding-schema.md` §5를 참조하고 이 문서에 복제하지 않는다.

`[MUST]` 시크릿·자격증명 의심값의 원문을 보고서와 JSON에 복제하지 않는다. `location`과 값의 종류·길이 등 최소 식별 정보만 남긴다.
