# PLAN: TDD RED-first 트랙 도입 — 독립 RED 작성 + 테스트코드 산출물 + state-tool red 게이트

> 작성일: 2026-06-09 | 입력: TASK.md (ANALYSIS.md 없음 — PLAN이 직접 코드 분석 수행)
> 모드: Multi-Feature (7개 기능)
> 작성자: opal-plan-agent (워커)

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

OPAL 하네스에 "실패하는 RED 테스트 → GREEN 구현" TDD 사이클을 도입한다. 핵심은 (1) 영속하는 테스트 코드 산출물, (2) RED 증거 선확보, (3) 작성자≠구현자 분리, (4) state-tool deterministic 집행(테스트 불변성)이다. SSOT는 하네스 신규 참조 문서 1개에 두고 opds/opd가 참조 상속한다. R-5(state-tool 코드)는 자기적용(dogfooding) — 본 PLAN의 TEST-SCENARIO.md L1/L2 시나리오가 곧 R-5의 RED 테스트가 된다.

### 1.2 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | RED-first SSOT 하네스 문서 신설 | R-1, R-2(일부), R-6(일부) | P0 | 없음 |
| F-002 | state-tool RED 게이트 + 테스트 불변성 (코드) | R-5 | P0 | F-001 (규칙 정의 선행) |
| F-003 | 파이프라인 RED→GREEN 순서 명문화 (opds/opd) | R-1 | P0 | F-001 |
| F-004 | RED 작성 주체 정의 + EXECUTE Scope 제약 | R-2 | P0 | F-001, F-002 |
| F-005 | 테스트 스택·위치 탐지 절차 | R-3 | P1 | F-001 |
| F-006 | 모듈 미러링 배치·명명·추적 + 테스트 @header | R-4 | P1 | F-001 |
| F-007 | 공개 인터페이스 검증 규율 + 변경이력·배포 정합 | R-6, R-7 | P1 | F-001~F-006 |

### 1.3 기능 의존 그래프 (ASCII)

```
F-001 (SSOT 문서) ─┬─ F-002 (state-tool 코드) ─┐
                   ├─ F-003 (파이프라인 순서)    │
                   ├─ F-005 (스택 탐지)          ├─ F-004 (작성주체+Scope) ─ F-007 (규율+이력)
                   └─ F-006 (배치·@header)       ┘
```

---

## 리스크 가설 표

> PLAN 단계에서 작성. TEST-SCENARIO.md §1의 입력이 됨.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | F-002 `verify --red-check` (state_tool.py) | RED 증거 없으면 GREEN/EXECUTE mark 차단 — 누락 시 self-confirming 통과 | P0 | L1(단위) + L2(mark 훅 통합) | S-1, S-2, S-7 |
| H-2 | F-002 `verify --changed-files` 테스트 불변성 | fix 루핑 중 테스트 파일 수정을 거부 못 하면 reward hacking 방어 무력화 | P0 | L1(단위) + L2(mark fix 훅) | S-3, S-4, S-8 |
| H-3 | F-002 신규 ERROR_CODES 2종 | 코드 미등재/오타 → err() 메시지 포맷 실패, completeness 테스트 깨짐 | P1 | L1(상수 검증) | S-5 |
| H-4 | F-002 graceful skip 분기 | 테스트 인프라 부재 프로젝트에서 RED 게이트가 강제 실패 유발 | P0 | L1(단위) | S-6 |
| H-5 | F-002 기존 28종 ERROR_CODES + 158 테스트 | 신규 분기가 기존 verify/mark 동작 회귀 유발 | P0 | L1/L2(전체 스위트 재실행) | S-9 (회귀) |
| H-6 | F-001~F-007 SSOT 단일성 | RED 규칙을 opds·opd에 중복 서술 → 발췌·복제 금지 위반, 드리프트 | P1 | L1(문서 grep 산출물 검사) | S-10 |
| H-7 | F-003/F-004 STATE 행 구조 | RED를 별도 행으로 추가 시 opds 10행/opd 15행 `--rows-from` SSOT 파손 | P1 | L1(행 카운트 산출물 검사) | S-11 |

---

## 2. 기능별 분석

### F-001: RED-first SSOT 하네스 문서 신설

#### 2.1.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 참조 | `opal/core/references/harness/red-first.md` | RED-first 규칙 SSOT (신규) | 신규 |
| 참조 | `opal/core/references/opal-harness.md` | §2 하네스 모듈 테이블에 red-first 등록 | 수정 |

#### 2.1.2 현재 구현
현재 RED-first 규칙은 어디에도 없다. 분산된 관련 규칙: 헌법 §4 "Add X → Write a check that fails without X, then make it pass" (`~/.opal/PRINCIPLES.md:37`), test-scenario-guide "TDD red-green 연결" (`test-scenario-guide.md:14`), execute Step 3-S "자가 점검 절차 (TDD red-green)" (`op-dev-execute/SKILL.md:57-66`). 그러나 **"실패 증거를 먼저 확보"라는 RED 순서**와 **테스트 코드 영속**은 명문화되지 않았다. 하네스 모듈은 `opal-harness.md` §2 "하네스 모듈" 테이블(`opal-harness.md:94-104`)에 등록되어 lazy 로드된다 (탐색: `{프로젝트}/.opal/references/harness/{file}` → `~/.opal/references/harness/{file}`).

#### 2.1.3 영향 범위
- 참조자(상위 의존): opds SKILL, opd SKILL, op-dev-test-scenario(SKILL+가이드), op-dev-execute SKILL, coding-principles.md — 모두 이 SSOT를 참조 상속.
- 피참조(하위 의존): 헌법 §4 (red-first.md가 헌법을 참조 상속, 재서술 금지).

### F-002: state-tool RED 게이트 + 테스트 불변성 (코드)

#### 2.2.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 코드 | `opal/tools/state-tool/state_tool.py` | `verify` 확장(`--red-check`/`--changed-files`/`--test-globs`) + ERROR_CODES 2종 + mark 훅 | 수정 |
| 테스트 | `opal/tools/state-tool/tests/test_state_tool.py` | RED 게이트·불변성 단위 테스트 + completeness 30종 | 수정 |

#### 2.2.2 현재 구현
- 언어/러너: **Python 3 + 표준 라이브러리 stdlib `unittest`** (`test_state_tool.py:24-29` import; `TASK T-11: 표준 라이브러리만 import` `state_tool.py:14`). pytest 미설치 — 실행은 `~/.opal/.venv/bin/python -m unittest discover -s tests` (검증 완료: 158 tests OK). `run.sh`는 `$HOME/.opal/.venv/bin/python state_tool.py "$@"` 래퍼 (`run.sh:4-12`).
- `verify` 서브커맨드 (013): `cmd_verify(args)` (`state_tool.py:1369-1403`) — `_find_scenario_file`(`:1283-1292`)로 TEST-SCENARIO.md 경로 결정 → 없으면 `skipped:true` ok (doc-only skip, `:1378-1384`). `_check_mock_patterns`(`:1295-1301`)로 mock 코드 정규식 검출, `_check_evidence`(`:1304-1366`)로 Pass 행 증거 누락 검출. 인자: `--scenario`만 (`:1527-1529`).
- mark TEST stage 훅: `cmd_mark`에서 `row["stage"] == "TEST"`이면 verify 로직 자동 실행 (`state_tool.py:968-978`) — mock/evidence 위반 시 `err("mark", ...)`로 mark 거부.
- ERROR_CODES: 28종 dict 상수 (`state_tool.py:67-98`), `mock_in_scenario`/`evidence_missing` 포함 (`:95-96`). `err()`(`:120-134`)가 `ERROR_CODES.get(code)` 템플릿 포맷.
- completeness 테스트: `TestErrorCodesCompleteness.EXPECTED_CODES` 28종 + `test_error_codes_count` (`assertEqual(len(ST.ERROR_CODES), 28)`, `test_state_tool.py:1735-1741`).
- argparse: `build_parser()`의 `p_vfy` 서브파서 (`:1522-1530`).

#### 2.2.3 영향 범위
- 호출자: opds/opd EXECUTE·TEST 단계 mark, fix 루핑 (`opal-pilot-dev-short/SKILL.md:144-162`), PM Gate 사전 검증.
- 회귀 위험: ERROR_CODES count 28→30 변경 → `test_error_codes_count` 동시 갱신 필수 (H-5). 기존 verify happy-path·mock·evidence·doc-skip 테스트(`TestVerify`, `test_state_tool.py:1749-1962`) 비파괴.
- 공유 상태: `_check_mock_patterns`/`_check_evidence` 헬퍼 재사용 (신규 RED 헬퍼와 독립).

### F-003: 파이프라인 RED→GREEN 순서 명문화 (opds/opd)

#### 2.3.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 오케스트레이터 | `opal/skills/opal-pilot-dev-short/SKILL.md` | STEP 2(PLAN)·STEP 3(EXECUTE)에 RED→GREEN 순서 참조 1줄 + fix 루핑 불변성 메모 | 수정 |
| 오케스트레이터 | `opal/skills/opal-pilot-dev/SKILL.md` | STEP 3.5·STEP 4에 RED→GREEN 순서 참조 1줄 | 수정 |

#### 2.3.2 현재 구현
opds는 3단계 압축(TASK→PLAN→EXECUTE→TEST→CLOSE), TEST-SCENARIO를 PLAN-equivalent(행 3)에 흡수 (`opal-pilot-dev-short/SKILL.md:52, 247`). opd는 STEP 3.5 TEST-SCENARIO를 PM 직접 작성으로 분리 (`opal-pilot-dev/SKILL.md:84-96`). 두 스킬 모두 EXECUTE 디스패치 시 `scenario_source`를 전달하고 자가점검(Step 3-S)으로 L1/L2 PASS를 완료기준에 둔다. 그러나 "실패(RED) 증거를 먼저 확보"라는 순서는 부재.

#### 2.3.3 영향 범위
- 두 스킬은 동일 규칙을 공유 → SSOT(F-001) 참조로 처리, 본문 중복 금지 (H-6).
- 변경이력 표 행 추가 의무 (R-7).

### F-004: RED 작성 주체 정의 + EXECUTE Scope 제약

#### 2.4.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 스킬 | `opal/skills/op-dev-test-scenario/SKILL.md` | 역할 분배표에 "RED 테스트 코드 작성" 행 + 작성 주체 정의 | 수정 |
| 에이전트 | `opal/agents/opal-test-agent/AGENT.md` | `mode: red` 추가 — M1 시나리오→실패 테스트 코드 변환·실행·RED 증거 기록 | 수정 |
| 스킬 | `opal/skills/op-dev-execute/SKILL.md` | 가드레일에 "RED 테스트 파일 수정 금지" 추가 + Step 3-S 갱신 | 수정 |

#### 2.4.2 현재 구현
- 시나리오 작성 = PM+페어 직접 (`op-dev-test-scenario/SKILL.md:13-14, 50-60` 역할 분배표). "실행 명령" 칸은 EXECUTE 워커, "결과/상세" 칸은 opal-test-agent가 채움.
- opal-test-agent는 BE/FE/E2E 3모드 (`opal-test-agent/AGENT.md:75-92`) — 시나리오 **실행·검증** 전담. 작성 권한 없음. self-confirming 방지를 위해 작성자 필드 무비판 신뢰 금지 (`AGENT.md:24, 139`).
- op-dev-execute 가드레일: "PLAN.md에 없는 파일 생성/수정 금지" 등 5종 (`op-dev-execute/SKILL.md:96-102`). 테스트 파일 수정 금지 규칙 부재.
- Step 3-S 자가점검: 워커가 시나리오 실행 명령을 채우고 Bash 실행 (`op-dev-execute/SKILL.md:57-66`).

#### 2.4.3 영향 범위
- 작성자≠구현자: opal-test-agent(RED 작성) ≠ op-dev-execute(GREEN 구현) — 기존 에이전트 분리 유지, 신규 에이전트 불필요(토큰 효율).
- EXECUTE Scope 위반 검출은 F-002 `verify --changed-files`로 deterministic 집행 연동.

### F-005: 테스트 스택·위치 탐지 절차

#### 2.5.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 가이드 | `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md` | 스택·위치 탐지 4단계 + 인프라 부재 에스컬레이션 | 수정 |

#### 2.5.2 현재 구현
가이드 Step 4 L1 작성 요령에 "도구: `.opal/test-tools.yaml` 또는 프로젝트 설정에서 결정 (vitest/pytest 등)" 1줄만 존재 (`test-scenario-guide.md:107`). 탐지 우선순위·인프라 부재 처리 규칙은 부재. M2 환경 미비 시 PM 반환 규칙은 test-agent에만 존재 (`opal-test-agent/AGENT.md:147-149`).

#### 2.5.3 영향 범위
- 플랫폼/프로젝트 독립성 — 특정 러너 하드코딩 금지 (C-2). 탐지 로직 자체가 어댑터.
- F-002 graceful skip(H-4)과 정합 — 탐지 실패 = 인프라 부재 = skip 또는 에스컬레이션.

### F-006: 모듈 미러링 배치·명명·추적 + 테스트 @header

#### 2.6.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 가이드 | `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md` | 모듈 미러링 배치 + 케이스명 프리픽스 규칙 | 수정 |
| 스킬 | `opal/skills/op-dev-test-scenario/SKILL.md` | §4 매핑표 스키마에 "테스트 파일:케이스" 열 추가 | 수정 |
| 참조 | `opal/core/references/harness/header-rules.md` | 테스트 파일 @header 필드(`task`, `scenarios`) 정의 | 수정 |

#### 2.6.2 현재 구현
- §4 매핑표 현 스키마: `AC ID | 가설 ID | 검증 계층 | 시나리오 | 비고` 5열 (`op-dev-test-scenario/SKILL.md:130-133`). "테스트 파일:케이스" 열 없음.
- header-rules: 필수 필드 `module/layer/domain/description/exports` (`header-rules.md:30`). 적용 대상 확장자 11종 (`header-rules.md:18-19`). 테스트 파일 전용 필드(`task`, `scenarios`) 정의 없음. 기존 테스트 파일은 `layer: test` 사용 중 (`test_state_tool.py:5`).

#### 2.6.3 영향 범위
- 추적 3중화: ① 케이스명 프리픽스 `[T016/L1-AC1]` ② @header `task`/`scenarios` ③ §4 매핑표 열. 모두 SSOT(F-001) 또는 가이드에 정의.
- header-standard.md(`~/.opal/references/header-standard.md`)는 배포본 — 본 태스크는 프로젝트 소스 `header-rules.md`만 수정(선택 필드 추가).

### F-007: 공개 인터페이스 검증 규율 + 변경이력·배포 정합

#### 2.7.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 가이드 | `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md` | "공개 인터페이스로 검증, 내부 구현 결합 금지" 규칙 | 수정 |
| 참조 | `opal/core/references/harness/coding-principles.md` | §3 또는 §4에 공개 인터페이스 검증 체크 1행 | 수정 |
| 문서 | 변경된 전 문서 + `DONE.md` | 변경이력 016 행 + install 재배포 메모 | 수정/신규 |

#### 2.7.2 현재 구현
- coding-principles §3 TEST-SCENARIO 체크에 "실데이터/실연동 검증" 항목은 있으나 "공개 인터페이스 검증/내부 결합 금지"는 없음 (`coding-principles.md:47-52`).
- 변경이력 의무: CONVENTIONS.md §변경이력 작성 의무 (`docs/CONVENTIONS.md:194-198`) — KST 일시 + 태스크 번호 괄호.
- 배포: install-mac.sh가 변경이력 strip + 배포 (`docs/CONVENTIONS.md:198, 202-203`).

#### 2.7.3 영향 범위
- 전 변경 문서 7~9개에 변경이력 행 추가 (R-7). state_tool.py @header description 갱신.
- install 재배포 필요(스킬·에이전트·참조·도구 전부 `~/.opal/`로 배포) — DONE.md에 기재.

---

## 3. 기능별 설계

> 인라인 인용: `(→ D-N §N)` 또는 `경로:줄번호`. 필수 제약은 `[MUST]` 포맷.

### F-001: RED-first SSOT 하네스 문서 신설

#### 3.1.1 파일 변경 계획
**신규 생성**
| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `opal/core/references/harness/red-first.md` | 참조 | RED-first 규칙 SSOT | C-1·C-4 (→ D-0 §확정 방향) |

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/core/references/opal-harness.md` | 참조 | §2 "하네스 모듈" 테이블에 `red-first.md` 행 추가 (로드 시점: TEST-SCENARIO/EXECUTE 단계) | `opal-harness.md:94-104` |

#### 3.1.2 API·데이터 모델·화면 설계 (문서 구조 설계)
`red-first.md` 섹션 구조 (헌법 §4를 참조 상속, 재서술 금지 — `~/.opal/PRINCIPLES.md:35-40`):
- `## 0. 상속` — 헌법 §4 참조 1줄. [MUST] 토큰.
- `## 1. RED→GREEN 순서` — [MUST] "RED 단계에서 실패 테스트 코드를 작성·실행하여 실패(exit code≠0)를 증거로 기록한 뒤 GREEN(구현) 진입. RED 증거 없이 GREEN 진입 금지." (R-1 AC 원문)
- `## 1.5 적용 기준 (하이브리드 자동분기)` — RED-first 트랙 적용 여부를 작업 성격으로 분기 (캡틴 결정 2026-06-09):
  - **RED-first 강제** (self-confirming 위험 높음): 비즈니스 로직 / DB 스키마·마이그레이션 / API 계약 / 인증·인가 / 버그 수정(회귀 방지).
  - **구현 후 시나리오 검증 허용** (탐색·시각): 탐색적 프로토타입 / UI 화면·컴포넌트 / 행위 불변 리팩터 / 설정·문서.
  - **판단 주체**: PM이 변경 영역으로 판단(TEST-SCENARIO 작성 시점). **모호하면 RED-first 기본**(안전측).
  - **공통 불변**: 어느 트랙이든 ① 테스트 코드 산출물 ② 작성자≠구현자 ③ TEST 단계 검증을 유지한다.
  - **state-tool 연동**: RED-first 트랙 → `verify --red-check` ON / 구현-후-검증 트랙 → 기존 동작(`--red-check` OFF). 이 분기로 §3.2.2 opt-in 구조가 정책을 그대로 집행.
- `## 2. 작성자≠구현자` — [MUST] "RED 테스트 코드 작성 주체는 EXECUTE 구현 워커(op-dev-execute)와 분리한다. RED 작성은 opal-test-agent(mode: red)가 담당한다." (R-2)
- `## 3. 테스트 불변성` — [MUST] "GREEN/fix 루핑 중 RED 테스트 파일 수정 금지. 위반 시 블로커." (C-4, reward hacking 방어 → D-13)
- `## 4. 공개 인터페이스 검증` — "내부 구현/private 결합 금지, 공개 인터페이스·관찰 행위로 검증." (R-6 → D-11)
- `## 5. graceful skip` — "테스트 인프라 부재 프로젝트/문서 전용 태스크는 RED 트랙 자동 우회 금지 — 인프라 부재 시 사용자 에스컬레이션. state-tool RED 게이트는 산출물 부재 시 skip." (제약 §하위 호환)
- `## 6. STATE 행 정책` — "RED는 EXECUTE 내부 서브스텝으로 흡수한다. 별도 STATE 행을 추가하지 않는다 (opds 10행/opd 15행 SSOT 보존)." (설계 결정 2 → H-7)
- `## 변경이력` 표.

#### 3.1.3 환경 변경
해당 없음.

#### 3.1.4 배치/마이그레이션
해당 없음.

#### 3.1.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | R-1 AC | 산출물 검사 | red-first.md에 RED→GREEN 순서 [MUST] 문장 존재 |
| TS-010 | R-1·SSOT 제약 | 산출물 검사 | opds/opd 본문이 규칙을 복제하지 않고 red-first.md 참조 (grep) |

### F-002: state-tool RED 게이트 + 테스트 불변성 (코드)

#### 3.2.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/state-tool/state_tool.py` | 코드 | ERROR_CODES 2종 추가, `verify` 확장, mark 훅 확장 | `state_tool.py:67-98, 1369-1403, 968-978` |
| 2 | `opal/tools/state-tool/tests/test_state_tool.py` | 테스트 | RED 게이트·불변성 단위 테스트 + completeness 30종 | `test_state_tool.py:1698-1962` |

#### 3.2.2 API·데이터 모델·함수 설계

**(a) ERROR_CODES 2종 추가** (`ERROR_CODES` dict, `state_tool.py:67-98`):
- [MUST] `"red_evidence_missing": "RED 증거(실패 출력) 누락 — GREEN/EXECUTE 진입 차단: {detail}"`
- [MUST] `"test_modified_in_fix": "fix 루핑 중 RED 테스트 파일 수정 거부: {files}"`

**(b) `verify` 서브커맨드 확장** — `cmd_verify(args)` (`state_tool.py:1369`):
- 신규 인자 (argparse `p_vfy`, `state_tool.py:1522-1530`):
  - `--red-check` (store_true): RED 증거 검증 모드 활성화.
  - `--changed-files` (nargs="*"): fix 루핑에서 변경된 파일 목록 (테스트 불변성 입력).
  - `--test-globs` (nargs="*"): 테스트 파일 식별 glob 패턴 (예: `tests/**`, `*_test.py`, `*.test.ts`). 프로젝트 탐지값 — 하드코딩 금지 (C-2).
  - `--fix-mode` (store_true): fix 루핑 컨텍스트임을 표시 (불변성 검사 활성화).
- 신규 헬퍼 함수 (모듈 레벨, 기존 `_check_*` 패턴 미러 — `:1295-1366`):
  - `def _check_red_evidence(lines) -> list[int]`: TEST-SCENARIO.md에서 RED 증거 섹션(예 "RED 증거"/"실패 출력" 열 또는 헤더)을 탐지. 증거 없으면 위반 라인 반환. 산출물 부재 시 호출 안 함(skip).
  - `def _match_test_files(changed_files, test_globs) -> list[str]`: `changed_files` ∩ `test_globs` (fnmatch) → 테스트로 식별된 파일 목록 반환. 표준 라이브러리 `fnmatch`만 사용 (T-11).
- 분기 로직:
  - `--red-check` 없으면 기존 동작(mock+evidence) 유지 — **하위 호환** (H-5).
  - `--red-check` + 산출물 부재 → `skipped:true` ok (graceful skip, H-4 — 기존 `:1378-1384` 패턴 재사용).
  - `--red-check` + RED 증거 누락 → `err("verify", "red_evidence_missing", detail=...)` exit 1.
  - `--fix-mode` + `_match_test_files` 결과 비어있지 않음 → `err("verify", "test_modified_in_fix", files=...)` exit 1.
  - `--fix-mode` + `--test-globs` 미지정 → 불변성 검사 skip(deterministic 입력 없음 = 검출 불가, graceful). 응답에 `immutability_check: "skipped (no test-globs)"`.

**(c) mark TEST stage 훅 확장** (`cmd_mark`, `state_tool.py:968-978`):
- 기존 TEST stage 자동 verify 훅은 **변경 없음** (mock/evidence 유지) — RED 게이트는 `--red-check` 명시 호출 전용. EXECUTE/GREEN mark 차단은 오케스트레이터가 `verify --red-check`를 호출하여 게이트하는 방식(집행 진입점 = PM/오케스트레이터의 명시 호출 + state-tool deterministic 판정). mark 자동 훅에 RED 게이트를 끼우지 않는 이유: EXECUTE 행은 stage="EXECUTE"이며 자동 verify 훅은 stage="TEST" 한정 — RED는 EXECUTE 내부 서브스텝(설계결정 2)이므로 별도 명시 게이트가 적절. (트레이드오프 기록: 자동성↓·명시성↑·하위호환↑)

> [MUST] `~/.opal/PRINCIPLES.md` §4: "Add X → Write a check that fails without X, then make it pass." / "Completion requires evidence: real run output. No evidence → not done." — RED 게이트 집행 근거.
> [MUST] TASK T-11(`state_tool.py:14`): 표준 라이브러리만 import (pytest/hypothesis 금지) — 신규 헬퍼는 `fnmatch`/`re`만 사용.
> [MUST] `docs/CONVENTIONS.md` §플랫폼 분기 격리: "스킬·에이전트 본문에 플랫폼 조건문을 추가하지 않는다" — 러너/언어/테스트 경로 하드코딩 금지, `--test-globs`로 주입.

#### 3.2.3 환경 변경
해당 없음 (표준 라이브러리만 사용). 테스트 실행: `~/.opal/.venv/bin/python -m unittest discover -s tests`.

#### 3.2.4 배치/마이그레이션
state.json 스키마 변경 없음. ERROR_CODES count 28→30 — completeness 테스트 동시 갱신.

#### 3.2.5 테스트 시나리오 (RED-first 자기적용 — 본 표가 R-5의 RED 테스트)
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-002 | R-5 AC(a) | 기능 테스트 | `verify --red-check` + RED 증거 정상 → ok exit 0 |
| TS-003 | R-5 AC(a) | 기능 테스트 | `verify --red-check` + RED 증거 누락 → `red_evidence_missing` exit 1 |
| TS-004 | R-5 AC(b) | 기능 테스트 | `verify --fix-mode --changed-files <test> --test-globs <pat>` 테스트파일 변경 → `test_modified_in_fix` exit 1 |
| TS-005 | R-5 AC(b) | 기능 테스트 | `--fix-mode` + 변경 파일이 테스트 아님 → ok exit 0 |
| TS-006 | R-5 ERROR_CODES | 산출물/단위 | ERROR_CODES에 2종 등재 + count 30 |
| TS-007 | 제약 §하위호환 | 기능 테스트 | `--red-check` + 산출물 부재 → `skipped:true` exit 0 |
| TS-008 | 제약 §하위호환 | 기능 테스트 | `--red-check` 없는 기존 verify happy/mock/evidence 비파괴 |
| TS-009 | H-5 회귀 | 회귀 테스트 | 전체 스위트(`unittest discover`) PASS (≥158+신규) |

### F-003: 파이프라인 RED→GREEN 순서 명문화

#### 3.3.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/skills/opal-pilot-dev-short/SKILL.md` | 오케스트레이터 | STEP 2/STEP 3에 red-first.md 참조 1줄 + fix 루핑 불변성 메모 | `:39-70, 144-162` |
| 2 | `opal/skills/opal-pilot-dev/SKILL.md` | 오케스트레이터 | STEP 3.5/STEP 4에 red-first.md 참조 1줄 | `:84-152` |

#### 3.3.2 설계
양 스킬에 동일 1줄 삽입 (복제 아님 — SSOT 참조): `> **[MUST] RED-first**: EXECUTE 진입 전 RED 증거 확보, fix 루핑 중 테스트 불변. 규칙 SSOT: `opal/core/references/harness/red-first.md`.` (→ D-2/D-?, H-6 회피).

#### 3.3.3 환경 변경 / 3.3.4 배치
해당 없음.

#### 3.3.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-011 | R-1·H-7 | 산출물 검사 | opds 10행/opd 15행 STATE 구조 불변 (RED 행 미추가) |

### F-004: RED 작성 주체 정의 + EXECUTE Scope 제약

#### 3.4.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/skills/op-dev-test-scenario/SKILL.md` | 스킬 | 역할 분배표에 "RED 테스트 코드 작성 = opal-test-agent(mode:red)" 행 | `:50-60` |
| 2 | `opal/agents/opal-test-agent/AGENT.md` | 에이전트 | `red` 모드 정의 — M1 시나리오→실패 테스트 코드 변환·실행·RED 증거 기록 | `:40-92, 137-150` |
| 3 | `opal/skills/op-dev-execute/SKILL.md` | 스킬 | 가드레일 #6 "RED 테스트 파일 수정 금지(위반 시 블로커)" 추가 | `:94-102` |

#### 3.4.2 설계
- **설계 결정 1 답**: opal-test-agent에 `mode: red` 신설 (안 d 변형). 근거 — (i) 디스패치 의무: 테스트 코드 작성은 코드 작업이므로 워커가 수행해야 함(`opal-harness.md:23-28`). (ii) 작성자≠구현자: test-agent ≠ op-dev-execute 구현 워커 — 기존 분리 유지(`opal-test-agent/AGENT.md:24,139` self-confirming 방어 철학과 일치). (iii) 토큰 효율: 기존 에이전트 확장 — 신규 에이전트 미신설. 마크다운 시나리오(M1)는 여전히 PM+페어 직접 작성, **실행 가능한 RED 테스트 코드 변환·실패 증거 확보만** test-agent(red 모드)가 수행. RED 작성 시점 = TEST-SCENARIO 단계 직후·EXECUTE 진입 전(EXECUTE 내부 서브스텝).
- [MUST] op-dev-execute 가드레일 #6: "RED 테스트 파일(opal-test-agent가 작성한 테스트)을 수정하지 않는다. 구현은 프로덕션 코드만 변경. 테스트 파일 수정 필요 시 블로커 보고." → F-002 `verify --fix-mode --changed-files`로 deterministic 집행.

#### 3.4.3 환경 변경 / 3.4.4 배치
해당 없음.

#### 3.4.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-012 | R-2 AC | 산출물 검사 | op-dev-execute에 "RED 테스트 파일 수정 금지" 가드 + test-agent red 모드 정의 존재 |

### F-005: 테스트 스택·위치 탐지 절차

#### 3.5.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md` | 가이드 | "스택·위치 탐지" 절 신설 (4단계 + 에스컬레이션) | `:98-129` |

#### 3.5.2 설계
[MUST] 탐지 우선순위 4단계 (C-2): ① `docs/CONVENTIONS.md`(테스트 위치 규칙) → ② 스택 문서(`docs/BACKEND.md`/`FRONTEND.md` 등) → ③ 설정파일(`package.json`/`pyproject.toml`/`go.mod`) → ④ 기존 테스트 관례(글로브 탐색). [MUST] "테스트 러너 부재 시 자동 우회 금지 — 사용자 에스컬레이션." 특정 프레임워크 하드코딩 없음.

#### 3.5.3 환경 변경 / 3.5.4 배치
해당 없음.

#### 3.5.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-013 | R-3 AC | 산출물 검사 | 가이드에 탐지 4단계 순서 + 에스컬레이션 규칙 + 하드코딩 부재 |

### F-006: 모듈 미러링 배치·명명·추적 + 테스트 @header

#### 3.6.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md` | 가이드 | 모듈 미러링 배치 + 케이스명 프리픽스 규칙 | `:98-143` |
| 2 | `opal/skills/op-dev-test-scenario/SKILL.md` | 스킬 | §4 매핑표 스키마에 "테스트 파일:케이스" 열 추가 | `:129-133` |
| 3 | `opal/core/references/harness/header-rules.md` | 참조 | 테스트 파일 @header 선택 필드 `task`/`scenarios` 정의 | `:30-43` |

#### 3.6.2 설계
- [MUST] 가이드: "모듈 1개=테스트 파일 1개. 후속 태스크는 기존 파일에 케이스 추가. 케이스명 프리픽스 포맷 `[T{NNN}/L{계층}-{AC}]` (예: `[T016/L1-AC1]`)." (C-3)
- §4 매핑표 6열로 확장: `AC ID | 가설 ID | 검증 계층 | 시나리오 | 테스트 파일:케이스 | 비고`.
- header-rules: 테스트 파일(`layer: test`) 선택 필드 `task`(태스크 번호), `scenarios`(연결 S-ID 목록) 추가.

#### 3.6.3 환경 변경 / 3.6.4 배치
해당 없음.

#### 3.6.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-014 | R-4 AC | 산출물 검사 | 가이드 모듈 미러링+프리픽스 + §4 "테스트 파일:케이스" 열 + header-rules task/scenarios 필드 |

### F-007: 공개 인터페이스 검증 규율 + 변경이력·배포 정합

#### 3.7.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md` | 가이드 | 공개 인터페이스 검증 규율 1~2줄 | `:124-129` |
| 2 | `opal/core/references/harness/coding-principles.md` | 참조 | §3 TEST-SCENARIO 체크에 공개 인터페이스 검증 1행 | `:47-52` |
| 3 | 변경된 전 문서 | 문서 | 변경이력 016 행 추가 | `docs/CONVENTIONS.md:194-198` |
| 4 | `tasks/016-.../DONE.md` | 문서 | install 재배포 필요 여부 기재 | 제약 §배포 경계 |

#### 3.7.2 설계
- [MUST] 규율: "테스트는 내부 구현/private에 결합하지 않고 공개 인터페이스·관찰 가능 행위(반환값/exit code/관측 출력)로 검증한다." (R-6 → D-11). state-tool 자기적용 — RED 테스트는 `cmd_verify` 내부가 아닌 exit code/JSON 응답으로 검증(공개 행위).
- [MUST] 변경이력: 변경 전 문서마다 `| vX.Y | 2026-06-09 HH:mm | <내용> (016) |` 행 (CONVENTIONS.md §변경이력 작성 의무).

#### 3.7.3 환경 변경 / 3.7.4 배치
변경된 스킬·에이전트·참조·도구 전체 install 재배포 — DONE.md 기재.

#### 3.7.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-015 | R-6 AC | 산출물 검사 | test-scenario-guide + coding-principles에 공개 인터페이스 규율 존재 |
| TS-016 | R-7 AC | 산출물 검사 | 전 변경 문서에 016 변경이력 행 + DONE.md에 install 메모 |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)

| Phase | 기능 | Step | agent | 실행 | 비고 |
|-------|------|------|-------|------|------|
| 1 | F-001 | 1 | opal-task-agent | 단독 | SSOT 선행 (모든 후속 참조) |
| 2 | F-002 | 2, 3 | opal-task-agent | 순차 | RED-first 자기적용 (RED 테스트→구현) |
| 3 | F-003·F-004·F-005·F-006·F-007 | 4, 5, 6 | opal-task-agent | 순차(동일 파일군 충돌) | 문서 일괄 수정 |
| 4 | F-007 | 7 | PM 직접 | 단독 | 변경이력·DONE.md (docs/ 갱신) |

### 4.2 실행 체크리스트
> 총 7개 Step | Phase 4개 | 실행 모드: 복잡 (변경 파일 9개·다중 모듈·신규 패턴)

#### Step 1: RED-first SSOT 하네스 문서 작성 + 하네스 등록
- [x] 완료
- **소속 기능**: F-001
- **영역**: 참조
- **agent**: opal-task-agent
- **파일**: `opal/core/references/harness/red-first.md`(신규), `opal/core/references/opal-harness.md`(§2 테이블)
- **작업 내용**: §3.1.2 섹션 구조(0~6 + 변경이력)대로 red-first.md 작성. 헌법 §4 참조 상속, 재서술 금지. opal-harness.md §2 하네스 모듈 테이블에 행 추가.
- **완료 기준**: red-first.md에 RED→GREEN [MUST] 문장·**적용 기준(하이브리드 자동분기)**·작성자≠구현자·테스트 불변성·graceful skip·STATE 행 정책 존재. opal-harness 테이블에 등록.
- **테스트**: TS-001, TS-010
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 2: state-tool RED 테스트 작성 (RED — 실패 확인)
- [x] 완료
- **소속 기능**: F-002
- **영역**: 코드(테스트)
- **agent**: opal-task-agent
- **파일**: `opal/tools/state-tool/tests/test_state_tool.py`
- **작업 내용**: TS-002~TS-009 시나리오를 `unittest` 테스트로 작성. 신규 인자(`--red-check`/`--changed-files`/`--test-globs`/`--fix-mode`)·ERROR_CODES 2종·count 30 검증. **구현 전 실행하여 실패(RED) 확인** 후 exit code≠0 증거를 TEST-SCENARIO.md RED 증거 칸에 기록.
- **완료 기준**: 신규 테스트가 미구현 상태에서 실패(RED 증거 확보). 기존 158 테스트는 영향 없음.
- **테스트**: TS-002~TS-009 (RED 단계)
- **실행 방법**: sub-agent
- **의존**: Step 1

#### Step 3: state-tool RED 게이트·불변성 구현 (GREEN)
- [x] 완료
- **소속 기능**: F-002
- **영역**: 코드
- **agent**: opal-task-agent
- **파일**: `opal/tools/state-tool/state_tool.py`
- **작업 내용**: §3.2.2 (a)ERROR_CODES 2종 (b)`verify` 확장+헬퍼 2종(`_check_red_evidence`/`_match_test_files`) (c)argparse 인자 4종. @header description 갱신. **Step 2 RED 테스트를 GREEN으로 전환**. RED 테스트 파일은 수정 금지.
- **완료 기준**: `~/.opal/.venv/bin/python -m unittest discover -s tests` 전체 PASS (≥158+신규). 표준 라이브러리만 사용.
- **테스트**: TS-002~TS-009 (GREEN 전환), TS-006 completeness
- **실행 방법**: sub-agent
- **의존**: Step 2

#### Step 4: 파이프라인 순서 + RED 작성주체 + Scope 제약 (opds/opd/test-scenario/test-agent/execute)
- [x] 완료
- **소속 기능**: F-003, F-004
- **영역**: 오케스트레이터/스킬/에이전트
- **agent**: opal-task-agent
- **파일**: `opal-pilot-dev-short/SKILL.md`, `opal-pilot-dev/SKILL.md`, `op-dev-test-scenario/SKILL.md`, `opal-test-agent/AGENT.md`, `op-dev-execute/SKILL.md`
- **작업 내용**: §3.3.2 red-first 참조 1줄(복제 금지) + §3.4.2 test-agent red 모드 정의 + 역할 분배표 행 + execute 가드레일 #6.
- **완료 기준**: opds/opd RED-first 참조, test-agent red 모드, execute "RED 테스트 파일 수정 금지" 가드 존재. SSOT 복제 없음.
- **테스트**: TS-011, TS-012
- **실행 방법**: sub-agent
- **의존**: Step 1, Step 3

#### Step 5: 테스트 스택 탐지 + 모듈 미러링·@header + 공개 인터페이스 규율 (가이드/header-rules/coding-principles)
- [x] 완료
- **소속 기능**: F-005, F-006, F-007
- **영역**: 가이드/참조
- **agent**: opal-task-agent
- **파일**: `op-dev-test-scenario/references/test-scenario-guide.md`, `op-dev-test-scenario/SKILL.md`(§4 열), `opal/core/references/harness/header-rules.md`, `opal/core/references/harness/coding-principles.md`
- **작업 내용**: §3.5.2 탐지 4단계+에스컬레이션, §3.6.2 모듈 미러링·프리픽스·§4 열, §3.7.2 공개 인터페이스 규율 + header-rules task/scenarios 필드.
- **완료 기준**: 탐지 4단계·미러링·프리픽스·§4 6열·header task/scenarios·공개 인터페이스 규율 모두 기재. 하드코딩 부재.
- **테스트**: TS-013, TS-014, TS-015
- **실행 방법**: sub-agent
- **의존**: Step 1

#### Step 6: 변경이력 016 행 추가 (전 변경 문서)
- [x] 완료
- **소속 기능**: F-007
- **영역**: 문서
- **agent**: opal-task-agent
- **파일**: Step 1·4·5에서 변경한 모든 SKILL.md/AGENT.md/참조 문서 + state_tool.py @header
- **작업 내용**: 각 문서 변경이력 표에 `| vX.Y | 2026-06-09 HH:mm | <내용> (016) |` 행 추가 (KST date 도구 사용).
- **완료 기준**: 변경된 전 문서에 016 행 존재.
- **테스트**: TS-016 (일부)
- **실행 방법**: sub-agent
- **의존**: Step 1, 4, 5

#### Step 7: docs/ 갱신 판단 + DONE.md install 재배포 메모
- [x] 완료
- **소속 기능**: F-007
- **영역**: 문서
- **agent**: PM 직접
- **파일**: `docs/ARCHITECTURE.md`/`docs/CONVENTIONS.md`(갱신 필요 시), `tasks/016-.../DONE.md`
- **작업 내용**: RED-first 트랙·신규 하네스 문서가 ARCHITECTURE/CONVENTIONS 내용에 영향 주는지 판단(새 패턴 도입 → 검토). DONE.md에 install 재배포 필요(전 변경 파일 `~/.opal/` 배포) 기재.
- **완료 기준**: docs/ 갱신 여부 판단 완료. DONE.md install 메모 기재.
- **테스트**: TS-016 (일부)
- **실행 방법**: direct
- **의존**: Step 6

### 4.3 병렬/순차 판별 근거
| 관계 | 근거 |
|------|------|
| Step 1 → Step 2~7 | SSOT 선행 — 전 후속이 red-first.md 참조 |
| Step 2 → Step 3 | RED-first 자기적용 — 테스트(RED) 먼저, 구현(GREEN) 후 (제약 §자기적용) |
| Step 4 ∥ Step 5 (논리) → 순차 처리 | 둘 다 op-dev-test-scenario 파일군 공유(가이드/SKILL) → 파일 충돌 방지 위해 순차 |
| Step 6 → Step 1·4·5 후행 | 변경이력은 변경 완료 후 |
| Step 7 → Step 6 후행 | docs/ 갱신·DONE.md는 최종 |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA
| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | RED-first SSOT 문서 존재·헌법 상속 | TS-001, TS-010 | [MUST] 문장 존재 + opds/opd 복제 없음 |
| F-002 | RED 게이트·불변성·ERROR_CODES·skip | TS-002~TS-009 | 전체 unittest PASS + 신규 2 ERROR_CODES + 회귀 0 |
| F-003 | 파이프라인 순서·STATE 행 불변 | TS-011 | opds 10행/opd 15행 보존 |
| F-004 | 작성주체·Scope 제약 | TS-012 | test-agent red 모드 + execute 가드 #6 |
| F-005 | 스택 탐지 4단계 | TS-013 | 순서+에스컬레이션+하드코딩 부재 |
| F-006 | 미러링·프리픽스·@header·§4 열 | TS-014 | 전 항목 기재 |
| F-007 | 공개 인터페이스 규율·변경이력·배포 | TS-015, TS-016 | 규율 존재 + 016 행 + DONE 메모 |

### 5.2 회귀 테스트
- [ ] state-tool 기존 158 unittest 비파괴 (TS-009)
- [ ] 기존 `verify`(--red-check 없는 호출) 동작 비파괴 (TS-008)
- [ ] opds/opd STATE 행 구조 비파괴 (TS-011)

### 5.3 코드/문서 품질
- [ ] state_tool.py 표준 라이브러리만 사용 (T-11)
- [ ] 변경 전 문서 변경이력 016 행 (CONVENTIONS §변경이력 의무)
- [ ] SSOT 단일성 — 규칙 복제 없음 (제약 §SSOT)

### 5.4 보안
- [ ] state_tool.py에 하드코딩 시크릿 없음
- [ ] 테스트 러너/언어/경로 하드코딩 없음 (`--test-globs` 주입, C-2)

---

## 6. 복잡도 판별
| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 7개 | 복잡 |
| 변경 파일 수 | 9개 (신규 1 + 수정 8, DONE 제외) | 복잡 |
| 모듈 범위 | 다중 (state-tool 코드 + 하네스 + 스킬 4 + 에이전트 1 + 참조 2) | 복잡 |
| 작업 유형 | 신규 패턴 도입(RED-first) + 코드 기능 추가 | 복잡 |
| 외부 의존성 | 없음 (표준 라이브러리) | 단순 |
| **실행 모드** | **복잡** | |

---

## 7. 실행 아키텍처 (복잡 모드)

### C-1. 에이전트 토폴로지
단일 전문 에이전트 프로젝트(opal-task-agent — `docs/PROJECT.md:79`)이므로 모든 Step을 opal-task-agent로 순차 디스패치. 파일 충돌 회피를 위해 Batch 직렬화:
- Batch 1: Step 1 (SSOT)
- Batch 2: Step 2 → Step 3 (RED→GREEN 직렬, 자기적용)
- Batch 3: Step 4 → Step 5 (문서 파일군 충돌 회피 직렬)
- Batch 4: Step 6 → Step 7 (변경이력·마감)

### C-2. 스킬 요구사항
기존 스킬(op-dev-execute generalist 가이드)로 충분. 신규 스킬 불필요. RED-first 규칙은 red-first.md(인라인 지침형 SSOT)로 충분 — 별도 스킬 갭 없음.

### C-3. 도구 요구사항
- state-tool 자체(테스트 대상). 테스트 러너: `~/.opal/.venv/bin/python -m unittest discover -s tests` (기존). KST date 도구(`~/.opal/tools/date/date.js`) — 변경이력.
- 신규 CLI/MCP/패키지 없음.

### C-4. 테스트 전략
TEST-SCENARIO.md L1/L2 시나리오(S-1~S-11)를 op-dev-test-agent가 M1(unittest) 방식으로 실행. RED-first 자기적용: Step 2에서 RED 작성→실패 증거 확보, Step 3에서 GREEN 전환. 회귀: 전체 스위트 재실행.

---

## 8. 기술 컨텍스트

### 8.1 기술 스택
| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| 도구 코드 | Python 3 stdlib (`argparse`/`re`/`fnmatch`/`unittest`) | (커뮤니티 스킬 미적용 — pytest 미사용) |
| 문서 | Markdown + YAML frontmatter | - |
| 시점 | Node.js date 도구 | - |

### 8.2 사용 MCP
| MCP | 조회 결과 요약 |
|-----|--------------|
| (없음) | 외부 라이브러리 API 조회 불요 — 표준 라이브러리만 |

### 8.3 참조 문서 (설계 결정 근거)
| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-0 | 기획 | TASK.md | `tasks/016-260609-opds-tdd-red-first-track/TASK.md` | 확정 방향 C-1~C-4, 요구사항 R-1~R-7 |
| D-1 | 설계 | OPAL 헌법 | `~/.opal/PRINCIPLES.md` §4 | RED 게이트·증거·목업 금지 근거 |
| D-2 | 소스 | opds SKILL | `opal/skills/opal-pilot-dev-short/SKILL.md` | 파이프라인·STATE 10행 |
| D-3 | 소스 | opd SKILL | `opal/skills/opal-pilot-dev/SKILL.md` | STEP 3.5·STATE 15행 |
| D-4 | 소스 | op-dev-test-scenario SKILL+가이드 | `opal/skills/op-dev-test-scenario/` | 역할 분배·§4 매핑표·탐지 |
| D-5 | 소스 | op-dev-execute SKILL | `opal/skills/op-dev-execute/SKILL.md` | 가드레일·Step 3-S |
| D-6 | 소스 | opal-test-agent | `opal/agents/opal-test-agent/AGENT.md` | red 모드 추가 지점 |
| D-7 | 소스 | state_tool.py + tests | `opal/tools/state-tool/` | verify 확장·ERROR_CODES·테스트 |
| D-8 | 설계 | header-rules | `opal/core/references/harness/header-rules.md` | 테스트 @header 필드 |
| D-9 | 설계 | coding-principles | `opal/core/references/harness/coding-principles.md` | 공개 인터페이스 규율 |
| D-10 | 설계 | CONVENTIONS | `docs/CONVENTIONS.md` | 변경이력·하드코딩·배포 경계 |
| D-11 | 외부 | aihero TDD skill | [aihero TDD skill](https://www.aihero.dev/skills-tdd) | RED/GREEN 분리·공개 인터페이스 |
| D-12 | 외부 | Codex CLI TDD | [Codex CLI TDD](https://codex.danielvaughan.com/2026/04/10/codex-cli-test-driven-development-workflow/) | exit code 게이트 |
| D-13 | 외부 | METR reward hacking | [METR](https://metr.org/blog/2025-06-05-recent-reward-hacking/) | 테스트 약화·삭제 방어 |
| D-14 | 설계 | opal-harness | `opal/core/references/opal-harness.md` §2 | 하네스 모듈 등록 |

---

## 9. 리스크 및 대응 (기능-리스크 연결)
| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| R-1 | ERROR_CODES count 28→30 변경으로 `test_error_codes_count` 회귀 | F-002 | P1 | Step 3에서 completeness 테스트 동시 갱신 (TS-006) |
| R-2 | mark 자동 훅(stage=TEST)과 RED 게이트(EXECUTE 서브스텝) 진입점 불일치 | F-002 | P1 | RED 게이트는 `--red-check` 명시 호출 전용 — mark 훅 비변경(하위호환). §3.2.2(c) 트레이드오프 명시 |
| R-3 | 테스트 불변성 입력 결정 방식 — git diff 비결정성 | F-002 | P2 | `--changed-files`+`--test-globs` 명시 입력(deterministic). git diff 미사용 |
| R-4 | SSOT 규칙을 opds/opd에 중복 서술 (발췌·복제 금지 위반) | F-001·F-003 | P1 | red-first.md 단일 SSOT + 참조 1줄만. TS-010 grep 검사 |
| R-5 | 문서/코드 불일치 — pytest 표기 가능성 | F-002 | P2 | 코드가 SSOT — 러너는 stdlib `unittest`. 시나리오·체크리스트에 unittest 명시 (문서 D-? 불일치 미발견) |

---

## 설계 피드백 (미해결 빈틈 / decision_required)

해결됨(설계로 확정):
1. **RED 작성 주체** → opal-test-agent `mode: red` (작성자≠구현자 + 디스패치 의무 + 토큰 효율 모두 충족). §3.4.2.
2. **STATE 행 구조** → EXECUTE 내부 서브스텝 흡수, 별도 행 미추가 (opds 10행/opd 15행 SSOT 보존). §3.1.2 §6.
3. **state-tool 게이트 방식** → 기존 `verify` 확장(`--red-check`), 신규 ERROR_CODES `red_evidence_missing`/`test_modified_in_fix`, 불변성 입력=`--changed-files`+`--test-globs`(git diff 미사용). §3.2.2.
4. **하위 호환·graceful skip** → 산출물/인프라 부재 시 `skipped:true` ok + `--red-check` 미지정 시 기존 동작. §3.2.2 분기.
5. **SSOT 위치** → 하네스 신규 문서 `red-first.md`에 SSOT, opds/opd/스킬/에이전트 참조 상속. §3.1.

decision_required (사용자/도메인 결정 권고): **없음.** (영역 간 용어 불일치 미검출. citation-rules §7 terminology_mismatch 해당 없음.)

---

## 에스컬레이션 권고

> **Full Task(opd) 에스컬레이션 권고: 검토 필요 (경계선).**
> - 변경 파일 9개(신규 1 + 수정 8) — opds PLAN 결과 에스컬레이션 기준 "≥10개"에 1개 미달이나 근접 (`opal-pilot-dev-short/SKILL.md:205`).
> - 다단계 기술 의사결정 5건 해결 — "다단계 기술 의사결정" 기준에 해당 (`SKILL.md:206`). 단, 본 PLAN에서 전부 설계 확정하여 EXECUTE는 결정 추종.
> - state-tool 코드는 RED-first 자기적용으로 테스트가 보호 → Short Task 범위 내 처리 가능.
> - **권고**: opds 유지 가능하나, PM/사용자가 9개 파일·복잡 모드를 근거로 opd 전환을 선택할 수 있음. 전환 결정은 PM/사용자.
