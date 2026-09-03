<#
.SYNOPSIS
    OPAL Windows 플랫폼 인스톨러 (install/macos.sh 와 대칭).

.DESCRIPTION
    install.ps1 의 Invoke-PlatformInstaller 함수가 호출하는 Windows 전용 설치 진입점.
    tarball 에서 압축 해제된 소스 트리를 기준으로 ~/.opal/ 배포를 수행한다.

    현재 상태: 핵심 흐름 골격 (PSScriptAnalyzer PASS 수준).
    실제 Windows 환경 검증은 TS-006(Windows VM) 에서 1회 수행 예정.

    macOS/Linux 대칭:
        scripts/install/macos.sh — exec bash scripts/install-mac.sh 위임
        scripts/install/windows.ps1 — Invoke-OpalWindowsInstall() 골격

    주요 단계:
        1. Test-WindowsDeps  — 필수 의존성 확인 (git, tar, PowerShell)
        2. Resolve-RepoRoot  — 스크립트 위치 기준 소스 루트 결정
        3. Install-OpalCore  — ~/.opal/ 디렉토리 생성 + 핵심 자산 복사
        4. Register-OpalBin  — ~/.opal/bin/opal-cli 심볼릭 링크(또는 래퍼 스크립트) 생성
        5. Register-EnvPath  — 사용자 PATH 에 ~/.opal/bin 추가 (idempotent)
        6. Register-Bootstrapper — CLAUDE.md / 기타 플랫폼 부트스트래퍼 마커 삽입 (후속)

.NOTES
    요구사항: Windows PowerShell 5.1+ 또는 PowerShell 7+
    근거:
        tasks/139-260508-opp-distribute-and-getstarted/PLAN.md §4.2 Step 6
        tasks/139-260508-opp-distribute-and-getstarted/PLAN.md §3.1.2 (install/macos.sh 와 대칭)
        tasks/139-260508-opp-distribute-and-getstarted/TASK.md D1: opal-cli 명칭
        tasks/139-260508-opp-distribute-and-getstarted/TASK.md D2: https://github.com/ceo4ever/opal
        docs/CONVENTIONS.md §구현 규칙 — 플랫폼 분기 격리

    변경이력:
        v1.0   2026-05-09 12:00  신규 작성 — Windows 플랫폼 인스톨러 골격 (139)
        v1.0.1 2026-05-09 14:30  Register-EnvPath 안내 보강 — 즉시 새로고침/검증/절대 경로 호출 (139 추가작업, macOS install_opal_bin과 동등)
        v1.0.2 2026-05-09 23:15  Register-OpalBin의 Join-Path 다중 인자(5.1 비호환) → [IO.Path]::Combine (139 추가작업)
        v1.0.3 2026-05-09 23:30  -OpalVersion 파라미터 신규 + Invoke-OpalWindowsInstall 끝에 ~/.opal/VERSION 기록 (env 잔존 결함 회피, install-mac.sh v1.8과 정합) (139 추가작업)
        v1.1.0 2026-05-10 00:30  Install-OpalCore + Register-Bootstrapper 본격 구현 — install-mac.sh install_opal()/install_opal_section/install_gemini_hardening PowerShell 이식.
                                 자산 실 복사(opal/core/AGENT.md / skills+opal/skills / agents+opal/agents / opal/templates / opal/tools / opal/core/references) +
                                 Strip 변경이력(Remove-ChangelogSection/Recursive) +
                                 부트스트래퍼 마커(Claude/Cursor/Gemini OPAL+HARDENING) 자동 삽입 (139 추가작업, v0.3.0)
        v1.1.1 2026-05-10 00:35  Install-OpalCore의 $skillCount/$agentCount .Count 접근을 @() 캐스트로 변경 — Set-StrictMode 3.0 환경에서 single object .Count 차단 결함 fix (139 추가작업, v0.3.1)
        v1.2.0 2026-05-10 00:40  Find-GitBash 신규 + Register-OpalBin 이 Git Bash explicit 경로 사용 — WSL bash.exe(/bin/bash 부재) 우회 결함 fix (139 추가작업, v0.3.2)
        v1.2.1 2026-05-10 08:50  opal-cli.ps1 미생성 + 옛 .ps1 정리 — PowerShell default ExecutionPolicy(Restricted) 차단 회피, .cmd 만 사용 (139 추가작업, v0.3.3)
        v1.3.0 2026-05-10 09:15  Find-Python / Find-Node (Microsoft Store stub 회피) + Install-OpalVenv (Python venv + requirements.txt) +
                                 Install-OpalMcp (claude/cursor/gemini/antigravity 4종 등록) + Install-PlatformAgents (sub-agent 어댑터 — Claude/Cursor/Gemini 모델 매핑) +
                                 Test-WindowsDeps Python/Node optional 검출 + 미설치 안내 (139 추가작업, v0.3.4)
        v1.3.1 2026-05-10 09:25  Install-OpalCore: skills/agents 결합을 Join-Path 명시로 — PowerShell nested @() 평탄화 결함 fix
                                 (스킬·에이전트 0개 + 어댑터 0개 결함 회복) (139 추가작업, v0.3.5)
        v1.3.2 2026-05-10 09:50  Set-ContentNoBom / Add-ContentNoBom 헬퍼 신규 + 모든 .md/.json 출력에 적용 —
                                 PowerShell 5.1 의 Set-Content -Encoding UTF8 가 BOM 을 추가해 Claude Code 의 frontmatter 파서가 '---' 매칭 실패하던 결함 fix
                                 (.claude/agents 어댑터가 Claude 에서 보이지 않던 문제 회복) (139 추가작업, v0.3.6)
        v1.3.3 2026-05-10 09:58  Install-OpalVenv 의 pip 호출 격리 — ErrorActionPreference='Continue' try/finally + python -m pip 우선 사용.
                                 Python 3.14 환경에서 pip 의 stderr 출력이 PowerShell 의 NativeCommandError(RemoteException)로 변환되어
                                 $ErrorActionPreference='Stop' + 2>&1 조합으로 throw 되던 설치 중단 결함 fix (140 추가작업, v0.3.7)
        v1.4.0 2026-05-10 10:35  Install-WindowsPython 신규 — Python 미설치 시 winget 으로 Python.Python.3.14 user-scope 자동 설치.
                                 옵트아웃: 환경변수 OPAL_AUTO_INSTALL_PYTHON=0 / winget 미보유·실패 시 graceful 폴백.
                                 설치 직후 User+Machine PATH 결합 + 표준 경로 직접 탐색으로 현재 세션 인터프리터 경로 확보.
                                 안내문구 Python 3.12 → 3.14 일괄 갱신 (140 추가작업, v0.3.9)
        v1.4.1 2026-05-10 11:10  native command stderr → NativeCommandError 결함 일괄 보강.
                                 상단에 $PSNativeCommandUseErrorActionPreference=$false 추가 (PowerShell 7.3+ 옵트아웃).
                                 5.x backstop 으로 venv 생성($py -m venv) / claude CLI / gemini CLI 호출에 try/finally + ErrorAction='Continue' 격리.
                                 claude CLI 가 idempotent 재등록 시 'MCP server X already exists' 를 stderr 로 출력해 install 중단되던 결함 fix
                                 (140 추가작업, v0.3.10)
        v1.5.0 2026-05-10 12:30  Windows MCP 등록 형식 보강 — Convert-McpConfigForWindows 신규.
                                 npx/npm/node command 를 'cmd /c <원래>' 로 래핑 (Node child_process.spawn 의 .cmd shim 미해석 +
                                 CVE-2024-27980 spawn restriction 회피) + args 의 /tmp/... → $env:TEMP\... 치환.
                                 Merge-McpConfig 에 -Force 추가, claude/gemini CLI 등록 전 'mcp remove' 로 기존 항목 제거 + 재등록 (mcps/*.json 변경 없이 install-time 변환).
                                 Claude/Cursor/Gemini/Antigravity 4개 platform 의 4개 MCP 가 Windows 에서 ✘ failed 로 동작하지 않던 결함 fix (140 추가작업, v0.3.11)
        v1.5.1 2026-05-10 13:15  Convert-McpConfigForWindows 의 wrapping 전략 변경 — 'cmd /c npx ...' → 'npx.cmd ...' 직접 호출.
                                 cmd /c 래핑은 PowerShell 직접 실행에선 정상이지만 Claude Code MCP host 가 stdio pipe 로 spawn 시
                                 자식 npx 의 stdio passthrough 가 깨져 4개 MCP 모두 ✘ failed 로 남던 결함 fix.
                                 Anthropic 권고와 정합 (Windows 는 npx.cmd / npm.cmd 직접 호출). v0.3.11 의 mcp remove + 재등록 로직이
                                 기존 cmd 래핑 항목을 자동 갱신함 (140 추가작업, v0.3.12)
        v1.5.2 2026-05-10 14:00  Cursor 부트스트래퍼 .mdc 복사 시 CRLF 정규화 + Set-ContentNoBom 적용 (일반적 호환성 보강).
                                 (140 추가작업, v0.3.13)
        v1.5.3 2026-05-10 14:30  Cursor 부트스트래퍼 미동작의 진짜 원인 fix — opal/bootstrapper/cursor-bootstrap.mdc 의 'globs:' 빈 값 라인 제거.
                                 mac 의 Cursor 는 alwaysApply: true 를 우선 적용해 통과하지만 Windows 빌드의 frontmatter 파서는
                                 globs: null 을 '매칭 영역 없음' 으로 해석해 룰을 비활성화하던 차이 (캡틴 머신에서 직접 globs 라인 삭제로 동작 검증).
                                 (140 추가작업, v0.3.14)
        v1.5.4 2026-05-10 15:30  install 출력 노이즈 정리 — Playwright chromium 미설치 시에만 안내 ($env:LOCALAPPDATA\ms-playwright\chromium-* 검사).
                                 마무리 단계의 'Python 미설치라면 ...' 라인을 Find-Python 부재 시에만 노출.
                                 (140 추가작업, v0.3.16)
        v1.6.0 2026-05-10 17:00  community-skills 번들 → fetch 방식 전환 — community-skills 복사 블록 제거 + cleanDirs에서 community-skills 제거 (사용자 데이터 보존, D-4) + 종료 안내 추가 (142)
        v1.7.0 2026-05-10 21:00  command 화이트리스트 + fork repo banner + OPAL_HOME 가드 (144)
        v1.8.0 2026-05-24        Codex CLI 통합 — Register-Bootstrapper 에 ~/.codex/AGENTS.md 추가 + Install-OpalMcp 에 'codex' 케이스 + Install-PlatformAgents 에 codex(TOML 직렬화) 추가 (009)
        v1.9.0 2026-06-17 10:24  Invoke-OpalWindowsInstall 에 git core.quotepath=false 전역 설정 추가 — 한글 태스크 폴더명 허용에 따른 git 경로 표시 개선 (install-mac.sh v3.1 정합) (026 L2: 한글 폴더명 허용)
        v1.9.0 2026-06-02 20:16  모델 매핑 최신화 — ModelMap gemini(gemini-3.1-flash-lite/gemini-flash-latest/gemini-pro-latest) + codex(gpt-5.4-mini/gpt-5.5/gpt-5.3-codex) + toml 기본값 gpt-5.5 (install-mac.sh 동기, 011)
        v1.10.0 2026-06-07       OPAL 헌법(PRINCIPLES.md) 배포 추가 — opal/core/PRINCIPLES.md → ~/.opal/PRINCIPLES.md (Strip 변경이력, always-on) (012)
        v1.11.0 2026-06-15       OPAL Console 설치 추가 — Install-Dashboard 신설 (FE npm.cmd 빌드·BE 복사·dashboard-server 배포) + cleanDirs에 dashboard-server 추가 (021)
        v1.12.0 2026-06-15       메뉴 [5] OPAL Console 자동 기동 추가 — Start-OpalConsole 신설 (기존 프로세스 Stop-OpalConsole + Start-Process uvicorn 백그라운드 + /health 확인) (021 후속)
        v1.13.0 2026-06-17       Codex 어댑터 정합 — Install-CodexConfig 신설(config.toml [agents] 멱등 작성, max_concurrent_threads_per_session=6/max_depth=1/job_max_runtime_seconds=1800) + 호출부 연결 + Install-PlatformAgents codex ModelMap stale(standard=gpt-5.5/advanced=gpt-5.3-codex) → SSOT v1.4 정정(standard=gpt-5.4/advanced=gpt-5.5) (028)
        v1.14.0 2026-06-21 16:18 Convert-BodyModelTokens 신규 — 본문 인라인 model 레벨 sub-dispatch 토큰('[,(]\s*model:\s*(light|standard|advanced)\b')을 ModelMap 실모델명으로 변환(cursor=inherit→토큰 제거+빈괄호 정리). Install-PlatformAgents Markdown 경로($convertedBody 직렬화)·Codex TOML 경로(escape 전) 양쪽 적용. install-mac.sh _sub_body_model 미러(문자 단위 동일 정규식) — 액션 에이전트 sub-dispatch model enum 위반 버그 fix (032)
        v1.15.0 2026-06-24 17:26 KST: Install-OpalCore setting.json create-if-absent 배포 추가 (043)
        v1.16.0 2026-06-29 15:24 KST: Invoke-OpalWindowsInstall에 $repoRoot/VERSION 각인값 최우선 읽기 추가 — install-mac.sh record_installed_version 대칭, -notlike '$Format:*' 판별 (048)
        v1.17.0 2026-07-10 18:07  Install-Dashboard 말미에 console.config.json 자동 생성/머지 로직 추가 — .opal\AGENT.md 마커 탐색 + scan_roots 병합(보존+추가+dedup)의 PowerShell 네이티브 등가, opal-cli console scan(install-mac.sh v3.9) 과 의미상 동등, try/catch 격리로 install 비중단 (057)
        v1.18.0 2026-07-17       Install-OpalCore 도구 복사 직후 fw-inbox 런타임 디렉토리 초기화 블록 추가 — New-Item -Force(멱등) + fw-inbox-README.md create-if-absent seed, cleanDirs(:433) 미포함으로 재설치 시 기존 수집 항목 보존(H-5 멱등, install-mac.sh v4.0 대칭). 스킬(opal-improve)·도구(improve-tool)는 기존 skills/tools 자동 복사 블록이 처리 (058)
        v1.19.0 2026-08-10 23:24 KST: Test-PythonMinVersion 신설 + Find-Python 하한 판정 추가(미달 인터프리터 비채택 → 자동 설치 트리거를 "미설치 또는 하한 미달"로 확대) + Install-WindowsPython 의 3.14 리터럴을 $OpalPythonTarget 상수 파생으로 전환, install-mac.sh v4.4 대칭 (087)
        v1.20.0 2026-09-02 18:00 KST: Install-CodexConfig — legacy 키 max_threads → max_concurrent_threads_per_session 전량 교체(리터럴·주석·변경이력 포함) + 멱등 판정 2분기 → 3분기 확장(append/migrate-in-place/skip), 기존 설치 머신의 [agents] 블록 내 legacy 키를 값 보존한 채 in-place 치환, [mcp_servers] 등 타 블록 무손상, install-mac.sh v4.6 대칭 (105)
        v1.21.0 2026-09-02 22:10 KST: install-mac.sh OPAL_ADAPTER_FIELD_SPEC(105 v4.7) 미러 반영 — $OpalAdapterFieldSpecMirror here-string 신설(센티넬 마커 사이 JSON 리터럴 바이트 동일, TS-011) + ConvertTo-OpalHashtable(PS5.1 호환 재귀 변환, AsHashtable 스위치 미사용) + Resolve-OpalFieldValue/ConvertTo-OpalFieldPairs/Get-OpalModelLevelMap(install-mac.sh resolve_value/build_pairs/model_level_map 미러) 신규. Get-AgentFrontmatter 의 name/description/model 3키 한정 switch 를 전 키 Fields 해시 수집으로 확장(기존 4키 Name/Description/Model/Body 유지, H-5 결함 fix). Install-PlatformAgents 의 $platforms 인라인 ModelMap·md 3줄/toml 4줄 고정 직렬화를 스펙 pairs 순회로 교체 — Convert-BodyModelTokens 의 [hashtable]$ModelMap 계약은 무변경(H-8). effort 를 Claude(effort 키)/Codex(model_reasoning_effort, max→xhigh)에 반영, Cursor 는 예약(omit)·Gemini 는 미지원(omit). 경고 문구 mac 과 동일 본문("unsupported {field} value '{raw}' for platform {platform} — field omitted"). 미러 규약을 "스펙 JSON 리터럴 블록의 바이트 동일 + 배치 모드 3종의 동일 의미 구현"으로 재정의(§3.2.2). Windows 런타임 검증(TS-012·013)은 본 환경 pwsh 미설치로 미수행 — 정적 리뷰 + TS-011/TS-014로 대체 (105)
#>

#Requires -Version 5.1

# install.ps1 이 -OpalVersion 으로 전달하는 framework 버전.
# ~/.opal/VERSION 기록에 사용. 미전달 시 "main" 폴백.
param(
    [string]$OpalVersion = 'main'
)

Set-StrictMode -Version 3.0
$ErrorActionPreference = 'Stop'

# PowerShell 7.3+ : native command 의 stderr 가 $ErrorActionPreference 와 결합해
# NativeCommandError(RemoteException)로 변환되어 throw 되는 결함을 사전 차단한다.
# 5.x 에서는 변수 자체가 무시되며, 5.x 의 동일 결함은 각 native 호출 라인의 inline 격리로 회피.
$PSNativeCommandUseErrorActionPreference = $false

# ─── 상수 ────────────────────────────────────────────────────────────────────

$OpalHome   = Join-Path $env:USERPROFILE '.opal'
$OpalBinDir = Join-Path $OpalHome 'bin'

# 부트스트래퍼 마커 (install-mac.sh:25-32 와 동일)
$OpalStart      = '# === OPAL START ==='
$OpalEnd        = '# === OPAL END ==='
$R2Start        = '# === R2 START ==='
$R2End          = '# === R2 END ==='
$HardeningStart = '# === GEMINI HARDENING START ==='
$HardeningEnd   = '# === GEMINI HARDENING END ==='

# Python 버전 계약 — install-mac.sh OPAL_PYTHON_MIN/OPAL_PYTHON_TARGET 미러 (087)
$OpalPythonMin    = '3.11'
$OpalPythonTarget = '3.14'

# ─── 유틸리티 ─────────────────────────────────────────────────────────────────

function Write-OpalInfo  { param([string]$Msg) Write-Host "[OPAL] $Msg" -ForegroundColor Cyan   }
function Write-OpalOk    { param([string]$Msg) Write-Host "[OPAL] $Msg" -ForegroundColor Green  }
function Write-OpalWarn  { param([string]$Msg) Write-Host "[OPAL][WARN] $Msg" -ForegroundColor Yellow }
function Write-OpalError { param([string]$Msg) Write-Host "[OPAL][ERROR] $Msg" -ForegroundColor Red   }

# BOM 없는 UTF-8 로 파일 작성 — PowerShell 5.1 의 Set-Content -Encoding UTF8 가 BOM 을 추가하는 결함 회피.
# Claude Code / Cursor 등의 frontmatter 파서가 첫 줄 BOM 으로 '---' 매칭 실패하는 문제 우회.
$Script:Utf8NoBom = New-Object System.Text.UTF8Encoding $false
function Set-ContentNoBom {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)]$Value
    )
    if ($Value -is [array]) {
        $text = $Value -join "`r`n"
    } else {
        $text = "$Value"
    }
    [System.IO.File]::WriteAllText($Path, $text, $Script:Utf8NoBom)
}

function Add-ContentNoBom {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)]$Value
    )
    if ($Value -is [array]) {
        $text = $Value -join "`r`n"
    } else {
        $text = "$Value"
    }
    [System.IO.File]::AppendAllText($Path, $text, $Script:Utf8NoBom)
}

# ─── Strip 변경이력 (install-mac.sh strip_deploy_md / strip_deploy_md_recursive 이식) ───

function Remove-ChangelogSection {
    <#
    .SYNOPSIS
        .md 파일에서 "## 변경이력" 섹션부터 파일 끝까지 제거 (in-place).
    .NOTES
        macOS: scripts/install-mac.sh:184-188 strip_deploy_md.
        배포본에서 변경이력 노출을 차단한다. 소스에는 그대로 유지.
    #>
    param([Parameter(Mandatory)][string]$Path)
    if (-not (Test-Path $Path)) { return }
    $lines = Get-Content -Path $Path -Encoding UTF8
    $kept = @()
    foreach ($line in $lines) {
        if ($line -eq '## 변경이력') { break }
        $kept += $line
    }
    Set-ContentNoBom -Path $Path -Value $kept
}

function Remove-ChangelogRecursive {
    <#
    .SYNOPSIS
        디렉토리 하위 모든 .md 파일에 Remove-ChangelogSection 적용.
    .NOTES
        macOS: scripts/install-mac.sh:190-199 strip_deploy_md_recursive.
    #>
    param([Parameter(Mandatory)][string]$Root)
    if (-not (Test-Path $Root)) { return }
    Get-ChildItem -Path $Root -Filter '*.md' -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object {
        $raw = Get-Content -Path $_.FullName -Raw -Encoding UTF8
        if ($raw -and ($raw -match '(?m)^## 변경이력$')) {
            Remove-ChangelogSection -Path $_.FullName
        }
    }
}

# ─── 부트스트래퍼 콘텐츠 추출 + 마커 삽입 (install_opal_section / install_gemini_hardening 이식) ───

function Get-BootstrapContent {
    <#
    .SYNOPSIS
        bootstrapper .md 파일의 markdown 코드 블록 내용만 추출.
        4-backtick(````markdown ... ````) 우선, 없으면 3-backtick(```markdown ... ```) 사용.
    .NOTES
        macOS: scripts/install-mac.sh:201-209 extract_bootstrap_content.
    #>
    param([Parameter(Mandatory)][string]$Path)
    $rawContent = Get-Content -Path $Path -Raw -Encoding UTF8
    $isFour = ($rawContent -match '(?m)^````markdown$')
    $marker = if ($isFour) { '````' } else { '```' }
    $startMarker = "${marker}markdown"

    $lines = Get-Content -Path $Path -Encoding UTF8
    $inBlock = $false
    $result = @()
    foreach ($line in $lines) {
        if (-not $inBlock -and $line -eq $startMarker) { $inBlock = $true; continue }
        if ($inBlock -and $line -eq $marker) { break }
        if ($inBlock) { $result += $line }
    }
    return ($result -join "`r`n")
}

function Install-OpalSection {
    <#
    .SYNOPSIS
        bootstrapper snippet 의 콘텐츠를 OPAL_START/OPAL_END 마커로 감싸 target 에 삽입한다.
        - 새 파일: 신규 생성
        - OPAL_START 마커 있음: 마커 블록 교체
        - R2_START 마커 있음: OPAL 로 전환
        - 마커 없음: 파일 끝에 추가 (기존 내용 보존)
    .NOTES
        macOS: scripts/install-mac.sh:211-285 install_opal_section.
    #>
    param(
        [Parameter(Mandatory)][string]$SnippetPath,
        [Parameter(Mandatory)][string]$Target,
        [Parameter(Mandatory)][string]$Label
    )
    $content = Get-BootstrapContent -Path $SnippetPath
    if (-not $content) {
        Write-OpalError "$Label 부트스트래퍼 내용을 추출 못 했습니다: $SnippetPath"
        return
    }
    $targetDir = Split-Path -Parent $Target
    if (-not (Test-Path $targetDir)) {
        New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
    }
    $block = "$OpalStart`r`n$content`r`n$OpalEnd"

    if (-not (Test-Path $Target)) {
        Set-ContentNoBom -Path $Target -Value "$block`r`n"
        Write-OpalOk "$Label OPAL 설치 (새 파일): $Target"
        return
    }
    $existing = Get-Content -Path $Target -Raw -Encoding UTF8
    if ($existing -match [regex]::Escape($OpalStart)) {
        # OPAL_START~OPAL_END 블록 교체 — regex literal Replace 사용 (block 의 $ 등 metachar 안전 처리)
        $pattern = '(?ms)' + [regex]::Escape($OpalStart) + '.*?' + [regex]::Escape($OpalEnd)
        $regex = [System.Text.RegularExpressions.Regex]::new($pattern)
        $newContent = $regex.Replace($existing, $block)
        Set-ContentNoBom -Path $Target -Value $newContent
        Write-OpalOk "$Label OPAL 업데이트 (마커 교체): $Target"
    }
    elseif ($existing -match [regex]::Escape($R2Start)) {
        $pattern = '(?ms)' + [regex]::Escape($R2Start) + '.*?' + [regex]::Escape($R2End)
        $regex = [System.Text.RegularExpressions.Regex]::new($pattern)
        $newContent = $regex.Replace($existing, $block)
        Set-ContentNoBom -Path $Target -Value $newContent
        Write-OpalOk "$Label R2→OPAL 전환 (마커 교체): $Target"
    }
    else {
        Add-ContentNoBom -Path $Target -Value "`r`n$block`r`n"
        Write-OpalOk "$Label OPAL 추가 (기존 보존): $Target"
    }
}

function Install-GeminiHardening {
    <#
    .SYNOPSIS
        Gemini HARDENING 마커 삽입 (install-mac.sh install_gemini_hardening 이식).
    #>
    param(
        [Parameter(Mandatory)][string]$SnippetPath,
        [Parameter(Mandatory)][string]$Target
    )
    $content = Get-BootstrapContent -Path $SnippetPath
    if (-not $content) {
        Write-OpalError "HARDENING 부트스트래퍼 내용을 추출 못 했습니다: $SnippetPath"
        return
    }
    $targetDir = Split-Path -Parent $Target
    if (-not (Test-Path $targetDir)) {
        New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
    }
    $block = "$HardeningStart`r`n$content`r`n$HardeningEnd"

    if (-not (Test-Path $Target)) {
        Set-ContentNoBom -Path $Target -Value "$block`r`n"
        Write-OpalOk "Gemini HARDENING 설치 (새 파일): $Target"
        return
    }
    $existing = Get-Content -Path $Target -Raw -Encoding UTF8
    if ($existing -match [regex]::Escape($HardeningStart)) {
        $pattern = '(?ms)' + [regex]::Escape($HardeningStart) + '.*?' + [regex]::Escape($HardeningEnd)
        $regex = [System.Text.RegularExpressions.Regex]::new($pattern)
        $newContent = $regex.Replace($existing, $block)
        Set-ContentNoBom -Path $Target -Value $newContent
        Write-OpalOk "Gemini HARDENING 업데이트 (마커 교체): $Target"
    }
    else {
        Add-ContentNoBom -Path $Target -Value "`r`n$block`r`n"
        Write-OpalOk "Gemini HARDENING 추가 (기존 보존): $Target"
    }
}

# ─── 함수 정의 ───────────────────────────────────────────────────────────────

function Test-WindowsDeps {
    <#
    .SYNOPSIS
        Windows 환경에 필수 의존성(git, tar)이 갖춰져 있는지 확인한다.
    #>
    $missing = @()

    if (-not (Get-Command 'git' -ErrorAction SilentlyContinue)) {
        $missing += 'git (https://git-scm.com/download/win)'
    }

    if (-not (Get-Command 'tar' -ErrorAction SilentlyContinue)) {
        $missing += 'tar (Windows 10 1803+ 기본 제공; 없으면 Git for Windows 설치)'
    }

    if ($missing.Count -gt 0) {
        Write-OpalError '필수 의존성이 누락되었습니다:'
        foreach ($m in $missing) {
            Write-OpalError "  - $m"
        }
        throw '[OPAL] 의존성 누락으로 설치를 중단합니다.'
    }

    Write-OpalOk '의존성 확인 완료.'

    # ── 선택 의존성 (warn 만, 설치 중단 안 함) ──
    $py = Find-Python
    if (-not $py) {
        if (Install-WindowsPython) {
            $py = Find-Python
        }
    }
    if ($py) {
        Write-OpalInfo "Python: $py"
    } else {
        Write-OpalWarn "Python ${OpalPythonMin} 이상 미확보 — Python venv / xlsx-tool / Playwright 동작 제한"
        Write-OpalInfo "  설치: winget install Python.Python.$OpalPythonTarget  또는  https://www.python.org/downloads/windows/"
        Write-OpalInfo '  (자동 설치 옵트아웃: $env:OPAL_AUTO_INSTALL_PYTHON=0)'
    }
    $nodeInfo = Find-Node
    if ($nodeInfo) {
        Write-OpalInfo "Node.js: v$($nodeInfo.Version) ($($nodeInfo.Path))"
        if ($nodeInfo.Version -lt 18) {
            Write-OpalWarn '  Node.js v18+ 권장 (skill-registry / state-tool 동작 보장)'
        }
    } else {
        Write-OpalWarn 'Node.js 미설치 — skill-registry / state-tool 등 일부 도구 동작 제한'
        Write-OpalInfo '  설치: winget install OpenJS.NodeJS  또는  https://nodejs.org/'
    }
}

function Resolve-RepoRoot {
    <#
    .SYNOPSIS
        이 스크립트의 위치(scripts/install/)를 기준으로 소스 루트를 결정한다.
        install.ps1 이 tarball 에서 압축 해제한 경로를 전달하거나,
        직접 실행 시 스크립트 위치에서 두 단계 상위가 소스 루트다.
    .OUTPUTS
        소스 루트 경로 문자열.
    #>
    $here = Split-Path -Parent $MyInvocation.ScriptName
    if (-not $here) {
        # 파이프(irm|iex) 실행 시 ScriptName 이 비어 있을 수 있음
        $here = $PWD.Path
    }
    $root = Split-Path -Parent (Split-Path -Parent $here)

    if (-not (Test-Path (Join-Path $root 'opal'))) {
        # 소스 루트를 찾지 못한 경우 현재 디렉토리 사용
        Write-OpalWarn "소스 루트를 자동 결정하지 못했습니다. PWD=$($PWD.Path) 를 사용합니다."
        $root = $PWD.Path
    }

    Write-OpalInfo "소스 루트: $root"
    return $root
}

function Install-OpalCore {
    <#
    .SYNOPSIS
        ~/.opal/ 에 OPAL 핵심 자산을 본격 복사한다 (install-mac.sh install_opal() PowerShell 이식).
        보존: identity.md, AGENT.md(덮어쓰지만 후속 사용자 메모는 별도 위치), projects/, .venv/.
        클린 후 재배포: skills/, agents/, references/, tools/, templates/.
        보존: ~/.opal/community-skills/(사용자 데이터, 142 D-4)
    #>
    param(
        [Parameter(Mandatory)]
        [string] $RepoRoot
    )

    Write-OpalInfo '~/.opal/ 디렉토리 준비 중...'

    # OPAL_HOME 가드 — 비표준 경로 거부 (GC-010, R-8)
    $defaultOpalHome = [IO.Path]::GetFullPath((Join-Path $env:USERPROFILE '.opal'))
    $currentOpalHome = [IO.Path]::GetFullPath($OpalHome)
    if ($currentOpalHome -ne $defaultOpalHome -and $env:OPAL_HOME_OVERRIDE -ne '1') {
        throw "[OPAL] 비표준 OPAL_HOME 거부: $OpalHome (예상: $defaultOpalHome). 옵트인: `$env:OPAL_HOME_OVERRIDE='1' 명시"
    }

    if (-not (Test-Path $OpalHome)) {
        New-Item -ItemType Directory -Path $OpalHome -Force | Out-Null
        Write-OpalOk "~/.opal/ 생성 완료."
    } else {
        Write-OpalInfo '~/.opal/ 이미 존재합니다 (업데이트 모드).'
    }

    # ── 클린: framework 디렉토리만 (사용자 데이터 보존) ──
    Write-OpalInfo '기존 프레임워크 파일 정리 (사용자 데이터 보존)...'
    # 사용자 데이터 보존: ~/.opal/community-skills/는 install이 절대 건드리지 않음 (TASK 142 D-4)
    $cleanDirs = @('skills', 'agents', 'references', 'templates', 'tools', 'dashboard-server')
    foreach ($d in $cleanDirs) {
        $p = Join-Path $OpalHome $d
        if (Test-Path $p) {
            Remove-Item -Recurse -Force -Path $p -ErrorAction SilentlyContinue
        }
    }

    # ── OPAL 코어: opal/core/AGENT.md → ~/.opal/AGENT.md (Strip 변경이력) ──
    $coreAgent = [IO.Path]::Combine($RepoRoot, 'opal', 'core', 'AGENT.md')
    $opalAgentDst = Join-Path $OpalHome 'AGENT.md'
    if (Test-Path $coreAgent) {
        Copy-Item -Force -Path $coreAgent -Destination $opalAgentDst
        Remove-ChangelogSection -Path $opalAgentDst
        Write-OpalOk "OPAL AGENT.md → $opalAgentDst"
    }

    # ── OPAL 헌법: opal/core/PRINCIPLES.md → ~/.opal/PRINCIPLES.md (Strip 변경이력, always-on) ──
    $corePrinciples = [IO.Path]::Combine($RepoRoot, 'opal', 'core', 'PRINCIPLES.md')
    $opalPrinciplesDst = Join-Path $OpalHome 'PRINCIPLES.md'
    if (Test-Path $corePrinciples) {
        Copy-Item -Force -Path $corePrinciples -Destination $opalPrinciplesDst
        Remove-ChangelogSection -Path $opalPrinciplesDst
        Write-OpalOk "OPAL PRINCIPLES.md (헌법) → $opalPrinciplesDst"
    }

    # ── OPAL 기본 설정: opal/core/setting.default.json → ~/.opal/setting.json (create-if-absent) ──
    $settingSrc = [IO.Path]::Combine($RepoRoot, 'opal', 'core', 'setting.default.json')
    $settingDst = Join-Path $OpalHome 'setting.json'
    if ((Test-Path $settingSrc) -and -not (Test-Path $settingDst)) {
        Copy-Item -Path $settingSrc -Destination $settingDst
        Write-OpalOk "OPAL setting.json (기본값) → $settingDst"
    } elseif ((Test-Path $settingSrc) -and (Test-Path $settingDst)) {
        # 파일 존재: models 키 없으면 scaffold 병합 (멱등) — install-mac.sh install_opal_setting 패리티
        try {
            $existing = Get-Content -Raw -Path $settingDst | ConvertFrom-Json
            if (-not $existing.PSObject.Properties['models']) {
                $default = Get-Content -Raw -Path $settingSrc | ConvertFrom-Json
                $existing | Add-Member -NotePropertyName 'models' -NotePropertyValue $default.models
                ($existing | ConvertTo-Json -Depth 10) | Set-Content -Path $settingDst -Encoding UTF8
                Write-OpalInfo 'setting.json에 models scaffold 병합 완료'
            } else {
                Write-OpalInfo 'setting.json 이미 존재 + models 보유 — 무변 (멱등)'
            }
        } catch {
            Write-OpalInfo 'setting.json models 병합 실패 — 기존 파일 유지'
        }
    }

    # ── 스킬: skills/ + opal/skills/ 합쳐서 ~/.opal/skills/ ──
    $skillsDst = Join-Path $OpalHome 'skills'
    New-Item -ItemType Directory -Path $skillsDst -Force | Out-Null
    # Join-Path 로 명시 결합 — PowerShell @() nested array 평탄화 결함 회피
    $skillSrcs = @(
        (Join-Path $RepoRoot 'skills'),
        (Join-Path $RepoRoot 'opal\skills')
    )
    foreach ($src in $skillSrcs) {
        if (-not (Test-Path $src)) { continue }
        Get-ChildItem -Path $src -Directory -ErrorAction SilentlyContinue | ForEach-Object {
            $skillDst = Join-Path $skillsDst $_.Name
            if (Test-Path $skillDst) { Remove-Item -Recurse -Force $skillDst }
            Copy-Item -Recurse -Force -Path $_.FullName -Destination $skillsDst
        }
    }
    Remove-ChangelogRecursive -Root $skillsDst
    # @() 강제 array 캐스트 — Set-StrictMode 3.0 환경에서 single object 의 .Count 접근 차단 회피
    $skillCount = @(Get-ChildItem -Path $skillsDst -Directory -ErrorAction SilentlyContinue).Count
    Write-OpalOk "스킬 ${skillCount}개 → $skillsDst"

    # ── 에이전트: opal/agents/ + agents/ 합쳐서 ~/.opal/agents/ (레거시 디렉토리 제외) ──
    $agentsDst = Join-Path $OpalHome 'agents'
    New-Item -ItemType Directory -Path $agentsDst -Force | Out-Null
    $agentSrcs = @(
        (Join-Path $RepoRoot 'opal\agents'),
        (Join-Path $RepoRoot 'agents')
    )
    foreach ($src in $agentSrcs) {
        if (-not (Test-Path $src)) { continue }
        Get-ChildItem -Path $src -Directory -ErrorAction SilentlyContinue | Where-Object {
            $_.Name -notin @('claude', 'cursor', 'antigravity')
        } | ForEach-Object {
            $agentDst = Join-Path $agentsDst $_.Name
            if (Test-Path $agentDst) { Remove-Item -Recurse -Force $agentDst }
            Copy-Item -Recurse -Force -Path $_.FullName -Destination $agentsDst
        }
    }
    Remove-ChangelogRecursive -Root $agentsDst
    $agentCount = @(Get-ChildItem -Path $agentsDst -Directory -ErrorAction SilentlyContinue).Count
    Write-OpalOk "에이전트 ${agentCount}개 → $agentsDst"

    # ── 템플릿: opal/templates/ → ~/.opal/templates/ ──
    $templatesSrc = [IO.Path]::Combine($RepoRoot, 'opal', 'templates')
    $templatesDst = Join-Path $OpalHome 'templates'
    if (Test-Path $templatesSrc) {
        Copy-Item -Recurse -Force -Path $templatesSrc -Destination $OpalHome
    }
    # opal/core/identity-template.md → ~/.opal/templates/identity-template.md
    $idTpl = [IO.Path]::Combine($RepoRoot, 'opal', 'core', 'identity-template.md')
    if (Test-Path $idTpl) {
        if (-not (Test-Path $templatesDst)) {
            New-Item -ItemType Directory -Path $templatesDst -Force | Out-Null
        }
        Copy-Item -Force -Path $idTpl -Destination (Join-Path $templatesDst 'identity-template.md')
    }
    if (Test-Path $templatesDst) {
        Write-OpalOk "templates → $templatesDst"
    }

    # ── 도구: opal/tools/ → ~/.opal/tools/ ──
    $toolsSrc = [IO.Path]::Combine($RepoRoot, 'opal', 'tools')
    $toolsDst = Join-Path $OpalHome 'tools'
    if (Test-Path $toolsSrc) {
        Copy-Item -Recurse -Force -Path $toolsSrc -Destination $OpalHome
        Remove-ChangelogRecursive -Root $toolsDst
        Write-OpalOk "tools → $toolsDst"
    }

    # ── fw-inbox 런타임 디렉토리 초기화 (058, create-if-absent — 사용자 데이터 보존, H-5 멱등) ──
    # [MUST] fw-inbox는 cleanDirs(:433)에 포함하지 않는다 — 재설치 시 기존 수집 항목(FW 개선 후보) 삭제 금지.
    $fwInbox = Join-Path $OpalHome 'fw-inbox'
    New-Item -ItemType Directory -Path $fwInbox -Force | Out-Null   # -Force = 존재 시 no-op(멱등)
    $fwInboxReadmeSrc = [IO.Path]::Combine($RepoRoot, 'opal', 'tools', 'improve-tool', 'fw-inbox-README.md')
    $fwInboxReadmeDst = Join-Path $fwInbox 'README.md'
    if ((Test-Path $fwInboxReadmeSrc) -and -not (Test-Path $fwInboxReadmeDst)) {
        Copy-Item -Path $fwInboxReadmeSrc -Destination $fwInboxReadmeDst
    }
    Write-OpalOk "fw-inbox 초기화 → $fwInbox (기존 항목 보존)"

    # ── 참조 레지스트리: opal/core/references/ → ~/.opal/references/ ──
    $refSrc = [IO.Path]::Combine($RepoRoot, 'opal', 'core', 'references')
    $refDst = Join-Path $OpalHome 'references'
    if (Test-Path $refSrc) {
        Copy-Item -Recurse -Force -Path $refSrc -Destination $OpalHome
        Remove-ChangelogRecursive -Root $refDst
        Write-OpalOk "references → $refDst"
    }

    # 커뮤니티 스킬은 번들로 배포하지 않음. 사용자가 //skill-manager로 검색·설치 (TASK 142)

    Write-OpalOk '핵심 자산 복사 완료.'
}

function Test-PythonMinVersion {
    <#
    .SYNOPSIS
        지정된 Python 인터프리터가 $OpalPythonMin 이상인지 판정한다.
    .NOTES
        판정 규칙(major/minor 정수 비교)은 install-mac.sh python_meets_min 과
        문자 그대로 동일한 계약이다 (087).
    .OUTPUTS
        하한 충족 시 $true, 미달·해석 실패 시 $false.
    #>
    param([Parameter(Mandatory)][string]$PythonPath)

    try {
        $verOut = & $PythonPath -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>&1
        if ($LASTEXITCODE -ne 0) { return $false }
        $parts = "$verOut".Trim() -split '\.'
        if ($parts.Count -lt 2) { return $false }
        $major = [int]$parts[0]
        $minor = [int]$parts[1]

        $minParts = $OpalPythonMin -split '\.'
        $minMajor = [int]$minParts[0]
        $minMinor = [int]$minParts[1]

        if ($major -gt $minMajor) { return $true }
        if ($major -eq $minMajor -and $minor -ge $minMinor) { return $true }
        return $false
    } catch {
        return $false
    }
}

function Find-Python {
    <#
    .SYNOPSIS
        실 Python 3 인터프리터를 검출한다 (Microsoft Store stub 회피).
        $OpalPythonMin 이상인 후보만 채택 — 미달 후보는 건너뛰고 다음 후보로 계속 순회한다.
    .NOTES
        Windows 의 python.exe 가 Microsoft Store stub 일 경우 실행 시 stub 안내 후 종료.
        --version 호출 결과로 진짜 Python 인지 검증 + Test-PythonMinVersion 으로 하한 판정.
        후보 목록은 $OpalPythonTarget~$OpalPythonMin 마이너 버전에서 파생한 versioned 이름을
        먼저 시도하고(내림차순), 이후 기존 PATH 기본 이름(python3/python/py)을 순회한다 (087).
    .OUTPUTS
        하한을 충족하는 첫 후보의 절대 경로, 모든 후보 순회 후 미발견이면 $null
    #>
    $targetParts = $OpalPythonTarget -split '\.'
    $minParts    = $OpalPythonMin -split '\.'
    $major       = [int]$targetParts[0]

    $versionedNames = @()
    for ($minor = [int]$targetParts[1]; $minor -ge [int]$minParts[1]; $minor--) {
        $versionedNames += "python$major.$minor"
    }
    $candidateNames = $versionedNames + @('python3', 'python', 'py')

    foreach ($name in $candidateNames) {
        $cmd = Get-Command $name -ErrorAction SilentlyContinue
        if (-not $cmd) { continue }
        try {
            $output = & $name --version 2>&1
            if ($LASTEXITCODE -eq 0 -and "$output" -match '^Python\s+\d+\.\d+' -and (Test-PythonMinVersion $cmd.Source)) {
                return $cmd.Source
            }
        } catch {}
    }
    return $null
}

function Install-WindowsPython {
    <#
    .SYNOPSIS
        Python 미설치 시 winget 으로 Python 3.14 user-scope 자동 설치를 시도한다.
    .NOTES
        - 옵트아웃: 환경변수 OPAL_AUTO_INSTALL_PYTHON=0
        - winget 미보유 / 비관리자 환경 / 설치 실패 시 graceful 폴백 ($false 반환)
        - 설치 직후 PATH 즉시 반영 안 됨 — User+Machine PATH 결합 + 표준 경로 직접 탐색으로 보완
        - winget 의 native stderr 가 NativeCommandError(RemoteException)로 변환되어
          $ErrorActionPreference='Stop' 와 결합 시 throw 되는 결함 회피 위해 ErrorAction 격리
    .OUTPUTS
        설치 후 Find-Python 성공 시 $true, 아니면 $false.
    #>
    if ($env:OPAL_AUTO_INSTALL_PYTHON -eq '0') {
        Write-OpalInfo 'Python 자동 설치 옵트아웃(OPAL_AUTO_INSTALL_PYTHON=0) — 스킵.'
        return $false
    }

    if (-not (Get-Command 'winget' -ErrorAction SilentlyContinue)) {
        Write-OpalWarn 'winget 미보유 — Python 자동 설치 불가.'
        Write-OpalInfo '  수동 설치: https://www.python.org/downloads/windows/ (PATH 추가 옵션 체크)'
        return $false
    }

    Write-OpalInfo "Python 미설치 또는 최소 버전 미달 감지 — winget 으로 Python $OpalPythonTarget 자동 설치 시도 중..."
    $prevErrPref = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    $exit = 1
    try {
        & winget install --id "Python.Python.$OpalPythonTarget" --silent --accept-package-agreements --accept-source-agreements --scope user 2>&1 | Out-Host
        $exit = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $prevErrPref
    }

    if ($exit -ne 0) {
        Write-OpalWarn "winget Python $OpalPythonTarget 설치 실패 (exit=$exit) — 수동 설치 권장."
        Write-OpalInfo '  수동 설치: https://www.python.org/downloads/windows/'
        return $false
    }

    # 설치 직후 PATH 새로고침 — winget 은 현재 세션 $env:Path 를 갱신하지 않음.
    $machinePath = [Environment]::GetEnvironmentVariable('Path', 'Machine')
    $userPath    = [Environment]::GetEnvironmentVariable('Path', 'User')
    if ($machinePath -or $userPath) {
        $env:Path = "$machinePath;$userPath"
    }

    $py = Find-Python
    if ($py) {
        Write-OpalOk "Python $OpalPythonTarget 자동 설치 완료: $py"
        return $true
    }

    # PATH 갱신 후에도 미발견 시 winget 표준 user-scope 설치 경로 직접 탐색.
    $pyFolderName = "Python$($OpalPythonTarget -replace '\.', '')"
    $candidates = @(
        (Join-Path $env:LOCALAPPDATA "Programs\Python\$pyFolderName\python.exe"),
        (Join-Path ${env:ProgramFiles} "$pyFolderName\python.exe")
    )
    foreach ($c in $candidates) {
        if ($c -and (Test-Path $c)) {
            $dir = Split-Path -Parent $c
            $env:Path = "$dir;$($env:Path)"
            Write-OpalOk "Python $OpalPythonTarget 자동 설치 완료(직접 탐색): $c"
            return $true
        }
    }

    Write-OpalWarn "Python $OpalPythonTarget 설치는 끝났으나 현재 세션에서 탐색 실패 — 새 PowerShell 세션에서 재설치 시도 권장."
    return $false
}

function Find-Node {
    <#
    .SYNOPSIS
        Node.js 검출 (선택 의존성).
    .OUTPUTS
        @{ Path; Version } 또는 $null
    #>
    $cmd = Get-Command node -ErrorAction SilentlyContinue
    if (-not $cmd) { return $null }
    try {
        $output = & node --version 2>&1
        if ($LASTEXITCODE -eq 0 -and "$output" -match '^v(\d+)\.') {
            return @{ Path = $cmd.Source; Version = [int]$matches[1] }
        }
    } catch {}
    return $null
}

function Find-GitBash {
    <#
    .SYNOPSIS
        Git for Windows 의 bash.exe 경로를 탐색한다 (WSL 의 bash.exe 우회 목적).
    .NOTES
        Windows PATH 의 bash.exe 는 보통 WSL 런처라 /bin/bash 부재 시 실패.
        Git Bash 의 bash.exe 를 explicit 경로로 호출해야 opal-cli.cmd 가 정상 동작.
    .OUTPUTS
        bash.exe 절대 경로 또는 $null
    #>
    $candidates = @(
        'C:\Program Files\Git\bin\bash.exe',
        'C:\Program Files\Git\usr\bin\bash.exe',
        'C:\Program Files (x86)\Git\bin\bash.exe',
        "$env:LOCALAPPDATA\Programs\Git\bin\bash.exe"
    )
    foreach ($c in $candidates) {
        if (Test-Path -LiteralPath $c) { return $c }
    }
    # git.exe 경로 기반 추정
    $gitCmd = Get-Command git -ErrorAction SilentlyContinue
    if ($gitCmd) {
        $gitDir = Split-Path -Parent $gitCmd.Source
        $derived = @(
            (Join-Path (Split-Path -Parent $gitDir) 'bin\bash.exe'),
            (Join-Path $gitDir 'bash.exe')
        )
        foreach ($c in $derived) {
            if (Test-Path -LiteralPath $c) { return $c }
        }
    }
    return $null
}

function Register-OpalBin {
    <#
    .SYNOPSIS
        ~/.opal/bin/opal-cli 래퍼 스크립트를 생성한다.
        Windows 에서는 symlink 대신 .cmd 래퍼 또는 PowerShell 래퍼를 사용한다.
        bash 는 Git for Windows 의 bash.exe 를 explicit 경로로 호출 (WSL 의존 제거).
    .NOTES
        macOS 대칭: scripts/install-mac.sh install_opal_bin() — ln -sfn 으로 symlink 생성.
    #>
    $cliTarget = [IO.Path]::Combine($OpalHome, 'tools', 'opal-cli', 'run.sh')
    $cliWrapper = Join-Path $OpalBinDir 'opal-cli.cmd'
    $cliPs1Old  = Join-Path $OpalBinDir 'opal-cli.ps1'

    if (-not (Test-Path $cliTarget)) {
        Write-OpalWarn "opal-cli/run.sh 부재 — bin 생성 스킵 (Step 3 완료 후 재실행 필요)."
        return
    }

    if (-not (Test-Path $OpalBinDir)) {
        New-Item -ItemType Directory -Path $OpalBinDir -Force | Out-Null
    }

    # bash.exe 경로 결정 — Git for Windows 우선 (WSL 우회)
    $bashExe = Find-GitBash
    if ($bashExe) {
        Write-OpalInfo "Git Bash 발견: $bashExe"
    } else {
        Write-OpalWarn 'Git Bash 미발견 — PATH 의 bash 사용 (WSL 일 수 있음).'
        Write-OpalWarn 'opal-cli 가 동작하지 않으면 Git for Windows 설치: https://git-scm.com/download/win'
        $bashExe = 'bash'
    }

    $runScriptPosix = $cliTarget -replace '\\', '/'

    # .cmd 래퍼 (cmd.exe 환경)
    if ($bashExe -eq 'bash') {
        $cmdContent = "@echo off`r`nbash `"$runScriptPosix`" %*`r`n"
    } else {
        $cmdContent = "@echo off`r`n`"$bashExe`" `"$runScriptPosix`" %*`r`n"
    }
    Set-Content -Path $cliWrapper -Value $cmdContent -Encoding ASCII
    Write-OpalOk "opal-cli.cmd 래퍼 생성: $cliWrapper"

    # opal-cli.ps1 은 만들지 않는다 — PowerShell default ExecutionPolicy(Restricted) 가 .ps1 을 차단하므로
    # 사용자가 PowerShell 에서도 .cmd 가 자동 호출되도록 PATHEXT 매칭에 위임한다.
    # 옛 .ps1 잔존 파일이 있으면 제거 (PowerShell 이 .ps1 을 우선시하면 ExecutionPolicy 차단으로 실패)
    if (Test-Path -LiteralPath $cliPs1Old) {
        Remove-Item -Force -LiteralPath $cliPs1Old -ErrorAction SilentlyContinue
        Write-OpalInfo 'opal-cli.ps1 제거 (PowerShell ExecutionPolicy 차단 회피, .cmd 사용으로 위임)'
    }
}

function Register-EnvPath {
    <#
    .SYNOPSIS
        사용자 PATH 환경 변수에 ~/.opal/bin 을 idempotent 하게 추가한다.
    .NOTES
        macOS 대칭: scripts/install-mac.sh register_path_in_shell_rc() — ~/.zshrc / ~/.bashrc.
        Windows 에서는 HKCU 사용자 환경 변수 PATH 를 직접 수정한다.
        현재 세션에는 즉시 반영; 이후 세션에는 재로그인 후 반영된다.
    #>
    $marker = $OpalBinDir

    $currentPath = [System.Environment]::GetEnvironmentVariable('PATH', 'User')
    if ($null -eq $currentPath) { $currentPath = '' }

    if ($currentPath -split ';' | Where-Object { $_ -eq $marker }) {
        Write-OpalOk "PATH 이미 등록됨: $marker"
    }
    else {
        $newPath = "$marker;$currentPath".TrimEnd(';')
        [System.Environment]::SetEnvironmentVariable('PATH', $newPath, 'User')
        Write-OpalOk "PATH 등록 완료: $marker"
    }

    # 현재 세션 PATH 에도 즉시 반영
    if ($env:PATH -notmatch [regex]::Escape($marker)) {
        $env:PATH = "$marker;$env:PATH"
    }

    # 사용 방법 안내 (macOS install_opal_bin과 동등)
    Write-Host ''
    Write-OpalInfo 'opal-cli 사용 방법:'
    Write-Host '    1) 현재 PowerShell 세션은 즉시 사용 가능 (위에서 $env:PATH 자동 갱신).'
    Write-Host '    2) 다른 세션/창에서는 다음 중 하나로 적용:'
    Write-Host '         - 새 터미널 창 열기 (PowerShell / Windows Terminal / cmd)'
    Write-Host '         - 같은 세션 강제 새로고침: $env:PATH = [Environment]::GetEnvironmentVariable("PATH","User") + ";" + $env:PATH'
    Write-Host '         - Chocolatey 사용 시: refreshenv'
    Write-Host ''
    Write-Host '    검증:'
    Write-Host '         opal-cli --version    # 버전 출력'
    Write-Host '         opal-cli doctor       # 환경 진단 (4섹션)'
    Write-Host ''
    Write-Host '    PATH 미적용 시 절대 경로 호출도 가능:'
    Write-Host '         %USERPROFILE%\.opal\bin\opal-cli.cmd doctor    (cmd / PowerShell 모두 동작)'
    Write-Host ''
}

function Register-Bootstrapper {
    <#
    .SYNOPSIS
        AI 플랫폼 부트스트래퍼 마커를 삽입한다.
        Claude / Cursor / Gemini(+HARDENING) 모두 처리.
    .NOTES
        macOS: scripts/install-mac.sh install_opal_section / install_gemini_hardening 이식.
    #>
    param([Parameter(Mandatory)][string]$RepoRoot)

    $bsDir = [IO.Path]::Combine($RepoRoot, 'opal', 'bootstrapper')
    $userHome = $env:USERPROFILE

    Write-OpalInfo 'OPAL 부트스트래퍼 설치...'

    # ── Claude ──
    $claudeSnippet = [IO.Path]::Combine($bsDir, 'claude-bootstrap.md')
    $claudeTarget  = [IO.Path]::Combine($userHome, '.claude', 'CLAUDE.md')
    if (Test-Path $claudeSnippet) {
        Install-OpalSection -SnippetPath $claudeSnippet -Target $claudeTarget -Label 'Claude'
    }

    # ── Cursor: 단일 .mdc 파일 (CRLF 정규화 + BOM 미부착) ──
    # 단순 Copy-Item 은 mac 에서 만든 LF 줄끝을 그대로 옮긴다. Cursor for Windows 의
    # frontmatter 파서가 LF only 파일에서 '---' 매칭을 실패하여 user-level 룰이 활성화되지 않던 결함 회피.
    $cursorSnippet = [IO.Path]::Combine($bsDir, 'cursor-bootstrap.mdc')
    $cursorTarget  = [IO.Path]::Combine($userHome, '.cursor', 'rules', '000-opal-agent.mdc')
    if (Test-Path $cursorSnippet) {
        $cursorDir = Split-Path -Parent $cursorTarget
        if (-not (Test-Path $cursorDir)) {
            New-Item -ItemType Directory -Path $cursorDir -Force | Out-Null
        }
        $raw = Get-Content -Path $cursorSnippet -Raw -Encoding UTF8
        $normalized = ($raw -replace "`r`n", "`n") -replace "`n", "`r`n"
        Set-ContentNoBom -Path $cursorTarget -Value $normalized
        Write-OpalOk "Cursor OPAL → $cursorTarget (CRLF 정규화)"
    }
    # 레거시 R2 규칙 정리
    $legacyR2 = [IO.Path]::Combine($userHome, '.cursor', 'rules', '000-r2-persona.mdc')
    if (Test-Path $legacyR2) {
        Remove-Item -Force -Path $legacyR2
        Write-OpalOk 'Cursor 기존 R2 규칙 제거: 000-r2-persona.mdc'
    }

    # ── Gemini OPAL ──
    $geminiSnippet = [IO.Path]::Combine($bsDir, 'gemini-bootstrap.md')
    $geminiTarget  = [IO.Path]::Combine($userHome, '.gemini', 'GEMINI.md')
    if (Test-Path $geminiSnippet) {
        Install-OpalSection -SnippetPath $geminiSnippet -Target $geminiTarget -Label 'Gemini'
    }

    # ── Gemini HARDENING (동일 GEMINI.md 에 별도 마커 영역) ──
    $hardeningSnippet = [IO.Path]::Combine($bsDir, 'gemini-hardening.md')
    if (Test-Path $hardeningSnippet) {
        Install-GeminiHardening -SnippetPath $hardeningSnippet -Target $geminiTarget
    }

    # ── Codex ──
    $codexSnippet = [IO.Path]::Combine($bsDir, 'codex-bootstrap.md')
    $codexTarget  = [IO.Path]::Combine($userHome, '.codex', 'AGENTS.md')
    if (Test-Path $codexSnippet) {
        Install-OpalSection -SnippetPath $codexSnippet -Target $codexTarget -Label 'Codex'
    }
}

# ─── Install-OpalVenv (install-mac.sh install_opal_venv 이식) ──────────────

function Install-OpalVenv {
    <#
    .SYNOPSIS
        ~/.opal/.venv 생성 + opal/tools/requirements.txt 설치.
        Python 미설치 시 graceful 스킵 + 설치 안내.
    #>
    param([Parameter(Mandatory)][string]$RepoRoot)

    $req = [IO.Path]::Combine($RepoRoot, 'opal', 'tools', 'requirements.txt')
    if (-not (Test-Path $req)) {
        Write-OpalWarn 'opal/tools/requirements.txt 없음 — Python venv 스킵'
        return
    }

    $py = Find-Python
    if (-not $py) {
        Write-OpalWarn "Python ${OpalPythonMin} 이상 미확보 — Python venv 스킵 (xlsx-tool / Playwright / 일부 MCP 도구 동작 제한)"
        Write-OpalInfo '설치 옵션:'
        Write-OpalInfo "  winget install Python.Python.$OpalPythonTarget"
        Write-OpalInfo '  또는 https://www.python.org/downloads/windows/ (PATH 추가 옵션 체크)'
        Write-OpalInfo '  (자동 설치 옵트아웃: $env:OPAL_AUTO_INSTALL_PYTHON=0)'
        return
    }
    Write-OpalInfo "Python 발견: $py"

    $venvDir = Join-Path $OpalHome '.venv'
    if (-not (Test-Path $venvDir)) {
        Write-OpalInfo '~/.opal/.venv 생성 중...'
        # native command stderr 격리 (5.x NativeCommandError 회피)
        $prevErrPref = $ErrorActionPreference
        $ErrorActionPreference = 'Continue'
        try {
            & $py -m venv $venvDir 2>&1 | Out-Null
        } finally {
            $ErrorActionPreference = $prevErrPref
        }
        if ($LASTEXITCODE -ne 0) {
            Write-OpalWarn 'venv 생성 실패 — Python venv 스킵'
            return
        }
        Write-OpalOk "venv 생성: $venvDir"
    } else {
        Write-OpalInfo "venv 기존 사용: $venvDir"
    }

    # Windows venv: Scripts/python.exe / Scripts/pip.exe
    $venvPip = [IO.Path]::Combine($venvDir, 'Scripts', 'pip.exe')
    if (-not (Test-Path $venvPip)) {
        # 비호환 venv (mac/linux 형식)
        $venvPip = [IO.Path]::Combine($venvDir, 'bin', 'pip')
    }
    if (-not (Test-Path $venvPip)) {
        Write-OpalWarn "venv pip 없음: $venvPip — 패키지 설치 스킵"
        return
    }

    Write-OpalInfo 'pip 업그레이드 + requirements.txt 설치 중...'
    # pip 호출 격리:
    #   - PowerShell 의 native command stderr 가 NativeCommandError(RemoteException)로 변환되어
    #     $ErrorActionPreference='Stop' 와 결합 시 throw 되는 결함 회피.
    #   - pip 자기 자신 업그레이드는 venvPip 직접 호출 대신 python -m pip 로 — Windows 의 pip.exe 자기교체 잠금 회피.
    $venvPython = [IO.Path]::Combine($venvDir, 'Scripts', 'python.exe')
    if (-not (Test-Path $venvPython)) {
        $venvPython = [IO.Path]::Combine($venvDir, 'bin', 'python')
    }
    $prevErrPref = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    $pipUpgradeExit = 0
    $pipInstallExit = 0
    try {
        if (Test-Path $venvPython) {
            & $venvPython -m pip install --quiet --no-cache-dir --upgrade pip 2>&1 | Out-Null
            $pipUpgradeExit = $LASTEXITCODE
        } else {
            & $venvPip install --quiet --no-cache-dir --upgrade pip 2>&1 | Out-Null
            $pipUpgradeExit = $LASTEXITCODE
        }
        & $venvPip install --quiet --no-cache-dir -r $req 2>&1 | Out-Null
        $pipInstallExit = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $prevErrPref
    }
    if ($pipInstallExit -eq 0) {
        Write-OpalOk 'Python 패키지 설치 완료 (requirements.txt)'
    } else {
        Write-OpalWarn "pip install 부분 실패 (upgrade=$pipUpgradeExit, install=$pipInstallExit) — 일부 패키지 누락 가능"
    }

    # Playwright 브라우저 — chromium 미설치 시에만 안내 (자동 설치 안 함, 다운로드 시간/대역폭 부담)
    $playwrightExe = [IO.Path]::Combine($venvDir, 'Scripts', 'playwright.exe')
    if (Test-Path $playwrightExe) {
        $pwBrowsersDir = if ($env:PLAYWRIGHT_BROWSERS_PATH) {
            $env:PLAYWRIGHT_BROWSERS_PATH
        } else {
            Join-Path $env:LOCALAPPDATA 'ms-playwright'
        }
        $hasChromium = $false
        if (Test-Path $pwBrowsersDir) {
            $chromiumDir = Get-ChildItem -Path $pwBrowsersDir -Filter 'chromium-*' -Directory -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($chromiumDir) { $hasChromium = $true }
        }
        if (-not $hasChromium) {
            Write-OpalInfo 'Playwright 브라우저 설치 (선택, 약 200MB):'
            Write-OpalInfo "  & `"$playwrightExe`" install chromium"
        }
    }
}

# ─── Install-Dashboard (install-mac.sh install_dashboard 이식) ─────────────

function Install-Dashboard {
    <#
    .SYNOPSIS
        OPAL Console 대시보드를 ~/.opal/dashboard-server/ 에 배포한다.
        install-mac.sh install_dashboard() 와 의미상 동등.
        - dashboard/frontend: npm.cmd install && npm.cmd run build → dist/ 복사
        - dashboard/backend:  BE를 dashboard/backend/ 패키지 구조로 복사
          (dashboard/__init__.py 생성 → 'from dashboard.backend...' 절대 import 동작)
        Node 미설치 또는 dashboard/ 소스 없으면 graceful skip.
    #>
    param([Parameter(Mandatory)][string]$RepoRoot)

    $src = [IO.Path]::Combine($RepoRoot, 'dashboard')
    $dst = Join-Path $OpalHome 'dashboard-server'

    # dashboard/ 소스가 없으면 graceful skip
    if (-not (Test-Path $src)) {
        Write-OpalInfo 'dashboard/ 소스 미존재 — OPAL Console 설치 스킵'
        return
    }

    Write-Host ''
    Write-OpalInfo 'OPAL Console 설치 중...'

    # ── FE 빌드 (Node 필요) ──
    $node = Find-Node
    $frontendSrc = [IO.Path]::Combine($src, 'frontend')
    if ($node -and (Test-Path $frontendSrc)) {
        Write-OpalInfo "Node 발견 ($node) — FE 빌드 시작..."
        # npm.cmd 사용 (Windows .cmd shim — CVE-2024-27980 대응, v1.5.0과 동일 패턴)
        $npmCmd = 'npm.cmd'
        try {
            $ErrorActionPreference = 'Continue'
            Push-Location $frontendSrc
            & $npmCmd install --silent 2>&1 | Out-Null
            & $npmCmd run build 2>&1 | Out-Null
            Pop-Location
            $ErrorActionPreference = 'Stop'

            # dist/ → ~/.opal/dashboard-server/dist/
            $distSrc = [IO.Path]::Combine($frontendSrc, 'dist')
            $distDst = Join-Path $dst 'dist'
            if (Test-Path $distSrc) {
                if (-not (Test-Path $distDst)) {
                    New-Item -ItemType Directory -Path $distDst -Force | Out-Null
                }
                Copy-Item -Path "$distSrc\*" -Destination $distDst -Recurse -Force
                Write-OpalOk "Console FE dist → $distDst"
            } else {
                Write-OpalWarn 'FE 빌드 후 dist/ 없음 — FE 배포 스킵'
            }
        } catch {
            $ErrorActionPreference = 'Stop'
            Write-OpalWarn "FE 빌드 실패 ($_) — Console FE 배포 스킵"
        }
    } else {
        Write-OpalWarn 'Node 미설치 또는 dashboard/frontend 없음 — FE 빌드 스킵 (node 설치 후 재실행 권장)'
    }

    # ── BE 복사 (패키지 구조 유지: dashboard/backend/) ──
    # main.py의 'from dashboard.backend.routers import ...' 절대 import가 동작하려면
    # --app-dir ~/.opal/dashboard-server 기준으로 dashboard/ 패키지가 존재해야 함.
    # → BE를 dashboard/backend/로 복사하고 dashboard/__init__.py 생성.
    $backendSrc = [IO.Path]::Combine($src, 'backend')
    $backendDst = Join-Path $dst 'dashboard\backend'
    if (Test-Path $backendSrc) {
        if (-not (Test-Path $backendDst)) {
            New-Item -ItemType Directory -Path $backendDst -Force | Out-Null
        }
        Copy-Item -Path "$backendSrc\*" -Destination $backendDst -Recurse -Force
        Write-OpalOk "Console BE → $backendDst"

        # dashboard 패키지 루트 __init__.py 생성 (없으면)
        $pkgInit = Join-Path $dst 'dashboard\__init__.py'
        if (-not (Test-Path $pkgInit)) {
            New-Item -ItemType File -Path $pkgInit -Force | Out-Null
        }
        Write-OpalOk "Console BE 패키지 구조 생성 → $pkgInit"
    } else {
        Write-OpalWarn 'dashboard/backend 없음 — BE 배포 스킵'
    }

    # ── console.config.json 자동 생성/갱신 (install_dashboard() console scan 연동 이식, 057) ──
    # mac: opal-cli console scan(bash find + python3 머지)의 PowerShell 네이티브 등가.
    # .opal\AGENT.md 마커 탐색 → 프로젝트 부모 디렉터리를 scan_roots 로 병합(보존+추가+dedup, prune 없음).
    # 실패해도 install 을 중단하지 않는다(try/catch 격리 — H-7 windows 등가, TS-011/TS-014).
    try {
        $scanConfigPath = Join-Path $OpalHome 'console.config.json'
        $scanBase       = $env:USERPROFILE
        $scanMaxDepth   = 5
        $scanExclude    = @('node_modules', '.git', '.venv', '__pycache__', '.DS_Store')

        # AGENT.md 마커 탐색 (console.sh scan 의 find '*/.opal/AGENT.md' 규칙과 동일 의미).
        # Get-ChildItem 은 bash find -prune 처럼 사전 가지치기를 지원하지 않으므로,
        # 탐색 후 경로 문자열 필터링으로 exclude 를 등가 적용한다(정확성 유지, 성능은 저하 — 코드 리뷰 수준).
        $allMarkers = Get-ChildItem -Path $scanBase -Recurse -Depth $scanMaxDepth -Filter 'AGENT.md' -File -ErrorAction SilentlyContinue
        $discoveredRoots = New-Object System.Collections.Generic.List[string]
        foreach ($marker in $allMarkers) {
            $opalDir = $marker.DirectoryName
            if ((Split-Path $opalDir -Leaf) -ne '.opal') { continue }

            $excluded = $false
            foreach ($ex in $scanExclude) {
                if ($opalDir -match [regex]::Escape("\$ex\")) { $excluded = $true; break }
            }
            if ($excluded) { continue }

            # OPAL 홈 자체가 마커로 잡히면 discovery 에서 제외 (H-2 windows 등가 — $OpalHome\AGENT.md 오탐 방지)
            if ($opalDir -eq $OpalHome) { continue }

            $projectDir = Split-Path $opalDir -Parent
            $scanRoot   = Split-Path $projectDir -Parent
            if (-not $discoveredRoots.Contains($scanRoot)) {
                [void]$discoveredRoots.Add($scanRoot)
            }
        }

        # 기존 console.config.json 로드(있으면 ConvertFrom-Json) → scan_roots 머지 → ConvertTo-Json 재기록.
        # 파싱 실패(손상 JSON) 시 예외가 catch 로 전파되어 write 하지 않는다.
        $scanExisted = Test-Path $scanConfigPath
        $scanData = [ordered]@{}
        if ($scanExisted) {
            $scanRaw = Get-Content -Path $scanConfigPath -Raw
            if (-not [string]::IsNullOrWhiteSpace($scanRaw)) {
                $scanParsed = $scanRaw | ConvertFrom-Json
                foreach ($prop in $scanParsed.PSObject.Properties) { $scanData[$prop.Name] = $prop.Value }
            }
        }

        $existingRoots = @()
        if ($scanData.Contains('scan_roots')) { $existingRoots = @($scanData['scan_roots']) }

        # 보존 + 추가 + dedup (--prune 미적용 — install 연동 기본, C-3 등가)
        $mergedRoots = New-Object System.Collections.Generic.List[string]
        foreach ($r in $existingRoots) { if (-not $mergedRoots.Contains($r)) { [void]$mergedRoots.Add($r) } }
        foreach ($r in $discoveredRoots) { if (-not $mergedRoots.Contains($r)) { [void]$mergedRoots.Add($r) } }
        $scanData['scan_roots'] = @($mergedRoots)

        if (-not $scanExisted) {
            # 신규 생성 시에만 기본값 기록 (config.py DEFAULT_SCAN_DEPTH/DEFAULT_EXCLUDE 와 동일)
            if (-not $scanData.Contains('scan_depth')) { $scanData['scan_depth'] = 2 }
            if (-not $scanData.Contains('exclude')) { $scanData['exclude'] = $scanExclude }
        }

        ($scanData | ConvertTo-Json -Depth 5) | Set-Content -Path $scanConfigPath -Encoding utf8
        Write-OpalOk "console.config.json 갱신 완료 → $scanConfigPath"
    } catch {
        Write-OpalWarn "console scan 실패 — 프로젝트 자동 탐색을 건너뜁니다 (수동: opal-cli console scan <경로>): $_"
    }

    Write-Host ''
    Write-OpalOk "OPAL Console 설치 완료 → $dst"
    Write-OpalInfo '기동 (Git Bash): opal-cli console start'
}

# ─── Start-OpalConsole (install-mac.sh console_autostart 이식) ─────────────

function Stop-OpalConsole {
    <#
    .SYNOPSIS
        실행 중인 OPAL Console 데몬(uvicorn dashboard.backend.main:app)을 종료한다.
    .NOTES
        macOS: pkill -f "dashboard.backend.main:app" 이식.
        Windows: WMI 또는 Get-Process + CommandLine 필터로 해당 프로세스를 종료.
    #>
    try {
        $procs = Get-CimInstance Win32_Process -Filter "Name = 'python.exe' OR Name = 'uvicorn.exe'" -ErrorAction SilentlyContinue
        $killed = 0
        foreach ($proc in $procs) {
            if ($proc.CommandLine -and $proc.CommandLine -match 'dashboard\.backend\.main:app') {
                Stop-Process -Id $proc.ProcessId -Force -ErrorAction SilentlyContinue
                $killed++
            }
        }
        if ($killed -gt 0) {
            Write-OpalOk "OPAL Console 데몬 ${killed}개 종료됨."
        }
    } catch {
        Write-OpalWarn "프로세스 종료 중 오류 (무시): $_"
    }
}

function Start-OpalConsole {
    <#
    .SYNOPSIS
        Install-Dashboard 후 OPAL Console 데몬을 자동 기동한다.
        기존 프로세스를 종료(Stop-OpalConsole)하고 Start-Process 로 백그라운드 기동.
        기동 후 /health 를 최대 10초 폴링하여 확인하고 접속 안내를 출력한다.
    .NOTES
        macOS: scripts/install-mac.sh console_autostart() 와 의미상 동등.
        Windows 플랫폼 분기 격리(CONVENTIONS) — Start-Process / WMI 는 이 함수에만 사용.
    #>

    $venvDir       = Join-Path $OpalHome '.venv'
    $uvicorn       = [IO.Path]::Combine($venvDir, 'Scripts', 'uvicorn.exe')
    $dashboardServer = Join-Path $OpalHome 'dashboard-server'
    $dashboardPkg  = [IO.Path]::Combine($dashboardServer, 'dashboard', 'backend')
    $opalCliBin    = Join-Path $OpalHome 'bin\opal-cli.cmd'
    $host          = '127.0.0.1'
    $port          = '7823'
    $healthUrl     = "http://${host}:${port}/health"
    $logFile       = [IO.Path]::Combine($env:TEMP, 'opal-console.log')

    Write-Host ''
    Write-OpalInfo 'OPAL Console 자동 재시작 중...'

    # ── 전제 점검 ──
    if (-not (Test-Path $dashboardPkg)) {
        Write-OpalWarn "dashboard-server/dashboard/backend 없음 — 서버 기동 스킵"
        Write-OpalInfo 'Install-Dashboard 가 정상 완료되었는지 확인하세요.'
        return
    }

    if (-not (Test-Path $uvicorn)) {
        Write-OpalWarn "uvicorn 미설치: $uvicorn"
        Write-OpalInfo 'Python venv를 먼저 설치하세요 (Install-OpalVenv).'
        return
    }

    # ── 기존 데몬 종료 ──
    Stop-OpalConsole
    # 종료 대기 (최대 3초)
    $waited = 0
    while ($waited -lt 3) {
        try {
            $resp = Invoke-WebRequest -Uri $healthUrl -TimeoutSec 1 -ErrorAction Stop
            Start-Sleep -Seconds 1
            $waited++
        } catch { break }
    }

    # ── 신규 기동 ──
    $startArgs = @(
        '--app-dir', $dashboardServer,
        'dashboard.backend.main:app',
        '--host', $host,
        '--port', $port
    )
    $proc = Start-Process -FilePath $uvicorn `
        -ArgumentList $startArgs `
        -RedirectStandardOutput $logFile `
        -RedirectStandardError  $logFile `
        -WindowStyle Hidden `
        -PassThru `
        -ErrorAction SilentlyContinue
    if ($proc) {
        Write-OpalOk "OPAL Console 기동됨 (PID: $($proc.Id), 로그: $logFile)"
    }

    # ── /health 확인 (최대 10초 대기) ──
    $ok = $false
    $healthBody = ''
    for ($i = 1; $i -le 10; $i++) {
        Start-Sleep -Seconds 1
        try {
            $resp = Invoke-WebRequest -Uri $healthUrl -TimeoutSec 2 -ErrorAction Stop
            $ok = $true
            $healthBody = $resp.Content
            break
        } catch {}
    }

    Write-Host ''
    if ($ok) {
        Write-OpalOk 'OPAL Console 기동 완료'
        Write-Host "  접속: http://${host}:${port}" -ForegroundColor Cyan
        Write-Host "  /health: $healthBody" -ForegroundColor Cyan
    } else {
        Write-OpalWarn "OPAL Console /health 응답 없음 (10초 초과)"
        Write-OpalInfo "로그 확인: Get-Content '$logFile'"
        Write-OpalInfo '수동 기동 (Git Bash): opal-cli console start'
    }
}

# ─── Install-OpalMcp (install-mac.sh install_mcp 이식) ──────────────────────

function Convert-McpConfigForWindows {
    <#
    .SYNOPSIS
        MCP config 의 command/args 를 Windows 호환 형식으로 변환한다.
    .DESCRIPTION
        - command 가 npx / npm 이면 .cmd 확장자를 명시한 직접 호출 (npx.cmd / npm.cmd) 로 변경.
          npm 은 Windows 에서 .cmd shim 만 제공하므로 확장자 없는 'npx' 는 child_process.spawn 에서 ENOENT.
          'cmd /c npx ...' 래핑은 PowerShell 에서는 정상 동작하지만 Claude Code 등 MCP host 의
          stdio pipe passthrough 와 함께 사용 시 자식 프로세스 stdio 가 끊기는 케이스가 있어
          npx.cmd 직접 호출이 권고된다.
        - node 는 .exe 이므로 그대로 둔다.
        - args 안의 unix 절대경로 (/tmp/...) 는 Windows 임시 경로 ($env:TEMP\...) 로 치환.
    .OUTPUTS
        새 hashtable (원본 변경 안 함).
    #>
    param([Parameter(Mandatory)][hashtable]$Config)

    $cmd = [string]$Config['command']
    $rawArgs = if ($Config.ContainsKey('args')) { @($Config['args']) } else { @() }

    # /tmp/... → $env:TEMP\... 변환
    $newArgs = @()
    foreach ($arg in $rawArgs) {
        if ($arg -is [string] -and $arg -match '^/tmp/(.*)$') {
            $sub = $Matches[1] -replace '/', '\'
            $newArgs += (Join-Path $env:TEMP $sub)
        } else {
            $newArgs += $arg
        }
    }

    $cmdMap = @{
        'npx' = 'npx.cmd'
        'npm' = 'npm.cmd'
    }
    if ($cmdMap.ContainsKey($cmd)) {
        $result = @{
            command = $cmdMap[$cmd]
            args    = $newArgs
        }
    } else {
        $result = @{
            command = $cmd
            args    = $newArgs
        }
    }

    if ($Config.ContainsKey('env')) {
        $result['env'] = $Config['env']
    }

    return $result
}

function Merge-McpConfig {
    <#
    .SYNOPSIS
        대상 JSON 파일의 mcpServers.<name> 항목에 config 를 병합한다.
        기본: 이미 있으면 스킵. -Force 시: 덮어쓰기 (Windows MCP 형식 갱신용).
    #>
    param(
        [Parameter(Mandatory)][string]$Target,
        [Parameter(Mandatory)][string]$Name,
        [Parameter(Mandatory)][hashtable]$Config,
        [switch]$Force
    )
    $targetDir = Split-Path -Parent $Target
    if (-not (Test-Path $targetDir)) {
        New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
    }

    $data = @{}
    if (Test-Path $Target) {
        try {
            $raw = Get-Content -Path $Target -Raw -Encoding UTF8
            if ($raw -and $raw.Trim()) {
                $parsed = $raw | ConvertFrom-Json -ErrorAction Stop
                # PSCustomObject → hashtable
                $data = @{}
                $parsed.PSObject.Properties | ForEach-Object { $data[$_.Name] = $_.Value }
            }
        } catch {
            Write-OpalWarn "기존 ${Target} 파싱 실패 — 새 파일로 작성"
            $data = @{}
        }
    }

    if (-not $data.ContainsKey('mcpServers')) {
        $data['mcpServers'] = @{}
    }
    $servers = if ($data['mcpServers'] -is [hashtable]) {
        $data['mcpServers']
    } else {
        $h = @{}
        $data['mcpServers'].PSObject.Properties | ForEach-Object { $h[$_.Name] = $_.Value }
        $h
    }
    if ($servers.ContainsKey($Name) -and -not $Force) {
        return $false  # 이미 등록됨, 스킵 (덮어쓰려면 -Force)
    }
    $servers[$Name] = $Config
    $data['mcpServers'] = $servers

    Set-ContentNoBom -Path $Target -Value ($data | ConvertTo-Json -Depth 10)
    return $true
}

function Install-OpalMcp {
    <#
    .SYNOPSIS
        opal/core/mcps/*.json 을 읽어 platform 별 등록.
        - claude / gemini: CLI (있으면) `<cli> mcp add` , 없으면 config_merge 폴백
        - cursor: ~/.cursor/mcp.json (config_merge)
        - antigravity: ~/.gemini/antigravity/mcp_config.json (config_merge)
    #>
    param([Parameter(Mandatory)][string]$RepoRoot)

    $mcpDir = [IO.Path]::Combine($RepoRoot, 'opal', 'core', 'mcps')
    if (-not (Test-Path $mcpDir)) {
        Write-OpalWarn 'opal/core/mcps/ 디렉토리 없음 — MCP 스킵'
        return
    }

    # fork repo banner (GC-002, R-4)
    $opalRepo = if ($env:OPAL_REPO) { $env:OPAL_REPO } else { 'ceo4ever/opal' }
    if ($opalRepo -ne 'ceo4ever/opal') {
        Write-Host ''
        Write-Host '════════════════════════════════════════════════════════'
        Write-Host "  [FORK INSTALL] OPAL_REPO=$opalRepo"
        Write-Host '  이 설치본은 OPAL 공식 저장소(ceo4ever/opal)가 아닙니다.'
        Write-Host '  MCP 서버 등록 항목을 직접 검토하세요.'
        Write-Host '════════════════════════════════════════════════════════'
        Write-Host ''
        # 비대화형: OPAL_ALLOW_FORK=1 옵트인 없으면 거부
        if ($env:OPAL_AUTO_INSTALL -eq '1' -or -not [Environment]::UserInteractive) {
            if ($env:OPAL_ALLOW_FORK -ne '1') {
                throw '[OPAL] fork repo 비대화형 설치 거부. 옵트인: $env:OPAL_ALLOW_FORK=''1'' 명시'
            }
        } else {
            $forkConfirm = Read-Host '계속하시겠습니까? [y/N]'
            if ($forkConfirm -notmatch '^[yY]$') {
                Write-OpalInfo 'MCP 설치를 건너뜁니다.'
                return
            }
        }
    }

    $userHome = $env:USERPROFILE
    $count = 0
    Get-ChildItem -Path $mcpDir -Filter '*.json' -File | ForEach-Object {
        try {
            $obj = Get-Content -Path $_.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
        } catch {
            Write-OpalWarn "MCP 설정 파싱 실패: $($_.FullName)"
            return
        }
        $name = $obj.name
        $config = @{}
        $obj.config.PSObject.Properties | ForEach-Object { $config[$_.Name] = $_.Value }
        $platforms = @($obj.platforms)
        $installType = $obj.install_type

        if ($installType -ne 'config_merge') {
            Write-OpalInfo "  ${name}: ${installType} 타입 — 수동 설치 필요"
            return
        }

        # command 화이트리스트 검증 (GC-002, R-4)
        $allowedCmds = @('npx', 'npm', 'node', 'python3', 'python')
        $rawCommand = $config['command']
        $cmdBase = [IO.Path]::GetFileNameWithoutExtension($rawCommand)
        # .cmd 확장자 제거 (npx.cmd → npx)
        if ($cmdBase -match '\.cmd$') { $cmdBase = $cmdBase -replace '\.cmd$', '' }
        if ($allowedCmds -notcontains $cmdBase) {
            Write-OpalWarn "${name}: command '$rawCommand' 화이트리스트 미통과 — 건너뜀"
            return
        }

        $installed = @()
        foreach ($platform in $platforms) {
            switch ($platform) {
                'claude' {
                    $claudeCli = Get-Command claude -ErrorAction SilentlyContinue
                    if ($claudeCli) {
                        # native stderr 격리 (idempotent 재등록 시 'already exists' / 'not found' 등을
                        # 5.x 에서 NativeCommandError 로 변환하여 throw 하는 결함 회피)
                        $prevErrPref = $ErrorActionPreference
                        $ErrorActionPreference = 'Continue'
                        try {
                            # 기존 등록 제거 (없으면 silent fail) — Windows 호환 형식으로 갱신 보장
                            & $claudeCli.Source mcp remove $name --scope user 2>&1 | Out-Null

                            $cfgWin = Convert-McpConfigForWindows -Config $config
                            $args = @('mcp', 'add', '--scope', 'user', $name, '--', $cfgWin.command) + @($cfgWin.args)
                            & $claudeCli.Source @args 2>&1 | Out-Null
                            if ($LASTEXITCODE -eq 0) { $installed += 'claude' }
                        } finally {
                            $ErrorActionPreference = $prevErrPref
                        }
                    } else {
                        Write-OpalWarn "claude CLI 없음 — ${name} 수동 등록 필요"
                    }
                }
                'gemini' {
                    $geminiCli = Get-Command gemini -ErrorAction SilentlyContinue
                    if ($geminiCli) {
                        $prevErrPref = $ErrorActionPreference
                        $ErrorActionPreference = 'Continue'
                        try {
                            & $geminiCli.Source mcp remove -s user $name 2>&1 | Out-Null

                            $cfgWin = Convert-McpConfigForWindows -Config $config
                            $args = @('mcp', 'add', '-s', 'user', $name, '--', $cfgWin.command) + @($cfgWin.args)
                            & $geminiCli.Source @args 2>&1 | Out-Null
                            if ($LASTEXITCODE -eq 0) { $installed += 'gemini' }
                        } finally {
                            $ErrorActionPreference = $prevErrPref
                        }
                    } else {
                        # 폴백 — settings.json
                        $target = Join-Path $userHome '.gemini\settings.json'
                        $cfgWin = Convert-McpConfigForWindows -Config $config
                        if (Merge-McpConfig -Target $target -Name $name -Config $cfgWin -Force) {
                            $installed += 'gemini'
                        }
                    }
                }
                'cursor' {
                    $target = Join-Path $userHome '.cursor\mcp.json'
                    $cfgWin = Convert-McpConfigForWindows -Config $config
                    if (Merge-McpConfig -Target $target -Name $name -Config $cfgWin -Force) {
                        $installed += 'cursor'
                    }
                }
                'antigravity' {
                    $target = Join-Path $userHome '.gemini\antigravity\mcp_config.json'
                    $cfgWin = Convert-McpConfigForWindows -Config $config
                    if (Merge-McpConfig -Target $target -Name $name -Config $cfgWin -Force) {
                        $installed += 'antigravity'
                    }
                }
                'codex' {
                    $codexCli = Get-Command codex -ErrorAction SilentlyContinue
                    if ($codexCli) {
                        $prevErrPref = $ErrorActionPreference
                        $ErrorActionPreference = 'Continue'
                        try {
                            & $codexCli.Source mcp remove $name 2>&1 | Out-Null
                            $cfgWin = Convert-McpConfigForWindows -Config $config
                            $codexArgs = @('mcp', 'add', $name, '--', $cfgWin.command) + @($cfgWin.args)
                            & $codexCli.Source @codexArgs 2>&1 | Out-Null
                            if ($LASTEXITCODE -eq 0) { $installed += 'codex' }
                        } finally {
                            $ErrorActionPreference = $prevErrPref
                        }
                    } else {
                        Write-OpalWarn "codex CLI 없음 — ${name} 수동 등록 필요"
                    }
                }
            }
        }
        if ($installed.Count -gt 0) {
            Write-OpalOk "${name} MCP → $($installed -join ', ')"
            $count++
        }
    }
    if ($count -eq 0) {
        Write-OpalInfo '머지할 MCP 서버가 없습니다'
    } else {
        Write-OpalOk "MCP 서버 ${count}건 설정 완료"
    }
}

# ─── Install-PlatformAgents (install-mac.sh emit_platform_agent_adapter 이식) ──

# ─── OPAL_ADAPTER_FIELD_SPEC (105) — install-mac.sh 미러 ──────────────────
# 아래 here-string은 scripts/install-mac.sh 의 OPAL_ADAPTER_FIELD_SPEC 선언부
# (센티넬 마커로 감싼 3줄)를 텍스트 그대로 보존한 미러다. bash 문법(readonly NAME='json')을
# 그대로 옮겨야 TS-011(스펙 JSON 블록 mac/windows 바이트 diff 공집합)이 언어 독립적으로
# 성립하므로, 이 here-string 내부는 실행되지 않는 순수 데이터로만 취급한다. 실제로 소비되는
# $OpalAdapterFieldSpec 은 아래에서 이 텍스트로부터 JSON 리터럴만 잘라내 만든다.
# mac 쪽 JSON 리터럴과 바이트 동일 — 값을 바꿀 때는 양쪽을 함께 갱신한다 (§3.1.2 D-결정1).
$OpalAdapterFieldSpecMirror = @'
# >>> OPAL_ADAPTER_FIELD_SPEC >>>
readonly OPAL_ADAPTER_FIELD_SPEC='{"fields":[{"opal":"name","order":10,"platforms":{"claude":{"mode":"key","to":"name"},"cursor":{"mode":"key","to":"name"},"gemini":{"mode":"key","to":"name"},"codex":{"mode":"key","to":"name"}}},{"opal":"description","order":20,"omit_if_empty":true,"flatten":true,"platforms":{"claude":{"mode":"key","to":"description"},"cursor":{"mode":"key","to":"description"},"gemini":{"mode":"key","to":"description"},"codex":{"mode":"key","to":"description"}}},{"opal":"model","order":30,"default":"standard","platforms":{"claude":{"mode":"key","to":"model","values":{"light":"haiku","standard":"sonnet","advanced":"opus"},"fallback":"inherit"},"cursor":{"mode":"key","to":"model","values":{"light":"inherit","standard":"inherit","advanced":"inherit"},"fallback":"inherit"},"gemini":{"mode":"key","to":"model","values":{"light":"gemini-3.1-flash-lite","standard":"gemini-flash-latest","advanced":"gemini-pro-latest"},"fallback":"inherit"},"codex":{"mode":"key","to":"model","values":{"light":"gpt-5.4-mini","standard":"gpt-5.4","advanced":"gpt-5.5"},"fallback":"gpt-5.5"}}},{"opal":"effort","order":40,"platforms":{"claude":{"mode":"key","to":"effort","values":{"low":"low","medium":"medium","high":"high","xhigh":"xhigh","max":"max"}},"cursor":{"mode":"omit","note":"reserved: model_param/effort - cursor inherit policy pending"},"gemini":{"mode":"omit"},"codex":{"mode":"key","to":"model_reasoning_effort","values":{"minimal":"minimal","low":"low","medium":"medium","high":"high","xhigh":"xhigh","max":"xhigh"}}}}]}'
# <<< OPAL_ADAPTER_FIELD_SPEC <<<
'@

$OpalAdapterFieldSpecDeclPrefix = "readonly OPAL_ADAPTER_FIELD_SPEC='"
$OpalAdapterFieldSpecDeclLine = ($OpalAdapterFieldSpecMirror -split "`r?`n") |
    Where-Object { $_.StartsWith($OpalAdapterFieldSpecDeclPrefix) } |
    Select-Object -First 1
if (-not $OpalAdapterFieldSpecDeclLine) {
    throw 'OPAL_ADAPTER_FIELD_SPEC 미러 파싱 실패 — 센티넬 블록 형식이 install-mac.sh와 어긋남'
}
$OpalAdapterFieldSpec = $OpalAdapterFieldSpecDeclLine.Substring(
    $OpalAdapterFieldSpecDeclPrefix.Length,
    $OpalAdapterFieldSpecDeclLine.Length - $OpalAdapterFieldSpecDeclPrefix.Length - 1)

function ConvertTo-OpalHashtable {
    <#
    .SYNOPSIS
        ConvertFrom-Json 이 반환하는 PSCustomObject 를 재귀적으로 Hashtable/배열로 변환한다.
        PS 5.1 은 ConvertFrom-Json 의 AsHashtable 스위치를 지원하지 않으므로(PS7 전용, TS-014 위반)
        직접 재귀 변환한다(H-5).
    #>
    param($InputObject)
    if ($null -eq $InputObject) { return $null }
    if (($InputObject -is [System.Collections.IEnumerable]) -and
        ($InputObject -isnot [string]) -and
        ($InputObject -isnot [System.Collections.IDictionary])) {
        $list = @()
        foreach ($item in $InputObject) { $list += , (ConvertTo-OpalHashtable $item) }
        return , $list
    }
    if ($InputObject -is [System.Management.Automation.PSCustomObject]) {
        $ht = @{}
        foreach ($prop in $InputObject.PSObject.Properties) {
            $ht[$prop.Name] = ConvertTo-OpalHashtable $prop.Value
        }
        return $ht
    }
    return $InputObject
}

$script:OpalAdapterFieldSpecObj = ConvertTo-OpalHashtable (ConvertFrom-Json $OpalAdapterFieldSpec)
$script:OpalOmit = New-Object object

function Resolve-OpalFieldValue {
    <#
    .SYNOPSIS
        install-mac.sh resolve_value() 미러 (§3.1.2 D-결정3): values 미보유=항등,
        values 매칭, fallback, 그 외 경고 + 생략.
    .OUTPUTS
        해석된 문자열 값, 또는 생략 시 $script:OpalOmit 센티넬.
    #>
    param($PlatformSpec, [string]$Raw, [string]$Ctx, [string]$Platform)
    $values = $PlatformSpec['values']
    if (-not $values) { return $Raw }
    if ($values.ContainsKey($Raw)) { return $values[$Raw] }
    if ($PlatformSpec['fallback']) { return $PlatformSpec['fallback'] }
    Write-OpalWarn "unsupported $Ctx value '$Raw' for platform $Platform — field omitted"
    return $script:OpalOmit
}

function ConvertTo-OpalFieldPairs {
    <#
    .SYNOPSIS
        install-mac.sh build_pairs() 미러: 스펙을 order 오름차순 순회해 (필드명, 값) pair
        목록을 만든다. mode(key/model_param/omit)에만 분기한다 — 플랫폼명 리터럴 비교는
        하지 않는다(R-1 AC).
    .OUTPUTS
        @(@{Key=...; Value=...}, ...) 순서 배열.
    #>
    param($Spec, [hashtable]$Fields, [string]$Platform, [string]$AgentName)
    $pairs = New-Object System.Collections.ArrayList
    $attachGroups = @{}
    $sortedFields = $Spec['fields'] | Sort-Object { [int]$_['order'] }
    foreach ($field in $sortedFields) {
        $opalKey = $field['opal']
        $platforms = $field['platforms']
        if ((-not $platforms) -or (-not $platforms.ContainsKey($Platform))) { continue }
        $pspec = $platforms[$Platform]
        if ($pspec['mode'] -eq 'omit') { continue }

        if ($opalKey -eq 'name') {
            $raw = $AgentName
        } else {
            $raw = $Fields[$opalKey]
            if ((($null -eq $raw) -or ($raw -eq '')) -and $field['default']) {
                $raw = $field['default']
            }
            if ($field['flatten']) {
                if ($raw) { $raw = ($raw -replace '\s+', ' ').Trim() } else { $raw = '' }
            }
        }
        if ($null -eq $raw) { continue }
        if (($raw -eq '') -and $field['omit_if_empty']) { continue }

        $resolved = Resolve-OpalFieldValue -PlatformSpec $pspec -Raw $raw -Ctx $opalKey -Platform $Platform
        if ($resolved -eq $script:OpalOmit) { continue }

        $mode = $pspec['mode']
        if ($mode -eq 'key') {
            $to = if ($pspec['to']) { $pspec['to'] } else { $opalKey }
            [void]$pairs.Add(@{ Key = $to; Value = $resolved })
        } elseif ($mode -eq 'model_param') {
            $attach = if ($pspec['attach']) { $pspec['attach'] } else { 'model' }
            $to = if ($pspec['to']) { $pspec['to'] } else { $opalKey }
            if (-not $attachGroups.ContainsKey($attach)) { $attachGroups[$attach] = New-Object System.Collections.ArrayList }
            [void]$attachGroups[$attach].Add(@{ Key = $to; Value = $resolved })
        }
    }
    foreach ($attachKey in $attachGroups.Keys) {
        foreach ($pair in $pairs) {
            if ($pair.Key -eq $attachKey) {
                $composed = ($attachGroups[$attachKey] | ForEach-Object { "$($_.Key)=$($_.Value)" }) -join ','
                $pair.Value = "$($pair.Value)[$composed]"
                break
            }
        }
    }
    return $pairs
}

function Get-OpalModelLevelMap {
    <#
    .SYNOPSIS
        install-mac.sh model_level_map() 미러 — 본문 인라인 model 레벨 sub-dispatch 토큰
        치환용 {light,standard,advanced}→실모델명 (H-8 계약 유지, Convert-BodyModelTokens 소비).
    #>
    param($Spec, [string]$Platform)
    foreach ($field in $Spec['fields']) {
        if ($field['opal'] -eq 'model') {
            $platforms = $field['platforms']
            if ($platforms -and $platforms.ContainsKey($Platform) -and $platforms[$Platform]['values']) {
                return $platforms[$Platform]['values']
            }
            return @{}
        }
    }
    return @{}
}

function Get-AgentFrontmatter {
    <#
    .SYNOPSIS
        AGENT.md 의 YAML frontmatter 를 정규식 기반으로 파싱한다(PyYAML 미의존).
        105 이전에는 name/description/model 3키만 switch 로 추출해 확장 필드(effort 등)가
        파싱 단계에서 소실됐다(H-5) — 이제 전 키를 Fields 해시로 수집한다.
    .OUTPUTS
        @{ Name; Description; Model; Body; Fields } — Name/Description/Model/Body 4키는
        기존 호출부 하위호환을 위해 유지, Fields 는 frontmatter 전체 key→value(문자열) 해시.
    #>
    param([Parameter(Mandatory)][string]$Path)
    $raw = Get-Content -Path $Path -Raw -Encoding UTF8
    if ($raw -notmatch '(?s)^---\r?\n(.*?)\r?\n---\r?\n?(.*)$') {
        return $null
    }
    $fmRaw = $matches[1]
    $body = $matches[2]

    $fields = @{}
    $lines = $fmRaw -split "`r?`n"
    for ($i = 0; $i -lt $lines.Count; $i++) {
        $line = $lines[$i]
        if ($line -match '^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)$') {
            $key = $matches[1]
            $val = $matches[2].Trim()
            # `|` 또는 `>` 블록 스타일 — 들여쓰기 라인 모두 수집
            if ($val -in @('|', '>', '|-', '>-', '|+', '>+')) {
                $blockLines = @()
                $j = $i + 1
                while ($j -lt $lines.Count) {
                    $nxt = $lines[$j]
                    if ($nxt -match '^\s+\S' -or $nxt.Trim() -eq '') {
                        $blockLines += $nxt.Trim()
                        $j++
                    } else { break }
                }
                $val = (($blockLines -join ' ') -replace '\s+', ' ').Trim()
                $i = $j - 1
            } else {
                if (($val -match '^"(.*)"$') -or ($val -match "^'(.*)'$")) {
                    $val = $matches[1]
                }
            }
            if ($key -eq 'description') { $val = ($val.Trim() -replace '\s+', ' ') } else { $val = $val.Trim() }
            $fields[$key] = $val
        }
    }
    $name = $fields['name']
    if (-not $name) {
        $name = (Split-Path -Parent $Path | Split-Path -Leaf)
    }
    $model = $fields['model']
    if (-not $model) { $model = 'standard' }
    return @{ Name = $name; Description = $fields['description']; Model = $model; Body = $body; Fields = $fields }
}

function Format-YamlValue {
    param([string]$Value)
    if (-not $Value) { return '' }
    if ($Value -match '[:#"`{}\[\]&*!|>%@\n]' -or $Value.Contains("'")) {
        $esc = $Value -replace '\\', '\\\\' -replace '"', '\\"'
        return '"' + $esc + '"'
    }
    return $Value
}

function Convert-BodyModelTokens {
    <#
    .SYNOPSIS
        본문(body) 인라인 model 레벨 sub-dispatch 토큰을 플랫폼 실모델명으로 치환 (032 — F-003 미러).
    .NOTES
        macOS 대칭: scripts/install-mac.sh emit_platform_agent_adapter `_sub_body_model` (문자 단위 동일 정규식).
        앵커 '[,(]\s*' = sub-dispatch 토큰 한정(괄호 내 ", model: <레벨>" 또는 "(model: <레벨>").
          - 바레-paren:  "(op-dev-plan, model: advanced)" → lead=", "
          - 백틱-skill paren: "`op-dev-plan` (model: advanced)" → lead="("
          - prose 자기참조("frontmatter의 `model: standard`를 따른다")는 선행 백틱이라 미매칭 → 오염 차단.
        '\b' 단어 경계로 부분 매칭 차단. cursor(inherit)는 오버라이드 토큰 제거.
    #>
    param([Parameter(Mandatory)][string]$Body, [Parameter(Mandatory)][hashtable]$ModelMap)
    # cursor inherit 제거 시 백틱-skill paren 잔여 빈 괄호만 정리하기 위한 sentinel (정상 괄호 미오염).
    # NUL 이스케이프(`u{...})는 PS5.1 비호환이므로 본문 충돌 불가능한 ASCII 마커 사용 (PS5.1+/7+ 공통).
    $inheritOpen = [char]0xE000 + 'OPAL_INHERIT_OPEN' + [char]0xE000
    $evaluator = {
        param($m)
        $lead = $m.Groups[1].Value
        $lvl  = $m.Groups[2].Value
        $repl = $ModelMap[$lvl]
        if (-not $repl) { return $m.Value }            # 매핑 부재 → 원문 유지 (H-2 방어)
        if ($repl -eq 'inherit') {                      # F-002 cursor: 오버라이드 토큰 제거
            if ($lead.TrimStart().StartsWith('(')) { return $inheritOpen } else { return '' }
        }
        return "$lead" + "model: $repl"
    }.GetNewClosure()
    $result = [regex]::Replace($Body, '(?<lead>[,(]\s*)model:\s*(?<lvl>light|standard|advanced)\b', $evaluator)
    # cursor 빈 괄호 2차 정리: sub-dispatch 유래 "(  )" 만 제거(sentinel-anchored — 정상 괄호 불간섭).
    $result = [regex]::Replace($result, [regex]::Escape($inheritOpen) + '\s*\)', '')
    $result = $result.Replace($inheritOpen, '(')        # 잔여 sentinel 복구(이론상 미도달 — 방어)
    return $result
}

function Install-PlatformAgents {
    <#
    .SYNOPSIS
        ~/.opal/agents/* 를 Claude / Cursor / Gemini sub-agent 어댑터로 변환 + 등록.
    .NOTES
        macOS 대칭: scripts/install-mac.sh emit_platform_agent_adapter / install_{claude,cursor,gemini}_agents.
        Antigravity 는 sub-agent 미지원 (2026-04 기준).
    #>
    $agentsSrc = Join-Path $OpalHome 'agents'
    if (-not (Test-Path $agentsSrc)) {
        Write-OpalWarn '~/.opal/agents 부재 — 플랫폼 어댑터 스킵'
        return
    }

    $userHome = $env:USERPROFILE
    # 플랫폼별 목적지·직렬화 포맷만 남긴다 — model 매핑 등 필드 변환 규칙은 전부
    # $OpalAdapterFieldSpec(위 OPAL_ADAPTER_FIELD_SPEC 미러) 순회로 대체한다(105).
    $platforms = @{
        'claude' = @{ Dst = Join-Path $userHome '.claude\agents'; Format = 'md' }
        'cursor' = @{ Dst = Join-Path $userHome '.cursor\agents'; Format = 'md' }
        'gemini' = @{ Dst = Join-Path $userHome '.gemini\agents'; Format = 'md' }
        'codex'  = @{ Dst = Join-Path $userHome '.codex\agents';  Format = 'toml' }
    }

    foreach ($pname in $platforms.Keys) {
        $cfg = $platforms[$pname]
        if (-not (Test-Path $cfg.Dst)) {
            New-Item -ItemType Directory -Path $cfg.Dst -Force | Out-Null
        }
        # 본문 인라인 model 레벨 sub-dispatch 토큰 치환용 맵 — 스펙의 model 필드
        # platforms[...].values 를 그대로 사용해 Convert-BodyModelTokens 계약(H-8) 유지.
        $modelLevelMap = Get-OpalModelLevelMap -Spec $script:OpalAdapterFieldSpecObj -Platform $pname
        $count = 0
        Get-ChildItem -Path $agentsSrc -Directory -ErrorAction SilentlyContinue | ForEach-Object {
            $agentMd = Join-Path $_.FullName 'AGENT.md'
            if (-not (Test-Path $agentMd)) { return }
            $fm = Get-AgentFrontmatter -Path $agentMd
            if (-not $fm) { return }

            # 본문 인라인 model 레벨 sub-dispatch 토큰 치환 (032 — F-003 미러, Markdown·Codex TOML 양 경로 공통)
            $convertedBody = Convert-BodyModelTokens -Body $fm.Body -ModelMap $modelLevelMap

            # 확장 필드 변환 스펙 순회(105) — install-mac.sh build_pairs() 미러.
            # mode(key/model_param/omit)에만 분기한다 — 플랫폼명 리터럴 비교는 하지 않는다(R-1 AC).
            $pairs = ConvertTo-OpalFieldPairs -Spec $script:OpalAdapterFieldSpecObj -Fields $fm.Fields -Platform $pname -AgentName $fm.Name

            if ($cfg.Format -eq 'toml') {
                # Codex sub-agent TOML 직렬화 — pairs 순회(105) + developer_instructions는
                # 스펙 밖 본문 슬롯으로 유지(mac install_codex_agents 대칭)
                $dstFile = Join-Path $cfg.Dst "$($fm.Name).toml"
                # 사용자 파일 충돌 가드
                if (Test-Path $dstFile) {
                    $existing = Get-Content -Path $dstFile -Raw -Encoding UTF8
                    if ($existing -notmatch 'AUTO-GENERATED by install') {
                        Write-OpalWarn "user-managed file (AUTO-GENERATED 헤더 없음) — 스킵: $dstFile"
                        return
                    }
                }
                # TOML escape: \ → \\, " → \"
                $escapedBody  = $convertedBody -replace '\\', '\\' -replace '"', '\"'
                $tomlContent  = "# AUTO-GENERATED by install-windows.ps1 from ~/.opal/agents/$($fm.Name)/AGENT.md. DO NOT EDIT.`r`n"
                $tomlContent += "# SSOT: opal/agents/$($fm.Name)/AGENT.md`r`n`r`n"
                foreach ($pair in $pairs) {
                    $escapedVal = ([string]$pair.Value) -replace '\\', '\\' -replace '"', '\"'
                    $tomlContent += "$($pair.Key) = `"$escapedVal`"`r`n"
                }
                $tomlContent += "developer_instructions = `"`"`"`r`n$escapedBody`r`n`"`"`"`r`n"
                Set-ContentNoBom -Path $dstFile -Value $tomlContent
            } else {
                # Markdown YAML 직렬화 — pairs 순회(105), Format-YamlValue 재사용
                $dstFile = Join-Path $cfg.Dst "$($fm.Name).md"
                # 사용자 파일 충돌 가드 — AUTO-GENERATED 헤더가 없으면 사용자 관리로 간주, 스킵
                if (Test-Path $dstFile) {
                    $existing = Get-Content -Path $dstFile -Raw -Encoding UTF8
                    if ($existing -notmatch 'AUTO-GENERATED by install') {
                        Write-OpalWarn "user-managed file (AUTO-GENERATED 헤더 없음) — 스킵: $dstFile"
                        return
                    }
                }
                $fmLines = @()
                foreach ($pair in $pairs) {
                    $fmLines += "$($pair.Key): $(Format-YamlValue ([string]$pair.Value))"
                }

                $header = "<!-- AUTO-GENERATED by install-windows.ps1 from ~/.opal/agents/$($fm.Name)/AGENT.md. DO NOT EDIT. -->`r`n<!-- SSOT: opal/agents/$($fm.Name)/AGENT.md -->`r`n`r`n"

                $output = "---`r`n" + ($fmLines -join "`r`n") + "`r`n---`r`n`r`n" + $header + $convertedBody
                Set-ContentNoBom -Path $dstFile -Value $output
            }
            $count++
        }
        Write-OpalOk "${pname} 어댑터 ${count}개 → $($cfg.Dst)"
    }
}

function Install-CodexConfig {
    <#
    .SYNOPSIS
        Codex config.toml 에 [agents] 글로벌 설정 블록을 멱등 작성한다.
    .NOTES
        키/기본값 출처: https://developers.openai.com/codex/config-reference (2026-06-17 확인)
          max_concurrent_threads_per_session=6, max_depth=1, job_max_runtime_seconds=1800
        멱등성 3분기 (105 — legacy alias 마이그레이션 추가):
          1) [agents] 없음(또는 파일 부재)              → append (정식 키로 신설)
          2) [agents] 있음 + legacy 키(max_threads) 있음 → 해당 라인만 in-place 치환(값 보존)
          3) [agents] 있음 + legacy 키 없음             → 스킵 (이미 정식 키)
        기존 [mcp_servers] 등 다른 블록은 훼손하지 않는다.
        macOS 대칭: scripts/install-mac.sh install_codex_config.
    #>
    $configFile = Join-Path $env:USERPROFILE '.codex\config.toml'
    $configDir  = Split-Path $configFile -Parent
    if (-not (Test-Path $configDir)) {
        New-Item -ItemType Directory -Path $configDir -Force | Out-Null
    }

    if (Test-Path $configFile) {
        $existing = Get-Content -Path $configFile -Raw -Encoding UTF8
        if ($existing -match '(?m)^\[agents\]') {
            # 분기 2) legacy 키 잔존 — 해당 라인만 in-place 치환, 값 보존, 타 블록 무손상
            if ($existing -match '(?m)^[ \t]*max_threads[ \t]*=') {
                $migrated = [regex]::Replace($existing, '(?m)^([ \t]*)max_threads([ \t]*=)', '${1}max_concurrent_threads_per_session${2}')
                [System.IO.File]::WriteAllText($configFile, $migrated, $Script:Utf8NoBom)
                Write-OpalOk "Codex config.toml — legacy 키 → max_concurrent_threads_per_session 마이그레이션(값 보존) → $configFile"
                return
            }
            # 분기 3) 이미 정식 키 — 스킵
            Write-OpalInfo 'Codex config.toml — [agents] 블록 이미 존재(정식 키), 스킵'
            return
        }
    }

    # 분기 1) [agents] 블록 append (기존 블록 보존)
    $block  = "`r`n"
    $block += "# AUTO-GENERATED by install-windows.ps1 — OPAL Codex 글로벌 에이전트 한계치`r`n"
    $block += "# 출처: https://developers.openai.com/codex/config-reference`r`n"
    $block += "[agents]`r`n"
    $block += "max_concurrent_threads_per_session = 6`r`n"
    $block += "max_depth = 1`r`n"
    $block += "job_max_runtime_seconds = 1800`r`n"

    if (Test-Path $configFile) {
        $existing = Get-Content -Path $configFile -Raw -Encoding UTF8
        [System.IO.File]::WriteAllText($configFile, $existing + $block, $Script:Utf8NoBom)
    } else {
        [System.IO.File]::WriteAllText($configFile, $block.TrimStart(), $Script:Utf8NoBom)
    }

    Write-OpalOk "Codex config.toml — [agents] 블록 추가 → $configFile"
}

# ─── main ────────────────────────────────────────────────────────────────────

function Invoke-OpalWindowsInstall {
    Write-Host ''
    Write-Host '╔══════════════════════════════════════╗' -ForegroundColor Cyan
    Write-Host '║   OPAL Platform Installer — Windows  ║' -ForegroundColor Cyan
    Write-Host '╚══════════════════════════════════════╝' -ForegroundColor Cyan
    Write-Host ''

    Test-WindowsDeps

    $repoRoot = Resolve-RepoRoot

    Install-OpalCore       -RepoRoot $repoRoot
    Register-OpalBin
    Register-EnvPath
    Register-Bootstrapper  -RepoRoot $repoRoot
    Install-OpalVenv       -RepoRoot $repoRoot
    Install-Dashboard      -RepoRoot $repoRoot
    Start-OpalConsole
    Install-OpalMcp        -RepoRoot $repoRoot
    Install-PlatformAgents
    Install-CodexConfig

    # git 한글 경로 표시 (core.quotepath=false) — install-mac.sh v3.1 과 정합
    # OPAL 태스크 폴더명은 한글/혼용을 허용한다(op-task SKILL.md §저장 경로).
    # git 기본값(quotepath=true)은 한글 경로를 octal 이스케이프로 표시하므로,
    # 전역 설정에 quotepath=false를 적용해 status/log에서 한글이 그대로 보이도록 한다.
    if (Get-Command git -ErrorAction SilentlyContinue) {
        git config --global core.quotepath false 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-OpalOk 'git core.quotepath=false 설정 (한글 경로 표시)'
        } else {
            Write-OpalInfo 'git core.quotepath 설정 실패 — 한글 경로가 octal로 표시될 수 있습니다'
        }
    }

    # ~/.opal/VERSION 기록 — opal-cli update 비교 기준 (install-mac.sh record_installed_version 대칭, 048)
    # 우선순위: $repoRoot/VERSION 각인값(tarball 최우선) → $OpalVersion(전달값) → "main" 폴백
    if (-not (Test-Path $OpalHome)) {
        New-Item -ItemType Directory -Path $OpalHome -Force | Out-Null
    }
    $versionFile = Join-Path $OpalHome 'VERSION'
    $effectiveVersion = $OpalVersion
    $srcVersionFile = [IO.Path]::Combine($repoRoot, 'VERSION')
    if (Test-Path $srcVersionFile) {
        $srcStamped = (Get-Content -Raw -LiteralPath $srcVersionFile -ErrorAction SilentlyContinue)
        if ($srcStamped) { $srcStamped = $srcStamped.Trim() }
        if ($srcStamped -and ($srcStamped -notlike '*$Format:*')) {
            $effectiveVersion = $srcStamped
        }
    }
    Set-Content -Path $versionFile -Value $effectiveVersion -Encoding ASCII -NoNewline
    Write-OpalOk "버전 기록 → $versionFile ($effectiveVersion)"

    Write-Host ''
    Write-OpalOk '설치 흐름 완료.'
    if (-not (Find-Python)) {
        Write-OpalInfo "Python ${OpalPythonMin} 이상 미확보 — 일부 도구 제한. 수동 설치 후 재실행 권장: winget install Python.Python.$OpalPythonTarget"
    }
    Write-OpalInfo '커뮤니티 스킬은 //skill-manager로 검색·설치하세요 (예: //skill-manager pdf)'
    Write-Host ''
}

Invoke-OpalWindowsInstall -OpalVersion $OpalVersion
