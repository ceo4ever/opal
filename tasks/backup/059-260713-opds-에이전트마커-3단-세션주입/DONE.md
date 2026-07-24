# DONE: opal-agent 부트스트랩 마커 3-way 확장 + caller-supplied session id 지원

> 완료일: 2026-07-13 15:59 KST | 적용 스킬: opds (semi-agentic) | 태스크: 059

## 목표 달성

opal-agent의 `--opal-bootstrap`을 3-way(`on|assistant|off`)로 확장하여 `[ASSISTANT]` 중간 tier(비서 tier 캡) 서브에이전트 호출을 지원하고, claude provider에 caller-supplied cold session id(`--session-id`) 주입을 추가했다. 브레인(opbr) 질의를 opal-agent로 이관하기 위한 선행 갭 2건이 모두 닫혔다.

## 변경 파일

| 파일 | 변경 |
|------|------|
| `opal/tools/opal-agent/opal_agent.py` | `_BOOTSTRAP_MARKERS` dict + `_mark()` 3-way / `AgentConfig.new_session_id` / `ProviderAdapter.supports_session_assign`(claude만 True) / `ClaudeAdapter` cold(`--session-id`)·warm(`--resume`) 분기 / `_run()` 상호배타 예외+미지원 provider stderr 경고 / CLI `--session-id`·`--resume` mutually exclusive / @header 블록 신설 / docstring v2.5 |
| `opal/tools/opal-agent/README.md` | 플래그 표(`on|assistant|off`·`--session-id`) / 3단 사다리 표 / cold session 사용 예 / 변경이력 v2.5 |
| `opal/tools/opal-agent/tests/test_opal_agent.py` | 신규 — stdlib unittest 17건 (TS-001~009 + baseline S-2·S-6), @header(layer: test, task 059) |

## 검증 증거

- **RED-first**: 구현 전 10 FAIL/7 PASS(exit 1) 증거 → test-scenario.json 7건 red_confirmed+lock → `verify --red-check` 게이트 통과 → GREEN 17/17 PASS(exit 0). RED 테스트 파일 GREEN 루핑 중 불변.
- **실측 캡 검증(S-11)**: 프로젝트 cwd(`.opal/AGENT.md` 존재)에서 배포본 `run.sh "..." --opal-bootstrap assistant --allowed-tools "Read,Grep,Glob"` 실행 → 응답 `[부트스트랩] ✅ principles ✅ identity ⬜ harness ⬜ PM ⬜ PM모드` — Phase A 로드 + Phase B 억제 실증(051 방식). 대조 `off` 프로브는 부트스트랩 전체 스킵 확인.
- **컨벤션**: GC-CONVENTION-260713-1532.md — Critical 0/High 0/Medium 1(GC-C001 @header, fix로 해소)/Low 1(보류).
- **보안**: 시크릿 스캔 NO_MATCH, `__pycache__` .gitignore 커버.
- **배포**: `./scripts/install-mac.sh` 성공, `~/.opal/tools/opal-agent/`에 v2.5 반영 확인.
- scenario-status: `{"total": 7, "red_confirmed": 7, "passed": 7, "failed": 0}` — 상세: TEST-SCENARIO.md §7.

## 운영 기록 (특이사항)

- fix 루프 2회: fix 1/3(haiku)이 @header 추가 중 기존 docstring(v2.5 변경이력 포함)을 무단 삭제(Guards 위반) → fix 2/3(sonnet, 복원 원문 전문 명시)로 복구 + PM 교차 검증. 교훈: 경량 모델 fix 디스패치 시 "보존 대상 원문"을 프롬프트에 명시하는 편이 안전.
- S-11 실측은 워커 샌드박스 권한 제약으로 1차 DEFERRED → PM 직접 재실측(--allowed-tools 부여)으로 해소.

## 잔여·후속 액션

1. **브레인 이관 본태스크**: `dashboard/backend/adapters/opbr_adapter.py`의 raw `claude -p` 서브프로세스를 opal-agent(`opal_bootstrap="assistant"` + `new_session_id`)로 대체 — 이번 태스크가 선행 조건을 완비.
2. **커밋**: 캡틴 지시 대기. 주의 — 워킹트리에 본 태스크 무관 수정(dashboard/backend 4파일, 병행 세션 058 추정) 혼재. 커밋 시 경로 분리 필요(`opal/tools/opal-agent/` + `tasks/059-*/` + `.opal/MEMORY.md` 채번만).
3. **ARCHITECTURE.md opal-agent 도구 등재**(후속 검토): 3단 사다리 절(§부트스트랩, :66)은 이미 정확. opal-agent 도구 자체의 등재 누락은 선행 태스크(f128565) 범위 — 별건 처리.
4. **GC-C002 (Low)**: opal_agent.py·README 변경이력이 표가 아닌 불릿 — v1.0부터의 관례로 보류.

## 산출물

TASK.md / PLAN.md / TEST-SCENARIO.md / test-scenario.json / AGENTIC-LOG.md / GC-CONVENTION-260713-1532.md / DONE.md
