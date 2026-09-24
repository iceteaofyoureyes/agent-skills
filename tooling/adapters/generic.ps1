param(
    [ValidateSet('user', 'project')][string]$Scope = 'project',
    [string]$ProjectRoot = (Get-Location).Path,
    [string]$Target
)

if (-not $Target) { throw 'Generic mode requires --target <skills-directory>.' }
[System.IO.Path]::GetFullPath($Target)
