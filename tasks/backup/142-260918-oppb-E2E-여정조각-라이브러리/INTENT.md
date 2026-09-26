# INTENT: E2E 여정·조각 라이브러리

> 작성일: 2026-09-18 | 스킬: //oppb

## 목표

E2E 시나리오가 태스크 캡슐이 아니라 프로젝트에 누적되게 만든다. 사람이 `//e2e`로 여정과 조각을 작성·실행·조회하고, 조각이 바뀌면 그 조각을 쓰는 여정만 재실행되며, 새 브라우저는 JSON 매니페스트 한 장으로 등록된다. 이 셋이 실제로 동작하면 프로젝트가 끝난다.

설계 근거는 `docs/proposals/archives/e2e-journey-fragment-library.md`(태스크 142 CLOSE에서 `적용완료`로 보관)다. 그 문서가 제안이고 이 INTENT가 실행 계약이다 — 충돌하면 INTENT가 이긴다.

## 제외 범위

- **기존 pilot의 단계 계약 변경.** `opd`·`opds`·`oppd`·`oppl`·`opsdd`의 파이프라인·행·게이트를 건드리지 않는다. CLOSE 조건부 발동은 기존 `verification.md` §1.5.3 규범에 집행 지점을 주는 것이며 새 규범을 만들지 않는다.
- **`test-tool` E2E exit 계약(0/6/7/18/19/20) 재정의.** 판정 주체는 그대로다.
- **`FIDELITY_ORDER` 재정의.** 충실도 등급은 `opal/tools/test-tool/lib/scenario.py:119`가 단독 소유하고 이 프로젝트는 참조만 한다.
- **`import` 모드.** 제안서 Q-9가 스스로 한계를 인정한다 — `TEST-SCENARIO.md`가 표 형식이라 실행 필드를 담기 비좁고 `author`로 2단 보완이 필요하다. 단독 가치가 얇아 이번 범위에서 뺀다. `author`·`run`·`status` 3모드로 시작한다.
- **실제 서비스 배포·외부 시스템 쓰기.**
- **기존 E2E 시나리오의 소급 이관.** 태스크 127이 임시 폴더에 만든 fixture 시나리오를 `docs/e2e/`로 옮기지 않는다.

## 완료조건

- C-1 `fill` 계열 action의 입력값이 `actions.jsonl`에 원문으로 남지 않는다. 마스킹 실패 시 원문을 남기지 않고 `infra_error`로 끝나는 기존 계약이 유지된다.
- C-2 시나리오 step이 요구하는 연산을 제공하지 않는 driver 후보가 **실행 전에** 걸러진다. 실행 도중 `driver_operation_unimplemented`로 `blocked`가 되는 경로가 재현되지 않는다.
- C-3 `test-tool e2e driver-verify --driver <name>`이 8연산 이행을 실제 실행으로 검사하고, 일부 연산만 구현한 driver를 통과시키지 않는다.
- C-4 조각 전개분과 본문에 같은 연산 signature가 함께 나타나도 재시도로 오판되지 않는다. 동결 RED S-27의 기대 계약은 그대로다.
- C-5 `.opal/e2e/drivers/`에 매니페스트 JSON 한 장을 두면 파이썬 모듈 없이 driver가 등록되고, `driver-verify`를 통과해야 후보가 된다.
- C-6 `.opal/e2e/order.json`의 값이 `resolve_candidates(candidate_order=...)`에 전달되어 후보 우선순위를 재정의한다.
- C-7 사후 조건이 없는 조각은 등록이 거부된다. 조각 전개 결과는 `actions.jsonl`에 실제 연산 단위로 남는다.
- C-8 신선도 키가 `(여정 해시, 조각 해시 집합, surface_id, 대상 commit, 선택 driver 정체, 달성 충실도)`로 판정되며, `order.json`만 바꿔 이전 `pass` 증적을 재인용하는 경로가 막힌다.
- C-9 재실행 생략이 "이전 증적 재인용"으로 기록되고 DONE에서 보인다. 생략이 미실행으로 침묵하지 않는다.
- C-10 `opal-e2e` 스킬(alias `//e2e`)이 `author`·`run`·`status` 3모드로 동작하고 스킬 레지스트리에서 매칭된다. 판정은 스킬이 하지 않고 `test-tool` 호출 결과를 해석만 한다.
- C-11 `docs/e2e/`와 `.opal/e2e/`가 추적되고 `.e2e/`는 `.gitignore` 1줄로 전량 무시되어 `git status`를 더럽히지 않는다.
- C-12 여정을 `docs/e2e/`로 승격하는 자격을 도구가 `pass` 증적으로 판정한다. 사람 산문 판단만으로 승격되지 않는다.
- C-13 `.e2e/artifacts/` 보존 정책이 집행되어 무한 증가하지 않는다.
- C-14 기존 회귀 0 — `test-tool` 기존 테스트와 E2E 계약 테스트가 프로젝트 전후로 모두 통과한다.

## 비가역 제약

사용자 승인 없이 하지 않는다.

- 실제 서비스·외부 시스템에 대한 쓰기 요청, 실제 배포.
- 동결 RED 시나리오(`red_confirmed: true`)의 기대 계약 약화·삭제. C-4는 중복 판정 **범위**를 고치는 것이지 S-27의 단언을 무르는 것이 아니다.
- `~/.opal/` 배포 파일 직접 수정. 프로젝트 소스를 고치고 install로 배포한다.
- `test-tool` E2E exit 계약과 `CONTRACT.md` 동결 조항 개정.
- 허브 `main` 머지 — P5 사용자 게이트에서만.

## 예산

- attempt 3회 (미니 태스크당 상한. 초과 시 구조화 blocked)
- `max_active_runners` 2 · `max_active_executors` 2 · `max_total_agent_processes` 4 (`supervisor.py:71-73` 기본값 유지 — 동시 워크트리 슬롯이 이미 3개라 공유 자원 경합을 늘리지 않는다)

## 참조 문서 (레지스트리가 등록한 것만)

| 문서 | 용도 | 신규 생성 |
|---|---|---|
| `docs/proposals/archives/e2e-journey-fragment-library.md` | 설계 근거·조각 계약·신선도 키·driver 매니페스트 형태 | 아니오 (기존 재사용, CLOSE에서 보관) |
| `docs/ARCHITECTURE.md` | 기술 기준 | 아니오 (기존 재사용) |
| `docs/CONVENTIONS.md` | 컨벤션 판정 기준 | 아니오 (기존 재사용) |
| `opal/tools/test-tool/README.md` · `CONTRACT.md` | E2E exit 계약·서브명령·동결 조항 | 아니오 (기존 재사용) |
| `.opal/brain/pages/concept/e2e-candidate-order-and-fidelity-ownership.md` | 후보 순서·충실도 소유 경계 | 아니오 (기존 재사용) |
| `.opal/brain/pages/concept/e2e-frozen-spec-seeding-constraint.md` | 동결 spec 제약 | 아니오 (기존 재사용) |
| `.opal/brain/pages/concept/skip-gate-key-must-include-execution-identity.md` | 신선도 키에 실행 정체를 넣는 근거 | 아니오 (기존 재사용) |

PRD·TRD는 신규 생성하지 않는다. 판정 근거는 `p1.conditional_prd` 행 note에 남긴다.
