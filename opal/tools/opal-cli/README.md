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
| `console <start\|stop\|status\|open\|scan\|log>` | OPAL Console 대시보드 관리 (포트 7823). `log`는 실시간 로그 팔로우(`-n N`, Ctrl+C 종료) |

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
