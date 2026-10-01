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

계약 인자 4개가 모두 없고 `events.json`의 `contract.legacy_accepted`가 `true`일 때만 구형 호출로 처리한다. 구형 load는 선별 없이 전체 문서와 `schema_version: 1` receipt를 돌려주고 `contract: "legacy"`·경고 `legacy_dispatch_contract`를 붙이며, 구형 load·verify마다 `{ts, op, event, project_root}` 한 줄을 원장(JSONL, 기본 `{deployed_root}/state/event-loader/legacy-dispatch.jsonl`, 환경변수 `OPAL_EVENT_LOADER_LEDGER`로 변경, `OPAL_EVENT_LOADER_NOW`로 시각 고정)에 남긴다. 전환 기간 한정 호환이며 새 호출은 항상 v2를 쓴다.

종료는 다음을 모두 만족할 때 `events.json`의 `contract.legacy_accepted`를 `false`로 바꾸는 것으로 수행한다. 전환 기준 시점은 이 변경이 `~/.opal`에 설치된 시각이다.

1. `legacy-report --since <기준 시점>`의 건수가 0이고 기준 시점부터 판정 시점까지 연속 168시간 이상 경과했다.
2. `static-check`가 구형 호출 0건(`dispatch_contract_args_missing` 없음)을 보고한다.
3. 직접 호출과 하위 디스패치 검증 시나리오가 통과했다.

### 설치본 loader 결함 복구

배포 전 `~/.opal/tools/event-loader`를 `.bak`으로 보존한다. 배포 직후 설치본에서 `session.assistant`·`pm.activate`·`stage.plan` load와 `static-check`를 실행해 하나라도 실패하면 변경 커밋을 `git revert`하고 `scripts/install-mac.sh`로 재설치한 뒤 같은 검사가 성공하는지 확인한다. 재설치도 실패하면 `.bak`으로 복원한다. 호환 종료 전에는 `legacy_accepted`가 `true`이므로 인자 없는 구형 호출이 계속 동작한다.

## Root tokens

manifest 문서는 다음 root token만 사용한다.

- `{source_root}`: framework source checkout
- `{deployed_root}`: 설치된 OPAL root(기본 `~/.opal`)
- `{project_root}`: 현재 태스크의 task root

CLI의 `--source-root`, `--deployed-root`, `--project-root`, `--manifest`로 테스트/설치 경계를 명시할 수 있다. 토큰 경로가 root 밖으로 탈출하면 거부한다. OS나 AI 플랫폼 이름에 따른 분기는 없다.

`--project-root`가 없으면 cwd에서 `.git`과 `.opal/AGENT.md`를 **함께** 가진 가장 가까운 조상을 task root로 쓴다. 경로에 `.opal-worktrees` 세그먼트가 있다는 이유로 허브에 수렴하지 않으므로, 자기완결 워크트리(자신의 `.opal/AGENT.md` 보유)는 그 워크트리 자신이 `{project_root}`다. 탐색 상한은 가장 가까운 Git 경계이며 — 임의 조상의 `~/.opal` 설치본을 프로젝트로 오인하지 않기 위함이다 — 비-Git 프로젝트는 `--project-root`를 명시해야 한다. 루트 소유권 계약의 원문은 `opal/core/references/harness/worktree.md` §task root와 allocator root 계약이 소유한다.

알려진 한계(후속 개선 후보): `--role-doc` 경로는 제한하지 않고 해시만 결속한다. 호출 원장 경로는 환경변수로 바뀔 수 있다.
