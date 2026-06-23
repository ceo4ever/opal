---
type: concept
title: 부트스트래퍼 마커 SSOT 단일 지점 수정 원칙
tags:
- bootstrap
- adapter
- platform
- ssot
- install
sources:
- task:040
related:
- opal-bootstrap-skip-gate
- opal-adapter-platform-isolation
- active-platform-dir-install-target-lesson
created: '2026-06-24'
updated: '2026-06-24'
status: draft
---
## 개념 요약

플랫폼별 부트스트랩 마커 텍스트의 SSOT는 install 스크립트의 emit 함수가 아니라 `opal/bootstrapper/` 디렉토리의 4개 마커 파일이며, 이 한 곳을 수정하면 macOS·Windows 어댑터가 전 플랫폼에 동일 내용을 자동 배포한다.

## 배경·문제 (WHY)

task:040 초기 전제는 "마커 문구를 install-mac.sh / windows.ps1의 emit 함수에 인라인으로 두고, 거기를 4종 플랫폼 분기로 수정한다"는 것이었다. 실제 코드를 읽은 결과 이 전제가 구조와 일치하지 않음이 드러났다 (근거: task:040 PLAN §1.2).

- install 스크립트는 마커 문구를 보유하지 않는다. `extract_bootstrap_content`(`scripts/install-mac.sh:237-245`)와 Windows의 `Get-BootstrapContent`(`scripts/install/windows.ps1:201-224`)는 `opal/bootstrapper/*.md`에서 코드블록을 **추출만** 한다.
- emit 함수(`install_opal_section` / `Install-OpalSection`)는 content-agnostic이다 — 어떤 텍스트든 `# === OPAL START/END ===` 마커로 감싸 멱등 삽입할 뿐, 문구 자체를 모른다.
- TASK가 가정한 `scripts/windows.ps1`은 존재하지 않으며 실제 미러 경로는 `scripts/install/windows.ps1`이다.

## 결정 내용 (HOW)

- 마커 문구 변경은 **4개 bootstrapper 소스 파일 한 곳만 수정**한다: `opal/bootstrapper/claude-bootstrap.md`, `codex-bootstrap.md`, `gemini-bootstrap.md`(코드블록 추출 방식), `cursor-bootstrap.mdc`(파일 전체 복사 방식, `scripts/install-mac.sh:1092`).
- 이 단일 수정으로 macOS·Windows 양쪽 어댑터가 동일 게이트를 자동 배포한다 — emit 함수를 손대지 않으며 플랫폼 분기도 추가하지 않는다.
- **추출 경계 주의**: claude/codex/gemini는 코드블록 내부에 추가 백틱이나 `` ```markdown `` 라인이 들어가면 추출이 조기 종료된다. 삽입 문구에는 코드 펜스를 쓰지 않고 인라인 백틱만 사용한다.
- **구조 차이 주의**: cursor `.mdc`는 frontmatter(`---`) + 산문이며 코드블록 추출이 아닌 파일 전체 복사다. 삽입은 frontmatter 바깥 본문에만 한다.
- 변경이력 섹션은 install `strip_deploy_md`(`scripts/install-mac.sh:220-224`)가 배포 시 잘라내므로, 배포되어야 할 내용은 변경이력 위 본문에 위치시킨다.

## 영향·관계

- 어댑터 계층 SSOT·플랫폼 분기 격리 원칙([[opal-adapter-platform-isolation]])에 정확히 부합한다 — 분기 없이 SSOT 1지점 수정으로 4종 플랫폼 + Windows 미러를 동시 충족한다.
- 이 원리 덕에 `OPAL_BOOTSTRAP=off` 스킵 게이트([[opal-bootstrap-skip-gate]])가 단일 수정으로 전 플랫폼에 배포되었다.
- install 타겟 경로 혼동 교훈([[active-platform-dir-install-target-lesson]])과 같은 결, "코드를 읽고 실제 배포 경로·SSOT를 확인한 뒤 수정 지점을 정한다"는 패턴이다.

## 근거 출처

- task:040 PLAN §1.2 — TASK 전제 vs 실제 구조 정정
- 추출 로직: `scripts/install-mac.sh:237-245`, `scripts/install/windows.ps1:201-224`
- cursor 복사: `scripts/install-mac.sh:1092`
- strip 경계: `scripts/install-mac.sh:220-224`
