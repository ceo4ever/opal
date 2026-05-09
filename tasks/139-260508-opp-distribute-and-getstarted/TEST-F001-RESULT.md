# F-001 통합 검증 결과 보고서 (Step 7)

> 작성일: 2026-05-09 | 작성자: opal-task-agent (op-dev-execute Step 7)
> 검증 유형: 정적 검증 전용 (syntax / grep / git diff)
> 범위: TS-001, TS-003, TS-007, TS-008, TS-010, TS-011

---

## 1. TS별 검증 결과 요약

| TS-ID | 시나리오 | 결과 | 비고 |
|-------|---------|------|------|
| TS-001 | mac one-liner 신규 설치 | **PASS** | syntax PASS + OPAL_REPO 기본값 + main "$@" 래핑 확인 |
| TS-003 | doctor 4섹션 출력 | **PASS** | syntax PASS + 4함수 정의 + exit 0/1 분기 확인 |
| TS-007 | 셸 idempotent | **PASS** | register_path_in_shell_rc() 내 grep -qF 마커 체크 + skip 로직 확인 |
| TS-008 | strip 누락 방지 | **PASS** | install_dir tools 직후 strip_deploy_md_recursive 호출 라인 확인 |
| TS-010 | install_opal() 호출 그래프 보존 | **PASS** | git diff 삭제 라인 0건 — 추가 라인만 존재 |
| TS-011 | PATH 충돌 회피 (opal-cli 명칭) | **PASS** | export PATH="$HOME/.opal/bin:$PATH" + opal-cli 명칭 일관 |

**최종 판정: F-001 통합 검증 ALL PASS**

---

## 2. TS별 상세 검증 근거

### TS-001: mac one-liner 신규 설치

**검증 방법**: `bash -n scripts/install.sh` + grep 패턴 확인

| 검사 항목 | 결과 | 근거 |
|----------|------|------|
| bash -n syntax | PASS | exit 0 |
| OPAL_REPO 기본값 = ceo4ever/opal | PASS | `install.sh:46` `OPAL_REPO="${OPAL_REPO:-ceo4ever/opal}"` |
| [MUST] D2 인용 주석 | PASS | `install.sh:16` `# OPAL_REPO GitHub 저장소 (기본: ceo4ever/opal)   [MUST] D2` |
| main "$@" 래핑 | PASS | `install.sh:287` `main "$@"` 존재 |
| 설명 주석 (이 파일 전체가 다운로드된 뒤 main "$@") | PASS | `install.sh:37` 주석 확인 |

### TS-003: opal-cli doctor 4섹션 출력

**검증 방법**: `bash -n` + grep 함수 정의 확인 + exit code 분기 확인

| 검사 항목 | 결과 | 근거 |
|----------|------|------|
| bash -n doctor/run.sh | PASS | exit 0 |
| bash -n doctor/lib/checks.sh | PASS | exit 0 |
| check_deps 함수 정의 | PASS | `checks.sh:39` `check_deps()` |
| check_paths 함수 정의 | PASS | `checks.sh:109` `check_paths()` |
| check_mcp 함수 정의 | PASS | `checks.sh:207` `check_mcp()` |
| check_bootstrappers 함수 정의 | PASS | `checks.sh:241` `check_bootstrappers()` |
| 4함수 순차 호출 (run.sh) | PASS | `run.sh:50-53` check_deps / check_paths / check_mcp / check_bootstrappers |
| exit 1 (FAIL_COUNT > 0) | PASS | `run.sh:74-75` `if [[ "$FAIL_COUNT" -gt 0 ]]; then exit 1` |
| exit 0 (Pass/Warn only) | PASS | `run.sh:78` `exit 0` |

### TS-007: 셸 idempotent

**검증 방법**: `install-mac.sh` 내 `register_path_in_shell_rc` 함수 코드 분석

| 검사 항목 | 결과 | 근거 |
|----------|------|------|
| register_path_in_shell_rc 함수 존재 | PASS | `install-mac.sh:659` |
| rc 파일 3종 대상 (zshrc/bashrc/profile) | PASS | `install-mac.sh:663` `rc_files=("$USER_HOME/.zshrc" "$USER_HOME/.bashrc" "$USER_HOME/.profile")` |
| grep -qF 마커 체크 | PASS | `install-mac.sh:668` `if grep -qF "$marker" "$rc"; then` |
| 마커 존재 시 skip (continue) | PASS | `install-mac.sh:669-670` `success "PATH 이미 등록됨: $rc"` + `continue` |
| 마커 = "# === OPAL PATH ===" | PASS | `install-mac.sh:661` `local marker="# === OPAL PATH ==="` |
| fish 사용자 안내 메시지 | PASS | `install-mac.sh:677-679` fish 설치 시 info 출력 |

### TS-008: strip 누락 방지

**검증 방법**: grep으로 `install_dir "$opal_dir/tools"` 직후 `strip_deploy_md_recursive` 호출 확인

| 검사 항목 | 결과 | 근거 |
|----------|------|------|
| install_dir tools 라인 | PASS | `install-mac.sh:766` `install_dir "$opal_dir/tools" "$opal_home/tools" "OPAL 도구"` |
| 직후 strip_deploy_md_recursive 호출 | PASS | `install-mac.sh:767` `strip_deploy_md_recursive "$opal_home/tools"` |
| 기존 skills/agents/references strip도 보존 | PASS | `:723` skills, `:755` agents, `:946` ref_dst — 모두 유지 |

### TS-010: install_opal() 호출 그래프 보존

**검증 방법**: `git diff HEAD scripts/install-mac.sh` — 삭제 라인 분석

| 검사 항목 | 결과 | 근거 |
|----------|------|------|
| 삭제 라인 (`-` prefix) 총계 | PASS | **0건** — git diff에서 삭제 라인 없음 |
| 추가 라인만 존재 | PASS | 4개 블록 추가: (1) 변경이력 주석 1줄, (2) install_opal_bin 함수 + register_path_in_shell_rc 함수 53줄, (3) strip_deploy_md_recursive tools 호출 1줄, (4) install_opal_bin 호출 3줄 |
| 기존 함수 호출 순서 유지 | PASS | 추가 위치는 기존 호출 사이 삽입이 아닌 말미(`:803` 직전)와 도구 배포 직후 — 기존 순서 변경 없음 |

**git diff 요약**:
```
-0건  (삭제 라인 없음)
+58줄 (추가만)
  - v1.4 변경이력 주석 (헤더)
  - install_opal_bin() 함수 신설 (L633~L657)
  - register_path_in_shell_rc() 함수 신설 (L658~L681)
  - strip_deploy_md_recursive "$opal_home/tools" 호출 추가 (L767)
  - install_opal_bin 호출 블록 추가 (L848~L852)
```

### TS-011: PATH 충돌 회피 (opal-cli 명칭)

**검증 방법**: grep으로 PATH export 형식 + opal-cli 명칭 일관성 확인

| 검사 항목 | 결과 | 근거 |
|----------|------|------|
| export PATH 형식 | PASS | `install-mac.sh:664` `local export_line='export PATH="$HOME/.opal/bin:$PATH"'` |
| symlink 대상 = opal-cli | PASS | `install-mac.sh:650` `ln -sfn "$cli_target" "$bin_dir/opal-cli"` |
| opal-cli 명칭 일관성 (install-mac.sh) | PASS | 모든 참조가 `opal-cli` — `~/.opal/bin/opal` 등 비충돌 명칭 없음 |
| opal-cli 명칭 일관성 (opal-cli/run.sh) | PASS | 커맨드 예시 모두 `opal-cli` |
| opal-cli/README.md D1 명시 | PASS | `README.md:6` `> **명칭**: \`opal-cli\` (Homebrew core \`opal\` = opalrb 충돌 회피 — TASK D1)` |
| ~/.opal/bin/opal (충돌 가능 명칭) 참조 없음 | PASS | grep 결과 0건 |

---

## 3. Shellcheck 결과 요약 (Step 1~6 통합)

| 파일 | bash -n | shellcheck | 비고 |
|------|---------|------------|------|
| scripts/install.sh | PASS (exit 0) | PASS (exit 0, 경고 없음) | - |
| scripts/install-mac.sh | PASS (exit 0) | PASS (exit 0, SC2088×5·SC2115×1·SC2010×3 warning — 신규 함수 외 기존 경고) | 신규 추가 함수에서 발생한 경고 없음 |
| opal/tools/doctor/run.sh | PASS (exit 0) | PASS (exit 0, SC1091 info — source 경로 미지정) | SC1091은 info 수준 |
| opal/tools/doctor/lib/checks.sh | PASS (exit 0) | PASS (exit 0) | - |
| opal/tools/opal-cli/run.sh | PASS | PASS (exit 0) | - |
| opal/tools/opal-cli/lib/*.sh (5종) | PASS | PASS (exit 0) | - |

> shellcheck SC2088 (Tilde in quotes)·SC2115 (Use "${var:?}")·SC2010 (ls|grep) warning은 install-mac.sh 기존 코드에서 유래. 신규 추가된 `install_opal_bin()`·`register_path_in_shell_rc()` 함수에서 추가 경고 없음.

---

## 4. 추가 검증 결과

### 4.1 변경이력 (139) 일관성

| 파일 | (139) 행 존재 | 형식 | 비고 |
|------|-------------|------|------|
| scripts/install.sh | PASS | `v1.0 2026-05-09 10:00: 신규 작성 ... (139)` | — |
| scripts/install-mac.sh | **주의** | `v1.4 2026-05-08 KST: ... — task 139` | 기존 파일 형식이 `— task NNN` 혼용. 다른 엔트리도 `(133)` 형식과 `task 133` 혼용하므로 파일 내 불일치이나, 파일 자체에 139 참조는 존재 |
| scripts/install/macos.sh | PASS | `v1.0 2026-05-08 15:00: ... (139)` | — |
| scripts/install.ps1 | PASS | `v1.0 2026-05-09 12:00 ... (139)` | — |
| opal/tools/opal-cli/run.sh | PASS | `v1.0 2026-05-08 11:00 초기 구현 ... (139)` | — |
| opal/tools/opal-cli/lib/install.sh | PASS | `v1.0 2026-05-08 11:00 ... (139)` | — |
| opal/tools/opal-cli/lib/update.sh | PASS | `v1.0 2026-05-08 11:00 ... (139)` | — |
| opal/tools/opal-cli/lib/doctor.sh | PASS | `v1.0 2026-05-08 11:00 ... (139)` | — |
| opal/tools/opal-cli/lib/uninstall.sh | PASS | `v1.0 2026-05-08 11:00 ... (139)` | — |
| opal/tools/opal-cli/lib/mcp.sh | PASS | `v1.0 2026-05-08 11:00 ... (139)` | — |
| opal/tools/opal-cli/README.md | PASS | `v1.0 ... (139)` 변경이력 표 | — |
| opal/tools/doctor/run.sh | PASS | `v1.0 2026-05-08 KST 초기 구현 ... (139)` | — |
| opal/tools/doctor/lib/checks.sh | PASS | `v1.0 2026-05-08 KST 초기 구현 ... (139)` | — |
| opal/tools/doctor/README.md | PASS | `v1.0 2026-05-08 KST ... (139)` 변경이력 표 | — |
| scripts/install/windows.ps1 | PASS | `v1.0 2026-05-09 12:00 ... (139)` | — |

**판정**: 모든 신규/수정 파일에 (139) 또는 task 139 참조 존재. `install-mac.sh`의 `task 139` 표기는 CONVENTIONS 엄격 위반은 아니나 `(139)` 형식으로 통일 권장 (기존 파일 내 혼용 패턴 선례 있음).

### 4.2 opal-cli 명칭 일관성 (D1 결정 준수)

`~/.opal/bin/opal` (명칭 충돌 가능 문자열) 참조: **0건**

모든 코드·주석·문서에서 `opal-cli` 명칭 일관 사용 확인.

### 4.3 D2 URL 일관성

`{REPO_URL}` 잔존: **0건** (scripts/·opal/ 디렉토리 전체 grep 결과)

`ceo4ever/opal` 및 `https://github.com/ceo4ever/opal` 참조 정상 확인:
- `install.sh:46` OPAL_REPO 기본값
- `install.sh:10` 주석 URL
- `opal-cli/README.md:7` D2 명시
- `opal-cli/lib/install.sh:55` git clone 안내
- `opal-cli/lib/update.sh:55` OPAL_REPO 기본값

---

## 5. F-001 통합 검증 결론

**모든 TS PASS** — Step 7 완료 조건 충족.

| 항목 | 결과 |
|------|------|
| TS-001 | PASS |
| TS-003 | PASS |
| TS-007 | PASS |
| TS-008 | PASS |
| TS-010 | PASS |
| TS-011 | PASS |
| 변경이력 (139) 일관성 | PASS (주의: install-mac.sh의 `task 139` 표기) |
| opal-cli 명칭 일관성 (D1) | PASS |
| D2 URL 일관성 ({REPO_URL} 잔존 0건) | PASS |

**재작업 필요 Step: 없음**

> 주의 사항: `scripts/install-mac.sh:11`의 `— task 139` 표기가 다른 파일의 `(139)` 형식과 다름. 기능·동작에는 영향 없으나, 향후 git grep `'(139)'` 스캔에서 install-mac.sh가 누락될 수 있음. Step 3 재작업 불필요 — PM 확인 후 v1.4 라인을 `(139)` 형식으로 선택적 수정 가능.
