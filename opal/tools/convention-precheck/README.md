# convention-precheck

> 컨벤션 검사 전에 기계적으로 판정되는 규칙 4종과 변경 구간을 결정론으로 산출하고, 모델 검사 결과와 결합하는 CLI
> 소스: `opal/tools/convention-precheck/` | 배포: `~/.opal/tools/convention-precheck/`
> 의존성: `~/.opal/.venv/bin/python3`(표준 라이브러리만) + git + node(@header 판정용 `../code-scan/code-scan.js`)

## 호출 형식

```bash
run.sh scan  --project-root <절대경로> --base-ref <ref> --output-dir <dir> --timestamp <ts> \
             [--target-files <csv>] [--context-lines 10] [--code-scan <code-scan.js 경로>]
run.sh merge --precheck <json> --review-input <json> --model-findings <json|none> --output <json>
```

표준 출력은 요약 JSON이다. 종료 코드는 정상 0, 사용·git 오류 1이며 finding 유무는 종료 코드에 영향이 없다.

## scan

- 기준 커밋 `base_sha = git merge-base <base-ref> HEAD`(HEAD는 `project-root`에 체크아웃된 HEAD). 변경 파일은 `git diff --name-only --diff-filter=ACMR base_sha HEAD`이고 `--target-files`가 있으면 그 교집합이다. 교집합에서 빠진 대상은 `checked_files`에만 넣고 검사 입력에서 건너뛴다. 파일 내용은 작업 트리에서 읽는다.
- 산출물 두 개를 `--output-dir`에 쓴다.
  - `gc-findings-convention-precheck-{ts}.json` — `gc-finding-schema.md`의 envelope 8필드와 finding 14필드만 쓴다(`report_path: null`).
  - `convention-review-input-{ts}.json` — `base_sha`, `head_sha`, `mechanical_rule_ids`, `files[{path, status: added|modified, whole_file, ranges}]`. 변경 구간은 `git diff -U0`의 신규 쪽 구간을 앞뒤 `--context-lines`줄 넓혀 겹침·인접을 병합한 것이고, 추가 파일은 `whole_file: true`와 `[[1, 전체 줄 수]]`다.

### 기계 규칙 4종 (모두 `source_tier: T0`)

| rule_id | severity / disposition | 판정 |
|---|---|---|
| `CONVENTIONS.md §구현 규칙 §@header 규칙` | high / blocking | 코드 확장자(`.md` 제외, 프로젝트 `exclude` 디렉터리 제외) 변경 파일 중 `code-scan target`이 `none`이 아니고, 추가 파일이거나, 기준 커밋 버전을 같은 상대경로의 임시 프로젝트에 두고 현재와 같은 `code-scan scan --json`을 적용했을 때 헤더가 인식되었는데 지금은 비면(회귀) 1건. 기준·현재 모두 인식되지 않는 기존 형식은 finding을 만들지 않는다. 추가 파일은 `module`·`layer`·`domain`·`description`·`exports` 누락마다 1건 |
| `CONVENTIONS.md §파일 구조 §YAML Frontmatter` | high / blocking | 변경된 `SKILL.md`는 `name`·`description`, `AGENT.md`는 `name`·`description`·`model`이 첫 frontmatter에 없으면 키마다 1건 |
| `opal-doc-standard.md §5` | medium / advisory | 변경된 `.md`에서 기준 커밋 대비 추가된 줄 중 `변경이력`·`Changelog`·`History`·`Revisions` 제목줄 |
| `CONVENTIONS.md §네이밍 규칙 §파일/폴더` | medium / advisory | 추가 파일 중 `opal/` 아래(새 디렉터리는 kebab-case, `.py`는 snake_case, 그 외는 `[A-Za-z0-9._-]`·공백 금지)와 `tasks/` 바로 아래 새 폴더(`NNN-YYMMDD-약어-이름`) |

네이밍은 기준 커밋에 이미 있던 디렉터리 구성요소와 점(`.`)으로 시작하는 디렉터리, `__pycache__`·`fixtures` 아래 경로는 검사하지 않는다. `fingerprint`는 `gc-finding-schema.md` §4(위치 앞뒤 3줄 정규화, 내용이 없으면 빈 문자열)로 만들며 같은 입력이면 재실행해도 같다.

### 실패 처리

`node`나 `code-scan.js`가 없거나 호출이 실패하면 `status: partial`과 `missing_capabilities`에 사유를 남기고 @header 규칙만 건너뛴다(조용한 통과 없음). 다른 규칙은 그대로 수행한다.

## merge

모델 finding(envelope 또는 배열, `none` 가능) 중 `location`이 `files[].ranges` 밖이거나 `rule_id`가 `mechanical_rule_ids`인 것을 제거하고, 개수를 `evidence[]`에 `model findings dropped: out_of_range=N, mechanical_rule=M`으로 남긴다. 남은 finding의 `id`는 사전 검사 finding 뒤에서 `GC-NNN`으로 이어 다시 매긴다. `status`·`missing_capabilities`·`checked_files`·`references`는 두 입력의 합집합이며 하나라도 `partial`이면 `partial`이다.

## 시험

```bash
~/.opal/.venv/bin/python3 -m pytest opal/tools/convention-precheck/tests/test_convention_precheck.py
```

시험은 임시 git 저장소를 만들어 사례를 재현한다. 162 회귀는 커밋 `48f25a5a`를 임시 워크트리로 체크아웃해 확인한다.
