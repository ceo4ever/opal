# TASK: 워크스페이스 Git 일괄 동기화 — git-sync-tool + opal-workspace-sync 스킬 신설

> 작성일: 2026-07-02 | 작업 유형: 신규 | 적용 스킬: opd | 모드: agentic
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

하나의 워크스페이스 아래에 존재하는 여러 독립 git 저장소를 순회하며 안전하게 일괄 최신화하는 기능을 OPAL 프레임워크에 신설한다. 결정론적 git 작업은 `git-sync-tool`(도구)이 집행하고, `opal-workspace-sync`(스킬)가 순회·보고·후속조치 오케스트레이션을 담당한다.

## 배경

캡틴의 워크스페이스는 두 유형이 혼재한다:
- **유형 A**: 워크스페이스 자체가 단일 git 루트 (예: ai-framework)
- **유형 B**: 워크스페이스 안에 여러 독립 git clone (예: pointail — `workspace/` 아래 7개 저장소)

여러 저장소를 매번 수동으로 `git pull` 하는 것은 반복적이고, 무분별한 pull은 로컬 미커밋 변경을 덮거나 충돌 잔재를 남길 위험이 있다. 순회+안전 최신화를 결정론적으로 집행하고, 문제 저장소는 건드리지 않고 보고·제안하는 표준 도구/스킬이 필요하다.

## 배경 분석 (대화에서 도출)

pointail 워크스페이스(`/Volumes/Data/StoreLinkStudio/pointail/workspace`) 실측 결과:

| 저장소 | 브랜치 | upstream | 작업트리 |
|--------|--------|----------|----------|
| app_android | develop | origin/develop | clean |
| app_ios | develop | origin/develop | clean |
| backend | main | origin/main | clean |
| frontend_admin | main | origin/main | clean |
| frontend_adv | main | origin/main | **DIRTY** |
| frontend_app | main | origin/main | clean |
| frontend | main | origin/main | **DIRTY** |

- `workspace/`는 상위 `pointail` 저장소의 `.gitignore`로 제외됨 → 각 하위 폴더는 서브모듈이 아닌 **독립 clone** (평면 구조, 직속 자식 1단계).
- 7개 모두 upstream tracking 정상. 2개(frontend_adv, frontend)가 dirty → 무분별 pull 시 충돌/실패 → skip 대상.
- 상위 `StoreLinkStudio/` 아래 다수 프로젝트가 유사 워크스페이스 구조를 가질 수 있음.

## 확정된 설계 방향 (대화에서 합의)

| 항목 | 확정 내용 |
|------|----------|
| 스킬명 | `opal-workspace-sync` |
| 구조 | `git-sync-tool`(결정론 도구: 순회·fetch·ff-pull 집행) + `opal-workspace-sync`(스킬: 오케스트레이션·보고·후속조치) — OPAL "enforce, don't advise" 정합 |
| 대상 결정 | `(프로젝트)/workspace` 존재 → 그 아래 순회 / 없으면 경로 질의 / 받은 경로가 단일 git 루트면 그 1개를 대상 (유형 A 통합) |
| 순회 깊이 | **직속 자식 1단계만** (재귀 안 함 — node_modules/vendor 오염 방지, Simplicity First) |
| pull 정책 | `git pull --ff-only` — clean + fast-forward 가능할 때만 자동 pull |
| skip 사유 5종 | dirty / diverged / detached HEAD / no-upstream / fetch-failed |
| 핵심 원칙 | 문제 저장소 = skip → 보고 → 제안 → **승인 후에만** 조치. 알투 자율 실행 절대 금지 (헌법 user sovereignty) |
| 자동 수행 경계 | clean+ff 저장소의 pull은 스킬 본연의 정상 동작으로 자동 수행 (매 저장소 승인 불요). 문제 저장소만 승인 게이트 |
| 보고서 | 5섹션: ① 요약 헤더 ② ✅최신화 ③ ⏭️Skip(사유별+제안조치) ④ ❌실패 ⑤ 📋조치제안(승인대기) |

## 명확화 결과

> TASK 4요소를 잠근다.

| 요소 | 확정값 | 미확정(있으면) | 의존 사실 |
|------|--------|--------------|----------|
| 목표 | 워크스페이스 직속 자식 git 저장소를 순회하여 안전 최신화(clean+ff-only pull)하고, 문제 저장소는 skip+보고+제안하는 `git-sync-tool` + `opal-workspace-sync` 신설 | - | pointail 7저장소 실측 (배경 분석) |
| 범위 | **포함**: git-sync-tool(순회·fetch·ff-pull·JSON 결과), opal-workspace-sync 스킬(대상결정·순회·5섹션 보고서·후속조치 승인게이트), install 등록, 테스트. **제외**: 재귀 순회, 문제 저장소 자동 조치(stash/rebase/force), 브랜치 전환, 커밋/푸시 | 재귀·자동조치는 향후 필요 시 확장 | 확정 설계 방향 |
| 제약 | ① 배포 경계: `~/.opal/` 직접 수정 금지 — 프로젝트 소스(`opal/tools/`, 스킬 디렉토리) 수정 후 install 재배포 (`.opal/AGENT.md` 금지사항). ② 플랫폼 분기 하드코딩 금지. ③ 도구는 `run.sh` 래퍼 + JSON 출력 규약 준수(harness §9). ④ 문제 저장소 자율 조치 절대 금지 | - | `.opal/AGENT.md` 금지사항, `opal-harness.md §9` |
| 완료기준 | ① git-sync-tool이 순회·fetch·ff-pull을 수행하고 5종 skip 사유를 정확히 판정하여 JSON 반환 ② 스킬이 대상 결정(3분기) + 5섹션 보고서 생성 ③ dirty/diverged 저장소를 건드리지 않음(무손실 검증) ④ install 등록 완료 ⑤ 테스트 시나리오 전체 PASS | - | 확정 설계 방향 보고서 5섹션 |

## 요구사항

- [ ] **git-sync-tool 신설** — 대상 경로를 받아 직속 자식(및 단일 루트) git 저장소를 순회. 각 저장소: `fetch --all --prune` → skip 판정(dirty/diverged/detached/no-upstream/fetch-failed) → clean+ff면 `pull --ff-only` → 저장소별 결과(status, 브랜치, prev→new head, ahead/behind, 사유)를 JSON으로 반환. `run.sh` 래퍼 + `"ok"` 계약 준수. (어디에: `opal/tools/git-sync-tool/`, 왜: 확정 설계 방향 구조/enforce-don't-advise, AC: 아래)
- [ ] **opal-workspace-sync 스킬 신설** — 대상 결정 3분기((프로젝트)/workspace → 질의 → 단일 루트), git-sync-tool 호출, JSON 결과를 5섹션 보고서로 정리, 문제 저장소에 사유별 후속조치를 AskUserQuestion으로 제시(승인 후에만 조치). skill-creator로 생성. (어디에: 표준 스킬 디렉토리 — ANALYSIS에서 `skills/` vs `opal/skills/` 확정, 왜: 확정 설계 방향, AC: 아래)
- [ ] **install 등록** — 신규 도구/스킬을 install 스크립트에 등록하여 `~/.opal/`로 배포되게 한다. (어디에: `scripts/install-mac.sh` 등, 왜: 배포 경계 준수, AC: install 후 `~/.opal/tools/git-sync-tool/run.sh` 및 스킬 배포 확인)
- [ ] **안전성 검증** — dirty/diverged 저장소가 pull되지 않고 원상 보존됨을 테스트로 증명. (왜: 헌법 §4 자기검증, AC: 아래 TEST 시나리오)

### AC (수용 기준)

- git-sync-tool: clean+ff 저장소 pull 성공, dirty/diverged/detached/no-upstream 저장소는 skip+사유 반환, fetch 실패는 fetch-failed로 분류. 모든 결과가 유효 JSON(`ok`, 저장소 배열).
- opal-workspace-sync: `(프로젝트)/workspace` 유무·단일 git 루트 3분기가 동작. 5섹션 보고서에 요약 집계(✅/⏭️/❌)와 skip 사유별 제안조치가 포함.
- 무손실: dirty/diverged 저장소의 작업트리·HEAD가 실행 전후 불변.
- 배포: install 실행 후 도구/스킬이 `~/.opal/`에 존재.

## 제약 조건

- **배포 경계**: `~/.opal/` 직접 편집 금지. 프로젝트 소스 수정 → install 재배포. (`.opal/AGENT.md` 금지사항)
- **플랫폼 독립성**: OS/플랫폼 분기는 어댑터 계층에만. 다만 이 도구는 로컬 git CLI 의존이므로 macOS 우선(캡틴 환경), 이식성은 셸 표준 준수로 확보.
- **도구 규약**: `~/.opal/tools/{name}/run.sh` 래퍼, JSON 출력, `"ok": false` 시 `"error"` 필드 (harness §9).
- **자율 조치 금지**: dirty/diverged 등 문제 저장소에 stash·rebase·force·commit·push 등 판단 필요 조치를 도구/스킬이 자동 수행 금지.
- **스킬 생성 방식**: 새 스킬은 skill-creator를 활용한다 (프로젝트 피드백 메모리).

## 기술 스택

- Bash (도구 `run.sh` + git CLI 호출), Python 또는 Bash (순회·JSON 조립 — ANALYSIS에서 기존 도구 구현 언어 관례 확인 후 확정), Markdown/YAML (스킬 SKILL.md)
- git CLI (`fetch`, `pull --ff-only`, `status --porcelain`, `rev-parse`, `rev-list`)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | ARCHITECTURE.md | `docs/ARCHITECTURE.md` | 도구/스킬 배포 모델·컴포넌트 구조 정합 |
| D-2 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | 네이밍·@header·배포 경계·도구 규약 |
| D-3 | 소스 | 기존 도구 (state-tool/tool-scan) | `opal/tools/` | 도구 구조·run.sh·JSON 계약 참조 패턴 |
| D-4 | 설계 | 도구 규약 | `opal/core/references/opal-harness.md §9` | OPAL Tools 호출 방식·JSON 출력 규약 |
| D-5 | 소스 | install 스크립트 | `scripts/install-mac.sh` | 신규 도구/스킬 배포 등록 |
