# RAR Inspector
# Fix encoding issues for Chinese paths
chcp 65001 > $null
$OutputEncoding = [Console]::OutputEncoding = [Console]::InputEncoding = [System.Text.Encoding]::UTF8
$PSDefaultParameterValues['*:Encoding'] = 'utf8'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "RAR File Inspector" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Set Python path
$pythonPath = "C:\Users\xbfoo\miniconda3\envs\manga\python.exe"

Write-Host "Select mode:" -ForegroundColor Yellow
Write-Host "1. Small test"
Write-Host "2. Scan Comics directory (simple)"
Write-Host "3. Scan Comics directory (detailed)"
Write-Host "4. Custom directory scan"
Write-Host ""

$choice = Read-Host "Enter choice (1-4)"

if ($choice -eq "1") {
    Write-Host ""
    Write-Host "[Small test]" -ForegroundColor Green
    $test_dir = Read-Host "Test directory path"
    & $pythonPath -X utf8 src\rar_inspector.py --dir $test_dir --mode simple --output reports\test_inspection.json
}
elseif ($choice -eq "2") {
    Write-Host ""
    Write-Host "[Scan Comics - Simple mode]" -ForegroundColor Green
    & $pythonPath -X utf8 src\rar_inspector.py --dir "Z:\漫画\日漫\日语原版\Comics" --mode simple --output reports\comics_inspection_simple.json
}
elseif ($choice -eq "3") {
    Write-Host ""
    Write-Host "[Scan Comics - Detailed mode]" -ForegroundColor Yellow
    Write-Host "WARNING: Detailed mode generates large data!" -ForegroundColor Yellow
    $confirm = Read-Host "Confirm? (y/n)"
    if ($confirm -eq "y") {
        & $pythonPath -X utf8 src\rar_inspector.py --dir "Z:\漫画\日漫\日语原版\Comics" --mode detailed --output reports\comics_inspection_detailed.json
    }
}
elseif ($choice -eq "4") {
    Write-Host ""
    Write-Host "[Custom scan]" -ForegroundColor Green
    $dir = Read-Host "Directory path"
    $mode = Read-Host "Mode (simple/detailed)"
    $output = Read-Host "Output filename (without path)"
    & $pythonPath -X utf8 src\rar_inspector.py --dir $dir --mode $mode --output "reports\$output"
}
else {
    Write-Host "Invalid choice" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Done! Log: rar_inspector.log" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Read-Host "Press Enter to exit"
