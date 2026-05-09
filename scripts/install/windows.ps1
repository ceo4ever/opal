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
        v1.0  2026-05-09 12:00  신규 작성 — Windows 플랫폼 인스톨러 골격 (139)
#>

#Requires -Version 5.1

Set-StrictMode -Version 3.0
$ErrorActionPreference = 'Stop'

# ─── 상수 ────────────────────────────────────────────────────────────────────

$OpalHome   = Join-Path $env:USERPROFILE '.opal'
$OpalBinDir = Join-Path $OpalHome 'bin'

# ─── 유틸리티 ─────────────────────────────────────────────────────────────────

function Write-OpalInfo  { param([string]$Msg) Write-Host "[OPAL] $Msg" -ForegroundColor Cyan   }
function Write-OpalOk    { param([string]$Msg) Write-Host "[OPAL] $Msg" -ForegroundColor Green  }
function Write-OpalWarn  { param([string]$Msg) Write-Host "[OPAL][WARN] $Msg" -ForegroundColor Yellow }
function Write-OpalError { param([string]$Msg) Write-Host "[OPAL][ERROR] $Msg" -ForegroundColor Red   }

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
        ~/.opal/ 에 OPAL 핵심 자산(skills, agents, core, tools, references)을 복사한다.
        사용자 데이터(identity.md, projects/)는 보존한다.
    .NOTES
        macOS 대칭: scripts/install-mac.sh install_opal() 함수의 핵심 복사 단계.
        현재 골격 수준 — 실제 복사 로직은 TS-006 검증 후 완성 예정.
    #>
    param(
        [Parameter(Mandatory)]
        [string] $RepoRoot
    )

    Write-OpalInfo '~/.opal/ 디렉토리 준비 중...'

    # 사용자 데이터 보존 목록 (macOS: scripts/install-mac.sh:646-654 정책 동일)
    $preserveItems = @('identity.md', 'projects', 'community-skills', '.venv')

    # ~/.opal/ 생성 (존재하면 스킵)
    if (-not (Test-Path $OpalHome)) {
        New-Item -ItemType Directory -Path $OpalHome -Force | Out-Null
        Write-OpalOk "~/.opal/ 생성 완료."
    }
    else {
        Write-OpalInfo "~/.opal/ 이미 존재합니다 (업데이트 모드)."
    }

    # 복사 대상 디렉토리 목록 (opal-cli update 정책: ~/. opal/skills|agents|tools 클린 후 재배포)
    $copyDirs = @('opal', 'skills', 'agents', 'references', 'tools', 'templates', 'hooks')

    foreach ($dir in $copyDirs) {
        $src = Join-Path $RepoRoot $dir
        $dst = Join-Path $OpalHome $dir

        if (-not (Test-Path $src)) {
            Write-OpalWarn "소스 디렉토리 없음, 건너뜀: $src"
            continue
        }

        Write-OpalInfo "복사 중: $dir → $dst"
        # TODO(TS-006): Windows 환경 검증 후 실제 파일 복사 로직 구현
        # Copy-Item -Recurse -Force -Path $src -Destination $OpalHome
    }

    Write-OpalOk '핵심 자산 복사 완료 (골격 — TS-006 실 검증 후 활성화).'
}

function Register-OpalBin {
    <#
    .SYNOPSIS
        ~/.opal/bin/opal-cli 래퍼 스크립트를 생성한다.
        Windows 에서는 symlink 대신 .cmd 래퍼 또는 PowerShell 래퍼를 사용한다.
    .NOTES
        macOS 대칭: scripts/install-mac.sh install_opal_bin() — ln -sfn 으로 symlink 생성.
        Windows Developer Mode 또는 관리자 권한이 있으면 New-Item -ItemType SymbolicLink 사용 가능.
        권한 없는 환경을 위해 .cmd 래퍼를 기본으로 사용한다.
    #>
    $cliTarget = Join-Path $OpalHome 'tools' 'opal-cli' 'run.sh'
    $cliWrapper = Join-Path $OpalBinDir 'opal-cli.cmd'
    $cliPs1 = Join-Path $OpalBinDir 'opal-cli.ps1'

    if (-not (Test-Path $cliTarget)) {
        Write-OpalWarn "opal-cli/run.sh 부재 — bin 생성 스킵 (Step 3 완료 후 재실행 필요)."
        return
    }

    if (-not (Test-Path $OpalBinDir)) {
        New-Item -ItemType Directory -Path $OpalBinDir -Force | Out-Null
    }

    # .cmd 래퍼 (cmd.exe 환경 호환)
    $cmdContent = "@echo off`r`nbash `"$($cliTarget -replace '\\', '/')`" %*`r`n"
    Set-Content -Path $cliWrapper -Value $cmdContent -Encoding ASCII
    Write-OpalOk "opal-cli.cmd 래퍼 생성: $cliWrapper"

    # PowerShell 래퍼 (pwsh/powershell 환경 호환)
    $ps1Content = "& bash `"$($cliTarget -replace '\\', '/')`" @args`n"
    Set-Content -Path $cliPs1 -Value $ps1Content -Encoding UTF8
    Write-OpalOk "opal-cli.ps1 래퍼 생성: $cliPs1"
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
        Write-OpalInfo '새 터미널 세션을 열면 opal-cli 명령을 사용할 수 있습니다.'
    }

    # 현재 세션 PATH 에도 즉시 반영
    if ($env:PATH -notmatch [regex]::Escape($marker)) {
        $env:PATH = "$marker;$env:PATH"
    }
}

function Register-Bootstrapper {
    <#
    .SYNOPSIS
        AI 플랫폼 부트스트래퍼 마커를 삽입한다.
    .NOTES
        macOS 대칭: scripts/install-mac.sh install_opal_section() / extract_bootstrap_content().
        마커: OPAL_START / OPAL_END (install-mac.sh:25-32 참조).
        현재 골격 수준 — Windows 경로 처리는 TS-006 검증 후 완성 예정.
    #>
    Write-OpalInfo '부트스트래퍼 마커 삽입 (골격 — TS-006 실 검증 후 활성화).'

    # TODO(TS-006): Windows 환경에서 Claude Code CLAUDE.md 경로 결정 후 구현
    # $claudeMd = Join-Path $env:USERPROFILE '.claude' 'CLAUDE.md'
    # ... OPAL_START / OPAL_END 마커 삽입 로직 ...

    Write-OpalWarn '부트스트래퍼 마커 삽입은 TS-006 검증 후 완성됩니다.'
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

    Install-OpalCore    -RepoRoot $repoRoot
    Register-OpalBin
    Register-EnvPath
    Register-Bootstrapper

    Write-Host ''
    Write-OpalOk '설치 흐름 완료.'
    Write-OpalInfo '부트스트래퍼 및 핵심 자산 복사는 TS-006(Windows VM) 검증 후 활성화됩니다.'
    Write-Host ''
}

Invoke-OpalWindowsInstall
