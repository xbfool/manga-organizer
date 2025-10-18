# Test using config.json paths
chcp 65001 > $null
$OutputEncoding = [Console]::OutputEncoding = [Console]::InputEncoding = [System.Text.Encoding]::UTF8
$PSDefaultParameterValues['*:Encoding'] = 'utf8'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$pythonPath = "C:\Users\xbfoo\miniconda3\envs\manga\python.exe"

Write-Host "Testing with config.json paths..." -ForegroundColor Cyan

& $pythonPath -X utf8 src\nested_rar_processor.py --use-config --max-files 1 --report reports\test_config.json
