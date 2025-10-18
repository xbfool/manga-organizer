# Test encoding
chcp 65001 > $null
$OutputEncoding = [Console]::OutputEncoding = [Console]::InputEncoding = [System.Text.Encoding]::UTF8
$PSDefaultParameterValues['*:Encoding'] = 'utf8'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$pythonPath = "C:\Users\xbfoo\miniconda3\envs\manga\python.exe"

Write-Host "Testing Chinese path encoding..." -ForegroundColor Cyan
& $pythonPath -X utf8 src\nested_rar_processor.py --input "Z:\漫画\日漫\日语原版\Comics" --output "output\test_encoding" --max-files 1 --report reports\test_encoding.json
