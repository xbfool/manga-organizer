# Test nested_rar_processor_v2 with metadata
chcp 65001 > $null
$OutputEncoding = [Console]::OutputEncoding = [Console]::InputEncoding = [System.Text.Encoding]::UTF8
$PSDefaultParameterValues['*:Encoding'] = 'utf8'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$pythonPath = "C:\Users\xbfoo\miniconda3\envs\manga\python.exe"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Testing V2 Processor (with metadata)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

& $pythonPath -X utf8 src\nested_rar_processor_v2.py --use-config --max-files 1 --report reports\test_v2.json
