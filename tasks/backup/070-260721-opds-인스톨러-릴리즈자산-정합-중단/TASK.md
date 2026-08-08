# TASK: 인스톨러 3종 릴리즈-자산 다운로드 정합 (체크섬·추출·폴백 수정)

> 작성일: 2026-07-21 | 작업 유형: 오류 | 적용 스킬: opds | 모드: agentic
> 입력: 사용자 요청 (`opal-cli update` 체크섬 불일치 장애 리포트)
> 출력: TASK.md

## 작업 목표

인스톨러 3종(`opal-cli update` / `install.sh` / `install.ps1`)이 **다운로드하는 tarball과 SHA-256 검증 기준 파일이 서로 다른 산출물**이어서 발생하는 구조적 체크섬 불일치를 제거한다. 다운로드 대상을 릴리즈 자산(`opal-vX.Y.Z.tar.gz`)으로 통일하고, 추출·폴백 로직을 이에 맞게 정합화한다.

## 배경

roi.kang 사용자가 Windows에서 `opal-cli update`(v0.5.0 → v0.6.10) 실행 시 체크섬 불일치로 업데이트가 하드 실패했다:

```
[ERROR] 체크섬 불일치! 다운로드가 손상되었을 수 있습니다.
[ERROR]   기대값: c97257f9ec51acd928efcc48e998f2030ff50e2c56d0ec14c4db021030123619
[ERROR]   실제값: cb231fe8162d43365a834b601c4e9a1aeeed4a35df2aac68ab2d8b2b9dbb3d98
```

다운로드 손상이 아니라, 서로 다른 두 tarball을 비교하기 때문에 발생하는 **구조적(재현성 100%) 결함**이다.

## 배경 분석 (대화에서 도출)

### 근본 원인 (실증 완료)

인스톨러는 두 개의 서로 다른 tarball을 교차 참조한다:

| 항목 | 실제 대상 | 해시 |
|------|----------|------|
| **다운로드** | GitHub 자동생성 소스아카이브 `github.com/ceo4ever/opal/archive/refs/tags/v0.6.10.tar.gz` — 최상위 `opal-0.6.10/` 디렉토리 포함 | `cb231fe8…` (= 사용자 "실제값") |
| **검증 기준** | 릴리즈 자산 `sha256sums.txt` → 워크플로우가 `git archive HEAD`로 만든 `opal-v0.6.10.tar.gz` (최상위 디렉토리 없음) | `c97257f9…` (= 사용자 "기대값") |

두 tarball은 최상위 디렉토리 구조·압축이 달라 해시가 영원히 불일치한다. 실증:
- GitHub 소스아카이브 top: `opal-0.6.10/`, `opal-0.6.10/.claude/…`
- 릴리즈 자산 top: `.claude/`, `.cursorrules` (prefix 없음)
- 릴리즈 자산 실제 해시 = `c97257f9…` = sha256sums.txt 기대값 (자산끼리는 일치)

### 계통성 (v0.6.10만의 문제 아님)

- sha256sums.txt 자산 존재: v0.6.0/0.6.5/0.6.9/0.6.10 = HTTP 200, v0.5.0/0.5.3 = HTTP 404
- v0.5.x는 자산이 없어 검증이 graceful skip → 그래서 "업데이트가 됐던" 것
- v0.6.9도 동일 불일치 실증: 기대값 `bc671201…` vs GitHub아카이브 실제 `cc600763…`
- **결론**: 릴리즈 자산이 생성되기 시작한 v0.6.0부터 계통적 결함. roi.kang은 v0.5.0(자산 없음)→v0.6.10(자산 있음) 전이에서 처음 게이트에 걸림

### 도입 시점

`install.sh` 변경이력(줄 35)에 "release 자산 URL(opal-{tag}.tar.gz) 사용으로 sha256 매칭 (139 추가작업)"이라 기록됨. 그러나 이후 "139 추가작업"에서 다운로드 URL만 `archive/refs/tags`로 바꾸고 검증 대상은 릴리즈 자산 그대로 둬서 불일치 발생.

### 3종 인스톨러 결함 위치

| 파일 | 다운로드 (GitHub 아카이브) | 검증 기준 (릴리즈 자산) |
|------|--------------------------|----------------------|
| `opal/tools/opal-cli/lib/update.sh` | 줄 130/132 (`archive/refs/heads|tags`) | 줄 174 (`releases/download/.../sha256sums.txt`) + 줄 181 (`grep opal-${version}.tar.gz`) |
| `scripts/install.sh` | 줄 116 (`archive/refs/tags`) | 줄 121 (`SHA_URL`) + 줄 258 (`grep ${tarball_name}`) + 줄 269/273 (`shasum -c`/`sha256sum -c`) |
| `scripts/install.ps1` | 줄 98 (`archive/refs/tags`) | 줄 102 (`ShaUrl`) |

### 추출 로직 주의 (Option A 핵심 리스크)

- 현재 추출은 `--strip-components=1`로 GitHub 아카이브의 `opal-0.6.10/` prefix를 제거한다 (`update.sh` 줄 211, `install.sh` 줄 295).
- 릴리즈 자산은 prefix가 **없으므로**, `--strip-components=1`을 그대로 적용하면 `.claude/…`의 첫 경로 요소가 잘못 제거되어 **추출이 조용히 깨진다**.
- 따라서 다운로드 대상을 릴리즈 자산으로 바꾸는 변경은 추출 분기 수정을 반드시 동반해야 한다.

### 사용자 측 현재 우회 수단 부재

- 불일치는 `return 1` 하드 실패 → `OPAL_ALLOW_UNVERIFIED=1`·`--force` 모두 무력(그 옵트인은 sha256sums.txt "부재" 경로 전용, "불일치"엔 미적용).
- 코드 수정 배포 없이는 정식 릴리즈로 업데이트 불가.

## 확정된 설계 방향 (대화에서 합의)

캡틴이 AskUserQuestion에서 **Option A(인스톨러가 릴리즈 자산 다운로드)**를 선택했다.

1. **다운로드 대상 전환**: 3종 인스톨러가 릴리즈 태그(v*)에서 `releases/download/${version}/opal-${version}.tar.gz`(워크플로우 산출물)를 받는다. 이 자산은 sha256sums.txt·build provenance와 완전 정합한다.
2. **폴백 유지**: 릴리즈 자산이 404(자산 미생성 릴리즈·main 브랜치 등)이면 기존 `archive/refs/tags`(태그) / `archive/refs/heads`(브랜치)로 폴백하되, 이 경로는 UNVERIFIED로 처리한다(기존 무결성 배너/거부 로직 재사용).
3. **추출 정합**: 릴리즈 자산(prefix 없음)은 `--strip-components=1` 없이 추출, GitHub 아카이브 폴백(prefix 있음)은 `--strip-components=1` 적용 — 다운로드 소스에 따라 추출 분기를 결정한다.
4. **검증 정합**: 릴리즈 자산을 받은 경우 기존 sha256sums.txt 검증이 그대로 매칭된다(파일명 token `opal-${version}.tar.gz` 유지).

### 부트스트랩 함정 (릴리즈 노트 필수 동반 사항)

- Option A 수정은 **새 버전 tarball**에 실린다. 그러나 업데이트를 실행하는 주체는 사용자에게 이미 깔린 **구버전 인스톨러**다 → 구 로직은 여전히 GitHub 아카이브를 받고 릴리즈자산 체크섬으로 검증하므로, 새 버전에도 sha256sums.txt가 있으면 동일하게 실패한다.
- 즉 v0.6.x(자산 보유)에 갇힌 사용자는 `opal-cli update`로 수정본에 **자가 도달 불가**.
- **복구 경로**: 수정된 main의 install.sh를 원라이너로 재설치 → `curl -fsSL https://raw.githubusercontent.com/ceo4ever/opal/main/scripts/install.sh | bash` (Windows: `iex (irm .../main/scripts/install.ps1)`). 수정 install.sh가 릴리즈 자산을 직접 받아 검증하므로 정상 동작.
- **완료기준에 반영**: 재릴리즈(v0.6.11 등)의 릴리즈 노트에 "기존 v0.6.x 사용자는 위 원라이너로 재설치" 안내를 반드시 포함한다.

## 명확화 결과

> TASK 4요소 잠금.

| 요소 | 확정값 | 미확정(있으면) | 의존 사실 |
|------|--------|--------------|----------|
| 목표 | 인스톨러 3종의 다운로드 대상을 릴리즈 자산으로 통일하여 체크섬 불일치 제거 (Option A) | - | AskUserQuestion 확정 |
| 범위 | 포함: `update.sh`·`install.sh`·`install.ps1`의 다운로드 URL·추출·폴백·검증 정합 + 테스트 추가 + 재릴리즈 안내. 제외: 워크플로우(release.yml) 변경, sha256sums.txt 생성 방식 변경 | - | Option A는 인스톨러 측만 수정 |
| 제약 | (1) 릴리즈 자산 404 시 기존 아카이브 폴백·UNVERIFIED 로직 보존 (2) 추출 prefix 처리 소스별 분기 (3) bash 3.2 호환(macOS) (4) PowerShell Restricted/RemoteSigned 호환 (5) 배포 경계: `~/.opal/` 직접수정 금지, 프로젝트 소스 수정 후 install 재배포 (6) 커밋은 캡틴 명시 요청 시에만 | - | 헌법·PM 프로필 금지사항 |
| 완료기준 | (1) 3종 인스톨러가 v* 릴리즈에서 릴리즈 자산을 받아 sha256sums.txt 검증 통과 (2) 릴리즈 자산 추출이 prefix 없이 정확 (3) 자산 404 시 아카이브 폴백 동작 + UNVERIFIED 처리 (4) 회귀: 기존 main/브랜치 업데이트 경로 유지 (5) 테스트가 다운로드-검증-추출 정합을 검증하고 통과 (6) 재릴리즈 안내 문구 산출 | - | - |

## 요구사항

- [ ] **R1 다운로드 대상 전환 (update.sh)**: v* 버전 시 `releases/download/${version}/opal-${version}.tar.gz`를 1순위로 받고, 404 시 `archive/refs/tags/${version}.tar.gz`로 폴백. 어디에: `opal/tools/opal-cli/lib/update.sh` tarball_url 결정부(줄 127~133). 왜: 확정 방향 §1·§2. AC: v* 시 자산 URL 우선 curl, 실패 시 아카이브 폴백 분기가 코드에 존재.
- [ ] **R2 다운로드 대상 전환 (install.sh)**: 동일 원칙. 어디에: `scripts/install.sh` TARBALL_URL 결정부(줄 112~121). AC: 자산 우선 + 아카이브 폴백 분기 존재.
- [ ] **R3 다운로드 대상 전환 (install.ps1)**: 동일 원칙. 어디에: `scripts/install.ps1` TarballUrl 결정부(줄 95~102). AC: 자산 우선 + 아카이브 폴백 분기 존재.
- [ ] **R4 추출 정합 (update.sh·install.sh)**: 릴리즈 자산(prefix 없음)은 strip 없이, 아카이브 폴백(prefix 있음)은 `--strip-components=1`로 추출하도록 소스별 분기. 어디에: `update.sh` 줄 207~213, `install.sh` 줄 295 인근. AC: 자산 추출 시 `.claude/` 등 최상위 파일이 온전히 배치됨.
- [ ] **R5 폴백·UNVERIFIED 보존**: 자산 404 폴백 경로는 기존 무결성 배너/거부(`OPAL_ALLOW_UNVERIFIED`, 비대화형 거부, main UNVERIFIED 배너) 로직을 재사용. 어디에: 3종 인스톨러 검증부. AC: 폴백 경로에서 검증 없이 진행 시 UNVERIFIED 경고 출력.
- [ ] **R6 검증 매칭 확인**: 자산을 받은 경우 sha256sums.txt의 `opal-${version}.tar.gz` 항목과 매칭되어 검증 통과. AC: 실제 v0.6.10 자산으로 검증 시 PASS.
- [ ] **R7 회귀 방지**: `main` 브랜치·commit SHA·미기록 버전 업데이트 경로는 기존과 동일 동작(아카이브 heads + UNVERIFIED). AC: `--to main` dry-run/실경로가 기존과 동일.
- [ ] **R8 테스트 추가**: `scripts/tests/`에 다운로드 대상 선택·추출 prefix 분기·폴백을 검증하는 테스트 추가(기존 `test_version_stamp.sh` 패턴 참조). AC: 신규 테스트가 정합을 검증하고 PASS.
- [ ] **R9 재릴리즈 안내 산출**: 기존 v0.6.x 사용자 복구용 원라이너 재설치 안내 문구를 DONE.md/릴리즈 노트 초안으로 산출. AC: 안내 문구가 산출물에 존재.
- [ ] **R10 변경이력 갱신**: 수정한 각 스크립트의 변경이력 표/헤더에 태스크 070 행 추가. AC: 3종 파일 모두 변경이력에 070 기재.

## 제약 조건

- bash 3.2 호환 (macOS 기본 bash) — `update.sh`·`install.sh`.
- PowerShell 5.1 + Restricted/RemoteSigned 환경 호환 — `install.ps1`.
- 배포 경계: `~/.opal/` 배포본 직접 수정 금지 → 프로젝트 소스(`opal/`·`scripts/`) 수정 후 install로 재배포.
- 커밋은 캡틴 명시 요청 시에만 (agentic 모드에서도 유지).
- 릴리즈 자산 404 폴백은 반드시 UNVERIFIED로 취급 (무결성 저하 은닉 금지).

## 기술 스택

- Bash (macOS/Linux 설치 스크립트), PowerShell (Windows 설치 스크립트)
- GitHub Releases / GitHub Actions (release.yml — 이번 범위에서 변경 없음, 참조만)
- 테스트: shell 기반 (`scripts/tests/*.sh`)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | opal-cli update | `opal/tools/opal-cli/lib/update.sh` | 수정 대상 1 (다운로드·검증·추출) |
| D-2 | 소스 | install.sh | `scripts/install.sh` | 수정 대상 2 |
| D-3 | 소스 | install.ps1 | `scripts/install.ps1` | 수정 대상 3 |
| D-4 | 소스 | release workflow | `.github/workflows/release.yml` | 검증 기준(sha256sums.txt) 생성 방식 참조 (변경 없음) |
| D-5 | 소스 | 기존 테스트 | `scripts/tests/test_version_stamp.sh` | 테스트 작성 패턴 참조 |
| D-6 | 설계 | export 규칙 | `.gitattributes` | 릴리즈 자산 tarball 구성(export-ignore/subst) 근거 |
