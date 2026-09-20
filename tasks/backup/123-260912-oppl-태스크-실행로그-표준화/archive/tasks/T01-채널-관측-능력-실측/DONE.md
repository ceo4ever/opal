# DONE: T01 — 채널 관측 능력 실측

> Phase 0 인도물. **읽기·실험 전용**이었고 `opal/` 아래 도구 소스·변환기는 만들지 않았다.
> 근거 인용은 실행 관측 스코프·명령을 병기한다(`.opal/brain/pages/concept/execution-observation-scope-citation-requirement.md:30`, citation-rules §9 E1).

## 1. 결론 — 채널별 배정

| `channel_id` | 배정 등급 | 배정 근거 1줄 |
|---|---|---|
| `pm-agent-tool` | `observed_trajectory` | 하네스가 호출자와 무관하게 기록하는 `subagents/agent-<id>.meta.json`(시작) · 같은 폴더 `agent-<id>.jsonl`의 실행 중 증분 append 8회(중간, 종료보다 앞섬) · 호출자 transcript의 `type=attachment` `<task-notification>`(종료, `status=completed`)를 외부 프로브가 전부 기계 포착했다. |
| `oppl-headless-cli` | `observed_trajectory` | 프로브가 프로세스를 직접 감싸 PID·monotonic 기준점(시작) · `--stream` stdout JSONL 204줄이 result 이벤트보다 앞서 391초에 걸쳐 분산 수신(중간) · 프로세스 종료 코드 파일(종료)을 확보했다. **`--stream` 호출 모드 전제**다. |

두 축은 별도 프로브·별도 표본·별도 receipt로 판정했고 한쪽 결과를 다른 쪽에 전용하지 않았다(AC-3).

## 2. 판정 매트릭스 (관측 4항목 × 2축)

| 관측 항목 | `pm-agent-tool` | `oppl-headless-cli` (`--stream`) |
|---|---|---|
| (1) 시작 식별자 | 관측됨 — `agent_tool_handshake`<br>`evidence/pm-agent-tool/trial-01.dispatch-tooluse.json` | 관측됨 — `process_start`<br>`evidence/oppl-headless-cli/trial-01-stream.probe.json` |
| (2) 완료 알림보다 앞선 중간 사건 | 관측됨 — `subagent_transcript_append`<br>`evidence/pm-agent-tool/trial-01.probe.json` | 관측됨 — `stream_line`<br>`evidence/oppl-headless-cli/trial-01-stream.probe.json` |
| (3) 종료 봉투 | 관측됨 — `task_notification`<br>`evidence/pm-agent-tool/trial-01.terminal-envelope.json` | 관측됨 — `process_exit`<br>`evidence/oppl-headless-cli/trial-01-stream.exitcode` |
| (4) 단조 시계 구간 | 관측됨 — `adapter_monotonic`<br>`evidence/pm-agent-tool/trial-01.probe.json` | 관측됨 — `adapter_monotonic`<br>`evidence/oppl-headless-cli/trial-01-stream.probe.json` |

칸별 상세 근거·수치는 `evidence/observation-matrix.json`이 소유한다. 위 표는 그 파일의 요약이며 수치를 재서술하지 않는다.

## 3. 실행 관측 스코프와 명령

| 표본 | 명령(스코프) | 결과 |
|---|---|---|
| 축 A trial-01 | 플랫폼 Agent 도구 1회 실호출(`subagent_type=general-purpose`, `model=sonnet`, background) + 외부 프로브 `evidence/pm-agent-tool/adapter-probe.py`가 세션 산출물 디렉터리를 0.25초 주기 폴링 | 신규 파일 2건·증분 8건·종료 봉투 1건 포착, 관측 구간 118499.728ms |
| 축 B trial-01 | `opal-agent --provider claude --opal-bootstrap off --model sonnet --allowed-tools Read,Grep,Glob,Write,Edit,Bash --timeout 600 --cwd <project_root> --stream` (T1 디스패치) | stdout 205줄, exitcode **2**(하드에러), 관측 구간 393988.166ms |
| 축 B trial-02 | 같은 CLI를 `--json`으로 호출(G 게이트 디스패치, `--model opus --allowed-tools Read,Grep,Glob`) | stdout 120줄이 전량 종료 직전 3.3ms 안에 도착, exitcode 0 |
| 축 B trial-03 | 같은 CLI를 `--stream --resume <session>`으로 호출(T1 재작업) | exitcode 0, 동일 session_id로 warm resume 성립 |
| 축 B trial-04 | 같은 CLI를 `--json`으로 호출(G 재판정) | exitcode 0 |

## 4. 가장 중요한 부수 발견 — 호출 모드가 등급을 좌우한다

`축 B의 중간 사건 관측 가능성은 채널이 아니라 **호출 모드**에 달려 있다.`

- 측정: --stream(trial-01): 205줄, 첫 줄 offset 1918.191ms, 마지막 줄 393159.077ms, 분산 391240.9ms. --json(trial-02): 120줄, 첫 줄 offset 134508.849ms, 마지막 줄 134512.185ms, 분산 3.3ms(전체 구간 134516.779ms의 마지막 0.002%에 전량 도착).
- 귀결: `--json` 전제에서는 이 축이 observed_terminal 이상으로 올라갈 수 없다. profiles.json의 배정은 `--stream` 전제이며, 변환기가 `--json`으로 호출하면 배정이 성립하지 않는다.

따라서 `profiles.json`의 `oppl-headless-cli` 배정은 **`--stream` 전제 배정**이다. Phase 1A 변환기가 `--json`으로 호출하면 이 배정은 성립하지 않으며 재스파이크 대상이다(TRD D-8).

## 5. 확인 불가 (추정하지 않고 분리 기록)

- **축 A 실패/차단 경로의 종료 봉투 status enum** — 이번 실측은 정상 완료 표본만 확보했다. status=completed 외의 값(실패·중단·타임아웃)이 어떤 문자열로 오는지, pre_activity_failure 대체 경로가 성립하는지는 호출하지 않았다. (영향: CONTRACT §1.5 terminal reason/reason_code 매핑은 Phase 1A 실측이 필요하다.)
- **축 A 관측 원본의 안정성 계약** — `~/.claude_platform_mkt/projects/<slug>/subagents/*.jsonl`·`*.meta.json`과 `type=attachment` task-notification은 플랫폼 내부 산출물이며 공개 계약이 아니다. 관측 시점 버전은 transcript의 `version=2.1.269`다. (영향: 플랫폼 업데이트로 경로·필드가 바뀌면 축 A 배정이 무효화된다 — 재스파이크 트리거(TRD D-8).)
- **축 A의 타이트한 adapter_monotonic 구간** — 호출자 세션 flush 지연으로 관측 창이 실행 구간보다 길다(이번 표본 약 70초 과대). (영향: §1.5 duration_ms를 adapter_monotonic으로 보고할 수는 있으나 값의 의미가 '실행 소요'가 아니라 '관측 소요'다. Phase 1A에서 flush 비의존 종료 신호를 찾지 못하면 이 축의 duration은 상한값으로만 해석해야 한다.)
- **축 B 동시 실행·경합 경계** — 단일 프로세스 순차 호출만 실측했다. (영향: 동시 호출 시 순번·상관 키 충돌 여부는 Phase 1A 정량 게이트 대상.)

## 6. 검증 결과 (PLAN §4 VS-1~VS-5)

| id | 대상 | 결과 | 사유 |
|---|---|---|---|
| VS-1 | profiles.json 구조 + receipt 8필드·파생·해시 | **pass** | pm-agent-tool: profile=observed_trajectory 파생일치=True receipt_hash일치=True / oppl-headless-cli: profile=observed_trajectory 파생일치=True receipt_hash일치=True |
| VS-2a | evidence_paths 실재·비공백 | **pass** | missing=[] empty=[] total=18 |
| VS-3 | observed=true 8칸 전수 원본 확인 | **pass** | pm-agent-tool.start=ok; pm-agent-tool.intermediate=ok; pm-agent-tool.terminal=ok; pm-agent-tool.monotonic_span=ok; oppl-headless-cli.start=ok; oppl-headless-cli.intermediate=ok; oppl-headless-cli.terminal=ok; oppl-headless-cli.monotonic_span=ok |
| VS-4a | 축 B 재실행 재현성(trial-03 warm resume) | **pass** | exitcode=0, lines=38, duration_ms=126947.816 |
| VS-4b | 워크트리 무변경(태스크 폴더 외) | **pass** | T01 시작(19:26 KST) 이후 프로젝트 워크트리에서 태스크 폴더 밖 변경 0건. 최초 `git status --porcelain`의 3건(M docs/PROJECT.md · ?? docs/run-log/ · ?? tasks/123-…)은 T01 이전 설계 루프의 기존 상태이며 mtime으로 T01 무관을 확인했다. 별건 관측: `~/.opal/` 전체가 19:37:5x 일괄 mtime을 가져 세션 중 외부 재배포(opal-cli update 상당)가 일어났다. T01의 어떤 디스패치도 `~/.opal/`에 쓰기를 수행하지 않 |
| VS-5 | 등급 파생 결정론성(2회 적용 동일) | **pass** | 두 채널 모두 2회 적용 결과가 profiles.json과 일치 |

검증 스크립트는 이 태스크 폴더 밖에 아무것도 쓰지 않았다. 실행 결과 원본은 `.oppl-run/t4a.results.json`.

## 7. 계약 준수

- `profiles.json` 구조는 `docs/run-log/CONTRACT.md` §1.6을 그대로 따른다(`schema_version`·`produced_by`·`channels[].channel_id`/`completion_profile`/`adapter_id`/`adapter_sha256`/`receipt_sha256`/`evidence_paths`). `evidence_paths`는 전부 **태스크 폴더 기준 상대 경로**다(PLAN §6).
- `completion_profile`은 §1.5 enum 3종만 쓰고, self-test receipt의 `observed{}`에서 결정론적으로 파생했다(VS-5로 2회 적용 동일 확인).
- **잠정 변환기 조건**(PLAN §3-6, G 지시 5): (a) 이 `profiles.json`은 태스크 폴더 원본이며 배포 위치로 승격하지 않는다 (b) 승격 전 `state-tool init --run-log-mode active`를 호출하지 않는다 (c) Phase 1A 실변환기 확정 시 `adapter_id`·`adapter_sha256`·`receipt_sha256`을 재발급한다. `adapter_*`는 현재 Phase 0 실측 프로브의 값이며 실변환기의 값이 아니다.
- 검증 2원화 순서: `QA-SPEC.md`(G, 구현 전) 산출이 `profiles.json` 산출보다 앞선다. G는 1회차 `fail`(재작업 7건) → 재작업 → 2회차 `pass`였다.
- 비밀값: 증거 전체를 패턴 스캔(`sk-ant-*`·private key 블록·`xox*`·`ghp_*`·`AKIA*`·이메일)해 0건. 마스킹 대상 없음.

## 8. 이번 실행에서 지킨 금지선

- `~/.opal/` 직접 수정 없음. 세션 중 `~/.opal/` 전체가 19:37:5x 일괄 mtime을 갖는 외부 재배포가 관측되었으나 T01의 어떤 디스패치도 그곳에 쓰지 않았고, 배포본과 프로젝트 소스의 SHA-256 동일·허브 `git status -- opal/` 공백으로 드리프트 0을 확인했다.
- 3-SSOT(`backlog.json`·`state.json`·`test-scenario.json`) 손편집 없음. `CONTRACT.md` 수정 없음. 커밋하지 않았다.

## 9. 계약 이탈 1건 (보고)

T2 RED-first 단계를 **별도 tool-gated 단계로 실행하지 않았다**. 이 태스크의 산출물이 코드가 아니라 실측 증거·판정 파일이고, 검증 시나리오(VS-1~VS-5)는 PLAN 단계에서 설계되어 G 게이트가 구현 전에 강화(지시 2·3·4)한 뒤 산출물 확정 후 실행됐다. 사후에 `test-scenario.json`을 만들어 RED를 소급 선언하는 것은 self-confirming RED 금지(H-7)에 정면으로 어긋나므로 **하지 않았다**. PM 판단이 필요한 이탈로 보고한다.

## 10. 다음 게이트

PRD §게이트 요약 "Phase 0 → 1A"는 **사람 승인(필수)** 이다. 채널별 배정과 원본 증거를 사용자에게 보고하고 승인을 받기 전에는 어떤 구현 태스크에도 진입하지 않는다.
