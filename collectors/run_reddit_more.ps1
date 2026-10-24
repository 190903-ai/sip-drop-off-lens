# 23 Oct Reddit pull for the brief's thin questions, as one detached chain (launched via WMI so it keeps
# running after Claude Code is closed). Every step is resumable, so a relaunch continues where it stopped.
#   1. investing-habit posts (checking, first salary, why start) Oct 2024 - Oct 2026, which the SIP filter dropped
#   2. full threads for question-shaped posts (checking first, then expectations, journeys, who-I-am)
#   3. wider subreddits, Oct 2024 - Oct 2026 (young salaried / new investors)
#   4. the four core subreddits, Oct 2022 - Sep 2024
#   5. threads again, now including posts from steps 3-4
# Log: data\reddit_more_log.txt. Stop it: Task Manager -> end the hidden powershell + python processes.
$root = Split-Path -Parent $PSScriptRoot
Set-Location (Join-Path $root "collectors")
$python = Join-Path $root ".venv\Scripts\python.exe"
$log = Join-Path $root "data\reddit_more_log.txt"
$env:PYTHONIOENCODING = "utf-8"
$steps = @(
    @("reddit.py", "habits", "2024-10-01", "2026-10-22"),  # habit posts the SIP filter dropped in y1/y2
    @("reddit_threads.py"),
    @("reddit.py", "wide", "2024-10-01", "2026-10-22", "developersIndia,IndianStreetBets,StockMarketIndia"),
    @("reddit.py", "y0", "2022-10-01", "2024-10-01"),
    @("reddit_threads.py")
)
foreach ($s in $steps) {
    Add-Content -Path $log -Value "=== $($s -join ' ') $(Get-Date -Format 'dd MMM HH:mm') ===" -Encoding utf8
    & $python -u @s 2>&1 | ForEach-Object { "$_" } | Out-File -FilePath $log -Append -Encoding utf8
}
Add-Content -Path $log -Value "=== chain done $(Get-Date -Format 'dd MMM HH:mm') ===" -Encoding utf8
