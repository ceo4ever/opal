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
                                 자산 실 복사(opal/core/AGENT.md / skills+opal/skills / agents+opal/agents / opal/templates / opal/tools / opal/core/references / community-skills) +
                                 Strip 변경이력(Remove-ChangelogSection/Recursive) +
                                 부트스트래퍼 마커(Claude/Cursor/Gemini OPAL+HARDENING) 자동 삽입 (139 추가작업, v0.3.0)
        v1.1.1 2026-05-10 00:35  Install-OpalCore의 $skillCount/$agentCount .Count 접근을 @() 캐스트로 변경 — Set-StrictMode 3.0 환경에서 single object .Count 차단 결함 fix (139 추가작업, v0.3.1)
        v1.2.0 2026-05-10 00:40  Find-GitBash 신규 + Register-OpalBin 이 Git Bash explicit 경로 사용 — WSL bash.exe(/bin/bash 부재) 우회 결함 fix (139 추가작업, v0.3.2)
#>

#Requires -Version 5.1

# install.ps1 이 -OpalVersion 으로 전달하는 framework 버전.
# ~/.opal/VERSION 기록에 사용. 미전달 시 "main" 폴백.
param(
    [string]$OpalVersion = 'main'
)

Set-StrictMode -Version 3.0
$ErrorActionPreference = 'Stop'

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

# ─── 유틸리티 ─────────────────────────────────────────────────────────────────

function Write-OpalInfo  { param([string]$Msg) Write-Host "[OPAL] $Msg" -ForegroundColor Cyan   }
function Write-OpalOk    { param([string]$Msg) Write-Host "[OPAL] $Msg" -ForegroundColor Green  }
function Write-OpalWarn  { param([string]$Msg) Write-Host "[OPAL][WARN] $Msg" -ForegroundColor Yellow }
function Write-OpalError { param([string]$Msg) Write-Host "[OPAL][ERROR] $Msg" -ForegroundColor Red   }

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
    Set-Content -Path $Path -Value $kept -Encoding UTF8
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
        Set-Content -Path $Target -Value "$block`r`n" -Encoding UTF8 -NoNewline
        Write-OpalOk "$Label OPAL 설치 (새 파일): $Target"
        return
    }
    $existing = Get-Content -Path $Target -Raw -Encoding UTF8
    if ($existing -match [regex]::Escape($OpalStart)) {
        # OPAL_START~OPAL_END 블록 교체 — regex literal Replace 사용 (block 의 $ 등 metachar 안전 처리)
        $pattern = '(?ms)' + [regex]::Escape($OpalStart) + '.*?' + [regex]::Escape($OpalEnd)
        $regex = [System.Text.RegularExpressions.Regex]::new($pattern)
        $newContent = $regex.Replace($existing, $block)
        Set-Content -Path $Target -Value $newContent -Encoding UTF8 -NoNewline
        Write-OpalOk "$Label OPAL 업데이트 (마커 교체): $Target"
    }
    elseif ($existing -match [regex]::Escape($R2Start)) {
        $pattern = '(?ms)' + [regex]::Escape($R2Start) + '.*?' + [regex]::Escape($R2End)
        $regex = [System.Text.RegularExpressions.Regex]::new($pattern)
        $newContent = $regex.Replace($existing, $block)
        Set-Content -Path $Target -Value $newContent -Encoding UTF8 -NoNewline
        Write-OpalOk "$Label R2→OPAL 전환 (마커 교체): $Target"
    }
    else {
        Add-Content -Path $Target -Value "`r`n$block`r`n" -Encoding UTF8
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
        Set-Content -Path $Target -Value "$block`r`n" -Encoding UTF8 -NoNewline
        Write-OpalOk "Gemini HARDENING 설치 (새 파일): $Target"
        return
    }
    $existing = Get-Content -Path $Target -Raw -Encoding UTF8
    if ($existing -match [regex]::Escape($HardeningStart)) {
        $pattern = '(?ms)' + [regex]::Escape($HardeningStart) + '.*?' + [regex]::Escape($HardeningEnd)
        $regex = [System.Text.RegularExpressions.Regex]::new($pattern)
        $newContent = $regex.Replace($existing, $block)
        Set-Content -Path $Target -Value $newContent -Encoding UTF8 -NoNewline
        Write-OpalOk "Gemini HARDENING 업데이트 (마커 교체): $Target"
    }
    else {
        Add-Content -Path $Target -Value "`r`n$block`r`n" -Encoding UTF8
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
        클린 후 재배포: skills/, agents/, references/, tools/, templates/, community-skills/(병합).
    #>
    param(
        [Parameter(Mandatory)]
        [string] $RepoRoot
    )

    Write-OpalInfo '~/.opal/ 디렉토리 준비 중...'

    if (-not (Test-Path $OpalHome)) {
        New-Item -ItemType Directory -Path $OpalHome -Force | Out-Null
        Write-OpalOk "~/.opal/ 생성 완료."
    } else {
        Write-OpalInfo '~/.opal/ 이미 존재합니다 (업데이트 모드).'
    }

    # ── 클린: framework 디렉토리만 (사용자 데이터 보존) ──
    Write-OpalInfo '기존 프레임워크 파일 정리 (사용자 데이터 보존)...'
    $cleanDirs = @('skills', 'agents', 'references', 'community-skills', 'templates', 'tools')
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

    # ── 스킬: skills/ + opal/skills/ 합쳐서 ~/.opal/skills/ ──
    $skillsDst = Join-Path $OpalHome 'skills'
    New-Item -ItemType Directory -Path $skillsDst -Force | Out-Null
    foreach ($srcRel in @(@('skills'), @('opal', 'skills'))) {
        $src = [IO.Path]::Combine(@($RepoRoot) + $srcRel)
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
    foreach ($srcRel in @(@('opal', 'agents'), @('agents'))) {
        $src = [IO.Path]::Combine(@($RepoRoot) + $srcRel)
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

    # ── 참조 레지스트리: opal/core/references/ → ~/.opal/references/ ──
    $refSrc = [IO.Path]::Combine($RepoRoot, 'opal', 'core', 'references')
    $refDst = Join-Path $OpalHome 'references'
    if (Test-Path $refSrc) {
        Copy-Item -Recurse -Force -Path $refSrc -Destination $OpalHome
        Remove-ChangelogRecursive -Root $refDst
        Write-OpalOk "references → $refDst"
    }

    # ── 커뮤니티 스킬: community-skills/ → ~/.opal/community-skills/ (vendor 단위 덮어쓰기) ──
    $csSrc = [IO.Path]::Combine($RepoRoot, 'community-skills')
    $csDst = Join-Path $OpalHome 'community-skills'
    if (Test-Path $csSrc) {
        if (-not (Test-Path $csDst)) {
            New-Item -ItemType Directory -Path $csDst -Force | Out-Null
        }
        Get-ChildItem -Path $csSrc -Directory -ErrorAction SilentlyContinue | ForEach-Object {
            $vendorDst = Join-Path $csDst $_.Name
            if (Test-Path $vendorDst) { Remove-Item -Recurse -Force $vendorDst }
            Copy-Item -Recurse -Force -Path $_.FullName -Destination $csDst
        }
        Write-OpalOk "community-skills → $csDst"
    }

    Write-OpalOk '핵심 자산 복사 완료.'
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
    $cliPs1 = Join-Path $OpalBinDir 'opal-cli.ps1'

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

    # PowerShell 래퍼 (pwsh/powershell 환경)
    if ($bashExe -eq 'bash') {
        $ps1Content = "& bash `"$runScriptPosix`" @args`n"
    } else {
        $ps1Content = "& `"$bashExe`" `"$runScriptPosix`" @args`n"
    }
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
    Write-Host '         & "$env:USERPROFILE\.opal\bin\opal-cli.ps1" doctor'
    Write-Host '         %USERPROFILE%\.opal\bin\opal-cli.cmd doctor'
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

    # ── Cursor: 단일 .mdc 파일 직접 복사 (마커 없는 형식) ──
    $cursorSnippet = [IO.Path]::Combine($bsDir, 'cursor-bootstrap.mdc')
    $cursorTarget  = [IO.Path]::Combine($userHome, '.cursor', 'rules', '000-opal-agent.mdc')
    if (Test-Path $cursorSnippet) {
        $cursorDir = Split-Path -Parent $cursorTarget
        if (-not (Test-Path $cursorDir)) {
            New-Item -ItemType Directory -Path $cursorDir -Force | Out-Null
        }
        Copy-Item -Force -Path $cursorSnippet -Destination $cursorTarget
        Write-OpalOk "Cursor OPAL → $cursorTarget"
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

    # ~/.opal/VERSION 기록 — opal-cli update 비교 기준 (install-mac.sh v1.8 과 정합)
    if (-not (Test-Path $OpalHome)) {
        New-Item -ItemType Directory -Path $OpalHome -Force | Out-Null
    }
    $versionFile = Join-Path $OpalHome 'VERSION'
    Set-Content -Path $versionFile -Value $OpalVersion -Encoding ASCII -NoNewline
    Write-OpalOk "버전 기록 → $versionFile ($OpalVersion)"

    Write-Host ''
    Write-OpalOk '설치 흐름 완료.'
    Write-OpalInfo 'Python venv / MCP 등록 / 플랫폼 어댑터는 후속 hotfix(v0.3.1+)에서 추가됩니다.'
    Write-Host ''
}

Invoke-OpalWindowsInstall -OpalVersion $OpalVersion
