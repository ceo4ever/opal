# PLAN: 릴리즈 체크섬 검증 경로 정합 — 다운로드 대상과 검증 대상 일치

> 작성일: 2026-08-07 | 입력: TASK.md (ANALYSIS.md 없음 — 코드 직접 분석)
> 모드: Multi-Feature (기능 6개)
> 실행 모드: **복잡** (§6)

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

릴리즈 태그(`v*`) 설치·업데이트 시 3개 부트스트랩 스크립트가 **체크섬이 발행된 자산과 동일한 파일**을 내려받도록 다운로드 대상을 릴리즈 자산으로 전환하고, 자산 부재 시 자동 아카이브 폴백 + 기존 UNVERIFIED 정책을 유지한다. 아카이브 형식 차이(상위 디렉토리 유무)에 대응하는 추출 분기와 `install.sh`의 매칭 취약점 정정을 함께 수행하여 `opal-cli update`·`install.ps1`의 하드 실패 2건과 `install.sh`의 검증 무음 스킵 1건을 동시에 해소한다.

`release.yml`·`.gitattributes`·main 브랜치 설치 동작은 변경하지 않는다 (→ D-9 §범위).

### 1.2 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | `update.sh` 다운로드 대상 전환 + 체크섬 하드닝 | TASK F-1 | P0 | 없음 (§3.0 규약 준수) |
| F-002 | `install.sh` 다운로드 대상 전환 + 매칭 정정 | TASK F-2 | P0 | F-001 (bash 헬퍼 이식) |
| F-003 | `install.ps1` 다운로드 대상 전환 | TASK F-3 | P0 | 없음 (§3.0 규약 준수) |
| F-004 | 릴리즈 자산 부재 시 폴백 + UNVERIFIED 정책 유지 | TASK F-4 | P0 | F-001·F-002·F-003 내부 구현 |
| F-005 | 추출 구조 분기 (`--strip-components` 판정) | TASK F-5 | P0 | F-001·F-002·F-003 내부 구현 |
| F-006 | 3경로 × 3조합 실측 검증 | TASK F-6 | P0 | F-001~F-005 |

> F-004·F-005는 **횡단 기능**이다 — 독립 파일을 갖지 않고 F-001~F-003 각 파일 내부에 동일 규약(§3.0)으로 구현된다. 따라서 §4.2 Step의 `소속 기능`에 복수 F-ID가 병기된다.

### 1.3 기능 의존 그래프 (ASCII)

```
        §3.0 DL-CONTRACT (설계 SSOT — 3경로 공통 규약)
                     │
        ┌────────────┼────────────┐
        │            │            │
     F-001        F-003        (F-004·F-005 = F-001~F-003 내부 횡단)
   update.sh    install.ps1
        │
     F-002
   install.sh
        │
        └────────────┴────────────┴──→ F-006 (3경로 × 3조합 실측)
```

---

## 리스크 가설 표

> PLAN 단계에서 작성. TEST-SCENARIO.md §1의 입력이 됨 (TEST-SCENARIO.md는 PM+소유자가 별도 작성).

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | §3.0 자산 존재 판정 (sha256sums.txt 단일 신호) | 네트워크 순단을 "자산 부재"로 오판 → 검증 가능한 설치가 UNVERIFIED로 강등 | P1 | L2 (자산 URL 차단 실측) | S: sha URL만 차단 후 install 실행 |
| H-2 | §3.0 strip 판정 (`_detect_strip`) | 추출 루트 계약 (`VERSION`·`opal/` 존재) | P0 | L1(3형식 판정 단위) + L2(실추출) | S: 발행자산/자동아카이브/main 3형식 추출 |
| H-3 | F-004 폴백 시 체크섬 정책 | 폴백 후에도 sha256sums.txt와 비교하면 **항상** 불일치 → 현 결함 재현 | P0 | L1 + L2 | S: 자산 없는 태그로 설치 |
| H-4 | F-002 로컬 파일명 `opal.tar.gz` → 자산명 | `OPAL_TARBALL` 참조 지점(`extract_to_tmp`) 누락 시 추출 실패 | P1 | L1 (grep 잔존 0건) + L2 | S: install.sh 전 경로 1회 실행 |
| H-5 | F-005 main 브랜치 경로 | 기존 `--strip-components=1` 동작 (`opal-main/` prefix) | P0 | L2 (main 실설치) | S: `OPAL_VERSION=main` 설치 |
| H-6 | F-001 `sha256sum` 하드 의존 (`update.sh:179`) | 미탑재 환경에서 `actual_sha` 공백 → 오판 | P1 | L1 (헬퍼 단위) + L2 | S: `sha256sum` 미탑재 시뮬레이션 |
| H-7 | F-003 PowerShell 조건부 `--strip-components` 인자 구성 | tar 인자 배열 전개 오류 → 추출 실패 | P1 | L2 (Windows) / 불가 시 L1 대체 | S: install.ps1 릴리즈 태그 설치 |
| H-8 | F-004 비대화형 거부 정책 | `OPAL_ALLOW_UNVERIFIED` 미지정 비대화형 = 거부 (R-2·GC-001) | P0 | L2 (파이프 stdin 실행) | S: 비대화형 + 자산 부재 |
| H-9 | F-002 grep 매칭 (`install.sh:258`) | `.`이 정규식 와일드카드로 동작 → 오매칭/미매칭 | P1 | L1 (고정문자열 매칭 단위) | S: 항목명 대조 |
| H-10 | F-001 빈 기대값 통과 (`update.sh:182`) | `expected_sha` 공백 시 **무음 통과** — install.sh와 동일 결함 클래스 | P0 | L1 | S: 손상 sha 파일 주입 |

---

## 2. 기능별 분석

### F-001: `update.sh` 다운로드 대상 전환 + 체크섬 하드닝

#### 2.1.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 공통 | `opal/tools/opal-cli/lib/update.sh` | `opal-cli update` 서브커맨드 — 버전 결정·다운로드·검증·추출·재설치 | 수정 |
| 공통 | `opal/tools/opal-cli/run.sh` | 진입 디스패처, `set -euo pipefail` 상속 | 참조 (변경 없음) |
| 배치 | `.github/workflows/release.yml` | 발행 자산 생성 (참조 전용) | 변경 없음 |

#### 2.1.2 현재 구현

- 버전 자동 결정: `/releases/latest` → `/tags?per_page=1` → `main` 3단 폴백 (`opal/tools/opal-cli/lib/update.sh:80-111`).
- Tarball URL: 릴리즈 태그 여부와 무관하게 **자동 아카이브** 사용 (`:127-133`).
  - `[MUST]` 현행 코드 `` `opal/tools/opal-cli/lib/update.sh:132` ``: `tarball_url="https://github.com/${opal_repo}/archive/refs/tags/${version}.tar.gz"`
- 로컬 저장명: `$tmp_dir/opal.tar.gz` (`:160`) — 발행 자산명과 무관.
- 체크섬: `sha256sum` 하드 호출(`:179`) 후 `grep "opal-${version}.tar.gz"`로 기대값 추출(`:181`), 불일치 시 하드 실패(`:182-187`).
- 추출: `tar ... --strip-components=1 2>/dev/null || tar ...`(`:211-212`) — **prefix 없는 아카이브에서도 `--strip-components=1`이 성공(exit 0)** 하므로 폴백이 발동하지 않고 루트 파일이 소리 없이 잘린다.
- `run.sh:24`가 `set -euo pipefail`을 설정하므로 파이프라인 실패가 즉시 종료된다 (`opal/tools/opal-cli/run.sh:24`).

**결함 3종 (실측 근거)**:
1. 받는 파일(자동 아카이브, SHA `463a5842…`) ≠ 검증 대상(발행 자산, SHA `1ae94e27…`) → 항상 하드 실패 (→ D-9 §A-1).
2. `expected_sha`가 공백이면 `[[ -n "$expected_sha" && ... ]]` 조건이 거짓이 되어 **무음 통과** (`:182`) — H-10.
3. `sha256sum`은 macOS 기본 탑재가 아니다 (macOS 26.5에서는 `/sbin/sha256sum` 존재를 실측 확인했으나 구버전 보장 없음) — H-6.

#### 2.1.3 영향 범위

- 상위 호출: `opal/tools/opal-cli/run.sh` → `cmd_update`.
- 하위 호출: 추출 결과의 `scripts/install/macos.sh` 또는 `scripts/install-mac.sh`(`:230-234`), `OPAL_VERSION` 전달(`:246`).
- 공유 상태: `~/.opal/VERSION` (다음 update 비교 기준), 추출 tarball의 `VERSION` 각인값 채택 로직(`:218-226`)은 추출 루트 정합에 직접 의존한다 → F-005와 결합.
- 관련 테스트: 없음 (자동화 테스트 부재 — 실측 검증으로 대체, F-006).

---

### F-002: `install.sh` 다운로드 대상 전환 + 매칭 정정

#### 2.2.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 공통 | `scripts/install.sh` | macOS/Linux one-liner 부트스트랩 | 수정 |
| 공통 | `scripts/install/macos.sh`, `scripts/install/linux.sh` | 플랫폼 인스톨러 (`OPAL_SOURCE_DIR` 소비) | 참조 (변경 없음) |

#### 2.2.2 현재 구현

- URL: 릴리즈 태그도 자동 아카이브 (`scripts/install.sh:115-119`), sha URL은 릴리즈 자산 (`:121`) — **소스가 어긋난 지점**.
- 로컬 저장명: `${OPAL_TMP}/opal.tar.gz` (`:180`).
- `verify_checksum`(`:210-279`):
  - sha256sums.txt 404 시 릴리즈 태그면 옵트인/프롬프트/비대화형 거부 (`:232-247`) — 이 정책은 **보존 대상**.
  - 항목 매칭: `grep "${tarball_name}" "${sha_file}"` (`:258`) — `tarball_name`이 `opal.tar.gz`이고 `.`이 정규식 와일드카드라 `opal-v0.6.11.tar.gz`와 매칭되지 않는다(실측). 미매칭 시 `warn` 후 `return 0` (`:260-263`) → **무음 스킵**.
  - 실제 검증: `shasum -a 256 -c ... --ignore-missing`(mac) / `sha256sum -c`(linux) (`:268-276`).
- 추출: `tar ... --strip-components=1` 고정 (`:295-296`).
- `adopt_stamped_version`(`:345-357`)이 추출 루트의 `VERSION`을 읽는다 → F-005와 결합.

**실측 확인**: macOS `shasum -a 256 -c <file> --ignore-missing`은 지원되며, 검증 대상이 하나도 없으면 `no file was verified`로 **exit 1**을 반환한다. 즉 파일명만 정합되면 검증 자체는 정상 작동한다.

#### 2.2.3 영향 범위

- `OPAL_TARBALL` 참조 지점: `fetch_tarball`(`:180,200`), `verify_checksum`(`:256`), `extract_to_tmp`(`:295`) — 파일명 변경 시 3곳 모두 정합 필요 (H-4).
- `OPAL_TMP` 생성 위치: 현재 `fetch_tarball` 내부(`:179`) — sha256sums.txt를 **다운로드보다 먼저** 받아야 하므로 생성 시점을 앞으로 옮겨야 한다.
- `main()` 호출 순서(`:374-380`): `detect_platform → check_deps → fetch_tarball → verify_checksum → extract_to_tmp → adopt_stamped_version → exec_platform_installer`.
- 상위: curl-pipe-bash 원라이너 (`README`·`update.sh:148-149` 안내 문구).

---

### F-003: `install.ps1` 다운로드 대상 전환

#### 2.3.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 공통 | `scripts/install.ps1` | Windows one-liner 부트스트랩 | 수정 |
| 공통 | `scripts/install/windows.ps1` | Windows 인스톨러 (`-OpalVersion` 소비) | 참조 (변경 없음) |

#### 2.3.2 현재 구현

- URL: 릴리즈 태그도 자동 아카이브 (`scripts/install.ps1:97-101`), sha URL은 릴리즈 자산 (`:102`).
- 로컬 저장명: `opal-$OpalVersion.tar.gz` (`:141`) — **발행 자산명과 우연히 동일**(`opal-v0.6.11.tar.gz`). 따라서 항목은 정확히 매칭되고, 내용이 다른 파일이라 `throw`로 중단된다 (`:227-229`).
- 항목 매칭은 `[regex]::Escape($tarballName)` 사용 (`:217`) — bash와 달리 정규식 취약점 없음. **변경 불필요**.
- 미매칭 시 `Write-Warning` 후 `return` (`:220-223`) — bash와 동일한 무음 스킵 클래스. 릴리즈 자산 경로에서는 하드 실패로 승격 필요.
- 추출: `tar -xzf ... --strip-components 1 --exclude='tasks/*' ...` 고정 (`:260-261`).
- `VERSION` 각인값 채택(`:275-283`) → F-005와 결합.

#### 2.3.3 영향 범위

- `$script:OpalVersion`은 `Resolve-DefaultVersion`(`:61-86`)·`Invoke-PlatformInstaller`(`:280`) 양쪽에서 갱신되며 `windows.ps1`에 `-OpalVersion`으로 전달된다 (`:300`).
- `--exclude='tasks/*'` 계열 인자(`:261`)는 `.gitattributes:7`의 `tasks/ export-ignore`로 이미 아카이브에서 제외되므로 **무해한 이중 방어**다. strip 값 변경과 무관하게 유지한다.
- `.NOTES` 블록의 변경이력(`:28-29`, v1.0에서 정지)과 실제 유지 중인 `# 변경이력` 블록(`:35-48`, v1.0.7)이 이원화되어 있다 — 갱신 대상은 후자.

---

### F-004: 릴리즈 자산 부재 시 폴백 + UNVERIFIED 정책 유지

#### 2.4.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 공통 | `opal/tools/opal-cli/lib/update.sh` | 폴백 분기 + UNVERIFIED 경로 (`:190-204`) | 수정 |
| 공통 | `scripts/install.sh` | 폴백 분기 + UNVERIFIED 경로 (`:231-251`) | 수정 |
| 공통 | `scripts/install.ps1` | 폴백 분기 + UNVERIFIED 경로 (`:189-211`) | 수정 |

#### 2.4.2 현재 구현

3경로 모두 "릴리즈 태그 + sha256sums.txt 부재" 조건에서 동일한 3분기를 구현하고 있다:
1. `OPAL_ALLOW_UNVERIFIED=1` → 경고 후 진행
2. 비대화형(`! -t 0` 또는 `OPAL_AUTO_INSTALL=1` / `-not [Environment]::UserInteractive`) → 거부
3. 대화형 → 프롬프트, 디폴트 N

이 정책 자체는 정상이며 **그대로 보존**한다 (→ D-9 §제약: "무결성 검증을 우회하는 방향의 해소는 채택하지 않는다").

**결함**: 현재는 이 분기가 "sha256sums.txt 부재"에만 반응한다. 새 규약에서는 "**릴리즈 자산으로 다운로드하지 못한 모든 경우**"가 이 경로로 수렴해야 한다.

#### 2.4.3 영향 범위

- 보안 계약: R-2·GC-001 (무결성 검증 도입 의도). 비대화형 거부가 깨지면 보안 회귀 (H-8).
- 폴백 진입 시 이미 받아둔 sha256sums.txt가 남아 있으면 **비교에 쓰이면 안 된다** (H-3).

---

### F-005: 추출 구조 분기

#### 2.5.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 공통 | `opal/tools/opal-cli/lib/update.sh` | 추출부 (`:207-213`) | 수정 |
| 공통 | `scripts/install.sh` | `extract_to_tmp` (`:283-299`) | 수정 |
| 공통 | `scripts/install.ps1` | `Invoke-PlatformInstaller` 추출부 (`:252-270`) | 수정 |

#### 2.5.2 현재 구현 — 실측 대조

`tar -tzf` 실측 결과 (v0.6.11 기준):

| 아카이브 | 최상위 세그먼트 종류 수 | 루트 직속 파일 수 | 필요 strip |
|---------|---------------------|---------------|-----------|
| 발행 자산 `opal-v0.6.11.tar.gz` | 13 | 6 (`.cursorrules`, `CLAUDE.md`, `GEMINI.md`, `LICENSE`, `README.md`, `VERSION`) | **0** |
| 자동 아카이브 `archive/refs/tags/v0.6.11.tar.gz` | 1 (`opal-0.6.11/`) | 0 | **1** |
| main 아카이브 `archive/refs/heads/main.tar.gz` | 1 (`opal-main/`) | 0 | **1** |

현행 3경로 모두 `--strip-components=1` 고정이므로 발행 자산에서 루트 파일이 잘린다. `update.sh:211-212`의 `|| tar ...` 폴백은 **prefix 없는 아카이브에서 첫 tar가 exit 0으로 성공하므로 발동하지 않는다**.

#### 2.5.3 영향 범위

- 추출 루트에 `VERSION`이 없으면 `adopt_stamped_version`(`install.sh:345-357`)·`update.sh:218-226`·`install.ps1:275-283`의 각인값 채택이 전부 무력화되어 `~/.opal/VERSION`에 잘못된 값이 기록된다.
- 추출 루트에 `scripts/install/`이 없으면 인스톨러 탐색이 실패한다 (`install.sh:310-313`, `update.sh:230-234`, `install.ps1:286`).

---

### F-006: 3경로 × 3조합 실측 검증

#### 2.6.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 공통 | `tasks/085-260807-opds-릴리즈-체크섬-검증경로-정합/TEST-SCENARIO.md` | 시나리오 SSOT (PM+소유자 작성) | 신규 (PLAN 범위 밖) |
| 공통 | `tasks/085-260807-opds-릴리즈-체크섬-검증경로-정합/TEST.md` | 실측 증거 기록 | 신규 |

#### 2.6.2 현재 구현

자동화 테스트 스위트가 없다. 검증은 실행 증거(명령어 + 출력) 기록으로 수행한다.

#### 2.6.3 영향 범위

- Windows 실행 환경 부재 가능성 → AC가 "사유 + 대체 검증 방법 명시"를 허용한다 (→ D-9 §F-6 AC).

---

## 3. 기능별 설계

### 3.0 공통 다운로드 규약 — DL-CONTRACT (3경로 설계 SSOT)

> 이 절이 F-001·F-002·F-003의 **단일 규약 SSOT**다. 3경로는 이 규약을 각 언어로 동형 구현한다.

#### D-A. 코드 공유 불가 판정 (판단 포인트 1)

**결론: 공통 함수/공통 파일 추출은 불가능하다. 규약 단일화로 대체한다.**

근거:

- `[MUST]` `` `scripts/install.sh` §부분 다운로드 실행 방지(`:44-48`) ``: "이 파일 전체가 다운로드된 뒤 `main "$@"` 이 호출된다." — curl-pipe-bash 진입점은 **단일 파일 자기완결**이 보안 계약이며, 외부 파일 `source`는 이 계약을 깨뜨린다.
- `scripts/install.sh`·`scripts/install.ps1`은 **소스를 내려받기 전에** 실행되므로 저장소 내 공통 라이브러리를 참조할 수 없다.
- `opal/tools/opal-cli/lib/update.sh`는 `~/.opal/tools/opal-cli/lib/`에 배포되어 실행되므로 (`opal/tools/opal-cli/run.sh:31-38`) 위 두 파일과 공유 런타임 위치가 없다.
- `install.ps1`은 언어 자체가 다르다.

**대안 검토 및 기각**: `update.sh`가 태그의 `scripts/install.sh`를 내려받아 위임하는 방식은 코드 중복을 제거하지만, update의 사용자 데이터 보존 계약(`opal/tools/opal-cli/lib/update.sh:11-15`)과 인스톨러 호출 경로(`:230-246`)를 재설계해야 하므로 회귀 위험이 크고 이번 태스크 범위를 벗어난다 (→ D-9 §범위). **기각**.

**정합 수단**: (a) 아래 규약 문구·함수명·로그 문구를 3경로 동일하게 사용, (b) 각 파일 헤더 주석에 `DL-CONTRACT (task 085)` 동일 문구 각인, (c) §4.2 Step 4에서 정적 대조 검사로 드리프트 차단.

#### D-B. 다운로드 소스 결정 (S-1·S-2, 판단 포인트 2)

**릴리즈 자산 존재 판정은 `sha256sums.txt` 다운로드 성공 여부를 단일 신호로 사용한다.**

근거:

- `[MUST]` `` `.github/workflows/release.yml:53-56` ``: `files: | opal-*.tar.gz` / `sha256sums.txt` — 두 자산은 **동일 릴리즈 생성 스텝**에서 함께 업로드되므로, sha256sums.txt 존재는 tarball 자산 존재와 동치다.
- **HTTP HEAD 프로브 미채택 근거(실측)**: `curl -fsSL -I` 로 존재하지 않는 릴리즈 자산을 조회하면 exit `22`(HTTP error)가 아니라 exit `56`을 반환한다(리다이렉트 대상에서의 수신 실패). 네트워크 실패와 자산 부재를 exit code로 구분할 수 없어 판정 신호로 부적합하다.
- **GitHub API 조회 미채택 근거**: 왕복이 1회 늘고 rate-limit(비인증 60/h) 영향을 받는다. 3경로 모두 이미 sha256sums.txt를 받고 있으므로 **추가 왕복 0**이 되는 재배치가 더 낫다.

**자산 파일명은 하드코딩하지 않고 `sha256sums.txt`의 파일명 컬럼에서 파생한다.** 발행 자산명이 바뀌어도 자동 추종하며, 검증 대상과 다운로드 대상이 **구조적으로** 동일해진다 (실측: `sha256sums.txt` 1행 = `1ae94e27…  opal-v0.6.11.tar.gz`).

#### D-C. 결정 흐름 (의사코드 — 3경로 동형)

```
resolve_download_plan(version):
  # 산출: TARBALL_URL, TARBALL_NAME, CHECKSUM_MODE, SHA_FILE
  if version !~ ^v :                        # 브랜치 설치
      TARBALL_URL   = {repo}/archive/refs/heads/{version}.tar.gz
      TARBALL_NAME  = opal-{version}.tar.gz
      CHECKSUM_MODE = branch                # 기존 UNVERIFIED 배너만
      return

  SHA_URL = {repo}/releases/download/{version}/sha256sums.txt
  if download(SHA_URL -> SHA_FILE) 실패:
      → fallback_to_archive("릴리즈 자산 없음")
      return

  ASSET = first_tar_gz_name(SHA_FILE)       # 파일명 컬럼 파생
  if ASSET 공백:
      → fallback_to_archive("sha256sums.txt 형식 이상")
      return

  TARBALL_URL   = {repo}/releases/download/{version}/{ASSET}
  TARBALL_NAME  = {ASSET}                   # [MUST] 로컬명 = 발행 자산명
  CHECKSUM_MODE = verify

fallback_to_archive(reason):
  TARBALL_URL   = {repo}/archive/refs/tags/{version}.tar.gz
  TARBALL_NAME  = opal-{version}-archive.tar.gz
  CHECKSUM_MODE = unverified
  discard(SHA_FILE)                         # [MUST] H-3 — 비교 금지
  warn("릴리즈 자산 미사용 폴백: {reason}")

fetch_tarball():
  if download(TARBALL_URL -> TMP/TARBALL_NAME) 실패:
      if CHECKSUM_MODE == verify:
          → fallback_to_archive("릴리즈 자산 다운로드 실패")
          if download(TARBALL_URL -> TMP/TARBALL_NAME) 실패: hard_error
      else:
          hard_error

apply_checksum_policy():
  case CHECKSUM_MODE:
    verify:      # [MUST] 무음 스킵 금지
       entry = fixed_string_find(SHA_FILE, TARBALL_NAME)
       if entry 없음:            hard_error("항목 부재 — 규약 위반")
       expected = entry.hash
       if expected 공백:          hard_error("기대값 파싱 실패")
       actual   = sha256(TMP/TARBALL_NAME)
       if actual 공백:            hard_error("sha256 도구 없음")
       if actual != expected:     hard_error("체크섬 불일치")
       success("체크섬 검증 완료")
    unverified:  # 기존 R-2·GC-001 3분기 그대로
       if OPAL_ALLOW_UNVERIFIED == 1: warn(UNVERIFIED); proceed
       elif 비대화형:                  hard_error(거부 + 옵트인 안내)
       else:                          prompt(default N)
    branch:
       warn("[UNVERIFIED] '{version}' 브랜치 — SHA-256 무결성 검증 없음")
```

**폴백 시 체크섬 정책 (판단 포인트 3) 결론**:

- `[MUST]` 폴백 경로에서는 `sha256sums.txt`를 **어떤 경우에도 비교에 사용하지 않는다**. 발행 자산과 자동 아카이브는 서로 다른 파일이므로(`1ae94e27…` vs `463a5842…`, → D-9 §A-1) 비교하면 **100% 불일치**한다 — 현 결함의 정확한 재현이다.
- 폴백은 곧 `CHECKSUM_MODE=unverified`이며, 기존 옵트인/프롬프트/비대화형 거부 3분기로 수렴한다. 즉 **fail-closed**: 비대화형에서는 여전히 거부된다 (H-8 보존).

#### D-D. 추출 구조 판정 (S-3, 판단 포인트 4)

**판정 규칙 (결정론)**:

```
strip = 1  iff  (루트 직속 항목 수 == 0)  AND  (최상위 세그먼트 종류 수 == 1)
strip = 0  그 외 전부
```

- "루트 직속 항목" = `tar -tzf` 출력 라인에 `/`가 없는 항목.
- 3형식 실측 대조는 §2.5.2 표 참조 — 발행 자산 → 0, 자동 아카이브 → 1, main 아카이브 → 1. **세 형식 모두 규칙과 일치**.

**bash 구현 (3경로 중 bash 2곳 동일)**:

```bash
# tar 목록 1회 스캔으로 strip 값(0|1)을 결정한다. grep 미사용(옵션 조합 이식성 회피), awk 단일 패스.
_dl_detect_strip() {
    tar -tzf "$1" | awk -F/ '
        NF == 0 { next }
        { if ($0 !~ /\//) root++; tops[$1] = 1 }
        END { n = 0; for (t in tops) n++; print (root == 0 && n == 1) ? 1 : 0 }
    '
}
```

**PowerShell 구현**:

```powershell
function Get-DlStripComponents {
    param([Parameter(Mandatory)][string] $TarballPath)
    $entries = @(& tar -tzf $TarballPath) | Where-Object { $_ }
    if ($LASTEXITCODE -ne 0 -or $entries.Count -eq 0) { throw "[OPAL] tarball 목록 조회 실패: $TarballPath" }
    $rootFiles = @($entries | Where-Object { $_ -notmatch '/' })
    $tops      = @($entries | ForEach-Object { ($_ -split '/', 2)[0] } | Sort-Object -Unique)
    if ($rootFiles.Count -eq 0 -and $tops.Count -eq 1) { return 1 } else { return 0 }
}
```

**추출 후 사후조건 (필수)**:

```
[MUST] 추출 완료 후 {extract_dir}/VERSION 과 {extract_dir}/opal/ 이 모두 존재해야 한다.
       하나라도 없으면 즉시 하드 실패한다 — 조용한 진행 금지.
```

근거: 이 두 항목이 각인 버전 채택(`scripts/install.sh:345-357`)과 인스톨러 탐색(`scripts/install.sh:310-313`)의 전제이며, 사후조건 검사가 없으면 strip 오판이 **다음 단계에서야** 모호한 오류로 드러난다.

#### D-E. 회귀 방지 지점 (판단 포인트 5)

| # | 회귀 위험 지점 | 현행 동작 | 보존 방법 |
|---|--------------|---------|----------|
| RG-1 | main 브랜치 URL | `archive/refs/heads/{branch}.tar.gz` | `CHECKSUM_MODE=branch` 분기에서 **동일 URL 유지**, 변경 없음 |
| RG-2 | main 브랜치 추출 | `--strip-components=1` | `_dl_detect_strip`이 main 아카이브에 대해 **1을 반환**(실측 §2.5.2) |
| RG-3 | main 브랜치 UNVERIFIED 배너 | `install.sh:370-372`, `update.sh:168-170`, `install.ps1:324-326` | 위치·문구 **무변경** |
| RG-4 | 릴리즈 태그 + sha 부재 시 3분기 | 옵트인/프롬프트/거부 | `unverified` 모드로 **동일 코드 재사용** |
| RG-5 | `install.sh` 로컬 파일명 참조 3지점 | `OPAL_TARBALL` | 변수 유지하고 **값만** 변경, `:180,200,256,295` 전수 확인 |
| RG-6 | `install.ps1` tasks 제외 인자 | `--exclude='tasks/*'` 외 3개 | strip 값과 무관하게 **유지** |
| RG-7 | DRY-RUN 흐름 (`OPAL_DRY_RUN=1`) | 네트워크 접근 0, 빈 파일로 흐름 검증 | `resolve_download_plan`에 **DRY-RUN 조기 반환** 추가 필수 |
| RG-8 | `opal-cli update --dry-run` | URL만 출력 후 종료 (`update.sh:138-143`) | 규약 적용 후에도 네트워크 접근 없이 출력 유지 |

`[MUST]` RG-7·RG-8: `resolve_download_plan`은 네트워크를 사용하므로 **DRY-RUN에서 반드시 조기 반환**해야 한다. 누락 시 dry-run이 네트워크에 접근하는 회귀가 발생한다 (`scripts/install.sh:75-78,184-189,211-214`의 기존 DRY-RUN 계약).

#### D-F. 변경이력 헤더 갱신 (판단 포인트 6)

**@header 적용 여부 판정**: `.opal/code-scan.json`의 `extensions`는 `.py/.js/.ts/.jsx/.tsx/.vue/.svelte/.kt/.kts/.java/.swift/.md`이며 `.sh`·`.ps1`을 포함하지 않는다. `scopes`는 `opal/`·`dashboard/frontend/src/`·`dashboard/backend/`이며 `scripts/`를 포함하지 않는다. 따라서 **code-scan @header 규칙은 이번 변경 대상 3파일에 적용되지 않는다**.

`[MUST]` `` `docs/CONVENTIONS.md` §구현 규칙 > @header 규칙 ``: "기록 위치는 `code-scan target <file>` 판정을 따른다 — 인라인 주석 또는 외부 소스 코드 지도(`.opal/code-map/`) 2소스 중 하나이며, 사람·워커가 임의 선택하지 않는다."
→ 스코프 밖이므로 판정 대상 아님. 대신 **각 파일의 기존 인라인 `변경이력` 주석 관례**를 따른다.

| 파일 | 기존 변경이력 블록 | 현재 최신 | 부여 버전 | 형식 |
|------|-----------------|---------|---------|------|
| `opal/tools/opal-cli/lib/update.sh` | `:17-24` | v1.0.6 | **v1.1** | `#   v1.1 2026-08-07 HH:mm KST: <내용> (085)` |
| `scripts/install.sh` | `:32-41` | v1.5 | **v1.6** | `#   v1.6 2026-08-07 HH:mm KST: <내용> (085)` |
| `scripts/install.ps1` | `:35-48` | v1.0.7 | **v1.1** | `#   v1.1   2026-08-07 HH:mm  <내용> (085)` |

- 패치가 아닌 **동작 변경**이므로 minor 승격(v1.1 / v1.6).
- `HH:mm`은 실행 시점의 실제 KST 시각을 기록한다 (`docs/CONVENTIONS.md` §변경이력: "일시 형식: `YYYY-MM-DD HH:mm` (KST 기준)").
- `install.ps1`의 `.NOTES` 블록 변경이력(`:28-29`)은 v1.0에서 정지된 이원 기록이다. 이번에는 **유지 중인 `# 변경이력` 블록만 갱신**하고, `.NOTES` 이원화는 §9 R-7로 관찰 기록만 남긴다(범위 밖).
- 헤더 상단 주석에 규약 각인 1줄을 추가한다: `# DL-CONTRACT (085): 릴리즈 태그는 릴리즈 자산 우선 + sha256sums.txt 부재 시 자동 아카이브 폴백(UNVERIFIED) + strip 자동 판정`

#### D-G. `release.yml --prefix` 추가 여부 판단 (TASK 미확정 항목 해소)

**결론: 추가하지 않는다.**

근거:
- 이미 발행된 v0.6.7~v0.6.11 자산이 전부 prefix 없음이므로, `--prefix`를 추가해도 **기존 릴리즈 호환 분기(D-D)는 여전히 필수**다 (→ D-9 §A-4).
- 분기가 유지되는 이상 `--prefix` 추가는 이득 없이 발행 자산 해시를 바꾸고 재릴리즈를 유발한다.
- `[MUST]` `` `tasks/085-260807-opds-릴리즈-체크섬-검증경로-정합/TASK.md` §범위 ``: "**제외**: 재릴리즈(태그 발행)·`release.yml` 아카이브 형식 변경·main 브랜치 설치 경로 동작"

---

### F-001: `update.sh` 다운로드 대상 전환 + 체크섬 하드닝

#### 3.1.1 파일 변경 계획

**신규 생성**: 없음

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/opal-cli/lib/update.sh` | 공통 | 헤더 변경이력 v1.1 + DL-CONTRACT 각인 | (→ §3.0 D-F) |
| 2 | `opal/tools/opal-cli/lib/update.sh` | 공통 | `:99` 안내 문구 정정 (자동 아카이브 단정 제거) | `opal/tools/opal-cli/lib/update.sh:99` |
| 3 | `opal/tools/opal-cli/lib/update.sh` | 공통 | `:127-133` URL 결정 → `_dl_resolve_plan` 호출로 교체 | (→ §3.0 D-C) |
| 4 | `opal/tools/opal-cli/lib/update.sh` | 공통 | `:160-165` 로컬명·다운로드를 plan 기반으로 교체 + 폴백 1회 강등 | (→ §3.0 D-C) |
| 5 | `opal/tools/opal-cli/lib/update.sh` | 공통 | `:172-205` 체크섬을 `CHECKSUM_MODE` 분기로 재구성, 빈 기대값 하드 실패 | `opal/tools/opal-cli/lib/update.sh:182` (H-10) |
| 6 | `opal/tools/opal-cli/lib/update.sh` | 공통 | `:179` `sha256sum` 하드 호출 → `_dl_sha256` 헬퍼 | (→ §3.0 D-C, H-6) |
| 7 | `opal/tools/opal-cli/lib/update.sh` | 공통 | `:207-213` 추출을 `_dl_detect_strip` 기반 분기 + 사후조건 검사 | (→ §3.0 D-D) |

#### 3.1.2 함수 설계

신규 헬퍼 4종을 `cmd_update` 위에 정의한다 (파일 내 지역, export 하지 않음).

```bash
# sha256 해시 계산 — 도구 이식성 흡수. 실패 시 공백 반환(호출자가 하드 실패 처리).
_dl_sha256() {
    if command -v sha256sum >/dev/null 2>&1; then
        sha256sum "$1" | awk '{print $1}'
    elif command -v shasum >/dev/null 2>&1; then
        shasum -a 256 "$1" | awk '{print $1}'
    else
        return 1
    fi
}

# sha256sums.txt에서 첫 .tar.gz 파일명 컬럼을 파생 (binary mode '*' 접두 제거)
_dl_asset_name() {
    awk '{ n = $2; sub(/^\*/, "", n); if (n ~ /\.tar\.gz$/) { print n; exit } }' "$1"
}

# tar 최상위 구조 판정 → 0 | 1   (§3.0 D-D)
_dl_detect_strip() { ... }   # §3.0 D-D bash 구현 그대로

# 다운로드 계획 수립 — 전역 3종을 설정한다
#   _DL_URL / _DL_NAME / _DL_MODE (verify|unverified|branch)
_dl_resolve_plan() { ... }   # §3.0 D-C 의사코드 구현
```

`[MUST]` `` `opal/tools/opal-cli/run.sh:24` ``: `set -euo pipefail` — `_dl_sha256`처럼 실패를 반환하는 헬퍼는 반드시 `|| true` 또는 `if ! ...` 형태로 호출해 조기 종료를 유발하지 않게 한다 (→ D-1).

**체크섬 분기 재구성 (`:172-205` 대체)**

```bash
case "$_DL_MODE" in
    verify)
        info "체크섬 검증 중..."
        local expected actual entry
        entry="$(grep -F -- "$_DL_NAME" "$sha_file" || true)"
        [[ -z "$entry" ]] && { error "sha256sums.txt에 ${_DL_NAME} 항목 없음 — DL-CONTRACT 위반"; return 1; }
        expected="$(printf '%s\n' "$entry" | awk '{print $1}')"
        [[ -z "$expected" ]] && { error "체크섬 기대값 파싱 실패"; return 1; }
        actual="$(_dl_sha256 "$tarball_path" || true)"
        [[ -z "$actual" ]] && { error "sha256 계산 도구(sha256sum/shasum)를 찾을 수 없습니다."; return 1; }
        if [[ "$actual" != "$expected" ]]; then
            error "체크섬 불일치! 다운로드가 손상되었을 수 있습니다."
            error "  기대값: $expected"; error "  실제값: $actual"; return 1
        fi
        success "체크섬 검증 완료"
        ;;
    unverified)  # 기존 :190-204 3분기 그대로 이식
        ... ;;
    branch)      # 기존 :168-170 배너 (호출 위치 유지)
        ... ;;
esac
```

`[MUST]` `grep -F` (고정 문자열)를 사용한다 — 파일명의 `.`이 정규식 와일드카드로 해석되는 결함을 원천 차단한다 (→ D-9 §A-3 실측).

**추출부 재구성 (`:207-213` 대체)**

```bash
local strip_n
strip_n="$(_dl_detect_strip "$tarball_path")"
info "압축 해제 중... (strip-components=${strip_n})"
if [[ "$strip_n" -eq 1 ]]; then
    tar -xzf "$tarball_path" -C "$extract_dir" --strip-components=1
else
    tar -xzf "$tarball_path" -C "$extract_dir"
fi
# [MUST] 사후조건 — 조용한 진행 금지
if [[ ! -f "$extract_dir/VERSION" || ! -d "$extract_dir/opal" ]]; then
    error "추출 결과 구조 이상 — VERSION 또는 opal/ 이 루트에 없습니다 (strip=${strip_n})"
    return 1
fi
success "압축 해제 완료"
```

#### 3.1.3 환경 변경

해당 없음 (추가 패키지·설정 없음).

#### 3.1.4 배치/마이그레이션

해당 없음. `~/.opal/`에 배포하려면 `./scripts/install-mac.sh` 재실행이 필요하다 —
`[MUST]` `` `.opal/AGENT.md` §금지사항 ``: "`~/.opal/` 직접 편집 금지 — 항상 프로젝트 소스를 수정한 후 install로 배포한다." (→ D-8, D-10 §배포 경계)

#### 3.1.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | F-1 AC | 기능 테스트 | v0.6.11 태그로 `opal-cli update --to v0.6.11 --force` 실행 시 "체크섬 검증 완료" 출력 후 설치 완료 |
| TS-002 | F-1 AC | 산출물 검사 | `update.sh`의 릴리즈 태그 경로에서 `archive/refs/tags` 사용이 폴백 분기 외 **0건** |
| TS-003 | H-10 | 보안 테스트 | sha256sums.txt를 항목 없는 파일로 대체 시 **하드 실패**(무음 통과 없음) |

---

### F-002: `install.sh` 다운로드 대상 전환 + 매칭 정정

#### 3.2.1 파일 변경 계획

**신규 생성**: 없음

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `scripts/install.sh` | 공통 | 헤더 변경이력 v1.6 + DL-CONTRACT 각인 | (→ §3.0 D-F) |
| 2 | `scripts/install.sh` | 공통 | `:111-121` URL 상수 블록 → `resolve_download_plan()` 함수로 이동 | (→ §3.0 D-C) |
| 3 | `scripts/install.sh` | 공통 | `OPAL_TMP` 생성을 `fetch_tarball`(`:179`)에서 `prepare_tmp()`로 분리 | §2.2.3 (sha 선다운로드 필요) |
| 4 | `scripts/install.sh` | 공통 | `:180` 로컬명 `opal.tar.gz` → `${OPAL_TARBALL_NAME}` | `scripts/install.sh:180` (H-4) |
| 5 | `scripts/install.sh` | 공통 | `:254-263` grep 매칭 → `grep -F` + 미매칭 **하드 실패** | `scripts/install.sh:258` (H-9) |
| 6 | `scripts/install.sh` | 공통 | `:210-279` `verify_checksum`을 `OPAL_CHECKSUM_MODE` 분기로 재구성 | (→ §3.0 D-C) |
| 7 | `scripts/install.sh` | 공통 | `:283-299` `extract_to_tmp` strip 자동 판정 + 사후조건 | (→ §3.0 D-D) |
| 8 | `scripts/install.sh` | 공통 | `:362-381` `main()` 호출 순서에 `prepare_tmp`·`resolve_download_plan` 삽입 | §2.2.3 |

#### 3.2.2 함수 설계

**신규/변경 시그니처**

```bash
prepare_tmp()            # OPAL_TMP 생성 (mktemp -d). trap cleanup EXIT는 기존 :127-132 유지
resolve_download_plan()  # 산출 전역: TARBALL_URL / OPAL_TARBALL_NAME / OPAL_CHECKSUM_MODE / OPAL_SHA_FILE
_dl_detect_strip <tarball> -> 0|1     # §3.0 D-D bash 구현 (update.sh와 동일 본문)
_dl_asset_name  <sha_file> -> name    # §3.0 D-C 파생 (update.sh와 동일 본문)
fetch_tarball()          # OPAL_TARBALL="${OPAL_TMP}/${OPAL_TARBALL_NAME}" 로 다운로드 + 폴백 1회 강등
verify_checksum()        # OPAL_CHECKSUM_MODE 분기
extract_to_tmp()         # strip 자동 판정 + 사후조건
```

**`main()` 새 호출 순서**

```bash
main() {
    info "OPAL 설치 시작 (repo: ${OPAL_REPO}, version: ${OPAL_VERSION})"
    ...
    detect_platform            # verify_checksum의 shasum/sha256sum 분기 전제 — 순서 유지
    check_deps
    prepare_tmp                # 신규 (구 fetch_tarball 내부 :179)
    resolve_download_plan      # 신규 — sha256sums.txt 선조회 + 소스 확정
    fetch_tarball
    verify_checksum
    extract_to_tmp
    adopt_stamped_version
    exec_platform_installer "$@"
}
```

- main 브랜치 UNVERIFIED 배너(`:369-372`)는 **현 위치 그대로 유지**한다 (RG-3).
- `[MUST]` `resolve_download_plan`은 `[[ "${OPAL_DRY_RUN}" == "1" ]]`이면 branch 계획으로 조기 반환한다 (RG-7).

**`verify_checksum` 재구성**

```bash
verify_checksum() {
    [[ "${OPAL_DRY_RUN}" == "1" ]] && { warn "[DRY-RUN] verify_checksum 생략"; return 0; }

    case "${OPAL_CHECKSUM_MODE}" in
        verify)
            local entry
            entry="$(grep -F -- "${OPAL_TARBALL_NAME}" "${OPAL_SHA_FILE}" || true)"
            # [MUST] 무음 스킵 금지 — 항목 부재는 규약 위반이므로 설치를 거부한다
            [[ -z "${entry}" ]] && error "sha256sums.txt에 ${OPAL_TARBALL_NAME} 항목 없음 — 설치를 중단합니다."
            info "SHA-256 검증 중..."
            if [[ "${OPAL_PLATFORM}" == "macos" ]]; then
                (cd "${OPAL_TMP}" && shasum -a 256 -c "${OPAL_SHA_FILE}" --ignore-missing) \
                    || error "SHA-256 체크섬 검증 실패 — 다운로드가 손상되었을 수 있습니다."
            else
                (cd "${OPAL_TMP}" && sha256sum -c "${OPAL_SHA_FILE}" --ignore-missing) \
                    || error "SHA-256 체크섬 검증 실패 — 다운로드가 손상되었을 수 있습니다."
            fi
            success "SHA-256 체크섬 검증 완료"
            ;;
        unverified)   # 기존 :232-247 3분기 그대로 이식 (옵트인 / 비대화형 거부 / 프롬프트)
            ... ;;
        branch)
            warn "sha256sums.txt 없음 (브랜치 설치) — 체크섬 검증 건너뜀" ;;
    esac
}
```

- 실측 확인: macOS `shasum -a 256 -c <file> --ignore-missing`은 지원되며, 대상 파일이 하나도 없으면 `no file was verified`로 exit 1을 반환한다 → **2중 안전망**(grep 선검사 + shasum 자체 실패).
- `2>/dev/null` 억제는 제거한다 — 실패 사유를 사용자에게 보여야 한다 (현행 `:269,273`).

**`extract_to_tmp` 재구성**

```bash
extract_to_tmp() {
    [[ "${OPAL_DRY_RUN}" == "1" ]] && { warn "[DRY-RUN] extract_to_tmp 생략"; OPAL_EXTRACT_DIR="${OPAL_TMP}/opal-extracted"; mkdir -p "${OPAL_EXTRACT_DIR}"; return 0; }
    OPAL_EXTRACT_DIR="${OPAL_TMP}/opal-extracted"
    mkdir -p "${OPAL_EXTRACT_DIR}"
    local strip_n; strip_n="$(_dl_detect_strip "${OPAL_TARBALL}")"
    info "tarball 추출 중... (strip-components=${strip_n})"
    if [[ "${strip_n}" -eq 1 ]]; then
        tar -xzf "${OPAL_TARBALL}" -C "${OPAL_EXTRACT_DIR}" --strip-components=1 || error "tarball 추출 실패"
    else
        tar -xzf "${OPAL_TARBALL}" -C "${OPAL_EXTRACT_DIR}" || error "tarball 추출 실패"
    fi
    # [MUST] 사후조건
    [[ -f "${OPAL_EXTRACT_DIR}/VERSION" && -d "${OPAL_EXTRACT_DIR}/opal" ]] \
        || error "추출 결과 구조 이상 — VERSION 또는 opal/ 이 루트에 없습니다 (strip=${strip_n})"
    success "추출 완료: ${OPAL_EXTRACT_DIR}"
}
```

#### 3.2.3 환경 변경

해당 없음.

#### 3.2.4 배치/마이그레이션

해당 없음. `scripts/install.sh`는 배포 대상이 아니라 **원본이 곧 배포본**(raw.githubusercontent 직접 fetch)이므로, 변경은 main 병합 시점에 즉시 유효해진다 — 이 특성 자체가 리스크다 (§9 R-3).

#### 3.2.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-004 | F-2 AC | 기능 테스트 | `OPAL_VERSION=v0.6.11 bash scripts/install.sh` 실행 시 "SHA-256 체크섬 검증 완료" 출력 |
| TS-005 | F-2 AC | 보안 테스트 | 스킵 경고(`항목 없음 — 체크섬 검증 건너뜀`)가 **0건** |
| TS-006 | F-2 AC | 보안 테스트 | tarball을 의도적으로 손상시키면 설치가 **거부**(exit≠0) |
| TS-007 | H-4 | 회귀 테스트 | `OPAL_DRY_RUN=1 bash scripts/install.sh` 흐름 검증 통과 + 네트워크 접근 0 |

---

### F-003: `install.ps1` 다운로드 대상 전환

#### 3.3.1 파일 변경 계획

**신규 생성**: 없음

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `scripts/install.ps1` | 공통 | `# 변경이력` 블록 v1.1 + DL-CONTRACT 각인 | (→ §3.0 D-F) |
| 2 | `scripts/install.ps1` | 공통 | `:94-102` URL 상수 → `Resolve-DownloadPlan` 함수로 이동 | (→ §3.0 D-C) |
| 3 | `scripts/install.ps1` | 공통 | `:129-162` `Fetch-Tarball`이 plan의 `Name`/`Url` 소비 + 폴백 1회 강등 | (→ §3.0 D-C) |
| 4 | `scripts/install.ps1` | 공통 | `:164-232` `Verify-Checksum`을 `$script:DlMode` 분기로 재구성, 항목 부재 → `throw` | `scripts/install.ps1:220-223` |
| 5 | `scripts/install.ps1` | 공통 | `:252-270` 추출 시 `Get-DlStripComponents` 기반 조건부 인자 | (→ §3.0 D-D) |
| 6 | `scripts/install.ps1` | 공통 | `:334-337` `Invoke-OpalInstall` 호출 순서에 `Resolve-DownloadPlan` 삽입 | §3.0 D-C |

#### 3.3.2 함수 설계

```powershell
# 산출 (script scope): $script:DlUrl / $script:DlName / $script:DlMode / $script:DlShaFile
function Resolve-DownloadPlan {
    param([Parameter(Mandatory)][string] $DestDir)
    if ($DryRun) { $script:DlUrl = "..."; $script:DlName = "opal-$script:OpalVersion.tar.gz"; $script:DlMode = 'branch'; return }
    if ($script:OpalVersion -notlike 'v*') { ... $script:DlMode = 'branch'; return }
    $shaUrl  = "https://github.com/$OpalRepo/releases/download/$script:OpalVersion/sha256sums.txt"
    $shaFile = Join-Path $DestDir 'sha256sums.txt'
    try { Invoke-RestMethod -Uri $shaUrl -OutFile $shaFile -ErrorAction Stop }
    catch { Set-DlFallback -Reason '릴리즈 자산 없음'; return }
    $asset = Get-DlAssetName -ShaFile $shaFile
    if (-not $asset) { Set-DlFallback -Reason 'sha256sums.txt 형식 이상'; return }
    $script:DlUrl = "https://github.com/$OpalRepo/releases/download/$script:OpalVersion/$asset"
    $script:DlName = $asset          # [MUST] 로컬명 = 발행 자산명
    $script:DlShaFile = $shaFile
    $script:DlMode = 'verify'
}

function Set-DlFallback {
    param([Parameter(Mandatory)][string] $Reason)
    $script:DlUrl  = "https://github.com/$OpalRepo/archive/refs/tags/$script:OpalVersion.tar.gz"
    $script:DlName = "opal-$script:OpalVersion-archive.tar.gz"
    $script:DlMode = 'unverified'
    # [MUST] H-3 — 폴백 시 sha256sums.txt 를 비교에 사용하지 않는다
    if ($script:DlShaFile -and (Test-Path $script:DlShaFile)) { Remove-Item -LiteralPath $script:DlShaFile -Force -ErrorAction SilentlyContinue }
    $script:DlShaFile = $null
    Write-Warning "[OPAL] 릴리즈 자산 미사용 폴백: $Reason"
}

function Get-DlAssetName { param([string] $ShaFile)
    foreach ($line in (Get-Content -LiteralPath $ShaFile)) {
        $cols = @($line -split '\s+' | Where-Object { $_ })
        if ($cols.Count -ge 2) { $n = $cols[1] -replace '^\*',''; if ($n -like '*.tar.gz') { return $n } }
    }
    return $null
}

function Get-DlStripComponents { ... }   # §3.0 D-D PowerShell 구현 그대로
```

**추출 인자 조건부 구성 (`:260-261` 대체)** — `[MUST]` PowerShell에서 조건부 CLI 인자는 **배열 splatting**으로 구성한다. 문자열 보간으로 조립하면 빈 인자가 tar에 전달되어 실패한다 (H-7).

```powershell
$strip    = Get-DlStripComponents -TarballPath $TarballPath
$tarArgs  = @('-xzf', $TarballPath, '-C', $extractDir)
if ($strip -eq 1) { $tarArgs += @('--strip-components', '1') }
$tarArgs += @('--exclude=tasks/*', '--exclude=*/tasks/*', '--exclude=tasks', '--exclude=*/tasks')
Write-Host "[OPAL] tarball 압축 해제 중... (strip-components=$strip)" -ForegroundColor Cyan
& tar @tarArgs
```

- 기존 `$LASTEXITCODE -ne 0` 관용 처리(`:262-270`)는 유지하되, 관용 조건을 **사후조건으로 승격**한다:

```powershell
# [MUST] 사후조건 — VERSION 과 opal/ 이 모두 루트에 있어야 한다
$okVersion = Test-Path ([IO.Path]::Combine($extractDir, 'VERSION'))
$okOpal    = Test-Path ([IO.Path]::Combine($extractDir, 'opal'))
if (-not ($okVersion -and $okOpal)) {
    throw "[OPAL] 추출 결과 구조 이상 — VERSION 또는 opal/ 이 루트에 없습니다 (strip=$strip, tar exit=$LASTEXITCODE)"
}
```

**`Verify-Checksum` 분기** — `verify` 모드에서 항목 부재는 `Write-Warning; return`(`:220-223`)이 아니라 `throw`로 승격한다. `unverified`·`branch` 모드는 기존 `:190-211` 코드를 그대로 이식한다.

#### 3.3.3 환경 변경

해당 없음.

#### 3.3.4 배치/마이그레이션

해당 없음.

#### 3.3.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-008 | F-3 AC | 기능 테스트 | Windows에서 `$env:OPAL_VERSION='v0.6.11'` 설치 시 "체크섬 검증 통과" 출력 후 설치 완료 |
| TS-009 | F-3 AC | 산출물 검사 | Windows 실행 불가 시 — PowerShell 구문 검사(`[ScriptBlock]::Create`)와 규약 대조로 대체하고 사유 기록 |
| TS-010 | H-7 | 기능 테스트 | strip=0/1 두 형식 추출 후 `VERSION`·`opal/`이 루트에 존재 |

---

### F-004: 릴리즈 자산 부재 시 폴백 + UNVERIFIED 정책 유지

#### 3.4.1 파일 변경 계획

**신규 생성**: 없음

**수정** — F-001 #4·#5, F-002 #2·#6, F-003 #2·#3·#4에 포함 (횡단 구현).

#### 3.4.2 설계

`[MUST]` 폴백 진입 시 다음 3가지를 **동시에** 수행한다 (하나라도 누락하면 H-3 재발):
1. URL을 `archive/refs/tags/{tag}.tar.gz`로 재지정
2. 로컬 파일명을 `opal-{tag}-archive.tar.gz`로 재지정 (발행 자산명과 **의도적으로 다르게** 하여 우발적 매칭을 차단)
3. 이미 받은 `sha256sums.txt`를 **삭제하고 참조 변수를 비운다**

`[MUST]` 폴백 후 체크섬 정책은 기존 R-2·GC-001 3분기를 그대로 사용한다 —
`` `scripts/install.sh:239-241` ``: "비대화형 모드 (stdin pipe 또는 OPAL_AUTO_INSTALL=1): 기본 거부"
`` `docs/... TASK.md §제약 조건` ``: "무결성 검증을 우회하는 방향의 해소(예: 체크섬 비교 삭제, 조건부 스킵 확대)는 채택하지 않는다 — R-2·GC-001 의도 유지." (→ D-9)

**폴백 사유별 로그 문구 (3경로 동일)**

| 사유 | 문구 |
|------|------|
| sha256sums.txt 404 | `릴리즈 자산 미사용 폴백: 릴리즈 자산 없음` |
| sha256sums.txt 파싱 실패 | `릴리즈 자산 미사용 폴백: sha256sums.txt 형식 이상` |
| 자산 다운로드 실패 | `릴리즈 자산 미사용 폴백: 릴리즈 자산 다운로드 실패` |

#### 3.4.3 환경 변경

해당 없음. 기존 환경 변수 계약 유지: `OPAL_ALLOW_UNVERIFIED`, `OPAL_AUTO_INSTALL`, `OPAL_DRY_RUN`, `OPAL_VERSION`, `OPAL_REPO`.

#### 3.4.4 배치/마이그레이션

해당 없음.

#### 3.4.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-011 | F-4 AC | 기능 테스트 | 릴리즈 자산 없는 태그(또는 sha URL 차단) + `OPAL_ALLOW_UNVERIFIED=1` → 설치 **중단되지 않고** 자동 아카이브로 완료 |
| TS-012 | F-4 AC / H-8 | 보안 테스트 | 동일 조건 + 옵트인 미지정 + 비대화형(`\| bash`) → **거부**(exit≠0) |
| TS-013 | H-3 | 보안 테스트 | 폴백 경로 로그에 체크섬 **불일치** 오류가 나타나지 않는다 (비교 자체가 수행되지 않음) |

---

### F-005: 추출 구조 분기

#### 3.5.1 파일 변경 계획

**신규 생성**: 없음

**수정** — F-001 #7, F-002 #7, F-003 #5에 포함 (횡단 구현).

#### 3.5.2 설계

§3.0 D-D의 판정 규칙·bash/PowerShell 구현·사후조건을 3경로에 동형 적용한다.

`[MUST]` `update.sh:211-212`의 `tar ... --strip-components=1 2>/dev/null || tar ...` 관용 폴백을 **삭제**한다 — prefix 없는 아카이브에서 첫 tar가 exit 0으로 성공하므로 폴백이 발동하지 않고 루트 파일이 소리 없이 소실된다 (→ §2.5.2 실측).

#### 3.5.3 환경 변경

해당 없음. 추가 도구 없음 (`tar`는 기존 `check_deps`가 이미 확인 — `scripts/install.sh:160`).

#### 3.5.4 배치/마이그레이션

해당 없음.

#### 3.5.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-014 | F-5 AC | 기능 테스트 | 발행 자산(prefix 없음) 추출 후 루트에 `VERSION`·`opal/` 존재, `VERSION` = `v0.6.11` |
| TS-015 | F-5 AC | 기능 테스트 | 자동 아카이브(prefix `opal-0.6.11/`) 추출 후 동일 결과 |
| TS-016 | H-5 / RG-2 | 회귀 테스트 | main 아카이브(prefix `opal-main/`) 추출 후 동일 구조 — 기존 동작 무변경 |

---

### F-006: 3경로 × 3조합 실측 검증

#### 3.6.1 파일 변경 계획

**신규 생성**

| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `tasks/085-260807-opds-릴리즈-체크섬-검증경로-정합/TEST.md` | 공통 | 3경로 × 3조합 실행 증거 기록 | (→ D-9 §F-6 AC) |

> `TEST-SCENARIO.md`는 PM+소유자가 별도 작성한다 (self-confirming 방지 — op-dev-plan SKILL.md §입력/출력 "제외 출력").

#### 3.6.2 설계 — 검증 매트릭스 (9칸)

| 경로 \ 조합 | 릴리즈 태그 (verify) | 자산 부재 폴백 (unverified) | main 브랜치 (branch) |
|------------|---------------------|--------------------------|---------------------|
| `install.sh` | TS-004·TS-005·TS-006 | TS-011·TS-012·TS-013 | TS-016 |
| `install.ps1` | TS-008 | TS-011 (Windows) | TS-016 (Windows) |
| `update.sh` | TS-001·TS-002·TS-003 | TS-011 | TS-016 |

**자산 부재 시뮬레이션 방법** (재릴리즈 없이 수행):
- `OPAL_REPO`를 릴리즈 자산이 없는 포크/태그로 지정, 또는
- `/etc/hosts`·프록시로 `objects.githubusercontent.com` 차단하여 sha256sums.txt 다운로드만 실패시킴, 또는
- `OPAL_VERSION`을 릴리즈 자산이 없는 과거 태그(v0.6.6 이하)로 지정 — **실행 전 실제 자산 유무를 확인**할 것.

**Windows 대체 검증 (실행 불가 시)**:
1. `[ScriptBlock]::Create((Get-Content -Raw scripts/install.ps1))` 구문 파싱 통과 (pwsh 설치 시)
2. `Get-DlStripComponents`·`Get-DlAssetName` 단위 호출로 3형식 판정값(0/1/1)·자산명 파생 확인
3. §3.0 규약 항목별 bash↔PowerShell 대조표를 증거로 첨부
4. **사유를 TEST.md에 명시** (→ D-9 §F-6 AC: "Windows 실행이 불가한 환경이면 그 사유와 대체 검증 방법을 명시한다")

#### 3.6.3 환경 변경

해당 없음 (검증용 임시 네트워크 차단은 검증 후 원복).

#### 3.6.4 배치/마이그레이션

`update.sh` 검증 전 `./scripts/install-mac.sh` 재배포가 선행되어야 한다 (`~/.opal/tools/opal-cli/lib/update.sh`가 실제 실행 대상).

#### 3.6.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-017 | F-6 AC | 산출물 검사 | TEST.md에 9칸 매트릭스 전부의 실행 명령어·출력·판정이 기록되고, 미실행 칸은 사유+대체 검증이 기재됨 |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)

| Phase | 기능 | Step | agent | 실행 | 비고 |
|-------|------|------|-------|------|------|
| 1 | F-001·F-004·F-005 / F-003·F-004·F-005 | 1, 2 | opal-task-agent | **병렬** | 독립 파일·독립 언어 (bash / PowerShell) |
| 2 | F-002·F-004·F-005 | 3 | opal-task-agent | 순차 | Step 1의 bash 헬퍼를 동일 본문으로 이식 |
| 3 | F-001~F-005 (S-5) | 4 | opal-task-agent | 순차 | 3경로 규약 드리프트 정적 대조 |
| 4 | F-006 | 5 | opal-test-agent | 순차 | 재배포 후 9칸 실측 |
| 5 | 문서 | 6 | PM 직접 | 순차 | `docs/ARCHITECTURE.md` §배포 채널 갱신 |

### 4.2 실행 체크리스트

> 총 6개 Step | Phase 5개 | 실행 모드: **복잡**

#### Step 1: `update.sh` 다운로드 규약 적용 (bash 기준 구현)

- [x] 완료
- **소속 기능**: F-001, F-004, F-005
- **영역**: 공통
- **agent**: opal-task-agent
- **파일**: `opal/tools/opal-cli/lib/update.sh`
- **작업 내용**:
  1. 헤더에 `v1.1` 변경이력 행 + `DL-CONTRACT (085)` 각인 1줄 추가 (§3.0 D-F)
  2. 헬퍼 4종 정의: `_dl_sha256` / `_dl_asset_name` / `_dl_detect_strip` / `_dl_resolve_plan` (§3.1.2)
  3. `:127-133` URL 결정부를 `_dl_resolve_plan` 호출로 교체, `--dry-run` 조기 반환 유지 (RG-8)
  4. `:160-165` 다운로드를 `$_DL_NAME` 기반으로 교체 + 실패 시 폴백 1회 강등
  5. `:172-205` 체크섬을 `verify` / `unverified` / `branch` 3분기로 재구성 — `grep -F`, 빈 기대값·항목 부재·해시 도구 부재 전부 **하드 실패**
  6. `:207-213` 추출을 `_dl_detect_strip` 분기 + `VERSION`·`opal/` 사후조건으로 교체
  7. `:99` 안내 문구를 "release 자산 없음 — archive tarball 사용" → 규약 중립 문구로 정정
- **완료 기준**:
  - `bash -n opal/tools/opal-cli/lib/update.sh` 통과
  - `shellcheck` 실행 시 신규 error 레벨 0건 (설치되어 있는 경우)
  - 릴리즈 태그 경로에서 `archive/refs/tags` 문자열이 **폴백 분기 내부에만** 존재
  - `--strip-components=1 ... || tar ...` 관용 폴백 잔존 0건
- **테스트**: TS-001, TS-002, TS-003, TS-014, TS-015
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 2: `install.ps1` 다운로드 규약 적용 (PowerShell)

- [x] 완료
- **소속 기능**: F-003, F-004, F-005
- **영역**: 공통
- **agent**: opal-task-agent
- **파일**: `scripts/install.ps1`
- **작업 내용**:
  1. `# 변경이력` 블록(`:35-48`)에 `v1.1` 행 + `DL-CONTRACT (085)` 각인 추가 (`.NOTES` 블록은 미변경)
  2. `Resolve-DownloadPlan` / `Set-DlFallback` / `Get-DlAssetName` / `Get-DlStripComponents` 신규 정의 (§3.3.2)
  3. `:94-102` 모듈 스코프 URL 상수 제거 → plan 함수로 이동, DRY-RUN 조기 반환
  4. `Fetch-Tarball`(`:129-162`)이 `$script:DlName`·`$script:DlUrl` 소비 + 실패 시 폴백 1회 강등
  5. `Verify-Checksum`(`:164-232`)을 `$script:DlMode` 3분기로 재구성 — `verify`에서 항목 부재는 `throw`로 승격
  6. `Invoke-PlatformInstaller` 추출부(`:252-270`)를 배열 splatting 조건부 인자 + 사후조건으로 교체 (`--exclude` 4종 유지)
  7. `Invoke-OpalInstall`(`:334-337`)에 `Resolve-DownloadPlan -DestDir $tmpDir` 삽입
- **완료 기준**:
  - PowerShell 구문 파싱 통과 (`pwsh -NoProfile -Command "[ScriptBlock]::Create((Get-Content -Raw ./scripts/install.ps1)) | Out-Null"`) — pwsh 미설치 시 사유 기록
  - 릴리즈 태그 경로에서 `archive/refs/tags` 사용이 `Set-DlFallback` 내부에만 존재
  - `--strip-components` 고정 인자 잔존 0건
- **테스트**: TS-008, TS-009, TS-010
- **실행 방법**: sub-agent
- **의존**: 없음 (Step 1과 **병렬**)

#### Step 3: `install.sh` 다운로드 규약 적용 + 매칭 정정

- [x] 완료
- **소속 기능**: F-002, F-004, F-005
- **영역**: 공통
- **agent**: opal-task-agent
- **파일**: `scripts/install.sh`
- **작업 내용**:
  1. 헤더 `변경이력`(`:32-41`)에 `v1.6` 행 + `DL-CONTRACT (085)` 각인 추가
  2. Step 1에서 확정한 `_dl_asset_name` / `_dl_detect_strip` 본문을 **문자 단위 동일**하게 이식 (§3.0 D-A 정합 수단 a)
  3. `prepare_tmp()` 신규 — `OPAL_TMP` 생성을 `fetch_tarball:179`에서 분리
  4. `resolve_download_plan()` 신규 — `:111-121` 모듈 스코프 URL 상수 블록 대체, DRY-RUN 조기 반환 (RG-7)
  5. `fetch_tarball`을 `${OPAL_TMP}/${OPAL_TARBALL_NAME}` 기반으로 교체 + 폴백 1회 강등
  6. `verify_checksum`을 `OPAL_CHECKSUM_MODE` 3분기로 재구성 — `grep -F`, 항목 부재 **하드 실패**, `2>/dev/null` 억제 제거
  7. `extract_to_tmp` strip 자동 판정 + 사후조건
  8. `main()` 호출 순서에 `prepare_tmp` → `resolve_download_plan` 삽입 (§3.2.2)
- **완료 기준**:
  - `bash -n scripts/install.sh` 통과
  - `opal.tar.gz` 리터럴 잔존 0건
  - `grep "${tarball_name}"` 형태의 비고정문자열 매칭 잔존 0건
  - `OPAL_DRY_RUN=1 bash scripts/install.sh`가 네트워크 접근 없이 `[DRY-RUN] 흐름 검증 완료` 출력
  - main 브랜치 배너(`:369-372`) 위치·문구 무변경
- **테스트**: TS-004, TS-005, TS-006, TS-007, TS-016
- **실행 방법**: sub-agent
- **의존**: Step 1

#### Step 4: 3경로 규약 정합 정적 대조 (S-5)

- [x] 완료
- **소속 기능**: F-001, F-002, F-003, F-004, F-005
- **영역**: 공통
- **agent**: opal-task-agent
- **파일**: `opal/tools/opal-cli/lib/update.sh`, `scripts/install.sh`, `scripts/install.ps1`
- **작업 내용**:
  1. 규약 항목 8종(자산 존재 판정 신호 / 자산명 파생 / 로컬명 = 자산명 / 폴백 3동작 / 폴백 로그 문구 / 체크섬 3모드 / strip 판정식 / 사후조건)을 3경로 대조표로 작성
  2. 정적 검사 실행:
     - `grep -rn "archive/refs/tags" scripts/install.sh scripts/install.ps1 opal/tools/opal-cli/lib/update.sh` → 각 파일에서 **폴백 분기 1회씩만** 등장
     - `grep -rn "opal.tar.gz" scripts/install.sh` → 0건
     - `grep -rn "strip-components" ...` → 조건부 분기 내부에만 등장
     - 3파일 헤더에 `DL-CONTRACT (085)` 각인 존재
  3. 불일치 발견 시 해당 Step으로 되돌려 수정
- **완료 기준**: 대조표 8행 전부 "일치" 판정, 정적 검사 4종 전부 기대값
- **테스트**: TS-002, TS-005, TS-009
- **실행 방법**: sub-agent
- **의존**: Step 1, Step 2, Step 3

#### Step 5: 3경로 × 3조합 실측 검증 + TEST.md 작성

- [x] 완료
- **소속 기능**: F-006
- **영역**: 공통
- **agent**: opal-test-agent
- **파일**: `tasks/085-260807-opds-릴리즈-체크섬-검증경로-정합/TEST.md`
- **작업 내용**:
  1. `./scripts/install-mac.sh` 재실행으로 `~/.opal/tools/opal-cli/lib/update.sh` 재배포 (§3.6.4)
  2. §3.6.2 9칸 매트릭스 실행 — 각 칸의 명령어·표준출력·exit code 기록
  3. 손상 tarball 거부(TS-006)·비대화형 거부(TS-012) 보안 시나리오 포함
  4. Windows 미실행 칸은 사유 + 대체 검증 3종 결과 기재
- **완료 기준**: 9칸 전부 기대 동작 일치(또는 사유+대체 검증 기재), 실행 증거가 재현 가능한 형태로 기록
- **테스트**: TS-001·TS-004·TS-006·TS-008·TS-011·TS-012·TS-013·TS-014·TS-015·TS-016·TS-017
- **실행 방법**: sub-agent
- **의존**: Step 4

#### Step 6: `docs/ARCHITECTURE.md` 배포 채널 규약 갱신

- [x] 완료
- **소속 기능**: F-001, F-002, F-003 (파생 문서)
- **영역**: 문서
- **agent**: PM 직접
- **파일**: `docs/ARCHITECTURE.md`
- **작업 내용**:
  1. `docs/ARCHITECTURE.md:325` `GitHub Releases` 행 비고에 소비 규약 추가 — "설치·업데이트는 릴리즈 자산(`opal-{tag}.tar.gz`)을 1순위로 소비하고, 자산 부재 시 자동 아카이브로 폴백(UNVERIFIED 정책 적용)"
  2. `:327` `One-liner installer` 행에 "다운로드 소스 규약은 `GitHub Releases` 행 참조" 1줄 추가
  3. `## 변경이력`에 태스크 085 행 추가
- **완료 기준**: 배포 채널 표가 코드의 실제 다운로드 소스와 일치, 변경이력 행 추가
- **테스트**: 문서 리뷰 (PM Gate)
- **의존**: Step 5

### 4.3 병렬/순차 판별 근거

| 관계 | 근거 |
|------|------|
| Step 1 ∥ Step 2 | 독립 파일 + 독립 언어(bash / PowerShell). 공유 편집 대상 없음 |
| Step 1 → Step 3 | 두 bash 파일이 `_dl_asset_name`·`_dl_detect_strip` **동일 본문**을 공유해야 함 — 기준 구현 확정 후 이식하여 드리프트 방지 (§3.0 D-A) |
| Step 2 → Step 4 | 대조 대상 3파일이 모두 확정되어야 규약 대조 가능 |
| Step 3 → Step 4 | 동일 |
| Step 4 → Step 5 | 정적 드리프트가 남은 상태로 실측하면 9칸 결과 해석이 오염됨 |
| Step 5 → Step 6 | 실측으로 확정된 동작만 문서에 기술 (추정 기재 금지 — `citation-rules.md` §0) |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA

| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | `opal-cli update`가 릴리즈 자산을 받아 체크섬 검증 통과 | TS-001 | "체크섬 검증 완료" 출력 + 설치 완료 (exit 0) |
| F-001 | 릴리즈 태그 경로에 자동 아카이브 URL 0건 | TS-002 | `archive/refs/tags`가 폴백 분기에만 존재 |
| F-001 | 빈 기대값 무음 통과 제거 | TS-003 | 항목 없는 sha 파일 주입 시 exit≠0 |
| F-002 | `install.sh` 체크섬 검증 실제 수행 | TS-004 | "SHA-256 체크섬 검증 완료" 출력 |
| F-002 | 무음 스킵 소멸 | TS-005 | 스킵 경고 0건 |
| F-002 | 손상 tarball 거부 | TS-006 | exit≠0 + 설치 미수행 |
| F-003 | `install.ps1` 릴리즈 태그 설치 완료 | TS-008 | "체크섬 검증 통과" 출력 + 설치 완료 |
| F-003 | Windows 미실행 시 대체 검증 | TS-009 | 사유 + 구문검사 + 단위 판정 결과 기재 |
| F-004 | 자산 부재 시 무중단 폴백 | TS-011 | 설치가 중단되지 않고 자동 아카이브로 완료 |
| F-004 | 비대화형 거부 보존 | TS-012 | 옵트인 미지정 비대화형에서 exit≠0 |
| F-004 | 폴백 시 잘못된 비교 금지 | TS-013 | 폴백 로그에 체크섬 불일치 오류 부재 |
| F-005 | prefix 없는 자산 추출 | TS-014 | 루트에 `VERSION`·`opal/` 존재, `VERSION`=`v0.6.11` |
| F-005 | prefix 있는 아카이브 추출 | TS-015 | 동일 |
| F-006 | 9칸 실측 증거 완결성 | TS-017 | 9칸 전부 기록(미실행은 사유+대체) |

### 5.2 회귀 테스트

- [ ] main 브랜치 설치(`OPAL_VERSION=main`)가 기존과 동일하게 UNVERIFIED 배너 후 완료 (TS-016, RG-1·RG-3)
- [ ] main 아카이브 추출 시 `_dl_detect_strip`이 `1`을 반환 (RG-2)
- [ ] `OPAL_DRY_RUN=1 bash scripts/install.sh` 흐름 검증 통과 + 네트워크 접근 0 (TS-007, RG-7)
- [ ] `opal-cli update --dry-run`이 네트워크 접근 없이 URL 출력 후 종료 (RG-8)
- [ ] `install.ps1`의 `--exclude` 4종 인자 유지 (RG-6)
- [ ] `install.sh` `OPAL_TARBALL` 참조 4지점 전수 정합 (RG-5)
- [ ] 릴리즈 자산 부재 시 3분기(옵트인/프롬프트/거부) 동작 무변경 (RG-4)

### 5.3 코드/문서 품질

- [ ] `bash -n` 구문 검사 2파일 통과
- [ ] PowerShell 구문 파싱 통과 (또는 미설치 사유 기재)
- [ ] 3파일 헤더 변경이력 갱신 — 버전·KST 일시·태스크 번호 `(085)` 포함 (`docs/CONVENTIONS.md` §변경이력)
- [ ] 3파일 헤더에 `DL-CONTRACT (085)` 각인 존재
- [ ] `~/.opal/` 배포본 직접 편집 0건 — 프로젝트 소스만 수정 (`.opal/AGENT.md` §금지사항)
- [ ] 하드코딩된 플랫폼 분기 신규 추가 0건 — 기존 어댑터 계층(`detect_platform`·`exec_platform_installer`) 내부에서만 분기 (`docs/CONVENTIONS.md` §플랫폼 분기 격리)
- [ ] `release.yml`·`.gitattributes` 무변경 (→ §3.0 D-G)
- [ ] 커밋·태그·push 미수행 (`opal/core/references/opal-harness.md` §1 Guards)

### 5.4 보안

- [ ] `curl -fsSL --proto '=https' --tlsv1.2` 플래그가 **신규 추가된 모든 다운로드**(sha256sums.txt 선조회 포함)에 적용됨 (`scripts/install.sh:20-25` 보안 패턴)
- [ ] PowerShell TLS 1.2/1.3 강제(`scripts/install.ps1:153`)가 신규 다운로드 경로에도 적용됨
- [ ] 무결성 검증 우회 경로 신규 생성 0건 — `verify` 모드에서 skip/warn-continue 분기 부재
- [ ] 비대화형 기본 거부 정책 유지 (fail-closed)
- [ ] 임시 디렉토리 `mktemp -d` + `trap cleanup EXIT` 유지 (`scripts/install.sh:123-132`)
- [ ] 하드코딩된 토큰/시크릿 0건, `.env` 미도입

---

## 6. 복잡도 판별

| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 6개 | **복잡** (6개 이상) |
| 변경 파일 수 | 4개 (`update.sh`, `install.sh`, `install.ps1`, `ARCHITECTURE.md`) + 신규 1개 (`TEST.md`) | **복잡** (4개 이상) |
| 모듈 범위 | 다중 (opal-cli 도구 계층 + 설치 부트스트랩 2종 + 문서) | **복잡** |
| 작업 유형 | 오류 수정 (기능 추가 없음) | 단순 |
| 외부 의존성 | 없음 (기존 `curl`/`tar`/`shasum`만 사용) | 단순 |
| **실행 모드** | **복잡** | 5기준 중 3개 복잡 → 복잡 모드 적용 |

**에스컬레이션 판정**: 변경 파일 4개(<10)이며, 다단계 기술 의사결정 4건(자산 존재 판정 / 폴백 체크섬 정책 / strip 판정 / 코드 공유 가능성)은 **§3.0에서 실측 근거와 함께 전부 해소**되었다. `release.yml --prefix` 미확정 항목도 §3.0 D-G에서 "추가하지 않음"으로 판단 완료. → **에스컬레이션 불요**. 단, 재릴리즈(다음 패치 태그 발행)는 TASK 범위 밖이며 별도 소유자 승인이 필요하다 (→ D-9 §제약 조건).

---

## 7. 실행 아키텍처 (복잡 모드)

### C-1. 에이전트 토폴로지

```
Batch 1 (병렬)
  ├─ A1 [opal-task-agent] Step 1  opal/tools/opal-cli/lib/update.sh   (bash 기준 구현)
  └─ A2 [opal-task-agent] Step 2  scripts/install.ps1                 (PowerShell)

Batch 2
  └─ A3 [opal-task-agent] Step 3  scripts/install.sh                  (A1 헬퍼 이식)

Batch 3
  └─ A4 [opal-task-agent] Step 4  3파일 정적 규약 대조 (읽기 + 대조표)

Batch 4
  └─ A5 [opal-test-agent] Step 5  재배포 + 9칸 실측 → TEST.md

Batch 5
  └─ PM  Step 6  docs/ARCHITECTURE.md 갱신
```

**그룹핑 근거**:
- 파일 충돌 방지: 1 에이전트 = 1 파일 (A1/A2/A3 각각 단일 파일 소유)
- 모듈 응집도: bash 2파일은 헬퍼 본문을 공유하므로 A1 → A3 순차 (드리프트 차단)
- 병렬 극대화: A1 ∥ A2 (언어·파일 완전 독립)

### C-2. 스킬 요구사항

| 에이전트 | 스킬 | 갭 |
|---------|------|---|
| A1·A2·A3 | `op-dev-execute` (EXECUTE 단계 스킬) | 갭 없음 |
| A4 | 인라인 지침 (§4.2 Step 4 정적 검사 4종) | 스킬화 불요 — 1회성 |
| A5 | `opal-test-agent` (mode: BE/스크립트 실행 검증) | 갭 없음 |

### C-3. 도구 요구사항

| 도구 | 용도 | 확보 상태 |
|------|------|----------|
| `curl` | tarball·sha256sums.txt 다운로드 | 기존 `check_deps` 확인 (`scripts/install.sh:160`) |
| `tar` | 목록 조회(`-tzf`)·추출 | 동일 |
| `shasum` / `sha256sum` | SHA-256 계산·검증 | macOS `shasum` 기본, Linux `sha256sum` 기본 — `_dl_sha256`이 흡수 |
| `awk` | 자산명 파생·strip 판정 | POSIX 기본 |
| `bash -n` | 구문 검사 | 기본 |
| `shellcheck` | 정적 분석 (선택) | 미설치 시 스킵 |
| `pwsh` | PowerShell 구문 검사 (선택) | 미설치 시 사유 기록 |

신규 패키지 설치 **없음**.

### C-4. 테스트 전략

| 계층 | 대상 | 명령/방법 | 기대 |
|------|------|----------|------|
| L1 정적 | 3파일 | `bash -n`, `pwsh` 구문 파싱, `grep` 잔존 검사 4종 | 전부 통과, 잔존 0건 |
| L1 단위 | `_dl_detect_strip` | 3형식 tarball 입력 → 판정값 | `0` / `1` / `1` |
| L1 단위 | `_dl_asset_name` | 실제 `sha256sums.txt` 입력 | `opal-v0.6.11.tar.gz` |
| L2 통합 | `install.sh` | `OPAL_VERSION=v0.6.11 bash scripts/install.sh` | 검증 통과 + 설치 완료 |
| L2 통합 | `update.sh` | 재배포 후 `opal-cli update --to v0.6.11 --force` | 검증 통과 + 설치 완료 |
| L2 보안 | 손상 tarball / 비대화형 폴백 | 개입 주입 실행 | 전부 거부 (exit≠0) |
| L2 회귀 | main 브랜치 | `OPAL_VERSION=main bash scripts/install.sh` | 기존 동작 동일 |
| L3 문서 | TEST.md | 9칸 매트릭스 완결성 | 전 칸 증거 또는 사유 |

---

## 8. 기술 컨텍스트

### 8.1 기술 스택

| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| 설치·업데이트 부트스트랩 | Bash (bash 3.2 호환 — `update.sh:217` 명시) | 없음 (커뮤니티 스킬 해당 없음) |
| Windows 부트스트랩 | PowerShell 5.1+ / 7+ (`install.ps1:32`) | 없음 |
| CI 발행 | GitHub Actions (참조 전용) | 없음 |
| 검증 도구 | `curl`, `shasum`/`sha256sum`, `tar`, `Get-FileHash`, `awk` | 없음 |

> React/Next.js/Python/shadcn 등 커뮤니티 스킬 대상 스택이 없어 Step 2(기술 컨텍스트 로딩)에서 추천 스킬 Read 대상 0건이다.

### 8.2 사용 MCP

| MCP | 조회 결과 요약 |
|-----|--------------|
| (없음) | 라이브러리 API 문서 참조가 불필요한 셸/PowerShell 내장 도구 작업. context7·shadcn MCP 미사용 |

### 8.3 참조 문서 (설계 결정 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | update.sh | `opal/tools/opal-cli/lib/update.sh` | URL 결정(`:127-133`)·체크섬(`:172-205`)·추출(`:207-213`) 현행 로직 (F-001·F-004·F-005) |
| D-2 | 소스 | install.sh | `scripts/install.sh` | URL(`:111-121`)·파일명(`:180`)·`verify_checksum`(`:210-279`)·`extract_to_tmp`(`:283-299`) (F-002·F-004·F-005) |
| D-3 | 소스 | install.ps1 | `scripts/install.ps1` | URL(`:94-102`)·파일명(`:141`)·`Verify-Checksum`(`:164-232`)·추출부(`:252-270`) (F-003·F-004·F-005) |
| D-4 | 설계 | release.yml | `.github/workflows/release.yml` | 발행 자산 생성 방식(`:26-35`)·자산 동시 업로드(`:53-56`)·provenance 대상(`:37-40`) — D-B 판정 근거 |
| D-5 | 설계 | .gitattributes | `.gitattributes` | `export-ignore`(`:7,10,13,16,19-21`)·`export-subst`(`:25`) 적용 범위 — `tasks/` 이중 제외 판단 |
| D-6 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | 구현 규칙 — Guards / @header / Citation / 변경이력 / 배포 경계 / 플랫폼 분기 격리 |
| D-7 | 설계 | PROJECT.md | `docs/PROJECT.md` | 원칙 3(플랫폼 독립성) / §프로젝트 구성 영역·전문 에이전트 매핑 |
| D-8 | 설계 | AGENT.md | `.opal/AGENT.md` | 금지사항 — `~/.opal/` 직접 편집 금지 / 하드코딩 플랫폼 분기 금지 |
| D-9 | 기획 | TASK.md | `tasks/085-260807-opds-릴리즈-체크섬-검증경로-정합/TASK.md` | 요구사항 F-1~F-6·AC·확정 설계 방향 S-1~S-5·실측 근거 A-1~A-4·범위/제약 |
| D-10 | 설계 | ARCHITECTURE.md | `docs/ARCHITECTURE.md` | §배포 모델(`:196-228`)·§배포 채널(`:321-331`) — Step 6 갱신 대상 |
| D-11 | 설계 | citation-rules.md | `opal/core/references/harness/citation-rules.md` | §0 근거 제시 원칙 / §2.4 `[MUST]` 포맷 / §3 참조 테이블+인라인 |
| D-12 | 설계 | opal-harness.md | `opal/core/references/opal-harness.md` | §1 Guards — 승인 전 코드 미작성·커밋 금지 |
| D-13 | 소스 | code-scan.json | `.opal/code-scan.json` | `extensions`·`scopes`에 `.sh`/`.ps1`·`scripts/` 미포함 → @header 규칙 비적용 판정 (D-F) |
| D-14 | 소스 | run.sh | `opal/tools/opal-cli/run.sh` | `set -euo pipefail`(`:24`)·symlink 해석(`:31-38`) — 헬퍼 호출 규약·공유 위치 부재 근거 |

---

## 9. 리스크 및 대응 (기능-리스크 연결)

| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| R-1 | 네트워크 순단이 "릴리즈 자산 부재"로 오판되어 검증 가능한 설치가 UNVERIFIED로 강등 (H-1) | F-004 | 중 | **수용** — fail-closed(비대화형 거부, 대화형 디폴트 N)라 보안 회귀 없음. 폴백 로그에 사유를 명시해 사용자가 재시도 판단 가능하게 함 |
| R-2 | 3경로 규약 드리프트 — 코드 공유가 불가능해 3중 중복 유지 (H-2·H-9) | F-001~F-005 | 높 | Step 1 기준 구현 → Step 3 문자 단위 이식, Step 4 정적 대조표 8항목으로 차단. 헤더 `DL-CONTRACT (085)` 각인으로 후속 유지보수자에게 규약 존재를 알림 |
| R-3 | `scripts/install.sh`는 `raw.githubusercontent.com/.../main/`에서 직접 fetch되므로 **main 병합 즉시 전 사용자에게 유효**해진다 | F-002 | 높 | Step 5 실측 완료 전 병합 금지. TEST.md 증거 확보 후 소유자 승인 하에 커밋 (Guards — `opal/core/references/opal-harness.md` §1) |
| R-4 | `update.sh` 변경은 `~/.opal/` 재배포가 있어야 반영되므로, 기존 사용자는 **한 번은 구버전 update.sh로** 업데이트를 수행한다 | F-001 | 중 | 구버전 사용자는 v0.6.11 이하 태그에서 여전히 하드 실패한다. 회피 경로를 안내: `OPAL_VERSION=<tag> curl … install.sh \| bash` 재설치. 소유자 보고 항목 |
| R-5 | Windows 실측 환경 부재 시 F-003 검증이 대체 수단에 의존 | F-003·F-006 | 중 | TS-009 대체 검증 3종(구문 파싱 + 단위 판정 + 규약 대조표) 정의. 사유를 TEST.md에 명시 (AC 허용 범위) |
| R-6 | `_dl_detect_strip`이 `tar -tzf`로 아카이브를 **2회 읽음**(판정 1회 + 추출 1회) — 대용량 시 지연 | F-005 | 낮 | 현행 아카이브 크기(수 MB)에서 무시 가능. 대안(추출 후 사후조건만으로 판정 후 재추출)은 디스크 I/O가 더 크므로 미채택 |
| R-7 | `install.ps1` 변경이력이 `.NOTES` 블록(`:28-29`, v1.0 정지)과 `# 변경이력` 블록(`:35-48`, v1.0.7)으로 **이원화** | F-003 | 낮 | 이번 범위에서는 유지 중인 블록만 갱신. 이원화 해소는 별도 정리 태스크 후보로 기록 (범위 밖) |
| R-8 | `update.sh`의 인스톨러 탐색이 `scripts/install/macos.sh`·`scripts/install-mac.sh`만 확인하여 **Linux 경로 미지원** (`opal/tools/opal-cli/lib/update.sh:230-234`) | — | 중 | **이번 태스크 범위 밖의 선재 결함**. 관찰 기록만 남기고 별도 태스크로 제안. 이번 변경으로 악화되지 않음 |
| R-9 | 용어 일관성 — 3경로가 동일 개념에 서로 다른 식별자 사용(bash `_DL_MODE` / `OPAL_CHECKSUM_MODE` / PowerShell `$script:DlMode`) | F-001~F-003 | 낮 | 언어별 네이밍 관례(bash 대문자 전역 / PowerShell PascalCase)를 따르되, **값 집합은 `verify`/`unverified`/`branch` 3종으로 완전 동일**하게 고정. Step 4 대조표 항목에 포함 (citation-rules.md §7 검출 대상) |
