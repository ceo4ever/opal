# PLAN: T01 — 채널 관측 능력 실측 명세·설계

> op-dev-plan 성격 · 입력: `backlog.json` T01 항목(AC-1), `docs/run-log/CONTRACT.md` §1.5·§1.6, `TRD.md` §채널 등급 모델, `PRD.md` §Phase 0.
> 이 문서는 T1(명세·설계) 단계의 유일 산출물이다. 실측(증거 수집)과 `profiles.json` 확정은 이 PLAN이 설계만 하고, 실행은 후속 단계(T3 성격)에서 이 설계를 그대로 따른다.
> 읽기·실험 전용. `opal/` 도구 소스, `~/.opal/`, 3-SSOT(backlog.json·state.json·test-scenario.json), `CONTRACT.md`는 이 단계에서도 후속 실행 단계에서도 손대지 않는다.
> 재작업(G 게이트 1회차 fail, `QA-SPEC.md` 재작업 지시 7건) 반영판. 등급 값(`observed_trajectory`/`observed_terminal`/`cooperative`)은 이 PLAN에서 어느 축에도 배정하지 않는다.

## 1. 축별 실측 설계

두 축은 관측 가능한 것이 구조적으로 다르므로(TRD D-6, §채널 등급 모델) 별도 설계·별도 판정을 유지하고 한쪽 결과를 다른 쪽에 전용하지 않는다.

### 축 A — `pm-agent-tool` (PM이 플랫폼 Agent 도구로 서브에이전트를 부르는 축)

- **무엇을 호출하는가**: 현재 PM 세션에서 Agent 도구(내부 명 `Task`)로 서브에이전트를 최소 1회 실호출한다. 합성(fabricated) 호출이 아니라, 이 태스크 진행 중 실제로 발생하는 디스패치 1건 이상을 표본으로 쓴다.
- **어떤 원본을 수집하는가** (아래는 재작업 중 실측으로 확정된 사실이며, 등급 값은 아직 배정하지 않는다):
  - (1) 시작 식별자: 호출자 PM 세션 `.jsonl`의 `tool_use`(`name: Task`) 블록의 `id`(=`toolUseId`)와 그 줄의 `timestamp`. 서브에이전트 쪽에서는 **같은 폴더의 `agent-<agentId>.meta.json`**(하네스가 기록)이 시작 메타를 담는다 — 필드: `agentType`·`description`·`toolUseId`·`parentAgentId`·`spawnDepth`·`requestShape`·`model`. `toolUseId`가 호출자 쪽 시작 식별자와 서브에이전트 쪽 시작 메타를 잇는 상관 키다.
  - (2) 중간 사건: 서브에이전트 transcript는 호출자와 **분리된 파일**이다 — `<세션디렉터리>/subagents/agent-<agentId>.jsonl`. 이 파일 안의 서브에이전트 자신의 `tool_use`/`tool_result`(Read, Bash, Grep 등) 각 항목의 `timestamp`가 중간 사건 후보다.
  - (3) 종료 봉투: 호출자 PM 세션 transcript에 `type=attachment` 항목으로 하네스가 기록하는 `<task-notification>`(`task-id`·`tool-use-id`·`output-file`·`status`·`usage.duration_ms`)이 종료 봉투 후보다.
  - (4) 단조 시계 구간: 외부 프로브가 자기 `time.monotonic()`으로 시작~종료 구간을 재는 방식이 실측으로 확인됐다(작동 자체는 가능). **caveat**: 이 구간은 하네스가 실제 작업 종료 후 결과를 디스크에 flush하고 task-notification을 기록하기까지의 지연을 포함하므로, 진짜 작업 소요와의 오차가 있는 **느슨한(loose)** 상한 구간이다. 이 느슨함을 `note` 필드에 명시하지 않고 정밀 구간처럼 profiles.json에 반영하는 것을 금지한다.
- **어디서 수집하는가**: 호출자 세션은 `~/.claude/projects/<project-slug>/*.jsonl`(project-slug는 현재 작업 디렉터리 경로의 `/`를 `-`로 치환한 이름), 서브에이전트 세션은 같은 세션 디렉터리 하위 `subagents/agent-<agentId>.jsonl`·`agent-<agentId>.meta.json`. 전부 read-only로만 접근한다.
- **수집 방법**: 위 경로들을 `toolUseId`를 상관 키로 파싱해 시작·중간·종료 후보를 묶는 읽기 전용 probe 스크립트를 `evidence/pm-agent-tool/` 아래 신설한다(`opal/` 도구 소스가 아니라 이 태스크 폴더 안의 1회성 실측 스크립트). 원본 transcript를 그대로 복사하지 않고, 상관된 결과만 `evidence/pm-agent-tool/*.json`으로 저장한다(비밀값 노출을 줄이기 위해 필요한 필드만 추출).

### 축 B — `oppl-headless-cli` (Project Loop 내부 헤드리스 CLI 축, `opal-agent`)

- **무엇을 호출하는가**: `~/.opal/tools/opal-agent/` 헤드리스 CLI를 서브프로세스로 최소 1회 실행한다.
- **호출 모드가 관측 능력을 좌우한다(실측 확정 사실)**: `--stream` 모드는 실행 중 stdout이 증분 수신되어 중간 사건 관측이 가능하다. `--json` 모드는 stdout 전량이 종료 직전에 한꺼번에 도착해 **중간 사건을 관측할 수 없다**. 따라서 이 축의 등급 판정·self-test receipt·profiles.json 어디에도 "어떤 호출 모드를 전제로 한 결과인가"를 반드시 병기한다(§3-4). 모드 표기 없는 축 B 판정은 무효로 취급한다.
- **probe 실행 안전 제약(신규)**:
  - 작업 디렉터리는 `evidence/oppl-headless-cli/`(태스크 폴더 하위) 고정. probe 스크립트가 다른 디렉터리에서 opal-agent를 실행하지 않는다.
  - 실행에 쓰는 프롬프트는 읽기/에코 수준으로 고정한다(예: 파일 시스템 변경·git 조작·외부 호출을 지시하지 않는 최소 확인용 프롬프트 1개). 프롬프트 본문은 probe 스크립트에 상수로 고정하고 실행마다 바꾸지 않는다.
  - 실행 직후 `git status --porcelain`으로 워크트리에 **태스크 폴더 산출물(`evidence/`, `.oppl-run/`) 이외의 변경이 없음**을 확인한다. 변경이 있으면 그 실행을 증거로 채택하지 않고 사유를 기록한다.
- **어떤 원본을 수집하는가**:
  - (1) 시작 식별자: 서브프로세스 PID + 프로세스 시작 시점의 monotonic 기준점.
  - (2) 중간 사건: `--stream` 모드일 때만 관측 가능 — stdout JSONL 스트림의 각 줄(수신 시점 monotonic 오프셋 + 줄 SHA-256). `--json` 모드에서는 이 칸을 관측 불가로 기록한다(추정 금지).
  - (3) 종료 봉투: 프로세스 `exitcode`(`process_exit`)와 stderr 해시.
  - (4) 단조 시계 구간: `time.monotonic()` 시작~종료 차분.
- **어디서 수집하는가**: `evidence/oppl-headless-cli/{run_id}.events.jsonl`(stdout 원본), `{run_id}.probe.json`(구조화 메타 — `start`/`stream_lines`/`terminal`/`monotonic_span`/`call_mode`), `{run_id}.err.log`, `{run_id}.exitcode`.
- **기존 자산 재사용**: 이 태스크 폴더에는 이미 이전 시도에서 만들어진 프로토타입 probe(`evidence/oppl-headless-cli/adapter-probe.py`)와 그 1회 실행 산출(`.oppl-run/t1.*`)이 있다. 이들은 삭제하지 않고 그대로 두되, 정식 증거로 확정하려면 위 안전 제약을 만족하는 조건으로 **최소 1회 재실행**해 재현성을 확인한 뒤 `evidence/oppl-headless-cli/`의 정식 경로에 정리한다. 기존 산출을 검증 없이 최종 근거로 승격하지 않는다.

## 2. 판정 매트릭스 — 빈 틀 (관측 4항목 × 2축 = 8칸)

값은 실측이 채운다. 아래는 실측 결과를 채울 자리와 각 칸이 가져야 할 값의 형태만 정의한다.

| 관측 항목 | `pm-agent-tool` | `oppl-headless-cli` |
|---|---|---|
| (1) 시작 식별자 | (실측 후 채움) | (실측 후 채움) |
| (2) 완료 알림보다 앞선 중간 사건 | (실측 후 채움) | (실측 후 채움) |
| (3) 종료 봉투 | (실측 후 채움) | (실측 후 채움) |
| (4) 단조 시계 구간 | (실측 후 채움) | (실측 후 채움) |

각 칸의 값은 다음 하위 필드를 갖는다(실측 단계에서 채움. 지금 어떤 값도 미리 적지 않는다):

```json
{
  "observed": true,
  "evidence_path": "evidence/<axis>/<file>",
  "source_kind_candidate": "<§1.1.2 source.kind 후보 1개>",
  "call_mode": "<축 B에서만 필수 — stream|json>",
  "note": "관측 근거 또는 관측 불가 사유"
}
```

`observed: true`인 칸은 `note`에 관측 불가 사유를 적을 수 없다(§3-1). 축 B 칸에는 `call_mode`를 반드시 채운다 — 미기재 칸은 무효(§1 축 B, §3-4).

## 3. 등급 배정 규칙 — 실측 결과 적용 결정 절차

CONTRACT §1.5 enum 3종(`observed_trajectory` / `observed_terminal` / `cooperative`)을 실측 매트릭스에 결정론적으로 적용하는 절차다. 등급 **메커니즘**은 CONTRACT가 이미 소유하므로 여기서 재정의하지 않고, 매트릭스 → self-test receipt → `profiles.json` 순서의 파생·산출 절차만 정한다.

1. **관측 판정 근거(강화)**. 축마다 매트릭스 4칸에서 boolean 3종을 도출하되, 각 boolean은 아래 조건을 **모두** 만족해야 참이다(파일 존재만으로 참이 되지 않는다):
   - `observed.X = (그 칸의 observed 필드가 true) ∧ (evidence_path가 가리키는 파일이 그 관측 항목을 실제로 담고 있음 — 예: 시작 식별자 칸이면 파일 안에 실제 시작 시각·식별자 값이 존재) ∧ (그 칸의 note가 "관측 불가" 계열 사유가 아님)`
   - `observed.intermediate`는 위 조건에 더해 §1.3 "완료 알림 분해 금지 불변식" 4개 조건(출처 id 상이·출처 해시 상이·중간 사건 관측시각·사건시각이 종료보다 앞섬·완료 메시지 분할 아님)까지 모두 충족해야 참이다.
   - 관측 불가로 판정된 칸(예: 축 A의 단조 구간, `--json` 모드의 축 B 중간 사건)은 `observed=false`로 두고 `note`에 사유를 남긴다. 이런 칸의 evidence_path가 존재한다는 사실만으로 `observed`를 true로 바꾸지 않는다.
2. `observed.start`/`observed.intermediate`/`observed.terminal`/`observed.monotonic_span`을 §1.5 self-test receipt 구조의 `observed{}`에 그대로 대입한다.
3. **self-test receipt 파일을 축마다 1건 산출한다**(§5 산출물). CONTRACT §1.5의 8필드를 그대로 채운다: `receipt_version="1.0"`, `channel_id`(`pm-agent-tool`|`oppl-headless-cli`), `adapter_id`, `adapter_sha256`, `observed{start,intermediate,terminal,monotonic_span}`(2에서 대입한 값), `claimed_profile`(아래 4에서 파생), `evidence`(그 축의 근거 파일 상대 경로 배열, 1건 이상), `produced_at`(UTC RFC 3339 밀리초).
4. `claimed_profile`을 `observed{}`에서 결정론적으로 파생한다(CONTRACT §1.5 receipt 절 그대로):
   - `start ∧ intermediate ∧ terminal` 모두 참 → `observed_trajectory`
   - `start ∧ terminal`만 참(`intermediate` 거짓) → `observed_terminal`
   - 그 외 → `cooperative`
   - 파생과 불일치하는 receipt는 거부한다(재작성). 축 B는 이 파생을 적용하기 전에 **어떤 `call_mode`를 전제로 했는지**를 receipt 근처에 별도로 밝힌다(receipt 8필드 자체에는 `call_mode` 필드가 없으므로, `evidence`의 probe 메타 파일이 `call_mode`를 담는 것으로 해석 근거를 남긴다).
   - `monotonic_span`은 `claimed_profile` enum 선택 자체를 낮추지 않는다(파생 규칙은 3항목만 기준). 다만 `monotonic_span`이 거짓이거나 §1 축 A의 caveat처럼 느슨한 경우, 그 축은 §1.5 "두 active 등급의 공통 조건"(`duration_source=adapter_monotonic` 필수)을 충족하지 못하거나 느슨한 근거로만 충족하므로 **해당 등급의 `mode=active` 채택 적격성에 의문이 남는다**는 사실을 receipt의 `evidence` 근거 파일(§1의 probe 메타)에 남긴다. enum 값 자체를 조작하지 않는다.
5. `profiles.json`의 각 `channels[]` 항목을 채운다: `channel_id`, `completion_profile`(4에서 파생한 값), `adapter_id`, `adapter_sha256`(§3-6의 잠정 채택 조건에 따름), **`receipt_sha256` = 그 축의 self-test receipt 파일(3에서 산출) 바이트의 SHA-256 hex**, `evidence_paths`(§2의 매트릭스 근거 파일 + receipt 파일 상대경로 전부, §6 기준점 적용).
6. **잠정 변환기 채택 조건(명문화)**. 이 단계는 실변환기를 만들지 않으므로(PRD §Phase 0 "범위 밖: 도구·변환기 구현") `adapter_id`/`adapter_sha256`은 이 Phase 0 실측 probe 스크립트 파일을 잠정 변환기로 채택해 그 파일의 SHA-256으로 채운다. 이 채택은 다음 세 조건 아래서만 유효하다:
   - (a) 이 `profiles.json`은 태스크 폴더 원본이며, 사람 승인 전까지 배포 위치(프로젝트 소스 `opal/` 하위 또는 `~/.opal/`)로 승격하지 않는다.
   - (b) 승격 전에는 `state-tool init --run-log-mode active`를 호출하지 않는다 — 호출하면 `profile_receipt_mismatch`(CONTRACT §2.2)가 확정적으로 발생한다.
   - (c) Phase 1A에서 실제 채널 변환기가 확정되면, 같은 `channel_id` 항목의 `adapter_id`/`adapter_sha256`/`receipt_sha256`을 그 실변환기 기준으로 재발급한다(TRD D-8 — 배정값 변경은 계약 재확정이 아니라 재스파이크).

## 4. 검증 시나리오

| id | 대상 | 기대 | required_fidelity |
|---|---|---|---|
| VS-1 | `profiles.json` 구조 + self-test receipt | §1.6 스키마 필수 필드 전부 존재(`schema_version="1.0"`, `produced_by`, `channels[].channel_id/completion_profile/adapter_id/adapter_sha256/receipt_sha256/evidence_paths`), `channel_id` 2건 유일 등재, `completion_profile`이 enum 3종 중 하나. **추가**: 각 축의 self-test receipt 파일이 CONTRACT §1.5 8필드를 모두 갖고, receipt의 `claimed_profile`이 그 receipt의 `observed{}`로부터 §3-4 파생 규칙을 적용한 결과와 일치하며, `profiles.json.receipt_sha256`이 그 receipt 파일 실제 바이트의 SHA-256과 일치함. non-null 존재 확인만으로 이 항목을 통과 처리하지 않는다 | real-usage |
| VS-2 | 매트릭스 각 칸이 주장하는 관측 항목의 실재 | 각 칸의 `evidence_path` 파일이 태스크 폴더(§6) 기준으로 존재·비공백일 뿐 아니라, **그 칸이 주장하는 관측 항목(시작 식별자/중간 사건/종료 봉투/단조 구간)이 파일 내용 안에서 실제로 확인됨**(예: 시작 식별자 칸이면 파일에 실제 타임스탬프·id 값이 있어야 하고, 단순 존재나 빈 로그 파일은 통과하지 않음) | real-usage |
| VS-3 | `observed=true`로 선언된 **모든 칸**(하나만이 아니라 전부) | 각 칸의 `evidence_path`가 그 칸을 개별적으로 뒷받침함 — 축·항목 조합 8칸 중 `observed=true`인 칸 전수를 칸 단위로 검사하고, 하나라도 근거가 부실하면 그 칸을 `observed=false`로 되돌린다 | real-usage |
| VS-4 | 축 B 실호출 재현성 + 안전 제약 준수 | `adapter-probe.py`를 §1 축 B의 안전 제약(고정 작업 디렉터리·고정 읽기/에코 프롬프트)대로 재실행해 `exitcode` 기록, `monotonic_span.duration_ms > 0`, `stream_lines`이 `call_mode=stream`일 때만 채워짐을 확인한다. **추가**: 실행 직후 `git status --porcelain`이 `evidence/`·`.oppl-run/` 이외의 변경을 보고하지 않음(워크트리 무변경) | real-usage |
| VS-5 | 등급 파생 결정론성 | §3에서 도출한 동일 `observed{}` 입력을 파생 규칙에 두 번 적용해도 같은 `claimed_profile`이 나오고, receipt와 `profiles.json`의 `completion_profile`이 서로 일치함 | real-usage |

## 5. 산출물 목록과 범위 밖

**이 PLAN(T1) 산출물**: `PLAN.md` 1건뿐.

**후속 실행 단계(설계를 그대로 따름) 산출물** — 참고용으로만 여기 나열하며 이번 단계에서 만들지 않는다:
- `evidence/pm-agent-tool/*`(probe 스크립트 + 상관 결과 JSON)
- `evidence/pm-agent-tool/self-test-receipt.json`(CONTRACT §1.5 8필드)
- `evidence/oppl-headless-cli/*`(기존 `adapter-probe.py` 재실행분 포함 정식 증거, `call_mode` 명시)
- `evidence/oppl-headless-cli/self-test-receipt.json`(CONTRACT §1.5 8필드)
- `profiles.json`(태스크 폴더 원본 — `receipt_sha256`은 대응 축 self-test receipt 파일의 SHA-256. 사람 승인 전 프로젝트 소스 승격은 하지 않음, §3-6)

**범위 밖**:
- `opal/` 아래 실제 채널 변환기(adapter) 구현
- `run-log-tool`/`state-tool` 코드 변경
- 3-SSOT(`backlog.json`·`state.json`·`test-scenario.json`) 손편집
- `CONTRACT.md`·`QA-SPEC.md` 수정
- Phase 1A 이후 작업(그림자 운영, 강제 게이트 집행 등)
- `profiles.json`의 프로젝트 소스 승격·`~/.opal/` 배포·`state-tool init --run-log-mode active` 호출(Phase 0 게이트 — 사람 승인 이후의 일, §3-6)

## 6. `evidence_paths` 상대 경로 기준

모든 `evidence_paths`(및 self-test receipt의 `evidence`)는 **태스크 폴더**(`tasks/123-260912-oppl-태스크-실행로그-표준화/tasks/T01-채널-관측-능력-실측/`)를 기준점으로 하는 상대 경로다. VS-2·VS-3은 각 경로를 `<task_folder>/<evidence_path>`로 해석해 파일 존재와 내용을 확인한다. 프로젝트 루트 기준 경로는 쓰지 않는다.
