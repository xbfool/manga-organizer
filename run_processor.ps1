# Nested RAR Processor
# Fix encoding issues for Chinese paths
chcp 65001 > $null
$OutputEncoding = [Console]::OutputEncoding = [Console]::InputEncoding = [System.Text.Encoding]::UTF8
$PSDefaultParameterValues['*:Encoding'] = 'utf8'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Nested RAR Processor" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Set Python path
$pythonPath = "C:\Users\xbfoo\miniconda3\envs\manga\python.exe"

Write-Host "Select mode:" -ForegroundColor Yellow
Write-Host "1. Test (5 files)"
Write-Host "2. Test (50 files)"
Write-Host "3. Dry-run preview"
Write-Host "4. Full processing (1472 files)"
Write-Host "5. Resume from last"
Write-Host "6. View progress"
Write-Host "7. Custom"
Write-Host ""

$choice = Read-Host "Enter choice (1-7)"

if ($choice -eq "1") {
    Write-Host ""
    Write-Host "[Test - 5 files]" -ForegroundColor Green
    & $pythonPath -X utf8 src\nested_rar_processor.py --use-config --max-files 5 --report reports\process_test_5files.json
}
elseif ($choice -eq "2") {
    Write-Host ""
    Write-Host "[Test - 50 files]" -ForegroundColor Green
    $confirm = Read-Host "Confirm? (y/n)"
    if ($confirm -eq "y") {
        & $pythonPath -X utf8 src\nested_rar_processor.py --use-config --max-files 50 --report reports\process_test_50files.json
    }
}
elseif ($choice -eq "3") {
    Write-Host ""
    Write-Host "[Dry-run mode]" -ForegroundColor Green
    $num = Read-Host "Number of files to preview (10-20)"
    & $pythonPath -X utf8 src\nested_rar_processor.py --use-config --max-files $num --dry-run
}
elseif ($choice -eq "4") {
    Write-Host ""
    Write-Host "[Full processing - 1472 files]" -ForegroundColor Red
    $confirm = Read-Host "Confirm? (yes/no)"
    if ($confirm -eq "yes") {
        & $pythonPath -X utf8 src\nested_rar_processor.py --use-config --report reports\process_full.json
    }
}
elseif ($choice -eq "5") {
    Write-Host ""
    Write-Host "[Resume mode]" -ForegroundColor Green
    $confirm = Read-Host "Confirm? (y/n)"
    if ($confirm -eq "y") {
        & $pythonPath -X utf8 src\nested_rar_processor.py --use-config --resume --report reports\process_resume.json
    }
}
elseif ($choice -eq "6") {
    Write-Host ""
    Write-Host "[View progress]" -ForegroundColor Green
    if (Test-Path ".progress\processing_progress.json") {
        & $pythonPath -X utf8 src\progress_tracker.py --file .progress\processing_progress.json --action summary
        Write-Host ""
        $export = Read-Host "Export report? (y/n)"
        if ($export -eq "y") {
            & $pythonPath -X utf8 src\progress_tracker.py --file .progress\processing_progress.json --action export --output reports\progress_summary.txt
            Write-Host "Saved: reports\progress_summary.txt" -ForegroundColor Green
        }
    } else {
        Write-Host "Progress file not found" -ForegroundColor Yellow
    }
}
elseif ($choice -eq "7") {
    Write-Host ""
    Write-Host "[Custom processing]" -ForegroundColor Green
    $input_dir = Read-Host "Input directory"
    $output_dir = Read-Host "Output directory"
    $max_files = Read-Host "Max files (blank=all)"
    $resume = Read-Host "Resume? (y/n)"

    $args = @("--input", $input_dir, "--output", $output_dir, "--report", "reports\custom.json")

    if ($max_files -ne "") {
        $args += @("--max-files", $max_files)
    }

    if ($resume -eq "y") {
        $args += "--resume"
    }

    & $pythonPath -X utf8 src\nested_rar_processor.py @args
}
else {
    Write-Host "Invalid choice" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Done! Log: nested_rar_processor.log" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Read-Host "Press Enter to exit"
