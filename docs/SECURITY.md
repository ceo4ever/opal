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

### Ego Lite 선택 설치

Ego Lite 앱은 OPAL 배포물에 번들하지 않는 개인·비상업 단일 사용자 선택 공급자다. 사용자가 `r2` 설치를 명시한 경우에만 `ego-browser-tool`이 macOS CPU 아키텍처에 맞는 version 0.4.5.9 DMG를 내려받는다. 설치 전 `hdiutil verify`, 고정 SHA-256, `codesign --verify --deep --strict`, `spctl --assess`가 모두 통과해야 하며 quarantine 속성을 제거하지 않는다. 기존 앱이나 검증 실패 대상은 덮어쓰지 않는다.

브라우저 결과에는 assertion에 필요한 제한된 expected/actual과 Space id만 남긴다. 저장 비밀번호·cookie·session token을 내보내지 않으며, 인증·MFA·결제·게시·삭제·설정 변경은 사람 승인 경계로 넘긴다. 조직·상업 사용자는 Citro Enterprise 조건을 먼저 확인한다.

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
- `citrolabs/ego-browser`는 `citrolabs/ego-lite@skills/ego-browser`, MIT, commit `d01be93325c7ea59d41c2ca9f4c59b58b4be4046`으로 고정하고 설치 전 `scan-risk` SAFE를 요구한다.

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

## §8 태스크 실행 기록 보존 경계

태스크 실행 tree를 canonical 저장 위치에 게시하는 도구는 source·destination 경로 문자열의
사전 검사만으로 신뢰 경계를 확정하지 않는다.

- source root와 lock 파일은 검증된 directory fd 기준 `O_NOFOLLOW`로 열고, 실행 writer의 lock을
  획득한 동일 구간에서 완료 판정과 snapshot을 수행한다.
- destination은 allocator root부터 `openat`/directory fd와 `O_NOFOLLOW`로 각 조상을 고정하고,
  임시 디렉터리 생성·copy·최종 rename을 같은 fd 기준으로 수행한다.
- 보존 hash는 파일 순서뿐 아니라 type·path byte length·path·content byte length·content 경계를
  canonical framing으로 봉인한다. 기존 보존본의 멱등 조회·재호출도 marker를 맹신하지 않고 현재
  tree hash를 재계산한다.
- symbol link와 socket/device 같은 특수 파일은 보존 묶음에서 거부한다.

현재 적용 표면은 `oppb-runtime-tool finalize-run`이다. 이 규칙은 CWE-22·CWE-362와
OWASP A08 기준을 함께 적용한다.

---

## §9 취약점 보고

보안 취약점 발견 시 GitHub Issues를 통해 보고하거나 `ceo4ever/opal` 저장소 관리자에게 직접 연락한다.

---

## §10 Console 로컬 인증 경계 (태스크 172)

OPAL Console(`127.0.0.1:7823`)은 로컬 데몬이지만 브라우저가 중간에 있어 같은 PC의 다른 웹 페이지가 요청을 보낼 수 있다. 이 절은 그 경계를 정한다. 구조는 `docs/ARCHITECTURE.md §인증 게이트`가 소유한다.

### 위협 모델

| 위협 | 설명 |
|------|------|
| 타 사이트 요청 | 사용자가 연 다른 웹 사이트가 브라우저로 `127.0.0.1:7823`에 POST 등을 보내 Console을 조작한다(CSRF·교차 출처 요청) |
| DNS rebinding | 공격자 도메인이 로컬 주소로 재해석되어 Host가 로컬이 아닌 요청이 Console에 도달한다 |
| 무세션 접근 | 세션 없이 포트에 직접 접근해 프로젝트·설정 데이터를 읽거나 쓴다 |

### 보호 범위

- `/api/` 전체는 default-deny다. 세션 쿠키가 없으면 401 `auth_required`이며, 예외는 `POST /api/auth/exchange`와 `GET /api/auth/session` 2종뿐이다.
- 모든 경로에서 Host(호스트명 `127.0.0.1`·`localhost`·`[::1]`, 추가는 `OPAL_CONSOLE_ALLOWED_HOSTS`)를 검사해 rebinding 요청을 403 `host_not_allowed`로 거절한다.
- `/api/` 요청의 Origin은 요청 Host와 같은 출처이거나 허용 CORS origin이어야 하며, 상태 변경 메서드는 Origin이 없어도 거절한다(403 `origin_required`). 상태 변경 요청은 세션별 `X-CSRF-Token`도 일치해야 한다(403 `csrf_invalid`).
- WebSocket handshake도 Host·Origin(필수)·세션을 검사하고 실패하면 accept 전에 close 1008로 끊는다.
- 세션 쿠키는 `HttpOnly; SameSite=Strict; Path=/`, 12시간 절대 만료이며 서버 재시작 시 소멸한다. 로컬 HTTP라 `Secure`는 붙이지 않는다.
- 진입은 `opal-cli console open`이 발급하는 1회용 token(기본 60초, 상한 300초)으로만 한다. token은 URL fragment로 전달되어 서버 요청·로그·Referrer에 실리지 않고, 소비는 원자적 1회이며 실패 사유는 구별하지 않는다. 채널 디렉터리(`OPAL_HOME/run/console-entry`)는 0700·소유자·symlink 검증을 통과해야 쓴다.
- 인증 우회 스위치는 없다.

### GET 점검 결과

모든 `/api/` GET 경로(프로젝트·태스크·메모리·환경·doctor·스킬 문서·브레인 조회·설정)는 세션이 필요하다. 세션 없이 응답하는 것은 SPA 정적 파일, `/health`, FastAPI 기본 문서 표면(`/docs`·`/redoc`·`/openapi.json`)이다. `/health`는 `{status, version, auth}` 상태 마커만 싣고 프로젝트·설정·계정 정보를 싣지 않으며, 문서 표면은 라우트 스키마만 싣는다(데이터 없음). 다만 `/docs`·`/redoc`은 외부 CDN 스크립트를 Console 출처에서 로드하므로 이 두 경로의 차단은 후속 과제다(현재 E2E가 `openapi.json` 200을 표면 검증에 사용한다).

### 구형 `claude -p` Brain의 위험

구형 Brain은 로컬 `claude -p` 서브프로세스로 질의를 처리하며 다음 위험이 있다.

1. 파일 읽기 범위가 프로젝트로 제한되지 않는다.
2. 임의 Bash 명령을 실행할 수 있다.
3. 읽은 내용이 네트워크로 유출될 수 있다.

따라서 기본 꺼짐이다. 켜짐 여부는 서버 측(`console.config.json`의 `legacy_brain_enabled`)에 저장하며 JSON `true`만 켜짐으로 읽고, 키 없음·파손·업그레이드는 꺼짐이다. 사용자가 화면에서 위험 3종을 확인(`risk_acknowledged`)하고 켠 뒤에만 동작하며, 꺼진 동안 prime·query는 403 `legacy_brain_disabled`이고 `claude` 프로세스는 시작되지 않는다. 끄기는 요청이 완료된 뒤의 새 프로세스 시작을 막지만 **이미 시작된 turn은 끝까지 진행**한다(화면이 진행 중 개수를 알린다).

### 한계

- 같은 사용자 권한으로 실행되는 로컬 프로세스는 막지 못한다. token 채널·세션 쿠키·메모리를 읽을 수 있는 프로세스는 같은 신뢰 경계 안이다.
- 구형 Brain이 켜진 동안 프로젝트 밖 파일 읽기를 차단하지 않는다.

### 비밀 값 취급

진입 token·세션 쿠키 값·CSRF 값은 로그·예외·URL·테스트 증적에 남기지 않는다. 디스크에는 token의 SHA-256 이름과 만료 시각만 있고, 세션 저장소 키도 해시다. E2E 증적은 `Cookie`·`X-CSRF-Token`·`#entry=` 값을 마스킹한다. 문서와 테스트에도 실제 값 예시를 적지 않는다.
