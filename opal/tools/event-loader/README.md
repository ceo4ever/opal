# event-loader

`events.json`을 유일한 필수 문서 목록으로 사용해 이벤트 시점의 문서 전문과 sha256 receipt를 반환하고, `session.project`의 사용자용 부트 브리핑을 완성하는 플랫폼 독립 CLI다. 소스 checkout에서는 source 경로를, 설치본에서는 deployed 경로를 선택하며 프로젝트 문서는 project root 토큰으로 해석한다.

## 공개 CLI

```bash
# 필수/존재하는 선택 문서의 전문과 receipt
opal/tools/event-loader/run.sh load --event session.assistant

# load 결과의 receipt object를 파일로 저장한 뒤 최신성 검증
opal/tools/event-loader/run.sh verify --receipt /path/to/receipt.json --event session.assistant

# manifest만 검사하거나 실제 소비자 계약까지 검사
opal/tools/event-loader/run.sh static-check --manifest-only
opal/tools/event-loader/run.sh static-check
opal/tools/event-loader/run.sh static-check --event worker.dispatch --path opal/agents

# 선언된 payload bytes와 반복 읽기 시간
opal/tools/event-loader/run.sh measure --event session.assistant --iterations 3

# worker.dispatch 계약 v2: 대상·역할·식별자를 넘기면 대상 항목만 선별된 본문과 v2 receipt를 반환
opal/tools/event-loader/run.sh load --event worker.dispatch --contract-version 2 --agent <대상> --role <역할> --dispatch-id <식별자> [--role-doc <역할 문서>] > /path/to/receipt.json
opal/tools/event-loader/run.sh verify --event worker.dispatch --receipt /path/to/receipt.json --contract-version 2 --agent <대상> --role <역할> --dispatch-id <식별자> [--role-doc <역할 문서>]

# 대상 선택용 가벼운 목록(매핑 테이블·폴백 규칙·탐색 경로·에이전트 이름)
opal/tools/event-loader/run.sh agent-index

# 게이트용 verify: 실행 경계 매니페스트가 정본일 때만 통과
opal/tools/event-loader/run.sh verify --event worker.dispatch --receipt /path/to/receipt.json --contract-version 2 --agent <대상> --role <역할> --dispatch-id <식별자> --require-default-manifest

# 실험(기본 꺼짐): 선언된 문서를 절 단위로 선별 전달하고 미전달 절은 나중에 가져온다
opal/tools/event-loader/run.sh load --event stage.design --section-mode lazy --section-context track=dev > /path/to/load.json
opal/tools/event-loader/run.sh section --receipt /path/to/load.json --id <절 id> > /path/to/section.json
opal/tools/event-loader/run.sh verify --event stage.design --receipt /path/to/load.json --section-mode lazy
opal/tools/event-loader/run.sh verify --receipt /path/to/section.json --parent-receipt /path/to/load.json --section-mode lazy

# 구형 호출 원장 집계, load 응답 파일들의 본문·응답 바이트 합계
opal/tools/event-loader/run.sh legacy-report --since <ISO8601> [--until <ISO8601>]
opal/tools/event-loader/run.sh load-report --receipt /path/a.json /path/b.json

# 상태·메모리 SSOT를 조회해 첫 응답용 Markdown을 완성
opal/tools/event-loader/run.sh project-brief --project-root /path/to/project

# 같은 결과를 JSON envelope로 확인
opal/tools/event-loader/run.sh project-brief --project-root /path/to/project --json
```

`project-brief` 성공은 첫 응답에 그대로 붙일 UTF-8 1,024바이트 이하 Markdown을 반환하며, `--json`이면 `markdown`과 `bytes`를 담은 단일 JSON object를 반환한다. 그 외 성공/실패는 stdout의 단일 JSON object다. 실패는 non-zero이며 `error`에 기계 판독 가능한 코드를 둔다. `load`의 `documents[].content`가 전문이고, receipt는 manifest 및 문서의 현재 `sha256`/`bytes`를 고정한다. `verify`는 receipt 누락, event 불일치, manifest 변경, 문서 누락·경로 변경·hash 변경을 거부한다.

`project-brief`는 `state-tool boot-summary`와 `memory-tool show --boot-brief`를 읽기 전용으로 호출한다. 성공한 상태 결과의 direct+registry 통합 진행 태스크를 최신순 최대 3건 렌더링하고, 표시 밖 후보는 `그 외 N건`, canonical 경로 이상은 `경로 이상 N건`으로 드러낸다. `review_rows`는 최대 2건을 유지하며, 개별 조회 실패는 해당 블록만 생략한다. 두 결과가 모두 비면 `[부트스트랩] ✅ session.project ⏳ PM`을 byte-identical하게 유지한다.

`session.disabled`는 `bootstrap: off`의 순수 모드다. 이 이벤트는 required/optional 문서를 모두 0건으로 선언하며 `load`와 `measure`가 `document_count: 0`, `payload_bytes: 0`을 반환한다. `[WORKER]`는 별도 `session.worker` 이벤트다.

## worker.dispatch 계약 v2

`load`/`verify`의 계약 인자는 `--contract-version`, `--agent`, `--role`, `--dispatch-id`(필수 4개)와 `--role-doc`(선택)이다. `--dispatch-id`는 호출마다 발급하는 불투명 문자열(`^[A-Za-z0-9][A-Za-z0-9._-]{7,63}$`)이다. 서브명령은 `agent-index`(대상 선택용 목록), `legacy-report`(`--since`/`--until` 구간의 구형 호출 건수·첫/마지막 시각·op별 건수), `load-report`(`--receipt` 응답 파일들의 본문·응답 바이트 합계, `load_id` 중복 제거)를 추가로 제공한다. 정적 검사 `static-check`는 `--event worker.dispatch`와 `load`/`verify`가 함께 있는 줄에 계약 인자 4개가 없으면 `dispatch_contract_args_missing`으로 보고한다.

- 응답: 모든 `load` 응답에 `response_version: 2`, `load_id`, `response_bytes`가 있다. v2 호출은 `contract`, `source_payload_bytes`, `selection`(선별 요약)을 더하고, 대상 에이전트 항목만 선별된 본문을 `documents[].content`로 돌려준다.
- receipt(`schema_version: 2`): 기존 필드에 `contract_version`, `load_id`, `dispatch_id`, `agent`, `role`, `role_doc`, `selection`, `body_sha256`, `source_payload_bytes`, `response_bytes`가 더해진다. 같은 대상이라도 역할이나 식별자가 다르면 재사용할 수 없다.
- 오류 코드: `contract_args_missing`(인자 일부 누락 또는 인자 없이 v2 receipt), `contract_arg_invalid`(형식 위반·빈 값·끝 개행·`--role-doc` 읽기 실패), `contract_not_declared`(계약을 선언하지 않은 이벤트에 계약 인자를 넘김; load·verify·measure 공통), `unsupported_contract_version`(`contract.supported` 밖), `contract_mismatch`(인자와 receipt 계약 버전 불일치), `dispatch_target_mismatch`(대상), `dispatch_role_mismatch`(역할), `dispatch_id_mismatch`(식별자), `body_hash_mismatch`(응답 본문이 receipt 해시와 다름), `agent_changed`(대상 에이전트 문서·출처 변경), `response_body_missing`(verify 입력에 본문 없음), `agent_not_found`, `stale_receipt`(manifest hash·문서 집합·경로·payload 변경, 그리고 receipt 매니페스트 경로가 실행 경계 매니페스트와 다름), `legacy_dispatch_rejected`(`legacy_accepted: false`에서 구형 load), `legacy_receipt_rejected`(같은 조건의 구형 receipt verify). 경고 `ledger_write_failed`는 원장 쓰기 실패이며 호출을 막지 않는다.

### 구형 호환과 종료

계약 인자 4개가 모두 없고 `events.json`의 `contract.legacy_accepted`가 `true`일 때만 구형 호출로 처리한다. 구형 load는 선별 없이 전체 문서와 `schema_version: 1` receipt를 돌려주고 `contract: "legacy"`·경고 `legacy_dispatch_contract`를 붙이며, 구형 load·verify마다 `{ts, op, event, project_root}` 한 줄을 원장(JSONL, 기본 `{deployed_root}/state/event-loader/legacy-dispatch.jsonl`, 환경변수 `OPAL_EVENT_LOADER_LEDGER`로 변경, `OPAL_EVENT_LOADER_NOW`로 시각 고정 — 둘 다 테스트 모드 전용, 아래 "보안 동작" 참고)에 남긴다. 전환 기간 한정 호환이며 새 호출은 항상 v2를 쓴다.

종료는 다음을 모두 만족할 때 `events.json`의 `contract.legacy_accepted`를 `false`로 바꾸는 것으로 수행한다. 전환 기준 시점은 이 변경이 `~/.opal`에 설치된 시각이다.

1. `legacy-report --since <기준 시점>`의 건수가 0이고 `reliable: true`이며, 기준 시점부터 판정 시점까지 연속 168시간 이상 경과했다.
2. `static-check`가 구형 호출 0건(`dispatch_contract_args_missing` 없음)을 보고한다.
3. 직접 호출과 하위 디스패치 검증 시나리오가 통과했다.

### 설치본 loader 결함 복구

배포 전 `~/.opal/tools/event-loader`를 `.bak`으로 보존한다. 배포 직후 설치본에서 `session.assistant`·`pm.activate`·`stage.plan` load와 `static-check`를 실행해 하나라도 실패하면 변경 커밋을 `git revert`하고 `scripts/install-mac.sh`로 재설치한 뒤 같은 검사가 성공하는지 확인한다. 재설치도 실패하면 `.bak`으로 복원한다. 호환 종료 전에는 `legacy_accepted`가 `true`이므로 인자 없는 구형 호출이 계속 동작한다.

## 보안 동작

- **원장 override는 테스트 전용**: `OPAL_EVENT_LOADER_LEDGER`·`OPAL_EVENT_LOADER_NOW`는 `OPAL_EVENT_LOADER_TEST_MODE=1`일 때만 적용한다. 테스트 모드 없이 둘 중 하나라도 설정돼 있으면 값을 무시하고(기본 원장에 실제 시각으로 기록) 응답 `warnings`에 `ledger_override_ignored`를 낸다. 테스트 모드에서 적용했으면 `ledger_override_active`를 낸다. 원장 경로는 override가 없으면 항상 설치 루트(설치본이면 그 설치 루트, 소스 실행이면 `~/.opal`)의 `state/event-loader/legacy-dispatch.jsonl`이며 `--deployed-root`·`OPAL_DEPLOYED_ROOT`로 옮겨지지 않는다.
- **무결성 기록**: 원장 쓰기 실패(`ledger_write_failed`), override 무시, override 적용이 일어날 때마다 `{ts(실제 UTC 시각), kind, op, event}` 한 줄을 원장 옆 `legacy-dispatch.integrity.jsonl`에 남긴다. 그곳에도 쓸 수 없으면 `tempfile.gettempdir()`의 `opal-event-loader-integrity-<uid>.jsonl`(0600), 그것도 실패하면 stderr에 한 줄을 쓴다.
- **`legacy-report`**: 결과에 `integrity`(`write_failures`·`override_ignored`·`override_active`)와 `reliable`을 더한다. `reliable`은 세 값이 모두 0이고 호출 시점에 override 환경변수가 적용·무시 상태가 아닐 때만 `true`다. 호출 시점에 override 환경변수가 있으면 `warnings`에 같은 코드를 낸다. `--since`·`--until`은 무결성 기록에도 적용한다.
- **`--role-doc` 제한**: 경로를 `resolve()`한 뒤 `project_root`·`source_root`·`deployed_root` 중 하나의 하위여야 하고, `stat` 결과가 일반 파일이며 크기가 1,048,576바이트 이하여야 읽는다(FIFO·장치 파일은 열지 않는다). 위반은 `contract_arg_invalid`(`argument: --role-doc`)에 `cause`를 더해 거부한다: `outside_allowed_roots`·`not_regular_file`·`too_large`·`unreadable`. `verify`도 같은 판정을 거친다.
- **기본 매니페스트 정규화**: 기본 매니페스트 경로는 `resolve()`한 실제 경로이며 receipt·응답의 `manifest_path`도 그 값이다. `verify`는 receipt 경로와 실행 경계 경로를 실제 경로로 비교하므로 심볼릭 링크 `events.json` 설치에서도 정당한 receipt가 통과한다. 다른 매니페스트를 가리키는 receipt는 `stale_receipt`다.
- **`verify --require-default-manifest`**: 정본 매니페스트는 설치본이면 loader 스크립트가 속한 설치 루트의 `references/events.json`, 소스 실행이면 `{source_root}/opal/core/references/events.json`이며 인자·환경변수의 영향을 받지 않는다. 플래그를 켠 호출에서 실행 경계 매니페스트가 정본과 다르면 `manifest_not_default`(`expected`·`actual` 포함)로 거부하고, 통과하면 결과에 `manifest_default: true`를 더한다. 플래그가 없는 호출의 결과는 바뀌지 않는다. `state-tool event-verify`는 같은 플래그를 받아 있을 때만 loader verify에 넘기며, `worker.dispatch` 게이트(PM 디스패치 절차·워커 진입 게이트·하위 디스패치)가 이 플래그를 쓴다. 문서 산문 확인만으로는 사본 매니페스트 통과를 막을 수 없어 도구가 판정하게 하기 위해서다. `static-check`는 게이트 verify 줄에 플래그가 없으면 `dispatch_gate_default_manifest_missing`, `--manifest`·`--deployed-root`·`--source-root`가 있으면 `dispatch_gate_manifest_override`로 보고한다.

## 절 단위 로딩 실험 모드

큰 문서를 "필수 절 + 나머지 목차"로 전달하고 필요한 절을 나중에 가져오는 실험이다. **기본 꺼짐이며, 플래그가 없으면 `load`·`verify`·`measure`·`load-report`의 응답과 receipt는 바뀌지 않는다.** 측정 결과와 권고는 태스크 177의 `MEASURE.md`에 있다.

- **켜기**: `load`·`measure`에 `--section-mode lazy`와 반복 가능한 `--section-context KEY=VALUE`를 준다. 이벤트 선언에 `sectioning`이 없으면 `section_mode_not_declared`, 계약 인자(`--contract-version`·`--agent`·`--role`·`--role-doc`·`--dispatch-id`)와 함께 쓰면 `section_mode_conflict`다. `--section-context`만 주면 `section_mode_args_missing`이다.
- **컨텍스트 키**: 선언 파일의 `contexts`에 정의된 키·값만 허용하며 아니면 `section_context_invalid`다. 현재 `contexts`가 있는 선언은 `citation-rules`(`track`: `dev`·`planning`)뿐이라, `pm.activate`처럼 대상 문서에 `contexts`가 없는 이벤트에는 `--section-context`를 줄 수 없다. 컨텍스트 키가 없으면(조건 불명) `conditional` 절은 전달한다.
- **선언**: `events.json` 이벤트의 `sectioning`은 `[{"document": <필수 문서 id>, "source": "{source_root}/opal/core/references/sections/<id>.json", "deployed": "{deployed_root}/references/sections/<id>.json"}]`이다. 대상은 `pm.activate`(`pm-process`)·`stage.task`·`stage.plan`·`stage.design`의 프레임워크 문서 4종(`citation-rules`·`design-gate`·`pm-review-gate`·`pm-process`)이며 `docs/PROJECT.md`·`.opal/AGENT.md` 같은 프로젝트 문서는 대상이 아니다.
- **선언 파일**: `{"document", "unit_level", "contexts": {키: [값…]}, "sections": [{"id", "title", "load": "always"|"conditional"|"on_demand", "when": {키: [값…]}, "depends": [id…]}]}`. 단위는 `unit_level` 헤딩과 그 하위 전체(코드 펜스 바깥 헤딩 기준)이고, 첫 단위 앞의 머리말은 항상 전달한다. `title`은 헤딩 원문 제목과 같아야 하고 절 id는 `^[a-z][a-z0-9-]{1,40}$`로 이벤트 안에서 유일하다. 문서의 모든 단위가 선언돼야 한다.
- **선별 규칙**: 전달 = `always` + `when`이 성립한 `conditional` + 그 단위들의 `depends` 전이 폐포. `when`은 모든 키가 컨텍스트 값 집합에 속하면 성립한다. 본문에 `[MUST`가 있는 단위는 선언이 `on_demand`여도 항상 전달하고(`forced_by_must`로 기록) `static-check`가 `section_must_not_ondemand`로 보고한다. 단위는 원문 순서로 전달한다.
- **전달 본문**: 머리말 + 목차 블록 + 전달 단위. 목차는 미전달 단위마다 `- <id> — <제목> (<바이트>B)` 한 줄과 가져오는 방법 안내 한 줄이며, 미전달 단위가 없으면 만들지 않는다. 선언 대상이 아닌 문서는 원문 그대로다.
- **receipt(`schema_version: 3`)**: 기존 필드에 `section_mode`(`mode`·`context`·문서별 `declaration_sha256`·`delivered`·`omitted`·`forced_by_must`·`unit_sha256`·`original_bytes`·`content_bytes`)와 `body_sha256`·`source_payload_bytes`·`response_bytes`를 더한다. 문서 항목의 `sha256`·`bytes`는 전달 내용의 값이고 `source_sha256`·`source_bytes`가 원본 값이며 `payload_bytes`는 전달 본문 합계다.
- **`section`**: `section --receipt <load 응답 파일> --id <절 id>…`(반복 또는 쉼표 구분)는 부모 load 응답을 먼저 verify하고(실패하면 그 오류), 요청 id와 그 의존 폐포 중 아직 전달되지 않은 단위만 `sections[{document,id,title,sha256,bytes,content,via}]`로 돌려준다. 이미 전달된 id는 `already_delivered`에 나열하고, 선언에 없는 id는 `section_not_found`다. 응답은 새 `load_id`·`parent_load_id`·`payload_bytes`·`response_bytes`를 담고, 별도 receipt(`kind: "section_fetch"`, `parent: {load_id, receipt_sha256}`)를 남기며 부모 receipt는 수정하지 않는다.
- **verify**: 켠 receipt는 `--section-mode lazy`가 필요하다(없으면 `section_mode_args_missing`, 켜지 않은 receipt에 플래그를 주면 `section_mode_mismatch`). 응답 본문 해시, 기록된 컨텍스트와 현재 선언·문서로 선별을 다시 수행한 전달 내용 해시(`document_hash_mismatch`·`section_declaration_changed`), 매니페스트·문서 최신성을 검사한다. 추가 절 응답은 `verify --receipt <추가 절 응답> --parent-receipt <load 응답> --section-mode lazy`로 검증하며 부모 검증, 부모 연결(`section_parent_mismatch`), 절·본문 해시(`section_hash_mismatch`) 순이다. `--parent-receipt`가 없으면 `section_parent_required`다.
- **측정**: 켠 `measure`는 `payload_bytes`·`source_payload_bytes`·`response_bytes`·`omitted_unit_count`를 함께 출력한다. `load-report`는 추가 절 응답도 `load_id` 기준으로 합산하고 `section_fetch_count`를 더한다.
- **정적 검사**: `static-check`(`--manifest-only` 제외)는 선언 파일을 읽어 `section_declaration_invalid`·`section_title_not_found`·`section_title_duplicate`·`section_undeclared`·`section_id_duplicate`·`section_depends_unknown`·`section_depends_cycle`·`section_unit_level_invalid`·`section_conditional_without_when`·`section_must_not_ondemand`를 보고하고, 매니페스트 검사는 `sectioning` 형식 위반을 `sectioning_invalid`로 보고한다.
- **기타 오류 코드**: `section_declaration_not_found`(선언 파일 없음). 선언이 문서와 맞지 않으면 load도 `section_declaration_invalid`로 거부한다.

한계: `[MUST` 표기가 없는 의무·금지·예외 문장은 도구가 잡지 못하며 선언 작성 시의 문서 검토에 의존한다. 선별 대상은 프레임워크 문서 4종뿐이다.

## Root tokens

manifest 문서는 다음 root token만 사용한다.

- `{source_root}`: framework source checkout
- `{deployed_root}`: 설치된 OPAL root(기본 `~/.opal`)
- `{project_root}`: 현재 태스크의 task root

CLI의 `--source-root`, `--deployed-root`, `--project-root`, `--manifest`로 테스트/설치 경계를 명시할 수 있다. 토큰 경로가 root 밖으로 탈출하면 거부한다. OS나 AI 플랫폼 이름에 따른 분기는 없다.

`--project-root`가 없으면 cwd에서 `.git`과 `.opal/AGENT.md`를 **함께** 가진 가장 가까운 조상을 task root로 쓴다. 경로에 `.opal-worktrees` 세그먼트가 있다는 이유로 허브에 수렴하지 않으므로, 자기완결 워크트리(자신의 `.opal/AGENT.md` 보유)는 그 워크트리 자신이 `{project_root}`다. 탐색 상한은 가장 가까운 Git 경계이며 — 임의 조상의 `~/.opal` 설치본을 프로젝트로 오인하지 않기 위함이다 — 비-Git 프로젝트는 `--project-root`를 명시해야 한다. 루트 소유권 계약의 원문은 `opal/core/references/harness/worktree.md` §task root와 allocator root 계약이 소유한다.

한계: 무결성 판정은 같은 사용자 권한을 전제로 한다(같은 사용자가 설치본 파일을 직접 바꾸는 경우는 막지 않는다). 검증 대상은 이벤트 문서이며 대상 문서의 내용과 프로젝트 문서는 판정하지 않는다.
