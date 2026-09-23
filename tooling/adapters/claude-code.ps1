param(
    [ValidateSet('user', 'project')][string]$Scope = 'project',
    [string]$ProjectRoot = (Get-Location).Path,
    [string]$Target
)

if ($Target) { return [System.IO.Path]::GetFullPath($Target) }
if ($Scope -eq 'project') { return [System.IO.Path]::GetFullPath((Join-Path $ProjectRoot '.claude\skills')) }
[System.IO.Path]::GetFullPath((Join-Path $HOME '.claude\skills'))
