# PLAN: 루프 액션 에이전트 투명 모니터링 — opal-agent stream-json 개조 + journal 규약 + oppl-monitor 도구

> 작성일: 2026-07-17 | 입력: TASK.md, ANALYSIS.md
> 모드: Multi-Feature | 실행 모드: 복잡
> 영역 축: 프레임워크 문서·도구 태스크 — **도구 / 에이전트 / 오케스트레이터 / 스킬 / 문서 / 환경 / 배치** 사용 (plan-guide §2.N.1 프레임워크 축)

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

루프 액션 에이전트의 내부 opal-agent 채널 실행을 **실행 중에도 관측 가능**하게 만든다: ① opal-agent에 stream-json 실행 경로(Popen 증분 소비 → `events.jsonl`)를 opt-in으로 신설하고, ② 결과 파일 규약을 v2로 개정(events.jsonl 편입·prompt 규약화)하며 journal 규약을 신설하고, ③ 신규 도구 `oppl-monitor`로 단계×축 현황판을 한 명령으로 렌더한다. 기존 `--json` 일괄 경로·5필드 계약·완료 마커(=exitcode)는 불변 유지한다.

### 1.2 참조 [MUST] 제약 (설계 집행 기준)

> citation-rules.md §4 PLAN 단계 [MUST] 의무 — 재해석 여지 있는 강제 규칙을 원문 인용으로 고정한다. (065/066 계승 계약은 `[066계승]`/`[065계승]` 접두로 구분.)

- [MUST] `.opal/AGENT.md` §금지사항: "`~/.opal/` 직접 편집 금지 — 항상 프로젝트 소스를 수정한 후 install로 배포한다." (→ D-11)
- [MUST] `docs/CONVENTIONS.md` §구현 규칙 배포 경계: "`~/.opal/` 배포 파일을 직접 편집하지 않는다. 변경은 항상 프로젝트 소스(`opal/`, `skills/`, `agents/`, `community-skills/`, `scripts/`)에서 수행한다." (→ D-9)
- [MUST] `docs/CONVENTIONS.md` §변경이력 작성 의무: "스킬·에이전트·참조 문서를 변경하면 '## 변경이력' 표에 행을 추가한다. 일시는 `YYYY-MM-DD HH:mm` (KST), 버전은 semver, 변경내용은 태스크 번호를 괄호로 포함." (→ D-9)
- [MUST] `docs/CONVENTIONS.md` §언어 규칙: "파일/폴더 이름 English, kebab-case (Python 파일은 snake_case)." → `oppl-monitor/`(kebab) + `oppl_monitor.py`(snake). (→ D-9)
- [MUST] `docs/CONVENTIONS.md` §@header 규칙: "코드 파일을 생성·수정할 때 파일 상단에 @header 블록을 작성한다." → `oppl_monitor.py`·`opal_agent.py`. (→ D-9)
- [066계승][MUST] `opal/agents/opal-loop-action-agent/AGENT.md` §결과 파일 규약: "**완료 마커** = `.exitcode` 파일의 **존재** … `.result.json`의 존재/비존재로 완료를 판정하지 않는다." → v2에서도 불변. (→ D-3)
- [066계승][MUST] `opal/agents/opal-loop-action-agent/AGENT.md` §allowedTools 표준: "`--dangerously-skip-permissions`는 어떤 축의 명령에서도 사용하지 않는다." (→ D-3)
- [MUST] `TASK.md` §제약: "opal-agent는 Python 3.10+ 표준 라이브러리만 — oppl-monitor도 동일 원칙." (→ D-0)
- [MUST] `TASK.md` §제약: "기존 `--json` 일괄 경로·5필드 반환 계약 하위호환 — stream은 opt-in." (→ D-0)
- [066계승][MUST] `ANALYSIS.md` §2.6: "범용 최소 보장 집합은 `system/init`(1회) → 0회 이상의 `assistant`/`user`(도구 호출 왕복) → `result`(정확히 1회, 마지막 줄)로 좁혀 방어적으로 설계 … 미보장 필드 의존 금지(R-H)." (→ D-1)
- [MUST] `opal/skills/opal-pilot-project-loop/references/loop-control.md` §2: 재시도 수치 비복제 — journal 규약·재시도 기록 서술 시 수치를 복제하지 않고 harness §1 포인터를 참조한다. (→ D-10)

### 1.3 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | opal-agent stream-json 실행 경로 (Popen 증분 → stdout passthrough, 5필드 last-line 추출, `--verbose` 자동, `--stream` CLI) | R-1 | P0 | 없음 |
| F-002 | 결과 파일 규약 v2 + journal 규약 (AGENT.md — events.jsonl 편입·prompt 규약화·완료마커 불변·§운행 일지 신설) | R-2, R-3 | P0 | F-001 |
| F-003 | oppl-monitor 신규 도구 (단계×축 현황판 렌더·`--json`·`--watch`·에러계약) | R-4 | P0 | F-002 |
| F-004 | 문서 정합·등록 (tools.md·harness §9·oppl SKILL·README·install·변경이력) | R-5 | P1 | F-001, F-003 |
| F-005 | 동작 실증 (재실증 fixture·events.jsonl·journal 실생성·monitor 렌더·blocked 표시) | R-6 | P0 | F-001~F-004 |

### 1.4 기능 의존 그래프 (ASCII)

```
F-001 ─┬─ F-002 ─── F-003 ─┬─ F-005
       │                    │
       └────────── F-004 ───┘
```

---

## 리스크 가설 표

> PLAN 단계 작성. TEST-SCENARIO.md §1 입력. 065/066 확정 계약 참조는 `[066계승]`/`[065계승]` 접두로 구분.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | F-001 stream 5필드 추출 | [066계승] stream 마지막 줄이 `type:result`가 아니거나 5필드 누락 시 반환 계약(result/session_id/is_error/total_cost_usd/duration_ms) 붕괴 | P0 | L1(파싱 단위)+L2(E2E 실측) | S-1, S-3 |
| H-2 | F-001 `--verbose` 자동 부착 | stream-json 시 `--verbose` 미부착 → CLI exit 1(사용법 에러)로 항상 실패 (ANALYSIS §2.5) | P0 | L1(build_invocation cmd 단위) | S-2 |
| H-3 | F-001 stream 분기 신설 | [066계승] 기존 `--json`(subprocess.run) 경로·5필드 계약 회귀 오염 | P1 | L1(기존 test_opal_agent.py 스위트)+L2 | S-4 |
| H-4 | F-001 증분 기록 | stdout 버퍼링으로 events.jsonl이 종료 시 일괄 flush → "실행 중 창" 미충족 | P1 | L2(실행 중 tail 관찰) | S-5 |
| H-5 | F-003 R-NEST 파싱 | 도구 이벤트가 `message.content[].type` 중첩(ANALYSIS §2.3) — 최상위 `type`만 보면 "최근 이벤트 요약" 공백 | P2 | L1(fixture 파싱) | S-8 |
| H-6 | F-003 방어적 파싱 | [066계승] 환경 의존 이벤트(`hook_*`/`thinking_tokens`) 의존 시 타 환경 붕괴 — 미보장 필드 의존 금지(R-H) | P1 | L1(최소 보장 집합 fixture) | S-8 |
| H-7 | F-003 상태 판정 | exitcode 부재를 blocked로 오판, 또는 exit 2를 완료로 오판 → 현황판 오표시 | P1 | L1(6상태 fixture) | S-7, S-9 |
| H-8 | F-003 `--watch` | 상주 미종료(무한 폴링)·재렌더 누수 → 리소스 점유 | P2 | L2(상한 도달 종료 관찰) | S-6 |
| H-9 | F-004 install 배포·chmod | run.sh 권한 비트 미보존/미배포 → `~/.opal/tools/oppl-monitor/run.sh` 실행 불가 | P1 | L2(install 후 실행) | S-10 |
| H-10 | F-002 규약 v2 | [066계승] 완료 마커=exitcode 불변 위반(규약이 마커를 events.jsonl로 이동시키면 판정 붕괴) | P0 | L1(문서 계약 검토) | S-11 |

---

## 2. 기능별 분석

### F-001: opal-agent stream-json 실행 경로

#### 2.1.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 도구 | `opal/tools/opal-agent/opal_agent.py` | 멀티 provider 호출 라이브러리+CLI — stream 경로 개조 본체 | 수정 |
| 도구 | `opal/tools/opal-agent/README.md` | 사용 설명서 — stream 모드 절 신설 | 수정 |
| 도구 | `opal/tools/opal-agent/tests/test_opal_agent.py` | 단위 테스트 — stream 조립/파싱 시나리오 추가 + 기존 회귀 baseline | 수정 |

#### 2.1.2 현재 구현 (ANALYSIS §1.2·§2 참조)
- `_run()`이 유일 실행 진입점이며 `subprocess.run(capture_output=True)` 블로킹 전용 — 증분 실행 경로 부재 (`opal_agent.py:558-618`).
- `ClaudeAdapter.build_invocation()`는 `--output-format {json|text}`만 조립 (`opal_agent.py:180-197`). `parse_result()`는 `_loads()`로 단일 JSON 객체를 파싱해 5필드 추출 (`opal_agent.py:199-211`).
- CLI `--json`/`--text`는 표시 방식만 분기하고 라이브러리는 항상 `output_format="json"` 고정 실행 (`opal_agent.py:701-717`, `:664-673`).
- 실측(ANALYSIS §2.4): stream-json 마지막 줄(`type:result`)이 기존 `--output-format json` 단일 객체와 **동일 스키마**로 5필드 보유 → 필드 추출 로직 재사용, 입력 표면만 "마지막 줄"로 변경.

#### 2.1.3 영향 범위
- 상위 의존: `opal/agents/opal-loop-action-agent/AGENT.md`(비동기 축 명령 형태 — F-002가 stream으로 전환), `opal/tools/opal-agent/run.sh`(무변경, 인자 pass-through).
- 하위 의존: claude CLI `--output-format stream-json --verbose` (ANALYSIS §2.5 필수).
- 공유 계약: `AgentConfig.output_format`에 `"stream-json"` 값 추가 — 기존 `"json"`/`"text"` 소비자 불변 (하위호환, ANALYSIS §3.3).

### F-002: 결과 파일 규약 v2 + journal 규약

#### 2.2.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 에이전트 | `opal/agents/opal-loop-action-agent/AGENT.md` | §결과 파일 규약 v1→v2 + §운행 일지 신설 | 수정 |

#### 2.2.2 현재 구현
- §결과 파일 규약(v1.1, 066): 3-분리(`<phase>.result.json`/`.err.log`/`.exitcode`) + 완료 마커=exitcode 존재 (`AGENT.md:153-190`).
- 비동기 축 명령 형태: `run.sh … --json "…" > <phase>.result.json 2> <phase>.err.log; echo $? > <phase>.exitcode` (`AGENT.md:59-74`).
- prompt 보존: 066 실증에서 `<phase>.prompt.txt`가 실생성되나(`samples/T01/.oppl-run/t1.prompt.txt`) 규약에 미명문(비규약 자발) — v2에서 규약화.
- journal: §운행 일지 절 부재 — 신설 (stream 대체 불가 영역, TASK 배경 분석).

#### 2.2.3 영향 범위
- 상위 의존: `opal/skills/opal-pilot-project-loop/SKILL.md`(`:291-303` `[opal-agent 채널]` 표기 — 구조 복제 없이 AGENT.md 포인터만 참조, `SKILL.md:375` → 본문 추가 수정 불요, ANALYSIS §3.2).
- 하위 의존: F-003 oppl-monitor가 events.jsonl·journal.md 경로 규약을 입력 계약으로 소비.

### F-003: oppl-monitor 신규 도구

#### 2.3.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 도구 | `opal/tools/oppl-monitor/oppl_monitor.py` | `.oppl-run/` 파싱 + 현황판 렌더 + `--json` + `--watch` | 신규 |
| 도구 | `opal/tools/oppl-monitor/run.sh` | OPAL .venv python 래퍼 (opal-agent run.sh 관례) | 신규 |
| 도구 | `opal/tools/oppl-monitor/README.md` | 도구 사용 설명서 | 신규 |

#### 2.3.2 현재 구현
- 부재 확인(ANALYSIS §1.1). 기존 OPAL 도구 관례: `run.sh` → `~/.opal/.venv/bin/python <tool>.py`, `{ "ok": true/false }` JSON 에러계약 (`opal/tools/opal-agent/run.sh`, tools.md xlsx-tool 출력 형식).
- 입력 실데이터(ANALYSIS §5): `samples/T01/.oppl-run/`에 3-분리 5축 + session.json + prompt.txt 실존. result.json은 claude 원문 전체 JSON(66필드) — 5필드만 방어적 소비.

#### 2.3.3 영향 범위
- 순환 의존 없음 — `.oppl-run/` 파일만 읽는 독립 리더 (ANALYSIS §1.3). opal-agent와 직접 import/호출 관계 없음(파일 계약으로만 연결).
- 외부 패키지 없음 — 표준 라이브러리만 (ANALYSIS §1.3).

### F-004: 문서 정합·등록 / F-005: 동작 실증

#### 2.4.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 문서 | `opal/core/references/tools.md` | 도구 레지스트리 — oppl-monitor 절 추가 | 수정 |
| 문서 | `opal/core/references/opal-harness.md` §9 | 등록 도구 표 — oppl-monitor 행 추가 (`:242-256`) | 수정 |
| 오케스트레이터 | `opal/skills/opal-pilot-project-loop/SKILL.md` | 모니터링 안내 1~2줄 | 수정 |
| 배치 | `scripts/install-mac.sh` | oppl-monitor 개별 chmod 블록 (`:1122-1178` 관례) | 수정 |
| 배치 | `tasks/067-260717-opd-루프액션-스트림-모니터링/samples/` | 재실증 fixture(정상·blocked) | 신규 |

---

## 3. 기능별 설계

### F-001: opal-agent stream-json 실행 경로

#### 3.1.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/opal-agent/opal_agent.py` | 도구 | `AgentConfig.output_format`에 `"stream-json"` / `ClaudeAdapter.supports_stream`+stream 분기(`--verbose`) / `parse_result` stream(마지막 줄) 경로 / `_run_stream()` Popen 신설 / `_run` 디스패치 / CLI `--stream` | (→ D-1 §2·§3.1), `opal_agent.py:180-211,558-618,664-673` |
| 2 | `opal/tools/opal-agent/README.md` | 도구 | stream 모드 절 + CLI 옵션 표 `--stream` 행 + 변경이력 | (→ D-2) |
| 3 | `opal/tools/opal-agent/tests/test_opal_agent.py` | 도구 | stream 조립/파싱 단위 시나리오 + 회귀 baseline | (→ D-12) |

#### 3.1.2 API·설계

**결정 R-ASYNC (핵심) — events.jsonl 기록 주체: 호출측 stdout 리다이렉트 (opal-agent 내부 파일 append 미채택)**

- opal-agent stream 모드는 claude stream-json 각 줄을 **자기 stdout으로 line-buffered passthrough**한다. 호출측(루프 액션 에이전트)이 `> <phase>.events.jsonl`로 리다이렉트하여 파일에 증분 기록한다. opal-agent에 `--events-file` 같은 내부 파일 인자를 **추가하지 않는다**.
- 근거·트레이드오프:
  - 파일 락/경합: 리다이렉트 방식은 **단일 writer(셸 fd)** — 비동기 축은 각 phase가 독립 파일(t1/t2/t3)이라 동시 write 없음. 내부 append 방식은 opal-agent가 파일을 별도 open/flush해야 해 코드·결합 증가. (→ D-1 §5 R-ASYNC)
  - 3-분리 정합: stream 축에서 **stdout 캡처 슬롯이 `result.json`→`events.jsonl`로 재포맷**될 뿐(단일 JSON→JSONL), `.err.log`(stderr)·`.exitcode`(완료 마커)는 불변. 완료 마커=exitcode 존재 계약 유지(H-10). ([066계승] `AGENT.md:167`)
  - 5필드 추출 정합: TASK R-ASYNC 힌트대로 stdout=이벤트 스트림이 되어 마지막 줄(`type:result`)에서 5필드 추출. (→ D-0 §PLAN 필수결정 1)
  - ANALYSIS §1.2는 events.jsonl을 "3-분리 위 4번째 파일"로 서술했으나, 이는 R-ASYNC 결정 이전 관점이다. 리다이렉트 방식에서는 stdout 슬롯 재포맷이므로 순증 파일이 아니라 result.json 대체(비동기 축 한정)로 확정한다 — 결정 근거 명시로 상충 해소.

**결정 R-EVSCHEMA — events.jsonl은 claude 원본 이벤트 그대로 기록 (정규화 요약 미채택)**

- passthrough 방식의 필연적 귀결: opal-agent는 mid-stream 이벤트를 정규화하지 않고 그대로 흘린다. 5필드 추출을 위해 마지막 `type:result` 줄만 파싱한다(최소 보장 집합, R-H 준수). (→ D-1 §2.6)
- 트레이드오프: opal-agent는 claude 스키마 변화에 최소 결합(마지막 result 줄 5필드만 의존). 파싱 부담(R-NEST `message.content[]` 순회)은 oppl-monitor가 방어적으로 진다(H-5). 정규화 요약을 opal-agent에 넣으면 claude 스키마 변경 취약성이 opal-agent로 이동 → 미채택. (→ D-1 §5 R-EVSCHEMA)

**결정 R-VERBOSE — `--verbose` 무조건 자동 부착 + 사용법 에러 흡수**

- `ClaudeAdapter.build_invocation`에서 `output_format=="stream-json"`이면 `["--output-format","stream-json","--verbose"]`를 항상 조립. 미부착 exit 1(ANALYSIS §2.5) 케이스는 코드 내부에서 원천 차단 — 별도 분류 불요. (→ D-1 §2.5, §4 발견3)
- [MUST] `opal_agent.py` stream 분기: "`--output-format stream-json`은 `--verbose`를 항상 동반한다."

**함수 시그니처 (설계)**

```python
# AgentConfig.output_format: "json" | "text" | "stream-json"   (신규 값, 기본 "json" 불변)

class ClaudeAdapter(ProviderAdapter):
    supports_stream = True          # claude만 True (타 어댑터 미설정 → False)
    def build_invocation(self, config, resolved_bin) -> Invocation:
        # output_format == "stream-json" → cmd += ["--output-format","stream-json","--verbose"]
        ...
    def parse_result(self, config, stdout) -> AgentResult:
        # output_format == "stream-json" → 마지막 비어있지 않은 JSON 줄(type=="result") 파싱
        #   → 기존 json 경로와 동일 필드 추출(result/session_id/is_error/total_cost_usd/duration_ms)
        ...

def _run_stream(config: AgentConfig, adapter, inv, env) -> AgentResult:
    # subprocess.Popen(inv.cmd, stdout=PIPE, stderr=None(inherit → 셸 2> 캡처),
    #                  text=True, bufsize=1, cwd, env)
    # for line in proc.stdout:  sys.stdout.write(line); sys.stdout.flush()  # 증분 passthrough(H-4)
    #                           lines.append(line)                          # 마지막 줄 추출용
    # 데드라인(config.timeout) 초과 시 proc.kill() → OpalAgentTimeout
    # proc.returncode != 0 → OpalAgentError (exit 코드·stderr)
    # adapter.parse_result(config, "".join(lines)) 반환

def _run(config):  # 디스패치 추가
    # output_format == "stream-json" → _run_stream(...) ; else 기존 subprocess.run 경로(불변)
    # provider가 supports_stream 아니면 OpalAgentError("… stream-json 미지원 provider") — 명시 에러(R-1 AC)
```

**CLI 표면**: fmt 상호배타 그룹에 `--stream` 추가 → `output_format="stream-json"`, `display="stream"`. `display=="stream"`이면 `main()`은 별도 dump 없이(실행 중 passthrough 완료) `result.is_error` 기준 종료코드만 반환. 종료코드 체계(0/1/2)는 [066계승] 불변.

#### 3.1.3 환경 변경
해당 없음 — 표준 라이브러리만(`subprocess.Popen`), 신규 패키지 없음.

#### 3.1.4 배치/마이그레이션
해당 없음 — opal-agent는 `~/.opal/tools/` 일괄 복사로 재배포(README:22-24), install 무변경.

#### 3.1.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | R-1 AC | 단위 | `ClaudeAdapter.build_invocation(output_format="stream-json").cmd`에 `--output-format stream-json` **및** `--verbose` 동시 포함 (H-2) |
| TS-002 | R-1 AC | 단위 | stream 마지막 줄 fixture(`type:result`) → `parse_result`가 5필드 정확 추출 (H-1) |
| TS-003 | R-1 AC | 회귀 | 기존 `test_opal_agent.py` 스위트 전체 PASS (json/text·마커·상호배타 baseline 무손상, H-3) |
| TS-004 | R-1 AC | 단위 | `output_format="stream-json"` + `provider="codex"` → `OpalAgentError`(명시 에러) |
| TS-005 | R-1 AC | 통합(E2E) | `run.sh --stream "…" > ev.jsonl` → ev.jsonl 유효 JSONL·마지막 줄 result·5필드 추출, 실행 중 파일 증분 성장(H-4) |

### F-002: 결과 파일 규약 v2 + journal 규약

#### 3.2.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/agents/opal-loop-action-agent/AGENT.md` | 에이전트 | §결과 파일 규약 v2(events.jsonl·prompt.txt 규약화·완료마커 불변·v1→v2 변경점 표) + §운행 일지 신설 + 비동기 축 명령 형태 stream 전환 + 변경이력 v1.2 | (→ D-3), (→ D-1 §1.2·§2) |

#### 3.2.2 설계

**규약 v2 — 비동기 축(T1/T2/T3) stream 전환**

- 비동기 축 명령 형태(`AGENT.md:59-74` 개정): `run.sh … --stream "…" > <phase>.events.jsonl 2> <phase>.err.log; echo $? > <phase>.exitcode`.
- 동기 축(G/T4a/T4b)은 `--json` → `<phase>.result.json` **유지**(빠른 foreground, 실행 중 창 불요, 5필드 추출 불변). 근거: 스트림의 가치는 장시간 비동기 축의 live window이며 동기 축은 Bash 반환으로 이미 수거됨 → 변경 최소·회귀 위험 최소.
- 경로 규약(개정):

```
비동기 축(t1/t2/t3): <phase>.events.jsonl  ← stdout (claude stream-json 원본 JSONL; 마지막 줄=result 이벤트)
동기 축(g/t4a/t4b):  <phase>.result.json   ← stdout (claude 단일 JSON; 5필드 소비)  [066계승 불변]
공통:                <phase>.err.log       ← stderr   /   <phase>.exitcode ← 완료 마커  [066계승 불변]
공통:                <phase>.prompt.txt    ← 디스패치 프롬프트 원문 (v2 규약화, 066 자발→명문)
```

- 5필드 소비(비동기 축): `.events.jsonl`의 **마지막 비어있지 않은 줄**(type==result)에서 `result`/`session_id`/`is_error`/`total_cost_usd`/`duration_ms` 추출. 미보장 필드 의존 금지(R-H). ([066계승] `AGENT.md:169-171`)
- [066계승][MUST] 완료 마커=exitcode 파일 존재 불변 — events.jsonl 존재/비존재로 완료 판정하지 않는다(H-10). 완료 판정 표(`AGENT.md:173-181`)는 result.json↔events.jsonl 파싱 대상만 축별 분기, 표 구조 불변.
- v1→v2 변경점 표를 규약 절에 명기(events.jsonl 편입·prompt 규약화·동기/비동기 산출물 분기).

**§운행 일지 (journal) 신설**

- 경로: `<task_folder>/.oppl-run/journal.md` (append-only 마크다운 표).
- 기록 주체: 루프 액션 에이전트(자신의 게이트 판단·재시도·단계 전환 — CLI 밖 행동, stream 대체 불가).
- 형식(컬럼): `시각 | 단계 | 이벤트 | 근거`
  - 시각: `YYYY-MM-DDTHH:mm:ssZ`(ISO8601) 또는 `YYYY-MM-DD HH:mm` KST.
  - 단계: `t1|t2|g|t3|t4a|t4b|task` (task=태스크 수준 이벤트).
  - 이벤트: `start | end | gate-verdict | retry | blocked`.
  - 근거: verdict+사유 / 재시도 회차+사유 / blocked 트리거 번호(§blocked 반환 계약 7종) 등.
- 기록 시점: 각 단계 시작/종료, G 게이트 판단(verdict+근거), 재시도(회차+사유 — [MUST] 수치는 harness §1 참조, 비복제 D-10 §2), blocked 사유.
- append-only 원칙 명문(기존 행 수정·삭제 금지).

#### 3.2.3 환경 변경 / 3.2.4 배치/마이그레이션
해당 없음 (문서 개정).

#### 3.2.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-006 | R-2 AC | 산출물 검사 | AGENT.md v2 절에 events.jsonl 경로·완료 마커 불변·prompt 규약·v1→v2 변경점 표가 명문화 (H-10) |
| TS-007 | R-3 AC | 산출물 검사 | AGENT.md §운행 일지에 기록 시점·4컬럼 형식·append-only 원칙 명문화 |

### F-003: oppl-monitor 신규 도구

#### 3.3.1 파일 변경 계획
**신규 생성**
| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `opal/tools/oppl-monitor/oppl_monitor.py` | 도구 | 파서+렌더러+`--json`+`--watch`+에러계약 (@header 필수) | (→ D-3 §결과 파일 규약), (→ D-1 §2.3) |
| 2 | `opal/tools/oppl-monitor/run.sh` | 도구 | `~/.opal/.venv/bin/python` 래퍼 (opal-agent run.sh 복제), +x 커밋 | `opal/tools/opal-agent/run.sh` |
| 3 | `opal/tools/oppl-monitor/README.md` | 도구 | 사용법·출력 스키마 | - |

#### 3.3.2 설계

**결정 8 — 화면 설계 (단계×축 현황판)**

- CLI: `run.sh <task_folder> [--json] [--watch [간격초]] [--watch-timeout <초>]`.
- 입력: `<task_folder>/.oppl-run/` 스캔 — phase 순서 `[t1, t2, g, t3, t4a, t4b]`.
- phase별 산출물 탐지: `<phase>.events.jsonl`(stream 축) **또는** `<phase>.result.json`(sync 축), `<phase>.err.log`, `<phase>.exitcode`, `<phase>.prompt.txt`. 재시도 접미사(`.a<N>.`, `AGENT.md:182-184`)는 최대 N을 최신으로 채택.

**상태 판정 로직(결정 8)** — H-7 방어:

| 조건 | 상태 | 표기 |
|------|------|------|
| exitcode 부재 + (events/result/prompt 존재) | 진행중 | `running` |
| exitcode 부재 + 산출물 전무 | 대기 | `pending` |
| exitcode == 0 | 완료 | `done` |
| exitcode == 1 | 실패(is_error, 프로세스 정상) | `failed` |
| exitcode == 2 | 하드에러(CLI 실행 실패) | `error` |
| journal.md에 해당 phase blocked 기록 | 차단 | `blocked` |

- blocked는 exitcode 체계 밖(루프 액션 에이전트 수준 verdict) → journal.md의 `blocked` 이벤트 행에서 검출(phase 매칭). 전체 blocked 플래그 = journal에 blocked 행 1개 이상. ([066계승] 완료 판정 표 `AGENT.md:173-181` + blocked 7종 계약 `AGENT.md:246-258`).

**컬럼(텍스트 현황판)**: `축(phase) | 상태 | 경과 | 최근 이벤트 요약 | 비용/세션`
- 경과: `min(prompt.txt mtime, events/result 최초 mtime)` → `exitcode mtime`(있으면) 또는 `now`(진행중) 차이(초). 파일 mtime 프록시(표준 라이브러리).
- 최근 이벤트 요약(R-NEST, H-5·H-6 방어): events.jsonl 역순 순회로 첫 의미 이벤트 추출 — `assistant.message.content[].type=="tool_use"` → `"tool_use: <name>"`, `user.message.content[].type=="tool_result"` → `"tool_result"`, `type=="result"` → `"result(<subtype>)"`, 그 외 → 최상위 `type`. 알 수 없는/미보장 타입은 generic 표기로 degrade(R-H). sync 축(result.json)은 `result` 텍스트 앞부분 요약.
- 비용/세션: 마지막 result에서 total_cost_usd·session_id(있으면).
- 하단: **journal tail**(마지막 N행, 기본 8) + 전체 blocked 배너(있으면).

**`--json` 스키마(결정 8)**:
```json
{
  "ok": true,
  "task_folder": "<abs>",
  "generated_at": "<ISO8601>",
  "blocked": false,
  "phases": [
    {"phase":"t1","axis":"stream","status":"done","exitcode":0,
     "elapsed_sec":68,"last_event":{"kind":"tool_use","name":"Write"},
     "cost_usd":0.56,"session_id":"9A63…","is_error":false}
  ],
  "journal_tail": [{"time":"…","phase":"g","event":"gate-verdict","detail":"pass"}]
}
```
- 에러계약: 폴더 부재·`.oppl-run/` 부재 → `{"ok": false, "error": "<메시지>"}` + exit 1 (tools.md xlsx-tool 출력 형식 관례).

**결정 R-WATCH**: `--watch [간격초]` 기본 2초 폴링. 재렌더 = ANSI clear+홈(`\033[2J\033[H`) 후 전체 재그림(full repaint, 표준 라이브러리, flicker 허용). 상주 상한: (a) 모든 phase가 terminal(exitcode 존재) + grace 1주기 후 자동 종료, (b) `--watch-timeout`(기본 1800초) 도달 시 종료, (c) KeyboardInterrupt. `--json`은 1회성(watch 무시). (→ D-1 §5 R-WATCH: 선례 없음 — 신규 정의.)

**결정 R-REG**: oppl-monitor만 레지스트리 등록. opal-agent는 [범위 외] 미등록 유지(ANALYSIS §4 발견1) — README "관련 도구" 서술에서 opal-agent는 등록 도구가 아니라 소스 경로(`opal/tools/opal-agent/`)로만 지시. (→ D-1 §5 R-REG)

#### 3.3.3 환경 변경
해당 없음 — 표준 라이브러리만(`json`, `argparse`, `pathlib`, `os`, `time`, `datetime`, `sys`). requirements.txt 무변경(ANALYSIS §1.3).

#### 3.3.4 배치/마이그레이션
- run.sh를 저장소에 `chmod +x`(rwxr-xr-x)로 커밋 → install `cp -Rf` 권한 비트 보존(ANALYSIS §3.2). F-004에서 개별 chmod 블록 병행(관례 일관성, R-CHMOD).

#### 3.3.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-008 | R-4 AC | 통합 | `samples/T01/.oppl-run/`(066 실증) 렌더 성공 — 5축 상태·경과·최근 이벤트·비용 표시, R-NEST tool_use 요약 정상 (H-5·H-6) |
| TS-009 | R-4 AC | 기능 | exit 2 fixture=`error`, exitcode 부재=`running`, exit 0=`done` 구분 표시 (H-7) |
| TS-010 | R-4 AC | 기능 | journal.md blocked 행 → 해당 phase `blocked` + 전체 blocked 배너 |
| TS-011 | R-4 AC | 기능 | `--json` 출력이 위 스키마 유효 JSON, 폴더 부재 시 `{"ok":false,...}` + exit 1 |
| TS-012 | R-4 AC | 기능 | `--watch` 진행중 fixture에서 주기 재렌더 + 상한(모든 terminal/`--watch-timeout`) 도달 시 정상 종료 (H-8) |

### F-004: 문서 정합·등록

#### 3.4.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/core/references/tools.md` | 문서 | oppl-monitor 절(용도·실행/소스 경로·커맨드·출력 형식·예시) 추가 | (→ D-8) |
| 2 | `opal/core/references/opal-harness.md` §9 | 문서 | 등록 도구 표에 oppl-monitor 행 추가 (`:242-256`) | (→ D-8) |
| 3 | `opal/tools/opal-agent/README.md` | 문서 | stream 모드 절(F-001 3.1.2) — F-001 Step에서 처리 | (→ D-2) |
| 4 | `opal/skills/opal-pilot-project-loop/SKILL.md` | 오케스트레이터 | 모니터링 안내 1~2줄(`oppl-monitor <task_folder>` — 진행 현황 관측) | (→ D-9 `:291-303`) |
| 5 | `scripts/install-mac.sh` | 배치 | oppl-monitor 개별 chmod 블록 추가 (`:1122-1178` 관례) | (→ D-11) |

#### 3.4.2 설계

**결정 R-CHMOD — 개별 chmod 블록 추가(관례 일관성 채택)**

- install-mac.sh는 신규 도구 도입마다 방어적 개별 `chmod +x` 블록을 추가해 온 관례(playwright/state/brain/cmux/tool-scan/memory/git-sync/backlog 8종, `install-mac.sh:1118-1178`). oppl-monitor도 동일 블록 추가 — `cp -Rf` 권한 보존이 이미 있어 필수는 아니나(ANALYSIS §3.2), 일관성·명시성·방어(권한 비트 유실 리스크 H-9)를 위해 채택. 저비용. (→ D-1 §5 R-CHMOD)
- opal-agent는 이 블록 없이도 배포됨(README:22-24) — opal-agent에는 블록 추가하지 않음(범위 외·관례상 opal-agent는 예외).

**변경이력([MUST] D-9)**: opal_agent.py·README·AGENT.md·tools.md·opal-harness.md·oppl SKILL.md 전부에 067 행 추가. install-mac.sh는 변경이력 표 대상 아님(스크립트).

#### 3.4.3~3.4.4 환경/배치
- install: `oppl-monitor/run.sh` 개별 chmod 블록 1개 추가 외 배포 로직 무변경(`install_dir("$opal_dir/tools", …)` 일괄 복사가 신규 디렉토리 자동 포함, `install-mac.sh:1112`).

#### 3.4.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-013 | R-5 AC | 산출물 검사 | tools.md·opal-harness.md §9 양쪽에 oppl-monitor 등록 + 변경 문서 전부 067 변경이력 행 |
| TS-014 | R-5 AC | 통합 | `./scripts/install-mac.sh` 후 `~/.opal/tools/oppl-monitor/run.sh <folder>` 실행 가능(+x) (H-9) |

### F-005: 동작 실증

#### 3.5.1 파일 변경 계획
**신규 생성**
| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `tasks/067-…/samples/` | 배치 | (A) 루프 액션 에이전트 실 디스패치 산출물(events.jsonl·journal.md 실생성) + (B) oppl-monitor 상태 판정용 4 fixture(정상/진행중/exit2/blocked) | (→ D-0 R-6) |

#### 3.5.2 설계

TASK 완료기준 ②는 "루프 액션 에이전트 재실증(066 S-8급)에서 events.jsonl·journal.md **실생성** 관측"이다(→ D-0 §완료기준). journal.md 기록 주체는 루프 액션 에이전트 자신(§3.2.2 — CLI 밖 행동)이므로 **fixture로는 실생성 검증이 성립하지 않는다**. 따라서 검증 경로를 3층으로 분리·강화한다:

**(a) [필수] 루프 액션 에이전트 실 디스패치 1회 — TS-015의 유일한 Pass 경로**
- 066 S-8급 슬라이스 fixture(예: greeting 슬라이스, `samples/T01-정상슬라이스` 준거)를 대상으로, **배포본**(`~/.opal/agents/opal-loop-action-agent/AGENT.md` v2 + `~/.opal/tools/opal-agent`·`~/.opal/tools/oppl-monitor` — Step 9 선두 재배포 후) 기준으로 루프 액션 에이전트를 **1회 실제 디스패치**한다.
- 관측: 비동기 축(t1/t2/t3)의 `<phase>.events.jsonl`이 규약 v2대로 실생성(유효 JSONL·마지막 줄 `type:result`·5필드), 루프 액션 에이전트가 `.oppl-run/journal.md`를 append-only 4컬럼으로 **실생성**. stream/fixture 대체는 이 경로의 Pass로 인정하지 않는다.

**(b) [선행] stream 모드 직접 실측(TS-005) — 별개 선행 검증으로 유지**
- F-001 stream 경로 자체의 events.jsonl 증분·5필드 추출 검증(§3.1.5 TS-005). (a)의 상류 전제이나 (a)와 역할이 다르다 — (a)는 규약 v2 통합·journal 실생성까지, (b)는 opal-agent 단독 stream 정합.

**(c) oppl-monitor 상태 판정 테스트(TS-009~TS-012) 한정 — 4 fixture**
- 정상/진행중/exit2/blocked 4 fixture는 **oppl-monitor 6상태 판정·blocked 검출 테스트 입력으로만** 사용한다(§3.3.2). 완료기준 ②(실생성)의 증거로는 사용하지 않는다 — fixture는 monitor 파싱 대상일 뿐 루프 액션 에이전트 산출물이 아니다.
- blocked fixture: journal.md에 blocked 행을 둔 `.oppl-run/`으로 monitor blocked 표시 실증(TS-010).

- 증거: (a) 실 디스패치 산출물 트리 + journal.md·events.jsonl 원문 발췌, (c) monitor 렌더 캡처(텍스트) + TEST-SCENARIO PASS 로그.

#### 3.5.3~3.5.4 환경/배치: 해당 없음(재배포는 Step 9 선두 작업 — §4.2).

#### 3.5.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-015 | R-6 AC | 통합(E2E) | **루프 액션 에이전트 실 디스패치 1회(배포본·규약 v2)**에서 비동기 축 events.jsonl(유효 JSONL·마지막 줄 result) + journal.md **실생성** 관측 (fixture/stream 대체 불가 — 유일 Pass 경로) |
| TS-016 | R-6 AC | 통합 | 4 fixture(정상/진행중/exit2/blocked)로 oppl-monitor 상태 판정·blocked 표시 실증 (TS-009~TS-012 한정 입력) |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)
| Phase | 기능 | Step | agent | 실행 | 비고 |
|-------|------|------|-------|------|------|
| 1 | F-001 | 1, 2 | opal-task-agent | 순차 | opal_agent.py 개조 → 테스트/README (동일 도구) |
| 2 | F-002 | 3 | opal-task-agent | Phase 1 후 | AGENT.md 규약 v2 (events.jsonl 계약 확정 후) |
| 3 | F-003 | 4, 5 | opal-task-agent | Phase 2 후 | oppl_monitor.py → run.sh (규약 입력 계약 확정 후) |
| 4 | F-004 | 6, 7, 8 | opal-task-agent | Phase 3 후 | 등록·SKILL·install (도구 존재 후) |
| 5 | F-005 | 9 | opal-task-agent | Phase 4 후 | 실증(전체 배포 후) |
| 6 | 문서 | 10 | PM 직접 | Phase 5 후 | docs/ 갱신 |

### 4.2 실행 체크리스트
> 총 10개 Step | Phase 6개 | 실행 모드: 복잡

#### Step 1: opal-agent stream-json 실행 경로 신설
- [x] 완료
- **소속 기능**: F-001
- **영역**: 도구
- **agent**: opal-task-agent
- **파일**: `opal/tools/opal-agent/opal_agent.py`
- **작업 내용**: `AgentConfig.output_format`에 `"stream-json"` 허용 / `ClaudeAdapter.supports_stream=True` + `build_invocation` stream 분기(`--output-format stream-json --verbose` 항상 동반) / `parse_result` stream 경로(마지막 비어있지 않은 `type:result` 줄에서 5필드 추출) / `_run_stream()` Popen(stdout=PIPE line-buffered passthrough → sys.stdout flush, stderr 상속, timeout 데드라인) 신설 / `_run` 디스패치(stream-json→`_run_stream`, else 기존 subprocess.run 불변) / supports_stream 아닌 provider에 stream 지정 시 `OpalAgentError` / CLI fmt 그룹에 `--stream` 추가(`output_format="stream-json"`, display="stream", main dump 생략). @header 변경이력 갱신.
- **완료 기준**: stream 분기가 기존 json/text 경로와 격리(디스패치 분기), `--verbose` 항상 조립, 비-claude stream 명시 에러. `python -m py_compile` 통과.
- **테스트**: TS-001, TS-002, TS-004 (Step 2에서 실행)
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 2: opal-agent stream 단위/회귀 테스트 + README 절
- [ ] 완료
- **소속 기능**: F-001
- **영역**: 도구
- **agent**: opal-task-agent
- **파일**: `opal/tools/opal-agent/tests/test_opal_agent.py`, `opal/tools/opal-agent/README.md`
- **작업 내용**: stream 조립 단위(build_invocation stream cmd에 `--verbose` 포함), stream 파싱 단위(마지막 줄 5필드 fixture), 비-claude stream 에러 단위 추가. 기존 스위트 전체 실행(회귀). README에 stream 모드 절(사용법·`--stream`·events.jsonl passthrough·verbose 자동·claude 1차) + CLI 옵션 표 `--stream` 행 + 변경이력 067.
- **완료 기준**: `python -m unittest`(또는 pytest) 신규+기존 전부 PASS(H-3). README stream 절 존재.
- **테스트**: TS-001, TS-002, TS-003, TS-004
- **실행 방법**: sub-agent
- **의존**: Step 1

#### Step 3: AGENT.md 결과 파일 규약 v2 + §운행 일지
- [x] 완료
- **소속 기능**: F-002
- **영역**: 에이전트
- **agent**: opal-task-agent
- **파일**: `opal/agents/opal-loop-action-agent/AGENT.md`
- **작업 내용**: 비동기 축(t1/t2/t3) 명령 형태를 `--stream … > <phase>.events.jsonl`로 전환(동기 축 result.json 유지) / §결과 파일 규약 경로·5필드 소비(events.jsonl 마지막 줄)·완료마커=exitcode 불변([066계승])·prompt.txt 규약화·v1→v2 변경점 표 / §운행 일지 신설(경로 `.oppl-run/journal.md`·`시각|단계|이벤트|근거` 4컬럼·기록 시점·append-only, 재시도 수치 비복제 harness §1 포인터 D-10). 변경이력 v1.2 추가.
- **완료 기준**: v2 절에 events.jsonl·완료마커 불변·prompt 규약·변경점 표 존재. §운행 일지 4컬럼·append-only 명문. [MUST] 완료 마커 문구 불변 확인(H-10).
- **테스트**: TS-006, TS-007
- **실행 방법**: sub-agent
- **의존**: Step 1

#### Step 4: oppl_monitor.py 신규 구현
- [x] 완료
- **소속 기능**: F-003
- **영역**: 도구
- **agent**: opal-task-agent
- **파일**: `opal/tools/oppl-monitor/oppl_monitor.py`
- **작업 내용**: `.oppl-run/` 파서(phase 6종·events/result 축 판별·재시도 접미사 최신 채택) / 상태 판정(6상태 표 §3.3.2, H-7) / 최근 이벤트 요약(R-NEST `message.content[]` 역순 순회, 미보장 타입 degrade — H-5·H-6) / 경과(mtime 프록시) / 텍스트 현황판 렌더 / `--json`(스키마 §3.3.2) / `--watch`(2초 폴링·ANSI clear+repaint·상한 3종 — R-WATCH) / journal.md tail·blocked 검출 / 에러계약 `{"ok":false,...}`+exit 1. @header 블록·표준 라이브러리만.
- **완료 기준**: `py_compile` 통과, samples/T01 렌더 성공, `--json` 유효, 폴더 부재 에러계약.
- **테스트**: TS-008~TS-012
- **실행 방법**: sub-agent
- **의존**: Step 3

#### Step 5: oppl-monitor run.sh 래퍼 + README
- [x] 완료
- **소속 기능**: F-003
- **영역**: 도구
- **agent**: opal-task-agent
- **파일**: `opal/tools/oppl-monitor/run.sh`, `opal/tools/oppl-monitor/README.md`
- **작업 내용**: opal-agent run.sh 복제(`~/.opal/.venv/bin/python oppl_monitor.py "$@"`, .venv 부재 시 `{"ok":false,...}`). `chmod +x run.sh`(rwxr-xr-x 커밋). README(용도·커맨드·출력 스키마·`--json`/`--watch`·관련 소스 opal-agent 경로 표기 — R-REG).
- **완료 기준**: `run.sh <folder>`가 oppl_monitor.py 호출, `ls -la`에 -rwxr-xr-x.
- **테스트**: TS-008
- **실행 방법**: sub-agent
- **의존**: Step 4

#### Step 6: install-mac.sh oppl-monitor chmod 블록
- [x] 완료
- **소속 기능**: F-004
- **영역**: 배치
- **agent**: opal-task-agent
- **파일**: `scripts/install-mac.sh`
- **작업 내용**: `:1178` backlog-tool 블록 뒤에 oppl-monitor `run.sh` 개별 `chmod +x` 블록 추가(관례 일관성, R-CHMOD). 배포 로직 무변경(일괄 복사가 신규 디렉토리 자동 포함).
- **완료 기준**: 블록 존재, `bash -n scripts/install-mac.sh` 통과.
- **테스트**: 산출물 검사(블록 존재·구문). 실행 검증(TS-014 배포 후 run.sh 실행)은 Step 9 (0) 재배포 지점에서 수행.
- **실행 방법**: sub-agent
- **의존**: Step 5

#### Step 7: 도구 레지스트리 등록 (tools.md + harness §9)
- [x] 완료
- **소속 기능**: F-004
- **영역**: 문서
- **agent**: opal-task-agent
- **파일**: `opal/core/references/tools.md`, `opal/core/references/opal-harness.md`
- **작업 내용**: tools.md에 oppl-monitor 절(용도·실행/소스 경로·의존성·커맨드·출력 형식·예시). opal-harness.md §9 등록 도구 표에 oppl-monitor 행(용도·트리거). opal-agent 미등록 유지(R-REG). 양 문서 변경이력 067.
- **완료 기준**: 2곳 등록 + 변경이력 행 존재.
- **테스트**: TS-013
- **실행 방법**: sub-agent
- **의존**: Step 5

#### Step 8: oppl SKILL 모니터링 안내
- [x] 완료
- **소속 기능**: F-004
- **영역**: 오케스트레이터
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-pilot-project-loop/SKILL.md`
- **작업 내용**: 파이프라인/디스패치 절(`:291-303` 인근)에 `oppl-monitor <task_folder>`로 진행 현황 관측 안내 1~2줄(AGENT.md 규약 v2 포인터). 변경이력 067.
- **완료 기준**: 모니터링 안내 문구·포인터 존재, 변경이력 행.
- **테스트**: TS-013
- **실행 방법**: sub-agent
- **의존**: Step 5

#### Step 9: install 재배포 + 동작 실증 (실 디스패치·E2E)
- [x] 완료
- **소속 기능**: F-005
- **영역**: 배치
- **agent**: opal-task-agent
- **파일**: `tasks/067-260717-opd-루프액션-스트림-모니터링/samples/`
- **작업 내용**:
  - **(0) [선두 필수] install 재배포 + 배포본 검증** — `./scripts/install-mac.sh` 실행(066 선례: TEST 단계 배포 후 실증). 배포 후 검증: `~/.opal/tools/oppl-monitor/run.sh <folder>` 실행 가능(+x)(TS-014), `grep`으로 `~/.opal/tools/opal-agent/opal_agent.py`에 stream 경로 반영·`~/.opal/agents/opal-loop-action-agent/AGENT.md`에 규약 v2(events.jsonl·§운행 일지) 반영 확인. ([MUST] `~/.opal/` 직접 편집 없이 소스→install 경유, D-9·D-11.)
  - **(a) stream 모드 직접 실측(TS-005, 선행)** — `run.sh --stream … > events.jsonl`로 events.jsonl 실생성·마지막 줄 result·증분 성장 관측(H-4).
  - **(b) [필수] 루프 액션 에이전트 실 디스패치 1회(TS-015)** — 배포본·규약 v2 기준 066 S-8급 슬라이스에 루프 액션 에이전트를 1회 실제 디스패치 → 비동기 축 events.jsonl + `.oppl-run/journal.md` **실생성** 관측(§3.5.2 (a)). fixture/stream 대체는 Pass로 인정 안 함.
  - **(c) oppl-monitor 상태 판정 실증(TS-016, TS-008~TS-012)** — 정상/진행중/exit2/blocked 4 fixture + (b) 실 디스패치 산출물로 oppl-monitor 렌더·`--json`·blocked 표시 실측. TEST-SCENARIO PASS 증거 기록.
- **완료 기준**: (0) 재배포 후 배포본 검증 통과(TS-014), (a) TS-005 PASS, (b) 실 디스패치에서 events.jsonl·journal.md 실생성(TS-015 유일 경로), (c) TS-016·상태 구분·blocked 표시 관측.
- **테스트**: TS-014(재배포 검증), TS-005, TS-008~TS-012, TS-015, TS-016
- **실행 방법**: sub-agent
- **의존**: Step 6, 7, 8 (전 소스 변경 완료 후 재배포)

#### Step 10: docs/ 갱신 (PROJECT.md Project Loop 컴포넌트 표)
- [x] 완료
- **소속 기능**: 문서
- **영역**: 문서
- **agent**: PM 직접
- **파일**: `docs/PROJECT.md`, (필요 시) `docs/ARCHITECTURE.md`
- **작업 내용**: 새 도구(oppl-monitor) 도입 반영 — PROJECT.md Project Loop 컴포넌트 표에 oppl-monitor 행 추가(선택), ARCHITECTURE.md Observability/oppl 서술에 관측 도구 1줄. 변경이력 067. (갱신 대상 판단: 새 도구·관측 구조 도입 → PROJECT/ARCHITECTURE, plan-guide docs 갱신 규칙.)
- **완료 기준**: 신규 도구가 프로젝트 문서에 반영 + 변경이력.
- **테스트**: 산출물 검사
- **실행 방법**: direct (PM)
- **의존**: Step 9

### 4.3 병렬/순차 판별 근거
| 관계 | 근거 |
|------|------|
| Step 1 → Step 2 | 동일 도구, 코드 확정 후 테스트/문서 |
| Step 1 → Step 3 | AGENT.md v2가 events.jsonl 산출 계약(F-001)을 참조 |
| Step 3 → Step 4 | oppl-monitor 입력 계약(events.jsonl·journal 경로)이 규약 v2에서 확정 |
| Step 4 → Step 5 | run.sh가 oppl_monitor.py 호출 |
| Step 5 → Step 6·7·8 | 도구 존재 후 배포 스크립트/등록/안내 (6·7·8 상호 독립 — 병렬 가능) |
| Step 6·7·8 → Step 9 | 전 소스 변경(opal_agent·AGENT.md v2·oppl-monitor·install)이 완료돼야 Step 9 (0)에서 `install-mac.sh` 재배포가 유효 — 재배포는 배포본 검증(TS-014)·루프 액션 에이전트 실 디스패치(TS-015)의 전제(066 선례: 배포 후 실증) |
| Step 9 (0) → Step 9 (b) | 배포본(AGENT.md v2·opal-agent stream·oppl-monitor)이 있어야 루프 액션 에이전트 실 디스패치가 규약 v2로 동작 |
| Step 9 → Step 10 | 실증 확정 후 docs/ 반영 |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA
| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | stream `--verbose` 자동 부착 | TS-001 | build_invocation cmd에 stream-json+verbose 동시 |
| F-001 | stream 5필드 last-line 추출 | TS-002 | 5필드 정확 추출 |
| F-001 | 기존 --json 경로 회귀 무 | TS-003 | 기존 스위트 전체 PASS |
| F-001 | 비-claude stream 명시 에러 | TS-004 | OpalAgentError |
| F-001 | events.jsonl E2E 증분 | TS-005 | 유효 JSONL·마지막 줄 result·증분 성장 |
| F-002 | 규약 v2 명문화 | TS-006 | events.jsonl·완료마커 불변·prompt·변경점 표 |
| F-002 | journal 규약 명문화 | TS-007 | 4컬럼·기록시점·append-only |
| F-003 | 066 실증 렌더 | TS-008 | 5축 상태·최근 이벤트(R-NEST) 정상 |
| F-003 | 상태 구분 표시 | TS-009 | error/running/done 구분 |
| F-003 | blocked 표시 | TS-010 | phase blocked + 배너 |
| F-003 | --json/에러계약 | TS-011 | 유효 JSON / `ok:false`+exit 1 |
| F-003 | --watch 상한 종료 | TS-012 | 주기 재렌더 + 상한 종료 |
| F-004 | 레지스트리·변경이력 | TS-013 | 2곳 등록 + 067 이력 |
| F-004 | install 실행 가능 | TS-014 | Step 9 (0) 재배포 후 `~/.opal/tools/oppl-monitor/run.sh` 실행(+x) + AGENT.md v2·opal-agent stream grep 반영 |
| F-005 | 루프 액션 에이전트 실 디스패치 실생성 | TS-015 | **실 디스패치 1회(배포본·규약 v2)**에서 비동기 축 events.jsonl + journal.md 실생성 (fixture/stream 대체 불가) |
| F-005 | oppl-monitor 상태 판정 실증 | TS-016 | 4 fixture(정상/진행중/exit2/blocked)로 렌더·상태 구분·blocked 표시 |

### 5.2 회귀 테스트
- [ ] 기존 `test_opal_agent.py` 전체 PASS (json/text·마커 3-way·상호배타 baseline, H-3)
- [ ] 066 실증 산출물(`samples/T01/.oppl-run/` 5축 3-분리+session.json) 구조 하위호환 — monitor가 v1 result.json 축도 렌더
- [ ] [066계승] 완료 마커=exitcode 존재 판정 불변 (H-10)
- [ ] [065/066계승] H-9 2원화·blocked 7종·3-SSOT·결과 6필드 계약 불변(문서 개정이 계약 미접촉)

### 5.3 코드/문서 품질
- [ ] 프로젝트 컨벤션 준수 — Python snake_case 파일·kebab-case 폴더(D-9), @header 블록(D-9)
- [ ] 변경 문서 전부 변경이력 067 행 (일시 KST·semver, D-9)
- [ ] 표준 라이브러리만 사용(opal_agent stream·oppl_monitor) — 신규 의존성 없음
- [ ] 인용/근거 문서화 (citation-rules)

### 5.4 보안
- [ ] [MUST] `--dangerously-skip-permissions` 미사용 (전 축·stream 포함, [066계승] D-3)
- [ ] 구독 로컬 claude -p 유지 — API키·SDK 미사용 (D-7)
- [ ] oppl-monitor는 읽기 전용(파일 read만, .oppl-run/ 쓰기 없음)
- [ ] 하드코딩 토큰/시크릿 없음 / `~/.opal/` 직접 편집 없음(소스만 수정, D-9·D-11)

---

## 6. 복잡도 판별
| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 10개 | 복잡 |
| 변경 파일 수 | 9개(신규 3·수정 6) | 복잡 |
| 모듈 범위 | 다중(도구·에이전트·오케스트레이터·문서·배치) | 복잡 |
| 작업 유형 | 신규 도구 + 실행 경로 개조 | 복잡 |
| 외부 의존성 | 신규 도구(oppl-monitor) + claude stream-json | 복잡 |
| **실행 모드** | **복잡** | |

---

## 7. 실행 아키텍처 (복잡 모드)

### C-1. 에이전트 토폴로지
- 전 Step Framework 영역 → `opal-task-agent`(PROJECT.md §프로젝트 구성 매핑). 파일 충돌 방지: 동일 파일 수정 Step은 순차(Step1→2 opal_agent 도구, Step4→5 oppl-monitor 도구).
- Batch 1: Step 1 (opal_agent 코어)
- Batch 2: Step 2, Step 3 (F-001 테스트/문서 ∥ F-002 규약 — 독립 파일, 병렬 가능)
- Batch 3: Step 4 → Step 5 (oppl-monitor, 순차)
- Batch 4: Step 6, 7, 8 (배포·등록·안내 — 독립 파일, 병렬 가능)
- Batch 5: Step 9 (E2E 실증)
- Batch 6: Step 10 (docs, PM 직접)

### C-2. 스킬 요구사항
- 기존 스킬 매칭: T1(op-dev-plan) 불요(본 PLAN이 산출). EXECUTE는 op-dev-execute 프로세스 준용. 신규 스킬 갭 없음(도구·문서 작업, 인라인 지침으로 충분).

### C-3. 도구 요구사항
- CLI: claude(`--output-format stream-json --verbose` 실측 2.1.212), python(`~/.opal/.venv`). MCP·신규 패키지 없음.
- 검증 도구: `python -m unittest`/`py_compile`, `bash -n`, `./scripts/install-mac.sh`.

### C-4. 테스트 전략
- 기능 테스트: TS-001~TS-016 (opal-test-agent — BE/유닛 모드 opal_agent, 통합 모드 oppl-monitor).
- 회귀: `test_opal_agent.py` 전체(§5.2).
- 코드 품질: py_compile·bash -n·@header·변경이력.
- 보안: skip-permissions 미사용·읽기전용·시크릿 스캔(§5.4).
- 실증(R-6): Step 9 E2E — stream events.jsonl·journal 실생성·monitor 렌더·blocked.

---

## 8. 기술 컨텍스트

### 8.1 기술 스택
| 영역 | 기술 | 적용 스킬/원칙 |
|------|------|----------|
| 도구 개조 | Python 3.10+ (표준 라이브러리 `subprocess.Popen`) | 무의존성(README §전제) |
| 신규 도구 | Python 3.10+ (`json/argparse/pathlib/os/time/datetime`) | OPAL run.sh 래퍼 관례 |
| 실행기 | Claude Code CLI 2.1.212 (`-p --output-format stream-json --verbose`) | ANALYSIS §2 실측 |
| 규약 문서 | Markdown | AGENT.md v2·journal·tools.md·SKILL |
| 배포 | Bash (install-mac.sh cp -Rf·chmod) | 도구 배포 관례 |

### 8.2 사용 MCP
| MCP | 조회 결과 요약 |
|-----|--------------|
| (해당 없음) | claude CLI stream-json은 공식 문서 미비 — 실측이 유일 근거(ANALYSIS §2.6, TASK 지시 원칙). context7/WebSearch 대상 아님 |

### 8.3 참조 문서 (설계 결정 근거)
| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-0 | 기획 | TASK.md | `tasks/067-…/TASK.md` | 요구사항 R-1~R-6·제약·PLAN 필수 결정 8종 |
| D-1 | 설계 | ANALYSIS.md | `tasks/067-…/ANALYSIS.md` | 개조 지점·stream 실측·리스크 8건(R-ASYNC/R-EVSCHEMA/R-WATCH 등) |
| D-2 | 소스 | opal-agent README | `opal/tools/opal-agent/README.md` | CLI 옵션·배포 경로·stream 절 추가 대상 |
| D-3 | 설계 | 루프 액션 에이전트 | `opal/agents/opal-loop-action-agent/AGENT.md` | 규약 v1.1·완료마커·allowedTools·blocked 계약 |
| D-4 | 소스 | opal_agent.py | `opal/tools/opal-agent/opal_agent.py` | `_run`·ClaudeAdapter·CLI 개조 본체 |
| D-5 | 실증 | 066 샘플 | `tasks/066-…/samples/T01-정상슬라이스/.oppl-run/` | monitor 입력 실데이터(3-분리 5축·prompt.txt·result.json 원문) |
| D-6 | 소스 | 066 tests | `opal/tools/opal-agent/tests/test_opal_agent.py` | 회귀 baseline 스위트 구조 |
| D-7 | 기록 | 구독 인증 메모리 | `memory/console-brain-subscription-auth.md` | API키·SDK 금지 제약 |
| D-8 | 설계 | 도구 레지스트리 | `opal/core/references/tools.md`, `opal/core/references/opal-harness.md` §9 | oppl-monitor 등록 대상 |
| D-9 | 설계 | 코드 컨벤션 | `docs/CONVENTIONS.md` | 네이밍·@header·변경이력·배포 경계 [MUST] |
| D-10 | 설계 | 루프 제어 | `opal/skills/opal-pilot-project-loop/references/loop-control.md` §2 | 재시도 수치 비복제 |
| D-11 | 배치 | install 스크립트 | `scripts/install-mac.sh:1110-1180` | 도구 배포·chmod 관례 |
| D-12 | 설계 | 오케스트레이터 | `opal/skills/opal-pilot-project-loop/SKILL.md` | 모니터링 안내 정합 대상 |

---

## 9. 리스크 및 대응 (기능-리스크 연결)
| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| R-1 | [066계승] stream 마지막 줄 5필드 붕괴(R-H — 이벤트 스키마 환경 의존) | F-001 | P0 | 최소 보장 집합(init→assist/user→result)만 의존·마지막 result 줄만 파싱·E2E 실측(H-1) |
| R-2 | `--verbose` 미부착 exit 1 | F-001 | P0 | build_invocation에서 무조건 자동 부착·단위 검증(H-2) |
| R-3 | 기존 --json 경로 회귀 | F-001 | P1 | 디스패치 분기로 격리·기존 스위트 회귀 실행(H-3) |
| R-4 | stdout 버퍼링으로 증분 미기록 | F-001 | P1 | Popen line-buffered + flush passthrough·실행 중 tail 관찰(H-4) |
| R-5 | R-NEST 중첩 파싱·미보장 타입 | F-003 | P2/P1 | content[] 역순 순회·미보장 타입 degrade(H-5·H-6) |
| R-6 | 상태 오판(blocked↔running) | F-003 | P1 | 6상태 표 판정 로직·fixture 검증(H-7) |
| R-7 | --watch 미종료 | F-003 | P2 | 상한 3종(terminal·watch-timeout·interrupt)(H-8) |
| R-8 | install 권한/배포 누락 | F-004 | P1 | run.sh +x 커밋 + 개별 chmod 블록·install 후 실행 검증(H-9) |
| R-9 | [066계승] 완료 마커 불변 위반 | F-002 | P0 | 규약 v2에서 exitcode 마커 문구 불변 유지·문서 계약 검토(H-10) |
| R-10 | [범위] opal-agent 미등록에 monitor가 의존 서술 | F-003 | 낮음 | oppl-monitor만 등록·opal-agent는 소스 경로로만 지시(R-REG) |

---

## 변경이력
| 날짜 | 버전 | 변경 내용 |
|------|------|----------|
| 2026-07-17 19:28 | v1.0 | 최초 작성 — F-001~F-005 5기능·10 Step·복잡 모드. 핵심 결정 9종(R-ASYNC 호출측 리다이렉트/R-EVSCHEMA 원본 기록/R-VERBOSE 자동부착/R-WATCH 폴링+상한/R-CHMOD 블록 추가/R-COMPAT 회귀 스위트/R-REG oppl-monitor만/화면 6상태·4컬럼/journal 4컬럼 append-only). 리스크 가설 10건(H-1~H-10, 066계승 접두 구분). TS-001~TS-016 |
| 2026-07-17 19:48 | v1.1 | PM Gate Fail 2건 보완 (1/3) — ① 완료기준② 완화 정정: Step 9·§3.5.2·TS-015를 "루프 액션 에이전트 실 디스패치 1회(배포본·규약 v2) 필수 — events.jsonl·journal.md 실생성이 TS-015 유일 Pass 경로"로 강화, stream 직접 실측(TS-005)은 선행 검증 분리, 4 fixture는 oppl-monitor 상태 판정(TS-009~012·TS-016) 한정으로 역할 분리. ② 배포 절차 부재 정정: Step 9 (0) 선두에 `install-mac.sh` 재배포 + 배포본 검증(run.sh 실행·AGENT.md v2·opal-agent stream grep) 명시, TS-014를 이 지점 매핑(Step 6은 산출물 검사로 조정), §4.3 의존 근거 갱신 |
