# QA: EXECUTE — OPAL 보안 강화 (SECURITY.md 신설 + High 4 + Medium 핵심 fix)

> 검토일: 2026-05-10 | 판정: Pass (with minor)

---

## 1. 요약

태스크 144 EXECUTE 단계에서 15개 파일(신규 1 + 수정 14)에 보안 강화가 적용되었다. SECURITY.md 8개 섹션 신설, install 무결성(sha256sums.txt 부재 시 prompt/거부), MCP spawn 화이트리스트(npx/npm/node/python3), third-party fetch 신뢰 모델(registry v2.1 + Unknown 라이선스 두 번째 확인), ReDoS 방어(isUnsafeRegex 휴리스틱), OPAL_HOME 가드, MCP `@latest` 핀, playwright /tmp 경로 변경이 모두 구현되었다. Step 16(mac+Windows 회귀 실환경 검증)은 캡틴 환경 의존으로 정상 미완료 상태이며, 2건의 경미한 Warning이 발견되었으나 정상 운영에 영향 없다.

---

## 2. 검증 결과

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| GE-1 | 체크리스트 완료 | Warning | Step 16 회귀 검증 `[ ]` — 캡틴 실환경 의존 (정상 미완료) |
| GE-2 | 산출물 존재 | Pass | 15개 파일 모두 확인됨 |
| GE-3 | TASK 충족 | Pass | R-1~R-8 모두 구현 완료, R-9(회귀)는 Step 16 의존 |
| R-1a | SECURITY.md 8 섹션 작성 | Pass | §1 위협 모델 ~ §8 취약점 보고 모두 확인 |
| R-1b | GC-DP-001~005 매핑 명시 | Pass | §2(GC-DP-001/003) / §3(GC-DP-002/005) / §4(GC-DP-004) 명시 |
| R-1c | SECURITY.md Markdown 형식 | Pass | 섹션 구분, 표, 코드블록 정상 |
| R-2a | install.sh verify_checksum 강화 | Pass | release tag + sha256sums.txt 부재 시 비대화형 거부 + `OPAL_ALLOW_UNVERIFIED=1` 옵트인 + main UNVERIFIED banner 구현 확인 (`L229-249`) |
| R-2b | install.ps1 Verify-Checksum 강화 | Pass | `$env:OPAL_ALLOW_UNVERIFIED` / `$env:OPAL_AUTO_INSTALL` / `[Environment]::UserInteractive` 검사 구현 확인 |
| R-2c | update.sh verify_checksum 강화 | Pass | install.sh와 동등 패턴 구현 확인 (`L164-201`) |
| R-2d | 변경이력 3 파일 | Pass | install.sh v1.3 / install.ps1 v1.0.6 / update.sh v1.0.4 행 추가 확인 |
| R-3a | community-skills-registry.json v2.1 | Pass | `$schema: opal-community-skills-registry-v2.1` / `version: 2.1.0` / `schema_notes`에 (144) 명시 확인 |
| R-3b | anthropics 18건 commit_sha: null 추가 | Pass | 18건 모두 `commit_sha: null` 필드 추가 확인 |
| R-3c | opal-skill-manager Unknown 라이선스 두 번째 확인 | Pass | §6에 Unknown 분기 + 두 번째 확인(영문+한글 병기) + commit_sha 노출 구현, v1.2 변경이력 추가 |
| R-4a | install-mac.sh install_mcp_cli 화이트리스트 | Pass | `npx|npm|node|python3|python` 화이트리스트 구현 확인 (`L1051-1057`) |
| R-4b | windows.ps1 Install-OpalMcp 화이트리스트 | Pass | `$allowedCmds` 배열 + `.cmd` 확장자 제거 후 검증 구현 확인 (`L1104-1113`) |
| R-4c | mcp.sh _mcp_add 화이트리스트 | Pass | `basename` 후 case 검증 구현 확인 (`L146-152`) |
| R-4d | fork repo banner (install-mac.sh) | Pass | `OPAL_REPO != ceo4ever/opal` 시 banner + 비대화형 거부 + `OPAL_ALLOW_FORK=1` 옵트인 구현 확인 (`L1081-1103`) |
| R-4e | fork repo banner (windows.ps1) | Pass | 동등 동작 구현 확인 (`L1060-1081`) |
| R-5a | isUnsafeRegex() 함수 신설 | Pass | `MAX_PATTERN_LENGTH=100` / `MAX_DOTSTAR_COUNT=2` (>2 reject) / nested quantifier 검출 구현 확인 |
| R-5b | react-components 거짓양성 방지 | Pass | 패턴 `(stitch.*react\|react\s*component.*stitch)` — dotStar count=2, 임계값 `>2` 조건으로 통과 (실측 검증: dotStarCount=2, unsafe=false) |
| R-5c | matchByTriggers 입력 256자 제한 | Pass | `L130` 입력 길이 제한 구현 확인 |
| R-5d | resolveFirstPath path.resolve + homedir 검증 | Pass | `~` → homedir expand + `path.resolve` + homedir/cwd 하위 아니면 skip 구현 확인 |
| R-5e | validate v2/v2.1 양쪽 인식 | Pass | `L302-303` `isV2Community` 조건 v2 + v2.1 모두 인식 확인 |
| R-5f | 변경이력 skill-registry.js | Pass | `v1.1 2026-05-10 21:00 KST` 변경이력 행 추가 확인 |
| R-6a | shadcn.json `@^4.7` 핀 | Pass | `"shadcn@^4.7"` 확인 |
| R-6b | playwright.json `@^0.0.75` 핀 | Pass | `"@playwright/mcp@^0.0.75"` 확인 |
| R-6c | context7.json `@^2.2` 핀 | Pass | `"@upstash/context7-mcp@^2.2"` 확인 |
| R-6d | sequential-thinking.json `@^2025.12` 핀 | Pass | `"@modelcontextprotocol/server-sequential-thinking@^2025.12"` 확인 |
| R-7a | playwright.json output-dir 변경 | Pass | `/tmp/playwright-mcp` → `~/.opal/cache/playwright-mcp` 확인 |
| R-7b | install-mac.sh 0700 mkdir 보장 | Pass | `mkdir -p "$USER_HOME/.opal/cache/playwright-mcp"` + `chmod 700 "$USER_HOME/.opal/cache"` 구현 확인 (`L1106-1108`) |
| R-8a | uninstall.sh OPAL_HOME 가드 | Pass | `pwd -P` 정규화 + `OPAL_HOME_OVERRIDE=1` 옵트인 구현 확인 (`L51-58`) |
| R-8b | install-mac.sh clean_dirs OPAL_HOME 가드 | Pass | 동등 가드 구현 확인 (`L731-738`) |
| R-8c | windows.ps1 Remove-Item OPAL_HOME 가드 | Pass | `[IO.Path]::GetFullPath` 비교 + `OPAL_HOME_OVERRIDE` 옵트인 구현 확인 (`L405-409`) |
| CH-1 | 변경이력 install-mac.sh | Pass | `v2.1 2026-05-10 21:00 KST` 행 추가 확인 |
| CH-2 | 변경이력 windows.ps1 | Pass | `v1.7.0 2026-05-10 21:00` 행 추가 확인 |
| CH-3 | 변경이력 uninstall.sh | Pass | `v1.0.1 2026-05-10 21:00` 행 추가 확인 |
| CH-4 | 변경이력 mcp.sh | Pass | `v1.0.1 2026-05-10 21:00` 행 추가 확인 |
| CH-5 | 변경이력 4 mcps/*.json | Pass | docs/JSON config 면제 (141 v0.3.15 선례) — 면제 정당 |
| CH-6 | 변경이력 SECURITY.md | Pass | docs 면제 (141 선례) — 메타데이터(작성일+적용 버전)로 추적성 확보 |
| CH-7 | community-skills-registry.json 변경이력 갈음 | Pass | schema_notes에 "v2.1 (144)" 태스크 번호 명시 — P-D-9 결정 준수 |
| W-1 | install.ps1 `[Environment]::UserInteractive` CLM 위험 | Warning | Constrained Language Mode 환경에서 throw 가능성. try/catch 미래용 보호 고려 권장 (캡틴 CLOSE 전 판단) |
| W-2 | validate communitySchema 표시 불일치 가능성 | Warning | 배포 환경(v2) vs 소스(v2.1) 불일치 — install 재실행 후 자동 해소 (정상 워크플로우) |

---

## 3. 지적 사항

### Warning W-1: install.ps1 `[Environment]::UserInteractive` CLM(Constrained Language Mode) 위험

**위치**: `scripts/install.ps1` `Verify-Checksum` 함수 L196

```powershell
$isNonInteractive = ($env:OPAL_AUTO_INSTALL -eq '1') -or (-not [Environment]::UserInteractive)
```

**내용**: PLAN.md §5 R-9에서 이미 식별된 잔존 리스크. PowerShell Constrained Language Mode(CLM) 환경에서 `[Environment]::UserInteractive` 접근이 제한될 경우 예외 발생 가능성이 있다. 현재 try/catch 보호가 없어 예외 시 스크립트 중단 가능성이 존재한다.

**영향**: CLM이 활성화된 Windows 정책 환경에서 install 실패 가능성. 일반 사용자 환경(CLM 미적용)에서는 영향 없음.

**권장**: CLOSE 진입 전 캡틴 판단 — try/catch 보호를 추가하여 CLM 환경에서도 폴백(비대화형 간주)으로 안전하게 처리하는 방안 검토. 단, 현재 PLAN §5 R-9에서 "try/catch 보호 + 폴백 — 검출 실패 시 비대화형으로 간주(보수적)"라고 이미 대응 방향이 명시되어 있으므로 후속 태스크 처리도 가능.

**심각도**: Warning — 일반 환경 무영향, CLM 특수 환경에서만 발현.

### Warning W-2: validate communitySchema 표시 불일치 (deploy v2 vs source v2.1)

**내용**: 현재 `~/.opal/references/community-skills-registry.json`이 배포 환경에 v2로 잔존할 경우, `skill-registry.js validate`의 `communitySchema` 출력이 "opal-community-skills-registry-v2"로 표시될 수 있다. install 재실행 후 v2.1 파일이 배포되면 자동 해소된다.

**영향**: validate 출력의 communitySchema 필드가 배포 환경과 소스 환경에서 다르게 보일 수 있으나 기능적 문제 없음.

**심각도**: Info — CLOSE 전 install 재실행(캡틴 Step 16)으로 자동 해소.

### 심각도 분류

- Critical: 없음
- Warning: 2건 (W-1 CLM 위험, W-2 communitySchema 불일치 — 모두 캡틴 실환경 검증에서 확인 가능)
- Info: 없음

---

## 4. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK.md R-1 | SECURITY.md 8 섹션 (워커 보고 8개, TASK.md에는 6개 명시 — §7 OPAL_HOME 가드 + §8 취약점 보고 추가됨) | Pass |
| TASK.md R-2 | install 3 파일 무결성 강화 AC 모두 충족 | Pass |
| TASK.md R-3 | community-skills-registry.json v2.1 + opal-skill-manager Unknown 두 번째 확인 | Pass |
| TASK.md R-4 | 3 파일 화이트리스트 + fork banner | Pass |
| TASK.md R-5 | isUnsafeRegex >2 임계값 (W-1 캡틴 결정 반영), 입력 256자, validate v2.1 | Pass |
| TASK.md R-6 | 4개 MCP 마이너 핀 | Pass |
| TASK.md R-7 | playwright.json 경로 + install-mac.sh 0700 mkdir | Pass |
| TASK.md R-8 | 3 위치 OPAL_HOME 가드 + OPAL_HOME_OVERRIDE=1 옵트인 | Pass |
| TASK.md R-9 | Step 16 캡틴 실환경 의존 — 정상 미완료 | Warning |
| TASK.md 제약 조건 | 변경이력 의무 파일(8개) 모두 행 추가 / 면제(6개) 선례 준수 | Pass |
| PLAN.md §7 P-D-7 | MAX_DOTSTAR_COUNT=2 (>2 reject), react-components 패턴 통과 | Pass |
| PLAN.md §5 R-9 | install.ps1 CLM 위험 try/catch 미보호 — 잔존 리스크로 W-1 등록 | Warning |
| PLAN.md §2 거짓양성 분석 | react-components `.*` 2회 → 임계값 `>2` 미만으로 통과 확인 (실측) | Pass |
| 142 정합 | skill-registry.js validate가 v2 + v2.1 모두 인식 (isV2Community 조건) | Pass |

---

## 5. 판정

**Pass (with minor)**

R-1~R-8 모든 요구사항이 구현되었고, 15개 파일 변경이 PLAN.md 설계와 정합하며 변경이력 의무를 준수한다. react-components 패턴의 거짓양성 방지(MAX_DOTSTAR_COUNT>2) 실측 검증 완료. Step 16 회귀 검증은 캡틴 환경 의존으로 정상 미완료 상태이며, Warning 2건(CLM 위험 + communitySchema 불일치)은 모두 경미하여 CLOSE 진행에 영향 없다.

---

## 부록: 잔존 리스크 3건 최종 상태

| # | 리스크 | 상태 |
|---|--------|------|
| 1 | Step 16 캡틴 실환경 검증 | 정상 미완료 — CLOSE 진입 전 캡틴 수행 |
| 2 | install.ps1 `[Environment]::UserInteractive` CLM 위험 | Warning 등록 — 후속 태스크 또는 캡틴 판단 |
| 3 | validate communitySchema 불일치 (deploy v2 vs source v2.1) | install 재실행 후 자동 해소 — CLOSE 전 Step 16에서 확인 |
