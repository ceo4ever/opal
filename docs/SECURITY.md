# OPAL 보안 모델

> 작성일: 2026-05-10 | 적용 버전: v0.4.x+
> 목적: OPAL 프레임워크의 보안 baseline 명문화 — opal-pilot-gc 비교 baseline + 사용자 신뢰 모델 SSOT

---

## §1 위협 모델

OPAL은 공개 OSS 프레임워크로 다음 위협 표면을 갖는다.

| 위협 표면 | 설명 |
|----------|------|
| curl-pipe-bash 신뢰 모델 | `curl | bash` 설치 패턴 — 다운로드 무결성 검증 필요 |
| fork 가능성 | GitHub fork로 배포되는 변형 OPAL — MCP / 스킬 내용 검토 불가 |
| third-party skill supply chain | 커뮤니티 스킬(vercel-labs/skills 등)의 외부 소스 코드 |
| MCP spawn | npx 등 외부 프로세스를 MCP 서버로 등록 — command injection 가능성 |

적용 표준:

- **OWASP Top 10 (2021)**: A05 Security Misconfiguration / A06 Vulnerable and Outdated Components / A08 Software and Data Integrity Failures
- **CWE Top 25**: CWE-22 (Path Traversal) / CWE-78 (OS Command Injection) / CWE-94 (Code Injection) / CWE-377 (Insecure Temporary File) / CWE-829 (Inclusion of Functionality from Untrusted Control Sphere) / CWE-1333 (ReDoS)

---

## §2 install 무결성 (GC-DP-001/003)

**적용 파일**: `scripts/install.sh` / `scripts/install.ps1` / `opal/tools/opal-cli/lib/update.sh`

### 흐름 결정 (PLAN Step 12-14)

| 시나리오 | 동작 |
|---------|------|
| release tag(v*) + sha256sums.txt 정상 | SHA-256 검증 통과 → 설치 계속 |
| release tag(v*) + sha256sums.txt 부재 + 대화형 | `[y/N]` prompt (디폴트 N) |
| release tag(v*) + sha256sums.txt 부재 + 비대화형 | 기본 **거부** — `OPAL_ALLOW_UNVERIFIED=1` 옵트인 시 통과 |
| main 브랜치 / 비release 버전 | UNVERIFIED banner 출력 + 설치 계속 (sha256 검증 skip) |

### 옵트인 환경 변수

- `OPAL_ALLOW_UNVERIFIED=1` — sha256sums.txt 부재 시 검증 없이 강제 진행 (CI/test 전용)
- `OPAL_AUTO_INSTALL=1` — 비대화형 모드 강제 (curl|bash one-liner에서 자동 발동)

### 기존 사용자 호환성

ceo4ever/opal의 공식 release tag(v*)에서 설치하는 정상 사용자는 sha256sums.txt가 CI에 의해 자동 생성되므로 새 prompt/거부 동작이 발동하지 않는다.

---

## §3 MCP 등록 신뢰 경계 (GC-DP-002/005)

**적용 파일**: `scripts/install-mac.sh` / `scripts/install/windows.ps1` / `opal/tools/opal-cli/lib/mcp.sh`

### command 화이트리스트

MCP 서버 등록 시 `command` 필드는 다음 허용 목록에 포함된 실행 파일만 허용한다 (basename 비교):

| 허용 command | 용도 |
|-------------|------|
| `npx` | Node.js 패키지 실행 |
| `npm` | Node.js 패키지 관리자 |
| `node` | Node.js 직접 실행 |
| `python3` | Python 3 실행 |
| `python` | Python 실행 (Windows 호환) |

허용 목록 외 command는 즉시 **reject** 된다 (exit 1 / throw).

### fork repo banner (P-D-2, P-D-10)

`OPAL_REPO != ceo4ever/opal` 환경에서 install 시 경고 banner가 표시된다:

```
════════════════════════════════════════════════════════
  [FORK INSTALL] OPAL_REPO=<fork-repo>
  이 설치본은 OPAL 공식 저장소(ceo4ever/opal)가 아닙니다.
  MCP 서버 등록 항목을 직접 검토하세요.
════════════════════════════════════════════════════════
```

- 대화형: `[y/N]` 동의 확인
- 비대화형: 기본 거부 → `OPAL_ALLOW_FORK=1` 옵트인 시 통과

### 의존성 핀 (PLAN Step 1-4)

신규 MCP 등록 정책: `version_pinned: "^x.y"` 마이너 핀 의무.

현재 등록된 4개 MCP (PLAN Step 1-4에서 핀 적용, v0.4.x+):

| MCP | 버전 핀 | 비고 |
|-----|--------|------|
| shadcn | `shadcn@^4.7` | npm shadcn@4.7.0 기준 |
| @playwright/mcp | `@playwright/mcp@^0.0.75` | npm @playwright/mcp@0.0.75 기준 |
| @upstash/context7-mcp | `@upstash/context7-mcp@^2.2` | npm @upstash/context7-mcp@2.2.4 기준 |
| @modelcontextprotocol/server-sequential-thinking | `@^2025.12` | 캘린더 버전 핀 |

MCP 핀은 분기마다 갱신을 권장한다 (후속 별도 태스크에서 자동화 예정).

### playwright output-dir (PLAN Step 2)

playwright MCP의 `--output-dir`를 `/tmp/playwright-mcp`(임시, 재부팅 시 소멸)에서 `~/.opal/cache/playwright-mcp`(영구)로 변경. install이 디렉토리를 0700 권한으로 사전 생성한다.

---

## §4 third-party 스킬 fetch (GC-DP-004)

**적용 파일**: `opal/core/references/community-skills-registry.json` / `opal/skills/opal-skill-manager/SKILL.md`

### registry v2.1 (PLAN Step 5)

- `$schema: opal-community-skills-registry-v2.1`
- `commit_sha` 옵션 필드 신설 — 검증 가능한 스킬만 채움
- v2 호환 유지 (`commit_sha` 미작성 시 `null`로 간주)

### 동의 prompt 강화 (PLAN Step 6)

`//커맨드` 미설치 스킬 매칭 시 표시되는 동의 prompt (opal-skill-manager §6):

```
이 스킬은 외부 스킬입니다.
- 출처: {source_repo}
- 라이선스: {license}  [Unknown 시 ⚠️ 경고 추가]
- commit SHA: {commit_sha || "미고정 (HEAD 가변)"}

다운로드해서 설치할까요? (Y/n)
```

`license: "Unknown"` 항목은 **두 번째 확인** 필수 (디폴트 N):

```
라이선스가 확인되지 않은 스킬입니다. 정말로 설치하시겠습니까?
This skill has an unverified license. Are you sure you want to install? (y/N)
```

### Unknown 라이선스 현황

다음 12개 항목이 `license: "Unknown"` 상태 (별도 후속 태스크에서 라이선스 확인 예정):

- google-labs-code 5개 (design-md / enhance-prompt / react-components / remotion / stitch-loop) — `source_repo: null`
- vercel-labs 5개 (react-best-practices / web-design-guidelines / composition-patterns / next-best-practices / shadcn)
- trailofbits 1개 (modern-python) — `source_repo: null`
- getsentry 1개 (code-review) — `source_repo: null`

`source_repo: null` 항목은 vercel-labs/skills 카탈로그 미등재로 수동 설치만 가능.

---

## §5 의존성 핀

### MCP 의존성

§3 참조. `@latest` 사용 금지 — 마이너 핀(`^x.y`) 의무.

### Python 패키지

`opal/tools/requirements.txt` — `pip-compile`로 lock 생성 (별도 후속 태스크 GC-005).

---

## §6 ReDoS 방어 (GC-004)

**적용 파일**: `opal/tools/skill-registry/skill-registry.js`

### 휴리스틱 임계값 (PLAN Step 7, W-1 결정)

| 항목 | 임계값 | 동작 |
|-----|--------|------|
| `MAX_PATTERN_LENGTH` | 100자 | 패턴 길이 초과 시 reject |
| `MAX_DOTSTAR_COUNT` | > 2 (3회 이상) | `.* / .+` 3회 이상 시 reject |
| nested quantifier | `(xxx[+*])[+*]` 패턴 | 검출 시 reject |
| `MAX_INPUT_LENGTH` | 256자 | 입력 길이 초과 시 match skip |

**거짓양성 분석**: 현재 등록된 모든 community 스킬 trigger 패턴은 위 임계값을 통과한다 (`.* / .+` 최대 2회, 길이 최대 50자). `google-labs-code/react-components`의 `(?i)(stitch.*react|react\s*component.*stitch)` 패턴은 `.* 2회`로 임계값(> 2) 미만 → 통과.

### path 정규화 (GC-013, CWE-22)

`resolveFirstPath()` 함수:
- `~` → `os.homedir()` expand
- `path.resolve()` 로 정규화
- 결과가 `homedir` 또는 `cwd` 하위가 아닌 경우 skip (path traversal 방어)

---

## §7 OPAL_HOME 가드 (GC-010, R-8)

**적용 파일**: `opal/tools/opal-cli/lib/uninstall.sh` / `scripts/install-mac.sh` / `scripts/install/windows.ps1`

`OPAL_HOME` 환경 변수가 `$HOME/.opal` (기본값)와 다른 경우 삭제/설치 동작을 거부한다.

- bash: `pwd -P` 기반 정규화 경로 비교
- PowerShell: `[IO.Path]::GetFullPath()` 기반 절대 경로 비교

**옵트인**: `OPAL_HOME_OVERRIDE=1` — CI/test 환경에서 비표준 경로 허용. 운영 환경에서 사용 금지.

---

## §8 취약점 보고

보안 취약점 발견 시 GitHub Issues를 통해 보고하거나 `ceo4ever/opal` 저장소 관리자에게 직접 연락한다.
