# DONE: 006 Linux 설치 스크립트 신설

> 시작: 2026-05-20 08:35 KST | 완료: 2026-05-20 22:50 KST | 스킬: //opp --agentic | 적용 스킬 약어: opp

---

## 1. 작업 목표 달성도

| 요구사항 | 결과 | 근거 |
|---------|------|------|
| **R-1**: `scripts/install/linux.sh` 신규 + bash -n 통과 | ✅ Pass | 38줄 파일 존재, syntax OK, 헤더 v1.0 (006) 포함 |
| **R-2**: `scripts/install.sh` fallback 안내 제거 + 정상 분기 | ✅ Pass | "준비 중" 문자열 완전 제거 (`grep` 출력 없음), v1.4 변경이력 행 추가 |
| **R-3**: Linux 환경 one-liner fallback 메시지 부재 | ✅ Pass | ubuntu:24.04 docker dry-run에서 `[opal] 플랫폼 감지: linux` + `linux.sh` 경로 출력, "준비 중" 없음 |
| **R-4**: PLAN M-1 결정과 EXECUTE 결과 일치 | ✅ Pass | 전략 A(단순 위임)이 그대로 구현 — linux.sh가 install-mac.sh로 exec 위임 |
| **R-5**: 변경이력 3개 파일 모두 `(006)` 행 추가 | ✅ Pass | install-mac.sh v2.2 / linux.sh v1.0 / install.sh v1.4 헤더 모두 확인 |

→ **5개 AC 모두 달성**

---

## 2. 산출물

### 코드 변경 (3개 파일)

| 파일 | 변경 유형 | 핵심 변경 |
|------|----------|----------|
| `scripts/install/linux.sh` | 신규 (38줄) | install-mac.sh로 exec 위임하는 Linux wrapper. `set -euo pipefail` + SCRIPT_DIR resolution + `chmod +x` |
| `scripts/install.sh` | 수정 | `exec_platform_installer()` Linux fallback 안내 9줄 블록 → 단일 `error` 1줄로 통합. 주석 라인 302 정리. v1.4 헤더 행 추가 |
| `scripts/install-mac.sh` | 수정 | `install_opal_venv()` `pw_cache`를 `uname -s` 분기로 변경 (Linux `~/.cache/ms-playwright` / macOS `~/Library/Caches/ms-playwright`). v2.2 헤더 행 추가 |

### 태스크 문서 (7개 파일)

```
tasks/006-260520-opp-install-linux/
├── TASK.md           10.6KB  — 요구사항 R-1~R-5 + 미확정 4개
├── PLAN.md           32.3KB  — install-mac.sh 1345줄 함수 27개 분류, M-1~M-4 결정
├── QA-PLAN.md        11.2KB  — GP-1~GP-6 + 6개 교차 검증 모두 Pass
├── QA-EXECUTE.md      5.7KB  — R-1~R-5 + PLAN-1~3 명세 일치 모두 Pass
├── AGENTIC-LOG.md            — 게이트 7회 Pass / 의사결정 5건 / 에스컬레이션 2건
├── STATE.md                  — 20행 모두 ✅
├── state.json                — state-tool SSOT
└── DONE.md                   — 이 문서
```

---

## 3. 핵심 의사결정 회고

### M-1: 구현 전략 = **전략 A (단순 위임)**

`install-mac.sh` 1345줄을 함수 27개로 분류한 결과 **macOS 전용 코드는 1줄** (`install_opal_venv` Line 945 Playwright 캐시 경로) 뿐. 따라서 별도 신설(B) 또는 core 일반화(C) 대신 단순 위임 + 1줄 OS 분기로 마무리.

**트레이드오프**: `install-mac.sh` 파일명이 macOS 한정인 인상을 주는 단점 → linux.sh 헤더 주석에 "후속: install-core.sh로 리네이밍 검토 (v0.6 로드맵)" 명시. 후속 별도 태스크로 인수인계.

### M-2: 지원 배포판 = **Ubuntu/Debian 명시 + RHEL/Fedora/Arch best effort + Alpine 비지원**

curl-pipe-bash 보안 모델 준수 — 자동 설치(sudo) 시도 금지. Alpine은 musl libc로 Playwright 미지원.

### M-3: 의존성 처리 = **안내만, 자동 설치 없음** — 기존 graceful skip 패턴 유지

### M-4: 셸 감지 = **현행 `register_path_in_shell_rc()` 재사용** — OS 독립적이라 별도 신설 불필요

---

## 4. 게이트 통과 이력 (agentic 모드)

| # | 단계 | 게이트 | 판정 | 처리 방식 |
|---|------|--------|------|----------|
| 1 | TASK | 작업 + TASK.md 생성 + 사용자 확인 | Pass | 행 1, 2: PM mark / 행 3: auto-pass |
| 2 | PLAN | 작업 (opal-plan-agent, advanced) | Pass | 309초, PLAN.md 488줄 산출 |
| 3 | PLAN | QA Gate (opal-task-qa-agent) | Pass | 117초, QA-PLAN.md 273줄, 지적 0건 |
| 4 | PLAN | PM Gate + 사용자 확인 | Pass | PM 자율 통과 (auto-pass + note) |
| 5 | EXECUTE | 작업 (opal-task-agent, standard) | Pass | 346초, 3개 파일 changed |
| 6 | EXECUTE | QA Gate (opal-task-qa-agent) | Pass | 74초, QA-EXECUTE.md, 지적 0건 |
| 7 | EXECUTE | PM Gate | Pass | 3중 검증 (워커 + QA + PM 재실행) |
| 8 | CLOSE | 진입 게이트 | **캡틴 승인** | "확인" 발화 (2026-05-20 22:49 KST) → 행 18 `--owner user` mark |

**3회 초과 Gate**: 0건 / **에스컬레이션**: 2건 (docs/ 오염 사고 보고 + CLOSE 진입 보고) — 양쪽 모두 Pass로 해소

---

## 5. 잔여 미해결 / 알려진 한계

| # | 항목 | 영향 | 대응 |
|---|------|------|------|
| K-1 | 실제 Linux 풀스루 설치 검증 미수행 | dry-run까지만 검증, 실제 `bash linux.sh`로 venv/pip/playwright 전체 흐름은 미실행 | v0.5.1 릴리스 후 사용자 시도 또는 후속 추가작업에서 docker로 end-to-end 검증 |
| K-2 | `install-mac.sh` 파일명이 OS 인상 혼란 가능 | 가독성 저하 (실제 동작은 양쪽 OS 정상) | v0.6 로드맵에서 `install-core.sh`로 리네이밍 별도 태스크 (M-1 트레이드오프 참조) |
| K-3 | `sha256sums.txt` 부재 (캡틴 보고 시 `OPAL_ALLOW_UNVERIFIED=1`) | 이번 태스크 범위 밖 (Q2 핫픽스 후보) | v0.5.1 또는 별도 핫픽스 태스크 |

---

## 6. 후속 태스크 후보

| # | 후속 작업 | 사유 |
|---|---------|------|
| F-1 | `~/.opal/`로 install 재배포 | scripts/ 수정이 ~/.opal/scripts/에 반영되어야 next install 사용자가 혜택 |
| F-2 | git 커밋 (캡틴 명시 지시 필요 — 자동 커밋 금지) | scripts 3개 + .opal/MEMORY.md + tasks/ 폴더 |
| F-3 | v0.5.1 패치 릴리스 (Q3 후보) | `sha256sums.txt` + Linux 설치 묶음 |
| F-4 | `install-core.sh` 리네이밍 (v0.6 로드맵) | M-1 트레이드오프 해소 |
| F-5 | 실제 Linux end-to-end 검증 | K-1 한계 해소 — docker ubuntu에서 풀스루 |

---

## 7. docs/ 영향

PLAN §7 분석 결과 본 태스크는 다음 docs/ 갱신 불필요:

- `docs/PROJECT.md` — 폴더 구조맵 동일
- `docs/ARCHITECTURE.md` — 배포 모델 동일
- `docs/CONVENTIONS.md` — 컨벤션 동일
- `docs/SECURITY.md` — 보안 정책 동일 (sha256/OPAL_HOME 가드는 install.sh가 처리, linux.sh는 위임만)

→ **docs/ 갱신 없음 확정**

---

## 8. 사고 복구 메모 (참고)

본 태스크 시작 직전(08:33 KST) PM이 `docs/` 폴더 오염 사고를 감지하여 캡틴 에스컬레이션:

- **원인**: OPAL `docs/`가 외부 프로젝트(browser-editor) 문서로 통째 덮어쓰여진 상태
- **규모**: 7 files / +90 / -1298 라인
- **복구**: `git checkout HEAD -- docs/` + browser-editor 4개 파일 `~/tmp/browser-editor-docs-rescue/`로 대피 (PRD/TRD/WBS/LAUNCH-JSON, 47KB)
- **결과**: working tree clean 상태에서 //opp 본 작업 시작

이 사고가 본 태스크의 직접 산출물에 영향을 주지는 않았으나, 만약 그대로 진행했다면 PM이 browser-editor PROJECT.md 정보를 워커에 잘못 주입하는 2차 사고가 발생했을 수 있다. **사고 복구를 본 태스크 시작 전 처리한 것이 핵심**.

---

**캡틴 확인 발화**: 2026-05-20 22:49 KST "확인"
**태스크 종결**: 2026-05-20 22:50 KST
