$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { Write-Error 'Python 3.8+ is required.'; exit 2 }
& $python.Source (Join-Path $PSScriptRoot 'lib\dev_kit.py') doctor @args
exit $LASTEXITCODE
