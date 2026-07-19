# ANALYSIS: oppl 계약 접합면 검증 강화 — 표면 인벤토리·커버리지·전수 conformance·목 금지·여정 스모크

> 작성일: 2026-07-18
> 입력: TASK.md
> 출력: ANALYSIS.md

## 0. 참조 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | oppl 오케스트레이터 본문 | `opal/skills/opal-pilot-project-loop/SKILL.md` | D4/D5/D7/L✓/병렬 실행 절 개정 대상 |
| D-2 | 설계 | CONTRACT 거버넌스 가이드 | `opal/skills/opal-pilot-project-loop/references/contract.md` | §2.2 기계검증절에 표면 인벤토리 의무 추가 |
| D-3 | 설계 | 검증 가이드 | `opal/skills/opal-pilot-project-loop/references/verification.md` | §2.1 conformance 분모 정의 + §3 목 금지 규칙 추가 |
| D-4 | 설계 | 여정·플로우 가이드 | `opal/skills/opal-pilot-project-loop/references/journey-flow.md` | 여정 스모크 게이트 규칙 추가 |
| D-5 | 소스 | backlog-tool | `opal/tools/backlog-tool/backlog_tool.py`, `README.md`, `schema/backlog.schema.json`, `tests/test_backlog_tool.py` | covers 필드·커버리지 게이트 구현 대상 |
| D-6 | 소스 | test-tool | `opal/tools/test-tool/test_tool.py`, `lib/scenario.py`, `README.md`, `schema/test-scenario.schema.json`, `tests/test_scenario.py` | fidelity 필드·게이트 구현 대상 |
| D-7 | 설계 | OPAL 헌법 | `~/.opal/PRINCIPLES.md` §4 | "Enforce, don't just advise" 원칙 — 본 태스크의 설계 근거 |
| D-8 | 설계 | 하네스 공통 | `opal/core/references/opal-harness.md` §1 | Guards·자동 루핑 제약과의 정합 확인 |
| D-9 | 설계 | opal-evaluator-agent 정의 | `opal/agents/opal-evaluator-agent/AGENT.md` | D6/G 판정 항목 확장 대상 |
| D-10 | 설계 | opal-loop-action-agent 정의 | `opal/agents/opal-loop-action-agent/AGENT.md` | T1~T4a 내부 디스패치 프롬프트 확장 영향 |
| D-11 | 설계 | citation-rules.md | `opal/core/references/harness/citation-rules.md` | 근거 인용 규칙 §0/§2/§7 |
| D-12 | 소스 | install-mac.sh | `scripts/install-mac.sh:1054-1200` | 배포 메커니즘(`install_dir` 전체 디렉토리 덮어쓰기) |
| D-13 | 설계 | brain — 3-SSOT 축 분리 | `.opal/brain/pages/concept/oppl-3-ssot-tool-gated-separation.md` | 축 분리 원칙의 정확한 적용 범위 확인 |
| D-14 | 설계 | brain — scenario red_confirmed 갭 | `.opal/brain/pages/concept/oppl-scenario-red-confirmed-gap.md` | 혼합 트랙(RED 필요/불필요) 선례 — fidelity 필드 설계에 참고 |
| D-15 | 설계 | brain — 2-루프 오케스트레이터 | `.opal/brain/pages/concept/oppl-two-loop-orchestrator.md` | oppl 전체 구조 배경 |

> 인용 형식: `opal/core/references/harness/citation-rules.md` §2 참조.

---

## 1. 기존 코드 분석

### 1.1 관련 파일 목록

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| `opal/tools/backlog-tool/backlog_tool.py` | backlog.json SSOT CLI (7서브명령) | O — `add-task`/`update-task`에 `--covers` 추가(R-2), 신규 커버리지 게이트 서브명령 또는 `done-check` 확장(R-3/R-4a) | `backlog_tool.py:596-607`(add-task argparse), `backlog_tool.py:622-633`(update-task argparse), `backlog_tool.py:335-355`(cmd_add_task 본문), `backlog_tool.py:512-527`(cmd_done_check) |
| `opal/tools/backlog-tool/schema/backlog.schema.json` | backlog.json JSON Schema (참조용, 런타임 미검증) | O — task 항목에 `covers` optional 필드 추가, `schema_version` 1.0→1.1 검토 | `backlog.schema.json:60-107`(tasks[].properties, `additionalProperties: false`) |
| `opal/tools/backlog-tool/README.md` | 사용 설명서 | O — 신규 옵션·서브명령·에러코드 문서화 | `README.md:55-78`(add-task), `README.md:189-204`(에러코드 표) |
| `opal/tools/backlog-tool/tests/test_backlog_tool.py` | 단위 테스트(9 TestCase) | O — covers/coverage-gate 신규 테스트 케이스, 기존 회귀 0 유지 | `test_backlog_tool.py:136-537` |
| `opal/tools/test-tool/lib/scenario.py` | test-scenario.json scenario-* 5서브명령 핸들러 | O — `scenarios[].fidelity` 필드, `_normalize_scenario` 기본값, `scenario-lock`/신규 게이트에 fidelity 미달 거부 로직 | `scenario.py:109-131`(_normalize_scenario), `scenario.py:187-214`(cmd_scenario_lock), `scenario.py:53-59`(SCENARIO_ERROR_CODES) |
| `opal/tools/test-tool/test_tool.py` | test-tool 진입점(resolve/check/unit/integration) | 변경 불필요(scenario-* 로직과 완전 격리 — `test_tool.py:37-40` import 구조) | `test_tool.py:1-25`(모듈 헤더 "본 모듈로 완전 격리") |
| `opal/tools/test-tool/schema/test-scenario.schema.json` | test-scenario.json JSON Schema (참조용) | O — `scenarios[].fidelity` enum(`mock\|real-http\|real-usage`) 필드 추가, `required` 배열 갱신 여부 결정 | `test-scenario.schema.json:31-70`(scenarios[].items) |
| `opal/tools/test-tool/README.md` | 사용 설명서 | O — fidelity 필드·신규 에러코드 문서화 | `README.md:239-256`(에러 코드 표) |
| `opal/tools/test-tool/tests/test_scenario.py` | scenario-* 단위 테스트 | O — fidelity 신규 케이스, 회귀 0 유지 | `test_scenario.py:1-380` |
| `opal/skills/opal-pilot-project-loop/SKILL.md` | oppl 오케스트레이터 본문 | O — D4/D5/D7/L✓/병렬 실행 절 개정 | `SKILL.md:204`(D4 CONTRACT 작성), `SKILL.md:206-211`(D5 백로그 생성), `SKILL.md:270-274`(L✓ 종료 판정), `SKILL.md:490-495`(병렬 실행 "통합 태스크 필수") |
| `opal/skills/opal-pilot-project-loop/references/contract.md` | CONTRACT 작성·거버넌스 가이드 | O — §2.2 기계검증절에 표면 인벤토리 필수 규칙, §2.1 경계에 origin 선언 규칙 | `contract.md:21-27`(§2.1 3파트), `contract.md:29-31`(§2.2 기계검증절) |
| `opal/skills/opal-pilot-project-loop/references/verification.md` | 검증 3-tier+2원화 가이드 | O — §1(신규, 충실도 사다리 정의)~§3 확장, §2.1 계약 conformance 행 갱신, §2.1 E2E(L3b) 행 갱신 | `verification.md:20-39`(§2.1 결정론 표), `verification.md:68-96`(§3 2원화) |
| `opal/skills/opal-pilot-project-loop/references/journey-flow.md` | USER_JOURNEY/FLOW 가이드 | O — 여정 스모크 게이트(§신규) + §5 확장 | `journey-flow.md:80-84`(§5 G게이트·검증 관계) |
| `opal/agents/opal-evaluator-agent/AGENT.md` | Evaluator 정의(D6/G 판정) | O — Phase1 Base 루브릭 표에 표면 완전성/auth/origin/스켈레톤 판정 항목 추가 | `AGENT.md:39-49`(Phase1 Base 루브릭 6차원), `AGENT.md:27-28`(target_artifacts 입력) |
| `opal/agents/opal-loop-action-agent/AGENT.md` | 루프 액션 에이전트 정의(T1~T5+G) | 검토 필요 — T2 fidelity 요구치 주입, T4a scenario-mark 앞뒤 문맥(직접 코드변경 없음 가능성 높음, PLAN에서 확정) | `AGENT.md:128-146`(파이프라인 흐름 2~5단계) |
| `scripts/install-mac.sh` | 설치 스크립트 | 변경 불필요(EXECUTE 후 별도 승인 — 범위 외) — `opal/tools/`·`opal/skills/` 전체 디렉토리 덮어쓰기 방식이라 신규 서브명령/필드가 자동 포함됨 | `install-mac.sh:1110-1113`(도구 install_dir), `install-mac.sh:1059-1070`(스킬 install_dir) |

### 1.2 아키텍처 패턴

- **state-tool 패턴 복제**: backlog-tool은 `ok()`/`err()` 단일라인 JSON 헬퍼, `get_kst_datetime()`(date.js subprocess), 마크다운 마커 렌더/치환(`<!-- backlog:start/end -->`)을 state-tool에서 그대로 복제했다 (`backlog_tool.py:1-12` @header, `README.md:9`).
- **fcntl 배타 락 read-modify-write**: `mark`/`add-task`/`update-task`는 `load_backlog_json_locked()` → `save_and_unlock()` 쌍으로 동시 쓰기를 직렬화한다 (`backlog_tool.py:165-193`). 신규 커버리지 게이트가 backlog.json을 쓰기(write)하지 않고 읽기 전용 판정만 한다면 이 락 패턴이 불필요할 수 있다 — R-3 게이트 설계 시 판단 필요.
- **ERROR_CODES SSOT + err() 헬퍼**: 모든 에러는 `ERROR_CODES` 딕셔너리 키를 통해 `{ok:false, command, error, message}` 단일라인 JSON으로 응답한다(`backlog_tool.py:42-54`). 신규 에러코드(`surface_uncovered`, `integration_task_missing`)는 이 딕셔너리에 추가하는 방식으로 확장한다.
- **test-tool은 완전 격리된 두 서브시스템**: `test_tool.py`(resolve/check/unit/integration, 4서브명령)와 `lib/scenario.py`(scenario-*, 5서브명령)는 별도 `ERROR_CODES`/`SCENARIO_ERROR_CODES` 딕셔너리를 가지며 exit code 대역도 분리되어 있다(0~7 vs 8~12) — `scenario.py:1-37` @header가 이 격리를 명문화한다. fidelity 게이트는 `scenario.py` 내부에 신설하는 것이 기존 패턴과 정합적이다.
- **spec존/result존 분리**: test-scenario.json은 `red_confirmed`(spec존, RED-first 동결 대상)와 `result`(result존, 구현 후 기록)를 분리한다(`test-scenario.schema.json:37-70`). `fidelity`는 시나리오의 "요구 충실도"를 나타내는 필드로, 의미상 spec존(작성 시점에 결정)에 속한다 — RED-first 동결(`scenario-lock`) 이전에 고정되어야 하는 필드다.
- **RED-first tool-gate 선례**: `scenario-lock`은 전 시나리오 `red_confirmed==true`가 아니면 `red_not_confirmed`(exit 8)로 거부한다(`scenario.py:187-214`). 이 "전부 게이트(all-or-nothing gate)" 패턴은 fidelity 게이트 설계의 직접 선례이나, `oppl-scenario-red-confirmed-gap.md`(task:061 재발 사례)가 지적하듯 **혼합 트랙(RED 필요/불필요 시나리오 공존) 문제를 그대로 물려받을 위험**이 있다(§5 하위 호환·회귀 리스크에서 상술).
- **markdown 미러는 도구 렌더 전용 + 손편집 금지**: BACKLOG.md는 `<!-- backlog:start/end -->` 마커 구간만 도구가 재렌더하고 마커 밖 자유 텍스트는 보존한다(`backlog_tool.py:218-260`). `covers` 필드가 BACKLOG.md 표에 렌더되려면 `render_backlog_table()`(`backlog_tool.py:200-215`)의 컬럼 구성을 확장해야 한다.

### 1.3 의존성 맵

```
backlog_tool.py
  └─ (표준 라이브러리만: argparse/fcntl/json/os/pathlib/subprocess/sys)
  └─ subprocess → ~/.opal/tools/date/date.js (KST 시점)
  └─ (schema/backlog.schema.json은 참조용 — 런타임 import/검증 없음)

test_tool.py
  └─ lib/resolver.py, lib/runner.py, lib/e2e_adapter.py (resolve/check/unit/integration 전용)
  └─ lib/scenario.py (scenario-* 전용, add_scenario_subparsers/SCENARIO_DISPATCH만 test_tool.py에 노출 — `test_tool.py:40,246-247`)
  └─ (schema/test-scenario.schema.json도 참조용 — 런타임 미검증)

opal-pilot-project-loop/SKILL.md
  └─ references/{contract.md, verification.md, journey-flow.md, loop-control.md} (인라인 참조 방식 — 본문에 "참조" 문구만 있고 내용은 각 파일이 SSOT)
  └─ backlog-tool run.sh (D5/L0/L∞/L✓ 호출)
  └─ test-tool run.sh scenario-* (T2/T4a 호출)
  └─ opal-loop-action-agent (Loop 2 태스크당 1회 디스패치) → 내부적으로 opal-evaluator-agent(G)/opal-test-agent(T2 red, T4a)/생성자(T1,T3)/checker(T4b) 디스패치
```

- **backlog.json ↔ test-scenario.json 무참조 확인**: `backlog_tool.py` 전체(661줄)에 `test-scenario`/`scenario`라는 토큰이 등장하지 않음(Grep 결과 미검출) — 축 분리가 코드 수준에서 실제로 지켜지고 있다. R-3/R-4 설계 시 이 무결성을 깨지 않아야 한다(§4에서 상술).
- **CONTRACT.md는 3-SSOT 밖의 문서**: `opal-3-ssot-tool-gated-separation.md`(D-13)는 3-SSOT를 `backlog.json`/`state.json`/`test-scenario.json` 3종으로만 한정한다. CONTRACT.md는 Loop 1 설계 산출물(Planner 작성, Evaluator 리뷰)이지 3-SSOT의 일원이 아니다 — 따라서 "backlog-tool이 CONTRACT.md(또는 그 파생 구조화 자산)를 읽는 것"은 3-SSOT 축 분리 규칙(`test-scenario.json 참조 금지`)의 직접 위반 대상이 아니다. 다만 §4에서 별도 설계 긴장(마크다운 파싱 결합도, 크로스-SSOT 집계)을 다룬다.

### 1.4 테스트 현황

- `backlog-tool`: `tests/test_backlog_tool.py` 537줄, 9개 TestCase(Init/SelectNext/MarkTransition/DoneCheck/ResultContract/BacklogMdMirror/ConcurrentMark/UpdateTask 등, `test_backlog_tool.py:136-537`) — unittest 기반, venv python 실행 가정. `covers`/커버리지 게이트 신규 테스트는 이 파일에 새 TestCase로 추가하는 것이 기존 컨벤션과 정합적이다.
- `test-tool`: `tests/test_scenario.py`(380줄) + `tests/test_test_tool.py`(998줄) — scenario-* 5서브명령과 resolve/check/unit/integration 4서브명령이 파일 단위로도 분리되어 있다. fidelity 신규 케이스는 `test_scenario.py`에 추가한다.
- 두 도구 모두 표준 라이브러리(`unittest`)만 사용하며 pytest 등 외부 러너 도입 여부는 `~/.opal/.venv` 환경에 의존 — 회귀 0 기준은 "기존 케이스 전부 pass 유지"로 명확히 측정 가능하다.

---

## 2. 외부 조사 결과 (해당 시)

R-4/R-8이 언급하는 "OpenAPI(스웨거) 기반 conformance 검증"은 본 태스크 범위에서 신규 외부 라이브러리 도입을 확정하지 않는다(TASK.md 제약: "표준 라이브러리만 import(신규 패키지 도입 금지, T-11 원칙 준용)" — `backlog_tool.py:14` 주석 및 `test_tool.py:20-21` [MUST] "러너 재구현 금지"). 따라서 본 ANALYSIS에서는 OpenAPI 생태계 도구(schemathesis, dredd, openapi-diff 등) 조사를 PLAN 단계로 이연하고, 여기서는 프로젝트 내부 설계 대안 비교(§7)에 집중한다. PLAN 단계에서 실제 OpenAPI 검증 도구를 확정하면 context7/WebSearch 조사가 필요하다.

### 2.1 라이브러리/API 조사
- 해당 없음(본 ANALYSIS 단계에서는 신규 외부 라이브러리 확정 보류).

### 2.2 버전 호환성
- 해당 없음.

---

## 3. 영향 범위

### 3.1 직접 영향

- `opal/tools/backlog-tool/backlog_tool.py`, `schema/backlog.schema.json`, `README.md`, `tests/test_backlog_tool.py`
- `opal/tools/test-tool/lib/scenario.py`, `schema/test-scenario.schema.json`, `README.md`, `tests/test_scenario.py`
- `opal/skills/opal-pilot-project-loop/SKILL.md`
- `opal/skills/opal-pilot-project-loop/references/{contract.md, verification.md, journey-flow.md}`
- `opal/agents/opal-evaluator-agent/AGENT.md`

### 3.2 간접 영향

- `opal/agents/opal-loop-action-agent/AGENT.md` — T1(생성자가 표면-fidelity 요구치를 인지해야 함)·T2(scenario-init 시 fidelity 필드 채움)·G(Evaluator가 확장된 판정 항목 수신)·T4a(scenario-mark 후 fidelity 게이트 통과 확인) 프롬프트 문맥 확장 필요 — TASK.md 범위 표에 명시적으로는 없으나 R-1/R-5/R-8의 실행 경로상 영향을 받는다. PLAN에서 변경 여부를 결정해야 한다(§7 미해결 질문).
- `opal/skills/opal-pilot-project-loop/references/loop-control.md` — 신규 게이트(surface_uncovered/integration_task_missing/fidelity 미달)가 §7 "에러 처리(복구가능 vs 하드블로커)" 분류표에 어느 범주로 들어가는지 명시가 필요할 수 있다(TASK.md D-8 범위 밖으로 보이나 정합성 확인 필요).
- `docs/PROJECT.md` — Project Loop 표의 backlog-tool/test-tool 설명(§주요 컴포넌트) 갱신 필요(R-7 변경이력 의무의 연장, CLOSE 단계 통상 절차).
- 실전 적용 중이던(또는 예정된) oppl 프로젝트의 기존 `backlog.json`(covers 미사용)·`test-scenario.json`(fidelity 미지정) — 하위 호환 검증 대상(§5).

### 3.3 영향 범위 요약

- [ ] DB 스키마 변경 — 해당 없음
- [x] API 인터페이스 변경 — backlog-tool CLI(신규 `--covers` 옵션, 신규 서브명령 후보), test-tool CLI(scenario-init `--scenarios` JSON 스키마에 fidelity 필드) 변경. 둘 다 하위 호환 필수(TASK.md 제약)
- [ ] 설정/환경변수 변경 — 해당 없음(확인된 범위 내)
- [x] 빌드/배포 파이프라인 변경 — 해당 없음, 단 install-mac.sh 재배포는 EXECUTE 완료 후 필요(§6)

---

## 4. 핵심 발견 사항

1. **R-3/R-4 게이트는 3-SSOT 축 분리의 "문자"는 위반하지 않지만 "정신"과 긴장한다.** 3-SSOT 축 분리 규칙은 문자 그대로 "`backlog.json`이 `test-scenario.json`을 참조하지 않는다"이며(`SKILL.md:44` "세 SSOT는 서로 참조하지 않는다(축 분리)", D-13 brain 페이지), CONTRACT.md는 3-SSOT의 일원이 아니므로 backlog-tool이 CONTRACT.md 파생 표면 인벤토리를 읽는 것 자체는 규칙 위반이 아니다. 그러나 R-4(표면×결과 매트릭스 all green 판정)는 "표면이 어느 태스크(backlog.json)에서 어떤 결과(test-scenario.json result존)로 검증되었는가"를 교차 판정해야 하므로, **이 판정을 수행하는 코드가 backlog.json과 test-scenario.json을 동시에 읽어야 한다**. `backlog_tool.py` 내부에 이 로직을 넣으면 backlog-tool이 test-scenario.json을 직접 파싱하게 되어 축 분리 규칙의 정신(각 도구는 자신의 SSOT만 소유)을 흐릴 수 있다. → PLAN에서 "제3의 읽기 전용 집계 지점"(예: 신규 경량 검사 스크립트 또는 오케스트레이터/루프 액션 에이전트가 양쪽 도구 출력을 조합)으로 분리할지, backlog-tool 내부에 넣을지 결정 필요(§7 미해결 질문).
2. **표면 인벤토리 SSOT 위치가 확정되지 않으면 R-2/R-3/R-1이 모두 불안정하다.** `add-task --covers <surface-id>`(R-2)가 유효하려면 "surface-id"의 정의역(表面 인벤토리)이 먼저 어딘가에 구조화되어 있어야 한다. 현재 CONTRACT.md는 순수 마크다운이고(`contract.md` 전체에 JSON/YAML 블록 없음), 이를 backlog-tool이 파싱하려면 마크다운 표 파서가 필요하다 — 이는 `docs/CONVENTIONS.md` 계열 문서를 md 그대로 사람이 읽는 기존 패턴과 다른 요구(기계가독)다. §7에서 (a)/(b) 대안을 비교한다.
3. **fidelity 게이트는 `scenario-lock`의 "전부-아니면-전무" 패턴을 그대로 물려받으면 task:061 재발 사례를 반복한다.** `oppl-scenario-red-confirmed-gap.md`(D-14)가 명시적으로 기록한 교훈 — RED 필요/불필요 시나리오가 혼재할 때 `scenario-lock`이 전체 시나리오의 `red_confirmed==true`를 요구하는 전부-게이트라 혼합 트랙을 지원하지 못해 우회(SSOT 축소)가 발생했다. R-5(fidelity 게이트)도 동일 구조 위험을 안고 있다 — "이 시나리오는 real-usage가 필요하고 저 시나리오는 mock으로 충분하다"는 **시나리오별 요구 충실도(required_fidelity)와 실제 충실도(fidelity) 분리 설계**가 없으면 all-or-nothing 게이트가 다시 부적합해진다. brain 페이지가 제안한 `red_required` 필드 패턴(D-14 "정제된 후속 제안")을 fidelity 설계에도 유비 적용할 필요가 있다.
4. **backlog-tool·test-tool 모두 기존 서브명령·필드를 건드리지 않고 확장(additive)하는 패턴이 이미 검증되어 있다.** `update-task`(056 ADD-3)가 status를 인자에서 의도적으로 제외하고 기존 `mark` 전용 구조를 지키면서 신규 서브명령을 추가한 선례(`backlog_tool.py:429-441` 주석), `scenario-red`(056/ADD-1)가 기존 4서브명령과 완전 격리된 상태로 신규 exit code 대역(8~12)을 배정한 선례(`scenario.py:1-37`)는 R-2/R-3/R-5 구현이 회귀 0을 달성할 수 있는 구조적 근거다.
5. **install 배포는 opal/tools·opal/skills 디렉토리 전체를 `cp -Rf`로 덮어쓰는 방식**(`install-mac.sh:208-222` `install_dir()`, `install-mac.sh:1059-1070`, `1110-1113`)이라, 신규 서브명령·필드·문서 절 추가는 **기존 install 로직 변경 없이 자동으로 배포 대상에 포함**된다. 단, 신규 `.sh` 실행파일이 생기면(예: 커버리지 게이트가 별도 wrapper라면) `chmod +x` 등록 라인(`install-mac.sh:1174-1179` backlog-tool 선례)이 별도로 필요하다(§6).

---

## 5. 제약/리스크

| 항목 | 설명 | 심각도 | 근거 |
|------|------|--------|------|
| R-A | 3-SSOT 축 분리 정신과 R-3/R-4 교차 판정 로직의 설계 긴장(§4-1) — 잘못 구현하면 backlog-tool이 test-scenario.json을 직접 파싱하게 되어 "각 도구는 자신의 SSOT만 소유" 원칙을 흐릴 위험 | 높음 | `SKILL.md:44`, `.opal/brain/pages/concept/oppl-3-ssot-tool-gated-separation.md` §결정 내용 |
| R-B | fidelity 게이트가 `scenario-lock`과 동일한 전부-아니면-전무 구조를 물려받으면 task:061 재발 사례(혼합 트랙 lock 불가)가 반복될 위험 | 높음 | `.opal/brain/pages/concept/oppl-scenario-red-confirmed-gap.md` §재발 사례(task:061), `scenario.py:187-214` |
| R-C | 표면 인벤토리 SSOT 위치 미확정 상태에서 `--covers <surface-id>`를 먼저 구현하면 surface-id 정의역이 붕 뜬 채로 구현될 위험(순서 의존성 — R-1 선행 후 R-2 구현이 안전) | 중간 | TASK.md 요구사항 R-1·R-2 서술(선후 관계 명시 없음), `contract.md` §2.2(현재 기계검증절에 표면 인벤토리 없음) |
| R-D | CONTRACT.md를 backlog-tool이 마크다운 그대로 파싱하는 방식을 택하면, 마크다운 표 포맷이 조금만 바뀌어도 파서가 깨지는 결합도 위험 — `docs/CONVENTIONS.md` 등 기존 md 문서는 전부 "사람이 읽고 AI가 Read하는" 용도이지 "도구가 파싱하는" 용도가 아니었다(선례 부재) | 중간 | `opal/tools/backlog-tool/`, `opal/tools/test-tool/` 전체에 마크다운 파서 코드 없음(Grep 결과 미검출) |
| R-E | 기존 backlog.json(`covers` 없음)·test-scenario.json(`fidelity` 없음) 하위 호환 — schema는 참조용이라 런타임 강제가 없으므로 스키마 갱신 자체는 즉시 깨지지 않으나, 신규 게이트 로직이 필드 부재를 "거부"로 취급하면 기존 프로젝트가 즉시 깨진다 | 높음 | `backlog.schema.json:60-107`(런타임 미검증), `test-scenario.schema.json`(동일), TASK.md 완료기준 "회귀 0" |
| R-F | Evaluator(opal-evaluator-agent) Base 루브릭 확장(표면 완전성·auth·origin·스켈레톤) 항목은 전부 Likert/LLM 판정(prose 집행)이며 도구 게이트가 아니다 — PRINCIPLES.md §4 "Enforce, don't just advise"와 배치될 수 있다. R-1 AC 자체가 "D6 Evaluator 판정 기준에 명시된다"로 되어 있어 prose 집행을 인정하는 것으로 보이나, 사용자가 열거한 개선 5건(①~⑤) 표는 R-1을 "문서" 성격으로 분류하고 R-2/R-3/R-5는 "도구" 성격으로 분류했다(TASK.md 확정 방향 표) — 설계 결정과 정합 | 낮음(TASK.md가 이미 문서 성격으로 확정) | TASK.md "확정된 설계 방향" 표 ①행 "성격: 문서", `~/.opal/PRINCIPLES.md` §4 |
| R-G | `opal-loop-action-agent`가 내부에서 area 기반 생성자·test-agent에 fidelity 요구치를 전달하지 않으면, T2에서 test-agent(mode:red)가 mock 시나리오만 작성해도 게이트를 통과하는 사각지대가 생길 수 있음 — AGENT.md 변경 필요 여부가 TASK.md 명시 범위(변경 대상 표)에 없음 | 중간 | `opal/agents/opal-loop-action-agent/AGENT.md:128-146`, TASK.md "관련 문서" 표(D-5/D-6만 소스로 명시, agents/ 불포함) |
| R-H | fidelity/coverage 게이트 실패가 loop-control.md §7의 "복구가능 vs 하드블로커" 어느 쪽으로 분류되는지 문서에 아직 정의되지 않음 — 정의 없이 구현하면 루프 액션 에이전트/PM의 에스컬레이션 판단 기준이 불명확해짐 | 낮음 | `references/loop-control.md:100-108` §7 표(신규 에러코드 행 부재) |

---

## 6. install 배포 영향 목록 (EXECUTE 완료 후 별도 승인 대상 — 본 태스크 범위 외)

| 변경 | 배포 메커니즘 | 추가 조치 필요 여부 |
|------|--------------|------------------|
| `backlog_tool.py`(covers/커버리지 게이트) | `install-mac.sh:1110-1113` `install_dir("$opal_dir/tools", "$opal_home/tools")` — 디렉토리 전체 `cp -Rf` 덮어쓰기 | 불필요(기존 backlog-tool 배포 경로에 자동 포함). 단, 신규 서브명령이 별도 `.sh` 실행파일이면 `install-mac.sh:1174-1179`와 유사한 `chmod +x` 라인 추가 필요 |
| `schema/backlog.schema.json`, `README.md` | 동일 `install_dir` 경로 | 불필요 |
| `lib/scenario.py`(fidelity), `schema/test-scenario.schema.json` | 동일 `install_dir` 경로 (test-tool도 `opal/tools/` 하위) | 불필요 |
| `SKILL.md` + `references/*.md` (contract/verification/journey-flow) | `install-mac.sh:1059-1070` — 스킬 디렉토리별 `install_dir` + `strip_deploy_md_recursive`(변경이력 섹션 제거 후 배포) | 불필요. 단, 변경이력 표(R-7)는 배포본에서 제거되므로 반드시 소스(`opal/skills/...`)에 기록해야 함 — 배포본 직접 수정 금지 원칙과 이미 정합 |
| `opal/agents/opal-evaluator-agent/AGENT.md`(루브릭 확장), `opal/agents/opal-loop-action-agent/AGENT.md`(영향 시) | `install-mac.sh:1076-1102` — `opal/agents/` 디렉토리별 `install_dir` + 플랫폼별 서브에이전트 변환(`install-mac.sh:462` 이하 Claude/Cursor/Gemini/Codex 어댑터) | 불필요(어댑터는 AGENT.md 내용을 그대로 소비하는 구조 — `install-mac.sh:598-599` 헤더 마커 방식). 어댑터 변환 로직 자체는 변경 대상 아님 |
| `docs/PROJECT.md` 등 문서 레지스트리 | 배포 대상 아님(docs/는 install 대상에 포함되지 않음 — 프로젝트 자체 문서) | 불필요 |

> 배포 자체(install-mac.sh 실행)는 TASK.md 제약("CLOSE 후 별도 승인")에 따라 본 태스크 EXECUTE 범위에 포함하지 않는다.

---

## 7. 미해결 질문 (PLAN 전달용)

1. **표면 인벤토리 SSOT 형식 확정** — (a) CONTRACT.md 내 마크다운 표 + 커스텀 파서 vs (b) OpenAPI(YAML) 파일을 SSOT로 채택하고 CONTRACT.md가 참조. 캡틴이 (b)를 1순위 검토 지시(TASK.md "미확정" 행) — 아래 대안 비교 참조. PLAN에서 최종 확정 필요.
2. **R-3/R-4 교차 판정 로직의 소유 위치** — backlog-tool 내부 신규 서브명령 vs 별도 경량 집계 스크립트/오케스트레이터 로직. 3-SSOT 축 분리 정신 유지 방식을 PLAN에서 결정해야 한다(§4-1).
3. **fidelity 게이트가 `scenario-lock`과 통합될지, 별도 신규 서브명령(예: `scenario-fidelity-check`)으로 분리될지** — task:061 재발 사례(§4-3)를 고려하면 `required_fidelity`(요구)와 `fidelity`(실제) 분리 + 시나리오별 부분 게이트 설계가 필요해 보이나, PLAN에서 스키마·서브명령 구조를 확정해야 한다.
4. **`opal-loop-action-agent`/`opal-evaluator-agent` AGENT.md 변경 범위** — TASK.md "관련 문서" 표(D-5/D-6)에는 backlog-tool/test-tool 소스만 명시되어 있고 agents/ 변경은 명시 범위에 없다. 그러나 R-1(auth/origin 판정)·R-5(fidelity 요구)가 실질적으로 Evaluator/루프 액션 에이전트 프롬프트 문맥에 영향을 준다(§3.2, §5 R-F/R-G). PLAN에서 이 두 AGENT.md의 변경 여부·범위를 명시적으로 결정해야 한다.
5. **fidelity 필드의 하위 호환 기본값** — TASK.md AC가 "미지정=mock 간주 등 보수적 기본값 — PLAN에서 결정"이라고 명시. `_normalize_scenario()`(`scenario.py:109-131`)에 기본값을 주입하는 구체적 위치·값을 PLAN에서 확정 필요.
6. **신규 게이트 실패의 loop-control.md §7 분류** — `surface_uncovered`/`integration_task_missing`/fidelity 미달이 "복구가능"인지 "하드블로커"인지 loop-control.md에 명시할지 여부(§5 R-H).

### 표면 인벤토리 형식 대안 비교

| 기준 | (a) CONTRACT.md 마크다운 표 + 파서 | (b) OpenAPI(YAML) spec + CONTRACT.md 참조 |
|------|-----------------------------------|---------------------------------------------|
| 도구 파싱 난이도 | 마크다운 표 포맷 변화에 취약한 커스텀 정규식/라인 파서 필요 — 기존 backlog-tool/test-tool 어디에도 md 파서 선례 없음(§5 R-D) | YAML은 표준 라이브러리 수준 도구(PyYAML, test-tool의 `resolve` 서브명령이 이미 사용 중 — `README.md:26` "의존: PyYAML")로 구조화 파싱이 가능해 견고함 |
| 프로젝트 적용 범용성(비-API 프로젝트 폴백) | 모든 프로젝트 유형(CLI/라이브러리/DB 등)에 동일하게 적용 가능 — API가 아닌 프로젝트도 자연스럽게 표 형태로 표면을 나열 | REST/HTTP API 프로젝트에만 자연스럽게 적용됨. CLI/라이브러리/배치 등 비-API 프로젝트는 별도 폴백(예: 단순 markdown 표 또는 최소 JSON) 필요 — journey-flow.md §2가 이미 "user-facing 여부"로 트리거를 조건화하는 선례가 있어 유사한 조건부 설계가 가능 |
| 기존 계약 conformance 서술과의 정합 | `verification.md` §2.1 "계약 conformance" 행이 이미 "스키마·시그니처 일치"를 결정론 tier로 규정 — 마크다운 표 기반이면 이 결정론 검증을 위해 결국 파서가 표를 구조체로 변환해야 하므로 이중 작업(표 작성 + 파서 유지) | OpenAPI는 스키마·시그니처(paths/operations/requestBody/responses)를 원어로 표현하므로 R-4(b) "실 HTTP 전수 conformance"·R-4(c) "CORS 검사"와 자연 정합. 생태계 도구(향후 도입 검토) 활용 가능성도 있음(§2 외부조사 보류) |
| auth/origin 필드 표현력 | 표 컬럼 추가로 표현 가능하나 파서가 컬럼 순서/이름 변경에 취약 | OpenAPI `securitySchemes`(auth)로 표현 가능하나 origin(CORS)은 OpenAPI 표준 범위 밖이라 별도 확장 또는 CONTRACT.md 경계절 병행 필요 |
| **권고** | 비-API 프로젝트 폴백 및 즉시 구현 단순성 측면에서 최소 구현 후보 | **1순위 채택 권고(캡틴 지시와 정합)** — API 프로젝트는 (b), 비-API 프로젝트는 (a) 또는 최소 JSON 폴백의 **조건부 이원화**를 PLAN에서 구체화할 것을 제안. 이 경우 backlog-tool의 커버리지 게이트는 "openapi.yaml 파싱 결과" 또는 "surfaces.json(a/b 공통 중간 표현)" 중 하나의 **구조화된 단일 인터페이스**만 소비하도록 설계해 파서 분기를 CONTRACT 작성 단계로 격리하는 것이 결합도 관리에 유리하다 |

---

## 8. 3-SSOT 축 분리 관점 설계 제약 (요약)

- **원칙 문언**: [MUST] `opal/skills/opal-pilot-project-loop/SKILL.md:44`: "세 SSOT는 서로 참조하지 않는다(축 분리)." — 여기서 "세 SSOT"는 `backlog.json`/`state.json`/`test-scenario.json`(D-13)로 명시적으로 한정된다. CONTRACT.md/surfaces.json/openapi.yaml은 이 3-SSOT에 포함되지 않으므로, backlog-tool이 이들을 읽는 것은 문언상 위반이 아니다.
- **위반 판정 대상은 backlog.json ↔ test-scenario.json 교차뿐**: R-4(표면×결과 매트릭스)가 요구하는 "표면이 어느 결과로 검증되었는가" 판정은 test-scenario.json의 result존(§4-1)을 읽어야 하므로, 이 교차 판정 로직이 backlog.json 내부(backlog-tool)에 놓이면 축 분리 정신을 흐린다. → 집행 지점을 backlog-tool 외부(신규 독립 도구, 또는 오케스트레이터/루프 액션 에이전트의 판단 로직)로 두는 것이 원칙에 더 부합한다(PLAN 결정 사항 §7-2).
- **enforce-don't-advise와의 교차**: R-2/R-3/R-5는 "도구 성격"(TASK.md 확정 방향 표)이므로 위 원칙에 따라 반드시 도구 거부(exit code + error 필드)로 집행되어야 한다. R-1/R-6/R-8은 "문서 성격"으로 확정되어 있어 Evaluator(LLM 판정)가 집행 지점이 되며, 이는 PRINCIPLES §4 원칙의 예외가 아니라 TASK.md 자체가 판정 방식을 이미 결정한 것으로 해석된다(§5 R-F 리스크 항목 참조, 재확인 필요).

---

## 9. 기술 컨텍스트

### 9.1 기술 스택

| 카테고리 | 기술 | 버전 |
|----------|------|------|
| 언어 | Python 3 (표준 라이브러리 우선 — PyYAML은 test-tool `resolve`에서 이미 사용 중) | `~/.opal/.venv` |
| CLI 프레임워크 | argparse (backlog_tool.py/test_tool.py 공통) | 표준 라이브러리 |
| 데이터 포맷 | JSON (backlog.json/test-scenario.json SSOT), JSON Schema Draft-07 (참조용) | Draft-07 |
| 문서 | Markdown (SKILL.md·references·README.md) | - |
| 동시성 제어 | fcntl 배타 락(POSIX) | - |

### 9.2 추천 스킬

| 스킬 | 용도 |
|------|------|
| (해당 프로젝트 내부 스킬 체계이므로 외부 프레임워크 스킬 해당 없음) | - |

### 9.3 추천 MCP

| MCP | 용도 |
|-----|------|
| context7 | PLAN 단계에서 OpenAPI 생태계 도구(스키마 검증 라이브러리 등) 확정 시 공식 문서 조회 |
