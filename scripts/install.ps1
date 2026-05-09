<#
.SYNOPSIS
    OPAL Windows one-liner installer (irm/iex entry point).

.DESCRIPTION
    PowerShell one-liner 진입 부트스트랩.
    Invoke-RestMethod 로 tarball 을 다운로드하고, Get-FileHash(SHA-256)로 체크섬을 검증한 뒤
    scripts/install/windows.ps1 을 호출하여 실제 설치를 수행한다.

    사용법:
        iex (irm https://raw.githubusercontent.com/ceo4ever/opal/main/scripts/install.ps1)

    ExecutionPolicy 가 Restricted 인 환경:
        powershell -ExecutionPolicy ByPass -c "irm https://raw.githubusercontent.com/ceo4ever/opal/main/scripts/install.ps1 | iex"

    환경 변수 오버라이드:
        $env:OPAL_REPO    = 'fork-owner/opal'   # 기본: ceo4ever/opal
        $env:OPAL_VERSION = 'v0.1'              # 기본: main
        $env:OPAL_DRY_RUN = '1'                 # fetch 생략 (흐름 검증용)

.NOTES
    요구사항: Windows PowerShell 5.1+ 또는 PowerShell 7+
    근거:
        tasks/139-260508-opp-distribute-and-getstarted/PLAN.md §4.2 Step 6
        tasks/139-260508-opp-distribute-and-getstarted/PLAN.md §3.1.2 scripts/install.ps1 진입 골격 (D-14)
        tasks/139-260508-opp-distribute-and-getstarted/TASK.md D2: https://github.com/ceo4ever/opal

    변경이력:
        v1.0  2026-05-09 12:00  신규 작성 — Windows one-liner 진입 부트스트랩 (139)
#>

#Requires -Version 5.1

Set-StrictMode -Version 3.0
$ErrorActionPreference = 'Stop'

# ─── 환경 변수 오버라이드 ────────────────────────────────────────────────────
$OpalRepo    = if ($env:OPAL_REPO)    { $env:OPAL_REPO    } else { 'ceo4ever/opal' }
$OpalVersion = if ($env:OPAL_VERSION) { $env:OPAL_VERSION } else { 'main' }
$DryRun      = ($env:OPAL_DRY_RUN -eq '1')

$TarballUrl  = "https://github.com/$OpalRepo/archive/refs/heads/$OpalVersion.tar.gz"
$ShaUrl      = "https://github.com/$OpalRepo/releases/download/$OpalVersion/sha256sums.txt"

# ─── 함수 정의 ───────────────────────────────────────────────────────────────

function Test-Deps {
    <#
    .SYNOPSIS
        필수 의존성(git, tar)이 설치되어 있는지 확인한다.
    #>
    $missing = @()

    if (-not (Get-Command 'git' -ErrorAction SilentlyContinue)) {
        $missing += 'git'
    }

    # PowerShell 7+ 에는 tar 가 기본 포함; 5.1 에서는 Windows 10 1803+ 기본 tar 사용
    if (-not (Get-Command 'tar' -ErrorAction SilentlyContinue)) {
        $missing += 'tar (Windows 10 1803+ 필요 또는 Git for Windows 의 tar 사용)'
    }

    if ($missing.Count -gt 0) {
        throw "[OPAL] 필수 의존성이 누락되었습니다: $($missing -join ', ')"
    }

    Write-Host '[OPAL] 의존성 확인 완료.' -ForegroundColor Green
}

function Fetch-Tarball {
    <#
    .SYNOPSIS
        GitHub 에서 OPAL tarball 을 임시 경로로 다운로드한다.
    .OUTPUTS
        다운로드된 .tar.gz 파일의 전체 경로.
    #>
    param(
        [Parameter(Mandatory)]
        [string] $DestDir
    )

    $outFile = Join-Path $DestDir "opal-$OpalVersion.tar.gz"

    if ($DryRun) {
        Write-Host "[OPAL][DRY-RUN] fetch 생략: $TarballUrl" -ForegroundColor Yellow
        # dry-run 시 빈 파일을 생성하여 이후 단계가 경로를 참조할 수 있게 한다
        Set-Content -Path $outFile -Value '' -Encoding UTF8
        return $outFile
    }

    Write-Host "[OPAL] tarball 다운로드 중: $TarballUrl" -ForegroundColor Cyan

    # TLS 1.2 이상 강제
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 -bor [Net.SecurityProtocolType]::Tls13

    Invoke-RestMethod `
        -Uri         $TarballUrl `
        -OutFile     $outFile `
        -ErrorAction Stop

    Write-Host "[OPAL] 다운로드 완료: $outFile" -ForegroundColor Green
    return $outFile
}

function Verify-Checksum {
    <#
    .SYNOPSIS
        sha256sums.txt 를 가져와 tarball 의 SHA-256 체크섬을 검증한다.
        sha256sums.txt 가 존재하지 않는 버전(main 브랜치 스냅샷 등)에서는 경고 후 건너뛴다.
    #>
    param(
        [Parameter(Mandatory)]
        [string] $TarballPath,

        [Parameter(Mandatory)]
        [string] $DestDir
    )

    if ($DryRun) {
        Write-Host '[OPAL][DRY-RUN] 체크섬 검증 생략.' -ForegroundColor Yellow
        return
    }

    $shaFile = Join-Path $DestDir 'sha256sums.txt'

    try {
        Write-Host "[OPAL] sha256sums.txt 다운로드 중: $ShaUrl" -ForegroundColor Cyan
        Invoke-RestMethod -Uri $ShaUrl -OutFile $shaFile -ErrorAction Stop
    }
    catch {
        Write-Warning "[OPAL] sha256sums.txt 를 가져올 수 없습니다 (릴리스 전 버전일 수 있음). 체크섬 검증을 건너뜁니다."
        return
    }

    $actualHash = (Get-FileHash -Path $TarballPath -Algorithm SHA256).Hash.ToLower()
    $tarballName = Split-Path $TarballPath -Leaf

    $expectedLine = Get-Content $shaFile |
        Where-Object { $_ -match [regex]::Escape($tarballName) } |
        Select-Object -First 1

    if (-not $expectedLine) {
        Write-Warning "[OPAL] sha256sums.txt 에 '$tarballName' 항목이 없습니다. 검증을 건너뜁니다."
        return
    }

    $expectedHash = ($expectedLine -split '\s+')[0].ToLower()

    if ($actualHash -ne $expectedHash) {
        throw "[OPAL] 체크섬 불일치! 예상: $expectedHash / 실제: $actualHash"
    }

    Write-Host '[OPAL] 체크섬 검증 통과.' -ForegroundColor Green
}

function Invoke-PlatformInstaller {
    <#
    .SYNOPSIS
        추출된 tarball 에서 scripts/install/windows.ps1 을 찾아 실행한다.
    #>
    param(
        [Parameter(Mandatory)]
        [string] $TarballPath,

        [Parameter(Mandatory)]
        [string] $DestDir
    )

    if ($DryRun) {
        Write-Host '[OPAL][DRY-RUN] 플랫폼 인스톨러 호출 생략.' -ForegroundColor Yellow
        return
    }

    Write-Host '[OPAL] tarball 압축 해제 중...' -ForegroundColor Cyan
    $extractDir = Join-Path $DestDir 'opal-src'
    New-Item -ItemType Directory -Path $extractDir -Force | Out-Null

    # tar: Windows 10 1803+ 기본 tar 또는 Git for Windows tar 사용
    & tar -xzf $TarballPath -C $extractDir --strip-components 1
    if ($LASTEXITCODE -ne 0) {
        throw "[OPAL] tarball 압축 해제 실패 (exit code: $LASTEXITCODE)"
    }

    $windowsInstaller = Join-Path $extractDir 'scripts' 'install' 'windows.ps1'
    if (-not (Test-Path $windowsInstaller)) {
        throw "[OPAL] windows.ps1 을 찾을 수 없습니다: $windowsInstaller"
    }

    Write-Host '[OPAL] windows.ps1 실행 중...' -ForegroundColor Cyan
    & $windowsInstaller
    if ($LASTEXITCODE -ne 0) {
        throw "[OPAL] windows.ps1 실행 실패 (exit code: $LASTEXITCODE)"
    }
}

# ─── main ────────────────────────────────────────────────────────────────────

function Invoke-OpalInstall {
    Write-Host ''
    Write-Host '╔══════════════════════════════════════╗' -ForegroundColor Cyan
    Write-Host '║   OPAL Installer — Windows           ║' -ForegroundColor Cyan
    Write-Host '╚══════════════════════════════════════╝' -ForegroundColor Cyan
    Write-Host ''

    if ($DryRun) {
        Write-Host '[OPAL][DRY-RUN] 드라이런 모드 활성화 — 실제 다운로드/설치를 수행하지 않습니다.' -ForegroundColor Yellow
    }

    Write-Host "[OPAL] repo    : $OpalRepo" -ForegroundColor DarkGray
    Write-Host "[OPAL] version : $OpalVersion" -ForegroundColor DarkGray
    Write-Host ''

    Test-Deps

    # 임시 폴더 생성 — try/finally 로 항상 정리
    $tmpDir = Join-Path $env:TEMP "opal-install-$([guid]::NewGuid())"
    New-Item -ItemType Directory -Path $tmpDir -Force | Out-Null

    try {
        $tarball = Fetch-Tarball -DestDir $tmpDir
        Verify-Checksum -TarballPath $tarball -DestDir $tmpDir
        Invoke-PlatformInstaller -TarballPath $tarball -DestDir $tmpDir

        Write-Host ''
        Write-Host '[OPAL] 설치가 완료되었습니다.' -ForegroundColor Green
        Write-Host '[OPAL] 새 PowerShell 세션을 열거나 PATH 를 갱신한 뒤 opal-cli 를 사용하세요.' -ForegroundColor Green
        Write-Host ''
    }
    finally {
        if (Test-Path $tmpDir) {
            Remove-Item -Recurse -Force -Path $tmpDir -ErrorAction SilentlyContinue
        }
    }
}

Invoke-OpalInstall
