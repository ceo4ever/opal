# DONE: OPAL 보안 강화 — SECURITY.md 신설 + High 4 + Medium 일부 fix

> 시작: 2026-05-10 20:23 | 완료: 2026-05-10 23:20 | 모드: semi-agentic | 적용 스킬: opp

## 작업 결과

OPAL v0.4.0 보안 진단(opal-security-checker, 14건 발견)에 따라 **High 4건 + Medium 핵심 3건 + SECURITY.md 신설**을 본 태스크에서 처리. 오픈소스 공개 프레임워크로서 install·MCP·third-party fetch 흐름의 신뢰 모델을 명문화·강화하고, 향후 GC 검증의 baseline을 확립.

## 캡틴 결정 SSOT

| ID | 결정 |
|----|------|
| §1~§10 | TASK.md §확정된 설계 방향 (범위 / SECURITY.md SSOT / install 무결성 / fetch 신뢰 / MCP spawn / ReDoS / Medium 핵심 / 후속 분리 / mac+Windows 동등 / 회귀 검증) |
| W-1 | ReDoS 임계값 `MAX_DOTSTAR_COUNT > 2` (3회 이상 reject) — 캡틴 결정 (react-components 거짓양성 방지) |
| P-D-9 | community-skills-registry.json 변경이력 = `schema_notes` (144) 갈음 |
| P-D-10 | fork banner 비대화형 옵트인 `OPAL_ALLOW_FORK=1` |
| P-D-11 | anthropics 18건 `commit_sha: null` 명시 추가 (실제 SHA 후속) |

## 최종 변경 파일 (신규 1 + 수정 14 = 15)

### 신규

| # | 경로 | 내용 |
|---|------|------|
| N-1 | `docs/SECURITY.md` | 8 섹션 보안 모델 SSOT (위협 모델 / install 무결성 / MCP 신뢰 / fetch 신뢰 / 의존성 핀 / ReDoS 방어 / 운영 정책 / 취약점 보고). GC-DP-001~005 매핑 |

### 수정

| # | 경로 | 변경 |
|---|------|------|
| M-1 | `opal/core/mcps/shadcn.json` | `shadcn@latest` → `shadcn@^4.7` (P-D-4) |
| M-2 | `opal/core/mcps/playwright.json` | `@playwright/mcp@latest` → `@^0.0.75` + output-dir `/tmp/playwright-mcp` → `~/.opal/cache/playwright-mcp` (P-D-4 + R-7) |
| M-3 | `opal/core/mcps/context7.json` | `@upstash/context7-mcp@latest` → `@^2.2` (P-D-4) |
| M-4 | `opal/core/mcps/sequential-thinking.json` | 버전 미고정 → `@^2025.12` (P-D-4) |
| M-5 | `opal/core/references/community-skills-registry.json` | v2 → **v2.1** schema bump + anthropics 18건 `commit_sha: null` + schema_notes (144) 갈음 (P-D-9 / P-D-11) |
| M-6 | `opal/skills/opal-skill-manager/SKILL.md` v1.2 | §6 동의 prompt — Unknown 라이선스 두 번째 확인 + commit_sha 노출 |
| M-7 | `opal/tools/skill-registry/skill-registry.js` v1.1 | `isUnsafeRegex()` 신설 (MAX_PATTERN_LENGTH=100 / MAX_DOTSTAR > 2 / nested quantifier) + matchByTriggers 입력 256자 제한 + resolveFirstPath path.resolve homedir + validate v2/v2.1 양쪽 인식 |
| M-8 | `opal/tools/opal-cli/lib/uninstall.sh` v1.0.1 | `rm -rf "$opal_home"` 직전 OPAL_HOME 가드 + `OPAL_HOME_OVERRIDE=1` 옵트인 |
| M-9 | `opal/tools/opal-cli/lib/mcp.sh` v1.0.1 | `_mcp_add` command 화이트리스트 검증 |
| M-10 | `opal/tools/opal-cli/lib/update.sh` v1.0.4 | release tag + sha256sums.txt 부재 시 prompt/거부 + main UNVERIFIED banner |
| M-11 | `scripts/install-mac.sh` v2.1 | OPAL_HOME 가드 + install_mcp_cli/install_mcp command 화이트리스트 + fork banner + playwright cache mkdir 0700 |
| M-12 | `scripts/install/windows.ps1` v1.7.0 | Install-OpalCore OPAL_HOME 가드 + Install-OpalMcp fork banner + command 화이트리스트 |
| M-13 | `scripts/install.sh` v1.3 | verify_checksum 강화 — release tag + sha256sums.txt 부재 시 prompt/거부 + main UNVERIFIED banner |
| M-14 | `scripts/install.ps1` v1.0.6 | Verify-Checksum 강화 동일 |

## 요구사항 매핑

| ID | 핵심 | 결과 |
|----|------|------|
| R-1 | SECURITY.md 신설 (6 → 8 섹션) | ✅ |
| R-2 | install 무결성 (GC-001) | ✅ 4 파일 |
| R-3 | third-party fetch 신뢰 (GC-002) | ✅ registry v2.1 + 동의 prompt 강화 |
| R-4 | MCP spawn 신뢰 (GC-003) | ✅ 3 파일 화이트리스트 + fork banner |
| R-5 | ReDoS 방어 (GC-004 + GC-013) | ✅ isUnsafeRegex + 256자 + path.resolve |
| R-6 | MCP `@latest` 핀 (GC-006) | ✅ 4 mcps/*.json |
| R-7 | `/tmp` 경로 (GC-007) | ✅ playwright `~/.opal/cache/` |
| R-8 | OPAL_HOME 가드 (GC-010) | ✅ 3 위치 + 옵트인 |
| R-9 | 회귀 검증 | ✅ mac 캡틴 검증 통과 / Windows는 push 후 |

## QA / 게이트 결과

- **PLAN QA**: pass_with_minor (W-1 ReDoS 임계값 거짓양성 분석 오류 → 캡틴 결정 `> 2`로 완화 / W-2 Step 카운트 오타)
- **EXECUTE QA**: pass_with_minor (Warning 2건 경미 — install.ps1 CLM `[Environment]::UserInteractive` try/catch 미보호 / validate communitySchema 표시 deploy v2 vs source v2.1 — install 재실행 후 자동 해소)
- **PM Gate**: TASK R-1~R-9 + 캡틴 결정 SSOT 모두 충족, 변경이력 8 파일 완비, react-components 거짓양성 방지 실측 검증 통과
- **mac 회귀 검증**: 캡틴 직접 검증 통과 (2026-05-10 23:20)

## 알려진 미해결 / 후속 분리

| ID | 내용 | 분리 대상 |
|----|------|----------|
| **Windows 회귀** | install.ps1 재실행 + match `//pdf` + doctor + OPAL_HOME 가드 검증 | push 후 별도 추가작업 |
| **install.ps1 CLM 보호** | `[Environment]::UserInteractive` try/catch 추가 | P1 별도 |
| **commit_sha 실 SHA 채우기** | anthropics 18건은 `null`로만 명시 — 실제 GitHub SHA 조회 후 채우기 | 별도 태스크 (외부 조회 + 정기 업데이트) |
| **GC-005** requirements.lock | pip-compile 도입 | 별도 태스크 |
| **GC-008** hooks/MCP JSON Schema 검증 | ajv 도입 | 별도 태스크 |
| **GC-009** chmod 일관성 / **GC-011** winget prompt / **GC-012** echo -e → printf | 일관성·UX 영역 | P1 |
| **release.yml 자동 publish 미동작** | v0.3.7~v0.4.0 release 자산 0 — 워크플로우 권한/실행 진단 | 별도 태스크 |
| **143 push** | f43e56a local만 있음 | 144 commit과 함께 push 검토 |

## STATE 최종

| Phase | 행 수 | 상태 |
|-------|------|------|
| TASK | 1~3 | ✅ (사용자 확인 owner=user) |
| PLAN | 4~11 | ✅ (사용자 확인 owner=user) |
| EXECUTE | 12~18 | ✅ (사용자 확인 owner=user, mac 회귀 통과) |
| CLOSE | 19~20 | 진행 중 (DONE.md 생성 → State Gate) |

## 후속 액션

1. **즉시**: 캡틴 명시 시 commit + push (143 + 144 묶음 또는 별도)
2. **push 후**: Windows 환경 회귀 검증
3. **Release**: 144는 보안 강화 minor bump → **v0.5.0** 권장 (143 응답 표준 + 144 보안을 한 release로 광고). release.yml 자동 publish가 안 되므로 `gh release create` 또는 GitHub 웹 UI publish 필요
4. **별도 태스크**: 위 후속 분리 항목들
