# DONE: 파이프라인 사용자 확인 행 — 자동 승인 경로 일원화

> 완료일: 2026-08-16 00:00 | 적용 스킬: opd | 모드: agentic | 워크스페이스: `--wt` (worktree 격리)
> 태스크 폴더: `tasks/093-260815-opd-사용자확인행-자동승인-일원화/`
> 코드 작업본: `.opal-worktrees/task_093/` (브랜치 `feat/OP-TASK-093`, base `main`=`d58a5df`)

## 1. 무엇을 했나

파이프라인 "사용자 확인" 행의 상태 전이를 **미확인(`pending`) → 자동 승인(`done/auto`) 또는 캡틴 승인(`done/user`)** 단일 축으로 일원화했다. 자동 승인을 PM의 명시 호출(`mark --auto-pass`)이 아니라 **도구 훅**이 집행하도록 바꿨다.

### 착수 배경 (실측된 결함)

| # | 결함 | 근거 |
|---|------|------|
| 1 | 캡틴 3조 중 2조("다음 단계 진입 시 자동 승인")가 **구현되어 있지 않았다** | 자동 승인이 PM의 명시 `--auto-pass` 호출로만 발생. 다음 단계 진입 훅 부재 |
| 2 | agentic의 `na`는 조항 2의 구현이 아니라 **가드 회피용 우회**였다 | `na`가 `_COMPLETE_STATUSES`에 포함돼 건너뛰기 가드를 통과시킴. `timestamp`가 `null`로 남아 승인 이력이 없음 |
| 3 | 같은 행에 진입 경로 3개(init auto-na / `--auto-pass` / `--owner user`)가 상호 계약 없이 공존 | `mark`에 상태 전제조건이 없어 `na → done` 무검증 덮어쓰기 |
| 4 | 멱등성 부재 — note 접두 중첩 | 092 `state.json` rows 5·8·11 **3건**에서 `agentic auto-pass: agentic auto-pass:` 실측 |
| 5 | 자동 승인 가부 판정이 3곳에 분산 | PM이 사전에 알 방법이 없고 호출해 봐야 에러로 알게 됨 |

## 2. 무엇이 바뀌었나

| ID | 변경 | 결과 |
|----|------|------|
| F-1 | init 시 agentic auto-na 분기 3곳 제거 | 사용자 확인 행이 **전 모드 `pending/⬜/PM`**으로 초기화 |
| F-2 | `auto_approve_prior_user_confirmations()` 신설 | 다음 단계 진입(`advance`/`mark`) 시 stage-transition guard **직전**에 앞 구간 미완 행을 `done/auto/timestamp` + note `auto-approved on <stage> entry`로 자동 승인 |
| F-3 | `can_auto_approve_user_confirmation()` 단일 판정 신설 | "CLOSE 여부(모드 무관 무조건 거부)"와 "`MODE_BOUNDARY_STAGES` 소속(semi-agentic 한정 거부)" 두 축을 합성. 분산 판정 수렴 |
| F-4 | `user_confirmation_required` 에러 신설 | 자동 승인 불가 구간에서 `row_id`·`stage`·`reason`·`required_action` 반환 |
| F-5 | note 접두 멱등 + 재-auto-pass no-op | 접두 중첩 0건. 접두 문자열 `agentic auto-pass` 자체는 불변 |
| F-6 | `na` 하위호환 + 문서 11종 정합 | 기존 `na` 보유 파일 무사고. 계약 본문은 하네스 2종에만, pilot 8종은 참조 포인터 |

**설계 후 불변식**: 사용자 확인 행의 최종 상태는 `done/auto`(자동 승인) 또는 `done/user`(캡틴 승인) 둘뿐이며, 두 경우 모두 `timestamp`가 남는다.

## 3. 변경 파일 (changed_files)

코드 작업본 `.opal-worktrees/task_093/` 기준. **미커밋 상태**(브랜치 `feat/OP-TASK-093`).

| 파일 | 규모 |
|------|------|
| `opal/tools/state-tool/state_tool.py` | +148 / −42 |
| `opal/tools/state-tool/tests/test_state_tool.py` | +973 / −19 |
| `opal/core/references/opal-harness-agentic.md` | 24행 변경 |
| `opal/core/references/opal-harness-semi-agentic.md` | +18 / −6 |
| `opal/skills/opal-pilot-{dev,dev-short,dev-wireframe,project,project-dev,project-loop}/SKILL.md` | 각 +2 / −1 |
| `opal/skills/opal-pilot-{gc,sdd}/SKILL.md` | 각 +4 / −2 |
| `docs/CONVENTIONS.md` | +2 |

- 태스크 문서(`tasks/093-*/`)와 `.opal/`은 하네스 §2.5 경로 계약대로 **허브 고정**.
- `~/.opal/` 배포본 **미접촉** — 전역 배포는 캡틴 수동 실행 대기.

## 4. 검증 결과

| 항목 | 결과 |
|------|------|
| 시나리오 | **25 Pass / 0 Fail / 1 Skip**(L3 S-23, 캡틴 확인 대기) |
| pytest | `1 failed / 314 passed / 65 subtests` — 실패는 확정 환경 예외 1건 |
| 테스트 함수 | 291 → **315**(+24), **삭제 0건** |
| 컨벤션 진단 | Critical·High **0건** (`GC-CONVENTION-260815.md`) |
| 코드 품질 | mypy Success / ruff 프로덕션 24→22(신규 0) / format 기준선 무변화 |
| 보안 | 시크릿 스캔·`.gitignore` Pass |
| 목표-커버 게이트 | iteration 1 pass — coverage-check exit 0 AND evaluator 2/2/2(평균 2.0) |

### 목표 달성 실증 (070형 공백 방지)

- **S-1 관통**: `--auto-pass`를 한 번도 전달하지 않고 TASK→EXECUTE를 진행해 사용자 확인 **4행이 자동 승인**됨을 state.json 재로드로 확인. 훅 미배선 시 `stage_transition_violation`으로 반드시 실패하는 구조.
- **S-2 잔존 0**: `agentic auto-na at init` grep 0건.
- **S-3 채택**: 동일 스펙 3모드 init 결과 `rows[]` diff 0.
- **S-25 구조**: `MODE_BOUNDARY_STAGES` 참조가 정의부 + 판정 함수 2곳으로 수렴 — 행동 불변만으로는 복붙도 통과하는 공백을 메움.

### P0 가설 해소

| 가설 | 해소 근거 |
|------|----------|
| H-1 CLOSE 우회 | 3중 방어(대상 행 CLOSE 즉시 no-op / 후보 수집 제외 / 판정 함수 무조건 거부). S-6·S-7 실측 |
| H-2 워커 권한 우회 | `as_worker` 시 훅 전면 비활성. S-8·S-9에서 **파일 바이트 완전 동일** 확인 |
| H-9 CLOSE 절차 훼손 | **3중 교차 검증** — 배치3 정규화 grep 100지점 동일 / PM `git diff` 삭제 축 0건 / TEST 워커 올바른 필터 재실행 100:100 |

## 5. PM이 잡아낸 것 (agentic 대행 기록)

전체 이력은 `AGENTIC-LOG.md` 38행. 판정에 영향을 준 항목만 추린다.

| # | 내용 |
|---|------|
| 1 | **worktree base 오분기** — `create`가 `origin/main`(091)에서 분기해 092 커밋 2건 누락. `baseBranch: main` 선언 + 브랜치 삭제 후 재생성으로 해소 |
| 2 | **TASK.md 근거 오류 2건** — note 이중 접두를 2건으로 적었으나 실측 3건, `check_close_gate`를 모드 경계 판정으로 오분류. ANALYSIS가 잡아내 정정 |
| 3 | **PLAN 자기모순** — §3.3.2 (2)의 필터 지시와 표 B V-7이 충돌. 워커가 `include_close_axis` 축 부재로 해소, PM 검증 후 승인 |
| 4 | **PM 디스패치 결함** — 담당을 Step 1~12로 한정하고 완료 기준은 전체 failed 0으로 적어 상충. 워커가 F-005를 앞당기지 않고 보고한 판단을 승인 |
| 5 | **PM 계수 오류** — `grep -c "def test_"`가 문자열 리터럴을 세어 316으로 과대 계수. `--collect-only` 315가 정답이며 워커 보고가 옳았음 |
| 6 | **공허한 검사 발견** — S-21 grep 필터가 전 행을 제거해 `before=0/after=0`로 무검증 통과가 되는 결함. TEST 워커 자진 보고 → PM 재현 → 문구 5곳 정정 |

## 6. 남은 것

| # | 항목 | 상태 |
|---|------|------|
| 1 | **S-23 전역 배포 실동작 확인** (L3 [SUPERVISOR]) | 캡틴 확인 대기 — `scripts/install-mac.sh` 수동 실행 후 신규 `--agentic` 태스크로 검증 |
| 2 | 승인 요구 산문의 모드 분기 처리 | 캡틴 결정 대기 (095 분리 / 093 F-6 흡수 / 회귀 방지만) |
| 3 | 094(STATE 저널화)와의 머지 충돌 처리 | 캡틴 결정 대기 (순차 / 각자 worktree 후 조정) |
| 4 | worktree sparse-checkout이 `tasks/` 의존 테스트를 깨뜨림 | 092 후속 개선 후보 |
| 5 | `baseBranch` 변경이 remove→create만으로 반영되지 않음 (보존된 브랜치 재사용, 응답 `base_ref`는 새 값을 보고해 오인 유발) | 092 후속 개선 후보 |
| 6 | `ruff format` 기준선 미준수 2파일 | 착수 전 부채, 포맷터 채택은 별도 의사결정 |

## 7. 커밋·배포

- **미커밋** — 커밋은 캡틴 명시 요청 시에만 수행한다(하네스 §1 커밋 규칙).
- **미배포** — `install-mac.sh`는 `$USER_HOME/.opal` 단일 타겟이라 배포 시 실행 중 세션의 파이프라인이 교체된다. CLOSE 이후 캡틴이 수동 실행한다.
- worktree `feat/OP-TASK-093`는 **머지 대기** 상태로 남긴다. 자동 커밋·자동 머지·자동 제거는 수행하지 않는다.
