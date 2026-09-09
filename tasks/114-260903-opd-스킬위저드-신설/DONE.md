# DONE: opal-skill-wizard 신설 — 프로젝트 적합 스킬 제안 + 프로젝트 스코프 설치

> 완료일: 2026-09-09 | 적용 스킬: opd (opds에서 승격) | 모드: agentic
> 태스크 번호: 114 | 파이프라인: TASK → ANALYSIS → PLAN → TEST-SCENARIO → EXECUTE → TEST → CLOSE (16행)

## 1. 무엇을 만들었는가

프로젝트에 적합한 커뮤니티 스킬을 인터뷰·분석으로 도출해 제안하고, 승인분을 **프로젝트 스코프**에 설치하는 신규 스킬 `opal-skill-wizard`(약어 `osw`)를 신설했다. 설치된 스킬은 `//osw` 등 `//` 커맨드 경로로 발동한다.

**핵심 설계 3가지**

| # | 결정 | 내용 |
|---|------|------|
| 1 | 스코프 분리 | 프로젝트 스코프는 `opal-skill-wizard`, 전역은 `opal-skill-manager`가 담당한다. wizard는 manager를 **호출하지 않고** 검색·clone·검사·복사·기록을 직접 수행한다 |
| 2 | 레지스트리 4소스 | `loadAllSkills()` 병합을 `main → community → user → **project**` 4소스로 확장했다. 프로젝트 registry는 `{project}/.opal/skills-registry.json`, 본체는 `{project}/.opal/community-skills/{vendor}/{skill}/SKILL.md` |
| 3 | 보안 게이트 | 복사 **직전** `skill-registry.js scan-risk`를 호출하고 SAFE/CAUTION/RISKY/UNKNOWN 4단으로 판정한다. RISKY는 추천 제외, 도구 실행 실패 시 설치 미진행 |

**변경 파일 7건**

| 파일 | 구분 | 요지 |
|------|------|------|
| `opal/skills/opal-skill-wizard/SKILL.md` | 신규 319줄 | 2모드(신규 인터뷰 / 기존 `docs/PROJECT.md` 재사용 + 결측 인터뷰) · 제안→승인→설치 3단 · scan-risk 게이트 · registry 기록 · `opal-skill-creator` 위임 |
| `opal/tools/skill-registry/tests/test-project-registry.js` | 신규 | TS-001~009·015·029 = 11 케이스 |
| `opal/tools/skill-registry/skill-registry.js` | 수정 +102/-2 | `findProjectRoot`·`loadProjectRegistry`·`resolveProjectSkillPath`·`isProjectSkill` 신설 + `loadAllSkills` 4번째 병합 + `matchCommand` project 분기(`scope` 필드) + `getCommand` `resolved_path` + `validate` project 분기 |
| `opal/core/references/harness/skill-commands.md` | 수정 +9/-3 | 미설치 라우팅 3중 분기화 (v1.4) |
| `opal/core/references/opal-skills-registry.json` | 수정 | `osw` 등재 + version 3.13.0 → 3.14.0 |
| `docs/ARCHITECTURE.md` | 수정 | 레지스트리 스코프 3원 확장 + 스키마 12필드 표 |
| `docs/PROJECT.md` | 수정 | `opal/skills/` 카운트 42 → 45종 정합 |

## 2. 검증 결과 (실측)

| 항목 | 결과 | 스코프 |
|------|------|--------|
| 신규 테스트 | **11 pass / 0 fail**, exit 0 | `node opal/tools/skill-registry/tests/test-project-registry.js`, cwd = 리포지토리 루트 |
| 회귀 기준선 | **41 pass / 0 fail** (test-match 11 / test-validate 5 / test-migrate 9 / test-scan-risk 16) | 4파일 개별 실행, cwd = 리포지토리 루트 |
| TEST-SCENARIO | **35/35 실행 시나리오 PASS, FAIL 0** + M3 2건 `[SUPERVISOR]` 대기 | 미채움 슬롯 0건 |
| 목표-커버 게이트 | **PASS** (iteration 2) — 결정론 exit 0 + 판단축 `{goal:2, adoption:2, boundary:1}` 평균 1.67 ≥ 1.5 | tool-gated 2증거 |
| 컨벤션 진단 | **Critical 0 / High 0** (Medium 1건 교정 완료, Low·Info 2건 이월) | `docs/CONVENTIONS.md` 기준 |
| 발동 확인 | `match "osw"` → `found:true`, `path:/Users/lucas/.opal/skills/opal-skill-wizard/SKILL.md` | 배포 후 실측 |

## 3. 이번 태스크의 최대 산출 — 검증 2원화가 실제로 작동했다

**작성자와 검증자를 분리한 지점마다 결함이 나왔다.** 이것이 이 태스크에서 가장 재사용 가치가 큰 관찰이다.

| 검출 주체 | 검출 대상 | 결함 |
|----------|----------|------|
| PM | ANALYSIS 워커 | 커밋 해시 오기(`21037f6` → 실제 `69f5ce1`), 착수 트랙 stale 기재 |
| PM | PLAN 워커 | **내부 자기모순** — 「동일한 마커」라고 쓰고 실제로는 다른 마커(파일 vs 디렉토리)를 가리켰다. 그대로 구현되면 최초 설치 전 루트를 못 찾는 **순환**과 설치 루트·해석 루트 **불일치**가 발생했을 것 |
| Evaluator | **PM(작성자)** | 목표-커버 게이트 iteration 1 fail — 「문서에 규칙이 쓰여 있다」와 「wizard가 실제로 그렇게 행동한다」를 구분하지 못했고, **보안 게이트조차 정적 grep에 그쳤다** |
| 테스트 | **PLAN 설계** | `validate()`에 project 분기가 없어 R-7 AC(error 0건)가 **원천 성립 불가**였다. PLAN §3.1.2 6건에 누락됐고 ANALYSIS Q3의 「신규 이슈 아님」 판정도 이 점에서 틀렸다 |
| TEST 워커 | **PM(작성자)** | §4 매핑 표가 **존재하지 않는 테스트 케이스**(`[T114/L2-GOAL]`)를 인용했다 |
| 컨벤션 워커 | **PM 지시** | 「변경이력 대상 아님(코드 파일)」이라는 내 지시가 `CONVENTIONS.md` §@header 「헤더 내 변경이력 라인」 규정을 놓쳤다 |

> **PM 귀책 3건**이 독립 검증자에게 적발됐다. 단일 주체 자가 검증으로는 이 중 어느 것도 잡히지 않았을 것이다.

**부작용 관측(side-effect observation) 방법론** — Evaluator가 M3(사용자 수동) 승격을 제시했으나, wizard의 행동은 결국 파일시스템 변화로 나타나므로 「무엇이 생겼는가 / 생기지 않았는가」를 검사하면 M1 자동화로도 실행-시간 검증이 성립한다. 가장 강한 장치는 **TS-031** — 설치 전후 전역 `~/.opal/community-skills/` 변화 0건이 곧 「manager 경로를 타지 않았다」는 증거다. Evaluator는 이 방법론 자체를 타당 판정했고, ⑤축을 1 → 2로 올렸다.

**음성 통제(negative control)** — 「통과시키려 검증을 약화한 것 아닌가」에 답하는 장치로 3회 사용했다. (1) realpath 정규화 후에도 기대 경로를 틀리게 하면 실패하는지 (2) 빈 `else if` 분기가 project 항목 검사를 통째로 무력화하지 않았는지 (3) 필수 필드 누락 시 `validate`가 실제로 error를 내는지. 3건 모두 반대 방향에서 실패를 확인했다.

## 4. 사고·특이사항

| # | 사고 | 처리 |
|---|------|------|
| 1 | **PLAN 워커 API 529 3회 연속 실패** (모델 `claude-opus-5`, 3회 전부 PLAN.md 빈손 종료) | 하네스 §1 재시도 1회 소진 후 중단·에스컬레이션. 캡틴 질문("강등하려는 이유가 뭐지?")을 받고 **모델 강등 권고를 철회** — 근거가 「지금 진행 가능한 유일 경로」뿐이었고 후단 게이트를 강등 정당화로 든 것은 순서 오류였다. 7시간 경과 후 규범 모델로 4차 시도해 성공 |
| 2 | 조기 에스컬레이션 — 요구사항 11건 > 8건 | 캡틴 승인으로 `opds` → `opd` 승격. 폴더 약어·헤더·파이프라인 11행 → 16행 재구성 |
| 3 | R-10 AC 「`validate` error 0건」이 **착수 시점부터 실현 불가** | `git stash` 대조로 확인 — `op-scenario-gate: unregistered`가 114 착수 이전부터 존재하던 무관 결함이다. 캡틴 배포로 `dangling`은 해소돼 **114 유발 오류 0건**이 됐고, 잔여 1건은 선존·무관으로 판정했다 |
| 4 | 승격 실행 절차 SSOT 공백 | `harness/track-routing.md`가 강등만 규정하고 승격 시 폴더 rename·state 재init 절차를 명문화하지 않았다. 개선 후보로 이월 |
| 5 | **채번 오류 — 106으로 발급받아 커밋까지 진행** | 로컬 `.opal/MEMORY.json`이 stale(105)인 상태에서 채번해 원격에 이미 있는 106과 중복됐다(원격 `last_task_number`=113). 커밋 해제 → `pull --ff-only` → 106→114 전수 재채번(23파일 145건 + 잔여 32건) → 재커밋으로 교정. `backup-106-preRenumber` 브랜치가 안전망. **교훈: 채번 전 원격 동기화가 선행되어야 한다** — 도구는 정상 동작했고 결함은 절차에 있다 |
| 6 | 원격 병합으로 이월 1건 자연 해소 | 원격 111이 `op-scenario-gate` 미등재를 이미 복구했다. 잔여 `validate` 오류 1건은 원격 106의 `opal-code-map-builder` 미배포분으로 우리와 동일 패턴이다 |
| 7 | 배포본이 소스보다 뒤처짐 | 배포가 Step 10(변경이력 기재)보다 먼저 실행됐다. 차이는 wizard `SKILL.md` §변경이력 5줄뿐(319 vs 314줄)이고 실행 영향 0. 다음 install 시 자연 동기화 |

## 5. 미수행 · 이월

**미수행**
- **커밋** — 캡틴 권한 ([MUST] `~/.opal/references/opal-harness.md` §1 커밋 규칙: "커밋은 사용자가 명시적으로 요청할 때만 수행한다")
- **TS-021·TS-022** — 인터뷰 흐름 M3 `[SUPERVISOR]` 대기. `//osw`를 실제 프로젝트에서 1회 실행해 (a) PROJECT.md 부재 프로젝트에서 인터뷰 후 후보 목록이 나오는지 (b) PROJECT.md 존재 프로젝트에서 기술 스택·폴더 구조를 다시 묻지 않는지 확인이 필요하다
- **재배포** — 변경이력 동기화용 (선택)

**이월 6건**

| # | 항목 | 근거 |
|---|------|------|
| R-1 | `harness/analysis-core.md` §5 축에 「도구(CLI 코드)」 라벨 추가 | DEC-6 — 축 개정은 전 pilot 산출물 포맷에 파급. [MUST] PRINCIPLES §3 "Don't improve adjacent code" |
| R-2 | `list` 응답의 섀도잉 가시성(`shadowed_by` 등) | DEC-4 — 완료기준에 요구 없음. PRINCIPLES §2 Simplicity First |
| R-3 | `listCommand()` `--group=project` 필터 | ANALYSIS H-7 — R-5/R-6 범위 밖 |
| R-4 | project 항목 필수 필드(`trust`·`license` 등) `validate` 검증 | 어떤 AC도 요구하지 않음. 현재 `name`만 검사된다 |
| R-5 | `op-scenario-gate` registry 미등재 | 114 착수 전부터의 선존 결함. 파이프라인이 파일 경로로 직접 호출하므로 실해는 낮다 |
| R-6 | 승격(`opds`→`opd`) 실행 절차 SSOT 명문화 | 사고 #4 |

## 6. 산출물

```
tasks/114-260903-opd-스킬위저드-신설/
├── TASK.md                      요구사항 R-1~R-11, 관련 문서 D-1~D-9
├── ANALYSIS.md                  Q1~Q10 답변, H-1~H-7, PLAN 결정 필요 6건 이관
├── PLAN.md                      DEC-1~DEC-7 확정, F-001~F-006, H-1~H-9, 10 Step / 7 Phase
├── TEST-SCENARIO.md             TS-001~TS-037 (37건), 6축 전건 커버
├── SCENARIO-GATE-1.md           iteration 1 채점 (fail, 1.33)
├── SCENARIO-GATE-2.md           iteration 2 채점 (pass, 1.67)
├── GC-CONVENTION-260904.md      컨벤션 진단 (Critical 0 / High 0)
├── AGENTIC-LOG.md               PM 대행 일지 79엔트리
├── STATE.md / state.json        파이프라인 16행
└── DONE.md                      본 문서
```

## 7. 다음에 이 설계를 건드릴 사람에게

- **`findProjectRoot()`의 마커는 `.opal/` 디렉토리다.** `.opal/skills-registry.json` 파일로 바꾸지 마라 — 최초 설치 전 루트를 못 찾는 순환이 생기고 wizard 진입 훅 마커와 갈린다. 이 마커 선택 때문에 `~/.opal/`이 항상 존재하므로 **홈 경계 정지가 유일한 방어선**이다(H-4/P0, TS-008).
- **`getCommand()`의 `resolved_path`는 additive다.** 기존 raw passthrough 필드를 계산값으로 덮어쓰지 마라 — `opal-help`·`opal-skill-manager` 문서 절차가 그 필드를 참조한다(H-3, TS-006이 보존을 단정).
- **`loadAllSkills()`의 기존 3소스 병합 코드는 무수정 계약이다.** TS-002가 프로젝트 registry 부재 시 전역 결과 동일성을 검사한다.
- **project 스킬은 `paths`를 갖지 않는다.** `validate()`에 project 분기가 필요한 이유이며, 이 분기를 지우면 스키마 준수 registry도 error를 낸다.
