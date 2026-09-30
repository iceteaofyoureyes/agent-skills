[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$NodeHome,
    [string]$PythonCommand = "python"
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$nodeHomePath = (Resolve-Path -LiteralPath $NodeHome).Path
$nodeExe = Join-Path $nodeHomePath "node.exe"
$npmCmd = Join-Path $nodeHomePath "npm.cmd"
if (-not (Test-Path -LiteralPath $nodeExe -PathType Leaf) -or -not (Test-Path -LiteralPath $npmCmd -PathType Leaf)) {
    throw "NodeHome must contain node.exe and npm.cmd."
}
if ($nodeHomePath -match "(?i)nvm4w") {
    throw "The smoke Node runtime must be portable and outside C:\nvm4w."
}
$pythonExe = (Get-Command $PythonCommand -ErrorAction Stop).Source
$pathSeparators = [char[]]@([char]92, [char]47)
$tempBase = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath()).TrimEnd($pathSeparators)
$tempRoot = Join-Path $tempBase ("test-kit-installed-smoke-" + [guid]::NewGuid().ToString("N"))
$project = Join-Path $tempRoot "project"
$skillTarget = Join-Path $project ".agents\skills"
$runtime = Join-Path $skillTarget ".test-kit"
$pythonDeps = Join-Path $tempRoot "python-deps"
$smokeScript = Join-Path $tempRoot "installed_package_smoke.py"
$completed = $false

try {
    New-Item -ItemType Directory -Force -Path $skillTarget | Out-Null
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot "fixtures\installed_package_smoke.py") -Destination $smokeScript

    & (Join-Path $repoRoot "tooling\install.ps1") -Kit test --agent generic --target $skillTarget
    if ($LASTEXITCODE -ne 0) { throw "Test Kit install failed with exit code $LASTEXITCODE." }

    $doctorCodexStub = Join-Path $project "codex-doctor-stub.exe"
    Set-Content -LiteralPath $doctorCodexStub -Value "stub" -NoNewline
    $oldDoctorCodexCommand = $env:TEST_KIT_CODEX_COMMAND
    try {
        $env:TEST_KIT_CODEX_COMMAND = $doctorCodexStub
        & (Join-Path $repoRoot "tooling\doctor.ps1") -Kit test --agent generic --target $skillTarget
        if ($LASTEXITCODE -ne 0) { throw "Installed Test Kit doctor failed with exit code $LASTEXITCODE." }
    }
    finally {
        $env:TEST_KIT_CODEX_COMMAND = $oldDoctorCodexCommand
    }

    Push-Location (Join-Path $runtime "tooling\xmind")
    try {
        & $npmCmd ci
        if ($LASTEXITCODE -ne 0) { throw "Explicit XMind npm ci bootstrap failed with exit code $LASTEXITCODE." }
    }
    finally {
        Pop-Location
    }

    & $pythonExe -m pip install --require-hashes --target $pythonDeps -r (Join-Path $runtime "tooling\requirements-excel.lock")
    if ($LASTEXITCODE -ne 0) { throw "Explicit Excel dependency bootstrap failed with exit code $LASTEXITCODE." }

    $oldPath = $env:PATH
    $oldPythonPath = $env:PYTHONPATH
    $oldCodexCommand = $env:TEST_KIT_CODEX_COMMAND
    $oldRealStub = $env:TEST_KIT_USE_REAL_CODEX_STUB
    $oldOptional = $env:TEST_KIT_RUN_OPTIONAL
    try {
        $remainingPath = @($oldPath -split ";" | Where-Object { $_ -notmatch "(?i)nvm4w" })
        $env:PATH = $nodeHomePath + ";" + ($remainingPath -join ";")
        $env:PYTHONPATH = $runtime + ";" + $pythonDeps
        $env:TEST_KIT_CODEX_COMMAND = Join-Path $project "codex-stub.js"
        $env:TEST_KIT_USE_REAL_CODEX_STUB = "1"
        $env:TEST_KIT_RUN_OPTIONAL = "1"

        Push-Location $project
        try {
            & $pythonExe -S -B $smokeScript $runtime $repoRoot
            if ($LASTEXITCODE -ne 0) { throw "Installed Test Kit smoke failed with exit code $LASTEXITCODE." }
        }
        finally {
            Pop-Location
        }
    }
    finally {
        $env:PATH = $oldPath
        $env:PYTHONPATH = $oldPythonPath
        $env:TEST_KIT_CODEX_COMMAND = $oldCodexCommand
        $env:TEST_KIT_USE_REAL_CODEX_STUB = $oldRealStub
        $env:TEST_KIT_RUN_OPTIONAL = $oldOptional
    }

    $completed = $true
}
finally {
    if (Test-Path -LiteralPath $tempRoot) {
        $resolvedTemp = [System.IO.Path]::GetFullPath((Resolve-Path -LiteralPath $tempRoot).Path)
        $actualParent = [System.IO.Path]::GetDirectoryName($resolvedTemp).TrimEnd($pathSeparators)
        if (-not [string]::Equals($actualParent, $tempBase, [System.StringComparison]::OrdinalIgnoreCase)) {
            throw "Refusing to clean smoke output outside OS temp: $resolvedTemp"
        }
        Remove-Item -LiteralPath $resolvedTemp -Recurse -Force
    }
}

if ($completed) {
    Write-Output "CLEAN_INSTALL_SMOKE: PASS"
}
