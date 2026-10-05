[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)] [string]$GatewayRequestPath,
    [Parameter(Mandatory = $true)] [string]$GatewayResultPath
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0

function Write-ProjectResult {
    param(
        [string]$Status,
        [string]$ErrorMessage = '',
        [hashtable]$Extra = @{}
    )
    $payload = [ordered]@{
        status = $Status
        error = $ErrorMessage
    }
    foreach ($key in $Extra.Keys) { $payload[$key] = $Extra[$key] }
    $payload | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $GatewayResultPath -Encoding UTF8
}

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)] [string]$FilePath,
        [Parameter(Mandatory = $true)] [string[]]$ArgumentList
    )
    & $FilePath @ArgumentList
    if ($LASTEXITCODE -ne 0) {
        throw "$FilePath failed with exit code $LASTEXITCODE"
    }
}

try {
    $request = Get-Content -LiteralPath $GatewayRequestPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $version = [string]$request.args.version
    if ([string]::IsNullOrWhiteSpace($version)) {
        $version = (Get-Content -LiteralPath 'RELEASE_VERSION' -Raw -Encoding UTF8).Trim()
    }
    $kind = (Get-Content -LiteralPath 'RELEASE_KIND' -Raw -Encoding UTF8).Trim()

    $releaseVersion = (Get-Content -LiteralPath 'RELEASE_VERSION' -Raw -Encoding UTF8).Trim()
    if ($releaseVersion -ne $version) {
        throw "RELEASE_VERSION is $releaseVersion, requested $version"
    }

    $python = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($null -eq $python) {
        $python = Get-Command python -ErrorAction SilentlyContinue
    }
    if ($null -eq $python) {
        throw 'Python is not available on the PC gateway host.'
    }
    $pythonExe = [string]$python.Source

    Invoke-Checked $pythonExe @('-m', 'pip', 'install', '--upgrade', 'pip')
    Invoke-Checked $pythonExe @('-m', 'pip', 'install', '-e', '.[dev]')
    Invoke-Checked $pythonExe @('-m', 'pytest', '-q')
    Invoke-Checked $pythonExe @('-m', 'ruff', 'check', 'src', 'tests', 'packaging/generate_icon.py')
    Invoke-Checked $pythonExe @('packaging/generate_icon.py')

    Invoke-Checked $pythonExe @(
        '-m', 'PyInstaller',
        '--noconfirm', '--clean', '--windowed', '--onedir',
        '--name', 'Megafon Desktop',
        '--icon', 'build\icon\megafon-desktop.ico',
        '--paths', 'src',
        'src/megafon_desktop/app.py'
    )

    $programFilesX86 = [Environment]::GetFolderPath('ProgramFilesX86')
    $compilerCandidates = @(
        (Join-Path $programFilesX86 'Inno Setup 6\ISCC.exe'),
        (Join-Path $env:LOCALAPPDATA 'Programs\Inno Setup 6\ISCC.exe')
    )
    $compiler = $compilerCandidates | Where-Object {
        Test-Path -LiteralPath $_ -PathType Leaf
    } | Select-Object -First 1

    if (-not $compiler) {
        $winget = Get-Command winget.exe -ErrorAction SilentlyContinue
        if ($null -ne $winget) {
            Invoke-Checked ([string]$winget.Source) @(
                'install', '--id', 'JRSoftware.InnoSetup', '--exact', '--silent',
                '--accept-package-agreements', '--accept-source-agreements'
            )
            $compiler = $compilerCandidates | Where-Object {
                Test-Path -LiteralPath $_ -PathType Leaf
            } | Select-Object -First 1
        }
    }
    if (-not $compiler) {
        throw 'Inno Setup 6 ISCC.exe is not available and could not be provisioned.'
    }

    Invoke-Checked ([string]$compiler) @(
        "/DMyAppVersion=$version",
        "/DPackageKind=$kind",
        'packaging\megafon-desktop.iss'
    )

    $installerName = "MegafonDesktop-$kind-v$version.exe"
    $installerPath = Join-Path 'dist-installer' $installerName
    if (-not (Test-Path -LiteralPath $installerPath -PathType Leaf)) {
        throw "Installer not found: $installerPath"
    }

    $installerItem = Get-Item -LiteralPath $installerPath
    $digest = (Get-FileHash -LiteralPath $installerPath -Algorithm SHA256).Hash.ToLowerInvariant()
    $tag = "v$version"
    $repository = 'lvlaksim1/megafon-desktop'
    $downloadUrl = "https://github.com/$repository/releases/download/$tag/$installerName"

    $gh = Get-Command gh.exe -ErrorAction SilentlyContinue
    if ($null -eq $gh) {
        $gh = Get-Command gh -ErrorAction SilentlyContinue
    }
    if ($null -eq $gh) {
        throw 'GitHub CLI is not available on the PC gateway host.'
    }
    $ghExe = [string]$gh.Source

    $savedGhToken = $env:GH_TOKEN
    $savedGitHubToken = $env:GITHUB_TOKEN
    try {
        Remove-Item Env:GH_TOKEN -ErrorAction SilentlyContinue
        Remove-Item Env:GITHUB_TOKEN -ErrorAction SilentlyContinue

        & $ghExe auth status --hostname github.com *> $null
        if ($LASTEXITCODE -ne 0) {
            throw 'The interactive PC runner has no usable local GitHub CLI authentication.'
        }

        $head = (& git rev-parse HEAD | Select-Object -First 1).Trim()
        $notesPath = Join-Path $env:TEMP "megafon-desktop-$version-release-notes.txt"
        @"
Megafon Desktop $tag

- Restored manual "Обновить выбранные"; removed "Обновить всё" and per-row actions.
- Resizable/movable columns with persisted layout and drag-reorderable account rows.
- Application-wide System/Light/Dark theme setting.
- Added latest-action amount/name/date, offers and blocking columns.
- Added "База оферов" and "Доступные опции" using the legacy VBA data model.
- Added selected-account number blocking/unblocking using the VBA option mechanism.
- Preserved the verified HTTP-only B2C authorization/session/CAPTCHA foundation.
- Refresh-token renewal remains intentionally unimplemented pending a proven current source.

Installer: $installerName
SHA-256: $digest
"@ | Set-Content -LiteralPath $notesPath -Encoding UTF8

        Invoke-Checked $ghExe @(
            'release', 'create', $tag, $installerPath,
            '--repo', $repository,
            '--target', $head,
            '--title', "Megafon Desktop $tag",
            '--notes-file', $notesPath
        )
        Remove-Item -LiteralPath $notesPath -Force -ErrorAction SilentlyContinue

        $releaseRows = & $ghExe release list --repo $repository --limit 100 --json tagName |
            ConvertFrom-Json
        foreach ($release in @($releaseRows)) {
            if ([string]$release.tagName -ne $tag) {
                Invoke-Checked $ghExe @(
                    'release', 'delete', [string]$release.tagName,
                    '--repo', $repository, '--cleanup-tag', '--yes'
                )
            }
        }
    }
    finally {
        if ($null -ne $savedGhToken) { $env:GH_TOKEN = $savedGhToken }
        if ($null -ne $savedGitHubToken) { $env:GITHUB_TOKEN = $savedGitHubToken }
    }

    Write-ProjectResult -Status 'success' -Extra @{
        version = $version
        installer_name = $installerName
        installer_size = [int64]$installerItem.Length
        sha256 = $digest
        download_url = $downloadUrl
    }
    exit 0
}
catch {
    Write-ProjectResult -Status 'failed' -ErrorMessage $_.Exception.Message
    Write-Error $_
    exit 1
}
