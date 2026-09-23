param(
    [Parameter(Mandatory = $true, Position = 0)][ValidateSet('install', 'doctor', 'uninstall')][string]$Operation,
    [Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments
)

$ErrorActionPreference = 'Stop'
$kit = if ($Arguments.Count -gt 0 -and $Arguments[0] -notlike '--*') { $Arguments[0] } else { 'ba' }
$agent = 'codex'
$scope = 'project'
$explicitTarget = $null
for ($i = 0; $i -lt $Arguments.Count; $i++) {
    switch ($Arguments[$i]) {
        '--agent' { if ($i + 1 -ge $Arguments.Count) { Write-Error 'Missing value for --agent.'; exit 2 }; $agent = $Arguments[++$i] }
        '--scope' { if ($i + 1 -ge $Arguments.Count) { Write-Error 'Missing value for --scope.'; exit 2 }; $scope = $Arguments[++$i] }
        '--target' { if ($i + 1 -ge $Arguments.Count) { Write-Error 'Missing value for --target.'; exit 2 }; $explicitTarget = $Arguments[++$i] }
        default {
            if ($Arguments[$i] -like '--*') { Write-Error "Unknown option '$($Arguments[$i])'. Supported options: --agent, --scope, --target."; exit 2 }
            if ($i -gt 0) { Write-Error "Unexpected argument '$($Arguments[$i])'."; exit 2 }
        }
    }
}
if ($kit -ne 'ba') { Write-Error "Unsupported kit '$kit'. This branch packages only BA Kit."; exit 2 }
$adapterName = switch ($agent) {
    'codex' { 'codex.ps1' }
    'claude-code' { 'claude-code.ps1' }
    'generic' { 'generic.ps1' }
    default { Write-Error "Unsupported agent '$agent'. Use codex, claude-code, or generic."; exit 2 }
}
$adapter = Join-Path $PSScriptRoot (Join-Path '..\adapters' $adapterName)
$target = & $adapter -Scope $scope -ProjectRoot (Get-Location).Path -Target $explicitTarget
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { Write-Error 'Python 3.8+ is required. Install Python and ensure python is on PATH.'; exit 2 }
$script = Join-Path $PSScriptRoot 'ba_kit.py'
$cli = @($Operation, $kit, '--agent', $agent, '--scope', $scope, '--target', $target)
& $python.Source $script @cli
exit $LASTEXITCODE
