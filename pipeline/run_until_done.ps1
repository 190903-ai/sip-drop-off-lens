# Standalone version of run_until_done.sh: rerun a resumable pipeline step until it has no work
# left, waiting 5 minutes between passes (survives Gemma 503 outages). Launched detached via WMI so
# it keeps running after Claude Code is closed.
# Usage: powershell -File pipeline\run_until_done.ps1 pipeline\detect_stories.py data\detect_log.txt
param([string]$Script, [string]$Log)
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$python = Join-Path $root ".venv\Scripts\python.exe"
for ($pass = 1; $pass -le 200; $pass++) {
    Add-Content -Path $Log -Value "=== pass $pass $(Get-Date -Format HH:mm) ===" -Encoding utf8
    & $python -u $Script *>> $Log
    $tail = Get-Content $Log -Tail 20
    if ($tail -match " 0 to go") {
        Add-Content -Path $Log -Value "=== all done $(Get-Date -Format HH:mm) ===" -Encoding utf8
        break
    }
    Start-Sleep -Seconds 300
}
