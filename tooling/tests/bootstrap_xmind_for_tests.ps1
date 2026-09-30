[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$NodeHome
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$nodeHomePath = (Resolve-Path -LiteralPath $NodeHome).Path
if (-not (Test-Path -LiteralPath (Join-Path $nodeHomePath "node.exe") -PathType Leaf) -or
    -not (Test-Path -LiteralPath (Join-Path $nodeHomePath "npm.cmd") -PathType Leaf)) {
    throw "NodeHome must contain node.exe and npm.cmd."
}
if ($nodeHomePath -match "(?i)nvm4w") {
    throw "Use a portable Node runtime outside C:\nvm4w."
}

$oldPath = $env:PATH
try {
    $remainingPath = @($oldPath -split ";" | Where-Object { $_ -notmatch "(?i)nvm4w" })
    $env:PATH = $nodeHomePath + ";" + ($remainingPath -join ";")
    Push-Location (Join-Path $repoRoot "tooling\xmind")
    try {
        & (Join-Path $nodeHomePath "npm.cmd") ci
        if ($LASTEXITCODE -ne 0) {
            throw "XMind test dependency bootstrap failed with exit code $LASTEXITCODE."
        }
    }
    finally {
        Pop-Location
    }
}
finally {
    $env:PATH = $oldPath
}

Write-Output "XMIND_TEST_DEPENDENCIES: READY"
