# opal-cli — OPAL AI Framework CLI

`opal-cli`는 OPAL AI Framework를 관리하는 단일 진입점 CLI 도구다.
업데이트, 진단, 제거, MCP 관리를 서브커맨드로 제공한다.

> **명칭**: `opal-cli` (Homebrew core `opal` = opalrb 충돌 회피 — TASK D1)
> **레포**: `https://github.com/ceo4ever/opal` (TASK D2)

---

## 설치 경로

```
~/.opal/bin/opal-cli  →  ~/.opal/tools/opal-cli/run.sh (symlink)
```

`install-mac.sh`가 `install_opal_bin()` 을 통해 symlink를 자동 생성한다.
PATH에 `~/.opal/bin`이 등록되어야 `opal-cli` 명령이 동작한다.

---

## 서브커맨드

| 서브커맨드 | 설명 |
|-----------|------|
| `update [--to vX.Y]` | 최신(또는 지정) 버전으로 업데이트 |
| `doctor` | 환경 진단 (의존성·경로·MCP·부트스트래퍼) |
| `uninstall [--yes]` | OPAL 완전 제거 |
| `mcp <list\|add\|remove\|install-all>` | MCP 서버 관리 |
| `console <start\|stop\|status\|open\|scan\|log>` | OPAL Console 대시보드 관리 (포트 7823). `log`는 실시간 로그 팔로우(`-n N`, Ctrl+C 종료). `open`은 인증된 진입 경로이며 계약은 아래 「console open — 진입 계약」 참조 |

---

## 옵션

| 옵션 | 설명 |
|------|------|
| `--version`, `-v` | 버전 출력 |
| `--help`, `-h` | 사용법 출력 |

---

## 사용 예시

```bash
# 최신 버전으로 업데이트
opal-cli update

# 특정 버전으로 업데이트
opal-cli update --to v0.2

# 환경 진단
opal-cli doctor

# MCP 서버 목록 확인
opal-cli mcp list

# MCP 서버 추가
opal-cli mcp add context7

# 모든 MCP 서버 재설치
opal-cli mcp install-all

# OPAL 제거 (확인 프롬프트 없이)
opal-cli uninstall --yes

# 버전 확인
opal-cli --version
```

---

## update 사용자 데이터 보존 정책

`opal-cli update` 실행 시 아래 정책에 따라 사용자 데이터를 보존한다.

| 항목 | 처리 |
|------|------|
| `~/.opal/identity.md` | 보존 (덮어쓰기 금지) |
| `~/.opal/AGENT.md` | 재배포 (strip 결과로 덮어쓰기) |
| `~/.opal/projects/` | 보존 |
| `~/.opal/skills/` | 클린 후 재배포 |
| `~/.opal/agents/` | 클린 후 재배포 |
| `~/.opal/community-skills/` | 보존 (사용자 추가 vendor 유지) |
| `~/.opal/tools/` | 클린 후 재배포 |
| `~/.opal/bin/opal-cli` | symlink 재생성 |
| `~/.opal/.venv/` | 보존 + requirements.txt 재적용 |

> **주의**: 커스텀 스킬(`~/.opal/skills/`)은 업데이트 시 삭제됩니다.
> 커스텀 스킬은 `~/.opal/skills.user/`(후속 태스크 예정)에 별도 보관하세요.

---

## doctor 출력 형식

```text
[OPAL Doctor]

[1/4] Dependencies
  ✓ bash 5.2.x
  ✓ git 2.43.x
  ✓ Node.js v18.x
  ✓ Python 3.11.x

[2/4] OPAL Paths
  ✓ ~/.opal/AGENT.md
  ✓ ~/.opal/identity.md
  ✓ ~/.opal/skills/ (29 skills)
  ✓ ~/.opal/agents/ (10 agents)
  ✓ ~/.opal/bin/opal-cli  → ~/.opal/tools/opal-cli/run.sh

[3/4] MCP Registration
  ✓ Claude: context7, playwright, shadcn, sequential-thinking
  ✓ Cursor: context7, playwright (mcp.json)

[4/4] Bootstrappers
  ✓ ~/.claude/CLAUDE.md (OPAL marker)
  ✓ ~/.cursor/rules/000-opal-agent.mdc

판정: All Pass (0 warnings, 0 errors)
```

종료 코드: `0` = All Pass, `1` = Fail 또는 Warn

---

## uninstall 제거 대상

`opal-cli uninstall` 실행 시:

1. `~/.opal/` 디렉토리 전체 삭제
2. OPAL 부트스트래퍼 마커 블록 제거 (파일 자체는 보존):
   - `~/.claude/CLAUDE.md` — `# === OPAL START ===` ~ `# === OPAL END ===`
   - `~/.gemini/GEMINI.md` — `# === R2 START ===` ~ `# === R2 END ===`
   - `# === GEMINI HARDENING START ===` ~ `# === GEMINI HARDENING END ===`
3. PATH 마커 제거: `~/.zshrc`, `~/.bashrc`, `~/.profile`

---

## 파일 구조

```
opal/tools/opal-cli/
├── run.sh              진입점 디스패처
├── lib/
│   ├── update.sh       update 서브커맨드 (--to vX.Y, 사용자 데이터 보존)
│   ├── doctor.sh       doctor 서브커맨드 (~/.opal/tools/doctor/run.sh 위임)
│   ├── uninstall.sh    uninstall 서브커맨드 (~/.opal 제거 + 마커 회수)
│   ├── mcp.sh          mcp 서브커맨드 (list/add/remove/install-all)
│   └── console.sh      console 서브커맨드 (start/stop/status/open/scan/log)
└── README.md           이 문서
```

---

## 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-05-08 11:00 | 초기 구현 — run.sh 디스패처 + 5개 서브커맨드 (install/update/doctor/uninstall/mcp) (139) |
| v1.1 | 2026-07-10 10:00 | install 서브커맨드 제거 — dispatch/help/문서 정리 + lib/install.sh 삭제 (055) |
| v1.2 | 2026-07-13 17:43 | console log 서브명령 신설 — tail -F 실시간 팔로우(-n N) + README console 항목 보강 (L2) |

## console open — 진입 계약 (172)

`opal-cli console open`은 Console 인증 게이트(`/api/` 세션 필요)를 통과하는 유일한 권장 진입 경로다.

1. `/health` 확인 — 미기동이면 기동한 뒤 준비될 때까지 대기한다(기존 동작).
2. 구버전 데몬 거부 — `/health` 본문에 `auth` 필드가 없으면 인증 게이트 이전 버전이므로 경고와 재기동 안내(`console stop` 후 `console open`, PID 레코드가 없으면 수동 종료 안내)만 출력하고 브라우저를 열지 않은 채 비0으로 끝난다.
3. 1회용 진입 token 발급 — OPAL 공유 venv python(없으면 `python3`)으로 `python -m dashboard.backend.entry_token issue`를 실행해 token을 받는다. 발급에 실패하면 오류를 출력하고 브라우저를 열지 않으며 비0으로 끝난다.
4. 브라우저 열기 — `http://127.0.0.1:7823/#entry=<token>` 형태의 fragment URL을 `open`(macOS)·`xdg-open`(Linux)에 전달한다. 두 명령이 모두 없으면 token이 1회용이라 URL을 출력하지 않고 오류로 끝난다.
5. token 비출력 — token과 fragment는 터미널 출력·로그에 쓰지 않으며 출력에는 기본 URL만 나온다.

## console stop — stale 레코드 판정 (127)

PID 레코드의 `started_at`이 시스템 부팅 시각보다 이르면 종료 대상으로 삼지 않고 stale로
판정해 레코드만 정리한다(`stopped=false pid=<pid> reason=stale_record`, kill 0회).

리부팅 후에는 PID가 재할당되므로, 부팅 이전에 기록된 레코드의 `pid`는 무관한 사용자
프로세스를 가리킬 수 있다. 이 판정이 없으면 `install-mac.sh`가 무인 호출하는 경로에서
리부팅 후 첫 설치가 임의 사용자 프로세스를 종료할 수 있었다.

- 부팅 시각: macOS `sysctl -n kern.boottime` / Linux `/proc/stat` btime
- `started_at` 파싱 실패는 **fail-open** — stale로 오판정하지 않고 기존 판정 경로를 유지한다
- 신규 reason 토큰을 도입하지 않는다. 기존 `stale_record`에 합류한다

