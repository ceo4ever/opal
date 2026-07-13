# TEST-SCENARIO: opal-agent 부트스트랩 마커 3-way 확장 + caller-supplied session id

> 작성일: 2026-07-13 | 입력: PLAN.md §리스크 가설 표 + §3.N.5 테스트 시나리오
> 검증 대상: F-001~F-003 / TS-001~TS-011
> 트랙 규칙 SSOT: `opal/core/references/harness/red-first.md`

---

## 0. 동작검증 원칙

[MUST] `docs/CONVENTIONS.md` §배포 경계: "변경 후 `./scripts/install-mac.sh`로 재배포하여 검증한다." 따라서:
- 단위 검증(TS-001~010)은 **소스** `opal_agent.py`를 직접 import하여 `build_invocation`/`_mark`/`_run`의 **공개 관찰 출력**(조립된 `cmd` 배열·조립 프롬프트·예외·stderr 경고)으로 수행한다. subprocess로 실제 CLI를 실행하지 않는다(순수 조립 로직 검증 → 결정론적·고속).
- 실측(TS-011, R-5)은 **재배포 산출물** `~/.opal/tools/opal-agent/run.sh`를 실제 claude로 호출하여 비서 tier 캡을 관측한다. 인증/환경 제약 시 DEFERRED + 대체 근거(조립 커맨드 검증)로 갈음한다(FAIL 아님, task 057 선례).
- 실 `~/.opal/` 배포본을 파괴하지 않도록 재배포 검증은 install 후 read-only 프로브만 수행한다.

---

## 1. RED-first 트랙 판정

### 판정 결과: **RED-first 적용** (F-001·F-002 로직) / 문서·실측은 구현-후 검증

### 근거 (red-first.md §1.5 자동분기)

| 요소 | 트랙 분류 | 근거 |
|------|----------|------|
| F-001 마커 3-way (`_mark` 조립) | **RED-first 강제** | 커맨드/프롬프트 **계약 로직** — 첫 줄 마커는 tier 격리 정합성의 계약(API 계약에 준함), self-confirming 위험 |
| F-002 cold/warm 세션 분기 + 상호배타 + 경고 | **RED-first 강제** | 커맨드 계약 로직 + correctness-critical(cold 드롭 시 브레인 세션 미생성) |
| F-003 문서·변경이력 | 구현-후 정적 검증 | 문서 — 로직 불변 |
| R-5 실측 프로브 | 구현-후 동작검증 | L3 관찰 — 배포 산출물 실행 관측 |

**종합**: 지배적 리스크(H-1 회귀·H-2 상호배타·H-3 조용한 드롭·H-4 최외곽 불변식)가 모두 결정론적 커맨드 계약 로직이라 self-confirming 위험이 있으므로 **RED-first 적용**. red-first.md §1.5 "모호하면 RED-first 기본(안전측)"에 부합. 문서(F-003)는 동일 테스트 스위트 밖 정적 검사로 흡수한다.

### 트랙 운용 규칙 (red-first.md)
- [MUST] §1 RED→GREEN: `tests/test_opal_agent.py`의 TS-001~009를 **구현(Step 2·3) 이전에 작성·실행하여 FAIL(exit≠0) 증거 기록** 후 GREEN 진입.
- [MUST] §2 작성자≠구현자: RED 테스트는 `opal-test-agent`(mode: red)가 작성(Step 1), 구현은 `opal-task-agent`가 담당(Step 2·3) — 분리.
- [MUST] §3 테스트 불변성: GREEN/fix 루핑 중 RED 테스트 파일 수정 금지(약화·삭제 금지).
- §4 공개 인터페이스 검증: 내부 private 결합 금지 — `ClaudeAdapter().build_invocation(config, "claude").cmd`·`_mark(prompt, config)` 반환값·`_run` 예외/경고 등 **관찰 행위**로만 검증.
- §6 STATE: RED는 EXECUTE 내부 서브스텝으로 흡수(별도 STATE 행 없음, opds 10행 보존).

> PLAN 워커(본 문서 작성자)는 TEST-SCENARIO만 작성하며 RED 테스트 **코드**는 작성하지 않는다(§2 — RED 코드는 opal-test-agent 담당).

---

## 2. 테스트 환경 및 격리

| 항목 | 값 |
|------|-----|
| 테스트 파일 | `opal/tools/opal-agent/tests/test_opal_agent.py` (신규) |
| 테스트 프레임워크 | 표준 라이브러리 `unittest` (외부 패키지 금지 — opal_agent.py:7 무의존성) + pytest 러너 |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/opal-agent/tests/test_opal_agent.py -q` (또는 `python -m unittest`) |
| 검증 대상 | 소스 `opal/tools/opal-agent/opal_agent.py` 직접 import — `AgentConfig`, `ClaudeAdapter`, `GeminiAdapter`, `call_agent`(미실행 조립 경로는 build_invocation 직접), `_run` 검증부 |
| subprocess | **미사용** (조립 로직만 검증) — 단, TS-007/008(_run 상호배타·경고)은 shutil.which 통과 후 subprocess 직전 검증이므로 미지원 provider/예외 경로로 subprocess 도달 전 관측 |
| 실측(TS-011) | `./scripts/install-mac.sh` 재배포 후 `~/.opal/tools/opal-agent/run.sh --opal-bootstrap assistant --provider claude ...` |
| 회귀 | 동일 스위트 내 on/off·warm resume·타 provider 무영향 TC |

### _run 경고/예외 검증 팁 (opal-test-agent 참고)
- TS-007(상호배타)·TS-008(경고)은 `_run`이 adapter dispatch **이전**에 검증하므로, `shutil.which("claude")` 성공 환경에서도 예외/경고가 subprocess 실행 전에 발생하도록 설계됨. `claude` 미설치 환경이면 `ClaudeNotFoundError` 이전 순서 확인 필요 — 상호배타 예외(TS-007)는 which보다 먼저 검증되도록 `_run` 진입부에 배치(PLAN §3.2.2). 경고(TS-008)는 gemini 미설치 시 which 실패가 먼저일 수 있어, 경고 검증은 build_invocation 결과에 `--session-id` 부재 + capability 플래그(`supports_session_assign is False`) 확인으로 보강한다.

---

## 3. 시나리오 상세 (S-N ↔ TS-N ↔ 리스크 가설)

| S-ID | 시나리오 | 관련 TS | 가설 | 유형 | 트랙 | 기대 결과 | 결과 |
|------|---------|---------|------|------|------|----------|------|
| S-1 | claude assistant 마커 조립 | TS-001 | H-4 | 기능 | RED | `ClaudeAdapter.build_invocation` 조립 프롬프트(`-p` 다음 인자) 첫 줄 == `[ASSISTANT]` | PASS |
| S-2 | on/off 하위호환 | TS-002 | H-1 | 회귀 | RED | on=프롬프트 불변(마커 없음) / off=`[WORKER]\n` 접두 / AgentConfig 기본값 `opal_bootstrap=="on"` | PASS |
| S-3 | cursor·antigravity 최외곽 불변식 | TS-003 | H-4 | 기능 | RED | system_prompt 접붙임 후에도 조립 프롬프트 첫 줄 == `[ASSISTANT]` | PASS |
| S-4 | CLI choices 확장 | TS-004 | H-1 | 회귀 | RED | `--opal-bootstrap assistant` 파싱 통과 / `bad` 값 argparse 거부(SystemExit) / 기본 on | PASS |
| S-5 | cold `--session-id` 조립 | TS-005 | H-5 | 기능 | RED | `new_session_id="sid-x"` → cmd에 `["--session-id","sid-x"]` 포함, `--resume` 부재 | PASS |
| S-6 | warm `--resume` 유지 | TS-006 | H-5 | 회귀 | RED | `session_id="sid-y"` → cmd에 `["--resume","sid-y"]` 유지, `--session-id` 부재 | PASS |
| S-7 | cold/warm 상호배타 | TS-007 | H-2 | 기능 | RED | `new_session_id`+`session_id` 동시 → `OpalAgentError` raise | PASS |
| S-8 | 미지원 provider 경고 | TS-008 | H-3 | 기능 | RED | gemini 등에 `new_session_id` → `supports_session_assign is False` + build_invocation cmd에 `--session-id` 부재 (+ _run stderr 경고) | PASS |
| S-9 | CLI 상호배타 방어 | TS-009 | H-2 | 회귀 | RED | `--resume a --session-id b` 동시 전달 → argparse 거부(SystemExit) | PASS |
| S-10 | 문서·변경이력 정적 검증 | TS-010 | - | 산출물 검사 | 정적 | README에 `assistant`·`--session-id` 행 + cold 사용 예 / opal_agent.py·README 변경이력에 v2.5(KST+059) | PASS |
| S-11 | 실측 비서 tier 캡 | TS-011 | H-4 | 동작검증 | 구현-후 | 재배포 후 `run.sh --opal-bootstrap assistant` 응답에 `⬜ harness ⬜ PM`(PM tier 미로드) 관측 | PASS (§7.10 PM 실측) |

---

## 4. RED 단계 기대 (구현 전 실행)

| TC 그룹 | RED 시점 기대 |
|---------|--------------|
| F-001 조립 TS-001·003 (S-1·3) | **FAIL** — `_mark`에 assistant 분기 없어 첫 줄이 `[ASSISTANT]` 아님 |
| F-001 CLI TS-004 (S-4) | **FAIL** — choices에 `assistant` 부재 → 파싱 거부 |
| F-002 cold TS-005·008 (S-5·8) | **FAIL** — `new_session_id` 필드/조립 로직 부재(AttributeError 또는 `--session-id` 미조립) |
| F-002 상호배타 TS-007·009 (S-7·9) | **FAIL** — `_run` 검증/argparse 그룹 부재 |
| on/off·warm 회귀 TS-002·006 (S-2·6) | RED 시점에도 **PASS**(기존 동작 — 회귀 감시용 baseline) |
| 문서 TS-010 (S-10) | 구현 전 **FAIL**(v2.5 미기재) → Step 4 후 PASS |

---

## 5. GREEN 완료 기준 (TEST 단계)

- [ ] `python -m pytest opal/tools/opal-agent/tests/test_opal_agent.py -q` → 전체 PASS, exit 0
- [ ] TS-001~TS-010 전부 PASS
- [ ] on/off·warm resume·타 provider 회귀 0 (TS-002, TS-006, S-8 build 부재 확인)
- [ ] 무의존성 유지 — 테스트가 stdlib만 import (pytest는 러너로만)
- [ ] RED 테스트 파일이 GREEN 루핑 중 수정되지 않음 (red-first.md §3 — `git status` 불변 확인)
- [ ] (배포검증) 재배포 후 `run.sh --opal-bootstrap assistant --provider claude` 실측으로 `⬜ harness ⬜ PM` 관측 (TS-011). 인증/환경 제약 시 DEFERRED + 조립 커맨드 대체 근거
- [ ] (보안) changed_files에 하드코딩 시크릿/토큰 없음 — 시크릿 스캔 (PLAN §5.4)
- [ ] (보안) 신규 테스트 폴더 산출물(캐시 등)이 `.gitignore`에 걸리는지 확인 — 추적 불필요 파일 미커밋

---

## 6. 커버리지 매트릭스 (요구사항 ↔ 시나리오)

| 요구사항 | AC 요지 | S-ID | TS-ID |
|---------|---------|------|-------|
| R-1 마커 3-way | assistant 첫 줄 `[ASSISTANT]` 최외곽 | S-1, S-3, S-4 | TS-001, TS-003, TS-004 |
| R-2 하위호환 | on 불변·off `[WORKER]`·기본 on | S-2 | TS-002 |
| R-3 cold session | `--session-id` 조립 / resume 유지 / 상호배타 / 미지원 경고 | S-5, S-6, S-7, S-8, S-9 | TS-005~009 |
| R-4 문서 갱신 | assistant/session-id 문서 + v2.5 변경이력 | S-10 | TS-010 |
| R-5 동작검증 | 실측 비서 tier 캡 `⬜ harness ⬜ PM` | S-11 | TS-011 |

---

## 7. TEST 실행 결과

> (TEST 단계에서 opal-test-agent가 채운다 — RED 증거 + GREEN 집계 + 실측/DEFERRED 사유)

### 7.1 RED 증거 (opal-test-agent, RED 트랙)

- 작성: `opal/tools/opal-agent/tests/test_opal_agent.py` (신규, stdlib `unittest`, TS-001~TS-009 전량 + baseline 2건)
- 실행 명령: `python3 -m pytest opal/tools/opal-agent/tests/test_opal_agent.py -q` (cwd: 프로젝트 루트)
- 실행 시각: 2026-07-13T15:23 KST 경
- 결과: **10 failed, 7 passed — exit 1** (RED 확보)

| S-ID | TS-ID | RED 시점 결과 | 대표 실패/통과 사유 |
|------|-------|--------------|-------------------|
| S-1 | TS-001 | FAIL | `AssertionError: '[ASSISTANT]' != 'hello world'` — `_mark`에 assistant 분기 없음 |
| S-2 | TS-002 | PASS(baseline, 회귀 감시용) | on/off 기존 동작 불변 — RED 대상 아님 |
| S-3 | TS-003 | FAIL (cursor·antigravity 2건) | 동일 사유 — `_mark` assistant 분기 부재로 최외곽 첫 줄이 `[ASSISTANT]` 아님 |
| S-4 | TS-004 | FAIL | `SystemExit(2)`: `invalid choice: 'assistant'` — CLI `choices=("on","off")`에 `assistant` 부재 |
| S-5 | TS-005 | FAIL | `TypeError: AgentConfig.__init__() got an unexpected keyword argument 'new_session_id'` |
| S-6 | TS-006 | PASS(baseline, 회귀 감시용) | warm resume(`session_id`→`--resume`) 기존 동작 불변 — RED 대상 아님 |
| S-7 | TS-007 | FAIL | 상동 `TypeError: ... 'new_session_id'` — `AgentConfig` 필드 부재로 상호배타 검증 자체 도달 불가 |
| S-8 | TS-008 | FAIL (3건) | `AttributeError: type object 'ClaudeAdapter'/'GeminiAdapter' has no attribute 'supports_session_assign'` + 상동 `TypeError('new_session_id')` |
| S-9 | TS-009 | FAIL | `SystemExit(2)`: `unrecognized arguments: --session-id sid-b` — CLI `--session-id` 플래그 미구현 |

**baseline_pass**: S-2(3건 전부 PASS) · S-6(1건 PASS) — RED 시점에도 정상 PASS 확인(회귀 baseline, RED 증거 대상 제외).

### 7.2 test-scenario.json SSOT 게이트

- `scenario-init --task-path tasks/059-260713-opds-에이전트마커-3단-세션주입 --scenarios [...]` → `{"ok": true, "scenarios_count": 7}` (S-1,3,4,5,7,8,9만 등록 — S-2·S-6은 baseline이라 SSOT 미등록)
- `scenario-red --id {S-1,S-3,S-4,S-5,S-7,S-8,S-9}` 전 7건 → `red_confirmed: true` (evidence는 위 표의 실패 메시지 요약)
- `scenario-lock` → `{"ok": true, "locked": true}` / `scenario-status` → `{"total": 7, "red_confirmed": 7, "passed": 0, "failed": 0}` (동결 완료)

### 7.3 GREEN 스위트 재실행 (opal-test-agent, 검증 전용)

- 실행 명령: `python3 -m pytest opal/tools/opal-agent/tests/test_opal_agent.py -q` (cwd: 프로젝트 루트)
- 실행 시각: 2026-07-13 (opal-test-agent TEST 단계)
- 결과: **17 passed — exit 0** (RED 시점 10 failed 전부 GREEN 전환, baseline 7건 PASS 유지 — 회귀 0)
- RED 테스트 파일 불변성: `git status --porcelain -- opal/tools/opal-agent/tests/` → `?? opal/tools/opal-agent/tests/`(신규 미추적, EXECUTE 단계에서 M 아님) / `git status --porcelain` 전체에서 M 목록은 `opal_agent.py`·`README.md`만 존재, `tests/`는 없음 — Step 1(RED 작성) 이후 수정 없음 확인. 보조로 `test_opal_agent.py` mtime(15:23:21)이 RED 기록 시각(test-scenario.json `red_at` 15:23:56 이전)과 일치하고 `__pycache__` 외 변경 없음, `--collect-only`로 수집된 테스트 17건이 RED 증거표(§7.1)의 10 FAIL + 7 PASS baseline과 개수 일치 — RED §3 불변 확인.
- 무의존성: 테스트 파일은 stdlib `unittest` 기반, pytest는 러너로만 사용(수집 시 외부 패키지 import 없음) 확인.

### 7.4 TS-010 문서·변경이력 정적 검증

- README 확인:
  - `--opal-bootstrap on|assistant|off` 옵션 행 및 `assistant` 의미 설명 존재 (L149)
  - `--session-id ID` 옵션 행 + `--resume`과 상호배타 명시 (L146-147, L33)
  - cold 세션 사용 예 블록 (`## cold session id 지정` L201, 예시 커맨드 L206-208)
  - 변경이력에 `v2.5 (2026-07-13 15:25 KST, 059)` 존재 (L185)
- `opal_agent.py` docstring에 `v2.5 2026-07-13 15:25 --opal-bootstrap 3-way(assistant) + caller-supplied ... cold --session-id (059)` 존재 (L51-52)
- 판정: **PASS**

### 7.5 보안 검사

- 하드코딩 시크릿/토큰 스캔: `opal_agent.py`, `README.md`, `tests/test_opal_agent.py` 3개 파일에 `(api[_-]?key|secret|password|token|sk-...|AKIA...)\s*[:=]\s*['"]...['"]` 패턴 매치 없음(NO_MATCH). 광의 키워드(`token|secret|password|sk-`) 스캔에서도 실제 시크릿 없음 — `README.md:45`의 `ask-for-approval`이 `sk-` 부분 문자열에 우연 매치된 false positive만 확인, 실제 하드코딩 값 없음. **PASS**
- `.gitignore` 커버리지: `git check-ignore -v opal/tools/opal-agent/tests/__pycache__` → `.gitignore:7:__pycache__/` 매치 확인. `git status --porcelain`에서 `tests/`가 신규 디렉토리로만 잡히고 `__pycache__`·`.pytest_cache` 개별 항목은 노출되지 않음(gitignore가 커버) — 커밋 시 산출물 유입 없음. **PASS**

### 7.6 재배포 검증

- 실행: `./scripts/install-mac.sh` (프로젝트 루트) → 프론트엔드 빌드·OPAL Console 재기동·`✓ OPAL 설치 완료 (v0.6.8-11-g8372f59)` 성공 종료
- 배포본 확인: `~/.opal/tools/opal-agent/opal_agent.py`에 `v2.5 2026-07-13 15:25 ... (059)`, `_BOOTSTRAP_MARKERS = {"off": "[WORKER]", "assistant": "[ASSISTANT]"}`, `choices=("on", "assistant", "off")` 반영 확인. `README.md`도 v2.5/assistant/--session-id 행 반영 확인. **PASS**

### 7.7 TS-011 실측 프로브 (S-11)

- cwd: 프로젝트 루트(`.opal/AGENT.md` 존재)
- 주 프로브: `~/.opal/tools/opal-agent/run.sh "현재 부트스트랩 상태를 [부트스트랩] 보고 라인 형식으로만 짧게 보고하라" --opal-bootstrap assistant --provider claude --model haiku --timeout 240 --text`
  - 응답 원문: `[부트스트랩] 권한 미부여로 ~/.opal/ 파일 접근 불가 — AGENT.md·identity.md 로드 불가 — OPAL 정체성 미결정 — 순수 어시스턴트 모드 대기 중`
  - 관측: 하위 claude 프로세스가 샌드박스 권한 제약으로 `~/.opal/` 파일 자체를 읽지 못해, 기대했던 `⬜ harness ⬜ PM` 체크박스 형식(AGENT.md에 정의된 보고 템플릿)을 재현하지 못함 — 다만 정성적으로는 PM tier로의 승격이 전혀 관측되지 않음("정체성 미결정", PM 절차 언급 없음)으로 R-1 취지(PM 미승격)와 방향은 일치.
- 보조 대조: 동일 프로브를 `--opal-bootstrap off`로 실행 → `[부트스트랩] SKIPPED — [WORKER] 마커 감지, OPAL 절차 전체 생략, tier 로드 없음` — off 마커는 정상적으로 완전 스킵 확인(§S-2 회귀와 정합).
- 판정: **DEFERRED** (FAIL 아님) — 사유: 현재 실행 환경(샌드박스)에서 하위 claude 프로세스의 `~/.opal/` 파일시스템 접근 권한이 비대화형 호출에 부여되지 않아, AGENT.md가 정의하는 정식 부트스트랩 보고 템플릿(`⬜ harness ⬜ PM`) 자체가 트리거되지 못함(harness 부트스트랩 절차 진입 실패) — claude 실행 자체는 성공했으나 "환경 제약"에 해당(task 057 선례와 동일 처리).
- 대체 근거: TS-001(S-1, PASS) — `ClaudeAdapter.build_invocation`이 `--opal-bootstrap assistant` 조립 시 프롬프트 최외곽 첫 줄에 `[ASSISTANT]` 마커를 정확히 주입함을 결정론적 단위 테스트로 확인. 이 마커가 `~/.opal/AGENT.md` §부트스트랩 게이트 규칙("첫 줄이 `[ASSISTANT]`이면 PM 승격만 억제")과 결합해 PM tier 미로드로 이어진다는 계약은 조립 로직 수준에서 GREEN 확보됨 — 실측 환경 제약과 별개로 계약 구현 자체는 검증 완료.

### 7.8 최종 scenario-status

```json
{"ok": true, "command": "scenario-status", "locked": true, "total": 7, "red_confirmed": 7, "passed": 7, "failed": 0}
```

- SSOT 등록 7건(S-1,3,4,5,7,8,9) 전부 `pass` 기록 완료 (`scenario-mark --result pass`, evidence는 각 pytest 테스트 노드 PASS 근거 문자열).
- SSOT 미등록 3건: S-2·S-6(baseline, RED 시점부터 PASS 유지 — §3 표에 PASS로 직접 기록), S-10(정적 검증 PASS — §7.4), S-11(실측 DEFERRED — §7.7).

### 7.9 최종 판정 (opal-test-agent 시점)

**PARTIAL** — 코드 계약 로직(F-001·F-002, S-1~S-9) 전부 GREEN PASS, 문서(S-10) PASS, 보안 PASS, 재배포 PASS. 단 S-11(실측 비서 tier 캡)은 환경(샌드박스 권한) 제약으로 DEFERRED — FAIL이 아니며 대체 근거(TS-001 GREEN)로 갈음. 핵심 기능(F-001·F-002) 전부 PASS이므로 Critical Fail 아님, 미확정 1건(DEFERRED)으로 인해 All Pass가 아닌 PARTIAL로 판정.

### 7.10 TS-011 PM 재실측 — DEFERRED 해소 (S-11 PASS)

- 실행 시각: 2026-07-13 15:36 KST | 실행 주체: PM(알투) 직접 — 워커 샌드박스 권한 제약을 우회해 비샌드박스 셸에서 재실측
- 실행: `~/.opal/tools/opal-agent/run.sh "현재 부트스트랩 상태를 [부트스트랩] 보고 라인 형식으로만 짧게 보고하라" --opal-bootstrap assistant --provider claude --model haiku --timeout 240 --allowed-tools "Read,Grep,Glob" --text` (cwd: 프로젝트 루트, `.opal/AGENT.md` 존재)
  - `--allowed-tools "Read,Grep,Glob"` 부여 — 헤드리스 하위 claude가 `~/.opal/` 부트스트랩 파일을 읽을 수 있도록 opbr_adapter와 동일 계약(`opbr_adapter.py:6`) 적용. 1차 시도(도구 미부여)는 권한 대기 응답으로 재현 불가했음(§7.7과 동일 사유).
- 응답 원문:
  ```
  [부트스트랩] ✅ principles ✅ identity ⬜ harness ⬜ PM ⬜ PM모드 ⏳ registry ⏳ references ⏳ model-mapping
  [안내] 프로젝트 초기화는 `//opi`, 일반 비서 작업은 자연어로 요청하세요
  ```
- 판정: **PASS** — 프로젝트 cwd(`.opal/AGENT.md` 존재)에서 Phase A(principles·identity ✅)는 로드되고 Phase B(harness·PM·PM모드 ⬜)는 억제됨. `opal/core/AGENT.md` §부트스트랩 완료 보고의 "[ASSISTANT] 캡 세션" 기대 표기와 정확히 일치(051 실측 방법 재현). 최종 판정을 **All Pass**로 갱신한다 (§7.9 PARTIAL의 유일 사유였던 S-11 해소).
