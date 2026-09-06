# DONE: 태스크 작업공간 worktree 분리 (`--worktree`/`--wt` 축 신설)

> 완료일: 2026-08-15 | 적용 스킬: opd | 모드: agentic | 파이프라인 16행 완주
> 판정: **All Pass** (기능 26/26 · 회귀 349 · 보안 4/4 · 컨벤션 위반 0)

## 1. 무엇을 만들었나

OPAL 태스크 파이프라인에 **모드 축과 직교하는 `--worktree`/`--wt` 축**을 신설했다. 태스크별 코드 작업공간을 `{프로젝트}/.opal-worktrees/task_{NNN}/`에 git worktree로 격리하며, **플래그가 없으면 현행 동작이 100% 그대로 유지**된다.

핵심 설계는 **문서와 코드의 분리**다. 병렬 태스크에서 실제로 충돌하는 것은 코드 레이어(빌드 캐시·의존성·포트·컨테이너)이며, `tasks/`·`.opal/MEMORY.json`·`.opal/brain/`은 오히려 공유되어야 한다(채번 중복 방지, 메모리·브레인 SSOT 유지). 그래서 **문서는 허브에 고정하고 코드만 분기**한다.

## 2. 산출물

### 신규

| 경로 | 내용 |
|------|------|
| `opal/tools/worktree-tool/worktree_tool.py` | 도구 본체 817행 — `create`/`list`/`status`/`remove` 4서브명령, `ERROR_CODES` 18종 |
| `opal/tools/worktree-tool/run.sh` | venv python 위임 래퍼 (git-sync-tool 동형) |
| `opal/tools/worktree-tool/schema/worktree.schema.json` | 7키 스키마 문서 SSOT (런타임 미로드 — DEC-4) |
| `opal/tools/worktree-tool/tests/` | pytest 1,364행 — 41 케이스, 실 git 저장소 fixture (mock 0) |
| `opal/templates/worktree-multi-repo.json` | 유형 A 템플릿 |
| `opal/templates/worktree-monorepo.json` | 유형 B 템플릿 |

### 수정

| 경로 | 변경 |
|------|------|
| `opal/core/references/opal-harness.md` | **§2.5 워크스페이스 축** 신설(3항목) + §9 도구 표 등록 |
| `opal/core/references/harness/task-process.md` | 오케스트레이터 공통 영역 **스텝 4.5**(worktree 생성 훅) + 스텝 5에 `--worktree` 1행 |
| `opal/core/references/pm/dispatch-process.md` | 조건부 `## 작업 경로` 블록(문서 루트/코드 루트 2필드, 절대경로) |
| `opal/core/references/tools.md` | worktree-tool 섹션(4서브명령·에러 카탈로그·출력 형식) |
| `opal/skills/opal-pilot-dev/SKILL.md` | STEP 6 CLOSE에 worktree 정리 안내 스텝 (**pilot 10종 중 유일 변경**) |
| `opal/skills/opal-project-init/SKILL.md` | `.gitignore` 멱등 보장 항목(초기화·최신화 두 모드) |
| `opal/tools/state-tool/state_tool.py` | `init --worktree` 조건부 영속화 (**+8/-1행**) |
| `opal/tools/state-tool/schema/state.schema.json` | `worktree` optional 필드 |
| `scripts/install-mac.sh` | worktree-tool `run.sh` chmod 블록 |
| `docs/ARCHITECTURE.md`·`CONVENTIONS.md`·`PROJECT.md` | 도구 18종 → **19종** + CONVENTIONS §브랜치 전략에 DEC-1 적용 범위 명시 |
| `.opal/code-scan.json` | `exclude`에 `.opal-worktrees` 1행 |

### 환경 (캡틴 로컬 — OPAL 산출물 아님)

- `~/.zshrc`: `export UV_CACHE_DIR=/Volumes/Data/.uv-cache  # OPAL 092` **1줄**

## 3. 확정 결정 사항 (DEC-1 ~ DEC-7)

| # | 결정 | 핵심 근거 |
|---|------|----------|
| DEC-1 | 브랜치 네이밍 두 규칙은 **적용 대상이 다른 별개 규칙** | OPAL 저장소는 `feat/{NNN}-{약어}-{설명}`, worktree 대상 프로젝트는 `branchTemplate`(기본 `feat/OP-TASK-{NNN}`). 충돌이 아니라 범위 미표기가 문제였다 |
| DEC-2 | 부분 실패는 **계층 분리** | 도구는 all-or-nothing 롤백, 파이프라인은 태스크 폴더를 롤백하지 않고 `--wt` 없이 비차단 계속. 사용자 승인 산출물을 자동 삭제하지 않는다 |
| DEC-3 | base-ref는 `create` 시점 **1회 해석 후 메타에 동결** | `remove` 시점 재조회는 그 사이 기본 브랜치가 바뀌면 판정이 뒤집혀 비결정론이 된다. 메타는 worktree **밖**에 둔다(내부면 dirty 가드 오탐) |
| DEC-4 | `worktree.json` 검증은 **hand-rolled** | `jsonschema`는 `mcp`의 전이 의존성일 뿐 `requirements.txt` 미선언. 직접 쓰려면 런타임 계약 확장이 필요해 Simplicity First 저촉 |
| DEC-5 | code-scan exclude는 **포함하되 축소** | OPAL 저장소는 1행 추가, 대상 프로젝트는 경고만. 자동 JSON 편집은 지표 왜곡(심각도 낮) 대비 부작용이 크다 |
| DEC-6 | DB 동시성 경고를 **관측 가능한 사실로 대체** | 태스크 성격 판정은 입력 계약이 없어 구현 불가 → 동시 활성 슬롯 수로 경고. TASK 제약을 조용히 빠뜨리지 않았다 |
| DEC-7 | 판정 기준을 **"존재"에서 "점유"로** | 슬롯 판정 = worktree 등록 여부, 브랜치 판정 = 점유 여부. 미점유 브랜치는 재사용. 살아 있는 슬롯 거부는 판정 기준 하나로 자연히 보존된다 |

## 4. 검증 결과

### 자동 (L1·L2)

| 항목 | 결과 |
|------|------|
| 기능 시나리오 | **26/26 Pass** (S-1~S-17, S-21~S-29) |
| worktree-tool 회귀 | **41 passed** |
| state-tool 회귀 | **308 passed** (기존 304 무손상 + 신규 4) |
| 코드 품질 | ruff check·mypy·ruff format 전건 Pass (092 신규·변경 파일 대상) |
| 보안 | **4/4 Pass** — 시크릿 0 / gitignore 멱등 / 커맨드 인젝션 방어(`shell=True` 0건) / 경로 이탈 차단 |
| 컨벤션 진단 | **위반 0건** (Critical/High/Medium/Low 전부 0) |

### 실환경 (L3)

| 시나리오 | 결과 |
|---------|------|
| **S-18 revup**(유형 A) | 코드 레포 2곳 worktree + **2슬롯 격리 실증**(092 커밋 시 093·메인 불변). 기준선 완전 원복(루트 변경 0건) |
| **S-19 mams**(유형 B) | sparse가 `workspace/`만 체크아웃, `tasks/`·`.opal/`·문서 3계층 전부 부재. **슬롯 13MB**(메인 1.9GB 대비). 사전 2건 기준선 원복 |
| **S-20 `UV_CACHE_DIR`** | 슬롯당 **263MB → 8.7MB (약 30배 절감)**. 볼륨 경고 소멸로 H-12 반증 성공 |

> L3 3건은 캡틴이 결과를 확인하고 **CLOSE 진입을 승인함으로써 수용**되었다(개별 PASS 발화가 아님 — 기록 정확성을 위해 명시).

### TASK 완료기준 7건

전건 충족. ①revup 2레포 worktree+브랜치 ②mams sparse+문서 미체크아웃 ③`--wt` 미사용 시 스키마·렌더 diff 0 ④`remove` 3중 가드 각 거부 ⑤`.gitignore` 멱등 ⑥`UV_CACHE_DIR` 이전+측정 보고 ⑦회귀 전량 pass

## 5. 이 태스크가 남긴 교훈

### (1) 단위 테스트 전건 GREEN이 실환경 정상을 보장하지 않는다

pytest **36건이 모두 통과한 상태**에서 revup 실환경 검증이 **차단성 결함**을 잡았다 — `remove` 후 빈 슬롯 껍데기가 남아 같은 번호 재생성이 `WORKTREE_EXISTS`로 영구 차단됐다. `list`는 "슬롯 없음"이라 답하는데 `create`는 "존재한다"고 거부하는 내부 모순이었다.

놓친 이유가 구조적이다 — S-9는 레포별 경로만 단언했고, S-27은 **살아 있는** 슬롯으로만 시험해 "제거된 슬롯의 재생성" 경로를 밟지 않았다. 이 경위를 `TEST-SCENARIO.md` S-29 주석에 증거로 남겼다.

### (2) 목표-커버 게이트가 070형 공백을 실제로 잡았다

iteration 1에서 Evaluator가 **fail**(평균 1.00)을 냈다. 지적의 핵심은 목표 문장의 주어가 `worktree-tool`이 아니라 "**OPAL 태스크 파이프라인**"인데, 플래그→훅→도구→state 접합을 한 번도 실행하지 않는다는 것이었다. 즉 **훅이 `create`를 아예 호출하지 않게 접합돼도 23개 시나리오가 전건 PASS**했다. S-24(파이프라인 관통)를 신설해 닫았고, ⓓ(문서 3종 문안 grep)까지 붙여 "테스트가 올바른 순서를 스스로 하드코딩하는" 여지도 제거했다.

### (3) 워커의 설계 이탈·에스컬레이션이 결과를 개선했다

- BE-A가 `worktree add -b` 단일 명령을 2단계로 분리 — git이 브랜치 ref를 먼저 쓰고 등록에서 실패하면 고아 브랜치가 남아 **PLAN 자신의 H-7(롤백 원자성)이 깨진다**는 재현 근거. PM 승인 후 PLAN에 기록.
- RED 워커가 "슬롯 루트만 고치면 `BRANCH_EXISTS`에 막힌다"를 **임의 판단 없이 블로커로 올림** → PM이 git 실동작 4건을 실측하고 DEC-7 확정.

### (4) PM 자신의 오류 4건도 기록에 남겼다

디스패치 프롬프트 결함(워커 간 해석 불일치), TEST-SCENARIO에 S-29 미기재(산출물 정합 파손), 컨벤션 진단 전 게이트 mark(순서 위반), 검증 스크립트 정규식 오탐. 마지막 것은 산출물이 아니라 **내 검증 도구가 먼저 틀린** 경우였다.

## 6. 알려진 제약 · 후속 과제

| # | 내용 | 성격 |
|---|------|------|
| 1 | mams의 `cmux.json`은 `.opal/cmux/...`를 가리키는 심볼릭 링크라 슬롯에서 **끊긴다**(`.opal/` 미체크아웃). 슬롯은 코드 편집·빌드용이라 실해 낮음. 필요 시 `worktree.json` `copy[]`로 해결 | 알려진 제약 |
| 2 | "스키마 마이그레이션 동반 태스크 동시 실행" 판정은 도구가 태스크 성격을 알 입력 계약이 없어 미구현. 동시 슬롯 수 경고로 대체(DEC-6). 필요해지면 `worktree.json`에 선언 키 추가 | 후속 과제 |
| 3 | `state_tool.py`의 기존 `ruff format` 비준수는 092 범위 밖이라 미접촉(2,600행 전체 포맷 시 092 변경 3곳이 묻힘) | 후속 과제 |
| 4 | pilot 9종(opds·opdw·opp·opwt·oppd·opsdd·oppl·opdd·opgc)에서 `--wt` 실사용 검증은 미수행. 하네스 SSOT 경유라 구조적으로 전파되나 실측은 opd만 | 후속 검증 |

## 7. 참조

- 설계 SSOT: `PLAN.md` §1.4 DEC-1~DEC-7 · §3 기능별 설계
- 검증 SSOT: `TEST-SCENARIO.md` (가설 22 · 시나리오 29)
- 게이트 기록: `SCENARIO-GATE-1.md`(fail 1.00) · `SCENARIO-GATE-2.md`(pass 1.67) · `GC-CONVENTION-2026-08-15T17-56-55.md`(위반 0)
- 전 과정 추적: `AGENTIC-LOG.md` (게이트 13 · 오류 7 · 수정 8 · PM 의사결정 11)
