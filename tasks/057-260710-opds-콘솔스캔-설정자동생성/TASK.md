# TASK: opal-cli console scan — console.config.json 자동 생성·머지 업데이트

> 작성일: 2026-07-10 | 작업 유형: 신규 | 적용 스킬: opds | 모드: semi-agentic
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

`opal-cli console scan` 서브명령을 신설하여 `~/.opal/console.config.json`을 없으면 생성하고 있으면 머지 갱신함으로써, 신규 머신에서 대시보드에 프로젝트가 보이지 않는 문제를 근본 해결한다.

## 배경

- `~/.opal/console.config.json`은 OPAL Console(dashboard) 백엔드가 프로젝트 스캔 루트로 사용하는 런타임 설정이다 (`dashboard/backend/config.py:19`).
- 현재 이 파일을 생성·갱신하는 코드 경로가 전무하다 — `config.py:33 load_config()`는 읽기만 하고, install 스크립트·`opal/tools/opal-cli/lib/console.sh` 어디에도 생성 로직이 없다.
- 파일 부재 시 기본값 `~/workspace`(depth 2)로 폴백하므로 (`dashboard/backend/config.py:21-22`), 프로젝트가 다른 경로에 있는 신규 머신에서는 대시보드가 떠도 프로젝트 목록이 빈다.
- **실사고**: 신규 구성원 맥북에서 install 후 대시보드는 기동됐으나 프로젝트가 보이지 않는 문제가 실제 발생했다 (2026-07-10 캡틴 보고).

## 배경 분석 (대화에서 도출)

| 항목 | 확인 내용 | 근거 |
|------|----------|------|
| config 소비자 | Console 백엔드 `load_config()` 유일. 쓰기 코드 0건 (json.dump·write 계열 grep 0건) | `dashboard/backend/config.py:33-52` |
| 기본값 폴백 | scan_roots=`~/workspace`, depth=2, exclude 5종 | `dashboard/backend/config.py:21-23` |
| 문서·코드 불일치 | config.py 독스트링 "설정 파일 생성은 install 단계에서 수행" ↔ install 스크립트에 미구현. 원 PLAN(021)은 "첫 기동 시 생성"이라 서술 — 3서술 상이 | `dashboard/backend/config.py:34-38` / `tasks/backup/021-260615-opd-opal-console/PLAN.md:231` |
| 기존 파일 출처 | 캡틴 머신의 실물은 태스크 021 진행 중 수동 작성 ("런타임 설정 (배포물 아님)") | `tasks/backup/021-260615-opd-opal-console/DONE.md` |
| 프로젝트 식별 방식 | 스캐너는 `.opal/AGENT.md` 마커 디스크 스캔으로 OPAL 프로젝트를 식별 | `docs/ARCHITECTURE.md:267` |
| console 서브명령 현황 | `lib/console.sh`에 start/stop/status/open 존재, config 관련 기능 없음 | `opal/tools/opal-cli/lib/console.sh` |

## 확정된 설계 방향 (대화에서 합의)

| # | 방향 | 합의 내용 |
|---|------|----------|
| C-1 | 명령 형태 | `opal-cli console scan [기준경로...]` — 기준경로 아래를 제한 깊이로 탐색해 `.opal/AGENT.md` 마커 프로젝트를 발견하고, 그 부모 디렉토리들을 scan_roots로 도출 |
| C-2 | 탐색 범위 | 전체 디스크 스캔 금지. 기준경로 명시 인자 우선, 미지정 시 안전한 기본 후보(`$HOME`) — `/Volumes/*` 등 외부 볼륨은 명시 인자로만 |
| C-3 | 머지 규칙 | config 없으면 생성, 있으면 머지(기존 roots 보존 + 신규 추가 + 중복 제거). scan이 못 찾은 기존 root도 지우지 않음 — 제거는 `--prune` 명시 플래그로만 |
| C-4 | install 연동 | `install_dashboard()` 말미에 scan 1회 자동 실행 (신규 머신 문제의 근본 해결) |
| C-5 | start 가드 | `console start` 시 config 부재면 "scan을 먼저 실행하세요" 안내 출력 |
| C-6 | 출력 계약 | 기존 opal-cli 도구 계약과 동일한 JSON: `{"ok":true, "created":true|false, "added_roots":[...], "projects_found":N}` |

## 명확화 결과

| 요소 | 확정값 | 미확정(있으면) | 의존 사실 |
|------|--------|--------------|----------|
| 목표 | `opal-cli console scan`으로 console.config.json 자동 생성·머지 갱신 + install/start 연동 | - | config 쓰기 경로 전무 (`dashboard/backend/config.py:33-52`) |
| 범위 | 포함: console.sh scan 서브명령, install-mac.sh 연동, start 가드, config.py 독스트링 정정, windows.ps1 동기화, 테스트. 제외: dashboard 백엔드 기능 변경(읽기 로직 유지), 설정 UI/API | - | 021 결정 C-2 "1차 = 읽기 전용 뷰어" |
| 제약 | 전체 디스크 스캔 금지 / 머지 시 사용자 수기 편집분 보존 / ~/.opal 직접 수정 금지(소스 수정 후 install) / JSON 출력 계약 준수 | - | `.opal/AGENT.md` §금지사항 배포 경계 |
| 완료기준 | 신규 머신 시나리오(config 부재)에서 scan 1회로 config 생성 + 대시보드 프로젝트 목록 표시. 기존 config 머지 시 수기 항목 보존. 테스트 GREEN | - | TEST-SCENARIO.md에서 검증 |

## 요구사항

- [ ] F-1 **scan 서브명령 신설** — 무엇을: `console scan [기준경로...] [--prune] [--depth N]` 서브명령 구현 / 어디에: `opal/tools/opal-cli/lib/console.sh` (+ `run.sh` 라우팅·help) / 왜: config 자동 생성·갱신 경로 부재 (배경 분석) / AC: config 부재 상태에서 `console scan <경로>` 실행 시 파일이 생성되고 `"ok":true, "created":true`가 반환된다. `.opal/AGENT.md` 마커 프로젝트의 부모 디렉토리가 scan_roots에 포함된다
- [ ] F-2 **머지 규칙 구현** — 무엇을: 기존 config 존재 시 roots 보존+신규 추가+중복 제거, `--prune` 없이는 제거 안 함, scan_depth·exclude 등 기존 키 보존 / 어디에: F-1 동일 / 왜: 확정 방향 C-3 / AC: 수기 root가 있는 config에 scan 실행 후 해당 root가 그대로 남아 있고, 신규 root가 중복 없이 추가된다. `--prune` 지정 시에만 미발견 root가 제거된다
- [ ] F-3 **install 연동** — 무엇을: `install_dashboard()` 말미에 `console scan` 1회 자동 실행(실패해도 install 중단 없음) / 어디에: `scripts/install-mac.sh` / 왜: 확정 방향 C-4, 신규 머신 실사고 / AC: install 실행 후 config 파일이 존재한다. scan 실패 시에도 install은 정상 종료한다
- [ ] F-4 **start 가드** — 무엇을: `console start` 시 config 부재면 scan 안내 메시지 출력(기동은 계속) / 어디에: `opal/tools/opal-cli/lib/console.sh` / 왜: 확정 방향 C-5 / AC: config 부재 상태 start 출력에 scan 안내 문구가 포함된다
- [ ] F-5 **config.py 독스트링 정정** — 무엇을: "설정 파일 생성은 install 단계에서 수행" 서술을 scan 명령 기준으로 정정 / 어디에: `dashboard/backend/config.py:34-38` / 왜: 배경 분석 문서·코드 불일치 / AC: 독스트링이 실제 생성 경로(`opal-cli console scan` + install 연동)를 정확히 서술한다
- [ ] F-6 **windows.ps1 동기화** — 무엇을: install 연동(F-3 등가)을 Windows 설치 스크립트에 반영 / 어디에: `scripts/install/windows.ps1` (021에서 동기화된 파일) / 왜: 멀티 플랫폼 배포 경계 / AC: windows.ps1에 등가 로직이 존재한다 (실기 검증은 제외, 코드 리뷰 수준)
- [ ] F-7 **테스트** — 무엇을: scan 생성/머지/prune/install 연동 시나리오 테스트 / 어디에: opal-cli 기존 테스트 체계(PLAN에서 위치 확정) / 왜: 완료기준 / AC: 신규 테스트 전체 GREEN + 기존 테스트 회귀 0

## 제약 조건

- [MUST] `.opal/AGENT.md` §금지사항: "~/.opal/ 직접 편집 금지 — 항상 프로젝트 소스를 수정한 후 install로 배포한다."
- 전체 디스크 스캔 금지 — 기준경로 + 제한 깊이 탐색만 (C-2)
- 머지 시 사용자 수기 편집분(roots·exclude·미지정 키) 보존 — 덮어쓰기 금지 (C-3)
- opal-cli JSON 출력 계약 준수 (`"ok": true|false`, 실패 시 `"error"` 필드) — `opal/core/references/opal-harness.md` §9 도구 호출 방식
- dashboard 백엔드는 읽기 전용 유지 — 021 결정 C-2 위반 금지
- 스킬·도구 문서 수정 시 변경이력 표 행 추가 (`.opal/AGENT.md` §업무 수행 지침)

## 기술 스택

- Bash (opal-cli — macOS zsh/bash 3.2 호환)
- Python 3 / FastAPI (dashboard 백엔드 — 독스트링 정정만)
- PowerShell (windows.ps1 동기화)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | Console config 로더 | `dashboard/backend/config.py` | 기본값·로드 로직 SSOT |
| D-2 | 소스 | opal-cli console 서브명령 | `opal/tools/opal-cli/lib/console.sh` | scan 신설 대상 |
| D-3 | 소스 | mac install 스크립트 | `scripts/install-mac.sh` | install_dashboard() 연동 지점 |
| D-4 | 설계 | 021 opal-console 태스크 | `tasks/backup/021-260615-opd-opal-console/` | 원 설계 결정(C-2 읽기 전용)·config 도입 경위 |
| D-5 | 설계 | 아키텍처 문서 | `docs/ARCHITECTURE.md` | 프로젝트 식별(.opal/AGENT.md 마커 스캔) 방식 |
