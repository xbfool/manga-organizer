# Progress Viewer
# Fix encoding issues for Chinese paths
chcp 65001 > $null
$OutputEncoding = [Console]::OutputEncoding = [Console]::InputEncoding = [System.Text.Encoding]::UTF8
$PSDefaultParameterValues['*:Encoding'] = 'utf8'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Progress Viewer" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Set Python path
$pythonPath = "C:\Users\xbfoo\miniconda3\envs\manga\python.exe"

# Check progress file
if (-not (Test-Path ".progress\processing_progress.json")) {
    Write-Host "Progress file not found!" -ForegroundColor Red
    Write-Host "No processing has been started yet" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit
}

Write-Host "Select action:" -ForegroundColor Yellow
Write-Host "1. View summary"
Write-Host "2. Export detailed report"
Write-Host "3. Reset progress (DANGER)"
Write-Host ""

$choice = Read-Host "Enter choice (1-3)"

if ($choice -eq "1") {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    & $pythonPath -X utf8 src\progress_tracker.py --file .progress\processing_progress.json --action summary
    Write-Host "========================================" -ForegroundColor Cyan
}
elseif ($choice -eq "2") {
    Write-Host ""
    Write-Host "Exporting report..." -ForegroundColor Green
    & $pythonPath -X utf8 src\progress_tracker.py --file .progress\processing_progress.json --action export --output reports\progress_summary.txt
    Write-Host ""
    Write-Host "Saved: reports\progress_summary.txt" -ForegroundColor Green
    Write-Host ""
    $open = Read-Host "Open report? (y/n)"
    if ($open -eq "y") {
        notepad reports\progress_summary.txt
    }
}
elseif ($choice -eq "3") {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "WARNING: This will delete all progress!" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    $confirm = Read-Host "Type YES to confirm reset"
    if ($confirm -eq "YES") {
        & $pythonPath -X utf8 src\progress_tracker.py --file .progress\processing_progress.json --action reset
        Write-Host "Progress reset" -ForegroundColor Green
    } else {
        Write-Host "Cancelled" -ForegroundColor Yellow
    }
}
else {
    Write-Host "Invalid choice" -ForegroundColor Red
}

Write-Host ""
Read-Host "Press Enter to exit"
