# event-loader

`events.json`을 유일한 필수 문서 목록으로 사용해 이벤트 시점의 문서 전문과 sha256 receipt를 반환하는 플랫폼 독립 CLI다. 소스 checkout에서는 source 경로를, 설치본에서는 deployed 경로를 선택하며 프로젝트 문서는 project root 토큰으로 해석한다.

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
```

모든 성공/실패는 stdout의 단일 JSON object로 반환한다. 실패는 non-zero이며 `error`에 기계 판독 가능한 코드를 둔다. `load`의 `documents[].content`가 전문이고, receipt는 manifest 및 문서의 현재 `sha256`/`bytes`를 고정한다. `verify`는 receipt 누락, event 불일치, manifest 변경, 문서 누락·경로 변경·hash 변경을 거부한다.

`session.disabled`는 `bootstrap: off`의 순수 모드다. 이 이벤트는 required/optional 문서를 모두 0건으로 선언하며 `load`와 `measure`가 `document_count: 0`, `payload_bytes: 0`을 반환한다. `[WORKER]`는 별도 `session.worker` 이벤트다.

## Root tokens

manifest 문서는 다음 root token만 사용한다.

- `{source_root}`: framework source checkout
- `{deployed_root}`: 설치된 OPAL root(기본 `~/.opal`)
- `{project_root}`: 현재 프로젝트 hub root

CLI의 `--source-root`, `--deployed-root`, `--project-root`, `--manifest`로 테스트/설치 경계를 명시할 수 있다. 토큰 경로가 root 밖으로 탈출하면 거부한다. OS나 AI 플랫폼 이름에 따른 분기는 없다.
