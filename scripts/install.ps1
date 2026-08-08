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
# 변경이력
#   v1.0   2026-05-09 12:00  초기 작성 — Windows one-liner 진입 (139)
#   v1.0.1 2026-05-09 23:00  Resolve-DefaultVersion + URL 분기(archive/refs/tags) +
#                            tar --exclude tasks/* + Remove-Item 단축 경로 강건화 (139 추가작업)
#   v1.0.2 2026-05-09 23:15  Invoke-PlatformInstaller 의 Join-Path 다중 인자(5.1 비호환)
#                            → [IO.Path]::Combine 으로 변경. tasks/ 자체는 .gitattributes export-ignore 로 archive 에서 제외 (139 추가작업)
#   v1.0.3 2026-05-09 23:30  $env:OPAL_VERSION export 제거 — PowerShell 세션 잔존 결함 회피.
#                            windows.ps1 호출 시 -OpalVersion 파라미터로 명시 전달 (139 추가작업)
#   v1.0.4 2026-05-09 23:40  windows.ps1 호출을 powershell.exe -ExecutionPolicy Bypass -File 로 변경.
#                            Restricted/RemoteSigned 환경에서 다운로드된 .ps1 실행 차단(PSSecurityException) 회피 (139 추가작업)
#   v1.0.5 2026-05-10 15:30  Resolve-DefaultVersion 의 '최신 태그 자동 선택 ... (release 자산 없음 — archive tarball 사용)' 안내 라인 제거.
#                            release 자산 부재는 정상 동작이며 사용자 노이즈 — '[OPAL] version :' 표시로 충분 (140 추가작업, v0.3.16)
#   v1.0.6 2026-05-10 21:00  Verify-Checksum 강화 — release tag + sha256sums.txt 부재 시 prompt/거부 + main UNVERIFIED banner (GC-001, R-2) (144)
#   v1.0.7 2026-06-29 15:24  Invoke-PlatformInstaller 추출 후 $extractDir/VERSION 각인값으로 $script:OpalVersion override — -notlike '*$Format:*' 판별 (048)
#   v1.1   2026-08-07 12:04  DL-CONTRACT (085) 적용 — 릴리즈 태그는 릴리즈 자산을 받아 검증(다운로드 대상 = 검증 대상),
#                            sha256sums.txt 부재/형식이상/자산 다운로드 실패 시 자동 아카이브 폴백(UNVERIFIED),
#                            추출 strip-components 자동 판정 + VERSION·opal/ 사후조건.
#                            [정합 fix] $script:DlShaFile 을 sha 다운로드 시도 이전에 기록 — 첫 폴백에서도
#                            부분 수신 파일이 폐기되도록 bash 2경로와 동형화(D-3).
#                            unverified·branch 사용자 안내를 실제 동작에 맞게 교정 — bash 2경로 문구와 정합(D-5).
#                            Set-DlSecurityProtocol 도입 — Tls13 열거 멤버 부재(.NET < 4.8) 환경에서
#                            즉시 throw 되던 결함 제거, TLS 1.2 로 안전 축퇴(PS-1).
#                            [정합 fix] DRY-RUN 계획을 버전 종류로 분기 — 태그(v*)에 실재하지 않는
#                            archive/refs/heads URL 을 안내하던 회귀 제거. 네트워크 0회 계약 유지(O-1).
#                            [정합 fix] 폴백 사유 문구에 괄호 상세구 보강 — bash 2경로 리터럴과
#                            상세 수준 일치(O-4) (085)
#
# DL-CONTRACT (085): 릴리즈 태그는 릴리즈 자산 우선 + sha256sums.txt 부재 시 자동 아카이브 폴백(UNVERIFIED) + strip 자동 판정
$ErrorActionPreference = 'Stop'

# ─── 환경 변수 오버라이드 ────────────────────────────────────────────────────
$OpalRepo    = if ($env:OPAL_REPO)    { $env:OPAL_REPO    } else { 'ceo4ever/opal' }
$OpalVersion = $env:OPAL_VERSION  # 미설정 시 Resolve-DefaultVersion 호출
$DryRun      = ($env:OPAL_DRY_RUN -eq '1')

# ─── Resolve-DefaultVersion (install.sh v1.2 와 정합) ─────────────────────
# OpalVersion 미설정 시 자동 결정:
#   1) /releases/latest → tag_name
#   2) 폴백: /tags?per_page=1 → name
#   3) 두 단계 모두 실패 시 "main"
function Resolve-DefaultVersion {
    if ($OpalVersion) { return }
    if ($DryRun)      { $script:OpalVersion = 'main'; return }

    $latest = $null
    try {
        $resp = Invoke-RestMethod -Uri "https://api.github.com/repos/$OpalRepo/releases/latest" -ErrorAction Stop
        if ($resp.tag_name) { $latest = $resp.tag_name }
    } catch {}

    if (-not $latest) {
        try {
            $resp = Invoke-RestMethod -Uri "https://api.github.com/repos/$OpalRepo/tags?per_page=1" -ErrorAction Stop
            if ($resp -and $resp.Count -gt 0 -and $resp[0].name) {
                $latest = $resp[0].name
            }
        } catch {}
    }

    if ($latest) {
        $script:OpalVersion = $latest
    } else {
        $script:OpalVersion = 'main'
        Write-Warning "[OPAL] 최신 버전 조회 실패 — main 브랜치 사용"
    }
}

Resolve-DefaultVersion

# 주의: $env:OPAL_VERSION 으로 export 하지 않는다.
#       PowerShell 세션에 값이 잔존하여 다음 실행 시 사용자 명시로 오인되는 결함을 회피.
#       windows.ps1 에는 -OpalVersion 파라미터로 명시 전달한다.

# ─── 다운로드 계획 상태 (DL-CONTRACT 085) ────────────────────────────────────
# URL·로컬 파일명·체크섬 모드는 모듈 스코프 상수가 아니라 Resolve-DownloadPlan 이 결정한다.
#   $script:DlMode 는 정확히 verify | unverified | branch 3종이다.
$script:DlUrl     = $null
$script:DlName    = $null
$script:DlMode    = $null
$script:DlShaFile = $null

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

function Set-DlSecurityProtocol {
    <#
    .SYNOPSIS
        다운로드 직전 전송 보안을 TLS 1.2 이상으로 강제한다 (DL-CONTRACT 085).
    .DESCRIPTION
        [Net.SecurityProtocolType]::Tls13 열거 멤버는 .NET Framework 4.8+ 에만 존재한다.
        구환경(Windows PowerShell 5.1 / .NET < 4.8)에서 직접 참조하면 $ErrorActionPreference='Stop'
        하에 즉시 throw 되어 폴백조차 타지 못하고 설치가 통째로 중단된다.
        따라서 Tls13 은 열거에 존재할 때만 추가하고, 플랫폼이 값을 거부하면 TLS 1.2 로 축퇴한다.
        [MUST] 어떤 경로에서도 TLS 1.2 미만으로 내려가지 않는다.
    #>
    $tls12  = [Net.SecurityProtocolType]::Tls12
    $target = $tls12
    if ([Enum]::GetNames([Net.SecurityProtocolType]) -contains 'Tls13') {
        $target = $tls12 -bor [Net.SecurityProtocolType]::Tls13
    }
    try {
        [Net.ServicePointManager]::SecurityProtocol = $target
    }
    catch {
        # 열거에는 있으나 플랫폼(SChannel)이 지원하지 않는 경우 — TLS 1.2 로 안전 축퇴.
        [Net.ServicePointManager]::SecurityProtocol = $tls12
    }
}

function Get-DlAssetName {
    <#
    .SYNOPSIS
        sha256sums.txt 의 파일명 컬럼에서 첫 .tar.gz 자산명을 파생한다 (DL-CONTRACT 085).
        자산명을 하드코딩하지 않으므로 발행 자산명이 바뀌어도 자동 추종한다.
        binary mode 표기('*' 접두)를 제거한다. 파생 실패 시 $null 반환 — 호출자가 폴백을 판단한다.
    #>
    param(
        [Parameter(Mandatory)]
        [string] $ShaFile
    )

    foreach ($line in @(Get-Content -LiteralPath $ShaFile -ErrorAction SilentlyContinue)) {
        $cols = @($line -split '\s+' | Where-Object { $_ })
        if ($cols.Count -ge 2) {
            $name = $cols[1] -replace '^\*', ''
            if ($name -like '*.tar.gz') { return $name }
        }
    }
    return $null
}

function Set-DlFallback {
    <#
    .SYNOPSIS
        릴리즈 자산을 사용할 수 없을 때 GitHub 자동 아카이브로 강등한다 (DL-CONTRACT 085).
        3동작을 동시에 수행한다: URL 재지정 / 로컬명을 발행 자산명과 다르게 재지정 / sha256sums.txt 폐기.
    #>
    param(
        [Parameter(Mandatory)]
        [string] $Reason
    )

    $script:DlUrl  = "https://github.com/$OpalRepo/archive/refs/tags/$($script:OpalVersion).tar.gz"
    $script:DlName = "opal-$($script:OpalVersion)-archive.tar.gz"
    $script:DlMode = 'unverified'

    # [MUST] 폴백 경로에서는 sha256sums.txt 를 어떤 경우에도 비교에 사용하지 않는다.
    #        발행 자산과 자동 아카이브는 서로 다른 파일이므로 비교하면 100% 불일치한다.
    if ($script:DlShaFile -and (Test-Path -LiteralPath $script:DlShaFile)) {
        Remove-Item -LiteralPath $script:DlShaFile -Force -ErrorAction SilentlyContinue
    }
    $script:DlShaFile = $null

    Write-Warning "[OPAL] 릴리즈 자산 미사용 폴백: $Reason"
}

function Resolve-DownloadPlan {
    <#
    .SYNOPSIS
        다운로드 소스를 확정한다 (DL-CONTRACT 085).
        산출(script scope): $script:DlUrl / $script:DlName / $script:DlMode / $script:DlShaFile
        릴리즈 자산 존재 판정은 sha256sums.txt 다운로드 성공 여부를 단일 신호로 사용한다.
    #>
    param(
        [Parameter(Mandatory)]
        [string] $DestDir
    )

    # DRY-RUN 은 네트워크에 접근하지 않는다 — 조회 없이 계획을 구성하고 조기 반환한다 (RG-7).
    # [MUST] 버전 종류로 분기한다. 태그(v*)에도 브랜치 URL(archive/refs/heads)을 안내하면
    #        실재하지 않는 경로를 안내하게 된다. 릴리즈 자산명은 sha256sums.txt 조회로만 확정되므로
    #        DRY-RUN 에서는 미확정임을 그대로 표시한다 (bash 2경로 dry-run 안내와 동형).
    if ($DryRun) {
        if ($script:OpalVersion -like 'v*') {
            # 1순위는 릴리즈 자산이다. 자산 부재 시에만 자동 아카이브로 폴백한다.
            # DlMode='verify' 는 '계획상 1순위'를 뜻한다 — 실제 모드는 실행 시 조회로 확정된다.
            $script:DlUrl  = "https://github.com/$OpalRepo/releases/download/$($script:OpalVersion)/<sha256sums.txt 파생 자산명>"
            $script:DlName = "opal-$($script:OpalVersion).tar.gz"   # DRY-RUN 흐름용 임시 로컬명
            $script:DlMode = 'verify'
            Write-Host "[OPAL][DRY-RUN] 다운로드 소스: releases/download/$($script:OpalVersion)/<sha256sums.txt 파생 자산명> (자산 부재 시 자동 아카이브 폴백)" -ForegroundColor Yellow
        }
        else {
            $script:DlUrl  = "https://github.com/$OpalRepo/archive/refs/heads/$($script:OpalVersion).tar.gz"
            $script:DlName = "opal-$($script:OpalVersion).tar.gz"
            $script:DlMode = 'branch'
            Write-Host "[OPAL][DRY-RUN] 다운로드 소스: $($script:OpalVersion) 브랜치 아카이브 (UNVERIFIED)" -ForegroundColor Yellow
        }
        Write-Host '[OPAL][DRY-RUN] 다운로드 계획 조회 생략 (네트워크 미접근).' -ForegroundColor Yellow
        return
    }

    # 브랜치 설치(main 등) — 기존 URL·정책 유지.
    if ($script:OpalVersion -notlike 'v*') {
        $script:DlUrl  = "https://github.com/$OpalRepo/archive/refs/heads/$($script:OpalVersion).tar.gz"
        $script:DlName = "opal-$($script:OpalVersion).tar.gz"
        $script:DlMode = 'branch'
        return
    }

    # TLS 1.2 이상 강제 (Tls13 은 가용할 때만 — 구환경 throw 회피)
    Set-DlSecurityProtocol

    $shaUrl  = "https://github.com/$OpalRepo/releases/download/$($script:OpalVersion)/sha256sums.txt"
    $shaFile = Join-Path $DestDir 'sha256sums.txt'
    # [MUST] 다운로드 시도 **이전**에 경로를 기록한다 — 실패 시 Set-DlFallback 이 부분 수신 파일을
    #        폐기할 수 있어야 한다 (폴백 3동작 중 'sha256sums.txt 폐기'. bash 2경로와 동형).
    $script:DlShaFile = $shaFile

    try {
        Write-Host "[OPAL] sha256sums.txt 다운로드 중: $shaUrl" -ForegroundColor Cyan
        Invoke-RestMethod -Uri $shaUrl -OutFile $shaFile -ErrorAction Stop
    }
    catch {
        Set-DlFallback -Reason '릴리즈 자산 없음 (sha256sums.txt 조회 실패)'
        return
    }

    $asset = Get-DlAssetName -ShaFile $shaFile
    if (-not $asset) {
        Set-DlFallback -Reason 'sha256sums.txt 형식 이상 (.tar.gz 항목 없음)'
        return
    }

    $script:DlUrl  = "https://github.com/$OpalRepo/releases/download/$($script:OpalVersion)/$asset"
    $script:DlName = $asset          # [MUST] 로컬명 = 발행 자산명 (검증 대상 = 다운로드 대상)
    $script:DlMode = 'verify'
}

function Get-DlStripComponents {
    <#
    .SYNOPSIS
        tarball 최상위 구조를 판정하여 --strip-components 값(0|1)을 반환한다 (DL-CONTRACT 085).
        루트 직속 항목이 0개이고 최상위 세그먼트가 1종이면 1, 그 외에는 0.
    #>
    param(
        [Parameter(Mandatory)]
        [string] $TarballPath
    )

    $entries = @()
    try {
        $entries = @(& tar -tzf $TarballPath | Where-Object { $_ })
    }
    catch {
        throw "[OPAL] tarball 목록 조회 실패: $TarballPath ($($_.Exception.Message))"
    }
    if ($LASTEXITCODE -ne 0 -or $entries.Count -eq 0) {
        throw "[OPAL] tarball 목록 조회 실패: $TarballPath (tar exit=$LASTEXITCODE)"
    }

    $rootFiles = @($entries | Where-Object { $_ -notmatch '/' })
    $tops      = @($entries | ForEach-Object { ($_ -split '/', 2)[0] } | Sort-Object -Unique)
    if ($rootFiles.Count -eq 0 -and $tops.Count -eq 1) { return 1 } else { return 0 }
}

function Fetch-Tarball {
    <#
    .SYNOPSIS
        Resolve-DownloadPlan 이 확정한 계획($script:DlUrl / $script:DlName)으로 tarball 을 다운로드한다.
        릴리즈 자산 다운로드에 실패하면 자동 아카이브로 1회 강등한 뒤 재시도한다 (DL-CONTRACT 085).
    .OUTPUTS
        다운로드된 .tar.gz 파일의 전체 경로.
    #>
    param(
        [Parameter(Mandatory)]
        [string] $DestDir
    )

    $outFile = Join-Path $DestDir $script:DlName

    if ($DryRun) {
        Write-Host "[OPAL][DRY-RUN] fetch 생략: $($script:DlUrl)" -ForegroundColor Yellow
        # dry-run 시 빈 파일을 생성하여 이후 단계가 경로를 참조할 수 있게 한다
        Set-Content -Path $outFile -Value '' -Encoding UTF8
        return $outFile
    }

    # TLS 1.2 이상 강제 (Tls13 은 가용할 때만 — 구환경 throw 회피)
    Set-DlSecurityProtocol

    Write-Host "[OPAL] tarball 다운로드 중: $($script:DlUrl)" -ForegroundColor Cyan
    try {
        Invoke-RestMethod `
            -Uri         $script:DlUrl `
            -OutFile     $outFile `
            -ErrorAction Stop
    }
    catch {
        if ($script:DlMode -ne 'verify') {
            throw "[OPAL] tarball 다운로드 실패: $($script:DlUrl)"
        }
        # 릴리즈 자산 다운로드 실패 — 자동 아카이브로 1회 강등(UNVERIFIED) 후 재시도.
        Set-DlFallback -Reason '릴리즈 자산 다운로드 실패'
        $outFile = Join-Path $DestDir $script:DlName
        Write-Host "[OPAL] tarball 다운로드 중: $($script:DlUrl)" -ForegroundColor Cyan
        try {
            Invoke-RestMethod `
                -Uri         $script:DlUrl `
                -OutFile     $outFile `
                -ErrorAction Stop
        }
        catch {
            throw "[OPAL] tarball 다운로드 실패: $($script:DlUrl)"
        }
    }

    Write-Host "[OPAL] 다운로드 완료: $outFile" -ForegroundColor Green
    return $outFile
}

function Verify-Checksum {
    <#
    .SYNOPSIS
        $script:DlMode 3분기로 체크섬 정책을 적용한다 (DL-CONTRACT 085).
          verify     — 발행 자산을 그대로 받았으므로 반드시 일치해야 한다. 무음 스킵 금지.
          unverified — 자동 아카이브 폴백 경로. 옵트인 / 비대화형 거부 / 프롬프트 3분기(fail-closed).
          branch     — 브랜치 설치. 검증 대상 자체가 없다 (UNVERIFIED 배너는 Invoke-OpalInstall 에서 출력).
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

    switch ($script:DlMode) {

        'verify' {
            if (-not $script:DlShaFile -or -not (Test-Path -LiteralPath $script:DlShaFile)) {
                throw "[OPAL] sha256sums.txt 를 찾을 수 없습니다 — 검증 모드에서 설치를 중단합니다."
            }

            # 파일명 컬럼을 고정 문자열로 비교한다 — '.' 이 정규식 와일드카드로 해석되는 결함을 원천 차단.
            $expectedHash = $null
            foreach ($line in @(Get-Content -LiteralPath $script:DlShaFile)) {
                $cols = @($line -split '\s+' | Where-Object { $_ })
                if ($cols.Count -ge 2) {
                    $name = $cols[1] -replace '^\*', ''
                    if ($name -eq $script:DlName) {
                        $expectedHash = $cols[0].ToLower()
                        break
                    }
                }
            }

            # [MUST] 무음 스킵 금지 — 항목 부재·기대값 파싱 실패는 규약 위반이므로 설치를 거부한다.
            if (-not $expectedHash) {
                throw "[OPAL] sha256sums.txt 에 '$($script:DlName)' 항목이 없거나 기대값을 파싱할 수 없습니다 — 설치를 중단합니다."
            }

            $actualHash = (Get-FileHash -Path $TarballPath -Algorithm SHA256).Hash.ToLower()
            if ($actualHash -ne $expectedHash) {
                throw "[OPAL] 체크섬 불일치! 예상: $expectedHash / 실제: $actualHash"
            }

            Write-Host '[OPAL] 체크섬 검증 통과.' -ForegroundColor Green
        }

        'unverified' {
            if ($env:OPAL_ALLOW_UNVERIFIED -eq '1') {
                Write-Warning "[UNVERIFIED] 릴리즈 자산 없음 — OPAL_ALLOW_UNVERIFIED=1로 무결성 검증 없이 진행"
                return
            }
            # 비대화형 검출: OPAL_AUTO_INSTALL=1 또는 UserInteractive 미지원 환경
            $isNonInteractive = ($env:OPAL_AUTO_INSTALL -eq '1') -or (-not [Environment]::UserInteractive)
            if ($isNonInteractive) {
                throw "[OPAL] 릴리즈 자산 없음 — 비대화형 모드에서 무결성 검증 없는 설치를 거부합니다. 옵트인: `$env:OPAL_ALLOW_UNVERIFIED='1'"
            }
            # 대화형: prompt (디폴트 N)
            $confirm = Read-Host "릴리즈 자산 없음 — 무결성 검증 없이 진행하시겠습니까? [y/N]"
            if ($confirm -notmatch '^[yY]$') {
                throw "[OPAL] 사용자가 취소했습니다. 옵트인: `$env:OPAL_ALLOW_UNVERIFIED='1'"
            }
            Write-Warning "[UNVERIFIED] 사용자 동의로 무결성 검증 없이 진행"
        }

        'branch' {
            # 브랜치 경로는 sha256sums.txt 를 조회조차 하지 않는다 — '없음' 이 아니라 '검증 대상 아님'.
            # UNVERIFIED 배너는 Invoke-OpalInstall 이 이미 출력했다 (RG-3).
            Write-Warning "[OPAL] 브랜치 설치 — SHA-256 무결성 검증 대상 아님"
        }

        default {
            # fail-closed: 계획이 수립되지 않은 상태로는 검증을 건너뛰지 않는다.
            throw "[OPAL] 다운로드 계획이 없습니다 (DlMode='$($script:DlMode)') — 설치를 중단합니다."
        }
    }
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

    $extractDir = Join-Path $DestDir 'opal-src'
    New-Item -ItemType Directory -Path $extractDir -Force | Out-Null

    # tar: Windows 10 1803+ 기본 tar 또는 Git for Windows tar 사용.
    # --exclude 'tasks*' / '*/tasks/*' — 프로젝트 작업 산출물(tasks/) 제외:
    #   archive 에는 tasks/ 가 포함되지만 install 대상이 아니다. tasks/backup/ 의 한글 파일명이
    #   Windows tar.exe(libarchive)에서 인코딩 처리 실패로 압축 해제를 throw 시키므로 제외.
    # [MUST] 조건부 인자는 배열 splatting 으로 구성한다 — 문자열 보간으로 조립하면
    #        빈 인자가 tar 에 전달되어 실패한다 (DL-CONTRACT 085).
    $strip   = Get-DlStripComponents -TarballPath $TarballPath
    $tarArgs = @('-xzf', $TarballPath, '-C', $extractDir)
    if ($strip -eq 1) { $tarArgs += @('--strip-components', '1') }
    $tarArgs += @('--exclude=tasks/*', '--exclude=*/tasks/*', '--exclude=tasks', '--exclude=*/tasks')

    Write-Host "[OPAL] tarball 압축 해제 중... (strip-components=$strip)" -ForegroundColor Cyan
    $tarExit = 0
    try {
        & tar @tarArgs
        $tarExit = $LASTEXITCODE
    }
    catch {
        $tarExit = 1
        Write-Warning "[OPAL] tar 실행 중 오류: $($_.Exception.Message)"
    }
    if ($tarExit -ne 0) {
        # tar 가 일부 오류로 0 이 아닌 코드를 반환해도 핵심 자산이 풀렸으면 진행 가능.
        # 성공 여부는 아래 사후조건이 최종 판정한다.
        Write-Warning "[OPAL] tar 일부 오류 (exit=$tarExit) — 추출 결과 사후조건으로 판정합니다."
    }

    # [MUST] 사후조건 — VERSION 과 opal/ 이 모두 루트에 있어야 한다. 조용한 진행 금지.
    $okVersion = Test-Path ([IO.Path]::Combine($extractDir, 'VERSION'))
    $okOpal    = Test-Path ([IO.Path]::Combine($extractDir, 'opal'))
    if (-not ($okVersion -and $okOpal)) {
        throw "[OPAL] 추출 결과 구조 이상 — VERSION 또는 opal/ 이 루트에 없습니다 (strip=$strip, tar exit=$tarExit)"
    }

    # 각인 VERSION 우선 — 추출된 tarball의 VERSION이 치환되어 있으면 채택 (048)
    # -notlike '*$Format:*' 판별 — placeholder 미치환 시 채택 안 함(폴백).
    # PowerShell -like 는 와일드카드, '$Format:' 의 '$' 는 작은따옴표로 리터럴 매칭.
    $versionFile = [IO.Path]::Combine($extractDir, 'VERSION')
    if (Test-Path $versionFile) {
        $stamped = (Get-Content -Raw -LiteralPath $versionFile -ErrorAction SilentlyContinue)
        if ($stamped) { $stamped = $stamped.Trim() }
        if ($stamped -and ($stamped -notlike '*$Format:*')) {
            $script:OpalVersion = $stamped
            Write-Host "[OPAL] tarball VERSION 각인값 채택: $stamped" -ForegroundColor DarkGray
        }
    }

    # [IO.Path]::Combine — PowerShell 5.1 에서도 다중 path 결합 안전 (Join-Path 5.1 은 위치 인자 2개만).
    $windowsInstaller = [IO.Path]::Combine($extractDir, 'scripts', 'install', 'windows.ps1')
    if (-not (Test-Path $windowsInstaller)) {
        throw "[OPAL] windows.ps1 을 찾을 수 없습니다: $windowsInstaller"
    }

    Write-Host '[OPAL] windows.ps1 실행 중...' -ForegroundColor Cyan
    # ExecutionPolicy Bypass 로 명시 — Restricted/RemoteSigned 환경에서도 다운로드된 .ps1 실행 가능.
    # 현재 실행 중인 PowerShell engine 경로 사용 (PS 5.1 powershell.exe, PS 7 pwsh.exe 자동 매칭).
    $psExe = (Get-Process -Id $PID).Path
    if (-not $psExe -or -not (Test-Path $psExe)) {
        # 폴백: PSHOME 기준
        $psExe = Join-Path $PSHOME 'powershell.exe'
        if (-not (Test-Path $psExe)) { $psExe = Join-Path $PSHOME 'pwsh.exe' }
    }
    & $psExe -ExecutionPolicy Bypass -NoProfile -File $windowsInstaller -OpalVersion $script:OpalVersion
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

    # main 브랜치 UNVERIFIED banner (release tag 외 모든 버전) (R-2, GC-001)
    if ($OpalVersion -notlike 'v*') {
        Write-Warning "[UNVERIFIED] '$OpalVersion' 브랜치 설치 — SHA-256 무결성 검증 없음. 공식 릴리스(v*)를 권장합니다."
    }

    Test-Deps

    # 임시 폴더 생성 — try/finally 로 항상 정리
    $tmpDir = Join-Path $env:TEMP "opal-install-$([guid]::NewGuid())"
    New-Item -ItemType Directory -Path $tmpDir -Force | Out-Null

    try {
        Resolve-DownloadPlan -DestDir $tmpDir
        $tarball = Fetch-Tarball -DestDir $tmpDir
        Verify-Checksum -TarballPath $tarball -DestDir $tmpDir
        Invoke-PlatformInstaller -TarballPath $tarball -DestDir $tmpDir

        Write-Host ''
        Write-Host '[OPAL] 설치가 완료되었습니다.' -ForegroundColor Green
        Write-Host '[OPAL] 새 PowerShell 세션을 열거나 PATH 를 갱신한 뒤 opal-cli 를 사용하세요.' -ForegroundColor Green
        Write-Host ''
    }
    finally {
        # 단축 경로(8.3) 처리 + 정리 실패 무시 (Resolve-Path 로 long path 우선 시도)
        try {
            if (Test-Path -LiteralPath $tmpDir) {
                $resolved = (Resolve-Path -LiteralPath $tmpDir -ErrorAction SilentlyContinue).Path
                if (-not $resolved) { $resolved = $tmpDir }
                Remove-Item -LiteralPath $resolved -Recurse -Force -ErrorAction SilentlyContinue
            }
        } catch {
            Write-Warning "[OPAL] 임시 디렉토리 정리 실패 (수동 삭제: $tmpDir)"
        }
    }
}

Invoke-OpalInstall
