# DONE: 배포 채널 정비 + Get Started UX 통합 (139)

- 시작: 2026-05-08 21:43
- 완료: 2026-05-09 09:09
- 모드: opd Full Task (interactive)
- Phase: TASK ✅ → ANALYSIS ✅ → PLAN ✅ → EXECUTE (Step 1~18) ✅ → CLOSE ✅

## 캡틴 확정 결정

| ID | 결정 | 적용 위치 |
|----|------|----------|
| **D1** | 바이너리 명칭 = `opal-cli` (Homebrew core `opal`/opalrb 충돌 회피) | `~/.opal/bin/opal-cli` PATH 등록, 모든 CLI 진입점 |
| **D2** | GitHub 레포 = `https://github.com/ceo4ever/opal` | one-liner, README, ARCHITECTURE.md |

## 변경 산출물 (신규 16개 + 수정 9개)

### F-001 G1 배포 인프라

| 파일 | 작업 |
|------|------|
| `scripts/install/macos.sh` | 신규 — `install-mac.sh` exec wrapper |
| `scripts/install/windows.ps1` | 신규 — Windows wrapper (대칭) |
| `scripts/install.sh` | 신규 — mac/linux 통합 one-liner (`OPAL_DRY_RUN`/`OPAL_VERSION`/`OPAL_REPO` 환경변수) |
| `scripts/install.ps1` | 신규 — Windows one-liner (irm/iex) |
| `scripts/install-mac.sh` | 수정 — `install_opal_bin`/`register_path_in_shell_rc` 신설(`:636-681`), `~/.opal/tools/` strip 확장(`:766-767`), 호출 그래프 보존 (58줄 추가만) |
| `opal/tools/opal-cli/{run.sh, lib/install.sh, lib/update.sh, lib/doctor.sh, lib/uninstall.sh, lib/mcp.sh, README.md}` | 신규 7개 — 진입점 + 5 서브커맨드 + 사용법 |
| `opal/tools/doctor/{run.sh, lib/checks.sh, README.md}` | 신규 3개 — 4섹션(Dependencies/Paths/MCP/Bootstrappers) + exit 0/1 |

### F-002 G2 Get Started UX

| 파일 | 작업 |
|------|------|
| `opal/core/AGENT.md` | 수정 — Eager Step 6.5 cwd 분기 + 부트스트랩 보고 `[안내]` 라인 + 변경이력 v2.1 |
| `opal/skills/opal-start/SKILL.md` + `references/start-flow.md` | 신규 2개 — `//start` 재진입 가이드 |
| `opal/skills/opal-onboarding/SKILL.md` | 수정 — `triggers:` 신설 + Step 9 직후 //start·//onboarding 안내 + 변경이력 v1.1 |
| `opal/core/references/opal-skills-registry.json` | 수정 — opal-start 등록 + opal-onboarding triggers 보강, version 3.3.0 → 3.4.0 |

### F-003 G3 문서·CI

| 파일 | 작업 |
|------|------|
| `.github/workflows/release.yml` | 신규 — 태그 push → tarball + sha256sums.txt + `actions/attest-build-provenance@v2` + `softprops/action-gh-release@v2`, fork 호환 |
| `README.md` | 수정 — §설치 4 Step 정제 + one-liner(mac/linux/win) + ExecutionPolicy ByPass 안내 + `{REPO_URL}` 치환 |
| `docs/ARCHITECTURE.md` | 수정 — §배포 채널 "예정 → 현행" 5행 표 (GitHub Releases / opal-cli / one-liner installer "현행", Homebrew / npm "예정") |

## 검증 결과

| 그룹 | TS | 결과 |
|------|----|------|
| F-001 (Step 7) | TS-001/003/007/008/010/011 (정적) | 6 PASS |
| F-002 (Step 12) | TS-012/013/014/015/016/017 (정적 + JSON 시뮬레이션) | 6 PASS |
| F-003 (Step 13~16) | TS-019/020/021 (산출물 검사) | 3 PASS |
| Step 17 (운영) | TS-018/022 (release Workflow + 자산) | **캡틴 (A) PASS 확인** |

## Git 결과

```
commit  5b2d6dc  feat(139): 배포 채널 정비 + Get Started UX 통합 (P1) + 138 opi PM 환경
push    main      2756fa3..5b2d6dc → origin/main
tag     v0.1      annotated tag
push    v0.1      origin/v0.1
release Workflow  PASS (캡틴 확인) — opal-v0.1.tar.gz + sha256sums.txt + attestation 자산 업로드
```

## 핵심 결정·관찰

1. **함수 분해는 단계적**: install-mac.sh의 함수 그룹별 본격 분해는 후속 리팩 태스크로 분리 — Step 1에서는 wrapper만 신설하여 호출 그래프 보존(R-A1 완화).
2. **PATH 우선순위**: `export PATH="$HOME/.opal/bin:$PATH"` 형식으로 PATH 앞에 등록 — opalrb(Homebrew core) 충돌 회피.
3. **strip 확장**: 신규 `~/.opal/tools/` 디렉토리에 `strip_deploy_md_recursive` 호출 추가 — 배포본 변경이력 노출 방지(R-A2 완화).
4. **부트스트랩 비파괴**: `[부트스트랩]` 한 줄 형식 유지 + `[안내]` 별도 줄 추가 — 기존 사용자 출력 형식 보존(R-B1 완화).
5. **Lazy 트리거 테이블 비변경**: `//start`는 `//`커맨드 입력 시 `harness/skill-commands.md` 자동 매칭이라 별도 행 추가 불필요(R-B2 완화).
6. **JSON SSOT 보강**: `opal-onboarding`의 JSON triggers에 `^onboarding$` + 자연어 정규식 추가 — `//onboarding` CLI 매칭 가능(F-002 검증 중 발견 → 즉시 보강).
7. **release.yml fork 호환**: `${{ github.repository }}` 사용으로 ceo4ever/opal 하드코딩 회피 — fork·미러 사용자에게도 동작.

## 후속 태스크 예약

| # | 항목 | 우선순위 |
|---|------|---------|
| F-1 | Homebrew tap (`brew install opal-cli`) | 2차 (사용자 풀 확보 후) |
| F-2 | npm 패키지 (`@opal/cli`) | 후속 |
| F-3 | `install-mac.sh` 함수 그룹별 본격 분해 (`install/macos.sh` wrapper만 두고 함수 분리) | Backlog |
| F-4 | `.gitignore` `.opal/` 룰 정밀화 — 기계 생성 파일(`.venv/`, `projects/`, `code-scan.json`)만 ignore, AGENT.md/MEMORY.md/memory/는 추적 | Backlog |
| F-5 | Windows VM 실제 검증 (TS-006) — `install/windows.ps1` 핵심 로직 활성화 | Backlog |
| F-6 | doctor `~/.opal/.venv/` 활성 진단 추가, MCP 등록 검증 강화 | Backlog |

## CLOSE 결과

- 캡틴 명시 승인: "확인했으니 close 해줘" (2026-05-09)
- 태스크 139 정상 종료. main + v0.1 release 운영 가능.
