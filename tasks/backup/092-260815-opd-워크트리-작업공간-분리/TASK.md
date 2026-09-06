# TASK: 태스크 작업공간 worktree 분리 (`--worktree`/`--wt` 축 신설)

> 작성일: 2026-08-15 | 작업 유형: 신규 | 적용 스킬: opd | 모드: agentic
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

OPAL 태스크 파이프라인에 모드 축과 **직교하는 `--worktree`/`--wt` 축**을 신설하여, 태스크별 코드 작업공간을 `{프로젝트}/.opal-worktrees/task_{NNN}/`에 git worktree로 격리한다. 플래그가 없으면 현행 동작을 100% 그대로 유지한다.

## 배경

캡틴이 여러 태스크를 동시에 수행하려 하나, 현재 파이프라인은 프로젝트당 단일 작업본을 전제한다. 두 태스크가 같은 작업본에서 진행되면 빌드 캐시·의존성·개발 서버 포트가 충돌하고, 브랜치 전환이 진행 중인 다른 태스크를 깨뜨린다.

동시에 프로젝트 작업 환경이 단일 형태가 아니어서, 하나의 플래그로 두 유형을 모두 흡수할 설계가 필요하다.

## 배경 분석 (대화에서 도출)

### 실측 대상 2개 프로젝트

| 축 | **유형 A — `/Volumes/Data/StoreLinkStudio/revup`** | **유형 B — `/Volumes/Data/StoreLinkStudio/mams`** |
|---|---|---|
| 루트 레포 내용 | 문서·태스크·`.opal`만 (548 추적 파일) | 문서 + 코드 전부 (3,099 추적 파일 / `workspace/` 1,006) |
| `workspace/` | `.gitignore` 처리, 독립 레포 2개 clone | 루트 레포에 추적됨 (모노레포) |
| 코드 저장소 | `storelink6`(BE) + `revup-front`(FE) 별도 | 없음 (단일) |
| 총 용량 | 161 MB | 1.9 GB |
| 빌드 산출물 | 없음 (미설치) | `.venv` 263MB, `node_modules` 642MB, `.next/dev` 784MB |
| 인프라 | 없음 | `docker-compose` 5종 |
| 태스크 스킬 분포 | opd 2·opdd 2·opi 3·opp 3·opwt 2 (문서 다수) | opd 7·opds 3 (코드 다수) |

- revup `.gitignore:2`: `"workspace/"` — 코드 레포를 루트에서 버전 관리하지 않음 (→ D-5)
- mams는 `workspace/backend`·`workspace/frontend` 이하 1,006 파일이 루트 레포에 추적됨

### 격리 대상 판별

병렬 태스크에서 실제로 충돌하는 것은 **코드 레이어**(빌드 캐시·의존성·포트·컨테이너)이며, `tasks/`·`.opal/MEMORY.json`·`.opal/brain/`은 오히려 **공유되어야 한다**(태스크 채번 중복 방지, 메모리·브레인 SSOT 유지). 문서 레이어까지 worktree로 분기하면 머지 충돌이 상시화된다.

### 파일시스템 실측 (2026-08-15)

| 검사 | 결과 |
|---|---|
| `/Volumes/Data` APFS CoW 클론 | **지원** — 300MB 파일 `cp -c` 시 디스크 추가 0MB, 일반 `cp`는 300MB 감소 |
| pnpm store 위치 | `/Volumes/Data/.pnpm-store/v10` — 프로젝트와 동일 파일시스템 (`dev=16777230`) |
| uv 캐시 위치 | `~/.cache/uv` — **다른 파일시스템** (`dev=16777235`, 시스템 볼륨), 12GB |
| `/Volumes/Data` 여유 | 217 GB |
| lock 변경 빈도 | 최근 20커밋 중 `uv.lock` 2회 / `pnpm-lock.yaml` 2회 (약 10%) |
| `pyvenv.cfg` | 프로젝트 경로 하드코딩 없음 |

→ pnpm은 동일 볼륨 store + APFS CoW라 재설치 디스크 비용이 0에 수렴한다. uv만 볼륨을 넘어 실복사 263MB가 발생하므로, `UV_CACHE_DIR`을 `/Volumes/Data`로 이전하면 이 비용도 제거된다.

### 병렬 실행 상한 요인 (mams 기준)

| # | 요인 | 실측 근거 | 심각도 |
|---|---|---|---|
| 1 | 공유 개발 DB | `workspace/backend/settings.local.yaml:41,54` DB 호스트가 원격 RDS — 모든 슬롯이 같은 DB를 봄 | 치명 |
| 2 | 포트 고정 | `workspace/docker/docker-compose.yml:55-91` — `8000:8000`·`3000:3000`·`8080:8080` | 높음 |
| 3 | compose 이름 고정 | `docker-compose.yml:14` `name: mams` + `.env.compose.local` `COMPOSE_PROJECT_NAME=mams` | 높음 |
| 4 | 런타임 자원 | next dev + uvicorn + airflow 4컨테이너 × 슬롯 | 중간 |

→ 디스크는 상한 요인이 아니다. "동시 편집"은 제한 없음, "동시 실행"은 2~3개, "스키마 마이그레이션 동반 태스크"는 동시 1개다.

### 현행 파이프라인 연동 지점

| # | 지점 | 현재 상태 |
|---|---|---|
| 1 | 모드 플래그 파싱 | 각 pilot `## Harness` 절 — 모드 3종만 인식 (`opal/skills/opal-pilot-dev/SKILL.md:14-18`) |
| 2 | TASK 후처리 | 채번 → 폴더 생성 → 모드 기록 → `state init` (→ D-2 §오케스트레이터 공통 영역) |
| 3 | state 영속화 | `state-tool init --mode`가 `state.json`에 모드 기록 |
| 4 | 워커 경로 주입 | 디스패치 프롬프트가 태스크 폴더·산출물 경로 전달 (`opal-pilot-dev/SKILL.md:36-47`) |
| 5 | code-scan 스코프 | `revup/.opal/code-scan.json` scopes가 `workspace/...` 상대경로 기준 |
| 6 | CLOSE | DONE.md → 관련 문서 갱신 → brain ingest → 회고 (`opal-pilot-dev/SKILL.md:236-260`) |

- 양 프로젝트 `.gitignore`에 `.opal-worktrees` 항목이 **없다** (실측 확인)
- git 2.50.1 — sparse-checkout cone mode 지원 확인

## 확정된 설계 방향 (대화에서 합의)

### C-1. 경로 계약

```
{프로젝트}/
  tasks/{NNN}-...            ← 태스크 문서. 분기하지 않음 (허브 고정)
  .opal-worktrees/task_{NNN}/ ← 코드 작업본만 격리
  workspace/                 ← --wt 미사용 시 쓰는 기본 작업본 (현행)
```

worktree 내부 레이아웃은 메인 프로젝트와 동일하게 맞춘다(`.opal-worktrees/task_092/workspace/...`) — 상대경로 스크립트·compose 볼륨 경로가 그대로 동작하게 하기 위함이다.

### C-2. 유형별 생성 방식

| | 유형 A (multi-repo) | 유형 B (monorepo) |
|---|---|---|
| 생성 대상 | 선언된 코드 레포 **각각** worktree | 루트 레포 **1개** worktree |
| 결과 경로 | `task_{NNN}/workspace/{backend,frontend}` | `task_{NNN}/workspace/` |
| 기법 | 다중 `git worktree add` | `git worktree add` + `sparse-checkout set workspace` |

### C-3. 프로젝트별 선언 파일 `.opal/worktree.json`

하나의 `--wt`가 두 유형을 흡수하려면 "무엇을 worktree 뜰지"를 프로젝트가 선언해야 한다. 선언 항목: `layout`(multi-repo/monorepo), `repos[]`, `branchTemplate`, `copy[]`(gitignore된 로컬 설정), `setup[]`(의존성 설치), `portOffset`.

### C-4. 브랜치 네이밍

기본값 `feat/OP-TASK-{NNN}`. `worktree.json`의 `branchTemplate`으로 프로젝트별 오버라이드한다. 치환 토큰은 `{NNN}`(태스크번호)·`{slug}`(태스크명)·`{skill}`(스킬약어).

### C-5. `.gitignore` 3계층 보장

| 계층 | 시점 | 대상 |
|---|---|---|
| 도구 | `worktree-tool create` 실행 시 멱등 자동 추가 | `--wt` 사용 시 자동 보장 |
| `opi` | 프로젝트 초기화·최신화 시 | 아직 `--wt` 미사용 기존 프로젝트 선반영 |
| 수동 | 즉시 | revup·mams 2곳 |

추가 위치는 루트 레포 `.gitignore` 1곳으로 충분하다 — 유형 A의 코드 레포는 worktree 경로가 자기 레포 밖이고, 유형 B는 sparse라 worktree 내부에서 보이지 않는다. `.git/info/exclude` 대안은 기각(양 프로젝트가 `.opal`을 팀과 커밋 공유 중).

### C-6. 정리 시점 — 머지 후 제거

CLOSE에서 **자동 제거하지 않는다**. 커밋 규칙상 PM이 머지·커밋을 자동 수행할 수 없으므로 CLOSE 시점의 worktree에는 미머지 커밋이 남아 있다. CLOSE는 "머지 대기" 상태로 남기고 안내만 하며, 캡틴이 머지·PR 처리 후 `worktree-tool remove`로 회수한다.

`remove` 3중 가드 (하나라도 걸리면 거부, `--force`로만 우회): ①작업본 dirty ②unpushed 커밋 ③브랜치 미머지.

### C-7. setup 지연 실행(lazy)

worktree 생성 시점에 의존성을 설치하지 않는다(체크아웃 + 설정파일 복사만). L1 검증·TEST 진입 시점에 필요하면 그때 실행한다. 편집만 하고 끝나는 슬롯의 설치 시간을 0으로 만드는 것이 목적이다(디스크 비용이 아니라 **시간** 절감).

lock 해시 비교 후 심볼릭 링크로 재사용하는 설계는 **폐기**한다 — APFS CoW + pnpm store 동일 볼륨으로 재설치 비용이 이미 0에 수렴하므로, 파일시스템이 해결한 문제에 추상화를 얹지 않는다(→ D-3 §2 Simplicity First).

### C-8. `UV_CACHE_DIR` 이전 (캡틴 승인 — 본 태스크 범위 포함)

uv 캐시가 시스템 볼륨에 있어 `/Volumes/Data` 프로젝트로는 하드링크/클론이 불가능하다. 캐시를 `/Volumes/Data` 하위로 이전하여 슬롯당 `.venv` 263MB 실복사를 제거한다. 더불어 `worktree-tool`이 캐시 볼륨 불일치를 진단·경고한다.

### C-9. pilot SKILL.md 10종 미변경

플래그 축 정의는 하네스 SSOT 1곳에 두고 집행은 도구가 담당한다. 산문 규칙을 pilot 10종에 복제하지 않는다 — 태스크 091의 "산문 규칙을 도구 집행으로" 기조와 일치한다.

## 명확화 결과

| 요소 | 확정값 | 미확정(있으면) | 의존 사실 |
|------|--------|--------------|----------|
| 목표 | OPAL 파이프라인에 모드 축과 직교하는 `--worktree`/`--wt` 축을 신설하여 태스크별 코드 작업공간을 `{프로젝트}/.opal-worktrees/task_{NNN}/`에 격리한다. 플래그 미사용 시 현행 동작 100% 유지 | - | C-1 |
| 범위 | **포함** — ①`.opal/worktree.json` 스키마·템플릿 ②`worktree-tool` 신설(create/list/remove/status) ③`--wt` 축 하네스 SSOT 정의 ④TASK 후처리 생성 훅 ⑤`state-tool init --worktree` 영속화 ⑥워커 디스패치 경로 계약 ⑦`.gitignore` 3계층 ⑧CLOSE 정리 안내 게이트 ⑨`UV_CACHE_DIR` 이전 + 볼륨 불일치 진단.<br>**제외** — pilot 10종 SKILL.md 개별 수정(C-9), mams 모노레포 구조 전환, 프로젝트 compose·포트 파일 실수정(선언·안내까지만), CI/CD 연동, 자동 머지 | - | C-3·C-9 |
| 제약 | ①배포 경계 — `~/.opal/` 직접 편집 금지, 프로젝트 소스 수정 후 install 재배포 ②하위호환 — `--wt` 미사용 시 `state.json`·동작·산출물 전부 현행과 동일 ③플랫폼 독립 — 표준 git 명령만 사용, APFS·macOS 전용 기능에 로직 의존 금지 ④커밋 규칙 — 자동 커밋·자동 머지·자동 worktree 제거 금지 ⑤검증 환경 — revup(유형 A)·mams(유형 B) 양쪽 실환경 실측 필수 | - | D-1 §금지사항 |
| 완료기준 | ①revup에서 `--wt` 실행 시 코드 레포 2개 worktree + `feat/OP-TASK-092` 규칙 브랜치 생성 확인 ②mams에서 sparse worktree 생성 + `tasks/`·`.opal/` 미체크아웃 확인 ③`--wt` 미사용 태스크의 `state.json` 스키마·STATE.md 렌더가 현행과 diff 0 ④`remove` 3중 가드가 각 조건에서 거부 반환 ⑤`.gitignore` 멱등 추가(2회 실행 시 중복 0행) ⑥`UV_CACHE_DIR` 이전 후 `uv sync` 정상 완료 + 신규 `.venv` 실디스크 증가 측정치 보고 ⑦`worktree-tool` 회귀 테스트 전량 pass | - | C-4·C-5·C-6·C-8 |

## 요구사항

- [ ] **F-1. `.opal/worktree.json` 스키마 정의 + 템플릿 제공**
  - 무엇을: `layout`·`repos[]`·`branchTemplate`·`copy[]`·`setup[]`·`portOffset` 6키 스키마 정의와 유형 A/B 각각의 템플릿 작성
  - 어디에: `opal/tools/worktree-tool/` (스키마) + `opal/templates/` (템플릿)
  - 왜: 하나의 `--wt`로 multi-repo·monorepo 두 유형을 흡수하기 위함 (확정 방향 C-3)
  - AC: 스키마 검증 함수가 유형 A/B 템플릿 2종을 모두 통과시키고, 필수 키 누락·`layout` 무효값·`repos[]` 경로 이탈(`..`) 3종을 각각 고유 에러 코드로 거부한다

- [ ] **F-2. `worktree-tool` 신설 — create/list/remove/status 4서브명령**
  - 무엇을: worktree 생성·열거·회수·상태조회를 결정론적으로 집행하는 CLI 신설. `run.sh` 래퍼 + JSON `"ok"` 계약
  - 어디에: `opal/tools/worktree-tool/`
  - 왜: 규칙을 산문이 아닌 도구로 집행 (→ D-3 Core Stance "Enforce, don't just advise")
  - AC: 4서브명령이 모두 JSON `{"ok": true|false}`를 반환하고, `create`가 유형 A에서 선언된 repos 수만큼 worktree를 생성하며 유형 B에서 sparse-checkout을 설정한다. 실패 시 `"error"` 필드에 에러 코드가 담긴다

- [ ] **F-3. `--worktree`/`--wt` 축을 하네스 SSOT에 정의**
  - 무엇을: 모드 축(`--interactive`/`--semi-agentic`/`--agentic`)과 **직교**하는 별도 축임을 명시하고, 조합 가능성(`--agentic --wt`)을 규정
  - 어디에: `opal/core/references/opal-harness.md` (신규 절)
  - 왜: pilot 10종에 산문을 복제하지 않고 SSOT 1곳에서 정의 (확정 방향 C-9)
  - AC: `opal-harness.md`에 `--worktree`/`--wt` 절이 존재하고, 해당 절이 ①직교 축 선언 ②`--wt` 미사용 시 현행 유지 ③`worktree.json` 부재 시 동작 3항목을 명시한다. pilot 10종 SKILL.md의 diff는 0이다

- [ ] **F-4. TASK 후처리에 worktree 생성 스텝 접합**
  - 무엇을: 태스크 채번·폴더 생성 후 `--wt` 존재 시 `worktree-tool create` 호출 스텝 추가
  - 어디에: `opal/core/references/harness/task-process.md` §오케스트레이터 공통 영역
  - 왜: 태스크 번호가 확정된 직후가 `task_{NNN}` 경로를 만들 수 있는 유일한 시점 (확정 방향 C-1)
  - AC: `task-process.md`에 `--wt` 분기 스텝이 존재하고, `--wt` 미사용 경로의 기존 스텝 순서·문구가 변경되지 않는다

- [ ] **F-5. `state-tool init --worktree <path>` 신설**
  - 무엇을: worktree 경로를 `state.json`에 영속화하여 세션 복원·경로 해석이 가능하게 한다
  - 어디에: `opal/tools/state-tool/state_tool.py`
  - 왜: 워커·PM이 어느 작업본에서 작업 중인지 도구가 답할 수 있어야 함 (확정 방향 C-1)
  - AC: `--worktree` 지정 시 `state.json`에 해당 필드가 기록되고, **미지정 시 필드가 아예 생성되지 않아** 기존 `state.json`과 스키마·바이트가 동일하다. 기존 state-tool 회귀 테스트 전량 pass

- [ ] **F-6. 워커 디스패치 경로 계약 명시**
  - 무엇을: worktree 태스크에서 워커에게 "문서 루트"와 "코드 루트" 2개를 절대경로로 분리 주입하는 규칙 추가
  - 어디에: `opal/core/references/pm/dispatch-process.md`
  - 왜: 문서는 허브 `tasks/`, 코드는 `.opal-worktrees/`로 이원화되므로 워커가 허브 `workspace/`를 잘못 수정할 위험이 있음 (배경 분석 §연동 지점 4)
  - AC: `dispatch-process.md`에 worktree 시 경로 주입 규칙이 존재하고, "상대경로 금지·절대경로 주입" 문구와 문서 루트/코드 루트 2필드 계약이 명시된다

- [ ] **F-7. `.gitignore` 멱등 추가 — 도구 + opi 2계층**
  - 무엇을: `worktree-tool create`가 루트 `.gitignore`에 `.opal-worktrees/`를 멱등 추가하고, `opi`가 프로젝트 최신화 시 동일 처리
  - 어디에: `opal/tools/worktree-tool/` + `opal/skills/opal-pilot-project-init/` (opi)
  - 왜: 양 프로젝트에 항목이 없어 미비 시 루트 레포가 worktree 전체를 변경분으로 인식 (확정 방향 C-5)
  - AC: 동일 프로젝트에서 `create`를 2회 실행해도 `.gitignore`에 `.opal-worktrees/` 행이 정확히 1개다. 항목이 이미 있으면 파일이 바이트 단위로 변경되지 않는다

- [ ] **F-8. CLOSE 정리 안내 게이트 + `remove` 3중 가드**
  - 무엇을: CLOSE에서 worktree를 자동 제거하지 않고 "머지 대기" 안내만 하며, `remove`는 dirty·unpushed·미머지 3조건을 검사
  - 어디에: `opal/skills/opal-pilot-dev/SKILL.md` STEP 6 (안내 1스텝) + `opal/tools/worktree-tool/` (가드)
  - 왜: 커밋 규칙상 PM이 머지를 자동 수행할 수 없어 CLOSE 시점에 미머지 커밋이 남음 (확정 방향 C-6)
  - AC: dirty·unpushed·미머지 3조건 각각에서 `remove`가 `{"ok": false}`와 조건별 고유 에러 코드를 반환하고, 3조건 모두 해소된 상태에서만 제거에 성공한다. `--force` 지정 시에만 우회되며 우회 사실이 stdout에 기록된다

- [ ] **F-9. `UV_CACHE_DIR` 이전 + 볼륨 불일치 진단**
  - 무엇을: (a) uv 캐시를 `/Volumes/Data` 하위로 이전하고 셸 환경변수를 영속 설정 (b) `worktree-tool`이 캐시·프로젝트 볼륨 불일치를 감지해 경고
  - 어디에: (a) 캡틴 로컬 환경 (b) `opal/tools/worktree-tool/`
  - 왜: uv 캐시가 시스템 볼륨(`dev=16777235`)에 있어 `/Volumes/Data`(`dev=16777230`) 프로젝트로 하드링크·클론이 불가하며, 슬롯당 `.venv` 263MB가 실복사됨 (확정 방향 C-8)
  - AC: (a) 이전 후 `uv sync`가 정상 완료되고, 신규 `.venv` 생성 시 실디스크 증가를 `df` 측정치로 보고한다 (b) 캐시·프로젝트 볼륨이 다를 때 `create`가 경고 메시지를 출력하되 **차단하지 않는다**

## 제약 조건

- **배포 경계**: `~/.opal/` 배포 파일을 직접 수정하지 않는다. 프로젝트 소스(`opal/`, `skills/`, `scripts/`)를 수정한 뒤 install로 재배포한다 (→ D-1 §금지사항)
- **하위호환 무손상**: `--wt` 미사용 시 `state.json` 스키마·STATE.md 렌더·산출물·디스패치 프롬프트가 전부 현행과 동일해야 한다
- **플랫폼 독립성**: 표준 git 명령만 사용한다. APFS 클론·macOS 전용 동작은 성능상 이점일 뿐이며 로직이 여기에 의존해서는 안 된다 (→ D-3 Core Stance)
- **커밋·머지 규칙**: 자동 커밋·자동 머지·자동 worktree 제거를 수행하지 않는다. worktree 생성(브랜치 생성)은 커밋이 아니므로 Guards 위반이 아니다 (→ D-2 §1 Guards)
- **검증 환경**: 프레임워크 단위 테스트만으로 완료 판정하지 않는다. revup(유형 A)·mams(유형 B) 실환경에서 실측한다
- **DB 동시성**: mams는 원격 공유 RDS를 사용하므로 스키마 마이그레이션 동반 태스크의 동시 실행을 도구가 경고한다 (차단은 하지 않는다)
- **변경이력 의무**: 스킬·에이전트·참조 문서 수정 시 변경이력 표에 행을 추가한다 (→ D-1 §금지사항)

## 기술 스택

- Python 3 (state-tool·worktree-tool — 기존 OPAL 도구 스택 일치)
- Bash (`run.sh` 래퍼, install 스크립트)
- Markdown (하네스·참조 문서 SSOT)
- git 2.50.1 (worktree, sparse-checkout cone mode)
- 검증 대상 외부 스택 — Gradle/Kotlin(revup BE), Vite/bun(revup FE), uv/Python(mams BE), pnpm/Next.js(mams FE), docker-compose(mams)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | OPAL PM 프로필 | `.opal/AGENT.md` | 배포 경계·변경이력·하네스 우회 금지 등 프로젝트 금지사항 |
| D-2 | 설계 | opal-harness.md | `opal/core/references/opal-harness.md` | Guards(구현 금지·커밋 규칙)·모드 축 정의·도구 등록 표 |
| D-3 | 설계 | PRINCIPLES.md | `~/.opal/PRINCIPLES.md` | Core Stance(Enforce·Platform-independent)·§2 Simplicity First |
| D-4 | 설계 | task-process.md | `opal/core/references/harness/task-process.md` | TASK 후처리 스텝 순서 — worktree 생성 훅 삽입 지점 |
| D-5 | 소스 | revup `.gitignore` | `/Volumes/Data/StoreLinkStudio/revup/.gitignore` | 유형 A의 `workspace/` 제외 선언 실측 근거 |
| D-6 | 소스 | mams compose | `/Volumes/Data/StoreLinkStudio/mams/workspace/docker/docker-compose.yml` | 포트·compose 이름 고정 실측 근거 |
| D-7 | 소스 | mams backend 설정 | `/Volumes/Data/StoreLinkStudio/mams/workspace/backend/settings.local.yaml` | 공유 원격 RDS 실측 근거 |
| D-8 | 소스 | opd SKILL.md | `opal/skills/opal-pilot-dev/SKILL.md` | 모드 플래그 파싱 위치·CLOSE 스텝 구조 |
| D-9 | 소스 | state_tool.py | `opal/tools/state-tool/state_tool.py` | `init --mode` 인자 처리 — `--worktree` 추가 지점 |
| D-10 | 설계 | dispatch-process.md | `opal/core/references/pm/dispatch-process.md` | 워커 컨텍스트 주입 절차 — 경로 계약 추가 지점 |
