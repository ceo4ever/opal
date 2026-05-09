# TASK: 배포 채널 정비 + Get Started UX 통합 (P1)

> 작성일: 2026-05-08 | 작업 유형: 신규 + 개선 | 적용 스킬: opd (Full Task) | 모드: interactive
> 입력: 사용자 요청 — 138 검토 결정에 따라 P1 단일 태스크로 통합
> 출력: TASK.md
> 단계: TASK ✅ → **ANALYSIS** → PLAN → TEST-SCENARIO → EXECUTE

## 작업 목표

OPAL을 **불특정 다수에게 안전하고 일관되게 배포**하고, **설치 직후 첫 사용자 경험(Get Started)을 단일 시나리오**로 정리한다. 배포 채널과 첫 실행 UX는 본질적으로 같은 사용자 시나리오의 양면이라 P1 단일 태스크로 통합한다.

## 배경

138(opi)에서 수행한 배포·UX 검토 결과:

- 현행 `scripts/install-mac.sh`는 macOS 전용이며 1회용 — 업데이트/진단/언인스톨 진입점 부재
- README의 빠른 시작은 `{REPO_URL}` 플레이스홀더 그대로, 공개 채널 미정
- 부트스트랩이 `cwd`가 프로젝트인지 비프로젝트인지 분기하지 않아, 첫 사용자가 `//opi` 권유 또는 비서 모드로 자연스럽게 안내되지 않음
- `opal-onboarding`은 `identity.md` 부재 시 자동 발화만 가능 — 명시적 재호출 진입점 부재

## 결정 사항 (138 검토 확정)

| 영역 | 결정 |
|------|------|
| **배포 채널** | One-liner installer (`curl \| bash` / `iex (irm)`) + `opal` CLI 단일 진입점 (`install`/`update`/`doctor`/`uninstall`/`mcp`) |
| **버전 관리** | GitHub Release 태그 + 체크섬, `opal update --to vX.Y` 옵션 |
| **OS 지원** | macOS + Linux (`install.sh`) + Windows (`install.ps1`) — 동일 release 자산 사용 |
| **Get Started 분기** | 부트스트랩에서 cwd 프로젝트 판별 → (a) `//opi` 권유 / (b) 비서 모드 + 보조 안내 |
| **재진입 가능 가이드** | `//start` 슬래시 스킬 신규 + `opal doctor` CLI |
| **Homebrew·npm** | **out of scope** — 사용자 풀 누적 후 후속 태스크 |

## 범위 (영역 매트릭스)

| 영역 | 변경 대상 | 신규/수정 |
|------|----------|---------|
| A. 설치 부트스트랩 | `scripts/install.sh`(신규), `scripts/install.ps1`(신규) | 신규 |
| B. install 본체 분리 | 현행 `scripts/install-mac.sh` → `scripts/install/macos.sh` 함수 분해 | 수정 |
| C. CLI 진입점 | `opal/tools/opal-cli/`(신규) — `install`/`update`/`doctor`/`uninstall`/`mcp` 서브커맨드 | 신규 |
| D. CLI 배포 경로 | `~/.opal/bin/opal` PATH 등록 + `install_opal()` 통합 | 수정 |
| E. doctor 도구 | `opal/tools/doctor/run.sh`(신규) — 의존성·경로·MCP·부트스트래퍼 정합성 점검 | 신규 |
| F. 부트스트랩 분기 | `opal/core/AGENT.md` cwd 프로젝트 판별 + a/b next-action 라인 | 수정 |
| G. //start 스킬 | `opal/skills/opal-start/SKILL.md`(신규) + `opal/core/references/skills.md` 등록 | 신규 |
| H. onboarding 트리거 | `opal/skills/opal-onboarding/SKILL.md` triggers + 환영 메시지 보강 | 수정 |
| I. README 정제 | 빠른 시작 4 Step + 설치 명령 갱신 (`{REPO_URL}` → 실제) | 수정 |
| J. GitHub Release Workflow | `.github/workflows/release.yml`(신규) + 체크섬·attestation | 신규 |
| K. 변경이력·문서 | 영향받는 SKILL/AGENT 변경이력, ARCHITECTURE.md "배포 채널(예정)" → "현행" 갱신 | 수정 |

→ 신규 5종, 수정 6종, 영향 디렉토리 7개.

## 비목표 (Out of Scope)

- Homebrew tap (`brew install opal`) — 후속 태스크
- npm 패키지 (`@opal/cli`) — 후속 태스크
- pip 패키지, Docker 이미지 — 검토 시 배제

## 산출물

- `scripts/install.sh`, `scripts/install.ps1` (신규)
- `scripts/install/macos.sh` (리팩)
- `opal/tools/opal-cli/` 신규 디렉토리 — 서브커맨드 구현
- `opal/tools/doctor/run.sh` (신규)
- `opal/core/AGENT.md` 부트스트랩 분기 보강
- `opal/skills/opal-start/SKILL.md` (신규)
- `opal/skills/opal-onboarding/SKILL.md` triggers 갱신
- `README.md` 빠른 시작 4 Step
- `.github/workflows/release.yml` (신규)
- `docs/ARCHITECTURE.md` 배포 채널 섹션 "예정" → "현행" 전환
- `tasks/139-260508-opp-distribute-and-getstarted/{ANALYSIS.md, PLAN.md, TEST-SCENARIO.md, STATE.md, DONE.md}`

## 검증 시나리오 개요

PLAN 단계에서 상세화. 핵심 골격:

| # | 시나리오 | 환경 |
|---|---------|------|
| S1 | 신규 설치 (one-liner) → 첫 응답 부트스트랩 체크리스트 정상 출력 | mac × claude/cursor/gemini |
| S2 | 신규 설치 → identity 미존재 → onboarding 자동 발화 → identity.md 생성 → //opi 권유 | mac |
| S3 | (a) 프로젝트 폴더에서 시작 → //opi 권유 메시지 | mac |
| S4 | (b) 비프로젝트 위치에서 시작 → 비서 모드 + 보조 안내 | mac |
| S5 | `opal update` → release tag 동기화 + 사용자 데이터 보존 | mac |
| S6 | `opal doctor` → 의존성·MCP·부트스트래퍼 정합성 정상 보고 | mac/linux/win |
| S7 | `opal uninstall` → `~/.opal/` 제거 + 부트스트래퍼 마커 회수 | mac |
| S8 | Linux 신규 설치 (`install.sh`) | linux |
| S9 | Windows 신규 설치 (`install.ps1`) | win |
| S10 | GitHub Release Workflow → 태그 push → tarball + 체크섬 자동 생성 | CI |
| S11 | `//start` 재진입 → 현재 상태 진단 + 다음 액션 권유 | mac |

## 제약 (138 결정 반영)

- **배포 경계**: `~/.opal/` 직접 편집 금지 — 항상 프로젝트 소스 수정 후 install로 재배포 검증
- **플랫폼 분기 격리**: Claude/Cursor/Gemini/Antigravity 분기는 어댑터 계층(install·plugin)에서만 흡수
- **하네스 준수**: Guards (승인 게이트), 디스패치 의무 (PLAN/EXECUTE는 워커 디스패치), Citation Rules ([MUST] 인용)
- **변경이력 의무**: 영향받는 모든 SKILL/AGENT/REFERENCE에 변경이력 행 추가 (`(139)`)

## 위험 (138 검토에서 식별)

| # | 위험 | 완화 |
|---|------|------|
| R1 | PLAN.md 비대화 (Step 14~18, 영역 4개) | PLAN을 영역(A/B/C/D/E ・ F/G/H ・ I/J/K)별로 명시 분할, Step 단위로 검증 항목 따로 |
| R2 | mac/linux/win × claude/cursor/gemini × a/b 시나리오 조합 폭증 | TEST-SCENARIO에서 최소 충분 셋(S1~S11)만 채택, 나머지는 doctor가 사후 점검 |
| R3 | 단일 PR 실패 시 롤백 폭 ↑ | EXECUTE를 영역별 commit으로 분할, 실패 시 영역 단위 rollback |
| R4 | 새 PM 프로필(.opal/AGENT.md) 첫 실전 | PM 검토 게이트에서 도메인 검토 6항목 명시 적용 |
| R5 | Windows 검증 환경 부담 | install.ps1은 PowerShell 표준만 사용, 실제 Windows 머신 검증은 1회 통과로 충분 처리 |

## 캡틴 확정 결정 사항 (ANALYSIS decision_required 후속)

| ID | 항목 | 결정 | 적용 위치 |
|----|------|------|----------|
| D1 | 바이너리 명칭 | **`opal-cli`** — Homebrew core `opal`(opalrb) 충돌 회피 | `~/.opal/bin/opal-cli` PATH 등록, 모든 CLI 진입점 명령 |
| D2 | GitHub 레포 URL | **`https://github.com/ceo4ever/opal`** | One-liner: `curl -fsSL https://raw.githubusercontent.com/ceo4ever/opal/main/install.sh \| bash` / PowerShell: `iex (irm https://raw.githubusercontent.com/ceo4ever/opal/main/install.ps1)` / README §설치 |

## 다음 단계

- **PLAN 단계 진입** — `opal-plan-agent`(advanced)으로 영역 그룹별 분할 PLAN.md 작성 (Group 1 배포 인프라 / Group 2 UX / Group 3 문서·CI)
- 캡틴 명시 승인 후 EXECUTE 진입
