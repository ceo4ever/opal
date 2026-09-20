# PROJECT-DESIGN (초안) — E2E 여정·조각 라이브러리

> 입력: `INTENT.md`(승인) · `docs/proposals/archives/e2e-journey-fragment-library.md` · `tasks/127-260912-oppl-E2E-하네스-구현/CONTRACT.md` · 코드 실측
> 기계 SSOT: `.oppb-workgraph-spec.json`(미니 태스크·lease·완료조건) · `.oppb-probe-commands.json`(명령·미추적 쓰기 관측 입력)
> 이 문서는 spec 필드를 옮겨 적지 않는다. spec이 담지 못하는 **판정 근거**만 소유한다.

## 슬라이스 근거

| capability ID | 비즈니스 대상·변경 이유·정책 | 수직 완결성 근거 | 합치기/나누기 판정 |
|---|---|---|---|
| T01 E2E 저장소 경계와 산출물 수명 | 대상: E2E 산출물의 **추적 여부와 수명**. 변경 이유: 제안서 §3이 "가르는 축은 git 추적 여부"라고 규정하고, 현재 기본 산출물 경로 `${TMPDIR}/opal-e2e-runs`(`lib/e2e/orchestrator.py:82`·`:1652`)는 실패 시 `/var/folders/...`를 뒤져야 한다 | 이 태스크만으로 사용자가 `.e2e/`에 산출물을 받고 `git status`가 깨끗하며 오래된 run이 회수된다. 폴더·무시 규칙·보존 정책은 한 정책의 세 면이다 | **합침**. `docs/e2e/`·`.opal/e2e/`·`.e2e/` 세 폴더는 전부 신규(실측: 하나도 없음)이고 `.gitignore` 1줄(선례 `.gitignore:41` `.oppl-run/`)과 보존 정책이 같은 변경 이유를 공유한다 |
| T02 증적 비밀 마스킹 | 대상: 증적에 남는 **비밀값**. 변경 이유: `lib/e2e/redaction.py`의 `SECRET_HEADER_NAMES`(`:26`)·`SECRET_QUERY_KEYS`(`:39`)가 **키 이름 집합**이고 `redact_value()`(`:175`) dict 분기(`:196`)가 그 집합의 키만 `MASK`로 바꾸므로, `{"kind":"fill","target":"#pw","value":"…"}`는 키가 `value`라 걸리지 않는다 | 이 태스크만으로 기존 모든 E2E 실행의 `actions.jsonl`이 안전해진다. 조각 도입과 무관하게 단독 가치가 선다 | **나눔**. 보안 경계이고(`§분할한다` "보안·migration처럼 위험과 검증 경계를 분리"), 변경 지점이 `evidence.py` 단일 관문 한 곳으로 좁혀져 독립 rollback이 가능하다 |
| T03 driver 연산 이행 검증과 실행 전 후보 게이트 | 대상: **driver가 실제로 할 수 있는 연산**. 변경 이유: 제안서 §7이 Q-6(ops 게이트)과 적합성 스위트를 §7 선행 조건 [MUST]로 규정하고, 태스크 127 실측에서 `agent_browser`가 `probe`·`open`·`close` 3연산만 구현하고도 자체 테스트 30건을 통과해 AC-4를 구조적으로 막았다 | 게이트(실행 전 거름)와 `driver-verify`(등록 전 검사)는 **같은 판정식의 사전/사후 두 적용**이다. 하나만 있으면 다른 쪽 구멍으로 부분 driver가 들어온다 | **합침**. 둘 다 `DRIVER_OPERATIONS`(`lib/e2e/drivers/__init__.py:44`) 8연산 집합을 공유하고 `scenario_adapter`의 요구 연산 추출을 공동 소비한다. 나누면 execution packet에 같은 문맥을 두 번 주입해야 한다 |
| T04 선언형 driver 등록과 후보 순서 데이터화 | 대상: **새 브라우저 추가 비용**. 변경 이유: 제안서 §7 ADD-1 실증 — 새 driver 추가에 4곳 수정 + `CONTRACT.md` 3곳 개정이 필요했다 | JSON 한 장을 두면 driver가 등록되고 순서를 바꿔 1순위로 올리는 것까지 한 사람이 끝까지 쓴다 | **합침**. "등록"과 "순서"를 나누면 등록만 된 driver를 쓸 방법이 없다. 둘 다 `resolve_candidates()`(`drivers/__init__.py:311`) 한 함수의 입력이다 |
| T05 여정·조각 라이브러리 | 대상: **재사용되는 사용자 여정**. 변경 이유: 제안서 §1·§4 — 태스크마다 시나리오를 처음부터 새로 쓰는 비용 | 조각을 등록하고 여정이 참조하고 전개가 증적에 남는 것까지가 하나의 사용 경험이다 | **합침**(C-4+C-7). C-4(중복 판정 범위)는 단독 수용 가치가 없는 내부 제약 해소이며(`§합친다` "단독 수용 가치가 없음"), 조각 전개가 없으면 재현조차 되지 않는다. 같은 실행 경로를 연속 수정한다 |
| T06 신선도 원장과 재실행 생략 기록 | 대상: **재실행 범위**. 변경 이유: 제안서 §5 + brain `skip-gate-key-must-include-execution-identity.md` — 대상만 담은 키는 설정 한 줄로 약한 증적을 재인용시킨다 | 키 판정·원장·생략 기록이 함께 있어야 "생략이 침묵하지 않는다"가 성립한다 | **합침**. C-9(기록)를 떼면 C-8(키)이 070 실패모드를 그대로 만든다 |
| T07 `//e2e` 발동층과 여정 승격 판정 | 대상: **사람이 쓰는 입구와 자산 승격**. 변경 이유: 제안서 §1 실측 2 — `e2e run`은 `--scenario <id>`만 받고 시나리오를 만드는 수단이 없다(발동층 부재) | 스킬 3모드 + 승격 판정이 있어야 여정이 실제로 `docs/e2e/`에 누적된다 | **합침**. 스킬(C-10)과 승격 게이트(C-12)를 나누면 "도구 변경"과 "그 도구를 쓰는 스킬"의 수평 분할이 된다 — 금지 대상이다. 제안서 §3 승격 표가 "승격 자격은 도구가 `pass` 증적으로 판정, 사람은 조각화 검토만"으로 둘을 한 흐름에 묶는다 |

**레이어 이름 태스크 없음**: 7개 모두 비즈니스 대상 용어이며 `api-only`·`ui-only`·`schema-only` 형태가 없다. 각 capability 내부의 코드/매니페스트/문서/테스트 work item은 `executors[]`에 있다.

## 병렬 판정

Controller `LEASE_AXES` 네 축으로 표현한 결과다. 나머지 세 축(계약·비즈니스 규칙·복구)은 `contracts`와 완료조건 ID 교집합으로 환원했다.

| A | B | 7축 교집합 검사 결과 | parallel_eligible | 근거 |
|---|---|---|---|---|
| T01 | T02 | tracked ∅ (T01: `.gitignore`·`docs/e2e/**`·`.opal/e2e/README.md`·`orchestrator.py`·`test_tool.py` / T02: `redaction.py`·`evidence.py`·신규 테스트 1개) · contracts ∅ · runtime ∅(T02는 `repo-git-index`·`e2e-artifact-root` 어느 쪽도 점유하지 않는다) · acceptance ∅(AC-STORAGE-LIFECYCLE vs AC-EVIDENCE-SECRET) | **true** | T02의 변경은 마스킹 **판정 규칙**(`redaction.py`)과 그것을 강제하는 단일 관문(`evidence.py`, `@header`가 "모든 증적 쓰기가 이 모듈을 거치고 저장 직전 반드시 redaction을 통과"로 명시)에 갇힌다. 두 파일 밖으로 나가면 lease 밖이므로 Controller가 `scope_violation`으로 잡는다 — 산문 약속이 아니라 도구 집행이다 |
| T02 | T03 | tracked ∅ · contracts ∅(T02 `task127-C-6`·`evidence-single-gateway-A.12` vs T03 `driver-8op-B.2`·`candidate-record-A.1.2`·`task127-C-3`) · runtime ∅(T02 공집합) · acceptance ∅ | **true** | T02는 `depends_on`이 없고 lease가 두 파일에 갇혀 있어 T01·T03·T04 중 어느 것과도 동시에 돌 수 있다. T05가 T02를 선행으로 잡으므로 늦어도 T05 전까지만 끝나면 된다 |
| T02 | T04 | 위와 동일 — 네 축 전건 ∅ | **true** | 같은 근거. 실제 동시 실행 폭은 `max_active_runners 2`가 상한을 준다 |
| T01 | T03~T07 | tracked 교집합 有 — `orchestrator.py`·`test_tool.py` | false | `depends_on`으로 순차 고정(T03이 T01을 선행) |
| T02 | T05 | tracked 교집합 有 가능(`evidence.py` 전개 증적) + 제안서 §4 "이 구멍을 막는 것이 조각 도입의 **선행 조건**" | false | T05가 T02를 `depends_on` |
| T03 | T04 | tracked 교집합 有 — `drivers/__init__.py`·`orchestrator.py` · contracts 교집합 有 — `driver-8op-B.2` · 제안서 §7 "[MUST] 부분 driver를 1순위에 두려면 Q-6(ops 게이트)이 선행한다" | false | 인과·파일 양쪽에서 순차. T04가 T03을 `depends_on` |
| T04 | T05 | tracked 교집합 有 — `orchestrator.py`(T04는 `resolve_candidates` 호출부 `orchestrator.py:1239`, T05는 조각 전개 배선) | false | 증명 불가가 아니라 **실제 충돌**이다. T05가 T04를 `depends_on` |
| T05 | T06 | tracked 교집합 有 — `orchestrator.py`·`test_tool.py` · 신선도 키가 조각 해시 집합을 입력으로 받음 | false | T06이 T05를 `depends_on` |
| T06 | T07 | tracked 교집합 有 — `test_tool.py` · `status` 모드가 원장을 읽음 | false | T07이 T06을 `depends_on` |

**병렬 후보는 T02를 축으로 한 3쌍(T01·T03·T04 각각과)뿐이고 나머지는 전건 순차다. 구조적 이유**: `orchestrator.py`(83KB 단일 모듈)와 `test_tool.py`(argparse 라우터)가 E2E 변경의 공통 통로다. 7개 중 6개가 둘 중 하나를 쓴다. `max_active_executors 2`(INTENT 예산)와도 맞는 폭이므로 분할을 더 밀어붙이지 않았다.

### P3 실측 보정

P3 실 run에서 Runner와 독립 Verifier가 각자 전체 test-tool 스위트를 동시에 실행하자
`dashboard/frontend/dist` 생성·정리 구간이 겹쳐 T02 검증이 두 번 실패했고, 단독 재시도에서는
436건이 통과했다. tracked write lease가 분리돼도 **전체 회귀의 작업공간 부수효과**는 분리되지
않으므로 운영 workgraph는 `T01 → T02 → T03`으로 직렬화한다. 또한 T01 ignore 검증은 존재하지
않는 디렉터리 자체가 아니라 `git check-ignore --no-index .../.e2e/probe`를 검사한다. 이 보정이
P2의 정적 병렬 후보 판정보다 우선한다.

### 미추적 쓰기 힌트 (probe 입력 — lease 아님)

`lease.ephemeral_writes`는 전건 비워 두었다. 봉인은 P2.2 probe의 책임이고 이 스킬은 힌트만 남긴다.

| 태스크 | 힌트 경로 | 예상 정책 | 관측 명령(`.oppb-probe-commands.json`) |
|---|---|---|---|
| T01 | `.e2e/artifacts/<run-id>/` · `.e2e/scratch/` · `${TMPDIR}/opal-e2e-runs/` | `exclusive`(run-id namespace) | `bootstrap-e2e-paths` · `probe-e2e-clean-dryrun` |
| T02 | 테스트별 `tempfile.TemporaryDirectory()` (`OPAL_E2E_ARTIFACT_DIR` override, 선례 `tests/test_red_s4_no_repo_pollution.py:54,57`) | `attempt_namespaced` | `bootstrap-e2e-paths` |
| 전건 | `opal/tools/test-tool/**/__pycache__/` | `shared_immutable` 아님 — 재생성 가능 | `build-compileall` |
| T06 | `.e2e/freshness.json` | `exclusive` | `bootstrap-e2e-paths` |

T01↔T02 병렬 판정은 위 두 힌트가 **서로 다른 루트**(저장소 내 `.e2e/` vs 프로세스별 임시 디렉터리)라는 전제 위에 있다. probe가 이 전제를 깨는 관측을 내면 T01∥T02를 취소하고 순차로 내려야 한다 — PM 판정 항목 ③.

## 계약 경계

| 계약 ID | producer | consumer | 동결 여부 |
|---|---|---|---|
| `task127-C-1`(profile·status 5종·exit 0/6/7/18/19/20, `e2e_contract.py`·`lib/scenario.py` 변경 0) | 태스크 125·127 | 전 미니 태스크 | **동결 — 읽기만**. INTENT 제외 범위 "exit 계약 재정의 0"과 같은 선. 어떤 태스크의 `tracked_writes`에도 두 파일이 없다 |
| `task127-C-6`(증적 저장 전 redaction, 실패 시 원문 미보존·`infra_error`) | 태스크 127 | T02 | **동결 — 강화만**. C-1(INTENT)은 판정 **대상**을 넓히는 변경이지 실패 계약을 무르는 변경이 아니다 |
| `task127-C-3`(`provider_unavailable`에만 후보 전환) | 태스크 127 (`CONTRACT.md:733` "예외 목록을 두지 않는다") | T03·T04 | **동결**. ops 게이트는 후보 **선정 전 필터**이지 전환 조건이 아니다 |
| `C-DRV-3`(기본 후보 순서 + 재정의 가능) | `CONTRACT.md:565`·`drivers/__init__.py:71` | T04 | **동결된 기본값 + 이미 열린 주입점**. `resolve_candidates(..., candidate_order=None)`(`:311`, 기본값 적용 `:337`)이 ADD-1에서 구현됨 — 남은 것은 파일 입력 경로뿐 |
| `driver-8op-B.2`(`DRIVER_OPERATIONS` 8연산 이름) | `drivers/__init__.py:44` | T03·T04 | **동결**(계약 표면). 새 연산을 만들지 않고 이행 여부만 판정한다 |
| `S-27-duplicate-signature-scope` | 동결 RED `tests/test_red_s27_no_retry_on_product_failure.py` (d-1, `:224`) | T05 | **동결된 단언 + 범위 정정**. 기대 계약("실패 뒤 같은 연산 반복 = retry 금지")은 불변이고, 조각 **전개분**과 본문을 구분 집계하도록 측정 범위만 좁힌다. INTENT 비가역 제약 "동결 RED 단언 약화 금지"의 경계선이 여기다 |
| `FIDELITY_ORDER`(`lib/scenario.py:119`) | 태스크 125 | T06 | **동결 — 참조만**. INTENT 제외 범위. T06은 `달성 ≥ 요구` 비교만 하고 등급 정의를 복제하지 않는다 |
| `fragment-postcondition-required` | T05 (신설) | T07(승격 판정) | 신설. 제안서 §4 "[MUST] 사후 조건이 없는 조각은 등록하지 않는다" |
| `freshness-key-composition` | T06 (신설) | T07(`status` 모드) | 신설. 6요소 구성은 INTENT C-8이 확정 |
| `promotion-requires-pass-evidence` | T07 (신설) | 사람·CLOSE | 신설. 제안서 §3 "[MUST] 승격 자격은 도구가 `pass` 증적을 확인한 뒤에만 성립" |
| `skill-registry-entry` | `opal/core/references/opal-skills-registry.json` | T07 | 전역 색인. **T07 단독 소유** — 다른 태스크가 쓰지 않으므로 전역 산출물 축 교집합이 0이다 |

## Profile 배정

| 태스크 | Profile | 근거 |
|---|---|---|
| T01 | **Critical** | 동결 RED S-4(`test_red_s4_no_repo_pollution.py:43` "실행 전후 `git status --porcelain` 델타 0")를 정면으로 건드린다. 기본 산출물 경로를 저장소 안 `.e2e/`로 옮기는 변경이라 `.gitignore` 1줄이 빠지면 그 RED가 즉시 깨진다 |
| T02 | **Critical** | 동결 조항 `task127-C-6`과 증적 단일 관문을 건드린다. 실패 시 원문이 디스크에 남는 경로가 생기면 비가역 유출이다 |
| T03 | **Critical** | `task127-C-3`·`driver-8op-B.2` 인접. 게이트를 잘못 만들면 완전한 driver가 `capability_missing`으로 걸러져 전건 `blocked`가 된다 |
| T04 | **Standard** | 계약 개정 없이 **이미 열린 주입점**(`:311`)에 파일 입력을 붙이는 가산 변경이고, 잘못 등록된 driver는 T03의 `driver-verify`가 앞서 막는다. 선행 게이트가 위험을 흡수한다 |
| T05 | **Critical** | 동결 RED S-27의 측정 범위를 건드린다. INTENT 비가역 제약("동결 RED 단언 약화 금지")과 가장 가까운 태스크다 |
| T06 | **Critical** | **검증을 건너뛰는 경로를 신설**한다. 제안서 §5 "이 장치가 없으면 신선도 키는 검증을 조용히 건너뛰는 가장 세련된 방법이 된다 — 태스크 070 실패모드가 정확히 그 형태" |
| T07 | **Standard** | 판정을 소유하지 않는다(제안서 §6 "[MUST] 판정은 스킬이 하지 않는다"). 스킬·레지스트리·승격 판정은 기존 exit 계약 해석에 얹히는 층이고 `skill-registry validate`가 기계 게이트를 준다 |

## 완료조건 역인덱스 (INTENT C-1~C-14)

| INTENT 완료조건 | 검증 미니 태스크 | acceptance ID |
|---|---|---|
| C-1 `fill` 입력값 원문 미보존 | T02 | AC-EVIDENCE-SECRET |
| C-2 요구 연산 미제공 후보 실행 전 제외 | T03 | AC-DRIVER-CONFORMANCE |
| C-3 `driver-verify` 8연산 실제 실행 검사 | T03 | AC-DRIVER-CONFORMANCE |
| C-4 전개분·본문 중복 signature 오판 없음 | T05 | AC-FRAGMENT-LIBRARY |
| C-5 매니페스트 JSON 한 장으로 driver 등록 | T04 | AC-DECLARATIVE-DRIVER |
| C-6 `order.json` → `resolve_candidates(candidate_order=...)` | T04 | AC-DECLARATIVE-DRIVER |
| C-7 사후 조건 없는 조각 등록 거부 · 전개 증적 | T05 | AC-FRAGMENT-LIBRARY |
| C-8 신선도 키 6요소 · `order.json` 우회 차단 | T06 | AC-FRESHNESS-SKIP |
| C-9 생략 = "이전 증적 재인용" 기록 | T06 | AC-FRESHNESS-SKIP |
| C-10 `opal-e2e` 3모드 + 레지스트리 매칭 | T07 | AC-E2E-OPERATOR |
| C-11 3폴더 추적 경계 · `.gitignore` 1줄 | T01 | AC-STORAGE-LIFECYCLE |
| C-12 승격 자격 도구 판정 | T07 | AC-E2E-OPERATOR |
| C-13 `.e2e/artifacts/` 보존 정책 집행 | T01 | AC-STORAGE-LIFECYCLE |
| C-14 기존 회귀 0 | T01~T07 전건 | AC-NO-REGRESSION |

**연결되지 않은 C 없음.** C-14는 각 미니 태스크의 `verify_command` 말미가 `"$HOME/.opal/.venv/bin/python" -m unittest discover -s tests -t tests`로 전체 스위트를 재실행해 태스크마다 확인한다. 두 가지가 실행으로 확정됐다 — (1) `-t tests`: `opal/tools/test-tool/tests/`에 `__init__.py`가 없어 `-t .`은 `ImportError: Start directory is not importable`로 **항상 exit 1**이다. (2) venv 인터프리터: 시스템 `python3`은 `jsonschema` 부재로 `test_scenario.py` 2건이 깨지고 수집 테스트 수도 425 vs 428로 다르다. `opal/tools/test-tool/run.sh`가 이미 `$HOME/.opal/.venv/bin/python`을 쓰는 것과 같은 경로다.

**probe snapshot 조건과 워크트리 조건은 다르다 — 실측.** `probe.py:309 _make_snapshot`은 `git archive HEAD`로 스냅샷을 만들고 `_observe_command`(`:411`)가 **명령마다 새 스냅샷을 만들어 실행 직후 `shutil.rmtree`로 버린다.** 그래서 (1) bootstrap이 만든 의존성은 다음 명령에 전달되지 않고, (2) `.gitattributes`의 `export-ignore` 대상이 스냅샷에 아예 없다 — `/tasks/`(`:16`)·`/docs/`(`:19`)·`/.opal/`(`:26`)·`/.gitignore`(`:30`). 실측: 스냅샷 최상위에 `tasks/`·`docs/`·`.opal/`이 없고 `git ls-files | grep ^tasks/`는 0건이다. 이 프로젝트의 lease 경로 중 `docs/e2e/**`·`.opal/e2e/**`와 C-11의 `.gitignore` 판정은 **probe가 구조적으로 관측할 수 없다.** 상세와 판정 요청은 §PM 판정 요청 항목 6~7.

**현 시점 `verify_command` 7건은 전건 exit 5다 — 결함이 아니라 fail-closed RED이다.** unittest는 수집된 테스트가 0건이면 exit 5(`NO TESTS RAN`)를 낸다(실측). 각 verify의 첫 구간이 그 태스크가 **앞으로 작성할** 테스트 파일을 `-p`로 지목하므로, 파일이 생기기 전에는 exit 5로 체인이 멈춘다. 실패(exit 1)와 미작성(exit 5)이 코드로 구분되고, 테스트를 쓰지 않으면 통과할 수 없다. 기존 자산을 지목하는 구간은 오늘 이미 초록이다 — `test_red_s4_no_repo_pollution.py`·`test_red_s7_redaction.py`·`test_red_s27_no_retry_on_product_failure.py` 각 exit 0, 전체 스위트 exit 0(167.1s), `skill-registry validate` exit 0.

## 통합 전략과 위험

**통합 전략** — P3 실측 보정 후 체인은 `T01 → T02 → T03 → T04 → T05 → T06 → T07`이다. 아래 순서가 우연이 아니라 인과다.

1. 저장 경계(T01)와 증적 안전(T02)이 먼저 선다 — 뒤 태스크 전부가 이 둘 위에 산출물을 쓴다.
2. 이행 검사(T03)가 등록 문턱을 낮추는 변경(T04)보다 앞선다 — 제안서 §7 [MUST].
3. 조각(T05)은 마스킹(T02)과 driver 정체 확정(T04) 뒤에 온다 — 조각이 자격증명을 다루고, 조각 전개가 요구 연산을 바꾸기 때문이다.
4. 신선도(T06)는 조각 해시와 driver 정체가 모두 확정된 뒤에만 키를 만들 수 있다.
5. 발동층(T07)은 아래 전부를 호출·해석만 한다.

**위험**

| 위험 | 근거 | 대응 |
|---|---|---|
| **브라우저 바이너리 전건 부재** — `ego`·`cmux`·`agent-browser`·`playwright`가 PATH에 없다(실측 2026-09-18) | `bootstrap-browser-binaries` probe | T03의 `driver-verify`가 "바이너리 없음"을 **통과로 처리하면 안 된다**. 태스크 127이 3연산 driver를 30건 통과시킨 것과 같은 형태의 사고다. 별도 outcome(`provider_unavailable`)으로 남기고 `pass` 판정과 분리 |
| `orchestrator.py` 단일 모듈(83KB)에 6개 태스크가 순차 진입 | 실측 | 병렬 폭을 1쌍으로 제한하고 `depends_on`으로 고정했다. 분할 시도는 오히려 lease 충돌을 만든다 |
| 신선도 키에 실행 정체를 넣으면 **생략률이 떨어져** §1이 지목한 "매번 전수 재실행"으로 회귀 | 제안서 §5 한계절 · brain `skip-gate-key-must-include-execution-identity.md` §한계 | 안전을 택하고 생략률 저하를 T06의 알려진 한계로 기록한다. 되돌림(키에서 정체 제거)은 비가역 제약으로 취급 |
| `api` profile 상한이 `real-http`인데 `real-usage`를 요구 충실도로 시드하면 키가 영원히 불충족 | 제안서 §5 주의 · brain `e2e-candidate-order-and-fidelity-ownership.md`(127 B-5 이월) | T06이 도달 불가 요구를 `blocked` 사유로 드러내고 조용히 대기하지 않는다 |
| 동결 spec 제약으로 태스크 캡슐 안에서 시나리오 사후 추가 불가 | brain `e2e-frozen-spec-seeding-constraint.md` | 이 프로젝트의 테스트는 127 선례대로 임시 폴더 fixture + `--task-path`를 쓴다. `test-scenario.json` 재시드를 시도하지 않는다 |

## PM 판정 요청 항목

1. **주입 문서 경로 불일치** — `project_docs`가 `opal/tools/test-tool/CONTRACT.md`·`opal/tools/test-tool/README.md`를 지목했으나 `CONTRACT.md`는 그 경로에 **없다**. 실측 소재는 `tasks/127-260912-oppl-E2E-하네스-구현/CONTRACT.md`(§C-DRV-3 `:565`, §C-3 `:733`)이며 동결 조항 C-1·C-3·C-6의 원문은 `tasks/127-.../TASK.md:37,39,42`다. 이 문서는 그 실측 경로를 인용했다. 레지스트리 경로 정정 여부는 PM이 판정한다.
2. **동결 RED S-27의 "범위 정정" 허용선** — C-4는 d-1 단언(`tests/test_red_s27_no_retry_on_product_failure.py:224`)의 측정 대상을 "한 run 안 같은 signature 2회"에서 "전개분/본문 구분 집계"로 좁힌다. 이것이 INTENT 비가역 제약의 "약화"인지 "범위 정정"인지는 PM 확정 사안이다. INTENT C-4가 이미 "동결 RED S-27의 기대 계약은 그대로"라고 적었으나, 단언 코드에 손이 닿는 것은 사실이므로 실행 전 승인을 요청한다.
3. **T01∥T02 병렬 확정** — probe가 두 태스크의 미추적 쓰기 루트 분리(저장소 내 `.e2e/` vs 프로세스별 임시 디렉터리)를 확인하지 못하면 병렬을 취소하고 `T02 → T01` 또는 `T01 → T02`로 내려야 한다.
4. **`docs/e2e/` 초기 시드 범위** — T05가 `fragments/login.md`·`journeys/login-to-dashboard.md` 2건을 참조 구현으로 넣는다. INTENT 제외 범위는 "태스크 127 fixture의 소급 이관"만 금지하므로 신규 작성 2건은 범위 안으로 읽었다. 이 해석의 확정을 요청한다.
5. **`suite-test-tool`이 probe snapshot에서 통과할 수 없다 — 구조적 blocker.** 스냅샷 재현 실측(`git archive HEAD` + `git init/add/commit`, probe와 동일 절차): 의존성 없이 exit 1(31 F/34 E, 105s), `npm ci` 후에도 exit 1(9 F/34 E, 148s). 잔여 실패 43건 중 **30건이 `FileNotFoundError: .../tasks/127-260912-oppl-E2E-하네스-구현/test-scenario.json`**이다(`tests/test_e2e_human_executor.py:52`). 그 파일은 **추적돼 있는데도** `/tasks/ export-ignore` 때문에 `git archive` 출력에서 빠진다. `npm ci` bootstrap을 넣어도(넣었다) 이 30건은 해소되지 않으며, 명령마다 스냅샷이 폐기되므로 순서 배치로도 해소되지 않는다. 선택지: (a) probe 명령 집합에서 전체 스위트·verify를 빼고 snapshot-safe 명령만 남긴다(내 권고 — probe의 목적은 미추적 쓰기·자원 관측이지 수용 판정이 아니다. 단 슬라이스 스킬 §3.2 "verify argv를 probe에 등재한다"와 충돌하므로 스킬 개정이 따라야 한다), (b) `.gitattributes` 개정(릴리스 tarball 의미가 바뀌고 `scripts/tests/test_archive_contents.sh` 회귀 위험), (c) `probe.py` 스냅샷 방식 변경(OPPB 도구 계약 변경). 세 선택지 모두 내 scope 밖이라 손대지 않았다.
6. **`COMMAND_TIMEOUT_SECONDS = 180`(`probe.py:64`) 대비 전체 스위트 소요가 아슬아슬하다.** 실측 105s·148s(스냅샷)·167s(워크트리)이고 PM 측정은 222s였다. 5번을 (a)로 풀지 않는 한 timeout으로도 막힌다.
7. **`driver-verify`의 바이너리 부재 판정** — 위 위험표 1행. "실제 실행 검사"를 요구하는 C-3을 바이너리 없는 환경에서 어떻게 종결할지(스텁 driver로 계약 검사 + 실제 바이너리는 `provider_unavailable` 기록)를 PM이 확정해야 T03의 수용 기준이 닫힌다.
