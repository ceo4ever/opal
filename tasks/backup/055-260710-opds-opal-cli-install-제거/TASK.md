# TASK: opal-cli install 서브커맨드 완전 제거

> 작성일: 2026-07-10 | 작업 유형: 개선(제거) | 적용 스킬: opds | 모드: agentic
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

`opal-cli install` 서브커맨드를 디스패처에서 **완전 제거**하고, 이를 전제하던 안내 문구들을 이식 가능한 경로(원라이너 / `opal-cli update`)로 리다이렉트한다.

## 배경

`opal-cli install`은 로컬 소스(FRAMEWORK_ROOT 또는 소스 레포)를 전제하는 "수동 진입점"이라, 소스가 없는 머신(다른 사람 PC 등)에서 실행 시 "설치 스크립트를 찾을 수 없습니다 → clone 하라"로만 안내되어 UX 함정이 된다. 그러나 이식 가능한 경로는 이미 완비되어 있다:
- **신규 설치(어느 OS·소스 없음)**: 원라이너 `curl -fsSL .../scripts/install.sh | bash` (mac/linux) / `iex (irm .../scripts/install.ps1)` (Windows).
- **갱신·재설치(어느 OS·소스 없음)**: `opal-cli update` — 원격 tarball fetch + 사용자 데이터 보존.
- **개발자 소스 배포**: `bash scripts/install-mac.sh` 직접.

따라서 `opal-cli install` 서브커맨드는 잉여이며, 캡틴 결정은 **완전 제거**다.

## 배경 분석 (대화에서 도출)

- (A)안 "install = OS감지+배포삭제+원격재설치"는 기각: `~/.opal` 배포본에 사용자 데이터(identity.md·projects·community-skills)가 함께 있어, 삭제 시 정체성 소실(위험)·보존 시 `opal-cli update`와 중복. 새 가치 없음.
- 캡틴 선택: **완전 제거**(리다이렉트 스텁도 없이 디스패처에서 삭제).
- 참조 전수(코드 대조):
  - dispatch/도움말/헤더: `opal/tools/opal-cli/run.sh` (dispatch `install|` 라인 114, 도움말 63/75, 헤더 주석 10/13, unknown 메시지 106)
  - 로직 파일: `opal/tools/opal-cli/lib/install.sh` (삭제 대상)
  - 문서: `opal/tools/opal-cli/README.md:47`
  - **연쇄 안내(깨짐 방지 필수)**: `lib/doctor.sh:52`, `lib/update.sh:147`, `lib/console.sh:47/53/123` — 미설치 시 "opal-cli install 을 먼저 실행하세요"로 안내 → 원라이너/`opal-cli update`로 교체 필요.

## 확정된 설계 방향 (대화에서 합의)

1. `opal-cli install` 디스패치 분기·도움말·예시·헤더 주석·lib/install.sh를 **완전 제거**. (리다이렉트 스텁 없음 — unknown subcommand 표준 처리로 흡수)
2. "install 먼저 실행" 안내(doctor/update/console)는 **원라이너(신규) 또는 `opal-cli update`(갱신)**로 리다이렉트.
3. unknown 메시지(run.sh:106 "run install or update first")도 install 제거에 맞춰 갱신.

## 명확화 결과

| 요소 | 확정값 | 미확정 | 의존 사실 |
|------|--------|--------|----------|
| 목표 | opal-cli install 서브커맨드 완전 제거 + 관련 안내 리다이렉트 | - | - |
| 범위 | 포함: run.sh(dispatch/help/헤더/unknown), lib/install.sh 삭제, README, doctor.sh·update.sh·console.sh 안내 리다이렉트, ARCHITECTURE.md(install 언급 시). 제외: update/one-liner 로직 변경, 신규 리다이렉트 스텁 | - | - |
| 제약 | 배포 경계(opal/ 소스만, ~/.opal 직접편집 금지) / 타 서브커맨드(update/doctor/uninstall/mcp/console) 회귀 0 / 변경이력 행 추가 | - | - |
| 완료기준 | 아래 요구사항 AC 전체 + 동작검증(opal-cli 정상·install 미노출) | - | - |

## 요구사항

- [ ] **R-1 install 디스패치 제거**: `run.sh`에서 `install` 분기·도움말(install 줄)·예시(`opal-cli install`)·헤더 주석의 install 언급 제거.
  - AC: `opal-cli --help` 출력에 `install` 미노출. `opal-cli install` 실행 시 unknown subcommand 표준 처리(설치 시도 안 함).
- [ ] **R-2 lib/install.sh 삭제**: `opal/tools/opal-cli/lib/install.sh` 파일 제거. run.sh가 이 파일을 source/호출하지 않도록 정리.
  - AC: 파일 부재 + run.sh에 install.sh 참조 0건.
- [ ] **R-3 연쇄 안내 리다이렉트**: `lib/doctor.sh:52`·`lib/update.sh:147`·`lib/console.sh:47/53/123`의 "opal-cli install 먼저 실행" 문구를 원라이너(신규 설치) 또는 `opal-cli update`(갱신)로 교체.
  - AC: `grep -rn "opal-cli install" opal/tools/opal-cli/` 결과 0건(변경이력 제외). 각 안내가 유효 명령을 가리킴.
- [ ] **R-4 unknown 메시지 갱신**: `run.sh:106` "opal-cli (unknown — run install or update first)"에서 install 제거 → "run update first" 또는 원라이너 안내.
  - AC: 해당 문구에 install 없음.
- [ ] **R-5 문서 정합**: `opal-cli/README.md` install 항목 제거. `docs/ARCHITECTURE.md`에 opal-cli install 언급 있으면 정정. 변경 문서에 변경이력 행 추가.
  - AC: opal-cli/README에 install 미노출. 변경 문서 변경이력 054... (055) 행 존재.

## 제약 조건

- **배포 경계**: `opal/` 소스만 수정, `~/.opal/` 직접 편집 금지. 검증은 소스 기준(+ 필요 시 재배포는 CLOSE 후 캡틴 지시).
- **회귀 0**: update/doctor/uninstall/mcp/console 서브커맨드 정상 동작 유지.
- **플랫폼 독립성**: 안내 문구는 mac/linux(원라이너 sh)·Windows(ps1) 모두 포괄하거나 `opal-cli update`로 통일.

## 기술 스택

- Bash (opal-cli run.sh + lib/*.sh) · Markdown(README/ARCHITECTURE)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | opal-cli run.sh | `opal/tools/opal-cli/run.sh` | dispatch/help/헤더/unknown — R-1/R-4 |
| D-2 | 소스 | lib/install.sh | `opal/tools/opal-cli/lib/install.sh` | 삭제 대상 — R-2 |
| D-3 | 소스 | lib/{doctor,update,console}.sh | `opal/tools/opal-cli/lib/` | "install 먼저" 안내 리다이렉트 — R-3 |
| D-4 | 설계 | opal-cli README | `opal/tools/opal-cli/README.md` | install 항목 제거 — R-5 |
| D-5 | 설계 | ARCHITECTURE.md | `docs/ARCHITECTURE.md` | 설치 경로 서술 정합 — R-5 |
| D-6 | 소스 | update.sh 원격 로직 | `opal/tools/opal-cli/lib/update.sh` | 이식 경로(대체 명령) 근거 |
