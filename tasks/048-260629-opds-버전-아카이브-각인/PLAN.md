# PLAN: 버전을 릴리스 아카이브에 각인 (export-subst) — 설치 시점 API 의존 제거

> 작성일: 2026-06-29 | 입력: TASK.md (ANALYSIS.md 없음)
> 모드: Multi-Feature

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

설치·업데이트가 GitHub API(`/releases/latest`, `/tags`)로 버전을 결정하는 현 구조를 제거하고, **릴리스(`git archive`) 시점에 git이 `VERSION` 파일에 실제 태그를 각인**(`export-subst` + `$Format:%(describe:tags)$`)하도록 전환한다. 설치기 4종은 "추출한 tarball의 `VERSION`을 읽되, 미치환 플레이스홀더(`$Format:` 잔존)이면 기존 폴백"으로 동작한다. API 403(rate limit)·네트워크 차단 시 버전 라벨이 `main`으로 오염되는 문제를 근본 제거한다 (`scripts/install.sh:100`, `opal/tools/opal-cli/lib/update.sh:107`).

### 1.2 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | 각인 인프라 — 루트 `VERSION`(`$Format:...$`) + `.gitattributes` `export-subst` | R1, R2 | P0 | 없음 |
| F-002 | `install.sh` tarball VERSION 우선 + API 폴백 | R3 | P0 | F-001 |
| F-003 | `opal-cli/lib/update.sh` tarball VERSION 우선 + API 폴백 | R4 | P0 | F-001 |
| F-004 | `install-mac.sh` VERSION 기록 우선순위 재배치 (tarball 최상위) | R5 | P0 | F-001 |
| F-005 | `install.ps1` tarball VERSION 우선 + API 폴백 (플랫폼 일관성) | R6 | P0 | F-001 |
| F-006 | 회귀 테스트 — `git archive` 3경로 + 설치기 셸 함수 단위 테스트 | R7 | P0 | F-001~F-005 |
| F-007 | 변경이력 행 추가 (스크립트·문서) | R8 | P1 | F-002~F-005 |

### 1.3 기능 의존 그래프 (ASCII)

```
F-001 ─┬─ F-002 ─┐
       ├─ F-003 ─┤
       ├─ F-004 ─┼─ F-006 ─ F-007
       └─ F-005 ─┘
```

> F-002~F-005는 F-001(각인 인프라)을 공유 전제로 하지만 서로 독립 파일이므로 병렬 가능. F-006 회귀 테스트는 F-001~F-005 산출물에 의존. F-007 변경이력은 각 파일 수정과 같은 Step에 흡수 가능(아래 §4 참조).

---

## 리스크 가설 표

> PLAN 단계에서 작성. TEST-SCENARIO.md §1의 입력이 됨.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | F-001 `.gitattributes` export-subst | `VERSION`이 export-ignore에 매칭되어 archive에서 누락 → 설치기가 폴백으로 전락 | P0 | L2 (실 `git archive`) | S-1, S-2 |
| H-2 | F-001 치환 메커니즘 | 태그 archive에서 `%(describe:tags)`가 미치환/오치환 → 잘못된 버전 각인 | P0 | L2 (실 `git archive` 태그/HEAD) | S-1 |
| H-3 | F-002~F-005 판별 로직 | tarball VERSION이 플레이스홀더(`$Format:` 잔존)인데 실값으로 오인 → git clone 경로에 `$Format:...$`가 `~/.opal/VERSION`에 기록 | P0 | L1 (셸 함수 단위) | S-4, S-7 |
| H-4 | F-002~F-005 폴백 | API 완전 실패(403/차단) 시 tarball VERSION을 못 읽으면 `main` 오염 재발 | P0 | L1 (curl 강제 실패 + 태그 tarball) | S-5 |
| H-5 | F-004 우선순위 재배치 | git clone(개발자) 경로에서 tarball VERSION 부재 시 `git describe` 폴백이 깨짐 | P1 | L1 (개발자 경로 시뮬레이션) | S-6 |
| H-6 | F-001 VERSION 파일 자체 | 루트 `VERSION` 파일이 `opal-cli --version` 등 런타임이 직접 읽어 미치환 placeholder를 표출 | P2 | L1 (grep 사용처 회귀) | S-8 |
| H-7 | F-005 install.ps1 | install.ps1이 추출 전에 버전 결정 후 windows.ps1에 `-OpalVersion`으로 넘기는 구조 — tarball VERSION을 추출 후 읽어 재전달해야 함(순서 의존) | P1 | L1 (PS 로직 흐름 검토) | S-9 |
| H-8 | 보안 | VERSION/스크립트 변경에 시크릿·토큰 혼입 | P1 | L1 (시크릿 스캔) | S-10 |

---

## 2. 기능별 분석

### F-001: 각인 인프라 — 루트 VERSION + .gitattributes export-subst

#### 2.1.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 환경 | `VERSION` | 각인 대상 플레이스홀더 파일 (루트) | 신규 |
| 환경 | `.gitattributes` | export 규칙 (export-ignore + 신규 export-subst) | 수정 |
| 배치 | `.github/workflows/release.yml` | `git archive HEAD`로 릴리스 tarball 생성 (각인 적용 지점) | 수정(주석/검증, 선택) |

#### 2.1.2 현재 구현
- 저장소에 커밋된 `VERSION` 파일 없음 (TASK.md 배경 분석 표). 버전은 설치 시점 API 조회로 결정.
- `.gitattributes:7-21`는 `export-ignore`만 사용: `tasks/`·`docs/`·`*/backup/`·`.opal/`·`.github/`·`.gitignore`·`.gitattributes` 제외. `export-subst`는 미사용.
- 루트 레벨 `VERSION`은 어떤 export-ignore 패턴에도 매칭되지 않음 → archive에 포함됨 (검증: `git check-attr export-ignore VERSION` → `unspecified`, 실측 확인됨).
- 릴리스 워크플로우 `.github/workflows/release.yml:30`: `git archive --format=tar.gz -o "${ARCHIVE}" HEAD`. 트리거는 태그 push(`on.push.tags: ['v*']`, `:8-10`)이므로 **HEAD == 태그 커밋** → `%(describe:tags)`가 정확한 태그로 치환됨 (실측 확인됨).

#### 2.1.3 영향 범위
- **하위 의존**: 없음 (git/GitHub 네이티브 메커니즘).
- **상위 의존**: F-002~F-005 설치기 전부가 이 파일의 치환 결과를 소비. F-006 테스트의 검증 대상.
- **공유 상태**: `~/.opal/VERSION`(설치 후 기록) — `opal-cli update`의 버전 비교 기준 (`update.sh:68-72`).
- **잠재 사용처 회귀(H-6)**: 런타임이 루트 `VERSION`을 직접 읽는 코드가 있으면 git clone 환경에서 placeholder 노출 위험 → §2.1.2 검증 필요 (Step 1 완료 기준에 포함).

### F-002: install.sh tarball VERSION 우선 + API 폴백

#### 2.2.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 배치 | `scripts/install.sh` | macOS/Linux one-liner 진입 부트스트랩 — 버전 결정·tarball 추출 | 수정 |

#### 2.2.2 현재 구현
- `resolve_default_version()` (`scripts/install.sh:69-103`): `OPAL_VERSION` 미설정 시 ① `/releases/latest` (`:81-83`) → ② `/tags?per_page=1` (`:87-89`) → ③ 둘 다 실패 시 `OPAL_VERSION="main"` + 경고 (`:100-101`).
- 결정된 `OPAL_VERSION`을 `export`(`:108`) → URL 구성(`:114-118`) → `fetch_tarball`(`:177`) → `verify_checksum`(`:209`) → `extract_to_tmp`(`:282`, `OPAL_EXTRACT_DIR`에 `--strip-components=1` 추출, `:294`) → `exec_platform_installer`(`:304`)가 `install/macos.sh|linux.sh`를 `exec`(`:336`)하며 `OPAL_VERSION`은 export로 전달.
- **현 구조의 핵심**: 버전 결정이 **추출 전(`resolve_default_version`)**에 일어나고, 추출된 tarball 내용은 버전 결정에 쓰이지 않음.

#### 2.2.3 영향 범위
- **하위 의존**: `extract_to_tmp`가 만든 `OPAL_EXTRACT_DIR` (추출 디렉토리). 신규 로직은 여기의 `VERSION`을 읽음.
- **상위 의존**: `install/macos.sh|linux.sh`(=install-mac.sh 계열)가 `OPAL_VERSION` env를 받아 `~/.opal/VERSION` 기록 (F-004).
- **순서 제약**: 버전 "각인값 채택"은 **추출 이후**에만 가능. `resolve_default_version`은 tarball URL 결정을 위해 추출 전에도 필요 → 2단계 구조(URL용 ref 결정 → 추출 후 VERSION 각인값으로 override).

### F-003: opal-cli/lib/update.sh tarball VERSION 우선 + API 폴백

#### 2.3.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 배치 | `opal/tools/opal-cli/lib/update.sh` | `opal-cli update` 서브커맨드 — 버전 결정·재배포 | 수정 |

#### 2.3.2 현재 구현
- `cmd_update()` (`update.sh:27-232`): 로컬 버전 읽기(`:68-72`) → `--to` 미지정 시 자동 결정 ① `/releases/latest`(`:87-89`) → ② `/tags`(`:93-95`) → ③ `main`(`:107`).
- 버전 비교(`:113-119`): 로컬==리모트이고 둘 다 `v*`이면 "이미 최신" 종료.
- URL 결정(`:127-131`) → 다운로드(`:158`) → 체크섬(`:170-202`) → 추출 `extract_dir`(`:205-209`) → 설치기 호출 `OPAL_VERSION="$version"`(`:230`) 전달.
- **현 구조 핵심**: install.sh와 동일하게 버전 결정이 추출 전. 추출된 `extract_dir/VERSION`은 미사용.

#### 2.3.3 영향 범위
- **하위 의존**: `extract_dir`의 `VERSION`. `--to <태그>` / latest / `main` 3경로 모두 적용.
- **상위 의존**: 설치기(`install/macos.sh` 또는 `install-mac.sh`)가 `OPAL_VERSION` env 소비 (F-004).
- **버전 비교 영향**: 각인값을 채택하면 `:113-119` 비교 시점 문제 — 비교는 추출 전 결정값으로 수행되므로 "이미 최신" 스킵 판단과 실제 설치 버전이 어긋날 수 있음 (S-5에서 검증; URL용 ref와 각인값이 동일 태그면 무해).

### F-004: install-mac.sh VERSION 기록 우선순위 재배치

#### 2.4.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 배치 | `scripts/install-mac.sh` | 실제 자산 배포 + `~/.opal/VERSION` 기록 | 수정 |

#### 2.4.2 현재 구현
- VERSION 기록 블록 (`install-mac.sh:1222-1231`): 우선순위 = `$OPAL_VERSION`(`:1225`) → git describe(`:1226-1228`, `FRAMEWORK_ROOT/.git` 존재 시) → `main` 폴백(`:1229`) → `echo > $opal_home/VERSION`(`:1230`).
- 비대화형 마무리 표시 (`install-mac.sh:1763-1766`): `final_version="${OPAL_VERSION:-main}"` 후 `~/.opal/VERSION` 파일이 있으면 그 값으로 덮어씀(`:1764`) → 완료 배너.
- **현 구조 핵심**: 추출된 소스 루트는 `FRAMEWORK_ROOT`(`detect_framework_root`, `:1743`). git clone이면 `.git` 존재, tarball 추출이면 `.git` 부재. 즉 **tarball 추출 경로는 현재 `$OPAL_VERSION`(install.sh가 결정한 API값)에만 의존**.

#### 2.4.3 영향 범위
- **하위 의존**: `FRAMEWORK_ROOT/VERSION` (추출된 소스 루트의 각인 파일). 신규 최상위 단계.
- **상위 의존**: `~/.opal/VERSION` → `opal-cli update` 비교 기준 / `opal-cli --version` 표시 (H-6 사용처 확인 대상).
- **자기완결 원칙**: install-mac.sh는 install.sh/update.sh 양쪽이 호출 → install-mac.sh 자체가 `FRAMEWORK_ROOT/VERSION`을 직접 읽으면 호출자(install.sh/update.sh)의 각인 채택 로직과 **중복**될 수 있음. 단일 진실 지점은 install-mac.sh(자산 배포·기록 주체)로 두는 것이 견고 (§3.4 D-설계1 참조).

### F-005: install.ps1 tarball VERSION 우선 + API 폴백

#### 2.5.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 배치 | `scripts/install.ps1` | Windows one-liner 진입 — 버전 결정·추출·windows.ps1 호출 | 수정 |
| 배치 | `scripts/install/windows.ps1` | 실제 배포 + `~/.opal/VERSION` 기록 (`-OpalVersion` 수신) | 수정(선택, §3.5 참조) |

#### 2.5.2 현재 구현
- `Resolve-DefaultVersion` (`install.ps1:60-85`): API ① `/releases/latest`(`:66`) → ② `/tags`(`:72`) → ③ `main`(`:82`).
- URL 구성(`:96-101`) → `Fetch-Tarball`(`:128`) → `Verify-Checksum`(`:163`) → `Invoke-PlatformInstaller`(`:233`)가 `tar` 추출(`:259`, `--strip-components 1` + `--exclude tasks*`) 후 `windows.ps1`을 `-OpalVersion $script:OpalVersion`으로 호출(`:286`).
- `windows.ps1:1758-1760`: 전달받은 `$OpalVersion`을 `~/.opal/VERSION`에 `Set-Content ... -NoNewline`으로 기록.
- **현 구조 핵심(H-7)**: install.ps1은 **추출 후** windows.ps1을 호출하므로, 추출 디렉토리(`$extractDir`)에서 `VERSION`을 읽어 `$script:OpalVersion`을 override한 뒤 `-OpalVersion`으로 넘기면 windows.ps1 변경 없이도 각인값 반영 가능. 단 추출은 `Invoke-PlatformInstaller` 내부(`:251-260`)에서 일어나므로 읽기 시점은 그 직후(`:272` 부근).

#### 2.5.3 영향 범위
- **하위 의존**: `$extractDir/VERSION`.
- **상위 의존**: `windows.ps1`의 `~/.opal/VERSION` 기록.
- **주의**: `:259-260` `tar --exclude='tasks/*'` 등은 VERSION에 영향 없음(루트 파일). `--strip-components 1`로 최상위 디렉토리가 벗겨지므로 `$extractDir/VERSION`이 올바른 경로.

### F-006: 회귀 테스트

#### 2.6.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 배치 | `scripts/tests/test_version_stamp.sh` | `git archive` 3경로 각인 + 설치기 셸 함수 단위 테스트 | 신규 |

#### 2.6.2 현재 구현
- 현재 `scripts/tests/` 디렉토리 존재 여부 미확정 — EXECUTE에서 신규 생성. 기존 테스트 하네스가 없으면 자기완결 bash 테스트 스크립트(exit code 기반)로 구성.

#### 2.6.3 영향 범위
- F-001~F-005 산출물 전체를 검증 대상으로 삼음. CI 통합은 본 태스크 범위 외(후속).

### F-007: 변경이력 행 추가

#### 2.7.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 배치 | `scripts/install.sh` 외 4종 | 헤더 내 변경이력 라인 | 수정 |

#### 2.7.2 현재 구현
- 각 스크립트는 헤더 주석에 `변경이력:` 블록 보유 (`install.sh:32-40`, `update.sh:17-22`, `install.ps1:35-47`, `windows.ps1:28-47` 부근). install-mac.sh도 동일 패턴.

#### 2.7.3 영향 범위
- 각 파일 수정 Step에 흡수 (별도 Step 불필요). `docs/CONVENTIONS.md §변경이력`: 일시 `YYYY-MM-DD HH:mm` KST + 태스크 번호 `(048)`.

---

## 3. 기능별 설계

### F-001: 각인 인프라

#### 3.1.1 파일 변경 계획
**신규 생성**
| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `VERSION` | 환경 | 한 줄 `$Format:%(describe:tags)$` (개행 정책은 §3.1.2) | TASK R1 |

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `.gitattributes` | 환경 | `VERSION export-subst` 행 추가 (export-ignore 매칭 안 됨 확인) | TASK R2, `.gitattributes:7-21` |
| 2 | `.github/workflows/release.yml` | 배치 | (선택) `git archive HEAD`가 각인 적용됨을 주석 보강 — 코드 변경 불필요 | `.github/workflows/release.yml:30` |

#### 3.1.2 설계 상세
- **`VERSION` 파일 내용**: 정확히 `$Format:%(describe:tags)$` 한 줄. (→ TASK §확정된 설계 방향 1)
  - **[MUST]** AC(R1): 파일 존재 + 내용이 정확히 해당 플레이스홀더. `git check-attr export-subst VERSION` → `set` (R2 AC).
  - **개행 정책**: 끝에 trailing newline 1개 허용. 설치기 판별·기록 시 `tr -d '[:space:]'`(update.sh:69 기존 패턴)·PS `Trim()`으로 정규화하므로 무해. 단 git clone 경로의 placeholder 비교는 trailing newline 포함 가능성 고려해 부분 매칭(`$Format:` prefix 검사)으로 설계 (§3.2.2).
- **`.gitattributes` 추가**: 파일 끝에
  ```
  # 릴리스 버전 각인 — git archive 시 %(describe:tags) 치환 (task 048)
  VERSION export-subst
  ```
  - **[MUST]** export-ignore 패턴(`.gitattributes:7-21`)에 루트 `VERSION`은 매칭되지 않음 (실측: `git check-attr export-ignore VERSION` → `unspecified`). export-subst와 export-ignore는 독립 속성이므로 충돌 없음.
- **치환 메커니즘 (실측 검증됨)**:
  - 태그 archive (또는 HEAD==태그 커밋) → `v0.6.5` 같은 clean 태그
  - HEAD가 태그 이후 커밋 → `v0.6.5-N-g<sha>` (describe 형식)
  - 작업트리 / git clone → `$Format:%(describe:tags)$` 미치환 (placeholder 그대로)
  - 근거: 로컬 `git archive` 데모 실측 (PLAN 작성 중 scratch repo 검증). git 2.32+ 필요 (`git --version` → 2.50.1 확인).
- **release.yml 무변경 근거**: `release.yml:30` `git archive HEAD`는 태그 push 트리거(`:8-10`) 시 HEAD가 태그 커밋이므로 각인이 정확히 동작. 코드 수정 불필요, 주석 보강만 선택적.

#### 3.1.3 환경 변경
git 2.32+ (이미 충족). 추가 패키지 없음.

#### 3.1.4 배치/마이그레이션
export-subst는 **설정 커밋 이후 생성되는 archive부터** 적용 → 첫 실효는 v0.6.5. v0.6.4 이하 소급 불가 (TASK 제약). 마이그레이션 스크립트 불필요.

#### 3.1.5 테스트 시나리오 (AC ↔ TS 매핑)
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | R1 AC | 산출물 검사 | 루트 `VERSION` 존재 + 내용 정확히 `$Format:%(describe:tags)$` |
| TS-002 | R2 AC | 산출물 검사 | `git check-attr export-subst VERSION` → `set`; `export-ignore VERSION` → `unspecified` |
| TS-003 | R7 AC | 회귀 테스트 | 로컬 `git archive <태그>` tarball의 `VERSION` = 실제 태그 |
| TS-004 | R7 AC | 회귀 테스트 | 브랜치/HEAD-after-tag archive `VERSION` = `<tag>-N-g<sha>` (describe) |
| TS-005 | R7 AC | 회귀 테스트 | 작업트리 `VERSION` = `$Format:...$` 미치환 (placeholder) |

### F-002: install.sh tarball VERSION 우선

#### 3.2.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `scripts/install.sh` | 배치 | `extract_to_tmp` 직후 각인값 채택 단계 추가 + `OPAL_VERSION` override | TASK R3, `install.sh:282-298` |

#### 3.2.2 설계 상세
- **신규 헬퍼 `adopt_stamped_version()`** (extract 후 호출):
  ```bash
  # 추출된 tarball의 VERSION이 치환되어 있으면(=$Format: 잔존 아님) 그 값을 채택.
  # 미치환/부재면 기존 OPAL_VERSION(resolve_default_version 결과) 유지 → 폴백.
  adopt_stamped_version() {
      local vf="${OPAL_EXTRACT_DIR}/VERSION"
      [[ -f "$vf" ]] || return 0
      local stamped
      stamped="$(tr -d '[:space:]' < "$vf" 2>/dev/null || true)"
      [[ -z "$stamped" ]] && return 0
      case "$stamped" in
          *'$Format:'*) return 0 ;;   # 미치환 placeholder → 폴백 유지
      esac
      OPAL_VERSION="$stamped"
      export OPAL_VERSION
      info "tarball VERSION 각인값 채택: ${OPAL_VERSION} (API 미사용)"
  }
  ```
  - **[MUST]** 판별 기준은 "`$Format:` 문자열 잔존 여부"(부분 매칭). `case ... *'$Format:'*` 사용 — bash 3.2 호환 (`[[ == ]]` glob도 가능하나 case가 명확). (→ TASK §확정 설계 3)
  - 호출 위치: `main()`의 `extract_to_tmp` 다음, `exec_platform_installer` 이전 (`install.sh:358-359` 사이). DRY-RUN 시 `OPAL_EXTRACT_DIR`은 빈 디렉토리(`:285-286`)라 `[[ -f ]]` false → no-op (안전).
  - **함수 추출 가능성(테스트용)**: `adopt_stamped_version`는 `OPAL_EXTRACT_DIR`만 입력으로 받는 순수 함수 형태 → F-006 단위 테스트에서 source 후 직접 호출 가능 (red-first §4 공개 인터페이스: 환경변수 `OPAL_VERSION` 관측).
- **URL/폴백 무변경**: `resolve_default_version`(`:69-103`)·URL 구성(`:114-118`)은 그대로 (tarball을 받기 위한 ref 결정에 여전히 필요). 각인값은 **받은 후** override.
- **API 미사용 보장(H-4)**: 사용자가 `OPAL_VERSION=v0.6.5`를 명시하면 `resolve_default_version`이 API 호출 자체를 스킵(`:70-72`) → 태그 tarball 추출 → 각인값 채택. API 403이어도 정확 버전. (S-5)

#### 3.2.3 환경 변경
해당 없음.

#### 3.2.4 배치/마이그레이션
해당 없음.

#### 3.2.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-010 | R3 AC | 기능 테스트 | `adopt_stamped_version`: 각인된 VERSION(`v0.6.5`) → `OPAL_VERSION=v0.6.5` |
| TS-011 | R3 AC | 기능 테스트 | placeholder VERSION(`$Format:...$`) → `OPAL_VERSION` 불변(폴백 유지) |
| TS-012 | R3 AC | 회귀 테스트 | VERSION 파일 부재(구 tarball) → `OPAL_VERSION` 불변 |
| TS-013 | R3 AC | 회귀 테스트 | DRY-RUN 모드에서 no-op (빈 추출 디렉토리) |

### F-003: opal-cli/lib/update.sh tarball VERSION 우선

#### 3.3.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/opal-cli/lib/update.sh` | 배치 | 추출(`:205-210`) 직후 각인값 채택 + `version`/`OPAL_VERSION` override | TASK R4 |

#### 3.3.2 설계 상세
- **추출 직후 각인 채택** (`update.sh:210` 직후, 설치기 호출 `:230` 이전):
  ```bash
  # 각인 VERSION 우선 — install.sh adopt_stamped_version과 동일 원칙
  if [[ -f "$extract_dir/VERSION" ]]; then
      stamped="$(tr -d '[:space:]' < "$extract_dir/VERSION" 2>/dev/null || true)"
      case "$stamped" in
          ''|*'$Format:'*) : ;;          # 부재/미치환 → version 유지(폴백)
          *) version="$stamped" ;;       # 각인값 채택
      esac
  fi
  ```
  - **[MUST]** `version` 변수를 override → 설치기 호출 `OPAL_VERSION="$version"`(`:230`)에 전달. (→ TASK R4 AC)
- **버전 비교(`:113-119`) 보존**: 비교는 추출 전 결정값 기준 — URL용 ref와 각인값이 같은 태그면 무해. `--to <태그>`/latest 모두 동일 태그를 가리키므로 일관. (S-5 검증)
- **`--force`/체크섬 흐름 무변경**.
- bash 3.2 호환: `case` 사용 (mac 기본 bash).

#### 3.3.3 환경 변경
해당 없음.

#### 3.3.4 배치/마이그레이션
해당 없음.

#### 3.3.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-020 | R4 AC | 기능 테스트 | 각인 VERSION → `version` override, 설치기에 정확 태그 전달 |
| TS-021 | R4 AC | 기능 테스트 | placeholder/부재 → `version` 불변(폴백) |
| TS-022 | R4 AC | 회귀 테스트 | API 403 시뮬레이션 + `--to v0.6.5` → tarball VERSION 우선 |

### F-004: install-mac.sh VERSION 기록 우선순위 재배치

#### 3.4.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `scripts/install-mac.sh` | 배치 | `:1222-1231` 우선순위에 "tarball/소스 루트 VERSION 각인값" 최상위 삽입 | TASK R5, `install-mac.sh:1223-1230` |

#### 3.4.2 설계 상세
- **D-설계1 (자기완결 채택)**: install-mac.sh는 install.sh·update.sh 양쪽이 호출하지만, **자산 배포·VERSION 기록의 주체**이므로 `FRAMEWORK_ROOT/VERSION`을 install-mac.sh 자체에서도 직접 읽어 최상위 우선순위로 둔다. 이로써 호출자(install.sh/update.sh)가 override를 안 하더라도 일관 동작 (방어적 이중화). 단 install.sh/update.sh의 `OPAL_VERSION` override(F-002/F-003)가 있으면 그 값과 각인값은 동일 태그이므로 충돌 없음.
- **신규 우선순위** (`install-mac.sh:1225` 부근 재구성):
  ```bash
  local installed_version="${OPAL_VERSION:-}"
  # 1) 추출된 소스 루트의 각인 VERSION (tarball 설치 경로 — 최우선)
  if [[ -f "$FRAMEWORK_ROOT/VERSION" ]]; then
      _stamped="$(tr -d '[:space:]' < "$FRAMEWORK_ROOT/VERSION" 2>/dev/null || true)"
      case "$_stamped" in
          ''|*'$Format:'*) : ;;              # 미치환/부재 → 다음 폴백
          *) installed_version="$_stamped" ;; # 각인값 채택
      esac
  fi
  # 2) $OPAL_VERSION (one-liner installer가 전달; 위에서 미채택 시)
  # 3) git describe (개발자 git clone 경로)
  if [[ -z "$installed_version" ]] && command -v git &>/dev/null && [[ -d "$FRAMEWORK_ROOT/.git" ]]; then
      installed_version="$(cd "$FRAMEWORK_ROOT" && git describe --tags --always 2>/dev/null || echo "main")"
  fi
  # 4) main 폴백
  installed_version="${installed_version:-main}"
  echo "$installed_version" > "$opal_home/VERSION"
  ```
  - **[MUST]** 우선순위 주석과 코드 일치 (R5 AC). 미치환 placeholder는 채택하지 않고 다음 폴백으로 (H-3 방어).
  - **[MUST]** git clone 경로(개발자): `FRAMEWORK_ROOT/VERSION`이 placeholder → 1단계 스킵, `$OPAL_VERSION` 미설정 → 3단계 `git describe` 폴백 유지 (TASK 제약, H-5). (→ TASK §제약 4)
- **`:1763-1764` 마무리 표시**: `~/.opal/VERSION` 파일을 다시 읽어 표시하므로 별도 변경 불필요 (각인값이 이미 기록됨).

#### 3.4.3 환경 변경
해당 없음.

#### 3.4.4 배치/마이그레이션
해당 없음.

#### 3.4.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-030 | R5 AC | 기능 테스트 | `FRAMEWORK_ROOT/VERSION`=각인값 → `~/.opal/VERSION` = 각인 태그 |
| TS-031 | R5 AC | 기능 테스트 | placeholder VERSION + git clone(`.git` 존재) → `git describe` 폴백 |
| TS-032 | R5 AC | 회귀 테스트 | VERSION 부재 + `$OPAL_VERSION` 설정 → `$OPAL_VERSION` 기록 |

### F-005: install.ps1 tarball VERSION 우선

#### 3.5.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `scripts/install.ps1` | 배치 | `Invoke-PlatformInstaller`에서 추출 후 `$extractDir/VERSION` 읽어 `-OpalVersion` override | TASK R6, `install.ps1:259-286` |

#### 3.5.2 설계 상세
- **순서(H-7)**: 추출(`install.ps1:259-260`)은 `Invoke-PlatformInstaller` 내부에서 일어나고 windows.ps1 호출(`:286`)이 그 뒤이므로, 추출 직후(`:272` 부근, windows.ps1 경로 확인 전후) `$extractDir/VERSION`을 읽어 `$script:OpalVersion`을 override.
  ```powershell
  # 각인 VERSION 우선 — 추출된 tarball의 VERSION이 치환되어 있으면 채택
  $versionFile = [IO.Path]::Combine($extractDir, 'VERSION')
  if (Test-Path $versionFile) {
      $stamped = (Get-Content -Raw -LiteralPath $versionFile -ErrorAction SilentlyContinue)
      if ($stamped) { $stamped = $stamped.Trim() }
      if ($stamped -and ($stamped -notlike '*$Format:*')) {
          $script:OpalVersion = $stamped
          Write-Host "[OPAL] tarball VERSION 각인값 채택: $stamped" -ForegroundColor DarkGray
      }
  }
  ```
  - **[MUST]** `-notlike '*$Format:*'` 판별 — placeholder 미치환 시 채택 안 함(폴백). PowerShell `-like`는 와일드카드, `$Format:`의 `$`는 문자 그대로 매칭(작은따옴표 리터럴). (→ TASK R6 AC)
  - 호출부 `:286` `-OpalVersion $script:OpalVersion`는 그대로 — override된 값이 전달됨.
- **windows.ps1 무변경(권장)**: `windows.ps1:1758-1760`은 전달받은 `$OpalVersion`을 기록하므로, install.ps1의 override만으로 충분. **단** 방어적 이중화를 위해 windows.ps1에도 `$extractDir/VERSION` 직접 읽기를 추가할지는 §설계 피드백 D-피1 참조 (기본: install.ps1만 변경, 범위 최소화).
- **`--exclude tasks*`(`:259-260`) 영향 없음**: VERSION은 루트 파일, tasks 제외와 무관.

#### 3.5.3 환경 변경
해당 없음.

#### 3.5.4 배치/마이그레이션
해당 없음.

#### 3.5.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-040 | R6 AC | 산출물 검사 | install.ps1에 추출 후 VERSION 읽기 + `-notlike '*$Format:*'` 판별 로직 존재 |
| TS-041 | R6 AC | 산출물 검사 | placeholder 분기 시 `$script:OpalVersion` 불변(폴백) — 코드 검토 |

> PowerShell 런타임 실측은 macOS 환경 제약 — TS-040/041은 정적 검토 + (가능 시 `pwsh` 설치 환경) 로직 단위 검증.

### F-006: 회귀 테스트

#### 3.6.1 파일 변경 계획
**신규 생성**
| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `scripts/tests/test_version_stamp.sh` | 배치 | git archive 3경로 + adopt_stamped_version 단위 + install-mac VERSION 기록 검증 | TASK R7 |

#### 3.6.2 설계 상세
- **자기완결 bash 테스트** (exit code 기반, 외부 의존 없음):
  - **Part A — git archive 3경로**: scratch repo 생성 → `VERSION`+`.gitattributes export-subst` 커밋 → 태그 → `git archive <tag>`/`HEAD`/추가커밋후 `HEAD` / 작업트리 파일 비교. (TS-003~005)
  - **Part B — install.sh `adopt_stamped_version` 단위**: install.sh를 source하지 않고(main 자동 실행 방지) 함수만 추출 검증이 어려우므로, **subshell에서 `OPAL_DRY_RUN`/`OPAL_VERSION` 제어 + 추출 디렉토리 mock** 방식 또는 함수를 별도 `lib`로 추출. 설계 결정: install.sh의 `main "$@"` 자동 실행 때문에 직접 source 불가 → **테스트는 mock `OPAL_EXTRACT_DIR`를 만들고 함수 본문을 복제 검증**하기보다, install.sh를 `OPAL_DRY_RUN=1` + 로컬 추출 디렉토리 주입이 어려우므로 **셸 함수를 작은 헬퍼로 분리**하는 방안을 §설계 피드백 D-피2에 제안. 최소안: Part A(archive)와 Part C(install-mac)를 핵심으로 하고, adopt 로직은 install-mac.sh 경로(Part C)로 통합 검증.
  - **Part C — install-mac.sh VERSION 기록**: mock `FRAMEWORK_ROOT`(VERSION 각인값/placeholder/.git 유무 조합) + `OPAL_HOME` 임시 → install_opal의 VERSION 기록 블록만 검증 가능하도록 함수 분리 또는 환경 구성. install-mac.sh 전체 실행은 부작용이 크므로 **VERSION 기록 로직을 함수(`record_installed_version`)로 추출**하여 단위 테스트 (§설계 피드백 D-피2).
  - **Part D — API 실패 시뮬레이션**: `PATH`에 curl을 가로채는 stub(항상 비정상 종료) 배치 → 태그 archive 추출 경로에서 정확 버전 확인. (TS-022)
- **bash 3.2 호환**: 연관 배열·`mapfile` 미사용. `case` 패턴 매칭 사용.
- **RED-first**: 본 테스트가 RED 트랙의 실패 테스트가 됨 (§TEST-SCENARIO에서 트랙 확정).

#### 3.6.3 환경 변경
해당 없음 (git, bash, tar만 사용).

#### 3.6.4 배치/마이그레이션
CI 통합은 후속 (본 태스크는 로컬 실행 테스트 산출).

#### 3.6.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-050 | R7 AC | 회귀 테스트 | test_version_stamp.sh 전체 exit 0 (전 케이스 통과) |
| TS-051 | R7 AC | 보안 테스트 | 시크릿 스캔 — 변경 파일에 토큰/키 없음 |

### F-007: 변경이력 행 추가

#### 3.7.1 파일 변경 계획
**수정** — 각 파일 수정 Step에 흡수 (별도 파일 없음).

#### 3.7.2 설계 상세
- 각 스크립트 헤더 변경이력 블록에 행 추가. 형식 예 (install.sh):
  - `#   v1.5 2026-06-29 HH:mm KST: 버전 결정을 tarball 내 VERSION 각인값 우선으로 전환 + API/main 폴백 강등 (048)`
  - **[MUST]** `docs/CONVENTIONS.md §변경이력` (`docs/CONVENTIONS.md:196-198`): 일시 `YYYY-MM-DD HH:mm` KST + 태스크 번호 `(048)` 괄호 포함.
  - install.ps1 `:35-47`, windows.ps1 `:28-47`, update.sh `:17-22`, install-mac.sh 헤더, `.gitattributes` 주석에도 동일 적용.

#### 3.7.3 환경 변경
해당 없음.
#### 3.7.4 배치/마이그레이션
해당 없음.
#### 3.7.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-060 | R8 AC | 산출물 검사 | 변경 5종(+`.gitattributes`)에 `(048)` 변경이력 행 존재 |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)
| Phase | 기능 | Step | agent | 실행 | 비고 |
|-------|------|------|-------|------|------|
| 1 | F-001 | 1 | opal-task-agent | 순차 | 각인 인프라 (전 후속의 전제) |
| 2 | F-002~F-005 | 2, 3, 4, 5 | opal-task-agent | 병렬 가능 | 독립 파일 4종 |
| 3 | F-006 | 6 | opal-test-agent (RED) / opal-task-agent (GREEN 검증) | 순차 | F-001~F-005 산출물 검증 |
| 4 | F-007 | (흡수) | opal-task-agent | — | 각 수정 Step 내 처리 |

> 본 작업은 셸/PS 스크립트 + git 설정으로 단일 영역(배치/환경, 공통 성격) → opal-task-agent 단일 배치로 묶음. F-006 RED 테스트 작성은 red-first §2(작성자≠구현자)에 따라 opal-test-agent(mode: red)가 담당.

### 4.2 실행 체크리스트
> 총 6개 Step | Phase 4개 | 실행 모드: 복잡 (변경 파일 6개 ≥ 4 → 복잡 모드 기준 충족, §6 참조)

#### Step 1: 각인 인프라 구축 (VERSION + .gitattributes)
- [x] 완료
- **소속 기능**: F-001
- **영역**: 환경
- **agent**: opal-task-agent
- **파일**: `VERSION` (신규), `.gitattributes` (수정), `.github/workflows/release.yml` (선택 주석)
- **작업 내용**: 루트 `VERSION`에 `$Format:%(describe:tags)$` 한 줄 작성. `.gitattributes` 끝에 `VERSION export-subst` + 주석 추가. release.yml은 `git archive HEAD` 각인 적용 주석만 보강(코드 무변경).
- **완료 기준**: `git check-attr export-subst VERSION` → `set`; `git check-attr export-ignore VERSION` → `unspecified`; `git archive` 로컬 데모로 태그→실태그 확인; 루트 VERSION을 런타임이 직접 읽는 사용처 없음 확인(grep).
- **테스트**: TS-001, TS-002, TS-003, TS-004, TS-005
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 2: install.sh 각인값 채택 전환
- [x] 완료
- **소속 기능**: F-002, F-007
- **영역**: 배치
- **agent**: opal-task-agent
- **파일**: `scripts/install.sh`
- **작업 내용**: `adopt_stamped_version()` 헬퍼 추가 + `main()`의 extract 후·exec 전 호출. 각인값이 placeholder가 아니면 `OPAL_VERSION` override. 헤더 변경이력 행 추가 `(048)`.
- **완료 기준**: 각인 VERSION→OPAL_VERSION 채택, placeholder/부재→불변, DRY-RUN no-op. `bash -n scripts/install.sh` 통과.
- **테스트**: TS-010, TS-011, TS-012, TS-013
- **실행 방법**: sub-agent
- **의존**: Step 1

#### Step 3: opal-cli/lib/update.sh 각인값 채택 전환
- [x] 완료
- **소속 기능**: F-003, F-007
- **영역**: 배치
- **agent**: opal-task-agent
- **파일**: `opal/tools/opal-cli/lib/update.sh`
- **작업 내용**: 추출(`:210`) 직후 `extract_dir/VERSION` 각인값으로 `version` override(placeholder/부재 시 폴백). 헤더 변경이력 행 추가 `(048)`.
- **완료 기준**: 각인값→version override, API 403 + `--to v*` 시 정확 버전. `bash -n` 통과.
- **테스트**: TS-020, TS-021, TS-022
- **실행 방법**: sub-agent
- **의존**: Step 1

#### Step 4: install-mac.sh VERSION 기록 우선순위 재배치
- [x] 완료
- **소속 기능**: F-004, F-007
- **영역**: 배치
- **agent**: opal-task-agent
- **파일**: `scripts/install-mac.sh`
- **작업 내용**: `:1222-1231` 우선순위에 "FRAMEWORK_ROOT/VERSION 각인값" 최상위 삽입, `$OPAL_VERSION`→`git describe`→`main` 강등. 주석·코드 일치. (테스트 용이성 위해 VERSION 기록 로직을 `record_installed_version` 함수로 추출 권장 — D-피2). 헤더 변경이력 행 추가 `(048)`.
- **완료 기준**: 각인값→~/.opal/VERSION 기록, placeholder+`.git`→git describe 폴백, 우선순위 주석 일치. `bash -n` 통과.
- **테스트**: TS-030, TS-031, TS-032
- **실행 방법**: sub-agent
- **의존**: Step 1

#### Step 5: install.ps1 각인값 채택 전환
- [x] 완료
- **소속 기능**: F-005, F-007
- **영역**: 배치
- **agent**: opal-task-agent
- **파일**: `scripts/install.ps1`
- **작업 내용**: `Invoke-PlatformInstaller` 추출 후 `$extractDir/VERSION` 읽어 `-notlike '*$Format:*'`이면 `$script:OpalVersion` override (`-OpalVersion`으로 전달). 헤더 변경이력 행 추가 `(048)`. windows.ps1은 무변경(기본) — 이중화 여부는 D-피1.
- **완료 기준**: 추출 후 VERSION 읽기 + placeholder 판별 분기 존재 (정적 검토; pwsh 가용 시 로직 단위 검증). PowerShell 구문 오류 없음.
- **테스트**: TS-040, TS-041
- **실행 방법**: sub-agent
- **의존**: Step 1

#### Step 6: 회귀 테스트 작성 (RED) + 전체 검증
- [x] 완료
- **소속 기능**: F-006
- **영역**: 배치
- **agent**: opal-test-agent (mode: red — RED 작성) → 검증은 PM/test-agent
- **파일**: `scripts/tests/test_version_stamp.sh` (신규)
- **작업 내용**: git archive 3경로(Part A) + API 실패 stub(Part D) + install-mac VERSION 기록(Part C) 단위 테스트. exit code 기반 자기완결 bash. bash 3.2 호환.
- **완료 기준**: RED 단계 — 구현 전 실패 증거(exit≠0) 기록. GREEN 단계 — Step 1~5 완료 후 전체 통과(exit 0).
- **테스트**: TS-050, TS-051 (+ TS-003~005, TS-010~013, TS-022, TS-030~032 실측 커버)
- **실행 방법**: sub-agent
- **의존**: Step 1 (RED 작성) / Step 1~5 (GREEN 검증)

> **docs/ 갱신 Step**: 본 변경은 버전 관리 모델의 구조 변경 — `docs/ARCHITECTURE.md`에 install 어댑터/버전 결정 모델 기술이 있는 경우 갱신 대상. ARCHITECTURE.md에 해당 기술이 없으면 스킵. PM이 PM Gate에서 ARCHITECTURE.md 내 "버전 결정/install 흐름" 기술 유무를 확인 후 갱신 Step(영역: 문서, agent: PM 직접)을 추가 판단.

### 4.3 병렬/순차 판별 근거
| 관계 | 근거 |
|------|------|
| Step 1 → Step 2,3,4,5 | 각인 인프라(VERSION/.gitattributes)가 전 설치기 동작의 전제 |
| Step 2 ∥ Step 3 ∥ Step 4 ∥ Step 5 | 독립 파일 4종, 상호 호출하지만 동일 원칙·파일 충돌 없음 |
| Step 5 → Step 4 (약결합) | install.ps1↔windows.ps1, install.sh↔install-mac.sh는 각각 호출 관계지만 본 변경은 각 진입점에서 독립 처리 → 병렬 안전 |
| Step 1~5 → Step 6 GREEN | 테스트 검증은 산출물 완성 후 |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA
| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | VERSION 내용·export 속성 | TS-001, TS-002 | 파일 내용 정확 + `check-attr export-subst`=set, export-ignore=unspecified |
| F-001 | git archive 3경로 각인 | TS-003, TS-004, TS-005 | 태그→실태그 / HEAD-after-tag→describe / 작업트리→placeholder |
| F-002 | install.sh 각인 채택·폴백 | TS-010~013 | 각인→채택, placeholder/부재→폴백, DRY-RUN no-op |
| F-003 | update.sh 각인 채택·폴백 | TS-020~022 | 각인→override, API 403+`--to`→정확 버전 |
| F-004 | install-mac.sh 우선순위 | TS-030~032 | 각인 최우선, git clone→describe 폴백 |
| F-005 | install.ps1 각인 채택 | TS-040, TS-041 | 추출 후 읽기 + placeholder 폴백 분기 |
| F-006 | 회귀 테스트 통과 | TS-050 | test_version_stamp.sh exit 0 |
| F-007 | 변경이력 행 | TS-060 | 변경 5종+.gitattributes에 `(048)` 행 |

### 5.2 회귀 테스트
- [x] 기존 설치 경로(태그 release 정상 자산) 미파손 — sha256sums.txt 검증 흐름 유지
- [x] git clone(개발자) 경로: `~/.opal/VERSION`이 placeholder 아닌 git describe 값으로 기록
- [x] 구 tarball(VERSION 부재, v0.6.4 이하) 설치 시 기존 API/main 폴백 동작
- [x] DRY-RUN 모드 흐름 비파손 (install.sh / install.ps1)
- [x] `opal-cli update` "이미 최신" 스킵 로직 비파손

### 5.3 코드/문서 품질
- [x] `bash -n` 구문 검사 통과 (install.sh, update.sh, install-mac.sh, test_version_stamp.sh)
- [x] bash 3.2 호환 (연관 배열·mapfile 미사용, case 패턴 사용)
- [x] 변경이력 행 추가 (KST 일시 + `(048)`, `docs/CONVENTIONS.md:196-198`)
- [x] 우선순위 주석과 실제 코드 일치 (install-mac.sh)

### 5.4 보안
- [x] 변경 파일에 하드코딩 토큰/시크릿 없음 (TS-051)
- [x] `VERSION` 파일에 placeholder 외 민감정보 없음
- [x] `.gitignore` 영향 없음 (VERSION은 커밋 대상 — 의도된 트래킹)
- [x] export-subst 치환값이 신뢰 경계(git 객체)에서 생성 — 외부 입력 주입 불가

---

## 6. 복잡도 판별
| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 6개 | 복잡 |
| 변경 파일 수 | 6개 (VERSION, .gitattributes, install.sh, update.sh, install-mac.sh, install.ps1) + 신규 테스트 1 + 선택 release.yml | 복잡 |
| 모듈 범위 | 다중 (install 어댑터 4종 + git 설정) | 복잡 |
| 작업 유형 | 버전 관리 모델 구조 개선 (self-confirming 위험 영역) | 복잡 |
| 외부 의존성 | 없음 (git/GitHub 네이티브, 신규 패키지 없음) | 단순 |
| **실행 모드** | **복잡** | (Step 6 / 파일 6 / 다중 모듈 → 복잡) |

> Short Task 범위 평가: 파일 6개(≥4 복잡 기준)·다중 모듈·self-confirming 위험. Short Task 5 Step 권장 상한을 초과(6 Step). 단 변경 패턴이 동형(4종 설치기 동일 원칙)이고 외부 의존 없음 → 복잡 모드로 진행하되 Full 에스컬레이션 불요. PM 판단 권고: 현 6 Step 유지.

---

## 7. 실행 아키텍처 (복잡 모드)

### C-1. 에이전트 토폴로지
```
Batch 1: [Step 1] opal-task-agent (각인 인프라)
            │
Batch 2: [Step 2][Step 3][Step 4][Step 5] opal-task-agent ×4 (병렬, 독립 파일)
            │
Batch 3: [Step 6] opal-test-agent(RED 작성) → 검증
```
- **그룹핑**: 파일 충돌 방지 — 각 설치기는 독립 파일이므로 별도 디스패치 가능하나, 동일 원칙·동형 변경이므로 단일 opal-task-agent에 순차 위임도 가능(병렬 시 4 에이전트). PM 재량.
- **RED 작성자 분리**: Step 6 RED 테스트는 opal-test-agent(mode: red) — red-first §2 작성자≠구현자.

### C-2. 스킬 요구사항
- 단계 스킬: EXECUTE는 `op-dev-execute`(또는 opds 단축 트랙 EXECUTE). 신규 스킬 갭 없음.
- 동형 변경 4종 → 인라인 지침으로 충분 (스킬 후보 아님).

### C-3. 도구 요구사항
- CLI: `git`(2.32+, 확인), `bash`(3.2+), `tar`. 신규 설치 없음.
- PowerShell 실측 환경(`pwsh`) 가용 시 F-005 동적 검증 — 없으면 정적 검토.
- MCP: 불필요.

### C-4. 테스트 전략
- opal-test-agent: `scripts/tests/test_version_stamp.sh` RED 작성 → Step 1~5 GREEN 후 실행.
- 기능 테스트: git archive 3경로 + adopt 로직 단위 + install-mac VERSION 기록 + API stub.
- 회귀: §5.2 항목.
- 보안: 시크릿 스캔(`git diff` grep 토큰 패턴), `.gitignore` 영향 확인.

---

## 8. 기술 컨텍스트

### 8.1 기술 스택
| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| 설치기 | Bash (3.2 호환) | — (인라인 지침) |
| Windows 설치기 | PowerShell 5.1+/7 | — |
| 각인 | git export-subst / `$Format:%(describe:tags)$` (git 2.32+) | — |
| 테스트 | bash 기반 (git archive 실측) | red-first 트랙 |

### 8.2 사용 MCP
| MCP | 조회 결과 요약 |
|-----|--------------|
| (없음) | git 네이티브 메커니즘 — 외부 문서 조회 불요. export-subst 동작은 로컬 실측으로 검증 |

### 8.3 참조 문서 (설계 결정 근거)
| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | install.sh | `scripts/install.sh:69-118, 282-298, 342-360` | resolve_default_version·추출·main 흐름 |
| D-2 | 소스 | install-mac.sh | `scripts/install-mac.sh:1222-1231, 1763-1766` | VERSION 기록 우선순위·마무리 표시 |
| D-3 | 소스 | opal-cli update | `opal/tools/opal-cli/lib/update.sh:78-131, 205-230` | 버전 결정·추출·설치기 호출 |
| D-4 | 소스 | install.ps1 | `scripts/install.ps1:60-101, 233-290` | Windows 버전 결정·추출·windows.ps1 호출 |
| D-5 | 소스 | windows.ps1 | `scripts/install/windows.ps1:99-102, 1754-1760, 1771` | `-OpalVersion` 수신·VERSION 기록 |
| D-6 | 소스 | .gitattributes | `.gitattributes:1-21` | export-ignore 규칙·export-subst 추가 지점 |
| D-7 | 소스 | release workflow | `.github/workflows/release.yml:8-32` | `git archive HEAD` 각인 적용 지점·태그 트리거 |
| D-8 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md:196-208` | 변경이력 의무·배포 경계·플랫폼 분기 격리 |
| D-9 | 외부 | git export-subst (실측) | 로컬 `git archive` scratch 데모 (PLAN 작성 중) | 태그→실태그/HEAD-after-tag→describe/작업트리→placeholder 검증 |

> [MUST] `docs/CONVENTIONS.md §배포 경계` (`docs/CONVENTIONS.md:202`): `~/.opal/` 배포 파일 직접 편집 금지 — 프로젝트 소스만 수정. 재배포는 캡틴 수행.
> [MUST] `docs/CONVENTIONS.md §플랫폼 분기 격리` (`docs/CONVENTIONS.md:206-208`): 플랫폼 차이는 install 어댑터에서만 흡수 — 각인 판별 로직은 install.sh/install.ps1(어댑터)에 위치, 공통 본문 침범 없음.
> [MUST] `docs/CONVENTIONS.md §변경이력 작성 의무` (`docs/CONVENTIONS.md:196-198`): 변경 시 일시(KST)+태스크 번호 `(048)`.

---

## 9. 리스크 및 대응 (기능-리스크 연결)
| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| H-1 | VERSION이 export-ignore에 매칭되어 archive 누락 | F-001 | P0 | `git check-attr export-ignore VERSION`=unspecified 확인(실측 완료) + TS-002 |
| H-2 | 태그 archive 치환 실패/오치환 | F-001 | P0 | 로컬 git archive 실측(완료) + TS-003/004 회귀 |
| H-3 | placeholder를 실값으로 오인 기록 | F-002~F-005 | P0 | `$Format:` 부분 매칭 판별 + 미치환 시 다음 폴백 (모든 설치기 공통) |
| H-4 | API 403 시 main 오염 재발 | F-002, F-003 | P0 | 사용자 `OPAL_VERSION=v*` 시 API 스킵 + tarball 각인 채택 / API stub 테스트(TS-022) |
| H-5 | git clone 경로 describe 폴백 깨짐 | F-004 | P1 | placeholder 채택 안 함 → `.git` 존재 시 git describe 유지 (TS-031) |
| H-6 | 루트 VERSION을 런타임이 직접 읽어 placeholder 표출 | F-001 | P2 | Step 1 완료 기준에 사용처 grep 포함 — 발견 시 별도 폴백 처리 |
| H-7 | install.ps1 추출 전 버전 결정 순서 | F-005 | P1 | 추출 후(`Invoke-PlatformInstaller`) override → `-OpalVersion` 전달 |
| H-8 | 시크릿 혼입 | 전체 | P1 | TS-051 시크릿 스캔 + 보안 체크리스트 §5.4 |

---

## 설계 피드백 (미해결 빈틈 / 대안 제안)

> TASK.md 확정 설계방향(B 방식)은 변경하지 않음. 아래는 구현 상세에 대한 제안·확인 요청.

- **D-피1 (windows.ps1 이중화 여부)**: install.ps1만 override하면 충분(권장, 범위 최소). 단 windows.ps1을 직접 호출하는 경로(예: 개발자가 windows.ps1 단독 실행)가 있다면 windows.ps1에도 `$FrameworkRoot/VERSION` 직접 읽기를 추가해야 일관. → 기본은 install.ps1만, PM이 windows.ps1 단독 호출 경로 유무 확인 후 결정.
- **D-피2 (테스트 용이성 위한 함수 추출)**: install.sh `adopt_stamped_version`·install-mac.sh `record_installed_version`을 명시적 함수로 분리하면 단위 테스트가 source 후 직접 호출 가능(red-first §4 공개 인터페이스 검증 용이). install.sh는 `main "$@"` 자동 실행 때문에 통째 source가 곤란 → 함수 분리 강력 권장. **다만 install.sh는 `main`이 항상 실행되므로**, 테스트는 (a) 함수만 정의된 lib 분리 또는 (b) `OPAL_DRY_RUN`+추출 디렉토리 mock 통합 테스트 중 택1. 최소안: install-mac.sh의 `record_installed_version` 함수 분리만으로 핵심 로직(VERSION 기록 우선순위) 단위 검증 확보.
- **D-피3 (install-mac.sh 자기완결 vs 호출자 override 중복)**: F-002~F-004가 모두 동일 각인값을 채택하므로 install.sh→OPAL_VERSION override와 install-mac.sh→FRAMEWORK_ROOT/VERSION 직접 읽기가 이중 적용됨(같은 값이라 무해). 단일화하려면 install-mac.sh만 각인 읽기를 담당하고 install.sh/update.sh override를 생략하는 안도 가능 — 그러나 install.sh의 `OPAL_VERSION`은 sha URL·UNVERIFIED 배너(`install.sh:350`)·tarball URL 재사용에도 쓰이므로, **install.sh도 override 유지**가 일관(태그 tarball을 받았으면 배너·URL도 그 태그 기준). 현 설계(이중화) 채택 권고.
- **D-피4 (release.yml `HEAD` vs 명시 태그 ref)**: 현재 `git archive HEAD`(`release.yml:30`)는 태그 push 시 HEAD==태그라 정확. 단 미래에 워크플로우가 다른 ref에서 트리거되면 describe가 어긋날 수 있음 → 방어적으로 `git archive "${GITHUB_REF_NAME}"`로 명시하는 안을 제안(선택). 본 태스크에선 무변경 + 주석 보강만 권고(범위 최소).
